"""Freeze a twelve-view diagnostic tour based on the previously exercised camera probe."""
from pathlib import Path
import hashlib,json,subprocess,sys
import numpy as np
import rasterio
from waterway_common import sample
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ev=ROOT/'evidence/overnight-2026-10-01/foundation-visual-v1'
    out=ROOT/'packages/foundation-visual-v1'
    mission=ROOT/'missions/BalticFoundationVisualV1.BalticTrial'
    for p in (ev,out,mission):
        if p.exists():raise ValueError('Fresh outputs required')
    terrain=ROOT/'tests/regional_foundation_combined_v10/baltic_regional_foundation_v10.asc'
    assert sha(terrain)=='8e25fab25e8f0909fdda302ed4ba3db4c43884c523920f5ef3424db90780eb8b'
    with rasterio.open(terrain) as ds:h=ds.read(1)
    def ground(x,z):return float(sample(h,np.array([x+200000]),np.array([z]))[0])+1.7
    poses=[
        ('Narva approach player',[2025,ground(2025,6950),6950],[2417,11,6889],1600,0),
        ('Narva medium',[2090,180,6500],[2417,2,6889],1600,0),
        ('Narva aerial',[2000,650,6100],[2417,2,6889],6000,10),
        ('SPB player',[8778,ground(8778,10122),10122],[8730,1,10250],1600,0),
        ('SPB delta aerial',[8775,600,9425],[8775,2,10125],6000,10),
        ('Neva Ladoga player',[10758,ground(10758,10062),10062],[10950,1,10800],1600,0),
        ('Ladoga distant diagnostic',[8775,1300,8725],[8775,2,10125],6000,10),
        ('Reserve aerial',[8200,600,4600],[8200,2,5700],6000,10),
        ('Reserve player',[8352,ground(8352,6234),6234],[8472,4,6234],1600,0),
        ('Northern relief',[5050,155,7470],[5225,95,7660],1600,0),
        ('Southern relief',[5540,180,250],[5800,65,522],6000,10),
        ('Regional overview',[6144,4300,1200],[6144,20,6500],12000,10)]
    base=ROOT/'tests/outline-consumer-v2/baltic_render_probe'
    source=base/'scripts/5_Mission/BalticRenderProbe.c';code=source.read_text()
    code=code.replace('baltic_outline_view_v3','baltic_foundation_visual_v1').replace('BALTIC_OUTLINE_VIEW_V3','BALTIC_FOUNDATION_VISUAL_V1')
    code=code.replace('m_OutlineControlTime < 450','m_BalticRenderPhase < 12')
    code=code.replace('if (m_BalticRenderPhase == 4) return;','if (m_BalticRenderPhase > 12) return;')
    start=code.index('        if (m_BalticRenderPhase == -1 &&')
    end=code.index('        if (m_BalticRenderNextRecord > 0',start)
    schedule=[];refs=[]
    for i,(name,pos,target,view,near) in enumerate(poses):
        when=15+45*i
        vector=lambda v:' '.join(f'{float(x):.9g}' for x in v)
        schedule.append(f'        if (m_BalticRenderPhase == {i-1} && m_BalticRenderTime >= {when})\n            BalticRenderPose({i}, "{vector(pos)}", "{vector(target)}", {view}, {near});')
        refs.append(dict(phase=i,name=name,start_s=when,settled_s=when+3,end_s=when+45,position=pos,target=target,view_requested=view,nearplane_requested=near or 'original'))
    finish=15+45*len(poses)
    schedule.append(f'''        if (m_BalticRenderPhase == 11 && m_BalticRenderTime >= {finish})
        {{
            BalticRenderRestore(); m_BalticRenderPhase=12; m_BalticRenderNextRecord=-1;
        }}
        if (m_BalticRenderPhase == 12 && m_BalticRenderTime >= {finish+3})
        {{
            BalticRenderRecord("COMPLETE_RESTORED_SETTLED", false);
            m_BalticRenderPhase=13; return;
        }}
''')
    code=code[:start]+'\n'.join(schedule)+'\n'+code[end:]
    code=code.replace('int phase, vector position, vector target)','int phase, vector position, vector target, float requestedView, float requestedNear)')
    code=code.replace('m_BalticRequestedViewDistance = 1600;\n        if (phase >= 1) m_BalticRequestedViewDistance = 6000;','m_BalticRequestedViewDistance = requestedView;')
    code=code.replace('if (phase >= 1) camera.SetNearPlane(10);','if (requestedNear > 0) camera.SetNearPlane(requestedNear);')
    code=code.replace('m_BalticRenderPhase = 4;','m_BalticRenderPhase = 13;')
    code=code.replace('GetGame().GetCurrentCameraPosition());','GetGame().GetCurrentCameraPosition().ToString());')
    code=code.replace('GetGame().GetCurrentCameraDirection());','GetGame().GetCurrentCameraDirection().ToString());')
    prefix='baltic_foundation_visual';stage=out/prefix
    (stage/'scripts/5_Mission').mkdir(parents=True);ev.mkdir(parents=True);mission.mkdir(parents=True)
    script=stage/'scripts/5_Mission/BalticRenderProbe.c';script.write_text(code)
    config=(base/'config.cpp').read_text().replace('baltic_render_probe',prefix)
    (out/'config.cpp').write_text(config);dest=out/'Addons';dest.mkdir()
    weather=(ROOT/'tools/navigation/regional_chase_init.c').read_text().split('class BalticRegionalChaseMission:')[0]
    clean=(ROOT/'missions/BalticNativeBasic.BalticTrial/init.c').read_text()
    body=clean[clean.index('class BalticNativeBasicMission:'):]
    body=body.replace('BalticNativeBasicMission','BalticFoundationVisualMission')
    body=body.replace('// Western dry landing, outside the 75m bridge; honor its prepared roadway.','// Western terrain approach of the 225m V10 bridge.')
    body=body.replace('2357.841309 0 6899.011230','2025 0 6950')
    (mission/'init.c').write_text(weather+body)
    tools=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
    for i,argv in enumerate([[tools/'CfgConvert/CfgConvert.exe','-bin','-dst',stage/'config.bin',out/'config.cpp'],
                            [tools/'PboUtils/FileBank.exe','-property','prefix='+prefix,'-property','product=dayz ugc','-dst',dest,stage]]):
        result=subprocess.run(list(map(str,argv)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/f'command-{i}.log').write_bytes(result.stdout)
        if result.returncode:raise RuntimeError('Probe packaging failed')
    pbo=dest/(prefix+'.pbo');_,props,entries=read_pbo(pbo)
    assert props['prefix']==prefix and entries=={p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()}
    ref=dict(status='PREPARED_NOT_RUN',parent_probe_sha256=sha(source),terrain_sha256=sha(terrain),probe_pbo_sha256=sha(pbo),
             mission_sha256=sha(mission/'init.c'),script_sha256=sha(script),poses=refs,finish_s=finish+3,
             restoration_view_distance=1600,limits=['Temporary diagnostic addon, not shipped map behavior.',
             'Original nearplane for ground and medium views; 10m only for named aerial diagnostics.',
             'Actual delayed camera/weather log and screenshots required. No automatic visual PASS.'])
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
    print(json.dumps({k:v for k,v in ref.items() if k!='poses'},indent=2))

if __name__=='__main__':main()
