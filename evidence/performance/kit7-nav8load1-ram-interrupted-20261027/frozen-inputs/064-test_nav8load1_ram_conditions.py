"""Actual mission/consumer compatibility controls; not RAM evidence."""
from pathlib import Path
import hashlib,json,sys,tempfile
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=R/'kit7-nav8load1-ram-ab-20261027'
sys.path.insert(0,str(W/'tools/performance'))
from compare_server_baseline_ev112 import conditions_identity,require_equivalent
manifest=json.loads((D/'missions.json').read_text(encoding='utf-8-sig'));checks=[];loaded=[];refs=[]
def reference(mission,engine,world):
 return dict(world=world,inputs={'config.cfg':'fixture-config','engine.exe':'fixture-engine','package.pbo':'fixture-package'},artifacts=dict(server_config='config.cfg',executable='engine.exe',mission=str(mission),engine=str(engine)),packages={'package.pbo':'fixture-package'})
def rejected(name,operation):
 try:operation()
 except ValueError as e:checks.append(dict(name=name,status='PASS_REJECTED',reason=str(e)))
 else:raise AssertionError(name+' accepted')
for row in manifest['passes']:
 mission=Path(row['mission'])/'init.c';assert hashlib.sha256(mission.read_bytes()).hexdigest()==row['mission_sha256']
 ref=reference(mission,row['profile_log'],row['world']);refs.append(ref)
 loaded.append((dict(world=row['world']),conditions_identity(ref)))
 checks.append(dict(name=f"actual_mission_{row['order']}",status='PASS_CONSUMER_COMPATIBLE'))
require_equivalent(loaded);checks.append(dict(name='six_actual_missions_equivalent',status='PASS'))
with tempfile.TemporaryDirectory(prefix='baltic-nav8load1-conditions-') as tmp:
 p=Path(tmp)/'init.c';row=manifest['passes'][0];source=(Path(row['mission'])/'init.c').read_text(encoding='utf-8-sig')
 old=row['profile_log'].replace('baltic_ab_','baltic_nav8load1_ab_',1);p.write_text(source.replace(row['profile_log'],old),encoding='utf-8')
 rejected('old_wrong_prefix',lambda:conditions_identity(reference(p,old,row['world'])))
 p.write_text(source,encoding='utf-8')
 identical=conditions_identity(reference(p,row['profile_log'],row['world']));assert identical==loaded[0][1]
 require_equivalent([(loaded[0][0],identical)]+loaded[1:]);checks.append(dict(name='identical_temporary_copy_preserves_equivalence',status='PASS'))
 rejected('mismatched_engine_log',lambda:conditions_identity(reference(p,manifest['passes'][1]['profile_log'],row['world'])))
 rejected('wrong_world_guard',lambda:conditions_identity(reference(p,row['profile_log'],'ChernarusPlus')))
 p.write_text(source+'\n// Deliberate fixture-only mission drift\n',encoding='utf-8');changed=conditions_identity(reference(p,row['profile_log'],row['world']))
 rejected('mission_drift_breaks_equivalence',lambda:require_equivalent([(loaded[0][0],changed)]+loaded[1:]))
result=dict(status='PASS_RAM_CONSUMER_CONTRACT_CONTROLS',checks=checks,count=len(checks),native_measurement=False,inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/'missions.json',W/'tools/performance/compare_server_baseline_ev112.py']})
(D/'conditions-controls.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
