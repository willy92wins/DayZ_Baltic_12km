"""Create isolated native recheck inputs only after all candidate binary gates."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'kit7-overlap-native-20261026';old=R/'kit7-water-native-20261026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read(R/'package-kit7-contact-only-20261026/verification.json')
assert v['status']=='NINETEEN_GEOMETRY_DELTA_PACKAGE_PASS'
assert read(R/'river-kit7-contact-only-20261026/compiled-contact-review.json')['status']=='PACKED_KIT7_OVERLAP_CONTACT_PASS'
assert read(old/'full/result.json')['failure_count']==19
accepted=read(R/'kit7-contact-only-review-20261026/accepted.json')
assert accepted['status']=='ACCEPTED_NATIVE_RECHECK'
assert all(sha(Path(p))==h for p,h in accepted['inputs'].items())
O.mkdir(exist_ok=False);mod=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Overlap');assert not mod.exists();(mod/'Addons').mkdir(parents=True)
base=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Native/Addons')
paths={n:base/n for n in ('narva_trial.pbo','baltic_water_v30.pbo')}
paths['baltic_stream_pilot.pbo']=R/'package-kit7-contact-only-20261026/Addons/baltic_stream_pilot.pbo'
expected={'narva_trial.pbo':'10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc','baltic_water_v30.pbo':'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43','baltic_stream_pilot.pbo':v['pbo_sha256']}
deployed={};inputs={}
for n,p in paths.items():
 assert sha(p)==expected[n];dest=mod/'Addons'/n;shutil.copyfile(p,dest);assert sha(dest)==expected[n]
 deployed[str(dest)]=expected[n];inputs[str(p)]=expected[n]
missions={k:Path('C:/temp/DayZ_MCP_130_dev/mpmissions')/n for k,n in [('full','BalticKit7OverlapWater.BalticTrial'),('calibration','BalticKit7OverlapCalibration.BalticTrial')]}
parent=read(old/'deployment.json');producers={}
for k,p in missions.items():
 p.mkdir(exist_ok=False);src=Path(parent['missions'][k])/'init.c';shutil.copyfile(src,p/'init.c');assert sha(src)==parent['producers'][k]==sha(p/'init.c')
 producers[k]=sha(src);inputs[str(src)]=sha(src);inputs[str(p/'init.c')]=sha(src);(O/k).mkdir()
shutil.copyfile(Path(parent['missions']['full'])/'points.csv',missions['full']/'points.csv');shutil.copyfile(old/'points.json',O/'points.json')
assert len(read(O/'points.json')['points'])==6801 and (O/'points.json').read_bytes()==(old/'points.json').read_bytes()
for p in [Path(__file__),missions['full']/'points.csv',O/'points.json',old/'full/result.json',old/'full/native.log',R/'package-kit7-contact-only-20261026/verification.json',R/'river-kit7-contact-only-20261026/compiled-contact-review.json',W/'tools/water/eval_visual_probe_v31.py',R/'consume_kit7_water_native_v2.py',R/'capture_kit7_water_log.ps1',R/'capture_owned_server_identity.ps1',R/'copy_owned_server_rpt.ps1']:
 inputs[str(p)]=sha(p)
dep=dict(status='PREPARED_BINARY_PASSED_RUNTIME_NOT_ACCEPTED',deployed=deployed,inputs=inputs,missions={k:str(p) for k,p in missions.items()},producers=producers,counts=parent['counts'],mod=mod.name,navmesh_data_server=True,navigation_accepted=False,client_started=False,points_exact_parent=sha(old/'points.json'))
(O/'deployment.json').write_text(json.dumps(dep,indent=2)+'\n')
pre=read(old/'prelaunch.json')
for key in ('executable','bridge_pbo'):
 if key in pre:assert Path(pre[key]).is_file()
# Rebind fresh actual installed files, never infer an engine identity.
engine=Path('E:/SteamLibrary/steamapps/common/DayZ Exp/DayZDiag_x64.exe');bridge=Path(pre['bridge_pbo'])
assert sha(engine)==pre['executable_sha256'] and sha(bridge)==pre['bridge_sha256']
pre.update(parent_prelaunch_sha256=sha(old/'prelaunch.json'));pre.pop('accepted_sha256',None)
(O/'prelaunch.json').write_text(json.dumps(pre,indent=2)+'\n')
code=(R/'consume_kit7_water_native_v2.py').read_text().replace("O=R/'kit7-water-native-20261026'","O=R/'kit7-overlap-native-20261026'")
a=code.index("fix=read(O/'consumer-clock-fix.json')");b=code.index("host=read",a)
code=code[:a]+"""for mapping in (dep['inputs'],accept['inputs']):
 for p,h in mapping.items():assert sha(Path(p))==h,p
"""+code[b:]
(R/'consume_kit7_overlap_native.py').write_text(code)
print(json.dumps(dict(status=dep['status'],deployed=deployed,missions=dep['missions']),indent=2))

