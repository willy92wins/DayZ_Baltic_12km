from pathlib import Path
import hashlib,json,sys
import numpy as np
from shapely.geometry import shape
B=Path(__file__).parent;W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-current-physical-consumers-2026-10-09'
sys.path.insert(0,str(W/'tools/terrain'))
from audit_fairway_triangles_v30 import records,depths,controls
from verify_roads_v30 import evaluate
from v30_common import vertex_plane_bounds
source=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/candidate/terrain.npz');t=dict(np.load(source));h=t['heights'].astype(float)
plane_path=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy');p=np.load(plane_path)
paths=[Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson'),W/'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson']
reports=[];proof=None
for path in paths:
 for f in json.loads(path.read_text())['features']:
  if f['properties'].get('kind','corridor24m')!='corridor24m':continue
  rec=records(shape(f['geometry']),p);d=depths(h,rec);k=int(d.argmin())
  if proof is None:proof=controls(h,rec)
  bad=d<.95-1e-7
  reports.append(dict(properties=f['properties'],faces=rec['faces'],intersection_vertices=len(d),min_depth_m=float(d[k]),worst_xz=rec['xz'][k].tolist(),failing_faces=int(np.unique(rec['face'][bad]).size)))
roads=evaluate(h,t['water'].astype(bool));(E/'roads-current.json').write_text(json.dumps(roads,indent=2)+'\n')
pmin,pmax=vertex_plane_bounds(p);dry=t['cls']==0;wet=~dry
old=np.load('E:/DayZ-Baltic-Build/v30-global-contour-pass-20261009/candidate-repaired/terrain.npz')['heights']
low=wet&(h<1-1e-6);created=low&~(wet&(old<1-1e-6));new_dry=dry&np.isfinite(pmax)&(h<pmax-1e-5)&~(old<pmax-1e-5)
counts={str(int(k)):int((low&(t['cls']==k)).sum()) for k in np.unique(t['cls'][low])}
report=dict(status='PASS_CURRENT_GEOMETRY' if len(reports)==19 and all(q['failing_faces']==0 for q in reports) and roads['status']=='PASS' and not created.any() and not new_dry.any() else 'FAIL_CURRENT_GEOMETRY',
 corridors=reports,total_faces=sum(q['faces'] for q in reports),min_depth_m=min(q['min_depth_m'] for q in reports),approved_nominal_minimum_m=.95,consumer_controls=proof,
 roads_status=roads['status'],wet_below_1_by_class=counts,new_bed_exceptions=int(created.sum()),new_dry_flood_vertices=int(new_dry.sum()),
 terrain_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),physical_field_sha256=hashlib.sha256(plane_path.read_bytes()).hexdigest(),
 limits=['Nominal corridor depths against the exact deployed physical planes, not reconstructed class planes.','Existing low-water/sea/Narva exceptions retained, not silently declared fixed.','Geometry does not prove crew, whole-network driving, or worst-wave envelope.'])
(E/'geometry-current.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='corridors'},indent=2))
assert report['status']=='PASS_CURRENT_GEOMETRY'
