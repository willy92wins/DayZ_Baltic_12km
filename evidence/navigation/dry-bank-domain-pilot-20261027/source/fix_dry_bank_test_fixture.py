from pathlib import Path
import hashlib,json
R=Path(__file__).parent;old=R/'dry-bank-domain-setup-20261027';new=R/'dry-bank-domain-setup-fixed-20261027';new.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
context=json.loads((old/'context.json').read_text(encoding='utf-8-sig'))
test=R/'test_dry_bank_domain.py';before=R/'dry-bank-domain-tests-20261027/test-before-fix.py'
assert sha(before)==context['hashes'][str(test)]
assert all(sha(Path(p))==h for p,h in context['hashes'].items() if p!=str(test))
context['hashes'][str(test)]=sha(test)
context['prior_context_sha256']=sha(old/'context.json')
(new/'context.json').write_text(json.dumps(context,indent=2)+'\n',encoding='utf-8')
(new/'budget.json').write_bytes((old/'budget.json').read_bytes())
record=dict(status='ONE_CONCRETE_TEST_FIX',failed_execution='PTY13749 exit1; before any CLI mutant or candidate',
    repro='test_dry_bank_domain.py:23 IndexError indexing argwhere(protected)[0]; frozen kit has zero protected vertices.',
    correction='Conditional protected mutant; zero coverage explicitly NOT_APPLICABLE. Mandatory mutations unaffected.',
    original_test_sha256=sha(before),fixed_test_sha256=sha(test),review='Fable SOUND by reading, but did not execute. Runtime counterexample supersedes expected 11 PASS.',
    mutation_count_before=0,candidate_count_before=0,remaining_code_correction_budget=0)
(new/'fix-adjudication.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
(before.parent/'failure.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print('ONE FIX FROZEN',new)
