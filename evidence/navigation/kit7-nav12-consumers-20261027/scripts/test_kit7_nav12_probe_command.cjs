const fs=require('node:fs'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const R='E:/DayZ-Baltic-Build/shape-repair-20261025';
const source=fs.readFileSync(R+'/orchestrate_kit7_nav12_probe.js','utf8');
const expr=source.split('\n').find(l=>l.startsWith('const cmd=')).replace(/^const cmd=/,'').replace(/;\s*$/,'');
(async()=>{
 const cases=[];
 for(const mode of ['immediate_success','immediate_failure','delayed_success','delayed_failure','fragmented_json','missing_exitcode','background_capture','leased_delayed_success']){
  let polls=0,beats=0;
  const tools={exec_command:async()=>mode==='immediate_success'?{exit_code:0,output:'ok'}:mode==='immediate_failure'?{exit_code:2,output:'known failure'}:{session_id:77,output:mode==='fragmented_json'?'{"a":':''},write_stdin:async()=>{polls++;return mode==='missing_exitcode'?{output:'incomplete'}:{exit_code:mode==='delayed_failure'?7:0,output:mode==='delayed_failure'?'known failure':mode==='fragmented_json'?'1}':'ok'};},mcp__dayz_mcp_130__session_heartbeat:async()=>{beats++;return {ok:true};}};
  const cmd=new Function('tools','w','token','parse','beat','return ('+expr+');')(tools,'unused',mode.startsWith('leased')?'FAKE':null,x=>x,async()=>tools.mcp__dayz_mcp_130__session_heartbeat());
  let error=null,q;try{q=await cmd('fixture',10000,mode==='background_capture');}catch(e){error=e.message;}
  if(mode.endsWith('failure'))assert.equal(error,'known failure');
  else if(mode==='missing_exitcode')assert.equal(error,'incomplete');
  else {assert.equal(error,null);if(mode==='background_capture'){assert.equal(q.session_id,77);assert.equal(polls,0);}else{assert.equal(q.exit_code,0);if(mode==='fragmented_json')assert.deepEqual(JSON.parse(q.output),{a:1});}}
  if(mode==='leased_delayed_success'){assert.equal(polls,1);assert.equal(beats,1);}
  cases.push({mode,polls,beats,passed:true});
 }
 const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
 const result={status:'COMMAND_COMPLETION_CONTROLS_PASS',coordinator_sha256:hash(source),tested_function_sha256:hash(expr),cases};
 fs.writeFileSync(R+'/kit7-nav12-consumer-20261027/command-flow-controls.json',JSON.stringify(result,null,2)+'\n',{flag:'wx'});
 fs.writeFileSync(R+'/kit7-nav12-consumer-20261027/tested-command-function-v2.js',expr+'\n',{flag:'wx'});
 console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
