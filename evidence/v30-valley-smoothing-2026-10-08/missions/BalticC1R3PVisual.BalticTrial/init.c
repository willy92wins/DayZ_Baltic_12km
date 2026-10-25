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

class BalticC1R3PVisualMission: MissionServer
{
    // Direct initial creation: no post-load teleport.
    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        pos = "7348 0 5780";
        pos[1] = GetGame().SurfaceY(pos[0], pos[2]) + 0.2;
        return super.CreateCharacter(identity, pos, ctx, characterName);
    }

    protected const string LOG = "$profile:baltic_c1r3p_visual.log";
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
        LogSurface("Q5001", 2196.000000, 7137.000000);
        LogSurface("Q5002", 2205.000000, 7194.000000);
        LogSurface("Q5003", 2178.000000, 7248.000000);
        LogSurface("Q5004", 8277.000000, 8976.000000);
        LogSurface("Q5005", 8238.000000, 9075.000000);
        LogSurface("Q5006", 8232.000000, 9180.000000);
        LogSurface("Q5007", 7269.000000, 5829.000000);
        LogSurface("Q5008", 7338.000000, 5748.000000);
        LogSurface("Q5009", 7386.000000, 5652.000000);
        LogSurface("Q5010", 7236.000000, 5850.000000);
        LogSurface("Q5011", 7254.000000, 5838.000000);
        LogSurface("Q5012", 7272.000000, 5826.000000);
        LogSurface("Q5013", 7278.000000, 5820.000000);
        LogSurface("Q5014", 7308.000000, 5802.000000);
        LogSurface("Q5015", 7326.000000, 5784.000000);
        LogSurface("Q5016", 7338.000000, 5766.000000);
        LogSurface("Q5017", 7338.000000, 5760.000000);
        LogSurface("Q5018", 7338.000000, 5724.000000);
        LogSurface("Q5019", 7356.000000, 5694.000000);
        LogSurface("Q5020", 7380.000000, 5670.000000);
        LogSurface("Q5021", 7386.000000, 5664.000000);
        LogSurface("Q5022", 7386.000000, 5658.000000);
        LogSurface("Q5023", 1992.000000, 6432.000000);
        LogSurface("Q5024", 1836.000000, 6384.000000);
        LogSurface("Q5025", 2207.500000, 7080.500000);
        LogSurface("Q5026", 2124.000000, 7254.000000);
        LogSurface("Q5027", 8262.000000, 8904.000000);
        LogSurface("Q5028", 7266.000000, 5826.000000);
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
Mission CreateCustomMission(string path) { return new BalticC1R3PVisualMission(); }
