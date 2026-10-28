const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(__dirname+'/finish_dry_road_full_native_20261028.js','utf8');
async function trial(mode){
 const calls=[],writes=[];let live=true,active=false,checks=0;const reply=x=>({structuredContent:x});
 const process={role:'server',pid:42,creation_time_utc:'2026-10-28T00:00:00+00:00'};
 const run={run_id:mode==='foreign_visible'?'foreign':'own',processes:[process],client_diagnostics:[{state:'not_started'}]};
 const tools={
  async apply_patch(p){writes.push(p);return {};},
  async mcp__dayz_mcp_130__session_acquire_wait(){calls.push('acquire');active=true;return reply({lease_token:'fake-test-token',adopted_run:{ok:true,run_id:mode==='wrong_adoption'?'foreign':'own'}});},
  async mcp__dayz_mcp_130__session_heartbeat(){calls.push('beat');return reply({ok:true});},
  async mcp__dayz_mcp_130__bridge_status(){checks++;return reply({lifecycle:{runs:live&&!(mode==='process_gone'&&checks>1)?[run]:[]},server_peer:{run_id:'own',binding_state:'BOUND',version_state:'ok',last_poll_age_s:1}});},
  async exec_command(a){calls.push('command');return {exit_code:mode==='capture_failure'?1:0,output:'synthetic command result'};},
  async mcp__dayz_mcp_130__dayz_test_close(a){assert.equal(a.run_id,'own');calls.push('close');if(mode!=='close_failure')live=false;return reply({run_id:'own',run_retired:!live});},
  async mcp__dayz_mcp_130__session_release(){calls.push('release');active=false;return reply({ok:true});},
  async mcp__dayz_mcp_130__session_status(){return reply({self:{state:active?'active':'none'},box:{runs:live?[run]:[]},pending_commands:0,cleanup_degraded:[]});}
 };
 const ctx=vm.createContext({tools,load:key=>{assert.equal(key,'dryRoadFullLaunch_probe');return {status:'succeeded',run_id:'own',mode:mode==='stale_phase'?'calibration':'probe',accepted_sha256:'0'.repeat(64),calibration_sha256:'1'.repeat(64)};},store:()=>{},setTimeout:f=>{f();},Date,JSON,Error,Promise});vm.runInContext(source,ctx);
 let error=null;try{await ctx.finishDryRoadFull('probe');}catch(e){error=e.message;}
 if(mode==='happy')assert.equal(error,null);else assert.ok(error);
 if(mode==='stale_phase'){assert.equal(calls.length,0);assert.equal(writes.length,0);return {mode,expected_outcome_verified:true,close_calls:0};}
 assert.equal(calls.filter(x=>x==='release').length,1);
 assert.equal(calls.filter(x=>x==='close').length,mode==='wrong_adoption'?0:1);
 if(mode==='wrong_adoption'||mode==='foreign_visible')assert.equal(calls.filter(x=>x==='command').length,0);
 assert.ok(writes.some(x=>x.includes('/cleanup.json')));return {mode,expected_outcome_verified:true,close_calls:calls.filter(x=>x==='close').length};
}
(async()=>{const rows=[];for(const mode of ['happy','wrong_adoption','foreign_visible','capture_failure','close_failure','process_gone','stale_phase'])rows.push(await trial(mode));fs.writeFileSync(__dirname+'/dry-road-full-flow-tests-r2-20261028.json',JSON.stringify({status:'SEVEN_MOCK_LIFECYCLE_CONTROLS_PASS',rows},null,2));console.log(JSON.stringify(rows));})().catch(e=>{console.error(e);process.exit(1);});
