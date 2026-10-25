"""Operating-asset and missing-resource controls for the junction diagnostic."""
from pathlib import Path
import copy
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/terrain'))
from verify_channel_reaches_v30 import retained_pond_surface

fit = Path('E:/DayZ-Baltic-Build/v30-v11/24')
manifest = json.loads((fit/'water/pieces.json').read_text())
level, hits = retained_pond_surface(fit, manifest, 2208, 7080)
checks = dict(actual_junction_145cm=abs(level-1.45) < 1e-9 and len(hits) == 2)
missing = copy.deepcopy(manifest)
names = {h['model'] for h in hits}
missing['poses'] = [p for p in missing['poses'] if p['model'] not in names]
checks['removed_support_rejected'] = retained_pond_surface(fit, missing, 2208, 7080)[0] is None
checks['point_outside_all_water_rejected'] = retained_pond_surface(fit, manifest, 0, 0)[0] is None
wrong = copy.deepcopy(manifest)
for model in wrong['model_list']:
    if model['name'] == 'pilot_00001':
        model['sha256'] = '0'*64
try:
    retained_pond_surface(fit, wrong, 2208, 7080)
except ValueError as exc:
    checks['mismatched_asset_rejected'] = 'Changed water model' in str(exc)
else:
    checks['mismatched_asset_rejected'] = False
result = dict(status='PASS' if all(checks.values()) else 'FAIL', checks=checks,
              scope='Nominal offline junction coverage only; no runtime acceptance.')
Path(__file__).with_name('diagnostic-controls.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, indent=1))
raise SystemExit(0 if all(checks.values()) else 1)
