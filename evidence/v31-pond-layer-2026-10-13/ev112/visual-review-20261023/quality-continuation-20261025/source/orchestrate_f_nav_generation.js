async function generateFNavigation(){
const r="E:/DayZ-Baltic-Build/shape-repair-20261025",w="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c",py="C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe",prep=r+"/f-nav-data-preparation",out=r+"/navmesh-rectangle-f-v9",mission="C:\\temp\\DayZ_MCP_130_dev\\mpmissions\\BalticPatchFNavData.BalticTrial";
if(!load("patchNavCodeReviewAccepted"))throw Error("Review missing");
const parse=x=>x.structuredContent??JSON.parse(x.content.find(c=>c.type==="text"&&c.text.trimStart().startsWith("{")).text);
const cmd=async(s,t=1000)=>{const x=await tools.exec_command({cmd:s,workdir:w,max_output_tokens:1200,yield_time_ms:t});if(x.exit_code!=null&&x.exit_code!==0)throw Error(x.output);return x;};
const write=async(path,j)=>tools.apply_patch("*** Begin Patch\n*** Add File: "+path+"\n+"+JSON.stringify(j,null,2).replace(/\n/g,"\n+")+"\n*** End Patch");
await cmd("$ErrorActionPreference='Stop'\nif(Test-Path -LiteralPath '"+out+"'){throw 'Generation attempt/output already exists'}\nif(-not(Test-Path -LiteralPath '"+r+"/patch-nav-e45/result.json')){throw 'E45 baseline capture missing'}\n$dep=Get-Content -LiteralPath '"+prep+"/inputs.json' -Raw|ConvertFrom-Json\nforeach($v in $dep.inputs.PSObject.Properties){if((Get-FileHash -LiteralPath $v.Name).Hash.ToLowerInvariant() -ne $v.Value){throw 'Frozen generation input drift'}}");
const status=parse(await tools.mcp__dayz_mcp_130__session_status({}));if(status.box.occupied||status.self.state!=="none")throw Error("Bank occupied");
const args={project:"DayZ_MCP",mode:"server",mission,extra_mods:["@DayZ_Baltic_EV112_RectangleF"],base_mods:[],no_base_mods:true,no_file_patching:true,build:false,takeover:false,wait_for_box_s:0,navmesh_data_server:true};
const launch=parse(await tools.mcp__dayz_mcp_130__dayz_test_run(args));
if(launch.status!=="succeeded"||!launch.run_id)throw Error("Launch refused: "+launch.status+" "+launch.error_code);
store("fNavDataRun",launch.run_id);
const a=parse(await tools.mcp__dayz_mcp_130__session_acquire_wait({purpose:"EV112 generación NM propia de F, un intento máximo7200s",max_wait_s:10}));
if(!a.lease_token)throw Error("No generation lease");
store("fNavDataLease",a.lease_token);
const beat=async()=>{const x=parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:a.lease_token}));if(x.ok===false||x.error)throw Error("Heartbeat failed");};
let p,problem,gen;
try {
 await beat();let b,run;
 for(let i=0;i<30;i++){
  b=parse(await tools.mcp__dayz_mcp_130__bridge_status({}));run=b.lifecycle.runs.find(x=>x.run_id===launch.run_id);
  if(b.server_peer?.binding_state==="BOUND"&&b.server_peer?.run_id===launch.run_id&&b.server_peer?.version_state==="ok")break;
  if(i===29)throw Error("Data server not bound within150s");
  await new Promise(resolve=>setTimeout(resolve,5000));await beat();
 }
 p=run?.processes?.find(x=>x.role==="server");if(!p||run.processes.length!==1)throw Error("Expected one owned data server");
 store("fNavDataProcess",p);
 await write(prep+"/mcp-before.json",{run_id:launch.run_id,processes:run.processes,client_diagnostics:run.client_diagnostics,server_binding:b.server_peer.binding_state,server_run_id:b.server_peer.run_id,version:b.server_peer.version,version_state:b.server_peer.version_state});
 await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/capture_owned_server_identity.ps1' -ServerProcessId "+p.pid+" -ExpectedStartUtc '"+p.creation_time_utc+"' -ExpectedMission '"+mission+"' -RunId '"+launch.run_id+"' -OutputPath '"+prep+"/host-identity.json'",10000);
 await cmd("$ErrorActionPreference='Stop'\n$h=Get-Content -LiteralPath '"+prep+"/host-identity.json' -Raw|ConvertFrom-Json\n$f=Get-Content -LiteralPath '"+r+"/f-nav-generation-inputs.json' -Raw|ConvertFrom-Json\nif(-not $h.navmesh_data_server -or $h.executable_file_sha256 -ne 'a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'){throw 'Wrong data server mode/executable'}\nforeach($v in $f.inputs.PSObject.Properties){if($h.package_hashes.($v.Name) -ne $v.Value){throw 'Loaded generation package mismatch'}}\nif(@($h.package_hashes.PSObject.Properties).Count -ne 4){throw 'Unexpected generation packages'}");
 let q=await cmd("& '"+py+"' -I './tools/navigation/generate_navmesh_console.py' --run-id '"+launch.run_id+"' --world-pbo 'P:/Mods/@DayZ_Baltic_EV112_RectangleF/Addons/narva_trial.pbo' --world-sha256 4e5f909d2a27e9322299d751d2d54d67f5cc06700499d0498e533b5e1674ef38 --water-pbo 'P:/Mods/@DayZ_Baltic_EV112_RectangleF/Addons/baltic_water_v30.pbo' --water-sha256 97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43 --additional-pbo 'P:/Mods/@DayZ_Baltic_EV112_RectangleF/Addons/baltic_stream_pilot.pbo' c0be9abc9d36ee19c636325b825dbf09880a9dc31b5dfb8432e0f91d0e1cfa87 --out '"+out+"' --timeout-s 7200");
 gen=q.session_id;store("fNavGeneratorSession",gen);
 notify({state:"F_NAV_GENERATING",run_id:launch.run_id,pid:p.pid,exec_session:gen,output:out});
 let rounds=0;
 while(q.session_id){
  await beat();q=await tools.write_stdin({session_id:gen,chars:"",yield_time_ms:10000,max_output_tokens:1000});
  rounds++;
  if(rounds%6===0){
   const progress=await cmd("Get-Content -LiteralPath '"+out+"/generator.stdout.log' -Tail 2",10000);
   notify({state:"F_NAV_GENERATING",poll_seconds:rounds*10,progress:progress.output.slice(-800)});
  }
  if(rounds>780)throw Error("Generator exceeded wrapper duration");
 }
 if(q.exit_code!==0)problem="Generator exit "+q.exit_code+": "+q.output;
 await beat();b=parse(await tools.mcp__dayz_mcp_130__bridge_status({}));run=b.lifecycle.runs.find(x=>x.run_id===launch.run_id);
 await write(prep+"/mcp-after.json",{run_id:launch.run_id,processes:run?.processes,client_diagnostics:run?.client_diagnostics,server_binding:b.server_peer?.binding_state,server_run_id:b.server_peer?.run_id,version:b.server_peer?.version,version_state:b.server_peer?.version_state});
 await cmd("$ErrorActionPreference='Stop'\n$dep=Get-Content -LiteralPath '"+prep+"/inputs.json' -Raw|ConvertFrom-Json\nforeach($v in $dep.inputs.PSObject.Properties){if((Get-FileHash -LiteralPath $v.Name).Hash.ToLowerInvariant() -ne $v.Value){throw 'Input drift after generation'}}");
}catch(e){problem=e.message;}
finally {
 await beat();const close=parse(await tools.mcp__dayz_mcp_130__dayz_test_close({run_id:launch.run_id,graceful_timeout_s:20}));
 await tools.mcp__dayz_mcp_130__session_release({lease_token:a.lease_token});
 const after=parse(await tools.mcp__dayz_mcp_130__session_status({}));
 await write(prep+"/cleanup.json",{close,self:after.self,pending_commands:after.pending_commands,cleanup_degraded:after.cleanup_degraded,box_occupied:after.box.occupied,error:problem||null});
 if(!close.run_retired||after.self.state!=="none"||after.cleanup_degraded.length)throw Error("Data server cleanup incomplete");
}
if(p)await cmd("powershell -NoProfile -ExecutionPolicy Bypass -File '"+r+"/copy_owned_server_rpt.ps1' -ExpectedStartUtc '"+p.creation_time_utc+"' -ExpectedMission '"+mission+"' -OutputDirectory '"+prep+"'",10000);
notify({state:"F_GENERATION_CLOSED",run_id:launch.run_id,error:problem||null});
if(problem)throw Error(problem);
return {run_id:launch.run_id,generation:out,identity:prep};
}
