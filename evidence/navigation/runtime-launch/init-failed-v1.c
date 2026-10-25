// Bounded server-owned empty-boat calibration. Never SetPosition after spawn.
// Native Boat API: scripts/3_game/vehicles/boat.c:49,55,97,119,123,139.
// This fixture cannot prove a seated player's clearance or a return journey.
void main()
{
    Hive ce = CreateHive();
    if (ce) ce.InitOffline();
    GetGame().GetWorld().SetDate(2026, 9, 30, 12, 0);
}

class BalticBoatMission: MissionServer
{
    protected BoatScript m_Boat;
    protected ref array<vector> m_Route;
    protected FileHandle m_Log;
    protected int m_Start;
    protected int m_Tick;
    protected int m_Target;
    protected float m_HealthStart;
    protected bool m_Stopped;

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        m_Route = new array<vector>;
        m_Route.Insert("2429.367762 0 6843.537472");
        m_Route.Insert("2434.447534 0 6852.114968");
        m_Route.Insert("2432.944784 0 6861.431815");
        m_Route.Insert("2425.751711 0 6868.226422");
        m_Route.Insert("2417.798140 0 6874.286888");
        m_Route.Insert("2415.265032 0 6882.807278");
        m_Route.Insert("2418.474328 0 6892.223047");
        m_Route.Insert("2424.364288 0 6900.234251");
        m_Route.Insert("2430.035175 0 6908.300297");
        m_Route.Insert("2432.517517 0 6917.913221");
        m_Route.Insert("2431.201883 0 6927.826299");
        m_Route.Insert("2427.648764 0 6937.047257");
        m_Route.Insert("2423.137375 0 6945.971794");
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BeginBoatTrial, 40000, false);
    }

    void ObserveGround(float x, float z)
    {
        FPrintln(m_Log, "G;" + x + ";" + z + ";" + GetGame().SurfaceY(x,z) + ";" + GetGame().SurfaceRoadY(x,z) + ";" + GetGame().SurfaceIsSea(x,z));
    }

    void BeginBoatTrial()
    {
        m_Log = OpenFile("$profile:baltic_boat_probe_v3.log", FileMode.WRITE);
        if (!m_Log) return;
        FPrintln(m_Log, "BALTIC_BOAT_PROBE_V3");
        FPrintln(m_Log, "ASC=c1f23f24808cb6f1ff858f47a378f6bdf8211387f63c110a12ff72fd3bd82d3c");
        FPrintln(m_Log, "BOOTSTRAP_NAV_STALE_NO_AI_ACCEPTANCE");
        FPrintln(m_Log, "W;" + GetGame().SurfaceGetSeaLevelMin() + ";" + GetGame().SurfaceGetSeaLevelMax() + ";" + GetGame().SurfaceGetSeaLevel());
        ObserveGround(2412, 6972);
        ObserveGround(2418, 6972);
        ObserveGround(2424, 6972);
        ObserveGround(2400, 6966);
        ObserveGround(2406, 6966);
        ObserveGround(2412, 6966);
        ObserveGround(2418, 6966);
        ObserveGround(2424, 6966);
        ObserveGround(2430, 6966);
        ObserveGround(2400, 6960);
        ObserveGround(2406, 6960);
        ObserveGround(2412, 6960);
        ObserveGround(2418, 6960);
        ObserveGround(2424, 6960);
        ObserveGround(2430, 6960);
        ObserveGround(2400, 6954);
        ObserveGround(2406, 6954);
        ObserveGround(2412, 6954);
        ObserveGround(2418, 6954);
        ObserveGround(2424, 6954);
        ObserveGround(2430, 6954);
        ObserveGround(2436, 6954);
        ObserveGround(2406, 6948);
        ObserveGround(2412, 6948);
        ObserveGround(2418, 6948);
        ObserveGround(2424, 6948);
        ObserveGround(2430, 6948);
        ObserveGround(2436, 6948);
        ObserveGround(2406, 6942);
        ObserveGround(2412, 6942);
        ObserveGround(2418, 6942);
        ObserveGround(2424, 6942);
        ObserveGround(2430, 6942);
        ObserveGround(2436, 6942);
        ObserveGround(2442, 6942);
        ObserveGround(2412, 6936);
        ObserveGround(2418, 6936);
        ObserveGround(2424, 6936);
        ObserveGround(2430, 6936);
        ObserveGround(2436, 6936);
        ObserveGround(2442, 6936);
        ObserveGround(2412, 6930);
        ObserveGround(2418, 6930);
        ObserveGround(2424, 6930);
        ObserveGround(2430, 6930);
        ObserveGround(2436, 6930);
        ObserveGround(2442, 6930);
        ObserveGround(2448, 6930);
        ObserveGround(2418, 6924);
        ObserveGround(2424, 6924);
        ObserveGround(2430, 6924);
        ObserveGround(2436, 6924);
        ObserveGround(2442, 6924);
        ObserveGround(2448, 6924);
        ObserveGround(2418, 6918);
        ObserveGround(2424, 6918);
        ObserveGround(2430, 6918);
        ObserveGround(2436, 6918);
        ObserveGround(2442, 6918);
        ObserveGround(2448, 6918);
        ObserveGround(2412, 6912);
        ObserveGround(2418, 6912);
        ObserveGround(2424, 6912);
        ObserveGround(2430, 6912);
        ObserveGround(2436, 6912);
        ObserveGround(2442, 6912);
        ObserveGround(2448, 6912);
        ObserveGround(2406, 6906);
        ObserveGround(2412, 6906);
        ObserveGround(2418, 6906);
        ObserveGround(2424, 6906);
        ObserveGround(2430, 6906);
        ObserveGround(2436, 6906);
        ObserveGround(2442, 6906);
        ObserveGround(2448, 6906);
        ObserveGround(2406, 6900);
        ObserveGround(2412, 6900);
        ObserveGround(2418, 6900);
        ObserveGround(2424, 6900);
        ObserveGround(2430, 6900);
        ObserveGround(2436, 6900);
        ObserveGround(2442, 6900);
        ObserveGround(2448, 6900);
        ObserveGround(2400, 6894);
        ObserveGround(2406, 6894);
        ObserveGround(2412, 6894);
        ObserveGround(2418, 6894);
        ObserveGround(2424, 6894);
        ObserveGround(2430, 6894);
        ObserveGround(2436, 6894);
        ObserveGround(2442, 6894);
        ObserveGround(2400, 6888);
        ObserveGround(2406, 6888);
        ObserveGround(2412, 6888);
        ObserveGround(2418, 6888);
        ObserveGround(2424, 6888);
        ObserveGround(2430, 6888);
        ObserveGround(2436, 6888);
        ObserveGround(2400, 6882);
        ObserveGround(2406, 6882);
        ObserveGround(2412, 6882);
        ObserveGround(2418, 6882);
        ObserveGround(2424, 6882);
        ObserveGround(2430, 6882);
        ObserveGround(2400, 6876);
        ObserveGround(2406, 6876);
        ObserveGround(2412, 6876);
        ObserveGround(2418, 6876);
        ObserveGround(2424, 6876);
        ObserveGround(2430, 6876);
        ObserveGround(2436, 6876);
        ObserveGround(2442, 6876);
        ObserveGround(2400, 6870);
        ObserveGround(2406, 6870);
        ObserveGround(2412, 6870);
        ObserveGround(2418, 6870);
        ObserveGround(2424, 6870);
        ObserveGround(2430, 6870);
        ObserveGround(2436, 6870);
        ObserveGround(2442, 6870);
        ObserveGround(2406, 6864);
        ObserveGround(2412, 6864);
        ObserveGround(2418, 6864);
        ObserveGround(2424, 6864);
        ObserveGround(2430, 6864);
        ObserveGround(2436, 6864);
        ObserveGround(2442, 6864);
        ObserveGround(2448, 6864);
        ObserveGround(2412, 6858);
        ObserveGround(2418, 6858);
        ObserveGround(2424, 6858);
        ObserveGround(2430, 6858);
        ObserveGround(2436, 6858);
        ObserveGround(2442, 6858);
        ObserveGround(2448, 6858);
        ObserveGround(2412, 6852);
        ObserveGround(2418, 6852);
        ObserveGround(2424, 6852);
        ObserveGround(2430, 6852);
        ObserveGround(2436, 6852);
        ObserveGround(2442, 6852);
        ObserveGround(2448, 6852);
        ObserveGround(2412, 6846);
        ObserveGround(2418, 6846);
        ObserveGround(2424, 6846);
        ObserveGround(2430, 6846);
        ObserveGround(2436, 6846);
        ObserveGround(2442, 6846);
        ObserveGround(2448, 6846);
        ObserveGround(2406, 6840);
        ObserveGround(2412, 6840);
        ObserveGround(2418, 6840);
        ObserveGround(2424, 6840);
        ObserveGround(2430, 6840);
        ObserveGround(2436, 6840);
        ObserveGround(2442, 6840);
        ObserveGround(2448, 6840);
        ObserveGround(2406, 6834);
        ObserveGround(2412, 6834);
        ObserveGround(2418, 6834);
        ObserveGround(2424, 6834);
        ObserveGround(2430, 6834);
        ObserveGround(2436, 6834);
        ObserveGround(2442, 6834);
        ObserveGround(2406, 6828);
        ObserveGround(2412, 6828);
        ObserveGround(2418, 6828);
        ObserveGround(2424, 6828);
        ObserveGround(2430, 6828);
        ObserveGround(2436, 6828);
        ObserveGround(2442, 6828);
        ObserveGround(2436, 6822);
        array<Object> objects = new array<Object>;
        array<CargoBase> cargos = new array<CargoBase>;
        GetGame().GetObjectsAtPosition3D("2417.143 9 6889.885", 100, objects, cargos);
        for (int index = 0; index < objects.Count(); index++)
        {
            Object obj = objects.Get(index);
            if (!obj) continue;
            string model = obj.GetShapeName();
            if (!model.Contains("bridge_metal_25")) continue;
            vector deck = obj.ModelToWorld("0 8.054884 0");
            FPrintln(m_Log, "O;" + model + ";" + obj.GetPosition() + ";" + obj.GetOrientation() + ";" + deck);
        }
        vector spawn = m_Route.Get(0);
        spawn[1] = GetGame().SurfaceGetSeaLevel() + 0.3;
        m_Boat = BoatScript.Cast(GetGame().CreateObjectEx("Boat_01_Orange", spawn, ECE_CREATEPHYSICS));
        if (!m_Boat)
        {
            Finish("SPAWN_FAILED");
            return;
        }
        vector ahead = m_Route.Get(1) - m_Route.Get(0);
        vector orientation = ahead.VectorToAngles();
        orientation[1] = 0;
        orientation[2] = 0;
        m_Boat.SetOrientation(orientation);
        m_Boat.GetInventory().CreateAttachment("SparkPlug");
        m_Boat.Fill(BoatFluid.FUEL, m_Boat.GetFluidCapacity(BoatFluid.FUEL));
        m_HealthStart = m_Boat.GetHealth("", "Health");
        m_Start = GetGame().GetTime();
        m_Target = 1;
        FPrintln(m_Log, "SPAWN;" + m_Boat.GetPosition() + ";" + m_Boat.GetOrientation() + ";" + m_HealthStart);
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BoatTick, 100, true);
    }

    void BoatTick()
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
        float speed = velocity.Length();
        float health = m_Boat.GetHealth("", "Health");
        vector target = m_Route.Get(m_Target);
        vector delta = target - pos;
        delta[1] = 0;
        float targetDistance = delta.Length();
        float steer;
        float throttle;
        if (seconds >= 10 && seconds < 10.3)
        {
            m_Boat.EngineStart();
            m_Boat.ShiftTo(m_Boat.GetNeutralGear() + 1);
        }
        if (seconds >= 11 && m_Boat.EngineIsOn())
        {
            if (targetDistance < 5)
            {
                if (m_Target >= m_Route.Count()-1)
                {
                    Finish("OUTWARD_ROUTE_REACHED_EMPTY_BOAT_ONLY");
                    return;
                }
                m_Target++;
                target = m_Route.Get(m_Target);
                delta = target - pos;
                delta[1] = 0;
            }
            vector heading = delta.VectorToAngles();
            float error = heading[0] - orientation[0];
            while (error > 180) error -= 360;
            while (error < -180) error += 360;
            steer = Math.Clamp(error/40, -0.6, 0.6);
            throttle = 0.22;
            if (speed > 2.5) throttle = 0;
            m_Boat.SetSteering(steer);
            m_Boat.SetThrottle(throttle);
        }
        m_Tick++;
        if (m_Tick % 5 == 0)
        {
            vector propeller = m_Boat.ModelToWorld(m_Boat.PropellerGetPosition());
            string record = "B;" + seconds + ";" + pos[0] + ";" + pos[1] + ";" + pos[2] + ";" + orientation[0] + ";" + speed + ";" + health;
            record = record + ";" + m_Boat.GetFluidFraction(BoatFluid.FUEL) + ";" + m_Boat.EngineIsOn() + ";" + m_Boat.GetCurrentGear();
            record = record + ";" + propeller[1] + ";" + GetGame().GetWaterDepth(propeller) + ";" + m_Boat.GetSteering() + ";" + m_Boat.GetThrottle() + ";" + m_Target;
            FPrintln(m_Log, record);
        }
        if (health < m_HealthStart - 1) Finish("DAMAGE_STOP");
        else if (seconds > 20 && !m_Boat.EngineIsOn()) Finish("ENGINE_STOPPED");
        else if (targetDistance > 40) Finish("OFF_ROUTE_STOP");
        else if (seconds > 180) Finish("TIMEOUT_CONTROL_INCONCLUSIVE");
    }

    void Finish(string reason)
    {
        m_Stopped = true;
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BoatTick);
        if (m_Boat)
        {
            m_Boat.SetThrottle(0);
            m_Boat.SetSteering(0);
            m_Boat.EngineStop();
        }
        if (m_Log)
        {
            FPrintln(m_Log, "END;" + reason);
            CloseFile(m_Log);
            m_Log = 0;
        }
    }

    void ~BalticBoatMission()
    {
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BeginBoatTrial);
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BoatTick);
        if (m_Log) CloseFile(m_Log);
    }

    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        pos = "2357.84 9.2 6899.01";
        pos[1] = GetGame().SurfaceY(pos[0],pos[2]) + 0.2;
        return super.CreateCharacter(identity,pos,ctx,characterName);
    }
}

Mission CreateCustomMission(string path)
{
    return new BalticBoatMission();
}
