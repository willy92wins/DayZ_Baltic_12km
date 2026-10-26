async function probeC45Retry(){
const r='E:/DayZ-Baltic-Build/shape-repair-20261025',w='C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c',py='C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe';
const d=r+'/patch-nav-c45',mission='C:\\temp\\DayZ_MCP_130_dev\\mpmissions\\BalticPatchNavC45.BalticTrial',log='C:/temp/DayZ_MCP_130_dev/_server/profiles-130/baltic_patch_nav_c45.log';
const parse=eval('('+load('parseMcpSafe')+')');
let token=null;
const cmd=async(s,ms=10000,background=false)=>{let q=await tools.exec_command({cmd:s,workdir:w,yield_time_ms:ms,max_output_tokens:2000});if(background&&q.session_id)return q;let output=q.output||'';while(q.session_id){if(token)parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));q=await tools.write_stdin({session_id:q.session_id,chars:'',yield_time_ms:10000,max_output_tokens:2000});output+=q.output||'';}if(q.exit_code!==0)throw Error(output||'Command did not complete successfully');return {...q,output};};
const write=async(path,obj)=>tools.apply_patch('*** Begin Patch\n*** Add File: '+path+'\n+'+JSON.stringify(obj,null,2).replace(/\n/g,'\n+')+'\n*** End Patch');
await cmd("$ErrorActionPreference='Stop'\nif(Test-Path -LiteralPath '"+log+"'){throw 'Fresh log required'}\n$dep=Get-Content -LiteralPath '"+d+"/deployment.json' -Raw|ConvertFrom-Json\n$review=Get-Content -LiteralPath '"+r+"/nav-c-retry-postprocess-review/accepted.json' -Raw|ConvertFrom-Json\nif($review.status -ne 'ACCEPTED_AFTER_REVIEW'){throw 'Review missing'}\nforeach($v in @($dep.inputs.PSObject.Properties)+@($review.inputs.PSObject.Properties)){if((Get-FileHash -LiteralPath $v.Name).Hash.ToLowerInvariant() -ne $v.Value){throw 'Frozen probe input drift'}}");
const initial=parse(await tools.mcp__dayz_mcp_130__session_status({}));if(initial.box.occupied||initial.self.state!=='none')throw Error('Bank occupied');
const launch=parse(await tools.mcp__dayz_mcp_130__dayz_test_run({project:'DayZ_MCP',mode:'server',mission,extra_mods:['@DayZ_Baltic_EV112_MidpointCNavV9'],base_mods:[],no_base_mods:true,no_file_patching:true,build:false,takeover:false,wait_for_box_s:0,navmesh_data_server:false}));
if(launch.status!=='succeeded'||!launch.run_id)throw Error('Launch refused');
const runid=launch.run_id;store('c45Run',runid);let p,problem=null,cleanupProblem=null,close=null;
const event=async(name)=>cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/record_nav_c_event.ps1' -Directory '"+d+"' -RunId '"+runid+"' -Event "+name);
const checked=async()=>{const b=parse(await tools.mcp__dayz_mcp_130__bridge_status({}));const run=b.lifecycle.runs.find(x=>x.run_id===runid);if(!run||run.processes.length!==1||run.processes[0].role!=='server'||run.client_diagnostics.some(x=>x.state!=='not_started'))throw Error('Own server/client identity mismatch');const now=run.processes[0];if(p&&(p.pid!==now.pid||p.creation_time_utc!==now.creation_time_utc))throw Error('Server process changed');return {b,run};};
const beat=async()=>{try{if(!token)throw Error('No lease');parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));}catch(e){await event('HEARTBEAT_ERROR');const s=parse(await tools.mcp__dayz_mcp_130__session_status({}));const own=s.box.runs.find(x=>x.run_id===runid);if(s.self.state!=='none'||s.owner||!own||own.state!=='RUNNING_IDLE')throw Error('Coordination lost; no forced adoption');const a=parse(await tools.mcp__dayz_mcp_130__session_acquire_wait({purpose:'Recuperar solo C45 '+runid,max_wait_s:10}));if(!a.lease_token)throw Error('No own lease');token=a.lease_token;store('c45Lease',token);await checked();await event('LEASE_RECOVERED');}};
try{
 await event('LAUNCHED');const a=parse(await tools.mcp__dayz_mcp_130__session_acquire_wait({purpose:'Verificar C45 '+runid,max_wait_s:10}));if(!a.lease_token)throw Error('No initial own lease');token=a.lease_token;store('c45Lease',token);await beat();
 let bound=false;
 for(let i=0;i<30;i++){const pair=await checked();p=pair.run.processes[0];if(pair.b.server_peer?.binding_state==='BOUND'&&pair.b.server_peer?.run_id===runid&&pair.b.server_peer?.version_state==='ok'){bound=true;break;}await new Promise(x=>setTimeout(x,5000));await beat();}
 if(!bound)throw Error('Bridge readiness deadline');
 await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/capture_owned_server_identity.ps1' -ServerProcessId "+p.pid+" -ExpectedStartUtc '"+p.creation_time_utc+"' -ExpectedMission '"+mission+"' -RunId '"+runid+"' -OutputPath '"+d+"/host-identity.json'");
 await cmd("$ErrorActionPreference='Stop'\n$h=Get-Content -LiteralPath '"+d+"/host-identity.json' -Raw|ConvertFrom-Json\n$x=Get-Content -LiteralPath '"+d+"/deployment.json' -Raw|ConvertFrom-Json\nif($h.navmesh_data_server -or $h.executable_file_sha256 -ne 'a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'){throw 'Wrong mode/executable'}\n$a=@{};foreach($v in $h.package_hashes.PSObject.Properties){$a[[IO.Path]::GetFullPath($v.Name)]=$v.Value}\nif($a.Count -ne 4 -or @($x.packages.PSObject.Properties).Count -ne 4){throw 'Wrong exact package count'}\nforeach($v in $x.packages.PSObject.Properties){if($a[[IO.Path]::GetFullPath($v.Name)] -ne $v.Value){throw 'Wrong exact package identity'}}");
 notify({state:'C45_CAPTURE_STARTED',run_id:runid,pid:p.pid});
 let q=await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/capture_patch_nav_log.ps1' -ServerProcessId "+p.pid+" -ExpectedStartUtc '"+p.creation_time_utc+"' -EngineLog '"+log+"' -OutputDirectory '"+d+"'",1000,true);let rounds=0;
 while(q.session_id){await beat();q=await tools.write_stdin({session_id:q.session_id,chars:'',yield_time_ms:10000,max_output_tokens:1000});if(++rounds>22)throw Error('Capture bound');}
 if(q.exit_code!==0)throw Error(q.output);
 await beat();const {b,run}=await checked();
 await write(d+'/mcp-identity.json',{run_id:runid,processes:run.processes,client_diagnostics:run.client_diagnostics,server_binding:b.server_peer?.binding_state,server_run_id:b.server_peer?.run_id,version:b.server_peer?.version,version_state:b.server_peer?.version_state});
}catch(e){problem=e.message;}
finally{
 try{await beat();const state=parse(await tools.mcp__dayz_mcp_130__session_status({}));if(!state.box.runs.some(x=>x.run_id===runid)||state.self.state!=='active')throw Error('Own live run/lease required for close');await checked();await event('CLOSE_INTENT');close=parse(await tools.mcp__dayz_mcp_130__dayz_test_close({run_id:runid,graceful_timeout_s:20}));if(!close.run_retired)throw Error('Run not retired');}
 catch(e){cleanupProblem=e.message;}
 try{const s=parse(await tools.mcp__dayz_mcp_130__session_status({}));if(token&&s.self.state==='active')parse(await tools.mcp__dayz_mcp_130__session_release({lease_token:token}));token=null;}
 catch(e){cleanupProblem=(cleanupProblem||'')+' Release: '+e.message;}
 try{const after=parse(await tools.mcp__dayz_mcp_130__session_status({}));const own=after.box.runs.some(x=>x.run_id===runid);if(own||after.self.state!=='none'||after.cleanup_degraded.length||after.pending_commands)cleanupProblem=(cleanupProblem||'')+' Incomplete terminal state';await write(d+'/cleanup.json',{close,self:after.self,pending_commands:after.pending_commands,cleanup_degraded:after.cleanup_degraded,box_occupied:after.box.occupied,own_run_present:own,error:problem,cleanup_error:cleanupProblem});}
 catch(e){cleanupProblem=(cleanupProblem||'')+' Final receipt: '+e.message;}
}
try{if(p)await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/copy_owned_server_rpt.ps1' -ExpectedStartUtc '"+p.creation_time_utc+"' -ExpectedMission '"+mission+"' -OutputDirectory '"+d+"'");}
catch(e){cleanupProblem=(cleanupProblem||'')+' RPT: '+e.message;}
notify({state:'C45_CLOSED',run_id:runid,error:problem,cleanup_error:cleanupProblem});
if(problem||cleanupProblem)throw Error((problem||'')+' '+(cleanupProblem||''));
let result=await cmd("& '"+py+"' -I '"+r+"/finish_c45_retry_probe.py'");
while(result.session_id)result=await tools.write_stdin({session_id:result.session_id,chars:'',yield_time_ms:10000,max_output_tokens:3000});
if(result.exit_code!==0)throw Error(result.output);
notify({state:'C45_CONSUMED',run_id:runid,result:result.output});
return {run_id:runid,folder:d};
}

