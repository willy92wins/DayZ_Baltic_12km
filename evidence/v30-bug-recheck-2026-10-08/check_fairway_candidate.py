"""Independent frozen-consumer checks of the bounded fairway proposal."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools/terrain'), str(ROOT/'tools/navigation')]
from audit_fairway_triangles_v30 import records
from waterway_common import sample
from v30_common import cell_planes
from verify_roads_v30 import evaluate

B = Path('E:/DayZ-Baltic-Build/v30-bug-recheck-20261008/fairway-proposal-r2')
old_path = Path('E:/DayZ-Baltic-Build/v30-bounded-integration-20261008/combined/terrain_inland.npz')
a, b = np.load(old_path), np.load(B/'terrain_fairways.npz')
old, new = a['heights'].astype(float), b['heights'].astype(float)
changed = old != new
checks = dict(metadata_exact=all(np.array_equal(a[k], b[k], equal_nan=True) for k in a.files if k != 'heights'),
              road_reserve_fixed=bool(np.array_equal(old[a['reserve']],new[a['reserve']])),
              changed_only_navigable_water=bool(np.all(a['cls'][changed] == 3)),
              dry_ground_exact=bool(np.array_equal(old[a['cls']==0],new[a['cls']==0])),
              maximum_lowering_10cm=float((old-new).max()) <= .10,
              no_raising=bool(np.all(new <= old)),
              high_water_bed_above_90cm=bool(np.all(new[changed & (a['level']>=2)] >= .90)))
planes = cell_planes(a['cls'], a['level'], sea_cut=.51)
results = []
for f in json.loads(Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson').read_text())['features']:
    rec = records(shape(f['geometry']), planes)
    x, z = rec['xz'].T
    before = rec['level']-sample(old,x+200000,z)
    after = rec['level']-sample(new,x+200000,z)
    results.append(dict(river=f['properties']['river'], faces=rec['faces'], before_min_m=float(before.min()),
                        after_min_m=float(after.min()), failing_faces=int(np.unique(rec['face'][after<.99]).size)))
checks['all_frozen_corridors_pass'] = all(r['failing_faces']==0 for r in results)
checks['baseline_rejected'] = any(r['before_min_m']<.99 for r in results)
# Different consumer for slopes, using native face gradients and wet/dry masks.
steeper = []
land = a['cls']==0
for dr,dc in [(0,1),(1,0)]:
    def slope(h):
        mid = h[dr:dr+2047,dc:dc+2047]
        return np.degrees(np.arctan(np.hypot(mid-h[:-1,:-1],h[1:,1:]-mid)/6))
    touch = land[:-1,:-1] | land[dr:dr+2047,dc:dc+2047] | land[1:,1:]
    so,sn = slope(old),slope(new)
    bad=touch & (sn>35.01) & (sn>so+1e-6)
    steeper.extend(dict(row=int(r),col=int(c),half=[dr,dc],before=float(so[r,c]),after=float(sn[r,c]))
                   for r,c in zip(*np.nonzero(bad)))
checks['no_new_or_worsened_steep_land_touching_faces'] = not steeper
roads = evaluate(new, a['water'].astype(bool))
checks['roads_pass'] = roads['status']=='PASS'
report = dict(status='PASS_OFFLINE_PROPOSAL' if all(checks.values()) else 'FAIL', checks=checks,
              terrain_sha256=hashlib.sha256((B/'terrain_fairways.npz').read_bytes()).hexdigest(),
              rivers=results, steep_faces=steeper, roads=roads,
              limitation='Floor exceptions require a product decision; no deployed or runtime result.')
Path(__file__).with_name('fairway-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=report['status'],checks=checks,steep_faces=steeper,
                     min_depth_m=min(r['after_min_m'] for r in results)),indent=1))
raise SystemExit(0 if all(checks.values()) else 1)
