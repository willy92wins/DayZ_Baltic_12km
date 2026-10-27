from pathlib import Path
import hashlib,json,sys
from datetime import datetime,timezone
R=Path(__file__).parent
W=Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c')
D=R/'kit7-nav8load1-ram-ab-20261027'
sys.path.insert(0,str(W/'tools/performance'))
from compare_server_baseline_ev112 import load_pass,require_equivalent,compare
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sources=[W/'tools/navigation/verify_terrain_perf.py',W/'tools/performance/read_server_baseline_ev112.py',W/'tools/performance/compare_server_baseline_ev112.py']
source_hashes={str(p):sha(p) for p in sources}
assert not (D/'comparison.json').exists(),'Fresh final aggregate required'
gate=load(D/'accepted.json');assert gate['status']=='ACCEPTED_AFTER_REVIEW'
review=R/'kit7-nav8load1-ram-review-20261027'
reviewed=load(review/'source-hashes.json');adjudication=load(review/'adjudication.json')
assert adjudication['status']=='ACCEPTED_AFTER_REVIEW' and reviewed
required=adjudication['inputs']
assert set(reviewed)<=set(required)<=set(gate['inputs'])
changed={str(R/n) for n in ('prepare_nav8load1_ram_pass.py','finalize_nav8load1_ram_ab.py','test_nav8load1_joint_gate.py')}|{str(D/'joint-gate-controls.json')}
assert set(adjudication['post_review_changes'])==changed
assert all(required[p]==h for p,h in reviewed.items() if p not in changed)
followup=R/'kit7-nav8load1-recovery-review-20261027'
final_review=load(followup/'adjudication.json');assert final_review['status']=='ACCEPTED_AFTER_REVIEW'
assert all(required[p]==final_review['inputs'][p] for p in changed)
assert all(gate['inputs'][p]==h for p,h in required.items())
for proof in (review/'source-hashes.json',review/'adjudication.json',followup/'source-hashes.json',followup/'adjudication.json'):
 assert gate['inputs'].get(str(proof))==sha(proof)
assert all(sha(p)==h for p,h in gate['inputs'].items())
native=R/'kit7-nav8load1-consumer-20261027'
nav=load(native/'result.json');config=load(native/'config-result.json');joint=load(native/'joint-result.json')
identity=load(native/'identity-verification.json');host=load(native/'host-identity.json');deployment=load(native/'deployment.json')
assert nav['status']=='PASS_KIT7_NATIVE_GRAPH' and config['status']=='PASS_NATIVE_LOAD1_CONFIG'
assert joint['status']=='PASS_LOAD1_CONFIG_AND_NATIVE607' and identity['status']=='PASS_BOUND_NATIVE_PROBE_INPUTS'
assert joint['run_id'] and joint['run_id']==identity['run_id']==host['run_id']
assert joint['config_status']==config['status'] and joint['native_status']==nav['status']
canonical=lambda rows:{str(Path(p).resolve()).casefold():h for p,h in rows.items()}
assert len(deployment['packages'])==4
assert canonical(joint['packages'])==canonical(identity['packages'])==canonical(host['package_hashes'])==canonical(deployment['packages'])
loaded=[];references=[];activity=[];seen_runs=set();observed_launches=0
assert {p.name for p in (D/'attempt-reservations').iterdir()}=={f'pass-{n:02d}.json' for n in range(1,7)}
for n in range(1,7):
    d=D/f'pass-{n:02}';reference=d/'reference.json'
    assert not (d/'result-revalidated.json').exists(),'Fresh per-pass revalidation required'
    gate=load(d/'benchmark-gate.json')
    assert gate['status']=='BOUND_AFTER_LOAD1_CONFIG_AND_NATIVE607' and all(sha(Path(p))==h for p,h in gate['inputs'].items())
    report,conditions=load_pass(reference)
    assert report['status']=='PASS_COMPLETE_EMPTY_SERVER_MEASUREMENT'
    loaded.append((report,conditions));references.append(reference)
    bound=load(reference);run=load(d/'run.json');cleanup=load(d/'cleanup.json')
    reservation=load(D/'attempt-reservations'/f'pass-{n:02d}.json')
    assert reservation['order']==n and reservation['mission']==gate['mission'] and reservation['accepted_sha256']==sha(D/'accepted.json')
    events=[json.loads(x) for x in (d/'timeline.jsonl').read_text(encoding='utf-8-sig').splitlines()]
    launches=[e for e in events if e['event']=='LAUNCHED']
    assert len(launches)==1 and launches[0]['run_id']==run['run_id'] and run['run_id'] not in seen_runs
    seen_runs.add(run['run_id']);observed_launches+=1
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
result['measurement_repeats']=None
result['repeat_evidence']=dict(observed_unique_runs=len(seen_runs),observed_launches=observed_launches,exclusive_attempt_reservations=6,host_wide_history='NOT_VERIFIED',limits=['Six exclusive slots and one launch per slot are verified. External or deleted history is not certified. No repetition authorized.'])
(D/'comparison.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(D/'background-activity-summary.json').write_text(json.dumps(activity,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['status']=='PASS_EMPTY_SERVER_RAM_BUDGET' else 1)
