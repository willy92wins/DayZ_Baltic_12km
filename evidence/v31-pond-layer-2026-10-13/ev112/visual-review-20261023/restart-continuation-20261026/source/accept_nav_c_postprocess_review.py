from pathlib import Path
import json,hashlib
R=Path(__file__).parent;O=R/'nav-c-postprocess-review'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
h=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
review=read(O/'review-response.json')
assert not review.get('is_error') and 'claude-fable-5-1' in review['modelUsage']
assert review['result'].startswith('**Veredicto: SOUND-with-fixes.')
old=read(O/'source-hashes.json')
for path,digest in old.items():
 if Path(path).name!='orchestrate_c45_probe.js':assert h(path)==digest,path
controls=read(O/'command-flow-controls.json');native=read(O/'delayed-command-control.json')
assert controls['status']=='COMMAND_COMPLETION_CONTROLS_PASS' and controls['coordinator_sha256']==h(R/'orchestrate_c45_probe.js')
assert native['status']=='DELAYED_FAILURE_REJECTED' and native['elapsed_ms']>=12000
paths=[Path(p) for p in old]
paths += [R/'test_c45_command_completion.cjs',O/'review-response.json',O/'command-flow-controls.json',O/'delayed-command-control.json',O/'tested-command-function.js',
 R/'capture_patch_nav_log.ps1',R/'capture_owned_server_identity.ps1',R/'copy_owned_server_rpt.ps1',R/'record_nav_c_event.ps1',
 W/'tools/navigation/verify_continuity_nav_v30.py',W/'tools/navigation/verify_patch_nav_coverage_ev112.py',W/'tools/navigation/prepare_patch_nav_probe_ev112.py',W/'tools/navigation/prepare_current_nav_probe_ev112.py',W/'tools/terrain/verify_v30_acceptance.py',W/'tools/terrain/v30_common.py',W/'tools/playtest/attach_navmesh.py',W/'tools/navigation/inspect_navmesh_v9_ev112.py']
result=dict(status='ACCEPTED_AFTER_REVIEW',review_model='claude-fable-5-1',inputs={str(p):h(p) for p in paths},fixes={'F1':'Foreground commands await final exit, keep lease alive while pending, and reject delayed nonzero/null completion. Only readonly capture explicitly opts into background, then polled. Native12s delayed failure rejected plus5 control cases.'},backlog=['Initial own lease acquisition is logged as HEARTBEAT_ERROR then LEASE_RECOVERED; known timeline naming, not server failure.','Probe consumer requires retired run and clean terminal state; does not additionally require graceful flag. Generation packager does.'],review_note='Consumer already requires mcp.server_binding BOUND; imported local verifier dependencies now frozen. Prior F results are bound by the consumer independent of launch timing; do not infer a past skip as a measured fact.',limits=['Acceptance of postprocess code only. Generation/package/runtime/coverage remain pending.'])
assert not (O/'accepted.json').exists()
(O/'accepted.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'bound_files':len(paths),'model':result['review_model']}))

