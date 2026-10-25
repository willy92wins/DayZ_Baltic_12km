from pathlib import Path
import hashlib

B = Path(__file__).parent
source = Path('E:/DayZ-Baltic-Build/v30-strict-dry-composition-20261009/prepare_probe.py')
code = source.read_text()
for old, new in [
    ('BalticStrictDryFloorFullWaterV1', 'BalticVolkhovBedFullWaterV1'),
    ('BalticStrictDryFloorFullWaterMission', 'BalticVolkhovBedFullWaterMission'),
    ('baltic_strict_dry_floor_fullwater_v1', 'baltic_volkhov_bed_fullwater_v1'),
    ('BALTIC_STRICT_DRY_FLOOR_FULLWATER_V1', 'BALTIC_VOLKHOV_BED_FULLWATER_V1'),
    ('dryfloor-fullwater', 'volkhov-bed-fullwater'),
    ('dryfloor-physical', 'volkhov-bed-physical'),
    ('dryfloor-unflagged', 'volkhov-bed-unflagged'),
]:
    assert old in code, old
    code = code.replace(old, new)
needle = "name='BalticVolkhovBedFullWaterV1.BalticTrial'"
assert needle in code
code = code.replace(needle, "assert terrain_hash=='1fc4fe267fa100697103ffb8fffd66b4c469cbf9cbd5be58ac33633022627444'\n" + needle)
target = B/'prepare_probe.py'
assert not target.exists()
target.write_text(code)
assert target.read_text() == code
print(hashlib.sha256(source.read_bytes()).hexdigest())
