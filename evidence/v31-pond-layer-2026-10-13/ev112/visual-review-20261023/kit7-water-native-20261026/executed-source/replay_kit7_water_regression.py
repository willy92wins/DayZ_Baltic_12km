"""Reproducible source regression discovery; never starts a native test."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/water'))
from prepare_visual_probe_v31 import triangles,height
from streambed_kit_v31 import tri_h
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
source=R/'runtime-rectangle-f/points.json';surface=R/'river-kit7-midpoint-a-20261026/kit-7-surfaces.npz';before=R/'rectangle-pilot-f-merged/terrain-buried.npz';after=R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz'
out=R/'kit7-regression-replay-20261026.json';assert not out.exists()
inputs={str(p):sha(p) for p in (Path(__file__),source,surface,before,after,W/'tools/water/prepare_visual_probe_v31.py',W/'tools/water/streambed_kit_v31.py')}
points=json.loads(source.read_text(encoding='utf-8'))['points'];assert len(points)==4749
q=np.array([[p['x'],p['z']] for p in points]);a=np.load(before)['heights'];b=np.load(after)['heights'];s=np.load(surface)
old=tri_h(a,q[:,0],q[:,1]);new=tri_h(b,q[:,0],q[:,1]);changed=np.flatnonzero(old!=new)
expected=np.array([p['ground'] for p in points]);drift=np.flatnonzero(abs(new-expected)>1e-5)
bed=triangles(s['bed']);water=triangles(s['water']);v=s['bed'].reshape(-1,3);lo=v[:,[0,2]].min(0);hi=v[:,[0,2]].max(0)
near=np.flatnonzero(((q>=lo-1e-5)&(q<=hi+1e-5)).all(axis=1));overlaps=[]
for i in near:
 by=height(bed,q[i]);wy=height(water,q[i])
 if by is not None or wy is not None:overlaps.append(dict(id=points[i]['id'],bed=by,water=wy))
positive=s['water'][len(s['water'])//2].mean(0)[[0,2]];assert height(bed,positive) is not None and height(water,positive) is not None
negative=lo-100;assert height(bed,negative) is None and height(water,negative) is None
report=dict(status='SOURCE_REGRESSION_REPLAY_PASS' if not len(changed) and not len(drift) and not overlaps else 'FAIL',inherited_points=4749,changed_ground=len(changed),ground_expectation_drift=len(drift),max_expected_numeric_delta_m=float(abs(new-expected).max()),within_new_geometry=len(overlaps),overlaps=overlaps,positive_geometry_control=True,negative_geometry_control=True,inputs=inputs,inputs_unchanged=all(sha(Path(p))==h for p,h in inputs.items()),limits=['Source terrain and saved new geometry only; does not inherit runtime result.'])
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='inputs'},indent=2));raise SystemExit(report['status']!='SOURCE_REGRESSION_REPLAY_PASS')
