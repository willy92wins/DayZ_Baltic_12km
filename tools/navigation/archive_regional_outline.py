"""Checkpoint the editable regional project and an explicitly identified trial PBO."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
from package_native_checkpoint import tree, sha

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pbo',type=Path,required=True)
    ap.add_argument('--sha256',required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--config',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists(): raise ValueError('Fresh checkpoint required')
    if sha(a.pbo)!=a.sha256: raise ValueError('Trial package changed')
    _,_,entries=read_pbo(a.pbo)
    if hashlib.sha256(entries['baltic_trial.wrp']).hexdigest()!='0a993128116d3cf769c2b7e6e4413fa44aa0164295f80da44837e43b42076c7e':
        raise ValueError('Wrong compiled terrain')
    native=ROOT/'tb/regional_outline_v3/baltic_regional_persisted_v3.wrp'
    if sha(native)!='9bf50853799764571d4c3a7ce87c17583019af149bed93ac1e73f2c91c7c8c68':
        raise ValueError('Native source changed')
    dirs=['tb/regional_outline_v3','tests/regional_outline_v3','derived/outline-v3']
    files=[p for d in dirs for p in tree(ROOT/d) if p.suffix!='.tmp']
    biome=ROOT/'tests/regional_outline_v1/biome_reservation.tif'
    if not biome.is_file(): raise ValueError('Missing reserved biome layer')
    files.append(biome)
    a.out.mkdir(parents=True)
    source=a.out/'world-config.cpp'
    shutil.copy2(a.config,source)
    compiled=a.out/'world-config.bin'
    convert=Path(r'C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\CfgConvert\CfgConvert.exe')
    conversion=subprocess.run([str(convert),'-bin','-dst',str(compiled),str(source)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (a.out/'config-convert.log').write_bytes(conversion.stdout)
    if conversion.returncode or compiled.read_bytes()!=entries['config.bin']:
        raise ValueError('Archived config does not reproduce the selected PBO')
    dest=a.out/'@DayZ_Baltic_Outline/Addons/narva_trial.pbo'
    dest.parent.mkdir(parents=True); shutil.copy2(a.pbo,dest)
    if sha(dest)!=a.sha256: raise ValueError('Copied PBO mismatch')
    shutil.copytree(ROOT/'missions/BalticNativeBasic.BalticTrial',a.out/'mpmissions/BalticNativeBasic.BalticTrial')
    mission_records=[]
    for p in tree(ROOT/'missions/BalticNativeBasic.BalticTrial'):
        relative=p.relative_to(ROOT/'missions/BalticNativeBasic.BalticTrial')
        copied=a.out/'mpmissions/BalticNativeBasic.BalticTrial'/relative
        if sha(p)!=sha(copied): raise ValueError('Copied mission mismatch')
        mission_records.append({'path':relative.as_posix(),'sha256':sha(copied)})
    archive=a.out/'terrain-builder-regional.zip'
    records=[]
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for p in files:
            name=p.relative_to(ROOT).as_posix(); digest=sha(p)
            z.write(p,name)
            records.append({'path':name,'bytes':p.stat().st_size,'sha256':digest})
    with zipfile.ZipFile(archive) as z:
        if len(z.namelist())!=len(records): raise ValueError('Archive count mismatch')
        for record in records:
            with z.open(record['path']) as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
            if digest!=record['sha256']: raise ValueError('Archived bytes mismatch')
    result={'status':'PASS_CHECKPOINT_BYTES_NOT_GAMEPLAY_ACCEPTANCE','pbo_sha256':sha(dest),
            'compiled_wrp_sha256':hashlib.sha256(entries['baltic_trial.wrp']).hexdigest(),
            'navmesh_sha256':hashlib.sha256(entries['navmesh/baltic_trial.nm']).hexdigest(),
            'config_source_sha256':sha(source),'config_compiled_exact':True,
            'mission_files':mission_records,
            'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'files':records,
            'limits':['Local editable project retains absolute original dependency paths.',
                      'Historical exports are retained; use only baltic_regional_persisted_v3.wrp.',
                      'See current runtime gates; byte identity does not close failed AI or hydrology gates.']}
    (a.out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    compact={k:v for k,v in result.items() if k!='files'}
    compact['file_count']=len(records); compact['directory']=str(a.out)
    (ROOT/'evidence/regional-outline-v3/checkpoint.json').write_text(json.dumps(compact,indent=2)+'\n')
    print(json.dumps(compact,indent=2))

if __name__=='__main__': main()
