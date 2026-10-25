void main()
{
    Hive ce = CreateHive();
    if (ce) ce.InitOffline();
    GetGame().GetWorld().SetDate(2026,9,30,12,0);
}

class BalticWaterPoseMission: MissionServer
{
    protected FileHandle m_Log;
    protected ref array<Object> m_Objects;

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BeginProbe,15000,false);
    }

    void BeginProbe()
    {
        m_Log = OpenFile("$profile:baltic_water_geometry_v1.log",FileMode.WRITE);
        if (!m_Log) return;
        m_Objects = new array<Object>;
        FPrintln(m_Log,"BALTIC_WATER_GEOMETRY_V1");
        vector rotation = "0 0.5729387 0";
        vector flat = "0 0 0";
        Object a = GetGame().CreateStaticObjectUsingP3D("baltic_water_probe\\flat.p3d","450 6 4000",flat,1,false);
        Object b = GetGame().CreateStaticObjectUsingP3D("baltic_water_probe\\grade01.p3d","600 6 4000",flat,1,false);
        Object c = GetGame().CreateObjectEx("BalticWaterGrade01","750 6 4000",ECE_NONE);
        Object d = GetGame().CreateObjectEx("StaticObj_water_pond_50x50m","900 6 4000",ECE_NONE);
        if (!a || !b || !c || !d)
        {
            FPrintln(m_Log,"END;SPAWN_FAILED");
            CloseFile(m_Log);
            return;
        }
        m_Objects.Insert(a);
        m_Objects.Insert(b);
        m_Objects.Insert(c);
        m_Objects.Insert(d);
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(FinishProbe,3000,false);
    }

    void FinishProbe()
    {
        for (int i = 0; i < m_Objects.Count(); i++)
        {
            Object obj = m_Objects.Get(i);
            FPrintln(m_Log,"OBJECT;" + i + ";" + obj.GetPosition() + ";" + obj.GetOrientation());
            for (int dz = -24; dz <= 24; dz += 3)
            {
                vector localPos = Vector(0,0,dz);
                vector worldPos = obj.ModelToWorld(localPos);
                vector query = worldPos;
                query[1] = 30;
                float surface = GetGame().GetWaterSurfaceHeightNoFakeWave(query);
                float depth = GetGame().GetWaterDepth(query);
                float ground = GetGame().SurfaceY(query[0],query[2]);
                bool pond = GetGame().SurfaceIsPond(query[0],query[2]);
                string row = "S;" + i + ";" + dz + ";" + worldPos[0] + ";" + worldPos[1] + ";" + worldPos[2];
                row = row + ";" + surface + ";" + depth + ";" + ground + ";" + pond;
                FPrintln(m_Log,row);
            }
        }
        FPrintln(m_Log,"END;POSE_SCAN_COMPLETE");
        CloseFile(m_Log);
        m_Log = null;
    }
}

Mission CreateCustomMission(string path)
{
    return new BalticWaterPoseMission();
}
