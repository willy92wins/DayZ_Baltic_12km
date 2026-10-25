"""Freeze native path queries that distinguish bridge graph from noise behavior."""
from pathlib import Path
import copy, hashlib, json, shutil

ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

CODE=r'''void main() {}
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
'''

def main():
    parent=ROOT/'evidence/overnight-2026-10-01/regional-chase-v1/reference.json';ref=json.loads(parent.read_text())
    ev=ROOT/'evidence/overnight-2026-10-01/bridge-path-v10';mission=ROOT/'missions/BalticBridgePathV10.BalticTrial'
    deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
    for p in (ev,mission,deployed):
        if p.exists():raise ValueError('Fresh output required: '+str(p))
    cases=[dict(name=str(c['case']),start=c['start'],goal=c['goal']) for c in ref['cases'][13:]]
    west=ref['cases'][13]['start'];east=ref['cases'][17]['goal']
    cases.extend([dict(name='full_out',start=west,goal=east),dict(name='full_back',start=east,goal=west),dict(name='negative',start=west,goal=east)])
    ev.mkdir(parents=True);mission.mkdir(parents=True);(mission/'init.c').write_text(CODE)
    rows=[c['name']+';'+' '.join(f'{v:.9g}' for v in c['start'])+';'+' '.join(f'{v:.9g}' for v in c['goal']) for c in cases]
    (mission/'queries.csv').write_text('\n'.join(rows)+'\n');shutil.copytree(mission,deployed)
    record=dict(status='FROZEN_BEFORE_RUNTIME',parent_sha256=sha(parent),cases=cases,bridge=ref['bridge'],terrain=ref['terrain'],terrain_sha256=ref['terrain_sha256'],
        world_pbo_sha256='d1008dd6c882193706f06c5e7b8495ee1a357f5819a8574118784f7e90f18577',
        mission={str(p):sha(p) for p in mission.iterdir()},deployed_mission=str(deployed),
        criteria=dict(max_sample_distance_m=2,max_height_error_m=.8,max_lateral_m=4,maximum_heightfield_error_m=.002),
        limits=['Graph query only; does not override or accept physical actors.','Eight directed bridge queries plus one NONE filter control.'])
    p=ev/'reference.json';p.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(reference_sha256=sha(p),mission=mission.name)))

if __name__=='__main__':main()
