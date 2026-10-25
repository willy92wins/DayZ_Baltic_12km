"""Consumer gates for the experimental composite, preserving the frozen road mask."""
from pathlib import Path
import json
import sys
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/terrain'))
from verify_roads_v30 import evaluate
from check_margin import steeper_faces

B = Path('E:/DayZ-Baltic-Build/v30-bounded-integration-20261008')
base = np.load('E:/DayZ-Baltic-Build/v30-v12/inland/terrain_inland.npz')
new = np.load(B/'combined/terrain_inland.npz')
shore = np.load(B/'luga-margin/terrain_inland.npz')
old_report = json.loads(Path('E:/DayZ-Baltic-Build/v30-v12/verify-v12.json').read_text(encoding='utf-8-sig'))
new_report = json.loads((B/'verify-combined.json').read_text(encoding='utf-8-sig'))
keys = ['water_depth', 'banks', 'pieces', 'bed_floor', 'land_floor', 'slopes', 'narva', 'status', 'limits']
checks = {k+'_same_as_v12': old_report[k] == new_report[k] for k in keys}
old_roads = evaluate(base['heights'], base['water'].astype(bool))
new_roads = evaluate(new['heights'], base['water'].astype(bool))
checks['roads_pass'] = new_roads['status'] == 'PASS'
checks['roads_identical_to_v12'] = old_roads == new_roads
checks['no_steeper_land_faces'] = steeper_faces(base['heights'], new['heights'], base['cls']) == 0
# Prove that every one of the four potential interpolation corners for every
# shore probe is exactly the independently accepted shore-only geometry.
supports = {}
for label in ['frozen', 'interleaved_1m']:
    s = np.load(B/'verification-r2'/f'stations-{label}.npz')
    p, normal = s['points'][s['keep']], s['normal'][s['keep']]
    q = p[:, None, :] + normal[:, None, :]*np.arange(-8, 8.0001, .25)[None, :, None]
    row = np.floor((12282-q[..., 1])/6).astype(int)
    col = np.floor(q[..., 0]/6).astype(int)
    assert row.min() >= 0 and col.min() >= 0 and row.max() < 2047 and col.max() < 2047
    changed = 0
    for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        changed += int(np.count_nonzero(new['heights'][row+dr, col+dc] != shore['heights'][row+dr, col+dc]))
    checks[label+'_all_probe_corners_exact'] = changed == 0
    supports[label] = dict(stations=len(p), probes=int(row.size), changed_corner_samples=changed)
report = dict(status='PASS_NO_REGRESSION' if all(checks.values()) else 'FAIL', checks=checks,
              general_status='FAIL_INHERITED_IDENTICAL_TO_V12', roads=new_roads, baseline_roads=old_roads,
              shore_supports=supports,
              discarded_command='roads-combined.json used historical v29 water, unlike frozen V12 road gate. Retained as diagnostic, not acceptance.')
path = B/'combined-verification.json'
assert not path.exists()
path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
print(json.dumps(dict(status=report['status'], checks=checks, road_samples=new_roads['samples'], supports=supports), indent=2))
sys.exit(0 if all(checks.values()) else 1)
