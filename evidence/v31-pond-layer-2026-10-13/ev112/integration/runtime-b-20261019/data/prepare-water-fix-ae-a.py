"""Isolated six-vertex physical margin candidate; never deploys or changes acceptance."""
from pathlib import Path
import numpy as np,json,sys,hashlib,subprocess,time
O=Path(__file__).parent;P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=O/'water-fix-a';D.mkdir(exist_ok=False)
sys.path.insert(0,str(P/'tools/water'));import shore_ramp_v31 as sr
sys.path.insert(0,str(P/'tools/terrain'));from v30_common import tri_sample
source=O/'terrain-ev112-c.npz';a=dict(np.load(source));old=a['heights'];h=old.copy()
patch=[(796,1721,1.72),(963,1876,1.90),(631,1685,1.65),(323,1134,float(h[323,1134])-.16),(324,1134,float(h[324,1134])-.16),(324,1135,float(h[324,1135])-.16)]
entries=[]
f=np.load(O/'fp-ev112-c/footprint.npz');W,covered=sr.corner_water(f['plane'],f['field'])
for r,c,target in patch:
 assert not any(a[k][r,c] for k in ('reserve','platform','narva','v31_bridge_cut','v31_bridge_fill','v31_dam','v31_lagoon'))
 assert np.hypot(c*6-10397.4,12282-r*6-9421.9)>60
 corners=[]
 for k,(dr,dc) in enumerate(sr.COFF):
  cr,cl=r-dr,c-dc
  water=float(W[cr,cl,k]);assert np.isfinite(water)
  corners.append(dict(cell=[cr,cl],water=water,before_wet=bool(old[r,c]<water),after_wet=bool(target<water)))
 h[r,c]=target;entries.append(dict(row=r,col=c,before=float(old[r,c]),after=float(h[r,c]),incident_corners=corners))
a['heights']=h;np.savez_compressed(D/'terrain.npz',**a)
points=json.loads((O/'probe-c/points.json').read_text());xs=[p['x'] for p in points];zs=[p['z'] for p in points];before=tri_sample(old,xs,zs);after=tri_sample(h,xs,zs)
changes=[dict(id=p['id'],family_id=p['family_id'],family=p['family'],kind=p['kind'],before=float(b),after=float(v)) for p,b,v in zip(points,before,after) if abs(b-v)>1e-6]
out=dict(status='EXPERIMENTAL_NOT_ACCEPTED',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),terrain_sha256=hashlib.sha256((D/'terrain.npz').read_bytes()).hexdigest(),patch=entries,unchanged_incident_water_signs=all(q['before_wet']==q['after_wet'] for e in entries for q in e['incident_corners']),probe_height_changes=changes,scope='Six mutable vertices only; no masks, footprint, records, production source or PBO changed. Margins are provisional and must pass all affected consumers and runtime.')
(D/'candidate.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
