"""Consume native kit7 navigation only with exact packages and owned run binding."""
from pathlib import Path
import hashlib,json,sys,datetime,subprocess
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent
sys.path.insert(0,str(R))
from verify_c_orderly_close import validate_close,validate_rpt
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'kit7-nav12-consumer-20261027'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
frozen=read(O/'frozen.json');deployment=read(O/'deployment.json')
for mapping in [frozen['inputs'],deployment['inputs']]:
 for path,digest in mapping.items():assert sha(path)==digest,path
host=read(O/'host-identity.json');mcp=read(O/'mcp-identity.json');binding=read(O/'log-binding.json')
assert host['run_id']==mcp['run_id']==mcp['server_run_id'] and mcp['server_binding']=='BOUND' and mcp['version_state']=='ok'
assert len(mcp['processes'])==1 and mcp['processes'][0]['role']=='server' and mcp['processes'][0]['pid']==host['pid']==binding['pid']
assert not host['navmesh_data_server'] and all(x['state']=='not_started' for x in mcp['client_diagnostics'])
assert Path(host['mission_path'])==Path(frozen['mission'])
assert host['executable_file_sha256']=='a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'
assert host['mission_sha256']==sha(Path(frozen['mission'])/'init.c')
canonical=lambda x:{str(Path(p).resolve()).casefold():h for p,h in x.items()}
assert canonical(host['package_hashes'])==canonical(deployment['packages']) and len(host['package_hashes'])==4
assert binding['sha256']==sha(O/'runtime.log') and binding['expected_end_count']==607
assert Path(binding['source']).name==frozen['log_name']
assert mcp['version']==read(R/'nav-kit7-12m-preparation-20261027/mcp-after.json')['version']
utc=lambda x:datetime.datetime.fromisoformat(x.replace('Z','+00:00')).astimezone(datetime.timezone.utc)
for stamp in [mcp['processes'][0]['creation_time_utc'],binding['created_utc']]:assert abs((utc(host['created_utc'])-utc(stamp)).total_seconds())<=.002
assert utc(binding['source_last_write_utc'])>=utc(host['created_utc'])
cleanup=read(O/'cleanup.json')
assert cleanup['close']['run_id']==host['run_id'] and cleanup['close']['run_retired'] and cleanup['self']['state']=='none' and not cleanup['cleanup_degraded']
assert not cleanup['error'] and not cleanup['cleanup_error'] and not cleanup['own_run_present'] and cleanup['pending_commands']==0
validate_close(cleanup['close'])
validate_rpt(read(O/'rpt-binding.json'),host,O/'server.RPT')
events=[json.loads(x) for x in (O/'timeline.jsonl').read_text(encoding='utf-8-sig').splitlines()]
assert all(e['run_id']==host['run_id'] for e in events)
intents=[e for e in events if e['event']=='CLOSE_INTENT'];assert len(intents)==1
assert utc(binding['source_last_write_utc'])<=utc(intents[0]['utc'])
assert not (O/'identity-verification.json').exists() and not (O/'result.json').exists() and not (O/'coverage.json').exists()
def execute(args,label):
 p=subprocess.run([sys.executable,'-I',*map(str,args)],capture_output=True)
 (O/(label+'.stdout.log')).write_bytes(p.stdout);(O/(label+'.stderr.log')).write_bytes(p.stderr)
 print(p.stdout.decode(errors='replace'));print(p.stderr.decode(errors='replace'))
 if p.returncode:raise SystemExit(p.returncode)
observer=read(O/'observer/terminal.json');attached=read(O/'observer/attached.json')
from verify_c_orderly_close import validate_generation_exit
assert attached['status']=='ATTACHED' and attached['handle_retained'] and not attached['mutation_attempted']
assert observer['process_id']==attached['process_id']==host['pid']
assert observer['observer_sha256']==attached['observer_sha256']==sha(W/'tools/navigation/observe_owned_server_exit.ps1')
assert attached['executable_sha256']==host['executable_file_sha256']
for stamp in (observer['start_utc'],attached['start_utc']):assert abs((utc(stamp)-utc(host['created_utc'])).total_seconds())<=.002
validate_generation_exit(observer,events,host['run_id'])
(O/'identity-verification.json').write_text(json.dumps(dict(status='PASS_BOUND_NATIVE_PROBE_INPUTS',close=cleanup['close'],run_id=host['run_id'],inputs_unchanged=True,navmesh_data_server=False,client_started=False,packages=deployment['packages'],limits=['Exact kit7 NM and packages; no actor or global acceptance.']),indent=2)+'\n')
execute([W/'tools/navigation/verify_kit7_nav_ev112.py','--reference',O/'reference.json','--reference-sha256',frozen['inputs'][str(O/'reference.json')],'--log',O/'runtime.log','--terrain-e',R/'guarded-relief-batch-e-merged/terrain-buried.npz','--out',O/'result.json'],'consumer')
assert read(O/'result.json')['status']=='PASS_KIT7_NATIVE_GRAPH'
print('KIT7_NATIVE607_GRAPH_PASS')
