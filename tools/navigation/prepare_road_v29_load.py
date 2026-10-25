"""Bind the exercised 0/25/100/0 fixture to the final V29 world before runtime."""
from pathlib import Path
import copy
import hashlib
import json
import numpy as np
import rasterio
from waterway_common import sample

ROOT = Path(__file__).resolve().parents[2]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    previous = ROOT/'evidence/overnight-2026-10-01/foundation-load-v1/reference.json'
    previous_sites = ROOT/'evidence/overnight-2026-10-01/performance-v10-sites.json'
    assert sha(previous) == '92dd06bca9ef71eefbf042bc693e007ddc2844395ee829bc1dfed831b4a87b4e'
    assert sha(previous_sites) == 'fca07201eb46701bcea4842ec9f66338802f2684731101c98ac53fd2f23f22b3'
    asc = ROOT/'tests/regional_road_network_v29/baltic_road_network_v29.asc'
    assert sha(asc) == 'ed6cdaa5a1b9100a6f74041e9338f1c21f100a6686f596c73f79f33c4b8662c6'
    packed = ROOT/'build-output/road_v29_freshnav/verification.json'
    receipt = json.loads(packed.read_text())
    assert receipt['status'] == 'PASS_NAVMESH_PACKED_BYTE_PARITY'
    assert receipt['wrp_sha256'] == '2c95ab7dde3b353f69ecb929de1b3d413ba0070a5ce8feb4ac6537b87033ec84'
    world = Path('P:/Mods/@DayZ_Baltic_RoadV29/Addons/narva_trial.pbo')
    water = world.with_name('baltic_water.pbo')
    ref = copy.deepcopy(json.loads(previous.read_text()))
    assert sha(world) == receipt['pbo_sha256'] and sha(water) == ref['water_pbo_sha256']
    mission = Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions/BalticFoundationLoadV1.BalticTrial')
    source = ROOT/'missions/BalticFoundationLoadV1.BalticTrial/init.c'
    assert sha(source) == sha(mission/'init.c') == ref['mission_sha256']
    sites = copy.deepcopy(json.loads(previous_sites.read_text()))
    xy = np.asarray(sites['points'])
    assert xy.shape == (101, 2)
    with rasterio.open(asc) as ds:
        heights = sample(ds.read(1), xy[:, 0]+200000, xy[:, 1]).astype(float)
    assert np.isfinite(heights).all() and heights.min() >= 1.25
    sites.update(status='FROZEN_ROAD_V29_LOAD_SITES_NOT_RUN',
                 terrain_sha256=sha(asc), heights=heights.tolist(),
                 parent_reference_sha256=sha(previous_sites))
    ref.update(status='FROZEN_ROAD_V29_LOAD_NOT_RUN',
               pbo_sha256=receipt['pbo_sha256'], navmesh_sha256=receipt['navmesh_sha256'],
               compiled_wrp_sha256=receipt['wrp_sha256'], terrain_sha256=sha(asc),
               parent_v10_reference_sha256=sha(previous), deployed_mission=str(mission),
               deployed_world=str(world), package_receipt_sha256=sha(packed),
               changes=['Only artifact identity and independent expected ground heights changed from V10.',
                        'Mission, population, timing, stimulus, site XY and criteria remain unchanged.'])
    out = ROOT/'evidence/foundation-followup-2026-10-01/road-v29-load'
    assert not out.exists()
    out.mkdir()
    (out/'sites.json').write_text(json.dumps(sites, indent=2)+'\n', encoding='utf-8')
    (out/'reference.json').write_text(json.dumps(ref, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status=ref['status'], reference_sha256=sha(out/'reference.json'),
                          sites_sha256=sha(out/'sites.json'), minimum_ground_m=float(heights.min()))))


if __name__ == '__main__':
    main()
