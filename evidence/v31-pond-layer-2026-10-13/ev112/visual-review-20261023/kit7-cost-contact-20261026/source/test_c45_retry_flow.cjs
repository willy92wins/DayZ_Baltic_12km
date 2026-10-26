const fs=require('node:fs'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const R='E:/DayZ-Baltic-Build/shape-repair-20261025';
const source=fs.readFileSync(R+'/orchestrate_c45_retry.js','utf8');
(async()=>{
 const cases=[];
 for(const mode of ['success','foreign_bank','delayed_precheck_failure','capture_failure','wrong_server_identity']){
  let launched=false,active=false,retired=false,closed=0,released=0,acquired=0,heartbeats=0,consumed=false,polls=0;
  const process={role:'server',pid:123,creation_time_utc:'2026-10-26T13:00:00Z'};
  const run={run_id:'owned',state:'RUNNING_IDLE',processes:[process],client_diagnostics:[{state:'not_started'}]};
  const tools={
   exec_command:async a=>{if(a.cmd.includes('Fresh log required')&&mode==='delayed_precheck_failure')return {session_id:10,output:'pre'};if(a.cmd.includes('capture_patch_nav_log.ps1'))return {session_id:20,output:''};if(a.cmd.includes('finish_c45_retry_probe.py'))consumed=true;return {exit_code:0,output:'ok'};},
   write_stdin:async a=>{polls++;return {exit_code:a.session_id===10?9:mode==='capture_failure'?8:0,output:a.session_id===10?'check failure':'capture'};},
   apply_patch:async()=>({}),
   mcp__dayz_mcp_130__session_status:async()=>({box:{occupied:mode==='foreign_bank'||launched&&!retired,runs:launched&&!retired?[run]:[]},self:{state:active?'active':'none'},owner:active?'self':null,cleanup_degraded:[],pending_commands:0}),
   mcp__dayz_mcp_130__dayz_test_run:async()=>{assert(!launched);launched=true;return {status:'succeeded',run_id:'owned'};},
   mcp__dayz_mcp_130__session_acquire_wait:async()=>{assert(launched&&!retired);active=true;acquired++;return {lease_token:'FAKE'};},
   mcp__dayz_mcp_130__session_heartbeat:async()=>{assert(active);heartbeats++;return {};},
   mcp__dayz_mcp_130__bridge_status:async()=>({lifecycle:{runs:[mode==='wrong_server_identity'?{...run,processes:[{...process,role:'client'}]}:run]},server_peer:{binding_state:'BOUND',run_id:'owned',version_state:'ok'}}),
   mcp__dayz_mcp_130__dayz_test_close:async a=>{assert(active&&a.run_id==='owned');closed++;retired=true;return {run_retired:true};},
   mcp__dayz_mcp_130__session_release:async()=>{assert(active);active=false;released++;return {};}
  };
  const execute=new Function('tools','load','store','notify','setTimeout',source+';return probeC45Retry();');
  let error=null;try{await execute(tools,()=>'(x)=>x',()=>{},()=>{},f=>f());}catch(e){error=e.message;}
  if(mode==='success'){assert.equal(error,null);assert.equal(acquired,1);assert(heartbeats>0);assert.equal(closed,1);assert.equal(released,1);assert(consumed);}
  else{assert(error);assert(!consumed);if(['foreign_bank','delayed_precheck_failure'].includes(mode)){assert(!launched);assert.equal(acquired,0);assert.equal(closed,0);}else if(mode==='capture_failure'){assert.equal(closed,1);assert.equal(released,1);}else{assert.equal(closed,0);assert.equal(released,1);}}
  cases.push({mode,passed:true,launched,acquired,closed,released,consumed,polls});
 }
 const result={status:'PASS_C45_CONTROL_FLOW',coordinator_sha256:crypto.createHash('sha256').update(source).digest('hex'),cases,limits:'Mock control flow only; native 45-query acceptance remains separate.'};
 fs.writeFileSync(R+'/nav-c-retry-postprocess-review/after-fixes/flow-controls.json',JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
