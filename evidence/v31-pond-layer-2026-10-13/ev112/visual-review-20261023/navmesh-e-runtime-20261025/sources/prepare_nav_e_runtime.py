from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=R/'navmesh-guarded-e-v9-probe'
receipt_path=out/'deployment.json';assert not receipt_path.exists()
package=R/'package-guarded-e-nav-v9/verification.json';p=json.loads(package.read_text())
inspection=R/'navmesh-guarded-e-v9/inspection.json';i=json.loads(inspection.read_text())
assert p['status']=='PASS_NAVMESH_PACKED_BYTE_PARITY' and i['status']=='EMPIRICAL_V9_PREFIX_AND_COVERAGE_PASS'
assert p['navmesh_sha256']==i['sha256'] and p['wrp_sha256']=='68aa27355fb02e89aabb96a859e7653295480e6283213fbc050554c1bd5d2a24'
assert p['previous_navmesh_sha256']=='eb0f131e5fc0f80d81c60b1f332d8ecfa6396cab9e09ffd36cd1c8504885c496'
mod=Path('P:/Mods/@DayZ_Baltic_EV112_GuardedENavV9');assert not mod.exists()
sources={R/'package-guarded-e-nav-v9/Addons/narva_trial.pbo':p['pbo_sha256'],Path('P:/Mods/@DayZ_Baltic_EV112_GuardedE/Addons/baltic_stream_pilot.pbo'):'c0be9abc9d36ee19c636325b825dbf09880a9dc31b5dfb8432e0f91d0e1cfa87',Path('P:/Mods/@DayZ_Baltic_EV112_GuardedE/Addons/baltic_water_v30.pbo'):'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43'}
for src,digest in sources.items():assert sha(src)==digest
(mod/'Addons').mkdir(parents=True);deployed={}
for src,digest in sources.items():
    dest=mod/'Addons'/src.name;shutil.copyfile(src,dest);assert sha(dest)==digest;deployed[str(dest)]=digest
mission=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticGuardedENavV9.BalticTrial')
inputs={str(path):sha(path) for path in (package,inspection,mission/'init.c',mission/'queries.csv',out/'reference.json',Path(__file__))}
inputs.update(deployed)
launch=dict(project='DayZ_MCP',mode='server',mission=str(mission),extra_mods=[mod.name],base_mods=[],no_base_mods=True,no_file_patching=True,build=False,takeover=False,wait_for_box_s=0,navmesh_data_server=False)
(out/'launch-server.json').write_text(json.dumps(launch,indent=2)+'\n',encoding='utf-8')
receipt=dict(status='DEPLOYED_NAV_E_PENDING_ENGINE',deployed=deployed,inputs=inputs,mission=str(mission),old_mods_preserved=True,limits=['No path/actor acceptance until fresh server loads this package and produces validated query evidence.','NavE corresponds to terrain E only; F is different.'])
receipt_path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2))
