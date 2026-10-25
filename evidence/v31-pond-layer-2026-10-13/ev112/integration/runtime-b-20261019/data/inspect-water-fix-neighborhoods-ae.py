from pathlib import Path
import numpy as np,json,sys
O=Path(__file__).parent;P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');sys.path.insert(0,str(P/'tools/water'));import streambed_kit_v31 as kit
a=np.load(O/'terrain-ev112-c.npz');fp=np.load(O/'fp-ev112-c/footprint.npz');print('TERRAIN_KEYS',a.files);print('FOOTPRINT_KEYS',fp.files)
ps={p['id']:p for p in json.loads((O/'probe-c/points.json').read_text())};out=[]
for pid in (3837,):
 p=ps[pid];rr,cc,ww=kit.tri_weights(np.array([[p['x'],p['z']]]));vs=[]
 for r,c,w in zip(rr[0],cc[0],ww[0]):
  masks={k:float(a[k][r,c]) for k in a.files if a[k].shape==(2048,2048) and k!='heights' and a[k][r,c]!=0}
  vs.append(dict(r=int(r),c=int(c),x=int(c)*6,z=12282-int(r)*6,w=float(w),h=float(a['heights'][r,c]),masks=masks,patch=a['heights'][r-1:r+2,c-1:c+2].tolist()))
 out.append(dict(id=pid,kind=p['kind'],vertices=vs))
(O/'water-temporal-ae/dry-neighborhood.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
