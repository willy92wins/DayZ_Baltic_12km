/* Adapter-driven coordinator. No HTTP, daemon bypass or credentials on disk.
 * Consumer: functions.exec supplies only official MCP tools and pinned host helpers.
 * Node fixture tests use the same state machine. */
(() => {
  const assert = (v, m) => { if (!v) throw Error(m); };
  async function runArm(api, spec) {
    const request = {project:'DayZ_MCP',mode:'server',mission:spec.mission,
      extra_mods:[spec.mod],build:false,clean:false,pack_only:false,preflight:false,
      no_base_mods:true,no_file_patching:true,navmesh_data_server:true,takeover:false,
      server_wait_s:300,on_busy:'queue',wait_for_box_s:600};
    let run=null,token=null,adopted=false,hb=null,hbError=null,resolveStop;
    let stopped=false,outcome={status:'NOT_ADMITTED'},error=null;
    const stopSignal=new Promise(resolve=>{resolveStop=resolve;});
    const heartbeats=[];
    const check=()=>{if(hbError)throw Error('heartbeat_failed');};
    const cleanup={close:null,release:null,self:null,own_run_present:null,pending_commands:null,cleanup_degraded:[],error:null,cleanup_error:null};
    try {
      await api.gate(spec);
      await api.preflight(request);
      const launched=await api.launch(request);
      run=launched.run_id||null;
      await api.save('launch.json',{...launched,request,accepted_sha256:spec.seal,readiness_budget_s:300,capture_budget_s:180});
      assert(launched.status==='succeeded' && launched.run_id,'launch_not_succeeded');
      run=launched.run_id;
      const adoptedResult=await api.acquire(run);
      token=adoptedResult.lease_token;
      assert(token && adoptedResult.adopted_run?.run_id===run && adoptedResult.adopted_run?.ok,'adopted_wrong_run');
      adopted=true;
      hb=(async()=>{
        while(!stopped){
          try {await api.heartbeat(token);heartbeats.push({at:api.now(),ok:true});}
          catch {hbError='heartbeat_failed';heartbeats.push({at:api.now(),ok:false});break;}
          await Promise.race([api.sleep(10000),stopSignal]);
        }
      })();
      await api.save('adoption.json',{run_id:run,status:'OWN_RUN_ADOPTED',at:api.now()});
      const readyEnd=api.millis()+300000;let bridge,own;
      while(true){
        check();assert(api.millis()<=readyEnd,'readiness_deadline');
        bridge=await api.bridge();check();own=bridge.lifecycle?.runs?.find(x=>x.run_id===run);
        assert(own,'own_run_missing');
        const p=bridge.server_peer;
        if(p?.run_id===run && p.binding_state==='BOUND' && p.version_state==='ok' && Number.isFinite(p.bound_last_poll_age_s) && p.bound_last_poll_age_s>=0 && p.bound_last_poll_age_s<10)break;
        await api.sleep(2000);
      }
      const ready=api.now(),deadline=new Date(Date.parse(ready)+180000).toISOString();
      await api.save('readiness.json',{run_id:run,ready_utc:ready,capture_deadline_utc:deadline});
      const p=bridge.server_peer;
      await api.save('mcp-identity.json',{run_id:run,server_run_id:p.run_id,server_binding:p.binding_state,version_state:p.version_state,poll_age_s:p.bound_last_poll_age_s,processes:own.processes,client_diagnostics:own.client_diagnostics});
      assert(own.processes?.length===1 && own.processes[0].role==='server','unexpected_processes');
      const proc=own.processes[0];
      await api.host('host-identity.json',proc,run);check();
      while(true){
        check();assert(api.millis()<=Date.parse(deadline),'capture_deadline');
        const observed=await api.observe(ready);check();
        if(observed.status==='CAPTURED_NOT_JUDGED')break;
        assert(['PENDING_NATIVE_LOG','PENDING_SAMPLES'].includes(observed.status),'observer_status');
        await api.sleep(2000);
      }
      await api.host('host-after.json',proc,run);check();
      outcome={status:'CAPTURED_PENDING_CONSUMER',run_id:run};
    } catch(e) {
      error=String(e.message||e);outcome={status:'FAILED',run_id:run,error};
    } finally {
      cleanup.error=error;
      if(adopted){
        try {cleanup.close=await api.close(run);cleanup.closed_utc=api.now();assert(cleanup.close.run_id===run && cleanup.close.run_retired===true,'run_not_retired');}
        catch(e){cleanup.cleanup_error=String(e.message||e);}
      }
      stopped=true;resolveStop();if(hb)await hb;
      cleanup.heartbeat_ended_utc=api.now();
      if(token){try{cleanup.release=await api.release(token);}catch(e){cleanup.cleanup_error=String(e.message||e);}}
      // close requires adoption. Official stop queues its own exact-run adoption;
      // never close the unrelated run returned by a failed/wrong adoption.
      if(run && cleanup.close?.run_retired!==true){
        try{cleanup.stop=await api.stop(run);assert(cleanup.stop.run_id===run && cleanup.stop.status==='succeeded','stop_failed');}
        catch(e){cleanup.cleanup_error=String(e.message||e);}
      }
      try {
        const terminal=(run||token)?await api.status():{};cleanup.self=terminal.self;cleanup.pending_commands=terminal.pending_commands;cleanup.cleanup_degraded=terminal.cleanup_degraded;
        // Retirement is demonstrated by close, never inferred from absent status fields.
        cleanup.own_run_present=run ? !(cleanup.close?.run_retired===true || cleanup.stop?.status==='succeeded') : null;
      }catch(e){cleanup.cleanup_error=String(e.message||e);}
      try{await api.save('heartbeats.json',{events:heartbeats,failure:hbError});await api.save('cleanup.json',cleanup);}
      catch(e){cleanup.cleanup_error='receipt_write_failed';}
    }
    if(cleanup.cleanup_error || hbError || ((run||token) && (cleanup.own_run_present || (token&&!cleanup.release?.released) || cleanup.self?.state!=='none' || cleanup.pending_commands!==0 || cleanup.cleanup_degraded?.length)))outcome={status:'FAILED_CLEANUP',run_id:run,error:error||hbError||cleanup.cleanup_error};
    try{await api.save('outcome.json',outcome);}catch{outcome={status:'FAILED_RECEIPTS',run_id:run};}
    return outcome;
  }
  return {runArm};
})()
