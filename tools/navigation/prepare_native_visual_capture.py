"""Clone frozen local camera groups with native capture and focus evidence."""
from pathlib import Path
import argparse,copy,hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--group',choices=['neva','reserve','south'],required=True);a=ap.parse_args();group=a.group
    old=f'visual_g_{group}_v1';stem=f'visual_native_{group}_v2';prefix='baltic_foundation_'+stem
    source_ref=ROOT/f'evidence/overnight-2026-10-01/foundation-{old}/reference.json';ref=json.loads(source_ref.read_text(encoding='utf-8'))
    oldpkg=ROOT/f'packages/foundation-{old}';source=oldpkg/f'baltic_foundation_{old}/scripts/5_Mission/BalticRenderProbe.c'
    assert sha(source)==ref['script_sha256']
    package=ROOT/f'packages/foundation-{stem}';ev=ROOT/f'evidence/foundation-followup-2026-10-01/foundation-{stem}'
    mission=ROOT/f'missions/BalticFoundationVisualNative{group.title()}V2.BalticTrial'
    deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
    mod=Path('P:/Mods')/f'@BalticFoundationVisualNative{group.title()}V2'
    assert not any(p.exists() for p in [package,ev,mission,deployed,mod])
    code=source.read_text(encoding='utf-8').replace(old,stem).replace(old.upper(),stem.upper()).replace(f'client_metrics_g_{group}_v1',f'client_metrics_native_{group}_v2').replace(f'METRICS_G_{group.upper()}_V1',f'METRICS_NATIVE_{group.upper()}_V2')
    before='    protected int m_BalticCapturePhase = -1;';assert code.count(before)==1
    code=code.replace(before,before+'\n    protected bool m_BalticNativeCaptureActive;')
    before='            // No native screenshot request: visual evidence is observed through Computer Use.';assert code.count(before)==1
    code=code.replace(before,'            m_BalticNativeCaptureActive = GetGame().IsAppActive();\n            if (m_BalticNativeCaptureActive) MakeScreenshot(name);')
    code=code.replace('OBSERVATION_READY_','CAPTURE_REQUEST_')
    before='        FPrintln(report, "world=" + GetGame().GetWorldName());';assert code.count(before)==1
    code=code.replace(before,before+'\n        FPrintln(report, "application_active=" + GetGame().IsAppActive());\n        FPrintln(report, "native_capture_requested=" + m_BalticNativeCaptureActive);')
    stage=package/prefix;(stage/'scripts/5_Mission').mkdir(parents=True);ev.mkdir(parents=True);mission.mkdir(parents=True)
    script=stage/'scripts/5_Mission/BalticRenderProbe.c';script.write_text(code,encoding='utf-8')
    config=(oldpkg/'config.cpp').read_text(encoding='utf-8').replace('baltic_foundation_'+old,prefix);(package/'config.cpp').write_text(config,encoding='utf-8')
    original_mission=ROOT/'missions'/Path(ref['deployed_mission']).name/'init.c';assert sha(original_mission)==ref['mission_sha256'];shutil.copy2(original_mission,mission/'init.c')
    lint=subprocess.run([sys.executable,'-X','utf8','C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(stage)],capture_output=True,text=True)
    (ev/'lint.json').write_text(lint.stdout,encoding='utf-8');receipt=json.loads(lint.stdout);assert lint.returncode==0 and receipt['status']=='PASS' and receipt['info']['files_scanned']==1
    addons=package/'Addons';addons.mkdir();tool=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
    for i,args in enumerate([[tool/'CfgConvert/CfgConvert.exe','-bin','-dst',stage/'config.bin',package/'config.cpp'],[tool/'PboUtils/FileBank.exe','-property','prefix='+prefix,'-property','product=dayz ugc','-dst',addons,stage]]):
        result=subprocess.run(list(map(str,args)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(package/f'command-{i}.log').write_bytes(result.stdout);assert result.returncode==0
    pbo=addons/(prefix+'.pbo');_,properties,entries=read_pbo(pbo);assert properties['prefix']==prefix and entries=={p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()}
    (mod/'Addons').mkdir(parents=True);shutil.copy2(pbo,mod/'Addons'/pbo.name);shutil.copytree(mission,deployed)
    assert sha(mod/'Addons'/pbo.name)==sha(pbo) and sha(deployed/'init.c')==sha(mission/'init.c')
    ref.update(status='FROZEN_NATIVE_VISUAL_RUNTIME_PENDING',parent_reference_sha256=sha(source_ref),script_sha256=sha(script),mission_sha256=sha(mission/'init.c'),probe_pbo_sha256=sha(pbo),deployed_mod=str(mod),deployed_mission=str(deployed),camera_header='BALTIC_FOUNDATION_'+stem.upper(),metrics_header=f'BALTIC_FOUNDATION_CLIENT_METRICS_NATIVE_{group.upper()}_V2',camera_log=prefix+'.log',metrics_log=f'baltic_foundation_client_metrics_native_{group}_v2.log',capture_event='CAPTURE_REQUEST',capture_api='MakeScreenshot; focused-app guard, original DDS requires independent pixel review',capture_prefix=prefix+'_',capture_change='Frozen local V1 poses and timing; native DDS replaces manually timed capture only.',limits=['Native requested capture and telemetry do not accept pixels.','Previous distant-transition crash remains outside this local-camera test.','Unchanged V10 map; no multiplayer capacity claim.'])
    ref['capture_name_mode']='Native DDS in profile ScreenShotes, dated filename with capture_prefix and phase'
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(group=group,status=ref['status'],reference=str(ev/'reference.json'),probe_sha256=sha(pbo))))

if __name__=='__main__':main()
