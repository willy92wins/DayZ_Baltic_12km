"""Physical consumer of authored L-water plus sea/pond overlap discriminator."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
text=(ROOT/'missions/BalticElevatedWaterV1.BalticTrial/init.c').read_text()
text=text.replace('baltic_elevated_water_v1','baltic_shape_boat_v1').replace('BALTIC_ELEVATED_WATER_V1','BALTIC_SHAPE_BOAT_V1')
start=text.index('        for (int xx = 450;')
end=text.index('        GetGame().GetCallQueue',start)
text=text[:start]+r'''        Object pond = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_probe\\lshape_memory.p3d", "550 6 3050", "0 0 0", 4, false);
        if (!pond) { Finish("POND_CREATE_FAILED"); return; }
        for (int i = 0; i < 3; i++)
        {
            float yy = 0.45;
            if (i == 1) yy = 0.75;
            if (i == 2) yy = 1.25;
            float xx = 1800 + i * 100;
            vector where = Vector(xx,yy,11000);
            Object seaPond = GetGame().CreateStaticObjectUsingP3D("dz\\water\\ponds\\pond_50x50.p3d",where,"0 0 0",1,false);
            if (!seaPond) { Finish("SEA_POND_CREATE_FAILED"); return; }
        }
'''+text[end:]
anchor='        LogWater("AFTER");'
extra=r'''
        for (int i = 0; i < 3; i++)
        {
            float xx = 1800 + i * 100;
            for (int dx = 0; dx <= 40; dx += 40)
            {
                vector point = Vector(xx+dx,20,11000);
                string row = "SEA;" + i + ";" + dx + ";" + GetGame().SurfaceY(point[0],point[2]);
                row = row + ";" + GetGame().GetWaterSurfaceHeightNoFakeWave(point);
                row = row + ";" + GetGame().SurfaceIsSea(point[0],point[2]) + ";" + GetGame().SurfaceIsPond(point[0],point[2]);
                FPrintln(m_Log,row);
            }
        }
'''
text=text.replace(anchor,anchor+extra)
dest=ROOT/'missions/BalticShapeBoatV1.BalticTrial';assert not dest.exists();dest.mkdir()
(dest/'init.c').write_text(text,encoding='utf-8',newline='\n')
print(json.dumps({'mission':str(dest),'sha256':hashlib.sha256((dest/'init.c').read_bytes()).hexdigest()}))
