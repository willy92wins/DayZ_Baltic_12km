"""Prepare the EV82 native readback mission from the verified EV80 probe.

Do not run until EV82 consumer PASS, deploy.json, and actual deployed PBO hashes are ready.
The readiness/hash gates precede any mission creation or editing.
"""
from pathlib import Path
import csv
import hashlib
import json
import shutil
import subprocess
import sys

import numpy as np

R = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010')
EV80 = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-constrained-20261010')
DEPLOY_PATH = R / 'deploy.json'
BASE_REF = EV80 / 'native-reference.json'
BASE_SNAPSHOT = EV80 / 'native-snapshot.log'
BASE_VERIFICATION = EV80 / 'native-verification.json'
CANDIDATE = R / 'candidate/terrain.npz'
EV80_TERRAIN = EV80 / 'candidate/terrain.npz'
W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
SERVER_MPMISSIONS = Path(r'C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')
MISSION_NAME = 'BalticIncrementalBankFullWaterV1.BalticTrial'
MISSION_CLASS = 'BalticIncrementalBankFullWaterMission'
HEADER = 'BALTIC_INCREMENTALBANK_FULLWATER_V1;BalticTrial;'
LOG_STEM = 'baltic_incrementalbank_fullwater_v1'
EXPECTED_MOD = Path(r'P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1')
EXPECTED_TERRAIN_SHA = 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
EXPECTED_EV80_TERRAIN_SHA = '0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b'
EXPECTED_EV80_SNAPSHOT_SHA = '5e14a189d288fa4725c7343831bd973357c4b3a5ef4e8ee217f2fb14148239c3'
EXPECTED_NATIVE_VERIFIER_SHA = '675daae3bc1fa5cfa7feecf211132000e91e56e281e86349f1b8f78947da8771'
EXPECTED_WATER_PBO_SHA = '3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
CONSUMER_REPORT = R / 'review-luna' / 'report.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_consumer_pass():
    assert CONSUMER_REPORT.is_file(), f'EV82 consumer report missing: {CONSUMER_REPORT}'
    report = json.loads(CONSUMER_REPORT.read_text(encoding='utf-8'))
    assert report.get('status') == 'PASS_EV82_CONSUMER', 'EV82 independent consumer has not passed'
    assert report.get('candidate_sha256') == EXPECTED_TERRAIN_SHA, 'consumer did not verify exact EV82 terrain'
    gates = report.get('gates')
    assert isinstance(gates, dict) and gates and all(gates.values()), 'one or more EV82 consumer gates are false or missing'
    return report


def verify_native_verifier_prepared():
    """Validate the prepared EV82 verifier without regenerating or overwriting it."""
    verifier_path = R / 'verify_native.py'
    assert verifier_path.is_file(), f'prepared EV82 native verifier missing: {verifier_path}'
    assert sha(verifier_path) == EXPECTED_NATIVE_VERIFIER_SHA, 'prepared EV82 native verifier identity drift'
    verifier = verifier_path.read_text(encoding='utf-8')
    required = (
        "['BALTIC_INCREMENTALBANK_FULLWATER_V1','BalticTrial',ref['terrain_sha256']]",
        "assert sha(source)==ref['terrain_sha256']",
        "EV80/'native-reference.json'",
        'wrong_translated_water_plane',
        'missing_grid_row',
        'missing_end',
        'missing_calibrated_point',
        'missing_scalar_diagnostic_end',
        'duplicate_anomaly',
        'height_mismatch',
        'assert all(negative.values())',
    )
    assert all(token in verifier for token in required), 'prepared EV82 verifier contract/negative controls drift'


def verify_deploy_ready():
    """Require EV82 consumer PASS and actual PBO hashes before mission writes."""
    consumer = verify_consumer_pass()
    assert DEPLOY_PATH.is_file(), f'deploy not ready; missing {DEPLOY_PATH}'
    deploy = json.loads(DEPLOY_PATH.read_text(encoding='utf-8'))
    assert str(deploy.get('status', '')).startswith('DEPLOYED_EV82_'), 'EV82 deployment status is not a deployed state'
    assert deploy.get('terrain_sha256') == EXPECTED_TERRAIN_SHA, 'deploy terrain identity mismatch'
    assert CANDIDATE.is_file() and sha(CANDIDATE) == EXPECTED_TERRAIN_SHA, 'candidate terrain SHA mismatch'
    assert Path(deploy.get('mod', '')).resolve() == EXPECTED_MOD.resolve(), 'deploy mod path mismatch'
    files = deploy.get('files')
    assert isinstance(files, dict) and set(files) == {'narva_trial.pbo', 'baltic_water_v30.pbo'}, 'deploy PBO manifest is not exact'
    assert files['baltic_water_v30.pbo'] == EXPECTED_WATER_PBO_SHA, 'baseline water PBO unexpectedly changed'
    deployed = EXPECTED_MOD / 'Addons'
    for filename, digest in files.items():
        assert Path(filename).name == filename and filename.lower().endswith('.pbo'), f'invalid PBO manifest entry: {filename}'
        pbo = deployed / filename
        assert pbo.is_file() and sha(pbo) == digest, f'actual deployed PBO hash mismatch: {pbo}'
    assert deploy.get('compiled_wrp_sha256'), 'deploy has no compiled WRP identity'
    return deploy


def main():
    # Consumer and deployment/PBO gates are intentionally first: no mission or
    # reference output is created if either required artifact is absent or stale.
    deploy = verify_deploy_ready()
    verify_native_verifier_prepared()
    baseline = json.loads(BASE_REF.read_text(encoding='utf-8'))
    baseline_verification = json.loads(BASE_VERIFICATION.read_text(encoding='utf-8'))
    assert baseline_verification.get('status') == 'PASS_COMPLETE_NATIVE_READBACK'
    assert baseline_verification.get('terrain_sha256') == baseline.get('terrain_sha256')
    assert baseline_verification.get('runtime_sha256') == sha(BASE_SNAPSHOT) == EXPECTED_EV80_SNAPSHOT_SHA, 'EV80 baseline runtime snapshot drift'
    assert baseline.get('terrain_sha256') == EXPECTED_EV80_TERRAIN_SHA
    assert baseline.get('vertices') == 4194304 and len(baseline['points']) == 1212
    assert sum('expected_water' in point for point in baseline['points']) == 1205
    assert sha(EV80_TERRAIN) == EXPECTED_EV80_TERRAIN_SHA, 'EV80 baseline candidate terrain drift'

    source_mission = Path(baseline['local_mission'])
    assert set(baseline['files']) == {'init.c', 'grid.csv', 'risks.csv'}
    for filename, digest in baseline['files'].items():
        assert sha(source_mission / filename) == digest, f'EV80 baseline mission drift: {filename}'

    # Verify EV82 preserves EV80 class metadata and exact P/F inputs.
    terrain = dict(np.load(CANDIDATE))
    previous = dict(np.load(EV80_TERRAIN))
    heights = terrain['heights']
    classes = terrain['cls']
    assert np.array_equal(classes, previous['cls']), 'EV82 class metadata changed from EV80'
    for name in ('plane.npy', 'visible-field.npy'):
        candidate_input = R / 'candidate' / name
        old_input = EV80 / 'candidate' / name
        assert sha(candidate_input) == sha(old_input), f'P/F changed from EV80: {name}'

    # Recalculate the same 1,212 expected-ground points using the verified
    # terrain sampler; keep translated-water values/point identity unchanged.
    sys.path.insert(0, str(W / 'tools/terrain'))
    from v30_common import tri_sample

    points = [dict(point) for point in baseline['points']]
    xs = np.asarray([point['x'] for point in points], dtype=np.float64)
    zs = np.asarray([point['z'] for point in points], dtype=np.float64)
    previous_ground = np.asarray(tri_sample(previous['heights'], xs, zs), dtype=np.float64)
    old_expected = np.asarray([point['expected_ground'] for point in points], dtype=np.float64)
    assert float(np.max(np.abs(previous_ground - old_expected))) < 1e-7, 'EV80 point reference does not match source interpolation'
    new_ground = np.asarray(tri_sample(heights, xs, zs), dtype=np.float64)
    changed_ground_points = int(np.count_nonzero(np.abs(new_ground - old_expected) > 1e-7))
    for i, point in enumerate(points):
        point['expected_ground'] = float(new_ground[i])

    risk_input = list(csv.reader((source_mission / 'risks.csv').open(encoding='ascii', newline=''), delimiter=';'))
    assert len(risk_input) == len(points) == 1212 and all(len(row) == 5 for row in risk_input)
    risk_x = np.asarray([float(row[1]) for row in risk_input], dtype=np.float64)
    risk_z = np.asarray([float(row[2]) for row in risk_input], dtype=np.float64)
    old_risk_ground = np.asarray(tri_sample(previous['heights'], risk_x, risk_z), dtype=np.float64)
    assert float(np.max(np.abs(old_risk_ground - np.asarray([float(row[3]) for row in risk_input])))) < 1e-7, 'EV80 risk points drift'
    risk_ground = np.asarray(tri_sample(heights, risk_x, risk_z), dtype=np.float64)
    for i, point in enumerate(points):
        assert abs(float(tri_sample(heights, point['x'], point['z'])) - float(new_ground[i])) < 1e-7
    assert sum('expected_water' in point for point in points) == 1205

    mission = R / 'missions' / MISSION_NAME
    server_mission = SERVER_MPMISSIONS / MISSION_NAME
    assert not mission.exists(), f'refusing to overwrite {mission}'
    assert not server_mission.exists(), f'refusing to overwrite {server_mission}'

    # Adapt only the three inputs named by EV80's verified reference. This
    # explicitly excludes sidecars such as storage_1.modset.json.
    mission.mkdir(parents=True)
    for filename in baseline['files']:
        shutil.copy2(source_mission / filename, mission / filename)

    code_path = mission / 'init.c'
    code = code_path.read_text(encoding='utf-8-sig')
    old_header = 'BALTIC_MIXEDBANK_FULLWATER_V1;BalticTrial;' + baseline['terrain_sha256']
    assert code.count(old_header) == 1
    assert code.count('BalticMixedBankFullWaterMission') == 2
    assert code.count('baltic_mixedbank_fullwater_v1') == 2
    code = code.replace('BalticMixedBankFullWaterMission', MISSION_CLASS)
    code = code.replace('baltic_mixedbank_fullwater_v1', LOG_STEM)
    code = code.replace(old_header, HEADER + EXPECTED_TERRAIN_SHA)
    code_path.write_text(code, encoding='utf-8', newline='\n')
    assert 'BalticMixedBankFullWaterMission' not in code
    assert 'baltic_mixedbank_fullwater_v1' not in code
    assert code.count(HEADER + EXPECTED_TERRAIN_SHA) == 1

    with (mission / 'grid.csv').open('w', encoding='ascii', newline='') as stream:
        for row in range(2048):
            for col0 in range(0, 2048, 32):
                fields = []
                for col in range(col0, col0 + 32):
                    fields.extend((format(float(heights[row, col]), '.9g'), str(int(classes[row, col]))))
                stream.write(f'{row};{col0};' + ';'.join(fields) + '\n')

    with (mission / 'risks.csv').open('w', encoding='ascii', newline='') as stream:
        for i, source_row in enumerate(risk_input):
            source_row[3] = format(float(risk_ground[i]), '.9g')
            stream.write(';'.join(source_row) + '\n')

    validator = Path(r'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py')
    lint = subprocess.run([sys.executable, str(validator), str(mission)], capture_output=True, text=True)
    try:
        lint_json = json.loads(lint.stdout)
    except Exception as exc:
        raise RuntimeError(f'validator output was not JSON: {lint.stdout[:1000]} {lint.stderr[:1000]}') from exc
    assert lint.returncode == 0 and lint_json.get('info', {}).get('files_scanned') == 1 and not lint_json.get('errors'), lint_json
    (R / 'native-probe-lint.json').write_text(json.dumps(lint_json, indent=2) + '\n', encoding='utf-8')

    file_hashes = {path.name: sha(path) for path in sorted(mission.iterdir()) if path.is_file()}
    reference = dict(baseline)
    reference.update({
        'mission': str(server_mission),
        'local_mission': str(mission),
        'terrain_sha256': EXPECTED_TERRAIN_SHA,
        'files': file_hashes,
        'pbo': deploy['files'],
        'deployed': {str(EXPECTED_MOD / 'Addons' / name): digest for name, digest in deploy['files'].items()},
        'ev80_baseline_terrain_sha256': EXPECTED_EV80_TERRAIN_SHA,
        'ev80_baseline_snapshot_sha256': EXPECTED_EV80_SNAPSHOT_SHA,
        'ev82_consumer_report_sha256': sha(CONSUMER_REPORT),
        'source_runtime_reference': str(BASE_REF),
        'source_runtime_reference_sha256': sha(BASE_REF),
        'source_runtime_snapshot': str(BASE_SNAPSHOT),
        'source_runtime_snapshot_sha256': sha(BASE_SNAPSHOT),
        'source_native_verification': str(BASE_VERIFICATION),
        'source_mission_files_verified': baseline['files'],
        'candidate_deploy_json_sha256': sha(DEPLOY_PATH),
        'compiled_wrp_sha256': deploy['compiled_wrp_sha256'],
        'plane_sha256': sha(R / 'candidate/plane.npy'),
        'visible_field_sha256': sha(R / 'candidate/visible-field.npy'),
        'ground_points_recalculated': len(points),
        'ground_points_changed_vs_ev80': changed_ground_points,
        'status': 'PREPARED_NOT_RUN_SERVER_ONLY',
        'criteria_source': 'EV80 verify_native.py; parser, sampling thresholds, classifications and negative controls retained; only mission identity, candidate source and output names changed.',
        'baseline_contract': 'EV80 native-reference.json and native-snapshot.log (SHA256 5e14a189d288fa4725c7343831bd973357c4b3a5ef4e8ee217f2fb14148239c3); 4,194,304 vertices, 1,212 calibrated points, 1,205 translated-water points.'
    })
    (R / 'native-reference.json').write_text(json.dumps(reference, indent=2) + '\n', encoding='utf-8')

    shutil.copytree(mission, server_mission)
    assert {path.name: sha(path) for path in server_mission.iterdir() if path.is_file()} == file_hashes
    print(json.dumps({
        'status': 'PREPARED_NOT_RUN_SERVER_ONLY',
        'mission': str(server_mission),
        'terrain_sha256': EXPECTED_TERRAIN_SHA,
        'mission_files': file_hashes,
        'native_points': len(points),
        'translated_water_points': sum('expected_water' in point for point in points),
        'ground_points_changed_vs_ev80': changed_ground_points,
        'P_sha256': reference['plane_sha256'],
        'F_sha256': reference['visible_field_sha256'],
        'PBOs_verified_at_deploy_path': deploy['files'],
        'lint_files': lint_json['info']['files_scanned'],
        'criteria_unchanged': True
    }, indent=2))


if __name__ == '__main__':
    main()
