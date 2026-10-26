"""Consume the native C45 log only with exact F terrain, C package and owned run binding."""
from pathlib import Path
import hashlib,json,sys,datetime,subprocess
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'patch-nav-c45'
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
assert binding['sha256']==sha(O/'runtime.log') and binding['expected_end_count']==45
utc=lambda x:datetime.datetime.fromisoformat(x.replace('Z','+00:00')).astimezone(datetime.timezone.utc)
for stamp in [mcp['processes'][0]['creation_time_utc'],binding['created_utc']]:assert abs((utc(host['created_utc'])-utc(stamp)).total_seconds())<=.002
assert utc(binding['source_last_write_utc'])>=utc(host['created_utc'])
cleanup=read(O/'cleanup.json')
assert cleanup['close']['run_id']==host['run_id'] and cleanup['close']['run_retired'] and cleanup['self']['state']=='none' and not cleanup['cleanup_degraded']
assert not cleanup['error'] and not cleanup['cleanup_error'] and not cleanup['own_run_present'] and cleanup['pending_commands']==0
assert not (O/'identity-verification.json').exists() and not (O/'result.json').exists() and not (O/'coverage.json').exists()
(O/'identity-verification.json').write_text(json.dumps(dict(status='PASS_BOUND_NATIVE_PROBE_INPUTS',run_id=host['run_id'],inputs_unchanged=True,navmesh_data_server=False,client_started=False,packages=deployment['packages'],limits=['Exact C NM and packages; no actor or25piece traversal claim.']),indent=2)+'\n')
def execute(args,label):
 p=subprocess.run([sys.executable,'-I',*map(str,args)],capture_output=True)
 (O/(label+'.stdout.log')).write_bytes(p.stdout);(O/(label+'.stderr.log')).write_bytes(p.stderr)
 print(p.stdout.decode(errors='replace'));print(p.stderr.decode(errors='replace'))
 if p.returncode:raise SystemExit(p.returncode)
execute([W/'tools/navigation/verify_continuity_nav_v30.py','--reference',O/'reference.json','--log',O/'runtime.log','--out',O/'result.json'],'consumer')
assert read(O/'result.json')['status']=='PASS_LOCAL_CONTINUITY_NAV_PATHS'
execute([W/'tools/navigation/verify_patch_nav_coverage_ev112.py','--reference',O/'reference.json','--reference-sha256',sha(O/'reference.json'),'--log',O/'runtime.log','--consumer',O/'result.json','--terrain-e',R/'guarded-relief-batch-e-merged/terrain-buried.npz','--terrain-f',R/'rectangle-pilot-f-merged/terrain-buried.npz','--local-routes',R/'f-nav-both-bands.json','--local-routes-sha256','7e6b6ae799643b28a7a49079c957d30130c0f1676e9674a96e75aa36d4af0989','--out',O/'coverage.json'],'coverage')
assert read(O/'coverage.json')['status']=='PASS_F_PATCH_WAYPOINT_COVERAGE'
print('C45_AND_F_PATCH_COVERAGE_PASS')

