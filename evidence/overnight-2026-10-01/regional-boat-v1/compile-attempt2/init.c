// Temporary dedicated-server consumer. One owned boat, no RPC or pose forcing.
void main() { Print("BALTIC_REGIONAL_BOAT_V1"); }

class BalticRegionalBoatMission: MissionServer
{
    protected BoatScript m_Boat;
    protected ref array<vector> m_Route;
    protected ref array<string> m_Fields;
    protected FileHandle m_Log;
    protected int m_Case = -1;
    protected int m_Start;
    protected int m_Tick;
    protected int m_Target;
    protected bool m_EngineRequested;
    protected bool m_Active;
    protected float m_HealthStart;
    protected float m_Arrived = -1;

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        m_Route = new array<vector>;
        m_Fields = new array<string>;
        m_Log = OpenFile("$profile:baltic_regional_boat_v1.log", FileMode.WRITE);
        if (!m_Log) return;
        FPrintln(m_Log,"BALTIC_REGIONAL_BOAT_V1");
        FPrintln(m_Log,"EMPTY_BOAT_INDEPENDENT_OUTWARD_AND_REVERSE_NO_TURN_OR_CREW_ACCEPTANCE");
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BeginNext,30000,false);
    }

    void BeginNext()
    {
        m_Case++;
        if (m_Case >= 8)
        {
            FPrintln(m_Log,"END;ALL_CASES_COMPLETE");
            CloseFile(m_Log);
            m_Log = 0;
            return;
        }
        m_Route.Clear();
        FileHandle input = OpenFile("$mission:routes.csv", FileMode.READ);
        if (!input) { FPrintln(m_Log,"END;INPUT_FAILED"); CloseFile(m_Log); m_Log=0; return; }
        string row;
        while (FGets(input,row)>=0)
        {
            if (row=="") continue;
            m_Fields.Clear(); row.Split(";",m_Fields);
            if (m_Fields.Count()!=5) continue;
            if (m_Fields[0].ToInt()!=m_Case) continue;
            m_Route.Insert(Vector(m_Fields[2].ToFloat(),m_Fields[3].ToFloat(),m_Fields[4].ToFloat()));
        }
        CloseFile(input);
        if (m_Route.Count()<3) { FPrintln(m_Log,"END;BAD_ROUTE"); CloseFile(m_Log); m_Log=0; return; }
        FPrintln(m_Log,"CASE;"+m_Case+";"+m_Route.Count());
        vector spawn=m_Route[0]; spawn[1]=spawn[1]+0.3;
        m_Boat=BoatScript.Cast(GetGame().CreateObjectEx("Boat_01_Orange",spawn,ECE_CREATEPHYSICS));
        if (!m_Boat) { EndCase("SPAWN_FAILED"); return; }
        vector direction=m_Route[1]-m_Route[0]; direction[1]=0;
        vector orientation=direction.VectorToAngles(); orientation[1]=0; orientation[2]=0;
        m_Boat.SetOrientation(orientation);
        m_Boat.GetInventory().CreateAttachment("SparkPlug");
        m_Boat.Fill(BoatFluid.FUEL,m_Boat.GetFluidCapacity(BoatFluid.FUEL));
        m_HealthStart=m_Boat.GetHealth("","Health");
        m_Start=GetGame().GetTime(); m_Tick=0; m_Target=1;
        m_EngineRequested=false; m_Active=true; m_Arrived=-1;
        FPrintln(m_Log,"SPAWN;"+m_Case+";"+m_Boat.GetPosition()+";"+m_Boat.GetOrientation()+";"+m_HealthStart);
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BoatTick,100,true);
    }

    float RouteDistance(vector pos)
    {
        float best=100000;
        int last = m_Route.Count() - 1;
        for (int i=0;i<last;i++)
        {
            vector a=m_Route[i]; vector d=m_Route[i+1] - a; vector q=pos - a;
            d[1]=0; q[1]=0;
            float square=d[0]*d[0]+d[2]*d[2];
            if (square<=0) continue;
            float t=Math.Clamp((q[0]*d[0]+q[2]*d[2])/square,0,1);
            vector residual=q - d*t;
            best=Math.Min(best,residual.Length());
        }
        return best;
    }

    void BoatTick()
    {
        if (!m_Active) return;
        if (!m_Boat) { EndCase("BOAT_LOST"); return; }
        float seconds=(GetGame().GetTime() - m_Start)*0.001;
        vector pos=m_Boat.GetPosition(); vector orientation=m_Boat.GetOrientation();
        vector velocity=GetVelocity(m_Boat); velocity[1]=0;
        float speed=velocity.Length(); float health=m_Boat.GetHealth("","Health");
        float routeDistance=RouteDistance(pos);
        if (seconds>=15 && !m_EngineRequested)
        {
            m_EngineRequested=true; m_Boat.EngineStart();
            FPrintln(m_Log,"ENGINE_REQUEST;"+m_Case+";"+seconds);
        }
        float steer=0; float throttle=0;
        if (seconds>=15 && m_Arrived<0)
        {
            vector delta=m_Route[m_Target] - pos; delta[1]=0;
            if (seconds>=20 && delta.Length()<4)
            {
                if (m_Target>=m_Route.Count() - 1)
                {
                    m_Arrived=seconds;
                    m_Boat.BalticProbeStop();
                    FPrintln(m_Log,"ARRIVED;"+m_Case+";"+seconds+";"+pos);
                }
                else
                {
                    m_Target++;
                    delta=m_Route[m_Target] - pos;delta[1]=0;
                }
            }
            if (m_Arrived<0)
            {
                vector heading=delta.VectorToAngles();
                float error=heading[0] - orientation[0];
                while (error>180) error-=360;
                while (error< -180) error+=360;
                steer=Math.Clamp(error/40,-0.6,0.6);
                if (seconds>=20 && speed<=2.5) throttle=0.22;
                m_Boat.BalticProbeSetInput(throttle,steer,true,true);
            }
        }
        m_Tick++;
        if (m_Tick%5==0)
        {
            vector propeller=m_Boat.ModelToWorld(m_Boat.PropellerGetPosition());
            float ground=GetGame().SurfaceY(pos[0],pos[2]);
            string record="B;"+m_Case+";"+seconds+";"+pos[0]+";"+pos[1]+";"+pos[2]+";"+orientation[0]+";"+speed+";"+health;
            record=record+";"+m_Boat.EngineIsOn()+";"+m_Boat.GetCurrentGear()+";"+m_Boat.GetNeutralGear();
            record=record+";"+m_Boat.EngineGetRPM()+";"+m_Boat.PropellerGetAngularVelocity()+";"+m_Boat.BalticProbeGetCalls();
            record=record+";"+m_Boat.GetThrottle()+";"+m_Boat.GetSteering()+";"+m_Target+";"+routeDistance;
            record=record+";"+ground+";"+GetGame().GetWaterDepth(propeller)+";"+m_Boat.GetFluidFraction(BoatFluid.FUEL);
            FPrintln(m_Log,record);
        }
        if (health<m_HealthStart - 1) EndCase("DAMAGE_STOP");
        else if (routeDistance>7) EndCase("CHANNEL_DEVIATION_STOP");
        else if (seconds>25 && m_Arrived<0 && !m_Boat.EngineIsOn()) EndCase("ENGINE_STOPPED");
        else if (seconds>450) EndCase("TIMEOUT_CONTROL_INCONCLUSIVE");
        else if (m_Arrived>=0 && seconds - m_Arrived>=10) EndCase("ARRIVED_AND_STOPPED");
    }

    void EndCase(string reason)
    {
        m_Active=false;
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BoatTick);
        if (m_Log) FPrintln(m_Log,"CASE_END;"+m_Case+";"+reason);
        if (m_Boat)
        {
            m_Boat.BalticProbeStop();
            GetGame().ObjectDelete(m_Boat); m_Boat=null;
        }
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BeginNext,2000,false);
    }
}

Mission CreateCustomMission(string path) { return new BalticRegionalBoatMission(); }
