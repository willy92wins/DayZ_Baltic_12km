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
        m_Log = OpenFile("$profile:baltic_static_shape_v2.log", FileMode.WRITE);
        if (!m_Log) return;
        FPrintln(m_Log,"BALTIC_STATIC_SHAPE_V2");
        LogWater("BEFORE");
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
        array<Object> found = new array<Object>;
        array<CargoBase> cargos = new array<CargoBase>;
        GetGame().GetObjectsAtPosition3D("700 6 3050",400,found,cargos);
        foreach (Object item: found)
        {
            string poseRow = "OBJECT;" + item.GetShapeName() + ";" + item.GetPosition();
            FPrintln(m_Log,poseRow);
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
