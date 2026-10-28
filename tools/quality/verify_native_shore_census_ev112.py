"""Independent consumer of native shoreline segments; does not import their producer.

Coverage is against every mixed native face, not the producer's reported count.
This proves a nominal terrain/water intersection inventory, not visible scenery.
"""
import numpy as np

TRIANGLES = np.array([[0, 1, 3], [0, 2, 3]])
OFFSETS = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
SEA = .75
GRID = 6.


def require(condition, reason):
    if not bool(condition):
        raise ValueError(reason)


def inputs(h, plane, field):
    require(h.ndim == 2 and h.shape[0] == h.shape[1] and len(h) >= 2,
            'height_shape')
    n = len(h) - 1
    require(plane.shape == (n, n), 'plane_shape')
    require(field.shape == (n, n, 4), 'field_shape')
    require(np.isfinite(h).all(), 'height_nonfinite')
    require(not np.isinf(plane).any(), 'plane_infinite')
    for start in range(0, n, 128):
        mask = np.isfinite(plane[start:start+128])
        require(np.isfinite(field[start:start+128][mask]).all(), 'pond_field_nonfinite')


def expected_faces(h, plane, field):
    """Independent full-grid wet/dry census, streamed in row strips."""
    n = len(h) - 1
    result = []
    for start in range(0, n, 128):
        end = min(start+128, n)
        for ti, corners in enumerate(TRIANGLES):
            states = []
            for corner in corners:
                dr, dc = OFFSETS[corner]
                ground = h[start+dr:end+dr, dc:n+dc]
                water = np.where(np.isfinite(plane[start:end]), field[start:end, :, corner], SEA)
                states.append(ground < water)
            mixed = (states[0] != states[1]) | (states[0] != states[2])
            row, col = np.nonzero(mixed)
            result.append(((row+start)*n+col)*2+ti)
    return np.sort(np.concatenate(result))


def segments(h, plane, field, seg):
    inputs(h, plane, field)
    n = len(h)
    count = len(seg['p'])
    require(count > 0, 'zero_coverage')
    for name, tail in [('p', (2, 2)), ('key', (2,)), ('cell', (2,)),
                       ('tri', ()), ('pond', ()), ('lev', ())]:
        require(seg[name].shape == (count,)+tail, 'segment_shape_'+name)
        require(np.isfinite(seg[name]).all(), 'segment_nonfinite_'+name)
    for name in ['key', 'cell', 'tri']:
        require(np.issubdtype(seg[name].dtype, np.integer), 'integer_required_'+name)
    r, c = seg['cell'].T
    ti = seg['tri']
    require(((r >= 0) & (c >= 0) & (r < n-1) & (c < n-1)).all(), 'cell_bounds')
    require(((ti == 0) | (ti == 1)).all(), 'triangle_bounds')
    face_ids = (r*(n-1)+c)*2+ti
    require(len(np.unique(face_ids)) == count, 'duplicate_face')
    key_pairs = np.sort(seg['key'], axis=1)
    require((key_pairs[:, 0] != key_pairs[:, 1]).all(), 'repeated_endpoint_edge')
    require(len(np.unique(key_pairs, axis=0)) == count, 'duplicate_edge_pair')
    require(np.array_equal(np.sort(face_ids), expected_faces(h, plane, field)),
            'mixed_face_coverage')
    pond = np.isfinite(plane[r, c])
    require(np.array_equal(seg['pond'], pond), 'pond_metadata')
    require(np.array_equal(seg['lev'], np.where(pond, plane[r, c], SEA)), 'level_metadata')

    # Decode actual edge identities; evaluate the submitted coordinate, not a
    # reconstructed crossing computed with the producer's dA/(dA-dB) formula.
    corners = TRIANGLES[ti]
    rr = r[:, None] + OFFSETS[corners, 0]
    cc = c[:, None] + OFFSETS[corners, 1]
    vertices = rr*n+cc
    differences = h[rr, cc] - np.where(pond[:, None], field[r[:, None], c[:, None], corners], SEA)
    max_edge_error = 0.
    max_residual = 0.
    for slot in [0, 1]:
        keys = seg['key'][:, slot]
        a, b = keys//(n*n), keys % (n*n)
        require(((a >= 0) & (b < n*n) & (a < b)).all(), 'edge_id_bounds')
        require(((vertices == a[:, None]).any(1) & (vertices == b[:, None]).any(1)).all(),
                'edge_not_in_face')
        da = np.where(vertices == a[:, None], differences, 0.).sum(1)
        db = np.where(vertices == b[:, None], differences, 0.).sum(1)
        require(((da < 0) != (db < 0)).all(), 'edge_not_straddling')
        pa = np.column_stack([a % n * GRID, ((n-1)-a//n)*GRID])
        pb = np.column_stack([b % n * GRID, ((n-1)-b//n)*GRID])
        point = seg['p'][:, slot]
        edge = pb-pa
        t = ((point-pa)*edge).sum(1)/(edge*edge).sum(1)
        error = np.linalg.norm(point-(pa+t[:, None]*edge), axis=1)
        require((error <= 1e-9).all() and ((t >= -1e-12) & (t <= 1+1e-12)).all(),
                'point_off_edge')
        # Barycentric coordinates in the actual triangle. No producer helper.
        x = cc*GRID
        z = ((n-1)-rr)*GRID
        denom = (z[:, 1]-z[:, 2])*(x[:, 0]-x[:, 2]) + (x[:, 2]-x[:, 1])*(z[:, 0]-z[:, 2])
        w0 = ((z[:, 1]-z[:, 2])*(point[:, 0]-x[:, 2]) +
              (x[:, 2]-x[:, 1])*(point[:, 1]-z[:, 2]))/denom
        w1 = ((z[:, 2]-z[:, 0])*(point[:, 0]-x[:, 2]) +
              (x[:, 0]-x[:, 2])*(point[:, 1]-z[:, 2]))/denom
        weights = np.column_stack([w0, w1, 1-w0-w1])
        require((weights >= -1e-12).all(), 'point_outside_face')
        residual = np.abs((weights*differences).sum(1))
        require((residual <= 1e-9).all(), 'water_height_residual')
        max_edge_error = max(max_edge_error, float(error.max()))
        max_residual = max(max_residual, float(residual.max()))
    return dict(segments=count, mixed_faces=count, maximum_edge_error_m=max_edge_error,
                maximum_water_height_residual_m=max_residual,
                exact_water_vertex_faces=int((differences == 0).any(1).sum()),
                zero_length_segments=int((np.linalg.norm(np.diff(seg['p'], axis=1)[:, 0], axis=1) < 1e-8).sum()))


def chains(seg, assembled):
    counts = np.zeros(len(seg['p']), np.int32)
    for item in assembled:
        order, points, keys = item['order'], item['pts'], item['keys']
        require(len(order) > 0 and points.shape == (len(order)+1, 2), 'chain_shape')
        require(keys.shape == (len(order)+1,), 'chain_key_shape')
        require(((order >= 0) & (order < len(counts))).all(), 'chain_index_bounds')
        np.add.at(counts, order, 1)
        source = seg['p'][order]
        forward = np.maximum(np.linalg.norm(points[:-1]-source[:, 0], axis=1),
                             np.linalg.norm(points[1:]-source[:, 1], axis=1)) <= 1e-6
        reverse = np.maximum(np.linalg.norm(points[:-1]-source[:, 1], axis=1),
                             np.linalg.norm(points[1:]-source[:, 0], axis=1)) <= 1e-6
        sk = seg['key'][order]
        forward &= (keys[:-1] == sk[:, 0]) & (keys[1:] == sk[:, 1])
        reverse &= (keys[:-1] == sk[:, 1]) & (keys[1:] == sk[:, 0])
        require((forward | reverse).all(), 'chain_geometry_or_key')
        if item['closed']:
            require(keys[0] == keys[-1] and np.linalg.norm(points[0]-points[-1]) <= 1e-6,
                    'false_closed_chain')
    require((counts == 1).all(), 'chain_assignment_coverage')
    return dict(chains=len(assembled), assigned_exactly_once=int((counts == 1).sum()))
