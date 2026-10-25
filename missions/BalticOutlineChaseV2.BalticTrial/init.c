// Isolated native-AI consumer test. No actor motion overrides or teleportation.
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

class BalticOutlineChaseV2Mission: MissionServer
{
    protected float m_Time;
    protected float m_StageStart;
    protected float m_NextStage = 15;
    protected float m_NextSample;
    protected float m_NextNoise;
    protected int m_Stage;
    protected int m_MaxMind;
    protected bool m_Started;
    protected bool m_Preparing;
    protected float m_PreparedAt;
    protected bool m_Finished;
    protected DayZInfected m_Actor;
    protected Man m_Prey;
    protected ref array<Man> m_NativeTestObservers = new array<Man>;
    protected ref NoiseParams m_Noise;
    protected vector m_Goal;

    override void OnInit()
    {
        super.OnInit();
        FileHandle report = OpenFile("$profile:baltic_outline_chase_v2.log", FileMode.WRITE);
        if (report)
        {
            FPrintln(report, "BALTIC_OUTLINE_CHASE_V2");
            FPrintln(report, "world=" + GetGame().GetWorldName());
            FPrintln(report, "event;t;stage;x;y;z;d;cross;health;mind;target_entity");
            CloseFile(report);
        }
        m_Noise = new NoiseParams;
        m_Noise.LoadFromPath("CfgWeapons Rifle_Base NoiseShoot");
    }

    vector PointOnAxis(float distance)
    {
        vector p = "5184.0 0 7644.0";
        p[0] = p[0] + 1.0 * distance;
        p[2] = p[2] - 0.0 * distance;
        p[1] = GetGame().SurfaceRoadY(p[0], p[2]) + 0.05;
        return p;
    }

    void Record(string marker)
    {
        FileHandle report = OpenFile("$profile:baltic_outline_chase_v2.log", FileMode.APPEND);
        if (!report) return;
        vector pos;
        float health;
        int mind = -1;
        string target = "not_read";
        if (m_Actor)
        {
            pos = m_Actor.GetPosition();
            health = m_Actor.GetHealth("", "Health");
            DayZInfectedInputController input = m_Actor.GetInputController();
            if (input)
            {
                mind = input.GetMindState();
                // Native noise targets can expose an unsafe EntityAI handle.
                // Do not dereference GetTargetEntity in this diagnostic.
            }
        }
        float d = (pos[0] - 5184.0) * 1.0 - (pos[2] - 7644.0) * 0.0;
        float cross = (pos[0] - 5184.0) * 0.0 + (pos[2] - 7644.0) * 1.0;
        FPrintln(report, marker + ";" + m_Time + ";" + m_Stage + ";" + pos[0] + ";" + pos[1] + ";" + pos[2] + ";" + d + ";" + cross + ";" + health + ";" + mind + ";" + target);
        if (m_Prey) FPrintln(report, "PREY;" + m_Time + ";" + m_Stage + ";" + m_Prey.GetPosition() + ";" + m_Goal);
        CloseFile(report);
    }

    void CleanupActor()
    {
        if (m_Actor) GetGame().ObjectDelete(m_Actor);
        m_Actor = null;
    }

    void PrepareStage()
    {
        float spawnDistance = -80;
        float goalDistance = -55;
        vector orientation = "90 0 0";
        if (m_Stage == 1)
        {
            spawnDistance = -50;
            goalDistance = 60;
            orientation = "90 0 0";
        }
        if (m_Stage == 2)
        {
            spawnDistance = 50;
            goalDistance = -60;
            orientation = "-90 0 0";
        }
        m_Goal = PointOnAxis(goalDistance);
        PGFilter filter = new PGFilter;
        filter.SetFlags(PGPolyFlags.WALK, PGPolyFlags.SWIM | PGPolyFlags.SWIM_SEA | PGPolyFlags.DISABLED, PGPolyFlags.NONE);
        AIWorld ai = GetGame().GetWorld().GetAIWorld();
        vector sampledStart, sampledGoal;
        if (!ai.SampleNavmeshPosition(PointOnAxis(spawnDistance), 2, filter, sampledStart) || !ai.SampleNavmeshPosition(m_Goal, 2, filter, sampledGoal))
        {
            Record("INCONCLUSIVE_NAV_ANCHOR");
            m_Finished = true;
            return;
        }
        FileHandle anchorReport = OpenFile("$profile:baltic_outline_chase_v2.log", FileMode.APPEND);
        if (anchorReport)
        {
            FPrintln(anchorReport, "GOAL;" + m_Stage + ";" + m_Goal + ";" + sampledStart + ";" + sampledGoal);
            CloseFile(anchorReport);
        }
        // Place only the human test target before spawning each independent AI.
        m_Prey.SetPosition(m_Goal);
        m_Prey.SetAllowDamage(false);
        m_Preparing = true;
        m_PreparedAt = m_Time;
        m_NextSample = m_Time;
        Record("SETTLE_BEGIN");
    }

    void BeginStage()
    {
        float spawnDistance = -80;
        vector orientation = "90 0 0";
        if (m_Stage == 1) spawnDistance = -50;
        if (m_Stage == 2)
        {
            spawnDistance = 50;
            orientation = "-90 0 0";
        }
        m_Preparing = false;
        m_Actor = DayZInfected.Cast(GetGame().CreateObjectEx("ZmbF_JournalistNormal_Blue", PointOnAxis(spawnDistance), ECE_PLACE_ON_SURFACE | ECE_INITAI | ECE_CREATEPHYSICS));
        if (!m_Actor)
        {
            Record("FAILED_SPAWN");
            m_Finished = true;
            return;
        }
        m_Actor.SetOrientation(orientation);
        m_StageStart = m_Time;
        m_NextNoise = m_Time + 3;
        m_NextSample = m_Time;
        m_MaxMind = 0;
        m_Started = true;
        Record("SPAWN");
    }

    void EndStage(string marker)
    {
        Record(marker);
        CleanupActor();
        m_Started = false;
        if (marker != "REACHED")
        {
            Record("INCONCLUSIVE_OR_FAILED_STAGE");
            m_Finished = true;
            return;
        }
        m_Stage++;
        m_NextStage = m_Time + 6;
        if (m_Stage == 3)
        {
            m_Finished = true;
            Record("COMPLETE_ALL_STAGES");
        }
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial" || m_Finished) return;
        m_Time = m_Time + timeslice;
        if (m_Prey)
        {
            Human preyHuman = Human.Cast(m_Prey);
            HumanInputController preyControl;
            if (preyHuman) preyControl = preyHuman.GetInputController();
            if (preyControl) preyControl.OverrideMovementSpeed(HumanInputControllerOverrideType.ENABLED, 0);
        }
        if (m_Preparing)
        {
            if (m_Time >= m_NextSample)
            {
                Record("SETTLE");
                m_NextSample = m_Time + 0.2;
            }
            if (m_Time - m_PreparedAt >= 20) BeginStage();
            return;
        }
        if (!m_Started)
        {
            if (m_Time < m_NextStage) return;
            m_NativeTestObservers.Clear();
            GetGame().GetPlayers(m_NativeTestObservers);
            if (m_NativeTestObservers.Count() == 0) return;
            if (m_NativeTestObservers.Count() != 1)
            {
                Record("INCONCLUSIVE_PLAYER_COUNT");
                m_Finished = true;
                return;
            }
            m_Prey = m_NativeTestObservers[0];
            PrepareStage();
            return;
        }
        if (!m_Actor || m_Actor.GetHealth("", "Health") <= 0)
        {
            EndStage("FAILED_ACTOR");
            return;
        }
        if (m_Time - m_StageStart > 90)
        {
            EndStage("TIMEOUT");
            return;
        }
        DayZInfectedInputController input = m_Actor.GetInputController();
        if (input && input.GetMindState() > m_MaxMind) m_MaxMind = input.GetMindState();
        if (m_Time >= m_NextNoise)
        {
            GetGame().GetNoiseSystem().AddNoisePos(m_Prey, m_Prey.GetPosition(), m_Noise, 1);
            m_NextNoise = m_Time + 3;
            Record("NOISE");
        }
        if (m_Time >= m_NextSample)
        {
            Record("SAMPLE");
            m_NextSample = m_Time + 0.2;
        }
        vector pos = m_Actor.GetPosition();
        float d = (pos[0] - 5184.0) * 1.0 - (pos[2] - 7644.0) * 0.0;
        bool reached = false;
        if (m_Stage == 0 && d >= -65 && m_MaxMind >= 1) reached = true;
        if (m_Stage == 1 && d >= 48) reached = true;
        if (m_Stage == 2 && d <= -48) reached = true;
        if (reached) EndStage("REACHED");
    }

    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        pos = "5100 0 7644";
        pos[1] = GetGame().SurfaceY(pos[0], pos[2]) + 0.2;
        return super.CreateCharacter(identity, pos, ctx, characterName);
    }

    override void OnMissionFinish()
    {
        CleanupActor();
        if (m_Prey)
        {
            Human preyHuman = Human.Cast(m_Prey);
            HumanInputController preyControl;
            if (preyHuman) preyControl = preyHuman.GetInputController();
            if (preyControl) preyControl.OverrideMovementSpeed(HumanInputControllerOverrideType.DISABLED, 0);
            m_Prey.SetAllowDamage(true);
        }
        super.OnMissionFinish();
    }
}

Mission CreateCustomMission(string path)
{
    return new BalticOutlineChaseV2Mission();
}
