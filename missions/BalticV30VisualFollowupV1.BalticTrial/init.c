// Temporary, bounded player-view inspection. No camera API or terrain changes.
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

class BalticV30VisualFollowupMission: MissionServer
{
    protected ref array<string> m_BalticSites = new array<string>;
    protected float m_BalticElapsed;
    protected int m_BalticStage = -1;
    protected int m_BalticSampled = -1;
    protected int m_BalticStable = -1;
    protected bool m_BalticReady;
    protected bool m_BalticComplete;

    void LogTour(string row)
    {
        FileHandle output = OpenFile("$profile:baltic_v30_visual_followup_v1.log", FileMode.APPEND);
        if (!output) return;
        FPrintln(output, row);
        CloseFile(output);
    }

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        FileHandle output = OpenFile("$profile:baltic_v30_visual_followup_v1.log", FileMode.WRITE);
        if (!output) return;
        FPrintln(output, "BALTIC_V30_VISUAL_FOLLOWUP_V1;BalticTrial");
        CloseFile(output);
        FileHandle input = OpenFile("$mission:sites.csv", FileMode.READ);
        if (!input) return;
        string row;
        array<string> fields = new array<string>;
        while (FGets(input, row) >= 0)
        {
            if (row == "") continue;
            fields.Clear(); row.Split(";", fields);
            if (fields.Count() != 5) { CloseFile(input); LogTour("FAIL;SCHEMA"); return; }
            m_BalticSites.Insert(row);
        }
        CloseFile(input);
        m_BalticReady = m_BalticSites.Count() == 2;
    }

    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        pos = "5142 0 1086";
        pos[1] = GetGame().SurfaceRoadY(pos[0], pos[2]) + 0.2;
        return super.CreateCharacter(identity, pos, ctx, characterName);
    }

    void SamplePoint(string name, string kind, vector pos)
    {
        float ground = GetGame().SurfaceY(pos[0], pos[2]);
        vector above = Vector(pos[0], ground + 100, pos[2]);
        vector bed = Vector(pos[0], ground + 0.01, pos[2]);
        string surface;
        GetGame().SurfaceGetType(pos[0], pos[2], surface);
        string row = "W;" + name + ";" + kind + ";" + pos.ToString() + ";" + ground;
        row = row + ";" + GetGame().SurfaceRoadY(pos[0], pos[2]) + ";" + GetGame().SurfaceIsSea(pos[0], pos[2]);
        row = row + ";" + GetGame().SurfaceIsPond(pos[0], pos[2]) + ";" + GetGame().GetWaterDepth(bed);
        row = row + ";" + GetGame().GetWaterSurfaceHeightNoFakeWave(above) + ";" + surface;
        LogTour(row);
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || !m_BalticReady || m_BalticComplete) return;
        array<Man> observers = new array<Man>;
        GetGame().GetPlayers(observers);
        if (observers.Count() != 1) return;
        PlayerBase player = PlayerBase.Cast(observers[0]);
        if (!player) return;
        m_BalticElapsed = m_BalticElapsed + timeslice;
        int stage = Math.Floor(m_BalticElapsed / 90);
        if (stage >= m_BalticSites.Count())
        {
            m_BalticComplete = true;
            LogTour("END;2");
            return;
        }
        array<string> fields = new array<string>;
        m_BalticSites[stage].Split(";", fields);
        vector destination = fields[1].ToVector();
        destination[1] = GetGame().SurfaceRoadY(destination[0], destination[2]) + 0.2;
        if (stage != m_BalticStage)
        {
            m_BalticStage = stage;
            player.SetPosition(destination);
            player.SetOrientation(fields[2].ToVector());
            LogTour("MOVE;" + stage + ";" + fields[0] + ";" + GetGame().GetTime() + ";" + destination.ToString());
        }
        if (m_BalticSampled != stage && m_BalticElapsed - stage * 90 >= 8)
        {
            m_BalticSampled = stage;
            LogTour("READY;" + stage + ";" + fields[0] + ";" + GetGame().GetTime() + ";" + player.GetPosition().ToString());
            LogTour("SEA;" + fields[0] + ";" + GetGame().SurfaceGetSeaLevelMin() + ";" + GetGame().SurfaceGetSeaLevelMax() + ";" + GetGame().SurfaceGetSeaLevel());
            SamplePoint(fields[0], "view_land", destination);
            SamplePoint(fields[0], "target", fields[3].ToVector());
            SamplePoint(fields[0], "near_water", fields[4].ToVector());
        }
        if (m_BalticStable != stage && m_BalticElapsed - stage * 90 >= 60)
        {
            m_BalticStable = stage;
            Weather weather = GetGame().GetWeather();
            LogTour("STABLE;" + stage + ";" + fields[0] + ";" + GetGame().GetTime() + ";" + player.GetPosition().ToString());
            LogTour("WX;" + fields[0] + ";" + weather.GetOvercast().GetActual() + ";" + weather.GetFog().GetActual() + ";" + weather.GetRain().GetActual());
        }
    }
}

Mission CreateCustomMission(string path) { return new BalticV30VisualFollowupMission(); }
