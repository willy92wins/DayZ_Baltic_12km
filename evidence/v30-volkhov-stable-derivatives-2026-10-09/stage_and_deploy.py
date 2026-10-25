from pathlib import Path
import json,shutil,sys,subprocess,argparse,hashlib
import numpy as np
B=Path(__file__).parent;OLD=B.parent/'v30-isolated-basin-repair-20261009'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/playtest')]
from wrp0wzd import read,write
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
BASE=Path('P:/Mods/@DayZ_Baltic_IsolatedBasinsV1/Addons')
def stage():
    assert json.loads((B/'verification.json').read_text())['status']=='PASS_INDEPENDENT_GEOMETRY'
    msta=B.parent/'v30-msta-dry-bank-solve-20261009'
    assert json.loads((msta/'verification.json').read_text())['status']=='INDEPENDENT_GEOMETRY_PASS'
    src=OLD/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial';dest=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
    assert sha(src/'baltic_trial.wrp')=='6c056a61402356aa0f48b04c528e5c696ef17ba6b7eeb42308a62f9942d52f91'
    a=read(src/'baltic_trial.wrp');h=np.load(OLD/'candidate/terrain.npz')['heights'];v=np.load(B/'candidate/terrain.npz')['heights'];assert np.array_equal(a['heights'],h[::-1])
    assert sha(B/'candidate/terrain.npz')=='f4600c90a088adf4df2c8f8f2067b03b77ca01aee9f4e9a8f786c0b1ea8cb7ba'
    shutil.copytree(src,dest,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
    write(dest/'baltic_trial.wrp',a['header'],v[::-1],a['materials'],[o['bytes'] for o in a['objects']],a['terminator'])
    c=read(dest/'baltic_trial.wrp');assert np.array_equal(c['heights'],v[::-1]);assert all(a[k]==c[k] for k in ['header','materials','terminator']);assert [o['bytes'] for o in a['objects']]==[o['bytes'] for o in c['objects']]
    for name in ['plane.npy','visible-field.npy']:shutil.copyfile(OLD/'candidate'/name,B/'candidate'/name)
    code=(OLD/'compile_native_world.ps1').read_text().replace(str(OLD).replace('/','\\'),str(B).replace('/','\\'))
    (B/'compile_native_world.ps1').write_text(code)
    shutil.copyfile(OLD/'audit_coverage.py',B/'audit_coverage.py')
    report=dict(status='STAGED_MSTA_VOLKHOV',source_wrp_sha256=sha(dest/'baltic_trial.wrp'),terrain_sha256=sha(B/'candidate/terrain.npz'),changed_vertices=int((v!=h).sum()),objects=len(c['objects']),objects_exact=True,fields_exact=True)
    (B/'stage.json').write_text(json.dumps(report,indent=2)+'\n')
    ref=dict(world_source_sha256=report['source_wrp_sha256'],water_sha256=sha(BASE/'baltic_water_v30.pbo'),plane_sha256=sha(B/'candidate/plane.npy'),field_sha256=sha(B/'candidate/visible-field.npy'))
    (B/'package-reference.json').write_text(json.dumps(ref,indent=2)+'\n');print(json.dumps(report,indent=2))
def deploy():
    assert json.loads((B/'compiled-coverage.json').read_text())['status']=='PASS_GLOBAL_COMPILED_COVERAGE'
    original=BASE/'narva_trial.pbo';assert sha(original)=='f3d6d58ea6d80042b23cd8e2958a14b653d1c903e82cc9f7f7b446992cd61c55'
    _,props,entries=read_pbo(original);_,_,compiled=read_pbo(B/'package/world/out/narva_trial.pbo');wrp=compiled['baltic_trial.wrp'];assert wrp[:4]==b'OPRW'
    dest=B/'distribution/narva_trial';dest.mkdir(parents=True,exist_ok=False)
    for name,data in entries.items():
        path=dest/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(wrp if name=='baltic_trial.wrp' else data)
    out=B/'packed';out.mkdir(exist_ok=False);cmd=['C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
    for k,v in props.items():cmd+=['-property',k+'='+v]
    done=subprocess.run(cmd+['-dst',str(out),str(dest)],capture_output=True,text=True);(B/'filebank.log').write_text(done.stdout+'\n'+done.stderr);assert done.returncode==0
    pbo=out/'narva_trial.pbo';_,gotprops,got=read_pbo(pbo);assert gotprops==props and set(got)==set(entries)
    changed=[name for name in entries if entries[name]!=got[name]];assert changed==['baltic_trial.wrp']
    water=BASE/'baltic_water_v30.pbo';assert sha(water)=='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
    target=Path('P:/Mods/@DayZ_Baltic_TerminalSmoothV1/Addons');target.mkdir(parents=True,exist_ok=False)
    for src in [pbo,water]:shutil.copyfile(src,target/src.name);assert sha(src)==sha(target/src.name)
    report=dict(status='DEPLOYED_TERMINAL_SMOOTH_PREVIEW',destination=str(target.parent),files={src.name:sha(src) for src in [pbo,water]},terrain_sha256=sha(B/'candidate/terrain.npz'),world_source_sha256=json.loads((B/'stage.json').read_text())['source_wrp_sha256'],compiled_wrp_sha256=hashlib.sha256(wrp).hexdigest(),baseline_world_sha256=sha(original),changed_world_entries=changed,unchanged_entries=len(entries)-1,limits=['Native readback and rendering pending.','EV28 textures retained pending local/final regeneration.','Navmesh retained until final TB acceptance.'])
    (B/'deploy.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['stage','deploy']);args=parser.parse_args()
    (stage if args.mode=='stage' else deploy)()
