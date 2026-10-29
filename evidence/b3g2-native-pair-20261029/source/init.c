// Server-only diagnostic. No spawning, world edits, player or camera control.
// Native signatures: dayzphysics.c:199/211; enentity.c:288.
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

class BalticContactB3GMission: MissionServer
{
    protected ref array<string> m_Rows = new array<string>;
    protected ref array<string> m_Fields = new array<string>;
    protected ref array<string> m_ObjectRows = new array<string>;
    protected ref array<Object> m_Objects = new array<Object>;
    protected ref array<CargoBase> m_Proxies = new array<CargoBase>;
    protected ref set<Object> m_RH = new set<Object>;
    protected ref set<Object> m_RL = new set<Object>;
    protected int m_StartMs;
    protected int m_Index;
    protected int m_Round;
    protected int m_QueryAfter;
    protected bool m_Ready;
    protected bool m_Done;
    protected bool m_Loaded;
    protected bool m_Linked;

    void LogRow(string row)
    {
        FileHandle file = OpenFile("$profile:baltic_contact_b3g.log", FileMode.APPEND);
        if (!file) { m_Done = true; return; }
        FPrintln(file, row);
        CloseFile(file);
    }

    void LogHit(string key, string code, int index, Object obj)
    {
        bool valid = false;
        string shape = "";
        vector pos = "0 0 0";
        if (obj)
        {
            valid = true;
            shape = obj.GetShapeName();
            pos = obj.GetPosition();
        }
        LogRow("H;" + key + ";" + code + ";" + index + ";" + valid + ";" + shape + ";" + pos);
    }

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        FileHandle file = OpenFile("$profile:baltic_contact_b3g.log", FileMode.WRITE);
        if (!file) return;
        FPrintln(file, "BALTIC_CONTACT_B3G;BalticTrial");
        CloseFile(file);
        FileHandle input = OpenFile("$mission:points.csv", FileMode.READ);
        if (!input) { LogRow("FAIL;NO_POINTS"); return; }
        string inputRow;
        while (FGets(input, inputRow) >= 0)
        {
            if (inputRow == "") continue;
            m_Fields.Clear();
            inputRow.Split(";", m_Fields);
            if (m_Fields.Count() != 4) { CloseFile(input); LogRow("FAIL;SCHEMA"); return; }
            m_Rows.Insert(inputRow);
        }
        CloseFile(input);
        if (m_Rows.Count() != 90) { LogRow("FAIL;COUNT"); return; }
        m_Ready = true;
        m_StartMs = GetGame().GetTime() + 10000;
        LogRow("BEGIN;90;3");
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || !m_Ready || m_Done) return;
        if (GetGame().GetTime() < m_StartMs) return;
        vector pos;
        vector high;
        vector low;
        vector end;
        vector rhPos = "0 0 0";
        vector rlPos = "0 0 0";
        vector bhPos = "0 0 0";
        vector blPos = "0 0 0";
        vector rhNormal = "0 0 0";
        vector rlNormal = "0 0 0";
        vector bhNormal = "0 0 0";
        vector blNormal = "0 0 0";
        vector matrix[4];
        vector objectPos;
        Object bhObject = null;
        Object blObject = null;
        Object obj;
        float ground;
        float bhFraction = 0;
        float blFraction = 0;
        int rhComponent = -1;
        int rlComponent = -1;
        int t0;
        int t1;
        int t2;
        int waterStart;
        int waterEnd;
        bool isSea;
        bool isPond;
        float surface;
        float depth;
        float road;
        bool seaA;
        bool pondA;
        bool seaB;
        bool pondB;
        bool seaC;
        bool pondC;
        float refA;
        float refB;
        float refC;
        int oi;
        int hi;
        int li;
        int rowIndex;
        bool rhHit;
        bool rlHit;
        bool bhHit;
        bool blHit;
        bool valid;
        string shape;
        string key;
        string row;
        m_Fields.Clear();
        m_Rows[m_Index].Split(";", m_Fields);
        pos = m_Fields[2].ToVector();
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
        pos[1] = ground;
        high = Vector(pos[0], ground + 100, pos[2]);
        low = Vector(pos[0], m_Fields[3].ToFloat(), pos[2]);
        end = Vector(pos[0], ground - 10, pos[2]);
        m_RH.Clear();
        m_RL.Clear();
        t0 = GetGame().GetTime();
        rhHit = DayZPhysics.RaycastRV(high, end, rhPos, rhNormal, rhComponent, m_RH, null, null, true, false, ObjIntersectGeom, 0.0, CollisionFlags.NEARESTCONTACT);
        rlHit = DayZPhysics.RaycastRV(low, end, rlPos, rlNormal, rlComponent, m_RL, null, null, true, false, ObjIntersectGeom, 0.0, CollisionFlags.NEARESTCONTACT);
        bhHit = DayZPhysics.RayCastBullet(high, end, PhxInteractionLayers.BUILDING, null, bhObject, bhPos, bhNormal, bhFraction);
        blHit = DayZPhysics.RayCastBullet(low, end, PhxInteractionLayers.BUILDING, null, blObject, blPos, blNormal, blFraction);
        t1 = GetGame().GetTime();
        waterStart = GetGame().GetTime();
        isSea = GetGame().SurfaceIsSea(pos[0], pos[2]);
        isPond = GetGame().SurfaceIsPond(pos[0], pos[2]);
        surface = GetGame().GetWaterSurfaceHeightNoFakeWave(high);
        depth = GetGame().GetWaterDepth(Vector(pos[0], ground + 0.01, pos[2]));
        road = GetGame().SurfaceRoadY3D(pos[0], ground + 100, pos[2], RoadSurfaceDetection.UNDER);
        seaA = GetGame().SurfaceIsSea(2400, 7000);
        pondA = GetGame().SurfaceIsPond(2400, 7000);
        refA = GetGame().GetWaterSurfaceHeightNoFakeWave("2400 100 7000");
        seaB = GetGame().SurfaceIsSea(2430, 7020);
        pondB = GetGame().SurfaceIsPond(2430, 7020);
        refB = GetGame().GetWaterSurfaceHeightNoFakeWave("2430 100 7020");
        seaC = GetGame().SurfaceIsSea(2410, 7040);
        pondC = GetGame().SurfaceIsPond(2410, 7040);
        refC = GetGame().GetWaterSurfaceHeightNoFakeWave("2410 100 7040");
        waterEnd = GetGame().GetTime();
        // Separate result containers survive until all four native calls finish.
        key = "" + m_Round + ";" + m_Fields[0] + ";" + m_Fields[1];
        m_ObjectRows.Clear();
        for (oi = 0; oi < m_Objects.Count(); oi++)
        {
            obj = m_Objects[oi];
            valid = false;
            shape = "";
            objectPos = "0 0 0";
            matrix[0] = "0 0 0";
            matrix[1] = "0 0 0";
            matrix[2] = "0 0 0";
            matrix[3] = "0 0 0";
            if (obj)
            {
                valid = true;
                shape = obj.GetShapeName();
                objectPos = obj.GetPosition();
                if (!m_Linked) LogRow("LINK;GetTransform;BEGIN");
                obj.GetTransform(matrix);
                if (!m_Linked) LogRow("LINK;GetTransform;OK");
                m_Linked = true;
            }
            row = "O;" + key + ";" + oi + ";" + valid + ";" + shape + ";" + objectPos;
            row = row + ";" + matrix[0] + ";" + matrix[1] + ";" + matrix[2] + ";" + matrix[3];
            m_ObjectRows.Insert(row);
        }
        t2 = GetGame().GetTime();
        if (!m_Linked) { LogRow("FAIL;NO_OBJECT_FOR_LINK_MARKER"); m_Done = true; return; }
        row = "Q;" + key + ";" + t0 + ";" + t1 + ";" + t2 + ";" + pos + ";" + ground;
        row = row + ";" + high + ";" + low + ";" + end + ";" + m_Objects.Count() + ";" + m_Proxies.Count() + ";" + PhxInteractionLayers.BUILDING;
        LogRow(row);
        row = "W;" + key + ";" + waterStart + ";" + waterEnd + ";" + isSea + ";" + isPond + ";" + surface + ";" + depth + ";" + road;
        row = row + ";" + seaA + ";" + pondA + ";" + refA;
        row = row + ";" + seaB + ";" + pondB + ";" + refB;
        row = row + ";" + seaC + ";" + pondC + ";" + refC;
        LogRow(row);
        LogRow("R;" + key + ";RH;" + rhHit + ";" + rhPos + ";" + rhNormal + ";" + rhComponent + ";0;" + m_RH.Count());
        for (hi = 0; hi < m_RH.Count(); hi++) LogHit(key, "RH", hi, m_RH.Get(hi));
        LogRow("R;" + key + ";RL;" + rlHit + ";" + rlPos + ";" + rlNormal + ";" + rlComponent + ";0;" + m_RL.Count());
        for (li = 0; li < m_RL.Count(); li++) LogHit(key, "RL", li, m_RL.Get(li));
        LogRow("R;" + key + ";BH;" + bhHit + ";" + bhPos + ";" + bhNormal + ";-1;" + bhFraction + ";1");
        LogHit(key, "BH", 0, bhObject);
        LogRow("R;" + key + ";BL;" + blHit + ";" + blPos + ";" + blNormal + ";-1;" + blFraction + ";1");
        LogHit(key, "BL", 0, blObject);
        for (rowIndex = 0; rowIndex < m_ObjectRows.Count(); rowIndex++) LogRow(m_ObjectRows[rowIndex]);
        if (m_Done) return;
        m_Index++;
        m_Loaded = false;
        if (m_Index == 90)
        {
            m_Index = 0;
            m_Round++;
            if (m_Round == 3) { LogRow("END;270"); m_Done = true; }
        }
    }
}
Mission CreateCustomMission(string path) { return new BalticContactB3GMission(); }
