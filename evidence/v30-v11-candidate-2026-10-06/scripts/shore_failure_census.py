"""Map-wide census of what the lake and river profiles left as it was (fast, whole-grid fields).

For every inland shore edge (native edge between water of classes 2, 3, 5, 6, 7 above the 0.80 m cut and land):
- moved: profile_lakes/profile_rivers changed one of its ends (heights differ from the pre-profile terrain);
- frozen reason: the first rule of the tools that fixes its water end (nature envelope, exact corridor, Narva, map
  border, platform, reserve, 22 m from the sea, from a vanilla reach, from water of the other kind);
- planform: sharp corners (turn > 45 degrees within 12 m) per km of outline, on the outline a 4 m shift can reach
  (sigma 12 m, clamped) and on a free one (sigma 30 m), by the class of the nearest water.
Usage: shore_failure_census.py PRE.npz POST.npz FITDIR OUT.json OUT.png [LABEL]"""
import json
import sys
from pathlib import Path

import contourpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy import ndimage  # noqa: E402

W = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
sys.path.insert(0, str(W / 'tools' / 'terrain'))
from v30_common import N, cell_planes, grid_xz  # noqa: E402
from finish_shores_v30 import protect_corridors  # noqa: E402
from profile_coast_v30 import EDGES, NARVA, NATURE  # noqa: E402

pre, post, fit, out_json, out_png = sys.argv[1], sys.argv[2], Path(sys.argv[3]), sys.argv[4], sys.argv[5]
label = sys.argv[6] if len(sys.argv) > 6 else 'v8'
t0, t1 = np.load(pre), np.load(post)
h0, h1 = t0['heights'].astype(float), t1['heights'].astype(float)
cls, lev = t1['cls'], t1['level'].astype(float)
assert np.array_equal(cls, t0['cls']), 'classes differ between the two terrains'
x, z = grid_xz()
INLAND = (2, 3, 5, 6, 7)
water = np.isin(cls, INLAND) & (lev > 0.80)
land = cls == 0
flow = np.isin(cls, (3, 5, 6)) & water
stand = np.isin(cls, (2, 7)) & water
sea = (cls > 0) & ~water
reach = np.zeros((N, N), bool)
for rr in json.loads((fit / 'axes.json').read_text(encoding='utf-8')).values():
    for a, b in rr['removed_cells']:
        reach[a:a + 2, b:b + 2] = True
d22 = lambda m: ndimage.distance_transform_edt(~m) * 6.0 <= 22.0  # noqa: E731
nature = np.load(NATURE)['reserve'].astype(bool)
exact, _, _, _ = protect_corridors(cell_planes(cls, lev, sea_cut=0.51))
narva = np.hypot(x - NARVA[0], z - NARVA[1]) <= 620.0
border = (x < 12) | (z < 12) | (x > 12270) | (z > 12270)
RULES = [('nature', nature), ('corridor', exact), ('narva', narva), ('border', border), ('platform', t1['platform']),
         ('reserve', t1['reserve']), ('near_sea', d22(sea)), ('near_vanilla_reach', d22(reach)),
         ('standing_near_flowing', stand & d22(flow)), ('flowing_near_standing', flow & d22(stand))]
reason = np.full((N, N), 'none', dtype=object)
for name, m in reversed(RULES):        # the first rule wins
    reason[m] = name
moved = h1 != h0

rw, cw, rl, cl = [], [], [], []
for dr, dc in EDGES:
    A = (slice(0, N - dr), slice(0, N - dc))
    B = (slice(dr, N), slice(dc, N))
    for wa, wb in ((A, B), (B, A)):
        r, c = np.nonzero(water[wa] & land[wb])
        rw.append(r + wa[0].start); cw.append(c + wa[1].start); rl.append(r + wb[0].start); cl.append(c + wb[1].start)
rw, cw, rl, cl = (np.concatenate(v) for v in (rw, cw, rl, cl))
kk = cls[rw, cw]
mv = moved[rw, cw] | moved[rl, cl]
rs = reason[rw, cw]

rep = {'terrains': {'pre': pre, 'post': post}, 'shore_edges': int(rw.size), 'by_class': {}}
for k in INLAND:
    m = kk == k
    fr = m & ~mv
    rep['by_class'][str(k)] = {'edges': int(m.sum()), 'moved_share': round(float(mv[m].mean()), 3) if m.any() else None,
                               'frozen': int(fr.sum()),
                               'frozen_by_reason': {str(q): int((fr & (rs == q)).sum()) for q in np.unique(rs[fr])}}

# planform: sharp corners on the reachable (clamped sigma 12) and free (sigma 30) outlines of all inland water
base = np.where(water, -ndimage.distance_transform_edt(water), ndimage.distance_transform_edt(~water)) * 6.0
s12 = np.clip(ndimage.gaussian_filter(base, 2.0), base - 4.0, base + 4.0)
s30 = ndimage.gaussian_filter(base, 5.0)
_, (ir, ic) = ndimage.distance_transform_edt(~water, return_indices=True)
near_cls = cls[ir, ic]
zone = np.abs(base) <= 30.0


def corners(field):
    gen = contourpy.contour_generator(x=np.arange(N) * 6.0, y=12282.0 - np.arange(N) * 6.0,
                                      z=np.ma.masked_invalid(np.where(zone, field, np.nan)),
                                      line_type=contourpy.LineType.Separate)
    out = {k: [0.0, 0] for k in INLAND}
    pts = []
    for ln in gen.lines(0.0):
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(ln, axis=0), axis=1))]
        if s[-1] < 48:
            continue
        q = np.arange(0, s[-1], 12.0)
        p = np.column_stack([np.interp(q, s, ln[:, 0]), np.interp(q, s, ln[:, 1])])
        ang = np.degrees(np.arctan2(*np.diff(p, axis=0).T[::-1]))
        turn = np.abs((np.diff(ang) + 180) % 360 - 180)
        mid = p[1:-1]
        r = np.clip(np.rint((12282 - mid[:, 1]) / 6).astype(int), 0, N - 1)
        c = np.clip(np.rint(mid[:, 0] / 6).astype(int), 0, N - 1)
        k = near_cls[r, c]
        for kc in INLAND:
            sel = k == kc
            out[kc][0] += 12.0 * sel.sum() / 1000.0
            out[kc][1] += int((sel & (turn > 45)).sum())
        sharp = turn > 45
        pts.append(mid[sharp])
    return ({str(kc): {'outline_km': round(v[0], 1), 'sharp_corners': v[1],
                       'per_km': round(v[1] / v[0], 2) if v[0] else None} for kc, v in out.items()},
            np.concatenate(pts) if pts else np.zeros((0, 2)))


rep['planform_sharp_corners'] = {}
rep['planform_sharp_corners']['reachable_4m'], sharp12 = corners(s12)
rep['planform_sharp_corners']['free_sigma30'], _ = corners(s30)
rep['planform_sharp_corners']['note'] = ('turn > 45 degrees within 12 m on the zero line of the smoothed signed distance; '
                                         'reachable = what profile_lakes/profile_rivers can follow; free = what a '
                                         'reshaped design could follow (narrow channels vanish under sigma 30)')
Path(out_json).write_text(json.dumps(rep, indent=1) + '\n', encoding='utf-8')
print(json.dumps(rep, indent=1))

# overview map: moved shore green, frozen by contact red, frozen by protection grey, sharp reachable corners orange
fig, ax = plt.subplots(figsize=(14, 14))
ax.imshow(np.where(water, 0.75, np.where(cls > 0, 0.55, 0.95)), cmap='gray', vmin=0, vmax=1,
          extent=(0, 12282, 0, 12282))
X, Z = cw * 6.0, 12282 - rw * 6.0
contact = np.isin(rs, ('standing_near_flowing', 'flowing_near_standing', 'near_sea', 'near_vanilla_reach'))
for m, col, lab in ((mv, '#2ca02c', 'orilla perfilada'), (~mv & contact, '#d62728', 'congelada por contacto'),
                    (~mv & ~contact & (rs != 'none'), '#7f7f7f', 'congelada por protección'),
                    (~mv & (rs == 'none'), '#9467bd', 'sin mover, sin regla')):
    ax.scatter(X[m], Z[m], s=0.3, c=col, label=lab, rasterized=True)
ax.scatter(sharp12[:, 0], sharp12[:, 1], s=2, c='#ff7f0e', label='esquina viva alcanzable (>45° en 12 m)')
ax.set_xlim(0, 12282); ax.set_ylim(0, 12282); ax.set_aspect('equal')
ax.legend(loc='lower left', markerscale=12, fontsize=10)
ax.set_title(f'Orillas de agua interior en la {label}: perfiladas, congeladas y esquinas vivas')
fig.savefig(out_png, dpi=110, bbox_inches='tight')
print(out_png)
