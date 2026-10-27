async function resumeKit7Nav8(){
const r='E:/DayZ-Baltic-Build/shape-repair-20261025',w='C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c',py='C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe';
const d=r+'/nav-kit7-8m-preparation-20261027',out=r+'/navmesh-kit7-8m-v9-20261027',mission='C:\\temp\\DayZ_MCP_130_dev\\mpmissions\\BalticKit7NavData.BalticTrial';
const parse=eval('('+load('parseKit7Mcp')+')');
let token=load('nav8RecoveryToken');if(!token)throw Error('Recovery token missing');
const cmd=async(s,ms=10000,max=1800,background=false)=>{let q=await tools.exec_command({cmd:s,workdir:w,yield_time_ms:ms,max_output_tokens:max});if(background&&q.session_id)return q;let output=q.output||'';while(q.session_id){if(token)await beat();q=await tools.write_stdin({session_id:q.session_id,chars:'',yield_time_ms:10000,max_output_tokens:max});output+=q.output||'';}if(q.exit_code!==0)throw Error(output||'Command did not complete successfully');return {...q,output};};
const read=async(path)=>JSON.parse((await cmd("Get-Content -LiteralPath '"+path+"' -Raw",10000,9000)).output);
const exists=async(path)=>(await cmd("Test-Path -LiteralPath '"+path+"'")).output.trim()==='True';
const write=async(path,obj)=>tools.apply_patch('*** Begin Patch\n*** Add File: '+path+'\n+'+JSON.stringify(obj,null,2).replace(/\n/g,'\n+')+'\n*** End Patch');
const runid='0db37e43-0bd0-4ac6-8b03-bc85daf9d5b2';let p={pid:46288,creation_time_utc:'2026-10-27T01:56:26.504646Z'},genSession=11394,observerSession=39068,genDone=false,problem=null,cleanupProblem=null,close=null,preserveForRecovery=false,generatorFinished=null;
const event=async(name)=>cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/record_nav_c_event.ps1' -Directory '"+d+"' -RunId '"+runid+"' -Event "+name);
const checkedBridge=async()=>{const b=parse(await tools.mcp__dayz_mcp_130__bridge_status({}));const run=b.lifecycle.runs.find(x=>x.run_id===runid);if(!run||run.processes.length!==1||run.processes[0].role!=='server'||run.client_diagnostics.some(x=>x.state!=='not_started'))throw Error('Owned server identity/client state lost');if(p&&(run.processes[0].pid!==p.pid||run.processes[0].creation_time_utc!==p.creation_time_utc))throw Error('Server process changed');return {b,run};};
const beat=async()=>{
 try {parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));}
 catch(e){
  const state=parse(await tools.mcp__dayz_mcp_130__session_status({}));const own=state.box.runs.find(x=>x.run_id===runid);
  if(state.self.state!=='none'||state.owner||!own||own.state!=='RUNNING_IDLE')throw Error('Coordination lost; no forced adoption');
  const a=parse(await tools.mcp__dayz_mcp_130__session_acquire_wait({purpose:'Recuperar solo nuestra generación kit7 '+runid,max_wait_s:10}));if(!a.lease_token)throw Error('Own run not adopted');token=a.lease_token;store('nav8RecoveryToken',token);
  await checkedBridge();await event('LEASE_RECOVERED');
 }
};
const snapshot=async(name)=>{const {b,run}=await checkedBridge();if(b.server_peer?.binding_state!=='BOUND'||b.server_peer?.run_id!==runid||b.server_peer?.version_state!=='ok')throw Error('Server bridge not bound');await write(d+'/'+name,{run_id:runid,processes:run.processes,client_diagnostics:run.client_diagnostics,server_binding:b.server_peer.binding_state,server_run_id:b.server_peer.run_id,version:b.server_peer.version,version_state:b.server_peer.version_state});return run;};
try {
 await beat();await snapshot('mcp-recovered.json');
 await cmd("$ErrorActionPreference='Stop'\n$i=Get-Content -LiteralPath '"+d+"/launch-inputs.json' -Raw|ConvertFrom-Json\nforeach($v in $i.inputs.PSObject.Properties){if((Get-FileHash -LiteralPath $v.Name).Hash.ToLowerInvariant() -ne $v.Value){throw 'Recovery input drift'}}");
 await event('LEASE_RECOVERED');let q={session_id:genSession};
 let rounds=0;const deadline=Date.parse('2026-10-27T01:59:33.833774Z')+18300e3;
 while(q.session_id){
  await beat();
  if(await exists(d+'/observer/terminal.json')){await event('SERVER_EXIT_OBSERVED');throw Error('Observer ended before requested close');}
  q=await tools.write_stdin({session_id:genSession,chars:'',yield_time_ms:10000,max_output_tokens:1600});rounds++;
  if(rounds%3===0){await event('HEARTBEAT_OK');await cmd("$row=[ordered]@{utc=[DateTimeOffset]::UtcNow.ToString('o');progress=(Get-Content -LiteralPath '"+out+"/generator.stderr.log' -Tail 2)}\nAdd-Content -LiteralPath '"+d+"/progress.jsonl' -Value ($row|ConvertTo-Json -Compress) -Encoding UTF8");}
  if(rounds%6===0){const progress=await cmd("Get-Content -LiteralPath '"+out+"/generator.stderr.log' -Tail 2");notify({state:'KIT7_NAV_PROGRESS',run_id:runid,progress:progress.output.slice(-600)});}
  if(Date.now()>deadline)throw Error('Coordinator duration bound');
 }
 generatorFinished=q;genDone=q.exit_code===0&&(await read(out+'/generation.json')).status==='GENERATED_FILE_PENDING_STRUCTURAL_AND_ENGINE_VALIDATION';if(!genDone)throw Error('Generator failed: '+q.output);
 await beat();await snapshot('mcp-after.json');
 await cmd("$ErrorActionPreference='Stop'\n$i=Get-Content -LiteralPath '"+d+"/launch-inputs.json' -Raw|ConvertFrom-Json\nforeach($v in $i.inputs.PSObject.Properties){if((Get-FileHash -LiteralPath $v.Name).Hash.ToLowerInvariant() -ne $v.Value){throw 'Post-generation input drift'}}");
} catch(e){problem=e.message;}
finally {
 if(genSession&&!genDone){try{await event('GENERATOR_CANCEL_INTENT');await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/cancel_owned_nav_c_generator.ps1' -RunId '"+runid+"' -IdentityPath '"+d+"/generator-identity.json' -OutputPath '"+d+"/generator-cancel.json'");const result=generatorFinished||await tools.write_stdin({session_id:genSession,chars:'',yield_time_ms:10000,max_output_tokens:1600});if(result.session_id)throw Error('Own wrapper still active after cancellation');await write(d+'/generator-wrapper-after-cancel.json',result);}catch(e){cleanupProblem='Generator cancellation: '+e.message;preserveForRecovery=true;}}
 try {
  if(preserveForRecovery)throw Error('Unconfirmed generator cancellation; keep the own server/lease for live recovery');
  if(token)await beat();const state=parse(await tools.mcp__dayz_mcp_130__session_status({}));const own=state.box.runs.find(x=>x.run_id===runid);
  if(own&&state.self.state==='active'){await checkedBridge();await event('CLOSE_INTENT');close=parse(await tools.mcp__dayz_mcp_130__dayz_test_close({run_id:runid,graceful_timeout_s:20}));}
  else if(!own)close={run_id:runid,already_gone:true,run_retired:true,method:'observed absent from lifecycle; not a claimed orderly close'};
  else throw Error('No ownership for DayZ cleanup; no termination attempted');
 }catch(e){cleanupProblem=(cleanupProblem?cleanupProblem+'; ':'')+'DayZ cleanup: '+e.message;}
 try{if(!preserveForRecovery){const state=parse(await tools.mcp__dayz_mcp_130__session_status({}));if(token&&state.self.state==='active')parse(await tools.mcp__dayz_mcp_130__session_release({lease_token:token}));token=null;}}catch(e){cleanupProblem=(cleanupProblem?cleanupProblem+'; ':'')+'Release: '+e.message;}
 try{const after=parse(await tools.mcp__dayz_mcp_130__session_status({}));await write(d+'/cleanup.json',{close,self:after.self,pending_commands:after.pending_commands,cleanup_degraded:after.cleanup_degraded,box_occupied:after.box.occupied,own_run_present:after.box.runs.some(x=>x.run_id===runid),preserve_for_recovery:preserveForRecovery,error:problem,cleanup_error:cleanupProblem});}catch(e){cleanupProblem=(cleanupProblem?cleanupProblem+'; ':'')+'Final status/receipt: '+e.message;}
}
if(!preserveForRecovery){
 try{if(p)await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/copy_owned_server_rpt.ps1' -ExpectedStartUtc '"+p.creation_time_utc+"' -ExpectedMission '"+mission+"' -OutputDirectory '"+d+"'");}catch(e){cleanupProblem=(cleanupProblem||'')+' RPT copy: '+e.message;}
 try{if(observerSession){let q=await tools.write_stdin({session_id:observerSession,chars:'',yield_time_ms:10000,max_output_tokens:1800});if(q.session_id||q.exit_code!==0)cleanupProblem=(cleanupProblem||'')+' Observer incomplete';}}catch(e){cleanupProblem=(cleanupProblem||'')+' Observer: '+e.message;}
 try{if(close?.run_retired&&!close.already_gone)await event('CLOSED');}catch(e){cleanupProblem=(cleanupProblem||'')+' Timeline close: '+e.message;}
}
try{await write(d+'/completion.json',{status:preserveForRecovery?'OWNED_RECOVERY_REQUIRED':(problem||cleanupProblem?'INCONCLUSIVE':'GENERATION_STAGE_COMPLETE_PENDING_VALIDATION'),run_id:runid,error:problem,cleanup_error:cleanupProblem});}catch(e){cleanupProblem=(cleanupProblem||'')+' Completion receipt: '+e.message;}
notify({state:preserveForRecovery?'KIT7_NAV_REQUIRES_OWNED_RECOVERY':'KIT7_NAV_FINISHED',run_id:runid,error:problem,cleanup_error:cleanupProblem});
if(problem||cleanupProblem)throw Error((problem||'')+' '+(cleanupProblem||''));
return {run_id:runid,output:out,identity:d};
}
