"""Classify measured query disagreements without treating presence flags as ground truth."""
from pathlib import Path
from collections import defaultdict
import json
from discover_native_turns import W, B, sha

E = W / 'evidence/v30-native-turn-optimizer-2026-10-09'
source = E / 'native-contour-temporal-runtime-verification.json'
data = json.loads(source.read_text())
groups = defaultdict(list)
for point in data['series']['results']:
    depth = point['ranges']['depth_bed']
    nominal = point['no_fake_minus_ground']
    state = ('always_positive' if depth['min'] > 0 else
             'always_nonpositive' if depth['max'] <= 0 else 'intermittent')
    flags = ('presence_observed' if point['pond_true'] or point['sea_true'] else 'both_flags_always_false')
    groups[point['role']].append(dict(id=point['id'], x=point['x'], z=point['z'],
        measured_depth=state, presence=flags, depth_range=depth,
        nominal_clearance=nominal, pond_true=point['pond_true'], sea_true=point['sea_true']))
counts = {}
for role, points in groups.items():
    counts[role] = dict(points=len(points), **{
        state: sum(p['measured_depth'] == state for p in points)
        for state in ('always_positive', 'always_nonpositive', 'intermittent')},
        both_flags_always_false=sum(p['presence'] == 'both_flags_always_false' for p in points))
residual = next(p for p in data['series']['results'] if p['id'] == 6113)
report = dict(status='COMPLETE_CLASSIFICATION_NOT_VISUAL_ACCEPTANCE', source_sha256=sha(source),
    counts=counts, points=dict(groups), bridge_residual=residual,
    limits=['Scalar wave depth and presence flags are reported separately. No API is silently preferred as an oracle.',
            'Intermittent contacts on shoreline are not certified as dry land or navigable water.',
            'Point 6113 remains physically dry in these 62 samples; no conclusion about distant renderer follows.',
            'The calm image retains a small bridge-area visual patch. No further elevation was applied for that image.'])
(B / 'native-diagnostic-classification.json').write_text(json.dumps(report, indent=2) + '\n')
(E / 'native-diagnostic-classification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(counts=counts, bridge_depth=residual['ranges']['depth_bed']), indent=2))
