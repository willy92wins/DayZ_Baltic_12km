"""Challenge inherited shoreline acceptance with historical and local damage."""
from pathlib import Path
import argparse, json
import numpy as np
import rasterio
from verify_road_outline_inheritance import ROOT, audit, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder', type=Path, required=True)
    p.add_argument('--positive', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(); assert not a.out.exists()
    proof = json.loads(a.positive.read_text())
    asc = next(a.folder.glob('*.asc'))
    assert proof['status'] == 'PASS_OFFLINE_INHERITED_CONTINUOUS_OUTLINE'
    assert proof['candidate_sha256'] == sha(asc) and all(proof['checks'].values())
    with rasterio.open(asc) as ds:
        h = ds.read(1)
    tests = []

    def reject(name, terrain, expected):
        result = audit(a.folder, terrain)
        rejected = result['status'] == 'FAIL_OUTLINE_INHERITANCE' and not result['checks'][expected]
        tests.append(dict(name=name, expected_check=expected, rejected=rejected))
        print(json.dumps(tests[-1]), flush=True)
        assert rejected

    historical = ROOT/'tests/regional_road_network_v24/baltic_road_network_v24.asc'
    assert sha(historical) == '5d75337b5046f4385918ec6e8ab27f2c3f2c0575d95e9cee0767872bd8939774'
    with rasterio.open(historical) as ds:
        reject('actual_v24_changed_water_faces', ds.read(1), 'water_and_shore_transition_native_faces_exact')
    source = ROOT/'tests/regional_foundation_combined_v10/reference.npz'
    assert sha(source) == 'a43cb0f128c17318207a114f94f08801ff35a81af5d36a4b7e3427dd3d6aca2d'
    baseline = np.load(source)
    damaged = h.copy(); row, col = np.argwhere(baseline['wet'])[0]
    damaged[row, col] += .25
    reject('changed_native_water_vertex', damaged, 'water_and_shore_transition_native_faces_exact')
    row, col = int((12282-10433)//6), int(8203//6)
    damaged = h.copy(); damaged[row:row+2, col:col+2] = baseline['candidate'][row:row+2, col:col+2]
    reject('historical_low_coast_restored', damaged, 'water_and_shore_transition_native_faces_exact')
    result = dict(status='PASS_INHERITED_OUTLINE_WITH_THREE_NEGATIVES',
                  candidate_sha256=sha(asc), positive_sha256=sha(a.positive), tests=tests,
                  verifier_sha256=sha(ROOT/'tools/navigation/verify_road_outline_inheritance.py'))
    a.out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
