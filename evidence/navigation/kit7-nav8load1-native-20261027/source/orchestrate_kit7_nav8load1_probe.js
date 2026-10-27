async function probeKit7Nav8Load1(){
const r='E:/DayZ-Baltic-Build/shape-repair-20261025',w='C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c',py='C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe';
const d=r+'/kit7-nav8load1-consumer-20261027',mission='C:\\temp\\DayZ_MCP_130_dev\\mpmissions\\BalticKit7Nav8Load1.BalticTrial',log='C:/temp/DayZ_MCP_130_dev/_server/profiles-130/baltic_kit7_nav_4b29679b-6161-41fb-8f1b-1254bb83aea2.log';
const configLog=log.replace('baltic_kit7_nav_','baltic_nav_config_');
const parse=eval('('+load('parseKit7Mcp')+')');
let token=null;
const cmd=async(s,ms=10000,background=false)=>{let q=await tools.exec_command({cmd:s,workdir:w,login:false,yield_time_ms:ms,max_output_tokens:2000});if(background&&q.session_id)return q;let output=q.output||'';while(q.session_id){if(token)await beat();q=await tools.write_stdin({session_id:q.session_id,chars:'',yield_time_ms:10000,max_output_tokens:2000});output+=q.output||'';}if(q.exit_code!==0)throw Error(output||'Command did not complete successfully');return {...q,output};};
const write=async(path,obj)=>tools.apply_patch('*** Begin Patch\n*** Add File: '+path+'\n+'+JSON.stringify(obj,null,2).replace(/\n/g,'\n+')+'\n*** End Patch');
await cmd("$ErrorActionPreference='Stop'\nif((Test-Path -LiteralPath '"+configLog+"') -or (Test-Path -LiteralPath '"+log+"')){throw 'Fresh log required'}\n$dep=Get-Content -LiteralPath '"+d+"/deployment.json' -Raw|ConvertFrom-Json\n$review=Get-Content -LiteralPath '"+r+"/kit7-nav8load1-code-review-20261027/accepted.json' -Raw|ConvertFrom-Json\nif($review.status -ne 'ACCEPTED_AFTER_REVIEW'){throw 'Review missing'}\n$stock=Get-Content -LiteralPath 'E:/DayZ-Baltic-Build/shape-repair-20261025/kit7-nav8load1-consumer-20261027/vanilla-packages.json' -Raw|ConvertFrom-Json\n$actual=@(Get-ChildItem -LiteralPath $stock.directory -Filter '*.pbo' -File|ForEach-Object {$_.FullName.ToLowerInvariant()}|Sort-Object)\n$expected=@($stock.packages.PSObject.Properties|ForEach-Object {[IO.Path]::GetFullPath($_.Name).ToLowerInvariant()}|Sort-Object)\nif(Compare-Object $actual $expected){throw 'Vanilla inventory drift'}\nforeach($v in @($dep.inputs.PSObject.Properties)+@($review.inputs.PSObject.Properties)){if((Get-FileHash -LiteralPath $v.Name).Hash.ToLowerInvariant() -ne $v.Value){throw 'Frozen probe input drift'}}");
const launch=parse(await tools.mcp__dayz_mcp_130__dayz_test_run({project:'DayZ_MCP',mode:'server',mission,extra_mods:['@DayZ_Baltic_EV112_Kit7Nav8Load1'],base_mods:[],no_base_mods:true,no_file_patching:true,build:false,takeover:false,on_busy:"queue",wait_for_box_s:600,navmesh_data_server:false}));
if(launch.status!=='succeeded'||!launch.run_id)throw Error('Launch refused');
const runid=launch.run_id;store('kit7Nav8Load1ProbeRun',runid);let p,observerSession=null,problem=null,cleanupProblem=null,close=null;
const event=async(name)=>cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/record_nav_c_event.ps1' -Directory '"+d+"' -RunId '"+runid+"' -Event "+name);
const checked=async()=>{const b=parse(await tools.mcp__dayz_mcp_130__bridge_status({}));const run=b.lifecycle.runs.find(x=>x.run_id===runid);if(!run||run.processes.length!==1||run.processes[0].role!=='server'||run.client_diagnostics.some(x=>x.state!=='not_started'))throw Error('Own server/client identity mismatch');const now=run.processes[0];if(p&&(p.pid!==now.pid||p.creation_time_utc!==now.creation_time_utc))throw Error('Server process changed');return {b,run};};
const beat=async()=>{try{if(!token)throw Error('No lease');parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));}catch(e){const s=parse(await tools.mcp__dayz_mcp_130__session_status({}));const own=s.box.runs.find(x=>x.run_id===runid);if(s.self.state!=='none'||s.owner||!own||own.state!=='RUNNING_IDLE')throw Error('Coordination lost; no forced adoption');const a=parse(await tools.mcp__dayz_mcp_130__session_acquire_wait({purpose:'Recuperar solo KIT7_LOAD1_607 '+runid,max_wait_s:10}));if(!a.lease_token)throw Error('No own lease');token=a.lease_token;store('kit7Nav8Load1ProbeLease',token);await checked();await event('LEASE_RECOVERED');}};
try{
 await event('LAUNCHED');const a=parse(await tools.mcp__dayz_mcp_130__session_acquire_wait({purpose:'Verificar KIT7_LOAD1_607 '+runid,max_wait_s:10}));if(!a.lease_token)throw Error('No initial own lease');token=a.lease_token;store('kit7Nav8Load1ProbeLease',token);await beat();
 let bound=false;
 for(let i=0;i<60;i++){const pair=await checked();p=pair.run.processes[0];if(pair.b.server_peer?.binding_state==='BOUND'&&pair.b.server_peer?.run_id===runid&&pair.b.server_peer?.version_state==='ok'){bound=true;break;}await new Promise(x=>setTimeout(x,5000));await beat();}
 if(!bound)throw Error('Bridge readiness deadline');
 await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/capture_owned_server_identity.ps1' -ServerProcessId "+p.pid+" -ExpectedStartUtc '"+p.creation_time_utc+"' -ExpectedMission '"+mission+"' -RunId '"+runid+"' -OutputPath '"+d+"/host-identity.json'");
 await cmd("$ErrorActionPreference='Stop'\n$h=Get-Content -LiteralPath '"+d+"/host-identity.json' -Raw|ConvertFrom-Json\n$x=Get-Content -LiteralPath '"+d+"/deployment.json' -Raw|ConvertFrom-Json\nif($h.navmesh_data_server -or $h.executable_file_sha256 -ne 'a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'){throw 'Wrong mode/executable'}\n$a=@{};foreach($v in $h.package_hashes.PSObject.Properties){$a[[IO.Path]::GetFullPath($v.Name)]=$v.Value}\nif($a.Count -ne 4 -or @($x.packages.PSObject.Properties).Count -ne 4){throw 'Wrong exact package count'}\nforeach($v in $x.packages.PSObject.Properties){if($a[[IO.Path]::GetFullPath($v.Name)] -ne $v.Value){throw 'Wrong exact package identity'}}");

 let observer=await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File './tools/navigation/observe_owned_server_exit.ps1' -TargetProcessId "+p.pid+" -ExpectedStartUtc '"+p.creation_time_utc+"' -ExpectedExecutable 'E:/SteamLibrary/steamapps/common/DayZ Exp/DayZDiag_x64.exe' -OutputDirectory '"+d+"/observer' -MaxSeconds 1200",1000,true);
 observerSession=observer.session_id;if(!observerSession)throw Error('Observer ended before capture');
 await cmd("$ErrorActionPreference='Stop'\n$deadline=[DateTime]::UtcNow.AddSeconds(15)\nwhile(-not(Test-Path -LiteralPath '"+d+"/observer/attached.json')){if([DateTime]::UtcNow -gt $deadline){throw 'Observer attach deadline'};Start-Sleep -Milliseconds 200}\n$a=Get-Content -LiteralPath '"+d+"/observer/attached.json' -Raw|ConvertFrom-Json\nif($a.status -ne 'ATTACHED' -or -not $a.handle_retained -or $a.process_id -ne "+p.pid+"){throw 'Observer identity mismatch'}");
 await event('ATTACHED');
 notify({state:'KIT7_LOAD1_607_CAPTURE_STARTED',run_id:runid,pid:p.pid});
 let q=await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/capture_kit7_nav8load1_logs.ps1' -ServerProcessId "+p.pid+" -ExpectedStartUtc '"+p.creation_time_utc+"' -EngineLog '"+log+"' -ConfigEngineLog '"+configLog+"' -OutputDirectory '"+d+"'",1000,true);let rounds=0;
 while(q.session_id){await beat();q=await tools.write_stdin({session_id:q.session_id,chars:'',yield_time_ms:10000,max_output_tokens:1000});if(++rounds>100)throw Error('Capture bound');}
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
try{if(observerSession){const end=await tools.write_stdin({session_id:observerSession,chars:'',yield_time_ms:10000,max_output_tokens:1000});if(end.session_id||end.exit_code!==0)throw Error('Observer incomplete');}}catch(e){cleanupProblem=(cleanupProblem||'')+' Observer: '+e.message;}
if(close?.run_retired&&!close.already_gone)await event('CLOSED');
notify({state:close?.run_retired?'KIT7_LOAD1_607_CLOSED':'KIT7_LOAD1_607_INCOMPLETE',run_id:runid,error:problem,cleanup_error:cleanupProblem});
if(problem||cleanupProblem)throw Error((problem||'')+' '+(cleanupProblem||''));
let result=await cmd("& '"+py+"' -I '"+r+"/finish_kit7_nav8load1_probe.py'");
while(result.session_id)result=await tools.write_stdin({session_id:result.session_id,chars:'',yield_time_ms:10000,max_output_tokens:3000});
if(result.exit_code!==0)throw Error(result.output);
notify({state:'KIT7_LOAD1_607_CONSUMED',run_id:runid,result:result.output});
return {run_id:runid,folder:d};
}

