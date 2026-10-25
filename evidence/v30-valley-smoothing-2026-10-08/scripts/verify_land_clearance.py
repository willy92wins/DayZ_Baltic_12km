"""Independent native-face and road-consumer checks for the 1.60 m dry-land control."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008');E=W/'evidence/v30-valley-smoothing-2026-10-08'
sys.path.insert(0,str(W/'tools/terrain'))
from verify_roads_v30 import evaluate
from v30_common import tri_sample
label=sys.argv[1] if len(sys.argv)>1 else 'land160'
assert label in ('land160','land180')
target=1.6 if label=='land160' else 1.8
source=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz');candidate=B/f'candidate-{label}/terrain_valley.npz'
t=dict(np.load(source));u=dict(np.load(candidate));h=t['heights'].astype(float);v=u['heights'].astype(float);wet=t['cls']>0;changed=h!=v
protected=t['reserve']|t['platform']|t['beach']
watertouch=np.zeros(h.shape,bool);badslopes=0
for dr,dc in ((0,1),(1,0)):
 slices=(np.s_[:-1,:-1],np.s_[dr:dr+2047,dc:dc+2047],np.s_[1:,1:])
 water=np.logical_or.reduce([wet[s] for s in slices]);land=np.logical_or.reduce([~wet[s] for s in slices])
 for s in slices:watertouch[s]|=water
 def angle(a):
  p,q,r=[a[s] for s in slices]
  return np.degrees(np.arctan(np.hypot(q-p,r-q)/6.))
 badslopes+=int((land&(angle(v)>np.maximum(angle(h),35)+1e-4)).sum())
roads=evaluate(v,t['water'].astype(bool))
def invariant(a):return dict(protected_exact=not bool(((a!=h)&protected).any()),water_native_faces_exact=not bool(((a!=h)&watertouch).any()),only_raises=not bool((a<h-1e-7).any()),target_points=float(tri_sample(a,2281.835241,7203.550968))>=target-1e-6 and float(tri_sample(a,2534.5868,7037.5396))>=target-1e-6)
checks=invariant(v)
checks.update(metadata_exact=all(np.array_equal(t[k],u[k],equal_nan=True) for k in t if k!='heights'),finite=bool(np.isfinite(v).all()),no_steeper_faces=badslopes==0,roads_pass=roads['status']=='PASS',max_raise_bounded=float((v-h).max())<=target-1.4+.0001)
neg={}
q=v.copy();idx=tuple(np.argwhere(protected)[0]);q[idx]+=1;neg['road_or_platform_change']=not invariant(q)['protected_exact']
q=v.copy();idx=tuple(np.argwhere(watertouch)[0]);q[idx]+=.1;neg['water_face_change']=not invariant(q)['water_native_faces_exact']
q=v.copy();idx=tuple(np.argwhere(~wet&~protected)[0]);q[idx]=h[idx]-.1;neg['new_lowering']=not invariant(q)['only_raises']
neg['unchanged_input_is_not_fix']=not invariant(h)['target_points']
checks['negative_controls']=all(neg.values())
report=dict(status='PASS_OFFLINE_LAND_CLEARANCE' if all(checks.values()) else 'FAIL',checks=checks,negative_controls=neg,changed_vertices=int(changed.sum()),water_support_vertices=int(watertouch.sum()),steep_faces=badslopes,roads=roads,terrain_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),interpreter=sys.executable,limits=['No waterline smoothing claimed; original water geometry and all shoreline faces are exact.','Visual sea-artifact comparison still required; protected low rings may keep patches.'])
(E/f'verification-{label}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='roads'},indent=2))
