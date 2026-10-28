"""One-shot final adjudication, preparation and immutable prelaunch seal."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');O=R/'dry-road-full-native-20261028';A=R/'dry-road-full-native-adjudication-20261028.json'
sys.path.insert(0,str(W/'tools/quality'))
from buried_roadway_semantics_ev112 import require,verify_frozen
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
require(not A.exists() and not O.exists(),'fresh_targets')
paths=[Path(__file__).resolve(),W/'plans/ev112-dry-road-full-consumer-20261028.md',W/'tools/quality/dry_road_native_consumer_ev112.py',W/'tools/quality/test_dry_road_native_consumer_ev112.py']
for name in ('dry-road-full-consumer-review-20261028','dry-road-full-binder-review-20261028'):
    p=R/name/'completion.json';x=read(p);require(x['returncode']==0 and not x['timeout'] and x['inputs_unchanged'] and x['finish_marker'] and not x['permission_denials'] and x['modelUsage']==['claude-fable-5-1'],'review_not_complete');paths.extend([p,R/name/'review.md'])
for name,key,count in [('dry-road-full-binding-tests-r2-20261028.json','tests',9),('dry-road-full-gate-tests-r2-20261028.json','cases',8),('dry-road-full-flow-tests-r2-20261028.json','rows',7)]:
    p=R/name;x=read(p);require(len(x[key])==count and all(v.get('verified',v.get('expected_outcome_verified',False)) for v in x[key]),'failed_controls:'+name);paths.append(p)
fixture=R/'dry-road-channels-native-fixture-r2-20261028/report.json';fx=read(fixture);verify_frozen(fx['inputs']);require(fx['status']=='CONSUMER_REAL_FIXTURE_REGRESSION_PASS','fixture_failed');paths.append(fixture)
t=R/'dry-road-full-consumer-tests-r2-20261028.json';x=read(t);require(x['status']=='CHANNEL_TESTS_AND_REFINEMENT_PASS' and 'Ran 22 tests' in x['tests'][0]['stderr'] and all(v['returncode']==0 for v in x['tests']),'channel_tests_failed');paths.append(t)
for name in ('prepare_dry_road_full_native_20261028.py','consume_dry_road_full_native_20261028.py','capture_dry_road_full_native_20261028.ps1','finish_dry_road_full_native_20261028.js','check_dry_road_full_gate_20261028.py','test_dry_road_full_binding_r2_20261028.py','test_dry_road_full_gate_r2_20261028.py','test_dry_road_full_flow_r2_20261028.cjs'):paths.append(R/name)
require(read(R/'dry-road-full-binding-tests-r2-20261028.json')['source_sha256']==sha(R/'consume_dry_road_full_native_20261028.py'),'binding_source_changed')
require(read(R/'dry-road-full-gate-tests-r2-20261028.json')['script_sha256']==sha(R/'check_dry_road_full_gate_20261028.py'),'gate_source_changed')
dump(A,dict(status='REVIEWED_PREPARATION_READY',inputs={str(p):sha(p) for p in paths},decision='Codex adjudicated independent Fable reviews and closed the calibration drift counterexample. Native/global acceptance remains pending.'))
active=R/'ACTIVE-WORK.md';active.write_text('# Preparación completa2658 en curso\n\nÚnica operación propia:seal_prepare_dry_road_full_native_20261028.py;seguir su salida.\nDosmisionesnuevas pendientesdeFIFO,norun ni lease. Público7970ae67.\nRevisionesFable236.625s/402s terminadas;22canales,9binding,8gates,7lifecycle pasan.\nNo duplicar scriptsconsumidos ni usarvisitaantigua.\n\n---\n'+active.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
q=subprocess.run([sys.executable,'-I',str(R/'prepare_dry_road_full_native_20261028.py')],capture_output=True,text=True,timeout=330,creationflags=0x08000000)
if O.exists():dump(O/'prepare-receipt.json',dict(returncode=q.returncode,stdout=q.stdout,stderr=q.stderr))
require(q.returncode==0,'preparation_failed:'+q.stderr)
d=read(O/'deployment.json');verify_frozen(d['inputs']);verify_frozen(d['deployed']);require(d['uncertain_point_count']==21,'uncertainty_count_changed')
pins={str(p):sha(p) for p in [*paths,A,*[O/n for n in ('deployment.json','prelaunch.json','points.json','prepare-receipt.json')]]}
dump(O/'accepted.json',dict(status='REVIEWED_FULL_NATIVE_READY',inputs=pins,scope='Two bounded native units,21uncertainIDs retained; no global/visual/RAM acceptance'))
print(json.dumps(dict(status='PREPARED_AND_SEALED',accepted_sha256=sha(O/'accepted.json'),uncertain=d['uncertain_labels'],uncertain_points=d['uncertain_point_count'],units=d['units'])))
