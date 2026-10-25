"""Persist the already-tested68 water pieces in a derived diagnostic WRP."""
import hashlib,json,re,shutil,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from verify_texture_grid_change import read
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    original=ROOT/'tb/regional_outline_v3/baltic_regional_persisted_v3.wrp'
    assert sha(original)=='9bf50853799764571d4c3a7ce87c17583019af149bed93ac1e73f2c91c7c8c68'
    src=ROOT/'packages/baltic-regional-outline-v3/source/BalticTrialWorld'
    out=ROOT/'packages/baltic-static-shape-probe-v1';assert not out.exists()
    files=list(src.rglob('*'));assert not any(p.is_symlink() or p.is_junction() for p in files)
    stage=out/'source/BalticTrialWorld';shutil.copytree(src,stage)
    shutil.copytree(ROOT/'packages/baltic-regional-outline-v3/tools',out/'tools')
    old=read(original);sentinel_start=old['objects'][-1]['end'];sentinel=old['bytes'][sentinel_start:];assert len(sentinel)==56
    body=bytearray(old['bytes'][:sentinel_start]);poses=[]
    mission_text=(ROOT/'missions/BalticShapeBoatV3.BalticTrial/init.c').read_text()
    pattern=r'Object p\d+ = GetGame\(\).CreateStaticObjectUsingP3D\("([^"]+)", "([^"]+)", "0 0 0", 1, false\);'
    found=re.findall(pattern,mission_text);assert len(found)==68
    next_id=max(o['id'] for o in old['objects'])+1
    for model,position in found:
        model=model.replace('\\\\','\\');xyz=list(map(float,position.split()));encoded=model.encode()+b'\0'
        body.extend(struct.pack('<12fII',1,0,0,0,1,0,0,0,1,*xyz,next_id,len(encoded))+encoded)
        poses.append({'id':next_id,'model':model,'position':xyz});next_id+=1
    body.extend(sentinel);target=stage/'baltic_trial.wrp';target.write_bytes(body)
    new=read(target);assert len(new['objects'])==71
    assert old['bytes'][:old['objects_start']]==new['bytes'][:new['objects_start']]
    assert new['objects'][:3]==old['objects']
    shutil.copyfile(ROOT/'packages/baltic-regional-v0.3-candidate/world-config.cpp',stage/'config.cpp')
    shutil.copyfile(ROOT/'tb/regional_outline_v3/navmesh/baltic_regional_tile12p5_v1.nm',stage/'navmesh/baltic_trial.nm')
    text=mission_text
    start=text.index('        Object p1 =');end=text.index('        for (int i = 0;',start)
    text=text[:start]+text[end:]
    text=text.replace('baltic_shape_boat_v3','baltic_static_shape_v1').replace('BALTIC_SHAPE_BOAT_V3','BALTIC_STATIC_SHAPE_V1')
    mission=ROOT/'missions/BalticStaticShapeV1.BalticTrial';assert not mission.exists();mission.mkdir()
    (mission/'init.c').write_text(text,encoding='utf-8',newline='\n')
    report={'status':'DERIVED_DIAGNOSTIC_WRP_NOT_TB_EXPORT','wrp_sha256':sha(target),'mission_sha256':sha(mission/'init.c'),
            'terrain_materials_original_objects_exact':True,'water_poses':poses,'navmesh':'STALE_BOOTSTRAP_ONLY'}
    (ROOT/'evidence/regional-foundation-v1/static-shape-preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='water_poses'},indent=2))

if __name__=='__main__':main()
