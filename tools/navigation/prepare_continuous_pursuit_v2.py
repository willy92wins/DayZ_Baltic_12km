"""Additional full-roadway observation, preserving V1 strict-lane failure."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    old=ROOT/'evidence/overnight-2026-10-01/continuous-pursuit-v1/reference-r4.json'
    ref=json.loads(old.read_text())
    for group in ('mission','probe_files','api_sha256'):
        for name,digest in ref[group].items():assert sha(Path(name))==digest,(group,name)
    ev=ROOT/'evidence/overnight-2026-10-01/continuous-pursuit-v2'
    out=ROOT/'packages/continuous-pursuit-v2';prefix='baltic_continuous_pursuit_v2'
    mission=ROOT/'missions/BalticContinuousPursuitV2.BalticTrial'
    deployed=Path(ref['deployed_mission']).with_name(mission.name)
    mod=Path('P:/Mods/@BalticContinuousPursuitV2')
    for p in (ev,out,mission,deployed,mod):assert not p.exists(),p
    ev.mkdir();mission.mkdir();out.mkdir();stage=out/prefix
    source=ROOT/'packages/continuous-pursuit-v1/baltic_continuous_pursuit_v1'
    for p in source.rglob('*.c'):
        dest=stage/p.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(p.read_text().replace('_v1','_v2').replace('_V1','_V2'))
    oldmission=ROOT/'missions/BalticContinuousPursuitV1.BalticTrial'
    code=(oldmission/'init.c').read_text().replace('_v1','_v2').replace('_V1','_V2')
    needle='    override void OnUpdate(float timeslice)'
    addition='''    float PermittedLateral(vector pos)
    {
        if (m_Case == 0) return 4;
        float dx = pos[0] - 2417.1428225906;
        float dz = pos[2] - 6889.8850822322;
        float along = dx * 0.98836436083 + dz * (-0.15210486594);
        if (Math.AbsFloat(along) <= 112.5) return 6;
        return 4;
    }
'''
    assert code.count(needle)==1
    code=code.replace(needle,addition+needle)
    oldcheck='Math.AbsFloat(Lateral(m_Actor.GetPosition())) > 4 || Math.AbsFloat(Lateral(m_Prey.GetPosition())) > 4'
    newcheck='Math.AbsFloat(Lateral(m_Actor.GetPosition())) > PermittedLateral(m_Actor.GetPosition()) || Math.AbsFloat(Lateral(m_Prey.GetPosition())) > PermittedLateral(m_Prey.GetPosition())'
    assert code.count(oldcheck)==1;code=code.replace(oldcheck,newcheck)
    (mission/'init.c').write_text(code);shutil.copy2(oldmission/'cases.csv',mission/'cases.csv')
    config=(ROOT/'packages/continuous-pursuit-v1/config.cpp').read_text().replace('_v1','_v2')
    (out/'config.cpp').write_text(config);addons=out/'Addons';addons.mkdir()
    tool=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
    commands=[[tool/'CfgConvert/CfgConvert.exe','-bin','-dst',stage/'config.bin',out/'config.cpp'],
              [tool/'PboUtils/FileBank.exe','-property','prefix='+prefix,'-property','product=dayz ugc','-dst',addons,stage]]
    for i,cmd in enumerate(commands):
        p=subprocess.run(list(map(str,cmd)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/f'command-{i}.log').write_bytes(p.stdout);assert p.returncode==0
    pbo=addons/(prefix+'.pbo');_,props,entries=read_pbo(pbo)
    expected={p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()}
    assert props['prefix']==prefix and entries==expected and len(entries)==3
    (mod/'Addons').mkdir(parents=True);shutil.copy2(pbo,mod/'Addons'/pbo.name);shutil.copytree(mission,deployed)
    assert sha(pbo)==sha(mod/'Addons'/pbo.name)
    for p in mission.iterdir():assert sha(p)==sha(deployed/p.name)
    ref['previous_reference_sha256']=sha(old);ref['preflight_revision']='V2 additional physical roadway consumer; V1 strict lane remains FAIL.'
    ref['bridge']['max_lateral_m']=6
    ref['criteria']['maximum_bridge_lateral_m']=6
    ref['strict_lane_criterion_m']=4
    ref['probe_pbo_sha256']=sha(pbo);ref['deployed_mod']=str(mod);ref['deployed_mission']=str(deployed)
    ref['mission']={str(p):sha(p) for p in mission.iterdir()}
    ref['probe_files']={str(p):sha(p) for p in stage.rglob('*') if p.is_file()}
    ref['roadway_source_sha256']=sha(ROOT/'evidence/narva/evidence/bridge-roadway.json')
    ref['limits'].append('Main deck +-6 m, approaches +-4 m; strict historical lane reported separately. No prior FAIL promotion.')
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
    (out/'verification.json').write_text(json.dumps(dict(status='PASS_SCRIPT_PBO_BYTE_PARITY',probe_pbo_sha256=sha(pbo),entries={k:hashlib.sha256(v).hexdigest() for k,v in entries.items()},engine='NOT_RUN'),indent=2)+'\n')
    print(json.dumps(dict(reference_sha256=sha(ev/'reference.json'),probe_pbo_sha256=sha(pbo))))

if __name__=='__main__':main()
