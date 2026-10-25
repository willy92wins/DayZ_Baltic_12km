"""Freeze the existing local water protocol against the final road V29 artifact."""
from pathlib import Path
import copy
import hashlib
import json
import rasterio
from shapely.geometry import Point, shape
from waterway_common import sample

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / 'evidence/foundation-followup-2026-10-01'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    original = EV / 'outline-water-probe-v1/reference.json'
    assert sha(original) == 'ccd68e21f63099cef41867c8f564172f8c570760eb2ad51395659c6426f93a15'
    asc = ROOT / 'tests/regional_road_network_v29/baltic_road_network_v29.asc'
    assert sha(asc) == 'ed6cdaa5a1b9100a6f74041e9338f1c21f100a6686f596c73f79f33c4b8662c6'
    packed = ROOT / 'build-output/road_v29_freshnav/verification.json'
    receipt = json.loads(packed.read_text())
    assert receipt['status'] == 'PASS_NAVMESH_PACKED_BYTE_PARITY'
    assert receipt['wrp_sha256'] == '2c95ab7dde3b353f69ecb929de1b3d413ba0070a5ce8feb4ac6537b87033ec84'
    deployed_world = Path('P:/Mods/@DayZ_Baltic_RoadV29/Addons/narva_trial.pbo')
    assert sha(deployed_world) == receipt['pbo_sha256']
    before = json.loads(original.read_text())
    probe = Path(before['deployed_mod']) / 'Addons/baltic_foundation_outline_water_v1.pbo'
    mission = Path(before['deployed_mission']) / 'init.c'
    script = ROOT / 'packages/foundation-outline-water-v1/baltic_foundation_outline_water_v1/scripts/5_Mission/BalticRenderProbe.c'
    assert sha(probe) == before['probe_pbo_sha256']
    assert sha(mission) == before['mission_sha256']
    assert sha(script) == before['script_sha256']
    ref = copy.deepcopy(before)
    with rasterio.open(asc) as dataset:
        heights = dataset.read(1)
    assert heights.shape == (2048, 2048)
    water_path = ROOT / 'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson'
    assert sha(water_path) == 'df860f693a1bf0115cb4af65a13cea5f8006a5a21bc9bca1d88276b83802ccdc'
    bodies = json.loads(water_path.read_text())['features']
    controls = []
    for point in ref['points']:
        x, z = point['xz']
        point['ground_m'] = float(sample(heights, x + 200000, z))
        if point['kind'] == 'wet_control':
            matches = [f for f in bodies if shape(f['geometry']).covers(Point(x, z))]
            assert len(matches) == 1
            level = matches[0]['properties']['level_m']
            controls.append(dict(index=point['index'],body=matches[0]['properties']['body'],
                                 level_m=level,ground_m=point['ground_m'],depth_m=level-point['ground_m']))
            assert level-point['ground_m'] >= .15
        else:
            assert point['ground_m'] >= 1.4-1e-6
    for old, new in zip(before['points'], ref['points']):
        assert {k:v for k,v in old.items() if k != 'ground_m'} == {k:v for k,v in new.items() if k != 'ground_m'}
    ref.pop('terrain_npz_sha256')
    ref.update(status='FROZEN_ROAD_V29_LOCAL_WATER_PROTOCOL_NOT_RUN',parent_reference_sha256=sha(original),
               terrain_asc_sha256=sha(asc),world_pbo_sha256=receipt['pbo_sha256'],
               compiled_wrp_sha256=receipt['wrp_sha256'],navmesh_sha256=receipt['navmesh_sha256'],
               deployed_world=str(deployed_world),package_receipt_sha256=sha(packed))
    out = EV / 'road-v29-water'
    assert not out.exists(), 'Preserve frozen runtime evidence'
    out.mkdir()
    (out/'reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
    (out/'preflight.json').write_text(json.dumps(dict(status='PASS_FIXED_LOCAL_SOURCE_POINTS',
        unchanged_coordinates_classes_camera=True,wet_controls=controls,
        reference_sha256=sha(out/'reference.json'),limits=['Local pond levels; not a dynamic wave measurement.']),indent=2)+'\n')
    print(json.dumps(dict(reference=str(out/'reference.json'),sha256=sha(out/'reference.json'),wet_controls=controls)))


if __name__ == '__main__':
    main()
