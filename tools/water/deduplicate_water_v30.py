"""Share byte-identical MLOD/ODOL water models, preserving every instance.

No remeshing, transforms, UV edits or approximate matching. Both source and
compiled bytes must match for every alias before a fresh output is written.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo

SOURCE=Path('E:/DayZ-Baltic-Build/v30-pond-recovery/water')
PBO_SHA='371ece8affe420aa5ffde0b0c6da5b69eca5e329fe550cb2ce74ecacba2bcedd'
MANIFEST_SHA='e0da8b7d819302d7cca78618890ce020099a800a63d8a0cffc2c8c9e54631f36'
FILEBANK=Path(r'C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\PboUtils\FileBank.exe')


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--source',type=Path,default=SOURCE)
    ap.add_argument('--pbo-sha',default=PBO_SHA)
    ap.add_argument('--manifest-sha',default=MANIFEST_SHA)
    a=ap.parse_args();assert not a.out.exists() and FILEBANK.is_file()
    manifest_path=a.source/'pieces.json';raw=manifest_path.read_bytes()
    manifest_sha=sha(raw);assert a.manifest_sha=='any' or manifest_sha==a.manifest_sha
    old=json.loads(raw)
    oldpbo,props,compiled=read_pbo(a.source/'baltic_water_v30.pbo')
    pbo_sha=sha(oldpbo);assert (a.pbo_sha=='any' or pbo_sha==a.pbo_sha) and props['prefix']=='baltic_water_v30'
    byhash={};aliases={};canonical=[];sourcebytes={};compiledbytes={}
    removed_bytes=0
    for row in old['model_list']:
        name=row['name'];data=(a.source/'source/baltic_water_v30'/f'{name}.p3d').read_bytes()
        assert data[:4]==b'MLOD' and sha(data)==row['sha256']
        odol=compiled[f'{name}.p3d'];assert odol[:4]==b'ODOL'
        assert odol==(a.source/'temp/baltic_water_v30'/f'{name}.p3d').read_bytes()
        key=sha(data)
        if key in byhash:
            selected=byhash[key]
            assert data==sourcebytes[selected] and odol==compiledbytes[selected], ('Non-identical compiled alias',name,selected)
            aliases[name]=selected;removed_bytes+=len(odol)
        else:
            byhash[key]=name;aliases[name]=name;canonical.append(row)
            sourcebytes[name]=data;compiledbytes[name]=odol
    # The pinned counts belong to the pinned manifest; another manifest keeps the general invariants.
    pinned=a.manifest_sha==MANIFEST_SHA
    assert len(aliases)==len(old['model_list']) and (not pinned or (len(aliases)==13434 and len(canonical)==8775))
    revised=copy.deepcopy(old)
    for pose in revised['poses']:
        prefix,name=pose['model'].split('\\')
        assert prefix=='baltic_water_v30' and name.endswith('.p3d')
        pose['model']=prefix+'\\'+aliases[name[:-4]]+'.p3d'
    revised['model_list']=canonical;revised['models']=len(canonical)
    revised['triangles']=sum(row['triangles'] for row in canonical)
    revised['status']='DEDUPLICATED_EXACT_MODELS_PENDING_WORLD_CONSUMER'
    revised['deduplication']=dict(source_manifest_sha256=manifest_sha,source_pbo_sha256=pbo_sha,
                                 source_models=len(aliases),removed_models=len(aliases)-len(canonical))
    assert len(revised['poses'])==old['instances'] and (not pinned or old['instances']==17637)
    for before,after in zip(old['poses'],revised['poses']):
        assert {k:v for k,v in before.items() if k!='model'}=={k:v for k,v in after.items() if k!='model'}
    source=a.out/'source/baltic_water_v30';temp=a.out/'temp/baltic_water_v30'
    source.mkdir(parents=True);temp.mkdir(parents=True)
    for name,data in sourcebytes.items():(source/(name+'.p3d')).write_bytes(data)
    expected={k:v for k,v in compiled.items() if not k.endswith('.p3d')}
    expected.update({name+'.p3d':data for name,data in compiledbytes.items()})
    for name,data in expected.items():
        p=temp/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    for name in ('config.cpp','$PBOPREFIX$'):(source/name).write_bytes((a.source/'source/baltic_water_v30'/name).read_bytes())
    (a.out/'pieces.json').write_text(json.dumps(revised)+'\n',encoding='utf-8')
    args=[str(FILEBANK),'-property','prefix=baltic_water_v30','-property','product=dayz ugc','-dst',str(a.out),str(temp)]
    result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    (a.out/'filebank.log').write_bytes(result.stdout)
    assert result.returncode==0
    packed,newprops,entries=read_pbo(a.out/'baltic_water_v30.pbo')
    assert entries==expected and newprops['prefix']==props['prefix']
    receipt=dict(status='PASS_EXACT_MODEL_DEDUPLICATION_PENDING_WORLD_AND_ENGINE',
        source_models=len(aliases),unique_models=len(canonical),removed_models=len(aliases)-len(canonical),
        instances=old['instances'],transforms_exact=True,raw_and_compiled_alias_bytes_exact=True,
        compiled_tree_from_original_pbo=True,source_pbo_sha256=pbo_sha,pbo_sha256=sha(packed),
        original_pbo_bytes=len(oldpbo),pbo_bytes=len(packed),removed_model_payload_bytes=removed_bytes,
        pieces_sha256=sha((a.out/'pieces.json').read_bytes()),aliases=aliases,
        input_hashes={str(manifest_path):manifest_sha,str(Path(__file__)):sha(Path(__file__).read_bytes()),
                      str(FILEBANK):sha(FILEBANK.read_bytes())},
        limits=['Same instance count, pose and model bytes; no FPS, RAM or loading-time measurement.',
                'World model references still need derivation, packing, native import and engine acceptance.'])
    (a.out/'deduplication.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('aliases','input_hashes')},indent=2))


if __name__=='__main__':main()
