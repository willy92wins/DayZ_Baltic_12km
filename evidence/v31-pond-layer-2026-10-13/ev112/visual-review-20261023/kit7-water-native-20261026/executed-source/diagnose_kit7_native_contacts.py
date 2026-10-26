"""Read actual packed geometry and poses at every failing native contact."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/water'),str(W/'tools/playtest'),'C:/temp/moto_lanes/review_g3/tools']
from diagnose_compiled_contact_v31 import classify
from eval_visual_probe_v31 import parse,projected_margin
from attach_navmesh import read_pbo
from odol_reader import ODOL
R0=R/'kit7-water-native-20261026';O=R/'kit7-native-contact-diagnosis-20261026';O.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=read(R0/'full/result.json');assert result['status']=='FAIL' and result['failure_count']==19
points=read(R0/'points.json')['points'];rows=parse((R0/'full/native.log').read_text(),6801)
records=read(R/'stage-kit7-fc-20261026/records.json') if (R/'stage-kit7-fc-20261026/records.json').exists() else None
if records is None:
 records=read(R/'river-kit7-midpoint-a-20261026/records.json')
poses={p['model'].split('\\')[-1]:p for p in records}
pbo=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Native/Addons/baltic_stream_pilot.pbo')
assert sha(pbo)=='46244e7f2abc6bd2d07be828097325ec9bba9c672b48bfcef177895b87380b2d'
_,_,entries=read_pbo(pbo);out=[];targets={}
for failed in result['failures']:
 ident=failed['id'];p=points[ident];m=rows[ident];name=m['bullet_shape'].split('\\')[-1]
 path=R/'pilot-kit7-fc-20261026/temp/baltic_stream_pilot'/name
 assert entries[name]==path.read_bytes()
 od=ODOL.from_file(str(path),strict=True);assert not od.lod_errors
 geo=min(od.lods,key=lambda l:abs(l.resolution-1e13));matrix=poses[name]['matrix']
 assert matrix[:9]==[1,0,0,0,1,0,0,0,1]
 xyz=(np.array([(v.x,v.y,v.z) for v in geo.vertices])+matrix[9:]).astype(np.float32)
 tris=xyz[np.array([f.vertex_indices for f in geo.faces])]
 diagnostic=classify(tris,p['x'],p['z'])
 nearby=[]
 for dx,dz in [(0,0),(.002,0),(-.002,0),(0,.002),(0,-.002),(.01,.01),(-.01,-.01)]:
  nearby.append(dict(offset=[dx,dz],**classify(tris,p['x']+dx,p['z']+dz)))
 out.append(dict(id=ident,model=name,expected=p,rv_height=m['rv_pos'][1],bullet_height=m['bullet_pos'][1],projected_margin_m=projected_margin(m),diagnostic=diagnostic,nearby=nearby,packed_sha256=sha(path)))
 targets.setdefault(name,[]).append(dict(id=ident,x=p['x'],z=p['z']))
report=dict(status='DIAGNOSTIC_ONLY',native_failures=19,results=out,inputs={str(p):sha(p) for p in [Path(__file__),R0/'full/result.json',R0/'full/native.log',R0/'points.json',R/'river-kit7-midpoint-a-20261026/records.json',pbo]},limits=['Float32 packed triangles isolate geometric boundary candidates, not internal RV algorithm or CCT.','No expected points, thresholds, model or world edited.'])
(O/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n');(O/'targets.json').write_text(json.dumps(targets,indent=2)+'\n')
for row in out:print(json.dumps({k:v for k,v in row.items() if k not in ('nearby','expected')}))
