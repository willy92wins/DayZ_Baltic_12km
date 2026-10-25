"""Parser fixtures only: no engine verification. Usage: script.py <fresh_out_dir>."""
import json
import pathlib
import subprocess
import sys

out = pathlib.Path(sys.argv[1])
out.mkdir(exist_ok=False)
gate = pathlib.Path(__file__).with_name('gate_g8_engine_probe.py')
cases = [
    ('wet', 'wet', 0.2, 1, None),
    ('missing_label', None, 0.2, 1, 'label'),
    ('test_label', 'test', 0.2, 1, 'label'),
    ('dry', 'wet', 0.0, 1, 'liquid_control_dry'),
    ('not_streamed', 'wet', 0.2, 0, 'not_streamed'),
    ('non_finite', 'wet', float('nan'), 1, 'non_finite_reading'),
]
checks = []
for name, label, depth, objects, failure in cases:
    run = out / name
    (run / 'probe').mkdir(parents=True)
    point = dict(id=1, kind='kit_confluence', ground=1.0, x=100.0, z=100.0)
    if label is not None:
        point['expect'] = label
    (run / 'probe/points.json').write_text(json.dumps([point]))
    log = run / 'synthetic.log'
    log.write_text(f'BALTIC_KIT_PROBE_V1\nBEGIN;1\nP;1;1;0;pond;surface;{depth};1.2;{objects}\nEND;1\n')
    proc = subprocess.run([sys.executable, '-I', str(gate), str(run), '--log', str(log)], capture_output=True, text=True)
    (run / 'parser.log').write_text(proc.stdout + proc.stderr)
    result = json.loads((run / 'gate-g8.json').read_text())
    passed = proc.returncode == (1 if failure else 0) and result['passed'] == (failure is None)
    passed = passed and (failure is None or failure in result['failures'])
    checks.append(dict(name=name, passed=passed, expected_failure=failure, exit=proc.returncode))
summary = dict(scope='Synthetic parser fixtures; not an engine run', passed=all(c['passed'] for c in checks), checks=checks)
(out / 'fixtures.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary))
sys.exit(0 if summary['passed'] else 1)
