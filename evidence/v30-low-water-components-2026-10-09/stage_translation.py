from pathlib import Path
import json,sys,shutil,subprocess,argparse
import numpy as np
from discover_components import sha
B=Path(__file__).parent;OLD=Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/playtest')]
from wrp0wzd import read,write,object_record
from attach_navmesh import read_pbo
BASE=Path('P:/Mods/@DayZ_Baltic_HingeSmoothV1/Addons')

def stage():
    info=json.loads((B/'translation-authoring.json').read_text());assert info['status']=='PASS_ISOLATED_TRANSLATION_SOURCE'
    src=OLD/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial';dst=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
    assert sha(src/'baltic_trial.wrp')=='a845bee973c2db1c94acf39758358dfcfb5967770e3879263ecf1a1bc4f66fd2'
    a=read(src/'baltic_trial.wrp');v=np.load(B/'translation/terrain.npz')['heights'];assert sha(B/'translation/terrain.npz')==info['terrain_sha256']
    records=[]
    for o in a['objects']:
        if o['id'] in info['object_ids']:
            m=list(o['matrix']);m[10]+=info['shift_m'];records.append(object_record(m,o['id'],o['raw_name']))
        else:records.append(o['bytes'])
    shutil.copytree(src,dst,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
    write(dst/'baltic_trial.wrp',a['header'],v[::-1],a['materials'],records,a['terminator'])
    got=read(dst/'baltic_trial.wrp');changed=[]
    for o,n in zip(a['objects'],got['objects']):
        assert o['id']==n['id'] and o['raw_name']==n['raw_name']
        d=np.array(n['matrix'])-o['matrix'];expected=np.zeros(12)
        if o['id'] in info['object_ids']:expected[10]=info['shift_m'];changed.append(o['id'])
        assert np.array_equal(d,expected),(o['id'],d.tolist())
    assert changed==info['object_ids'] and np.array_equal(got['heights'],v[::-1])
    assert all(got[k]==a[k] for k in ['header','materials','terminator'])
    code=(OLD/'compile_native_world.ps1').read_text().replace(str(OLD).replace('/','\\'),str(B).replace('/','\\'))
    (B/'compile_native_world.ps1').write_text(code)
    (B/'stage.json').write_text(json.dumps(dict(source_wrp_sha256=sha(dst/'baltic_trial.wrp'),objects=len(records),translated_y_only=changed,terrain_sha256=info['terrain_sha256']),indent=2)+'\n')
    print('STAGED: four Y translations; all other objects and world structure exact.')

def deploy():
    original=BASE/'narva_trial.pbo';assert sha(original)=='9eb9f4006c55e3ed3f73461816bed0272e8ab5fdc2f0ca58e214687ef0b82ee5'
    _,props,entries=read_pbo(original);_,_,built=read_pbo(B/'package/world/out/narva_trial.pbo');wrp=built['baltic_trial.wrp'];assert wrp[:4]==b'OPRW'
    dest=B/'distribution/narva_trial';dest.mkdir(parents=True,exist_ok=False)
    for name,data in entries.items():
        p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(wrp if name=='baltic_trial.wrp' else data)
    out=B/'packed';out.mkdir(exist_ok=False)
    cmd=['C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
    for k,v in props.items():cmd+=['-property',k+'='+v]
    done=subprocess.run(cmd+['-dst',str(out),str(dest)],capture_output=True,text=True);(B/'filebank.log').write_text(done.stdout+'\n'+done.stderr);assert done.returncode==0
    pbo=out/'narva_trial.pbo';_,newprops,got=read_pbo(pbo);assert props==newprops and set(entries)==set(got)
    changed=[name for name in entries if got[name]!=entries[name]];assert changed==['baltic_trial.wrp']
    water=BASE/'baltic_water_v30.pbo';assert sha(water)=='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
    target=Path('P:/Mods/@DayZ_Baltic_BasinTranslateProbeV1/Addons');target.mkdir(parents=True,exist_ok=False)
    for p in (pbo,water):shutil.copyfile(p,target/p.name);assert sha(p)==sha(target/p.name)
    result=dict(status='DEPLOYED_DIAGNOSTIC_ONLY',destination=str(target.parent),files={p.name:sha(p) for p in (pbo,water)},terrain_sha256=sha(B/'translation/terrain.npz'),source_wrp_sha256=json.loads((B/'stage.json').read_text())['source_wrp_sha256'],compiled_wrp_sha256=__import__('hashlib').sha256(wrp).hexdigest(),changed_entries=changed,unchanged_entries=len(entries)-1)
    (B/'deploy.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['stage','deploy']);args=parser.parse_args()
    stage() if args.mode=='stage' else deploy()
