"""Carve narrow pond-piece streams as thin V channels, the way Chernarus does.

Measured 2026-10-13 on Astra's Chernarus survey (384 stream_14 pieces): the ground is 0.22 m below the ribbon on the axis
and already +1.22 m above it 6 model units out, so the visible water is a 1-2 m strip at the bottom of a steep V; the
terrain, not the ribbon edge, draws the outline, and the 6-7.5 m grid steps read as a thin meander. Ours: a quarter of the
stream banks rise only 0.07-0.31 m in 6 m, so the water spreads around every wet vertex in wide steps.

Width (v4, 13-10 vanilla survey E:/DayZ-Baltic-Build/vanilla-tricks-20261013/REPORT.md section 3): Chernarus shows 4/5/9 m of
visible water on stream_14 and 3/4/5.5 m on the streambed kit (p10/p50/p90). v3 thinned every narrow reach to ~2.6 m, so
smooth 5-6 m reaches became stepped threads; v4 thins only where the visible width (medial-axis estimate on the native
triangle waterline) exceeds W_GATE, and sizes the V for ~4 m: thalweg depth d = clamp(h/2, D_MIN, DEPTH) for the lowest bank
rise h, so the waterline sits a third of the way along every thalweg-bank edge (2 m on a 6 m edge).
Narrow reach (v3, local): a wet vertex (below its piece plane) of a river or stream (cls 5/6) whose 7x7 neighbourhood
(+-18 m) has no wet vertex farther than MAX_HALF_CELLS from dry ground (<= 2 vertices wide there); reaches connected through
native triangle edges (4-neighbours + the NW-SE diagonal) with at least MIN_BODY vertices. Wider water attached to a reach
keeps its shape: the reach vertices touching it are neither dried nor raised (v2 required the whole body to be narrow, which
left every stream joined to a pond or a wide reach untouched).
  thin     wet vertices are dried shallowest first while the body stays connected through native edges, never the deepest
           of its neighbourhood and never an end (one wet native neighbour): one thalweg vertex across, steps included.
  dried    a dried vertex goes to min(P + SIDE, highest dry 8-neighbour), at least P + DRY_MIN.
  banks    dry 8-neighbours of the thalweg go to max(H, min(P + BANK, highest of their other dry 8-neighbours)),
           so no bank rises above the terrain behind it (no levee, the 017 complaint).
  thalweg  H = max(BED_MIN, P - d) (raised or lowered: a deep thalweg widens the water as much as a low bank).
Never touches reserve/platform/narva or water of another plane; slopes stay <= max(35 deg, before).
Usage: v_streams_v31.py <terrain.npz> <footprint.npz> <out_terrain.npz> <report.json> [--window x0 x1 z0 z1]
"""
import argparse, json
from collections import deque
import numpy as np
from scipy.ndimage import label, distance_transform_edt, maximum_filter, binary_dilation

DEPTH, D_MIN, BANK, SIDE, DRY_MIN, BED_MIN = 0.45, 0.10, 0.9, 0.6, 0.06, 1.0
W_GATE, K = 5.0, 4
MAX_HALF_CELLS, MIN_BODY, LOCAL, CLASSES = 1.5, 6, 7, (5, 6)
NATIVE = ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1))          # native triangle edges from a vertex
N8 = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]


def tri_slopes(H):
    nw, ne, sw, se = H[:-1, :-1], H[:-1, 1:], H[1:, :-1], H[1:, 1:]
    return (np.degrees(np.arctan(np.hypot((ne - nw) / 6.0, (ne - se) / 6.0))),
            np.degrees(np.arctan(np.hypot((se - sw) / 6.0, (nw - sw) / 6.0))))


def offending(H, H0, s0, limit=35.0):
    ch = H != H0
    s1 = tri_slopes(H)
    out = np.zeros(H.shape, bool)
    for (a0, a1), corners in zip(zip(s0, s1), (((0, 0), (0, 1), (1, 1)), ((0, 0), (1, 1), (1, 0)))):
        chc = np.zeros(a0.shape, bool)
        for dr, dc in corners:
            chc |= ch[dr:dr + 2047, dc:dc + 2047]
        bad = chc & (a1 > np.maximum(limit, a0))
        for dr, dc in corners:
            out[dr:dr + 2047, dc:dc + 2047] |= bad
    return out


def local_connected(wet, r, c):
    """Do the wet native neighbours of (r, c) stay connected among themselves (inside the 3x3) without (r, c)?"""
    nb = [(r + dr, c + dc) for dr, dc in NATIVE if wet[r + dr, c + dc]]
    if len(nb) <= 1:
        return False                                   # an end or isolated: keep it
    seen, q = {nb[0]}, deque([nb[0]])
    while q:
        a = q.popleft()
        for dr, dc in NATIVE:
            b = (a[0] + dr, a[1] + dc)
            if b in seen or b == (r, c) or not wet[b]:
                continue
            if abs(b[0] - r) <= 1 and abs(b[1] - c) <= 1:
                seen.add(b); q.append(b)
    return all(p in seen for p in nb)


def visible_width(H, vp_cell, r0, r1, c0, c1):
    """Medial-axis width (m) of the native-triangle waterline in vertex rows r0..r1, cols c0..c1, per vertex (nearest ridge)."""
    h = H[r0:r1 + 1, c0:c1 + 1]; p = vp_cell[r0:r1, c0:c1]
    nr, nc = r1 - r0, c1 - c0
    wet = np.zeros((nr * K, nc * K), bool)
    for i in range(K):
        for j in range(K):
            fr, fc = (i + 0.5) / K, (j + 0.5) / K
            nw, ne, sw, se = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
            t = np.where(fc >= fr, nw + fc * (ne - nw) + fr * (se - ne), nw + fr * (sw - nw) + fc * (se - sw))
            wet[i::K, j::K] = np.isfinite(p) & (t < p)
    px = 6.0 / K
    e = distance_transform_edt(wet) * px
    ridge = wet & (e >= maximum_filter(e, size=3))
    w = np.where(ridge, 2.0 * e, 0.0)
    # per vertex: largest ridge width within one cell around the vertex
    wv = maximum_filter(w, size=2 * K + 1)
    out = np.zeros((nr + 1, nc + 1))
    rr = np.clip(np.arange(nr + 1) * K, 0, nr * K - 1); cc = np.clip(np.arange(nc + 1) * K, 0, nc * K - 1)
    out[:, :] = wv[np.ix_(rr, cc)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("terrain"); ap.add_argument("footprint"); ap.add_argument("out"); ap.add_argument("report")
    ap.add_argument("--window", nargs=4, type=float)
    a = ap.parse_args()
    z = np.load(a.terrain); arrays = {k: z[k].copy() for k in z.files}
    H0 = arrays["heights"].astype(np.float64); H = H0.copy()
    frozen = arrays["reserve"] | arrays["platform"] | arrays["narva"]
    pl = np.load(a.footprint)["plane"].astype(np.float64)
    vp = np.full(H.shape, -np.inf); cp = np.where(np.isfinite(pl), pl, -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            vp[dr:dr + 2047, dc:dc + 2047] = np.maximum(vp[dr:dr + 2047, dc:dc + 2047], cp)
    piece = np.isfinite(vp)
    wet0 = piece & (H0 < vp)
    win = np.zeros(H.shape, bool); win[2:-2, 2:-2] = True
    if a.window:
        zz, xx = 6.0 * (2047 - np.arange(2048))[:, None], 6.0 * np.arange(2048)[None, :]
        x0, x1, z0, z1 = a.window
        win &= (xx >= x0) & (xx <= x1) & (zz >= z0) & (zz <= z1)
    kern = np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]])                  # native adjacency
    edt = distance_transform_edt(wet0)
    local = wet0 & (maximum_filter(edt, size=LOCAL) <= MAX_HALF_CELLS) & np.isin(arrays["cls"], CLASSES) & win
    lab, n = label(local, kern)
    size = np.bincount(lab.ravel(), minlength=n + 1)
    narrow_ids = np.nonzero(size >= MIN_BODY)[0]
    narrow_ids = narrow_ids[narrow_ids > 0]
    narrow = np.isin(lab, narrow_ids)
    vp_cell = np.where(np.isfinite(pl), pl, np.nan)
    width = np.zeros(H.shape)
    for i in narrow_ids:
        rr, cc = np.nonzero(lab == i)
        r0, r1 = max(rr.min() - 3, 0), min(rr.max() + 3, 2047); c0, c1 = max(cc.min() - 3, 0), min(cc.max() + 3, 2047)
        wv = visible_width(H0, vp_cell, r0, r1, c0, c1)
        sub = lab[r0:r1 + 1, c0:c1 + 1] == i
        width[r0:r1 + 1, c0:c1 + 1] = np.where(sub, wv, width[r0:r1 + 1, c0:c1 + 1])
    gate = narrow & (width > W_GATE)
    gate = binary_dilation(gate, np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]], bool), iterations=2) & narrow
    narrow_all = narrow
    wide = np.zeros(H.shape, bool)                                     # touches wet water that is not thinned
    for dr, dc in N8:
        wide |= np.roll(np.roll(wet0 & ~gate, dr, 0), dc, 1)
    narrow = gate
    # thinning
    wet = wet0.copy()
    depth = vp - H0
    cand = sorted(map(tuple, np.argwhere(narrow & ~frozen & ~wide)), key=lambda p: depth[p])
    dried = []
    for _ in range(3):
        changed = False
        for p in cand:
            if not wet[p]:
                continue
            r, c = p
            nbd = [depth[r + dr, c + dc] for dr, dc in NATIVE if wet[r + dr, c + dc]]
            if not nbd or depth[p] >= max(nbd):
                continue                               # the deepest of its neighbourhood stays
            if local_connected(wet, r, c):
                wet[p] = False; dried.append(p); changed = True
        if not changed:
            break
    thal = narrow & wet
    # heights
    for r, c in dried:
        nbh = [H0[r + dr, c + dc] for dr, dc in N8 if not wet[r + dr, c + dc]]
        top = max(nbh) if nbh else vp[r, c] + SIDE
        H[r, c] = max(H0[r, c], vp[r, c] + DRY_MIN, min(vp[r, c] + SIDE, top))
    other = np.zeros(H.shape, bool)
    for dr, dc in N8:
        other |= np.roll(np.roll(wet & ~narrow, dr, 0), dc, 1)
    banks = 0
    hmin = np.full(H.shape, BANK)
    for r, c in map(tuple, np.argwhere(thal)):
        P = vp[r, c]
        for dr, dc in N8:
            b = (r + dr, c + dc)
            if wet[b] or frozen[b] or other[b] or b in dried:
                continue
            beyond = [H0[b[0] + er, b[1] + ec] for er, ec in N8 if not wet[b[0] + er, b[1] + ec] and (b[0] + er, b[1] + ec) != (r, c)]
            cap = max(beyond) if beyond else P + BANK
            t = max(P + DRY_MIN, min(P + BANK, cap))
            if t > H[b]:
                H[b] = t; banks += 1
        for dr, dc in N8:                                             # lowest bank rise around this thalweg vertex
            b = (r + dr, c + dc)
            if not wet[b] and not other[b]:
                hmin[r, c] = min(hmin[r, c], max(H[b] - P, 0.0))
    tl = thal & ~frozen & ~wide
    d = np.clip(hmin / 2.0, D_MIN, DEPTH)
    H = np.where(tl, np.maximum(BED_MIN, vp - d), H)
    # slope guard
    H = H.astype(np.float32).astype(np.float64)
    s0 = tri_slopes(H0); guard = 0
    for it in range(13):
        bad = offending(H, H0, s0)
        if not bad.any():
            break
        fix = bad & (H != H0); guard += int(fix.sum())
        H = np.where(fix, H0 if it == 12 else H0 + 0.5 * (H - H0), H).astype(np.float32).astype(np.float64)
    ch = H != H0
    assert not (ch & frozen).any()
    arrays["heights"] = H.astype(np.float32); arrays["v31_v_stream"] = ch; arrays["v31_v_thalweg"] = tl
    np.savez(a.out, **arrays)
    rep = dict(schema="v-streams-v31.v4", params=dict(DEPTH=DEPTH, D_MIN=D_MIN, W_GATE=W_GATE, BANK=BANK, SIDE=SIDE, DRY_MIN=DRY_MIN, BED_MIN=BED_MIN,
               MAX_HALF_CELLS=MAX_HALF_CELLS, MIN_BODY=MIN_BODY, LOCAL=LOCAL, CLASSES=CLASSES), window=a.window,
               narrow_reaches=int(len(narrow_ids)), narrow_vertices_all=int(narrow_all.sum()),
               width_p10_50_90_before=[round(float(x), 2) for x in np.percentile(width[narrow_all], [10, 50, 90])],
               narrow_wet_vertices=int(narrow.sum()), dried=len(dried), thalweg=int(thal.sum()), banks_raised=banks,
               slope_guard_fixes=guard, changed=int(ch.sum()))
    json.dump(rep, open(a.report, "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
