"""Verify exact compiled archives, then stage a new isolated offline preview."""
import json,re,shutil,sys
from pathlib import Path
from discover_native_turns import B,B12,sha
sys.path.insert(0,str(B12))
from author_global_visual import read_pbo,read

source=json.loads((B/'candidate-feasible-verification.json').read_text());coverage=json.loads((B/'candidate-feasible-final-coverage.json').read_text());ref=json.loads((B/'package-seams.json').read_text())
assert source['status']=='PASS_SOURCE_TERRAIN' and coverage['status']=='PASS_GLOBAL_COMPILED_COVERAGE'
assert source['candidate_sha256']==coverage['terrain_sha256']==ref['terrain_sha256']
world=B/'package/world/out/narva_trial.pbo';water=B/'package/water/packed/baltic_water_v30.pbo'
wp=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
assert sha(water)==ref['water_sha256']==coverage['water_sha256'] and sha(wp)==ref['world_source_sha256']==coverage['world_source_sha256']
_,oldprops,old=read_pbo(B12/'final/world/out/narva_trial.pbo');_,props,packed=read_pbo(world)
assert props==oldprops and set(old)==set(packed)
changes=[k for k in old if old[k]!=packed[k]];assert changes==['baltic_trial.wrp']
compiled=B/'package/world/temp/narva_trial'
if not compiled.is_dir():compiled=B/'package/world/temp/dayz_baltic_12km_dev/tb/narva_trial'
assert all((compiled/k).read_bytes()==v for k,v in packed.items())
assert packed['baltic_trial.wrp'].startswith(b'OPRW') and packed['config.bin'].startswith(b'\0raP')
names={s.decode('ascii') for s in re.findall(rb'baltic_water_v30\\[a-z0-9_]+\.p3d',packed['baltic_trial.wrp'].lower())}
expected={o['name'].lower() for o in read(wp)['objects'] if o['name'].startswith('baltic_water_v30')}
assert names==expected
destination=Path('P:/Mods/@DayZ_Baltic_NativeContourV1/Addons');destination.mkdir(parents=True,exist_ok=False)
for p in (world,water):shutil.copyfile(p,destination/p.name);assert sha(p)==sha(destination/p.name)
report=dict(status='ISOLATED_NATIVE_CONTOUR_PREVIEW_NOT_RUNTIME_ACCEPTED',destination=str(destination.parent),
            files={p.name:sha(p) for p in destination.glob('*.pbo')},terrain_sha256=ref['terrain_sha256'],world_source_sha256=sha(wp),
            changed_world_entries=changes,compiled_tree_byte_parity=True,referenced_water_models=len(names),
            textures_config_materials_navmesh_unchanged=True,runtime_status='NOT_RUN_PORT_ATTRIBUTION_UNKNOWN',
            limits=['261 terrain vertices and two extra seam instances; earlier preview retained.','No TB/navmesh promotion or global shape acceptance.'])
(B/'deploy.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
