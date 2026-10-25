// Sea swell probe for views: the server logs the global sea level and the water surface at three points every
// 250 ms, plus one row per real-time second that ties the server clock to the wall clock of the captures.
// No RPC, player movement or terrain edits.
// APIs: world.c SetDate :51; ensystem.c GetHourMinuteSecond :28; game.c SurfaceGetSeaLevelMin/Max/SeaLevel
// :1174-1176, SurfaceGetSeaWaveMax :1178, GetWaterSurfaceHeightNoFakeWave/WithFakeWave :1185-1187;
// weather.c GetActual :38, Set :49, SetLimits :74, GetWindSpeed :243, SetWindSpeed :251,
// SetWindMaximumSpeed :264, SetWindFunctionParams :280, MissionWeather :383.
void main()
{
    GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0);
    GetGame().GetWorld().SetTimeMultiplier(0);
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

class BalticWaterVisualDiagMission: MissionServer
{
    // Direct initial creation: no post-load teleport.
    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        pos = "2244 0 7164";
        pos[1] = GetGame().SurfaceY(pos[0], pos[2]) + 0.2;
        return super.CreateCharacter(identity, pos, ctx, characterName);
    }

    protected const string LOG = "$profile:baltic_water_visual_diag.log";
    protected bool m_Ready;
    protected bool m_Stormy;
    protected int m_NextMs;
    protected int m_Sample;
    protected int m_LastSecond;

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
        FPrintln(file, "BALTIC_TIDE_PROBE_V2;BalticTrial");
        CloseFile(file);
        m_Ready = true;
        m_LastSecond = -1;
        LogRow("CFG;" + GetGame().SurfaceGetSeaLevelMin() + ";" + GetGame().SurfaceGetSeaLevelMax() + ";" + GetGame().SurfaceGetSeaWaveMax());
        m_NextMs = GetGame().GetTime() + 5000;
    }

    string WaterAt(float x, float z)
    {
        vector above = Vector(x, 100, z);
        return GetGame().GetWaterSurfaceHeightWithFakeWave(above).ToString();
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
            LogRow("WIND;storm;" + GetGame().GetTime());
        }
        else if (m_Stormy && overcast <= 0.2)
        {
            weather.SetWindFunctionParams(0, 0, 1);
            weather.SetWindSpeed(0.1);
            m_Stormy = false;
            LogRow("WIND;calm;" + GetGame().GetTime());
        }
    }

    void LogSurface(string label, float x, float z)
    {
        float ground = GetGame().SurfaceY(x,z);
        vector pos = Vector(x,ground+0.01,z);
        float queried = GetGame().GetWaterSurfaceHeightNoFakeWave(pos);
        bool pond = GetGame().SurfaceIsPond(x,z);
        bool sea = GetGame().SurfaceIsSea(x,z);
        float depth = GetGame().GetWaterDepth(pos);
        LogRow("DRY;" + m_Sample + ";" + label + ";" + ground + ";" + queried + ";" + pond + ";" + sea + ";" + depth);
    }

    void LogDiagnostic()
    {
        LogSurface("land_reflection_e", 2179.537858, 7086.083408);
        LogSurface("land_dark_w", 2281.835241, 7203.550968);
        LogSurface("land_bright_w", 2534.586800, 7037.539623);
        LogSurface("land_reflection_n", 2210.061284, 6866.549706);
        LogSurface("R1_water", 2202.430000, 7164.680000);
        LogSurface("R2_water", 8272.520000, 9041.160000);
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!m_Ready) return;
        int hour;
        int minute;
        int second;
        GetHourMinuteSecond(hour, minute, second);
        if (second != m_LastSecond)
        {
            m_LastSecond = second;
            LogRow("RT;" + GetGame().GetTime() + ";" + hour + ";" + minute + ";" + second);
        }
        if (GetGame().GetTime() < m_NextMs) return;
        m_NextMs = GetGame().GetTime() + 250;
        FollowWeather();
        Weather weather = GetGame().GetWeather();
        string row = "SEA;" + m_Sample + ";" + GetGame().GetTime() + ";" + GetGame().SurfaceGetSeaLevel();
        row = row + ";" + WaterAt(1244, 10604) + ";" + WaterAt(2091, 7371) + ";" + WaterAt(4404, 9378);
        row = row + ";" + weather.GetWindSpeed() + ";" + weather.GetOvercast().GetActual() + ";" + weather.GetRain().GetActual();
        LogRow(row);
        if (m_Sample % 40 == 0) Print("BALTIC_TIDE_PROBE_V2 " + row);
        if (m_Sample % 4 == 0) LogDiagnostic();
        m_Sample++;
    }
}
Mission CreateCustomMission(string path) { return new BalticWaterVisualDiagMission(); }
