from pathlib import Path
import json, hashlib, shutil, subprocess, sys

B = Path(__file__).parent
OLD = B.parent / 'v30-strict-dry-composition-20261009'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
ref = json.loads((OLD / 'dryfloor-fullwater-reference.json').read_text())
source = Path(ref['mission'])
assert all(sha(source / n) == s for n, s in ref['files'].items())
deploy = json.loads((B / 'deploy.json').read_text())
assert deploy['terrain_sha256'] == ref['terrain_sha256']
mods = Path(deploy['destination']) / 'Addons'
assert all(sha(mods / n) == s for n, s in deploy['files'].items())
name = 'BalticBridgeFlagOmissionFullWaterV1.BalticTrial'
mission = B / 'missions' / name
shutil.copytree(source, mission, ignore=shutil.ignore_patterns('storage_*'))
code = (mission / 'init.c').read_text()
for old, new in [
    ('BalticStrictDryFloorFullWaterMission', 'BalticBridgeFlagOmissionFullWaterMission'),
    ('baltic_strict_dry_floor_fullwater_v1', 'baltic_bridge_flag_omission_fullwater_v1'),
    ('BALTIC_STRICT_DRY_FLOOR_FULLWATER_V1', 'BALTIC_BRIDGE_FLAG_OMISSION_FULLWATER_V1'),
]:
    assert old in code
    code = code.replace(old, new)
(mission / 'init.c').write_text(code)
for n in ['grid.csv', 'risks.csv']:
    assert sha(mission / n) == ref['files'][n]
validator = Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py')
done = subprocess.run([sys.executable, str(validator), str(mission)], capture_output=True, text=True)
(B / 'probe-lint.json').write_text(done.stdout)
lint = json.loads(done.stdout)
assert done.returncode == 0 and lint['info']['files_scanned'] == 1 and not lint['errors']
destination = source.parent / name
shutil.copytree(mission, destination)
newref = ref | dict(mission=str(destination), pbo=deploy['files'],
    deployed={str(mods/n): s for n,s in deploy['files'].items()},
    files={p.name:sha(p) for p in mission.iterdir() if p.is_file()},
    baseline_reference_sha256=sha(OLD/'dryfloor-fullwater-reference.json'))
(B / 'bridge-omission-fullwater-reference.json').write_text(json.dumps(newref, indent=2)+'\n')
verifier = (OLD / 'verify_native.py').read_text()
for old,new in [
    ('dryfloor-fullwater','bridge-omission-fullwater'),
    ('dryfloor-physical','bridge-omission-physical'),
    ('dryfloor-unflagged','bridge-omission-unflagged'),
    ('baltic_strict_dry_floor_fullwater_v1','baltic_bridge_flag_omission_fullwater_v1'),
    ('BALTIC_STRICT_DRY_FLOOR_FULLWATER_V1','BALTIC_BRIDGE_FLAG_OMISSION_FULLWATER_V1'),
]:
    assert old in verifier
    verifier = verifier.replace(old,new)
(B / 'verify_native.py').write_text(verifier)
print(json.dumps(dict(status='PREPARED', mission=str(destination), pbo=newref['pbo'], files=newref['files']), indent=2))
