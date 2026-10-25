// Bounded server-authoritative test: 0/25/100/0 native infected, one real client.
void main()
{
    GetGame().GetWorld().SetDate(2026, 9, 29, 12, 0);
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

class BalticAILoadMission: MissionServer
{
    protected ref array<DayZInfected> m_LoadActors = new array<DayZInfected>;
    protected ref array<vector> m_LoadPreviousPositions = new array<vector>;
    protected ref array<Man> m_LoadObservers = new array<Man>;
    protected ref NoiseParams m_LoadNoise;
    protected Man m_LoadPrey;
    protected vector m_LoadGoal;
    protected int m_LoadPhase;
    protected int m_LoadSample;
    protected int m_LoadUpdates;
    protected int m_LoadOver50;
    protected float m_LoadStart;
    protected float m_LoadWindow;
    protected float m_LoadNext;
    protected float m_LoadNextNoise;
    protected float m_LoadSumDt;
    protected float m_LoadMaxDt;
    protected bool m_LoadStarted;
    protected bool m_LoadRecording;
    protected bool m_LoadFinished;

    void WriteLoad(string line)
    {
        FileHandle report = OpenFile("$profile:baltic_ai_load_v1.log", FileMode.APPEND);
        if (!report) { m_LoadFinished = true; return; }
        FPrintln(report, line);
        CloseFile(report);
    }

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial")
        { m_LoadFinished = true; return; }
        FileHandle report = OpenFile("$profile:baltic_ai_load_v1.log", FileMode.WRITE);
        if (!report) { m_LoadFinished = true; return; }
        FPrintln(report, "BALTIC_AI_LOAD_V1;BalticTrial;SERVER;NO_CE");
        FPrintln(report, "columns;phase;sample;tick;mission_ms;window_s;updates;sum_dt;max_dt;over50;expected;alive;awake;moving;health_min;prey_drift");
        CloseFile(report);
        m_LoadNoise = new NoiseParams;
        m_LoadNoise.LoadFromPath("CfgWeapons Rifle_Base NoiseShoot");
    }

    int LoadCount()
    {
        if (m_LoadPhase == 1) return 25;
        if (m_LoadPhase == 2) return 100;
        return 0;
    }

    void CleanLoadActors()
    {
        foreach (DayZInfected actor : m_LoadActors)
        {
            if (actor) GetGame().ObjectDelete(actor);
        }
        m_LoadActors.Clear();
        m_LoadPreviousPositions.Clear();
    }

    void BeginLoadPhase()
    {
        CleanLoadActors();
        int wanted = LoadCount();
        for (int row = 0; row < 10; row++)
        {
            for (int col = 0; col < 10; col++)
            {
                if (m_LoadActors.Count() >= wanted) break;
                vector spawn = Vector(2050 + col * 4.5, 0, 6900 + row * 4.5);
                spawn[1] = GetGame().SurfaceY(spawn[0], spawn[2]) + 0.05;
                DayZInfected actor = DayZInfected.Cast(GetGame().CreateObjectEx("ZmbF_JournalistNormal_Blue", spawn, ECE_PLACE_ON_SURFACE | ECE_INITAI | ECE_CREATEPHYSICS));
                if (!actor)
                {
                    WriteLoad("FAIL_SPAWN;" + m_LoadPhase + ";" + row + ";" + col);
                    CleanLoadActors();
                    m_LoadFinished = true;
                    return;
                }
                actor.SetOrientation("90 0 0");
                m_LoadActors.Insert(actor);
                m_LoadPreviousPositions.Insert(actor.GetPosition());
                WriteLoad("SPAWN;" + m_LoadPhase + ";" + (m_LoadActors.Count() - 1) + ";" + actor.GetPosition());
            }
        }
        m_LoadSample = 0;
        m_LoadRecording = false;
        m_LoadStart = GetGame().GetTickTime();
        m_LoadNextNoise = m_LoadStart + 3;
        WriteLoad("BEGIN;" + m_LoadPhase + ";" + m_LoadStart + ";" + GetGame().GetTime() + ";" + wanted + ";" + m_LoadPrey.GetPosition());
    }

    void ResetLoadCounters(float now)
    {
        m_LoadWindow = now;
        m_LoadNext = now + 1;
        m_LoadUpdates = 0;
        m_LoadSumDt = 0;
        m_LoadMaxDt = 0;
        m_LoadOver50 = 0;
    }

    void SampleLoad(float now)
    {
        int alive;
        int awake;
        int moving;
        float minimumHealth = 100;
        for (int i = 0; i < m_LoadActors.Count(); i++)
        {
            DayZInfected actor = m_LoadActors[i];
            if (!actor) continue;
            float health = actor.GetHealth("", "Health");
            minimumHealth = Math.Min(minimumHealth, health);
            if (health <= 0) continue;
            alive++;
            DayZInfectedInputController input = actor.GetInputController();
            if (input && input.GetMindState() >= 1) awake++;
            vector pos = actor.GetPosition();
            if (vector.Distance(pos, m_LoadPreviousPositions[i]) > 0.1) moving++;
            m_LoadPreviousPositions[i] = pos;
        }
        m_LoadSample++;
        string line = "S;" + m_LoadPhase + ";" + m_LoadSample + ";" + now + ";" + GetGame().GetTime();
        line = line + ";" + (now - m_LoadWindow) + ";" + m_LoadUpdates + ";" + m_LoadSumDt + ";" + m_LoadMaxDt + ";" + m_LoadOver50;
        line = line + ";" + LoadCount() + ";" + alive + ";" + awake + ";" + moving + ";" + minimumHealth + ";" + vector.Distance(m_LoadPrey.GetPosition(), m_LoadGoal);
        WriteLoad(line);
        ResetLoadCounters(now);
        if (m_LoadSample == 60)
        {
            WriteLoad("END;" + m_LoadPhase + ";" + now + ";" + GetGame().GetTime());
            m_LoadPhase++;
            if (m_LoadPhase == 4)
            {
                CleanLoadActors();
                m_LoadPrey.SetAllowDamage(true);
                WriteLoad("COMPLETE;" + now);
                m_LoadFinished = true;
            }
            else BeginLoadPhase();
        }
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (m_LoadFinished) return;
        float now = GetGame().GetTickTime();
        if (!m_LoadStarted)
        {
            m_LoadObservers.Clear();
            GetGame().GetPlayers(m_LoadObservers);
            if (m_LoadObservers.Count() == 0) return;
            if (m_LoadObservers.Count() != 1)
            { WriteLoad("FAIL_PLAYER_COUNT"); m_LoadFinished = true; return; }
            m_LoadPrey = m_LoadObservers[0];
            m_LoadGoal = "2120 0 6920";
            m_LoadGoal[1] = GetGame().SurfaceY(m_LoadGoal[0], m_LoadGoal[2]) + 0.05;
            m_LoadPrey.SetPosition(m_LoadGoal);
            m_LoadPrey.SetAllowDamage(false);
            m_LoadStarted = true;
            BeginLoadPhase();
            return;
        }
        if (now >= m_LoadNextNoise && LoadCount() > 0)
        {
            GetGame().GetNoiseSystem().AddNoisePos(m_LoadPrey, m_LoadPrey.GetPosition(), m_LoadNoise, 1);
            m_LoadNextNoise = now + 3;
        }
        if (!m_LoadRecording)
        {
            if (now - m_LoadStart < 25) return;
            m_LoadRecording = true;
            ResetLoadCounters(now);
            return;
        }
        m_LoadUpdates++;
        m_LoadSumDt += timeslice;
        m_LoadMaxDt = Math.Max(m_LoadMaxDt, timeslice);
        if (timeslice > 0.05) m_LoadOver50++;
        if (now >= m_LoadNext) SampleLoad(now);
    }

    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        pos = "2120 0 6920";
        pos[1] = GetGame().SurfaceY(pos[0], pos[2]) + 0.2;
        return super.CreateCharacter(identity, pos, ctx, characterName);
    }

    override void OnMissionFinish()
    {
        CleanLoadActors();
        if (m_LoadPrey) m_LoadPrey.SetAllowDamage(true);
        super.OnMissionFinish();
    }
}

Mission CreateCustomMission(string path)
{
    return new BalticAILoadMission();
}
