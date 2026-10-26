"""Replace only nineteen ODOL entries; prove all decoded non-Geometry content exact."""
from pathlib import Path
import hashlib,json,subprocess,sys
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/playtest'),'C:/temp/moto_lanes/review_g3/tools']
from attach_navmesh import read_pbo
from odol_reader import ODOL
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
B=R/'river-kit7-contact-only-20261026';O=R/'package-kit7-contact-only-20261026'
assert read(B/'compiled-contact-review.json')['status']=='PACKED_KIT7_OVERLAP_CONTACT_PASS'
frozen=read(R/'kit7-contact-only-build-20261026/inputs.json')
assert all(sha(Path(p))==h for p,h in frozen.items())
base=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Native/Addons/baltic_stream_pilot.pbo')
assert sha(base)=='46244e7f2abc6bd2d07be828097325ec9bba9c672b48bfcef177895b87380b2d'
candidate=B/'packed/baltic_stream_pilot.pbo';binary=read(B/'binary-review.json')
assert binary['status']=='BINARY_PASS' and sha(candidate)==binary['pbo_sha256']
names=set(read(R/'kit7-native-contact-diagnosis-20261026/targets.json'))
assert len(names)==19
_,props,old=read_pbo(base);_,candidate_props,new=read_pbo(candidate);assert props==candidate_props
assert len([n for n in old if n.endswith('.p3d')])==201 and names<=set(new)<=set(old)
assert read(B/'records.json')==read(R/'river-kit7-midpoint-a-20261026/records.json')
# Everything decoded, including opaque streams retained as bytes, is compared;
# only physical file offsets differ when Geometry length changes.
def normalized(x):
 if x is None or isinstance(x,(str,int,float,bool)):return x
 if isinstance(x,bytes):return {'bytes_hex':x.hex()}
 if isinstance(x,(list,tuple)):return [normalized(v) for v in x]
 if isinstance(x,dict):return {str(k):normalized(v) for k,v in x.items()}
 if hasattr(x,'__dict__'):return {k:normalized(v) for k,v in vars(x).items() if k not in ('declared_end','parsed_end')}
 if hasattr(x,'__slots__'):return {k:normalized(getattr(x,k)) for k in x.__slots__ if hasattr(x,k)}
 raise TypeError(type(x))
rows=[]
for name in sorted(names):
 a=R/'pilot-kit7-fc-20261026/temp/baltic_stream_pilot'/name;b=B/'temp/baltic_stream_pilot'/name
 assert a.read_bytes()==old[name] and b.read_bytes()==new[name]
 before=ODOL.from_file(str(a),strict=True);after=ODOL.from_file(str(b),strict=True)
 assert not before.lod_errors and not after.lod_errors and len(before.lods)==len(after.lods)==4
 assert normalized(before.model_info.bounding_center)==normalized(after.model_info.bounding_center)
 nongeo=[]
 for al,bl in zip(before.lods,after.lods):
  assert al.resolution==bl.resolution
  if abs(al.resolution-1e13)/1e13<1e-4:continue
  assert normalized(al)==normalized(bl),('Decoded non-Geometry changed',name,al.resolution)
  nongeo.append(al.resolution)
 assert len(nongeo)==3
 rows.append(dict(model=name,non_geometry_decoded_exact=True,bounding_centre_exact=True,non_geometry_lods=nongeo,before_sha256=sha(a),after_sha256=sha(b)))
expected={**old,**{n:new[n] for n in names}};changed={n for n in old if old[n]!=expected[n]};assert changed==names
O.mkdir(exist_ok=False);folder=O/'compiled/baltic_stream_pilot';folder.mkdir(parents=True);dest=O/'Addons';dest.mkdir()
for n,data in expected.items():
 p=folder/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
args=['C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
for k,v in props.items():args+=['-property',k+'='+v]
q=subprocess.run(args+['-dst',str(dest),str(folder)],capture_output=True,timeout=120,creationflags=0x08000000)
(O/'filebank.log').write_bytes(q.stdout+q.stderr);assert q.returncode==0
pbo=dest/'baltic_stream_pilot.pbo';_,actual_props,actual=read_pbo(pbo);assert actual_props==props and actual==expected
report=dict(status='NINETEEN_GEOMETRY_DELTA_PACKAGE_PASS',pbo_sha256=sha(pbo),baseline_sha256=sha(base),changed_entries=sorted(changed),other_model_entries_exact=182,config_exact=actual['config.bin']==old['config.bin'],all_139_poses_exact=True,models=rows,inputs={str(p):sha(p) for p in [Path(__file__),base,candidate,B/'compiled-contact-review.json',B/'binary-review.json',B/'records.json']},limits=['Native result pending; decoded binary exactness excludes file offsets only.','No world, terrain, vegetation, water or WRP change.'])
report['inputs'].update(frozen)
report['inputs'][str(R/'verify_kit7_contact_only_compiled.py')]=sha(R/'verify_kit7_contact_only_compiled.py')
(O/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('models','inputs')},indent=2))

