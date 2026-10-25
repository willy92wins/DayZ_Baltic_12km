// Dedicated terrain measurements. No player, object, RPC or client mutations.
// Native signatures: P:/scripts/3_Game/global/game.c:1176,1196,1197.
void main() {}

class BalticForestBoundaryV1Mission: MissionServer
{
    protected ref array<string> m_Rows = new array<string>;
    protected ref array<string> m_Fields = new array<string>;
    protected int m_Index;
    protected int m_StartMs;
    protected bool m_Ready;
    protected bool m_Done;

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        FileHandle output = OpenFile("$profile:baltic_forest_boundary_v1.log", FileMode.WRITE);
        if (!output) return;
        FPrintln(output, "BALTIC_FOREST_BOUNDARY_V1;BalticTrial");
        FileHandle identity = OpenFile("$mission:identity.txt", FileMode.READ);
        if (!identity) { FPrintln(output, "FAIL;NO_IDENTITY"); CloseFile(output); return; }
        string surveyId;
        FGets(identity, surveyId);
        CloseFile(identity);
        if (surveyId == "") { FPrintln(output, "FAIL;EMPTY_IDENTITY"); CloseFile(output); return; }
        FPrintln(output, "SURVEY;" + surveyId);
        FileHandle input = OpenFile("$mission:points.csv", FileMode.READ);
        if (!input) { FPrintln(output, "FAIL;NO_POINTS"); CloseFile(output); return; }
        string row;
        while (FGets(input, row) >= 0)
        {
            if (row == "") continue;
            m_Fields.Clear();
            row.Split(";", m_Fields);
            if (m_Fields.Count() != 2)
            {
                CloseFile(input);
                FPrintln(output, "FAIL;SCHEMA");
                CloseFile(output);
                return;
            }
            m_Rows.Insert(row);
        }
        CloseFile(input);
        FPrintln(output, "BEGIN;" + m_Rows.Count());
        CloseFile(output);
        m_Ready = m_Rows.Count() > 0;
        m_StartMs = GetGame().GetTime() + 10000;
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!m_Ready || m_Done || GetGame().GetTime() < m_StartMs) return;
        FileHandle output = OpenFile("$profile:baltic_forest_boundary_v1.log", FileMode.APPEND);
        if (!output) { m_Done = true; return; }
        // SurfaceY is native terrain; unlike object raycasts it needs no WRP
        // object streaming/settlement. Bound each frame to 128 measurements.
        for (int batch = 0; batch < 128 && m_Index < m_Rows.Count(); batch++)
        {
            m_Fields.Clear();
            m_Rows[m_Index].Split(";", m_Fields);
            vector pos = m_Fields[1].ToVector();
            float height = GetGame().SurfaceY(pos[0], pos[2]);
            bool sea = GetGame().SurfaceIsSea(pos[0], pos[2]);
            bool pond = GetGame().SurfaceIsPond(pos[0], pos[2]);
            int time = GetGame().GetTime();
            string result = "P;" + m_Fields[0] + ";" + height + ";" + sea + ";" + pond + ";" + time;
            FPrintln(output, result);
            m_Index++;
        }
        if (m_Index == m_Rows.Count())
        {
            FPrintln(output, "END;" + m_Rows.Count());
            m_Done = true;
        }
        CloseFile(output);
    }
}

Mission CreateCustomMission(string path) { return new BalticForestBoundaryV1Mission(); }
