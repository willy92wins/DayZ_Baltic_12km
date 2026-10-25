"""Prepare the EV80 native readback mission from the verified EV79 probe.

Do not run until EV80 deploy.json and the actual deployed PBO hashes are ready.
The first operations are readiness/hash checks; no output is written before them.
"""
from pathlib import Path
import csv
import hashlib
import json
import shutil
import subprocess
import sys

import numpy as np

R = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-constrained-20261010')
EV79 = Path(r'E:/DayZ-Baltic-Build/v30-narva-dry-bank-relief-20261010')
DEPLOY_PATH = R / 'deploy.json'
BASE_REF = EV79 / 'native-reference.json'
BASE_SNAPSHOT = EV79 / 'native-snapshot.log'
BASE_VERIFICATION = EV79 / 'native-verification.json'
CANDIDATE = R / 'candidate/terrain.npz'
EV79_TERRAIN = EV79 / 'candidate/terrain.npz'
W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
SERVER_MPMISSIONS = Path(r'C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')
MISSION_NAME = 'BalticMixedBankFullWaterV1.BalticTrial'
MISSION_CLASS = 'BalticMixedBankFullWaterMission'
HEADER = 'BALTIC_MIXEDBANK_FULLWATER_V1;BalticTrial;'
LOG_STEM = 'baltic_mixedbank_fullwater_v1'
EXPECTED_MOD = Path(r'P:/Mods/@DayZ_Baltic_MixedBankPreviewV1')
EXPECTED_TERRAIN_SHA = '0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_deploy_ready():
    """Refuse to prepare anything until the real EV80 deployment is verified."""
    assert DEPLOY_PATH.is_file(), f'deploy not ready; missing {DEPLOY_PATH}'
    deploy = json.loads(DEPLOY_PATH.read_text(encoding='utf-8'))
    assert deploy.get('terrain_sha256') == EXPECTED_TERRAIN_SHA, 'deploy terrain identity mismatch'
    assert CANDIDATE.is_file() and sha(CANDIDATE) == EXPECTED_TERRAIN_SHA, 'candidate terrain SHA mismatch'
    assert Path(deploy.get('mod', '')).resolve() == EXPECTED_MOD.resolve(), 'deploy mod path mismatch'
    files = deploy.get('files')
    assert isinstance(files, dict) and files, 'deploy has no PBO file manifest'
    deployed = EXPECTED_MOD / 'Addons'
    for filename, digest in files.items():
        assert Path(filename).name == filename and filename.lower().endswith('.pbo'), f'invalid PBO manifest entry: {filename}'
        pbo = deployed / filename
        assert pbo.is_file() and sha(pbo) == digest, f'actual deployed PBO hash mismatch: {pbo}'
    assert deploy.get('compiled_wrp_sha256'), 'deploy has no compiled WRP identity'
    return deploy


def main():
    # The deployment gate is intentionally first: no mission or reference output
    # is created if deploy.json or an actual P:\ PBO is absent/stale.
    deploy = verify_deploy_ready()
    baseline = json.loads(BASE_REF.read_text(encoding='utf-8'))
    baseline_verification = json.loads(BASE_VERIFICATION.read_text(encoding='utf-8'))
    assert baseline_verification.get('status') == 'PASS_COMPLETE_NATIVE_READBACK'
    assert baseline_verification.get('terrain_sha256') == baseline.get('terrain_sha256')
    assert baseline_verification.get('runtime_sha256') == sha(BASE_SNAPSHOT), 'EV79 baseline runtime snapshot drift'
    assert baseline.get('terrain_sha256') == 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'
    assert baseline.get('vertices') == 4194304 and len(baseline['points']) == 1212
    assert sum('expected_water' in point for point in baseline['points']) == 1205

    source_mission = Path(baseline['local_mission'])
    assert set(baseline['files']) == {'init.c', 'grid.csv', 'risks.csv'}
    for filename, digest in baseline['files'].items():
        assert sha(source_mission / filename) == digest, f'EV79 baseline mission drift: {filename}'

    # Verify EV80 preserves EV79 classification and exact P/F inputs.
    terrain = dict(np.load(CANDIDATE))
    previous = dict(np.load(EV79_TERRAIN))
    heights = terrain['heights']
    classes = terrain['cls']
    assert np.array_equal(classes, previous['cls']), 'EV80 class metadata changed from EV79'
    for name in ('plane.npy', 'visible-field.npy'):
        candidate_input = R / 'candidate' / name
        old_input = EV79 / 'candidate' / name
        assert sha(candidate_input) == sha(old_input), f'P/F changed from EV79: {name}'

    # Recalculate the same 1,212 expected-ground points using the verified
    # terrain sampler; keep translated-water values/point identity unchanged.
    sys.path.insert(0, str(W / 'tools/terrain'))
    from v30_common import tri_sample

    points = [dict(point) for point in baseline['points']]
    xs = np.asarray([point['x'] for point in points], dtype=np.float64)
    zs = np.asarray([point['z'] for point in points], dtype=np.float64)
    previous_ground = np.asarray(tri_sample(previous['heights'], xs, zs), dtype=np.float64)
    old_expected = np.asarray([point['expected_ground'] for point in points], dtype=np.float64)
    assert float(np.max(np.abs(previous_ground - old_expected))) < 1e-7, 'EV79 point reference does not match source interpolation'
    new_ground = np.asarray(tri_sample(heights, xs, zs), dtype=np.float64)
    changed_ground_points = int(np.count_nonzero(np.abs(new_ground - old_expected) > 1e-7))
    for i, point in enumerate(points):
        point['expected_ground'] = float(new_ground[i])

    risk_input = list(csv.reader((source_mission / 'risks.csv').open(encoding='ascii', newline=''), delimiter=';'))
    assert len(risk_input) == len(points) == 1212 and all(len(row) == 5 for row in risk_input)
    risk_x = np.asarray([float(row[1]) for row in risk_input], dtype=np.float64)
    risk_z = np.asarray([float(row[2]) for row in risk_input], dtype=np.float64)
    old_risk_ground = np.asarray(tri_sample(previous['heights'], risk_x, risk_z), dtype=np.float64)
    assert float(np.max(np.abs(old_risk_ground - np.asarray([float(row[3]) for row in risk_input])))) < 1e-7, 'EV79 risk points drift'
    risk_ground = np.asarray(tri_sample(heights, risk_x, risk_z), dtype=np.float64)
    for i, point in enumerate(points):
        assert abs(float(tri_sample(heights, point['x'], point['z'])) - float(new_ground[i])) < 1e-7
    assert sum('expected_water' in point for point in points) == 1205

    mission = R / 'missions' / MISSION_NAME
    server_mission = SERVER_MPMISSIONS / MISSION_NAME
    assert not mission.exists(), f'refusing to overwrite {mission}'
    assert not server_mission.exists(), f'refusing to overwrite {server_mission}'

    # Adapt only the three inputs named by EV79's verified reference. This
    # explicitly excludes sidecars such as storage_1.modset.json.
    mission.mkdir(parents=True)
    for filename in baseline['files']:
        shutil.copy2(source_mission / filename, mission / filename)

    code_path = mission / 'init.c'
    code = code_path.read_text(encoding='utf-8-sig')
    old_header = 'BALTIC_NARVA_DRYBANK_FULLWATER_V1;BalticTrial;' + baseline['terrain_sha256']
    assert code.count(old_header) == 1
    assert code.count('BalticNarvaDryBankFullWaterMission') == 2
    assert code.count('baltic_narva_drybank_fullwater_v1') == 2
    code = code.replace('BalticNarvaDryBankFullWaterMission', MISSION_CLASS)
    code = code.replace('baltic_narva_drybank_fullwater_v1', LOG_STEM)
    code = code.replace(old_header, HEADER + EXPECTED_TERRAIN_SHA)
    code_path.write_text(code, encoding='utf-8', newline='\n')
    assert 'BalticNarvaDryBankFullWaterMission' not in code
    assert 'baltic_narva_drybank_fullwater_v1' not in code
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

    # Keep the EV79 verifier's thresholds, parsing and negative controls. Only
    # mission identity, source terrain and EV80 output names are changed.
    verifier = (EV79 / 'verify_native.py').read_text(encoding='utf-8-sig')
    assert "['BALTIC_NARVA_DRYBANK_FULLWATER_V1','BalticTrial',ref['terrain_sha256']]" in verifier
    assert "E/'native-reference.json'" in verifier
    verifier = verifier.replace("'BALTIC_NARVA_DRYBANK_FULLWATER_V1'", "'BALTIC_MIXEDBANK_FULLWATER_V1'")
    verifier = verifier.replace('narva-drybank-physical-anomalies.csv', 'mixedbank-physical-anomalies.csv')
    verifier = verifier.replace('narva-drybank-unflagged-scalar-queries.csv', 'mixedbank-unflagged-scalar-queries.csv')
    verifier = verifier.replace('narva-drybank-fullwater-runtime.log', 'mixedbank-fullwater-runtime.log')
    old_source = "Path('E:/DayZ-Baltic-Build/v30-narva-dry-bank-relief-20261010/candidate/terrain.npz')"
    assert verifier.count(old_source) == 1
    verifier = verifier.replace(old_source, f"Path('{CANDIDATE.as_posix()}')")
    verifier = verifier.replace("'BALTIC_NARVA_DRYBANK_FULLWATER_V1'", "'BALTIC_MIXEDBANK_FULLWATER_V1'")
    (R / 'verify_native.py').write_text(verifier, encoding='utf-8', newline='\n')

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
        'ground_points_changed_vs_ev79': changed_ground_points,
        'status': 'PREPARED_NOT_RUN_SERVER_ONLY',
        'criteria_source': 'EV79 verify_native.py; parser, sampling thresholds, classifications and negative controls retained; only mission identity, source terrain and output names changed.',
        'baseline_contract': 'EV79 native-reference.json and native-snapshot.log; 4,194,304 vertices, 1,212 calibrated points, 1,205 translated-water points.'
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
        'ground_points_changed_vs_ev79': changed_ground_points,
        'P_sha256': reference['plane_sha256'],
        'F_sha256': reference['visible_field_sha256'],
        'PBOs_verified_at_deploy_path': deploy['files'],
        'lint_files': lint_json['info']['files_scanned'],
        'criteria_unchanged': True
    }, indent=2))


if __name__ == '__main__':
    main()
