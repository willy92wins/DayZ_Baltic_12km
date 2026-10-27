const fs=require('node:fs'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const R='E:/DayZ-Baltic-Build/shape-repair-20261025',source=fs.readFileSync(R+'/orchestrate_kit7_nav8_probe.js','utf8');
(async()=>{
 const cases=[];
 for(const mode of ['success','slow_readiness','readiness_timeout','queue_timeout','delayed_precheck_failure','capture_failure','wrong_server_identity','observer_failure','consumer_failure','lease_recovery','foreign_takeover']){
  let reads=0;let started=false,attempted=false,active=false,foreign=false,retired=false,closed=0,released=0,acquired=0,heartbeats=0,consumed=false,polls=0;
  const process={role:'server',pid:123,creation_time_utc:'2026-10-26T13:00:00Z'};
  const run={run_id:'owned',state:'RUNNING_IDLE',processes:[process],client_diagnostics:[{state:'not_started'}]};
  const tools={
   exec_command:async a=>{
    if(a.cmd.includes('Fresh log required')&&mode==='delayed_precheck_failure')return {session_id:10,output:'pre'};
    if(a.cmd.includes('capture_kit7_nav_log.ps1'))return {session_id:20,output:''};
    if(a.cmd.includes('observe_owned_server_exit.ps1'))return mode==='observer_failure'?{exit_code:1,output:'observer failed'}:{session_id:30,output:''};
    if(a.cmd.includes('finish_kit7_nav8_probe.py')){consumed=true;if(mode==='consumer_failure')return {exit_code:1,output:'native FAIL'};}
    return {exit_code:0,output:'ok'};
   },
   write_stdin:async a=>{polls++;if(a.session_id===30){return retired?{exit_code:0,output:'observer complete'}:{session_id:30,output:''};}return {exit_code:a.session_id===10?9:mode==='capture_failure'?8:0,output:a.session_id===10?'check failure':'capture'};},
   apply_patch:async()=>({}),
   mcp__dayz_mcp_130__session_status:async()=>{assert(attempted,'Forbidden prelaunch bank poll');return {box:{occupied:started&&!retired,runs:started&&!retired?[run]:[]},self:{state:active?'active':'none'},owner:foreign?'OTHER':active?'self':null,cleanup_degraded:[],pending_commands:0};},
   mcp__dayz_mcp_130__dayz_test_run:async a=>{assert(!attempted);assert.equal(a.on_busy,'queue');assert.equal(a.wait_for_box_s,600);assert.equal(a.takeover,false);assert.equal(a.navmesh_data_server,false);assert.equal(acquired,0);attempted=true;if(mode==='queue_timeout')return {status:'queue_timeout'};started=true;return {status:'succeeded',run_id:'owned'};},
   mcp__dayz_mcp_130__session_acquire_wait:async()=>{assert(started&&!retired&&!foreign);active=true;acquired++;return {lease_token:'FAKE'};},
   mcp__dayz_mcp_130__session_heartbeat:async()=>{assert(active);heartbeats++;if(['lease_recovery','foreign_takeover'].includes(mode)&&heartbeats===2){active=false;foreign=mode==='foreign_takeover';throw Error('lease expired');}return {};},
   mcp__dayz_mcp_130__bridge_status:async()=>({lifecycle:{runs:[mode==='wrong_server_identity'?{...run,processes:[{...process,role:'client'}]}:run]},server_peer:{binding_state:(mode==='readiness_timeout'||(mode==='slow_readiness'&&++reads<=35))?'WAITING':'BOUND',run_id:'owned',version_state:'ok'}}),
   mcp__dayz_mcp_130__dayz_test_close:async a=>{assert(active&&!foreign&&a.run_id==='owned');closed++;retired=true;return {run_retired:true};},
   mcp__dayz_mcp_130__session_release:async()=>{assert(active&&!foreign);active=false;released++;return {};}
  };
  const execute=new Function('tools','load','store','notify','setTimeout',source+';return probeKit7Nav8();');
  let error=null;try{await execute(tools,()=>'(x)=>x',()=>{},()=>{},f=>f());}catch(e){error=e.message;}
  if(['success','slow_readiness','lease_recovery'].includes(mode)){assert.equal(error,null);assert.equal(acquired,mode==='lease_recovery'?2:1);assert(heartbeats>0);assert.equal(closed,1);assert.equal(released,1);assert(consumed);}
  else{assert(error);if(mode==='consumer_failure'){assert(consumed);assert.equal(closed,1);assert.equal(released,1);}else{assert(!consumed);if(['queue_timeout','delayed_precheck_failure'].includes(mode)){assert(!started);assert.equal(acquired,0);assert.equal(closed,0);}else if(mode==='foreign_takeover'){assert.equal(closed,0);assert.equal(released,0);}else if(mode==='wrong_server_identity'){assert.equal(closed,0);assert.equal(released,1);}else{assert.equal(closed,1);assert.equal(released,1);}}}
  cases.push({mode,passed:true,attempted,started,acquired,closed,released,consumed,polls,error});
 }
 const result={status:'PASS_KIT7_PROBE_CONTROL_FLOW',coordinator_sha256:crypto.createHash('sha256').update(source).digest('hex'),cases,limits:'Mock control flow only; native607 remains separate.'};
 fs.writeFileSync(R+'/kit7-nav8-consumer-20261027/coordinator-controls.json',JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
