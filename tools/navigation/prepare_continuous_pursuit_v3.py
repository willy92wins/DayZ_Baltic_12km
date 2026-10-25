"""Heading-sign discriminator; immutable V2 geometry and physical limits."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def change(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new,1)

def main():
    parent=ROOT/'evidence/overnight-2026-10-01/continuous-pursuit-v2/reference.json'
    ref=json.loads(parent.read_text(encoding='utf-8'))
    for group in ('mission','probe_files','api_sha256'):
        for p,d in ref[group].items():assert sha(Path(p))==d,(group,p)
    ev=ROOT/'evidence/foundation-followup-2026-10-01/continuous-pursuit-v3'
    out=ROOT/'packages/continuous-pursuit-v3';prefix='baltic_continuous_pursuit_v3'
    mission=ROOT/'missions/BalticContinuousPursuitV3.BalticTrial'
    deployed=Path(ref['deployed_mission']).with_name(mission.name)
    mod=Path('P:/Mods/@BalticContinuousPursuitV3')
    for p in (ev,out,mission,deployed,mod):assert not p.exists(),p
    ev.mkdir(parents=True);mission.mkdir();out.mkdir();stage=out/prefix
    src=ROOT/'packages/continuous-pursuit-v2/baltic_continuous_pursuit_v2'
    for p in src.rglob('*.c'):
        target=stage/p.relative_to(src);target.parent.mkdir(parents=True,exist_ok=True)
        text=p.read_text(encoding='utf-8').replace('_v2','_v3').replace('_V2','_V3')
        if p.name=='BalticPursuitClient.c':
            text=change(text,'Math.Atan2(dx, dz) - control.GetHeadingAngle()', 'Math.Atan2(dx, dz) + control.GetHeadingAngle()')
            text=change(text,'protected FileHandle m_BalticPursuitLog;', 'protected FileHandle m_BalticPursuitLog;\n    protected FileHandle m_BalticHeadingLog;')
            text=change(text,'m_BalticPursuitLog = OpenFile(', 'm_BalticHeadingLog = OpenFile("$profile:baltic_heading_client_v3.log", FileMode.WRITE);\n        m_BalticPursuitLog = OpenFile(')
            text=change(text,'m_BalticPursuitStopped = true;', 'if (m_BalticHeadingLog) { CloseFile(m_BalticHeadingLog); m_BalticHeadingLog = null; }\n        m_BalticPursuitStopped = true;')
            needle='            control.GetMovement(actualSpeed, localDirection);'
            addition='''
            vector bodyOrientation = m_BalticPursuitPlayer.GetOrientation();
            if (m_BalticHeadingLog) FPrintln(m_BalticHeadingLog, "D;" + m_BalticPursuitTime + ";" + GetGame().GetTime() + ";" + command + ";" + pos.ToString() + ";" + control.GetHeadingAngle() + ";" + bodyOrientation.ToString() + ";" + m_BalticPursuitPlayer.GetCurrentCommandID() + ";" + m_BalticPursuitPlayer.IsFighting() + ";" + actualSpeed + ";" + localDirection.ToString() + ";" + angle);'''
            text=change(text,needle,needle+addition)
        target.write_text(text,encoding='utf-8')
    oldmission=ROOT/'missions/BalticContinuousPursuitV2.BalticTrial'
    code=(oldmission/'init.c').read_text(encoding='utf-8').replace('_v2','_v3').replace('_V2','_V3')
    code=change(code,'Math.Atan2(dx, dz) - control.GetHeadingAngle()', 'Math.Atan2(dx, dz) + control.GetHeadingAngle()')
    code=change(code,'protected FileHandle m_Log;', 'protected FileHandle m_Log;\n    protected FileHandle m_HeadingLog;')
    code=change(code,'m_Log = OpenFile(', 'm_HeadingLog = OpenFile("$profile:baltic_heading_server_v3.log", FileMode.WRITE);\n        m_Log = OpenFile(')
    needle='            command = m_Prey.BalticPursuitCommand(); unconscious = m_Prey.IsUnconscious();'
    addition='''
            HumanInputController humanInput = m_Prey.GetInputController();
            float actualSpeed; vector localDirection;
            vector bodyOrientation = m_Prey.GetOrientation();
            if (humanInput)
            {
                humanInput.GetMovement(actualSpeed, localDirection);
                if (m_HeadingLog) FPrintln(m_HeadingLog, "D;" + m_Time + ";" + GetGame().GetTime() + ";" + command + ";" + prey.ToString() + ";" + humanInput.GetHeadingAngle() + ";" + bodyOrientation.ToString() + ";" + m_Prey.GetCurrentCommandID() + ";" + m_Prey.IsFighting() + ";" + actualSpeed + ";" + localDirection.ToString() + ";" + marker);
            }'''
    code=change(code,needle,needle+addition)
    needle='        CleanActor();\n        if (m_Log)'
    code=change(code,needle,'        CleanActor();\n        if (m_HeadingLog) { CloseFile(m_HeadingLog); m_HeadingLog = null; }\n        if (m_Log)')
    (mission/'init.c').write_text(code,encoding='utf-8');shutil.copy2(oldmission/'cases.csv',mission/'cases.csv')
    config=(ROOT/'packages/continuous-pursuit-v2/config.cpp').read_text(encoding='utf-8').replace('_v2','_v3')
    (out/'config.cpp').write_text(config,encoding='utf-8');addons=out/'Addons';addons.mkdir()
    validator=Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py')
    for label,path in [('mission',mission),('probe',stage)]:
        checked=subprocess.run([sys.executable,'-X','utf8',str(validator),str(path)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (ev/('lint-'+label+'.json')).write_bytes(checked.stdout)
        assert checked.returncode==0,checked.stdout.decode(errors='replace')
    tool=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
    commands=[[tool/'CfgConvert/CfgConvert.exe','-bin','-dst',stage/'config.bin',out/'config.cpp'],
        [tool/'PboUtils/FileBank.exe','-property','prefix='+prefix,'-property','product=dayz ugc','-dst',addons,stage]]
    for i,cmd in enumerate(commands):
        p=subprocess.run(list(map(str,cmd)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/f'command-{i}.log').write_bytes(p.stdout);assert p.returncode==0
    pbo=addons/(prefix+'.pbo');_,properties,entries=read_pbo(pbo)
    expected={p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()}
    assert properties['prefix']==prefix and entries==expected and len(entries)==3
    (mod/'Addons').mkdir(parents=True);shutil.copy2(pbo,mod/'Addons'/pbo.name);shutil.copytree(mission,deployed)
    assert sha(pbo)==sha(mod/'Addons'/pbo.name)
    for p in mission.iterdir():assert sha(p)==sha(deployed/p.name)
    ref.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),previous_reference_sha256=sha(parent),
        preflight_revision='V3 heading addition instead of subtraction on both peers; extra native heading/command logs. Original V2 limits unchanged.',
        probe_pbo_sha256=sha(pbo),deployed_mod=str(mod),deployed_mission=str(deployed),
        mission={str(p):sha(p) for p in mission.iterdir()},probe_files={str(p):sha(p) for p in stage.rglob('*') if p.is_file()},
        heading_analysis_sha256=sha(ROOT/'evidence/foundation-followup-2026-10-01/pursuit-heading-analysis.json'))
    ref['api_sha256'][str(Path('P:/scripts/3_game/entities/object.c'))]=sha(Path('P:/scripts/3_game/entities/object.c'))
    ref['limits'].append('Heading sign hypothesis needs nonzero native heading evidence; no engine-root-cause claim based only on trajectory completion.')
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
    (out/'verification.json').write_text(json.dumps(dict(status='PASS_SCRIPT_PBO_BYTE_PARITY',probe_pbo_sha256=sha(pbo),entries={k:hashlib.sha256(v).hexdigest() for k,v in entries.items()},engine='NOT_RUN'),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='PREPARED_NOT_RUN',reference_sha256=sha(ev/'reference.json'),probe_pbo_sha256=sha(pbo))))

if __name__=='__main__':main()
