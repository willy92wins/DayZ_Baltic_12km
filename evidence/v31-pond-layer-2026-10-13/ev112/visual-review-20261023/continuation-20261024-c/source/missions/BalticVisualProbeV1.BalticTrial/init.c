// Dedicated-server measurements only. No client state, RPC, spawn or player control.
// game.c:923,1176-1200; dayzphysics.c:199,211; Object.c:503 (live P:/scripts).
void main()
{
    GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0);
    Weather weather = GetGame().GetWeather();
    weather.MissionWeather(true);
    weather.GetOvercast().SetLimits(0.1, 0.1);
    weather.GetOvercast().Set(0.1, 0, 3600);
    weather.GetRain().SetLimits(0, 0);
    weather.GetRain().Set(0, 0, 3600);
    weather.SetWindMaximumSpeed(20);
    weather.SetWindFunctionParams(0, 0, 1);
    weather.GetWindMagnitude().SetLimits(0.1, 0.1);
    weather.GetWindMagnitude().Set(0.1, 0, 3600);
}

class BalticVisualProbeV1Mission: MissionServer
{
    protected ref array<string> m_Rows = new array<string>;
    protected ref array<string> m_Fields = new array<string>;
    protected ref array<Object> m_Objects = new array<Object>;
    protected ref array<CargoBase> m_Proxies = new array<CargoBase>;
    protected ref set<Object> m_Hits = new set<Object>;
    protected int m_StartMs;
    protected int m_Index;
    protected bool m_Ready;
    protected bool m_Done;
    protected bool m_Loaded;
    protected int m_QueryAfter;

    void LogRow(string row)
    {
        FileHandle file = OpenFile("$profile:baltic_visual_probe_v1.log", FileMode.APPEND);
        if (!file) { m_Done = true; return; }
        FPrintln(file, row);
        CloseFile(file);
    }

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        FileHandle file = OpenFile("$profile:baltic_visual_probe_v1.log", FileMode.WRITE);
        if (!file) return;
        FPrintln(file, "BALTIC_VISUAL_PROBE_V3;BalticTrial");
        CloseFile(file);
        FileHandle input = OpenFile("$mission:points.csv", FileMode.READ);
        if (!input) { LogRow("FAIL;NO_POINTS"); return; }
        string inputRow;
        while (FGets(input, inputRow) >= 0)
        {
            if (inputRow == "") continue;
            m_Fields.Clear();
            inputRow.Split(";", m_Fields);
            if (m_Fields.Count() != 2) { CloseFile(input); LogRow("FAIL;SCHEMA"); return; }
            m_Rows.Insert(inputRow);
        }
        CloseFile(input);
        m_Ready = m_Rows.Count() > 0;
        m_StartMs = GetGame().GetTime() + 10000;
        LogRow("BEGIN;" + m_Rows.Count());
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || !m_Ready || m_Done) return;
        if (GetGame().GetTime() < m_StartMs) return;
        vector pos;
        vector above;
        vector below;
        vector contact;
        vector normal;
        vector bulletContact;
        vector bulletNormal;
        Object bulletObject;
        Object hitObject;
        float ground;
        float waterSurface;
        float waterDepth;
        float roadHeight;
        float seaRefA;
        float seaRefB;
        float seaRefC;
        bool seaRefsValid;
        int queryTime;
        bool isSea;
        bool isPond;
        float fraction;
        int component;
        bool rvHit;
        bool bulletHit;
        string row;
        string shapes;
        string bulletShape;
        if (m_Index < m_Rows.Count())
        {
            m_Fields.Clear();
            m_Rows[m_Index].Split(";", m_Fields);
            pos = m_Fields[1].ToVector();
            // Allow a settlement interval, then refresh the native WRP references.
            // A server without players discards these objects between frames.
            if (!m_Loaded)
            {
                m_Objects.Clear();
                m_Proxies.Clear();
                GetGame().GetObjectsAtPosition(Vector(pos[0], 0, pos[2]), 40.0, m_Objects, m_Proxies);
                m_Loaded = true;
                m_QueryAfter = GetGame().GetTime() + 100;
                return;
            }
            if (GetGame().GetTime() < m_QueryAfter) return;
            m_Objects.Clear();
            m_Proxies.Clear();
            GetGame().GetObjectsAtPosition(Vector(pos[0], 0, pos[2]), 40.0, m_Objects, m_Proxies);
            ground = GetGame().SurfaceY(pos[0], pos[2]);
            above = Vector(pos[0], ground + 100, pos[2]);
            below = Vector(pos[0], ground - 10, pos[2]);
            m_Hits.Clear();
            contact = "0 0 0";
            normal = "0 0 0";
            component = -1;
            rvHit = DayZPhysics.RaycastRV(above, below, contact, normal, component, m_Hits, null, null, true, false, ObjIntersectGeom, 0.0, CollisionFlags.NEARESTCONTACT);
            shapes = "";
            for (int hitIndex = 0; hitIndex < m_Hits.Count(); hitIndex++)
            {
                hitObject = m_Hits.Get(hitIndex);
                if (hitObject) shapes = shapes + hitObject.GetShapeName() + "|";
            }
            bulletObject = null;
            bulletContact = "0 0 0";
            bulletNormal = "0 0 0";
            fraction = 0;
            bulletHit = DayZPhysics.RayCastBullet(above, below, PhxInteractionLayers.BUILDING, null, bulletObject, bulletContact, bulletNormal, fraction);
            bulletShape = "";
            if (bulletObject) bulletShape = bulletObject.GetShapeName();
            // Finish native queries before assembling the output string. A first
            // native object query can initialize scripts and emit config strings.
            isSea = GetGame().SurfaceIsSea(pos[0], pos[2]);
            isPond = GetGame().SurfaceIsPond(pos[0], pos[2]);
            waterSurface = GetGame().GetWaterSurfaceHeightNoFakeWave(above);
            waterDepth = GetGame().GetWaterDepth(Vector(pos[0], ground + 0.01, pos[2]));
            roadHeight = GetGame().SurfaceRoadY3D(pos[0], ground + 100.0, pos[2], RoadSurfaceDetection.UNDER);
            // Three prevalidated, pond-free deep-sea points, sampled in this same
            // frame: the engine sea level changes during the sequential survey.
            seaRefsValid = GetGame().SurfaceIsSea(2400, 7000) && !GetGame().SurfaceIsPond(2400, 7000);
            seaRefsValid = seaRefsValid && GetGame().SurfaceIsSea(2430, 7020) && !GetGame().SurfaceIsPond(2430, 7020);
            seaRefsValid = seaRefsValid && GetGame().SurfaceIsSea(2410, 7040) && !GetGame().SurfaceIsPond(2410, 7040);
            seaRefA = GetGame().GetWaterSurfaceHeightNoFakeWave("2400 100 7000");
            seaRefB = GetGame().GetWaterSurfaceHeightNoFakeWave("2430 100 7020");
            seaRefC = GetGame().GetWaterSurfaceHeightNoFakeWave("2410 100 7040");
            queryTime = GetGame().GetTime();
            row = "P;" + m_Fields[0] + ";" + ground;
            row = row + ";" + isSea;
            row = row + ";" + isPond;
            row = row + ";" + waterSurface;
            row = row + ";" + waterDepth;
            row = row + ";" + roadHeight;
            row = row + ";" + m_Objects.Count() + ";" + rvHit + ";" + contact + ";" + shapes;
            row = row + ";" + bulletHit + ";" + bulletContact + ";" + bulletShape;
            row = row + ";" + seaRefA + ";" + seaRefB + ";" + seaRefC + ";" + seaRefsValid + ";" + queryTime;
            row = row + ";" + normal + ";" + bulletNormal;
            LogRow(row);
            if (m_Done) return;
            m_Index++;
            m_Loaded = false;
        }
        if (m_Index == m_Rows.Count())
        {
            LogRow("END;" + m_Rows.Count());
            m_Done = true;
        }
    }
}
Mission CreateCustomMission(string path) { return new BalticVisualProbeV1Mission(); }
