from pathlib import Path
import json,hashlib
B=Path(__file__).parent;R=B.parent
old=R/'v30-surface-aligned-20261009';geometry=R/'v30-remaining-exact-dry-support-20261009'
d=json.loads((geometry/'deploy.json').read_text());assert d['status']=='DEPLOYED_EXACT_DRY_PREVIEW'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(Path(d['destination'])/'Addons/narva_trial.pbo')==d['files']['narva_trial.pbo']
assert d['terrain_sha256']=='b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36'
code=(old/'package_surface.py').read_text()
for a,b in [('@DayZ_Baltic_StrictDryFloorV1','@DayZ_Baltic_ExactDrySupportV2'),('1423f25da029ab0524a9d7861c2fbd1b2cda5f97b2244aa27e2a3fc03e3b5580',d['files']['narva_trial.pbo']),('1b6fcff311b7de44b032a1e50eb4a0ae478d0035d2a5066b2d9e59a2b9f9788f',d['compiled_wrp_sha256']),('7bcfae7662acf3f83ff0f52434a3d9c3f1e8af745574b2fdc3ad689db123a990',d['terrain_sha256']),('@DayZ_Baltic_SurfaceAlignedV2','@DayZ_Baltic_BaseSurfacePreviewV1'),('EV61 terrain/objects','EV71 terrain/objects')]:
    assert a in code,a;code=code.replace(a,b)
(B/'package_surface.py').write_text(code)
code=(R/'v30-strict-dry-composition-20261009/prepare_probe.py').read_text()
for a,b in [('BalticStrictDryFloorFullWaterV1','BalticBaseSurfaceFullWaterV1'),('BalticStrictDryFloorFullWaterMission','BalticBaseSurfaceFullWaterMission'),('baltic_strict_dry_floor_fullwater_v1','baltic_base_surface_fullwater_v1'),('BALTIC_STRICT_DRY_FLOOR_FULLWATER_V1','BALTIC_BASE_SURFACE_FULLWATER_V1'),('dryfloor-fullwater','base-surface-fullwater'),('dryfloor-physical','base-surface-physical'),('dryfloor-unflagged','base-surface-unflagged')]:
    assert a in code,a;code=code.replace(a,b)
assert "Path(deploy['destination'])" in code;code=code.replace("Path(deploy['destination'])","Path(deploy['mod'])")
needle="name='BalticBaseSurfaceFullWaterV1.BalticTrial'";assert needle in code;code=code.replace(needle,"assert terrain_hash=='"+d['terrain_sha256']+"'\n"+needle)
(B/'prepare_probe.py').write_text(code)
print('EV72_FINAL_PACKAGE_AND_NATIVE_PROBE_PREPARERS_READY')
