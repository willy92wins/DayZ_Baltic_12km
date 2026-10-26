from pathlib import Path
import json,hashlib
R=Path(__file__).parent;V=R/'nav-c-retry-postprocess-review';F=V/'after-fixes'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
review=read(F/'review-response.json');completion=read(F/'completion.json')
assert completion['exit_code']==0 and completion['inputs_unchanged'] and not review.get('is_error') and review['result'].startswith('**Veredicto: SOUND.')
inputs=read(F/'source-hashes.json');assert all(sha(p)==h for p,h in inputs.items())
for name,source,key in [('close-controls.json','verify_c_orderly_close.py','helper_sha256'),('flow-controls.json','orchestrate_c45_retry.js','coordinator_sha256'),('command-flow-controls.json','orchestrate_c45_retry.js','coordinator_sha256')]:
 c=read(F/name);assert c[key]==sha(R/source) and all(x['passed'] for x in c['cases'])
delay=read(F/'delayed-command-control.json');assert delay['status']=='PASS_REAL_DELAYED_FAILURE_REJECTED' and delay['duration_ms']>=12000
resolution=dict(status='ACCEPTED_AFTER_REVIEW',review_model='claude-fable-5-1',verdict='SOUND',run_id='e02b1334-4098-4a95-b92d-4346ceff73e9',decisions=['Allow only native integer0/-1 with complete independent orderly-close/RPT/identity/timeline proofs; every other code rejected.','The previous run remains rejected for early exit. Its recorded native orderly termination demonstrates that0 alone was an uncalibrated restriction.','This supersedes only the historical zero-only postprocess assumption; frozen launch/generation evidence is untouched.','C45 acquires its lease explicitly and requires the same complete official close/RPT binding.','Inspection output is single-use. No automatic rerun or threshold change.'],limits=['Current generation and C45 native outcomes still pending.','45queries and8Fpatch routes do not cover25Coptimizedmodels or actor movement.','No client or visual acceptance.'])
(V/'resolution.json').write_text(json.dumps(resolution,indent=2)+'\n')
files=[Path(__file__),R/'verify_c_orderly_close.py',R/'finish_c45_retry_probe.py',R/'test_c45_retry_command_final.cjs',R/'nav-c-retry-human-close-20261026/launch-inputs.json',R/'capture_patch_nav_log.ps1',R/'record_nav_c_event.ps1',R/'copy_owned_server_rpt.ps1',R/'capture_owned_server_identity.ps1',R/'patch-nav-c45/frozen.json',W/'tools/navigation/inspect_navmesh_v9_ev112.py',W/'tools/navigation/verify_continuity_nav_v30.py',W/'tools/navigation/verify_patch_nav_coverage_ev112.py',W/'tools/playtest/attach_navmesh.py',V/'review-response.json',V/'completion.json',V/'resolution.json']
files+=list(F.glob('*.json'))+[F/'tested-command-function.js',F/'review-brief.md']
inputs.update({str(p):sha(p) for p in files})
inputs.update(read(R/'patch-nav-c45/frozen.json')['inputs'])
assert all(sha(p)==h for p,h in inputs.items())
out=V/'accepted.json';assert not out.exists();out.write_text(json.dumps(dict(status='ACCEPTED_AFTER_REVIEW',inputs=inputs,run_id=resolution['run_id'],review_sha256=sha(F/'review-response.json')),indent=2)+'\n')
print('ACCEPTED_AFTER_REVIEW',len(inputs))
