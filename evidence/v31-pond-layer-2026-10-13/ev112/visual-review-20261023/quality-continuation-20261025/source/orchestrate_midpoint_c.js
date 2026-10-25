async function midpointProbe(kind){
if(!['full','grid'].includes(kind))throw Error('Bad kind');
const count=kind==='full'?4749:300;
const r='E:/DayZ-Baltic-Build/shape-repair-20261025',d=r+'/runtime-midpoint-c/'+kind,w='C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c',py='C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe';
const mission='C:\\temp\\DayZ_MCP_130_dev\\mpmissions\\'+(kind==='full'?'BalticMidpointC.BalticTrial':'BalticMidpointCGrid.BalticTrial'),log='C:/temp/DayZ_MCP_130_dev/_server/profiles-130/baltic_visual_probe_v1.log';
const parse=eval('('+load('parseMcpSafe')+')');
const cmd=async(s,t=1000)=>{const x=await tools.exec_command({cmd:s,workdir:w,max_output_tokens:1600,yield_time_ms:t});if(x.exit_code!=null&&x.exit_code!==0)throw Error(x.output);return x;};
const write=async(path,j)=>tools.apply_patch('*** Begin Patch\n*** Add File: '+path+'\n+'+JSON.stringify(j,null,2).replace(/\n/g,'\n+')+'\n*** End Patch');
await cmd("$ErrorActionPreference='Stop'\nif(Test-Path -LiteralPath '"+d+"/runtime.log'){throw 'Fresh capture required'}\n$dep=Get-Content -LiteralPath '"+d+"/deployment.json' -Raw|ConvertFrom-Json\nforeach($v in $dep.inputs.PSObject.Properties){if((Get-FileHash -LiteralPath $v.Name).Hash.ToLowerInvariant() -ne $v.Value){throw 'Frozen forest input drift'}}",10000);
const s=parse(await tools.mcp__dayz_mcp_130__session_status({}));if(s.box.occupied||s.self.state!=='none')throw Error('Bank occupied');
await cmd("$ErrorActionPreference='Stop'\nif(Test-Path -LiteralPath '"+log+"'){if(Test-Path -LiteralPath '"+d+"/previous-engine.log'){throw 'Previous log already archived'};Copy-Item -LiteralPath '"+log+"' -Destination '"+d+"/previous-engine.log';if((Get-FileHash -LiteralPath '"+log+"').Hash -ne (Get-FileHash -LiteralPath '"+d+"/previous-engine.log').Hash){throw 'Prior log archive differs'}}",10000);
const args={project:'DayZ_MCP',mode:'server',mission,extra_mods:['@DayZ_Baltic_EV112_MidpointC'],base_mods:[],no_base_mods:true,no_file_patching:true,build:false,takeover:false,wait_for_box_s:0,navmesh_data_server:true};
const launch=parse(await tools.mcp__dayz_mcp_130__dayz_test_run(args));if(launch.status!=='succeeded'||!launch.run_id)throw Error('Launch refused');
store('midpointCRun',launch.run_id);
const a=parse(await tools.mcp__dayz_mcp_130__session_acquire_wait({purpose:'EV112 midpoint B: contactos congelados, sin cliente',max_wait_s:10}));if(!a.lease_token)throw Error('No forest lease');store('midpointCLease',a.lease_token);
const beat=async()=>{const x=parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:a.lease_token}));if(x.ok===false||x.error)throw Error('Heartbeat refused');};
let p,problem;
try{
 await beat();let b=parse(await tools.mcp__dayz_mcp_130__bridge_status({}));let run=b.lifecycle.runs.find(x=>x.run_id===launch.run_id);
 p=run?.processes?.find(x=>x.role==='server');if(!p||run.processes.length!==1)throw Error('Expected one owned server');store('midpointCProcess',p);
 notify({state:'MIDPOINT_NATIVE_STARTED',run_id:launch.run_id,pid:p.pid,points:count});
 await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/capture_owned_server_identity.ps1' -ServerProcessId "+p.pid+" -ExpectedStartUtc '"+p.creation_time_utc+"' -ExpectedMission '"+mission+"' -RunId '"+launch.run_id+"' -OutputPath '"+d+"/host-identity.json'",10000);
 let q=await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/capture_midpoint_log.ps1' -ServerProcessId "+p.pid+" -ExpectedStartUtc '"+p.creation_time_utc+"' -EngineLog '"+log+"' -OutputDirectory '"+d+"' -ExpectedCount "+count);
 const session=q.session_id;let rounds=0;
 while(q.session_id){await beat();q=await tools.write_stdin({session_id:session,chars:'',yield_time_ms:10000,max_output_tokens:1000});if(++rounds>95)throw Error('Capture wrapper bound');if(rounds%6===0){const progress=await cmd("Get-Content -LiteralPath '"+log+"' -Tail 1",10000);notify({state:'MIDPOINT_NATIVE_CAPTURING',progress:progress.output.trim()});}}
 if(q.exit_code!==0)throw Error(q.output);
 await beat();b=parse(await tools.mcp__dayz_mcp_130__bridge_status({}));run=b.lifecycle.runs.find(x=>x.run_id===launch.run_id);
 await write(d+'/mcp-identity.json',{run_id:launch.run_id,state:run?.state,mission,processes:run?.processes,client_diagnostics:run?.client_diagnostics,server_binding:b.server_peer?.binding_state,server_run_id:b.server_peer?.run_id,version:b.server_peer?.version,version_state:b.server_peer?.version_state});
}catch(e){problem=e.message;}
finally{
 await beat();const close=parse(await tools.mcp__dayz_mcp_130__dayz_test_close({run_id:launch.run_id,graceful_timeout_s:20}));await tools.mcp__dayz_mcp_130__session_release({lease_token:a.lease_token});
 const after=parse(await tools.mcp__dayz_mcp_130__session_status({}));await write(d+'/cleanup.json',{close,self:after.self,pending_commands:after.pending_commands,cleanup_degraded:after.cleanup_degraded,box_occupied:after.box.occupied,error:problem||null});
 if(!close.run_retired||after.self.state!=='none'||after.cleanup_degraded.length)throw Error('Forest cleanup incomplete');
}
if(p)await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/copy_owned_server_rpt.ps1' -ExpectedStartUtc '"+p.creation_time_utc+"' -ExpectedMission '"+mission+"' -OutputDirectory '"+d+"'",10000);
notify({state:'MIDPOINT_CAPTURE_CLOSED',run_id:launch.run_id,error:problem||null});if(problem)throw Error(problem);
let q=await cmd("& '"+py+"' -I '"+r+"/finish_midpoint_c_probe.py' "+kind,10000);while(q.session_id)q=await tools.write_stdin({session_id:q.session_id,chars:'',yield_time_ms:10000,max_output_tokens:1800});
notify({state:'MIDPOINT_CONSUMED',exit_code:q.exit_code,output:q.output});
return {run_id:launch.run_id,folder:d,consumer_exit_code:q.exit_code};
}
