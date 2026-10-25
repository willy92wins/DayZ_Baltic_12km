"""Prepare the EV93 native readback mission from the verified EV82 probe.

Do not run until real EV93 selection receipt, independent consumer PASS,
offline stage/surface gates, and deployed preview PBO hashes are ready. This
source has not created or copied a mission.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys

import numpy as np

from ev93_build_common import (BASE_TERRAIN_SHA, BASE_WATER_PLANE_SHA, BASE_VISIBLE_FIELD_SHA,
    EV82, EV87_NATIVE_V2_VERIFIER_SOURCE_SHA, PREVIEW_MOD, W, acceptance_args,
    load_accepted_inputs, sha, verify_baseline_reference_inputs)

R = Path(__file__).parent
DEPLOY_PATH = R / 'deploy.json'
BASE_REF = EV82 / 'native-reference.json'
BASE_SNAPSHOT = EV82 / 'native-snapshot.log'
BASE_VERIFICATION = EV82 / 'native-verification.json'
CANDIDATE = R / 'candidate/terrain.npz'
EV82_TERRAIN = EV82 / 'candidate/terrain.npz'
SERVER_MPMISSIONS = Path(r'C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')
MISSION_NAME = 'BalticGlobalBankFairingV1.BalticTrial'
MISSION_CLASS = 'BalticGlobalBankFairingMission'
HEADER = 'BALTIC_EV93_SELECTED_BANK_V1;BalticTrial;'
LOG_STEM = 'baltic_ev93_selected_bank_v1'
EXPECTED_MOD = PREVIEW_MOD
EXPECTED_EV82_TERRAIN_SHA = BASE_TERRAIN_SHA
EXPECTED_EV82_SNAPSHOT_SHA = 'c0effbbcf0200bd916a691e94d44546bc573dc30a7c275b8049a8ad64b2863a2'
EXPECTED_NATIVE_VERIFIER_SHA = '5ef9d2b599cb3860d23fba13996fbfdff571f3d655fdd6c60dadbe2729b67df9'
EXPECTED_WATER_PBO_SHA = '3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def barycentric_height_independent(heights, x, z):
    """Solve the local NW-SE triangle plane directly, independent of tri_sample."""
    col = int(x // 6.0)
    row = int((12282.0 - z) // 6.0)
    u, v = x / 6.0 - col, (12282.0 - z) / 6.0 - row
    nodes = ((row, col), (row, col + 1), (row + 1, col + 1)) if u >= v else (
        (row, col), (row + 1, col), (row + 1, col + 1))
    matrix = np.asarray([[cc - col, rr - row, 1.0] for rr, cc in nodes], dtype=np.float64)
    coeff = np.linalg.solve(matrix, np.asarray([heights[rr, cc] for rr, cc in nodes], dtype=np.float64))
    return float(coeff @ np.asarray([u, v, 1.0], dtype=np.float64))


def recalibrated_points(baseline_points, new_ground):
    """Return new serialized points while preserving identity and water values."""
    if len(baseline_points) != len(new_ground):
        raise ValueError('point/height count mismatch')
    points = [dict(point) for point in baseline_points]
    for point, ground in zip(points, new_ground):
        point['expected_ground'] = float(ground)
    for before, after in zip(baseline_points, points):
        if {k: v for k, v in before.items() if k != 'expected_ground'} != {
                k: v for k, v in after.items() if k != 'expected_ground'}:
            raise ValueError('point identity or water fields changed during recalibration')
    return points


def reference_with_points(baseline_reference, points):
    """Start a candidate reference with the recalibrated point list serialized."""
    reference = dict(baseline_reference)
    reference.update({'points': [dict(point) for point in points]})
    if reference['points'] != points:
        raise ValueError('point serialization changed during reference construction')
    return reference


def verify_native_verifier_prepared():
    """Validate the prepared EV93 verifier without regenerating or overwriting it."""
    verifier_path = R / 'verify_native.py'
    assert verifier_path.is_file(), f'prepared EV93 native verifier missing: {verifier_path}'
    assert sha(verifier_path) == EXPECTED_NATIVE_VERIFIER_SHA, 'prepared EV93 native verifier identity drift'
    assert EV87_NATIVE_V2_VERIFIER_SOURCE_SHA == 'be9a531e9ca1fdd663ebe4064345f821b2fb185d0c2e0479522d834cc1689f0c'
    verifier = verifier_path.read_text(encoding='utf-8')
    required = (
        "['BALTIC_EV93_SELECTED_BANK_V1','BalticTrial',ref['terrain_sha256']]",
        "assert sha(source)==ref['terrain_sha256']",
        "EV82/'native-reference.json'",
        'wrong_translated_water_plane',
        'missing_grid_row',
        'missing_end',
        'missing_calibrated_point',
        'missing_scalar_diagnostic_end',
        'duplicate_anomaly',
        'height_mismatch',
        'assert all(negative.values())',
    )
    assert all(token in verifier for token in required), 'prepared EV93 verifier contract/negative controls drift'


def verify_deploy_ready(accepted):
    """Require EV93 consumer PASS and actual isolated preview PBO hashes."""
    stage_path = R / 'stage.json'
    surface_path = R / 'surface-verification.json'
    assert stage_path.is_file() and surface_path.is_file(), 'EV93 stage and surface receipts are required'
    stage = json.loads(stage_path.read_text(encoding='utf-8'))
    surface = json.loads(surface_path.read_text(encoding='utf-8'))
    assert stage.get('status') == 'STAGED_EV93_HEIGHTS_ONLY' and stage.get('objects_and_materials_exact') is True
    assert surface.get('status') == 'PASS_EV93_AFFECTED_SURFACE'
    assert surface.get('gates') and all(surface['gates'].values())
    for artifact in (stage, surface):
        assert artifact.get('terrain_sha256') == accepted['candidate_sha256']
        assert artifact.get('ev93_selection_receipt_sha256') == accepted['receipt_sha256']
        assert artifact.get('ev93_compound_pool_sha256') == accepted['compound_pool_sha256']
        assert artifact.get('ev93_consumer_report_sha256') == accepted['consumer_report_sha256']
        assert artifact.get('ev93_selector_source_sha256') == accepted['selector_source_sha256']
        assert artifact.get('ev93_consumer_source_sha256') == accepted['consumer_source_sha256']
    assert DEPLOY_PATH.is_file(), f'deploy not ready; missing {DEPLOY_PATH}'
    deploy = json.loads(DEPLOY_PATH.read_text(encoding='utf-8'))
    assert deploy.get('status') == 'PACKAGED_EV93_SELECTED_PREVIEW_NATIVE_READBACK_PENDING', 'EV93 selected preview package state is not ready'
    assert deploy.get('terrain_sha256') == accepted['candidate_sha256'], 'deploy terrain identity mismatch'
    assert deploy.get('ev93_selection_receipt_sha256') == accepted['receipt_sha256']
    assert deploy.get('ev93_compound_pool_sha256') == accepted['compound_pool_sha256']
    assert deploy.get('ev93_consumer_report_sha256') == accepted['consumer_report_sha256']
    assert deploy.get('ev93_selector_source_sha256') == accepted['selector_source_sha256']
    assert deploy.get('ev93_consumer_source_sha256') == accepted['consumer_source_sha256']
    assert Path(deploy.get('ev93_candidate', '')).resolve() == accepted['candidate_path'].resolve()
    assert CANDIDATE.is_file() and sha(CANDIDATE) == accepted['candidate_sha256'], 'staged candidate terrain SHA mismatch'
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
    parser = argparse.ArgumentParser(description=__doc__)
    acceptance_args(parser)
    args = parser.parse_args()
    accepted = load_accepted_inputs(args.selection_receipt, args.consumer_report)
    EXPECTED_TERRAIN_SHA = accepted['candidate_sha256']
    deploy = verify_deploy_ready(accepted)
    verify_native_verifier_prepared()
    baseline = json.loads(BASE_REF.read_text(encoding='utf-8'))
    baseline_verification = json.loads(BASE_VERIFICATION.read_text(encoding='utf-8'))
    assert baseline_verification.get('status') == 'PASS_COMPLETE_NATIVE_READBACK'
    assert baseline_verification.get('terrain_sha256') == baseline.get('terrain_sha256')
    assert baseline_verification.get('runtime_sha256') == sha(BASE_SNAPSHOT) == EXPECTED_EV82_SNAPSHOT_SHA, 'EV82 baseline runtime snapshot drift'
    assert baseline.get('terrain_sha256') == EXPECTED_EV82_TERRAIN_SHA
    assert baseline.get('vertices') == 4194304 and len(baseline['points']) == 1212
    assert sum('expected_water' in point for point in baseline['points']) == 1205
    assert sha(EV82_TERRAIN) == EXPECTED_EV82_TERRAIN_SHA, 'EV82 baseline candidate terrain drift'
    assert sha(EV82 / 'candidate/plane.npy') == BASE_WATER_PLANE_SHA
    assert sha(EV82 / 'candidate/visible-field.npy') == BASE_VISIBLE_FIELD_SHA
    verify_baseline_reference_inputs()

    source_mission = Path(baseline['local_mission'])
    assert set(baseline['files']) == {'init.c', 'grid.csv', 'risks.csv'}
    for filename, digest in baseline['files'].items():
        assert sha(source_mission / filename) == digest, f'EV82 baseline mission drift: {filename}'

    # Verify EV93 preserves EV82 class metadata and exact P/F inputs.
    terrain = dict(np.load(CANDIDATE, allow_pickle=False))
    previous = dict(np.load(EV82_TERRAIN, allow_pickle=False))
    heights = terrain['heights']
    classes = terrain['cls']
    assert set(terrain) == set(previous), 'EV93 candidate array schema changed from EV82'
    assert all(np.array_equal(terrain[name], previous[name]) for name in previous if name != 'heights'), 'EV93 class/protection metadata changed from EV82'
    for name in ('plane.npy', 'visible-field.npy'):
        candidate_input = R / 'candidate' / name
        old_input = EV82 / 'candidate' / name
        expected_input_sha = BASE_WATER_PLANE_SHA if name == 'plane.npy' else BASE_VISIBLE_FIELD_SHA
        assert sha(candidate_input) == sha(old_input) == expected_input_sha, f'P/F changed from EV82: {name}'

    # Recalculate the same 1,212 expected-ground points using the verified
    # terrain sampler; keep translated-water values/point identity unchanged.
    sys.path.insert(0, str(W / 'tools/terrain'))
    from v30_common import tri_sample

    points = [dict(point) for point in baseline['points']]
    xs = np.asarray([point['x'] for point in points], dtype=np.float64)
    zs = np.asarray([point['z'] for point in points], dtype=np.float64)
    previous_ground = np.asarray(tri_sample(previous['heights'], xs, zs), dtype=np.float64)
    old_expected = np.asarray([point['expected_ground'] for point in points], dtype=np.float64)
    assert float(np.max(np.abs(previous_ground - old_expected))) < 1e-7, 'EV82 point reference does not match source interpolation'
    new_ground = np.asarray(tri_sample(heights, xs, zs), dtype=np.float64)
    independent_ground = np.asarray([barycentric_height_independent(heights, x, z) for x, z in zip(xs, zs)], dtype=np.float64)
    independent_error = np.abs(independent_ground - new_ground)
    assert float(independent_error.max()) < 1e-5, 'independent triangle-plane audit differs from sampler'
    changed_ground_points = int(np.count_nonzero(np.abs(new_ground - old_expected) > 1e-7))
    points = recalibrated_points(baseline['points'], new_ground)

    risk_input = list(csv.reader((source_mission / 'risks.csv').open(encoding='ascii', newline=''), delimiter=';'))
    assert len(risk_input) == len(points) == 1212 and all(len(row) == 5 for row in risk_input)
    risk_x = np.asarray([float(row[1]) for row in risk_input], dtype=np.float64)
    risk_z = np.asarray([float(row[2]) for row in risk_input], dtype=np.float64)
    old_risk_ground = np.asarray(tri_sample(previous['heights'], risk_x, risk_z), dtype=np.float64)
    assert float(np.max(np.abs(old_risk_ground - np.asarray([float(row[3]) for row in risk_input])))) < 1e-7, 'EV82 risk points drift'
    risk_ground = np.asarray(tri_sample(heights, risk_x, risk_z), dtype=np.float64)
    for i, point in enumerate(points):
        source_row = risk_input[i]
        assert int(source_row[0]) == i and int(source_row[4]) == int(point['cls'])
        assert abs(float(source_row[1]) - float(point['x'])) < 1e-7
        assert abs(float(source_row[2]) - float(point['z'])) < 1e-7
        assert abs(float(tri_sample(heights, point['x'], point['z'])) - float(new_ground[i])) < 1e-7
        assert abs(barycentric_height_independent(heights, point['x'], point['z']) - float(new_ground[i])) < 1e-5
        assert abs(barycentric_height_independent(heights, float(source_row[1]), float(source_row[2])) - float(risk_ground[i])) < 1e-5
    assert sum('expected_water' in point for point in points) == 1205

    mission = R / 'missions' / MISSION_NAME
    server_mission = SERVER_MPMISSIONS / MISSION_NAME
    assert not mission.exists(), f'refusing to overwrite {mission}'
    assert not server_mission.exists(), f'refusing to overwrite {server_mission}'

    # Adapt only the three inputs named by EV82's verified reference. This
    # explicitly excludes sidecars such as storage_1.modset.json.
    mission.mkdir(parents=True)
    for filename in baseline['files']:
        shutil.copy2(source_mission / filename, mission / filename)

    code_path = mission / 'init.c'
    code = code_path.read_text(encoding='utf-8-sig')
    old_header = 'BALTIC_INCREMENTALBANK_FULLWATER_V1;BalticTrial;' + baseline['terrain_sha256']
    assert code.count(old_header) == 1
    assert code.count('BalticIncrementalBankFullWaterMission') == 2
    assert code.count('baltic_incrementalbank_fullwater_v1') == 2
    code = code.replace('BalticIncrementalBankFullWaterMission', MISSION_CLASS)
    code = code.replace('baltic_incrementalbank_fullwater_v1', LOG_STEM)
    code = code.replace(old_header, HEADER + EXPECTED_TERRAIN_SHA)
    code_path.write_text(code, encoding='utf-8', newline='\n')
    assert 'BalticIncrementalBankFullWaterMission' not in code
    assert 'baltic_incrementalbank_fullwater_v1' not in code
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
    reference = reference_with_points(baseline, points)
    reference.update({
        'mission': str(server_mission),
        'local_mission': str(mission),
        'terrain_sha256': EXPECTED_TERRAIN_SHA,
        'files': file_hashes,
        'pbo': deploy['files'],
        'deployed': {str(EXPECTED_MOD / 'Addons' / name): digest for name, digest in deploy['files'].items()},
        'ev82_baseline_terrain_sha256': EXPECTED_EV82_TERRAIN_SHA,
        'ev82_baseline_snapshot_sha256': EXPECTED_EV82_SNAPSHOT_SHA,
        'ev93_selection_receipt_sha256': accepted['receipt_sha256'],
        'ev93_compound_pool_sha256': accepted['compound_pool_sha256'],
        'ev93_selector_source_sha256': accepted['selector_source_sha256'],
        'ev93_consumer_source_sha256': accepted['consumer_source_sha256'],
        'ev93_consumer_report_sha256': accepted['consumer_report_sha256'],
        'ev87_v2_verifier_source_sha256': EV87_NATIVE_V2_VERIFIER_SOURCE_SHA,
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
        'ground_points_changed_vs_ev82': changed_ground_points,
        'ground_points_independent_plane_max_error_m': float(independent_error.max()),
        'ground_points_independent_plane_audit': 'all 1212 points independently solved from the local NW-SE triangle; expected_water and point identity retained',
        'status': 'PREPARED_NOT_RUN_SERVER_ONLY',
        'criteria_source': 'EV82 native verifier; parser, sampling thresholds, classifications and negative controls retained; only mission identity, candidate source and output names changed.',
        'baseline_contract': 'EV82 native-reference.json and native-snapshot.log (SHA256 c0effbbcf0200bd916a691e94d44546bc573dc30a7c275b8049a8ad64b2863a2); 4,194,304 vertices, 1,212 calibrated points, 1,205 translated-water points.'
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
        'ground_points_changed_vs_ev82': changed_ground_points,
        'P_sha256': reference['plane_sha256'],
        'F_sha256': reference['visible_field_sha256'],
        'PBOs_verified_at_deploy_path': deploy['files'],
        'lint_files': lint_json['info']['files_scanned'],
        'criteria_unchanged': True,
        'points_serialized_and_independently_audited': True
    }, indent=2))


if __name__ == '__main__':
    main()
