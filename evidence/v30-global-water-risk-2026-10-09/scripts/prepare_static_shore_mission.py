from pathlib import Path
import shutil,json,subprocess,sys,hashlib
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-global-water-risk-2026-10-09'
name='BalticShoreDiagnosticV1.BalticTrial';out=B/'missions'/name;out.mkdir(parents=True,exist_ok=False)
code=(B/'missions/BalticScalarTemporalV2.BalticTrial/init.c').read_text().split('class BalticV30WaterTemporalV3Mission')[0]
code+='\nclass BalticShoreDiagnosticMission: MissionServer {}\nMission CreateCustomMission(string path) { return new BalticShoreDiagnosticMission(); }\n'
(out/'init.c').write_text(code)
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(out)],capture_output=True,text=True)
r=json.loads(lint.stdout);assert lint.returncode==0 and not r['errors'] and r['info']['files_scanned']==1
dest=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/name;shutil.copytree(out,dest)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(dest/'init.c')==sha(out/'init.c')
(E/'shore-mission-reference.json').write_text(json.dumps(dict(mission=str(dest),sha256=sha(out/'init.c'),weather='Constant calm, copied from the validated probe main()',source='P:/scripts/5_mission/mission/missionserver.c'),indent=2)+'\n')
print(str(dest))
