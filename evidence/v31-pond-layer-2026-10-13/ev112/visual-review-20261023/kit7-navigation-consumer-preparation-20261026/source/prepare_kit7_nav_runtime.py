"""Freeze dedicated mission and derive a bounded FIFO runtime coordinator."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=R/'kit7-nav-consumer-20261026'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
ref=json.loads((D/'reference.json').read_text());mission=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticKit7NavV1.BalticTrial');mission.mkdir(exist_ok=False)
template=W/'missions/BalticKit7NavV1.BalticTrial/init.c';code=template.read_text();assert code.count('@PROBE_ID@')==3
code=code.replace('@PROBE_ID@',ref['probe_id']);(mission/'init.c').write_text(code,encoding='ascii',newline='\n');shutil.copyfile(D/'queries.csv',mission/'queries.csv')
validator=Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py')
bootstrap="import runpy,sys;sys.path.insert(0,"+repr(str(validator.parent))+");sys.argv="+repr([str(validator),str(mission),'--vanilla-root','P:/scripts'])+";runpy.run_path("+repr(str(validator))+",run_name='__main__')"
p=subprocess.run([sys.executable,'-I','-c',bootstrap],capture_output=True)
(D/'script-validator.json').write_bytes(p.stdout);(D/'script-validator.stderr.log').write_bytes(p.stderr)
assert p.returncode in (0,2),(p.returncode,p.stdout,p.stderr)
capture=(R/'capture_patch_nav_log.ps1').read_text().replace('AddSeconds(180)','AddSeconds(900)').replace('END;45','END;607').replace('expected_end_count=45','expected_end_count=607').replace('45-query','607-query').replace('180 seconds','900 seconds')
(R/'capture_kit7_nav_log.ps1').write_text(capture)
s=(R/'orchestrate_c45_retry.js').read_text()
changes={'probeC45Retry':'probeKit7Nav','patch-nav-c45':'kit7-nav-consumer-20261026','BalticPatchNavC45.BalticTrial':'BalticKit7NavV1.BalticTrial','baltic_patch_nav_c45.log':ref['log_name'],'parseMcpSafe':'parseKit7Mcp','nav-c-retry-postprocess-review':'kit7-nav-postprocess-review-20261026','@DayZ_Baltic_EV112_MidpointCNavV9':'@DayZ_Baltic_EV112_Kit7NavV9','wait_for_box_s:0':'on_busy:"queue",wait_for_box_s:600','c45Run':'kit7NavProbeRun','c45Lease':'kit7NavProbeLease','C45':'KIT7_NAV607','capture_patch_nav_log.ps1':'capture_kit7_nav_log.ps1','++rounds>22':'++rounds>100','finish_c45_retry_probe.py':'finish_kit7_nav_probe.py','let p,problem=null':'let p,observerSession=null,problem=null'}
for a,b in changes.items():assert a in s,a;s=s.replace(a,b)
old="const initial=parse(await tools.mcp__dayz_mcp_130__session_status({}));if(initial.box.occupied||initial.self.state!=='none')throw Error('Bank occupied');\n";assert old in s;s=s.replace(old,'')
anchor=" notify({state:'KIT7_NAV607_CAPTURE_STARTED',run_id:runid,pid:p.pid});"
observer="""
 let observer=await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File './tools/navigation/observe_owned_server_exit.ps1' -TargetProcessId "+p.pid+" -ExpectedStartUtc '"+p.creation_time_utc+"' -ExpectedExecutable 'E:/SteamLibrary/steamapps/common/DayZ Exp/DayZDiag_x64.exe' -OutputDirectory '"+d+"/observer' -MaxSeconds 1200",1000,true);
 observerSession=observer.session_id;if(!observerSession)throw Error('Observer ended before capture');
 await cmd("$ErrorActionPreference='Stop'\\n$deadline=[DateTime]::UtcNow.AddSeconds(15)\\nwhile(-not(Test-Path -LiteralPath '"+d+"/observer/attached.json')){if([DateTime]::UtcNow -gt $deadline){throw 'Observer attach deadline'};Start-Sleep -Milliseconds 200}\\n$a=Get-Content -LiteralPath '"+d+"/observer/attached.json' -Raw|ConvertFrom-Json\\nif($a.status -ne 'ATTACHED' -or -not $a.handle_retained -or $a.process_id -ne "+p.pid+"){throw 'Observer identity mismatch'}");
 await event('ATTACHED');
"""
assert anchor in s;s=s.replace(anchor,observer+anchor)
anchor="notify({state:'KIT7_NAV607_CLOSED',run_id:runid,error:problem,cleanup_error:cleanupProblem});"
finish="""try{if(observerSession){const end=await tools.write_stdin({session_id:observerSession,chars:'',yield_time_ms:10000,max_output_tokens:1000});if(end.session_id||end.exit_code!==0)throw Error('Observer incomplete');}}catch(e){cleanupProblem=(cleanupProblem||'')+' Observer: '+e.message;}
if(close?.run_retired&&!close.already_gone)await event('CLOSED');
notify({state:close?.run_retired?'KIT7_NAV607_CLOSED':'KIT7_NAV607_INCOMPLETE',run_id:runid,error:problem,cleanup_error:cleanupProblem});"""
assert anchor in s;s=s.replace(anchor,finish)
(R/'orchestrate_kit7_nav_probe.js').write_text(s)
# Derive the native evidence binding, then invoke the new607 consumer once.
s=(R/'finish_c45_retry_probe.py').read_text().replace('patch-nav-c45','kit7-nav-consumer-20261026').replace('expected_end_count\']==45','expected_end_count\']==607')
start=s.index("execute([W/'tools/navigation/verify_continuity_nav_v30.py'")
s=s[:start]+"""observer=read(O/'observer/terminal.json');attached=read(O/'observer/attached.json')
from verify_c_orderly_close import validate_generation_exit
assert attached['status']=='ATTACHED' and attached['handle_retained'] and not attached['mutation_attempted']
assert observer['process_id']==attached['process_id']==host['pid']
assert observer['observer_sha256']==attached['observer_sha256']==sha(W/'tools/navigation/observe_owned_server_exit.ps1')
assert attached['executable_sha256']==host['executable_file_sha256']
for stamp in (observer['start_utc'],attached['start_utc']):assert abs((utc(stamp)-utc(host['created_utc'])).total_seconds())<=.002
validate_generation_exit(observer,events,host['run_id'])
execute([W/'tools/navigation/verify_kit7_nav_ev112.py','--reference',O/'reference.json','--reference-sha256',sha(O/'reference.json'),'--log',O/'runtime.log','--terrain-e',R/'guarded-relief-batch-e-merged/terrain-buried.npz','--out',O/'result.json'],'consumer')
assert read(O/'result.json')['status']=='PASS_KIT7_NATIVE_GRAPH'
print('KIT7_NATIVE607_GRAPH_PASS')
"""
s=s.replace("'Exact C NM and packages; no actor or25piece traversal claim.'","'Exact kit7 NM and packages; no actor or global acceptance.'")
(R/'finish_kit7_nav_probe.py').write_text(s)
geometry=json.loads(Path(ref['geometry']).read_text());inputs={**ref['inputs'],**geometry['inputs']}
paths=[Path(__file__),template,mission/'init.c',mission/'queries.csv',D/'reference.json',D/'queries.csv',W/'tools/navigation/verify_kit7_nav_ev112.py',W/'tools/navigation/verify_continuity_nav_v30.py',W/'tools/terrain/verify_v30_acceptance.py',W/'tools/navigation/prepare_patch_nav_probe_ev112.py',W/'tools/navigation/observe_owned_server_exit.ps1',R/'capture_kit7_nav_log.ps1',R/'orchestrate_kit7_nav_probe.js',R/'finish_kit7_nav_probe.py',R/'capture_owned_server_identity.ps1',R/'copy_owned_server_rpt.ps1',R/'record_nav_c_event.ps1',R/'verify_c_orderly_close.py',R/'guarded-relief-batch-e-merged/terrain-buried.npz']
inputs.update({str(p):sha(p) for p in paths});assert all(sha(p)==h for p,h in inputs.items())
(D/'frozen.json').write_text(json.dumps(dict(status='PREPARED_PENDING_CODE_REVIEW_AND_NAV_GENERATION',mission=str(mission),log_name=ref['log_name'],probe_id=ref['probe_id'],expected_count=607,inputs=inputs),indent=2)+'\n')
print(json.dumps(dict(status='PREPARED_PENDING_CODE_REVIEW_AND_NAV_GENERATION',inputs=len(inputs),validator_returncode=p.returncode if hasattr(p,'returncode') else None)))
