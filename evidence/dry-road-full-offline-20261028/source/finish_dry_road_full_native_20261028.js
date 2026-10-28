async function finishDryRoadFull(mode) {
 const root='E:/DayZ-Baltic-Build/shape-repair-20261025',w='C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c';
 if(!['calibration','probe'].includes(mode))throw Error('Invalid unit');
 const folder=root+'/dry-road-full-native-20261028',d=folder+'/'+mode,mission='C:/temp/DayZ_MCP_130_dev/mpmissions/'+(mode==='calibration'?'BalticDryRoadCal.BalticTrial':'BalticDryRoadFull.BalticTrial');
 const parse=r=>{if(r.isError)throw Error('MCP tool error');if(r.structuredContent)return r.structuredContent;return JSON.parse(r.content.filter(x=>x.type==='text').map(x=>x.text).join('\n'));};
 const launch=load('dryRoadFullLaunch_'+mode),runid=launch?.run_id;if(launch?.status!=='succeeded'||!runid||launch.mode!==mode||!/^[a-f0-9]{64}$/.test(launch.accepted_sha256)||mode==='probe'&&!/^[a-f0-9]{64}$/.test(launch.calibration_sha256))throw Error('No own admitted sealed unit');
 let token=null,proc=null,problem=null,cleanupError=null,close=null,adopted=false,precloseIdentityError=null;
 const write=async(p,value)=>tools.apply_patch('*** Begin Patch\n*** Add File: '+p+'\n+'+JSON.stringify(value,null,2).replace(/\n/g,'\n+')+'\n*** End Patch');
 const beat=async()=>{const x=parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));if(x.error||x.ok===false)throw Error('Heartbeat rejected');};
 const cmd=async(command)=>{await beat();let q=await tools.exec_command({cmd:command,workdir:w,yield_time_ms:1000,max_output_tokens:1500});while(q.session_id){await beat();q=await tools.write_stdin({session_id:q.session_id,chars:'',yield_time_ms:10000,max_output_tokens:1500});}if(q.exit_code!==0)throw Error(q.output);return q;};
 const checked=async()=>{const b=parse(await tools.mcp__dayz_mcp_130__bridge_status({}));const r=b.lifecycle.runs.find(x=>x.run_id===runid);if(!r||r.processes.length!==1||r.processes[0].role!=='server'||r.client_diagnostics.some(x=>x.state!=='not_started'))throw Error('Own server identity mismatch');if(proc&&(proc.pid!==r.processes[0].pid||proc.creation_time_utc!==r.processes[0].creation_time_utc))throw Error('Own process identity changed');return {b,r};};
 try{
  await write(d+'/launch.json',launch);
  const grant=parse(await tools.mcp__dayz_mcp_130__session_acquire_wait({purpose:'EV112 full dry Roadway own run '+runid,max_wait_s:60}));
  token=grant.lease_token;store('dryRoadFullLease_'+mode,token);if(!token)throw Error('No lease grant');
  if(grant.adopted_run?.ok!==true||grant.adopted_run.run_id!==runid)throw Error('Own run not adopted');adopted=true;
  // The lifecycle lookup below binds exactly the run admitted by our launch;
  // no mutation/close is allowed for a different run.
  await beat();let ready=false;
  for(let i=0;i<60;i++){
   const {b,r}=await checked();proc=r.processes[0];
   if(b.server_peer?.run_id===runid&&b.server_peer?.binding_state==='BOUND'&&b.server_peer?.version_state==='ok'&&b.server_peer?.last_poll_age_s<10){ready=true;break;}
   await new Promise(resolve=>setTimeout(resolve,5000));await beat();
  }
  if(!ready)throw Error('Own bridge deadline300s');
  await cmd("$ErrorActionPreference='Stop'\nif((Get-FileHash -LiteralPath '"+folder+"/accepted.json').Hash.ToLowerInvariant() -ne '"+launch.accepted_sha256+"'){throw 'Launch seal changed'}"+(mode==='probe'?"\nif((Get-FileHash -LiteralPath '"+folder+"/calibration/result.json').Hash.ToLowerInvariant() -ne '"+launch.calibration_sha256+"'){throw 'Launch calibration changed'}":""));
  await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+root+"/capture_owned_server_identity.ps1' -ServerProcessId "+proc.pid+" -ExpectedStartUtc '"+proc.creation_time_utc+"' -ExpectedMission '"+mission+"' -RunId '"+runid+"' -OutputPath '"+d+"/host-identity.json'");
  await cmd("$ErrorActionPreference='Stop'\n$h=Get-Content -LiteralPath '"+d+"/host-identity.json' -Raw|ConvertFrom-Json\n$x=Get-Content -LiteralPath '"+folder+"/deployment.json' -Raw|ConvertFrom-Json\n$p=Get-Content -LiteralPath '"+folder+"/prelaunch.json' -Raw|ConvertFrom-Json\nif(-not $h.navmesh_data_server -or $h.executable_file_sha256 -ne $p.executable_sha256){throw 'Wrong engine/mode'}\n$a=@{};foreach($v in $h.package_hashes.PSObject.Properties){$a[[IO.Path]::GetFullPath($v.Name)]=$v.Value}\nif($a.Count -ne 4){throw 'Wrong loaded package count'}\nforeach($v in $x.deployed.PSObject.Properties){if($a[[IO.Path]::GetFullPath($v.Name)] -ne $v.Value){throw 'Wrong map package'}}\nif($a[[IO.Path]::GetFullPath($p.bridge_pbo)] -ne $p.bridge_sha256){throw 'Wrong bridge package'}\nforeach($v in $x.inputs.PSObject.Properties){if((Get-FileHash -LiteralPath $v.Name).Hash.ToLowerInvariant() -ne $v.Value){throw 'Frozen input drift'}}");
  await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+root+"/capture_dry_road_full_native_20261028.ps1' -ServerProcessId "+proc.pid+" -ExpectedStartUtc '"+proc.creation_time_utc+"' -OutputDirectory '"+d+"' -Mode '"+mode+"'");
  const {b,r}=await checked();if(b.server_peer?.run_id!==runid||b.server_peer?.binding_state!=='BOUND'||b.server_peer?.version_state!=='ok'||b.server_peer?.last_poll_age_s>=10)throw Error('Bridge binding lost');
  await write(d+'/mcp-identity.json',{run_id:runid,processes:r.processes,client_diagnostics:r.client_diagnostics,server_binding:b.server_peer.binding_state,server_run_id:b.server_peer.run_id,version_state:b.server_peer.version_state,poll_age_s:b.server_peer.last_poll_age_s});
 }catch(e){problem=e.message;}
 finally{
  if(token){
   try{if(!adopted)throw Error('Own run not adopted; no close attempted');await beat();try{await checked();}catch(e){precloseIdentityError=e.message;}await write(d+'/close-intent.json',{run_id:runid,utc:new Date().toISOString(),error:problem,preclose_identity_error:precloseIdentityError});close=parse(await tools.mcp__dayz_mcp_130__dayz_test_close({run_id:runid,graceful_timeout_s:20}));if(!close.run_retired)throw Error('Run not retired');}catch(e){cleanupError=e.message;}
   try{const s=parse(await tools.mcp__dayz_mcp_130__session_status({}));if(s.self.state==='active')parse(await tools.mcp__dayz_mcp_130__session_release({lease_token:token}));store('dryRoadFullLease_'+mode,null);}catch(e){cleanupError=(cleanupError||'')+' release '+e.message;}
  }else cleanupError='Lease/adoption failed; own run not closed, do not take over';
  const s=parse(await tools.mcp__dayz_mcp_130__session_status({}));const own=s.box.runs.some(x=>x.run_id===runid);if(own||s.self.state!=='none'||s.pending_commands||s.cleanup_degraded.length)cleanupError=(cleanupError||'')+' terminal state incomplete';
  await write(d+'/cleanup.json',{close,self:s.self,own_run_present:own,pending_commands:s.pending_commands,cleanup_degraded:s.cleanup_degraded,error:problem,cleanup_error:cleanupError,preclose_identity_error:precloseIdentityError});
  if(!cleanupError)store('dryRoadFullLaunch_'+mode,null);
 }
 if(problem||cleanupError)throw Error((problem||'')+' '+(cleanupError||''));
 return {run_id:runid,folder:d,closed:true};
}
