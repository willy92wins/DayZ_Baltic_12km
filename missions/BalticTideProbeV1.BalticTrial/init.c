// Tide probe: the server scans the sea level over eight dates of one lunar month, then holds the first date at
// its highest tide and logs the sea every 2 s while views are taken. No RPC, player movement or terrain edits.
// APIs: world.c SetDate :51, GetDate :33; game.c SurfaceGetSeaLevelMin/Max/SeaLevel :1174-1176,
// SurfaceGetSeaWaveMax/Current :1178-1180, GetWaterSurfaceHeightNoFakeWave/WithFakeWave :1185-1187;
// weather.c GetActual :38, Set :49, SetLimits :74, GetWindSpeed :243, SetWindSpeed :251,
// SetWindMaximumSpeed :264, SetWindFunctionParams :280, MissionWeather :383.
void main()
{
    GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0);
    Weather weather = GetGame().GetWeather();
    weather.MissionWeather(true);
    weather.GetOvercast().SetLimits(0, 1);
    weather.GetOvercast().Set(0.1, 0, 3600);
    weather.GetRain().SetLimits(0, 1);
    weather.GetRain().Set(0, 0, 3600);
    weather.GetFog().SetLimits(0, 0);
    weather.GetFog().Set(0, 0, 3600);
    weather.GetSnowfall().SetLimits(0, 0);
    weather.GetSnowfall().Set(0, 0, 3600);
    weather.SetWindMaximumSpeed(20);
    weather.SetWindFunctionParams(0, 0, 1);
    weather.SetWindSpeed(0.1);
}

class BalticTideProbeV1Mission: MissionServer
{
    protected const string LOG = "$profile:baltic_tide_probe_v1.log";
    protected const int STEPS = 100;
    protected const int SETTLE_MS = 400;
    protected ref array<int> m_Days = {2, 6, 9, 13, 17, 20, 24, 28};
    protected bool m_Ready;
    protected bool m_Scanning;
    protected bool m_Stormy;
    protected int m_DayIndex;
    protected int m_Step;
    protected int m_NextMs;
    protected int m_Sample;
    protected int m_PrintEvery;
    protected float m_BestLevel;
    protected int m_BestStep;

    void LogRow(string row)
    {
        FileHandle file = OpenFile(LOG, FileMode.APPEND);
        if (!file) { m_Ready = false; return; }
        FPrintln(file, row);
        CloseFile(file);
    }

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        FileHandle file = OpenFile(LOG, FileMode.WRITE);
        if (!file) return;
        FPrintln(file, "BALTIC_TIDE_PROBE_V1;BalticTrial;" + m_Days.Count() + ";" + STEPS);
        CloseFile(file);
        m_Ready = true;
        m_Scanning = true;
        m_BestLevel = -1000;
        SetScanTime();
        m_NextMs = GetGame().GetTime() + 5000;
    }

    // Step k of a day is k quarter-hours after 00:00; step 96..99 runs into the next day.
    void SetScanTime()
    {
        int minutes = m_Step * 15;
        GetGame().GetWorld().SetDate(2026, 10, m_Days[m_DayIndex] + minutes / 1440, (minutes % 1440) / 60, minutes % 60);
    }

    string Clock()
    {
        int year;
        int month;
        int day;
        int hour;
        int minute;
        GetGame().GetWorld().GetDate(year, month, day, hour, minute);
        return year.ToString() + "-" + month.ToString() + "-" + day.ToString() + ";" + hour.ToString() + ";" + minute.ToString();
    }

    string Sea()
    {
        string row = GetGame().SurfaceGetSeaLevel().ToString();
        row = row + ";" + GetGame().SurfaceGetSeaLevelMin().ToString();
        row = row + ";" + GetGame().SurfaceGetSeaLevelMax().ToString();
        row = row + ";" + GetGame().SurfaceGetSeaWaveMax().ToString();
        row = row + ";" + GetGame().SurfaceGetSeaWaveCurrent().ToString();
        return row;
    }

    string WaterAt(float x, float z)
    {
        vector above = Vector(x, 100, z);
        string row = GetGame().GetWaterSurfaceHeightNoFakeWave(above).ToString();
        row = row + ";" + GetGame().GetWaterSurfaceHeightWithFakeWave(above).ToString();
        return row;
    }

    void ScanStep()
    {
        float level = GetGame().SurfaceGetSeaLevel();
        LogRow("SCAN;" + m_DayIndex + ";" + m_Step + ";" + Clock() + ";" + Sea());
        if (m_DayIndex == 0 && level > m_BestLevel)
        {
            m_BestLevel = level;
            m_BestStep = m_Step;
        }
        m_Step++;
        if (m_Step == STEPS)
        {
            m_Step = 0;
            m_DayIndex++;
        }
        if (m_DayIndex == m_Days.Count())
        {
            // Hold the first date at its highest tide for the views.
            m_Scanning = false;
            m_DayIndex = 0;
            m_Step = m_BestStep;
            SetScanTime();
            LogRow("HOLD;" + m_BestStep + ";" + m_BestLevel + ";" + Clock());
            Print("BALTIC_TIDE_PROBE_V1 HOLD " + m_BestStep + " " + m_BestLevel + " " + Clock());
            m_NextMs = GetGame().GetTime() + 2000;
            return;
        }
        SetScanTime();
        m_NextMs = GetGame().GetTime() + SETTLE_MS;
    }

    // Wind follows the overcast set from outside (world_weather_set): calm below 0.2, storm above 0.9.
    void FollowWeather()
    {
        Weather weather = GetGame().GetWeather();
        float overcast = weather.GetOvercast().GetActual();
        if (!m_Stormy && overcast >= 0.9)
        {
            weather.SetWindFunctionParams(1, 1, 1);
            weather.SetWindSpeed(20);
            m_Stormy = true;
            LogRow("WIND;storm;" + Clock());
        }
        else if (m_Stormy && overcast <= 0.2)
        {
            weather.SetWindFunctionParams(0, 0, 1);
            weather.SetWindSpeed(0.1);
            m_Stormy = false;
            LogRow("WIND;calm;" + Clock());
        }
    }

    void HoldSample()
    {
        Weather weather = GetGame().GetWeather();
        string row = "SEA;" + m_Sample + ";" + GetGame().GetTime() + ";" + Clock() + ";" + Sea();
        row = row + ";" + WaterAt(1244, 10604) + ";" + WaterAt(2091, 7371) + ";" + WaterAt(4404, 9378);
        row = row + ";" + weather.GetWindSpeed() + ";" + weather.GetOvercast().GetActual() + ";" + weather.GetRain().GetActual();
        LogRow(row);
        if (m_PrintEvery == 0) Print("BALTIC_TIDE_PROBE_V1 " + row);
        m_PrintEvery = (m_PrintEvery + 1) % 5;
        m_Sample++;
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!m_Ready || GetGame().GetTime() < m_NextMs) return;
        if (m_Scanning)
        {
            ScanStep();
            return;
        }
        FollowWeather();
        HoldSample();
        m_NextMs = GetGame().GetTime() + 2000;
    }
}
Mission CreateCustomMission(string path) { return new BalticTideProbeV1Mission(); }
