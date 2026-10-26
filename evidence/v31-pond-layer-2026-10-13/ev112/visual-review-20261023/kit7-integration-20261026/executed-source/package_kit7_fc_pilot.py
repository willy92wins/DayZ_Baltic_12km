"""Combine exact C62 and kit7-139 ODOL entries, extending only house config."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(R),str(W/'tools/playtest'),str(W/'tools/water')]
from check_kit7_stage_inputs import validate
from attach_navmesh import read_pbo
from continuous_stream_pilot_v31 import model_config
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def config_parts(text):
 # Actual flat terrain-house config only; reject duplicate class/model declarations.
 pattern=r'class\s+(Land_\w+)\s*:\s*HouseNoDestruct\s*\{\s*scope\s*=\s*1\s*;\s*model\s*=\s*"([^"\n]+)"\s*;\s*\};'
 found=re.findall(pattern,text); assert found and len(found)==len(dict(found))
 residual=re.sub(r'\s+','',re.sub(pattern,'',text))
 assert residual.count('classHouseNoDestruct;')==1 and 'Land_' not in residual
 assert len({model.lower() for _,model in found})==len(found)
 return dict(found),residual
def main():
 P=R/'pilot-kit7-fc-20261026'; K=R/'river-kit7-midpoint-a-20261026'; O=R/'package-kit7-fc-pilot-20261026'
 assert read(R/'stage-kit7-fc-20261026/independent-source-review.json')['status']=='PASS_INDEPENDENT_SOURCE_COMPOSITION'
 assert read(R/'kit7-package-review-20261026/accepted.json')['status']=='ACCEPTED_PILOT_COMPOSITION_ONLY'
 gate=read(R/'kit7-package-review-20261026/accepted.json')
 required=[Path(__file__),W/'tools/water/continuous_stream_pilot_v31.py',W/'tools/playtest/attach_navmesh.py',P/'author-report.json',R/'kit7-stage-review-20261026/accepted.json',R/'stage-kit7-fc-20261026/independent-source-review.json',R/'package-midpoint-c/Addons/baltic_stream_pilot.pbo',K/'packed/baltic_stream_pilot.pbo']
 assert all(Path(p).is_absolute() for p in gate['inputs'])
 assert {str(p) for p in required}<=set(gate['inputs']),'incomplete package manifest'
 assert all(sha(p)==h for p,h in gate['inputs'].items())
 validate(read(R/'kit7-stage-review-20261026/accepted.json'))
 base=R/'package-midpoint-c/Addons/baltic_stream_pilot.pbo'; kit=K/'packed/baltic_stream_pilot.pbo'
 assert sha(base)=='c7dc430d809bcec2f29ff1fe86f266f0f9680b8ad676a8722b0b45d4494de02f'
 assert sha(kit)=='1f27e9d3ed05036fd359b49c9fa30a5665c8056cc1f85585b63ff278852d7a8e'
 _,props,old=read_pbo(base);_,kp,new=read_pbo(kit);assert props==kp and props['prefix']=='baltic_stream_pilot'
 oldmodels={n:d for n,d in old.items() if n.endswith('.p3d')};newmodels={n:d for n,d in new.items() if n.endswith('.p3d')}
 assert len(oldmodels)==62 and len(newmodels)==139 and not set(oldmodels)&set(newmodels)
 assert set(new)-set(newmodels)=={'config.bin'} and set(old)-set(oldmodels)=={'config.bin'}
 author=read(P/'author-report.json'); assert {i['model'].split('\\')[-1] for i in author['instances']}==set(oldmodels)|set(newmodels)
 cv=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe')
 fb=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe');assert cv.is_file() and fb.is_file()
 O.mkdir(exist_ok=False);(O/'old-config.bin').write_bytes(old['config.bin'])
 def call(args,log):
  p=subprocess.run([str(x) for x in args],capture_output=True,timeout=120,creationflags=0x08000000);(O/log).write_bytes(p.stdout+p.stderr);assert p.returncode==0
 call([cv,'-txt','-dst',O/'old-config.cpp',O/'old-config.bin'],'decode-old.log')
 cpp=model_config(author['instances']);(O/'config.cpp').write_text(cpp,encoding='ascii')
 call([cv,'-bin','-dst',O/'config.bin',O/'config.cpp'],'compile-config.log')
 call([cv,'-txt','-dst',O/'decoded.cpp',O/'config.bin'],'decode-new.log')
 oc,orr=config_parts((O/'old-config.cpp').read_text(encoding='utf-8-sig')); nc,nrr=config_parts((O/'decoded.cpp').read_text(encoding='utf-8-sig'))
 assert len(oc)==62 and len(nc)==201 and orr==nrr and all(nc.get(k)==v for k,v in oc.items())
 expectclasses={'Land_'+n[:-4]:'\\baltic_stream_pilot\\'+n for n in newmodels}
 assert {k:v for k,v in nc.items() if k not in oc}==expectclasses
 expected={**old,**newmodels,'config.bin':(O/'config.bin').read_bytes()}
 folder=O/'compiled/baltic_stream_pilot';folder.mkdir(parents=True);dest=O/'Addons';dest.mkdir()
 for name,data in expected.items():
  target=folder/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 args=[fb]
 for k,v in props.items():args+=['-property',k+'='+v]
 call(args+['-dst',dest,folder],'filebank.log')
 packed=dest/'baltic_stream_pilot.pbo';_,actualprops,actual=read_pbo(packed);assert actualprops==props and actual==expected
 assert all(actual[n]==v for n,v in oldmodels.items()) and all(actual[n]==v for n,v in newmodels.items())
 assert all(sha(p)==h for p,h in gate['inputs'].items())
 report=dict(status='PASS_201_MODELS_BYTE_EXACT_CONFIG_EXTENDED',pbo_sha256=sha(packed),preserved_C_models=62,added_kit7_models=139,total_models=201,old_classes_exact=62,added_house_classes=139,other_config_semantics_exact=True,pbo_properties_exact=True,inputs_unchanged=True,models={n:hashlib.sha256(v).hexdigest() for n,v in actual.items() if n.endswith('.p3d')},limits=['Isolated pilot PBO only. Compiled world placement, native water/collision/navigation and client remain pending.'])
 write(O/'verification.json',report);print(json.dumps({k:v for k,v in report.items() if k!='models'},indent=2))
if __name__=='__main__':main()
