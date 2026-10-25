"""Create a fresh local checkpoint, reject links and reread every ZIP member."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[2]
TARGET=ROOT/'packages/baltic-native-v0.2'


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while block:=f.read(2**20): h.update(block)
    return h.hexdigest()


def tree(directory):
    for entry in sorted(directory.iterdir()):
        if entry.is_symlink() or entry.is_junction():
            raise ValueError(f'Refusing linked dependency: {entry}')
        if entry.is_dir(): yield from tree(entry)
        elif entry.is_file(): yield entry


def main():
    if TARGET.exists(): raise ValueError('Fresh checkpoint required')
    source=ROOT/'tb/narva_navigation_v3'
    files=list(tree(source))
    pbo=ROOT/'packages/baltic-navigation-native-v1/navmesh-v1/Addons/narva_trial.pbo'
    nm=source/'navmesh/baltic_navigation_native_v1.nm'
    wrp=source/'baltic_navigation_native_reopened_v2.wrp'
    expected={pbo:'fd2c70238128657f5b92731396b73e3a961f4fc580c24f6c4671f083153b3d62',nm:'68450401421904660b10bf47563ca069458c722c3b86d3626c1c15fb5e2a3626',wrp:'9625ecf593c9c17288942d98ccf06933081bbcaffb367bb307146aa338cf9b5b'}
    for p,digest in expected.items():
        if sha(p)!=digest: raise ValueError(f'Frozen artifact drift: {p}')
    TARGET.mkdir(parents=True)
    dest=TARGET/'@DayZ_Baltic_12km/Addons/narva_trial.pbo'
    dest.parent.mkdir(parents=True)
    shutil.copy2(pbo,dest)
    shutil.copytree(ROOT/'missions/BalticNativeBasic.BalticTrial',TARGET/'mpmissions/BalticNativeBasic.BalticTrial')
    archive=TARGET/'terrain-builder-native.zip'
    records=[]
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for p in files:
            if p.suffix=='.tmp': continue
            name=p.relative_to(source).as_posix()
            digest=sha(p)
            z.write(p,name)
            records.append({'path':name,'bytes':p.stat().st_size,'sha256':digest})
    with zipfile.ZipFile(archive) as z:
        for item in records:
            h=hashlib.sha256()
            with z.open(item['path']) as f:
                while block:=f.read(2**20): h.update(block)
            if h.hexdigest()!=item['sha256']: raise ValueError('Archive member mismatch')
    result={'status':'PASS_CHECKPOINT_BYTES','pbo_sha256':sha(dest),'wrp_native_sha256':sha(wrp),'navmesh_sha256':sha(nm),'zip_sha256':sha(archive),'zip_bytes':archive.stat().st_size,'files':records,'limits':['Local editable checkpoint retains absolute source paths. Not a portable installer.','Historical exports including rejected objects_v1 are retained, not build inputs.','External GIS/source dependencies remain in the original project and earlier regional checkpoint.']}
    (TARGET/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    receipt={k:v for k,v in result.items() if k!='files'}
    receipt.update(file_count=len(records),path=str(TARGET))
    (ROOT/'evidence/navigation/native-checkpoint-v2.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__': main()
