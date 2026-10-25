"""Real joint candidate plus wet-vertex, island, reserve and historical failures."""
from pathlib import Path
import argparse, json
import numpy as np
import rasterio
from shapely.geometry import shape
from verify_joint_road_hydrology import ROOT, EV, sha, audit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder', type=Path, required=True)
    p.add_argument('--outline-proof', type=Path, required=True)
    p.add_argument('--positive', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(); assert not a.out.exists()
    proof = json.loads(a.positive.read_text()); asc = next(a.folder.glob('*.asc'))
    assert proof['status'] == 'PASS_OFFLINE_JOINT_HYDROLOGY_AND_PROTECTED_LAND'
    assert proof['candidate_sha256'] == sha(asc) and all(proof['checks'].values())
    actual = audit(a.folder, a.outline_proof)
    assert actual['status'] == proof['status']
    with rasterio.open(asc) as ds:
        h = ds.read(1)
    ref = np.load(ROOT/'tests/regional_outline_smoothing_v33/reference.npz')
    wet = ref['wet'] | ref['ocean']; rr, cc = np.argwhere(wet)[0]
    island = shape(json.loads((EV/'protected-islands-game.json').read_text())['features'][0]['geometry']).representative_point()
    reserve = np.load(ROOT/'tests/regional_outline_v3/reference.npz')['reserve']
    dry = np.argwhere(reserve & ~wet); r0, c0 = dry[len(dry)//2]
    cases = [('changed_wet_vertex', int(rr), int(cc), .25, 'wet_vertices_exact'),
             ('island_sunk', int((12282-island.y)//6), int(island.x//6), -100., 'protected_land_planes'),
             ('reserve_sunk', int(r0), int(c0), -100., 'reserve_dry_classification_preserved')]
    results = []
    for name, row, col, delta, key in cases:
        damaged = h.copy(); damaged[row:row+2, col:col+2] += delta
        report = audit(a.folder, a.outline_proof, heights=damaged)
        assert report['status'] == 'FAIL_JOINT_HYDROLOGY' and not report['checks'][key]
        # The requested physical guard must reject the mutation independently
        # of the file-proof mismatch on synthetic in-memory terrain.
        results.append(dict(name=name, rejected=True, physical_guard=key))
        print(json.dumps(results[-1]), flush=True)
    old = ROOT/'tests/regional_road_network_v24'
    try:
        audit(old, old/'full-outline-discriminator.json')
    except AssertionError as error:
        assert str(error) == 'Continuous source geometry not accepted', str(error)
        results.append(dict(name='actual_v24_invalid_shore_proof', rejected=True))
    else:
        raise AssertionError('Historical physical shore failure accepted')
    result = dict(status='PASS_REAL_JOINT_HYDROLOGY_AND_FOUR_NEGATIVES',
                  candidate_sha256=sha(asc), positive_sha256=sha(a.positive), tests=results)
    a.out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
