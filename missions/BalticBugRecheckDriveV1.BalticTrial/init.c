void main() { Print("BALTIC_FOUNDATION_DRIVE_V1"); }

class BalticFoundationDrive: MissionServer
{
    protected CarScript m_Car;
    protected ref array<vector> m_Route;
    protected ref array<string> m_Fields;
    protected FileHandle m_Log;
    protected int m_Case=-1;
    protected int m_Start;
    protected int m_Tick;
    protected int m_Nearest;
    protected bool m_Active;
    protected bool m_EngineRequested;
    protected float m_HealthStart;
    protected float m_Arrived=-1;
    protected float m_Stopped=-1;

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName()!="BalticTrial") return;
        m_Route=new array<vector>; m_Fields=new array<string>;
        m_Log=OpenFile("$profile:baltic_bug_recheck_drive_v1.log",FileMode.WRITE);
        if (!m_Log) return;
        FPrintln(m_Log,"BALTIC_FOUNDATION_DRIVE_V1");
        FPrintln(m_Log,"EMPTY_VANILLA_SEDAN_NO_POSE_OR_VELOCITY_FORCING");
        FileHandle placement=OpenFile("$profile:baltic_bug_recheck_drive_v1_placement.log",FileMode.WRITE);
        if (placement) { FPrintln(placement,"BALTIC_INITIAL_SEDAN_PLACEMENT_V3"); CloseFile(placement); }
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BeginNext,30000,false);
    }

    void PlacementRecord(string stage,vector wanted)
    {
        FileHandle f=OpenFile("$profile:baltic_bug_recheck_drive_v1_placement.log",FileMode.APPEND);
        if (!f) return;
        FPrintln(f,"P;"+m_Case+";"+stage+";"+wanted.ToString()+";"+m_Car.GetPosition().ToString()+";"+m_Car.GetOrientation().ToString());
        CloseFile(f);
    }

    void BeginNext()
    {
        m_Case++;
        if (m_Case>=6) { Finish("ALL_CASES_COMPLETE"); return; }
        m_Route.Clear();
        FileHandle f=OpenFile("$mission:routes.csv",FileMode.READ);
        if (!f) { Finish("INPUT_FAILED"); return; }
        string row;
        while (FGets(f,row)>=0)
        {
            m_Fields.Clear(); row.Split(";",m_Fields);
            if (m_Fields.Count()!=5 || m_Fields[0].ToInt()!=m_Case) continue;
            m_Route.Insert(Vector(m_Fields[2].ToFloat(),m_Fields[3].ToFloat(),m_Fields[4].ToFloat()));
        }
        CloseFile(f);
        if (m_Route.Count()<3) { Finish("BAD_ROUTE"); return; }
        FPrintln(m_Log,"CASE;"+m_Case+";"+m_Route.Count());
        vector spawn=m_Route[0]; spawn[1]=spawn[1]+0.5;
        m_Car=CarScript.Cast(GetGame().CreateObjectEx("CivilianSedan",spawn,ECE_CREATEPHYSICS));
        if (!m_Car) { EndCase("SPAWN_FAILED"); return; }
        PlacementRecord("CREATED",spawn);
        vector direction=m_Route[1] - m_Route[0]; direction[1]=0;
        vector orientation=direction.VectorToAngles(); orientation[1]=0; orientation[2]=0;
        m_Car.SetOrientation(orientation);
        PlacementRecord("ORIENTED",spawn);
        EntityAI battery=m_Car.GetInventory().CreateAttachment("CarBattery");
        if (battery && battery.GetCompEM()) battery.GetCompEM().SetEnergy0To1(1);
        m_Car.GetInventory().CreateAttachment("CarRadiator");
        m_Car.GetInventory().CreateAttachment("SparkPlug");
        for (int w=0;w<4;w++) m_Car.GetInventory().CreateAttachment("CivSedanWheel");
        m_Car.Fill(CarFluid.FUEL,m_Car.GetFluidCapacity(CarFluid.FUEL));
        m_Car.Fill(CarFluid.OIL,m_Car.GetFluidCapacity(CarFluid.OIL));
        m_Car.Fill(CarFluid.BRAKE,m_Car.GetFluidCapacity(CarFluid.BRAKE));
        m_Car.Fill(CarFluid.COOLANT,m_Car.GetFluidCapacity(CarFluid.COOLANT));
        PlacementRecord("ASSEMBLED",spawn);
        // Initial setup only, before the15s settlement and all physical motion.
        m_Car.SetPosition(spawn);
        PlacementRecord("PLACED",spawn);
        m_HealthStart=m_Car.GetHealth("","Health");
        m_Start=GetGame().GetTime(); m_Tick=0; m_Nearest=0;
        m_EngineRequested=false; m_Active=true; m_Arrived=-1; m_Stopped=-1;
        FPrintln(m_Log,"SPAWN;"+m_Case+";"+m_Car.GetPosition().ToString()+";"+m_Car.GetOrientation().ToString()+";"+m_HealthStart+";"+m_Car.WheelCountPresent());
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(DriveTick,100,true);
    }

    float NearestRoute(vector pos)
    {
        float best=100000;
        for (int i=0;i<m_Route.Count() - 1;i++)
        {
            vector d=m_Route[i+1] - m_Route[i]; d[1]=0;
            vector q=pos - m_Route[i]; q[1]=0;
            float square=d[0]*d[0]+d[2]*d[2];
            if (square<=0) continue;
            float t=Math.Clamp((q[0]*d[0]+q[2]*d[2])/square,0,1);
            vector residual=q - d*t;
            float distance=residual.Length();
            if (distance<best) { best=distance; m_Nearest=i; }
        }
        return best;
    }

    void DriveTick()
    {
        if (!m_Active) return;
        if (!m_Car) { EndCase("CAR_LOST"); return; }
        float seconds=(GetGame().GetTime() - m_Start)*0.001;
        vector pos=m_Car.GetPosition(); vector orientation=m_Car.GetOrientation();
        vector velocity=GetVelocity(m_Car); vector flatVelocity=velocity; flatVelocity[1]=0;
        float speed=flatVelocity.Length(); float health=m_Car.GetHealth("","Health");
        float routeDistance=NearestRoute(pos);
        int last=m_Route.Count() - 1;
        vector remaining=m_Route[last] - pos; remaining[1]=0;
        if (seconds>=15 && !m_EngineRequested)
        {
            m_EngineRequested=true; m_Car.EngineStart();
            FPrintln(m_Log,"ENGINE_REQUEST;"+m_Case+";"+seconds+";"+m_Car.CheckOperationalRequirements());
        }
        float throttle=0; float steering=0; float brake=1;
        int gear=CarGear.FIRST;
        if (seconds>=20 && m_Arrived<0)
        {
            if (remaining.Length()<=1.5 && speed<=0.8 && m_Nearest>=last - 6)
            {
                m_Arrived=seconds; FPrintln(m_Log,"ARRIVED;"+m_Case+";"+seconds+";"+pos.ToString());
            }
            else
            {
                int target=Math.Min(m_Nearest+5,last);
                vector delta=m_Route[target] - pos; delta[1]=0;
                vector heading=delta.VectorToAngles();
                float error=heading[0] - orientation[0];
                while (error>180) error-=360;
                while (error< -180) error+=360;
                steering=Math.Clamp(error/35,-0.6,0.6);
                float desiredSpeed=9.722222;
                if (m_Case<2) desiredSpeed=6.944444;
                if (remaining.Length()<50) desiredSpeed=4;
                if (remaining.Length()<20) desiredSpeed=2;
                if (remaining.Length()<8) desiredSpeed=0.6;
                throttle=Math.Clamp(0.1+(desiredSpeed - speed)*0.25,0,0.5);
                if (m_Case>=4 && remaining.Length()<8 && speed<0.2) throttle=0.5;
                brake=Math.Clamp((speed - desiredSpeed - 0.455556)*0.2,0,0.5);
                if (remaining.Length()<50) brake=Math.Clamp((speed - desiredSpeed)*0.8,0,1);
                if (speed>=3) gear=CarGear.SECOND;
                if (speed>=7) gear=CarGear.THIRD;
            }
        }
        if (m_Arrived<0) m_Car.BalticDriveInput(throttle,steering,brake,gear);
        else m_Car.BalticDriveStop();
        if (m_Arrived>=0)
        {
            if (speed<=0.2 && m_Stopped<0) m_Stopped=seconds;
            if (speed>0.2) m_Stopped=-1;
        }
        m_Tick++;
        vector up=m_Car.GetDirectionUp();
        if (m_Tick%2==0)
        {
            string record="D;"+m_Case+";"+seconds+";"+pos.ToString()+";"+orientation.ToString()+";"+velocity.ToString();
            record=record+";"+health+";"+m_Car.GetHealth("Engine","Health")+";"+m_Car.EngineIsOn()+";"+m_Car.EngineGetRPM();
            record=record+";"+m_Car.GetCurrentGear()+";"+m_Car.BalticDriveCalls()+";"+m_Car.GetThrottle()+";"+m_Car.GetSteering()+";"+m_Car.GetBrake();
            record=record+";"+m_Nearest+";"+routeDistance+";"+m_Car.WheelCountPresent()+";"+up[1]+";"+GetGame().SurfaceY(pos[0],pos[2]);
            for (int wheel=0;wheel<4;wheel++)
            {
                EntityAI entity=m_Car.WheelGetEntity(wheel); float wheelHealth=-1;
                if (entity) wheelHealth=entity.GetHealth("","Health");
                record=record+";"+m_Car.WheelHasContact(wheel)+";"+m_Car.WheelGetContactPosition(wheel).ToString()+";"+wheelHealth;
            }
            FPrintln(m_Log,record);
        }
        if (seconds>20 && health<m_HealthStart - 1) EndCase("DAMAGE_STOP");
        else if (routeDistance>3) EndCase("CORRIDOR_DEVIATION_STOP");
        else if (seconds>20 && up[1]<0.8660254) EndCase("TILT_STOP");
        else if (seconds>25 && m_Arrived<0 && !m_Car.EngineIsOn()) EndCase("ENGINE_STOPPED");
        else if (seconds>300) EndCase("TIMEOUT_CONTROL_INCONCLUSIVE");
        else if (m_Stopped>=0 && seconds - m_Stopped>=5.5) EndCase("ARRIVED_AND_STOPPED");
    }

    void EndCase(string reason)
    {
        m_Active=false; GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(DriveTick);
        if (m_Log) FPrintln(m_Log,"CASE_END;"+m_Case+";"+reason);
        if (m_Car) { m_Car.BalticDriveStop(); GetGame().ObjectDelete(m_Car); m_Car=null; }
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BeginNext,2000,false);
    }

    void Finish(string reason)
    {
        m_Active=false;
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(DriveTick);
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BeginNext);
        if (m_Car) { m_Car.BalticDriveStop(); GetGame().ObjectDelete(m_Car); m_Car=null; }
        if (m_Log) { FPrintln(m_Log,"END;"+reason); CloseFile(m_Log); m_Log=null; }
    }
    override void OnMissionFinish() { Finish("MISSION_FINISH"); super.OnMissionFinish(); }
}
Mission CreateCustomMission(string path) { return new BalticFoundationDrive(); }
