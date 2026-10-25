"""Exercise CLI exit codes; synthetic controls are not observations of DayZ."""
from pathlib import Path
import json
import subprocess
import sys

workspace = Path(__file__).resolve().parent.parent
repo = Path('P:/DayZ_Baltic_12km_dev')
out = workspace / 'work/water-extent/exit-gate-controls'
out.mkdir(exist_ok=False)
baseline = (repo / 'evidence/render-water/agua/baltic_water_observer_v1.log').read_text()
records = []
for name, expected_status, expected_exit in (
    ('authentic_flooding', 'FAIL_DRY_LAND_FLOODING', 1),
    ('synthetic_zero_depth_low_clearance', 'FAIL_DRY_LAND_CLEARANCE', 1),
    ('synthetic_low_sea_no_depth', 'PASS_SAMPLED_DRY_INTERIOR', 0),
    ('synthetic_incomplete_log', None, 1),
):
    lines = baseline.splitlines()
    if name.startswith('synthetic_'):
        for i, line in enumerate(lines):
            if line.startswith('G;'):
                fields = line.split(';')
                fields[6] = '0'
                lines[i] = ';'.join(fields)
    if name == 'synthetic_low_sea_no_depth':
        # All sampled dry ground is above 0.2 m in the independent native ASC.
        values = {'sea_min': '0', 'sea_max': '0.2', 'sea_now': '0.1'}
        lines = [line.split('=', 1)[0] + '=' + values[line.split('=', 1)[0]]
                 if '=' in line and line.split('=', 1)[0] in values else line
                 for line in lines]
    if name == 'synthetic_incomplete_log':
        lines = lines[:-1]
    log = out / (name + '.log')
    log.write_text('\n'.join(lines) + '\n')
    report = out / (name + '.json')
    run = subprocess.run([sys.executable, '-X', 'utf8', str(repo / 'tools/narva/verify_water_observer.py'),
                          '--repo', str(repo), '--log', str(log), '--out', str(report)],
                         capture_output=True, text=True)
    status = json.loads(report.read_text())['status'] if report.exists() else None
    assert run.returncode == expected_exit and status == expected_status, (name, run.returncode, status, run.stderr)
    records.append({'case': name, 'exit_code': run.returncode, 'status': status,
                    'is_runtime_observation': name == 'authentic_flooding'})
result = {'status': 'PASS_CLI_EXIT_GATE', 'cases': records,
          'limits': ['Synthetic controls exercise process exit codes only; they do not validate corrected terrain in DayZ.']}
(out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
