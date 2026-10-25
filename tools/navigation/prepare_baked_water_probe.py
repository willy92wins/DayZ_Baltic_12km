from pathlib import Path
import hashlib,json
from shapely.geometry import box
from water_mesh import write_water_mesh
ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'tests/water_shape_v2/source/baltic_water_shape_v2'
assert not out.exists();out.mkdir(parents=True)
reports={}
for name,geometry in [('lshape',box(-100,-100,100,100).difference(box(0,0,100,100))),
                      ('hole',box(-100,-100,100,100).difference(box(-20,-20,20,20)))]:
    path=out/f'{name}.p3d'
    reports[name]=write_water_mesh(geometry,path,(0,0))
    reports[name]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
(out/'$PBOPREFIX$').write_text('baltic_water_shape_v2')
(out/'config.cpp').write_text('class CfgPatches { class Baltic_Water_Shape_V2 { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Water"}; }; };\n')
text=(ROOT/'missions/BalticShapeBoatV1.BalticTrial/init.c').read_text()
text=text.replace('baltic_shape_boat_v1','baltic_shape_boat_v2').replace('BALTIC_SHAPE_BOAT_V1','BALTIC_SHAPE_BOAT_V2')
text=text.replace(r'baltic_water_shape_probe\\lshape_memory.p3d',r'baltic_water_shape_v2\\lshape.p3d').replace('"0 0 0", 4, false','"0 0 0", 1, false')
anchor='        if (!pond) { Finish("POND_CREATE_FAILED"); return; }'
text=text.replace(anchor,anchor+r'''
        Object hole = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v2\\hole.p3d","900 6 3050","0 0 0",1,false);
        if (!hole) { Finish("HOLE_CREATE_FAILED"); return; }
''')
anchor='        vector check = "500 20 3000";'
text=text.replace(anchor,r'''        for (int hx = -110; hx <= 110; hx += 10)
        {
            for (int hz = -110; hz <= 110; hz += 10)
            {
                vector hp = Vector(900+hx,20,3050+hz);
                string hr = "HOLE;" + hx + ";" + hz;
                hr = hr + ";" + GetGame().GetWaterSurfaceHeightNoFakeWave(hp) + ";" + GetGame().SurfaceIsPond(hp[0],hp[2]);
                FPrintln(m_Log,hr);
            }
        }
'''+anchor)
mission=ROOT/'missions/BalticShapeBoatV2.BalticTrial';assert not mission.exists();mission.mkdir()
(mission/'init.c').write_text(text,encoding='utf-8',newline='\n')
reports['mission_sha256']=hashlib.sha256((mission/'init.c').read_bytes()).hexdigest()
(ROOT/'evidence/regional-foundation-v1/water-shape-v2-preparation.json').write_text(json.dumps(reports,indent=2)+'\n')
print(json.dumps(reports,indent=2))
