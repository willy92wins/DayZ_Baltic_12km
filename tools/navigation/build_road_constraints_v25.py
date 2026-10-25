"""Add continuous coverage and exact vector-water protection to frozen V24 rows."""
from pathlib import Path
from array import array
import hashlib, json, time
import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.sparse import load_npz, save_npz, coo_matrix, vstack
from rasterio.features import rasterize
from affine import Affine
from shapely.geometry import shape, Polygon
from refine_road_network_v16 import touched, triangle
from fit_road_native_triangles import weights

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'tests/regional_road_network_v24_constraints'
OUT = ROOT / 'tests/regional_road_network_v25_constraints'
CENTRE = np.array([2417.1428225906, 6889.8850822322])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def position(p, station, s):
    return np.column_stack([np.interp(s, station, p[:, k]) for k in (0, 1)])


def breaks(p, station, forms, circle=False):
    """Analytic intersections with parallel lines and the frozen Narva circle."""
    answer = list(station)
    for i, (a, b) in enumerate(zip(p[:-1], p[1:])):
        length = station[i+1] - station[i]
        assert length > 0
        delta = b-a
        for normal, offset in forms:
            u, v = float(a @ normal), float(b @ normal)
            if abs(v-u) < 1e-12:
                continue
            k0 = int(np.floor((min(u, v)-offset)/6))+1
            k1 = int(np.ceil((max(u, v)-offset)/6))
            t = (np.arange(k0, k1)*6+offset-u)/(v-u)
            answer.extend((station[i]+length*t[(t > 0) & (t < 1)]).tolist())
        if circle:
            rel = a-CENTRE
            aa, bb = delta @ delta, 2*(rel @ delta)
            cc = rel @ rel-480**2
            discriminant = bb*bb-4*aa*cc
            if discriminant >= 0:
                for t in ((-bb-np.sqrt(discriminant))/(2*aa),
                          (-bb+np.sqrt(discriminant))/(2*aa)):
                    if 0 < t < 1:
                        answer.append(float(station[i]+length*t))
    return np.unique(np.asarray(answer))


def main():
    began = time.monotonic()
    assert not OUT.exists()
    OUT.mkdir()
    assert sha(ROOT/'tools/navigation/refine_road_network_v16.py') == '92640b4a25e3bc8037fc9d62ebe775232b31fb66ad1051a9a0db3e6cf6cb98de'
    parent = ROOT/'tests/regional_outline_smoothing_v33/reference.npz'
    assert sha(parent) == '8e84d5ce38da8863116c52ecdf9953d5b201a097459513054eea8e0f0e14c45a'
    frozen = json.loads((SOURCE/'build-receipt.json').read_text())
    assert sha(SOURCE/'constraints.npz') == frozen['constraints_sha256']
    assert sha(SOURCE/'variables.npz') == frozen['variables_sha256']
    ref = np.load(parent)
    heights = ref['candidate']; prior = heights.ravel().astype(float)
    old = np.load(SOURCE/'variables.npz'); indices = old['indices']; n = len(indices)
    mapping = np.full(heights.size, -1, dtype=int); mapping[indices] = np.arange(n)
    wd = distance_transform_edt(~(ref['wet'] | ref['ocean']))*6

    def dry(p):
        r = np.clip(np.rint((12282-p[:, 1])/6).astype(int), 0, 2047)
        c = np.clip(np.rint(p[:, 0]/6).astype(int), 0, 2047)
        return (wd[r, c] > 48) & (np.linalg.norm(p-CENTRE, axis=1) > 480)

    # Protect faces containing water even when none of their corners is wet.
    ev = ROOT/'evidence/regional-foundation-v1'
    source_hashes = {'water-surfaces-contour-v2.geojson': 'df860f693a1bf0115cb4af65a13cea5f8006a5a21bc9bca1d88276b83802ccdc',
                     'ocean-game.json': 'c72aaafd6ee35abfcdec180135571e34b9c5eaefb42d3bca1bfbabad6493f757'}
    geos = []
    for name, digest in source_hashes.items():
        assert sha(ev/name) == digest
        geos.extend(shape(f['geometry']) for f in json.loads((ev/name).read_text())['features'])
    cells = rasterize([(g, 1) for g in geos], out_shape=(2047, 2047),
                      transform=Affine(6, 0, 0, 0, -6, 12282),
                      all_touched=True, dtype='uint8').astype(bool)
    water_vertices = np.zeros(heights.shape, bool)
    for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1)):
        water_vertices[dy:2047+dy, dx:2047+dx] |= cells
    exact_water = distance_transform_edt(~water_vertices)*6 <= 30
    frozen_variables = exact_water.ravel()[indices]

    rows, cols, vals, rhs = array('i'), array('i'), array('d'), array('d')
    directions = {}; missing_pieces = 0; extra_joins = 0; chord_points = 0

    def band(poly, tangents):
        for tri in touched(poly):
            bucket = directions.setdefault(tri, {})
            for tangent in tangents:
                normal = np.array([-tangent[1], tangent[0]])
                for vector, limit in ((normal, .0032), (tangent, .06)):
                    for sign in (-1, 1):
                        vector_signed = vector*sign
                        key = (*np.round(vector_signed, 14), limit)
                        bucket[key] = (vector_signed, limit)

    def bound(ix, w, limit):
        row = len(rhs)
        rhs.append(float(limit-w @ prior[ix]))
        for j, value in zip(mapping[ix], w):
            if j >= 0 and abs(value) > 1e-14:
                rows.append(row); cols.append(int(j)); vals.append(float(value))

    grid_forms = [(np.array([1., 0.]), 3.), (np.array([0., 1.]), 3.)]
    native_forms = [(np.array([1., 0.]), 0.), (np.array([0., 1.]), 0.),
                    (np.array([1., 1.]), 0.)]
    angle = np.arange(16)*np.pi/8
    circle = np.column_stack([np.cos(angle), np.sin(angle)])*(4.001/np.cos(np.pi/16))
    for route_number, route in enumerate(frozen['routes']):
        p = np.asarray(route['source_polyline'])
        station = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
        lo, hi = route['solve_start_m'], route['solve_end_m']
        old_knots = np.r_[lo, station[(station > lo) & (station < hi)], hi]
        old_q = position(p, station, old_knots); old_dry = dry(old_q)
        eligibility_breaks = breaks(p, station, grid_forms, circle=True)
        cuts = np.unique(np.r_[lo, eligibility_breaks[(eligibility_breaks > lo) & (eligibility_breaks < hi)], hi])
        mid = (cuts[:-1]+cuts[1:])*.5
        valid = dry(position(p, station, mid))
        span_start, span_end = cuts[:-1][valid], cuts[1:][valid]
        for start, end in zip(span_start, span_end):
            k = int(np.clip(np.searchsorted(old_knots, (start+end)/2)-1, 0, len(old_knots)-2))
            if old_dry[k] and old_dry[k+1]:
                continue
            a, b = position(p, station, [start, end])
            tangent = (b-a)/np.linalg.norm(b-a)
            normal = np.array([-tangent[1], tangent[0]])
            band(Polygon([a+normal*4, b+normal*4, b-normal*4, a-normal*4]), [tangent])
            missing_pieces += 1
        for i in range(1, len(old_q)-1):
            if np.all(old_dry[i-1:i+2]):
                continue
            # Independent consumer uses a 0.37m central difference for direction.
            # Cover eligible intervals within 0.5m on either side of a corner.
            if not np.any((span_start < old_knots[i]+.5) & (span_end > old_knots[i]-.5)):
                continue
            tangents = [old_q[i]-old_q[i-1], old_q[i+1]-old_q[i]]
            tangents = [v/np.linalg.norm(v) for v in tangents]
            bisector = tangents[0]+tangents[1]
            assert np.linalg.norm(bisector) > 1e-6
            tangents.append(bisector/np.linalg.norm(bisector))
            band(Polygon(old_q[i]+circle), tangents); extra_joins += 1

        native_breaks = breaks(p, station, native_forms)
        base_breaks = np.union1d(native_breaks, eligibility_breaks)
        knots = np.unique(np.r_[lo+3, hi-3, base_breaks-3, base_breaks, base_breaks+3])
        knots = knots[(knots >= lo+3) & (knots <= hi-3)]
        if len(knots) < 2:
            continue
        centres = (knots[:-1]+knots[1:])/2
        chord_valid = np.logical_and.reduce([dry(position(p, station, centres+shift)) for shift in (-3, 0, 3)])
        ends = np.unique(np.r_[knots[:-1][chord_valid], knots[1:][chord_valid]])
        pts = np.array([position(p, station, ends+shift) for shift in (-3, 0, 3)])
        ix, w = weights(pts.reshape(-1, 2)); ix = ix.reshape(3, -1, 3); w = w.reshape(3, -1, 3)
        for i in range(len(ends)):
            vertices = ix[:, i, :].ravel()
            coefficients = (w[:, i, :]*np.array([-.5, 1., -.5])[:, None]).ravel()
            bound(vertices, coefficients, .022); bound(vertices, -coefficients, .022)
        chord_points += len(ends)
        if route_number % 20 == 0:
            print(json.dumps(dict(route=route_number, missing_pieces=missing_pieces,
                                  extra_joins=extra_joins, chord_points=chord_points)), flush=True)
    chord_rows = len(rhs)
    for tri, bucket in directions.items():
        ix, gx, gz = triangle(*tri)
        for vector, limit in bucket.values():
            bound(ix, gx*vector[0]+gz*vector[1], limit)
    extra = coo_matrix((np.asarray(vals), (np.asarray(rows), np.asarray(cols))), shape=(len(rhs), n)).tocsr()
    original = load_npz(SOURCE/'constraints.npz')
    combined = vstack([original, extra], format='csr')
    # The immutable prefix allows exact row reuse, not heuristic index reuse.
    assert np.array_equal(combined.indptr[:original.shape[0]+1], original.indptr)
    assert np.array_equal(combined.indices[:len(original.indices)], original.indices)
    assert np.array_equal(combined.data[:len(original.data)], original.data)
    save_npz(OUT/'constraints.npz', combined)
    np.savez_compressed(OUT/'variables.npz', **{k: old[k] for k in old.files if k != 'rhs'},
                        rhs=np.r_[old['rhs'], np.asarray(rhs)], force_unchanged=frozen_variables)
    receipt = dict(frozen)
    receipt.update(status='FROZEN_CONSTRAINTS_ONLY', constraints=combined.shape[0],
                   source_constraints_sha256=frozen['constraints_sha256'],
                   source_variables_sha256=frozen['variables_sha256'],
                   source_prefix_rows=original.shape[0], source_prefix_exact=True,
                   constraints_sha256=sha(OUT/'constraints.npz'), variables_sha256=sha(OUT/'variables.npz'),
                   exact_water_sources=source_hashes, additional_frozen_variables=int(frozen_variables.sum()),
                   water_cell_count=int(cells.sum()), missing_band_pieces=missing_pieces,
                   extra_joins=extra_joins, extra_triangles=len(directions),
                   continuous_chord_points=chord_points, extra_chord_rows=chord_rows,
                   extra_band_rows=len(rhs)-chord_rows, elapsed_s=time.monotonic()-began)
    (OUT/'build-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'routes'}), flush=True)


if __name__ == '__main__':
    main()
