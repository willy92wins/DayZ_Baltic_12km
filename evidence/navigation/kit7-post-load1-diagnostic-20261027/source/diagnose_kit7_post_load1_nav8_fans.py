"""Compare archived local Nav8 polygon geometry with six already captured engine points."""
from pathlib import Path
import json,hashlib,datetime,re
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');A=W/'evidence/navigation/kit7-nav12-rejected-20261027';N=W/'evidence/navigation/kit7-nav8load1-native-20261027';O=R/'kit7-post-load1-nav8-fans-20261027';O.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
budget=read(R/'kit7-post-load1-vertex-surfaces-20261027/budget.json');assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(budget['deadline_utc'])
gridpath=A/'diagnostics/kit7-grid-vertex-diagnostic-20261027.json';native12path=A/'diagnostics/kit7-nav12-height-diagnostic-20261027.json';logpath=N/'runtime.log'
for base,path in [(A,gridpath),(A,native12path),(N,logpath)]:assert sha(path)==read(base/'MANIFEST.json')[path.relative_to(base).as_posix()]['sha256']
grid=read(gridpath);native12=read(native12path);navs=[n for n in grid['navmeshes'] if n['label']=='8m'];assert len(navs)==1 and navs[0]['sha256']=='360a7348b86bb9560352f2aead028fb6ec801f8d3bdd30526f43e0cb7e9efb23'
triangles=[];seen=set()
for tile in navs[0]['tiles']:
 tx,tz=tile['tile'];assert (tx,tz) not in seen;seen.add((tx,tz));v=np.array(tile['vertices']);assert np.isfinite(v).all() and v.ndim==2 and v.shape[1]==3
 assert (v[:,0]>=tx*8-1e-4).all() and (v[:,0]<=(tx+1)*8+1e-4).all() and (v[:,2]>=tz*8-1e-4).all() and (v[:,2]<=(tz+1)*8+1e-4).all()
 known={tuple(q) for q in tile['vertices']}
 for pi,poly in enumerate(tile['polygons']):
  assert 3<=len(poly)<=6 and len({tuple(q) for q in poly})==len(poly) and all(tuple(q) in known for q in poly)
  for i in range(1,len(poly)-1):triangles.append(dict(tile=tile['tile'],polygon=pi,vertices=[poly[0],poly[i],poly[i+1]]))
def reconstruct(x,z):
 hits=[]
 for tr in triangles:
  t=np.array(tr['vertices']);m=np.vstack([t[:,[0,2]].T,np.ones(3)])
  if abs(np.linalg.det(m))<1e-10:continue
  weights=np.linalg.solve(m,[x,z,1])
  if min(weights)<-1e-7:continue
  hits.append(dict(**tr,weights=weights.tolist(),height=float(np.dot(weights,t[:,1]))))
 return max(hits,key=lambda h:h['height']) if hits else None,len(hits)
# Literal arithmetic controls, independent of captured values.
t=np.array([[0.,0.,0.],[1.,2.,0.],[0.,1.,1.]]);v=np.linalg.solve(np.vstack([t[:,[0,2]].T,np.ones(3)]),[.25,.25,1]);assert np.allclose(v,[.5,.25,.25])
def vector(v):
 assert v.startswith('<') and v.endswith('>');q=[float(s.strip()) for s in v[1:-1].split(',')];assert len(q)==3 and np.isfinite(q).all();return q
native8={}
for line in logpath.read_text(encoding='utf-8-sig').splitlines():
 f=line.split(';')
 if f[0]=='P' and f[1] in {s['query'] for s in native12['samples']}:
  key=(f[1],int(f[2]));assert key not in native8;native8[key]=dict(nav=vector(f[3]),terrain=vector(f[4]),road=vector(f[5]))
assert len(native8)==6
rows=[]
for old in native12['samples']:
 key=(old['query'],old['index']);new=native8[key];assert new['nav'][::2]==old['nav'][::2] and new['road']==old['engine_roadway']
 hit,count=reconstruct(new['nav'][0],new['nav'][2]);assert hit is not None
 residual=hit['height']-new['nav'][1];assert abs(residual)<1e-6
 rows.append(dict(query=key[0],index=key[1],xz=new['nav'][::2],same_native_xz=True,native8_y=new['nav'][1],native12_y=old['nav'][1],engine_surface_y=new['road'][1],error8_m=abs(new['nav'][1]-new['road'][1]),error12_m=abs(old['nav'][1]-old['engine_roadway'][1]),reconstruction8_residual_m=residual,candidate_triangles=count,selected=hit))
result=dict(status='LOCAL_NAV8_FAN_NATIVE_MATCH',acceptance_eligible=False,samples=rows,archived_tiles=len(seen),max_residual_m=max(abs(r['reconstruction8_residual_m']) for r in rows),inputs={str(p):sha(p) for p in [Path(__file__),gridpath,native12path,logpath,R/'kit7-post-load1-vertex-surfaces-20261027/budget.json']},limits=['No NM binary decoded or written; consumes only already archived empirical local polygon geometry.','Finite vertices, tile XY bounds, membership and polygon cardinality checked; not a proof of VAND12 format or full coverage.','Six independently captured Nav8 engine points match at identical XZ and surface Y to Nav12.','Does not isolate generator algorithm, predict other grids, provide RAM acceptance or authorize a new candidate.'])
(O/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');(O/'completion.json').write_text(json.dumps(dict(returncode=0,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),dayz_runs=0,binary_decodes=0,inputs_unchanged=all(sha(Path(p))==h for p,h in result['inputs'].items())),indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['inputs','samples']},indent=2));print(json.dumps([{k:v for k,v in r.items() if k!='selected'} for r in rows],indent=2))
