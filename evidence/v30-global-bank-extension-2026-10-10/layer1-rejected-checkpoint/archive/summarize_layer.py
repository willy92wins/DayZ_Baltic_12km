"""Compact evidence from immutable EV93 author and whole-field diagnostics."""
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAYER = ROOT / 'fairing-layer1'
OUT = ROOT / 'layer1-results-summary.json'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    receipt_path = LAYER / 'authoring.json'
    ledger_path = LAYER / 'ledger.jsonl'
    receipt = json.loads(receipt_path.read_text())
    assert receipt['status'] == 'AUTHORED_PENDING_GLOBAL_CONSUMER'
    assert sha(ledger_path) == receipt['ledger_sha256']
    assert sha(receipt['candidate_path']) == receipt['candidate_sha256']
    events = [json.loads(x) for x in ledger_path.read_text().splitlines()]
    results = [x for x in events if x['event'] == 'result']
    assert len(results) == len({x['queue_id'] for x in results}) == 703
    counts, reasons = collections.Counter(), collections.Counter()
    for event in results:
        assert sha(event['result_path']) == event['result_sha256']
        result = json.loads(Path(event['result_path']).read_text())
        assert event['state'] == result['state']
        counts[result['state']] += 1
        if result['state'] == 'rejected':
            reasons[result['reason']] += 1
    assert all(counts[key] == value for key, value in receipt['result_counts'].items())
    diag_path = ROOT / 'consumer-global/runs/attempt-01/any-populations.json'
    diag = json.loads(diag_path.read_text())
    assert diag['candidate_sha256'] == receipt['candidate_sha256'] and diag['readset_stable']
    metrics = {}
    for name, data in diag['diagnostic']['by_population'].items():
        m = data['ANY']['aggregate_families_concatenated_once_for_this_population']
        metrics[name] = {key: m[key] for key in ('hinges', 'new_over_30_0001_count',
            'improved_strict_count', 'worsened_strict_count', 'unchanged_exact_count')}
        metrics[name].update({side: {key: m[side][key] for key in ('p99', 'max', 'above30',
            'mean_square')} for side in ('B', 'H')})
    output = {'status': 'AUTHOR_COMPLETE_DIAGNOSTICS_ONLY', 'terrain_accepted': False,
        'candidate_sha256': receipt['candidate_sha256'],
        'authoring_sha256': sha(receipt_path), 'ledger_sha256': sha(ledger_path),
        'changed_vertices': receipt['changed_vertices'], 'result_counts': dict(counts),
        'rejection_reasons': dict(reasons.most_common()), 'ANY_populations': metrics,
        'diagnostic_sha256': sha(diag_path),
        'limits': ['Populations share some incident hinges; do not sum as disjoint totals.',
                   'Whole compound water/navigation consumer is a separate gate.',
                   'Inherited absolute defects remain; no engine or artistic acceptance.']}
    OUT.write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(OUT), 'sha256': sha(OUT), 'results': dict(counts)}))

if __name__ == '__main__':
    main()
