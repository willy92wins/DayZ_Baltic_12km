"""Read-only recheck of frozen consumers; report changes, never inherit runtime PASS."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import rasterio
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/terrain'))
from v30_common import cell_planes, tri_sample
from audit_fairway_triangles_v30 import records, depths, controls

OUT = Path(__file__).resolve().parent
SOURCE = Path('E:/DayZ-Baltic-Build/v30-bounded-integration-20261008/combined/terrain_inland.npz')
t = np.load(SOURCE)
h = t['heights'].astype(float)
planes = cell_planes(t['cls'], t['level'], sea_cut=.51)
report = dict(terrain=str(SOURCE), terrain_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest())

fairways = []
for f in json.loads(Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson').read_text())['features']:
    rec = records(shape(f['geometry']), planes)
    d = depths(h, rec)
    bad = d < .99  # 1 m current contract, same historic 1 cm numerical allowance.
    k = int(np.argmin(d))
    fairways.append(dict(river=f['properties']['river'], faces=rec['faces'], minimum_depth_m=float(d[k]),
                         failing_faces_1m=int(np.unique(rec['face'][bad]).size), worst_xz=rec['xz'][k].tolist(),
                         worst_weights=rec['weights'][k].tolist(), worst_ids=rec['ids'][k].tolist(),
                         water_level_m=float(rec['level'][k]), controls=controls(h, rec)))
report['current_24m_fairways'] = fairways

delta = []
for f in json.loads(Path('E:/DayZ-Baltic-Build/v30-v11/07-evidence/axes-corridors.geojson').read_text())['features']:
    if f['properties']['kind'] != 'corridor24m':
        continue
    rec = records(shape(f['geometry']), planes)
    d = depths(h, rec)
    k = int(np.argmin(d))
    delta.append(dict(name=f['properties']['name'], faces=rec['faces'], min_depth_m=float(d[k]),
                      failing_faces_3m=int(np.unique(rec['face'][d < 2.99]).size), worst_xz=rec['xz'][k].tolist()))
report['delta_old_3m_contract'] = delta

routes = {}
for label, path in {
    'bridge': 'evidence/foundation-followup-2026-10-01/continuous-pursuit-v4/reference.json',
    'cars_v3': 'evidence/foundation-followup-2026-10-01/regional-drive-v3/reference.json',
    'cars_v4': 'evidence/foundation-followup-2026-10-01/regional-drive-v4/reference.json',
    'neva_boats': 'evidence/v30-delta-fairways-2026-10-02/navmesh/boat-reference.json',
    'luga_boats': 'evidence/v30-luga-boat-2026-10-02/reference.json',
}.items():
    ref = json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
    with rasterio.open(ref['terrain']) as ds:
        old = ds.read(1).astype(float)
    rr = []
    for case in ref['cases']:
        pts = case.get('waypoints_xz') or case.get('route_xz')
        if pts is None and 'start' in case and 'goal' in case:
            pts = [np.asarray(case['start'])[[0, 2]], np.asarray(case['goal'])[[0, 2]]]
        if pts is None:
            rr.append(dict(case=case['case'], status='UNRECOGNIZED_ROUTE_SCHEMA', keys=list(case)))
            continue
        pts = np.asarray(pts)
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
        d = np.linspace(0, s[-1], max(2, int(np.ceil(s[-1]))+1))
        q = np.column_stack([np.interp(d, s, pts[:, j]) for j in range(2)])
        delta_h = tri_sample(h, q[:, 0], q[:, 1])-tri_sample(old, q[:, 0], q[:, 1])
        rr.append(dict(case=case['case'], samples=len(q), changed=int(np.count_nonzero(delta_h)),
                       max_ground_change_m=float(np.abs(delta_h).max())))
    routes[label] = dict(reference=path, cases=rr)
report['historical_route_ground_comparison'] = routes

wave = json.loads((ROOT/'evidence/v30-shore-wave-2026-10-03/temporal-v3-result.json').read_text())
report['old_shallow_points'] = []
for p in wave['results']:
    if p['role'] != 'frozen_shallow_failure':
        continue
    x, z = p['x'], p['z']
    r, c = int((12282-z)//6), int(x//6)
    ground = float(tri_sample(h, x, z))
    plane = float(planes[r, c]) if np.isfinite(planes[r, c]) else None
    report['old_shallow_points'].append(dict(id=p['id'], x=x, z=z, current_ground_m=ground,
        prior_ground_m=p['ranges']['ground']['min'], current_cell_plane_m=plane,
        current_nominal_depth_m=plane-ground if plane is not None else None,
        note='Plane diagnostic only; moved shore and vanilla replacements require their own classification.'))

with (OUT/'current-geometry.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(report, stream, indent=2, allow_nan=False)
    stream.write('\n')
print(json.dumps(dict(fairways=fairways, delta=delta, routes=routes), indent=1))
