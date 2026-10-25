"""Recheck the already generated candidate after a precision-control correction.
No solve, candidate rewrite or threshold change.
"""
from pathlib import Path
import sys
import numpy as np
import json
from shapely.geometry import shape
R=Path('P:/DayZ_Baltic_12km_dev')
E=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'tools/terrain'))
from audit_fairway_triangles_v30 import records,describe,controls,sha,save
from v30_common import cell_planes

source=R/'tests/terrain_v30/terrain_v30.npz'
path=Path('E:/DayZ-Baltic-Build/v30-fairway-candidate-bounded/terrain_v30.npz')
base=np.load(source);t=np.load(path)
h=t['heights'];old=base['heights'].astype(float)
delta=old-h
changed=np.flatnonzero(delta.ravel()!=0)
mutable=base['water']&~base['platform']&~base['narva']
assert len(changed)>0 and np.all(mutable.ravel()[changed])
assert delta.min()>=0 and delta.max()<=1.550001 and h.min()>=-12.000001
assert all(np.array_equal(t[k],base[k],equal_nan=True) for k in base.files if k!='heights')
planes=cell_planes(t['cls'],t['level'].astype(float))
features=json.loads((E/'corridors.geojson').read_text())['features']
after={};checks={}
for f in features:
 name=f['properties']['river'];rec=records(shape(f['geometry']),planes)
 after[name]=describe(h,rec);checks[name]=controls(h,rec)
assert all(r['failing_faces']==0 for r in after.values())
out=dict(status='OFFLINE_CANDIDATE_NOT_DEPLOYED',file=str(path),sha256=sha(path),
 source_sha256=sha(source),vertices_changed=len(changed),max_lowering_m=float(delta.max()),
 invariants=dict(all_non_height_arrays_identical=True,only_water_not_road_or_narva=True,
                 dry_vertices_identical=True,all_heights_nonincreasing=True),
 changes=[dict(row=int(i//2048),col=int(i%2048),x=float(i%2048*6),z=float(12282-i//2048*6),
               before=float(old.ravel()[i]),after=float(h.ravel()[i])) for i in changed],
 rivers=after,controls=checks,verifier_sha256=sha(R/'tools/terrain/audit_fairway_triangles_v30.py'))
save(E/'candidate.json',out)
print(json.dumps({k:out[k] for k in ['status','vertices_changed','max_lowering_m','sha256']}))
print('Luga',after['Luga_0'])
