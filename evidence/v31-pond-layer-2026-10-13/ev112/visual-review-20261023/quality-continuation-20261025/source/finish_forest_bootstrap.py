from pathlib import Path
import hashlib,json,datetime,subprocess,sys
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;O=R/'forest-boundary-full-f'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
assert not (O/'result.json').exists() and not (O/'identity-verification.json').exists()
d=read(O/'deployment.json');host=read(O/'host-identity.json');m=read(O/'mcp-identity.json');b=read(O/'log-binding.json');c=read(O/'cleanup.json')
for path,h in d['inputs'].items():assert sha(path)==h,path
assert host['run_id']==m['run_id']==m['server_run_id'] and m['server_binding']=='BOUND' and m['version_state']=='ok'
assert len(m['processes'])==1 and m['processes'][0]['role']=='server' and m['processes'][0]['pid']==host['pid']==b['pid']
assert host['navmesh_data_server'] and all(x['state']=='not_started' for x in m['client_diagnostics'])
assert Path(host['mission_path'])==Path(d['mission']) and host['mission_sha256']==sha(Path(d['mission'])/'init.c')
assert host['executable_file_sha256']=='a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'
actual={str(Path(p).resolve()).casefold():h for p,h in host['package_hashes'].items()}
expected={**d['deployed'],'P:/Mods/@DayZ_MCP/Addons/DayZ_MCP.pbo':'7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'}
assert actual=={str(Path(p).resolve()).casefold():h for p,h in expected.items()}
for p,h in expected.items():assert sha(p)==h,p
utc=lambda x:datetime.datetime.fromisoformat(x.replace('Z','+00:00')).astimezone(datetime.timezone.utc)
assert abs((utc(host['created_utc'])-utc(m['processes'][0]['creation_time_utc'])).total_seconds())<=.002
assert b['sha256']==sha(O/'runtime.log') and b['expected_end_count']==269968 and b['survey_id']==d['survey_id']
assert utc(b['source_last_write_utc'])>=utc(host['created_utc'])
assert c['close']['run_retired'] and c['self']['state']=='none' and not c['cleanup_degraded']
(O/'identity-verification.json').write_text(json.dumps(dict(status='PASS_BOUND_NATIVE_FOREST_INPUTS',run_id=host['run_id'],inputs_unchanged=True,objects=3727,points=269968,navmesh_data_server=True,client_started=False,limits=['Finite terrain samples; no continuous-disc or compiled-object acceptance.']),indent=2)+'\n')
args=[sys.executable,'-I',str(W/'tools/vegetation/eval_forest_boundary_probe_v31.py'),d['manifest'],str(O/'runtime.log'),'--mod','P:/Mods/@DayZ_Baltic_EV112_RectangleF','--output',str(O/'result.json')]
p=subprocess.run(args,capture_output=True,cwd=W)
(O/'consumer.stdout.log').write_bytes(p.stdout);(O/'consumer.stderr.log').write_bytes(p.stderr)
print(p.stdout.decode(errors='replace'));print(p.stderr.decode(errors='replace'));raise SystemExit(p.returncode)
