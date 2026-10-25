from pathlib import Path
import json,shutil,sys,subprocess,argparse
import numpy as np
B=Path(__file__).parent;OLD=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/playtest')]
from wrp0wzd import read,write
from attach_navmesh import read_pbo
from author_hinges import sha,SOURCE
BASE=Path('P:/Mods/@DayZ_Baltic_AlignedMaskV1/Addons')

def stage():
    result=json.loads((B/'verification.json').read_text());assert result['status']=='PASS_NATIVE_HINGE_SOURCE'
    terrain=B/'candidate/terrain.npz';assert sha(terrain)==result['candidate_sha256']
    src=OLD/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial';dest=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
    assert sha(src/'baltic_trial.wrp')=='770359d0e4f3a37b5a2103db859a562530ee611123c70bce682399108adac0f8'
    a=read(src/'baltic_trial.wrp');h=np.load(SOURCE)['heights'];v=np.load(terrain)['heights'];assert np.array_equal(a['heights'],h[::-1])
    shutil.copytree(src,dest,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
    write(dest/'baltic_trial.wrp',a['header'],v[::-1],a['materials'],[o['bytes'] for o in a['objects']],a['terminator'])
    check=read(dest/'baltic_trial.wrp');assert np.array_equal(check['heights'],v[::-1])
    assert all(a[k]==check[k] for k in ('header','materials','terminator')) and [o['bytes'] for o in a['objects']]==[o['bytes'] for o in check['objects']]
    code=(OLD/'compile_native_world.ps1').read_text().replace(str(OLD).replace('/','\\'),str(B).replace('/','\\'))
    # Read-only junction directly to the already verified source water tree.
    code=code.replace(str(B).replace('/','\\')+'\\package\\water\\temp\\baltic_water_v30',str(OLD).replace('/','\\')+'\\package\\water\\temp\\baltic_water_v30')
    (B/'compile_native_world.ps1').write_text(code)
    result=dict(status='STAGED_NATIVE_HINGE_WORLD',source_wrp_sha256=sha(dest/'baltic_trial.wrp'),terrain_sha256=sha(terrain),objects_exact=True,objects=len(a['objects']),water_cells_exact=True)
    (B/'stage.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

def deploy():
    original=BASE/'narva_trial.pbo';assert sha(original)=='6c9becaa2be8345402eb4863f2c48938860a8a0bb8238ea0acecf31dd8188104'
    _,props,entries=read_pbo(original)
    built=B/'package/world/out/narva_trial.pbo';_,_,compiled=read_pbo(built);wrp=compiled['baltic_trial.wrp'];assert wrp!=entries['baltic_trial.wrp'] and wrp[:4]==b'OPRW'
    dest=B/'distribution/narva_trial';dest.mkdir(parents=True,exist_ok=False)
    for name,data in entries.items():
        path=dest/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(wrp if name=='baltic_trial.wrp' else data)
    out=B/'packed';out.mkdir(exist_ok=False)
    cmd=['C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
    for k,v in props.items():cmd+=['-property',k+'='+v]
    done=subprocess.run(cmd+['-dst',str(out),str(dest)],capture_output=True,text=True);(B/'filebank.log').write_text(done.stdout+'\n'+done.stderr);assert done.returncode==0
    pbo=out/'narva_trial.pbo';_,gotprops,got=read_pbo(pbo);assert gotprops==props and set(got)==set(entries)
    changed=[name for name in entries if entries[name]!=got[name]];assert changed==['baltic_trial.wrp']
    water=BASE/'baltic_water_v30.pbo';assert sha(water)=='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
    target=Path('P:/Mods/@DayZ_Baltic_HingeSmoothV1/Addons');target.mkdir(parents=True,exist_ok=False)
    for src in [pbo,water]:shutil.copyfile(src,target/src.name);assert sha(src)==sha(target/src.name)
    result=dict(status='DEPLOYED_NATIVE_HINGE_PREVIEW',destination=str(target.parent),files={src.name:sha(src) for src in (pbo,water)},terrain_sha256=sha(B/'candidate/terrain.npz'),world_source_sha256=json.loads((B/'stage.json').read_text())['source_wrp_sha256'],compiled_wrp_sha256=__import__('hashlib').sha256(wrp).hexdigest(),baseline_world_sha256=sha(original),changed_world_entries=changed,unchanged_entries=len(entries)-1,limits=['Native full readback and visual review pending.','Water cells and source object records exact; EV23 masks and all other archive entries exact.','Navmesh retained provisionally; must regenerate after final Terrain Builder acceptance.'])
    (B/'deploy.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['stage','deploy']);a=parser.parse_args()
    if a.mode=='stage':stage()
    else:deploy()
