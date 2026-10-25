"""Make a diagnostic derived WRP with fifteen vanilla ponds; never a native-export claim."""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from verify_texture_grid_change import read


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    original=ROOT/'tb/regional_outline_v3/baltic_regional_persisted_v3.wrp'
    assert sha(original)=='9bf50853799764571d4c3a7ce87c17583019af149bed93ac1e73f2c91c7c8c68'
    src=ROOT/'packages/baltic-regional-outline-v3/source/BalticTrialWorld'
    out=ROOT/'packages/baltic-static-water-probe-v1'
    if out.exists(): raise ValueError('Fresh output required')
    items=list(src.rglob('*'))
    if any(p.is_symlink() or p.is_junction() for p in items): raise ValueError('Reparse point in source')
    before={p.relative_to(src).as_posix():sha(p) for p in items if p.is_file()}
    stage=out/'source/BalticTrialWorld'
    shutil.copytree(src,stage)
    shutil.copytree(ROOT/'packages/baltic-regional-outline-v3/tools',out/'tools')
    old=read(original)
    sentinel_start=old['objects'][-1]['end']
    sentinel=old['bytes'][sentinel_start:]
    assert len(sentinel)==56
    body=bytearray(old['bytes'][:sentinel_start]); poses=[]
    model=b'dz\\water\\ponds\\pond_50x50.p3d\0'
    next_id=max(o['id'] for o in old['objects'])+1
    for x in (450,500,550):
        for z in (2950,3000,3050,3100,3150):
            mat=[1,0,0,0,1,0,0,0,1,x,6,z]
            body.extend(struct.pack('<12fII',*mat,next_id,len(model))+model)
            poses.append({'id':next_id,'position':[x,6,z],'model':model[:-1].decode()})
            next_id+=1
    body.extend(sentinel)
    target=stage/'baltic_trial.wrp';target.write_bytes(body)
    new=read(target)
    assert len(new['objects'])==18
    assert new['bytes'][:old['objects_start']]==old['bytes'][:old['objects_start']]
    for a,b in zip(old['objects'],new['objects'][:3]):
        assert a==b
    for pose,obj in zip(poses,new['objects'][3:]):
        assert list(struct.unpack('<12f',bytes.fromhex(obj['matrix']))[9:])==pose['position']
        assert obj['id']==pose['id'] and obj['name']==pose['model']
    config=ROOT/'packages/baltic-regional-v0.3-candidate/world-config.cpp'
    shutil.copyfile(config,stage/'config.cpp')
    nm=ROOT/'tb/regional_outline_v3/navmesh/baltic_regional_tile12p5_v1.nm'
    shutil.copyfile(nm,stage/'navmesh/baltic_trial.nm')
    changed={'config.cpp','navmesh/baltic_trial.nm','baltic_trial.wrp'}
    for rel,digest in before.items():
        if rel not in changed: assert sha(stage/rel)==digest,rel
    receipt={'status':'DERIVED_DIAGNOSTIC_WRP_NOT_TB_EXPORT', 'source_sha256':sha(original),
             'wrp_sha256':sha(target),'poses':poses,'terrain_material_and_three_objects_exact':True,
             'navmesh_status':'STALE_BOOTSTRAP_ONLY; pond objects added after generation',
             'unchanged_files':len(before)-len(changed)}
    (ROOT/'evidence/regional-foundation-v1/static-water-preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    # Identical consumer, with dynamic creation removed. Existing first sample now sees static water.
    text=(ROOT/'missions/BalticElevatedWaterV1.BalticTrial/init.c').read_text()
    start=text.index('        for (int xx = 450;')
    end=text.index('        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BeginCalibration,3000,false);',start)
    text=text[:start]+text[end:]
    text=text.replace('baltic_elevated_water_v1.log','baltic_static_water_v1.log').replace('BALTIC_ELEVATED_WATER_V1','BALTIC_STATIC_WATER_V1')
    mission=ROOT/'missions/BalticStaticWaterV1.BalticTrial'
    if mission.exists():raise ValueError('Fresh mission required')
    mission.mkdir();(mission/'init.c').write_text(text,encoding='utf-8',newline='\n')
    print(json.dumps({'package':str(out),'wrp_sha256':sha(target),'mission_sha256':sha(mission/'init.c')},indent=2))


if __name__=='__main__':main()
