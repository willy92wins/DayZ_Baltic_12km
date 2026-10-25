"""Close only the authorized server scope. Preserve strict FAIL for concrete joints."""
from pathlib import Path
import hashlib,json,sys,datetime
O=Path(__file__).parent;D=O/'runtime-eval-runtime-b-20261019'
sys.path.insert(0,str(O));from eval_bridge_regression_ev112 import load_rows
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
evidence={}
def read(p):
 p=O/p;evidence[str(p)]=sha(p);return json.loads(p.read_text(encoding='utf-8'))
deploy=read('deploy-runtime-b.json');review=read('build-review-closure-runtime-b.json')
assert review['critical_major_open']==0 and review['ready_for_server_probe'] and review['review_round']==2
assert review['deploy_sha256']==sha(O/'deploy-runtime-b.json')
assert all(sha(p)==h for p,h in deploy['evidence'].items())
assert all(sha(p)==h for p,h in deploy['probe_binding'].items())
for name,key in [('narva_trial.pbo','world_sha256'),('baltic_water_v30.pbo','water_sha256')]:assert sha(Path(deploy['mod'])/'Addons'/name)==deploy[key]
accept=read('runtime-eval-runtime-b-20261019/acceptance.json')
kit=read('runtime-eval-runtime-b-20261019/kit-g8.json');bs=read('runtime-eval-runtime-b-20261019/eval-bridges-shores.json')
bridge=read('runtime-eval-runtime-b-20261019/bridge-regression.json');dam=read('runtime-eval-runtime-b-20261019/dam.json')
capture=read('runtime-capture-runtime-b-20261019/capture.json');life=read('runtime-capture-runtime-b-20261019/lifecycle.json')
temporal=read('water-temporal-runtime-b/diagnosis.json');tlife=read('water-temporal-runtime-b/lifecycle.json')
view=read('personal-view-runtime-b/route.json')
points=read('probe-runtime-b/points.json');rows=load_rows(D/'baltic_bridge_probe_v2.log',points)
oldpoints=read('probe-c/points.json');oldrows=load_rows(O/'runtime-eval-ae-20261019/baltic_bridge_probe_v2.log',oldpoints)
assert sha(D/'baltic_bridge_probe_v2.log')==capture['raw_log_sha256']==accept['raw_log_sha256']
assert capture['world_sha256']==deploy['world_sha256'] and capture['water_sha256']==deploy['water_sha256']
assert accept['terrain_sha256']==deploy['terrain_sha256']
required=[p for p in points if p['family']=='kit' and p.get('expect') in ('wet','dry')]
bad=[p['id'] for p in required if (rows[p['id']]['depth']>0)!=(p['expect']=='wet')]
pending=[p for p in points if p['family']=='kit' and p.get('expect')=='test' and rows[p['id']]['depth']<=0]
oldpending=[p for p in oldpoints if p['family']=='kit' and p.get('expect')=='test' and oldrows[p['id']]['depth']<=0]
concrete_new=set(p['id'] for p in pending)-set(p['id'] for p in oldpending)
checks=dict(frame=capture['status']=='CAPTURED_FRAME_VALID' and capture['captured_rows']==4114,
 bridges_shores=bs['pass'] is True,no_bridge_regression=bridge['status']=='PASS',dam=dam['pass'] is True,
 required_kit=len(required)==2450 and not bad,only_known_concrete_failures=set(kit['failures'])<= {'lip_joint_dry'} and not concrete_new,
 kit_command_only_expected_failure=all(r['rc']==(1 if r['step']=='kit' and pending else 0) for r in accept['steps']),
 engine_ground_matches=max(v['maximum'] for v in accept['ground_match_diagnostic_by_family'].values())<=.05,
 corrected_points_all_temporal=temporal['required_points_match_all_samples'],temporal_controls=temporal['controls_match_all_samples'],
 temporal_rows=temporal['rows']==240,
 temporal_duration_and_fixed_ground=all(58000<=v['duration_ms']<=120000 and v['ground_range'][0]==v['ground_range'][1] for v in temporal['points'].values()),
 personal_installed=all(sha(Path(view['mission'])/p)==h for p,h in view['live_files'].items()),
 personal_not_launched=view['status']=='INSTALLED_AND_PREPARED_NOT_LAUNCHED_NOT_VISUALLY_ACCEPTED')
for label,c,l in [('probe',capture,life),('temporal',temporal,tlife)]:
 checks[label+'_closed']=l['run_id']==c['run_id'] and l['close']['run_id']==c['run_id'] and l['close']['graceful'] and l['close']['run_retired'] and not l['close']['stop_required']
 checks[label+'_released']=l['release']['ok'] and l['postclose']['self']['state']=='none' and not l['postclose']['owner_present']
assert all(checks.values()),checks
corrected={str(i):dict(kind=next(p['kind'] for p in points if p['id']==i),depth_before=oldrows[i]['depth'],depth_after=rows[i]['depth'],ground_after=rows[i]['ground'],temporal=temporal['points'][str(i)]) for i in (2733,3807,3808,3836)}
out=dict(status='AUTHORIZED_SERVER_SCOPE_COMPLETED_WITH_EXPLICIT_PENDING',time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=checks,
 world_sha256=deploy['world_sha256'],water_sha256=deploy['water_sha256'],terrain_sha256=deploy['terrain_sha256'],mod=deploy['mod'],review=review['verdict'],strict_runtime_verdict=accept['status'],kit_g8_passed=kit['passed'],kit_required=dict(passed=len(required)-len(bad),total=len(required)),kit_unclassified_reference_points=3000-sum(p['family']=='kit' and p.get('expect') in ('wet','dry','test') for p in points),concrete_pending_count=len(pending),concrete_pending_ids=[p['family_id'] for p in pending],concrete_same_ids_as_first_probe=set(p['id'] for p in pending)==set(p['id'] for p in oldpending),probe_rows=len(rows),temporal_rows=temporal['rows'],dam_points=dam['points'],dam_rows=dam['rows'],bridge_sites=len(bs['bridges']),bridge_passed=sum(v['pass'] for v in bs['bridges'].values()),bridge_01518=bridge['sites']['015-18'],shore_wet_total=sum(p['family']=='shores' and p['expect']=='wet' for p in points),shore_dry_total=sum(p['family']=='shores' and p['expect']=='dry' for p in points),shores=bs['shores'],corrected_points=corrected,ground_match=accept['ground_match_diagnostic_by_family'],probe_run_id=capture['run_id'],temporal_run_id=temporal['run_id'],evidence=evidence,
 limits=['Kit G8 and strict AND retain FAIL for the known concrete lip/joint tests permitted pending by plan section5; no threshold was changed.','Protected 015-45 disk60m remains PENDING, never PASS.','Temporal check is30samples over one minute at fixed weather, not proof for all weather or player wetness.','Central OT4 and forest statistical/phase/domain limits remain as in OT7R1/R2; no global shoreline, FPS, visual or80-100player claim.','Personal mission installed and hashes checked, client not launched. No push.'])
target=O/'runtime-b-closure.json';assert not target.exists();target.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ('status','strict_runtime_verdict','kit_required','concrete_pending_count','concrete_same_ids_as_first_probe','probe_run_id','temporal_run_id')},indent=2))
