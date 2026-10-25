"""Bind the existing bounded load fixture to V10 and add a separate pre-load site check."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    src=ROOT/'missions/BalticAILoad.BalticTrial/init.c'
    original=ROOT/'evidence/performance/ai-load-reference-v1.json'
    ref=json.loads(original.read_text());assert sha(src)==ref['mission_sha256']
    mission=ROOT/'missions/BalticFoundationLoadV1.BalticTrial'
    ev=ROOT/'evidence/overnight-2026-10-01/foundation-load-v1'
    if mission.exists() or ev.exists():raise ValueError('Fresh outputs required')
    code=src.read_text().replace('BalticAILoadMission','BalticFoundationLoadMission').replace('baltic_ai_load_v1.log','baltic_foundation_ai_load_v1.log')
    code=code.replace('    protected bool m_LoadStarted;', '    protected bool m_LoadSitesReady;\n    protected bool m_LoadStarted;')
    anchor='        m_LoadNoise.LoadFromPath("CfgWeapons Rifle_Base NoiseShoot");'
    assert code.count(anchor)==1
    code=code.replace(anchor,anchor+'\n        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(CheckLoadSites,15000,false);')
    code=code.replace('        if (m_LoadFinished) return;','        if (m_LoadFinished || !m_LoadSitesReady) return;')
    method='''
    void CheckLoadSites()
    {
        FileHandle f=OpenFile("$profile:baltic_foundation_load_sites_v1.log",FileMode.WRITE);
        if (!f) { m_LoadFinished=true; return; }
        FPrintln(f,"BALTIC_FOUNDATION_LOAD_SITES_V1");
        PGFilter filter=new PGFilter;
        filter.SetFlags(PGPolyFlags.WALK,PGPolyFlags.SWIM | PGPolyFlags.SWIM_SEA | PGPolyFlags.DISABLED,PGPolyFlags.NONE);
        AIWorld ai=GetGame().GetWorld().GetAIWorld();
        TVectorArray route=new TVectorArray;
        vector goal="2120 0 6920";
        float goalGround=GetGame().SurfaceY(goal[0],goal[2]); goal[1]=goalGround+0.05;
        vector target;
        bool goalFound=ai.SampleNavmeshPosition(goal,2,filter,target);
        bool passed=goalFound && goalGround>=1.25 && Math.AbsFloat(target[1]-goalGround)<=0.8;
        FPrintln(f,"G;"+goal.ToString()+";"+goalGround+";"+goalFound+";"+target.ToString());
        for (int row=0;row<10;row++)
        {
            for (int col=0;col<10;col++)
            {
                vector p=Vector(2050+col*4.5,0,6900+row*4.5);
                float ground=GetGame().SurfaceY(p[0],p[2]); p[1]=ground+0.05;
                vector sampled;
                bool found=ai.SampleNavmeshPosition(p,2,filter,sampled);
                route.Clear(); bool path=false;
                if (found && goalFound) path=ai.FindPath(sampled,target,filter,route);
                bool ok=found && path && ground>=1.25 && Math.AbsFloat(sampled[1]-ground)<=0.8;
                if (!ok) passed=false;
                FPrintln(f,"S;"+(row*10+col)+";"+p.ToString()+";"+ground+";"+found+";"+sampled.ToString()+";"+path+";"+route.Count());
            }
        }
        FPrintln(f,"END;"+passed); CloseFile(f);
        m_LoadSitesReady=passed;
        if (!passed) { WriteLoad("FAIL_SITE_PRECHECK"); m_LoadFinished=true; }
    }

'''
    assert code.count('    int LoadCount()')==1
    code=code.replace('    int LoadCount()',method+'    int LoadCount()')
    code=code.replace('        CleanLoadActors();\n        if (m_LoadPrey)', '        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(CheckLoadSites);\n        CleanLoadActors();\n        if (m_LoadPrey)')
    mission.mkdir(parents=True);ev.mkdir(parents=True);(mission/'init.c').write_text(code)
    ref.update(status='FROZEN_BEFORE_RUNTIME',parent_reference_sha256=sha(original),parent_mission_sha256=sha(src),
               mission_sha256=sha(mission/'init.c'),pbo_sha256='d1008dd6c882193706f06c5e7b8495ee1a357f5819a8574118784f7e90f18577',
               water_pbo_sha256='f9a5cdf7461ff09e80a102641289513896011a78b090fdbbd1056f9b985898d3',
               navmesh_sha256='e8348efc2f361d8aa82cbd69c4fc8ad72470a628abd2a10ca8411d7f40fc313c',
               sites=dict(points=101,routes=100,minimum_ground_m=1.25,nav_radius_m=2,maximum_height_error_m=.8),
               changes=['Unique mission/log name and world binding.',
                        'Before population: separate 101-site / 100-path WALK check; no AI or measured phase changes.'],
               limits=['Same fixed population, stimulus, warmup and criteria as original baseline.',
                       'Separate site query check occurs before all measured phases.',
                       'No CE, cities, player capacity or rendering FPS acceptance.'])
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
    print(json.dumps(dict(status=ref['status'],reference_sha256=sha(ev/'reference.json'),mission_sha256=ref['mission_sha256'])))

if __name__=='__main__':main()
