from pathlib import Path
import hashlib,json,subprocess,shutil,sys
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009');E=W/'evidence/v30-global-water-risk-2026-10-09'
src=B/'terrain-detail-probe/baltic_terrain_detail';out=B/'terrain-detail-probe/packed';out.mkdir(exist_ok=False)
cv=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe')
run=subprocess.run([str(cv),'-bin','-dst',str(src/'config.bin'),str(src/'config.cpp')],capture_output=True);assert run.returncode==0,run.stderr
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(src)],capture_output=True,text=True)
got=json.loads(lint.stdout);assert lint.returncode==0 and not got['errors'] and got['info']['files_scanned']==2,lint.stdout
(E/'terrain-detail-lint.json').write_text(lint.stdout)
bank=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe')
run=subprocess.run([str(bank),'-property','prefix=baltic_terrain_detail','-dst',str(out),str(src)],capture_output=True);assert run.returncode==0
(B/'terrain-detail-probe/filebank.log').write_bytes(run.stdout+run.stderr)
dest=Path('P:/Mods/@BalticTerrainDetailDiagnostic/Addons');dest.mkdir(parents=True,exist_ok=False)
p=out/'baltic_terrain_detail.pbo';shutil.copyfile(p,dest/p.name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(p)==sha(dest/p.name)
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
_,_,a=read_pbo(dest/p.name)
assert a['scripts/5_Mission/BalticTerrainDetail.c']==(src/'scripts/5_Mission/BalticTerrainDetail.c').read_bytes()
shutil.copytree(src,E/'terrain-detail-probe-source')
ref=dict(pbo=str(dest/p.name),sha256=sha(p),source_sha256=sha(src/'scripts/5_Mission/BalticTerrainDetail.c'),
    source_api=['P:/scripts/3_game/gameplay.c:1320-1512','P:/scripts/5_mission/gui/newui/options/optionsmenuvideo.c:496', 'P:/scripts/5_mission/mission/missiongameplay.c:257'],
    limits=['One original-alternative-original sequence, only terrain detail.','Test only, no Apply/profile save; restore original before orderly close.'])
(E/'terrain-detail-reference.json').write_text(json.dumps(ref,indent=2)+'\n')
print(json.dumps(ref,indent=2))
