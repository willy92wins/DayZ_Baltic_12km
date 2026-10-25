"""Joint-bank acceptance: continuous geometry replaces unchanged-face inheritance."""
from pathlib import Path
import argparse, json
import numpy as np
import rasterio
from shapely import STRtree, points, distance
from shapely.geometry import shape
from verify_road_hydrology import ROOT, EV, sha, audit as legacy_audit


def audit(folder, outline_proof, heights=None):
    asc = next(folder.glob('*.asc')); digest = sha(asc)
    proof = json.loads(outline_proof.read_text())
    expected = {'pre-solve.json': '5d16aa9664008555cdc96b58ea74d424256a91fdcb9f5d350ffa7d1cc55ffa31',
                'shore-transition.json': '15652b897b68e5ab3dc7927db964cae3d732ec42ae7249cbd4204eba61f5c488'}
    assert proof['candidate_sha256'] == digest and proof['pinned_design'] == expected
    assert proof['status'] == 'PASS_OFFLINE_OUTLINE_GEOMETRY' and all(proof['checks'].values()), 'Continuous source geometry not accepted'
    report = legacy_audit(folder, heights=heights, outline_v33_parent=True)
    checks = report['checks']
    faces_exact = checks.pop('water_native_cells_exact')
    parent = ROOT/'tests/regional_outline_smoothing_v33/reference.npz'
    assert sha(parent) == '8e84d5ce38da8863116c52ecdf9953d5b201a097459513054eea8e0f0e14c45a'
    base = np.load(parent)['candidate']
    with rasterio.open(asc) as ds:
        h = ds.read(1) if heights is None else heights
    r, c = np.where(h != base)
    vertices = points(np.c_[c*6, 12282-r*6])
    source_pins = {'water-surfaces-contour-v2.geojson': 'df860f693a1bf0115cb4af65a13cea5f8006a5a21bc9bca1d88276b83802ccdc',
                   'ocean-game.json': 'c72aaafd6ee35abfcdec180135571e34b9c5eaefb42d3bca1bfbabad6493f757'}
    geos = []
    for name, wanted in source_pins.items():
        assert sha(EV/name) == wanted
        geos.extend(shape(f['geometry']) for f in json.loads((EV/name).read_text())['features'])
    geos = np.asarray(geos, dtype=object); tree = STRtree(geos)
    wet_changes = int(np.sum(distance(vertices, geos[tree.nearest(vertices)]) == 0)) if len(vertices) else 0
    checks['vector_water_vertices_exact'] = wet_changes == 0
    # Supplied mutated arrays are diagnostic only. A file proof cannot validate
    # a different in-memory field, even when its other guards happen to pass.
    checks['full_continuous_outline_proof'] = heights is None
    report.update(status='PASS_OFFLINE_JOINT_HYDROLOGY_AND_PROTECTED_LAND' if all(checks.values()) else 'FAIL_JOINT_HYDROLOGY',
                  candidate_sha256=digest, continuous_outline_proof=str(outline_proof),
                  continuous_outline_sha256=sha(outline_proof), outline_v33_parent=True,
                  face_equality_diagnostic=faces_exact, changed_vector_water_vertices=wet_changes,
                  acceptance='Full continuous V33 plane/depth/margin tests re-executed on this ASC; unchanged faces are not inherited.')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder', type=Path, required=True)
    p.add_argument('--outline-proof', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(); assert not a.out.exists()
    report = audit(a.folder, a.outline_proof)
    a.out.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'islands'}), flush=True)
    raise SystemExit(0 if report['status'].startswith('PASS_') else 1)


if __name__ == '__main__':
    main()
