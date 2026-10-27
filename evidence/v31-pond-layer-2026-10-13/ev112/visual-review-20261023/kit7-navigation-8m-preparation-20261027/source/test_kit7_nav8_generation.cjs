const fs=require('node:fs'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root='E:/DayZ-Baltic-Build/shape-repair-20261025';
const source=fs.readFileSync(root+'/orchestrate_kit7_nav8_generation.js','utf8');
const digest=s=>crypto.createHash('sha256').update(s).digest('hex');
const runId='11111111-2222-4333-8444-555555555555',start='2026-10-26T11:00:00Z';
async function scenario(name,code=source) {
 const calls=[],writes={},notifications=[];
 let launched=false,active=false,closed=false,foreign=false,captureCount=0,pollCount=0,cancelled=false;
 const engine='a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d';
 const packages={
 'P:/Mods/@DayZ_Baltic_EV112_Kit7Nav8Input/Addons/narva_trial.pbo':'9fbc7608dc407b8b90c7809071aa01f4c27082e6943b293d58d09cb4fd451b49',
 'P:/Mods/@DayZ_Baltic_EV112_Kit7Nav8Input/Addons/baltic_water_v30.pbo':'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43',
 'P:/Mods/@DayZ_Baltic_EV112_Kit7Nav8Input/Addons/baltic_stream_pilot.pbo':'3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6',
 'P:/Mods/@DayZ_MCP/Addons/DayZ_MCP.pbo':'7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'};
 const physicalPackages={
 'P:/Mods/@DayZ_Baltic_EV112_Kit7Overlap/Addons/narva_trial.pbo':'10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc',
 'P:/Mods/@DayZ_Baltic_EV112_Kit7Overlap/Addons/baltic_water_v30.pbo':'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43',
 'P:/Mods/@DayZ_Baltic_EV112_Kit7Overlap/Addons/baltic_stream_pilot.pbo':'3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6',
 'P:/Mods/@DayZ_MCP/Addons/DayZ_MCP.pbo':'7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'};
 const gateFailure=name.startsWith('physics_')&&!['physics_mixed_paths'].includes(name);
 const phys={status:'SERVER_PROBE_PASS',points:6801,identity_bound:true,inputs_unchanged:true,failure_count:0,engine_sha256:engine,packages:{...physicalPackages}};
 if(name==='physics_fail'){phys.status='FAIL';phys.failure_count=19;}
 if(name==='physics_missing')delete phys.packages;
 if(name==='physics_mismatch')phys.packages[Object.keys(physicalPackages)[2]]='wrong';
 if(name==='physics_engine')phys.engine_sha256='wrong';
 if(name==='physics_count')phys.points=6800;
 if(name==='physics_unbound')phys.identity_bound=false;
 if(name==='physics_drift')phys.inputs_unchanged=false;
 if(name==='physics_old_coherent'){phys.packages[Object.keys(physicalPackages)[2]]='old';packages[Object.keys(packages)[2]]='old';}
 if(name==='physics_duplicate')phys.packages[Object.keys(physicalPackages)[0].toLowerCase()]=Object.values(physicalPackages)[0];
 if(name==='physics_mixed_paths')phys.packages=Object.fromEntries(Object.entries(physicalPackages).map(([p,h],i)=>[i%2?p.toLowerCase():p.replaceAll('/','\\'),h]));

 const failedWrapper=name==='wrapper_failure'||name==='cancel_failure';
 const finalFailure=name==='final_status_failure',rptFailure=name==='rpt_failure';
 let statusFailed=false,clock=0;
 const ok=output=>({exit_code:0,output:output||''});
 const tools={
  async exec_command(a){
   const c=a.cmd;calls.push(c);
   if(c.startsWith('Get-Content -LiteralPath')){
    if(c.includes('launch-inputs.json'))return ok(JSON.stringify({status:'READY_AFTER_CODE_REVIEW',observer_sha256:'observer',packages}));
    if(c.includes('/full/result.json'))return ok(JSON.stringify(phys));
    if(c.includes('/attached.json'))return ok(JSON.stringify({status:'ATTACHED',handle_retained:true,process_id:123,start_utc:start,observer_sha256:'observer',executable_sha256:'a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'}));
    if(c.includes('/generation.json'))return ok(JSON.stringify({status:'GENERATED_FILE_PENDING_STRUCTURAL_AND_ENGINE_VALIDATION'}));
    return ok('progress');
   }
   if(c.startsWith('Test-Path'))return ok(c.includes('/attached.json')?'True':'False');
   if(c.includes("-File './tools/navigation/observe_owned_server_exit.ps1'"))return {session_id:88,output:''};
   if(c.includes("-I './tools/navigation/generate_navmesh_console.py'"))return {session_id:77,output:''};
   if(c.includes('/capture_nav_c_generator.ps1')){
    captureCount++;
    if(name==='delayed_capture'&&captureCount<4)return {exit_code:1,output:'Exactly one generator child of this run required'};
    return ok();
   }
   if(c.includes('/cancel_owned_nav_c_generator.ps1')){
    if(name==='cancel_failure')return {exit_code:1,output:'Generator identity could not be confirmed'};
    cancelled=true;return ok();
   }
   if(c.includes('/copy_owned_server_rpt.ps1')&&rptFailure)return {exit_code:1,output:'RPT fixture read error'};
   return ok();
  },
  async write_stdin(a){
   calls.push('poll:'+a.session_id);
   if(a.session_id===88)return ok('observer finished');
   assert.equal(a.session_id,77);
   pollCount++;clock+=name==='rapid_progress'?1:10000;
   if(name==='rapid_progress'&&pollCount<=1900)return {session_id:77,output:'progress'};
   if(name==='elapsed_deadline'&&!cancelled){assert(pollCount<4,'Missing deadline');clock=18300001;return {session_id:77,output:''};}
   if(name==='wrapper_failure'&&pollCount>1)throw Error('Session already completed');
   if(name==='delayed_capture'&&captureCount<4)return {session_id:77,output:''};
   if(name==='foreign_owner'&&!foreign){foreign=true;active=false;return {session_id:77,output:''};}
   return {exit_code:failedWrapper||cancelled?1:0,output:failedWrapper?'wrapper failed':''};
  },
  async apply_patch(p){const m=p.match(/\*\*\* Add File: (.+)\n([\s\S]+)\n\*\*\* End Patch/);assert(m);writes[m[1]]=JSON.parse(m[2].split('\n').map(x=>x.slice(1)).join('\n'));return {};},
  async mcp__dayz_mcp_130__session_status(){
   calls.push('status');
   if(finalFailure&&closed&&!active&&!statusFailed){statusFailed=true;throw Error('Final status fixture failure');}
   return {self:{state:active?'active':'none'},owner:foreign?{id:'foreign'}:null,box:{occupied:launched&&!closed,runs:launched&&!closed?[{run_id:runId,state:foreign?'RUNNING':'RUNNING_IDLE'}]:[]},pending_commands:0,cleanup_degraded:[]};
  },
  async mcp__dayz_mcp_130__dayz_test_run(a){assert(!calls.includes('status'),'No pre-launch occupancy polling; lifecycle owns FIFO');calls.push('launch');assert.equal(a.mode,'server');assert.equal(a.takeover,false);assert.equal(a.on_busy,'queue');assert.equal(a.wait_for_box_s,600);assert(!calls.includes('acquire'),'Lifecycle must queue without preacquired lease');assert.equal(a.navmesh_data_server,true);assert.deepEqual(a.extra_mods,['@DayZ_Baltic_EV112_Kit7Nav8Input']);assert(a.mission.endsWith('BalticKit7NavData.BalticTrial'));launched=true;return {status:'succeeded',run_id:runId};},
  async mcp__dayz_mcp_130__session_acquire_wait(){calls.push('acquire');active=true;return {lease_token:'fake-lease-never-live'};},
  async mcp__dayz_mcp_130__session_heartbeat(){calls.push('beat');if(foreign)throw Error('Foreign owner');return {};},
  async mcp__dayz_mcp_130__bridge_status(){return {server_peer:{binding_state:'BOUND',run_id:runId,version_state:'ok'},lifecycle:{runs:[{run_id:runId,processes:[{pid:123,creation_time_utc:start,role:'server'}],client_diagnostics:[{state:'not_started'}]}]}};},
  async mcp__dayz_mcp_130__dayz_test_close(a){calls.push('close');assert(active&&!foreign);assert.equal(a.run_id,runId);closed=true;return {run_retired:true};},
  async mcp__dayz_mcp_130__session_release(){calls.push('release');active=false;return {};},
 };
 const f=new Function('tools','load','store','notify','setTimeout','Date',code+'\nreturn generateKit7Nav8;')(tools,()=>'(x)=>x',()=>{},x=>notifications.push(x),f=>f(),{now:()=>clock,parse:Date.parse});
 let error=null;try{await f();}catch(e){error=e.message;}
 if(gateFailure){assert(error);assert.equal(calls.filter(x=>x==='launch').length,0);assert(!active);return {name,passed:true,launches:0,error};}
 assert.equal(calls.filter(x=>x==='launch').length,1);
 if(name==='success'||name==='rapid_progress'||name==='physics_mixed_paths'||name==='delayed_capture'){assert.equal(error,null);assert(closed&&!active);}
 else assert(error,'Injected failure must fail');
 if(name==='delayed_capture')assert.equal(captureCount,4);
 if(name==='rapid_progress')assert.equal(pollCount,1901);
 if(name==='elapsed_deadline'){assert(error.includes('Coordinator duration bound'));assert(cancelled&&closed&&!active);}
 if(name==='wrapper_failure')assert(cancelled&&closed&&!active,'Failed wrapper must still cancel exact generator before closing');
 if(name==='cancel_failure'){assert(!closed&&active,'Unconfirmed cancel must preserve own run for recovery');assert(!calls.includes('release'));assert.equal(notifications.at(-1).state,'KIT7_NAV_REQUIRES_OWNED_RECOVERY');}
 if(finalFailure||rptFailure){assert(calls.includes('poll:88'),'Observer completion must still be inspected');assert(closed&&!active);}
 if(name==='foreign_owner'){assert(cancelled&&!closed&&!active);assert(!calls.includes('close'));assert(!calls.includes('release'));}
 const summary=Object.values(writes).find(x=>x.status==='OWNED_RECOVERY_REQUIRED'||x.status==='INCONCLUSIVE'||x.status==='GENERATION_STAGE_COMPLETE_PENDING_VALIDATION');
 assert(summary,'Durable completion required');
 if(['success','rapid_progress','physics_mixed_paths','delayed_capture'].includes(name))assert.equal(summary.status,'GENERATION_STAGE_COMPLETE_PENDING_VALIDATION');
 if(name==='foreign_owner')assert(!calls.some(c=>c.includes('-Event CLOSED')),'Never record a foreign close');
 return {name,passed:true,captureCount,pollCount,closed,released:calls.includes('release'),cancelled,error};
}
(async()=>{
 const cases=[];for(const name of ['physics_fail','physics_missing','physics_mismatch','physics_engine','physics_count','physics_unbound','physics_drift','physics_old_coherent','physics_duplicate','physics_mixed_paths','success','rapid_progress','elapsed_deadline','delayed_capture','wrapper_failure','cancel_failure','final_status_failure','rpt_failure','foreign_owner'])cases.push(await scenario(name));
 const mutations=[
 ['iteration_counter',source.replace('if(Date.now()>deadline)','if(rounds>1830)'),'rapid_progress'],
 ['deadline_removed',source.replace('if(Date.now()>deadline)','if(false)'),'elapsed_deadline'],
 ['single_capture',source.replace('i<24&&!captured','i<1&&!captured'),'delayed_capture'],
 ['skip_cancel_after_wrapper_error',source.replace("genDone=q.exit_code===0&&(await read(out+'/generation.json')).status==='GENERATED_FILE_PENDING_STRUCTURAL_AND_ENGINE_VALIDATION';if(!genDone)throw Error('Generator failed: '+q.output);","genDone=true;if(q.exit_code!==0)throw Error('Generator failed');"),'wrapper_failure'],
 ['close_with_unconfirmed_cancel',source.replace('preserveForRecovery=true;','preserveForRecovery=false;'),'cancel_failure']
 ];
 const negatives=[];
 for(const [name,mutated,test] of mutations){assert.notEqual(mutated,source);let rejected=false;try{await scenario(test,mutated);}catch{rejected=true;}assert(rejected,'Mutation survived: '+name);negatives.push({name,rejected});}
 const result={status:'CONTROL_FLOW_PASS',coordinator_sha256:digest(source),harness_sha256:digest(fs.readFileSync(__filename)),scope:'Mocked tools test JS ownership and cleanup; inline PowerShell is not covered here; not native DayZ or MCP acceptance',cases,negative_mutations:negatives};
 const out=root+'/nav-kit7-8m-preparation-20261027/generation-controls-deadline.json';
 fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
