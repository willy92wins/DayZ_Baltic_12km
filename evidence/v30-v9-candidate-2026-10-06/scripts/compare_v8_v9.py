"""v8 against v9 on the points the plan names: inland water near the map border, the navigable corridors (the boat
tests of BALTIC-012/013 hold while the Luga corridor is unchanged), and the vertex count per class.
Usage: compare_v8_v9.py V8.npz V9.npz CORRIDORS.geojson OUT.json"""
import json
import sys

import numpy as np
import shapely
from shapely.geometry import shape

sys.path.insert(0, r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees'
                   r'\codex-handoff-review-74f290\tools\terrain')
from v30_common import grid_xz  # noqa: E402

v8, v9 = np.load(sys.argv[1]), np.load(sys.argv[2])
feats = json.load(open(sys.argv[3], encoding='utf-8'))['features']
x, z = grid_xz()
names = ['land', 'sea', 'lake', 'navigable', 'delta', 'river', 'stream', 'pond']
out = {'classes': {n: [int((v8['cls'] == k).sum()), int((v9['cls'] == k).sum())] for k, n in enumerate(names)}}
inland = (2, 5, 6, 7)
for m in (12, 60):
    band = (x < m) | (z < m) | (x > 12282 - m) | (z > 12282 - m)
    out[f'inland_water_within_{m}m'] = [int((band & np.isin(v8['cls'], inland)).sum()),
                                        int((band & np.isin(v9['cls'], inland)).sum())]
h8, h9 = v8['heights'].astype(float), v9['heights'].astype(float)
corr = {}
for f in feats:
    name = f['properties']['river']
    g = shape(f['geometry'])
    x0, z0, x1, z1 = g.bounds
    box = (x >= x0) & (x <= x1) & (z >= z0) & (z <= z1)
    inside = np.zeros_like(box)
    inside[box] = shapely.contains_xy(g, x[box], z[box])
    d = np.abs(h9[inside] - h8[inside])
    corr[name] = {'vertices': int(inside.sum()), 'changed': int((d > 1e-4).sum()),
                  'max_abs_dh_m': round(float(d.max()) if d.size else 0.0, 3),
                  'class_changed': int((v8['cls'][inside] != v9['cls'][inside]).sum()),
                  'level_changed': int((~np.isclose(v8['level'][inside], v9['level'][inside], equal_nan=True)).sum())}
out['navigable_corridors'] = corr
out['changed_vertices'] = int((np.abs(h9 - h8) > 1e-4).sum())
json.dump(out, open(sys.argv[4], 'w', encoding='utf-8'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'navigable_corridors'}, indent=1))
for k, v in corr.items():
    if v['changed'] or v['class_changed'] or v['level_changed']:
        print(' corridor', k, v)
print(' corridors unchanged:', sum(1 for v in corr.values() if not (v['changed'] or v['class_changed'] or v['level_changed'])),
      'of', len(corr))
