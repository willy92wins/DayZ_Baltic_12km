from pathlib import Path
import hashlib,json,sys
from datetime import datetime,timezone
R=Path(__file__).parent
W=Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c')
D=R/'kit7-navv9diag-ram-ab-20261027'
sys.path.insert(0,str(W/'tools/performance'))
from compare_server_baseline_ev112 import load_pass,require_equivalent,compare
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sources=[W/'tools/navigation/verify_terrain_perf.py',W/'tools/performance/read_server_baseline_ev112.py',W/'tools/performance/compare_server_baseline_ev112.py']
source_hashes={str(p):sha(p) for p in sources}
assert not (D/'comparison.json').exists(),'Fresh final aggregate required'
sys.path.insert(0,str(R))
from navv9diag_gate import validate_diagnostic
validate_diagnostic(R/'kit7-nav-consumer-20261026/result.json',D/'deployment.json')
loaded=[];references=[];activity=[]
for n in range(1,7):
    d=D/f'pass-{n:02}';reference=d/'reference.json'
    gate=load(d/'benchmark-gate.json')
    assert gate['status']=='BOUND_DIAGNOSTIC_ONLY_HEIGHT_FAIL'
    assert all(sha(Path(p))==h for p,h in gate['inputs'].items()),'Diagnostic inputs drifted'
    assert not (d/'result-revalidated.json').exists(),'Fresh per-pass revalidation required'
    report,conditions=load_pass(reference)
    assert report['status']=='PASS_COMPLETE_EMPTY_SERVER_MEASUREMENT'
    loaded.append((report,conditions));references.append(reference)
    bound=load(reference);run=load(d/'run.json');cleanup=load(d/'cleanup.json')
    assert cleanup['close']['run_retired'] and cleanup['self']['state']=='none' and not cleanup['cleanup_degraded']
    assert run['server_binding']=='BOUND' and run['server_run_id']==bound['run_id'] and not run['client_started']
    report['inputs']={str(reference):sha(reference),str(d/'host.jsonl'):sha(d/'host.jsonl'),bound['artifacts']['engine']:sha(Path(bound['artifacts']['engine']))}
    report['validation_sources']=source_hashes
    report['revalidated_utc']=datetime.now(timezone.utc).isoformat()
    report['all_bound_files_rehashed']=True
    (d/'result-revalidated.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    before=load(d/'processes-before.json');after=load(d/'processes-after.json')
    left={(x['pid'],x['start_utc']):x for x in before}
    right={(x['pid'],x['start_utc']):x for x in after}
    common=set(left)&set(right);deltas=[max(0,right[k]['cpu_s']-left[k]['cpu_s']) for k in common if k[0]!=bound['process_id']]
    activity.append(dict(pass_order=n,surviving_other_processes=len(deltas),surviving_other_processes_cpu_delta_s=sum(deltas),started_or_ended_process_identities=len(set(left)^set(right)),observed_interval_s=(d/'processes-after.json').stat().st_mtime-(d/'processes-before.json').stat().st_mtime,source_sha256={name:sha(d/name) for name in ['processes-before.json','processes-after.json']},limits=['Snapshots span launch/capture/identity capture, not exactly the timed engine window.','Includes OS and measurement processes; no private application names published.','Does not measure complete host CPU or prove absence of unrelated load.']))
    print(json.dumps(dict(pass_order=n,status=report['status'],warmup_seconds=report['engine']['warmup_seconds'])),flush=True)
require_equivalent(loaded)
result=compare([x[0] for x in loaded])
assert source_hashes=={str(p):sha(p) for p in sources},'Validator changed during final comparison'
result['inputs']={str(p):sha(p) for p in references}
result['validation_sources']=source_hashes
result['completed_utc']=datetime.now(timezone.utc).isoformat()
result['measurement_repeats']=0
result['acceptance_eligible']=False
result['scope']='DIAGNOSTIC_ONLY_ORIGINAL_FOUR_HEIGHT_FAILURES_PRESERVED'
result['height_result_sha256']='e086af218bc393476256cbfc17a540964d2daf53735dd9587585ae15eb9f7041'
(D/'comparison.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(D/'background-activity-summary.json').write_text(json.dumps(activity,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['status']=='PASS_EMPTY_SERVER_RAM_BUDGET' else 1)
