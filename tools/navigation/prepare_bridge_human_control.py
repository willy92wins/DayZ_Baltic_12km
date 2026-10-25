"""Freeze a no-infected counterpart to the failed continuous pursuit controller."""
from pathlib import Path
import json,hashlib,subprocess,shutil,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    old=ROOT/'evidence/overnight-2026-10-01/continuous-pursuit-v2/reference.json'
    ref=json.loads(old.read_text(encoding='utf-8'))
    for group in ('mission','probe_files','api_sha256'):
        for name,digest in ref[group].items():assert sha(Path(name))==digest,name
    name='bridge-human-control-v1';prefix='baltic_bridge_human_control_v1'
    ev=ROOT/'evidence/overnight-2026-10-01'/name;out=ROOT/'packages'/name
    mission=ROOT/'missions/BalticContinuousPursuitHumanControlV1.BalticTrial'
    deployed=Path(ref['deployed_mission']).with_name(mission.name)
    mod=Path('P:/Mods/@BalticContinuousPursuitHumanControlV1')
    for p in (ev,out,mission,deployed,mod):assert not p.exists(),p
    ev.mkdir();out.mkdir();mission.mkdir();stage=out/prefix
    source=ROOT/'packages/continuous-pursuit-v2/baltic_continuous_pursuit_v2'
    for p in source.rglob('*.c'):
        dest=stage/p.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True)
        s=p.read_text(encoding='utf-8').replace('baltic_continuous_pursuit_client_v2','baltic_bridge_human_control_client_v1').replace('BALTIC_CONTINUOUS_PURSUIT_CLIENT_V2','BALTIC_BRIDGE_HUMAN_CONTROL_CLIENT_V1').replace('> 1250','> 750')
        dest.write_text(s,encoding='utf-8')
    oldmission=ROOT/'missions/BalticContinuousPursuitV2.BalticTrial'
    s=(oldmission/'init.c').read_text(encoding='utf-8').replace('baltic_continuous_pursuit_v2','baltic_bridge_human_control_v1').replace('BALTIC_CONTINUOUS_PURSUIT_V2','BALTIC_BRIDGE_HUMAN_CONTROL_V1')
    s=s.replace('m_Starts.Count() != 3','m_Starts.Count() != 2').replace('m_Case >= 3','m_Case >= 2').replace('m_Time > 1200','m_Time > 700')
    a=s.index('            m_Actor = DayZInfected.Cast(');b=s.index('        float limit = 500;',a)
    s=s[:a]+'''            m_Stage = m_Time; m_Phase = 3;
            m_Prey.BalticSetPursuitCommand(m_Case + 1);
            Record("MOVE_BEGIN"); return;
        }
        if (Math.AbsFloat(Lateral(m_Prey.GetPosition())) > PermittedLateral(m_Prey.GetPosition())) { Fail("CORRIDOR"); return; }
'''+s[b:]
    s=s.replace(' && vector.Distance(m_Actor.GetPosition(), m_Goals[m_Case]) <= 4','')
    assert 'CreateObjectEx(' not in s and 'AddNoisePos(' not in s
    (mission/'init.c').write_text(s,encoding='utf-8')
    (mission/'cases.csv').write_text('\n'.join((oldmission/'cases.csv').read_text().splitlines()[:2])+'\n')
    config=(ROOT/'packages/continuous-pursuit-v2/config.cpp').read_text().replace('baltic_continuous_pursuit_v2',prefix)
    (out/'config.cpp').write_text(config);addons=out/'Addons';addons.mkdir()
    tool=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
    commands=[[tool/'CfgConvert/CfgConvert.exe','-bin','-dst',stage/'config.bin',out/'config.cpp'],[tool/'PboUtils/FileBank.exe','-property','prefix='+prefix,'-property','product=dayz ugc','-dst',addons,stage]]
    for i,cmd in enumerate(commands):
        p=subprocess.run(list(map(str,cmd)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/f'command-{i}.log').write_bytes(p.stdout);assert p.returncode==0
    pbo=addons/(prefix+'.pbo');_,props,entries=read_pbo(pbo)
    expected={p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()}
    assert props['prefix']==prefix and entries==expected and len(entries)==3
    (mod/'Addons').mkdir(parents=True);shutil.copy2(pbo,mod/'Addons'/pbo.name);shutil.copytree(mission,deployed)
    assert sha(pbo)==sha(mod/'Addons'/pbo.name)
    for p in mission.iterdir():assert sha(p)==sha(deployed/p.name)
    ref['previous_reference_sha256']=sha(old);ref['status']='FROZEN_NO_INFECTED_HUMAN_CONTROL_PENDING'
    ref['cases']=ref['cases'][:2];ref['criteria']['session_timeout_s']=700
    ref['probe_pbo_sha256']=sha(pbo);ref['deployed_mod']=str(mod);ref['deployed_mission']=str(deployed)
    ref['mission']={str(p):sha(p) for p in mission.iterdir()};ref['probe_files']={str(p):sha(p) for p in stage.rglob('*') if p.is_file()}
    ref['input_contract']='Same V2 human inputs, no infected creation or noise. Two cases: local and bridge east.'
    ref['preflight_revision']='No-infected discriminator; previous pursuit FAILs unchanged.'
    ref['limits']=['Human controller only; not AI or navmesh acceptance.','No randomization or causal isolation of native collision/control internals.','Original pursuit V1/V2 FAILs remain.']
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
    (out/'verification.json').write_text(json.dumps(dict(status='PASS_SCRIPT_PBO_BYTE_PARITY',probe_pbo_sha256=sha(pbo),engine='NOT_RUN'),indent=2)+'\n')
    print(json.dumps(dict(reference_sha256=sha(ev/'reference.json'),probe_pbo_sha256=sha(pbo))))

if __name__=='__main__':main()
