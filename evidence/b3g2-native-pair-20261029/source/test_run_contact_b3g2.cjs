const fs=require('fs'),assert=require('node:assert/strict'),path=require('path');
const {runArm}=eval(fs.readFileSync(path.join(__dirname,'run_contact_b3g2.js'),'utf8'));
function fixture(kind){
 let tick=Date.parse('2026-10-29T00:00:00Z'),pending=[],beat=0;const calls=[],saved={};
 const api={now:()=>new Date(tick).toISOString(),millis:()=>tick,sleep:ms=>ms===10000?new Promise(r=>pending.push(r)):(tick+=ms,Promise.resolve()),
 save:async(n,v)=>{if(kind==='write'&&n==='cleanup.json')throw Error('disk');assert(!saved[n]);saved[n]=structuredClone(v);},
 gate:async()=>{calls.push('gate');if(kind==='gate')throw Error('gatefail');},preflight:async()=>calls.push('preflight'),
 launch:async req=>{calls.push('launch');assert.equal(req.on_busy,'queue');assert.equal(req.wait_for_box_s,600);return {status:kind==='launch'?'failed':'succeeded',run_id:kind==='launch'?null:'own'};},
 acquire:async run=>{calls.push('acquire');assert.equal(run,'own');if(kind==='adoption')throw Error('acquire_failed');return {lease_token:'never-save-token',adopted_run:{run_id:kind==='foreign'?'foreign':'own',ok:true}};},
 heartbeat:async token=>{assert.equal(token,'never-save-token');calls.push('heartbeat');if(kind==='heartbeat'&&beat++===1)throw Error('bad');},
 bridge:async()=>({server_peer:{run_id:'own',binding_state:'BOUND',version_state:'ok',bound_last_poll_age_s:0},lifecycle:{runs:[{run_id:'own',processes:[{role:'server',pid:4}],client_diagnostics:[{state:'not_started'}]}]}}),
 host:async()=>{for(let i=0;i<2;i++){await new Promise(r=>setImmediate(r));tick+=15000;const ready=pending;pending=[];ready.forEach(r=>r());await new Promise(r=>setImmediate(r));}if(kind==='host')throw Error('hostfail');},
 observe:async()=>{calls.push('observe');if(kind==='script')throw Error('native_script_error');return {status:kind==='timeout'?'PENDING_SAMPLES':'CAPTURED_NOT_JUDGED'};},
 close:async run=>{calls.push('close');assert.equal(run,'own');if(kind==='close')throw Error('close_failed');return {run_id:run,run_retired:true};},
 stop:async run=>{calls.push('stop');assert.equal(run,'own');return {run_id:run,status:'succeeded'};},
 release:async()=>{calls.push('release');return {released:true,cleanup:{terminal_safe:true}};},
 status:async()=>{calls.push('status');return {self:{state:'none'},pending_commands:0,cleanup_degraded:[]};}};
 return {api,calls,saved};
}
(async()=>{let tests=0;
 for(const kind of ['ok','gate','launch','foreign','heartbeat','host','script','timeout','adoption','close','write']){
   const f=fixture(kind),r=await runArm(f.api,{mission:'canonical',mod:'isolated',seal:'hash'});tests++;
   assert.equal(r.status==='CAPTURED_PENDING_CONSUMER',kind==='ok',kind);
   assert(!JSON.stringify(f.saved).includes('never-save-token'));
   if(['ok','heartbeat','host','script','timeout','close','write'].includes(kind)){assert(f.calls.includes('close'));assert(f.calls.includes('release'));assert(f.calls.indexOf('launch')<f.calls.indexOf('acquire'));}
   else assert(!f.calls.includes('close'));
   if(['foreign','adoption','close'].includes(kind))assert(f.calls.includes('stop'));
   if(kind==='ok'){assert(f.calls.filter(x=>x==='heartbeat').length>=3);assert.equal(Date.parse(f.saved['readiness.json'].capture_deadline_utc)-Date.parse(f.saved['readiness.json'].ready_utc),180000);}
   if(kind==='heartbeat')assert(!f.calls.includes('observe'));
   if(kind==='gate')assert(!f.calls.includes('status'));
 }
 console.log(JSON.stringify({status:'PASS_COORDINATOR_FIXTURES',tests}));
})().catch(e=>{console.error(e);process.exitCode=1;});
