from pathlib import Path
import hashlib,json,sys,datetime,subprocess
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
side=sys.argv[1];assert side in ('E','F');out=R/('patch-nav-'+side.lower()+'45')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=json.loads((R/'patch-nav-frozen.json').read_text())[side]
deployment=json.loads((out/'deployment.json').read_text())
for path,digest in {**frozen['inputs'],**deployment['inputs']}.items():assert sha(Path(path))==digest,path
host=json.loads((out/'host-identity.json').read_text());mcp=json.loads((out/'mcp-identity.json').read_text());binding=json.loads((out/'log-binding.json').read_text())
assert host['run_id']==mcp['run_id']==mcp['server_run_id'] and mcp['server_binding']=='BOUND' and mcp['version_state']=='ok'
assert len(mcp['processes'])==1 and mcp['processes'][0]['role']=='server' and mcp['processes'][0]['pid']==host['pid']==binding['pid']
assert not host['navmesh_data_server'] and all(x['state']=='not_started' for x in mcp['client_diagnostics'])
assert Path(host['mission_path'])==Path(frozen['mission'])
assert host['executable_file_sha256']=='a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'
assert host['mission_sha256']==sha(Path(frozen['mission'])/'init.c')
actual={str(Path(p).resolve()).casefold():h for p,h in host['package_hashes'].items()}
for p,h in deployment['deployed'].items():assert actual[str(Path(p).resolve()).casefold()]==h
assert len(actual)==4,'Expected only world/pilot/water plus MCP'
assert binding['sha256']==sha(out/'runtime.log')
utc=lambda x:datetime.datetime.fromisoformat(x.replace('Z','+00:00')).astimezone(datetime.timezone.utc)
assert abs((utc(host['created_utc'])-utc(mcp['processes'][0]['creation_time_utc'])).total_seconds())<=.002
assert utc(binding['source_last_write_utc'])>=utc(host['created_utc'])
cleanup=json.loads((out/'cleanup.json').read_text());assert cleanup['close']['run_retired'] and cleanup['self']['state']=='none' and not cleanup['cleanup_degraded']
(out/'identity-verification.json').write_text(json.dumps(dict(status='PASS_BOUND_NATIVE_PROBE_INPUTS',run_id=host['run_id'],inputs_unchanged=True,navmesh_data_server=False,client_started=False,limits=['MCP executable identity is path-derived; host executable_file_sha256 hashes bytes.','Loaded package hashes identify native navmesh; patch height alone does not.']),indent=2)+'\n')
args=[sys.executable,'-I',str(W/'tools/navigation/verify_continuity_nav_v30.py'),'--reference',str(out/'reference.json'),'--log',str(out/'runtime.log'),'--out',str(out/'result.json')]
p=subprocess.run(args,capture_output=True);(out/'consumer.stdout.log').write_bytes(p.stdout);(out/'consumer.stderr.log').write_bytes(p.stderr)
print(p.stdout.decode(errors='replace'));print(p.stderr.decode(errors='replace'))
raise SystemExit(p.returncode)
