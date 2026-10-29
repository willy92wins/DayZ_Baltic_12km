/* Official-tool adapter for functions.exec. Tokens remain in the caller's isolate. */
((tools, spec, paths, sleep) => {
  const assert=(v,m)=>{if(!v)throw Error(m);};
  const quote=s=>"'"+String(s).replaceAll("'","''")+"'";
  const unpack=r=>{
    assert(!r.isError,'mcp_tool_error');
    const v=r.structuredContent||JSON.parse(r.content.find(x=>x.type==='text').text);
    assert(!v.error && v.ok!==false,'mcp_rejected');return v;
  };
  let sequence=0;
  async function command(argv,seconds){
    const log=spec.root+'/host-'+(++sequence)+'.log';
    const code="import sys;from pathlib import Path;sys.path.insert(0,"+JSON.stringify(paths.quality)+");from build_prism_b3e_ev112 import run_tree;run_tree("+JSON.stringify(argv)+","+JSON.stringify(paths.workspace)+",Path("+JSON.stringify(log)+"),"+seconds+");print(Path("+JSON.stringify(log)+").read_text(encoding='utf-8-sig'))";
    let r=await tools.exec_command({cmd:'& '+quote(paths.python)+' -I -c '+quote(code),workdir:paths.workspace,max_output_tokens:2000});
    let output=r.output;
    while(r.session_id){r=await tools.write_stdin({session_id:r.session_id,chars:'',yield_time_ms:1000,max_output_tokens:2000});output+=r.output;}
    assert(r.exit_code===0,'host_command_failed:'+log);
    return JSON.parse(output.trim());
  }
  async function save(name,value){
    assert(/^[a-z-]+\.json$/.test(name),'receipt_name');
    const raw=JSON.stringify(value,null,2)+'\n';
    const cmd='$ErrorActionPreference=\'Stop\'; $receiptStream=[IO.File]::Open('+quote(spec.root+'/'+name)+',[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None); try { $receiptBytes=[Text.UTF8Encoding]::new($false).GetBytes('+quote(raw)+'); $receiptStream.Write($receiptBytes,0,$receiptBytes.Length); $receiptStream.Flush($true) } finally { $receiptStream.Dispose() }';
    const r=await tools.exec_command({cmd,workdir:paths.workspace,max_output_tokens:500});
    assert(r.exit_code===0,'receipt_write');
  }
  return {
    now:()=>new Date().toISOString(),millis:()=>Date.now(),sleep,save,
    gate:()=>command([paths.python,'-I','-c',"import sys;sys.path.insert(0,"+JSON.stringify(paths.quality)+");import prepare_contact_b3g1_ev112 as p;p.main()",'gate','--arm',spec.arm,'--sha',spec.seal],120),
    preflight:async request=>{const r=unpack(await tools.mcp__dayz_mcp_130__dayz_test_run({...request,preflight:true}));await save('preflight.json',{request:{...request,preflight:true},status:r.status,preflight:r.preflight,phase:r.phase,error_code:r.error_code,at:new Date().toISOString()});assert(r.status==='succeeded'&&r.preflight===true,'preflight_failed');},
    launch:async request=>{const r=unpack(await tools.mcp__dayz_mcp_130__dayz_test_run(request));return Object.fromEntries(['status','run_id','phase','elapsed_s','error_code','cleanup_degraded','artifacts_paths'].map(k=>[k,r[k]]));},
    acquire:async run=>unpack(await tools.mcp__dayz_mcp_130__session_acquire_wait({max_wait_s:30,purpose:'B3G1 own run '+run})),
    heartbeat:async token=>{const r=unpack(await tools.mcp__dayz_mcp_130__session_heartbeat({lease_token:token}));assert(r.status==='active','heartbeat_not_active');},
    bridge:async()=>unpack(await tools.mcp__dayz_mcp_130__bridge_status({})),
    host:(name,proc,run)=>command(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',paths.quality+'/capture_contact_b3g1_identity.ps1','-ServerProcessId',String(proc.pid),'-ExpectedStartUtc',proc.creation_time_utc,'-ExpectedMission',spec.mission,'-RunId',run,'-OutputPath',spec.root+'/'+name],60),
    observe:ready=>command(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',paths.quality+'/observe_contact_b3g1.ps1','-Directory',spec.root,'-ReadyUtc',ready],20),
    close:async run=>unpack(await tools.mcp__dayz_mcp_130__dayz_test_close({run_id:run,graceful_timeout_s:5})),
    stop:async run=>unpack(await tools.mcp__dayz_mcp_130__dayz_test_stop({run_id:run})),
    release:async token=>{const r=unpack(await tools.mcp__dayz_mcp_130__session_release({lease_token:token}));return {released:r.released,ok:r.ok,cleanup:r.cleanup,cleanup_degraded:r.cleanup_degraded};},
    status:async()=>{const r=unpack(await tools.mcp__dayz_mcp_130__session_status({}));return {self:r.self,pending_commands:r.pending_commands,cleanup_degraded:r.cleanup_degraded};}
  };
})
