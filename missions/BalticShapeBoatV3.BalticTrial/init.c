// Diagnostic mission only. No per-frame pose or velocity writes.
void main()
{
    Hive ce = CreateHive();
    if (ce) ce.InitOffline();
    GetGame().GetWorld().SetDate(2026, 9, 30, 12, 0);
}

class BalticCalibrationMission: MissionServer
{
    protected BoatScript m_Boat;
    protected FileHandle m_Log;
    protected int m_Start;
    protected int m_Tick;
    protected bool m_Started;
    protected bool m_Stopped;
    protected float m_HealthStart;
    protected vector m_Origin;

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(PrepareWater, 15000, false);
    }

    void LogWater(string stage)
    {
        for (int xx = 400; xx <= 600; xx += 25)
        {
            for (int zz = 2900; zz <= 3200; zz += 25)
            {
                float ground = GetGame().SurfaceY(xx,zz);
                for (int yy = 0; yy <= 9; yy += 3)
                {
                    vector pos = Vector(xx,yy,zz);
                    vector above = Vector(xx,20,zz);
                    string row = "WATER;" + stage + ";" + xx + ";" + yy + ";" + zz + ";" + ground;
                    row = row + ";" + GetGame().SurfaceIsSea(xx,zz) + ";" + GetGame().SurfaceIsPond(xx,zz);
                    row = row + ";" + GetGame().GetWaterDepth(pos) + ";" + GetGame().GetWaterSurfaceHeightNoFakeWave(above);
                    FPrintln(m_Log,row);
                }
            }
        }
    }

    void PrepareWater()
    {
        m_Log = OpenFile("$profile:baltic_shape_boat_v3.log", FileMode.WRITE);
        if (!m_Log) return;
        FPrintln(m_Log,"BALTIC_SHAPE_BOAT_V3");
        LogWater("BEFORE");
        Object p1 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_000.p3d", "430 6 2930", "0 0 0", 1, false);
        if (!p1) { Finish("POND_CREATE_FAILED"); return; }
        Object p2 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_001.p3d", "430 6 2978", "0 0 0", 1, false);
        if (!p2) { Finish("POND_CREATE_FAILED"); return; }
        Object p3 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_002.p3d", "430 6 3026", "0 0 0", 1, false);
        if (!p3) { Finish("POND_CREATE_FAILED"); return; }
        Object p4 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_003.p3d", "430 6 3074", "0 0 0", 1, false);
        if (!p4) { Finish("POND_CREATE_FAILED"); return; }
        Object p5 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_004.p3d", "430 6 3122", "0 0 0", 1, false);
        if (!p5) { Finish("POND_CREATE_FAILED"); return; }
        Object p6 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_005.p3d", "430 6 3170", "0 0 0", 1, false);
        if (!p6) { Finish("POND_CREATE_FAILED"); return; }
        Object p7 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_006.p3d", "478 6 2930", "0 0 0", 1, false);
        if (!p7) { Finish("POND_CREATE_FAILED"); return; }
        Object p8 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_007.p3d", "478 6 2978", "0 0 0", 1, false);
        if (!p8) { Finish("POND_CREATE_FAILED"); return; }
        Object p9 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_008.p3d", "478 6 3026", "0 0 0", 1, false);
        if (!p9) { Finish("POND_CREATE_FAILED"); return; }
        Object p10 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_009.p3d", "478 6 3074", "0 0 0", 1, false);
        if (!p10) { Finish("POND_CREATE_FAILED"); return; }
        Object p11 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_010.p3d", "478 6 3122", "0 0 0", 1, false);
        if (!p11) { Finish("POND_CREATE_FAILED"); return; }
        Object p12 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_011.p3d", "478 6 3170", "0 0 0", 1, false);
        if (!p12) { Finish("POND_CREATE_FAILED"); return; }
        Object p13 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_012.p3d", "526 6 2930", "0 0 0", 1, false);
        if (!p13) { Finish("POND_CREATE_FAILED"); return; }
        Object p14 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_013.p3d", "526 6 2978", "0 0 0", 1, false);
        if (!p14) { Finish("POND_CREATE_FAILED"); return; }
        Object p15 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_014.p3d", "526 6 3026", "0 0 0", 1, false);
        if (!p15) { Finish("POND_CREATE_FAILED"); return; }
        Object p16 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_015.p3d", "526 6 3074", "0 0 0", 1, false);
        if (!p16) { Finish("POND_CREATE_FAILED"); return; }
        Object p17 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_016.p3d", "526 6 3122", "0 0 0", 1, false);
        if (!p17) { Finish("POND_CREATE_FAILED"); return; }
        Object p18 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_017.p3d", "526 6 3170", "0 0 0", 1, false);
        if (!p18) { Finish("POND_CREATE_FAILED"); return; }
        Object p19 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_018.p3d", "574 6 2930", "0 0 0", 1, false);
        if (!p19) { Finish("POND_CREATE_FAILED"); return; }
        Object p20 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_019.p3d", "574 6 2978", "0 0 0", 1, false);
        if (!p20) { Finish("POND_CREATE_FAILED"); return; }
        Object p21 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_020.p3d", "574 6 3026", "0 0 0", 1, false);
        if (!p21) { Finish("POND_CREATE_FAILED"); return; }
        Object p22 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_021.p3d", "574 6 3074", "0 0 0", 1, false);
        if (!p22) { Finish("POND_CREATE_FAILED"); return; }
        Object p23 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_022.p3d", "574 6 3122", "0 0 0", 1, false);
        if (!p23) { Finish("POND_CREATE_FAILED"); return; }
        Object p24 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_023.p3d", "574 6 3170", "0 0 0", 1, false);
        if (!p24) { Finish("POND_CREATE_FAILED"); return; }
        Object p25 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_024.p3d", "622 6 2930", "0 0 0", 1, false);
        if (!p25) { Finish("POND_CREATE_FAILED"); return; }
        Object p26 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_025.p3d", "622 6 2978", "0 0 0", 1, false);
        if (!p26) { Finish("POND_CREATE_FAILED"); return; }
        Object p27 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_026.p3d", "622 6 3026", "0 0 0", 1, false);
        if (!p27) { Finish("POND_CREATE_FAILED"); return; }
        Object p28 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_027.p3d", "622 6 3074", "0 0 0", 1, false);
        if (!p28) { Finish("POND_CREATE_FAILED"); return; }
        Object p29 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_028.p3d", "670 6 2930", "0 0 0", 1, false);
        if (!p29) { Finish("POND_CREATE_FAILED"); return; }
        Object p30 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_029.p3d", "670 6 2978", "0 0 0", 1, false);
        if (!p30) { Finish("POND_CREATE_FAILED"); return; }
        Object p31 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_030.p3d", "670 6 3026", "0 0 0", 1, false);
        if (!p31) { Finish("POND_CREATE_FAILED"); return; }
        Object p32 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\lshape_031.p3d", "670 6 3074", "0 0 0", 1, false);
        if (!p32) { Finish("POND_CREATE_FAILED"); return; }
        Object p33 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_032.p3d", "780 6 2930", "0 0 0", 1, false);
        if (!p33) { Finish("POND_CREATE_FAILED"); return; }
        Object p34 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_033.p3d", "780 6 2978", "0 0 0", 1, false);
        if (!p34) { Finish("POND_CREATE_FAILED"); return; }
        Object p35 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_034.p3d", "780 6 3026", "0 0 0", 1, false);
        if (!p35) { Finish("POND_CREATE_FAILED"); return; }
        Object p36 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_035.p3d", "780 6 3074", "0 0 0", 1, false);
        if (!p36) { Finish("POND_CREATE_FAILED"); return; }
        Object p37 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_036.p3d", "780 6 3122", "0 0 0", 1, false);
        if (!p37) { Finish("POND_CREATE_FAILED"); return; }
        Object p38 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_037.p3d", "780 6 3170", "0 0 0", 1, false);
        if (!p38) { Finish("POND_CREATE_FAILED"); return; }
        Object p39 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_038.p3d", "828 6 2930", "0 0 0", 1, false);
        if (!p39) { Finish("POND_CREATE_FAILED"); return; }
        Object p40 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_039.p3d", "828 6 2978", "0 0 0", 1, false);
        if (!p40) { Finish("POND_CREATE_FAILED"); return; }
        Object p41 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_040.p3d", "828 6 3026", "0 0 0", 1, false);
        if (!p41) { Finish("POND_CREATE_FAILED"); return; }
        Object p42 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_041.p3d", "828 6 3074", "0 0 0", 1, false);
        if (!p42) { Finish("POND_CREATE_FAILED"); return; }
        Object p43 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_042.p3d", "828 6 3122", "0 0 0", 1, false);
        if (!p43) { Finish("POND_CREATE_FAILED"); return; }
        Object p44 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_043.p3d", "828 6 3170", "0 0 0", 1, false);
        if (!p44) { Finish("POND_CREATE_FAILED"); return; }
        Object p45 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_044.p3d", "876 6 2930", "0 0 0", 1, false);
        if (!p45) { Finish("POND_CREATE_FAILED"); return; }
        Object p46 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_045.p3d", "876 6 2978", "0 0 0", 1, false);
        if (!p46) { Finish("POND_CREATE_FAILED"); return; }
        Object p47 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_046.p3d", "876 6 3026", "0 0 0", 1, false);
        if (!p47) { Finish("POND_CREATE_FAILED"); return; }
        Object p48 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_047.p3d", "876 6 3074", "0 0 0", 1, false);
        if (!p48) { Finish("POND_CREATE_FAILED"); return; }
        Object p49 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_048.p3d", "876 6 3122", "0 0 0", 1, false);
        if (!p49) { Finish("POND_CREATE_FAILED"); return; }
        Object p50 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_049.p3d", "876 6 3170", "0 0 0", 1, false);
        if (!p50) { Finish("POND_CREATE_FAILED"); return; }
        Object p51 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_050.p3d", "924 6 2930", "0 0 0", 1, false);
        if (!p51) { Finish("POND_CREATE_FAILED"); return; }
        Object p52 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_051.p3d", "924 6 2978", "0 0 0", 1, false);
        if (!p52) { Finish("POND_CREATE_FAILED"); return; }
        Object p53 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_052.p3d", "924 6 3026", "0 0 0", 1, false);
        if (!p53) { Finish("POND_CREATE_FAILED"); return; }
        Object p54 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_053.p3d", "924 6 3074", "0 0 0", 1, false);
        if (!p54) { Finish("POND_CREATE_FAILED"); return; }
        Object p55 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_054.p3d", "924 6 3122", "0 0 0", 1, false);
        if (!p55) { Finish("POND_CREATE_FAILED"); return; }
        Object p56 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_055.p3d", "924 6 3170", "0 0 0", 1, false);
        if (!p56) { Finish("POND_CREATE_FAILED"); return; }
        Object p57 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_056.p3d", "972 6 2930", "0 0 0", 1, false);
        if (!p57) { Finish("POND_CREATE_FAILED"); return; }
        Object p58 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_057.p3d", "972 6 2978", "0 0 0", 1, false);
        if (!p58) { Finish("POND_CREATE_FAILED"); return; }
        Object p59 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_058.p3d", "972 6 3026", "0 0 0", 1, false);
        if (!p59) { Finish("POND_CREATE_FAILED"); return; }
        Object p60 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_059.p3d", "972 6 3074", "0 0 0", 1, false);
        if (!p60) { Finish("POND_CREATE_FAILED"); return; }
        Object p61 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_060.p3d", "972 6 3122", "0 0 0", 1, false);
        if (!p61) { Finish("POND_CREATE_FAILED"); return; }
        Object p62 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_061.p3d", "972 6 3170", "0 0 0", 1, false);
        if (!p62) { Finish("POND_CREATE_FAILED"); return; }
        Object p63 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_062.p3d", "1020 6 2930", "0 0 0", 1, false);
        if (!p63) { Finish("POND_CREATE_FAILED"); return; }
        Object p64 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_063.p3d", "1020 6 2978", "0 0 0", 1, false);
        if (!p64) { Finish("POND_CREATE_FAILED"); return; }
        Object p65 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_064.p3d", "1020 6 3026", "0 0 0", 1, false);
        if (!p65) { Finish("POND_CREATE_FAILED"); return; }
        Object p66 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_065.p3d", "1020 6 3074", "0 0 0", 1, false);
        if (!p66) { Finish("POND_CREATE_FAILED"); return; }
        Object p67 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_066.p3d", "1020 6 3122", "0 0 0", 1, false);
        if (!p67) { Finish("POND_CREATE_FAILED"); return; }
        Object p68 = GetGame().CreateStaticObjectUsingP3D("baltic_water_shape_v3\\hole_067.p3d", "1020 6 3170", "0 0 0", 1, false);
        if (!p68) { Finish("POND_CREATE_FAILED"); return; }
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
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BeginCalibration,3000,false);
    }

    void BeginCalibration()
    {
        FPrintln(m_Log, "W;" + GetGame().SurfaceGetSeaLevelMin() + ";" + GetGame().SurfaceGetSeaLevelMax() + ";" + GetGame().SurfaceGetSeaLevel());
        LogWater("AFTER");
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

        for (int hx = -110; hx <= 110; hx += 10)
        {
            for (int hz = -110; hz <= 110; hz += 10)
            {
                vector hp = Vector(900+hx,20,3050+hz);
                string hr = "HOLE;" + hx + ";" + hz;
                hr = hr + ";" + GetGame().GetWaterSurfaceHeightNoFakeWave(hp) + ";" + GetGame().SurfaceIsPond(hp[0],hp[2]);
                FPrintln(m_Log,hr);
            }
        }
        vector check = "500 20 3000";
        float waterY = GetGame().GetWaterSurfaceHeightNoFakeWave(check);
        float levelError = waterY - 6;
        levelError = Math.AbsFloat(levelError);
        bool isPond = GetGame().SurfaceIsPond(500,3000);
        if (!isPond || levelError > 0.1)
        {
            Finish("ELEVATED_WATER_NOT_REGISTERED");
            return;
        }
        m_Origin = "500 6.3 3000";
        m_Boat = BoatScript.Cast(GetGame().CreateObjectEx("Boat_01_Orange", m_Origin, ECE_CREATEPHYSICS));
        if (!m_Boat)
        {
            Finish("SPAWN_FAILED");
            return;
        }
        m_Boat.SetOrientation("0 0 0");
        m_Boat.GetInventory().CreateAttachment("SparkPlug");
        m_Boat.Fill(BoatFluid.FUEL, m_Boat.GetFluidCapacity(BoatFluid.FUEL));
        m_HealthStart = m_Boat.GetHealth("", "Health");
        m_Start = GetGame().GetTime();
        FPrintln(m_Log, "COLUMNS;t;phase;x;y;z;yaw;horizontal_speed;health;fuel;engine;rpm;clutch;gear;future_gear;neutral;prop_omega;prop_y;prop_depth;throttle;active;authority;proxy;input_calls");
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(CalibrationTick, 100, true);
    }

    void CalibrationTick()
    {
        if (m_Stopped) return;
        if (!m_Boat)
        {
            Finish("BOAT_LOST");
            return;
        }
        float seconds = (GetGame().GetTime() - m_Start) * 0.001;
        vector pos = m_Boat.GetPosition();
        vector orientation = m_Boat.GetOrientation();
        vector velocity = GetVelocity(m_Boat);
        velocity[1] = 0;
        float horizontalSpeed = velocity.Length();
        vector offset = pos - m_Origin;
        offset[1] = 0;
        float displacement = offset.Length();
        float health = m_Boat.GetHealth("", "Health");
        int phase = 0;
        float throttle = 0;
        int forwardGear;
        if (seconds >= 10 && !m_Started)
        {
            m_Started = true;
            m_Boat.EngineStart();
            forwardGear = m_Boat.GetNeutralGear() + 1;
            m_Boat.ShiftTo(forwardGear);
        }
        if (seconds >= 11 && seconds < 26)
        {
            phase = 1;
            throttle = 0.22;
        }
        else if (seconds >= 26 && seconds < 41)
        {
            phase = 2;
            throttle = 0.22;
        }
        else if (seconds >= 41 && seconds < 56)
        {
            phase = 3;
            throttle = 0.50;
        }
        else if (seconds >= 56 && seconds < 71)
        {
            phase = 4;
            throttle = 0.75;
        }
        else if (seconds >= 71)
        {
            phase = 5;
            m_Boat.EngineStop();
        }
        m_Boat.BalticProbeSetInput(throttle, 0, phase >= 1 && phase <= 4, phase >= 2);
        m_Tick++;
        if (m_Tick % 5 == 0)
        {
            vector propeller = m_Boat.ModelToWorld(m_Boat.PropellerGetPosition());
            string row = "B;" + seconds + ";" + phase + ";" + pos[0] + ";" + pos[1] + ";" + pos[2] + ";" + orientation[0] + ";" + horizontalSpeed + ";" + health;
            row = row + ";" + m_Boat.GetFluidFraction(BoatFluid.FUEL) + ";" + m_Boat.EngineIsOn() + ";" + m_Boat.EngineGetRPM() + ";" + m_Boat.GetClutch();
            row = row + ";" + m_Boat.GetCurrentGear() + ";" + m_Boat.GetGear() + ";" + m_Boat.GetNeutralGear() + ";" + m_Boat.PropellerGetAngularVelocity();
            row = row + ";" + propeller[1] + ";" + GetGame().GetWaterDepth(propeller) + ";" + m_Boat.GetThrottle();
            row = row + ";" + dBodyIsActive(m_Boat) + ";" + m_Boat.IsAuthority() + ";" + m_Boat.IsProxy();
            row = row + ";" + m_Boat.BalticProbeGetCalls();
            FPrintln(m_Log, row);
        }
        if (health < m_HealthStart - 1) Finish("DAMAGE_STOP");
        else if (displacement > 90) Finish("DISTANCE_SAFETY_STOP");
        else if (GetGame().SurfaceY(pos[0],pos[2]) > 2.5) Finish("SHALLOW_SAFETY_STOP");
        else if (seconds > 3 && (pos[1] < 4 || pos[1] > 8)) Finish("BUOYANCY_FAILED");
        else if (seconds >= 85) Finish("CALIBRATION_COMPLETE");
    }

    void Finish(string reason)
    {
        m_Stopped = true;
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(CalibrationTick);
        if (m_Boat)
        {
            m_Boat.BalticProbeStop();
            m_Boat.SetThrottle(0);
            m_Boat.SetSteering(0);
            m_Boat.EngineStop();
        }
        if (m_Log)
        {
            FPrintln(m_Log, "END;" + reason);
            CloseFile(m_Log);
            m_Log = null;
        }
    }

    void ~BalticCalibrationMission()
    {
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(PrepareWater);
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BeginCalibration);
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(CalibrationTick);
        if (m_Log) CloseFile(m_Log);
    }

    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        pos = "610 0 3000";
        pos[1] = GetGame().SurfaceY(pos[0],pos[2]) + 0.3;
        PlayerBase player = super.CreateCharacter(identity,pos,ctx,characterName);
        if (player) player.SetAllowDamage(false);
        return player;
    }
}

Mission CreateCustomMission(string path)
{
    return new BalticCalibrationMission();
}
