from pathlib import Path
import hashlib,json
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
V=R/'kit7-hybrid-rebase-review-20261026';O=R/'kit7-hybrid-pilot-20261026';T=R/'kit7-hybrid-rebase-tests-20261026-v2'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not (V/'accepted.json').exists()
review=read(V/'review-response.json');assert not review['is_error'] and not review['permission_denials']
assert 'SOUND-with-fixes' in review['result'] and set(review['modelUsage'])=={'claude-fable-5-1'}
old=read(V/'source-hashes.json');changed=[]
for p,h in old.items():
    if sha(p)!=h:
        changed.append(Path(p).name);assert sha(V/'reviewed-source'/Path(p).name)==h
assert set(changed)=={'test_hybrid_witnesses_ev112.py','test_guarded_retention_ev112.py','feasible-witness-1171-190.json'}
tests=read(T/'result.json');assert tests['returncode']==0 and tests['tests_run']==29 and tests['inputs_unchanged']
for p,h in tests['inputs'].items():assert sha(p)==h
assert sha(T/'stderr.log')==tests['stderr_sha256'] and sha(T/'stdout.log')==tests['stdout_sha256']
assert read(T/'routing-negative.json')['status']=='EXPECTED_MUTATION_REJECTED'
assert read(O/'validation.json')['status']=='OFFLINE_GUARDS_PASS_PENDING_REVIEW_STAGE_NATIVE'
baseline=read(O/'baseline-shape-screen.json');candidate=read(O/'candidate-shape-screen.json')
key=lambda f:(f['kind'],f['row'],f['col'],f.get('radius_m'))
old_findings={key(f):f for f in baseline['findings']};new_findings={key(f):f for f in candidate['findings']}
assert len(old_findings)==len(baseline['findings']) and len(new_findings)==len(candidate['findings'])
assert not set(new_findings)-set(old_findings)
removed=set(old_findings)-set(new_findings);assert removed=={('native_spike',1171,190,None)},removed
assert all(f==old_findings[k] for k,f in new_findings.items()),'Inspect changed retained finding before acceptance'
paths=[Path(p) for p in old]+[Path(__file__),V/'review-response.json',V/'completion.json',T/'result.json',T/'stderr.log',T/'stdout.log',T/'routing-negative.json',T/'routing-negative.log',O/'validation.json',O/'baseline-shape-screen.json',O/'candidate-shape-screen.json']
inputs={str(p):sha(p) for p in paths}
result=dict(status='ACCEPTED_OFFLINE_UNIT',review_verdict='SOUND-with-fixes',fixes_verified_by='Codex executor/integrator against current source and tests',
            inputs=inputs,tests=29,negative_routing_detected=True,new_shape_findings=0,removed_shape_findings=[list(x) for x in removed],retained_findings_exact=True,
            findings={'1':'Fixed: assert actual solver witness receipt; lost-flag mutant is rejected.',
                      '2':'Fixed: real fixture also asserts the solver receipt.',
                      '3':'Metadata now names external diagnostic origin and explicitly separates it from fixture-only unit hash validation.',
                      '4':'The original stderr.log already retained unittest output. New receipt additionally pins both logs and records29tests.',
                      '5':'Documented scope: fresh hybrid applies to every group selected in discovery. This unit selects exactly one; no runtime claim of a one-group-only CLI.'},
            limits=['Candidate only: no forest/stage/binary/native/visual or global acceptance.','Current deployed kit7 remains unchanged; its607probe is a different artifact.'])
(V/'accepted.json').write_text(json.dumps(result,indent=2)+'\n')
(V/'adjudication.md').write_text('''# Review adjudication

Fable: SOUND-with-fixes. Findings1/2 fixed and verified with29passing tests;
the synthetic lost-flag mutation is rejected at the actual solver receipt.
Finding3: origin path and unit-test provenance scope are now explicit.
Finding4: unittest stderr was already saved; v2 also pins logs and test count.
Finding5: fresh hybrid applies to ALL groups selected by discovery. The current
experiment selects exactly one group; using a full inventory requires its own
plan and validation. No implicit one-group runtime restriction is claimed.

Completed full census: only native_spike(1171,190) disappears. Every retained
finding is exactly unchanged; no new location or type. All-protected audit,
water footprint and road consumer pass. This closes the isolated offline unit,
not forest staging, composition, compilation, runtime, navigation or visuals.
''',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','findings')},indent=2))
