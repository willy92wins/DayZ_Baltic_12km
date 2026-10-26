"""Seal the actually reviewed bytes and tests, preserving the previous manifest."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=R/'kit7-nav-consumer-20261026';O=R/'kit7-nav-postprocess-review-20261026';F=R/'kit7-nav-postprocess-fix-review-20261026'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
review=read(F/'review-response.json');assert review['result'].startswith('**Veredicto: SOUND.**') and not review['is_error'] and not review['permission_denials']
assert set(review['modelUsage'])=={'claude-fable-5-1'}
checked=read(F/'source-hashes.json');assert all(sha(Path(p))==h for p,h in checked.items())
# Preserve the initial review's package bytes too; the fix adds one bound snapshot.
p=R/'package_and_deploy_kit7_nav9.py';s=p.read_text().replace(",str(I/'mcp-after.json'):sha(I/'mcp-after.json')",'');expected=read(O/'source-hashes.json')[str(p)]
raw=s.replace('\n','\r\n').encode()
if hashlib.sha256(raw).hexdigest()!=expected:raw=s.encode()
assert hashlib.sha256(raw).hexdigest()==expected
(O/'reviewed-source'/p.name).write_bytes(raw)
frozen=read(D/'frozen.json');allowed={str(R/'orchestrate_kit7_nav_probe.js'),str(R/'finish_kit7_nav_probe.py'),str(W/'tools/navigation/verify_kit7_nav_ev112.py')};changes=[]
for name,before in frozen['inputs'].items():
    after=sha(Path(name))
    if after!=before:
        assert name in allowed,name;changes.append(dict(path=name,before=before,after=after));frozen['inputs'][name]=after
assert {v['path'] for v in changes}==allowed
for p in [R/'package_and_deploy_kit7_nav9.py',R/'finish_kit7_nav_probe.py',W/'tools/navigation/verify_kit7_nav_ev112.py']:ast.parse(p.read_text(),filename=str(p))
controls=read(D/'synthetic-controls-v2/result.json');assert len(controls['controls'])==19 and all(c['ok'] for c in controls['controls']) and controls['native_acceptance'] is False
for p,h in controls['sources'].items():assert sha(Path(p))==h,p
coordinator=sha(R/'orchestrate_kit7_nav_probe.js')
for filename,count in [('coordinator-controls-v2.json',11),('command-flow-controls-v2.json',8)]:
    v=read(D/filename);assert v['coordinator_sha256']==coordinator and len(v['cases'])==count and all(c['passed'] for c in v['cases'])
static=read(D/'script-validator.json');assert static['status']=='PASS' and static['info']['files_scanned']==1 and not static['errors'] and not static['warnings']
old=D/'frozen-before-final-review.json';assert not old.exists();old.write_bytes((D/'frozen.json').read_bytes())
frozen.update(status='READY_FOR_GENERATION_RESULT_AND_NATIVE_RUN',review_response_sha256=sha(F/'review-response.json'))
(D/'frozen.json').write_text(json.dumps(frozen,indent=2)+'\n')
inputs={**frozen['inputs'],**checked}
more=[D/'frozen.json',R/'package_and_deploy_kit7_nav9.py',R/'verify_c_orderly_close.py',W/'tools/playtest/attach_navmesh.py',W/'tools/navigation/inspect_navmesh_v9_ev112.py',W/'tests/test_kit7_nav_ev112.py',D/'script-validator.json',D/'freeze-summary.json',F/'review-response.json',F/'completion.json',Path(__file__)]
inputs.update({str(p):sha(p) for p in more})
accepted=dict(status='ACCEPTED_AFTER_REVIEW',inputs=inputs,reviewer='claude-fable-5-1',verdict='SOUND',review_response_sha256=sha(F/'review-response.json'),reviewed_changed_inputs=changes,
adjudication=['Mandatory1..4 and optional5 closed and independently rereviewed.','The accepted manifest pins the final frozen.json hash; runtime deployment additionally binds generation mcp-after.','Four initial corridor overhangs and six routes with extra allowed models are distinct metrics.','Synthetic controls are not native acceptance.'],limits=['Generation, structure/package and native607 remain required before graph acceptance.','No locomotion, boats, visual, FPS, capacity or global map verdict.'])
assert not (O/'accepted.json').exists();(O/'accepted.json').write_text(json.dumps(accepted,indent=2)+'\n')
(D/'ready-summary.json').write_text(json.dumps(dict(status='PREPARED_REVIEWED_NOT_NATIVE',queries=607,local_queries=562,models=139,joints=138,fixture_tests=11,synthetic_controls=19,lifecycle_controls=11,command_controls=8,review_verdict='SOUND',accepted_sha256=sha(O/'accepted.json'),frozen_sha256=sha(D/'frozen.json'),native_acceptance=False),indent=2)+'\n')
print(json.dumps(dict(status=accepted['status'],inputs=len(inputs),queries=607,verdict='SOUND')))
