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
    weather.SetWindMaximumSpeed(20);
    weather.SetWindFunctionParams(0, 0, 1);
    weather.SetWindSpeed(0.1);
}

class BalticV30WaterTemporalV3Mission: MissionServer
{
    protected ref array<string> m_Rows = new array<string>;
    protected ref array<string> m_Fields = new array<string>;
    protected int m_NextSampleMs;
    protected int m_Sample;
    protected bool m_Ready;
    protected bool m_Done;

    void LogRow(string row)
    {
        FileHandle file = OpenFile("$profile:baltic_v30_water_temporal_v3.log", FileMode.APPEND);
        if (!file) { m_Done = true; return; }
        FPrintln(file, row);
        CloseFile(file);
    }

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        FileHandle file = OpenFile("$profile:baltic_v30_water_temporal_v3.log", FileMode.WRITE);
        if (!file) return;
        FPrintln(file, "BALTIC_V30_WATER_TEMPORAL_V3;BalticTrial");
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
        m_NextSampleMs = GetGame().GetTime() + 5000;
        FileHandle orderFile = OpenFile("$profile:baltic_v30_water_order_v3.log", FileMode.WRITE);
        if (!orderFile) { m_Ready = false; return; }
        FPrintln(orderFile, "BALTIC_V30_WATER_ORDER_V3;BalticTrial");
        CloseFile(orderFile);
        LogRow("BEGIN;" + m_Rows.Count() + ";302;2");
    }

    void SampleAll()
    {
        vector pos;
        vector above;
        float ground;
        float noFake;
        float withFake;
        float beforePresence;
        float afterDepth;
        float bedDepth;
        bool sea;
        bool pond;
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
            beforePresence = GetGame().GetWaterSurfaceHeightNoFakeWave(above);
            sea = GetGame().SurfaceIsSea(pos[0], pos[2]);
            pond = GetGame().SurfaceIsPond(pos[0], pos[2]);
            noFake = GetGame().GetWaterSurfaceHeightNoFakeWave(above);
            withFake = GetGame().GetWaterSurfaceHeightWithFakeWave(above);
            row = "T;" + m_Sample + ";" + m_Fields[0];
            row = row + ";" + timeMs + ";" + ground;
            row = row + ";" + sea;
            row = row + ";" + pond;
            row = row + ";" + noFake + ";" + withFake;
            bedDepth = GetGame().GetWaterDepth(Vector(pos[0], ground + 0.01, pos[2]));
            afterDepth = GetGame().GetWaterSurfaceHeightNoFakeWave(above);
            row = row + ";" + bedDepth;
            row = row + ";" + GetGame().GetWaterDepth(above);
            row = row + ";" + GetGame().GetWaterDepth(Vector(pos[0], noFake - 1, pos[2]));
            row = row + ";" + GetGame().SurfaceGetSeaLevel();
            row = row + ";" + GetGame().SurfaceGetSeaWaveCurrent();
            row = row + ";" + GetGame().SurfaceGetSeaWaveMax();
            row = row + ";" + GetGame().GetWeather().GetWindSpeed();
            row = row + ";" + GetGame().GetWeather().GetOvercast().GetActual();
            LogRow(row);
            FileHandle orderFile = OpenFile("$profile:baltic_v30_water_order_v3.log", FileMode.APPEND);
            if (!orderFile) { m_Done = true; return; }
            string orderRow = "O;" + m_Sample + ";" + m_Fields[0] + ";" + timeMs;
            orderRow = orderRow + ";" + beforePresence + ";" + noFake + ";" + afterDepth;
            FPrintln(orderFile, orderRow);
            CloseFile(orderFile);
        }
    }

    void StartStorm()
    {
        Weather weather = GetGame().GetWeather();
        weather.GetOvercast().SetLimits(1, 1);
        weather.GetOvercast().Set(1, 0, 3600);
        weather.SetWindFunctionParams(1, 1, 1);
        weather.SetWindSpeed(20);
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || !m_Ready || m_Done) return;
        if (GetGame().GetTime() < m_NextSampleMs) return;
        SampleAll();
        m_Sample++;
        // Schedule after the complete batch using the same clock as the recorded samples.
        m_NextSampleMs = GetGame().GetTime() + 2000;
        if (m_Sample == 151)
        {
            // Calm phase complete: switch to the storm and let waves settle.
            StartStorm();
            m_NextSampleMs = GetGame().GetTime() + 30000;
        }
        if (m_Sample == 302)
        {
            LogRow("END;302;17");
            FileHandle orderFile = OpenFile("$profile:baltic_v30_water_order_v3.log", FileMode.APPEND);
            if (orderFile) { FPrintln(orderFile, "END;302;17"); CloseFile(orderFile); }
            m_Done = true;
        }
    }
}
Mission CreateCustomMission(string path) { return new BalticV30WaterTemporalV3Mission(); }
