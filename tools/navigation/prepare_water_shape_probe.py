"""Authored L-shaped horizontal water planes: test footprint versus bounding box.

Original procedural geometry with installed vanilla shader/material references.
This is an isolated experiment, not an adopted production asset.
"""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,r'C:\Users\guill\DayZ-Modding-Knowledge-Pack\tools\py3d')
import py3d
assert py3d.IS_DAYZ_FORK
OUT=ROOT/'tests/water_shape_v1/source/baltic_water_shape_probe'
assert not OUT.exists()
OUT.mkdir(parents=True)
quads=[(-25,-25,0,0),(0,-25,25,0),(-25,0,0,25)]
reports={}
for name,include_memory in [('lshape_memory',True),('lshape',False)]:
    model=py3d.P3D()
    for resolution in (1,1e13,1e15,3e15):
        if resolution==1e15 and not include_memory:continue
        lod=py3d.LOD();lod.resolution=resolution
        if resolution==1e13:lod.properties.update({'damage':'no','class':'pond'})
        elif resolution==1e15:
            for x,z in [(-25,-25),(25,-25),(-25,25),(25,25)]:
                p=py3d.Point();p.coords=(x,0,z);lod.points.append(p)
        else:
            lod.facenormals.append((0,-1,0) if resolution==1 else (0,1,0))
            if resolution==1:lod.properties['lodnoshadow']='1'
            for x0,z0,x1,z1 in quads:
                face=py3d.Face(lod.points,lod.facenormals)
                face.texture=r'dz\data\data\normalmap1_dxt5.paa' if resolution==1 else r'dz\surfaces\data\roadway\water_ext.paa'
                face.material=r'dz\water\ponds\data\pond_moss_1.rvmat' if resolution==1 else ''
                for x,z in [(x0,z0),(x1,z0),(x1,z1),(x0,z1)]:
                    p=py3d.Point();p.coords=(x,0,z)
                    v=py3d.Vertex(lod.points,lod.facenormals)
                    v.point_index=len(lod.points);v.normal_index=0;v.uv=(x/25,z/25)
                    lod.points.append(p);face.vertices.append(v)
                lod.faces.append(face)
        model.lods.append(lod)
    path=OUT/f'{name}.p3d';model.save(str(path))
    reports[name]=hashlib.sha256(path.read_bytes()).hexdigest()
(OUT/'$PBOPREFIX$').write_text('baltic_water_shape_probe')
(OUT/'config.cpp').write_text('class CfgPatches { class Baltic_Water_Shape_Probe { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Water"}; }; };\n')
mission=ROOT/'missions/BalticWaterShapeV1.BalticTrial'
assert not mission.exists()
mission.mkdir()
(mission/'init.c').write_text(r'''void main()
{
    Hive ce=CreateHive();
    if(ce) ce.InitOffline();
    GetGame().GetWorld().SetDate(2026,9,30,12,0);
}
class BalticWaterShapeMission: MissionServer
{
    protected FileHandle m_Log;
    protected ref array<Object> m_Objects;
    override void OnInit()
    {
        super.OnInit();
        if(!GetGame().IsDedicatedServer() || GetGame().GetWorldName()!="BalticTrial") return;
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BeginProbe,15000,false);
    }
    void BeginProbe()
    {
        m_Log=OpenFile("$profile:baltic_water_shape_v1.log",FileMode.WRITE);
        if(!m_Log) return;
        FPrintln(m_Log,"BALTIC_WATER_SHAPE_V1");
        m_Objects=new array<Object>;
        Object a=GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_probe\\lshape_memory.p3d","500 6 4000","0 0 0",1,false);
        Object b=GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_probe\\lshape.p3d","600 6 4000","0 0 0",1,false);
        Object c=GetGame().CreateStaticObjectUsingP3D("dz\\water\\ponds\\pond_50x50.p3d","700 6 4000","0 0 0",1,false);
        if(!a || !b || !c)
        {
            FPrintln(m_Log,"END;SPAWN_FAILED");CloseFile(m_Log);m_Log=null;return;
        }
        m_Objects.Insert(a);m_Objects.Insert(b);m_Objects.Insert(c);
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(Measure,3000,false);
    }
    void Measure()
    {
        for(int i=0;i<m_Objects.Count();i++)
        {
            Object obj=m_Objects.Get(i);
            FPrintln(m_Log,"OBJECT;"+i+";"+obj.GetPosition()+";"+obj.GetOrientation());
            for(int x=-30;x<=30;x+=5)
            {
                for(int z=-30;z<=30;z+=5)
                {
                    vector p=obj.ModelToWorld(Vector(x,20,z));
                    float ground=GetGame().SurfaceY(p[0],p[2]);
                    float surface=GetGame().GetWaterSurfaceHeightNoFakeWave(p);
                    float depth=GetGame().GetWaterDepth(p);
                    bool pond=GetGame().SurfaceIsPond(p[0],p[2]);
                    string row = "S;" + i + ";" + x + ";" + z;
                    row = row + ";" + p[0] + ";" + p[2] + ";" + ground;
                    row = row + ";" + surface + ";" + depth + ";" + pond;
                    FPrintln(m_Log,row);
                }
            }
        }
        FPrintln(m_Log,"END;SHAPE_SCAN_COMPLETE");CloseFile(m_Log);m_Log=null;
    }
}
Mission CreateCustomMission(string path){return new BalticWaterShapeMission();}
''',encoding='utf-8',newline='\n')
# The raw Enforce string contains literal backslashes, not Python path escapes.
receipt={'status':'PREPARED_NOT_RUN','models':reports,'mission_sha256':hashlib.sha256((mission/'init.c').read_bytes()).hexdigest(),
         'independent_shape_oracle':'Inside 50m square except NE quadrant; exclude boundary samples. Vanilla square is the positive control.'}
(ROOT/'evidence/regional-foundation-v1/water-shape-preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
