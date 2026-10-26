"""Close bounded review findings and freeze runtime inputs; no launch here."""
from pathlib import Path
import hashlib,json,sys
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;O=R/'kit7-water-native-20261026';V=R/'kit7-water-review-20261026'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not (O/'accepted.json').exists()
review=read(V/'review-response.json');completion=read(V/'completion.json');assert not review['is_error'] and not review.get('permission_denials') and completion['exit_code']==0 and completion['inputs_unchanged'] and 'claude-fable-5-1' in review['modelUsage']
contact=read(R/'kit7-contact-controls-discovery-20261026.json');assert contact['points']==contact['dry_controls']==2 and contact['inputs_unchanged']
for k in ('dry_conflicts','wet_missing','ground_expectation_drift','bed_expectation_drift','water_level_drift'):assert not contact[k],k
regression=read(R/'kit7-regression-replay-20261026.json');assert regression['status']=='SOURCE_REGRESSION_REPLAY_PASS' and regression['inherited_points']==4749 and regression['inputs_unchanged']
dep=read(O/'deployment.json');doc=read(O/'points.json');inputs={}
for mapping in (dep['inputs'],read(V/'source-hashes.json'),contact['inputs'],regression['inputs']):
 for p,h in mapping.items():assert sha(Path(p))==h,p;inputs[p]=h
original=read(R/'runtime-rectangle-f/points.json')['points']
assert [{k:v for k,v in p.items() if k not in ('origin_set','original_id')} for p in doc['points'][:4749]]==original
witnesses=doc['points'][-2:];assert all(p['origin_set']=='contact_certificate' and p['expect']=='dry' and p['water_ext'] is None and p['collision_pilot'] for p in witnesses)
assert 'Ran 5 tests' in (O/'consumer-tests.log').read_text(encoding='utf-8-sig') and (O/'consumer-tests.log').read_text(encoding='utf-8-sig').rstrip().endswith('OK')
for p in (Path(__file__),O/'deployment.json',V/'review-response.json',V/'completion.json',R/'kit7-contact-controls-discovery-20261026.json',R/'kit7-regression-replay-20261026.json',R/'capture_kit7_water_log.ps1',R/'consume_kit7_water_native.py',R/'finish_kit7_water_survey.js',R/'capture_owned_server_identity.ps1',R/'copy_owned_server_rpt.ps1',O/'consumer-tests.log'):inputs[str(p)]=sha(p)
result=dict(status='ACCEPTED_FOR_NATIVE_RUNS',review_verdict='SOUND-with-fixes',reviewer='claude-fable-5-1',receiver='Codex',closure=[dict(finding=1,resolution='Both added witnesses screened against native ponds/sea,6352retained vanilla and201custom models:0conflicts.'),dict(finding=2,resolution='Persistent regression generator replayed4749points, source/producer hashes, positive/negative geometry controls,0changedground/0overlaps.'),dict(finding=3,resolution='Both witnesses explicitly required dry, water_ext null, exposed collision true before launch.')],inputs=inputs,limits=['Authorizes bounded native measurements; no runtime PASS yet.','Separate identity consumer checks run/process/mission/CSV/log/package/calibration before accepting.'])
(O/'accepted.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
for kind in ('full','calibration'):(O/kind).mkdir()
print(json.dumps(dict(status=result['status'],frozen_inputs=len(inputs),F_exact=4749,witnesses=len(witnesses))))
