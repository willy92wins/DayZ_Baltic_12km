"""Isolate WRP authored-origin versus ODOL bounding-centre placement.

The previous static test flooded exterior controls while the dynamic array did
not. Change only WRP translation by the decoded model centre; keep every mesh.
"""
from pathlib import Path
import hashlib,json,shutil,struct,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
sys.path.insert(0,r'C:\Users\guill\.agents\skills\dayz-p3d-debinarizer\scripts')
from verify_texture_grid_change import read
from odol_reader import ODOL
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    out=ROOT/'packages/baltic-static-shape-probe-v2';assert not out.exists()
    source=ROOT/'packages/baltic-static-shape-probe-v1'
    assert not any(p.is_junction() or p.is_symlink() for p in source.rglob('*'))
    shutil.copytree(source,out)
    p=out/'source/BalticTrialWorld/baltic_trial.wrp'
    old=read(p);data=bytearray(old['bytes']);changes=[]
    for obj in old['objects']:
        if not obj['name'].startswith('baltic_water_shape_v3\\'):continue
        model=ROOT/'build-temp/water_shape_v3'/obj['name'].replace('\\','/')
        decoded=ODOL.from_file(str(model));assert not decoded.lod_errors
        v=decoded.model_info.bounding_center
        centre=[v.x,v.y,v.z]
        matrix=list(struct.unpack('<12f',bytes.fromhex(obj['matrix'])))
        assert matrix[:9]==[1,0,0,0,1,0,0,0,1]
        original=matrix[9:];matrix[9:]=[a+b for a,b in zip(original,centre)]
        struct.pack_into('<12f',data,obj['start'],*matrix)
        changes.append({'model':obj['name'],'authored_origin':original,'bounding_centre':centre,'native_position':matrix[9:]})
    assert len(changes)==68
    p.write_bytes(data);new=read(p)
    assert old['bytes'][:old['objects_start']]==new['bytes'][:new['objects_start']]
    assert old['objects'][:3]==new['objects'][:3]
    text=(ROOT/'missions/BalticStaticShapeV1.BalticTrial/init.c').read_text()
    text=text.replace('baltic_static_shape_v1','baltic_static_shape_v2').replace('BALTIC_STATIC_SHAPE_V1','BALTIC_STATIC_SHAPE_V2')
    anchor='        vector check = "500 20 3000";'
    text=text.replace(anchor,r'''        array<Object> found = new array<Object>;
        array<CargoBase> cargos = new array<CargoBase>;
        GetGame().GetObjectsAtPosition3D("700 6 3050",400,found,cargos);
        foreach (Object item: found)
        {
            string poseRow = "OBJECT;" + item.GetShapeName() + ";" + item.GetPosition();
            FPrintln(m_Log,poseRow);
        }
'''+anchor)
    mission=ROOT/'missions/BalticStaticShapeV2.BalticTrial';assert not mission.exists();mission.mkdir()
    (mission/'init.c').write_text(text,encoding='utf-8',newline='\n')
    receipt={'status':'PLACEMENT_HYPOTHESIS_NOT_RUN','wrp_sha256':sha(p),'changes':changes,'mission_sha256':sha(mission/'init.c')}
    (ROOT/'evidence/regional-foundation-v1/static-shape-v2-preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='changes'},indent=2))

if __name__=='__main__':main()
