from pathlib import Path
B=Path(__file__).parent;old=B.parent/'v30-strict-dry-composition-20261009/risk-census';out=B/'risk-census';out.mkdir(exist_ok=False)
for name in ['census_low_dry.py','verify_low_dry.py']:
    code=(old/name).read_text().replace('7bcfae7662acf3f83ff0f52434a3d9c3f1e8af745574b2fdc3ad689db123a990','682d5553480e779cda1874725dd6a8a5a3615c356b65c546c77342f251857244')
    (out/name).write_text(code)
print('EV70_CENSUS_PREPARED')
