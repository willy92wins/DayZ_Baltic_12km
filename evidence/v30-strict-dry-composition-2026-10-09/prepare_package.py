from pathlib import Path
import json,shutil
B=Path(__file__).parent;OLD=B.parent/'v30-volkhov-stable-derivatives-20261009'
s=(OLD/'stage_and_deploy.py').read_text()
s=s.replace("OLD=B.parent/'v30-isolated-basin-repair-20261009'","OLD=B.parent/'v30-volkhov-stable-derivatives-20261009'")
s=s.replace("'PASS_INDEPENDENT_GEOMETRY'","'PASS_STRICT_DRY_FLOOR_SOURCE'")
s=s.replace("    msta=B.parent/'v30-msta-dry-bank-solve-20261009'\n    assert json.loads((msta/'verification.json').read_text())['status']=='INDEPENDENT_GEOMETRY_PASS'\n",'')
s=s.replace('6c056a61402356aa0f48b04c528e5c696ef17ba6b7eeb42308a62f9942d52f91','36a40b8aef2769c8377ca396c3f2c5041849bbf534c47f2102eae9a13a42a0a1')
s=s.replace('f4600c90a088adf4df2c8f8f2067b03b77ca01aee9f4e9a8f786c0b1ea8cb7ba','7bcfae7662acf3f83ff0f52434a3d9c3f1e8af745574b2fdc3ad689db123a990')
s=s.replace('@DayZ_Baltic_IsolatedBasinsV1','@DayZ_Baltic_TerminalSmoothV1').replace('f3d6d58ea6d80042b23cd8e2958a14b653d1c903e82cc9f7f7b446992cd61c55','b31215548e8ce881e8f72fbc808433c722b99c6f4f278563ee1e759c1931836c')
s=s.replace("target=Path('P:/Mods/@DayZ_Baltic_TerminalSmoothV1/Addons')","target=Path('P:/Mods/@DayZ_Baltic_StrictDryFloorV1/Addons')")
s=s.replace('STAGED_MSTA_VOLKHOV','STAGED_STRICT_DRY_COMPOSITION').replace('DEPLOYED_TERMINAL_SMOOTH_PREVIEW','DEPLOYED_STRICT_DRY_PREVIEW')
s=s.replace("'PASS_GLOBAL_COMPILED_COVERAGE'","'PASS_INHERITED_COMPILED_COVERAGE'")
(B/'stage_and_deploy.py').write_text(s)
s=(OLD/'prepare_probe.py').read_text().replace('BalticTerminalSmoothFullWaterV1','BalticStrictDryFloorFullWaterV1').replace('BalticTerminalSmoothFullWaterMission','BalticStrictDryFloorFullWaterMission').replace('baltic_terminal_smooth_fullwater_v1','baltic_strict_dry_floor_fullwater_v1').replace('BALTIC_TERMINAL_SMOOTH_FULLWATER_V1','BALTIC_STRICT_DRY_FLOOR_FULLWATER_V1').replace('terminal-fullwater','dryfloor-fullwater').replace('terminal-physical','dryfloor-physical').replace('terminal-unflagged','dryfloor-unflagged')
(B/'prepare_probe.py').write_text(s)
C=B/'risk-census';C.mkdir(exist_ok=False);prior=B.parent/'v30-isolated-basin-repair-20261009/risk-census'
for name in ['census_low_dry.py','verify_low_dry.py']:
    code=(prior/name).read_text().replace('73f4cc82192a6042eee30da3e1aeca90b0c4fb578f0ac9e38e31b3a8852556d2','7bcfae7662acf3f83ff0f52434a3d9c3f1e8af745574b2fdc3ad689db123a990');(C/name).write_text(code)
