from pathlib import Path
import hashlib,json
R=Path(__file__).parent;D=R/'nav-kit7-8m-preparation-20261027';O=R/'kit7-nav8-code-review-20261027'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
review=read(O/'response.json');done=read(O/'completion.json');assert not review['is_error'] and not review['permission_denials'] and set(review['modelUsage'])=={'claude-fable-5-1'}
assert review['result'].startswith('**Veredicto: SOUND-with-fixes.**') and done['returncode']==0 and done['inputs_unchanged']
allowed={str(R/'orchestrate_kit7_nav8_generation.js'),str(R/'test_kit7_nav8_generation.cjs')}
changed=[]
for p,h in read(O/'source-hashes.json').items():
 if sha(p)!=h:
  assert p in allowed,p;assert sha(O/'reviewed-source'/Path(p).name)==h;changed.append(p)
assert set(changed)==allowed
controls=read(D/'generation-controls-deadline.json')
assert controls['status']=='CONTROL_FLOW_PASS' and controls['coordinator_sha256']==sha(R/'orchestrate_kit7_nav8_generation.js') and controls['harness_sha256']==sha(R/'test_kit7_nav8_generation.cjs')
assert len(controls['cases'])==19 and all(v['passed'] for v in controls['cases']) and len(controls['negative_mutations'])==5 and all(v['rejected'] for v in controls['negative_mutations'])
assert read(D/'wrong-baseline.json')['status']=='PASS_NEGATIVE_REJECTED_BEFORE_OUTPUT'
p=D/'launch-inputs.json';doc=read(p);assert doc['status']=='PREPARED_PENDING_CODE_REVIEW'
assert sha(p)==sha(O/'reviewed-source'/p.name)
for n,h in doc['inputs'].items():
 actual=sha(n)
 if actual!=h:assert n in allowed,n;doc['inputs'][n]=actual
receipt=dict(status='ACCEPTED_WITH_REPRODUCED_FIX',review_verdict='SOUND-with-fixes',changed_after_review=changed,adjudication=['Fixed loop bound using elapsed wall-clock time;19cases and5mutants include1901 rapid polls, elapsed deadline and deletion/count regressions.','Kept all reviewed bytes and old controls; no deletion or blind regeneration as suggested by reviewer.','Optional duplicated generator_status not added: generation.json remains authoritative.','Old NM already pinned by world SHA; never native acceptance.'],native_acceptance=False)
write(O/'accepted.json',receipt)
more=[O/'accepted.json',O/'response.json',O/'completion.json',O/'source-hashes.json',D/'generation-controls-deadline.json',D/'wrong-baseline.json',R/'fix_nav8_deadline.py',Path(__file__),R/'kit7-nav8-plan-review-20261027/adjudication.md']
doc['inputs'].update({str(p):sha(p) for p in more});doc.update(status='READY_AFTER_CODE_REVIEW',coordinator_sha256=sha(R/'orchestrate_kit7_nav8_generation.js'),queue_mode='Native lifecycle FIFO; no availability precheck or takeover.')
write(p,doc)
print(json.dumps(dict(status=doc['status'],inputs=len(doc['inputs']),coordinator_sha256=doc['coordinator_sha256'])))
