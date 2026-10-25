"""Check final world archive and deploy a new isolated, unaccepted preview."""
from pathlib import Path
import hashlib,json,re,shutil,sys

B=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path.insert(0,str(B))
from author_global_visual import sha,read,read_pbo

def main():
    for name,status in [('global-coverage-final.json','PASS_GLOBAL_COMPILED_COVERAGE'),
                        ('retained-visual-verification.json','PASS_RETAINED_NATIVE_FIELD'),
                        ('compiled-verification-r2.json','PASS_COMPILED_VISIBLE_GEOMETRY'),
                        ('seam-verification.json','PASS_COMPILED_EXACT_SEAMS')]:
        assert json.loads((B/name).read_text())['status']==status
    ref=json.loads((B/'package-final.json').read_text())
    base=Path('P:/Mods/@DayZ_Baltic_HaloFixV3/Addons/narva_trial.pbo')
    assert sha(base)=='b30ca647abb85568301ec960ece4d2113c562d339b115ba798a9301e1af29e82'
    world=B/'final/world/out/narva_trial.pbo';water=B/'final/water/packed/baltic_water_v30.pbo'
    assert sha(water)==ref['water_sha256']
    _,oldprops,old=read_pbo(base);_,props,packed=read_pbo(world)
    assert props==oldprops and set(packed)==set(old)
    changed=[k for k in old if old[k]!=packed[k]];assert changed==['baltic_trial.wrp']
    compiled=B/'final/world/temp/narva_trial'
    if not compiled.exists():compiled=B/'final/world/temp/dayz_baltic_12km_dev/tb/narva_trial'
    assert compiled.is_dir(),compiled
    assert all((compiled/k).read_bytes()==v for k,v in packed.items())
    wrp=packed['baltic_trial.wrp'];assert wrp.startswith(b'OPRW') and packed['config.bin'].startswith(b'\0raP')
    wp=B/'final/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';assert sha(wp)==ref['world_source_sha256']
    native_names={s.decode('ascii') for s in re.findall(rb'baltic_water_v30\\[a-z0-9_]+\.p3d',wrp.lower())}
    expected_names={o['name'].lower() for o in read(wp)['objects'] if o['name'].startswith('baltic_water_v30')}
    assert native_names==expected_names,(len(native_names),len(expected_names),sorted(expected_names-native_names)[:5])
    destination=Path('P:/Mods/@DayZ_Baltic_GlobalWaterV1/Addons');destination.mkdir(parents=True,exist_ok=False)
    for path in (world,water):
        shutil.copyfile(path,destination/path.name);assert sha(destination/path.name)==sha(path)
    report=dict(status='ISOLATED_GLOBAL_WATER_PREVIEW_NOT_NATIVE_ACCEPTED',destination=str(destination.parent),
                files={p.name:sha(p) for p in destination.glob('*.pbo')},world_source_sha256=sha(wp),
                changed_world_entries=changed,compiled_tree_byte_parity=True,
                compiled_water_model_names=len(native_names),materials_textures_config_and_navmesh_exact=True,
                runtime_status='NOT_RUN_PORT_ATTRIBUTION_UNKNOWN',limits=['Compiled world content and reference names checked; native height/object readback still required.',
                        'Old preview retained; no promotion to Terrain Builder or base 1.0.'])
    (B/'deploy.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
