"""Independent unchanged-face proof for inherited V33 shoreline acceptance."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
import rasterio
from rasterio.features import rasterize
from affine import Affine
from shapely.geometry import shape
from verify_outline_smoothing import basic_checks, frozen_runtime_points

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'tests/regional_outline_smoothing_v33'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
PINNED = {
    'reference.npz': '8e84d5ce38da8863116c52ecdf9953d5b201a097459513054eea8e0f0e14c45a',
    'independent-consumer.json': '0cf85d0dd9c87c0175d10e51579bc28e6016657fe1f773317a3d5c5af8cfbfa6',
    'shore-transition.json': '15652b897b68e5ab3dc7927db964cae3d732ec42ae7249cbd4204eba61f5c488',
    'pre-solve.json': '5d16aa9664008555cdc96b58ea74d424256a91fdcb9f5d350ffa7d1cc55ffa31',
    'baltic_outline_smoothing_v33.asc': '9d2954fc0600272ec72b61149f5df6b7bbbd347e20979000d96d74bd603b0107',
}


def audit(folder, heights=None):
    for name, digest in PINNED.items():
        assert sha(SOURCE/name) == digest, name
    proof = json.loads((SOURCE/'independent-consumer.json').read_text())
    assert proof['status'] == 'PASS_OFFLINE_OUTLINE_GEOMETRY' and all(proof['checks'].values())
    assert proof['candidate_sha256'] == PINNED['baltic_outline_smoothing_v33.asc']
    source = np.load(SOURCE/'reference.npz')['candidate']
    with rasterio.open(SOURCE/'baltic_outline_smoothing_v33.asc') as ds:
        assert np.array_equal(ds.read(1), source)
    paths = list(folder.glob('*.asc')); assert len(paths) == 1
    with rasterio.open(paths[0]) as ds:
        assert ds.shape == (2048, 2048) and ds.transform == Affine(6, 0, 200000, 0, -6, 12288)
        h = ds.read(1) if heights is None else heights
    assert h.shape == (2048, 2048) and np.isfinite(h).all()
    v10 = ROOT/'tests/regional_foundation_combined_v10/reference.npz'
    assert sha(v10) == 'a43cb0f128c17318207a114f94f08801ff35a81af5d36a4b7e3427dd3d6aca2d'
    ref = np.load(v10)
    # Use explicitly pinned V33 design seeds; do not copy them over road metadata.
    checks, statistics = basic_checks(h, ref['candidate'], ref, SOURCE)
    ev = ROOT/'evidence/regional-foundation-v1'
    hashes = {'water-surfaces-contour-v2.geojson': 'df860f693a1bf0115cb4af65a13cea5f8006a5a21bc9bca1d88276b83802ccdc',
              'ocean-game.json': 'c72aaafd6ee35abfcdec180135571e34b9c5eaefb42d3bca1bfbabad6493f757'}
    geometry = []
    policy = json.loads((SOURCE/'shore-transition.json').read_text())
    assert policy['scope'] == 'all_freshwater_with_marine_floor' and policy['transition_m'] == 6
    for name, digest in hashes.items():
        assert sha(ev/name) == digest
        for feature in json.loads((ev/name).read_text())['features']:
            g = shape(feature['geometry'])
            # Superset of original water, lake cores, original coast and the
            # six-metre lake transition boundaries used by the accepted proof.
            if feature['properties'].get('body', '').startswith('lake_'):
                g = g.buffer(6)
            geometry.append(g)
    cells = rasterize([(g, 1) for g in geometry], out_shape=(2047, 2047),
                      transform=Affine(6, 0, 0, 0, -6, 12282), all_touched=True,
                      dtype='uint8').astype(bool)
    changed = h != source
    affected = changed[:-1, :-1] | changed[1:, :-1] | changed[:-1, 1:] | changed[1:, 1:]
    intersections = int(np.sum(cells & affected))
    checks['water_and_shore_transition_native_faces_exact'] = intersections == 0
    points = frozen_runtime_points(h)
    checks['frozen_81212_points'] = points['passed']
    checks['inherited_source_proof'] = True
    return dict(status='PASS_OFFLINE_INHERITED_CONTINUOUS_OUTLINE' if all(checks.values()) else 'FAIL_OUTLINE_INHERITANCE',
                checks=checks, statistics=statistics, changed_inherited_faces=intersections,
                inherited_native_cells=int(cells.sum()), source_proof_sha256=PINNED['independent-consumer.json'],
                pinned_source=PINNED, geometry_sources=hashes, candidate_sha256=sha(paths[0]),
                frozen_points=points, limits=['Exact equality of all vertices of protected native faces transfers the V33 continuous-plane proof; whole-map dry floor, slopes, deltas and 81212 frozen points are checked again.',
                                            'Island planes and reserve must also pass the independent road hydrology consumer.',
                                            'Offline only; no new native, runtime, wave or performance acceptance.'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--folder', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(); assert not args.out.exists()
    result = audit(args.folder)
    args.out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'frozen_points'}))
    raise SystemExit(0 if result['status'].startswith('PASS_') else 1)


if __name__ == '__main__':
    main()
