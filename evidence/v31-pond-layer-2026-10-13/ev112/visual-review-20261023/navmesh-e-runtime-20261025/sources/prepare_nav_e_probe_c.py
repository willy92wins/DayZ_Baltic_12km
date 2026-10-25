from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
source=W/'missions/BalticV30ContinuityNavV1.BalticTrial/init.c'
mission=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticGuardedENavV9C.BalticTrial');mission.mkdir(exist_ok=False)
out=R/'navmesh-guarded-e-v9-probe-c';out.mkdir(exist_ok=False)
s=source.read_text(encoding='utf-8');assert s.count('baltic_v30_continuity_nav_v1.log')==1 and s.count('BALTIC_V30_CONTINUITY_NAV_V1')==1
s=s.replace('baltic_v30_continuity_nav_v1.log','baltic_ev112_nav_v9_c.log').replace('BALTIC_V30_CONTINUITY_NAV_V1','BALTIC_EV112_NAV_V9')
(mission/'init.c').write_bytes(s.encode())
shutil.copyfile('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticGuardedENavV9.BalticTrial/queries.csv',mission/'queries.csv')
shutil.copyfile(R/'navmesh-guarded-e-v9-probe/reference.json',out/'reference.json')
original=json.loads((R/'navmesh-guarded-e-v9-probe/deployment.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p,digest in original['deployed'].items():assert sha(Path(p))==digest
inputs={str(p):sha(p) for p in (source,mission/'init.c',mission/'queries.csv',out/'reference.json',Path(__file__))};inputs.update(original['deployed'])
launch=json.loads((R/'navmesh-guarded-e-v9-probe/launch-server.json').read_text());launch['mission']=str(mission)
(out/'launch-server.json').write_text(json.dumps(launch,indent=2)+'\n',encoding='utf-8')
(out/'deployment.json').write_text(json.dumps(dict(status='FINAL_SOURCE_PROBE_PREPARED_NOT_RUN',inputs=inputs,deployed=original['deployed'],mission=str(mission)),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(mission=str(mission),source_sha256=sha(source),mission_sha256=sha(mission/'init.c')),indent=2))
