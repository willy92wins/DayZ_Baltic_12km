// Server-only graph probe. Template markers are frozen before launch.
// aiworld.c:65,98,122; game.c:923,1177. No client state or RPC.
void main() { GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0); }
class BalticKit7NavV1Mission: MissionServer
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

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer()) return;
        FileHandle output = OpenFile("$profile:baltic_kit7_nav_3325b685-d8cf-42d1-a476-aa2a3fe2e857.log", FileMode.WRITE);
        if (!output) { Print("KIT7_NAV_FAIL_OPEN_OUTPUT"); return; }
        FPrintln(output, "BALTIC_KIT7_NAV_V1;" + GetGame().GetWorldName() + ";3325b685-d8cf-42d1-a476-aa2a3fe2e857");
        FileHandle input = OpenFile("$mission:queries.csv", FileMode.READ);
        if (!input) { FPrintln(output, "FAIL;NO_INPUT"); CloseFile(output); return; }
        string row;
        while (FGets(input, row) >= 0)
        {
            if (row == "") continue;
            m_Fields.Clear();
            row.Split(";", m_Fields);
            if (m_Fields.Count() != 3) { FPrintln(output, "FAIL;SCHEMA"); CloseFile(input); CloseFile(output); return; }
            m_Rows.Insert(row);
        }
        CloseFile(input);
        if (m_Rows.Count() != 607) { FPrintln(output, "FAIL;COUNT"); CloseFile(output); return; }
        CloseFile(output);
        m_Walk.SetFlags(PGPolyFlags.WALK, PGPolyFlags.SWIM | PGPolyFlags.SWIM_SEA | PGPolyFlags.DISABLED, PGPolyFlags.NONE);
        m_None.SetFlags(PGPolyFlags.NONE, PGPolyFlags.ALL, PGPolyFlags.NONE);
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
        FileHandle output = OpenFile("$profile:baltic_kit7_nav_3325b685-d8cf-42d1-a476-aa2a3fe2e857.log", FileMode.APPEND);
        if (!output) { Print("KIT7_NAV_FAIL_APPEND_OUTPUT"); m_Done = true; return; }
        m_Fields.Clear();
        m_Rows[m_Index].Split(";", m_Fields);
        vector start = m_Fields[1].ToVector();
        vector goal = m_Fields[2].ToVector();
        PGFilter filter = m_Walk;
        // The historical NONE control keeps its exact name and filter.
        if (m_Fields[0] == "negative") filter = m_None;
        AIWorld ai = GetGame().GetWorld().GetAIWorld();
        vector a, b;
        bool sa = ai.SampleNavmeshPosition(start, 2, filter, a);
        bool sb = ai.SampleNavmeshPosition(goal, 2, filter, b);
        m_Path.Clear();
        bool found = false;
        if (sa && sb) found = ai.FindPath(a, b, filter, m_Path);
        FPrintln(output, "Q;" + m_Fields[0] + ";" + sa + ";" + sb + ";" + found + ";" + m_Path.Count() + ";" + start.ToString() + ";" + goal.ToString() + ";" + a.ToString() + ";" + b.ToString());
        int i;
        vector p, warm, groundSample, roadSample;
        float pointX, pointZ, groundY, roadY;
        string pointText, groundText, roadText;
        for (i = 0; i < m_Path.Count(); i++)
        {
            p = m_Path[i];
            pointX = p[0];
            pointZ = p[2];
            warm = Vector(pointX, 0, pointZ);
            m_Objects.Clear();
            m_Proxies.Clear();
            GetGame().GetObjectsAtPosition(warm, 40, m_Objects, m_Proxies);
            groundY = GetGame().SurfaceY(pointX, pointZ);
            roadY = GetGame().SurfaceRoadY(pointX, pointZ);
            groundSample = Vector(pointX, groundY, pointZ);
            roadSample = Vector(pointX, roadY, pointZ);
            pointText = p.ToString();
            groundText = groundSample.ToString();
            roadText = roadSample.ToString();
            FPrintln(output, "P;" + m_Fields[0] + ";" + i + ";" + pointText + ";" + groundText + ";" + roadText);
        }
        m_Index = m_Index + 1;
        if (m_Index == m_Rows.Count())
        {
            FPrintln(output, "END;" + m_Index);
            m_Done = true;
        }
        CloseFile(output);
    }
}
Mission CreateCustomMission(string path) { return new BalticKit7NavV1Mission(); }
