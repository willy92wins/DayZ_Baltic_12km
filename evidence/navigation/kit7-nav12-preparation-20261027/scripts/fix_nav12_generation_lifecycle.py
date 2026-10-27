"""Derive Nav12 from the exercised Nav8 coordinator; close the measured lease gap."""
from pathlib import Path
import hashlib,json
R=Path(__file__).parent
D=R/'nav-kit7-12m-preparation-20261027'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dep=json.loads((D/'launch-inputs.json').read_text())
assert dep['status']=='PREPARED_PENDING_CODE_REVIEW'
coordinator=R/'orchestrate_kit7_nav12_generation.js'
harness=R/'test_kit7_nav12_generation.cjs'
for p in (coordinator,harness):assert sha(p)==dep['inputs'][str(p)],p
assert not (D/'lifecycle-derived.json').exists()
mapping={
 'generateKit7Nav8':'generateKit7Nav12',
 'nav-kit7-8m-preparation-20261027':'nav-kit7-12m-preparation-20261027',
 'navmesh-kit7-8m-v9-20261027':'navmesh-kit7-12m-v9-20261027',
 'Kit7Nav8Input':'Kit7Nav12Input','kit7nav8input':'kit7nav12input',
 'navKit7Eight':'navKit7Twelve',
 '9fbc7608dc407b8b90c7809071aa01f4c27082e6943b293d58d09cb4fd451b49':'ed1acb1d993a705996edad1bc3008f14e0b904483ad207d5b903a4d2aee35287',
 'orchestrate_kit7_nav8_generation.js':'orchestrate_kit7_nav12_generation.js',
 'generation-controls-deadline.json':'generation-controls.json'}
def derive(name):
 s=(R/name).read_text(encoding='utf-8')
 for a,b in mapping.items():s=s.replace(a,b)
 return s
def replace_once(s,a,b):
 assert s.count(a)==1,(a,s.count(a))
 return s.replace(a,b,1)
s=derive('orchestrate_kit7_nav8_generation.js')
s=replace_once(s,'let token=null;','let token=null,budget=null;')
s=replace_once(s,'if(token)parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));q=','if(token)await beat();q=')
s=replace_once(s,"  await event('HEARTBEAT_ERROR');const state=","  const state=")
s=replace_once(s,"  await checkedBridge();await event('LEASE_RECOVERED');","  await checkedBridge();if(budget)await checkBudget();await event('LEASE_RECOVERED');")
budget_code="""const budgetFrom=receipt=>{
 const started=Date.parse(receipt?.started_utc);
 if(receipt?.run_id!==runid||!Number.isFinite(started)||started<=0)throw Error('Invalid generation clock receipt');
 return {run_id:runid,started_utc:receipt.started_utc,generation_seconds:18000,generation_deadline_utc:new Date(started+18000e3).toISOString(),coordinator_seconds:18300,deadline_utc:new Date(started+18300e3).toISOString()};
};
const checkBudget=async()=>{
 const current=await read(d+'/generation-budget.json'),expected=budgetFrom(await read(out+'/generation.json'));
 const keys=Object.keys(expected);
 if(Object.keys(current).length!==keys.length||keys.some(k=>current[k]!==expected[k])||(budget&&keys.some(k=>current[k]!==budget[k])))throw Error('Generation budget drift; deadline cannot reset');
 return current;
};
"""
s=replace_once(s,"try {\n await event('LAUNCHED');",budget_code+"try {\n await event('LAUNCHED');")
s=replace_once(s," if(!captured)throw Error('Generator identity capture deadline');", """ if(!captured)throw Error('Generator identity capture deadline');
 if(await exists(d+'/generation-budget.json'))throw Error('Fresh generation budget receipt required');
 budget=budgetFrom(await read(out+'/generation.json'));
 await write(d+'/generation-budget.json',budget);await checkBudget();
 store('navKit7TwelveBudget',budget);""")
s=replace_once(s,'let rounds=0;const deadline=Date.now()+18300e3;','let rounds=0;const deadline=Date.parse(budget.deadline_utc);')
s=replace_once(s,"if(genSession&&!genDone){try{await event('GENERATOR_CANCEL_INTENT');", "if(genSession&&!genDone){try{await beat();const cancellationState=parse(await tools.mcp__dayz_mcp_130__session_status({}));if(cancellationState.self.state!=='active'||!cancellationState.box.runs.some(x=>x.run_id===runid))throw Error('No owned lease for generator cancellation');await checkedBridge();await event('GENERATOR_CANCEL_INTENT');")
t=derive('test_kit7_nav8_generation.cjs')
t=replace_once(t,'let statusFailed=false,clock=0;','let statusFailed=false,clock=0,expired=false,recoverCount=0,commandExpiryInjected=false,generatorStarted=null;')
t=replace_once(t,'const c=a.cmd;calls.push(c);',"""const c=a.cmd;calls.push(c);
   if(calls.length>30000)throw Error('Mock recursion bound');
   if(c.includes('-Event HEARTBEAT_ERROR')&&expired)return {session_id:99,output:''};
   if(['expiry_during_command','expiry_with_foreign_owner','expiry_pid_reuse'].includes(name)&&c.includes('/capture_owned_server_identity.ps1')&&!commandExpiryInjected){commandExpiryInjected=true;expired=true;active=false;if(name==='expiry_with_foreign_owner')foreign=true;return {session_id:99,output:''};}""")
t=replace_once(t,"if(c.includes('/generation.json'))return ok(JSON.stringify({status:'GENERATED_FILE_PENDING_STRUCTURAL_AND_ENGINE_VALIDATION'}));", """if(c.includes('/generation-budget.json')){
     const value=Object.values(writes).find(x=>x.generation_seconds===18000);
     if(name==='budget_missing_on_recovery'&&recoverCount>1)return {exit_code:1,output:'Budget receipt missing'};
     const valueCopy=value?{...value}:null;
     if(name==='budget_changed_on_recovery'&&recoverCount>1)valueCopy.deadline_utc=new Date(Date.parse(valueCopy.deadline_utc)+1000).toISOString();
     return ok(JSON.stringify(valueCopy));
    }
    if(c.includes('/generation.json'))return ok(JSON.stringify({status:'GENERATED_FILE_PENDING_STRUCTURAL_AND_ENGINE_VALIDATION',run_id:runId,started_utc:generatorStarted||start}));""")
t=replace_once(t,"if(c.startsWith('Test-Path'))return ok(c.includes('/attached.json')?'True':'False');", "if(c.startsWith('Test-Path'))return ok(c.includes('/attached.json')||(name==='budget_preexists'&&c.includes('/generation-budget.json'))?'True':'False');")
t=replace_once(t,"if(c.includes(\"-I './tools/navigation/generate_navmesh_console.py'\"))return {session_id:77,output:''};", "if(c.includes(\"-I './tools/navigation/generate_navmesh_console.py'\")){generatorStarted=new Date(Date.parse(start)+clock).toISOString();return {session_id:77,output:''};}")
t=replace_once(t,"calls.push('poll:'+a.session_id);", "calls.push('poll:'+a.session_id);if(a.session_id===99){clock+=5000;return ok('command complete');}")
t=replace_once(t,"if(name==='foreign_owner'&&!foreign)","if(['expiry_after_budget','budget_changed_on_recovery','budget_missing_on_recovery'].includes(name)&&pollCount===1){expired=true;active=false;return {session_id:77,output:''};}\n   if(name==='foreign_owner'&&!foreign)")
t=replace_once(t,"async mcp__dayz_mcp_130__session_acquire_wait(){calls.push('acquire');active=true;return {lease_token:'fake-lease-never-live'};}","async mcp__dayz_mcp_130__session_acquire_wait(){calls.push('acquire');active=true;expired=false;recoverCount++;return {lease_token:'fake-lease-never-live'};}")
t=replace_once(t,"if(foreign)throw Error('Foreign owner');return {};", "if(foreign)throw Error('Foreign owner');if(expired)throw Error('lease_expired');return {};")
t=replace_once(t,"processes:[{pid:123,creation_time_utc:start,role:'server'}]", "processes:[{pid:name==='expiry_pid_reuse'&&recoverCount>1?124:123,creation_time_utc:start,role:'server'}]")
t=replace_once(t,"const f=new Function(", "class FakeDate extends Date {constructor(...args){super(...(args.length?args:[Date.parse(start)+clock]));}static now(){return Date.parse(start)+clock;}}\n const f=new Function(")
t=replace_once(t,"{now:()=>clock,parse:Date.parse}","FakeDate")
t=t.replace("name==='success'||name==='rapid_progress'||name==='physics_mixed_paths'||name==='delayed_capture'", "['success','rapid_progress','physics_mixed_paths','delayed_capture','expiry_during_command','expiry_after_budget'].includes(name)")
t=replace_once(t,"if(name==='foreign_owner'){assert(cancelled&&!closed&&!active);", "if(name==='foreign_owner'){assert(!cancelled&&!closed&&!active,'Foreign ownership must preserve native processes');")
t=replace_once(t,"['success','rapid_progress','physics_mixed_paths','delayed_capture'].includes(name)","['success','rapid_progress','physics_mixed_paths','delayed_capture','expiry_during_command','expiry_after_budget'].includes(name)")
extra_assertions="""
 if(['expiry_during_command','expiry_after_budget'].includes(name)){
  assert.equal(recoverCount,2);assert(calls.some(c=>c.includes('-Event LEASE_RECOVERED')));
  const value=Object.values(writes).find(x=>x.generation_seconds===18000);
  assert.equal(value.started_utc,generatorStarted);assert.equal(Date.parse(value.deadline_utc)-Date.parse(generatorStarted),18300e3);
  assert.equal(Date.parse(value.generation_deadline_utc)-Date.parse(generatorStarted),18000e3);
 }
 if(['budget_changed_on_recovery','budget_missing_on_recovery','budget_preexists'].includes(name)){assert(cancelled&&closed&&!active);assert(error.includes('budget')||error.includes('Budget'));}
 if(['expiry_with_foreign_owner','expiry_pid_reuse'].includes(name)){assert(!generatorStarted&&!closed&&!cancelled);}
"""
t=replace_once(t," const summary=Object.values(writes)",extra_assertions+" const summary=Object.values(writes)")
t=replace_once(t,"'rpt_failure','foreign_owner'])cases.push", "'rpt_failure','foreign_owner','expiry_during_command','expiry_after_budget','budget_changed_on_recovery','budget_missing_on_recovery','budget_preexists','expiry_with_foreign_owner','expiry_pid_reuse'])cases.push")
t=replace_once(t," const mutations=[", """ const mutations=[
 ['cmd_direct_heartbeat',source.replace('if(token)await beat();q=', 'if(token)parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));q='),'expiry_during_command'],
 ['skip_recovery_budget_check',source.replace('if(budget)await checkBudget();',''),'budget_changed_on_recovery'],
 ['event_before_recovery',source.replace('  const state=parse(',"  await event('HEARTBEAT_ERROR');const state=parse("),'expiry_during_command'],""")
for p,new in ((coordinator,s),(harness,t)):
 (D/(p.stem+'-before-lifecycle'+p.suffix)).write_bytes(p.read_bytes())
 p.write_text(new,encoding='utf-8')
 dep['inputs'][str(p)]=sha(p)
dep['coordinator_sha256']=sha(coordinator)
for p in (Path(__file__),R/'kit7-nav12-plan-review-20261027/accepted.json',R/'archived-mods-nav12-space-20261027/archive-plan.json',R/'archived-mods-nav12-space-20261027/archive-complete.json'):
 dep['inputs'][str(p)]=sha(p)
dep['generation_budget_receipt']='generation-budget.json; fixed from native wrapper started_utc, 18000s generation/18300s coordinator'
(D/'launch-inputs.json').write_text(json.dumps(dep,indent=2)+'\n',encoding='utf-8')
(D/'lifecycle-derived.json').write_text(json.dumps(dict(status='PENDING_CODE_REVIEW',source_coordinator_sha256=sha(R/'orchestrate_kit7_nav8_generation.js'),source_harness_sha256=sha(R/'test_kit7_nav8_generation.cjs'),coordinator_sha256=sha(coordinator),harness_sha256=sha(harness),changes=['Recover heartbeat in cmd without pre-adoption command recursion','Persist and recheck fixed deadlines from generation receipt','Require own lease and matching process before cancellation']),indent=2)+'\n')
print('NAV12_LIFECYCLE_DERIVED_PENDING_TESTS_AND_REVIEW')
