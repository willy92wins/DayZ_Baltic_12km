"""EV80: deterministic single-vertex bank relief with local angular constraints.

This authors one offline candidate from EV79. It does not package, deploy, or run DayZ.
"""
from pathlib import Path
import hashlib
import json
import math
import time

import numpy as np
from numpy.polynomial import polynomial as poly
from scipy.optimize import minimize_scalar
from scipy.ndimage import distance_transform_edt


B = Path(__file__).resolve().parent
R = B.parent
SOURCE = R / 'v30-narva-dry-bank-relief-20261010' / 'candidate'
TERRAIN = SOURCE / 'terrain.npz'
CONSTRAINTS = R / 'v30-narva-dry-bank-relief-20261010' / 'constraints.npz'
BASELINE_REPORT = R / 'v30-narva-dry-bank-relief-20261010' / 'review-luna' / 'report.json'
OUT = B / 'candidate'
EXPECTED_SHA = 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'
N = 2048
STEP = 6.0
Z0 = 12282.0
MAX_SECONDS = 1200.0
EPS_ANGLE = 1e-8
EPS_HEIGHT = 1e-10


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def topology():
    """Return six faces and twelve unique shared-edge hinges in a local 5x5 patch."""
    triangles = []
    edge_to_faces = {}
    for r in range(-2, 2):
        for c in range(-2, 2):
            nw, ne = (r, c), (r, c + 1)
            sw, se = (r + 1, c), (r + 1, c + 1)
            triangles.extend(((nw, ne, se), (nw, sw, se)))
    for i, tri in enumerate(triangles):
        for j in range(3):
            e = tuple(sorted((tri[j], tri[(j + 1) % 3])))
            edge_to_faces.setdefault(e, []).append(i)
    center = (0, 0)
    incident = [i for i, tri in enumerate(triangles) if center in tri]
    edges = {}
    for i in incident:
        tri = triangles[i]
        for j in range(3):
            e = tuple(sorted((tri[j], tri[(j + 1) % 3])))
            adj = edge_to_faces[e]
            if len(adj) != 2:
                raise AssertionError(f'non-manifold local edge {e}: {adj}')
            edges[e] = tuple(adj)
    hinges = [(e, p) for e, p in sorted(edges.items())]
    if len(incident) != 6 or len(hinges) != 12:
        raise AssertionError(f'expected 6 faces/12 hinges, got {len(incident)}/{len(hinges)}')
    return triangles, incident, hinges


TRIANGLES, INCIDENT, HINGES = topology()


def local_patch(a, r, c):
    return a[r - 2:r + 3, c - 2:c + 3]


def face_affine(patch, tri):
    """Upward unnormalised normal n(delta)=n0+delta*n1 for a local face."""
    ids = [((r + 2) * 5 + (c + 2)) for r, c in tri]
    xz = np.asarray([(c * STEP, -r * STEP) for r, c in tri], dtype=float)
    mat = np.stack((xz[1] - xz[0], xz[2] - xz[0]))
    inv = np.linalg.inv(mat)
    y = np.asarray([patch[r + 2, c + 2] for r, c in tri], dtype=float)
    dmask = np.asarray([1.0 if (r, c) == (0, 0) else 0.0 for r, c in tri])
    g0 = inv @ (y[1:] - y[0])
    gd = inv @ (dmask[1:] - dmask[0])
    n0 = np.asarray([-g0[0], 1.0, -g0[1]])
    n1 = np.asarray([-gd[0], 0.0, -gd[1]])
    return n0, n1


def direct_face_normal(patch, tri, delta=0.0):
    """Independent cross-product normal, oriented toward +Y."""
    xyz = np.asarray([(c * STEP, patch[r + 2, c + 2] + (delta if (r, c) == (0, 0) else 0.0), -r * STEP)
                      for r, c in tri], dtype=float)
    n = np.cross(xyz[1] - xyz[0], xyz[2] - xyz[0])
    if n[1] < 0:
        n = -n
    return n / np.linalg.norm(n)


def norm_coeffs(patch):
    # Includes the six incident faces and neighboring faces across the outer
    # edges of the twelve hinges; only the six incident faces have nonzero n1.
    return [face_affine(patch, tri) for tri in TRIANGLES]


def unit_n(n0, n1, d):
    n = n0 + d * n1
    return n / np.linalg.norm(n)


def face_slope_deg(pair, d=0.0):
    n = pair[0] + d * pair[1]
    return math.degrees(math.atan2(math.hypot(n[0], n[2]), abs(n[1])))


def hinge_deg(pairs, i, j, d=0.0):
    a = unit_n(*pairs[i], d)
    b = unit_n(*pairs[j], d)
    return math.degrees(math.atan2(float(np.linalg.norm(np.cross(a, b))), float(np.dot(a, b))))


def direct_hinge_deg(patch, tri_i, tri_j, d=0.0):
    a = direct_face_normal(patch, tri_i, d)
    b = direct_face_normal(patch, tri_j, d)
    return math.degrees(math.atan2(float(np.linalg.norm(np.cross(a, b))), float(np.dot(a, b))))


def _trim(c):
    c = np.asarray(c, dtype=float)
    while len(c) > 1 and abs(c[-1]) < 1e-13 * max(1.0, float(np.max(np.abs(c)))):
        c = c[:-1]
    return c


def _real_roots(c, lo, hi):
    c = _trim(c)
    if len(c) <= 1 or np.max(np.abs(c)) < 1e-15:
        return []
    roots = poly.polyroots(c)
    out = []
    for z in roots:
        if abs(float(z.imag)) <= 2e-7 and lo - 1e-8 <= float(z.real) <= hi + 1e-8:
            out.append(float(np.clip(z.real, lo, hi)))
    return out


def _dot_poly(a0, a1, b0, b1):
    out = np.zeros(3, dtype=float)
    for k in range(3):
        product = poly.polymul(np.asarray([a0[k], a1[k]]), np.asarray([b0[k], b1[k]]))
        out[:len(product)] += product
    return _trim(out)


def hinge_constraint_roots(a, b, theta_deg, lo, hi):
    """All boundaries of angle(a(delta),b(delta)) <= theta via quadratic/quartic roots."""
    theta = math.radians(theta_deg)
    dot = _dot_poly(a[0], a[1], b[0], b[1])
    aa = _dot_poly(a[0], a[1], a[0], a[1])
    bb = _dot_poly(b[0], b[1], b[0], b[1])
    f = poly.polysub(poly.polymul(dot, dot), (math.cos(theta) ** 2) * poly.polymul(aa, bb))
    return _real_roots(dot, lo, hi) + _real_roots(f, lo, hi)


def slope_constraint_roots(n, theta_deg, lo, hi):
    theta = math.radians(theta_deg)
    # |horizontal|^2 - tan(theta)^2 * vertical^2 <= 0
    hx = np.asarray([n[0][0], n[1][0]])
    hz = np.asarray([n[0][2], n[1][2]])
    vy = np.asarray([n[0][1], n[1][1]])
    f = poly.polysub(poly.polyadd(poly.polymul(hx, hx), poly.polymul(hz, hz)),
                     (math.tan(theta) ** 2) * poly.polymul(vy, vy))
    return _real_roots(f, lo, hi)


def component_containing_zero(roots, lo, hi, feasible):
    pts = [lo, hi]
    pts.extend(float(x) for x in roots if lo + 1e-9 < x < hi - 1e-9)
    pts = sorted(pts)
    uniq = []
    for x in pts:
        if not uniq or x - uniq[-1] > 1e-8:
            uniq.append(x)
    seg_ok = [bool(feasible((a + b) * 0.5)) for a, b in zip(uniq[:-1], uniq[1:])]
    point_ok = [bool(feasible(x)) for x in uniq]
    runs = []
    i = 0
    while i < len(seg_ok):
        if not seg_ok[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(seg_ok) and seg_ok[j + 1] and point_ok[j + 1]:
            j += 1
        runs.append((uniq[i], uniq[j + 1]))
        i = j + 1
    if feasible(0.0):
        for a, b in runs:
            if a - 1e-8 <= 0.0 <= b + 1e-8:
                return max(lo, a), min(hi, b)
        return 0.0, 0.0
    return None


def angle_component(pair_a, pair_b, theta_deg, lo, hi):
    roots = hinge_constraint_roots(pair_a, pair_b, theta_deg, lo, hi)
    feasible = lambda d: hinge_deg((pair_a, pair_b), 0, 1, d) <= theta_deg + 1e-9
    return component_containing_zero(roots, lo, hi, feasible)


def slope_component(pair, theta_deg, lo, hi):
    roots = slope_constraint_roots(pair, theta_deg, lo, hi)
    return component_containing_zero(roots, lo, hi, lambda d: face_slope_deg(pair, d) <= theta_deg + 1e-9)


def self_test():
    rng = np.random.default_rng(80079)
    patch = rng.normal(2.0, 1.25, (5, 5))
    pairs = norm_coeffs(patch)
    for tri_i in INCIDENT:
        for d in (-1.7, -0.25, 0.0, 0.4, 1.9):
            a = unit_n(*pairs[tri_i], d)
            b = direct_face_normal(patch, TRIANGLES[tri_i], d)
            if not np.allclose(a, b, rtol=0, atol=2e-12):
                raise AssertionError(f'normal mismatch for face {tri_i}, delta={d}: {a} != {b}')
    for e, (i, j) in HINGES:
        for d in (-1.3, 0.0, 0.85):
            actual = hinge_deg(pairs, i, j, d)
            direct = direct_hinge_deg(patch, TRIANGLES[i], TRIANGLES[j], d)
            if abs(actual - direct) > 2e-10:
                raise AssertionError(f'hinge cross-product mismatch {e}, delta={d}: {actual} != {direct}')
    vector_mask = source_fold_nodes(patch)
    local_fold = any(hinge_deg(pairs, i, j) > 30.0 + EPS_ANGLE for _e, (i, j) in HINGES)
    if bool(vector_mask[2, 2]) != local_fold:
        raise AssertionError(f'vectorized fold selector disagrees with local 12-hinge template: {vector_mask[2,2]} vs {local_fold}')
    # Known scalar fixture: angle between (-delta,1,0) and (0,1,0) is atan(|delta|).
    a = (np.asarray([0.0, 1.0, 0.0]), np.asarray([-1.0, 0.0, 0.0]))
    b = (np.asarray([0.0, 1.0, 0.0]), np.zeros(3))
    theta = 20.0
    bound = math.tan(math.radians(theta))
    got = angle_component(a, b, theta, -2.0, 2.0)
    if got is None or abs(got[0] + bound) > 1e-8 or abs(got[1] - bound) > 1e-8:
        raise AssertionError(f'quartic/root interval fixture failed: {got} expected +/-{bound}')
    # Same crossing checked through independent atan2/cross formula at interior/exterior samples.
    for d in (-1.0, -bound, 0.0, bound, 1.0):
        direct = math.degrees(math.atan2(float(np.linalg.norm(np.cross(a[0]+d*a[1], b[0]))),
                                         float(np.dot(a[0]+d*a[1], b[0]))))
        if (direct <= theta + 1e-10) != (abs(d) <= bound + 1e-10):
            raise AssertionError('direct formula disagrees with known fixture interval')
    # Face-slope fixture uses a similar affine normal and its exact tangent root.
    sg = slope_component(a, theta, -2.0, 2.0)
    if sg is None or abs(sg[0] + bound) > 1e-8 or abs(sg[1] - bound) > 1e-8:
        raise AssertionError(f'slope root fixture failed: {sg}')
    # End-to-end node solve with a deliberately sub-metre upper cota catches
    # accidental name shadowing between a bound and the hinge loop index.
    src = np.zeros((5, 5), dtype=np.float32); src[2, 2] = 2.0
    trace = []
    node, reason = solve_node(2, 2, src.copy(), src, np.zeros((5, 5), dtype=np.uint8),
                              np.zeros((5, 5), dtype=bool), np.zeros((5, 5), dtype=bool),
                              np.zeros((5, 5), dtype=bool), np.zeros((5, 5), dtype=float),
                              np.full((5, 5), 0.85), 180.0, 180.0, max_delta=0.5,
                              interval_trace=trace)
    if not trace or any(a < -0.2000001 or b > 0.5000001 for a, b in trace):
        raise AssertionError(f'end-to-end node interval escaped [-0.2,0.5]: {trace[:3]}')
    sector_fixture = {
        'vertical_vertex_col_65_maps_edge_col_64': edge_sector(((0, 0), (1, 0)), 64, 65) == (1, 1),
        'horizontal_vertex_row_64_maps_edge_row_63': edge_sector(((0, 0), (0, 1)), 64, 64) == (0, 1),
        'diagonal_63_63_stays_in_sector_0_0': edge_sector(((0, 0), (1, 1)), 63, 63) == (0, 0),
    }
    if not all(sector_fixture.values()):
        raise AssertionError(f'64-cell sector boundary fixture failed: {sector_fixture}')
    if water_floor_bound(0.5, 2.0) != 0.5 or abs(water_floor_bound(3.0, 2.0) - 2.0001) > 1e-12:
        raise AssertionError('source-clamped P/F floor fixture failed')
    return dict(status='PASS', template_faces=len(INCIDENT), template_hinges=len(HINGES),
                random_patch='25 heights; five deltas per face', direct_cross_product_checks=6*5+12*3,
                vectorized_selector_matches_local_template=bool(vector_mask[2,2]) == local_fold,
                hinge_interval_fixture_bounds=list(got), slope_interval_fixture_bounds=list(sg),
                bounded_node_fixture=dict(max_delta=0.5, lower_delta=-0.2, intervals=len(trace),
                                          result_reason=reason, accepted=node is not None),
                sector_64_boundary_fixture=sector_fixture,
                source_clamped_water_floor_fixture='PASS',
                independent_formula='normalized 3D cross products + atan2')


def edge_sector(edge, row, col):
    (r0, c0), (r1, c1) = edge
    if c0 == c1:
        er, ec = min(r0, r1) + row, c0 + col - 1
    elif r0 == r1:
        er, ec = r0 + row - 1, min(c0, c1) + col
    else:
        er, ec = min(r0, r1) + row, min(c0, c1) + col
    return er // 64, ec // 64


def water_floor_bound(source_height, incident_level):
    return min(float(source_height), float(incident_level) + 1e-4)


def incident_water_floor(base, p, f):
    """Vertex-wise max of static P/F surfaces incident to each native vertex."""
    out = np.full((N, N), 0.85, dtype=np.float64)
    for i, (dr, dc) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
        sl = out[dr:dr + N - 1, dc:dc + N - 1]
        pp = np.fmax(p, 0.85)
        ff = np.where(np.isfinite(p), f[:, :, i], 0.85)
        np.fmax(sl, np.fmax(pp, ff), out=sl)
    return np.minimum(base.astype(np.float64, copy=False), out + 1e-4)


def source_fold_nodes(h):
    """Vectorized independent cross-product dihedrals; mark all 4 vertices of each hinge >30 deg."""
    h = h.astype(np.float64, copy=False)
    nw, ne, sw, se = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
    # Positive-Y face normals scaled by six; normalization is unnecessary for atan2 cross/dot.
    a = np.stack((-(ne-nw), np.full_like(nw, 6.0), (se-nw)-(ne-nw)), axis=-1)
    b = np.stack(((sw-nw)-(se-nw), np.full_like(nw, 6.0), (sw-nw)), axis=-1)
    a /= np.linalg.norm(a, axis=-1)[..., None]
    b /= np.linalg.norm(b, axis=-1)[..., None]
    touched = np.zeros(h.shape, dtype=bool)
    diag = np.degrees(np.arctan2(np.linalg.norm(np.cross(a, b), axis=-1),
                                 np.einsum('...i,...i->...', a, b))) > 30.0 + EPS_ANGLE
    touched[:-1, :-1] |= diag; touched[:-1, 1:] |= diag
    touched[1:, :-1] |= diag; touched[1:, 1:] |= diag
    vert = np.degrees(np.arctan2(np.linalg.norm(np.cross(a[:, :-1], b[:, 1:]), axis=-1),
                                 np.einsum('...i,...i->...', a[:, :-1], b[:, 1:]))) > 30.0 + EPS_ANGLE
    touched[:-1, :-2] |= vert; touched[:-1, 1:-1] |= vert
    touched[1:, 1:-1] |= vert; touched[1:, 2:] |= vert
    horiz = np.degrees(np.arctan2(np.linalg.norm(np.cross(b[:-1, :], a[1:, :]), axis=-1),
                                  np.einsum('...i,...i->...', b[:-1, :], a[1:, :]))) > 30.0 + EPS_ANGLE
    touched[:-2, :-1] |= horiz; touched[1:-1, :-1] |= horiz
    touched[1:-1, 1:] |= horiz; touched[2:, 1:] |= horiz
    return touched


def solve_node(r, c, current, source, cls, fixed, wet_support, engineering, distance,
               water_floor, p99_bank, p99_interior, max_delta=2.0, interval_trace=None):
    patch_now = local_patch(current, r, c).astype(np.float64, copy=True)
    patch_src = local_patch(source, r, c).astype(np.float64, copy=False)
    now_pairs = norm_coeffs(patch_now)
    src_pairs = norm_coeffs(patch_src)
    lo = max(-2.0, float(water_floor[r, c]) - float(current[r, c]),
             min(float(source[r, c]), 1.8) - float(current[r, c]))
    hi = min(float(max_delta), float(source[r, c]) + 2.0 - float(current[r, c]))
    if lo > 1e-10 or hi < -1e-10 or lo > hi:
        return None, 'empty_height_interval'
    comps = [(lo, hi)]
    for tri_i in INCIDENT:
        source_slope = face_slope_deg(src_pairs[tri_i])
        cap = max(35.0, source_slope)
        q = slope_component(now_pairs[tri_i], cap, lo, hi)
        if q is None:
            return None, 'empty_slope_component'
        if q[0] < lo - 1e-8 or q[1] > hi + 1e-8:
            raise AssertionError(f'slope interval {q} escaped node bounds [{lo},{hi}]')
        if interval_trace is not None:
            interval_trace.append((q[0], q[1]))
        comps.append(q)
    now_hinge = []; src_hinge = []; sectors = []
    for edge, (ta, tb) in HINGES:
        now_hinge.append(hinge_deg(now_pairs, ta, tb))
        src_hinge.append(hinge_deg(src_pairs, ta, tb))
        sectors.append(edge_sector(edge, r, c))
    sector_caps = {}
    for sec, a in zip(sectors, src_hinge):
        sector_caps[sec] = max(sector_caps.get(sec, -np.inf), a)
    # Dry bank/interior classification follows the independent EV79 consumer's all-four-vertices rule.
    hinge_categories = []
    for edge, (ta, tb) in HINGES:
        vertices = set(TRIANGLES[ta] + TRIANGLES[tb])
        ids = [(r + dr, c + dc) for dr, dc in vertices]
        is_bank = all(cls[rr, cc] == 0 and not wet_support[rr, cc] and not engineering[rr, cc]
                      and distance[rr, cc] <= 96.0 + 1e-9 for rr, cc in ids)
        is_interior = all(cls[rr, cc] == 0 and not wet_support[rr, cc] and not engineering[rr, cc]
                          and distance[rr, cc] > 96.0 + 1e-9 for rr, cc in ids)
        hinge_categories.append('bank' if is_bank else ('interior' if is_interior else None))
    for hinge_index, (edge, (ta, tb)) in enumerate(HINGES):
        thresholds = [sector_caps[sectors[hinge_index]]]
        if src_hinge[hinge_index] <= 30.0 + EPS_ANGLE:
            thresholds.append(30.0)
        kind = hinge_categories[hinge_index]
        if kind == 'bank' and src_hinge[hinge_index] <= p99_bank + EPS_ANGLE:
            thresholds.append(p99_bank)
        elif kind == 'interior' and src_hinge[hinge_index] <= p99_interior + EPS_ANGLE:
            thresholds.append(p99_interior)
        for cap in thresholds:
            q = angle_component(now_pairs[ta], now_pairs[tb], cap, lo, hi)
            if q is None:
                return None, 'empty_hinge_component'
            if q[0] < lo - 1e-8 or q[1] > hi + 1e-8:
                raise AssertionError(f'root interval {q} escaped node bounds [{lo},{hi}]')
            if interval_trace is not None:
                interval_trace.append((q[0], q[1]))
            comps.append(q)
    a = max(q[0] for q in comps); b = min(q[1] for q in comps)
    if a > b + 1e-8 or a > 1e-8 or b < -1e-8:
        return None, 'incompatible_intervals'
    a = min(a, 0.0); b = max(b, 0.0)
    def objective(d):
        return sum(hinge_deg(now_pairs, ta, tb, d) ** 2
                   for _edge, (ta, tb) in HINGES)
    before = objective(0.0)
    options = [(0.0, before)]
    if b - a > 1e-10:
        res = minimize_scalar(objective, bounds=(a, b), method='bounded',
                              options={'xatol': 2e-9, 'maxiter': 80})
        if res.success and np.isfinite(res.fun):
            options.append((float(res.x), float(res.fun)))
        options.extend(((a, objective(a)), (b, objective(b))))
    # Explicit unchanged option is part of the contract.
    d, after = min(options, key=lambda item: (item[1], abs(item[0]), item[0]))
    if before <= 1e-18 or (before - after) / before < 1e-4:
        return None, 'benefit_below_material_floor'
    # Validate float32 outcome against direct cross-product formulas and original EV79 caps.
    old_h = float(current[r, c]); new_h = np.float32(old_h + d)
    actual_d = float(new_h) - old_h
    check_patch = patch_now.copy(); check_patch[2, 2] = float(new_h)
    check_pairs = norm_coeffs(check_patch)
    for tri_i in INCIDENT:
        lim = max(35.0, face_slope_deg(src_pairs[tri_i]))
        direct_n = direct_face_normal(check_patch, TRIANGLES[tri_i])
        direct = math.degrees(math.atan2(math.hypot(direct_n[0], direct_n[2]), abs(direct_n[1])))
        if direct > lim + 2e-8:
            return None, 'float32_slope_rejected'
    after_hinges = []
    for i, (edge, (ta, tb)) in enumerate(HINGES):
        direct = direct_hinge_deg(check_patch, TRIANGLES[ta], TRIANGLES[tb])
        after_hinges.append(direct)
        if direct > sector_caps[sectors[i]] + 2e-8:
            return None, 'float32_sector_rejected'
        if src_hinge[i] <= 30.0 + EPS_ANGLE and direct > 30.0 + 2e-8:
            return None, 'float32_new_over30_rejected'
        kind = hinge_categories[i]
        if kind == 'bank' and src_hinge[i] <= p99_bank + EPS_ANGLE and direct > p99_bank + 2e-8:
            return None, 'float32_bank_p99_rejected'
        if kind == 'interior' and src_hinge[i] <= p99_interior + EPS_ANGLE and direct > p99_interior + 2e-8:
            return None, 'float32_interior_p99_rejected'
    if abs(actual_d) < 1e-8:
        return None, 'float32_no_move'
    if new_h < min(float(source[r, c]), 1.8) - 1e-8 or new_h < water_floor[r, c] - 1e-8:
        return None, 'float32_floor_rejected'
    if abs(float(new_h) - float(source[r, c])) > 2.0 + 1e-8:
        return None, 'float32_budget_rejected'
    before_f32 = sum(x*x for x in now_hinge)
    after_f32 = sum(x*x for x in after_hinges)
    if before_f32 <= 1e-18 or (before_f32 - after_f32) / before_f32 < 1e-4:
        return None, 'float32_benefit_rejected'
    return float(new_h), 'accepted'


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    test = self_test()
    (B / 'root-fixture-test.json').write_text(json.dumps(test, indent=2) + '\n', encoding='utf-8')
    if args.self_test:
        print(json.dumps(test, indent=2)); return
    if sha(TERRAIN) != EXPECTED_SHA:
        raise RuntimeError('EV79 terrain SHA mismatch')
    if OUT.exists() or (B / 'authoring.json').exists():
        raise RuntimeError('Fresh EV80 output required; refusing to overwrite')
    terrain = np.load(TERRAIN)
    src = terrain['heights'].copy()
    cur = src.copy()
    cls = terrain['cls']
    constraint = np.load(CONSTRAINTS)
    fixed = constraint['fixed'].astype(bool, copy=False)
    wet_support = constraint['wet_support'].astype(bool, copy=False)
    engineering = terrain['reserve'] | terrain['platform']
    if fixed.shape != src.shape or wet_support.shape != src.shape:
        raise RuntimeError('EV79 fixed/wet-support shape mismatch')
    rep = json.loads(BASELINE_REPORT.read_text(encoding='utf-8'))
    if rep.get('candidate_sha256') != EXPECTED_SHA:
        raise RuntimeError('EV79 independent report does not identify current source terrain')
    p99_bank = float(rep['angles']['stats']['bank']['candidate']['p99'])
    p99_interior = float(rep['angles']['stats']['interior']['candidate']['p99'])
    p = np.load(SOURCE / 'plane.npy', mmap_mode='r')
    f = np.load(SOURCE / 'visible-field.npy', mmap_mode='r')
    if p.shape != (N-1, N-1) or f.shape != (N-1, N-1, 4):
        raise RuntimeError('EV79 P/F shape mismatch')
    water_floor = incident_water_floor(src, p, f)
    flow = np.isin(cls, (3, 5, 6))
    distance = distance_transform_edt(~flow, sampling=STEP)
    domain = (cls == 0) & (distance <= 96.0 + 1e-9) & ~fixed
    fold_nodes = source_fold_nodes(src)
    selector = domain & fold_nodes
    rr, cc = np.nonzero(selector)
    started = time.monotonic()
    selected = accepted = 0
    reasons = {}
    rows = []
    # Every node is considered at most once in stable row/column order.
    for idx, (r, c) in enumerate(zip(rr.tolist(), cc.tolist())):
        if time.monotonic() - started > MAX_SECONDS:
            break
        if r < 2 or c < 2 or r >= N-2 or c >= N-2:
            reasons['local_border'] = reasons.get('local_border', 0) + 1; continue
        selected += 1
        out, why = solve_node(r, c, cur, src, cls, fixed, wet_support, engineering,
                              distance, water_floor, p99_bank, p99_interior)
        reasons[why] = reasons.get(why, 0) + 1
        if why == 'accepted':
            cur[r, c] = np.float32(out)
            accepted += 1
            rows.append((r, c, float(src[r, c]), float(cur[r, c])))
        if idx % 250 == 0:
            print(json.dumps(dict(considered=idx, selected=selected, accepted=accepted,
                                  seconds=round(time.monotonic()-started, 2)), separators=(',', ':')), flush=True)
    elapsed = time.monotonic() - started
    if elapsed > MAX_SECONDS + 1.0:
        raise RuntimeError(f'1200-second budget exceeded: {elapsed:.2f}s')
    if selected != len(rr):
        # Never emit a candidate from a time-truncated selector traversal.
        (B / 'partial-run-invalid.json').write_text(json.dumps(
            dict(status='INVALID_PARTIAL_RUN', selected_processed=selected,
                 selected_expected=int(len(rr)), elapsed_seconds=round(elapsed, 3),
                 candidate_written=False), indent=2) + '\n', encoding='utf-8')
        raise RuntimeError(f'incomplete selector traversal: processed {selected}/{len(rr)}; no candidate written')
    delta = cur.astype(np.float64) - src.astype(np.float64)
    changed = cur != src
    if np.any(changed & fixed):
        raise AssertionError('EV79 fixed vertex changed')
    if np.any(np.abs(delta[changed]) > 2.0 + 1e-7):
        raise AssertionError('height budget exceeded')
    if np.any(cur.astype(np.float64)[changed] < np.minimum(src.astype(np.float64)[changed], 1.8) - 1e-7):
        raise AssertionError('soil floor violated')
    OUT.mkdir()
    arrays = {k: terrain[k] for k in terrain.files}
    arrays['heights'] = cur.astype(np.float32, copy=False)
    np.savez_compressed(OUT / 'terrain.npz', **arrays)
    for name in ('plane.npy', 'visible-field.npy'):
        import shutil
        shutil.copyfile(SOURCE / name, OUT / name)
    # Sparse edits are deterministic and tied directly to the full candidate.
    records = np.asarray(rows, dtype=np.float64).reshape((-1, 4))
    np.savez_compressed(B / 'terrain-delta.npz', row=records[:, 0].astype(np.int32),
                        col=records[:, 1].astype(np.int32), before=records[:, 2].astype(np.float32),
                        after=records[:, 3].astype(np.float32))
    report = dict(status='CANDIDATE_AUTHORED_PENDING_INDEPENDENT_CONSUMER',
                  source_sha256=sha(TERRAIN), candidate_sha256=sha(OUT/'terrain.npz'),
                  constraints_sha256=sha(CONSTRAINTS), plane_sha256=sha(OUT/'plane.npy'),
                  visible_field_sha256=sha(OUT/'visible-field.npy'),
                  p99_source_report_sha256=sha(BASELINE_REPORT), p99_bank_source_ev79=p99_bank,
                  p99_interior_source_ev79=p99_interior,
                  selector=dict(classes=[0], nearby_flow_classes=[3,5,6], distance_m=96.0,
                                fixed_sha256=hashlib.sha256(fixed.tobytes()).hexdigest(),
                                domain_vertices=int(domain.sum()), source_fold_vertex_mask=int(fold_nodes.sum()),
                                selector_vertices=int(selector.sum()), source_fold_nodes=selected),
                  counts=dict(changed_vertices=int(changed.sum()), accepted_nodes=accepted,
                              rejected_by_reason=reasons, wet_support_vertices=int(wet_support.sum()),
                              fixed_vertices=int(fixed.sum())),
                  delta=dict(min_m=float(delta.min()), max_m=float(delta.max()),
                             max_abs_m=float(np.abs(delta).max()), lowered=int((delta<0).sum()),
                             raised=int((delta>0).sum())),
                  method=dict(order='native row then column', once_per_node=True, local_patch='5x5',
                              local_faces=6, local_hinges=12, objective='sum of 12 hinge angles squared',
                              max_seconds=MAX_SECONDS, elapsed_seconds=round(elapsed, 3),
                              neighbor_state='current deterministic EV80 state',
                              hard_thresholds_compared_to='original EV79 source'),
                  fixtures=test, terrain_delta_sha256=sha(B/'terrain-delta.npz'))
    (B / 'authoring.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
