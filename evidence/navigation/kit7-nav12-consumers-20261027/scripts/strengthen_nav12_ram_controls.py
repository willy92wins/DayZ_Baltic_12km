from pathlib import Path
import re,json
R=Path(__file__).parent;p=R/'test_nav12_ram_flow.cjs';s=p.read_text()
old=s
s=s.replace("let reads=0,commands=0,commandExpired=false;", "let reads=0,commands=0,commandExpired=false,captureFinished=false;")
s=s.replace("if(++commands>150)","if(a.cmd.includes('capture_owned_server_identity.ps1'))assert(captureFinished,'Identity hashing must follow measurement completion');\n    if(++commands>150)")
s=s.replace("write_stdin:async a=>{polls++;", "write_stdin:async a=>{polls++;if(a.session_id===20)captureFinished=true;")
s=s.replace("assert.equal(a.navmesh_data_server,false);", "assert.equal(a.navmesh_data_server,false);assert.deepEqual(a.extra_mods,mode==='chernarus_success'?[]:['@DayZ_Baltic_EV112_Kit7Nav12']);")
s=s.replace("['success','slow_readiness'", "['success','chernarus_success','slow_readiness'")
pattern=r"key=>key==='nav12RamConfig'\?(\{[^\n]+\}):'\(x\)=>x'"
m=re.search(pattern,s);assert m
fixture=json.loads(m.group(1))
s=s[:m.start()]+"key=>key==='nav12RamConfig'?fixture:'(x)=>x'"+s[m.end():]
anchor="  const execute=new Function("
assert s.count(anchor)==1
s=s.replace(anchor,"  const fixture="+json.dumps(fixture)+";if(mode==='chernarus_success'){fixture.passes[0].world='ChernarusPlus';fixture.passes[0].mission=fixture.passes[0].mission.replace('.BalticTrial','.ChernarusPlus');}\n"+anchor)
anchor=" ['cmd_direct_heartbeat',"
assert s.count(anchor)==1
s=s.replace(anchor," ['hash_during_measurement',source.replace('// Start the read-only sampler',\"await cmd('capture_owned_server_identity.ps1'); // Start the read-only sampler\")],\n"+anchor)
assert s!=old
p.write_text(s)
print('RAM controls cover both map mod sets, delayed lease recovery and hashing outside the measurement window')
