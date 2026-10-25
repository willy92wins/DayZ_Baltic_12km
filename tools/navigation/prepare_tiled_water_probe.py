"""Isolate footprint-size issue with unscaled 48m pieces and a known dry hole."""
from pathlib import Path
import hashlib,json,math
from shapely.geometry import box
from water_mesh import write_water_mesh
ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'tests/water_shape_v3/source/baltic_water_shape_v3'
assert not out.exists();out.mkdir(parents=True)
reports=[];spawns=[]
for group,geometry,centre in [('lshape',box(-100,-100,100,100).difference(box(0,0,100,100)),(550,3050)),
                              ('hole',box(-100,-100,100,100).difference(box(-20,-20,20,20)),(900,3050))]:
    for x in range(-144,100,48):
        for z in range(-144,100,48):
            g=geometry.intersection(box(x-.01,z-.01,x+48.01,z+48.01))
            if g.area<.001:continue
            name=f'{group}_{len(reports):03d}'
            origin=(x+24,z+24)
            report=write_water_mesh(g,out/f'{name}.p3d',origin)
            report.update(name=name,origin_xz=origin)
            reports.append(report)
            spawns.append(f'        Object p{len(reports)} = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\\\{name}.p3d", "{centre[0]+origin[0]} 6 {centre[1]+origin[1]}", "0 0 0", 1, false);\n        if (!p{len(reports)}) {{ Finish("POND_CREATE_FAILED"); return; }}')
(out/'$PBOPREFIX$').write_text('baltic_water_shape_v3')
(out/'config.cpp').write_text('class CfgPatches { class Baltic_Water_Shape_V3 { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Water"}; }; };\n')
text=(ROOT/'missions/BalticShapeBoatV2.BalticTrial/init.c').read_text()
text=text.replace('baltic_shape_boat_v2','baltic_shape_boat_v3').replace('BALTIC_SHAPE_BOAT_V2','BALTIC_SHAPE_BOAT_V3')
start=text.index('        Object pond = ');end=text.index('        for (int i = 0;',start)
text=text[:start]+'\n'.join(spawns)+'\n'+text[end:]
mission=ROOT/'missions/BalticShapeBoatV3.BalticTrial';assert not mission.exists();mission.mkdir()
(mission/'init.c').write_text(text,encoding='utf-8',newline='\n')
report={'models':reports,'count':len(reports),'mission_sha256':hashlib.sha256((mission/'init.c').read_bytes()).hexdigest(),
        'expected':'L-water and square with40m square dry hole. Every piece48.02m max, scale1, no orientation.'}
(ROOT/'evidence/regional-foundation-v1/water-shape-v3-preparation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='models'}))
