"""Freeze the same V1 routes/criteria for V10, adding precise vector logging."""
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
    parent = ROOT/'evidence/overnight-2026-10-01/regional-boat-v1/reference.json'
    assert sha(parent) == 'a2b77d0fbbd64b0abda36cb322beb51026bd8889ca47b15615c93015da3ce9d2'
    old = json.loads(parent.read_text())
    ref = copy.deepcopy(old)
    src = ROOT/'missions/BalticRegionalBoatV1.BalticTrial/routes.csv'
    route_hashes = [v for k,v in old['mission'].items() if Path(k).name == 'routes.csv']
    assert len(route_hashes) == 1 and sha(src) == route_hashes[0]
    asc = ROOT/'tests/regional_foundation_combined_v10/baltic_regional_foundation_v10.asc'
    assert sha(asc) == '8e25fab25e8f0909fdda302ed4ba3db4c43884c523920f5ef3424db90780eb8b'
    with rasterio.open(asc) as ds:
        heights = ds.read(1)
    for case in ref['cases']:
        xz = np.asarray(case['waypoints_xz'])
        depth = np.asarray(case['water_levels'])-sample(heights,xz[:,0]+200000,xz[:,1])
        assert np.min(depth) >= 3
        case['v10_minimum_waypoint_depth_m'] = float(np.min(depth))
    mission = ROOT/'missions/BalticRegionalBoatV2.BalticTrial'
    ev = ROOT/'evidence/overnight-2026-10-01/regional-boat-v2'
    assert not mission.exists() and not ev.exists()
    addon = Path('P:/Mods/@BalticBoatInputProbe/Addons/baltic_boat_input.pbo')
    assert sha(addon) == 'c5414ffe385eae5b85e1fe6dfef671db568d50a8eb11c74a3f4346f7c6417b2e'
    # NM is attached after generation; freeze the world artifacts in the run receipt.
    mission.mkdir(parents=True)
    ev.mkdir(parents=True)
    (mission/'routes.csv').write_bytes(src.read_bytes())
    (mission/'init.c').write_bytes((ROOT/'tools/navigation/regional_boat_v2_init.c').read_bytes())
    ref.update(log_version=2, terrain=str(asc), terrain_sha256=sha(asc),
               parent_reference_sha256=sha(parent), routes_and_criteria_unchanged=True,
               mission={str(p):sha(p) for p in mission.iterdir()},
               deployment={str(addon):sha(addon)},
               world_deployment_binding='Required fresh run receipt before launch')
    ref['limits'].append('V1 sampled-sector geometry unchanged; V10 depth checked at every waypoint. No release persistence claim.')
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
    print(json.dumps(dict(status='FROZEN_BEFORE_ENGINE', reference_sha256=sha(ev/'reference.json'),
                         mission=str(mission),cases=len(ref['cases'])),indent=2))


if __name__ == '__main__':
    main()
