from pathlib import Path
import csv, hashlib, json, shutil, subprocess, sys
import numpy as np

R = Path(r'E:/DayZ-Baltic-Build/v30-narva-dry-bank-relief-20261010')
BASE = Path(r'E:/DayZ-Baltic-Build/v30-base-surface-runtime-20261009')
REF_PATH = BASE / 'base-surface-fullwater-reference.json'
DEPLOY_PATH = R / 'deploy.json'
CANDIDATE = R / 'candidate/terrain.npz'
EV71 = Path(r'E:/DayZ-Baltic-Build/v30-remaining-exact-dry-support-20261009/candidate')
W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev')
SERVER_MPMISSIONS = Path(r'C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')
MISSION_NAME = 'BalticNarvaDryBankFullWaterV1.BalticTrial'
HEADER = 'BALTIC_NARVA_DRYBANK_FULLWATER_V1;BalticTrial;'
LOG_STEM = 'baltic_narva_drybank_fullwater_v1'
EXPECTED_TERRAIN_SHA = 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

reference = json.loads(REF_PATH.read_text(encoding='utf-8'))
deploy = json.loads(DEPLOY_PATH.read_text(encoding='utf-8'))
assert deploy['terrain_sha256'] == EXPECTED_TERRAIN_SHA
assert sha(CANDIDATE) == EXPECTED_TERRAIN_SHA
source_mission = Path(reference['mission'])
assert {p.name: sha(source_mission / p.name) for p in source_mission.iterdir() if p.is_file() and p.name in reference['files']} == reference['files']
for filename, digest in reference['files'].items():
    assert sha(source_mission / filename) == digest, f'EV72 mission source drift: {filename}'
mod_dir = Path(deploy['mod'])
for filename, digest in deploy['files'].items():
    assert sha(mod_dir / 'Addons' / filename) == digest, f'deployed PBO mismatch: {filename}'

# Verify this candidate changes the EV71 heights only; class grid and water inputs remain identical.
t = dict(np.load(CANDIDATE)); h = t['heights']; cls = t['cls']
prev = dict(np.load(EV71 / 'terrain.npz'))
assert np.array_equal(cls, prev['cls']), 'class metadata changed from EV71'
for name in ('plane.npy', 'visible-field.npy'):
    assert sha(R / 'candidate' / name) == sha(EV71 / name), f'P/F changed: {name}'

# Use the already verified native NW-SE interpolation used to prepare the EV72 fullwater probe.
sys.path.insert(0, str(W / 'tools/terrain'))
from v30_common import tri_sample
points = reference['points']
xs = np.array([q['x'] for q in points], dtype=np.float64)
zs = np.array([q['z'] for q in points], dtype=np.float64)
old_h = prev['heights']
old_interp = np.asarray(tri_sample(old_h, xs, zs), dtype=np.float64)
old_expected = np.array([q['expected_ground'] for q in points], dtype=np.float64)
assert float(np.max(np.abs(old_interp - old_expected))) < 1e-7, 'reference points do not match verified EV72 native triangle sampling'
new_ground_reference = np.asarray(tri_sample(h, xs, zs), dtype=np.float64)
changed_ground_points = int(np.count_nonzero(np.abs(new_ground_reference-old_expected) > 1e-7))
for i, q in enumerate(points):
    q['expected_ground'] = float(new_ground_reference[i])
risk_input = list(csv.reader((source_mission / 'risks.csv').open(encoding='ascii', newline=''), delimiter=';'))
assert len(risk_input) == len(points) == 1212 and all(len(row) == 5 for row in risk_input)
risk_x = np.array([float(row[1]) for row in risk_input], dtype=np.float64)
risk_z = np.array([float(row[2]) for row in risk_input], dtype=np.float64)
risk_ground = np.asarray(tri_sample(h, risk_x, risk_z), dtype=np.float64)
assert float(np.max(np.abs(np.asarray(tri_sample(old_h, risk_x, risk_z))-np.array([float(row[3]) for row in risk_input])))) < 1e-7, 'EV72 risks.csv no longer matches source triangle interpolation'
for i, q in enumerate(points):
    assert abs(float(tri_sample(h, q['x'], q['z']))-risk_ground[i]) < 1e-7
    q['expected_ground'] = float(risk_ground[i])

mission = R / 'missions' / MISSION_NAME
assert not mission.exists(), f'mission output already exists: {mission}'
mission.mkdir(parents=True)
for filename in reference['files']:
    shutil.copy2(source_mission / filename, mission / filename)

code_path = mission / 'init.c'
code = code_path.read_text(encoding='utf-8-sig')
old_header = 'BALTIC_BASE_SURFACE_FULLWATER_V1;BalticTrial;' + reference['terrain_sha256']
assert code.count(old_header) == 1
assert code.count('BalticBaseSurfaceFullWaterMission') == 2
assert code.count('baltic_base_surface_fullwater_v1') == 2
code = code.replace('BalticBaseSurfaceFullWaterMission', 'BalticNarvaDryBankFullWaterMission')
code = code.replace('baltic_base_surface_fullwater_v1', LOG_STEM)
code = code.replace(old_header, HEADER + EXPECTED_TERRAIN_SHA)
code_path.write_text(code, encoding='utf-8', newline='\n')
assert 'BalticBaseSurfaceFullWaterMission' not in code
assert 'baltic_base_surface_fullwater_v1' not in code
assert code.count(HEADER + EXPECTED_TERRAIN_SHA) == 1

# Preserve the native readback contract: all 4,194,304 vertex samples, 32 samples per line.
with (mission / 'grid.csv').open('w', encoding='ascii', newline='') as stream:
    for r in range(2048):
        for c0 in range(0, 2048, 32):
            fields = []
            for c in range(c0, c0 + 32):
                fields.extend((format(float(h[r, c]), '.9g'), str(int(cls[r, c]))))
            stream.write(f'{r};{c0};' + ';'.join(fields) + '\n')

with (mission / 'risks.csv').open('w', encoding='ascii', newline='') as stream:
    for i, source_row in enumerate(risk_input):
        source_row[3] = format(float(risk_ground[i]), '.9g')
        stream.write(';'.join(source_row) + '\n')
assert len(points) == 1212
assert sum('expected_water' in q for q in points) == 1205

# Verify the adapted Enforce probe has only the expected identity changes; native sampling/gates stay EV72.
original_verifier = (BASE / 'verify_native.py').read_text(encoding='utf-8-sig')
assert "if not f or f[0]!=['BALTIC_BASE_SURFACE_FULLWATER_V1','BalticTrial',ref['terrain_sha256']]" in original_verifier
assert "if len(p)!=len(ref['points'])" in original_verifier
verifier = original_verifier
verifier = verifier.replace("E=Path(__file__).parent", "E=Path(__file__).parent")
verifier = verifier.replace("'BALTIC_BASE_SURFACE_FULLWATER_V1'", "'BALTIC_NARVA_DRYBANK_FULLWATER_V1'")
verifier = verifier.replace('baltic_base_surface_physical_anomalies.csv', 'narva-drybank-physical-anomalies.csv')
verifier = verifier.replace('base-surface-physical-anomalies.csv', 'narva-drybank-physical-anomalies.csv')
verifier = verifier.replace('base-surface-unflagged-scalar-queries.csv', 'narva-drybank-unflagged-scalar-queries.csv')
verifier = verifier.replace('base-surface-fullwater-runtime.log', 'narva-drybank-fullwater-runtime.log')
verifier = verifier.replace('base-surface-fullwater-verification.json', 'native-verification.json')
old_source = "Path('E:/DayZ-Baltic-Build/v30-complete-dry-surface-20261009/candidate/terrain.npz')"
assert verifier.count(old_source) == 1
verifier = verifier.replace(old_source, f"Path('{CANDIDATE.as_posix()}')")
verifier = verifier.replace("E/'base-surface-fullwater-reference.json'", "E/'native-reference.json'")
(R / 'verify_native.py').write_text(verifier, encoding='utf-8', newline='\n')

# Run the one-file Enforce lint before publishing this mission copy.
validator = Path(r'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py')
lint = subprocess.run([sys.executable, str(validator), str(mission)], capture_output=True, text=True)
try:
    lint_json = json.loads(lint.stdout)
except Exception as exc:
    raise RuntimeError(f'validator output was not JSON: {lint.stdout[:1000]} {lint.stderr[:1000]}') from exc
assert lint.returncode == 0 and lint_json.get('info', {}).get('files_scanned') == 1 and not lint_json.get('errors'), lint_json
(R / 'native-probe-lint.json').write_text(json.dumps(lint_json, indent=2)+'\n', encoding='utf-8')

file_hashes = {p.name: sha(p) for p in sorted(mission.iterdir()) if p.is_file()}
new_ref = dict(reference)
new_ref.update({
    'mission': str(SERVER_MPMISSIONS / MISSION_NAME),
    'local_mission': str(mission),
    'terrain_sha256': EXPECTED_TERRAIN_SHA,
    'files': file_hashes,
    'pbo': deploy['files'],
    'deployed': {str(mod_dir / 'Addons' / name): digest for name, digest in deploy['files'].items()},
    'source_runtime_reference': str(REF_PATH),
    'source_runtime_reference_sha256': sha(REF_PATH),
    'source_mission_files_verified': reference['files'],
    'candidate_deploy_json_sha256': sha(DEPLOY_PATH),
    'compiled_wrp_sha256': deploy['compiled_wrp_sha256'],
    'plane_sha256': sha(R / 'candidate/plane.npy'),
    'visible_field_sha256': sha(R / 'candidate/visible-field.npy'),
    'ground_points_recalculated': len(points),
    'ground_points_changed_vs_ev72': changed_ground_points,
    'status': 'PREPARED_NOT_RUN_SERVER_ONLY',
    'criteria_source': 'EV72 verify_native.py; sampling thresholds and classifications preserved byte-for-byte apart from reference/header/output identities.'
})
(R / 'native-reference.json').write_text(json.dumps(new_ref, indent=2)+'\n', encoding='utf-8')

# Fresh copy to the server's mpmissions directory is explicitly authorized; refuse any existing target.
server_mission = SERVER_MPMISSIONS / MISSION_NAME
assert not server_mission.exists(), f'will not overwrite existing mission: {server_mission}'
shutil.copytree(mission, server_mission)
assert {p.name: sha(p) for p in server_mission.iterdir() if p.is_file()} == file_hashes
print(json.dumps({
    'status': 'PREPARED_NOT_RUN_SERVER_ONLY', 'mission': str(server_mission), 'terrain_sha256': EXPECTED_TERRAIN_SHA,
    'mission_files': file_hashes, 'runtime_points': len(points), 'changed_expected_ground_points_vs_ev72': changed_ground_points,
    'P_sha256': new_ref['plane_sha256'], 'F_sha256': new_ref['visible_field_sha256'],
    'PBOs': deploy['files'], 'lint_files': lint_json['info']['files_scanned'], 'criteria_unchanged': True
}, indent=2))
