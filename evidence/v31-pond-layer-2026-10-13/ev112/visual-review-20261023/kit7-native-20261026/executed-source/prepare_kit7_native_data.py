"""Prepare two isolated server surveys; never start/stop a DayZ process."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,uuid
if sys.flags.optimize:
 raise SystemExit('optimized Python disables preparation gates; refused')
import numpy as np
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
S=R/'stage-kit7-fc-20261026';M=R/'river-kit7-merged-byteexact-20261026';O=R/'kit7-native-20261026'
mod=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Native')
missions=Path('C:/temp/DayZ_MCP_130_dev/mpmissions')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
gate=read(R/'kit7-native-data-review-20261026/accepted.json')
assert gate['status']=='REVIEW_ACCEPTED_PREPARE_ONLY' and gate['inputs'] and all(sha(p)==h for p,h in gate['inputs'].items())
required=[Path(__file__),W/'tools/terrain/native_height_probe_ev112.py',W/'tools/water/streambed_kit_v31.py',W/'tools/vegetation/eval_forest_boundary_probe_v31.py',W/'tools/vegetation/prepare_forest_boundary_probe_v31.py',W/'tools/vegetation/review_visual_forest_support_v31.py',W/'missions/BalticForestBoundaryV1.BalticTrial/init.c',M/'terrain-buried.npz',M/'bury-work/fp0/footprint.npz',R/'rectangle-pilot-f-merged/terrain-buried.npz',S/'stage-report.json',S/'forest-support-review-full.json',S/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp',B/'stage-nonforest-c/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp',R/'forest-boundary-full-f/points.json',R/'package-kit7-fc-world-20261026/verification.json',R/'package-kit7-fc-pilot-v2-20261026/verification.json']
required.append(Path(read(S/'stage-report.json')['forest_reference']['path']))
required.append(W/'tools/terrain/wrp0wzd.py')
assert {str(p) for p in required}<=set(gate['inputs'])
v=read(R/'package-kit7-fc-world-20261026/verification.json');p=read(R/'package-kit7-fc-pilot-v2-20261026/verification.json')
assert v['status']=='OBJECTS_AND_PAYLOAD_VERIFIED_BOUNDARY_PENDING' and p['status']=='PASS_201_MODELS_BYTE_EXACT_CONFIG_EXTENDED'
assert v['pbo_sha256']=='10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc' and p['pbo_sha256']=='46244e7f2abc6bd2d07be828097325ec9bba9c672b48bfcef177895b87380b2d'
sources={'narva_trial.pbo':R/'package-kit7-fc-world-20261026/Addons/narva_trial.pbo','baltic_stream_pilot.pbo':R/'package-kit7-fc-pilot-v2-20261026/Addons/baltic_stream_pilot.pbo','baltic_water_v30.pbo':Path('P:/Mods/@DayZ_Baltic_EV112_MidpointCNavV9/Addons/baltic_water_v30.pbo')}
expected={'narva_trial.pbo':v['pbo_sha256'],'baltic_stream_pilot.pbo':p['pbo_sha256'],'baltic_water_v30.pbo':'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43'}
assert all(sha(path)==expected[name] for name,path in sources.items())
forest_mission=missions/'BalticKit7Boundary.BalticTrial';height_mission=missions/'BalticKit7Heights.BalticTrial'
assert missions.is_dir() and Path('P:/DZ').is_dir() and Path('P:/Mods').is_dir()
assert all(not q.exists() for q in (O,mod,forest_mission,height_mission))
O.mkdir();(mod/'Addons').mkdir(parents=True)
for name,path in sources.items():shutil.copyfile(path,mod/'Addons'/name)
packages={str(mod/'Addons'/name):sha(mod/'Addons'/name) for name in sources}
assert {Path(k).name:h for k,h in packages.items()}==expected
args=[sys.executable,'-I',str(W/'tools/vegetation/prepare_forest_boundary_probe_v31.py'),'--build',str(B),'--stage',str(S),'--merged',str(M),'--mod',str(mod),'--output',str(O/'forest'),'--mission',str(forest_mission)]
with (O/'forest-prepare.log').open('wb') as f:subprocess.run(args,cwd=W,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=600)
forest=read(O/'forest/points.json');support=read(S/'forest-support-review-full.json');old=read(R/'forest-boundary-full-f/points.json')
assert {a['id'] for a in forest['objects']}==set(support['boundary_pending']['ids']) and len(forest['objects'])==3727
assert forest['objects']==old['objects'] and forest['points']==old['points'] and forest['csv_sha256']==old['csv_sha256']
assert forest['mod_sha256']==expected and forest['source_wrp_sha256']==v['source_wrp_sha256'] and forest['terrain_sha256']==sha(M/'terrain-buried.npz')
(O/'forest/preparation-verification.json').write_text(json.dumps(dict(status='BOUNDARY_PREPARED_NOT_RUN',objects=len(forest['objects']),points=len(forest['points']),all_records_exact_F=True,IDs_exact_full_support_report=True,native_result_inherited=False),indent=2)+'\n')
sys.path.insert(0,str(W/'tools/terrain'));import native_height_probe_ev112 as height
before=R/'rectangle-pilot-f-merged/terrain-buried.npz';after=M/'terrain-buried.npz'
assert sha(before)=='caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc' and sha(after)=='815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40'
a=np.load(before)['heights'];b=np.load(after)['heights'];points=height.points_for_changes(a,b);counts=height.verify_coverage(a,b,points)
assert counts['changed_vertices']==read(S/'stage-report.json')['terrain_vertices']==3430
height_mission.mkdir();init=W/'missions/BalticForestBoundaryV1.BalticTrial/init.c'
shutil.copyfile(init,height_mission/'init.c');(height_mission/'points.csv').write_text(height.csv_text(points),encoding='ascii')
survey=str(uuid.uuid4());(height_mission/'identity.txt').write_text(survey+'\n',encoding='ascii')
inputs={str(path):sha(path) for path in [before,after,Path(height.__file__),W/'tools/water/streambed_kit_v31.py',W/'tools/vegetation/eval_forest_boundary_probe_v31.py',init]}
doc=dict(schema='ev112-native-height-v1',survey_id=survey,points=points,counts=counts,terrain_before=str(before),terrain_after=str(after),producer=str(init),inputs=inputs,packages=packages,mission=str(height_mission),mission_hashes={str(height_mission/n):sha(height_mission/n) for n in ('init.c','points.csv','identity.txt')})
height.verify_binding(doc);(O/'heights').mkdir();(O/'heights/points.json').write_text(json.dumps(doc,indent=2)+'\n')
(O/'heights/preparation.json').write_text(json.dumps(dict(status='HEIGHTS_PREPARED_NOT_RUN',counts=counts,survey_id=survey,manifest_sha256=sha(O/'heights/points.json')),indent=2)+'\n')
frozen={**gate['inputs'],**packages}
for mission in (forest_mission,height_mission):frozen.update({str(mission/n):sha(mission/n) for n in ('init.c','points.csv','identity.txt')})
for path in (O/'forest/points.json',O/'heights/points.json'):frozen[str(path)]=sha(path)
assert all(sha(path)==digest for path,digest in gate['inputs'].items())
deployment=dict(status='PREPARED_BOUND_SURVEYS_NOT_RUN',mod=str(mod),deployed=packages,inputs=frozen,missions=dict(forest=str(forest_mission),heights=str(height_mission)),surveys=dict(forest=forest['survey_id'],heights=survey),counts=dict(forest_objects=len(forest['objects']),forest_points=len(forest['points']),heights=counts),client_started=False,navmesh_data_server=True,navigation_accepted=False)
(O/'deployment.json').write_text(json.dumps(deployment,indent=2)+'\n');print(json.dumps({k:v for k,v in deployment.items() if k not in ('inputs','deployed')},indent=2))
