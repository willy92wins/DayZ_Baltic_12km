"""Independent corruption controls on the actual native acceptance log."""
import hashlib
import json
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parents[1] / 'tools/terrain'))
from verify_v30_acceptance import verify

reference = json.loads((here.parents[1] / 'evidence/v30-resume-2026-10-02/acceptance-reference.json').read_text())
text = (here / 'native-paths.log').read_text()
rows = text.splitlines()
mutants = {
    'missing_end': '\n'.join(rows[:-1]),
    'wrong_world': text.replace(';BalticTrial', ';ChernarusPlus', 1),
    'missing_case': '\n'.join(r for r in rows if not r.startswith(('Q;delta;', 'P;delta;'))),
    'duplicate_query': '\n'.join([rows[0], rows[1]] + rows[1:]),
    'partial_endpoint': text.replace('P;delta;1;<8622.000000', 'P;delta;1;<8600.000000', 1),
    'nonfinite_endpoint': text.replace('P;delta;1;<8622.000000', 'P;delta;1;<nan', 1),
    'negative_succeeds': text.replace('Q;negative;false;false;false;', 'Q;negative;true;true;true;', 1),
}
out = here / 'path-log-controls'
out.mkdir(exist_ok=False)
results = [{'name': 'native_original', 'expected': 'PASS', 'actual': verify(reference, text)['status']}]
assert results[0]['actual'] == 'PASS_NATIVE_V30_PATHS'
for name, mutated in mutants.items():
    assert mutated != text
    raw = mutated.encode()
    (out / (name + '.log')).write_bytes(raw)
    try:
        result = verify(reference, mutated)
        rejected = result['status'] == 'FAIL_NATIVE_V30_PATHS'
        actual = result['status']
    except (ValueError, IndexError) as e:
        rejected, actual = True, f'{type(e).__name__}: {e}'
    results.append({'name': name, 'expected': 'REJECT', 'rejected': rejected,
                    'actual': actual, 'sha256': hashlib.sha256(raw).hexdigest()})
assert all(r.get('rejected', True) for r in results)
(out / 'result.json').write_text(json.dumps({'status': 'PASS_OFFLINE_PARSER_CONTROLS',
    'cases': results, 'limits': 'Mutated-log verifier controls, not additional engine runs.'}, indent=2) + '\n')
print('PASS: original plus seven rejected corruptions; no engine claims added.')
