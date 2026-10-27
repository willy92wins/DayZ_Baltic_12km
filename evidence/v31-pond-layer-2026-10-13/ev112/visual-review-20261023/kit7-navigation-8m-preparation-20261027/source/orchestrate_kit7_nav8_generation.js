async function generateKit7Nav8(){
const r='E:/DayZ-Baltic-Build/shape-repair-20261025',w='C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c',py='C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe';
const d=r+'/nav-kit7-8m-preparation-20261027',out=r+'/navmesh-kit7-8m-v9-20261027',mission='C:\\temp\\DayZ_MCP_130_dev\\mpmissions\\BalticKit7NavData.BalticTrial';
const parse=eval('('+load('parseKit7Mcp')+')');
let token=null;
const cmd=async(s,ms=10000,max=1800,background=false)=>{let q=await tools.exec_command({cmd:s,workdir:w,yield_time_ms:ms,max_output_tokens:max});if(background&&q.session_id)return q;let output=q.output||'';while(q.session_id){if(token)parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));q=await tools.write_stdin({session_id:q.session_id,chars:'',yield_time_ms:10000,max_output_tokens:max});output+=q.output||'';}if(q.exit_code!==0)throw Error(output||'Command did not complete successfully');return {...q,output};};
const read=async(path)=>JSON.parse((await cmd("Get-Content -LiteralPath '"+path+"' -Raw",10000,9000)).output);
const exists=async(path)=>(await cmd("Test-Path -LiteralPath '"+path+"'")).output.trim()==='True';
const write=async(path,obj)=>tools.apply_patch('*** Begin Patch\n*** Add File: '+path+'\n+'+JSON.stringify(obj,null,2).replace(/\n/g,'\n+')+'\n*** End Patch');
const prepared=JSON.parse((await cmd("Get-Content -LiteralPath '"+d+"/launch-inputs.json' -Raw | ConvertFrom-Json | Select-Object status,observer_sha256,packages | ConvertTo-Json -Depth 6",10000,3000)).output);if(prepared.status!=='READY_AFTER_CODE_REVIEW')throw Error('Code gate missing');
await cmd("$ErrorActionPreference='Stop'\nif(Test-Path -LiteralPath '"+out+"'){throw 'Attempt already exists'}\n$dep=Get-Content -LiteralPath '"+d+"/launch-inputs.json' -Raw|ConvertFrom-Json\nforeach($v in $dep.inputs.PSObject.Properties){if((Get-FileHash -LiteralPath $v.Name).Hash.ToLowerInvariant() -ne $v.Value){throw 'Generation input drift'}}");
const physical=await read(r+'/kit7-overlap-native-20261026/full/result.json');if(physical.status!=='SERVER_PROBE_PASS'||physical.points!==6801||!physical.identity_bound||!physical.inputs_unchanged)throw Error('Kit7 physical gate missing');
const packageMap=value=>{const out={};for(const [path,hash] of Object.entries(value||{})){const key=path.replaceAll('\\','/').toLowerCase();if(!/^[a-z]:\//.test(key)||key.split('/').includes('..')||Object.hasOwn(out,key))throw Error('Invalid or duplicate package path');out[key]=hash;}return out;};
const requiredPackages={
 'p:/mods/@dayz_baltic_ev112_kit7nav8input/addons/narva_trial.pbo':'9fbc7608dc407b8b90c7809071aa01f4c27082e6943b293d58d09cb4fd451b49',
 'p:/mods/@dayz_baltic_ev112_kit7nav8input/addons/baltic_water_v30.pbo':'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43',
 'p:/mods/@dayz_baltic_ev112_kit7nav8input/addons/baltic_stream_pilot.pbo':'3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6',
 'p:/mods/@dayz_mcp/addons/dayz_mcp.pbo':'7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'};
const physicalRequiredPackages={
 'p:/mods/@dayz_baltic_ev112_kit7overlap/addons/narva_trial.pbo':'10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc',
 'p:/mods/@dayz_baltic_ev112_kit7overlap/addons/baltic_water_v30.pbo':'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43',
 'p:/mods/@dayz_baltic_ev112_kit7overlap/addons/baltic_stream_pilot.pbo':'3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6',
 'p:/mods/@dayz_mcp/addons/dayz_mcp.pbo':'7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'};
const frozenPackages=packageMap(prepared.packages),physicalPackages=packageMap(physical.packages);
if(physical.failure_count!==0||physical.engine_sha256!=='a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'||Object.keys(frozenPackages).length!==4||Object.entries(requiredPackages).some(([path,hash])=>frozenPackages[path]!==hash)||Object.keys(physicalPackages).length!==4||Object.entries(physicalRequiredPackages).some(([path,hash])=>physicalPackages[path]!==hash))throw Error('Kit7 physical package binding missing');
const launch=parse(await tools.mcp__dayz_mcp_130__dayz_test_run({project:'DayZ_MCP',mode:'server',mission,extra_mods:['@DayZ_Baltic_EV112_Kit7Nav8Input'],base_mods:[],no_base_mods:true,no_file_patching:true,build:false,takeover:false,on_busy:'queue',wait_for_box_s:600,navmesh_data_server:true}));
if(launch.status!=='succeeded'||!launch.run_id)throw Error('Launch not successful');
const runid=launch.run_id;let p,genSession,observerSession,genDone=false,problem=null,cleanupProblem=null,close=null,preserveForRecovery=false,generatorFinished=null;
store('navKit7EightRun',runid);
const event=async(name)=>cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/record_nav_c_event.ps1' -Directory '"+d+"' -RunId '"+runid+"' -Event "+name);
const checkedBridge=async()=>{const b=parse(await tools.mcp__dayz_mcp_130__bridge_status({}));const run=b.lifecycle.runs.find(x=>x.run_id===runid);if(!run||run.processes.length!==1||run.processes[0].role!=='server'||run.client_diagnostics.some(x=>x.state!=='not_started'))throw Error('Owned server identity/client state lost');if(p&&(run.processes[0].pid!==p.pid||run.processes[0].creation_time_utc!==p.creation_time_utc))throw Error('Server process changed');return {b,run};};
const beat=async()=>{
 try {parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));}
 catch(e){
  await event('HEARTBEAT_ERROR');const state=parse(await tools.mcp__dayz_mcp_130__session_status({}));const own=state.box.runs.find(x=>x.run_id===runid);
  if(state.self.state!=='none'||state.owner||!own||own.state!=='RUNNING_IDLE')throw Error('Coordination lost; no forced adoption');
  const a=parse(await tools.mcp__dayz_mcp_130__session_acquire_wait({purpose:'Recuperar solo nuestra generación kit7 '+runid,max_wait_s:10}));if(!a.lease_token)throw Error('Own run not adopted');token=a.lease_token;store('navKit7EightLease',token);
  await checkedBridge();await event('LEASE_RECOVERED');
 }
};
const snapshot=async(name)=>{const {b,run}=await checkedBridge();if(b.server_peer?.binding_state!=='BOUND'||b.server_peer?.run_id!==runid||b.server_peer?.version_state!=='ok')throw Error('Server bridge not bound');await write(d+'/'+name,{run_id:runid,processes:run.processes,client_diagnostics:run.client_diagnostics,server_binding:b.server_peer.binding_state,server_run_id:b.server_peer.run_id,version:b.server_peer.version,version_state:b.server_peer.version_state});return run;};
try {
 await event('LAUNCHED');const a=parse(await tools.mcp__dayz_mcp_130__session_acquire_wait({purpose:'EV112 kit7: navegación propia tras gate físico, máximo18000s, sin cliente',max_wait_s:10}));if(!a.lease_token)throw Error('No lease');token=a.lease_token;store('navKit7EightLease',token);
 await beat();let bound=false;
 for(let i=0;i<30;i++){const pair=await checkedBridge();p=pair.run.processes[0];if(pair.b.server_peer?.binding_state==='BOUND'&&pair.b.server_peer?.run_id===runid&&pair.b.server_peer?.version_state==='ok'){bound=true;break;}await new Promise(x=>setTimeout(x,5000));await beat();}
 if(!bound)throw Error('Bridge readiness deadline');await snapshot('mcp-before.json');
 await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/capture_owned_server_identity.ps1' -ServerProcessId "+p.pid+" -ExpectedStartUtc '"+p.creation_time_utc+"' -ExpectedMission '"+mission+"' -RunId '"+runid+"' -OutputPath '"+d+"/host-identity.json'");
 await cmd("$ErrorActionPreference='Stop'\n$h=Get-Content -LiteralPath '"+d+"/host-identity.json' -Raw|ConvertFrom-Json\n$i=Get-Content -LiteralPath '"+d+"/launch-inputs.json' -Raw|ConvertFrom-Json\nif(-not $h.navmesh_data_server -or $h.executable_file_sha256 -ne 'a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'){throw 'Wrong engine identity/mode'}\nif(@($h.package_hashes.PSObject.Properties).Count -ne 4){throw 'Unexpected package set'}\n$hh=@{};foreach($item in $h.package_hashes.PSObject.Properties){$key=[IO.Path]::GetFullPath($item.Name).ToLowerInvariant();if($hh.ContainsKey($key)){throw 'Duplicate host package path'};$hh[$key]=$item.Value}\nforeach($v in $i.packages.PSObject.Properties){if($hh[[IO.Path]::GetFullPath($v.Name).ToLowerInvariant()] -ne $v.Value){throw 'Loaded stack mismatch'}}");
 let obs=await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File './tools/navigation/observe_owned_server_exit.ps1' -TargetProcessId "+p.pid+" -ExpectedStartUtc '"+p.creation_time_utc+"' -ExpectedExecutable 'E:/SteamLibrary/steamapps/common/DayZ Exp/DayZDiag_x64.exe' -OutputDirectory '"+d+"/observer' -MaxSeconds 18300",1000,1800,true);observerSession=obs.session_id;
 for(let i=0;i<15&&!await exists(d+'/observer/attached.json');i++){if(await exists(d+'/observer/terminal.json'))throw Error('Observer attach failed');await beat();await new Promise(x=>setTimeout(x,1000));}
 const attached=await read(d+'/observer/attached.json');
 if(attached.status!=='ATTACHED'||!attached.handle_retained||attached.process_id!==p.pid||Math.abs(Date.parse(attached.start_utc)-Date.parse(p.creation_time_utc))>2||attached.observer_sha256!==prepared.observer_sha256||attached.executable_sha256!=='a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d')throw Error('Observer identity mismatch');
 await event('ATTACHED');await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/bind_nav_c_rpt_clock.ps1' -ExpectedStartUtc '"+p.creation_time_utc+"' -ExpectedMission '"+mission+"' -OutputPath '"+d+"/clock-binding.json'");
 let q=await cmd("& '"+py+"' -I './tools/navigation/generate_navmesh_console.py' --run-id '"+runid+"' --world-pbo 'P:/Mods/@DayZ_Baltic_EV112_Kit7Nav8Input/Addons/narva_trial.pbo' --world-sha256 9fbc7608dc407b8b90c7809071aa01f4c27082e6943b293d58d09cb4fd451b49 --water-pbo 'P:/Mods/@DayZ_Baltic_EV112_Kit7Nav8Input/Addons/baltic_water_v30.pbo' --water-sha256 97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43 --additional-pbo 'P:/Mods/@DayZ_Baltic_EV112_Kit7Nav8Input/Addons/baltic_stream_pilot.pbo' 3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6 --out '"+out+"' --timeout-s 18000",1000,1800,true);
 genSession=q.session_id;store('navKit7EightGeneratorSession',genSession);store('navKit7EightObserverSession',observerSession);if(!genSession)throw Error('Generator ended before observation');
 let captured=false;
 for(let i=0;i<24&&!captured;i++){
  try {await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/capture_nav_c_generator.ps1' -RunId '"+runid+"' -ServerStartUtc '"+p.creation_time_utc+"' -GenerationDirectory '"+out+"' -OutputPath '"+d+"/generator-identity.json'");captured=true;}
  catch(e){
   if(!/Exactly one generator child/.test(e.message))throw e;
   q=await tools.write_stdin({session_id:genSession,chars:'',yield_time_ms:5000,max_output_tokens:800});await beat();
   if(!q.session_id){generatorFinished=q;if(q.exit_code===0&&(await read(out+'/generation.json')).status==='GENERATED_FILE_PENDING_STRUCTURAL_AND_ENGINE_VALIDATION')genDone=true;throw Error('Wrapper ended before generator identity capture');}
  }
 }
 if(!captured)throw Error('Generator identity capture deadline');
 await event('GENERATOR_STARTED');notify({state:'KIT7_NAV_GENERATING',run_id:runid,pid:p.pid,generator_session:genSession,observer_session:observerSession,output:out});
 let rounds=0;const deadline=Date.now()+18300e3;
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
