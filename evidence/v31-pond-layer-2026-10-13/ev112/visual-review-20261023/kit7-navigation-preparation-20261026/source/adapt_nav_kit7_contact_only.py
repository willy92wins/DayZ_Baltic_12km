from pathlib import Path
R=Path(__file__).parent
p=R/'orchestrate_nav_kit7.js';old=p.read_text();backup=R/'nav-kit7-preparation-20261026/orchestrate-before-contact-only.js';assert not backup.exists();backup.write_text(old)
new=old.replace('kit7-water-native-20261026/full/result.json','kit7-overlap-native-20261026/full/result.json').replace('@DayZ_Baltic_EV112_Kit7Native','@DayZ_Baltic_EV112_Kit7Overlap').replace('46244e7f2abc6bd2d07be828097325ec9bba9c672b48bfcef177895b87380b2d','3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6')
needle="throw Error('Kit7 physical gate missing');"
new=new.replace(needle,needle+"\nif(physical.failure_count!==0||Object.keys(physical.packages||{}).length!==4||Object.keys(prepared.packages||{}).length!==4||Object.entries(prepared.packages).some(([path,hash])=>physical.packages[path]!==hash))throw Error('Kit7 physical package binding missing');")
p.write_text(new)
p=R/'test_nav_kit7_coordinator.cjs';s=p.read_text();(R/'nav-kit7-preparation-20261026/coordinator-test-before-contact-only.cjs').write_text(s)
s=s.replace("const failedWrapper=","const packages={'world':'worldhash','water':'waterhash','pilot':'3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6','bridge':'bridgehash'};\n const gateFailure=['physics_fail','physics_missing','physics_mismatch'].includes(name);\n const failedWrapper=")
s=s.replace("status:'READY_AFTER_CODE_REVIEW',observer_sha256:'observer'","status:'READY_AFTER_CODE_REVIEW',observer_sha256:'observer',packages")
s=s.replace("status:'SERVER_PROBE_PASS',points:6801,identity_bound:true,inputs_unchanged:true","status:name==='physics_fail'?'SERVER_PROBE_FAIL':'SERVER_PROBE_PASS',points:6801,identity_bound:true,inputs_unchanged:true,failure_count:name==='physics_fail'?19:0,packages:name==='physics_missing'?undefined:name==='physics_mismatch'?{...packages,pilot:'wrong'}:packages")
s=s.replace("assert.equal(a.takeover,false);launched=true;","assert.equal(a.takeover,false);assert.equal(a.navmesh_data_server,true);assert.deepEqual(a.extra_mods,['@DayZ_Baltic_EV112_Kit7Overlap']);assert(a.mission.endsWith('BalticKit7NavData.BalticTrial'));launched=true;")
s=s.replace("assert.equal(calls.filter(x=>x==='launch').length,1);","if(gateFailure){assert(error);assert.equal(calls.filter(x=>x==='launch').length,0);assert(!active);return {name,passed:true,launches:0,error};}\n assert.equal(calls.filter(x=>x==='launch').length,1);")
s=s.replace("'C_NAV_REQUIRES_OWNED_RECOVERY'","'KIT7_NAV_REQUIRES_OWNED_RECOVERY'")
s=s.replace("['success','delayed_capture'","['physics_fail','physics_missing','physics_mismatch','success','delayed_capture'")
p.write_text(s)
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
p=W/'plans/ev112-kit7-navmesh-generation-20261026.md';s=p.read_text().replace('piloto46244e7f','piloto3d9550bf');s+='\nLa puerta física usa exclusivamente la repetición kit7-overlap-native-20261026:6801puntos,0fallos y los cuatro paquetes exactos del lanzamiento. Un PASS del piloto anterior o un resultado sin identidad de paquetes debe impedir el arranque. El plan sigue pendiente de revisión y resultado físico; no hay generación activa.\n';p.write_text(s)
print('NAV_ADAPTED_NOT_READY')

