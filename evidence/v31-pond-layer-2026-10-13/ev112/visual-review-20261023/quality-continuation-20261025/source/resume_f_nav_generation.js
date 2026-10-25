async function resumeFNavGeneration(){
const r='E:/DayZ-Baltic-Build/shape-repair-20261025',prep=r+'/f-nav-data-preparation';
const parse=eval('('+load('parseMcpSafe')+')');
const runId=load('fNavDataRun'),token=load('fNavDataLease');
if(runId!=='4944fd64-7a44-4940-a910-0b0428dbcc9b'||!token)throw Error('Wrong recovery');
const beat=async()=>{const x=parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));if(x.ok===false||x.error)throw Error('Heartbeat refused');};
const cmd=async(cmd)=>{const z=await tools.exec_command({cmd,max_output_tokens:1500});if(z.exit_code!==0)throw Error(z.output);return z;};
const write=async(path,obj)=>tools.apply_patch('*** Begin Patch\n*** Add File: '+path+'\n+'+JSON.stringify(obj,null,2).replace(/\n/g,'\n+')+'\n*** End Patch');
await beat();
await write(prep+'/lease-recovery.json',{run_id:runId,reason:'Original coordinator failed parsing an explicit lease_expired response; same original owned run re-adopted through session_acquire_wait.',server_pid:174160,server_creation_time_utc:'2026-10-25T21:14:00.672534Z',generator_session:86377,restarted:false});
let q,round=0;
do{await beat();q=await tools.write_stdin({session_id:86377,chars:'',yield_time_ms:10000,max_output_tokens:1200});round++;if(round%6===0){const s=await cmd("Get-Content -LiteralPath '"+r+"/navmesh-rectangle-f-v9/generator.stderr.log' -Tail 1");notify({state:'F_NAV_GENERATING',progress:s.output.trim()});}}while(q.session_id);
await beat();
const b=parse(await tools.mcp__dayz_mcp_130__bridge_status({}));const run=b.lifecycle.runs.find(x=>x.run_id===runId);
if(!run||run.processes.length!==1||run.processes[0].pid!==174160||b.server_peer?.run_id!==runId)throw Error('Post-generation identity changed');
await write(prep+'/mcp-after.json',{run_id:runId,processes:run.processes,client_diagnostics:run.client_diagnostics,server_binding:b.server_peer.binding_state,server_run_id:b.server_peer.run_id,version:b.server_peer.version,version_state:b.server_peer.version_state});
const close=parse(await tools.mcp__dayz_mcp_130__dayz_test_close({run_id:runId,graceful_timeout_s:20}));
await tools.mcp__dayz_mcp_130__session_release({lease_token:token});
const after=parse(await tools.mcp__dayz_mcp_130__session_status({}));
await write(prep+'/cleanup.json',{close,self:after.self,pending_commands:after.pending_commands,cleanup_degraded:after.cleanup_degraded,box_occupied:after.box.occupied,generator_exit_code:q.exit_code});
if(!close.run_retired||after.self.state!=='none'||after.cleanup_degraded.length)throw Error('Cleanup incomplete');
await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/copy_owned_server_rpt.ps1' -ExpectedStartUtc '2026-10-25T21:14:00.672534Z' -ExpectedMission 'C:\\temp\\DayZ_MCP_130_dev\\mpmissions\\BalticPatchFNavData.BalticTrial' -OutputDirectory '"+prep+"'");
await cmd("$ErrorActionPreference='Stop'\n$dep=Get-Content -LiteralPath '"+prep+"/inputs.json' -Raw|ConvertFrom-Json\nforeach($v in $dep.inputs.PSObject.Properties){if((Get-FileHash -LiteralPath $v.Name).Hash.ToLowerInvariant() -ne $v.Value){throw 'Input drift after generation'}}");
if(q.exit_code!==0)throw Error('Generator failure '+q.exit_code+': '+q.output);
return {state:'F_GENERATION_COMPLETE_AND_CLOSED',run_id:runId};
}
