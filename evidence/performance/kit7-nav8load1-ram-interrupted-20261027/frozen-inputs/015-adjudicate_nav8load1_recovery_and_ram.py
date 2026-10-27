from pathlib import Path
import json,hashlib,difflib
R=Path(__file__).parent;V=R/'kit7-nav8load1-recovery-review-20261027';D=R/'kit7-nav8load1-consumer-20261027';M=R/'kit7-nav8load1-ram-ab-20261027'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
review=read(V/'response.json');assert not review['is_error'] and not review.get('permission_denials') and 'claude-fable-5-1' in review['modelUsage'] and review['result'].strip().endswith('FIN_REVISION')
assert '**Veredicto RECOVERY: SOUND-with-fixes.** **Veredicto RAM_FIXES: SOUND-with-fixes.**' in review['result'] and read(V/'completion.json')['returncode']==0
changes={str(R/n) for n in ['recover_kit7_nav8load1_config_consumer.py','prepare_nav8load1_ram_pass.py','finalize_nav8load1_ram_ab.py','test_nav8load1_joint_gate.py']}|{str(M/'joint-gate-controls.json')}
original=read(V/'source-hashes.json');actual={p:sha(p) for p in original}
assert {p for p,h in original.items() if actual[p]!=h}==changes
for path in changes:
 p=Path(path)
 if p.suffix=='.py':
  before=V/('reviewed-'+p.name);assert sha(before)==original[path]
  diff=''.join(difflib.unified_diff(before.read_text().splitlines(keepends=True),p.read_text().splitlines(keepends=True),fromfile='reviewed/'+p.name,tofile='final/'+p.name))
  (V/(p.name+'.diff')).write_text(diff)
assert read(M/'joint-gate-controls.json')['count']==80 and all(x['passed'] for x in read(M/'joint-gate-controls.json')['checks'])
rc=(R/'recover_kit7_nav8load1_config_consumer.py').read_text();assert rc.count(".open('xb')")==2 and "'config-recovery.json','config-consumer-recovery.stdout.log','config-consumer-recovery.stderr.log'" in rc
for n in ('prepare_nav8load1_ram_pass.py','finalize_nav8load1_ram_ab.py'):
 t=(R/n).read_text();assert "assert all(required[p]==h for p,h in reviewed.items() if p not in changed)" in t and "assert set(adjudication['post_review_changes'])==changed" in t and "assert all(required[p]==final_review['inputs'][p] for p in changed)" in t
paths=[V/'response.json',V/'completion.json',V/'source-hashes.json',Path(__file__),R/'seal_nav8load1_ram_block.py']+list(V.glob('*.diff'))
inputs={**actual,**{str(p):sha(p) for p in paths}}
with (V/'adjudication.json').open('x',encoding='utf-8') as f:json.dump(dict(status='ACCEPTED_AFTER_REVIEW',original_verdicts=dict(recovery='SOUND-with-fixes',ram_fixes='SOUND-with-fixes'),post_review_changes=sorted(changes),inputs=inputs,fixes=['Recovery uses exclusive log writes and rejects any previous output','Original reviewed hash values enforced except exactly four RAM paths; final adjudication binds sanctioned followup fixes','80 admission controls include original/followup hash divergence and expanded allowlist negatives'],limits=['No extra native run; no RAM yet; one failed reservation kills block without retry']),f,indent=2)
print('ACCEPTED_AFTER_REVIEW recovery and RAM fixes; 80 controls')
