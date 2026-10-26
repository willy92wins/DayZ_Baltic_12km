"""Read-only discovery of fixed kit7 controls against the composed water world.

Writes a fresh report, never changes expectations, missions or deployed content.
"""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/vegetation'),str(W/'tools/water'),str(W/'evidence/v31-pond-layer-2026-10-13/ev112/ot1/gates'),'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d']
from prune_visual_forest_v31 import prefix,objects
from prepare_visual_probe_v31 import triangles,height
import gatelib as K
import py3d
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'kit7-water-controls-discovery-20261026.json';assert not out.exists()
P=R/'pilot-kit7-fc-20261026';S=R/'stage-kit7-fc-20261026';M=R/'river-kit7-merged-byteexact-20261026'
wrp=S/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';author=read(P/'author-report.json');source=R/'probe-kit7-prepared-20261026/points.json'
doc=read(source);pts=[p for p in doc['points'] if p.get('site')=='kit-7'];assert len(pts)==1655
q=np.array([[p['x'],p['z']] for p in pts]);H=np.load(M/'terrain-buried.npz')['heights'].astype(float);fp=np.load(M/'bury-work/fp0/footprint.npz')
ground=K.terrain_y(H,q[:,0],q[:,1]);rows=np.floor((12282-q[:,1])/6).astype(int);cols=np.floor(q[:,0]/6).astype(int)
pond=fp['plane'][rows,cols];native_wet=(np.isfinite(pond)&(pond>ground))|(ground<.75)
paths=[Path(__file__),source,P/'author-report.json',wrp,M/'terrain-buried.npz',M/'bury-work/fp0/footprint.npz',Path(K.__file__),Path(K.GEOM),W/'tools/vegetation/prune_visual_forest_v31.py',W/'tools/water/prepare_visual_probe_v31.py',Path(py3d.__file__)]
inputs={str(p):sha(p) for p in paths};geometry=read(Path(K.GEOM))['models'];pieces=[];total=0
with wrp.open('rb') as f:
 prefix(f)
 for ident,name,raw in objects(f):
  total+=1
  if '\\streambed\\streambed_' in name and 'stones' not in name:pieces.append(K.Piece(dict(model=name,matrix=list(struct.unpack_from('<12f',raw))),geometry))
assert total==2578398
vanilla=K.surface(pieces,q,'road_ext');custom=np.full(len(q),-np.inf);bed=np.full(len(q),-np.inf);model_hits={}
for inst in author['instances']:
 p=P/'source'/inst['model'].replace('\\','/');assert sha(p)==inst['sha256'];inputs[str(p)]=inst['sha256']
 with p.open('rb') as f:
  assert struct.unpack('<4s2I',f.read(12))==(b'MLOD',257,4);lod=py3d.LOD(f)
 v=np.array([x.coords for x in lod.points])+inst['origin'];lo=v[:,[0,2]].min(0);hi=v[:,[0,2]].max(0)
 ix=np.flatnonzero(((q>=lo-.00001)&(q<=hi+.00001)).all(axis=1))
 if not len(ix):continue
 wet=[];dry=[]
 for face in lod.faces:
  a=v[[x.point_index for x in face.vertices]];assert len(a)==3
  (wet if 'water_streambed' in face.material else dry).append(a)
 wy=K.tri_max(np.array(wet),q[ix],np.full(len(ix),-np.inf))-.25
 by=K.tri_max(np.array(dry),q[ix],np.full(len(ix),-np.inf))
 custom[ix]=np.maximum(custom[ix],wy);bed[ix]=np.maximum(bed[ix],by)
 model_hits[inst['model']]=[pts[int(i)]['id'] for i,h in zip(ix,wy) if np.isfinite(h)]
expected=np.array([p['expect'] for p in pts]);all_water=np.maximum(custom,vanilla);wet_global=native_wet|(all_water>ground)
dry_conflicts=np.flatnonzero((expected=='dry')&wet_global)
wet_missing=np.flatnonzero((expected=='wet')&~wet_global)
height_drift=np.flatnonzero(abs(ground-np.array([p['ground'] for p in pts]))>1e-5)
bed_drift=np.flatnonzero(abs(bed-np.array([p['bed'] for p in pts]))>1e-4)
wet_ids=np.flatnonzero(expected=='wet');wet_level_drift=wet_ids[abs(all_water[wet_ids]-np.array([pts[i]['water_ext'] for i in wet_ids]))>1e-4]
def records(ix):
 return [dict(id=pts[i]['id'],kind=pts[i]['kind'],xz=q[i].tolist(),ground=float(ground[i]),native_pond=None if not np.isfinite(pond[i]) else float(pond[i]),vanilla=None if not np.isfinite(vanilla[i]) else float(vanilla[i]),custom=None if not np.isfinite(custom[i]) else float(custom[i])) for i in ix]
# Prove the actual authored intervals are covered, not merely a total point count.
kit=[i for i in author['instances'] if i['site']=='kit-7'];assert len(kit)==139
uncovered=[i['model'] for i in kit if not model_hits.get(i['model'])]
surface=R/'river-kit7-midpoint-a-20261026/kit-7-surfaces.npz';inputs[str(surface)]=sha(surface);z=np.load(surface)
seamq=np.array([[p['x'],p['z']] for p in pts if p['kind']=='chunk_seam']);joint_results=[]
for left,right in zip(kit,kit[1:]):
 assert abs(left['station'][1]-right['station'][0])<1e-9
 st=left['station'][1];wanted=np.array([[np.interp(st+d,z['station'],z['axis'][:,dim]) for dim in (0,1)] for d in (-.05,0,.05)])
 err=np.min(np.linalg.norm(seamq[:,None]-wanted[None],axis=2),axis=0)
 joint_results.append(dict(left=left['model'],right=right['model'],max_coordinate_error_m=float(err.max())))
report=dict(status='DISCOVERY_ONLY_NO_RUNTIME_AUTHORIZATION',points=len(pts),dry_controls=int((expected=='dry').sum()),retained_vanilla_pieces=len(pieces),custom_models=len(author['instances']),dry_conflicts=records(dry_conflicts),wet_missing=records(wet_missing),ground_expectation_drift=records(height_drift),bed_expectation_drift=records(bed_drift),water_level_drift=records(wet_level_drift),models_without_wet_query=uncovered,kit_models=139,joints=len(joint_results),joint_coordinate_max_m=max(x['max_coordinate_error_m'] for x in joint_results),joint_results=joint_results,inputs=inputs,inputs_unchanged=all(sha(Path(p))==h for p,h in inputs.items()),limits=['Source geometry discovery, no engine water/collision claim.','Native ponds and conservative .75m sea band; retained vanilla water_ext and every custom model included.','Contact extrema and combined manifest/fresh calibration still pending.'])
out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('inputs','joint_results')},indent=2))
