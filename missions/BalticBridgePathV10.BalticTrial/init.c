void main() {}
class BalticBridgePathMission: MissionServer
{
    protected float m_Elapsed;
    protected bool m_Done;
    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (m_Done || !GetGame().IsDedicatedServer()) return;
        m_Elapsed = m_Elapsed + timeslice;
        if (m_Elapsed < 5) return;
        m_Done = true;
        FileHandle input=OpenFile("$mission:queries.csv",FileMode.READ);
        FileHandle output=OpenFile("$profile:baltic_bridge_path_v10.log",FileMode.WRITE);
        if (!input || !output) return;
        FPrintln(output,"BALTIC_BRIDGE_PATH_V10;"+GetGame().GetWorldName());
        AIWorld ai=GetGame().GetWorld().GetAIWorld();
        PGFilter walk=new PGFilter;
        walk.SetFlags(PGPolyFlags.WALK,PGPolyFlags.SWIM | PGPolyFlags.SWIM_SEA | PGPolyFlags.DISABLED,PGPolyFlags.NONE);
        PGFilter none=new PGFilter;
        none.SetFlags(PGPolyFlags.NONE,PGPolyFlags.ALL,PGPolyFlags.NONE);
        ref array<string> fields=new array<string>;
        ref array<vector> path=new array<vector>;
        string row;
        int count=0;
        while (FGets(input,row)>=0)
        {
            if (row=="") continue;
            fields.Clear();row.Split(";",fields);
            if (fields.Count()!=3) { FPrintln(output,"FAIL;SCHEMA"); break; }
            vector start=fields[1].ToVector();vector goal=fields[2].ToVector();
            PGFilter filter=walk;
            if (fields[0]=="negative") filter=none;
            vector a,b;
            bool sa=ai.SampleNavmeshPosition(start,2,filter,a);
            bool sb=ai.SampleNavmeshPosition(goal,2,filter,b);
            path.Clear();bool found=false;
            if (sa && sb) found=ai.FindPath(a,b,filter,path);
            FPrintln(output,"Q;"+fields[0]+";"+sa+";"+sb+";"+found+";"+path.Count()+";"+start.ToString()+";"+goal.ToString()+";"+a.ToString()+";"+b.ToString());
            for (int i=0;i<path.Count();i++)
            {
                vector p=path[i];
                vector groundSample=Vector(p[0],GetGame().SurfaceY(p[0],p[2]),p[2]);
                vector roadSample=Vector(p[0],GetGame().SurfaceRoadY(p[0],p[2]),p[2]);
                FPrintln(output,"P;"+fields[0]+";"+i+";"+p.ToString()+";"+groundSample.ToString()+";"+roadSample.ToString());
            }
            count++;
        }
        FPrintln(output,"END;"+count);
        CloseFile(input);CloseFile(output);
    }
}
Mission CreateCustomMission(string path) { return new BalticBridgePathMission(); }
