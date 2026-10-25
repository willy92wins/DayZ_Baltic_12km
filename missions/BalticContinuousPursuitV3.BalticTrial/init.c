// One initial placement per case, then native human inputs and untouched AI.
void main()
{
    GetGame().GetWorld().SetDate(2026, 9, 29, 12, 0);
    Weather weather = GetGame().GetWeather();
    weather.MissionWeather(true);
    weather.GetOvercast().SetLimits(0.1, 0.1); weather.GetOvercast().Set(0.1, 0, 1800);
    weather.GetRain().SetLimits(0, 0); weather.GetRain().Set(0, 0, 1800);
    weather.GetFog().SetLimits(0, 0); weather.GetFog().Set(0, 0, 1800);
    weather.GetSnowfall().SetLimits(0, 0); weather.GetSnowfall().Set(0, 0, 1800);
}
class BalticContinuousPursuitMission: MissionServer
{
    protected float m_Time;
    protected float m_Stage;
    protected float m_SpawnAt;
    protected float m_Next = 15;
    protected float m_NextSample;
    protected float m_NextNoise;
    protected int m_Case = -1;
    protected int m_Phase;
    protected bool m_Finished;
    protected DayZInfected m_Actor;
    protected PlayerBase m_Prey;
    protected ref array<Man> m_BalticPursuitPlayers = new array<Man>;
    protected ref array<vector> m_Starts = new array<vector>;
    protected ref array<vector> m_Preys = new array<vector>;
    protected ref array<vector> m_Goals = new array<vector>;
    protected ref array<string> m_Fields = new array<string>;
    protected ref NoiseParams m_Noise;
    protected FileHandle m_Log;
    protected FileHandle m_HeadingLog;

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        m_HeadingLog = OpenFile("$profile:baltic_heading_server_v3.log", FileMode.WRITE);
        m_Log = OpenFile("$profile:baltic_continuous_pursuit_v3.log", FileMode.WRITE);
        if (!m_Log) { m_Finished = true; return; }
        FPrintln(m_Log, "BALTIC_CONTINUOUS_PURSUIT_V3");
        FPrintln(m_Log, "world=" + GetGame().GetWorldName());
        FileHandle input = OpenFile("$mission:cases.csv", FileMode.READ);
        if (!input) { Finish("BAD_INPUT"); return; }
        string row;
        while (FGets(input, row) >= 0)
        {
            if (row == "") continue;
            m_Fields.Clear(); row.Split(";", m_Fields);
            if (m_Fields.Count() != 4 || m_Fields[0].ToInt() != m_Starts.Count())
            { CloseFile(input); Finish("BAD_CASES"); return; }
            m_Starts.Insert(m_Fields[1].ToVector());
            m_Preys.Insert(m_Fields[2].ToVector());
            m_Goals.Insert(m_Fields[3].ToVector());
        }
        CloseFile(input);
        if (m_Starts.Count() != 3) { Finish("BAD_COUNT"); return; }
        m_Noise = new NoiseParams;
        m_Noise.LoadFromPath("CfgWeapons Rifle_Base NoiseShoot");
    }
    void Record(string marker)
    {
        if (!m_Log || m_Case < 0) return;
        vector actor; vector prey; vector direction; vector aground; vector pground;
        float ah; float ph; float ar; float pr; float heading;
        int mind = -1; int command = -1; bool unconscious;
        if (m_Prey)
        {
            prey = m_Prey.GetPosition(); ph = m_Prey.GetHealth("", "Health");
            pground = Vector(prey[0], GetGame().SurfaceY(prey[0], prey[2]), prey[2]);
            pr = GetGame().SurfaceRoadY(prey[0], prey[2]);
            command = m_Prey.BalticPursuitCommand(); unconscious = m_Prey.IsUnconscious();
            HumanInputController humanInput = m_Prey.GetInputController();
            float actualSpeed; vector localDirection;
            vector bodyOrientation = m_Prey.GetOrientation();
            if (humanInput)
            {
                humanInput.GetMovement(actualSpeed, localDirection);
                if (m_HeadingLog) FPrintln(m_HeadingLog, "D;" + m_Time + ";" + GetGame().GetTime() + ";" + command + ";" + prey.ToString() + ";" + humanInput.GetHeadingAngle() + ";" + bodyOrientation.ToString() + ";" + m_Prey.GetCurrentCommandID() + ";" + m_Prey.IsFighting() + ";" + actualSpeed + ";" + localDirection.ToString() + ";" + marker);
            }
        }
        if (m_Actor)
        {
            actor = m_Actor.GetPosition(); ah = m_Actor.GetHealth("", "Health");
            aground = Vector(actor[0], GetGame().SurfaceY(actor[0], actor[2]), actor[2]);
            ar = GetGame().SurfaceRoadY(actor[0], actor[2]); direction = m_Actor.GetDirection();
            DayZInfectedInputController input = m_Actor.GetInputController();
            if (input && m_Time - m_SpawnAt >= 1) { mind = input.GetMindState(); heading = input.GetHeading(); }
        }
        FPrintln(m_Log, "P;" + m_Case + ";" + m_Time + ";" + marker + ";" + actor.ToString() + ";" + prey.ToString() + ";" + ah + ";" + ph + ";" + mind + ";" + command + ";" + aground.ToString() + ";" + ar + ";" + pground.ToString() + ";" + pr + ";" + m_Goals[m_Case].ToString() + ";" + direction.ToString() + ";" + heading + ";" + unconscious);
    }
    void CleanActor()
    {
        if (m_Actor) GetGame().ObjectDelete(m_Actor);
        m_Actor = null;
    }
    void ControlPrey(bool moving, bool release = false)
    {
        if (!m_Prey) return;
        HumanInputController control = m_Prey.GetInputController();
        if (!control) return;
        if (release)
        {
            control.OverrideMovementSpeed(HumanInputControllerOverrideType.DISABLED, 0);
            control.OverrideMovementAngle(HumanInputControllerOverrideType.DISABLED, 0);
            return;
        }
        float speed = 0; float angle = 0;
        if (moving && m_Case >= 0 && m_Case < m_Goals.Count())
        {
            vector pos = m_Prey.GetPosition(); vector goal = m_Goals[m_Case];
            float dx = goal[0] - pos[0]; float dz = goal[2] - pos[2];
            if (dx * dx + dz * dz > 2.25)
            {
                speed = 1;
                angle = (Math.Atan2(dx, dz) + control.GetHeadingAngle()) * Math.RAD2DEG;
                while (angle > 180) angle = angle - 360;
                while (angle < -180) angle = angle + 360;
            }
        }
        control.OverrideMovementSpeed(HumanInputControllerOverrideType.ENABLED, speed);
        control.OverrideMovementAngle(HumanInputControllerOverrideType.ENABLED, angle);
    }
    void Finish(string reason)
    {
        if (m_Finished) return;
        m_Finished = true;
        if (m_Prey) { m_Prey.BalticSetPursuitCommand(0); m_Prey.SetAllowDamage(true); }
        ControlPrey(false, true);
        CleanActor();
        if (m_HeadingLog) { CloseFile(m_HeadingLog); m_HeadingLog = null; }
        if (m_Log) { FPrintln(m_Log, "END;" + reason); CloseFile(m_Log); m_Log = null; }
    }
    void Fail(string reason)
    {
        Record(reason); Finish("CASE_FAILED_" + reason);
    }
    void BeginCase()
    {
        m_Case = m_Case + 1;
        if (m_Case >= 3) { Finish("ALL_CASES_COMPLETE"); return; }
        m_Prey.BalticSetPursuitCommand(0);
        ControlPrey(false);
        m_Prey.SetAllowDamage(false);
        m_Prey.SetPosition(m_Preys[m_Case]);
        FPrintln(m_Log, "CASE;" + m_Case + ";" + m_Starts[m_Case].ToString() + ";" + m_Preys[m_Case].ToString() + ";" + m_Goals[m_Case].ToString());
        m_Phase = 1; m_Stage = m_Time; m_NextSample = m_Time;
        Record("SETTLE_BEGIN");
    }
    float Lateral(vector pos)
    {
        vector delta = m_Goals[m_Case] - m_Starts[m_Case]; delta[1] = 0; delta.Normalize();
        vector relative = pos - m_Starts[m_Case];
        return relative[0] * (-delta[2]) + relative[2] * delta[0];
    }
    float PermittedLateral(vector pos)
    {
        if (m_Case == 0) return 4;
        float dx = pos[0] - 2417.1428225906;
        float dz = pos[2] - 6889.8850822322;
        float along = dx * 0.98836436083 + dz * (-0.15210486594);
        if (Math.AbsFloat(along) <= 112.5) return 6;
        return 4;
    }
    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial" || m_Finished) return;
        m_Time = m_Time + timeslice;
        if (m_Time > 1200) { Finish("SESSION_TIMEOUT"); return; }
        if (m_Phase == 0)
        {
            if (m_Time < m_Next) return;
            m_BalticPursuitPlayers.Clear(); GetGame().GetPlayers(m_BalticPursuitPlayers);
            if (m_BalticPursuitPlayers.Count() == 0) return;
            if (m_BalticPursuitPlayers.Count() != 1) { Finish("BAD_PLAYER_COUNT"); return; }
            m_Prey = PlayerBase.Cast(m_BalticPursuitPlayers[0]);
            if (!m_Prey) { Finish("BAD_PLAYER"); return; }
            BeginCase(); return;
        }
        if (!m_Prey || m_Prey.GetHealth("", "Health") <= 0 || m_Prey.IsUnconscious()) { Fail("BAD_PREY"); return; }
        ControlPrey(m_Phase == 3);
        if (m_Time >= m_NextSample) { m_NextSample = m_Time + 0.2; Record("SAMPLE"); }
        if (m_Phase == 1)
        {
            if (m_Time - m_Stage < 20) return;
            if (vector.Distance(m_Prey.GetPosition(), m_Preys[m_Case]) > 2) { Fail("UNSTABLE_PREY"); return; }
            m_Actor = DayZInfected.Cast(GetGame().CreateObjectEx("ZmbF_JournalistNormal_Blue", m_Starts[m_Case], ECE_PLACE_ON_SURFACE | ECE_INITAI | ECE_CREATEPHYSICS));
            if (!m_Actor) { Fail("SPAWN_FAILED"); return; }
            vector direction = m_Preys[m_Case] - m_Starts[m_Case]; direction[1] = 0;
            vector orientation = direction.VectorToAngles(); orientation[1] = 0; orientation[2] = 0;
            m_Actor.SetOrientation(orientation);
            m_SpawnAt = m_Time; m_Stage = m_Time; m_NextNoise = m_Time + 3; m_Phase = 2;
            Record("SPAWN"); return;
        }
        if (!m_Actor || m_Actor.GetHealth("", "Health") <= 0) { Fail("ACTOR_DEAD"); return; }
        if (Math.AbsFloat(Lateral(m_Actor.GetPosition())) > PermittedLateral(m_Actor.GetPosition()) || Math.AbsFloat(Lateral(m_Prey.GetPosition())) > PermittedLateral(m_Prey.GetPosition())) { Fail("CORRIDOR"); return; }
        if (m_Time >= m_NextNoise)
        {
            GetGame().GetNoiseSystem().AddNoisePos(m_Prey, m_Prey.GetPosition(), m_Noise, 4);
            m_NextNoise = m_Time + 3; Record("NOISE");
        }
        DayZInfectedInputController input = m_Actor.GetInputController();
        int mind = -1;
        if (input && m_Time - m_SpawnAt >= 1) mind = input.GetMindState();
        if (m_Phase == 2)
        {
            if (mind >= 3)
            {
                m_Prey.BalticSetPursuitCommand(m_Case + 1); m_Phase = 3; m_Stage = m_Time;
                Record("MOVE_BEGIN");
            }
            else if (m_Time - m_Stage > 30) Fail("ACQUISITION_TIMEOUT");
            return;
        }
        float limit = 500;
        if (m_Case == 0) limit = 90;
        if (m_Time - m_Stage > limit) { Fail("WALK_TIMEOUT"); return; }
        if (vector.Distance(m_Prey.GetPosition(), m_Goals[m_Case]) <= 2 && vector.Distance(m_Actor.GetPosition(), m_Goals[m_Case]) <= 4)
        {
            Record("REACHED"); m_Prey.BalticSetPursuitCommand(0); CleanActor();
            ControlPrey(false);
            m_Phase = 0; m_Next = m_Time + 6;
        }
    }
    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        pos = "5100 0 7644"; pos[1] = GetGame().SurfaceY(pos[0], pos[2]) + 0.2;
        return super.CreateCharacter(identity, pos, ctx, characterName);
    }
    override void OnMissionFinish()
    {
        Finish("MISSION_FINISH"); super.OnMissionFinish();
    }
}
Mission CreateCustomMission(string path) { return new BalticContinuousPursuitMission(); }
