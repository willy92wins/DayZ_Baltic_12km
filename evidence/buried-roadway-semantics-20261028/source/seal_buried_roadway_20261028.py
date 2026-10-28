from pathlib import Path
import hashlib,json,subprocess,sys,time
R=Path(__file__).resolve().parent;O=R/'buried-roadway-semantics-20261028'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/quality'))
from buried_roadway_semantics_ev112 import require,verify_frozen
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_bytes())
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
require(not (O/'accepted.json').exists() and not (O/'consumer-tests.json').exists(),'fresh_seal_required')
review=R/'buried-roadway-code-review-20261028';done=read(review/'completion.json')
require(done['returncode']==0 and not done['timeout'] and done['inputs_unchanged'] and done['modelUsage']==['claude-fable-5-1'] and done['finish_marker'] and not done['permission_denials'],'review_incomplete')
flow=read(R/'buried-roadway-flow-tests-r2-20261028.json');require(flow['status']=='SIX_MOCK_LIFECYCLE_CONTROLS_PASS' and len(flow['rows'])==6 and all(x['expected_outcome_verified'] for x in flow['rows']),'flow_tests_incomplete')
start=time.monotonic();test=W/'tools/quality/test_buried_roadway_semantics_ev112.py'
out=subprocess.run([sys.executable,'-I',str(test),'-v'],capture_output=True,text=True,timeout=120,creationflags=0x08000000)
doc=dict(returncode=out.returncode,seconds=time.monotonic()-start,stdout=out.stdout,stderr=out.stderr,source_sha256=sha(test));dump(O/'consumer-tests.json',doc)
require(out.returncode==0 and 'Ran 10 tests' in out.stderr and 'OK' in out.stderr,'consumer_tests_failed')
dep=read(O/'deployment.json');verify_frozen(dep['inputs']);verify_frozen(dep['deployed'])
paths=[O/x for x in ('deployment.json','prelaunch.json','points.json','consumer-tests.json')]+[review/'review.md',review/'completion.json',R/'buried-roadway-flow-tests-r2-20261028.json',R/'test_buried_roadway_flow_20261028.cjs',R/'check_buried_roadway_gate_20261028.py',Path(__file__).resolve()]
dump(O/'accepted.json',dict(status='REVIEWED_DIAGNOSTIC_READY',review='Fable5.1 SOUND-with-fixes + Codex verified corrections',inputs={str(p):sha(p) for p in paths},scope='One16point server query discriminator, no visual/global acceptance'))
print(json.dumps(dict(status='SEALED',accepted_sha256=sha(O/'accepted.json'),tests=10,lifecycle_controls=6)))
