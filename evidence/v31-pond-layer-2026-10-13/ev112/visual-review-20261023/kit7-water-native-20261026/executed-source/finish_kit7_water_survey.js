async function finishKit7Water(kind,count){
const parse=eval("("+load("parseKit7Mcp")+")"),root="E:/DayZ-Baltic-Build/shape-repair-20261025",d=root+"/kit7-water-native-20261026/"+kind,w="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c";
const mission="C:\\temp\\DayZ_MCP_130_dev\\mpmissions\\"+(kind==="full"?"BalticKit7Water":"BalticKit7Calibration")+".BalticTrial";
const runid=load("kit7NativeRun"),token=load("kit7NativeLease");let proc,problem=null,cleanupError=null,close=null;
const write=async(path,obj)=>tools.apply_patch("*** Begin Patch\n*** Add File: "+path+"\n+"+JSON.stringify(obj,null,2).replace(/\n/g,"\n+")+"\n*** End Patch");
const beat=async()=>parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));
const cmd=async(cmd)=>{let q=await tools.exec_command({cmd,workdir:w,yield_time_ms:1000,max_output_tokens:1600});let progress=0;while(q.session_id){if(++progress%5===0)notify({state:'MEASUREMENT_RUNNING',kind,run_id:runid,elapsed_poll_s:progress*10});await beat();q=await tools.write_stdin({session_id:q.session_id,chars:"",yield_time_ms:10000,max_output_tokens:1600});}if(q.exit_code!==0)throw Error(q.output);return q;};
const checked=async()=>{const b=parse(await tools.mcp__dayz_mcp_130__bridge_status({}));const r=b.lifecycle.runs.find(x=>x.run_id===runid);if(!r||r.processes.length!==1||r.processes[0].role!=="server"||r.client_diagnostics.some(x=>x.state!=="not_started"))throw Error("Own server identity mismatch");if(proc&&(proc.pid!==r.processes[0].pid||proc.creation_time_utc!==r.processes[0].creation_time_utc))throw Error("Process changed");return {b,r};};
try{
 await beat();let ready=false;
 for(let i=0;i<60;i++){const {b,r}=await checked();proc=r.processes[0];if(b.server_peer?.run_id===runid&&b.server_peer?.binding_state==="BOUND"&&b.server_peer?.version_state==="ok"&&b.server_peer?.last_poll_age_s<10){ready=true;break;}if(i%9===0)notify({state:"WAITING_OWN_BRIDGE",kind,seconds:i*5});await new Promise(x=>setTimeout(x,5000));await beat();}
 if(!ready)throw Error("Bridge deadline");
 await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+root+"/capture_owned_server_identity.ps1' -ServerProcessId "+proc.pid+" -ExpectedStartUtc '"+proc.creation_time_utc+"' -ExpectedMission '"+mission+"' -RunId '"+runid+"' -OutputPath '"+d+"/host-identity.json'");
 await cmd("$ErrorActionPreference='Stop'\n$h=Get-Content -LiteralPath '"+d+"/host-identity.json' -Raw|ConvertFrom-Json\n$x=Get-Content -LiteralPath '"+root+"/kit7-water-native-20261026/deployment.json' -Raw|ConvertFrom-Json\n$p=Get-Content -LiteralPath '"+root+"/kit7-water-native-20261026/prelaunch.json' -Raw|ConvertFrom-Json\nif(-not $h.navmesh_data_server -or $h.executable_file_sha256 -ne $p.executable_sha256){throw 'Wrong engine/mode'}\n$a=@{};foreach($v in $h.package_hashes.PSObject.Properties){$a[[IO.Path]::GetFullPath($v.Name)]=$v.Value}\nif($a.Count -ne 4){throw 'Wrong loaded package count'}\nforeach($v in $x.deployed.PSObject.Properties){if($a[[IO.Path]::GetFullPath($v.Name)] -ne $v.Value){throw 'Wrong map package'}}\nif($a[[IO.Path]::GetFullPath($p.bridge_pbo)] -ne $p.bridge_sha256){throw 'Wrong bridge package'}\nforeach($v in $x.inputs.PSObject.Properties){if((Get-FileHash -LiteralPath $v.Name).Hash.ToLowerInvariant() -ne $v.Value){throw 'Frozen input drift'}}");
 notify({state:"MEASURING_NATIVE",kind,run_id:runid,pid:proc.pid,count});
 await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+root+"/capture_kit7_water_log.ps1' -ServerProcessId "+proc.pid+" -ExpectedStartUtc '"+proc.creation_time_utc+"' -Kind '"+kind+"' -OutputDirectory '"+d+"'");
 await beat();const {b,r}=await checked();if(b.server_peer.run_id!==runid||b.server_peer.binding_state!=="BOUND"||b.server_peer.version_state!=="ok"||b.server_peer.last_poll_age_s>=10)throw Error("Fresh bridge binding lost");
 await write(d+"/mcp-identity.json",{run_id:runid,processes:r.processes,client_diagnostics:r.client_diagnostics,server_binding:b.server_peer.binding_state,server_run_id:b.server_peer.run_id,version:b.server_peer.version,version_state:b.server_peer.version_state,poll_age_s:b.server_peer.last_poll_age_s});
 await write(d+"/launch.json",load("kit7WaterLaunch_"+kind));
}catch(e){problem=e.message;}
finally{
 try{await beat();const s=parse(await tools.mcp__dayz_mcp_130__session_status({}));if(s.self.state!=="active"||!s.box.runs.some(x=>x.run_id===runid))throw Error("No own lease/live run for close");await checked();await write(d+"/close-intent.json",{run_id:runid,utc:new Date().toISOString(),reason:"Survey finished or failed",error:problem});close=parse(await tools.mcp__dayz_mcp_130__dayz_test_close({run_id:runid,graceful_timeout_s:20}));if(!close.run_retired)throw Error("Run not retired");}
 catch(e){cleanupError=e.message;}
 try{const s=parse(await tools.mcp__dayz_mcp_130__session_status({}));if(s.self.state==="active")parse(await tools.mcp__dayz_mcp_130__session_release({lease_token:token}));store("kit7NativeLease",null);}catch(e){cleanupError=(cleanupError||"")+" release "+e.message;}
 const s=parse(await tools.mcp__dayz_mcp_130__session_status({}));const own=s.box.runs.some(x=>x.run_id===runid);if(own||s.self.state!=="none"||s.pending_commands||s.cleanup_degraded.length)cleanupError=(cleanupError||"")+" terminal state incomplete";
 await write(d+"/cleanup.json",{close,self:s.self,own_run_present:own,box_occupied:s.box.occupied,pending_commands:s.pending_commands,cleanup_degraded:s.cleanup_degraded,error:problem,cleanup_error:cleanupError});
}
if(proc)await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+root+"/copy_owned_server_rpt.ps1' -ExpectedStartUtc '"+proc.creation_time_utc+"' -ExpectedMission '"+mission+"' -OutputDirectory '"+d+"'");
notify({state:"SURVEY_CLOSED",kind,error:problem,cleanup_error:cleanupError});
if(problem||cleanupError)throw Error((problem||"")+" "+(cleanupError||""));
return {kind,run_id:runid,folder:d};
}
