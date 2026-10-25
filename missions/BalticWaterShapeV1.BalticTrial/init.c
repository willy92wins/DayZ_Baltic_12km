void main()
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
