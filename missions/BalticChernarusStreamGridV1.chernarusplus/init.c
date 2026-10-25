// Server-only grid probe of vanilla Chernarus stream pieces: terrain and water height on a 1 m grid around each centre.
// APIs: game.c:1162 SurfaceY, GetWaterSurfaceHeightNoFakeWave and GetWaterDepth at ground + 0.01 (as
// BalticVanillaWaterSurveyV1: from 50 m up the pitched stream pieces are not found); no RPC, no edits.
void main()
{
    GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0);
    Weather weather = GetGame().GetWeather();
    weather.MissionWeather(true);
    weather.GetOvercast().SetLimits(0.1, 0.1);
    weather.GetOvercast().Set(0.1, 0, 3600);
    weather.GetRain().SetLimits(0, 0);
    weather.GetRain().Set(0, 0, 3600);
}

class BalticChernarusStreamGridV1Mission: MissionServer
{
    protected ref array<string> m_Rows = new array<string>;
    protected ref array<string> m_Fields = new array<string>;
    protected ref array<Object> m_Objects = new array<Object>;
    protected ref array<CargoBase> m_Proxies = new array<CargoBase>;
    protected int m_Next;
    protected int m_StartMs;
    protected bool m_Ready;
    protected bool m_Done;

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer()) return;
        FileHandle file = OpenFile("$profile:baltic_chern_stream_grid_v1.log", FileMode.WRITE);
        if (!file) return;
        FPrintln(file, "BALTIC_CHERN_STREAM_GRID_V1;" + GetGame().GetWorldName());
        CloseFile(file);
        FileHandle input = OpenFile("$mission:points.csv", FileMode.READ);
        if (!input) return;
        string row;
        while (FGets(input, row) >= 0)
        {
            if (row != "") m_Rows.Insert(row);
        }
        CloseFile(input);
        m_Ready = m_Rows.Count() > 0;
        m_StartMs = GetGame().GetTime() + 10000;
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || !m_Ready || m_Done) return;
        if (GetGame().GetTime() < m_StartMs) return;
        if (m_Next >= m_Rows.Count())
        {
            FileHandle endFile = OpenFile("$profile:baltic_chern_stream_grid_v1.log", FileMode.APPEND);
            if (endFile) { FPrintln(endFile, "END;" + m_Rows.Count()); CloseFile(endFile); }
            m_Done = true;
            return;
        }
        m_Fields.Clear();
        m_Rows[m_Next].Split(";", m_Fields);
        vector c = m_Fields[1].ToVector();
        // as BalticVanillaWaterSurveyV1 (init.c:78): touching the objects makes the server answer water queries there;
        // load and sample in the same frame and keep every reference (m_Objects is never cleared)
        m_Proxies.Clear();
        int before = m_Objects.Count();
        GetGame().GetObjectsAtPosition(Vector(c[0], 0, c[2]), 60.0, m_Objects, m_Proxies);
        FileHandle note = OpenFile("$profile:baltic_chern_stream_grid_v1.log", FileMode.APPEND);
        if (note) { FPrintln(note, "L;" + m_Fields[0] + ";" + (m_Objects.Count() - before)); CloseFile(note); }
        FileHandle file = OpenFile("$profile:baltic_chern_stream_grid_v1.log", FileMode.APPEND);
        if (!file) { m_Done = true; return; }
        for (int i = -20; i <= 20; i++)
        {
            for (int j = -20; j <= 20; j++)
            {
                float x = c[0] + i;
                float z = c[2] + j;
                float ground = GetGame().SurfaceY(x, z);
                float water = GetGame().GetWaterSurfaceHeightNoFakeWave(Vector(x, ground + 50, z));
                float depth = GetGame().GetWaterDepth(Vector(x, ground + 0.01, z));
                FPrintln(file, "G;" + m_Fields[0] + ";" + i + ";" + j + ";" + ground + ";" + water + ";" + depth);
            }
        }
        CloseFile(file);
        m_Next++;
    }
}
Mission CreateCustomMission(string path) { return new BalticChernarusStreamGridV1Mission(); }
