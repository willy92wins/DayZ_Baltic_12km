"""Depth census of a terrain: water depth (level - bed) per class, the ceiling the 1.0 m bed floor leaves
(level - 1.0), how far from the shore the bed reaches its depth, and how high the land stands over the water next to
it. Usage: depth_census.py TERRAIN.npz [LABEL]"""
import json
import sys

import numpy as np
from scipy import ndimage

t = np.load(sys.argv[1])
lab = sys.argv[2] if len(sys.argv) > 2 else 'terrain'
h, cls, lv = t['heights'].astype(float), t['cls'], t['level'].astype(float)
names = {2: 'lake', 5: 'river', 6: 'stream', 7: 'pond', 3: 'navigable'}
out = {'terrain': sys.argv[1], 'label': lab}
pct = lambda a, qs=(10, 50, 90): [round(float(np.percentile(a, q)), 2) for q in qs] if a.size else None
water = cls > 0
dist_in = ndimage.distance_transform_edt(water) * 6.0          # metres to the nearest land vertex, inside water
for k, n in names.items():
    m = (cls == k) & np.isfinite(lv)
    d = (lv - h)[m]
    ceil = (lv - 1.0)[m]
    di = dist_in[m]
    out[n] = {'vertices': int(m.sum()), 'depth_p10_p50_p90': pct(d), 'depth_max': round(float(d.max()), 2) if d.size else None,
              'share_depth_ge_0_5': round(float((d >= 0.5).mean()), 3) if d.size else None,
              'share_depth_ge_1_0': round(float((d >= 1.0).mean()), 3) if d.size else None,
              'level_p10_p50_p90': pct(lv[m]),
              'ceiling_level_minus_1m_p10_p50_p90': pct(ceil),
              'depth_by_shore_distance_m': {f'{a}-{b}': pct(d[(di > a) & (di <= b)], (50,))
                                            for a, b in ((0, 6), (6, 12), (12, 24), (24, 1e9))}}
# land next to inland water (classes 2, 5, 6, 7): height over the nearest water level, by distance
inland = np.isin(cls, (2, 5, 6, 7))
dist_out, idx = ndimage.distance_transform_edt(~inland, return_indices=True)
dist_out *= 6.0
near_lv = lv[idx[0], idx[1]]
land = ~water
out['banks_over_water_m'] = {f'{a}-{b}m': pct((h - near_lv)[land & (dist_out > a) & (dist_out <= b)])
                             for a, b in ((0, 6.1), (6.1, 12.1), (12.1, 24.1), (24.1, 60.1))}
print(json.dumps(out, indent=1))
