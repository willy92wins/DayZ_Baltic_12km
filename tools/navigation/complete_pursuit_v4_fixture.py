"""Close client probe on replicated completion, independent of process shutdown."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ev=ROOT/'evidence/foundation-followup-2026-10-01/continuous-pursuit-v4';refpath=ev/'reference.json'
    ref=json.loads(refpath.read_text(encoding='utf-8'))
    for group in ['mission','probe_files']:
        for p,h in ref[group].items():assert sha(Path(p))==h,p
    out=ROOT/'packages/continuous-pursuit-v4';prefix='baltic_continuous_pursuit_v4';stage=out/prefix
    mission=ROOT/'missions/BalticContinuousPursuitV4.BalticTrial'
    deployed=Path(ref['deployed_mission']).with_name(mission.name);mod=Path('P:/Mods/@BalticContinuousPursuitV4')
    for p in [out,mission,deployed,mod]:assert not p.exists(),p
    out.mkdir();mission.mkdir();stage.mkdir()
    source=ROOT/'packages/continuous-pursuit-v3/baltic_continuous_pursuit_v3'
    for p in source.rglob('*.c'):
        dest=stage/p.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True)
        code=p.read_text(encoding='utf-8').replace('_v3','_v4').replace('_V3','_V4')
        if p.name=='BalticPursuitClient.c':
            code=code.replace('    protected bool m_BalticPursuitStopped;','    protected bool m_BalticPursuitStopped;\n    protected bool m_BalticPursuitSawLastCase;')
            anchor='        if (command < 0) return;';assert code.count(anchor)==1
            code=code.replace(anchor,anchor+'\n        if (command == 3) m_BalticPursuitSawLastCase = true;\n        if (command == 0 && m_BalticPursuitSawLastCase) { BalticPursuitRelease("PROBE_COMPLETE"); return; }')
        dest.write_text(code,encoding='utf-8')
    oldmission=ROOT/'missions/BalticContinuousPursuitV3.BalticTrial'
    (mission/'init.c').write_text((oldmission/'init.c').read_text(encoding='utf-8').replace('_v3','_v4').replace('_V3','_V4'),encoding='utf-8')
    shutil.copy2(oldmission/'cases.csv',mission/'cases.csv')
    config=(ROOT/'packages/continuous-pursuit-v3/config.cpp').read_text(encoding='utf-8').replace('_v3','_v4')
    (out/'config.cpp').write_text(config,encoding='utf-8');addons=out/'Addons';addons.mkdir()
    tool=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
    for i,cmd in enumerate([[tool/'CfgConvert/CfgConvert.exe','-bin','-dst',stage/'config.bin',out/'config.cpp'],[tool/'PboUtils/FileBank.exe','-property','prefix='+prefix,'-property','product=dayz ugc','-dst',addons,stage]]):
        result=subprocess.run(list(map(str,cmd)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/f'command-{i}.log').write_bytes(result.stdout);assert result.returncode==0
    pbo=addons/(prefix+'.pbo');_,props,entries=read_pbo(pbo)
    assert props['prefix']==prefix and entries=={p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()}
    (mod/'Addons').mkdir(parents=True);shutil.copy2(pbo,mod/'Addons'/pbo.name);shutil.copytree(mission,deployed)
    verifier=ROOT/'tools/navigation/verify_continuous_pursuit_v4.py'
    code=verifier.read_text(encoding='utf-8').replace('BALTIC_CONTINUOUS_PURSUIT_V3','BALTIC_CONTINUOUS_PURSUIT_V4').replace('BALTIC_CONTINUOUS_PURSUIT_CLIENT_V3','BALTIC_CONTINUOUS_PURSUIT_CLIENT_V4').replace("cells[1]!='MISSION_FINISH'","cells[1]!='PROBE_COMPLETE'").replace("clines[-1].startswith('END;MISSION_FINISH;')","clines[-1].startswith('END;PROBE_COMPLETE;')")
    verifier.write_text(code,encoding='utf-8')
    shutil.copy2(refpath,ev/'reference-before-probe-close.json')
    ref.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),preflight_revision='V4 producer: V3 input unchanged; client probe closes on observed command3->0. Cadence-aware consumer. Old V3 incomplete client end retained.',deployed_mod=str(mod),deployed_mission=str(deployed),probe_pbo_sha256=sha(pbo),mission={str(p):sha(p) for p in mission.iterdir()},probe_files={str(p):sha(p) for p in stage.rglob('*') if p.is_file()},consumer_sha256=sha(verifier))
    refpath.write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='PREPARED_NOT_RUN',probe_pbo_sha256=sha(pbo),reference_sha256=sha(refpath),entries=len(entries))))

if __name__=='__main__':main()
