from pathlib import Path
import json
R=Path(__file__).parent
s=(R/'orchestrate_nav_kit7.js').read_text()
a=s.index('if(physical.failure_count');b=s.index("\nlet s=parse",a)
gate="""const packageMap=value=>{const out={};for(const [path,hash] of Object.entries(value||{})){const key=path.replaceAll('\\\\','/').toLowerCase();if(!/^[a-z]:\\//.test(key)||key.split('/').includes('..')||Object.hasOwn(out,key))throw Error('Invalid or duplicate package path');out[key]=hash;}return out;};
const requiredPackages={
 'p:/mods/@dayz_baltic_ev112_kit7overlap/addons/narva_trial.pbo':'10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc',
 'p:/mods/@dayz_baltic_ev112_kit7overlap/addons/baltic_water_v30.pbo':'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43',
 'p:/mods/@dayz_baltic_ev112_kit7overlap/addons/baltic_stream_pilot.pbo':'3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6',
 'p:/mods/@dayz_mcp/addons/dayz_mcp.pbo':'7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'};
const frozenPackages=packageMap(prepared.packages),physicalPackages=packageMap(physical.packages);
if(physical.failure_count!==0||physical.engine_sha256!=='a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'||[frozenPackages,physicalPackages].some(v=>Object.keys(v).length!==4||Object.entries(requiredPackages).some(([path,hash])=>v[path]!==hash)))throw Error('Kit7 physical package binding missing');"""
s=s[:a]+gate+s[b:]
s=s.replace("preserveForRecovery=false;","preserveForRecovery=false,generatorFinished=null;",1)
old="foreach($v in $i.packages.PSObject.Properties){if($h.package_hashes.($v.Name) -ne $v.Value){throw 'Loaded stack mismatch'}}"
new="$hh=@{};foreach($item in $h.package_hashes.PSObject.Properties){$key=[IO.Path]::GetFullPath($item.Name).ToLowerInvariant();if($hh.ContainsKey($key)){throw 'Duplicate host package path'};$hh[$key]=$item.Value}\\nforeach($v in $i.packages.PSObject.Properties){if($hh[[IO.Path]::GetFullPath($v.Name).ToLowerInvariant()] -ne $v.Value){throw 'Loaded stack mismatch'}}"
assert old in s;s=s.replace(old,new)
s=s.replace("if(!q.session_id){if(q.exit_code===0","if(!q.session_id){generatorFinished=q;if(q.exit_code===0")
s=s.replace("genDone=q.exit_code===0","generatorFinished=q;genDone=q.exit_code===0")
old="const result=await tools.write_stdin({session_id:genSession,chars:'',yield_time_ms:10000,max_output_tokens:1600});"
assert old in s;s=s.replace(old,"const result=generatorFinished||await tools.write_stdin({session_id:genSession,chars:'',yield_time_ms:10000,max_output_tokens:1600});")
s=s.replace("try{await event('CLOSED');}","try{if(close?.run_retired&&!close.already_gone)await event('CLOSED');}")
out=R/'orchestrate_nav_kit7_v2.js';assert not out.exists();out.write_text(s)
# Fresh test artifacts preserve prior verdict/receipts.
s=(R/'test_nav_kit7_coordinator.cjs').read_text().replace('orchestrate_nav_kit7.js','orchestrate_nav_kit7_v2.js')
a=s.index("const packages=");b=s.index("\n const failedWrapper",a)
s=s[:a]+"""const engine='a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d';
 const packages={
 'P:/Mods/@DayZ_Baltic_EV112_Kit7Overlap/Addons/narva_trial.pbo':'10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc',
 'P:/Mods/@DayZ_Baltic_EV112_Kit7Overlap/Addons/baltic_water_v30.pbo':'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43',
 'P:/Mods/@DayZ_Baltic_EV112_Kit7Overlap/Addons/baltic_stream_pilot.pbo':'3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6',
 'P:/Mods/@DayZ_MCP/Addons/DayZ_MCP.pbo':'7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'};
 const gateFailure=name.startsWith('physics_')&&!['physics_mixed_paths'].includes(name);
 const phys={status:'SERVER_PROBE_PASS',points:6801,identity_bound:true,inputs_unchanged:true,failure_count:0,engine_sha256:engine,packages:{...packages}};
 if(name==='physics_fail'){phys.status='FAIL';phys.failure_count=19;}
 if(name==='physics_missing')delete phys.packages;
 if(name==='physics_mismatch')phys.packages[Object.keys(packages)[2]]='wrong';
 if(name==='physics_engine')phys.engine_sha256='wrong';
 if(name==='physics_count')phys.points=6800;
 if(name==='physics_unbound')phys.identity_bound=false;
 if(name==='physics_drift')phys.inputs_unchanged=false;
 if(name==='physics_old_coherent'){phys.packages[Object.keys(packages)[2]]='old';packages[Object.keys(packages)[2]]='old';}
 if(name==='physics_duplicate')phys.packages[Object.keys(packages)[0].toLowerCase()]=Object.values(packages)[0];
 if(name==='physics_mixed_paths')phys.packages=Object.fromEntries(Object.entries(packages).map(([p,h],i)=>[i%2?p.toLowerCase():p.replaceAll('/','\\\\'),h]));
"""+s[b:]
a=s.index("if(c.includes('/full/result.json'))");b=s.index('\n',a)
s=s[:a]+"if(c.includes('/full/result.json'))return ok(JSON.stringify(phys));"+s[b:]
s=s.replace("pollCount++;","pollCount++;if(name==='wrapper_failure'&&pollCount>1)throw Error('Session already completed');")
s=s.replace("if(name==='success'||name==='delayed_capture')","if(name==='success'||name==='physics_mixed_paths'||name==='delayed_capture')")
s=s.replace("assert(summary,'Durable completion required');","assert(summary,'Durable completion required');\n if(['success','physics_mixed_paths','delayed_capture'].includes(name))assert.equal(summary.status,'GENERATION_STAGE_COMPLETE_PENDING_VALIDATION');\n if(name==='foreign_owner')assert(!calls.some(c=>c.includes('-Event CLOSED')),'Never record a foreign close');")
s=s.replace("['physics_fail','physics_missing','physics_mismatch','success'","['physics_fail','physics_missing','physics_mismatch','physics_engine','physics_count','physics_unbound','physics_drift','physics_old_coherent','physics_duplicate','physics_mixed_paths','success'")
s=s.replace("scope:'Mocked tools test ownership and cleanup flow; not native DayZ or MCP acceptance'","scope:'Mocked tools test JS ownership and cleanup; inline PowerShell is not covered here; not native DayZ or MCP acceptance'")
s=s.replace('coordinator-control-flow.json','coordinator-control-flow-v2.json')
out=R/'test_nav_kit7_coordinator_v2.cjs';assert not out.exists();out.write_text(s)
s=(R/'test_nav_kit7_command.cjs').read_text().replace('orchestrate_nav_kit7.js','orchestrate_nav_kit7_v2.js').replace('command-flow-controls.json','command-flow-controls-v2.json').replace('tested-command-function.js','tested-command-function-v2.js')
out=R/'test_nav_kit7_command_v2.cjs';assert not out.exists();out.write_text(s)
print('V2_PREPARED')

