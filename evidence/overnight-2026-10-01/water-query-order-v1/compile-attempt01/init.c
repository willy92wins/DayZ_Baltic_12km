// Temporary server-only, read-only discriminator. No terrain edits or actors.
// Verified contracts: game.c:1162-1187,1127,933,1525; ensystem.c:417,443,481,501.
void main() { Print("BALTIC_WATER_QUERY_ORDER_V1"); }

class BalticWaterQueryOrderMission: MissionServer
{
    protected FileHandle m_Input;
    protected FileHandle m_Output;
    protected ref array<string> m_Fields;
    protected int m_Count;
    protected int m_Stage;
    protected bool m_Finished;

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        m_Fields = new array<string>;
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(Begin,15000,false);
    }

    void Begin()
    {
        m_Input = OpenFile("$mission:points.csv",FileMode.READ);
        m_Output = OpenFile("$profile:baltic_water_query_order_v1.log",FileMode.WRITE);
        if (!m_Input || !m_Output) { Finish("INPUT_OUTPUT_ERROR"); return; }
        FPrintln(m_Output,"BALTIC_WATER_QUERY_ORDER_V1");
        FPrintln(m_Output,"world=" + GetGame().GetWorldName());
        FPrintln(m_Output,"stage;index;query;ground;road;prepond;raw1;raw2;sea;pond;raw3;typeY;type;raw4;depth;pond2");
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(Point,30,true);
    }

    void Point()
    {
        if (m_Finished) return;
        string line;
        if (FGets(m_Input,line) <= 0) { NextStage(); return; }
        m_Fields.Clear();
        line.Split(";",m_Fields);
        if (m_Fields.Count()!=7) { Finish("MALFORMED_INPUT"); return; }
        vector query = m_Fields[2].ToVector();
        float ground = GetGame().SurfaceY(query[0],query[2]);
        query[1] = ground+1;
        if (m_Fields[0]=="W")
        {
            query[1] = m_Fields[4].ToFloat()+0.25;
            if (query[1]<1.5) query[1]=1.5;
        }
        bool prepond = false;
        if (m_Stage==1) prepond = GetGame().SurfaceIsPond(query[0],query[2]);
        float raw1 = GetGame().GetWaterSurfaceHeightNoFakeWave(query);
        float raw2 = GetGame().GetWaterSurfaceHeightNoFakeWave(query);
        bool sea = GetGame().SurfaceIsSea(query[0],query[2]);
        bool pond = GetGame().SurfaceIsPond(query[0],query[2]);
        float raw3 = GetGame().GetWaterSurfaceHeightNoFakeWave(query);
        string type = "unresolved";
        float typeY = GetGame().SurfaceGetType3D(query[0],query[1],query[2],type);
        if (type=="") type="empty";
        float raw4 = GetGame().GetWaterSurfaceHeightNoFakeWave(query);
        vector atGround = Vector(query[0],ground,query[2]);
        float depth = GetGame().GetWaterDepth(atGround);
        bool pond2 = GetGame().SurfaceIsPond(query[0],query[2]);
        float road = GetGame().SurfaceRoadY(query[0],query[2]);
        string row = m_Stage + ";" + m_Fields[1] + ";" + query + ";" + ground + ";" + road;
        row = row + ";" + prepond + ";" + raw1 + ";" + raw2 + ";" + sea + ";" + pond;
        row = row + ";" + raw3 + ";" + typeY + ";" + type + ";" + raw4 + ";" + depth + ";" + pond2;
        FPrintln(m_Output,row);
        m_Count++;
    }

    void NextStage()
    {
        FPrintln(m_Output,"STAGE_COMPLETE;" + m_Stage + ";" + m_Count);
        CloseFile(m_Input);m_Input=null;
        if (m_Stage==0)
        {
            m_Stage=1;m_Count=0;
            m_Input=OpenFile("$mission:points.csv",FileMode.READ);
            if (!m_Input) Finish("REOPEN_ERROR");
        }
        else Finish("COMPLETE");
    }

    void Finish(string reason)
    {
        if (m_Finished) return;
        m_Finished=true;
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(Point);
        if (m_Input) { CloseFile(m_Input);m_Input=null; }
        if (m_Output) { FPrintln(m_Output,"BALTIC_WATER_QUERY_ORDER_END;"+reason);CloseFile(m_Output);m_Output=null; }
        Print("BALTIC_WATER_QUERY_ORDER_END;"+reason);
    }

    void ~BalticWaterQueryOrderMission()
    {
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(Begin);
        Finish("MISSION_CLOSED");
    }
}

Mission CreateCustomMission(string path) { return new BalticWaterQueryOrderMission(); }
