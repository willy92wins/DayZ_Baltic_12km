from pathlib import Path
import json
B=Path(__file__).parent;R=B.parent;OLD=R/'v30-exact-dry-support-20261009'
assert json.loads((B/'verification.json').read_text())['status']=='PASS_STRICT_DRY_FLOOR_SOURCE'
for name in ['audit_exposure.py','stage_and_deploy.py','audit_coverage.py']:
    code=(OLD/name).read_text()
    if name!='audit_coverage.py':
        code=code.replace("S=R/'v30-strict-dry-composition-20261009'","S=R/'v30-exact-dry-support-20261009'")
        code=code.replace("OLD=Path('E:/DayZ-Baltic-Build/v30-strict-dry-composition-20261009')","OLD=Path('E:/DayZ-Baltic-Build/v30-exact-dry-support-20261009')")
        code=code.replace('931dd215fcb211bf233e18dd4e7fd0ce7a64f772d7294d28abbc5b1a6fbd3107','bb2662993963892c4b0903492d2b4b100ec075c517d63e0797b0f9782e91d435')
        code=code.replace('@DayZ_Baltic_ExactDrySupportV1','@DayZ_Baltic_ExactDrySupportV2')
    (B/name).write_text(code)
C=B/'risk-census';C.mkdir(exist_ok=False)
for name in ['census_low_dry.py','verify_low_dry.py']:
    code=(OLD/'risk-census'/name).read_text().replace('682d5553480e779cda1874725dd6a8a5a3615c356b65c546c77342f251857244','b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36')
    (C/name).write_text(code)
print('EV71_EXPOSURE_PACKAGE_CENSUS_PREPARED')
