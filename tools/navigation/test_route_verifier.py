"""Reject corruptions of the measured boat route; never invent a positive run."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--log', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
raw = a.log.read_text(encoding='utf-8-sig')
lines = raw.splitlines()
motion = [i for i, line in enumerate(lines) if line.startswith('B;')]
if len(motion) < 100 or lines[-1] != 'END;OUTWARD_ROUTE_REACHED_EMPTY_BOAT_ONLY':
    raise ValueError('A complete measured route is required')


def changed(field, value, selector=lambda i: True):
    result = lines.copy()
    for i, index in enumerate(motion):
        if selector(i):
            row = result[index].split(';')
            row[field] = str(value(row))
            result[index] = ';'.join(row)
    return '\n'.join(result) + '\n'


cases = {
    'missing_end': ('\n'.join(lines[:-1]) + '\n', 'route_end_marker'),
    'propeller_stopped': (changed(17, lambda row: 0), 'powered_motion'),
    'health_lost': (changed(7, lambda row: 500, lambda i: i >= 80), 'no_health_loss'),
    'gap_during_motion': (changed(1, lambda row: float(row[1]) + 2, lambda i: i >= 80), 'continuous_samples'),
    'teleport_during_motion': (changed(2, lambda row: float(row[2]) + 20, lambda i: i == 80), 'continuous_samples'),
    'runtime_distance_forged': (changed(20, lambda row: float(row[20]) + 1), 'engine_route_distance_agrees'),
}
results = []
with tempfile.TemporaryDirectory(prefix='baltic-route-verifier-') as temporary:
    for name, (content, expected_failed_check) in cases.items():
        log = Path(temporary) / (name + '.log')
        out = Path(temporary) / (name + '.json')
        log.write_text(content, encoding='utf-8')
        run = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'tools/navigation/verify_boat_route_input.py'),
                              '--log', str(log), '--out', str(out)], capture_output=True)
        if run.returncode != 1 or not out.exists():
            raise AssertionError((name, run.returncode, run.stderr.decode(errors='replace')))
        result = json.loads(out.read_text())
        if result['status'] != 'INCONCLUSIVE_OR_FAIL' or result['checks'][expected_failed_check]:
            raise AssertionError((name, result))
        results.append({'case': name, 'rejected_by': expected_failed_check})
a.out.write_text(json.dumps({'status': 'PASS_NEGATIVE_CONTROLS', 'source_log': str(a.log),
                            'cases': results, 'limits': 'Synthetic corruptions, not new engine observations.'}, indent=2) + '\n')
print(json.dumps(results, indent=2))
