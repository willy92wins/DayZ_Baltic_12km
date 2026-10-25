from pathlib import Path
import json,shutil,sys,subprocess,argparse,hashlib
import numpy as np
B=Path(__file__).parent;OLD=Path('E:/DayZ-Baltic-Build/v30-strict-dry-composition-20261009');W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/playtest')]
from wrp0wzd import read,write,object_record
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
BASE=Path('P:/Mods/@DayZ_Baltic_SurfaceAlignedV2/Addons')
def stage():
    result=json.loads((B/'verification.json').read_text());assert result['status']=='PASS_GEOMETRIC_PROPOSAL_POLICY_PENDING'
    assert json.loads((B/'compiled-exposure.json').read_text())['status']=='PASS_COMPILED_EXPOSURE'
    terrain=B/'candidate/terrain.npz';assert sha(terrain)==result['terrain_sha256']
    shift={int(k):v for k,v in json.loads((B/'authoring.json').read_text())['object_translations'].items()}
    src=OLD/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial';dest=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
    assert sha(src/'baltic_trial.wrp')=='931dd215fcb211bf233e18dd4e7fd0ce7a64f772d7294d28abbc5b1a6fbd3107'
    a=read(src/'baltic_trial.wrp');h=np.load(OLD/'candidate/terrain.npz')['heights'];v=np.load(terrain)['heights'];assert np.array_equal(a['heights'],h[::-1])
    shutil.copytree(src,dest,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
    records=[]
    for o in a['objects']:
        m=list(o['matrix'])
        if o['id'] in shift:m[10]+=shift[o['id']]
        records.append(object_record(m,o['id'],o['raw_name']) if o['id'] in shift else o['bytes'])
    write(dest/'baltic_trial.wrp',a['header'],v[::-1],a['materials'],records,a['terminator'])
    check=read(dest/'baltic_trial.wrp');assert np.array_equal(check['heights'],v[::-1])
    assert all(a[k]==check[k] for k in ('header','materials','terminator'))
    for old,new in zip(a['objects'],check['objects']):
        assert old['id']==new['id'] and old['raw_name']==new['raw_name']
        expected=np.array(old['matrix'],dtype=np.float32);expected[10]=np.float32(float(old['matrix'][10])+shift.get(old['id'],0))
        assert np.array_equal(expected,new['matrix'])
        if old['id'] not in shift:assert old['bytes']==new['bytes']
    code=(OLD/'compile_native_world.ps1').read_text().replace(str(OLD).replace('/','\\'),str(B).replace('/','\\'))
    (B/'compile_native_world.ps1').write_text(code)
    report=dict(status='STAGED_VOLKHOV_PROPOSAL_POLICY_PENDING',source_wrp_sha256=sha(dest/'baltic_trial.wrp'),terrain_sha256=sha(terrain),objects=len(a['objects']),translated_y_only=len(shift),other_objects_exact=True)
    (B/'package-reference.json').write_text(json.dumps(dict(world_source_sha256=report['source_wrp_sha256'],water_sha256='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14',plane_sha256=sha(B/'candidate/plane.npy'),field_sha256=sha(B/'candidate/visible-field.npy')),indent=2)+'\n')
    (B/'stage.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
def deploy():
    gate=json.loads((B/'compiled-coverage.json').read_text());assert gate['status']=='PASS_GLOBAL_COMPILED_COVERAGE'
    original=BASE/'narva_trial.pbo';assert sha(original)==json.loads(Path('E:/DayZ-Baltic-Build/v30-surface-aligned-20261009/deploy.json').read_text())['files']['narva_trial.pbo']
    _,props,entries=read_pbo(original);built=B/'package/world/out/narva_trial.pbo';_,_,compiled=read_pbo(built);wrp=compiled['baltic_trial.wrp'];assert wrp!=entries['baltic_trial.wrp'] and wrp[:4]==b'OPRW'
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
    target=Path('P:/Mods/@DayZ_Baltic_VolkhovBedProposalV1/Addons');target.mkdir(parents=True,exist_ok=False)
    for src in [pbo,water]:shutil.copyfile(src,target/src.name);assert sha(src)==sha(target/src.name)
    report=dict(status='DEPLOYED_VOLKHOV_PROPOSAL_POLICY_PENDING',destination=str(target.parent),files={src.name:sha(src) for src in (pbo,water)},terrain_sha256=sha(B/'candidate/terrain.npz'),world_source_sha256=json.loads((B/'stage.json').read_text())['source_wrp_sha256'],compiled_wrp_sha256=hashlib.sha256(wrp).hexdigest(),baseline_world_sha256=sha(original),changed_world_entries=changed,unchanged_entries=len(entries)-1,limits=['Native readback and local visual check pending.','EV67 textures retained provisionally over the same wet footprints; local shore apron semantics need final regeneration if accepted.','Navmesh retained until final TB acceptance.'])
    (B/'deploy.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['stage','deploy']);args=parser.parse_args()
    if args.mode=='stage':stage()
    else:deploy()
