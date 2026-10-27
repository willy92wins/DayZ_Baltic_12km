"""Prepare fresh missions and isolated RAM runners; do not launch or reuse samples."""
from pathlib import Path
import hashlib,json,uuid,ast,subprocess,sys
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'kit7-nav12-ram-ab-20261027';D.mkdir(exist_ok=False)
source=W/'missions/BalticTerrainPerf.BalticTrial/init.c'
raw=source.read_bytes();text=raw.decode('utf-8').replace('\r\n','\n')
assert text.count('"baltictrial"')==1 and text.count('baltic_terrain_perf_v1.log')==2
rows=[]
for index,world in enumerate(('BalticTrial','ChernarusPlus','ChernarusPlus','BalticTrial','BalticTrial','ChernarusPlus'),1):
    suffix=uuid.uuid4().hex[:12];log=f'baltic_ab_{index:02d}_{suffix}.log'
    mission=Path('C:/temp/DayZ_MCP_130_dev/mpmissions')/f'BalticNav12AB{index:02d}_{suffix}.{world}'
    mission.mkdir(exist_ok=False)
    code=text.replace('"baltictrial"','"'+world.lower()+'"').replace('baltic_terrain_perf_v1.log',log)
    assert code.replace('"'+world.lower()+'"','"baltictrial"').replace(log,'baltic_terrain_perf_v1.log')==text
    target=mission/'init.c';target.write_bytes(code.encode('utf-8'))
    rows.append(dict(order=index,world=world,mission=str(mission),mission_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),profile_log=log,canonical_source_parity=True))
manifest=dict(status='PREPARED_NOT_EXECUTED',source=str(source),source_sha256=hashlib.sha256(raw).hexdigest(),order='A-B-B-A-A-B',passes=rows,limits=['Requires own kit7 Nav12 native607 PASS before each launch; no borrowed measurements.','RAM budget 1.10 and dispersion 5 percent unchanged; no client/FPS/capacity acceptance.'])
(D/'missions.json').write_text(json.dumps(manifest,indent=2)+'\n')
(D/'mission-template.c').write_bytes(raw)
for name in ('prepare_nav8_ram_pass.py','finish_nav8_ram_pass.py','finalize_nav8_ram_ab.py','orchestrate_nav8_ram.js','test_nav8_ram_conditions.py'):
    old=(R/name).read_text();s=old.replace('nav8','nav12').replace('Nav8','Nav12').replace('NAV8','NAV12')
    if name=='orchestrate_nav8_ram.js':
        a='if(token)parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));q='
        b="catch(e){await event('HEARTBEAT_ERROR');const s=parse("
        assert s.count(a)==s.count(b)==1
        s=s.replace(a,'if(token)await beat();q=').replace(b,'catch(e){const s=parse(')
    target=R/name.replace('nav8','nav12');assert not target.exists()
    if target.suffix=='.py':ast.parse(s)
    target.write_text(s)
flow=(R/'test_kit7_nav12_probe_flow.cjs').read_text()
for old,new in [('orchestrate_kit7_nav12_probe.js','orchestrate_nav12_ram.js'),('probeKit7Nav12()','benchKit7Nav12(1)'),('Fresh log required','prepare_nav12_ram_pass.py'),('capture_kit7_nav_log.ps1','capture_server_baseline_ev112.ps1'),('finish_kit7_nav12_probe.py','finish_nav12_ram_pass.py'),('kit7-nav12-consumer-20261027','kit7-nav12-ram-ab-20261027'),('PASS_KIT7_PROBE_CONTROL_FLOW','PASS_NAV12_RAM_CONTROL_FLOW'),('native607 remains separate','native RAM acceptance remains separate')]:flow=flow.replace(old,new)
fixture={'order':'A-B-B-A-A-B','passes':[rows[0]]}
assert flow.count("()=>'(x)=>x'")==1
flow=flow.replace("()=>'(x)=>x'","key=>key==='nav12RamConfig'?"+json.dumps(fixture)+":'(x)=>x'")
(R/'test_nav12_ram_flow.cjs').write_text(flow)
commands=(R/'test_kit7_nav12_probe_command.cjs').read_text().replace('orchestrate_kit7_nav12_probe.js','orchestrate_nav12_ram.js').replace('kit7-nav12-consumer-20261027','kit7-nav12-ram-ab-20261027')
(R/'test_nav12_ram_command.cjs').write_text(commands)
validator=Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py')
checks=[]
for row in rows:
    mission=Path(row['mission'])
    bootstrap='import runpy,sys;sys.path.insert(0,'+repr(str(validator.parent))+');sys.argv='+repr([str(validator),str(mission),'--vanilla-root','P:/scripts'])+';runpy.run_path('+repr(str(validator))+',run_name="__main__")'
    p=subprocess.run([sys.executable,'-I','-c',bootstrap],capture_output=True)
    (D/f'script-validator-{row["order"]:02}.json').write_bytes(p.stdout)
    (D/f'script-validator-{row["order"]:02}.stderr.log').write_bytes(p.stderr)
    result=json.loads(p.stdout)
    assert p.returncode in (0,2) and result['status']=='PASS' and result['info']['files_scanned']==1 and not result['errors'] and not result['warnings']
    checks.append({'order':row['order'],'status':'PASS','files':1,'mission_sha256':row['mission_sha256']})
(D/'mission-validation.json').write_text(json.dumps({'status':'PASS_SIX_MISSION_FILES','missions':checks,'native_acceptance':False},indent=2)+'\n')
print('Prepared six new missions and isolated Nav12 RAM runners; no native launch')
