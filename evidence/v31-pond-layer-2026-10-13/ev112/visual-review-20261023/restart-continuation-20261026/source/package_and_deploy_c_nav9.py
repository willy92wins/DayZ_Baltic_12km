"""Attach C-generated navmesh only after generation, observer and owned cleanup gates."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,sys
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
G=R/'navmesh-c-v9-20261026';I=R/'nav-c-data-preparation-v2-20261026';O=R/'package-midpoint-c-nav-v9'
BASE=Path('P:/Mods/@DayZ_Baltic_EV112_MidpointC');DEST=Path('P:/Mods/@DayZ_Baltic_EV112_MidpointCNavV9')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def run(args,label):
 z=subprocess.run([sys.executable,'-I',*map(str,args)],capture_output=True,cwd=W)
 (I/(label+'.stdout.log')).write_bytes(z.stdout);(I/(label+'.stderr.log')).write_bytes(z.stderr)
 if z.returncode:raise RuntimeError(label+': '+z.stderr.decode(errors='replace'))
 print(z.stdout.decode(errors='replace'),flush=True)
assert not O.exists() and not DEST.exists() and not (R/'patch-nav-c45/deployment.json').exists()
gate=read(R/'nav-c-postprocess-review/accepted.json')
for p,digest in gate['inputs'].items():assert sha(p)==digest,p
assert gate['status']=='ACCEPTED_AFTER_REVIEW'
dep=read(I/'launch-inputs.json');gen=read(G/'generation.json');close=read(I/'cleanup.json');host=read(I/'host-identity.json')
completion=read(I/'completion.json');observer=read(I/'observer/terminal.json');attached=read(I/'observer/attached.json')
assert completion['status']=='GENERATION_STAGE_COMPLETE_PENDING_VALIDATION' and not completion['error'] and not completion['cleanup_error']
assert gen['status']=='GENERATED_FILE_PENDING_STRUCTURAL_AND_ENGINE_VALIDATION' and gen['returncode']==0 and gen['inputs_unchanged'] and not gen['failure_reasons']
assert close['close']['run_retired'] and close['close']['graceful'] and close['self']['state']=='none' and not close['cleanup_degraded']
assert not close['own_run_present'] and not close['preserve_for_recovery'] and close['pending_commands']==0 and not close['error'] and not close['cleanup_error']
assert gen['run_id']==host['run_id']==completion['run_id']==close['close']['run_id']=='a2619a56-4b44-49f1-bb6f-da2a16da3f86'
assert host['navmesh_data_server'] and host['executable_file_sha256']=='a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'
utc=lambda x:datetime.datetime.fromisoformat(x.replace('Z','+00:00'))
assert observer['status']=='EXIT_OBSERVED' and observer['exit_code']==0 and not observer['error']
assert attached['status']=='ATTACHED' and attached['handle_retained'] and not attached['mutation_attempted']
assert observer['process_id']==attached['process_id']==host['pid']
assert observer['observer_sha256']==attached['observer_sha256']==dep['observer_sha256']
assert attached['executable_sha256']==host['executable_file_sha256']
for stamp in [observer['start_utc'],attached['start_utc']]:assert abs((utc(stamp)-utc(host['created_utc'])).total_seconds())<=.002
events=[json.loads(x) for x in (I/'timeline.jsonl').read_text(encoding='utf-8-sig').splitlines()]
assert all(e['run_id']==gen['run_id'] for e in events)
intent=[e for e in events if e['event']=='CLOSE_INTENT'];assert len(intent)==1
assert not any(e['event'] in ('SERVER_EXIT_OBSERVED','GENERATOR_CANCEL_INTENT') for e in events)
assert utc(attached['utc'])<=utc(gen['started_utc'])<=utc(gen['finished_utc'])<=utc(intent[0]['utc'])<=utc(observer['observed_utc'])
for name in ('mcp-before.json','mcp-after.json'):
 m=read(I/name);assert m['run_id']==m['server_run_id']==gen['run_id'] and m['server_binding']=='BOUND' and m['version_state']=='ok'
 assert len(m['processes'])==1 and m['processes'][0]['pid']==host['pid'] and m['processes'][0]['role']=='server'
 assert abs((utc(m['processes'][0]['creation_time_utc'])-utc(host['created_utc'])).total_seconds())<=.002
 assert all(x['state']=='not_started' for x in m['client_diagnostics'])
for mapping in [dep['inputs'],gen['inputs'],host['package_hashes'],read(R/'patch-nav-c45/frozen.json')['inputs']]:
 for p,digest in mapping.items():assert sha(p)==digest,p
assert host['package_hashes']==dep['packages'] and len(host['package_hashes'])==4
assert gen['generator_sha256']=='66935ce864436892247cd520ea2205c179d661e6390478ec35a2c304aa2ecbb7'
assert sha(G/'baltic_trial.nm')==gen['navmesh_sha256']
run([W/'tools/navigation/inspect_navmesh_v9_ev112.py',G/'baltic_trial.nm',G/'inspection.json','--expected-sha256',gen['navmesh_sha256'],'--grid','983','983','--tile-width','12.5'],'inspection')
run([W/'tools/playtest/attach_navmesh.py','--baseline',BASE/'Addons/narva_trial.pbo','--navmesh',G/'baltic_trial.nm','--wrp-sha256','0139cd1a7ce360436e474fa6448470dfe93bf34a21229b6cf44f4e839af54126','--filebank','C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe','--output',O,'--replace-existing-sha256','eb0f131e5fc0f80d81c60b1f332d8ecfa6396cab9e09ffd36cd1c8504885c496'],'package')
v=read(O/'verification.json')
assert v['status']=='PASS_NAVMESH_PACKED_BYTE_PARITY' and v['original_entries_unchanged']==6826 and v['replaced_entry']=='navmesh/baltic_trial.nm'
assert v['baseline_pbo_sha256']=='4e5f909d2a27e9322299d751d2d54d67f5cc06700499d0498e533b5e1674ef38' and v['navmesh_sha256']==gen['navmesh_sha256']
(DEST/'Addons').mkdir(parents=True,exist_ok=False)
deployed={}
for name in ('narva_trial.pbo','baltic_stream_pilot.pbo','baltic_water_v30.pbo'):
 source=(O if name=='narva_trial.pbo' else BASE)/'Addons'/name
 target=DEST/'Addons'/name;shutil.copyfile(source,target);digest=sha(source);assert sha(target)==digest
 deployed[str(target)]=digest
packages={**deployed,str(Path('P:/Mods/@DayZ_MCP/Addons/DayZ_MCP.pbo')):'7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'}
frozen=read(R/'patch-nav-c45/frozen.json')
write(R/'patch-nav-c45/deployment.json',dict(deployed=deployed,packages=packages,inputs={**frozen['inputs'],**packages,**gate['inputs']},mission=frozen['mission']))
write(O/'deployment.json',dict(status='C_NAV9_DEPLOYED_RUNTIME_PENDING',mod=str(DEST),deployed=deployed,generation_run=gen['run_id'],wrp_sha256=v['wrp_sha256'],unchanged_entries=v['original_entries_unchanged'],limits=['Same WRP/pilot bytes preserve previous physical artifact; navigation45 and patch coverage remain pending.','No claim of actor movement or traversal of25Cmodels.']))
print(json.dumps(dict(status='C_NAV9_DEPLOYED_RUNTIME_PENDING',deployed=deployed),indent=2))

