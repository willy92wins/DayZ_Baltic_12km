// Bounded physical consumer. No infected motion overrides after spawning.
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

class BalticRegionalChaseMission: MissionServer
{
    protected float m_Time;
    protected float m_StageStart;
    protected float m_PreparedAt;
    protected float m_NextStage = 15;
    protected float m_NextSample;
    protected float m_NextNoise;
    protected int m_Case;
    protected int m_MaxMind;
    protected bool m_Active;
    protected bool m_Preparing;
    protected bool m_Finished;
    protected DayZInfected m_Actor;
    protected Man m_Prey;
    protected ref array<Man> m_Observers = new array<Man>;
    protected ref array<vector> m_Starts = new array<vector>;
    protected ref array<vector> m_Goals = new array<vector>;
    protected ref array<string> m_Fields = new array<string>;
    protected ref NoiseParams m_Noise;
    protected ref PGFilter m_Filter;
    protected vector m_Goal;
    protected vector m_Start;
    protected FileHandle m_Log;

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        m_Log = OpenFile("$profile:baltic_regional_chase_v1.log", FileMode.WRITE);
        if (!m_Log) { m_Finished=true; return; }
        FPrintln(m_Log,"BALTIC_REGIONAL_CHASE_V1");
        FPrintln(m_Log,"world="+GetGame().GetWorldName());
        FileHandle input = OpenFile("$mission:cases.csv", FileMode.READ);
        if (!input) { Finish("BAD_INPUT"); return; }
        string row;
        while (FGets(input,row)>=0)
        {
            if (row=="") continue;
            m_Fields.Clear(); row.Split(";",m_Fields);
            if (m_Fields.Count()!=3 || m_Fields[0].ToInt()!=m_Starts.Count())
            { CloseFile(input); Finish("BAD_CASE_SCHEMA"); return; }
            m_Starts.Insert(m_Fields[1].ToVector());
            m_Goals.Insert(m_Fields[2].ToVector());
        }
        CloseFile(input);
        if (m_Starts.Count()!=19) { Finish("BAD_CASE_COUNT"); return; }
        m_Noise=new NoiseParams;
        m_Noise.LoadFromPath("CfgWeapons Rifle_Base NoiseShoot");
        m_Filter=new PGFilter;
        m_Filter.SetFlags(PGPolyFlags.WALK,PGPolyFlags.SWIM | PGPolyFlags.SWIM_SEA | PGPolyFlags.DISABLED,PGPolyFlags.NONE);
    }

    void Record(string marker)
    {
        if (!m_Log) return;
        vector pos; vector prey;
        float health; float ground; float road;
        int mind=-1;
        if (m_Prey) prey=m_Prey.GetPosition();
        if (m_Actor)
        {
            pos=m_Actor.GetPosition();
            health=m_Actor.GetHealth("","Health");
            ground=GetGame().SurfaceY(pos[0],pos[2]);
            road=GetGame().SurfaceRoadY(pos[0],pos[2]);
            DayZInfectedInputController control=m_Actor.GetInputController();
            if (control && m_Time-m_StageStart>=1) mind=control.GetMindState();
        }
        FPrintln(m_Log,"A;"+m_Case+";"+m_Time+";"+marker+";"+pos.ToString()+";"+prey.ToString()+";"+m_Goal.ToString()+";"+health+";"+mind+";"+ground+";"+road);
    }

    void CleanActor()
    {
        if (m_Actor) GetGame().ObjectDelete(m_Actor);
        m_Actor=null;
    }

    void Finish(string reason)
    {
        CleanActor();
        m_Active=false; m_Preparing=false; m_Finished=true;
        if (m_Log) { FPrintln(m_Log,"END;"+reason); CloseFile(m_Log); m_Log=null; }
    }

    void EndCase(string reason)
    {
        Record(reason);
        CleanActor();
        m_Active=false; m_Preparing=false;
        m_Case++;
        m_NextStage=m_Time+6;
        if (m_Case>=m_Starts.Count()) Finish("ALL_CASES_COMPLETE");
    }

    void Prepare()
    {
        m_Start=m_Starts[m_Case]; m_Goal=m_Goals[m_Case];
        vector navStart,navGoal;
        AIWorld ai=GetGame().GetWorld().GetAIWorld();
        if (!ai || !ai.SampleNavmeshPosition(m_Start,2,m_Filter,navStart) || !ai.SampleNavmeshPosition(m_Goal,2,m_Filter,navGoal))
        { EndCase("INCONCLUSIVE_NAV_ANCHOR"); return; }
        FPrintln(m_Log,"ANCHOR;"+m_Case+";"+m_Start.ToString()+";"+m_Goal.ToString()+";"+navStart.ToString()+";"+navGoal.ToString());
        m_Prey.SetPosition(m_Goal);
        m_Prey.SetAllowDamage(false);
        m_Preparing=true; m_PreparedAt=m_Time; m_NextSample=m_Time;
        Record("SETTLE_BEGIN");
    }

    void Begin()
    {
        m_Preparing=false;
        m_Actor=DayZInfected.Cast(GetGame().CreateObjectEx("ZmbF_JournalistNormal_Blue",m_Start,ECE_PLACE_ON_SURFACE | ECE_INITAI | ECE_CREATEPHYSICS));
        if (!m_Actor) { EndCase("FAILED_SPAWN"); return; }
        vector direction=m_Goal-m_Start; direction[1]=0;
        vector orientation=direction.VectorToAngles(); orientation[1]=0; orientation[2]=0;
        m_Actor.SetOrientation(orientation);
        m_StageStart=m_Time; m_NextNoise=m_Time+3; m_NextSample=m_Time;
        m_MaxMind=0; m_Active=true;
        Record("SPAWN");
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName()!="BalticTrial" || m_Finished) return;
        m_Time=m_Time+timeslice;
        if (m_Time>3500) { Finish("SESSION_TIMEOUT"); return; }
        if (m_Prey)
        {
            Human human=Human.Cast(m_Prey);
            HumanInputController preyControl;
            if (human) preyControl=human.GetInputController();
            if (preyControl) preyControl.OverrideMovementSpeed(HumanInputControllerOverrideType.ENABLED,0);
        }
        if (m_Preparing)
        {
            if (m_Time>=m_NextSample) { Record("SETTLE"); m_NextSample=m_Time+0.2; }
            if (m_Time-m_PreparedAt>=20) Begin();
            return;
        }
        if (!m_Active)
        {
            if (m_Time<m_NextStage) return;
            m_Observers.Clear(); GetGame().GetPlayers(m_Observers);
            if (m_Observers.Count()==0) return;
            if (m_Observers.Count()!=1) { Finish("INCONCLUSIVE_PLAYER_COUNT"); return; }
            m_Prey=m_Observers[0]; Prepare(); return;
        }
        if (!m_Actor || m_Actor.GetHealth("","Health")<=0) { EndCase("FAILED_ACTOR"); return; }
        if (m_Time-m_StageStart>90) { EndCase("TIMEOUT"); return; }
        DayZInfectedInputController input=m_Actor.GetInputController();
        int mind=-1;
        if (input && m_Time-m_StageStart>=1) mind=input.GetMindState();
        if (mind>=1 && mind<=4 && mind>m_MaxMind) m_MaxMind=mind;
        if (m_Time>=m_NextNoise)
        {
            GetGame().GetNoiseSystem().AddNoisePos(m_Prey,m_Prey.GetPosition(),m_Noise,4);
            m_NextNoise=m_Time+3; Record("NOISE");
        }
        if (m_Time>=m_NextSample) { Record("SAMPLE"); m_NextSample=m_Time+0.2; }
        if (vector.Distance(m_Actor.GetPosition(),m_Goal)<=4 && m_MaxMind>=1) EndCase("REACHED");
    }

    override PlayerBase CreateCharacter(PlayerIdentity identity,vector pos,ParamsReadContext ctx,string characterName)
    {
        pos="5100 0 7644"; pos[1]=GetGame().SurfaceY(pos[0],pos[2])+0.2;
        return super.CreateCharacter(identity,pos,ctx,characterName);
    }

    override void OnMissionFinish()
    {
        Finish("MISSION_FINISH");
        if (m_Prey)
        {
            Human human=Human.Cast(m_Prey);
            HumanInputController control;
            if (human) control=human.GetInputController();
            if (control) control.OverrideMovementSpeed(HumanInputControllerOverrideType.DISABLED,0);
            m_Prey.SetAllowDamage(true);
        }
        super.OnMissionFinish();
    }
}

Mission CreateCustomMission(string path) { return new BalticRegionalChaseMission(); }
