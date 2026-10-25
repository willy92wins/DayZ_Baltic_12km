"""Classify EV82 native-query additions relative to the verified EV80 baseline."""
from pathlib import Path
import hashlib
import json
import numpy as np

B = Path(__file__).parent
S = B.parent / 'v30-mixed-bank-constrained-20261010'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
baseline = dict(np.load(S / 'candidate/terrain.npz'))
candidate = dict(np.load(B / 'candidate/terrain.npz'))
verification = json.loads((B / 'native-verification.json').read_text(encoding='utf-8'))
assert verification['status'] == 'PASS_COMPLETE_NATIVE_READBACK'
assert verification['terrain_sha256'] == 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
assert sha(B / 'candidate/terrain.npz') == verification['terrain_sha256']
assert sha(S / 'native-snapshot.log') == '5e14a189d288fa4725c7343831bd973357c4b3a5ef4e8ee217f2fb14148239c3'
comparison = json.loads((B / 'native-inventory-comparison.json').read_text(encoding='utf-8'))
changed = baseline['heights'] != candidate['heights']
added_flags = []
inventories = {}
for name in ('physical_anomalies_A', 'unflagged_scalar_Q'):
    additions = comparison[name]['added']
    changed_count = 0
    for item in additions:
        row, col = item['key']
        changed_count += int(changed[row, col])
        if name == 'physical_anomalies_A':
            added_flags.append(dict(
                row=row, col=col, x=6 * col, z=12282 - 6 * row,
                record=item['candidate'],
                ev80_height=float(baseline['heights'][row, col]),
                ev82_height=float(candidate['heights'][row, col]),
                cls=int(baseline['cls'][row, col]),
                beach=bool(baseline['beach'][row, col]),
                height_unchanged=not bool(changed[row, col])))
    inventories[name] = dict(added=len(additions), added_at_changed_vertex=changed_count)
dry_flags = [item for item in added_flags if item['cls'] == 0]
result = dict(
    status='CLASSIFIED_EV82_NATIVE_DIFFERENCES_RELATIVE_TO_EV80',
    baseline_terrain_sha256=sha(S / 'candidate/terrain.npz'),
    candidate_terrain_sha256=verification['terrain_sha256'],
    baseline_runtime_sha256=sha(S / 'native-snapshot.log'),
    candidate_runtime_sha256=verification['runtime_sha256'],
    inventories=inventories,
    added_flags=added_flags,
    summary=dict(
        added_dry_class_flags=len(dry_flags),
        added_dry_flags_at_beach=sum(item['beach'] for item in dry_flags),
        added_flags_at_changed_vertices=sum(v['added_at_changed_vertex'] for v in inventories.values()),
        changed_height_vertices=int(np.count_nonzero(changed))),
    limits=[
        'Classification is relative to the EV80 runtime and terrain baseline.',
        'Wave-phase or scalar differences do not establish render causality.',
        'Native inventory classification does not close visual water-on-land or grey-water reports.'])
(B / 'native-difference-classification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'added_flags'}, indent=2))
