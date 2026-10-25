// Temporary, dedicated-server-only, read-only world consumer. No RPC or actors.
// Inputs/server logs only: no client state or network synchronization.
// Installed contracts: game.c:1162,1174-1187; aiworld.c:57-67,98,122;
// enstring.c:20,46,59,396; ensystem.c:417,443,481,501.
void main() { Print("BALTIC_FOUNDATION_CONSUMER_V5"); }

class BalticFoundationConsumerMission: MissionServer
{
    protected FileHandle m_Input;
    protected FileHandle m_Output;
    protected ref array<string> m_Fields;
    protected ref TVectorArray m_Path;
    protected ref PGFilter m_Walk;
    protected ref PGFilter m_None;
    protected int m_Count;
    protected int m_Stage;
    protected bool m_Finished;

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        m_Fields = new array<string>;
        m_Path = new TVectorArray;
        m_Walk = new PGFilter;
        m_Walk.SetFlags(PGPolyFlags.WALK, PGPolyFlags.SWIM | PGPolyFlags.SWIM_SEA | PGPolyFlags.DISABLED, PGPolyFlags.NONE);
        m_None = new PGFilter;
        m_None.SetFlags(PGPolyFlags.NONE, PGPolyFlags.ALL, PGPolyFlags.NONE);
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(Begin, 15000, false);
    }

    void Begin()
    {
        m_Input = OpenFile("$mission:water-points.csv", FileMode.READ);
        m_Output = OpenFile("$profile:baltic_foundation_water_v5.log", FileMode.WRITE);
        if (!m_Input || !m_Output) { Finish("INPUT_OUTPUT_ERROR"); return; }
        FPrintln(m_Output, "BALTIC_FOUNDATION_WATER_V5");
        FPrintln(m_Output, "world=" + GetGame().GetWorldName());
        string seaRow = "SEA;" + GetGame().SurfaceGetSeaLevelMin() + ";" + GetGame().SurfaceGetSeaLevelMax();
        FPrintln(m_Output, seaRow);
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(Batch, 100, true);
    }

    void WaterPoint()
    {
        vector query = m_Fields[2].ToVector();
        float ground = GetGame().SurfaceY(query[0], query[2]);
        query[1] = ground + 1;
        if (m_Fields[0] == "W")
        {
            query[1] = m_Fields[4].ToFloat() + 0.25;
            if (query[1] < 1.5) query[1] = 1.5;
        }
        // Query-order discriminator: SurfaceIsPond primes the scenery lookup.
        bool pond = GetGame().SurfaceIsPond(query[0],query[2]);
        bool sea = GetGame().SurfaceIsSea(query[0],query[2]);
        float surface = GetGame().GetWaterSurfaceHeightNoFakeWave(query);
        string surfaceType;
        float typeHeight = GetGame().SurfaceGetType3D(query[0],query[1],query[2],surfaceType);
        bool liquid = false;
        int liquidType = 0;
        SurfaceInfo info;
        if (surfaceType != "")
        {
            info = SurfaceInfo.GetByName(surfaceType);
            if (info)
            {
                liquid = info.IsLiquid();
                liquidType = info.GetLiquidType();
            }
        }
        else surfaceType = "empty";
        vector atGround = Vector(query[0], ground, query[2]);
        string row = "S;" + m_Fields[1] + ";" + query + ";" + ground + ";" + surface;
        row = row + ";" + sea + ";" + pond;
        row = row + ";" + GetGame().GetWaterDepth(atGround);
        row = row + ";" + typeHeight + ";" + surfaceType + ";" + liquid + ";" + liquidType;
        FPrintln(m_Output,row);
    }

    void NavPoint()
    {
        vector query = m_Fields[2].ToVector();
        query[1] = GetGame().SurfaceY(query[0],query[2]);
        vector sampled;
        bool found = GetGame().GetWorld().GetAIWorld().SampleNavmeshPosition(query,2,m_Walk,sampled);
        FPrintln(m_Output,"D;" + m_Fields[1] + ";" + query + ";" + found + ";" + sampled);
    }

    void NavPath()
    {
        vector start = m_Fields[2].ToVector();
        vector end = m_Fields[3].ToVector();
        start[1] = GetGame().SurfaceY(start[0],start[2]);
        end[1] = GetGame().SurfaceY(end[0],end[2]);
        PGFilter filter = m_Walk;
        if (m_Fields[1] == "negative") filter = m_None;
        AIWorld ai = GetGame().GetWorld().GetAIWorld();
        vector a,b;
        bool sa = ai.SampleNavmeshPosition(start,2,filter,a);
        bool sb = ai.SampleNavmeshPosition(end,2,filter,b);
        bool found = false;
        m_Path.Clear();
        if (sa && sb) found = ai.FindPath(a,b,filter,m_Path);
        FPrintln(m_Output,"Q;" + m_Fields[1] + ";" + sa + ";" + sb + ";" + found + ";" + m_Path.Count());
        for (int i=0; i<m_Path.Count(); i++) FPrintln(m_Output,"P;" + m_Fields[1] + ";" + i + ";" + m_Path[i]);
    }

    void Batch()
    {
        if (m_Finished) return;
        string line;
        for (int i=0; i<500; i++)
        {
            if (FGets(m_Input,line) <= 0) { NextStage(); return; }
            m_Fields.Clear();
            line.Split(";",m_Fields);
            if (m_Stage == 0)
            {
                if (m_Fields.Count()!=7) { Finish("MALFORMED_WATER_INPUT"); return; }
                WaterPoint();
            }
            else if (m_Fields.Count()==3 && m_Fields[0]=="D") NavPoint();
            else if (m_Fields.Count()==4 && m_Fields[0]=="Q") NavPath();
            else { Finish("MALFORMED_NAV_INPUT"); return; }
            m_Count++;
        }
    }

    void NextStage()
    {
        if (m_Stage == 0)
        {
            FPrintln(m_Output,"BALTIC_FOUNDATION_WATER_COMPLETE;" + m_Count);
            CloseFile(m_Input); m_Input = null;
            CloseFile(m_Output); m_Output = null;
            m_Stage = 1;
            m_Count = 0;
            m_Input = OpenFile("$mission:nav-points.csv",FileMode.READ);
            m_Output = OpenFile("$profile:baltic_foundation_nav_v5.log",FileMode.WRITE);
            if (!m_Input || !m_Output) { Finish("NAV_INPUT_OUTPUT_ERROR"); return; }
            FPrintln(m_Output,"BALTIC_FOUNDATION_NAV_V5");
            FPrintln(m_Output,"world=" + GetGame().GetWorldName());
            FPrintln(m_Output,"flags=" + m_Walk.GetIncludeFlags() + ";" + m_Walk.GetExcludeFlags());
        }
        else
        {
            FPrintln(m_Output,"BALTIC_FOUNDATION_NAV_COMPLETE");
            Finish("COMPLETE");
        }
    }

    void Finish(string reason)
    {
        if (m_Finished) return;
        m_Finished = true;
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(Batch);
        if (m_Input) { CloseFile(m_Input); m_Input = null; }
        if (m_Output) { CloseFile(m_Output); m_Output = null; }
        Print("BALTIC_FOUNDATION_CONSUMER_END;" + reason);
    }

    void ~BalticFoundationConsumerMission()
    {
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(Begin);
        Finish("MISSION_CLOSED");
    }
}

Mission CreateCustomMission(string path) { return new BalticFoundationConsumerMission(); }
