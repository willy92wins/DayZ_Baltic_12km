from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.spatial import cKDTree
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/water'))
from review_compact_collision_v31 import load
P=R/'river-kit7-midpoint-a-20261026';T=R/'kit7-native-contact-diagnosis-20261026/targets.json'
targets=json.loads(T.read_text());q=[dict(model=n,**p) for n,ps in targets.items() for p in ps]
xy=np.array([[p['x'],p['z']] for p in q]);hits=[];inputs={str(T):hashlib.sha256(T.read_bytes()).hexdigest()}
for i in json.loads((P/'author-report.json').read_text())['instances']:
 path=P/'source'/i['model'].replace('\\','/');raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==i['sha256'];inputs[str(path)]=i['sha256']
 _,lods,_=load(path);xyz=(np.array([p.coords for p in lods[1].points])+i['origin']).astype(np.float32).astype(float)
 distances=cKDTree(xyz[:,[0,2]]).query(xy)[0]
 for p,dist in zip(q,distances):
  if dist<=1/512 and i['model'].split('\\')[-1]!=p['model']:hits.append(dict(target=p,neighbour=i['model'],distance_m=float(dist)))
out=dict(status='NO_NEIGHBOUR_VERTEX_CONFLICT' if not hits else 'NEIGHBOUR_CONTACTS_REQUIRE_DESIGN',targets=len(q),models=139,neighbour_hits=hits,inputs=inputs)
(R/'kit7-native-contact-diagnosis-20261026/neighbours.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='inputs'},indent=2))
