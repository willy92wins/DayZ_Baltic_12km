"""Numbers behind the pointy-edge report on the v5 terrain (E:/DayZ-Baltic-Build/v30-v5/coast/terrain_coast.npz).

1. The east strip of the Kronstadt dam (x 7050-7550, z 10640-10790): land cells, how many are platform or reserve
   (fixed for tools/terrain/profile_coast_v30.py), crest heights and strip width.
2. Shore length by water class, as land-water cell edges times 6 m (a staircase length, longer than the true one).
3. Inland water (every class but sea 1 and delta 4) whose bed lies below the highest swell sea, 0.85 m.
Usage: edges_v5_numbers.py OUT.json
"""
import hashlib
import json
import sys

import numpy as np

T = 'E:/DayZ-Baltic-Build/v30-v5/coast/terrain_coast.npz'
t = np.load(T)
h, cls, platform, reserve = t['heights'].astype(float), t['cls'], t['platform'], t['reserve']
land = cls == 0


def window(x0, z0, x1, z1):
    return slice(int((12282 - z1) / 6), int((12282 - z0) / 6)), slice(int(x0 / 6), int(x1 / 6))


r, c = window(7050, 10640, 7550, 10790)
dam = land[r, c] & (h[r, c] > 0.85)
width = dam.sum(axis=0) * 6
dam_out = dict(window_xz=[7050, 10640, 7550, 10790], land_cells=int(dam.sum()),
               platform=int((dam & platform[r, c]).sum()), reserve=int((dam & reserve[r, c]).sum()),
               crest_m_p5_p50_p95=[round(float(v), 2) for v in np.percentile(h[r, c][dam], [5, 50, 95])],
               width_m_min_p50_max=[int(width[width > 0].min()), float(np.median(width[width > 0])), int(width.max())])


def shore_edges(water):
    return int((water[:, :-1] & land[:, 1:]).sum() + (water[:, 1:] & land[:, :-1]).sum()
               + (water[:-1, :] & land[1:, :]).sum() + (water[1:, :] & land[:-1, :]).sum())


shore = {str(k): round(shore_edges(cls == k) * 6 / 1000, 1) for k in range(1, 8)}
fixed_land = land & (platform | reserve)
water = cls > 0
shore_fixed = (water[:, :-1] & fixed_land[:, 1:]).sum() + (water[:, 1:] & fixed_land[:, :-1]).sum() \
    + (water[:-1, :] & fixed_land[1:, :]).sum() + (water[1:, :] & fixed_land[:-1, :]).sum()
inland = water & ~np.isin(cls, (1, 4))
out = dict(status='DIAGNOSTIC_EDGES_V5', terrain=T,
           terrain_sha256=hashlib.sha256(open(T, 'rb').read()).hexdigest(),
           kronstadt_dam_east=dam_out,
           shore_staircase_km_by_class=shore,
           shore_staircase_km_on_platform_or_reserve=round(int(shore_fixed) * 6 / 1000, 1),
           inland_water_cells=int(inland.sum()), inland_bed_below_085=int((inland & (h < 0.85)).sum()),
           limits=['Staircase lengths overstate true shore length; use them as shares.',
                   'Classes as in the v5 terrain; sea 1 and delta 4 are the only ones the coast profile edits.'])
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), indent=1)
print(json.dumps(out, indent=1))
