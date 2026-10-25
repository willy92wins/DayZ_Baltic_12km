"""BALTIC-018 policy numbers: inland water whose bed lies below the engine sea crest, and the depth a bed floor leaves.

For every water class above the sea (classes 2, 3, 5, 6, 7 with level > 0.80, the pond-plane rule), on the v6 terrain:
vertices with the bed below 0.85 m, and with a bed floor F the depth left = level - max(bed, F). Standing bodies are
listed by the census labelling with area and level; navigable reaches by level band.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\tools\terrain')
from relevel_bodies_v30 import label_bodies  # noqa: E402

T = 'E:/DayZ-Baltic-Build/v30-v6/causeway/terrain_causeway.npz'
CREST, FLOOR = 0.85, 1.00
d = np.load(T)
h, cls, lev = d['heights'].astype(np.float64), d['cls'], d['level'].astype(np.float64)
above = np.isin(cls, (2, 3, 5, 6, 7)) & (np.nan_to_num(lev, nan=-1) > 0.80)
names = {2: 'lake', 3: 'navigable', 5: 'river', 6: 'stream', 7: 'pond'}
out = {'terrain': T, 'crest_m': CREST, 'floor_m': FLOOR, 'classes': {}}
for k, n in names.items():
    m = above & (cls == k)
    below = m & (h < CREST)
    lv = lev[below]
    room = lv - FLOOR   # depth left with the bed at the floor
    out['classes'][n] = {
        'vertices': int(m.sum()), 'bed_below_crest': int(below.sum()),
        'level_of_those_p5_p50_p95': np.percentile(lv, [5, 50, 95]).round(2).tolist() if below.any() else None,
        'depth_now_p50': round(float(np.median(lv - h[below])), 2) if below.any() else None,
        'depth_left_at_floor': {'<0.3': int((room < 0.3).sum()), '0.3-1': int(((room >= 0.3) & (room < 1)).sum()),
                                '1-2': int(((room >= 1) & (room < 2)).sum()), '>=2': int((room >= 2).sum())}}
ids = label_bodies(cls, lev)
rows = []
for i in np.unique(ids[ids > 0]):
    b = ids == i
    nb = int((b & (h < CREST)).sum())
    if nb == 0:
        continue
    L = float(np.median(lev[b]))
    rr, cc = np.nonzero(b)
    rows.append({'id': int(i), 'area_km2': round(b.sum() * 36 / 1e6, 3), 'level_m': round(L, 2),
                 'bed_below_crest': nb, 'depth_left_at_floor_m': round(L - FLOOR, 2),
                 'xz': [round(float(cc.mean() * 6)), round(float(12282 - rr.mean() * 6))]})
rows.sort(key=lambda r: -r['area_km2'])
out['standing_bodies_with_bed_below_crest'] = len(rows)
out['standing_area_km2_with_bed_below_crest'] = round(sum(r['area_km2'] for r in rows), 2)
out['standing_bodies_level_below_floor_plus_0p3'] = [r for r in rows if r['depth_left_at_floor_m'] < 0.3]
out['largest'] = rows[:15]
nav = above & (cls == 3)
bands = {}
for lo, hi in ((0.8, 1.5), (1.5, 2.5), (2.5, 3.5), (3.5, 6), (6, 99)):
    m = nav & (lev >= lo) & (lev < hi)
    bands[f'{lo}-{hi}'] = {'vertices': int(m.sum()), 'bed_below_crest': int((m & (h < CREST)).sum())}
out['navigable_by_level'] = bands
Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in out.items() if k != 'largest'}, indent=1)[:4000])
print('largest:')
for r in rows[:15]:
    print(' ', r)
