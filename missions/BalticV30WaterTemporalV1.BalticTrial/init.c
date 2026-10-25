// Server owns all measurements; no RPC, player movement, or terrain edits.
void main()
{
    GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0);
    Weather weather = GetGame().GetWeather();
    weather.MissionWeather(true);
    weather.GetOvercast().SetLimits(0.1, 0.1);
    weather.GetOvercast().Set(0.1, 0, 3600);
    weather.GetRain().SetLimits(0, 0);
    weather.GetRain().Set(0, 0, 3600);
    weather.GetFog().SetLimits(0, 0);
    weather.GetFog().Set(0, 0, 3600);
    weather.GetSnowfall().SetLimits(0, 0);
    weather.GetSnowfall().Set(0, 0, 3600);
}

class BalticV30WaterTemporalV1Mission: MissionServer
{
    protected ref array<string> m_Rows = new array<string>;
    protected ref array<string> m_Fields = new array<string>;
    protected float m_Elapsed;
    protected float m_NextSample = 5;
    protected int m_Sample;
    protected bool m_Ready;
    protected bool m_Done;

    void LogRow(string row)
    {
        FileHandle file = OpenFile("$profile:baltic_v30_water_temporal_v1.log", FileMode.APPEND);
        if (!file) { m_Done = true; return; }
        FPrintln(file, row);
        CloseFile(file);
    }

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        FileHandle file = OpenFile("$profile:baltic_v30_water_temporal_v1.log", FileMode.WRITE);
        if (!file) return;
        FPrintln(file, "BALTIC_V30_WATER_TEMPORAL_V1;BalticTrial");
        CloseFile(file);
        FileHandle input = OpenFile("$mission:points.csv", FileMode.READ);
        if (!input) { LogRow("FAIL;NO_POINTS"); return; }
        string row;
        while (FGets(input, row) >= 0)
        {
            if (row == "") continue;
            m_Fields.Clear();
            row.Split(";", m_Fields);
            if (m_Fields.Count() != 2) { CloseFile(input); LogRow("FAIL;SCHEMA"); return; }
            m_Rows.Insert(row);
        }
        CloseFile(input);
        m_Ready = m_Rows.Count() == 17;
        LogRow("BEGIN;" + m_Rows.Count() + ";151;2");
    }

    void SampleAll()
    {
        vector pos;
        vector above;
        float ground;
        float noFake;
        float withFake;
        string row;
        int timeMs;
        for (int i = 0; i < m_Rows.Count(); i++)
        {
            m_Fields.Clear();
            m_Rows[i].Split(";", m_Fields);
            pos = m_Fields[1].ToVector();
            ground = GetGame().SurfaceY(pos[0], pos[2]);
            above = Vector(pos[0], ground + 100, pos[2]);
            timeMs = GetGame().GetTime();
            noFake = GetGame().GetWaterSurfaceHeightNoFakeWave(above);
            withFake = GetGame().GetWaterSurfaceHeightWithFakeWave(above);
            row = "T;" + m_Sample + ";" + m_Fields[0];
            row = row + ";" + timeMs + ";" + ground;
            row = row + ";" + GetGame().SurfaceIsSea(pos[0], pos[2]);
            row = row + ";" + GetGame().SurfaceIsPond(pos[0], pos[2]);
            row = row + ";" + noFake + ";" + withFake;
            row = row + ";" + GetGame().GetWaterDepth(Vector(pos[0], ground + 0.01, pos[2]));
            row = row + ";" + GetGame().GetWaterDepth(above);
            row = row + ";" + GetGame().GetWaterDepth(Vector(pos[0], noFake - 1, pos[2]));
            row = row + ";" + GetGame().SurfaceGetSeaLevel();
            row = row + ";" + GetGame().SurfaceGetSeaWaveCurrent();
            row = row + ";" + GetGame().SurfaceGetSeaWaveMax();
            LogRow(row);
        }
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || !m_Ready || m_Done) return;
        m_Elapsed = m_Elapsed + timeslice;
        if (m_Elapsed < m_NextSample) return;
        SampleAll();
        m_Sample++;
        // Schedule from the actual tick: never backfill missing temporal samples.
        m_NextSample = m_Elapsed + 2;
        if (m_Sample == 151)
        {
            LogRow("END;151;17");
            m_Done = true;
        }
    }
}
Mission CreateCustomMission(string path) { return new BalticV30WaterTemporalV1Mission(); }
