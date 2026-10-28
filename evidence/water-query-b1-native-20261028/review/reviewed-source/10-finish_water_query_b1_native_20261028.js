// Executed inside functions.exec; credentials remain in this isolate/store only.
async function finishWaterB1(){
 const root='E:/DayZ-Baltic-Build/shape-repair-20261025',w='C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c',d=root+'/water-query-b1-native-20261028';
 const parse=r=>{if(r.isError)throw Error('MCP tool error');if(r.structuredContent)return r.structuredContent;return JSON.parse(r.content.filter(x=>x.type==='text').map(x=>x.text).join('\n'));};
 const launch=load('waterB1Launch'),runid=launch?.run_id;
 if(launch?.status!=='succeeded'||!runid||!/^[a-f0-9]{64}$/.test(launch.accepted_sha256)||!launch.mission)throw Error('No own sealed B1 launch');
 const quote=s=>"'"+s.replace(/'/g,"''")+"'";
 const write=async(p,value)=>tools.apply_patch('*** Begin Patch\n*** Add File: '+p+'\n+'+JSON.stringify(value,null,2).replace(/\n/g,'\n+')+'\n*** End Patch');
 let token=null,proc=null,adopted=false,problem=null,cleanupError=null,close=null,stop=null,precloseIdentityError=null,deadline=null;
 const beat=async()=>{const x=parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));if(x.error||x.ok===false)throw Error('Heartbeat rejected');};
 const cmd=async(command)=>{await beat();let q=await tools.exec_command({cmd:command,workdir:w,yield_time_ms:1000,max_output_tokens:1200});while(q.session_id){await beat();q=await tools.write_stdin({session_id:q.session_id,chars:'',yield_time_ms:10000,max_output_tokens:1200});}if(q.exit_code!==0)throw Error(q.output);return q;};
 const checked=async()=>{
  const b=parse(await tools.mcp__dayz_mcp_130__bridge_status({})),r=b.lifecycle.runs.find(x=>x.run_id===runid);
  if(!r||r.processes.length!==1||r.processes[0].role!=='server'||r.client_diagnostics.some(x=>x.state!=='not_started'))throw Error('Own server identity mismatch');
  if(proc&&(proc.pid!==r.processes[0].pid||proc.creation_time_utc!==r.processes[0].creation_time_utc))throw Error('Own process identity changed');
  return {b,r};
 };
 const identity=async(name)=>cmd("powershell -NoProfile -ExecutionPolicy Bypass -File "+quote(root+"/capture_owned_server_identity.ps1")+" -ServerProcessId "+proc.pid+" -ExpectedStartUtc "+quote(proc.creation_time_utc)+" -ExpectedMission "+quote(launch.mission)+" -RunId "+quote(runid)+" -OutputPath "+quote(d+"/"+name));
 const frozen=async()=>cmd("$ErrorActionPreference='Stop'\nif((Get-FileHash -LiteralPath "+quote(d+"/accepted.json")+").Hash.ToLowerInvariant() -ne '"+launch.accepted_sha256+"'){throw 'Seal changed'}\n$a=Get-Content -LiteralPath "+quote(d+"/accepted.json")+" -Raw|ConvertFrom-Json\n$x=Get-Content -LiteralPath "+quote(d+"/deployment.json")+" -Raw|ConvertFrom-Json\nforeach($m in @($a.inputs,$x.inputs)){foreach($p in $m.PSObject.Properties){if((Get-FileHash -LiteralPath $p.Name).Hash.ToLowerInvariant() -ne $p.Value){throw 'Frozen input drift'}}}");
 try{
  await write(d+'/launch.json',launch);
  const grant=parse(await tools.mcp__dayz_mcp_130__session_acquire_wait({purpose:'EV112 water B1 own run '+runid,max_wait_s:60}));
  token=grant.lease_token;store('waterB1Lease',token);if(!token)throw Error('No lease grant');
  if(grant.adopted_run?.ok!==true||grant.adopted_run.run_id!==runid)throw Error('Own run not adopted');adopted=true;
  let ready=false;
  for(let i=0;i<60;i++){
   await beat();const {b,r}=await checked();proc=r.processes[0];
   if(b.server_peer?.run_id===runid&&b.server_peer?.binding_state==='BOUND'&&b.server_peer?.version_state==='ok'&&b.server_peer?.last_poll_age_s<10){ready=true;deadline=new Date(Date.now()+180000).toISOString();break;}
   await new Promise(resolve=>setTimeout(resolve,5000));
  }
  if(!ready)throw Error('Own bridge deadline300s');
  await frozen();await identity('host-identity.json');
  await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File "+quote(root+"/capture_water_query_b1_native_20261028.ps1")+" -ServerProcessId "+proc.pid+" -ExpectedStartUtc "+quote(proc.creation_time_utc)+" -OutputDirectory "+quote(d)+" -DeadlineUtc "+quote(deadline));
  await identity('host-after.json');await frozen();
  const {b,r}=await checked();if(b.server_peer?.run_id!==runid||b.server_peer?.binding_state!=='BOUND'||b.server_peer?.version_state!=='ok'||b.server_peer?.last_poll_age_s>=10)throw Error('Bridge binding lost');
  await write(d+'/mcp-identity.json',{run_id:runid,processes:r.processes,client_diagnostics:r.client_diagnostics,server_binding:b.server_peer.binding_state,server_run_id:b.server_peer.run_id,version_state:b.server_peer.version_state,poll_age_s:b.server_peer.last_poll_age_s});
 }catch(e){problem=e.message;}
 finally{
  if(token){
   try{
    if(!adopted)throw Error('Own run not adopted; no close attempted');
    await beat();try{await checked();}catch(e){precloseIdentityError=e.message;}
    await write(d+'/close-intent.json',{run_id:runid,utc:new Date().toISOString(),error:problem,preclose_identity_error:precloseIdentityError});
    const c=parse(await tools.mcp__dayz_mcp_130__dayz_test_close({run_id:runid,graceful_timeout_s:20}));
    close={run_id:c.run_id,run_retired:c.run_retired,stop_required:c.stop_required};
    if(!c.run_retired&&!c.stop_required)throw Error('Run not retired without stop instruction');
   }catch(e){cleanupError=e.message;}
   try{const s=parse(await tools.mcp__dayz_mcp_130__session_status({}));if(s.self.state==='active')parse(await tools.mcp__dayz_mcp_130__session_release({lease_token:token}));store('waterB1Lease',null);}catch(e){cleanupError=(cleanupError||'')+' release '+e.message;}
   if(adopted&&close?.stop_required&&!close.run_retired&&!cleanupError){
    try{const v=parse(await tools.mcp__dayz_mcp_130__dayz_test_stop({run_id:runid}));stop={run_id:v.run_id,status:v.status};if(v.run_id!==runid||v.status!=='succeeded')throw Error('Official stop failed');}catch(e){cleanupError=e.message;}
   }
  }else cleanupError='Lease/adoption failed; own run not closed, no takeover';
  const s=parse(await tools.mcp__dayz_mcp_130__session_status({})),own=s.box.runs.some(x=>x.run_id===runid);
  if(own||s.self.state!=='none'||s.pending_commands||s.cleanup_degraded.length)cleanupError=(cleanupError||'')+' terminal state incomplete';
  await write(d+'/cleanup.json',{close,stop,self:{state:s.self.state},own_run_present:own,pending_commands:s.pending_commands,cleanup_degraded:s.cleanup_degraded,error:problem,cleanup_error:cleanupError,preclose_identity_error:precloseIdentityError});
  if(!cleanupError)store('waterB1Launch',null);
 }
 if(problem||cleanupError)throw Error((problem||'')+' '+(cleanupError||''));
 return {run_id:runid,folder:d,closed:true};
}
