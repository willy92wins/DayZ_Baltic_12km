from pathlib import Path
import hashlib,json,uuid
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
out=R/'server-baseline-ab-v2';out.mkdir(exist_ok=False)
root=Path('C:/temp/DayZ_MCP_130_dev/mpmissions')
source=W/'missions/BalticTerrainPerf.BalticTrial/init.c';raw=source.read_bytes();text=raw.decode('utf-8').replace('\r\n','\n')
assert text.count('"baltictrial"')==1 and text.count('baltic_terrain_perf_v1.log')==2
rows=[]
for index,world in enumerate(('BalticTrial','ChernarusPlus','ChernarusPlus','BalticTrial','BalticTrial','ChernarusPlus'),1):
    token=uuid.uuid4().hex[:12];log=f'baltic_ab_{index:02d}_{token}.log'
    mission=root/f'BalticAB{index:02d}_{token}.{world}';mission.mkdir(exist_ok=False)
    code=text.replace('"baltictrial"','"'+world.lower()+'"').replace('baltic_terrain_perf_v1.log',log)
    assert code.replace('"'+world.lower()+'"','"baltictrial"').replace(log,'baltic_terrain_perf_v1.log')==text
    target=mission/'init.c';target.write_bytes(code.encode('utf-8'))
    rows.append(dict(order=index,world=world,mission=str(mission),mission_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),profile_log=log,canonical_source_parity=True))
manifest=dict(status='PREPARED_NOT_EXECUTED',source=str(source),source_sha256=hashlib.sha256(raw).hexdigest(),order='A-B-B-A-A-B',passes=rows,limits=['Requires own E navmesh v9 verified, quiet host, current binary/mod/config identities before launching.','No client, CE, AI or player-capacity acceptance.'])
(out/'missions.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
(out/'mission-template.c').write_bytes(raw)
print(json.dumps(manifest,indent=2))
