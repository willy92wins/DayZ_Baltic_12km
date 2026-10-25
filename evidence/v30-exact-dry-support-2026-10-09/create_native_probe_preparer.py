from pathlib import Path
B=Path(__file__).parent
source=B.parent/'v30-strict-dry-composition-20261009/prepare_probe.py'
code=source.read_text()
for old,new in [
    ('BalticStrictDryFloorFullWaterV1','BalticExactDrySupportFullWaterV1'),
    ('BalticStrictDryFloorFullWaterMission','BalticExactDrySupportFullWaterMission'),
    ('baltic_strict_dry_floor_fullwater_v1','baltic_exact_dry_support_fullwater_v1'),
    ('BALTIC_STRICT_DRY_FLOOR_FULLWATER_V1','BALTIC_EXACT_DRY_SUPPORT_FULLWATER_V1'),
    ('dryfloor-fullwater','exact-dry-fullwater'),
    ('dryfloor-physical','exact-dry-physical'),
    ('dryfloor-unflagged','exact-dry-unflagged')]:
    assert old in code;code=code.replace(old,new)
needle="name='BalticExactDrySupportFullWaterV1.BalticTrial'";assert needle in code
code=code.replace(needle,"assert terrain_hash=='682d5553480e779cda1874725dd6a8a5a3615c356b65c546c77342f251857244'\n"+needle)
assert not (B/'prepare_probe.py').exists();(B/'prepare_probe.py').write_text(code)
print('EV70_NATIVE_PROBE_PREPARER_READY')
