"""Adapt the proven generator coordinator without launching or accepting a run."""
from pathlib import Path
import hashlib,json
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'nav-kit7-preparation-20261026';assert not O.exists();O.mkdir()
source=R/'orchestrate_nav_c_retry_v3.js';s=source.read_text(encoding='utf-8')
replacements={
'retryCNavigationAfterHumanClose':'generateKit7Navigation',
'nav-c-retry-human-close-20261026':'nav-kit7-preparation-20261026',
'navmesh-c-retry-v9-20261026':'navmesh-kit7-v9-20261026',
'BalticCNavData':'BalticKit7NavData',
'parseMcpSafe':'parseKit7Mcp',
'@DayZ_Baltic_EV112_MidpointC':'@DayZ_Baltic_EV112_Kit7Native',
'4e5f909d2a27e9322299d751d2d54d67f5cc06700499d0498e533b5e1674ef38':'10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc',
'c7dc430d809bcec2f29ff1fe86f266f0f9680b8ad676a8722b0b45d4494de02f':'46244e7f2abc6bd2d07be828097325ec9bba9c672b48bfcef177895b87380b2d',
'navRetry':'navKit7',
'Recuperar solo nuestra generación C':'Recuperar solo nuestra generación kit7',
'EV112 C: nuevo intento tras cierre humano confirmado, máximo7200s, sin cliente':'EV112 kit7: navegación propia tras gate físico, máximo7200s, sin cliente',
'C_NAV_':'KIT7_NAV_'}
for a,b in replacements.items():assert a in s,a;s=s.replace(a,b)
needle="let s=parse(await tools.mcp__dayz_mcp_130__session_status({}));"
gate="const physical=await read(r+'/kit7-water-native-20261026/full/result.json');if(physical.status!=='SERVER_PROBE_PASS'||physical.points!==6801||!physical.identity_bound||!physical.inputs_unchanged)throw Error('Kit7 physical gate missing');\n"
assert s.count(needle)==1;s=s.replace(needle,gate+needle)
dest=R/'orchestrate_nav_kit7.js';assert not dest.exists();dest.write_text(s,encoding='utf-8')
restored=s.replace(gate,'')
for a,b in reversed(list(replacements.items())):restored=restored.replace(b,a)
assert restored==source.read_text(encoding='utf-8')
for old,new in [('test_nav_c_retry_command.cjs','test_nav_kit7_command.cjs'),('test_nav_c_retry_coordinator.cjs','test_nav_kit7_coordinator.cjs')]:
 t=(R/old).read_text(encoding='utf-8').replace('orchestrate_nav_c_retry_v3.js','orchestrate_nav_kit7.js').replace('nav-c-retry-review','nav-kit7-preparation-20261026').replace('retryCNavigationAfterHumanClose','generateKit7Navigation')
 # The new production gate is driven through a real mock full-result response.
 if 'coordinator' in old:
  needle="if(c.includes('launch-inputs.json'))return ok(JSON.stringify({status:'READY_AFTER_CODE_REVIEW',observer_sha256:'observer'}));";assert needle in t
  t=t.replace(needle,needle+"\n    if(c.includes('/full/result.json'))return ok(JSON.stringify({status:'SERVER_PROBE_PASS',points:6801,identity_bound:true,inputs_unchanged:true}));")
 p=R/new;assert not p.exists();p.write_text(t,encoding='utf-8')
mission=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticKit7NavData.BalticTrial');assert not mission.exists();mission.mkdir()
oldmission=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticCNavData.BalticTrial/init.c');code=oldmission.read_text(encoding='ascii');assert 'BalticCNavDataMission' in code;(mission/'init.c').write_text(code.replace('BalticCNavDataMission','BalticKit7NavDataMission'),encoding='ascii')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(status='DRAFT_PENDING_PHYSICS_AND_REVIEW',source=str(source),source_sha256=sha(source),adapted=str(dest),adapted_sha256=sha(dest),inverse_substitutions_exact=True,replacements=replacements,additional_physics_gate=gate,mission=str(mission),mission_sha256=sha(mission/'init.c'),generator_not_started=True)
(O/'adaptation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='replacements'},indent=2,ensure_ascii=True))
