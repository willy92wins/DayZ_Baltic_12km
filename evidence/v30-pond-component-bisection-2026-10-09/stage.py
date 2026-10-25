from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
import numpy as np
B=Path(__file__).parent;OLD=Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009')
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/playtest')]
from wrp0wzd import read,write
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
BASE=Path('P:/Mods/@DayZ_Baltic_CurrentSurfaceV1/Addons')
EXPECTED={'narva_trial.pbo':'b69265c5feb99d1bda7a5c9f02282818d0ffe4cd26f89f3a095c128e62d374f3','baltic_water_v30.pbo':'3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'}

def stage():
 assert all(sha(BASE/name)==digest for name,digest in EXPECTED.items())
 src=OLD/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial';dst=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
 assert sha(src/'baltic_trial.wrp')=='a845bee973c2db1c94acf39758358dfcfb5967770e3879263ecf1a1bc4f66fd2'
 cohort=json.loads(Path('E:/DayZ-Baltic-Build/v30-low-water-components-20261009/cohort.json').read_text());ids={r['id']:r for r in cohort['objects']}
 assert set(ids)=={16800387,16800388,16800454,16800455}
 a=read(src/'baltic_trial.wrp');removed=[];remaining=[]
 for obj in a['objects']:
  if obj['id'] in ids:
   target=ids[obj['id']];assert obj['name'].replace('\\','/').split('/')[-1]==target['model'] and obj['matrix'][9:]==target['position'];removed.append(obj)
  else:remaining.append(obj)
 assert len(removed)==4
 shutil.copytree(src,dst,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
 write(dst/'baltic_trial.wrp',a['header'],a['heights'],a['materials'],[o['bytes'] for o in remaining],a['terminator'])
 got=read(dst/'baltic_trial.wrp');assert np.array_equal(a['heights'],got['heights']);assert all(a[k]==got[k] for k in ('header','materials','terminator'));assert [o['bytes'] for o in got['objects']]==[o['bytes'] for o in remaining]
 code=(OLD/'compile_native_world.ps1').read_text().replace(str(OLD).replace('/','\\'),str(B).replace('/','\\'));(B/'compile_native_world.ps1').write_text(code)
 report=dict(status='STAGED_DIAGNOSTIC_REMOVAL_ONLY',source_wrp_sha256=sha(src/'baltic_trial.wrp'),diagnostic_source_wrp_sha256=sha(dst/'baltic_trial.wrp'),removed=[dict(id=o['id'],model=o['name'],matrix=o['matrix']) for o in removed],before_objects=len(a['objects']),after_objects=len(got['objects']),height_bytes_exact=True,remaining_object_bytes_exact=True,all_other_world_fields_exact=True,baseline=EXPECTED)
 (B/'stage.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

def deploy():
 assert all(sha(BASE/name)==digest for name,digest in EXPECTED.items())
 original=BASE/'narva_trial.pbo';_,props,entries=read_pbo(original);_,_,built=read_pbo(B/'package/world/out/narva_trial.pbo');wrp=built['baltic_trial.wrp'];assert wrp[:4]==b'OPRW'
 dest=B/'distribution/narva_trial';dest.mkdir(parents=True,exist_ok=False)
 for name,data in entries.items():
  path=dest/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(wrp if name=='baltic_trial.wrp' else data)
 out=B/'packed';out.mkdir(exist_ok=False);cmd=['C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
 for k,v in props.items():cmd+=['-property',k+'='+v]
 done=subprocess.run(cmd+['-dst',str(out),str(dest)],capture_output=True,text=True);(B/'filebank.log').write_text(done.stdout+'\n'+done.stderr);assert done.returncode==0
 packed=out/'narva_trial.pbo';_,newprops,got=read_pbo(packed);assert props==newprops and set(got)==set(entries);changed=[name for name in entries if entries[name]!=got[name]];assert changed==['baltic_trial.wrp']
 water=BASE/'baltic_water_v30.pbo';target=Path('P:/Mods/@DayZ_Baltic_PondOmissionProbeV1/Addons');target.mkdir(parents=True,exist_ok=False)
 for path in (packed,water):shutil.copyfile(path,target/path.name);assert sha(path)==sha(target/path.name)
 report=dict(status='DEPLOYED_DIAGNOSTIC_ONLY_NOT_A_FIX',destination=str(target.parent),files={path.name:sha(path) for path in (packed,water)},changed_world_entries=changed,unchanged_world_entries=len(entries)-1,compiled_wrp_sha256=hashlib.sha256(wrp).hexdigest(),removed_objects=[16800387,16800388,16800454,16800455],baseline=EXPECTED)
 (B/'deploy.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['stage','deploy']);args=parser.parse_args();stage() if args.mode=='stage' else deploy()
