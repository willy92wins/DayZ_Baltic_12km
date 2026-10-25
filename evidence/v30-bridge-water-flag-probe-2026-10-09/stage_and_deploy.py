from pathlib import Path
import sys,json,shutil,hashlib,subprocess,argparse
import numpy as np
B=Path(__file__).parent;OLD=B.parent/'v30-strict-dry-composition-20261009';W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/playtest')]
from wrp0wzd import read,write
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
OMIT={16787374,16787375,16787376};BASE=Path('P:/Mods/@DayZ_Baltic_StrictDryFloorV1/Addons')
def stage():
    src=OLD/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial';dst=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
    assert sha(src/'baltic_trial.wrp')=='931dd215fcb211bf233e18dd4e7fd0ce7a64f772d7294d28abbc5b1a6fbd3107';a=read(src/'baltic_trial.wrp');removed=[o for o in a['objects'] if o['id'] in OMIT];assert len(removed)==3;assert all(o['name']=='dz\\structures\\roads\\bridges\\bridge_metal_25.p3d' for o in removed)
    shutil.copytree(src,dst,ignore=shutil.ignore_patterns('baltic_trial.wrp'));records=[o['bytes'] for o in a['objects'] if o['id'] not in OMIT];write(dst/'baltic_trial.wrp',a['header'],a['heights'],a['materials'],records,a['terminator']);b=read(dst/'baltic_trial.wrp');assert np.array_equal(a['heights'],b['heights']);assert [o['bytes'] for o in b['objects']]==records
    code=(OLD/'compile_native_world.ps1').read_text().replace(str(OLD).replace('/','\\'),str(B).replace('/','\\'));(B/'compile_native_world.ps1').write_text(code)
    report=dict(status='STAGED_DIAGNOSTIC_NO_BRIDGES',omitted=[{k:o[k] for k in ['id','name','matrix']} for o in removed],heights_exact=True,other_objects_exact=True,source_wrp_sha256=sha(dst/'baltic_trial.wrp'),baseline_world_source_sha256=sha(src/'baltic_trial.wrp'));(B/'stage.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
def deploy():
    original=BASE/'narva_trial.pbo';assert sha(original)=='1423f25da029ab0524a9d7861c2fbd1b2cda5f97b2244aa27e2a3fc03e3b5580';_,props,entries=read_pbo(original);_,_,compiled=read_pbo(B/'package/world/out/narva_trial.pbo');wrp=compiled['baltic_trial.wrp'];assert wrp[:4]==b'OPRW';dest=B/'distribution/narva_trial';dest.mkdir(parents=True,exist_ok=False)
    for name,data in entries.items():
        path=dest/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(wrp if name=='baltic_trial.wrp' else data)
    out=B/'packed';out.mkdir(exist_ok=False);cmd=['C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
    for k,v in props.items():cmd+=['-property',k+'='+v]
    done=subprocess.run(cmd+['-dst',str(out),str(dest)],capture_output=True,text=True);(B/'filebank.log').write_text(done.stdout+'\n'+done.stderr);assert done.returncode==0
    pbo=out/'narva_trial.pbo';_,gp,got=read_pbo(pbo);assert gp==props and set(got)==set(entries);changed=[name for name in entries if got[name]!=entries[name]];assert changed==['baltic_trial.wrp']
    water=BASE/'baltic_water_v30.pbo';assert sha(water)=='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14';target=Path('P:/Mods/@BalticBridgeFlagOmissionV1/Addons');target.mkdir(parents=True,exist_ok=False)
    for src in [pbo,water]:shutil.copyfile(src,target/src.name);assert sha(src)==sha(target/src.name)
    report=dict(status='DEPLOYED_DIAGNOSTIC_ONLY',destination=str(target.parent),files={src.name:sha(src) for src in [pbo,water]},terrain_sha256=sha(OLD/'candidate/terrain.npz'),world_source_sha256=json.loads((B/'stage.json').read_text())['source_wrp_sha256'],compiled_wrp_sha256=hashlib.sha256(wrp).hexdigest(),changed_entries=changed,other_entries_exact=len(entries)-1)
    (B/'deploy.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['stage','deploy']);a=parser.parse_args();(stage if a.mode=='stage' else deploy)()
