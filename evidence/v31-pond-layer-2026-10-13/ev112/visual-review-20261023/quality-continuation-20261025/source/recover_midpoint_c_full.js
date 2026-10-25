async function recover(){
const R='E:/DayZ-Baltic-Build/shape-repair-20261025',D=R+'/runtime-midpoint-c/full',runid='36bd8f62-bccd-4f8d-9889-6d822f005604',mission='C:\\temp\\DayZ_MCP_130_dev\\mpmissions\\BalticMidpointC.BalticTrial';
const parse=eval('('+load('parseMcpSafe')+')'),token=load('midpointCLeaseRecovered');
const cmd=async(s)=>{const r=await tools.exec_command({cmd:s,max_output_tokens:1400,yield_time_ms:10000});if(r.exit_code!==0)throw Error(r.output);return r;};
const write=async(path,j)=>tools.apply_patch('*** Begin Patch\n*** Add File: '+path+'\n+'+JSON.stringify(j,null,2).replace(/\n/g,'\n+')+'\n*** End Patch');
let done=false;
for(let i=0;i<30;i++){
 parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));
 const q=await cmd("Test-Path -LiteralPath '"+D+"/log-binding.json'");
 if(q.output.trim()==='True'){done=true;break;}
 if(i%6===0)notify((await cmd("Get-Content -LiteralPath 'C:/temp/DayZ_MCP_130_dev/_server/profiles-130/baltic_visual_probe_v1.log' -Tail 1")).output.trim());
 await new Promise(r=>setTimeout(r,10000));
}
if(!done)throw Error('Capture not complete after recovery bound');
const b=parse(await tools.mcp__dayz_mcp_130__bridge_status({}));const run=b.lifecycle.runs.find(x=>x.run_id===runid);
if(!run||run.processes.length!==1||run.processes[0].pid!==242484)throw Error('Run mismatch');
await write(D+'/mcp-identity.json',{run_id:runid,state:run.state,mission,processes:run.processes,client_diagnostics:run.client_diagnostics,server_binding:b.server_peer?.binding_state,server_run_id:b.server_peer?.run_id,version:b.server_peer?.version,version_state:b.server_peer?.version_state});
await write(D+'/lease-recovery.json',{run_id:runid,reason:'Coordinator heartbeat lease_expired; exact own RUNNING_IDLE run adopted with session_acquire_wait; capture continued with unchanged PID/start',relaunch:false});
parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));
const close=parse(await tools.mcp__dayz_mcp_130__dayz_test_close({run_id:runid,graceful_timeout_s:20}));
parse(await tools.mcp__dayz_mcp_130__session_release({lease_token:token}));
const after=parse(await tools.mcp__dayz_mcp_130__session_status({}));
await write(D+'/cleanup.json',{close,self:after.self,pending_commands:after.pending_commands,cleanup_degraded:after.cleanup_degraded,box_occupied:after.box.occupied,error:null,coordinator_recovered:true});
if(!close.run_retired||after.self.state!=='none'||after.cleanup_degraded.length)throw Error('Cleanup incomplete');
notify({state:'C_FULL_CLOSED',run_id:runid});
await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+R+"/copy_owned_server_rpt.ps1' -ExpectedStartUtc '"+run.processes[0].creation_time_utc+"' -ExpectedMission '"+mission+"' -OutputDirectory '"+D+"'");
const result=await tools.exec_command({cmd:"& 'C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe' -I '"+R+"/finish_midpoint_c_probe.py' full",yield_time_ms:10000,max_output_tokens:1800});
text(result);return result;
}
