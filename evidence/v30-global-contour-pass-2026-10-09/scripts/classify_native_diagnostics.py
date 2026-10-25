"""Preserve measured scalar/presence disagreements for all 674 EV14 points."""
from pathlib import Path
import hashlib, json
from collections import Counter, defaultdict
B = Path(__file__).parent
E = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/evidence/v30-global-contour-pass-2026-10-09')
source = E / 'global-contour-temporal-runtime-verification.json'
data = json.loads(source.read_text())
groups = defaultdict(list)
for point in data['series']['results']:
    depth = point['ranges']['depth_bed']
    state = ('always_positive' if depth['min'] > 0 else 'always_nonpositive' if depth['max'] <= 0 else 'intermittent')
    groups[point['role']].append(dict(id=point['id'], x=point['x'], z=point['z'], measured_depth=state, depth_range=depth, nominal_clearance=point['no_fake_minus_ground'], pond_true=point['pond_true'], sea_true=point['sea_true']))
counts = {role: dict(points=len(points), **dict(Counter(p['measured_depth'] for p in points)), both_flags_always_false=sum(not p['pond_true'] and not p['sea_true'] for p in points)) for role, points in groups.items()}
report = dict(status='COMPLETE_CLASSIFICATION_NOT_VISUAL_ACCEPTANCE', source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), counts=counts, points=dict(groups), bridge_residual=next(p for p in data['series']['results'] if p['id']==6113), limits=['Scalar wave depth and presence flags reported independently, without selecting an oracle.', 'Intermittent shoreline contacts are neither dry-land nor navigation acceptance.', 'No renderer claim follows from point 6113 remaining physically dry.'])
assert sum(r['points'] for r in counts.values()) == 674
for target in (B, E): (target/'native-diagnostic-classification.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(counts, indent=2))
