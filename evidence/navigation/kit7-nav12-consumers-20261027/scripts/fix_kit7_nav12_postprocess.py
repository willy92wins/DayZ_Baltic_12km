from pathlib import Path
import hashlib,json
R=Path(__file__).parent;D=R/'kit7-nav12-consumer-20261027'
def change(name,edits):
    p=R/name;s=p.read_text();(D/(name+'.before-lifecycle')).write_text(s)
    for old,new in edits:
        assert s.count(old)==1,(name,old,s.count(old))
        s=s.replace(old,new)
    p.write_text(s)
change('orchestrate_kit7_nav12_probe.js',[
 ("if(token)parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));q=","if(token)await beat();q="),
 ("catch(e){await event('HEARTBEAT_ERROR');const s=parse(","catch(e){const s=parse(")])
change('test_kit7_nav12_probe_command.cjs',[
 ("new Function('tools','w','token','parse','return ('+expr+');')(tools,'unused',mode.startsWith('leased')?'FAKE':null,x=>x)","new Function('tools','w','token','parse','beat','return ('+expr+');')(tools,'unused',mode.startsWith('leased')?'FAKE':null,x=>x,async()=>tools.mcp__dayz_mcp_130__session_heartbeat())")])
change('test_kit7_nav12_probe_flow.cjs',[
 ("(async()=>{\n const cases=[];\n for(const mode of [", "async function scenario(mode,code=source){"),
 ("'success','slow_readiness','readiness_timeout','queue_timeout','delayed_precheck_failure','capture_failure','wrong_server_identity','observer_failure','consumer_failure','lease_recovery','foreign_takeover']){", ""),
 ("let reads=0;let started", "let reads=0,commands=0,commandExpired=false;let started"),
 ("exec_command:async a=>{", "exec_command:async a=>{\n    if(++commands>150)throw Error('Command recursion bound');\n    if(a.cmd.includes('-Event HEARTBEAT_ERROR')&&!active)return {session_id:40,output:''};\n    if(a.cmd.includes('capture_owned_server_identity.ps1')&&['command_lease_recovery','command_lease_foreign'].includes(mode)&&!commandExpired){commandExpired=true;active=false;foreign=mode==='command_lease_foreign';return {session_id:40,output:''};}"),
 ("a.cmd.includes('finish_kit7_nav_probe.py')", "a.cmd.includes('finish_kit7_nav12_probe.py')"),
 ("['success','slow_readiness','lease_recovery'].includes(mode)", "['success','slow_readiness','lease_recovery','command_lease_recovery'].includes(mode)"),
 ("mode==='lease_recovery'?2:1", "['lease_recovery','command_lease_recovery'].includes(mode)?2:1"),
 ("mode==='foreign_takeover'){assert.equal(closed", "['foreign_takeover','command_lease_foreign'].includes(mode)){assert.equal(closed"),
 ("source+';return probeKit7Nav12();'", "code+';return probeKit7Nav12();'"),
 ("  cases.push({mode,passed:true,attempted,started,acquired,closed,released,consumed,polls,error});\n }\n const result=", "  return {mode,passed:true,attempted,started,acquired,closed,released,consumed,polls,error};\n}\n(async()=>{\n const cases=[];\n for(const mode of ['success','slow_readiness','readiness_timeout','queue_timeout','delayed_precheck_failure','capture_failure','wrong_server_identity','observer_failure','consumer_failure','lease_recovery','foreign_takeover','command_lease_recovery','command_lease_foreign'])cases.push(await scenario(mode));\n const negative_mutations=[];\n for(const [name,mutated] of [\n ['cmd_direct_heartbeat',source.replace('if(token)await beat();q=','if(token)parse(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));q=')],\n ['event_before_recovery',source.replace('catch(e){const s=parse(',\"catch(e){await event('HEARTBEAT_ERROR');const s=parse(\")]\n ]){assert.notEqual(mutated,source);let rejected=false;try{await scenario('command_lease_recovery',mutated);}catch{rejected=true;}assert(rejected,'Mutation survived: '+name);negative_mutations.push({name,rejected});}\n const result="),
 ("cases,limits:","cases,negative_mutations,limits:")])
change('package_and_deploy_kit7_nav12.py',[
 ("from verify_c_orderly_close import validate_close,validate_rpt,validate_generation_exit", "from verify_c_orderly_close import validate_close,validate_rpt,validate_generation_exit\nfrom verify_nav12_generation_budget import validate_budget"),
 ("utc=lambda x:datetime.datetime.fromisoformat", "budget_result=validate_budget(read(I/'generation-budget.json'),gen)\nwrite(I/'budget-verification.json',budget_result)\nutc=lambda x:datetime.datetime.fromisoformat"),
 ("Path(__file__),R/'verify_c_orderly_close.py'", "Path(__file__),R/'verify_c_orderly_close.py',R/'verify_nav12_generation_budget.py'")])
frozen_path=D/'frozen.json';frozen=json.loads(frozen_path.read_text())
for p in frozen['inputs']:
    if Path(p).parent==R and Path(p).name in {'orchestrate_kit7_nav12_probe.js','finish_kit7_nav12_probe.py'}:
        frozen['inputs'][p]=hashlib.sha256(Path(p).read_bytes()).hexdigest()
frozen_path.write_text(json.dumps(frozen,indent=2)+'\n')
print('Nav12 postprocessing patched; generation sources untouched')
