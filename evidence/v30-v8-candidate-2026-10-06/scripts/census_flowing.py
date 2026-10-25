"""Census of flowing water (navigable 3, rivers 5, streams 6) on a terrain: levels, depths, beds under the engine sea,
the fixed 24 m corridors, and the crossing offset of each shore edge against a smoothed outline (sigma 12, shift 4)."""
import json
import sys
from pathlib import Path

import numpy as np
import shapely
from scipy import ndimage

W = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
sys.path.insert(0, str(W / 'tools' / 'terrain'))
from v30_common import N, cell_planes, grid_xz  # noqa: E402
from finish_shores_v30 import protect_corridors  # noqa: E402
from profile_coast_v30 import EDGES, NARVA, SEA_CLASSES  # noqa: E402
from profile_lakes_v30 import window_lines  # noqa: E402

FLOW = (3, 5, 6)
t = dict(np.load(sys.argv[1]))
h = t['heights'].astype(np.float64)
cls, level = t['cls'], t['level'].astype(np.float64)
x, z = grid_xz()
planes = cell_planes(cls, level)
exact, margin, entries, _ = protect_corridors(planes)
narva = np.hypot(x - NARVA[0], z - NARVA[1]) <= 620.0
border = (x < 12) | (z < 12) | (x > 12270) | (z > 12270)
flow = np.isin(cls, FLOW)
land = cls == 0
rep = {'terrain': sys.argv[1], 'corridor_entries': len(entries)}
for k in FLOW:
    m = cls == k
    d = level[m] - h[m]
    lv = level[m]
    rep[f'class_{k}'] = {
        'vertices': int(m.sum()),
        'level_m': [round(float(np.percentile(lv, q)), 2) for q in (0, 10, 50, 90, 100)],
        'depth_m': [round(float(np.percentile(d, q)), 2) for q in (0, 10, 50, 90, 100)],
        'bed_below_0p85_and_level_above_0p80': int((m & (h < 0.85) & (level > 0.80)).sum()),
        'level_at_or_below_0p80': int((m & (level <= 0.80)).sum()),
        'in_exact_corridor': int((m & exact).sum()), 'in_corridor_margin': int((m & margin).sum()),
        'in_narva_620': int((m & narva).sum()), 'on_border': int((m & border).sum())}

# components of flowing water, 8-connected
lab, n = ndimage.label(flow, structure=np.ones((3, 3), int))
sizes = np.bincount(lab.ravel())[1:]
rep['components'] = {'count': int(n), 'sizes_top10': sorted(sizes.tolist(), reverse=True)[:10],
                     'under_4_vertices': int((sizes < 4).sum())}
# shore edges: native edges between a flowing water vertex and a land vertex; local level = the water end's level
rows = []
for dr, dc in EDGES:
    a = (slice(0, N - dr), slice(0, N - dc))
    b = (slice(dr, N), slice(dc, N))
    for wa, wb in ((a, b), (b, a)):
        e = flow[wa] & land[wb]
        r, c = np.nonzero(e)
        rw, cw = r + wa[0].start, c + wa[1].start
        rl, cl = r + wb[0].start, c + wb[1].start
        rows.append((rw, cw, rl, cl, np.full(r.size, 6.0 * (2 ** 0.5 if dr and dc else 1.0))))
rw, cw, rl, cl, length = (np.concatenate(v) for v in zip(*rows))
L = level[rw, cw]
hw, hl = h[rw, cw] - L, h[rl, cl] - L
tcross = hw / (hw - hl)             # fraction from the water end where the terrain crosses L
edge_cls = cls[rw, cw]
fixed_w = margin[rw, cw]
fixed_e = exact[rw, cw]
rep['shore_edges'] = {}
for k in FLOW:
    s = edge_cls == k
    rep['shore_edges'][f'class_{k}'] = {
        'edges': int(s.sum()),
        'water_end_in_exact_corridor': int((s & fixed_e).sum()),
        'water_end_in_corridor_margin': int((s & fixed_w).sum()),
        'crossing_fraction_from_water_p10_p50_p90': [round(float(np.percentile(tcross[s], q)), 3) for q in (10, 50, 90)],
        'water_end_depth_m_p50': round(float(np.median(-hw[s])), 2),
        'land_end_freeboard_m_p50': round(float(np.median(hl[s])), 2)}

# crossing offset against a smoothed outline, per component (sigma 12 m, shift 4 m), as profile_lakes measures it
offs = {k: [] for k in FLOW}
g = 12
objs = ndimage.find_objects(lab)
for i, sl in enumerate(objs, 1):
    if sl is None or sizes[i - 1] < 4:
        continue
    r0, r1 = max(sl[0].start - g, 0), min(sl[0].stop + g, N)
    c0, c1 = max(sl[1].start - g, 0), min(sl[1].stop + g, N)
    Wn = (slice(r0, r1), slice(c0, c1))
    B = lab[Wn] == i
    base = np.where(B, -ndimage.distance_transform_edt(B), ndimage.distance_transform_edt(~B)) * 6.0
    smooth = np.clip(ndimage.gaussian_filter(base, 2.0), base - 4.0, base + 4.0)
    near = np.abs(base) <= 25.0
    lines = window_lines(smooth, near, r0, c0)
    if not lines:
        continue
    segs = np.concatenate([np.stack([ln[:-1], ln[1:]], axis=1) for ln in lines])
    tree = shapely.STRtree(shapely.linestrings(segs))
    xw, zw = x[Wn], z[Wn]
    _, dist = tree.query_nearest(shapely.points(xw[near], zw[near]), return_distance=True, all_matches=False)
    sd = np.full(B.shape, np.nan)
    sd[near] = np.where(smooth[near] < 0, -dist, dist)
    hh, ll, cc = h[Wn], level[Wn], cls[Wn]
    lnd = land[Wn]
    nr, nc = B.shape
    for dr, dc in EDGES:
        for flip in (False, True):
            A = (slice(0, nr - dr), slice(0, nc - dc))
            Bs = (slice(dr, nr), slice(dc, nc))
            wa, wb = (Bs, A) if flip else (A, Bs)
            e = B[wa] & lnd[wb]
            sa, sb = sd[wa][e], sd[wb][e]
            ok = np.isfinite(sa) & np.isfinite(sb) & (sa * sb < 0)
            tstar = np.abs(sa[ok]) / (np.abs(sa[ok]) + np.abs(sb[ok]))
            Lw = ll[wa][e][ok]
            ha, hb = hh[wa][e][ok] - Lw, hh[wb][e][ok] - Lw
            tt = ha / (ha - hb)
            ln = 6.0 * (2 ** 0.5 if dr and dc else 1.0)
            kk = cc[wa][e][ok]
            for k in FLOW:
                offs[k].append((np.abs(tt - tstar) * ln)[kk == k])
rep['crossing_offset_m_vs_smoothed_outline'] = {}
for k in FLOW:
    v = np.concatenate(offs[k]) if offs[k] else np.zeros(0)
    rep['crossing_offset_m_vs_smoothed_outline'][f'class_{k}'] = {
        'edges': int(v.size), **({f'p{q}': round(float(np.percentile(v, q)), 2) for q in (50, 90, 99)} if v.size else {})}
print(json.dumps(rep, indent=1))
