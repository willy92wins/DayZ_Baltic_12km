"""Attach kit7-generated navmesh only after generation, observer and owned cleanup gates."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,sys
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
G=R/'navmesh-kit7-8m-v9-20261027';I=R/'nav-kit7-8m-preparation-20261027';O=R/'package-kit7-nav8-v9-20261027'
import sys
sys.path.insert(0,str(R))
from verify_c_orderly_close import validate_close,validate_rpt
from verify_nav8_recovered_exit import validate_generation_exit
BASE=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Nav8Input');DEST=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Nav8')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def run(args,label):
 z=subprocess.run([sys.executable,'-I',*map(str,args)],capture_output=True,cwd=W)
 (I/(label+'.stdout.log')).write_bytes(z.stdout);(I/(label+'.stderr.log')).write_bytes(z.stderr)
 if z.returncode:raise RuntimeError(label+': '+z.stderr.decode(errors='replace'))
 print(z.stdout.decode(errors='replace'),flush=True)
assert not O.exists() and not DEST.exists() and not (R/'kit7-nav8-consumer-20261027/deployment.json').exists()
gate=read(R/'kit7-nav8-postprocess-review-20261027/accepted.json')
for p,digest in gate['inputs'].items():assert sha(p)==digest,p
assert gate['status']=='ACCEPTED_AFTER_REVIEW'
assert {str(p) for p in [R/'package_and_deploy_kit7_nav8.py',R/'verify_c_orderly_close.py']}<=set(gate['inputs'])
recovery_gate_path=R/'kit7-nav8-recovered-postprocess-review-20261027/accepted.json'
recovery_gate=read(recovery_gate_path)
assert recovery_gate['status']=='ACCEPTED_AFTER_REVIEW'
recovery_required=[Path(__file__),R/'verify_nav8_recovered_exit.py',R/'resume_kit7_nav8_generation.js',R/'nav8-recovery-addendum.md',R/'test_nav8_recovered_exit.py',R/'kit7-nav8-recovered-exit-controls.json']
recovery_required += [I/n for n in ('generator-identity.json','generator-after-unexecuted-cancel.json','completion-before-lease-recovery.json','cleanup-before-lease-recovery.json','mcp-recovered.json','mcp-before.json','lease-recovery.json')]
assert {str(p) for p in recovery_required}<=set(recovery_gate['inputs'])
assert read(I/'lease-recovery.json')['source_sha256']==sha(R/'resume_kit7_nav8_generation.js')
for p,digest in recovery_gate['inputs'].items():assert sha(p)==digest,p
gate=dict(status=gate['status'],inputs={**gate['inputs'],**recovery_gate['inputs'],str(recovery_gate_path):sha(recovery_gate_path)})
dep=read(I/'launch-inputs.json');gen=read(G/'generation.json');close=read(I/'cleanup.json');host=read(I/'host-identity.json')
completion=read(I/'completion.json');observer=read(I/'observer/terminal.json');attached=read(I/'observer/attached.json')
assert completion['status']=='GENERATION_STAGE_COMPLETE_PENDING_VALIDATION' and not completion['error'] and not completion['cleanup_error']
assert gen['status']=='GENERATED_FILE_PENDING_STRUCTURAL_AND_ENGINE_VALIDATION' and gen['returncode']==0 and gen['inputs_unchanged'] and not gen['failure_reasons']
assert close['close']['run_retired'] and close['close']['graceful'] and close['self']['state']=='none' and not close['cleanup_degraded']
assert not close['own_run_present'] and not close['preserve_for_recovery'] and close['pending_commands']==0 and not close['error'] and not close['cleanup_error']
from uuid import UUID
assert str(UUID(gen['run_id']))==gen['run_id']
assert gen['run_id']==host['run_id']==completion['run_id']==close['close']['run_id']
assert dep['status']=='READY_AFTER_CODE_REVIEW' and dep['generation_seconds']==18000 and dep['observer_seconds']==18300
assert host['navmesh_data_server'] and host['executable_file_sha256']=='a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'
utc=lambda x:datetime.datetime.fromisoformat(x.replace('Z','+00:00'))
validate_close(close['close'])
validate_rpt(read(I/'rpt-binding.json'),host,I/'server.RPT')
assert attached['status']=='ATTACHED' and attached['handle_retained'] and not attached['mutation_attempted']
assert observer['process_id']==attached['process_id']==host['pid']
assert observer['observer_sha256']==attached['observer_sha256']==dep['observer_sha256']
assert attached['executable_sha256']==host['executable_file_sha256']
for stamp in [observer['start_utc'],attached['start_utc']]:assert abs((utc(stamp)-utc(host['created_utc'])).total_seconds())<=.002
events=[json.loads(x) for x in (I/'timeline.jsonl').read_text(encoding='utf-8-sig').splitlines()]
server_exit_code_observed=validate_generation_exit(observer,events,gen['run_id'])
intent=[e for e in events if e['event']=='CLOSE_INTENT'];assert len(intent)==1
assert not any(e['event']=='SERVER_EXIT_OBSERVED' for e in events)  # exact unexecuted cancel intent classified by reviewed recovery verifier above
assert utc(attached['utc'])<=utc(gen['started_utc'])<=utc(gen['finished_utc'])<=utc(intent[0]['utc'])<=utc(observer['observed_utc'])
for name in ('mcp-before.json','mcp-after.json'):
 m=read(I/name);assert m['run_id']==m['server_run_id']==gen['run_id'] and m['server_binding']=='BOUND' and m['version_state']=='ok'
 assert len(m['processes'])==1 and m['processes'][0]['pid']==host['pid'] and m['processes'][0]['role']=='server'
 assert abs((utc(m['processes'][0]['creation_time_utc'])-utc(host['created_utc'])).total_seconds())<=.002
 assert all(x['state']=='not_started' for x in m['client_diagnostics'])
for mapping in [dep['inputs'],gen['inputs'],host['package_hashes']]:
 for p,digest in mapping.items():assert sha(p)==digest,p
assert {str(Path(p).resolve()).casefold():h for p,h in host['package_hashes'].items()}=={str(Path(p).resolve()).casefold():h for p,h in dep['packages'].items()} and len(host['package_hashes'])==len(dep['packages'])==4
assert gen['generator_sha256']=='66935ce864436892247cd520ea2205c179d661e6390478ec35a2c304aa2ecbb7'
assert {Path(p).name.casefold():h for p,h in host['package_hashes'].items()}=={'narva_trial.pbo':'9fbc7608dc407b8b90c7809071aa01f4c27082e6943b293d58d09cb4fd451b49','baltic_stream_pilot.pbo':'3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6','baltic_water_v30.pbo':'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43','dayz_mcp.pbo':'7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'}
assert sha(G/'baltic_trial.nm')==gen['navmesh_sha256']
run([W/'tools/navigation/inspect_navmesh_v9_ev112.py',G/'baltic_trial.nm',G/'inspection.json','--expected-sha256',gen['navmesh_sha256'],'--grid','1536','1536','--tile-width','8'],'inspection')
run([W/'tools/playtest/attach_navmesh.py','--baseline',BASE/'Addons/narva_trial.pbo','--navmesh',G/'baltic_trial.nm','--wrp-sha256','0da63d3f258923e784a62bcb59bb1d7f2ab99866816f530bfe73cd4211b23254','--filebank','C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe','--output',O,'--replace-existing-sha256','13e1ab1567740aca2ff94d6607b6f2c6423b9142674878562bf477994597f80b'],'package')
v=read(O/'verification.json')
assert v['status']=='PASS_NAVMESH_PACKED_BYTE_PARITY' and v['original_entries_unchanged']==6826 and v['replaced_entry']=='navmesh/baltic_trial.nm'
assert v['baseline_pbo_sha256']=='9fbc7608dc407b8b90c7809071aa01f4c27082e6943b293d58d09cb4fd451b49' and v['navmesh_sha256']==gen['navmesh_sha256']
(DEST/'Addons').mkdir(parents=True,exist_ok=False)
deployed={}
for name in ('narva_trial.pbo','baltic_stream_pilot.pbo','baltic_water_v30.pbo'):
 source=(O if name=='narva_trial.pbo' else BASE)/'Addons'/name
 target=DEST/'Addons'/name;shutil.copyfile(source,target);digest=sha(source);assert sha(target)==digest
 deployed[str(target)]=digest
packages={**deployed,str(Path('P:/Mods/@DayZ_MCP/Addons/DayZ_MCP.pbo')):'7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'}
frozen=read(R/'kit7-nav8-consumer-20261027/frozen.json')
for p,digest in frozen['inputs'].items():assert sha(p)==digest,p
write(R/'kit7-nav8-consumer-20261027/deployment.json',dict(server_exit_code_observed=server_exit_code_observed,deployed=deployed,packages=packages,inputs={**frozen['inputs'],**packages,**gate['inputs'],str(I/'mcp-after.json'):sha(I/'mcp-after.json')},mission=frozen['mission']))
write(O/'deployment.json',dict(status='KIT7_NAV8_DEPLOYED_RUNTIME_PENDING',server_exit_code_observed=server_exit_code_observed,mod=str(DEST),deployed=deployed,packages=packages,inputs=gate['inputs'],generation_run=gen['run_id'],wrp_sha256=v['wrp_sha256'],unchanged_entries=v['original_entries_unchanged'],limits=['Same WRP/pilot bytes preserve previous physical artifact; navigation607 and patch coverage remain pending.','No graph or actor acceptance before the kit7 consumer.']))
print(json.dumps(dict(status='KIT7_NAV8_DEPLOYED_RUNTIME_PENDING',deployed=deployed),indent=2))

