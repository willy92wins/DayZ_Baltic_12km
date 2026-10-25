"""EV110 bridge gates for tools/terrain/bridges_v31.py v5 (BALTIC-015). Independent of the tool: own ODOL parsing, own
planar NW-SE terrain, own exact extremes on polygons (candidate points = polygon vertices, polygon edges crossed with the
grid lines x = 6i, z = 12282 - 6j and the NW-SE diagonals, and grid vertices inside the polygon's plan, lifted onto it)
and a sampled second route where noted. Each gate prints 'G<n> PASS' or 'G<n> FAIL' with its numbers and writes JSON.

Usage: gates_v5.py <G1..G8> --run DIR [--v4 DIR] [--input NPZ] [--sites JSON] [--fixture DIR ...] [--out JSON]
  --run    folder with terrain-br.npz, envelope-br.npy, bridge-records.json, bridge-report.json (the run under test)
  --v4     the v4 baseline of the same inputs (same file names)
  --input  the terrain the run started from (G5, G6)
  --sites  the sites file of the run
  --fixture  G3: sweep folders (one site, several widths), each with sites.json, v4/ and run/: the opening must not drop
           below v4 and the excess over v4 must not jump between neighbouring widths; G7: overlap fixture run folder
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts")
from odol_reader import ODOL

DZ = Path("P:/DZ/structures/roads/bridges")
ZT, GN = 12282.0, 2048
STACK_DY = 5.04
VARIANT_MODELS = ("bridge_wood_50_1",)
CONT_TOL = 0.05                       # G3: max change of (run - v4) opening between neighbouring sweep widths
AGREE_TOL = 0.005                     # G7: tool's final measurement vs this script's
LEG_GAP = 0.05                        # G4 / G7: a foot more than this above its support hangs


# ---------- terrain ----------
def terr(H, x, z):
    x = np.asarray(x, float); z = np.asarray(z, float)
    c, r = x / 6.0, (ZT - z) / 6.0
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int); u, v = c - c0, r - r0
    nw, ne, sw, se = H[r0, c0], H[r0, c0 + 1], H[r0 + 1, c0], H[r0 + 1, c0 + 1]
    return np.where(u >= v, nw + u * (ne - nw) + v * (se - ne), nw + v * (sw - nw) + u * (se - sw))


def tri_vertices(x, z):
    c, r = x / 6.0, (ZT - z) / 6.0
    c0, r0 = int(math.floor(c)), int(math.floor(r))
    return [(r0, c0), (r0, c0 + 1), (r0 + 1, c0 + 1)] if c - c0 >= r - r0 else [(r0, c0), (r0 + 1, c0 + 1), (r0 + 1, c0)]


def cands(P):
    """Exact-extreme candidates of (face height - terrain) over a planar polygon P (k, 3)."""
    P = np.asarray(P, float); out = [P]
    gx = lambda Q: Q[..., 0] / 6.0
    gz = lambda Q: (ZT - Q[..., 2]) / 6.0
    gd = lambda Q: Q[..., 0] / 6.0 - (ZT - Q[..., 2]) / 6.0
    for i in range(len(P)):
        A, B = P[i], P[(i + 1) % len(P)]
        for f in (gx, gz, gd):
            fa, fb = f(A), f(B)
            if abs(fb - fa) < 1e-12:
                continue
            ks = np.arange(math.ceil(min(fa, fb)), math.floor(max(fa, fb)) + 1)
            if len(ks):
                tt = (ks - fa) / (fb - fa); out.append(A + tt[:, None] * (B - A))
    n = np.cross(P[1] - P[0], P[2] - P[0])
    if len(P) >= 3 and abs(n[1]) > 1e-9:
        cs = np.arange(math.ceil(P[:, 0].min() / 6), math.floor(P[:, 0].max() / 6) + 1)
        rs = np.arange(math.ceil((ZT - P[:, 2].max()) / 6), math.floor((ZT - P[:, 2].min()) / 6) + 1)
        if len(cs) and len(rs):
            C, R = np.meshgrid(cs, rs); X, Z = 6.0 * C.ravel(), ZT - 6.0 * R.ravel()
            inside = inside_poly(P, X, Z)
            if inside.any():
                Y = P[0, 1] - (n[0] * (X[inside] - P[0, 0]) + n[2] * (Z[inside] - P[0, 2])) / n[1]
                out.append(np.stack([X[inside], Y, Z[inside]], 1))
    return np.concatenate(out)


def inside_poly(P, X, Z):
    """Plan point-in-convex-polygon (either winding)."""
    s = []
    for i in range(len(P)):
        A, B = P[i], P[(i + 1) % len(P)]
        s.append((B[0] - A[0]) * (Z - A[2]) - (B[2] - A[2]) * (X - A[0]))
    s = np.array(s)
    return (s >= -1e-9).all(0) | (s <= 1e-9).all(0)


def clip(P, f, k):
    """Part of polygon P where f(P) <= k."""
    out = []; v = f(P)
    for i in range(len(P)):
        A, B, va, vb = P[i], P[(i + 1) % len(P)], v[i], v[(i + 1) % len(P)]
        if va <= k:
            out.append(A)
        if (va - k) * (vb - k) < 0:
            out.append(A + (k - va) / (vb - va) * (B - A))
    return np.array(out)


# ---------- models ----------
_M = {}


def lod(od, res):
    c = [l for l in od.lods if abs(l.resolution - res) <= 1e-6 * max(1, abs(res))]
    assert len(c) == 1, f"LOD {res} missing"
    return c[0]


def model(name):
    if name in _M:
        return _M[name]
    od = ODOL.from_file(str(DZ / f"{name}.p3d"))
    m = dict(name=name, od=od)
    rv = np.array([(p.x, p.y, p.z) for p in lod(od, 3e15).vertices])
    ax = 0 if np.ptp(rv[:, 0]) >= np.ptp(rv[:, 2]) else 2; lat = 2 - ax
    lo, hi = rv[:, ax].min(), rv[:, ax].max()
    ends = [rv[np.abs(rv[:, ax] - e) < 0.6, 1].max() for e in (lo, hi)]
    rt = []
    for f in lod(od, 3e15).faces:
        ids = list(f.vertex_indices)
        for i in range(1, len(ids) - 1):
            rt.append(rv[[ids[0], ids[i], ids[i + 1]]])
    rt = np.array(rt)
    m.update(ax=ax, lat=lat, lo=lo, hi=hi, ends=ends, road=rt, deck=rt[rt[..., 1].min(1) >= min(ends) - 0.01],
             c_lat=(rv[:, lat].max() + rv[:, lat].min()) / 2, half_w=np.ptp(rv[:, lat]) / 2)
    for res in (1.0, 2.0, 3.0, 4.0, 1e13):
        try:
            l = lod(od, res)
        except AssertionError:
            continue
        V = np.array([(p.x, p.y, p.z) for p in l.vertices]); key = np.unique(V.round(4), axis=0, return_inverse=True)[1].ravel()
        a, b, T, tc = [], [], [], []
        for f in l.faces:
            ids = list(f.vertex_indices)
            for j in ids[1:]:
                a.append(key[ids[0]]); b.append(key[j])
            for i in range(1, len(ids) - 1):
                T.append(V[[ids[0], ids[i], ids[i + 1]]]); tc.append(ids[0])
        n = key.max() + 1
        lab = connected_components(coo_matrix((np.ones(len(a)), (a, b)), shape=(n, n)), directed=False)[1][key]
        m[res] = dict(V=V, lab=lab, T=np.array(T), tlab=lab[np.array(tc)])
    _M[name] = m
    return m


def legs(m, res=1.0):
    d = m[res]; V, lab = d["V"], d["lab"]; ymin = V[:, 1].min(); out = []
    for k in np.unique(lab):
        p = V[lab == k]
        if p[:, 1].min() < ymin + 0.3:
            out.append(np.unique(p[p[:, 1] < p[:, 1].min() + 0.05].round(4), axis=0))
    return out


def ray_top(T, x, z, lowest=False):
    best = np.full(np.shape(x), np.nan)
    for A, B, C in T:
        mm = np.array([[B[0] - A[0], C[0] - A[0]], [B[2] - A[2], C[2] - A[2]]])
        if abs(np.linalg.det(mm)) < 1e-12:
            continue
        iv = np.linalg.inv(mm); u = iv[0, 0] * (x - A[0]) + iv[0, 1] * (z - A[2]); w = iv[1, 0] * (x - A[0]) + iv[1, 1] * (z - A[2])
        ins = (u >= -1e-9) & (w >= -1e-9) & (u + w <= 1 + 1e-9); y = A[1] + u * (B[1] - A[1]) + w * (C[1] - A[1])
        best = np.where(ins & ~((best <= y) if lowest else (best >= y)), y, best)
    return best


def world(M, P):
    M = np.asarray(M, float)
    return np.asarray(P, float) @ M[:9].reshape(3, 3) + M[9:12]


def matrix_errors(run):
    """Records whose matrix is not 12 finite numbers (review 2 of 15-10: a NaN position of a lower copy passed G8)."""
    bad = {}
    for r in run["rec"]:
        M = r.get("matrix")
        if not isinstance(M, list) or len(M) != 12:
            err = "matrix is not a list of 12 values"
        elif not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in M):
            err = "matrix has a non-finite or non-numeric value"
        else:
            continue
        bad[f"{r.get('site')}/{r.get('span')}/{r.get('role') or 'upper'}"] = err
    return bad


# ---------- run data ----------
def load_run(d):
    d = Path(d); t = np.load(d / "terrain-br.npz")
    return dict(dir=d, npz=t, H=t["heights"].astype(np.float64), env=np.load(d / "envelope-br.npy"),
                rec=json.load(open(d / "bridge-records.json")), rep=json.load(open(d / "bridge-report.json")))


def mname(r):
    return r["model"].split("\\")[-1][:-4]


def site_records(run):
    out = {}
    for r in run["rec"]:
        out.setdefault(r["site"], dict(upper=[], lower=[]))["lower" if r.get("role") == "stack-lower" else "upper"].append(r)
    return out


def level(run, sid):
    return [s for s in run["rep"]["sites"] if s["site"] == sid][0]["level"]


def outer_ends(m, ups):
    """(record, end index 0 = lo / 1 = hi, roadway end coordinate, inward sign) for the outer ends."""
    ups = sorted(ups, key=lambda r: r["span"])
    return [(ups[0], 0, m["lo"], 1.0), (ups[-1], 1, m["hi"], -1.0)]


# ---------- gates ----------
def g1(run):
    res = {}
    for sid, rr in site_records(run).items():
        m = model(mname(rr["upper"][0])); vals = []
        for rec, ei, e, inw in outer_ends(m, rr["upper"]):
            mn = np.inf
            for T in m["deck"]:
                P = clip(T, lambda Q: (Q[:, m["ax"]] - e) * inw, 2.0)
                if len(P) < 3:
                    continue
                C = cands(world(rec["matrix"], P))
                mn = min(mn, float((C[:, 1] - terr(run["H"], C[:, 0], C[:, 2])).min()))
            vals.append(round(mn, 4))
        res[sid] = vals
    ok = all(v >= 0.01 for vs in res.values() for v in vs)
    return ok, dict(rule="deck faces of the outer end strips (2 m): terrain <= deck - 0.01 m, exact", min_clearance_m=res)


def block_faces(m, ei):
    d = m[1.0]; V, lab = d["V"], d["lab"]; e = m["lo"] if ei == 0 else m["hi"]
    for k in np.unique(lab):
        p = V[lab == k]
        if p[:, 1].min() < -10 and np.abs(p[:, m["ax"]] - e).min() < 0.1:
            return d["T"][d["tlab"] == k]
    raise SystemExit("no block")


def ramp_points(m, ei, step=0.05):
    """Model points on the ramp underside (lower envelope of the slab) from the tip to the first leg."""
    d = m[1.0]; V, lab = d["V"], d["lab"]; ax, lat = m["ax"], m["lat"]
    e, inw = (m["lo"], 1.0) if ei == 0 else (m["hi"], -1.0)
    a = (V[:, ax] - e) * inw; ymin = V[:, 1].min()
    legk = [k for k in np.unique(lab) if V[lab == k, 1].min() < ymin + 0.3]
    a_leg = min(a[lab == k].min() for k in legk if a[lab == k].min() > 0)
    slab = max((k for k in np.unique(lab) if a[lab == k].min() <= 0.5 and np.ptp(a[lab == k]) > 3 and V[lab == k, 1].min() > m["ends"][ei] - 0.6),
               key=lambda k: np.ptp(a[lab == k]))
    T = d["T"][d["tlab"] == slab]
    sl = V[lab == slab, lat]
    A_, L_ = np.meshgrid(np.arange(step, a_leg, step), np.arange(sl.min(), sl.max() + 1e-9, step), indexing="ij")
    X = np.zeros(A_.shape + (3,)); X[..., ax] = e + inw * A_; X[..., lat] = L_
    y = ray_top(T, X[..., 0], X[..., 2], lowest=True)
    X[..., 1] = y; ok = np.isfinite(y)
    return X[ok], a_leg


def g2(run):
    out, ok = {}, True
    for sid, rr in site_records(run).items():
        m = model(mname(rr["upper"][0])); L = level(run, sid); ends = []
        for rec, ei, e, inw in outer_ends(m, rr["upper"]):
            if m["name"] == "bridge_metal_25":
                ex, samp = -np.inf, -np.inf
                for T in block_faces(m, ei):
                    W = world(rec["matrix"], T); C = cands(W)
                    ex = max(ex, float((C[:, 1] - terr(run["H"], C[:, 0], C[:, 2])).max()))
                    u = np.linspace(0, 1, 21); U, V_ = np.meshgrid(u, u); k = U + V_ <= 1
                    S = W[0] + U[k][:, None] * (W[1] - W[0]) + V_[k][:, None] * (W[2] - W[0])
                    samp = max(samp, float((S[:, 1] - terr(run["H"], S[:, 0], S[:, 2])).max()))
                good = ex <= 0.02
                ends.append(dict(end=ei, kind="block", max_exposure_m=round(ex, 4), sampled_second_route_m=round(samp, 4), pass_=good))
            else:
                P, a_leg = ramp_points(m, ei)
                W = world(rec["matrix"], P); air = W[:, 1] - terr(run["H"], W[:, 0], W[:, 2])
                wet = np.array([any(run["H"][v] < L for v in tri_vertices(x, z)) for x, z in zip(W[:, 0], W[:, 2])])
                bad = (air > 0.10) & ~wet
                good = not bad.any()
                ends.append(dict(end=ei, kind="ramp", first_leg_m=round(float(a_leg), 3), points=len(air), max_air_m=round(float(air.max()), 4),
                                 max_air_dry_m=round(float(air[~wet].max()), 4) if (~wet).any() else None,
                                 points_over_0_10_dry=int(bad.sum()), water_exceptions_listed=int(((air > 0.10) & wet).sum()), pass_=bool(good)))
            ok &= ends[-1]["pass_"]
        out[sid] = ends
    return ok, dict(rule="metal: max exposure of the visual-LOD pier block faces <= 0.02 m (exact); wood: air under the ramp "
                         "underside (lower envelope of the slab, 0.05 m grid, tip to first leg) <= 0.10 m except points over a "
                         "triangle with a vertex below the stream level (listed)", sites=out)


def opening(H, s, m, L):
    wb = math.radians(s["water_bearing"]); wd = np.array([math.sin(wb), math.cos(wb)]); wn = np.array([-wd[1], wd[0]])
    b = math.radians(s["bearing"]); dr = np.array([math.sin(b), math.cos(b)])
    sn = abs(wd[0] * dr[1] - wd[1] * dr[0]); td = min(m["half_w"] / max(sn, 1e-3), 30.0); qm = s["width"] / 2 + 12
    widths = []
    for t in np.arange(-td, td + 1e-9, 0.1):
        x0, z0 = s["x"] + t * wd[0], s["z"] + t * wd[1]
        # breakpoints: crossings of the section with x = 6i, z = ZT - 6j and the diagonals
        q = [-qm, qm]
        for gx0, gdx in ((x0 / 6, wn[0] / 6), ((ZT - z0) / 6, -wn[1] / 6), (x0 / 6 - (ZT - z0) / 6, wn[0] / 6 + wn[1] / 6)):
            if abs(gdx) > 1e-12:
                lo_, hi_ = sorted((gx0 - qm * gdx, gx0 + qm * gdx))
                q += [(k - gx0) / gdx for k in range(math.ceil(lo_), math.floor(hi_) + 1)]
        q = np.unique(np.clip(q, -qm, qm)); g = terr(H, x0 + q * wn[0], z0 + q * wn[1]) - (L - 0.02)
        segs, a0 = [], (q[0] if g[0] < 0 else None)
        for i in range(len(q) - 1):
            if (g[i] < 0) and not (g[i + 1] < 0):
                segs.append((a0, q[i] + g[i] / (g[i] - g[i + 1]) * (q[i + 1] - q[i]))); a0 = None
            elif not (g[i] < 0) and (g[i + 1] < 0):
                a0 = q[i] + g[i] / (g[i] - g[i + 1]) * (q[i + 1] - q[i])
        if a0 is not None:
            segs.append((a0, q[-1]))
        if not segs:
            widths.append(0.0); continue
        hit = [sg for sg in segs if sg[0] <= 0 <= sg[1]]
        sg = hit[0] if hit else min(segs, key=lambda sg: min(abs(sg[0]), abs(sg[1])))
        widths.append(sg[1] - sg[0])
    return float(min(widths))


def deck_vertices(run_or_H, s, m, ups):
    H = run_or_H; out = set()
    for rec in ups:
        P = np.array([[m["lo"], 0, m["c_lat"] - m["half_w"]], [m["hi"], 0, m["c_lat"] - m["half_w"]], [m["hi"], 0, m["c_lat"] + m["half_w"]], [m["lo"], 0, m["c_lat"] + m["half_w"]]])
        if m["ax"] == 2:
            P = P[:, [2, 1, 0]]
        W = world(rec["matrix"], P)
        c0, c1 = int(W[:, 0].min() // 6), int(W[:, 0].max() // 6) + 1; r0, r1 = int((ZT - W[:, 2].max()) // 6), int((ZT - W[:, 2].min()) // 6) + 1
        R, C = np.mgrid[r0:r1 + 1, c0:c1 + 1]; X, Z = 6.0 * C, ZT - 6.0 * R
        k = inside_poly(W, X, Z)
        out |= set(zip(R[k].tolist(), C[k].tolist()))
    return out


def g3(run, v4, sites, fixtures):
    res, ok = {}, True
    s_by = {s["id"]: s for s in sites}
    for sid, rr in site_records(run).items():
        s = s_by[sid]; m = model(mname(rr["upper"][0])); L = level(run, sid)
        dv = deck_vertices(run["H"], s, m, rr["upper"])
        w4 = {v for v in dv if v4["H"][v] < L}; w5 = {v for v in dv if run["H"][v] < L}
        o4, o5 = opening(v4["H"], s, m, L), opening(run["H"], s, m, L)
        good = w4 <= w5 and o5 >= o4 - 1e-6
        res[sid] = dict(wet_vertices_under_deck_v4=len(w4), v5=len(w5), lost=len(w4 - w5), opening_v4_m=round(o4, 4), opening_v5_m=round(o5, 4), pass_=good)
        ok &= good
    fx, rows = {}, []
    for f in fixtures or []:
        f = Path(f); s = json.load(open(f / "sites.json"))[0]; m = model(s["model"])
        a, b = load_run(f / "v4"), load_run(f / "run"); L = a["rep"]["sites"][0]["level"]
        o4, o5 = opening(a["H"], s, m, L), opening(b["H"], s, m, L)
        fx[f.name] = dict(site=s["id"], width=s["width"], opening_v4_m=round(o4, 6), opening_run_m=round(o5, 6), excess_m=round(o5 - o4, 6), pass_=o5 >= o4 - 1e-6)
        ok &= fx[f.name]["pass_"]; rows.append((s["id"], float(s["width"]), o5 - o4, f.name))
    cont = []                                                                  # neighbouring widths of the sweep, same site
    rows.sort()
    for (s1, w1, e1, n1), (s2, w2, e2, n2) in zip(rows, rows[1:]):
        if s1 != s2:
            continue
        good = abs(e2 - e1) <= CONT_TOL
        cont.append(dict(between=[n1, n2], widths=[w1, w2], excess_step_m=round(e2 - e1, 6), pass_=good))
        ok &= good
    if fixtures and len(rows) > 1 and not cont:
        ok = False
    return ok, dict(rule="wet vertices (H < level) under the deck plan: v4 subset of run; narrowest wet width across the water "
                         "axis under the deck (exact, sections every 0.1 m) >= v4; synthetic W fixtures likewise, and the run's "
                         f"excess over v4 changes by at most {CONT_TOL} m between neighbouring widths of the sweep (continuity)",
                    sites=res, fixtures=fx, continuity=cont, max_excess_step_m=round(max((abs(c["excess_step_m"]) for c in cont), default=0.0), 6))


def rel_frame(up, lo):
    """Map lower-record model coordinates into the upper record's model frame, from both records' real matrices."""
    U, Lw = np.asarray(up["matrix"], float), np.asarray(lo["matrix"], float)
    Ru, Rl = U[:9].reshape(3, 3), Lw[:9].reshape(3, 3); iRu = np.linalg.inv(Ru)
    return lambda P: (np.asarray(P, float) @ Rl + Lw[9:12] - U[9:12]) @ iRu


def contact(mu, ml, res, rel):
    """Per upper foot (LOD res of the upper model): its bottom minus the top of the lower record's own model (same LOD),
    in the upper model frame; None where no lower face lies under the foot."""
    T = rel(ml[res]["T"].reshape(-1, 3)).reshape(-1, 3, 3); rows = []
    for F in legs(mu, res):
        top = ray_top(T, F[:, 0], F[:, 2])
        rows.append(float(F[:, 1].min() - np.nanmax(top)) if np.isfinite(top).any() else None)
    return rows


def zfight(mu, ml, rel):
    """Coplanar overlapping face pairs between the upper model's LOD 1 and the lower record's model LOD 1 (real frames)."""
    T = mu[1.0]["T"]; Tl = rel(ml[1.0]["T"].reshape(-1, 3)).reshape(-1, 3, 3)
    def unit(X):
        n = np.cross(X[:, 1] - X[:, 0], X[:, 2] - X[:, 0]); nn = np.linalg.norm(n, axis=1); k = nn > 1e-12
        return X[k], n[k] / nn[k][:, None]
    T, n = unit(T); Tl, nl = unit(Tl)
    up = np.flatnonzero(T[..., 1].min(1) < -1.5); lo = np.flatnonzero(Tl[..., 1].max(1) > -3.5)
    if not len(up) or not len(lo):
        return 0
    Tl, nl = Tl[lo], nl[lo]; lmin, lmax = Tl.min(1), Tl.max(1); hits = 0
    for i in up:
        par = np.abs(np.abs(nl @ n[i]) - 1) <= 1e-6
        cop = np.abs((Tl[:, 0] - T[i, 0]) @ n[i]) <= 1e-3
        ov = (np.minimum(T[i].max(0), lmax) - np.maximum(T[i].min(0), lmin) > 1e-4).sum(1) >= 2
        hits += int((par & cop & ov).sum())
    return hits


def model_path(name):
    return f"dz\\structures\\roads\\bridges\\{name}.p3d"


def g4(run, sites):
    s_by = {s["id"]: s for s in sites}; res, ok = {}, True
    for sid, rr in site_records(run).items():
        s = s_by[sid]
        if not (s.get("stack") or s["model"] in VARIANT_MODELS or rr["lower"]):
            continue
        mu = model(mname(rr["upper"][0])); L = level(run, sid); row = dict(model=mu["name"], stack=bool(s.get("stack"))); errors = []
        def hang(rec, m):
            g = []
            for F in legs(m):
                W = world(rec["matrix"], F); g.append(float(W[:, 1].min() - terr(run["H"], W[:, 0], W[:, 2]).max()))
            return g
        if any(r["model"] != model_path(s["model"]) for r in rr["upper"] + rr["lower"]):
            errors.append("a record's model is not the site's model")
        good = True
        if s.get("stack"):
            ups = sorted(rr["upper"], key=lambda r: r["span"]); los = sorted(rr["lower"], key=lambda r: r["span"])
            if [r["span"] for r in ups] != [r["span"] for r in los]:
                errors.append("lower spans do not match the upper spans")
            per = []
            for up, lo in zip(ups, los):
                ml = model(mname(lo)); rel = rel_frame(up, lo)
                U, Lw = np.asarray(up["matrix"]), np.asarray(lo["matrix"])
                dyv = float((U[9:12] - Lw[9:12]) @ U[3:6]); axes = float(np.abs(U[:9] - Lw[:9]).max())
                gl = hang(lo, ml)                                                       # lower feet over the terrain
                lods = [r_ for r_ in (1.0, 2.0, 3.0, 4.0, 1e13) if r_ in mu and r_ in ml]
                cont = {str(r_): contact(mu, ml, r_, rel) for r_ in lods}
                c1 = [np.inf if c is None else c for c in cont["1.0"]]                 # upper foot over the lower copy, LOD 1
                gt = hang(up, mu)                                                      # upper foot over the terrain
                sup = [min(a_, b_) for a_, b_ in zip(c1, gt)]
                on_copy = [c for c in c1 if c <= LEG_GAP]
                zf = zfight(mu, ml, rel)
                pc = np.zeros(3); pc[ml["ax"]] = (ml["lo"] + ml["hi"]) / 2; pc[ml["lat"]] = ml["c_lat"]; pc[1] = ml["road"][..., 1].max()
                road = world(lo["matrix"], [pc])[0][1]
                # exposed lower roadway: the lower model's real roadway faces, full width, 0.05 m grid, above terrain + 0.05
                xs = np.arange(ml["lo"], ml["hi"], 0.05); zs = np.arange(ml["c_lat"] - ml["half_w"], ml["c_lat"] + ml["half_w"] + 1e-9, 0.05)
                X, Z = np.meshgrid(xs, zs, indexing="ij")
                if ml["ax"] == 2:
                    X, Z = Z, X
                Y = ray_top(ml["road"], X, Z); k = np.isfinite(Y)
                Pw = world(lo["matrix"], np.stack([X[k], Y[k], Z[k]], 1)); ex = Pw[:, 1] > terr(run["H"], Pw[:, 0], Pw[:, 2]) + 0.05
                along = np.stack([X[k], Z[k]], 1)[:, 0 if ml["ax"] == 0 else 1]
                ramp = Y[k] < Y[k].max() - 1e-4
                d = dict(span=up["span"], lower_model=ml["name"], stack_offset_m=round(dyv, 4), axes_equal=axes < 1e-12,
                         lower_hanging=int(sum(x > LEG_GAP for x in gl)), lower_max_gap_m=round(max(gl), 3),
                         upper_feet=len(c1), upper_on_lower_copy=len(on_copy), upper_on_ground=int(sum(a_ > LEG_GAP and b_ <= LEG_GAP for a_, b_ in zip(c1, gt))),
                         upper_hanging=int(sum(x > LEG_GAP for x in sup)), upper_max_gap_m=round(max(sup), 4),
                         lod1_contact_gap_on_copy_m=[round(min(on_copy), 4), round(max(on_copy), 4)] if on_copy else None,
                         zfighting_pairs=zf,
                         lod_bbox_gap_m={str(r_): round(float(mu[r_]["V"][:, 1].min() - rel(ml[r_]["V"])[:, 1].max()), 4) for r_ in lods},
                         per_lod_contact_gap_m={k_: [round(min(x for x, c in zip(v, c1) if x is not None and c <= LEG_GAP), 4), round(max(x for x, c in zip(v, c1) if x is not None and c <= LEG_GAP), 4)]
                                                for k_, v in cont.items() if any(x is not None and c <= LEG_GAP for x, c in zip(v, c1))},
                         lower_roadway_y=round(float(road), 3), lower_roadway_above_water_m=round(float(road - L), 3),
                         lower_roadway_exposed_area_m2=round(float(ex.sum() * 0.0025), 1),
                         lower_roadway_exposed_length_m=round(float(np.ptp(along[ex])) if ex.any() else 0.0, 2),
                         lower_ramps_exposed_area_m2=round(float((ex & ramp).sum() * 0.0025), 2),
                         lower_ramps_max_above_terrain_m=round(float((Pw[ramp, 1] - terr(run["H"], Pw[ramp, 0], Pw[ramp, 2])).max()), 3))
                per.append(d)
                good &= d["lower_hanging"] == 0 and d["upper_hanging"] == 0 and zf == 0 and d["axes_equal"]
            if not per:
                errors.append("no lower record")
            row["spans"] = per
        else:
            if rr["lower"]:
                errors.append("lower record at a site without stack")
            gu = [x for r in rr["upper"] for x in hang(r, mu)]
            row.update(upper_hanging=int(sum(x > LEG_GAP for x in gu)), upper_max_gap_m=round(max(gu), 3),
                       hanging_gaps_m=sorted(round(x, 3) for x in gu if x > LEG_GAP))
            good = row["upper_hanging"] == 0
        row["errors"] = errors; row["pass_"] = bool(good and not errors); ok &= row["pass_"]; res[sid] = row
    return ok, dict(rule="stacked sites: each lower record is the site's model, span by span; no lower leg (the lower record's "
                         "own model and matrix) more than 0.05 m above the terrain; every upper foot within 0.05 m of the lower "
                         "record's model (visual LOD 1, mapped through both real matrices) or of the terrain; no coplanar "
                         "overlapping faces between the two models; same axes; swapped sites: no leg more than 0.05 m above the "
                         "terrain. Contact gaps of the feet resting on the copy reported per LOD (1-4 visual, 1e13 geometry)", sites=res)


def footprint_support(run):
    sup = np.zeros((GN, GN), bool)
    for r in run["rec"]:
        if r.get("role"):
            continue
        m = model(mname(r)); V = m[1.0]["V"]; mn, mx = V.min(0), V.max(0)
        P = world(r["matrix"], [[mn[0], 0, mn[2]], [mx[0], 0, mn[2]], [mx[0], 0, mx[2]], [mn[0], 0, mx[2]]])
        c0, c1 = int(P[:, 0].min() // 6) - 1, int(P[:, 0].max() // 6) + 2; r0, r1 = int((ZT - P[:, 2].max()) // 6) - 1, int((ZT - P[:, 2].min()) // 6) + 2
        for rr in range(r0, r1):
            for cc in range(c0, c1):
                for tri in (((rr, cc), (rr, cc + 1), (rr + 1, cc + 1)), ((rr, cc), (rr + 1, cc + 1), (rr + 1, cc))):
                    Tp = np.array([[6.0 * c_, ZT - 6.0 * r_] for r_, c_ in tri])
                    if tri_rect(Tp, P[:, [0, 2]]):
                        for v in tri:
                            sup[v] = True
    return sup


def tri_rect(T, R):
    """Plan triangle T (3, 2) intersects convex polygon R (4, 2): separating axis test."""
    for poly in (T, R):
        for i in range(len(poly)):
            e = poly[(i + 1) % len(poly)] - poly[i]; n = np.array([-e[1], e[0]])
            a, b = T @ n, R @ n
            if a.max() < b.min() - 1e-9 or b.max() < a.min() - 1e-9:
                return False
    return True


def g5(run, v4, H0, sites):
    """Strict contract: a frozen vertex may differ from the input only inside the support of a deck/ramp footprint
    (triangles under an upper record's visual-LOD plan rectangle). No corridor exception: frozen vertices lowered by the
    v4 channel cut beyond the footprint are listed and FAIL the gate, with their origin (inherited from v4 or new)."""
    frz = run["npz"]["reserve"] | run["npz"]["platform"] | run["npz"]["narva"]
    sup = footprint_support(run)
    ch = frz & (run["H"] != H0)
    bad_in = ch & ~sup
    ch4 = frz & (run["H"] != v4["H"])
    bad_v4 = ch4 & ~sup
    ok = not bad_in.any() and not bad_v4.any()
    lv = {s["site"]: s["level"] for s in run["rep"]["sites"]}
    pos = [(s["id"], s["x"], s["z"]) for s in sites]
    rows = []
    for r, c in np.argwhere(bad_in | bad_v4):
        x, z = 6.0 * c, ZT - 6.0 * r
        sid = min(pos, key=lambda p: math.hypot(p[1] - x, p[2] - z))[0]; L = lv.get(sid)
        h0, h4, h5 = float(H0[r, c]), float(v4["H"][r, c]), float(run["H"][r, c])
        rows.append(dict(vertex=[int(r), int(c)], site=sid, input=round(h0, 4), v4=round(h4, 4), run=round(h5, 4),
                         inherited_from_v4=bool(h5 == h4 and h4 != h0), wet_in_run=bool(L is not None and h5 < L),
                         input_above_level_m=round(h0 - L, 3) if L is not None else None))
    return ok, dict(rule="frozen vertices (reserve | platform | narva) changed vs the input only inside the support of a deck/ramp "
                         "footprint (triangles under an upper record's visual-LOD plan rectangle); frozen vertices that differ from "
                         "v4 likewise. No corridor exception", frozen_changed_vs_input=int(ch.sum()), outside=int(bad_in.sum()),
                    outside_inherited_from_v4=int(sum(x["inherited_from_v4"] for x in rows)),
                    outside_new_in_run=int(sum(not x["inherited_from_v4"] for x in rows)),
                    outside_wet_in_run=int(sum(x["wet_in_run"] for x in rows)),
                    frozen_changed_vs_v4=int(ch4.sum()), outside_vs_v4=int(bad_v4.sum()),
                    max_lowering_outside_m=round(max((x["input"] - x["run"] for x in rows), default=0.0), 4),
                    outside_list=rows[:500])


def slopes(A):
    nw, ne, sw, se = A[:-1, :-1], A[:-1, 1:], A[1:, :-1], A[1:, 1:]
    return np.stack([np.degrees(np.arctan(np.hypot((ne - nw) / 6, (ne - se) / 6))), np.degrees(np.arctan(np.hypot((se - sw) / 6, (nw - sw) / 6)))])


def stuck(H, H0):
    s0, s1 = slopes(H0), slopes(H); ch = H != H0
    chg = np.stack([ch[:-1, :-1] | ch[:-1, 1:] | ch[1:, 1:], ch[:-1, :-1] | ch[1:, 1:] | ch[1:, :-1]])
    return chg & (s1 > np.maximum(35.0, s0) + 1e-4)


def g6(run, v4, H0, sites):
    win = np.zeros((2, GN - 1, GN - 1), bool)
    for s in sites:
        rc, cc = int((ZT - s["z"]) / 6), int(s["x"] / 6); win[:, rc - 20:rc + 20, cc - 20:cc + 20] = True
    S5, S4, S0 = slopes(run["H"]), slopes(v4["H"]), slopes(H0)
    new55 = (S5 > 55) & ~(S4 > 55)
    cnt = lambda S, a: int(((S > a) & win).sum())
    st5, st4 = stuck(run["H"], H0), stuck(v4["H"], H0)
    worse = (S5 > S4 + 1e-6) & win
    ok = not new55.any()
    return ok, dict(rule="no triangle > 55 deg that was not > 55 deg in v4 (whole map); counts in +-120 m windows",
                    new_over_55=int(new55.sum()), new_over_55_list=[list(map(int, v)) for v in np.argwhere(new55)[:10]],
                    over_35=dict(v4=cnt(S4, 35), v5=cnt(S5, 35)), over_45=dict(v4=cnt(S4, 45), v5=cnt(S5, 45)), over_55=dict(v4=cnt(S4, 55), v5=cnt(S5, 55)),
                    max_deg=dict(v4=round(float(S4[win].max()), 2), v5=round(float(S5[win].max()), 2)),
                    triangles_steeper_than_v4=int(worse.sum()),
                    stuck_triangles=dict(v4=int(st4.sum()), v5=int(st5.sum()), v4_cells=int(st4.any(0).sum()), v5_cells=int(st5.any(0).sum())))


def deck_clear(run):
    """Per site: min over every deck face (roadway LOD at or above its lower end, whole length) of the upper records of
    deck - terrain, exact."""
    res = {}
    for sid, rr in site_records(run).items():
        m = model(mname(rr["upper"][0])); mn = np.inf
        for rec in rr["upper"]:
            for T in m["deck"]:
                C = cands(world(rec["matrix"], T)); mn = min(mn, float((C[:, 1] - terr(run["H"], C[:, 0], C[:, 2])).min()))
        res[sid] = round(mn, 4)
    return res


def leg_gaps(run, sites):
    """Per site: max leg gap over the terrain of the lower records (stack) and of the upper records of a model swap; at a
    stacked site also every upper foot over its support, min(gap over the lower record's model, LOD 1 through both real
    matrices; gap over the terrain) as 'upper_stack' (review 2 of 15-10: two 015-19 upper feet standing on the ground hung
    0.17 m and G7 passed; G4 alone caught them)."""
    s_by = {s["id"]: s for s in sites}; out = {}
    for sid, rr in site_records(run).items():
        s = s_by.get(sid, {}); d = {}
        for role, recs in (("lower", rr["lower"]), ("upper", rr["upper"] if s.get("model") in VARIANT_MODELS else [])):
            g = []
            for rec in recs:
                m = model(mname(rec))
                for F in legs(m):
                    W = world(rec["matrix"], F); g.append(float(W[:, 1].min() - terr(run["H"], W[:, 0], W[:, 2]).max()))
            if g:
                d[role] = dict(n=len(g), max_gap_m=round(max(g), 4), hanging=int(sum(x > LEG_GAP for x in g)))
        if s.get("stack"):
            los = {r["span"]: r for r in rr["lower"]}; g = []
            for up in sorted(rr["upper"], key=lambda r: r["span"]):
                mu = model(mname(up)); lo = los.get(up["span"]); feet = legs(mu)
                c1 = contact(mu, model(mname(lo)), 1.0, rel_frame(up, lo)) if lo is not None else [None] * len(feet)
                for F, c in zip(feet, c1):
                    W = world(up["matrix"], F); gt = float(W[:, 1].min() - terr(run["H"], W[:, 0], W[:, 2]).max())
                    g.append(min(np.inf if c is None else c, gt))
            d["upper_stack"] = dict(n=len(g), max_gap_m=round(max(g), 4) if g else None, hanging=int(sum(x > LEG_GAP for x in g)) if g else 1)
        if d:
            out[sid] = d
    return out


def ramp_caps(run, v4):
    """Per wood end: max of final terrain - max(v4 terrain, ramp underside - 0.05) on the underside points (the fill
    never pokes through the ramp where the ground was not already higher)."""
    out = {}
    for sid, rr in site_records(run).items():
        m = model(mname(rr["upper"][0]))
        if m["name"] == "bridge_metal_25":
            continue
        vals = []
        for rec, ei, e, inw in outer_ends(m, rr["upper"]):
            P, _ = ramp_points(m, ei); W = world(rec["matrix"], P)
            t5, t4 = terr(run["H"], W[:, 0], W[:, 2]), terr(v4["H"], W[:, 0], W[:, 2])
            vals.append(round(float((t5 - np.maximum(t4, W[:, 1] - 0.05)).max()), 4))
        out[sid] = vals
    return out


def g7(run, v4, sites, fixture):
    """Every constraint family recomputed by this script on the final terrain (all sites, after the guard), the tool's
    final report checked for completeness and agreement. Wood ramp air itself is G2's verdict; here only the tool's
    reported air is checked against this script's. Every record matrix must be 12 finite numbers (checked first: nothing
    is measured on an invalid pose)."""
    bad = matrix_errors(run)
    if bad:
        return False, dict(rule="every record matrix 12 finite numbers (checked before any measurement)", invalid_matrices=bad)
    ok1, d1 = g1(run); ok2, d2 = g2(run); dk = deck_clear(run); lg = leg_gaps(run, sites); cp = ramp_caps(run, v4)
    tool = {s["site"]: s for s in run["rep"].get("sites", [])}; missing, agree = [], []
    num = lambda v: isinstance(v, (int, float)) and math.isfinite(v)
    for s in sites:
        sid = s["id"]; t = tool.get(sid)
        if t is None:
            missing.append(f"{sid}: no report"); continue
        metal = s["model"] == "bridge_metal_25"
        fe = {e.get("end"): e for e in t.get("fit_ends") or []}
        for ei in (0, 1):
            e = fe.get(ei); key = "max_exposure_m" if metal else "max_air_m"
            if e is None or e.get("kind") != ("block" if metal else "ramp") or not num(e.get(key)):
                missing.append(f"{sid}: end {ei} {key}"); continue
            g = [x for x in d2["sites"][sid] if x["end"] == ei][0]
            if metal:
                agree.append(dict(site=sid, what=f"end {ei} face exposure", tool=e[key], gate=g["max_exposure_m"], pass_=abs(e[key] - g["max_exposure_m"]) <= AGREE_TOL))
            else:                                                          # the gate runs to the first leg, beyond the tool's first bent
                agree.append(dict(site=sid, what=f"end {ei} ramp air (tool <= gate)", tool=e[key], gate=g["max_air_m"], pass_=e[key] <= g["max_air_m"] + AGREE_TOL))
        for key, gate_v in (("deck_strip_min_clear_m", min(d1["min_clearance_m"][sid])), ("deck_min_clear_m", dk[sid])):
            if not num(t.get(key)):
                missing.append(f"{sid}: {key}"); continue
            agree.append(dict(site=sid, what=key, tool=t[key], gate=gate_v, pass_=abs(t[key] - gate_v) <= AGREE_TOL))
        need = (["lower"] if s.get("stack") else []) + (["upper"] if s["model"] in VARIANT_MODELS else [])
        for role in need:
            tl = (t.get("legs") or {}).get(role); gl = lg.get(sid, {}).get(role)
            if not tl or not num(tl.get("max_gap_m")) or gl is None or tl.get("n") != gl["n"]:
                missing.append(f"{sid}: legs {role}"); continue
            agree.append(dict(site=sid, what=f"legs {role} max gap", tool=tl["max_gap_m"], gate=gl["max_gap_m"], pass_=abs(tl["max_gap_m"] - gl["max_gap_m"]) <= AGREE_TOL))
        if not isinstance(t.get("opening_m"), dict) or not num(t["opening_m"].get("v5")):
            missing.append(f"{sid}: opening_m")
    extra = sorted(set(tool) - {s["id"] for s in sites})
    deck_ok = all(v >= 0.01 for v in dk.values())
    metal_ok = all(e["pass_"] for ends in d2["sites"].values() for e in ends if e["kind"] == "block")
    legs_ok = all(v["hanging"] == 0 for d in lg.values() for v in d.values())
    caps_ok = all(v <= 0.002 for vs in cp.values() for v in vs)
    agree_ok = all(a["pass_"] for a in agree)
    fx = {}
    if fixture:
        f = load_run(fixture); okf1, df1 = g1(f); okf2, df2 = g2(f); dkf = deck_clear(f)
        fx = dict(g1=okf1, g2_metal=all(e["pass_"] for ends in df2["sites"].values() for e in ends if e["kind"] == "block"),
                  deck=all(v >= 0.01 for v in dkf.values()), exposure=df2["sites"], strips=df1["min_clearance_m"], deck_min_clear_m=dkf)
    ok = (not missing and not extra and agree_ok and ok1 and deck_ok and metal_ok and legs_ok and caps_ok
          and (not fixture or (fx["g1"] and fx["g2_metal"] and fx["deck"])))
    return ok, dict(rule="recomputed by this script on the final terrain (all sites, after the guard): deck end strips and every deck "
                         "face (interior included) terrain <= deck - 0.01; metal abutment faces (inner faces included) <= 0.02; "
                         "lower stack legs and swapped-model legs <= 0.05 m over the terrain; every upper foot of a stacked "
                         "site <= 0.05 m over the lower copy (LOD 1) or the terrain; the ramp fill never above "
                         "max(v4, underside - 0.05) + 0.002; the tool's final report complete for every site and end and in "
                         f"agreement within {AGREE_TOL} m (ramp air: tool <= gate, the gate's range is longer); overlap fixture "
                         "(two 015-13 sites 18 m / 6 m apart) holds strips, deck and metal faces. Wood ramp air is G2's verdict",
                    g1=ok1, deck_faces=deck_ok, deck_min_clear_m=dk, metal_faces=metal_ok, legs=lg, legs_ok=legs_ok,
                    ramp_fill_over_cap_m=cp, caps_ok=caps_ok, missing=missing, extra_report_sites=extra, agreement=agree,
                    agreement_ok=agree_ok, max_tool_vs_gate_diff_m=(lambda v: None if v is None else round(v, 5))(max((abs(a["tool"] - a["gate"]) for a in agree if "<=" not in a["what"]), default=None)),
                    fixture=fx)


def g8(run, v4, sites):
    sh = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    env_same = sh(run["dir"] / "envelope-br.npy") == sh(v4["dir"] / "envelope-br.npy")
    env_diff = int((~((run["env"] == v4["env"]) | (np.isnan(run["env"]) & np.isnan(v4["env"])))).sum())
    arr = {}
    for k in set(run["npz"].files) | set(v4["npz"].files):
        if k in ("heights", "v31_bridge_cut", "v31_bridge_fill"):
            continue
        arr[k] = k in run["npz"].files and k in v4["npz"].files and np.array_equal(run["npz"][k], v4["npz"][k], equal_nan=run["npz"][k].dtype.kind == "f")
    s_by = {s["id"]: s for s in sites}
    bad = matrix_errors(run)
    up5 = {(r["site"], r["span"]): r for r in run["rec"] if not r.get("role")}
    up4 = {(r["site"], r["span"]): r for r in v4["rec"]}
    rec_rows, ok_rec = {}, set(up5) == set(up4) and len(up5) == sum(1 for r in run["rec"] if not r.get("role"))
    for key, r4 in up4.items():
        r5 = up5.get(key)
        if r5 is None:
            continue
        M4, M5 = np.array(r4["matrix"]), np.array(r5["matrix"])
        fields = set(r5) == set(r4) and r5["model"] == model_path(s_by[key[0]]["model"])
        if r5["model"] == r4["model"]:
            same = bool(np.array_equal(M4, M5)) and fields; rec_rows[f"{key[0]}/{key[1]}"] = dict(identical=same); ok_rec &= same
        else:
            m4, m5 = model(mname(r4)), model(mname(r5))
            Rw4, Rw5 = world(M4, m4["road"].reshape(-1, 3)), world(M5, m5["road"].reshape(-1, 3))
            dev = float(np.abs(Rw4 - Rw5).max()); axes = float(np.abs(M4[:9] - M5[:9]).max())
            intended = s_by[key[0]]["model"] == mname(r5)
            rec_rows[f"{key[0]}/{key[1]}"] = dict(model_swap=f"{mname(r4)} -> {mname(r5)}", intended=intended, axes_identical=axes == 0.0,
                                                  world_roadway_max_dev_m=round(dev, 4), fields_ok=fields)
            ok_rec &= intended and axes == 0.0 and dev <= 0.005 and fields
    seen = []
    for r in (r for r in run["rec"] if r.get("role")):
        key = (r["site"], r["span"]); u = up5.get(key); s = s_by.get(r["site"]); errs = []
        if r.get("role") != "stack-lower":
            errs.append(f"unknown role {r.get('role')}")
        if set(r) != {"site", "span", "role", "model", "matrix"}:
            errs.append("fields differ from site/span/role/model/matrix")
        if key in seen:
            errs.append("duplicate lower record")
        seen.append(key)
        if u is None:
            errs.append("no upper record with this site and span")
        else:
            if r["model"] != u["model"]:
                errs.append(f"model {mname(r)} differs from the upper record's {mname(u)}")
            U, l = np.array(u["matrix"]), np.array(r["matrix"])
            if not np.array_equal(U[:9], l[:9]):
                errs.append("axes differ from the upper record's")
            if np.abs(U[9:12] - STACK_DY * U[3:6] - l[9:12]).max() >= 1e-9:
                errs.append("position is not the upper record's - 5.04 Y")
        if s is None or not s.get("stack"):
            errs.append("the site does not ask for a stack")
        elif r["model"] != model_path(s["model"]):
            errs.append("model is not the site's model")
        rec_rows[f"{r['site']}/{r['span']}/{r.get('role')}"] = dict(ok=not errs, errors=errs); ok_rec &= not errs
    expected = sorted(k for k in up5 if s_by.get(k[0], {}).get("stack"))
    ok_rec &= sorted(seen) == expected
    ok = env_same and all(arr.values()) and ok_rec and not bad
    return ok, dict(rule="every record matrix 12 finite numbers; envelope byte-identical to v4; npz arrays other than heights/v31_bridge_cut/v31_bridge_fill identical; "
                         "upper records identical to v4 (fields, model = the site's, matrix) except intended model swaps (same "
                         "axes, world roadway within 5 mm); one lower record per span of each stacked site and none elsewhere, "
                         "each exactly {site, span, role stack-lower, the upper record's model = the site's, upper axes, position "
                         "- 5.04 Y}", envelope_identical=env_same,
                    envelope_cells_different=env_diff, arrays_identical=arr, new_arrays=sorted(set(run["npz"].files) - set(v4["npz"].files)),
                    expected_lower=[list(k) for k in expected], invalid_matrices=bad, records=rec_rows)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("gate"); ap.add_argument("--run", required=True); ap.add_argument("--v4")
    ap.add_argument("--input"); ap.add_argument("--sites"); ap.add_argument("--fixture", nargs="*"); ap.add_argument("--out")
    a = ap.parse_args()
    run = load_run(a.run); v4 = load_run(a.v4) if a.v4 else None
    sites = json.load(open(a.sites)) if a.sites else None
    H0 = np.load(a.input)["heights"].astype(np.float64) if a.input else None
    g = a.gate.upper()
    ok, det = {"G1": lambda: g1(run), "G2": lambda: g2(run), "G3": lambda: g3(run, v4, sites, a.fixture),
               "G4": lambda: g4(run, sites), "G5": lambda: g5(run, v4, H0, sites), "G6": lambda: g6(run, v4, H0, sites),
               "G7": lambda: g7(run, v4, sites, a.fixture[0] if a.fixture else None), "G8": lambda: g8(run, v4, sites)}[g]()
    det = dict(gate=g, verdict="PASS" if ok else "FAIL", run=str(a.run), **det)
    if a.out:
        Path(a.out).write_text(json.dumps(det, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), newline="\n")
    print(f"{g} {'PASS' if ok else 'FAIL'}")
    print(json.dumps({k: v for k, v in det.items() if k not in ("gate", "verdict", "run", "rule")}, default=lambda o: o.item() if hasattr(o, "item") else str(o))[:3000])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
