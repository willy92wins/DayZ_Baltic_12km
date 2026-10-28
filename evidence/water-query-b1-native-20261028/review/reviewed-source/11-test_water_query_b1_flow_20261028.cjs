const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const source=fs.readFileSync(__dirname+'/finish_water_query_b1_native_20261028.js','utf8');
async function trial(mode){
 const calls=[],writes=[];let live=true,active=false,checks=0;
 const reply=x=>({structuredContent:x}), process={role:'server',pid:42,creation_time_utc:'2026-10-28T00:00:00+00:00'};
 const run={run_id:mode==='foreign_visible'?'foreign':'own',processes:[process],client_diagnostics:[{state:'not_started'}]};
 const tools={
  async apply_patch(p){writes.push(p);return {};},
  async mcp__dayz_mcp_130__session_acquire_wait(){calls.push('acquire');active=true;return reply({lease_token:'fake-test-token',adopted_run:{ok:true,run_id:mode==='wrong_adoption'?'foreign':'own'}});},
  async mcp__dayz_mcp_130__session_heartbeat(){calls.push('beat');return reply({ok:true});},
  async mcp__dayz_mcp_130__bridge_status(){checks++;return reply({lifecycle:{runs:live&&!(mode==='process_gone'&&checks>1)?[run]:[]},server_peer:{run_id:'own',binding_state:'BOUND',version_state:'ok',last_poll_age_s:1}});},
  async exec_command(a){calls.push('command');return {exit_code:mode==='capture_failure'?1:0,output:'synthetic command result'};},
  async mcp__dayz_mcp_130__dayz_test_close(a){assert.equal(a.run_id,'own');calls.push('close');if(!['close_failure','stop_required'].includes(mode))live=false;return reply({run_id:'own',run_retired:!live,stop_required:mode==='stop_required'});},
  async mcp__dayz_mcp_130__dayz_test_stop(a){assert.equal(a.run_id,'own');assert.equal(active,false);calls.push('stop');live=false;return reply({run_id:'own',status:'succeeded'});},
  async mcp__dayz_mcp_130__session_release(){calls.push('release');active=false;return reply({ok:true});},
  async mcp__dayz_mcp_130__session_status(){return reply({self:{state:active?'active':'none'},box:{runs:live?[run]:[]},pending_commands:0,cleanup_degraded:[]});}
 };
 const ctx=vm.createContext({tools,load:key=>{assert.equal(key,'waterB1Launch');return {status:mode==='bad_launch'?'failed':'succeeded',run_id:'own',mission:'C:\\temp\\mission',accepted_sha256:'0'.repeat(64)};},store:()=>{},setTimeout:f=>f(),Date,JSON,Error,Promise});
 vm.runInContext(source,ctx);let error=null;try{await ctx.finishWaterB1();}catch(e){error=e.message;}
 if(['happy','stop_required'].includes(mode))assert.equal(error,null);else assert.ok(error);
 if(mode==='bad_launch'){assert.equal(calls.length,0);assert.equal(writes.length,0);return {mode,verified:true};}
 assert.equal(calls.filter(x=>x==='release').length,1);
 assert.equal(calls.filter(x=>x==='close').length,mode==='wrong_adoption'?0:1);
 if(mode==='wrong_adoption'||mode==='foreign_visible')assert.equal(calls.filter(x=>x==='command').length,0);
 assert.equal(calls.filter(x=>x==='stop').length,mode==='stop_required'?1:0);
 assert.ok(writes.some(x=>x.includes('/cleanup.json')));
 assert.ok(writes.every(x=>!x.includes('fake-test-token')));
 return {mode,verified:true};
}
(async()=>{const rows=[];for(const mode of ['happy','wrong_adoption','foreign_visible','capture_failure','close_failure','process_gone','bad_launch','stop_required'])rows.push(await trial(mode));const report={status:'EIGHT_MOCK_LIFECYCLE_CONTROLS_PASS',source_sha256:crypto.createHash('sha256').update(source).digest('hex'),rows};fs.writeFileSync(__dirname+'/water-query-b1-flow-tests-20261028.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));})().catch(e=>{console.error(e);process.exit(1);});
