"""BALTIC-015 (Guillermo, 2026-10-11: vanilla bridges by width): place a vanilla bridge where a road crosses a stream on a
dry embankment, open the channel under its span and seal that channel into the v31 pond envelope.

Per site (JSON list: id, x, z, road bearing deg, model, level, water bearing deg, width m, optional spans = 1 or 2,
optional stack = true):
  model     DZ\\structures\\roads\\bridges\\<model>.p3d, read from its ODOL: length axis (X for wood, Z for metal), roadway
            end heights at +-half length, centre of the roadway in model coordinates. Only models with a verified seat
            (SEATS) are accepted; anything else is refused, as is a model without an exact roadway (3e15) or visual
            (1.0) LOD or whose seat does not pass the checks in seat_*().
  variant   a model in VARIANTS (bridge_wood_50_1: the tall vanilla wood_50, roadway 1.301 m higher in the model) is posed
            and cut exactly as its base model, then moved down its own Y axis by the measured roadway offset, so the
            world roadway stays where the base model's is (015-42: wood_50 legs hung up to 3.3 m over the cut gully).
  pose      length axis along the road bearing, pitched so both roadway ends sit on the road terrain (world = position +
            R . ODOL vertex, the convention of the WRP records; matrix = local X, Y, Z axes as columns, then position).
            Each end height is the road terrain on the axis, or, where the terrain under the deck end strip (full deck
            width at the end, END_IN m inward, less the deck's rise along its pitch) stands higher, that terrain +
            END_CLEAR: a deck wider than the road
            (bridge_metal_25: 14.2 m) sat with one corner a few cm inside a cross-sloped road (Guillermo, 15-10, 015-8).
            With spans = 2 (the 015 plan's 'bridge_metal_25 x2') two copies stand end to end on one straight pitched line
            between the two outer roadway ends; each span's centre height is interpolated on that line.
  stack     stack = true adds a second copy of the same model, same axes, STACK_DY m lower along its Y axis (record role
            'stack-lower'): the upper legs' feet (y -2.603..-2.524) stand on the lower copy's kerbs (2.56/2.60), the
            posts line up, and the lower legs reach the ground where a single trestle hung up to 4.8 m over the cut
            gully (Guillermo, 15-10, 015-16: 'apilar un puente debajo').
  channel   q = distance to the water axis through the site, t = distance along it: H = min(H, bed + BANK (|q| - W/2)) for
            |t| <= CUT_T, bed = max(1.0, level - 0.5); this may lower reserve/platform vertices, but only under the deck
            (|s| <= flat half-span along the road), which is the explicit exception of the plan.
  seals     cells within W/2 + 6 m of the water axis and |t| <= CUT_T take the stream level in the envelope.
  corridor  the road reserve band is often far wider than the deck (015-16: 24 m against 8 m), so the channel is opened
            through the whole band under the deck's length (frozen vertices with |s| <= flat half-span, any lateral offset;
            limiting it to the deck width left the shoulders as dams). The cut reaches, on each side separately,
            max(25 m, the far end of the frozen run met along the water axis + 6 m, the first point where the terrain within
            3 m of the axis is below the stream level + 4 m), capped at 60 m: a fixed 25 m stopped short of the band on
            oblique or wide crossings (015-4) and of the water beyond the EV102 road cones (015-13/16/40: water resumed at
            ~30 m), leaving dams and, against them, sealed pond edges.
  link      the inventory's water bearing is a chord: where no water lies on the straight axis on one side within 60 m,
            the channel is also carved (same width and banks, frozen vertices untouched) and sealed along a straight
            segment from the axis just beyond the frozen run to the nearest wet vertex of an envelope cell at the stream
            level on that side (015-16 north, 015-40 south: the natural channel ran 6-12 m beside the axis).
  slopes    a changed triangle steeper than max(35 deg, before) has its highest vertex lowered in 0.1 m steps when that
            vertex is neither channel floor (|q| <= W/2 from the axis or a link) nor frozen and lies within 2 vertices of
            the edit (80 passes): the wall is laid back; the channel floor and the frozen embankment never move. Steep faces where the frozen embankment meets the
            channel under the deck (the abutments) stay: the bridge stands over them, as in Chernarus.
            This pass, run after all sites, gives the v4 terrain (kept internally as the reference of the water checks).
  sea mode  when the water on the axis within CUT_T is engine sea (terrain < 0.75 m outside every envelope cell; EV96 turned
            many low reaches into sea), the bed is SEA_BED below the sea and no seal is written: the engine sea fills the
            channel, so no pond piece ever covers sea water (the two-colour rule of 11-10).
  end fit   (v5) after all cuts and the v4 slope pass, one joint raise-only solve (linear programme over vertex raises,
            every site at once, so overlapping sites cannot undo each other) on the planar NW-SE triangles, with the real
            ODOL faces transformed by each record and cut by the triangle edges (each piece lies in one triangle, where
            terrain and face are both linear, so the piece vertices give the exact extremes):
              abutment  bridge_metal_25: no face of the visual-LOD pier block at an outer end may stand more than
                        FACE_TOL above the terrain (015-13: the oblique cut left a 6 m triangle that bared the block's inner
                        corner by 1.17 m; the prototype's 0.5 m samples missed a 0.049 m residual).
              ramp      wood bridges: under the visual-LOD underside of each outer ramp, from the tip to the first pile bent
                        (4.0-4.5 m), the terrain rises toward underside - RAMP_AIR, never above underside - RAMP_CAP where
                        it was not already higher, with soft 1:WING wings beside it (the ramp rises 0.30 m/m from the
                        road: ~1 m of air at the first bent on all 14 ramps before any cut; Chernarus median 0).
                        Within reach only where the cut lowered the ground: on the 6 m grid a triangle that crosses the
                        tip carries the road vertex beyond it, and the deck rule below keeps it from tilting up 0.30 m/m.
              legs      every foot of a lower stack copy and of a variant model must touch the terrain (LEG_TOL).
              deck      a raise never brings the terrain above any deck (roadway LOD) face - DECK_CLEAR.
            A raise is never more than a row needs (deficit / weight, weights >= 0.05) nor OVER_MAX above that row's bound.
            Never raised: vertices under the stream level, the sea or an envelope cell (the wet set and its connectivity
            stay), frozen vertices outside the support of a bridge footprint (the triangles under the visual LOD's plan
            rectangle) and the map border. Where a raise narrows the opening (narrowest wet width across the water axis
            under the deck, exact on the planar triangles, sections every 0.1 m) below the v4 terrain's, free bank vertices
            (dry, cut-allowed by the v4 rules, not held by a fit row) are lowered toward the bed, best gain first, until
            it is back; if that fails, the raised shore vertices of that site are kept and the solve repeats. No width
            threshold: the prototype's W < 6 m neighbour rule dropped a 015-25 fixture from 4.1 to 1.3 m at W = 6.0.
            The slope pass then runs again; it never lowers a vertex if that would break a satisfied fit row or deepen a
            broken one. Every row is measured again on the final terrain and reported per end (stuck triangles counted
            by triangle, not by cell).
Outputs: terrain (v31_bridge_cut = every vertex this pass changed, lowered or raised, OR earlier cuts; v31_bridge_fill =
vertices left above their input height, OR earlier fills), envelope, records (upper records exactly as v4 except a
variant's model and position; stack copies after their upper record), report (schema bridges-v31.v5).
Usage: bridges_v31.py <terrain.npz> <envelope.npy> <sites.json> <out_terrain.npz> <out_envelope.npy> <records.json> <report.json>
"""
import json, math, sys
import numpy as np
from scipy.ndimage import binary_dilation
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts")
from odol_reader import ODOL

BANK, CUT_T, BED_MIN, ZTOP = 0.5, 25.0, 1.0, 12282
END_IN, END_CLEAR = 2.0, 0.02
SEA, SEA_BED = 0.75, 0.0
STACK_DY = 5.04                                     # lower copy offset along model Y; contact window 4.993..5.084 (LOD 1)
FACE_TOL, RAMP_CAP, RAMP_AIR, LEG_TOL, DECK_CLEAR, WING = 0.01, 0.05, 0.09, 0.04, 0.015, 1.5
FIT_ROUNDS = 8
SLOPE_MAX = 55.0                                    # no fit raise or widening cut leaves a triangle steeper than this
OVER_MAX = 1.0                                      # a raised vertex stands at most this above the bound it serves
DZ = "P:/DZ/structures/roads/bridges"
SEATS = {"bridge_metal_25": "block", "bridge_wood_25": "ramp", "bridge_wood_50": "ramp", "bridge_wood_50_1": "ramp"}
VARIANTS = {"bridge_wood_50_1": "bridge_wood_50"}
GN = 2048
_MODELS = {}


def refuse(msg):
    raise SystemExit(f"bridges_v31: refused: {msg}")


def lod_exact(od, res, name):
    c = [l for l in od.lods if abs(l.resolution - res) <= 1e-6 * max(1.0, abs(res))]
    if len(c) != 1:
        refuse(f"{name}: no single LOD with resolution {res:g}")
    return c[0]


def welded(l):
    """Vertices, per-vertex welded component label, triangles (n, 3, 3) and their component labels."""
    V = np.array([(p.x, p.y, p.z) for p in l.vertices], float)
    U, inv = np.unique(V.round(4), axis=0, return_inverse=True); inv = inv.ravel()
    a, b, tris, tv = [], [], [], []
    for f in l.faces:
        ids = list(f.vertex_indices)
        for j in ids[1:]:
            a.append(inv[ids[0]]); b.append(inv[j])
        for i in range(1, len(ids) - 1):
            tris.append(V[[ids[0], ids[i], ids[i + 1]]]); tv.append(ids[0])
    _, lab = connected_components(coo_matrix((np.ones(len(a)), (a, b)), shape=(len(U), len(U))), directed=False)
    vl = lab[inv]
    return V, vl, np.array(tris), vl[np.array(tv)]


def top_at(tris, x, z):
    """Highest triangle hit of vertical rays; nan where none."""
    best = np.full(np.shape(x), np.nan)
    for A, B, C in tris:
        m = np.array([[B[0] - A[0], C[0] - A[0]], [B[2] - A[2], C[2] - A[2]]])
        if abs(np.linalg.det(m)) < 1e-12:
            continue
        iv = np.linalg.inv(m); u = iv[0, 0] * (x - A[0]) + iv[0, 1] * (z - A[2]); w = iv[1, 0] * (x - A[0]) + iv[1, 1] * (z - A[2])
        ins = (u >= -1e-9) & (w >= -1e-9) & (u + w <= 1 + 1e-9); y = A[1] + u * (B[1] - A[1]) + w * (C[1] - A[1])
        best = np.where(ins & ~(best >= y), y, best)
    return best


def seat_block(tris, tl, V, vl, ax, lat, e, inw, y_end, c_lat, half_w, name):
    a = (V[:, ax] - e) * inw
    deep = [k for k in np.unique(vl) if V[vl == k, 1].min() < y_end - 5 and a[vl == k].min() <= 0.1 and a[vl == k].max() < 8]
    if len(deep) != 1:
        refuse(f"{name}: {len(deep)} pier blocks flush with the end at {e:g}")
    k = deep[0]; p = V[vl == k]; pa = a[vl == k]
    top, a_in, hw = float(p[:, 1].max()), float(pa.max()), float(np.abs(p[:, lat] - c_lat).max())
    if not (y_end - 2.5 <= top <= y_end - 1.0 and 2.5 <= a_in <= 5.0 and hw <= half_w + 0.1 and p[:, 1].min() < top - 5):
        refuse(f"{name}: unverified pier block at {e:g} (top {top:.3f}, roadway {y_end:.3f}, length {a_in:.2f}, half width {hw:.2f})")
    return dict(kind="block", faces=tris[tl == k], top=top, a_in=a_in, hw=hw)


def seat_ramp(tris, tl, V, vl, ax, lat, e, inw, y_end, c_lat, road_tris, name):
    a = (V[:, ax] - e) * inw
    slabs = [k for k in np.unique(vl) if a[vl == k].min() <= 0.5 and np.ptp(a[vl == k]) > 3 and V[vl == k, 1].min() > y_end - 0.6]
    if not slabs:
        refuse(f"{name}: no ramp slab at {e:g}")
    k = max(slabs, key=lambda q: np.ptp(a[vl == q])); st = tris[tl == k]
    nrm = np.cross(st[:, 1] - st[:, 0], st[:, 2] - st[:, 0]); flat = np.abs(nrm[:, 1]) > 0.7 * np.linalg.norm(nrm, axis=1)
    cen = st.mean(1); above = top_at(st, cen[:, 0], cen[:, 2])
    bottom = st[flat & (above > cen[:, 1] + 0.05)]                                    # a slab face with slab above it
    if len(bottom) < 2:
        refuse(f"{name}: no ramp underside at {e:g}")
    ba = (bottom[..., ax] - e) * inw
    s1, y1 = np.polyfit(ba.ravel(), bottom[..., 1].ravel(), 1)
    others = (vl != k) & (a > 0.5) & (V[:, 1] < y1 + s1 * a - 0.05)                     # first pile bent below the slab
    a_seat = float(a[others].min()) if others.any() else np.inf
    faces = [P for P in (clip_le(T, (T[:, ax] - e) * inw, a_seat) for T in bottom) if len(P) >= 3]
    fv = np.concatenate(faces) if faces else np.zeros((0, 3))
    res = float(np.abs(fv[:, 1] - (y1 + s1 * (fv[:, ax] - e) * inw)).max()) if len(fv) else np.inf
    ra = np.linspace(0.5, min(a_seat, 4.0), 8)
    rx = np.zeros((len(ra), 3)); rx[:, ax] = e + inw * ra; rx[:, lat] = c_lat
    gap = top_at(road_tris, rx[:, 0], rx[:, 2]) - (y1 + s1 * ra)
    if not (3.5 <= a_seat <= 5.0 and res <= 0.02 and 0.27 <= s1 <= 0.34 and np.all((gap >= 0.2) & (gap <= 0.45))):
        refuse(f"{name}: unverified ramp at {e:g} (first bent {a_seat:.2f} m, slope {s1:.4f}, fit residual {res:.3f}, roadway-underside {np.nanmin(gap):.3f}..{np.nanmax(gap):.3f})")
    lv = fv[:, lat] - c_lat
    return dict(kind="ramp", faces=faces, a_seat=a_seat, y0=float(y1), slope=float(s1), fit_residual=res,
                lat_lo=float(lv.min()), lat_hi=float(lv.max()), road_gap=[float(np.nanmin(gap)), float(np.nanmax(gap))])


def model_info(name):
    if name in _MODELS:
        return _MODELS[name]
    if name not in SEATS:
        refuse(f"{name}: no verified seat (known: {', '.join(sorted(SEATS))})")
    od = ODOL.from_file(f"{DZ}/{name}.p3d")
    road = min(od.lods, key=lambda l: abs(l.resolution - 3e15))
    lod_exact(od, 3e15, name)
    v = np.array([(p.x, p.y, p.z) for p in road.vertices])
    ax = 0 if np.ptp(v[:, 0]) >= np.ptp(v[:, 2]) else 2
    lat = 2 - ax
    lo, hi = v[:, ax].min(), v[:, ax].max()
    ends = [float(v[np.abs(v[:, ax] - e) < 0.6, 1].max()) for e in (lo, hi)]
    c_lat = (v[:, lat].max() + v[:, lat].min()) / 2
    end_w = max(float(np.abs(v[(np.abs(v[:, ax] - e) < 0.6) & (v[:, 1] >= y - 0.3), lat] - c_lat).max()) for e, y in zip((lo, hi), ends))
    m = dict(axis=ax, half=(hi - lo) / 2, centre_len=(hi + lo) / 2, centre_lat=c_lat,
             end_y=ends, deck_max=float(v[:, 1].max()), width=float(np.ptp(v[:, lat])), end_half_w=end_w)
    # v5: deck faces (roadway faces at or above the lower roadway end), visual LOD 1 seats, legs and plan bbox
    rt = np.array([v[[f.vertex_indices[0], f.vertex_indices[i], f.vertex_indices[i + 1]]] for f in road.faces for i in range(1, len(f.vertex_indices) - 1)])
    m["deck_faces"] = rt[rt[..., 1].min(1) >= min(ends) - 0.01]
    vis = lod_exact(od, 1.0, name)
    V, vl, tris, tl = welded(vis)
    kind = SEATS[name]
    m["seats"] = [seat_block(tris, tl, V, vl, ax, lat, e, inw, y, c_lat, m["width"] / 2, name) if kind == "block" else
                  seat_ramp(tris, tl, V, vl, ax, lat, e, inw, y, c_lat, rt, name)
                  for e, y, inw in ((lo, ends[0], 1.0), (hi, ends[1], -1.0))]
    ymin = V[:, 1].min(); legs = []
    for k in np.unique(vl):
        p = V[vl == k]
        if p[:, 1].min() < ymin + 0.3 and kind == "ramp":
            legs.append(np.unique(p[p[:, 1] < p[:, 1].min() + 0.05].round(4), axis=0))
    m["legs"] = legs
    m["legs_over_stack"] = [float(F[:, 1].min() - np.nanmax(top_at(tris, F[:, 0], F[:, 2]) - STACK_DY)) if np.isfinite(top_at(tris, F[:, 0], F[:, 2])).any() else np.inf
                            for F in legs]
    m["roadway_lo_hi"] = (float(lo), float(hi))
    m["bbox"] = (V.min(0), V.max(0))
    m["road_vertices"] = v
    _MODELS[name] = m
    return m


def variant_offset(base, var, name):
    """Model-Y offset of a variant's roadway over its base's; refused unless the roadways are congruent to 3 mm."""
    a, b = base["road_vertices"], var["road_vertices"]
    if len(a) != len(b):
        refuse(f"{name}: roadway vertex count differs from its base")
    sa, sb = a[np.lexsort((a[:, 2], a[:, 0]))], b[np.lexsort((b[:, 2], b[:, 0]))]
    dy = float(np.mean(sb[:, 1] - sa[:, 1]))
    if np.abs(sb[:, [0, 2]] - sa[:, [0, 2]]).max() > 0.003 or np.abs(sb[:, 1] - sa[:, 1] - dy).max() > 0.003:
        refuse(f"{name}: roadway is not its base's moved along Y")
    return dy


def tri_h(H, x, z):
    c, r = x / 6, (ZTOP - z) / 6
    c0, r0 = int(c), int(r); fc, fr = c - c0, r - r0
    nw, ne, sw, se = H[r0, c0], H[r0, c0 + 1], H[r0 + 1, c0], H[r0 + 1, c0 + 1]
    return nw + fc * (ne - nw) + fr * (se - ne) if fc >= fr else nw + fr * (sw - nw) + fc * (se - sw)


def tri_w(x, z):
    """Flat vertex indices (n, 3) and planar weights (n, 3) of world points, NW-SE split as in tri_h."""
    c, r = np.asarray(x, float) / 6, (ZTOP - np.asarray(z, float)) / 6
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int); fc, fr = c - c0, r - r0
    up = fc >= fr
    rows = np.stack([r0, np.where(up, r0, r0 + 1), r0 + 1], -1); cols = np.stack([c0, np.where(up, c0 + 1, c0), c0 + 1], -1)
    w = np.stack([np.where(up, 1 - fc, 1 - fr), np.where(up, fc - fr, fr - fc), np.where(up, fr, fc)], -1)
    return rows * GN + cols, w


def terrain_at(Hf, x, z):
    i, w = tri_w(x, z)
    return (Hf[i] * w).sum(-1)


def to_world(matrix, P):
    m = np.asarray(matrix, float)
    return np.asarray(P, float) @ m[:9].reshape(3, 3) + m[9:12]


FAMS = (lambda P: P[:, 0] / 6, lambda P: (ZTOP - P[:, 2]) / 6, lambda P: P[:, 0] / 6 - (ZTOP - P[:, 2]) / 6)


def split(P, v, k):
    lo, hi = [], []
    n = len(P)
    for i in range(n):
        A, B, va, vb = P[i], P[(i + 1) % n], v[i], v[(i + 1) % n]
        if va <= k:
            lo.append(A)
        if va >= k:
            hi.append(A)
        if (va - k) * (vb - k) < 0:
            X = A + (k - va) / (vb - va) * (B - A); lo.append(X); hi.append(X)
    return np.array(lo), np.array(hi)


def pieces(P):
    """Convex 3D polygon cut by the vertical planes of the terrain triangle edges: each piece lies in one triangle."""
    out = [np.asarray(P, float)]
    for f in FAMS:
        nxt = []
        for Q in out:
            v = f(Q)
            for k in range(int(np.floor(v.min())) + 1, int(np.ceil(v.max()))):
                lo, Q = split(Q, f(Q), k)
                if len(lo) >= 3:
                    nxt.append(lo)
                if len(Q) < 3:
                    break
            if len(Q) >= 3:
                nxt.append(Q)
        out = nxt
    return out


def clip_le(P, v, k):
    return split(P, v, k)[0]


def face_points(polys, Hf=None, cap=None):
    """Piece vertices of world polygons (each piece inside one terrain triangle). With cap (per polygon: callable giving
    the face height minus a margin at points) the pieces are also split where cap - terrain changes sign, so a constraint
    max(0, cap - terrain) is linear on every piece. Returns points (n, 3) and the sign flag of cap - terrain."""
    pts, pos = [], []
    for j, P in enumerate(polys):
        for Q in pieces(P):
            if cap is None:
                pts.append(Q); continue
            g = cap[j](Q) - terrain_at(Hf, Q[:, 0], Q[:, 2])
            if g.min() < 0 < g.max():
                a, b = split(Q, g, 0.0)
                for R_, sg in ((a, False), (b, True)):
                    if len(R_) >= 3:
                        pts.append(R_); pos.append(np.full(len(R_), sg))
            else:
                pts.append(Q); pos.append(np.full(len(Q), bool(g.max() > 0) or bool(g.min() >= 0)))
    if not pts:
        return np.zeros((0, 3)), np.zeros(0, bool)
    P = np.concatenate(pts)
    return P, (np.concatenate(pos) if cap is not None else np.ones(len(P), bool))


def tri_slopes(A_):
    nw, ne, sw, se = A_[:-1, :-1], A_[:-1, 1:], A_[1:, :-1], A_[1:, 1:]
    return (np.degrees(np.arctan(np.hypot((ne - nw) / 6.0, (ne - se) / 6.0))),
            np.degrees(np.arctan(np.hypot((se - sw) / 6.0, (nw - sw) / 6.0))))


CORNERS = (((0, 0), (0, 1), (1, 1)), ((0, 0), (1, 1), (1, 0)))


def slope_pass(H, H0, core, frz_all, rows=None, passes=80):
    """v4 wall lay-back; with rows (sparse A, lower bound b) a lowering is refused where it would break a satisfied row or
    deepen a broken one."""
    s0 = tri_slopes(H0); guard = 0
    near = binary_dilation(H != H0, np.ones((3, 3), bool), iterations=2)
    for it in range(passes):
        s1 = tri_slopes(H); ch = H != H0; low = np.zeros(H.shape, bool)
        for (a0, a1), cor in zip(zip(s0, s1), CORNERS):
            chc = np.zeros(a0.shape, bool)
            for dr, dc in cor:
                chc |= ch[dr:dr + GN - 1, dc:dc + GN - 1]
            for r, c in np.argwhere(chc & (a1 > np.maximum(35.0, a0) + 1e-4)):
                top_v = max(((r + dr, c + dc) for dr, dc in cor), key=lambda v: H[v])
                if not core[top_v] and not frz_all[top_v] and near[top_v]:
                    low[top_v] = True
        if rows is not None and low.any():
            A, b = rows
            cur = A @ H.ravel()
            while low.any():
                new = A @ (H - 0.1 * low).ravel()
                bad = (new < b - 1e-9) & (new < cur - 1e-12)
                if not bad.any():
                    break
                hit = np.unique(A[np.flatnonzero(bad)].indices)
                hit = hit[low.ravel()[hit]]
                if not len(hit):
                    break
                low.ravel()[hit] = False
        if not low.any():
            break
        H = np.where(low, H - 0.1, H); guard += int(low.sum())
    return H, guard


def steep_changed(H, H0):
    """Changed triangles still steeper than max(35 deg, before), by triangle (row, col, half)."""
    s0, s1 = tri_slopes(H0), tri_slopes(H); ch = H != H0; out = []
    for half, ((a0, a1), cor) in enumerate(zip(zip(s0, s1), CORNERS)):
        chc = np.zeros(a0.shape, bool)
        for dr, dc in cor:
            chc |= ch[dr:dr + GN - 1, dc:dc + GN - 1]
        out += [(int(r), int(c), half) for r, c in np.argwhere(chc & (a1 > np.maximum(35.0, a0) + 1e-4))]
    return out


def section_widths(Hf, x0, z0, wd, wn, ts, qmax, level):
    """Exact wet width (planar terrain < level - 0.02) of the run at or nearest the axis, per section at t in ts (lines
    across the water axis; the terrain is linear between the crossings of the triangle edges)."""
    out = []
    for t in ts:
        P0 = np.array([x0 + t * wd[0], 0.0, z0 + t * wd[1]]); D = np.array([wn[0], 0.0, wn[1]])
        qs = [-qmax, qmax]
        for f in FAMS:
            fa, fb = f((P0 - qmax * D)[None])[0], f((P0 + qmax * D)[None])[0]
            if abs(fb - fa) > 1e-12:
                ks = np.arange(np.ceil(min(fa, fb)), np.floor(max(fa, fb)) + 1)
                qs += list(-qmax + (ks - fa) / (fb - fa) * 2 * qmax)
        qs = np.unique(np.clip(qs, -qmax, qmax))
        g = terrain_at(Hf, P0[0] + qs * D[0], P0[2] + qs * D[2]) - (level - 0.02)
        runs, start = [], (qs[0] if g[0] < 0 else None)
        for i in range(len(qs) - 1):
            if (g[i] < 0) != (g[i + 1] < 0):
                xq = qs[i] + g[i] / (g[i] - g[i + 1]) * (qs[i + 1] - qs[i])
                if g[i + 1] < 0:
                    start = xq
                else:
                    runs.append((start, xq)); start = None
        if start is not None:
            runs.append((start, qs[-1]))
        out.append(0.0 if not runs else max(0.0, (lambda r: r[1] - r[0])(min(runs, key=lambda r: 0 if r[0] <= 0 <= r[1] else min(abs(r[0]), abs(r[1]))))))
    return np.array(out)


def main():
    tpath, epath, spath, out_t, out_e, rec_path, rep_path = sys.argv[1:8]
    z = np.load(tpath); arrays = {k: z[k].copy() for k in z.files}
    H0 = arrays["heights"].astype(np.float64); H = H0.copy()
    env = np.load(epath).astype(np.float64); env_new = env.copy()
    records, rep, ctx = [], [], []
    core = np.zeros(H.shape, bool)                                                     # channel floor: never raised
    for s in json.load(open(spath)):
        base = VARIANTS.get(s["model"])
        m = model_info(base or s["model"])
        mv = model_info(s["model"]) if base else m
        dy_var = variant_offset(m, mv, s["model"]) if base else 0.0
        b = math.radians(s["bearing"]); d = np.array([math.sin(b), 0.0, math.cos(b)])
        C = np.array([s["x"], 0.0, s["z"]])
        n_sp = int(s.get("spans", 1)); half_all = n_sp * m["half"]
        e1, e2 = C - half_all * d, C + half_all * d
        nl = np.array([d[2], 0.0, -d[0]])                                                  # horizontal, across the road
        a1, a2 = tri_h(H0, e1[0], e1[2]), tri_h(H0, e2[0], e2[2])
        k_pitch = (a2 - a1) / (2 * half_all)                                                # deck rise per metre from e1
        def end_h(e, inward, rise):
            strip = max(tri_h(H0, *(e + a * inward + l * nl)[[0, 2]]) - a * rise for a in np.linspace(0.0, END_IN, 5)
                        for l in np.linspace(-m["end_half_w"], m["end_half_w"], 9))
            return strip + END_CLEAR
        h1, h2 = max(a1, end_h(e1, d, k_pitch)), max(a2, end_h(e2, -d, -k_pitch))
        phi = math.atan2(h2 - h1, 2 * half_all)
        f = np.array([d[0] * math.cos(phi), math.sin(phi), d[2] * math.cos(phi)])          # model length axis
        u = np.array([-d[0] * math.sin(phi), math.cos(phi), -d[2] * math.sin(phi)])         # model up
        if m["axis"] == 0:
            X, Y = f, u; Z = np.cross(X, Y)
        else:
            Z, Y = f, u; X = np.cross(Y, Z)
        Rm = np.stack([X, Y, Z], axis=1)                                                     # columns = local axes
        y_end = (m["end_y"][0] + m["end_y"][1]) / 2
        local_c = np.zeros(3); local_c[m["axis"]] = m["centre_len"]; local_c[2 - m["axis"]] = m["centre_lat"]
        span_pos, upper, lower = [], [], []
        for k in range(n_sp):
            frac = (2 * k + 1) / (2 * n_sp)                                                   # 0..1 along e1 -> e2
            Ck = C + (-half_all + (2 * k + 1) * m["half"]) * d
            pos = Ck - Rm @ np.array([local_c[0], 0.0, local_c[2]])
            pos[1] = h1 + frac * (h2 - h1) - y_end * math.cos(phi)
            pos = pos - dy_var * Y                                                           # variant: same world roadway
            span_pos.append(pos.copy())
            matrix = [*X.tolist(), *Y.tolist(), *Z.tolist(), *pos.tolist()]
            records.append(dict(site=s["id"], span=k, model=f"dz\\structures\\roads\\bridges\\{s['model']}.p3d", matrix=matrix))
            upper.append(matrix)
            if s.get("stack"):
                lm = [*X.tolist(), *Y.tolist(), *Z.tolist(), *(pos - STACK_DY * Y).tolist()]
                records.append(dict(site=s["id"], span=k, role="stack-lower", model=f"dz\\structures\\roads\\bridges\\{s['model']}.p3d", matrix=lm))
                lower.append(lm)
        pos = np.mean(span_pos, axis=0)
        # channel and seals
        wb = math.radians(s["water_bearing"]); wd = np.array([math.sin(wb), math.cos(wb)])
        wn = np.array([-wd[1], wd[0]])
        W = float(s["width"])
        flat = half_all - 6.5
        deck_half_w = m["width"] / 2 + 1.0
        frz = arrays["reserve"] | arrays["platform"] | arrays["narva"]
        run_end, cut_side, run_side, wet_side = 0.0, {}, {}, {}
        for sgn in (-1, 1):                                                            # per side: frozen run, first water
            last, gap = 0.0, 0.0
            for tt in np.arange(0.0, 60.0, 1.0):
                xx, zz = s["x"] + sgn * tt * wd[0], s["z"] + sgn * tt * wd[1]
                if frz[int(round((ZTOP - zz) / 6)), int(round(xx / 6))]:
                    last, gap = tt, 0.0
                else:
                    gap += 1.0
                    if gap > 3.0 and tt > 3.0:
                        break
            first_wet = 0.0
            for tt in np.arange(4.0, 60.0, 1.0):
                xx, zz = s["x"] + sgn * tt * wd[0], s["z"] + sgn * tt * wd[1]
                if min(tri_h(H0, xx + u * wd[1], zz - u * wd[0]) for u in (-3.0, -1.5, 0.0, 1.5, 3.0)) < float(s["level"]) - 0.01:
                    first_wet = tt; break
            run_end = max(run_end, last); run_side[sgn] = last; wet_side[sgn] = first_wet
            cut_side[sgn] = max(CUT_T, min(max(last + 6.0, first_wet + 4.0), 60.0))
        cut_t = max(cut_side.values())
        k = int((cut_t + 30) / 6) + 2
        rc, cc = int((ZTOP - s["z"]) / 6), int(s["x"] / 6)
        R_, C_ = np.mgrid[rc - k:rc + k + 1, cc - k:cc + k + 1]
        X_, Z_ = 6.0 * C_ - s["x"], (ZTOP - 6.0 * R_) - s["z"]
        t = X_ * wd[0] + Z_ * wd[1]; q = X_ * wn[0] + Z_ * wn[1]
        envv = np.full(H.shape, False)
        fin = np.isfinite(env)
        for dr in (0, 1):
            for dc in (0, 1):
                envv[dr:dr + 2047, dc:dc + 2047] |= fin
        in_t = (t >= -cut_side[-1]) & (t <= cut_side[1])
        axis = (np.abs(q) <= W / 2) & in_t
        sub0 = (slice(rc - k, rc + k + 1), slice(cc - k, cc + k + 1))
        sea_mode = bool((axis & ~envv[sub0] & (H0[sub0] < SEA)).any()) and not bool((axis & envv[sub0]).any())
        L = SEA if sea_mode else float(s["level"])
        bed = SEA_BED if sea_mode else max(BED_MIN, L - 0.5)
        sroad = X_ * d[0] + Z_ * d[2]
        target = bed + BANK * np.maximum(np.abs(q) - W / 2, 0)
        zone = in_t
        sub = (slice(rc - k, rc + k + 1), slice(cc - k, cc + k + 1))
        frozen = (arrays["reserve"] | arrays["platform"] | arrays["narva"])[sub]
        slat = X_ * d[2] - Z_ * d[0]                                                       # lateral offset from the road axis
        deck = (np.abs(sroad) <= flat) & (np.abs(slat) <= deck_half_w)
        allowed = zone & (~frozen | (np.abs(sroad) <= flat))
        hs = H[sub].copy()
        new = np.where(allowed, np.minimum(hs, target), hs)
        envl = np.zeros(H.shape, bool)                                                  # vertices of envelope cells at L
        fl = np.isfinite(env) & (np.abs(env - L) < 0.05)
        for dr in (0, 1):
            for dc in (0, 1):
                envl[dr:dr + 2047, dc:dc + 2047] |= fl
        links = []
        for sgn in (-1, 1):
            if wet_side[sgn] or sea_mode:
                continue
            cand = envl[sub] & (H0[sub] < L - 0.01) & (sgn * t > max(run_side[sgn], 6.0)) & ~frozen & (np.hypot(X_, Z_) <= 60.0)
            if not cand.any():
                continue
            i = int(np.argmin(np.where(cand, np.hypot(X_, Z_), np.inf)))
            tgt = np.array([X_.flat[i], Z_.flat[i]]); st = np.array(wd) * sgn * (run_side[sgn] + 3.0)
            ab = tgt - st; tt_ = np.clip(((X_ - st[0]) * ab[0] + (Z_ - st[1]) * ab[1]) / max(ab @ ab, 1e-9), 0, 1)
            dl = np.hypot(X_ - (st[0] + tt_ * ab[0]), Z_ - (st[1] + tt_ * ab[1]))
            new = np.where(~frozen & (dl <= W / 2 + 8.0), np.minimum(new, bed + BANK * np.maximum(dl - W / 2, 0)), new)
            links.append(dict(side=sgn, start=(st + [s["x"], s["z"]]).round(1).tolist(), target=(tgt + [s["x"], s["z"]]).round(1).tolist()))
            core[sub] |= (dl <= W / 2) & ~frozen
        core[sub] |= (np.abs(q) <= W / 2) & zone & allowed
        H[sub] = new
        cR, cC = np.mgrid[rc - k:rc + k, cc - k:cc + k]
        cx, cz = 6.0 * cC + 3 - s["x"], (ZTOP - 6.0 * cR - 3) - s["z"]
        ct, cq = cx * wd[0] + cz * wd[1], cx * wn[0] + cz * wn[1]
        seal = (np.abs(cq) <= W / 2 + 6) & (ct >= -cut_side[-1]) & (ct <= cut_side[1])
        for lk in links:
            st = np.array(lk["start"]) - [s["x"], s["z"]]; tg = np.array(lk["target"]) - [s["x"], s["z"]]; ab = tg - st
            tt_ = np.clip(((cx - st[0]) * ab[0] + (cz - st[1]) * ab[1]) / max(ab @ ab, 1e-9), 0, 1)
            seal |= np.hypot(cx - (st[0] + tt_ * ab[0]), cz - (st[1] + tt_ * ab[1])) <= W / 2 + 6
        es = env_new[rc - k:rc + k, cc - k:cc + k]
        block = np.isfinite(es) & (np.abs(es - L) > 0.05)
        if not sea_mode:
            env_new[rc - k:rc + k, cc - k:cc + k] = np.where(seal & ~block, L, es)
        under = deck & (np.abs(q) <= W / 2)                                                  # channel inside the deck footprint
        rep.append(dict(site=s["id"], model=s["model"], spans=n_sp, cut_t=round(cut_t, 1), cut_up_down=[round(cut_side[1], 1), round(cut_side[-1], 1)], frozen_run_m=run_end, links=links, water="sea" if sea_mode else "pond", pitch_deg=round(math.degrees(phi), 3), ends_road_y=[round(h1, 3), round(h2, 3)], ends_lift=[round(h1 - a1, 3), round(h2 - a2, 3)],
                        position=[round(v, 3) for v in pos], deck_road_mid=round(pos[1] + (mv["deck_max"] if mv["axis"] == 0 else (mv["end_y"][0] + mv["end_y"][1]) / 2), 2), level=L, bed=bed,
                        cut_vertices=int((new < hs).sum()), cut_frozen_vertices=int(((new < hs) & frozen).sum()),
                        max_cut_m=round(float((hs - new).max()), 2), channel_ground_max_under_deck=round(float(new[under].max()), 2) if under.any() else None,
                        seal_cells=0 if sea_mode else int((seal & ~block).sum())))
        ctx.append(dict(s=s, m=mv, upper=upper, lower=lower, L=L, bed=bed, sea=sea_mode, W=W, wd=wd, wn=wn, d=d, n_sp=n_sp,
                        sub=sub, cut_allowed=allowed, variant=bool(base), dy_var=dy_var))
    frz_all = arrays["reserve"] | arrays["platform"] | arrays["narva"]
    H_v4, guard_v4 = slope_pass(H, H0, core, frz_all)                                  # the v4 terrain
    stuck_v4 = steep_changed(H_v4, H0)
    H, fit = end_fit(H_v4, H0, env_new, ctx, core, frz_all)
    arrays["heights"] = H.astype(np.float32)
    arrays["v31_bridge_cut"] = (arrays["heights"] != H0.astype(np.float32)) | arrays.get("v31_bridge_cut", np.zeros(H.shape, bool))
    arrays["v31_bridge_fill"] = (arrays["heights"] > H0.astype(np.float32)) | arrays.get("v31_bridge_fill", np.zeros(H.shape, bool))
    np.savez(out_t, **arrays); np.save(out_e, env_new.astype(np.float32))
    json.dump(records, open(rec_path, "w"), indent=1)
    for r, f_ in zip(rep, fit["sites"]):
        r.update(f_)
    json.dump(dict(schema="bridges-v31.v5", params=dict(BANK=BANK, CUT_T=CUT_T, BED_MIN=BED_MIN, END_IN=END_IN, END_CLEAR=END_CLEAR, STACK_DY=STACK_DY,
                                                         FACE_TOL=FACE_TOL, RAMP_CAP=RAMP_CAP, RAMP_AIR=RAMP_AIR, LEG_TOL=LEG_TOL, DECK_CLEAR=DECK_CLEAR, WING=WING),
                   sites=rep, slope_guard_steps=guard_v4, slope_stuck_triangles=len(stuck_v4),
                   end_fit=fit["summary"]), open(rep_path, "w", newline="\n"), indent=1)
    print(json.dumps(dict(sites=[{k_: v for k_, v in r.items() if k_ in ("site", "fit_ends", "legs", "opening_m", "fill_vertices")} for r in rep], end_fit=fit["summary"]), indent=1))


def end_geometry(c):
    """World polygons of one site: abutment faces and ramp undersides (per outer end), deck faces, end strips, legs and
    footprint rectangles."""
    m = c["m"]; ax, lat = m["axis"], 2 - m["axis"]; lo, hi = m["roadway_lo_hi"]
    out = dict(ends=[], deck=[], strips=[], legs=[], foot=[])
    for k, M in enumerate(c["upper"]):
        out["deck"] += [to_world(M, T) for T in m["deck_faces"]]
        for ei, (e, inw) in enumerate(((lo, 1.0), (hi, -1.0))):
            if (ei == 0 and k == 0) or (ei == 1 and k == len(c["upper"]) - 1):
                for T in m["deck_faces"]:
                    P = clip_le(T, (T[:, ax] - e) * inw, END_IN)
                    if len(P) >= 3:
                        out["strips"].append((ei, to_world(M, P)))
                st = m["seats"][ei]
                out["ends"].append(dict(end=ei, kind=st["kind"], faces=[to_world(M, T) for T in st["faces"]], seat=st, matrix=M, e=e, inw=inw))
        bmin, bmax = m["bbox"]
        rect = np.array([[bmin[0], 0, bmin[2]], [bmax[0], 0, bmin[2]], [bmax[0], 0, bmax[2]], [bmin[0], 0, bmax[2]]])
        out["foot"].append(to_world(M, rect) * [1, 0, 1])
        if c["variant"]:
            out["legs"] += [("upper", k, to_world(M, f)) for f in m["legs"]]
        elif c["lower"]:                                                              # upper feet not resting on the copy
            out["legs"] += [("upper", k, to_world(M, f)) for f, g in zip(m["legs"], m["legs_over_stack"]) if g > LEG_TOL]
    for k, M in enumerate(c["lower"]):
        out["legs"] += [("lower", k, to_world(M, f)) for f in m["legs"]]
    return out


def end_fit(H_v4, H0, env, ctx, core, frz_all):
    H_v4 = H_v4.astype(np.float32).astype(np.float64)                                 # the v4 output, as stored
    Hf0 = H_v4.ravel()
    geo = [end_geometry(c) for c in ctx]
    support = np.zeros(GN * GN, bool)                                                   # vertices under a footprint
    for g in geo:
        for F in g["foot"]:
            for Q in pieces(F):
                cq = Q.mean(0)
                support[tri_w(cq[0], cq[2])[0].ravel()] = True
    # wet: below the site level, the sea or any adjacent envelope cell's level
    envmax = np.full((GN, GN), -np.inf)
    e_ = np.where(np.isfinite(env), env, -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            envmax[dr:dr + GN - 1, dc:dc + GN - 1] = np.maximum(envmax[dr:dr + GN - 1, dc:dc + GN - 1], e_)
    wet = (H_v4 < envmax) | (H_v4 < SEA)
    for c in ctx:
        wet[c["sub"]] |= H_v4[c["sub"]] < c["L"]
    shore = binary_dilation(wet, np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]], bool)) & ~wet   # NW-SE triangle neighbours
    sec = [sections(c) for c in ctx]
    w_v4 = [section_widths(Hf0, c["s"]["x"], c["s"]["z"], c["wd"], c["wn"], ts, c["W"] / 2 + 12, c["L"]) for c, ts in zip(ctx, sec)]
    open_v4 = [float(w.min()) for w in w_v4]
    protect = np.zeros(GN * GN, bool)
    rows = build_rows(geo, ctx, Hf0)
    held = np.zeros(GN * GN, bool); held[np.unique(rows["A"][np.flatnonzero(rows["hard_lb"])].indices)] = True
    log = []
    for rnd in range(FIT_ROUNDS):
        x, info = solve(rows, Hf0, wet.ravel() | protect | (frz_all.ravel() & ~support) | edge_mask())
        Hfit = (Hf0 + x).reshape(GN, GN)
        comp = []
        for i, c in enumerate(ctx):                                                   # widen what the raise narrowed
            Hfit, low = compensate(Hfit, c, sec[i], open_v4[i], held | (x > 0), frz_all, support)
            comp += low
        lb_rows = (rows["A"][rows["hard_lb"]], rows["b"][rows["hard_lb"]])
        Hfin, guard = slope_pass(Hfit, H0, core, frz_all, rows=lb_rows)
        Hfin = Hfin.astype(np.float32).astype(np.float64)
        op = [float(section_widths(Hfin.ravel(), c["s"]["x"], c["s"]["z"], c["wd"], c["wn"], ts, c["W"] / 2 + 12, c["L"]).min()) for c, ts in zip(ctx, sec)]
        narrowed = [i for i, (a, b) in enumerate(zip(open_v4, op)) if b < a - 1e-6]
        log.append(dict(round=rnd + 1, lp=info, compensation_vertices=len(comp), narrowed=[ctx[i]["s"]["id"] for i in narrowed]))
        if not narrowed:
            break
        for i in narrowed:                                                           # last resort: protect the raised shore
            msk = np.zeros((GN, GN), bool); msk[ctx[i]["sub"]] = True
            protect |= ((x > 0) & shore.ravel() & msk.ravel())
    # final measurement of every constraint on the final terrain
    rows_f = build_rows(geo, ctx, Hfin.ravel())
    v = rows_f["A"] @ Hfin.ravel(); v4v = rows_f["A"] @ Hf0
    Ab = rows_f["A"].copy(); Ab.data = (Ab.data > 1e-9).astype(float)
    rowblk = (Ab @ (wet.ravel() | protect).astype(float)) > 0                         # row touches a water-protected vertex
    sites = []
    for i, (c, g) in enumerate(zip(ctx, geo)):
        sel = rows_f["site"] == i; fe = []
        for ei in sorted({e["end"] for e in g["ends"]}):
            kind = [e["kind"] for e in g["ends"] if e["end"] == ei][0]
            r = sel & (rows_f["end"] == ei) & (rows_f["kind"] == ("face" if kind == "block" else "ramp"))
            if kind == "block":
                expo = rows_f["y"][r] - v[r]
                fe.append(dict(end=ei, kind=kind, max_exposure_m=round(float(expo.max()), 4), max_exposure_v4_m=round(float((rows_f["y"][r] - v4v[r]).max()), 4)))
            else:
                air = rows_f["y"][r] - v[r]; wat = rowblk[r]; bad = air > 0.10
                fe.append(dict(end=ei, kind=kind, max_air_m=round(float(air.max()), 4), max_air_v4_m=round(float((rows_f["y"][r] - v4v[r]).max()), 4),
                               max_air_dry_m=round(float(air[~wat].max()), 4) if (~wat).any() else None,
                               points=int(r.sum()), points_over_0_10=int(bad.sum()), water_exceptions=int((bad & wat).sum()),
                               fill_over_cap_m=round(float(np.maximum(v[r] - np.maximum(v4v[r], rows_f["y"][r] - RAMP_CAP), 0).max()), 4)))
        rs = sel & (rows_f["kind"] == "strip")
        legs = {}
        for role in ("upper", "lower"):
            rl = sel & (rows_f["kind"] == "leg") & (rows_f["role"] == role)
            if rl.any():
                gaps = []
                for lid in np.unique(rows_f["leg"][rl]):
                    j = rl & (rows_f["leg"] == lid)
                    gaps.append(float(rows_f["y"][j].min() - v[j].max()))
                legs[role] = dict(n=len(gaps), hanging=int(sum(gp > 0.05 for gp in gaps)), max_gap_m=round(max(gaps), 3))
        msk = np.zeros((GN, GN), bool); msk[c["sub"]] = True
        sites.append(dict(fit_ends=fe, deck_strip_min_clear_m=round(float((rows_f["y"][rs] - v[rs]).min()), 4) if rs.any() else None,
                          legs=legs, opening_m=dict(v4=round(open_v4[i], 3), v5=round(op[i], 3)),
                          fill_vertices=int(((Hfin > H_v4) & msk).sum()), fill_max_m=round(float((Hfin - H_v4)[msk].max()), 3),
                          lowered_vs_v4=int(((Hfin < H_v4) & msk).sum()),
                          stack=bool(c["lower"]), record_model=c["s"]["model"], variant_offset_m=round(c["dy_var"], 4)))
    stuck = steep_changed(Hfin, H0)
    summary = dict(rounds=log, protected_shore_vertices=int(protect.sum()), slope_guard_steps_v5=guard,
                   slope_stuck_triangles=len(stuck), raised_vertices=int((Hfin > H_v4).sum()),
                   lowered_vertices_vs_v4=int((Hfin < H_v4).sum()))
    return Hfin, dict(sites=sites, summary=summary)


def sections(c):
    sn = abs(c["wd"][0] * c["d"][2] - c["wd"][1] * c["d"][0])                         # |sin| water axis vs road
    td = min(c["m"]["width"] / 2 / max(sn, 1e-3), 30.0)
    return np.arange(-td, td + 1e-9, 0.1)


def compensate(Hc, c, ts, target, held, frz_all, support, step=0.25):
    """Where the raise narrowed a wet section below the v4 opening, lower free bank vertices (dry, cut-allowed by the
    v4 rules, not held by any fit constraint, frozen ones only under a footprint) toward the bed, best gain first."""
    s = c["s"]; qmax = c["W"] / 2 + 12
    w = section_widths(Hc.ravel(), s["x"], s["z"], c["wd"], c["wn"], ts, qmax, c["L"])
    if w.min() >= target - 1e-6:
        return Hc, []
    Hc = Hc.copy(); lowered = []
    r0, c0 = c["sub"][0].start, c["sub"][1].start
    cand = np.argwhere(c["cut_allowed"]) + [r0, c0]
    for _ in range(200):
        bad = w < target - 1e-6
        if not bad.any():
            break
        tb = ts[bad]; base = (target - w[bad]).sum(); best = (0.0, None)
        wetm = Hc < c["L"]
        for r, cc in cand:
            fl = r * GN + cc
            if held[fl] or Hc[r, cc] <= c["bed"] + 1e-6 or (frz_all[r, cc] and not support[fl]) or wetm[r, cc]:
                continue
            if not (wetm[max(r - 1, 0):r + 2, max(cc - 1, 0):cc + 2].any()):
                continue
            h = Hc[r, cc]; Hc[r, cc] = max(c["bed"], h - step)
            if any(math.degrees(math.atan(math.hypot(*tri_grad([Hc[a] for a in tri_ids(r0_, c0_, hf)], hf)))) > SLOPE_MAX + 1e-9 and
                   math.degrees(math.atan(math.hypot(*tri_grad([Hc[a] if a != (r, cc) else h for a in tri_ids(r0_, c0_, hf)], hf)))) <= SLOPE_MAX
                   for r0_, c0_, hf in ((r - 1, cc - 1, 0), (r - 1, cc - 1, 1), (r - 1, cc, 1), (r, cc - 1, 0), (r, cc, 0), (r, cc, 1))):
                Hc[r, cc] = h; continue
            gain = base - np.maximum(target - section_widths(Hc.ravel(), s["x"], s["z"], c["wd"], c["wn"], tb, qmax, c["L"]), 0).sum()
            Hc[r, cc] = h
            if gain > best[0] + 1e-9:
                best = (gain, (r, cc))
        if best[1] is None:
            break
        r, cc = best[1]; Hc[r, cc] = max(c["bed"], Hc[r, cc] - step); lowered.append((int(r), int(cc)))
        w = section_widths(Hc.ravel(), s["x"], s["z"], c["wd"], c["wn"], ts, qmax, c["L"])
    return Hc, sorted(set(lowered))


_EDGE = None


def edge_mask():
    global _EDGE
    if _EDGE is None:
        e = np.zeros((GN, GN), bool); e[0, :] = e[-1, :] = e[:, 0] = e[:, -1] = True; _EDGE = e.ravel()
    return _EDGE


def build_rows(geo, ctx, Hf):
    """Constraint rows on vertex heights: value = A @ H. kinds: face (>= y - FACE_TOL), ramp (>= y - RAMP_AIR; cap rows <=),
    leg (>= foot - LEG_TOL), wing (soft), deck and strip (<=)."""
    R = dict(idx=[], w=[], y=[], lb=[], ub=[], kind=[], site=[], end=[], role=[], leg=[], soft=[])
    def add(P, lb, ub, kind, i, end=-1, role="", leg=-1, soft=False):
        if not len(P):
            return
        P, iu = np.unique(P.round(6), axis=0, return_index=True)
        ix, w = tri_w(P[:, 0], P[:, 2])
        n = len(P)
        R["idx"].append(ix); R["w"].append(w); R["y"].append(P[:, 1])
        R["lb"].append(lb(P) if callable(lb) else np.full(n, lb)); R["ub"].append(ub(P) if callable(ub) else np.full(n, ub))
        R["kind"] += [kind] * n; R["site"] += [i] * n; R["end"] += [end] * n; R["role"] += [role] * n; R["leg"] += [leg] * n; R["soft"] += [soft] * n
    leg_id = 0
    for i, g in enumerate(geo):
        for e in g["ends"]:
            if e["kind"] == "block":
                P, _ = face_points(e["faces"])
                add(P, lambda P: P[:, 1] - FACE_TOL, np.inf, "face", i, e["end"])
            else:
                st = e["seat"]
                P, _ = face_points(e["faces"])
                add(P, lambda P: P[:, 1] - RAMP_AIR, np.inf, "ramp", i, e["end"])
                caps = [lambda Q: Q[:, 1] - RAMP_CAP] * len(e["faces"])
                P, pos = face_points(e["faces"], Hf, caps)
                if len(P):
                    T = terrain_at(Hf, P[:, 0], P[:, 2])
                    ub = np.where(pos, np.maximum(P[:, 1] - RAMP_CAP, T), T)
                    add_ub = P.copy()
                    ix, w = tri_w(add_ub[:, 0], add_ub[:, 2]); n = len(add_ub)
                    R["idx"].append(ix); R["w"].append(w); R["y"].append(add_ub[:, 1]); R["lb"].append(np.full(n, -np.inf)); R["ub"].append(ub)
                    R["kind"] += ["cap"] * n; R["site"] += [i] * n; R["end"] += [e["end"]] * n; R["role"] += [""] * n; R["leg"] += [-1] * n; R["soft"] += [False] * n
                # wings: 1:WING beside the ramp (soft)
                M = e["matrix"]; ax = ctx[i]["m"]["axis"]; lat = 2 - ax; cl = ctx[i]["m"]["centre_lat"]
                aa = np.linspace(0.5, st["a_seat"] - 0.1, 5); pts, yy = [], []
                for side, l0 in ((-1, st["lat_lo"]), (1, st["lat_hi"])):
                    for r in (0.5, 1.0, 2.0, 3.0, 4.5):
                        p = np.zeros((len(aa), 3)); p[:, ax] = e["e"] + e["inw"] * aa; p[:, lat] = cl + l0 + side * r
                        p[:, 1] = st["y0"] + st["slope"] * aa - RAMP_CAP - r / WING
                        pts.append(to_world(M, p))
                P = np.concatenate(pts)
                add(P, lambda P: P[:, 1], np.inf, "wing", i, e["end"], soft=True)
        for ei, P3 in g["strips"]:
            P, _ = face_points([P3])
            add(P, -np.inf, lambda P: P[:, 1] - DECK_CLEAR, "strip", i, ei)
        P, _ = face_points(g["deck"])
        add(P, -np.inf, lambda P: P[:, 1] - DECK_CLEAR, "deck", i)
        for role, k, F in g["legs"]:
            add(F, lambda P: np.full(len(P), P[:, 1].min()) - LEG_TOL, np.inf, "leg", i, role=role, leg=leg_id)
            leg_id += 1
    idx = np.concatenate(R["idx"]); w = np.concatenate(R["w"]); n = len(idx)
    A = csr_matrix((w.ravel(), idx.ravel(), np.arange(0, 3 * n + 1, 3)), shape=(n, GN * GN))
    A.eliminate_zeros()
    out = dict(A=A, y=np.concatenate(R["y"]), lb=np.concatenate(R["lb"]), ub=np.concatenate(R["ub"]),
               kind=np.array(R["kind"]), site=np.array(R["site"]), end=np.array(R["end"]), role=np.array(R["role"]),
               leg=np.array(R["leg"]), soft=np.array(R["soft"]))
    out["b"] = out["lb"]
    out["hard_lb"] = np.isfinite(out["lb"]) & ~out["soft"]
    return out


def tri_ids(r0, c0, half):
    return ((r0, c0), (r0, c0 + 1), (r0 + 1, c0 + 1)) if half == 0 else ((r0, c0), (r0 + 1, c0 + 1), (r0 + 1, c0))


def tri_grad(Hv, half):
    """Gradient (per metre) of a triangle from its three heights, as tri_slopes."""
    a, b, c = Hv
    return ((b - a) / 6.0, (b - c) / 6.0) if half == 0 else ((b - c) / 6.0, (a - c) / 6.0)


def slope_rows(cols, Hf):
    """Linear rows (raises of cols) keeping every triangle around them under SLOPE_MAX (inscribed octagon of the slope
    circle) unless it was already steeper; right-hand side never below what the current terrain uses."""
    pos = {int(v): i for i, v in enumerate(cols)}; rows, rhs = [], []
    lim = math.tan(math.radians(SLOPE_MAX)) * math.cos(math.radians(22.5))
    seen = set()
    for v in cols:
        r, c = divmod(int(v), GN)
        for r0, c0, half in ((r - 1, c - 1, 0), (r - 1, c - 1, 1), (r - 1, c, 1), (r, c - 1, 0), (r, c, 0), (r, c, 1)):
            if (r0, c0, half) in seen or not (0 <= r0 < GN - 1 and 0 <= c0 < GN - 1):
                continue
            seen.add((r0, c0, half))
            ids = [a * GN + b for a, b in tri_ids(r0, c0, half)]
            gx, gz = tri_grad([Hf[i] for i in ids], half)
            if math.degrees(math.atan(math.hypot(gx, gz))) > SLOPE_MAX:
                continue
            ex = tri_grad(np.eye(3), half)                                             # coefficients per vertex
            for th in (0.0, 45.0, 90.0, 135.0):
                co = np.cos(np.radians(th)) * np.array(ex[0]) + np.sin(np.radians(th)) * np.array(ex[1])
                cur = float(co @ [Hf[i] for i in ids])
                for sg in (1.0, -1.0):
                    row = {pos[i]: sg * co[j] for j, i in enumerate(ids) if i in pos and abs(co[j]) > 0}
                    if row:
                        rows.append(row); rhs.append(max(lim - sg * cur, 0.0))
    data, ri, ci = [], [], []
    for k, row in enumerate(rows):
        for j, val in row.items():
            ri.append(k); ci.append(j); data.append(val)
    return csr_matrix((data, (ri, ci)), shape=(len(rows), len(cols))), np.array(rhs)


def solve(rows, Hf, blocked):
    """min sum(raise) + 1000 sum(hard deficit) + 2 sum(wing deficit); raise >= 0 only on free vertices, never more than a
    row it serves needs (deficit / weight, for weights >= 0.05) nor more than OVER_MAX above that row's bound (no spikes
    on far vertices); upper rows never pushed above max(current, bound)."""
    from scipy.sparse import hstack, vstack, identity
    A, lb, ub = rows["A"], rows["lb"], rows["ub"]
    cur = A @ Hf
    has_lb = np.isfinite(lb) & (lb > cur + 1e-9)
    x = np.zeros(GN * GN)
    if not has_lb.any():
        return x, "nothing to raise"
    li = np.flatnonzero(has_lb)
    Al = A[li].tocoo()
    dfc, lbe = (lb[li] - cur[li])[Al.row], lb[li][Al.row] - Hf[Al.col]                 # row deficit, row bound over vertex
    need = np.where(Al.data >= 0.05, np.minimum(dfc / np.maximum(Al.data, 1e-9), lbe + OVER_MAX), lbe)
    top = np.full(GN * GN, -np.inf); np.maximum.at(top, Al.col, need)                    # largest useful raise per vertex
    cols = np.unique(Al.col); cols = cols[~blocked[cols] & (top[cols] > 1e-9)]
    if not len(cols):
        return x, "nothing free to raise"
    Ac = A[:, cols]
    ui = np.flatnonzero(np.isfinite(ub) & (Ac.getnnz(axis=1) > 0))
    Sa, sb = slope_rows(cols, Hf)
    nv, ns = len(cols), len(li)
    G1 = hstack([-Ac[li], -identity(ns, format="csr")])
    h1 = -(lb[li] - cur[li])
    G2 = vstack([hstack([Ac[ui], csr_matrix((len(ui), ns))]), hstack([Sa, csr_matrix((Sa.shape[0], ns))])])
    h2 = np.concatenate([np.maximum(ub[ui] - cur[ui], 0.0), sb])
    pen = np.where(rows["soft"][li], 2.0, 1000.0)
    res = linprog(np.concatenate([np.ones(nv), pen]), A_ub=vstack([G1, G2]).tocsr(), b_ub=np.concatenate([h1, h2]),
                  bounds=list(zip(np.zeros(nv), top[cols])) + [(0, None)] * ns, method="highs")
    if res.status != 0:
        refuse(f"end fit LP failed: {res.message}")
    x[cols] = np.where(res.x[:nv] > 1e-7, res.x[:nv], 0.0)
    return x, f"{res.message} ({nv} vertices, {ns} lower rows, {len(ui)} upper rows)"


if __name__ == "__main__":
    main()
