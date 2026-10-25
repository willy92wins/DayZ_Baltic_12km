// Geometry-only discriminator. No player, boat or terrain motion overrides.
void main()
{
    Hive ce = CreateHive();
    if (ce) ce.InitOffline();
    GetGame().GetWorld().SetDate(2026,9,30,12,0);
}

class BalticWaterSlopeMission: MissionServer
{
    protected FileHandle m_Log;

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BeginProbe,15000,false);
    }

    void Scan(string stage)
    {
        for (int xx = 900; xx <= 1100; xx += 100)
        {
            for (int zz = 2970; zz <= 3200; zz += 2)
            {
                vector pos = Vector(xx,20,zz);
                float surface = GetGame().GetWaterSurfaceHeightNoFakeWave(pos);
                float depth = GetGame().GetWaterDepth(pos);
                float ground = GetGame().SurfaceY(xx,zz);
                bool pond = GetGame().SurfaceIsPond(xx,zz);
                string row = "S;" + stage + ";" + xx + ";" + zz + ";" + surface + ";" + depth + ";" + ground + ";" + pond;
                FPrintln(m_Log,row);
            }
        }
    }

    void BeginProbe()
    {
        m_Log = OpenFile("$profile:baltic_water_slope_v1.log",FileMode.WRITE);
        if (!m_Log) return;
        FPrintln(m_Log,"BALTIC_WATER_SLOPE_V1");
        Scan("BEFORE");
        vector rotation = "0 0.5729387 0";
        for (int zz = 3000; zz <= 3150; zz += 50)
        {
            float y = zz - 3000;
            y = y * 0.01 + 6;
            vector pos = Vector(900,y,zz);
            Object a = GetGame().CreateStaticObjectUsingP3D("dz\\water\\ponds\\pond_50x50.p3d",pos,rotation,1,false);
            FPrintln(m_Log,"POND;" + a);
        }
        vector noRotation = "0 0 0";
        for (int z2 = 3000; z2 <= 3144; z2 += 24)
        {
            float y2 = z2 - 3000;
            y2 = y2 * 0.005842208862304688 + 6;
            vector pos2 = Vector(1100,y2,z2);
            Object b = GetGame().CreateStaticObjectUsingP3D("dz\\water\\streams\\river_24_24.p3d",pos2,noRotation,1,false);
            FPrintln(m_Log,"RIVER;" + b);
        }
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(FinishProbe,3000,false);
    }

    void FinishProbe()
    {
        Scan("AFTER");
        FPrintln(m_Log,"END;GEOMETRY_SCAN_COMPLETE");
        CloseFile(m_Log);
        m_Log = null;
    }
}

Mission CreateCustomMission(string path)
{
    return new BalticWaterSlopeMission();
}
