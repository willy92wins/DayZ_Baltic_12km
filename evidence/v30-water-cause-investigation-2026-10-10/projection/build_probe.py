from pathlib import Path
import hashlib,json,subprocess,sys,shutil,re
B=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
name='baltic_water_projection_v2'
src=B/'probe'/name; scripts=src/'scripts/5_Mission';scripts.mkdir(parents=True,exist_ok=True)
points=[(x,2,z) for z in [6810,6888,6948,7020] for x in [2352,2394,2436,2478]]
old=(B/'BalticProjectionProbe.c').read_text()
points_code='\n'.join(f'  m_BalticProjectionPoints.Insert("{x} {y} {z}");' for x,y,z in points)
start=old.index('  m_BalticProjectionPoints.Insert(');end=old.index('\n }',start)
new=old[:start]+points_code+old[end:]
new=new.replace('BalticProjection','BalticWaterProjectionV2').replace('baltic_projection_probe_v1.log','baltic_water_projection_v2.log').replace('BALTIC_PROJECTION_PROBE_V1;EV43','BALTIC_WATER_PROJECTION_V2;EV76')
assert new.count('.Insert(')==16
(scripts/'BalticWaterProjectionV2.c').write_text(new,encoding='utf-8')
cfg=(W/'evidence/v30-global-water-risk-2026-10-09/projection-probe-source/config.cpp').read_text().replace('BalticProjectionProbe','BalticWaterProjectionV2').replace('baltic_projection_probe',name)
(src/'config.cpp').write_text(cfg,encoding='utf-8')
tools=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
run=subprocess.run([str(tools/'CfgConvert/CfgConvert.exe'),'-bin','-dst',str(src/'config.bin'),str(src/'config.cpp')],capture_output=True)
assert run.returncode==0,run.stderr
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(src)],capture_output=True,text=True)
(B/'lint.json').write_text(lint.stdout)
check=json.loads(lint.stdout);assert lint.returncode==0 and not check['errors'] and check['info']['files_scanned']==2,check
packed=B/'probe/packed';packed.mkdir(exist_ok=True)
run=subprocess.run([str(tools/'PboUtils/FileBank.exe'),'-property',f'prefix={name}','-dst',str(packed),str(src)],capture_output=True)
(B/'filebank.log').write_bytes(run.stdout+run.stderr);assert run.returncode==0
dest=Path('P:/Mods/@BalticWaterProjectionV2/Addons');dest.mkdir(parents=True,exist_ok=False)
p=packed/(name+'.pbo');shutil.copyfile(p,dest/p.name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(p)==sha(dest/p.name)
sys.path.insert(0,str(W/'tools/playtest'));from attach_navmesh import read_pbo
_,_,entries=read_pbo(dest/p.name)
assert entries['scripts/5_Mission/BalticWaterProjectionV2.c']==(scripts/'BalticWaterProjectionV2.c').read_bytes()
report=dict(status='READ_ONLY_PROJECTION_PROBE_PACKED',pbo=str(dest/p.name),sha256=sha(p),points=points,source_sha256=sha(scripts/'BalticWaterProjectionV2.c'),purpose='Native projection of existing EV72 bridge scene. No world/material/options writes.',profile_sha256=sha(Path('P:/DayZ_MCP_dev/_client/profiles/Users/Dev/guill_settings.DayZProfile')))
(B/'probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
