"""Vanilla dam where a pond-layer river meets the engine sea (Guillermo, 2026-10-17, Narva spawn (2392, 6948): "agua de
dos colores y a dos alturas" -> "Presa vanilla", as Livonia does with dam_stone_40; the real Narva has its dam and the
Kreenholm falls there).

Model: DZ\\structures\\industrial\\dams\\dam_stone_40.p3d, read from its ODOL. Visual LOD x +-20.03, y +-4.077, z +-2.04;
roadway (3e15, concrete_ext, walkable) flat at y 4.077 for |x| >= 6.1 with a 6.8 m spillway notch at y 2.477 in the
middle; geometry LOD = 3 convex components (the solid used here); no water faces, no memory LOD. Livonia (enoch) places
it 7 times, always level (Y vertical), across a stream valley, with a 50 x 50 m moss pond on one side whose edge runs
under the wall and dry ground on the other (evidence/v31-pond-layer-2026-10-13/dam/scripts/livonia_dams.py; levels in
LIVONIA_WATER below).

Per site (JSON list: id, pieces = [[x, z], ...] centres of a straight chain, bearing = model X axis in degrees from
north, downstream = +1 / -1 (side of model +Z that holds the sea), cut_radius m, frozen_exception = contract file,
relative to the sites file):
  level     upstream water = highest plane of the envelope cells within 6 m upstream of the axis along the chain;
            origin y = level - WATER_REL, WATER_REL = median of Livonia's water-minus-origin (seat_livonia()).
  cut       envelope and cover cells whose centre lies downstream of the axis line, within cut_radius of the chain
            centre and in an envelope component that touches the chain rectangle, leave the water layer: the pond then
            ends on the axis, under the wall, as Livonia's ponds do (the ground beyond is the old bed, dry at mid tide).
  bury      the vertices of the new pond border that lie inside the wall (|z_local| <= BURY_HALF) are raised to their
            highest incident kept plane + EDGE_MARGIN + PAD (bury_edges_v31.py:1-3 rule), so the pond edge is buried
            and bury_edges finds nothing new; frozen vertices included, because the wall covers them.
  abutment  each free end of the chain is seated as Livonia's: the terrain on the end face (x_local = +-20, z_local in
            [-2.04, 2.04]) must reach roadway top - END_EXPOSURE_MAX (Livonia's largest end exposure). Solved as one
            raise-only linear programme over the vertices within ABUT_R of the end samples: minimise the total raise, no
            vertex above the roadway top, the planar NW-SE triangles exact at the samples, and every changed triangle's
            gradient components bounded by max(ABUT_SLOPE/sqrt 2, before), ABUT_SLOPE = tan 35 deg, the slope guard of
            the EV102 sills and cones (sills_and_cones_ev102.py:29), so no changed face is steeper than 35 deg unless it
            already was. A 1:2 cone (that file's CONE_SLOPE) is infeasible within ABUT_R at the Narva west end, where the
            end meets a sea basin 2-5 m deep. A raise may reach a vertex of a kept pond cell (the water then meets the
            mound) but may not leave that cell with no corner under its plane (it would leave the footprint).
Sites are applied in order on the running terrain and envelope.
Frozen exception (HANDOFF.md:13 keeps reserve, platform and Narva fixed): a site may move frozen vertices only through
its contract (evidence/v31-pond-layer-2026-10-13/dam/frozen-exception-narva.json for narva-dam, approved by Guillermo
on 2026-10-18 "tal cual"), whose sha256 is pinned in PINNED_CONTRACTS below and in dam_gates_v31.py. The contract lists
every vertex the site may move, with its exact input height (old) and its output height (new, +-1e-4 m), and every
envelope/cover cell the cut removes. The pass refuses before writing anything if: the contract sha differs; an input
height at a contract vertex differs from old (T_IN changed there: re-derive and re-approve, never relax); the moved set,
any new height, the cut set or the set of sea vertices turned dry differs from the contract; any vertex is lowered.
Outputs: terrain (heights; masks unchanged; new mask v31_dam = vertices this pass raised), cover, envelope, records
(stage_bridges_v31.py format: site, piece, model, matrix = model X, Y, Z axes then position), report.
Usage: dam_v31.py <terrain.npz> <cover.npy> <envelope.npy> <sites.json> <out_terrain.npz> <out_cover.npy> <out_envelope.npy>
       <records.json> <report.json>
"""
import hashlib, json, math, os, sys
import numpy as np
from scipy.ndimage import label
from scipy.optimize import linprog
from scipy.sparse import lil_matrix
sys.path.insert(0, r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts")
from odol_reader import ODOL

ZTOP, GN = 12282.0, 2048
MODEL = "dz\\structures\\industrial\\dams\\dam_stone_40.p3d"
P3D = "P:/DZ/structures/industrial/dams/dam_stone_40.p3d"
EDGE_MARGIN, PAD = 0.05, 0.01          # bury_edges_v31.py:10
BURY_HALF = 1.0                        # m; the wall is >= 2.3 m thick at the pond level (geometry LOD, y <= 2.4)
ABUT_R, ABUT_SLOPE, U_MAX = 18.0, math.tan(math.radians(35.0)), 6.0   # 35 deg: sills_and_cones_ev102.py:29
N8 = np.ones((3, 3), bool)
LIVONIA = "E:/DayZ-Baltic-Build/vanilla-tricks-20261013"
# Livonia's pond level beside each dam_stone_40 (x, z) -> water y: highest roadway face of the W-category water pieces
# (all enoch_50x50_moss) 6-32 m from the wall on its wet side; the other side has no water piece (dry ground). Measured
# by evidence/v31-pond-layer-2026-10-13/dam/scripts/livonia_dams.py over enoch_objects.csv and the pieces' ODOL roadway LODs.
LIVONIA_WATER = {(2160.92, 1366.35): 468.816, (2099.47, 3557.79): 309.974, (11411.71, 3679.62): 252.276,
                 (4826.54, 5095.7): 315.547, (1135.58, 5163.33): 246.689, (8499.5, 5136.89): 265.121,
                 (10337.87, 6034.18): 216.45}
# site id -> sha256 of its frozen-exception contract (the approved list; a new list needs a new approval and a new pin)
PINNED_CONTRACTS = {"narva-dam": "28191cce4fe4ec7f240bbaf14cc7a07546748a98fdaa5221661b1649150668a2"}
NEW_TOL = 1e-4                         # m, contract 'new' heights (LP round-off); 'old' heights are compared exactly
SEA_DRY = 0.75                         # m, mid tide: a vertex below it outside the water layer is engine sea


def load_contract(site_id, path):
    """The pinned contract of one site, or SystemExit."""
    if site_id not in PINNED_CONTRACTS:
        raise SystemExit(f"dam_v31: refused: {site_id}: no pinned frozen-exception contract")
    if not os.path.isfile(path) or sha(path) != PINNED_CONTRACTS[site_id]:
        raise SystemExit(f"dam_v31: refused: {site_id}: contract {path} missing or sha256 != pinned "
                         f"{PINNED_CONTRACTS[site_id][:12]}... (an edited list needs a new approval and a new pin)")
    con = json.load(open(path))
    if con.get("site") != site_id or con.get("schema") != "dam-frozen-exception.v1":
        raise SystemExit(f"dam_v31: refused: {site_id}: contract site/schema mismatch")
    return con


def contract_diff(con, H_in, H_out, masks, cut, sea_dry):
    """List of human-readable mismatches between one site's result and its contract (empty = conforms)."""
    bad = []
    want = {(v["r"], v["c"]): v for v in con["vertices"]}
    moved = {(int(r), int(c)) for r, c in np.argwhere(H_out != H_in)}
    for k in sorted(moved - set(want)):
        bad.append(f"vertex {6 * k[1]},{int(ZTOP - 6 * k[0])} moved but not in the contract")
    for k, v in sorted(want.items()):
        r, c = k
        if np.float32(H_in[r, c]) != np.float32(v["old"]):
            bad.append(f"vertex {v['x']},{v['z']}: input {float(H_in[r, c])!r} != contract old {v['old']!r}")
        if abs(float(H_out[r, c]) - v["new"]) > NEW_TOL:
            bad.append(f"vertex {v['x']},{v['z']}: output {float(H_out[r, c])!r} != contract new {v['new']!r}")
        for m in ("reserve", "platform", "narva"):
            if bool(masks[m][r, c]) != v[m]:
                bad.append(f"vertex {v['x']},{v['z']}: mask {m} {bool(masks[m][r, c])} != contract {v[m]}")
    low = np.argwhere(H_out < H_in)
    if len(low):
        bad.append(f"{len(low)} vertices lowered (first {6 * low[0][1]},{int(ZTOP - 6 * low[0][0])})")
    cut_want = {(k["r"], k["c"]) for k in con["cut_cells"]}
    cut_got = {(int(r), int(c)) for r, c in np.argwhere(cut)}
    if cut_got != cut_want:
        bad.append(f"cut cells differ: {len(cut_got - cut_want)} extra, {len(cut_want - cut_got)} missing")
    dry_want = {(v["r"], v["c"]) for v in con["vertices"] if v["sea_to_dry"]}
    dry_got = {(int(r), int(c)) for r, c in np.argwhere(sea_dry)}
    if dry_got != dry_want:
        bad.append(f"sea vertices turned dry differ: {sorted(dry_got ^ dry_want)[:5]}")
    return bad


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# ---------------------------------------------------------------- model
_MODEL = {}


def model():
    """Geometry LOD convex components (half-spaces + points), visual bbox, roadway top / notch heights."""
    if not _MODEL:
        from scipy.spatial import ConvexHull
        od = ODOL.from_file(P3D)
        geo = [l for l in od.lods if abs(l.resolution - 1e13) < 1e9]
        vis = [l for l in od.lods if abs(l.resolution - 1.0) < 1e-6]
        rw = [l for l in od.lods if abs(l.resolution - 3e15) < 1e10]
        if len(geo) != 1 or len(vis) != 1 or len(rw) != 1:
            raise SystemExit("dam_v31: refused: dam_stone_40 needs exactly one geometry, visual and roadway LOD")
        V = np.array([(p.x, p.y, p.z) for p in geo[0].vertices])
        comps = []
        for s in geo[0].named_selections:
            if s.name.lower().startswith("component"):
                P = V[sorted(set(int(i) for i in s.selected_vertices))]
                h = ConvexHull(P)
                comps.append((h.equations[:, :3].copy(), h.equations[:, 3].copy(), P))
        Vv = np.array([(p.x, p.y, p.z) for p in vis[0].vertices])
        Vr = np.array([(p.x, p.y, p.z) for p in rw[0].vertices])
        _MODEL.update(comps=comps, vis_min=Vv.min(0), vis_max=Vv.max(0), top=float(Vr[:, 1].max()),
                      notch=float(Vr[:, 1].min()), half_len=float(max(-Vv[:, 0].min(), Vv[:, 0].max())))
    return _MODEL


def axes(bearing):
    b = math.radians(bearing)
    ax = np.array([math.sin(b), 0.0, math.cos(b)])
    return ax, np.array([0.0, 1.0, 0.0]), np.array([-ax[2], 0.0, ax[0]])     # det +1; Livonia rows: az = (-ax_z, 0, ax_x)


def record_matrix(x, y, z, bearing):
    ax, ay, az = axes(bearing)
    return [float(v) for v in np.concatenate([ax, ay, az, [x, y, z]])]


def to_local(mat, X, Y, Z):
    A = np.array(mat[:9]).reshape(3, 3).T          # columns ax, ay, az
    t = np.array(mat[9:12])
    d = np.stack([X - t[0], Y - t[1], Z - t[2]], -1)
    return d @ A


def solid(mats, X, Y, Z, margin=0.0):
    """True where (X, Y, Z) lies inside the geometry LOD of any record (margin m inside every face)."""
    ins = np.zeros(np.shape(X), bool)
    for mat in mats:
        m = to_local(mat, X, Y, Z)
        for nrm, off, _ in model()["comps"]:
            ins |= np.all(m @ nrm.T + off <= -margin, axis=-1)
    return ins


# ---------------------------------------------------------------- terrain sampling (planar NW-SE triangles)
def tri_weights(x, z):
    """Vertex indices (3) and weights of the planar triangle under (x, z): fc >= fr -> NW + fc (NE - NW) + fr (SE - NE);
    else NW + fr (SW - NW) + fc (SE - SW)."""
    c = int(math.floor(x / 6.0)); r = int(math.floor((ZTOP - z) / 6.0))
    fc = x / 6.0 - c; fr = (ZTOP - z) / 6.0 - r
    if fc >= fr:
        return [(r, c), (r, c + 1), (r + 1, c + 1)], [1 - fc, fc - fr, fr]
    return [(r, c), (r + 1, c), (r + 1, c + 1)], [1 - fr, fr - fc, fc]


def height(H, x, z):
    v, w = tri_weights(x, z)
    return sum(wi * H[ri, ci] for (ri, ci), wi in zip(v, w))


def height_grid(H, X, Z):
    c = np.floor(X / 6.0).astype(int); r = np.floor((ZTOP - Z) / 6.0).astype(int)
    fc = X / 6.0 - c; fr = (ZTOP - Z) / 6.0 - r
    nw, ne, sw, se = H[r, c], H[r, c + 1], H[r + 1, c], H[r + 1, c + 1]
    return np.where(fc >= fr, nw + fc * (ne - nw) + fr * (se - ne), nw + fr * (sw - nw) + fc * (se - sw))


# ---------------------------------------------------------------- seat metrics (same function for Livonia and Baltic)
def seat(sample, mat, free_ends, water_y):
    """sample(x, z) -> terrain height. Metrics of one record: end exposure (roadway top - terrain at x_local = +-20 on
    z_local -2.04 / 0 / +2.04, free ends only), bottom clearance (terrain - bottom over the bottom footprint, >= 0 means
    buried, < 0 means air under the wall), top burial (terrain - roadway over the roadway footprint), water_rel."""
    M = model(); top, bot = M["top"], float(M["vis_min"][1])
    A = np.array(mat[:9]).reshape(3, 3).T; t = np.array(mat[9:12])
    W = lambda xl, zl: t + A @ np.array([xl, 0.0, zl])
    out = dict(origin_y=round(float(t[1]), 3))
    ends = []
    for sgn in free_ends:
        for zl in (-2.04, 0.0, 2.04):
            p = W(sgn * 20.0, zl)
            ends.append(round(float(t[1] + top - sample(p[0], p[2])), 3))
    out["end_exposure"] = ends
    xs = np.arange(-20.0, 20.01, 1.0); zs = np.arange(-1.8, 1.81, 0.6)
    clear, bur = [], []
    for xl in xs:
        for zl in zs:
            p = W(xl, zl); h = sample(p[0], p[2])
            clear.append(h - (t[1] + bot))
            rw = M["notch"] if abs(xl) < 3.3 else top
            bur.append(h - (t[1] + rw))
    out["bottom_clearance_min"] = round(float(min(clear)), 3)
    out["top_burial_max"] = round(float(max(bur)), 3)
    out["water_rel"] = None if water_y is None else round(float(water_y - t[1]), 3)
    return out


def seat_livonia():
    """Livonia's 7 dam_stone_40: seat metrics with both ends free and the pond level from LIVONIA_WATER."""
    sys.path.insert(0, LIVONIA + "/scripts")
    from terrain import Terrain, objects                          # vanilla-tricks-20261013/scripts/terrain.py:8-55
    T = Terrain("enoch")
    rows = []
    for o in objects("enoch"):
        if "dam_stone_40" not in o["shape"]:
            continue
        mat = [o["ax_x"], o["ax_y"], o["ax_z"], o["ay_x"], o["ay_y"], o["ay_z"], o["az_x"], o["az_y"], o["az_z"], o["x"], o["y"], o["z"]]
        wy = LIVONIA_WATER[(round(o["x"], 2), round(o["z"], 2))]
        rows.append(dict(x=round(o["x"], 2), z=round(o["z"], 2), **seat(lambda x, z: float(T.y(x, z)), mat, (-1, 1), wy)))
    return rows


def ranges(rows):
    f = lambda k: [v for r in rows for v in (r[k] if isinstance(r[k], list) else [r[k]]) if v is not None]
    return {k: [min(f(k)), max(f(k))] for k in ("end_exposure", "bottom_clearance_min", "top_burial_max", "water_rel")}


# ---------------------------------------------------------------- main
def c2v_any(m):
    o = np.zeros((GN, GN), bool)
    for dr in (0, 1):
        for dc in (0, 1):
            o[dr:dr + GN - 1, dc:dc + GN - 1] |= m
    return o


def c2v_max(a):
    o = np.full((GN, GN), -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            o[dr:dr + GN - 1, dc:dc + GN - 1] = np.maximum(o[dr:dr + GN - 1, dc:dc + GN - 1], a)
    return o


def abutments(H, ends, top_targets, keep_v, cap):
    """Raise-only LP: terrain at every end-face sample >= its target; minimise the total raise. keep_v vertices never move;
    a raised vertex of a kept pond cell is allowed (it buries part of the cell), the caller refuses one that empties it."""
    G = ABUT_SLOPE / math.sqrt(2.0)
    samples, cand = [], set()
    for (p0, p1), tgt in zip(ends, top_targets):
        for s in np.linspace(0.0, 1.0, 9):
            x, z = p0 + s * (p1 - p0)
            samples.append((x, z, tgt))
    for x, z, _ in samples:
        c0 = int(x // 6); r0 = int((ZTOP - z) // 6); k = int(ABUT_R // 6) + 2
        for r in range(r0 - k, r0 + k + 2):
            for c in range(c0 - k, c0 + k + 2):
                if math.hypot(6 * c - x, ZTOP - 6 * r - z) <= ABUT_R and not keep_v[r, c]:
                    cand.add((r, c))
    cand = sorted(cand); idx = {v: i for i, v in enumerate(cand)}; n = len(cand)
    rows, rhs = [], []
    for x, z, tgt in samples:
        v, w = tri_weights(x, z)
        h0 = sum(wi * H[a, b] for (a, b), wi in zip(v, w))
        if h0 >= tgt:
            continue
        row = {}
        for (a, b), wi in zip(v, w):
            if (a, b) in idx and wi > 1e-9:
                row[idx[(a, b)]] = row.get(idx[(a, b)], 0.0) - wi
        if not row:
            return None, dict(infeasible=f"end sample ({x:.1f}, {z:.1f}) has no free vertex")
        rows.append(row); rhs.append(-(tgt - h0))
    # slope rows on every triangle with a candidate corner
    tris = set()
    for (r, c) in cand:
        for dr in (-1, 0):
            for dc in (-1, 0):
                tris.add((r + dr, c + dc))
    for (r, c) in sorted(tris):
        for kind in ("up", "lo"):
            if kind == "up":   # NW, NE, SE : dh/dx = (NE - NW)/6 ; dh/dz = -(SE - NE)/6
                comps = [({(r, c + 1): 1, (r, c): -1}), ({(r + 1, c + 1): -1, (r, c + 1): 1})]
            else:              # NW, SW, SE : dh/dx = (SE - SW)/6 ; dh/dz = -(SW - NW)/6
                comps = [({(r + 1, c + 1): 1, (r + 1, c): -1}), ({(r + 1, c): -1, (r, c): 1})]
            for comp in comps:
                if not any(v in idx for v in comp):
                    continue
                g0 = sum(s * H[v] for v, s in comp.items()) / 6.0
                lim = max(G, abs(g0))
                for sgn in (1, -1):        # sgn * g <= lim
                    row = {}
                    const = sgn * g0
                    for v, s in comp.items():
                        if v in idx:
                            row[idx[v]] = row.get(idx[v], 0.0) + sgn * s / 6.0
                    rows.append(row); rhs.append(lim - const)
    A = lil_matrix((len(rows), n))
    for i, row in enumerate(rows):
        for j, a in row.items():
            A[i, j] = a
    res = linprog(np.ones(n), A_ub=A.tocsr(), b_ub=np.array(rhs), bounds=[(0.0, max(0.0, min(U_MAX, cap - H[v]))) for v in cand], method="highs")
    if res.status != 0:
        return None, dict(infeasible=res.message)
    u = np.where(res.x > 1e-6, res.x, 0.0)
    return {cand[i]: float(u[i]) for i in range(n) if u[i] > 0}, dict(candidates=n, rows=len(rows), total_raise=round(float(u.sum()), 3))


def main():
    (tp, cp, ep, sp, out_t, out_c, out_e, rec_p, rep_p) = sys.argv[1:10]
    for p in (out_t, out_c, out_e, rec_p, rep_p):
        assert not os.path.exists(p), f"fresh output required: {p}"
    z = np.load(tp); arrays = {k: z[k].copy() for k in z.files}
    H0 = arrays["heights"].astype(np.float64); H = H0.copy()
    cover = np.load(cp).astype(np.float64); env = np.load(ep).astype(np.float64)
    frozen = arrays["reserve"] | arrays["platform"] | arrays["narva"]
    M = model()
    liv = seat_livonia(); rng = ranges(liv)
    water_rel = float(np.median([r["water_rel"] for r in liv]))
    expo_max = rng["end_exposure"][1]
    sites = json.load(open(sp))
    records, rep_sites = [], []
    cut_all = np.zeros(cover.shape, bool)
    contracts = {}
    for s in sites:
        Hs = H.copy()
        if "budget" in s:
            raise SystemExit(f"dam_v31: refused: {s['id']}: 'budget' is retired; the site needs its frozen_exception contract")
        con = load_contract(s["id"], os.path.join(os.path.dirname(os.path.abspath(sp)), s["frozen_exception"]))
        contracts[s["id"]] = con
        stale = [v for v in con["vertices"] if np.float32(Hs[v["r"], v["c"]]) != np.float32(v["old"])]
        if stale:
            v = stale[0]
            raise SystemExit(f"dam_v31: refused: {s['id']}: the input terrain differs from the approved base at {len(stale)} "
                             f"contract vertices (first {v['x']},{v['z']}: {float(Hs[v['r'], v['c']])!r} != {v['old']!r}); "
                             f"re-derive the site on this terrain and get the new list approved")
        ax, ay, az = axes(s["bearing"])
        pcs = [np.array([p[0], p[1]], float) for p in s["pieces"]]
        ctr = np.mean(pcs, axis=0)
        u = np.array([ax[0], ax[2]]); n = np.array([az[0], az[2]]) * s["downstream"]   # plan: along, downstream
        half = M["half_len"]
        along = [float((p - ctr) @ u) for p in pcs]
        a0, a1 = min(along) - half, max(along) + half
        for p in pcs:
            assert abs(float((p - ctr) @ n)) < 1e-6, "pieces must lie on one straight axis"
        # cells: centres in plan
        rr, cc = np.mgrid[0:GN - 1, 0:GN - 1]
        X = 6.0 * cc + 3.0; Z = ZTOP - 6.0 * rr - 3.0
        sa = (X - ctr[0]) * u[0] + (Z - ctr[1]) * u[1]
        sn = (X - ctr[0]) * n[0] + (Z - ctr[1]) * n[1]
        envc = np.isfinite(env)
        rect = (sa >= a0) & (sa <= a1) & (np.abs(sn) <= 6.0)
        # upstream level
        up = envc & (sa >= a0) & (sa <= a1) & (sn < 0) & (sn >= -6.0)
        if not up.any():
            raise SystemExit(f"dam_v31: refused: {s['id']}: no envelope cell within 6 m upstream of the axis")
        level = float(np.nanmax(np.where(up, env, np.nan)))
        oy = round(level - water_rel, 3)
        # cut
        lab, _ = label(envc, N8)
        comps = np.unique(lab[rect & envc]); comps = comps[comps > 0]
        cut = np.isin(lab, comps) & (sn > 0) & (np.hypot(X - ctr[0], Z - ctr[1]) <= s["cut_radius"])
        cut_all |= cut
        kept_env = envc & ~cut
        env = np.where(cut, np.nan, env)                             # the next site sees this cut
        # bury: vertices touching kept and cut cells, inside the wall
        vk = c2v_any(kept_env); vc = c2v_any(cut)
        VPk = c2v_max(np.where(kept_env, env, -np.inf))
        vr, vcol = np.mgrid[0:GN, 0:GN]
        VX = 6.0 * vcol; VZ = ZTOP - 6.0 * vr
        vsa = (VX - ctr[0]) * u[0] + (VZ - ctr[1]) * u[1]; vsn = (VX - ctr[0]) * n[0] + (VZ - ctr[1]) * n[1]
        border = vk & vc
        inwall = (np.abs(vsn) <= BURY_HALF) & (vsa >= a0) & (vsa <= a1)
        need = border & (H < VPk + EDGE_MARGIN)
        bury = need & inwall
        H = np.where(bury, VPk + EDGE_MARGIN + PAD, H)
        unburied = need & ~inwall
        # records
        mats = []
        for k, p in enumerate(pcs):
            mat = record_matrix(p[0], oy, p[1], s["bearing"])
            mats.append(mat)
            records.append(dict(site=s["id"], piece=k, model=MODEL, matrix=mat))
        # abutments on the free ends of the chain
        top = oy + M["top"]
        tgt = top - expo_max + 0.02
        azp = np.array([az[0], az[2]])
        end_lines = []
        for ae in (min(along) - 20.0, max(along) + 20.0):               # Livonia's end samples: x_local = +-20.0
            q = ctr + ae * u
            end_lines.append((q - 2.04 * azp, q + 2.04 * azp))
        keep_v = np.zeros((GN, GN), bool)                           # the map border never moves
        keep_v[:2, :] = keep_v[-2:, :] = keep_v[:, :2] = keep_v[:, -2:] = True
        raise_, lp = abutments(H, end_lines, [tgt, tgt], keep_v, top)
        if raise_ is None:
            raise SystemExit(f"dam_v31: refused: {s['id']}: abutment LP infeasible: {lp}")
        for (r, c), dv in raise_.items():
            H[r, c] += dv
        H = H.astype(np.float32).astype(np.float64)
        # a raise may bury part of a kept pond cell but never all of it (it would leave the footprint: new edges)
        cmin = lambda A: np.minimum.reduce([A[:-1, :-1], A[1:, :-1], A[:-1, 1:], A[1:, 1:]])
        vis0 = kept_env & (cmin(H0) < env); vis1 = kept_env & (cmin(H) < env)
        if (vis0 & ~vis1).any():
            raise SystemExit(f"dam_v31: refused: {s['id']}: the abutments bury {int((vis0 & ~vis1).sum())} visible kept pond cells")
        moved = (H != Hs)
        fz_moved = moved & frozen
        sea_dry = moved & (Hs < SEA_DRY) & ~c2v_any(np.isfinite(cover) | envc) & (H >= SEA_DRY)
        bad = contract_diff(con, Hs, H, arrays, cut, sea_dry)
        cov_cut = {(int(r), int(c)) for r, c in np.argwhere(cut & np.isfinite(cover))}
        if cov_cut != {(k["r"], k["c"]) for k in con["cut_cells"]}:
            bad.append("cover cells removed by the cut differ from the contract")
        if bad:
            raise SystemExit(f"dam_v31: refused: {s['id']}: result differs from the approved contract "
                             f"({len(bad)} mismatches): " + "; ".join(bad[:8]))
        rep_sites.append(dict(
            id=s["id"], bearing=s["bearing"], pieces=[[float(p[0]), float(p[1])] for p in pcs], downstream=s["downstream"],
            level=level, water_rel=round(level - oy, 3), origin_y=oy, roadway_top_y=round(top, 3), notch_y=round(oy + M["notch"], 3),
            bottom_y=round(oy + float(M["vis_min"][1]), 3), chain_along=[round(a0, 3), round(a1, 3)],
            cut_cells=int(cut.sum()), cut_cover_cells=int((cut & np.isfinite(cover)).sum()),
            cut_bbox_xz=[float(X[cut].min() - 3), float(X[cut].max() + 3), float(Z[cut].min() - 3), float(Z[cut].max() + 3)] if cut.any() else None,
            bury_vertices=[[int(6 * c), int(ZTOP - 6 * r), round(float(H0[r, c]), 3), round(float(H[r, c]), 3)] for r, c in np.argwhere(bury)],
            unburied_border_vertices=[[int(6 * c), int(ZTOP - 6 * r), round(float(H[r, c]), 3)] for r, c in np.argwhere(unburied)],
            abutment=dict(lp, target_y=round(tgt, 3), end_exposure_max=expo_max,
                          vertices=[[int(6 * c), int(ZTOP - 6 * r), round(float(H0[r, c]), 3), round(float(H[r, c]), 3)] for (r, c) in sorted(raise_)]),
            moved_vertices=int(moved.sum()), frozen_moved=int(fz_moved.sum()), frozen_moved_narva=int((moved & arrays["narva"]).sum()),
            max_raise=round(float((H - Hs).max()), 3), sea_vertices_turned_dry=int(sea_dry.sum()),
            frozen_exception=dict(file=s["frozen_exception"], sha256=PINNED_CONTRACTS[s["id"]], vertices=len(con["vertices"]),
                                  cut_cells=len(con["cut_cells"]), conforms=True)))
    cover2 = np.where(cut_all, np.nan, cover).astype(np.float32)
    env2 = env.astype(np.float32)
    arrays["heights"] = H.astype(np.float32)
    arrays["v31_dam"] = (H != H0)
    np.savez(out_t, **arrays)
    np.save(out_c, cover2); np.save(out_e, env2)
    with open(rec_p, "w", newline="\n") as f:
        json.dump(records, f, indent=1)
    rep = dict(schema="dam-v31.v2", inputs=dict(terrain=tp, terrain_sha256=sha(tp), cover=cp, cover_sha256=sha(cp), envelope=ep,
               envelope_sha256=sha(ep), sites=sp, sites_sha256=sha(sp)),
               outputs=dict(terrain_sha256=sha(out_t), cover_sha256=sha(out_c), envelope_sha256=sha(out_e), records_sha256=sha(rec_p)),
               model=dict(path=MODEL, top=M["top"], notch=M["notch"], half_len=M["half_len"], vis_min=M["vis_min"].tolist(), vis_max=M["vis_max"].tolist()),
               livonia=dict(seats=liv, ranges=rng, water_rel_median=water_rel),
               params=dict(EDGE_MARGIN=EDGE_MARGIN, PAD=PAD, BURY_HALF=BURY_HALF, ABUT_R=ABUT_R, ABUT_SLOPE=ABUT_SLOPE, U_MAX=U_MAX),
               contracts={k: dict(sha256=PINNED_CONTRACTS[k], approval=v["approval"]) for k, v in contracts.items()},
               sites=rep_sites)
    with open(rep_p, "w", newline="\n") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep_sites, indent=1)[:6000])


if __name__ == "__main__":
    main()
