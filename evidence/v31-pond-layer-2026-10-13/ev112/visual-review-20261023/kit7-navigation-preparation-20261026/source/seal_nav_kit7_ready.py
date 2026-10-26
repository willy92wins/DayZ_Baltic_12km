from pathlib import Path
import hashlib,json,datetime
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=R/'nav-kit7-preparation-20261026';N=R/'kit7-overlap-native-20261026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
inputs={}
def bind(p):p=Path(p);inputs[str(p)]=sha(p)
def freeze(mapping):
 for p,h in mapping.items():assert sha(Path(p))==h,p;inputs[p]=h
V=R/'kit7-nav-coordinator-fix-review-20261026';c=read(V/'completion.json');review=read(V/'review-response.json')
assert c['exit_code']==0 and c['inputs_unchanged'] and not review['is_error'] and not review['permission_denials']
assert review['result'].startswith('**Veredicto: SOUND.**')
freeze(read(V/'source-hashes.json'))
for name in ['completion.json','source-hashes.json','review-response.json','review-brief.md']:bind(V/name)
for name in ['coordinator-control-flow-v2.json','command-flow-controls-v2.json','host-check-controls-v2.json','lease-control-flow-v2.json']:
 q=read(D/name);assert q['coordinator_sha256']==sha(R/'orchestrate_nav_kit7_v2.js') and all(x['passed'] for x in q['cases']);bind(D/name)
assert read(D/'functions-runtime-capabilities.json')['status']=='ACTUAL_FUNCTIONS_RUNTIME_FEATURES_PASS';bind(D/'functions-runtime-capabilities.json')
f=read(N/'full/result.json');cal=read(N/'calibration/result.json')
assert f['status']=='SERVER_PROBE_PASS' and f['points']==6801 and f['failure_count']==0 and f['identity_bound'] and f['inputs_unchanged']
assert cal['status']=='FRESH_VANILLA_CALIBRATION_PASS' and cal['packages']==f['packages'] and cal['log_sha256']==sha(N/'calibration/native.log')==f['calibration_log_sha256']
assert f['log_sha256']==sha(N/'full/native.log')
freeze(read(N/'accepted.json')['inputs'])
for kind in ['calibration','full']:
 q=read(N/kind/'cleanup.json');assert q['close']['run_retired'] and q['self']['state']=='none' and not q['own_run_present'] and not q['cleanup_degraded'] and not q['pending_commands']
 for name in ['result.json','native.log','host-identity.json','mcp-identity.json','cleanup.json']:bind(N/kind/name)
packages={str(Path(p)):h for p,h in f['packages'].items()};freeze(packages)
for rel in ['capture_nav_c_generator.ps1','cancel_owned_nav_c_generator.ps1','bind_nav_c_rpt_clock.ps1','record_nav_c_event.ps1','copy_owned_server_rpt.ps1','capture_owned_server_identity.ps1','orchestrate_nav_kit7_v2.js','test_nav_kit7_coordinator_v2.cjs','test_nav_kit7_command_v2.cjs','test_nav_kit7_host_binding_v2.cjs','test_nav_kit7_lease_v2.cjs','repair_nav_kit7_review.py','seal_nav_kit7_ready.py']:bind(R/rel)
for rel in ['tools/navigation/generate_navmesh_console.py','tools/navigation/observe_owned_server_exit.ps1','tools/navigation/inspect_navmesh_v9_ev112.py','tools/playtest/attach_navmesh.py','plans/ev112-kit7-navmesh-generation-20261026.md']:bind(W/rel)
mission=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticKit7NavData.BalticTrial');bind(mission/'init.c')
engine=Path('E:/SteamLibrary/steamapps/common/DayZ Exp/DayZDiag_x64.exe');generator=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/NavMeshGenerator/NavMeshGenerator_x64.exe')
assert sha(engine)==f['engine_sha256']=='a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'
assert sha(generator)=='66935ce864436892247cd520ea2205c179d661e6390478ec35a2c304aa2ecbb7';bind(engine);bind(generator)
bind(D/'adaptation-v2.json');bind(N/'accepted.json')
doc=dict(status='READY_AFTER_CODE_REVIEW',mission=str(mission),packages=packages,inputs=inputs,timeout_s=7200,attempt_budget=1,observer_max_s=7500,observer_sha256=sha(W/'tools/navigation/observe_owned_server_exit.ps1'),scope='Kit7 generation only; structure, repackaging and own route traversal remain separate gates.',frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),output=str(R/'navmesh-kit7-v9-20261026'),coordinator_sha256=sha(R/'orchestrate_nav_kit7_v2.js'),review_adjudication='Five required findings closed, independent re-review SOUND; conservative heartbeat behavior retained. Real Functions runtime supports both JS methods.')
p=D/'launch-inputs.json';assert not p.exists();p.write_text(json.dumps(doc,indent=2)+'\n')
print(json.dumps(dict(status=doc['status'],inputs=len(inputs),coordinator_sha256=doc['coordinator_sha256'])))

