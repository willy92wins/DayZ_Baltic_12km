// Diagnostic server-only reference. No spawn, RPC, client state or world edits.
// Data: anchors -> SERVER via mission CSV; observations -> SERVER profile log only.
// APIs: aiworld.c:98,122; game.c:923,1176-1180; object.c:287,503,873.
void main() { GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0); }
class BalticChernarusNavHeightReferenceMission: MissionServer
{
    protected ref array<string> m_Rows = new array<string>;
    protected ref array<string> m_Fields = new array<string>;
    protected ref array<vector> m_Path = new array<vector>;
    protected ref array<Object> m_Objects = new array<Object>;
    protected ref array<CargoBase> m_Proxies = new array<CargoBase>;
    protected ref PGFilter m_Walk = new PGFilter;
    protected ref PGFilter m_None = new PGFilter;
    protected int m_Index;
    protected float m_Elapsed;
    protected bool m_Ready;
    protected bool m_Done;
    protected bool m_Armed;

    protected void AbortProbe(FileHandle output, string name, string reason)
    {
        FPrintln(output, "FAIL;" + name + ";" + reason);
        FPrintln(output, "END;" + m_Index);
        CloseFile(output);
        m_Done = true;
    }

    protected void WarmAt(vector point)
    {
        m_Objects.Clear();
        m_Proxies.Clear();
        GetGame().GetObjectsAtPosition(Vector(point[0], 0, point[2]), 40, m_Objects, m_Proxies);
    }

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer()) return;
        FileHandle output = OpenFile("$profile:chernarus_nav_height_69871ff0-95ee-4cab-b147-de820d95d9d8.log", FileMode.WRITE);
        if (!output) { Print("CHERNARUS_NAV_REF_FAIL_OUTPUT"); return; }
        string world = GetGame().GetWorldName();
        FPrintln(output, "CHERNARUS_NAV_HEIGHT_REFERENCE_V1;" + world + ";69871ff0-95ee-4cab-b147-de820d95d9d8;24;49");
        world.ToLower();
        if (world != "chernarusplus") { AbortProbe(output, "init", "WRONG_WORLD"); return; }
        FileHandle input = OpenFile("$mission:anchors.csv", FileMode.READ);
        if (!input) { AbortProbe(output, "init", "NO_INPUT"); return; }
        string row;
        while (FGets(input, row) >= 0)
        {
            if (row == "") continue;
            m_Fields.Clear();
            row.Split(";", m_Fields);
            if (m_Fields.Count() != 3)
            {
                CloseFile(input);
                AbortProbe(output, "init", "INPUT_SCHEMA");
                return;
            }
            m_Rows.Insert(row);
        }
        CloseFile(input);
        if (m_Rows.Count() != 24) { AbortProbe(output, "init", "INPUT_COUNT"); return; }
        m_Walk.SetFlags(PGPolyFlags.WALK, PGPolyFlags.SWIM | PGPolyFlags.SWIM_SEA | PGPolyFlags.DISABLED, PGPolyFlags.NONE);
        m_None.SetFlags(PGPolyFlags.NONE, PGPolyFlags.ALL, PGPolyFlags.NONE);
        CloseFile(output);
        m_Ready = true;
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || !m_Ready || m_Done) return;
        m_Elapsed = m_Elapsed + timeslice;
        if (!m_Armed)
        {
            if (m_Elapsed < 5) return;
            m_Armed = true;
        }
        else if (m_Elapsed < 0.1) return;
        m_Elapsed = 0;
        FileHandle output = OpenFile("$profile:chernarus_nav_height_69871ff0-95ee-4cab-b147-de820d95d9d8.log", FileMode.APPEND);
        if (!output) { Print("CHERNARUS_NAV_REF_FAIL_APPEND"); m_Done = true; return; }
        int anchorIndex = m_Index / 2;
        if (m_Index == 48) anchorIndex = 0;
        m_Fields.Clear();
        m_Rows[anchorIndex].Split(";", m_Fields);
        string anchorId = m_Fields[0];
        string expectedShape = m_Fields[1];
        expectedShape.ToLower();
        vector expected = m_Fields[2].ToVector();
        string name = anchorId + "_left";
        float q = -6;
        if (m_Index < 48 && m_Index % 2 == 1) { q = 6; name = anchorId + "_right"; }
        if (m_Index == 48) name = "negative";
        WarmAt(expected);
        Object matched;
        int matches = 0;
        foreach (Object item: m_Objects)
        {
            if (!item) continue;
            string shape = item.GetShapeName();
            shape.ToLower();
            if (shape != expectedShape) continue;
            vector delta = item.GetPosition() - expected;
            float squared = delta[0] * delta[0] + delta[1] * delta[1] + delta[2] * delta[2];
            if (squared <= 0.0025) { matches = matches + 1; matched = item; }
        }
        if (matches != 1 || !matched) { AbortProbe(output, name, "ANCHOR_NOT_UNIQUE_OR_DRIFT"); return; }
        vector position = matched.GetPosition();
        string actualShape = matched.GetShapeName();
        actualShape.ToLower();
        vector origin = matched.ModelToWorld(Vector(0, 0, 0));
        // Ten-metre offsets reduce float cancellation in world-space coordinates.
        vector tenX = matched.ModelToWorld(Vector(10, 0, 0));
        vector tenY = matched.ModelToWorld(Vector(0, 10, 0));
        vector tenZ = matched.ModelToWorld(Vector(0, 0, 10));
        vector axisX = (tenX - origin) * 0.1;
        vector axisY = (tenY - origin) * 0.1;
        vector axisZ = (tenZ - origin) * 0.1;
        vector rawStart = matched.ModelToWorld(Vector(q, 0, -6));
        vector rawGoal = matched.ModelToWorld(Vector(q, 0, 6));
        WarmAt(rawStart);
        float startGround = GetGame().SurfaceY(rawStart[0], rawStart[2]);
        float startRoad = GetGame().SurfaceRoadY(rawStart[0], rawStart[2]);
        string startType;
        GetGame().SurfaceGetType(rawStart[0], rawStart[2], startType);
        WarmAt(rawGoal);
        float goalGround = GetGame().SurfaceY(rawGoal[0], rawGoal[2]);
        float goalRoad = GetGame().SurfaceRoadY(rawGoal[0], rawGoal[2]);
        string goalType;
        GetGame().SurfaceGetType(rawGoal[0], rawGoal[2], goalType);
        FPrintln(output, "A;" + name + ";" + anchorId + ";" + matches + ";" + actualShape + ";" + expected.ToString() + ";" + position.ToString() + ";" + origin.ToString() + ";" + axisX.ToString() + ";" + axisY.ToString() + ";" + axisZ.ToString() + ";" + rawStart.ToString() + ";" + rawGoal.ToString() + ";" + startGround + ";" + startRoad + ";" + goalGround + ";" + goalRoad + ";" + startType + ";" + goalType);
        vector start = rawStart;
        vector goal = rawGoal;
        start[1] = startRoad + 0.2;
        goal[1] = goalRoad + 0.2;
        PGFilter filter = m_Walk;
        if (m_Index == 48) filter = m_None;
        AIWorld ai = GetGame().GetWorld().GetAIWorld();
        if (!ai) { AbortProbe(output, name, "NO_AI_WORLD"); return; }
        vector a = Vector(0, 0, 0);
        vector b = Vector(0, 0, 0);
        bool sa = ai.SampleNavmeshPosition(start, 2, filter, a);
        bool sb = ai.SampleNavmeshPosition(goal, 2, filter, b);
        m_Path.Clear();
        bool found = false;
        if (sa && sb) found = ai.FindPath(a, b, filter, m_Path);
        FPrintln(output, "Q;" + name + ";" + sa + ";" + sb + ";" + found + ";" + m_Path.Count() + ";" + start.ToString() + ";" + goal.ToString() + ";" + a.ToString() + ";" + b.ToString());
        for (int i = 0; i < m_Path.Count(); i++)
        {
            vector point = m_Path[i];
            WarmAt(point);
            float groundY = GetGame().SurfaceY(point[0], point[2]);
            float roadY = GetGame().SurfaceRoadY(point[0], point[2]);
            vector groundSample = Vector(point[0], groundY, point[2]);
            vector roadSample = Vector(point[0], roadY, point[2]);
            string surfaceType;
            GetGame().SurfaceGetType(point[0], point[2], surfaceType);
            FPrintln(output, "P;" + name + ";" + i + ";" + point.ToString() + ";" + groundSample.ToString() + ";" + roadSample.ToString() + ";" + surfaceType);
        }
        m_Index = m_Index + 1;
        if (m_Index == 49) { FPrintln(output, "END;49"); m_Done = true; }
        CloseFile(output);
    }
}
Mission CreateCustomMission(string path) { return new BalticChernarusNavHeightReferenceMission(); }
