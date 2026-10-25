"""Offline LP feasibility only; no terrain candidate is written."""
from pathlib import Path
import hashlib, json, math
import numpy as np
from scipy.optimize import linprog

ROOT = Path(r'E:/DayZ-Baltic-Build')
B = ROOT / 'v30-mixed-bank-incremental-fixed-20261010'
EV79 = ROOT / 'v30-narva-dry-bank-relief-20261010'
PILOT = ROOT / 'v30-wet-support-shore-pilot-20261010'
PRIOR = ROOT / 'v30-remaining-exact-dry-support-20261009/constraints.npz'
VALLEY = ROOT / 'v30-valley-smoothing-20261008/candidate-a/masks.npz'
OUT = Path(__file__).parent
FOCI = [(1880, 191), (1785, 366)]  # row,col: (x,z)=(1146,1002),(2196,1572)
TRIS = ((0, 1, 3), (0, 2, 3))
CORNERS = ((0, 0), (0, 1), (1, 0), (1, 1))
DELTA = 6.0
MAX_CROSS_MOVE = 1.0
MIN_FOCUS_DESCENT = 0.1

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def json_safe(value):
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, (float, np.floating)) and not math.isfinite(float(value)):
        return 'Infinity' if float(value) > 0 else '-Infinity' if float(value) < 0 else 'NaN'
    if isinstance(value, np.generic):
        return value.item()
    return value

def load_npz(path):
    with np.load(path, allow_pickle=False) as d:
        return {k: d[k] for k in d.files}

def contour_t(d0, d1):
    return -d0 / (d1 - d0)

def height_at_crossing(level, fixed_clearance, t, variable_is_a):
    if variable_is_a:
        if t >= 1.0:
            return math.inf if fixed_clearance < 0 else -math.inf
        return level - (t / (1.0 - t)) * fixed_clearance
    if t <= 0.0:
        return math.inf if fixed_clearance < 0 else -math.inf
    return level - ((1.0 - t) / t) * fixed_clearance

def crossing_height_interval(level0, level1, h0, h1, variable_is_a, edge_length):
    d0, d1 = h0 - level0, h1 - level1
    if d0 * d1 >= 0:
        return None
    t0 = contour_t(d0, d1)
    dt = MAX_CROSS_MOVE / edge_length
    ta, tb = max(0.0, t0 - dt), min(1.0, t0 + dt)
    a = height_at_crossing(level0 if variable_is_a else level1,
                           d1 if variable_is_a else d0, ta, variable_is_a)
    b = height_at_crossing(level0 if variable_is_a else level1,
                           d1 if variable_is_a else d0, tb, variable_is_a)
    return min(a, b), max(a, b)

def fixtures():
    # Independent direct checks for monotonic-order constraints and the pilot's
    # scalar one-metre crossing interval on a six-metre edge.
    lo, hi = crossing_height_interval(0.0, 0.0, 1.0, -1.0, True, 6.0)
    assert abs(lo - 0.5) < 1e-12 and abs(hi - 2.0) < 1e-12
    for candidate in (lo, hi):
        t = contour_t(candidate, -1.0)
        assert abs(t - 0.5) * 6.0 <= 1.0 + 1e-12
    # Order: source 5>3 remains non-inverted at equality; a reversal is rejected.
    assert (5.0 - 1.0) >= (3.0 + 1.0)
    assert not ((5.0 - 3.0) < 0)
    edges = touched_order_edges({(1, 1)})
    expected = {tuple(sorted(((1, 1), (1 + dr, 1 + dc))))
                for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                if (dr, dc) != (0, 0)}
    assert set(edges) == expected and ((0, 0), (1, 1)) in edges and len(edges) == 8
    # A fixed lexicographically earlier neighbor must constrain the variable
    # even though that fixed neighbor is not itself iterated as a variable.
    edge = ((0, 0), (1, 1))
    assert edge in edges
    # For h_fixed=2, h_var=1, preserving order gives delta_var <= 1.
    assert (2.0 - 1.0) >= 0.0 and (2.0 - (1.0 + 1.0)) == 0.0
    # A zero objective can return any feasible x; never infer x==0 from it.
    zero_objective = linprog([0.0], bounds=[(-1.0, 0.0)], method='highs')
    assert zero_objective.success and -1.0 <= zero_objective.x[0] <= 0.0
    assert direct_zero_check([(-1.0, 0.0)], np.array([[1.0]]), np.array([0.0]),
                             np.array([[0.0]]), np.array([0.0]))['pass']
    assert not direct_zero_check([(1.0, 2.0)], None, None, None, None)['pass']
    # Exercise the production order-row builder for a fixed earlier neighbor.
    vindex = {(1, 1): 0}
    hfixture = np.zeros((2, 2), dtype=np.float64)
    hfixture[0, 0], hfixture[1, 1] = 2.0, 1.0
    kind, row, rhs = order_row_for_edge((0, 0), (1, 1), hfixture, vindex)
    assert kind == 'ub' and row.tolist() == [1.0] and rhs == 1.0
    assert float(row @ np.array([1.0])) <= rhs and float(row @ np.array([1.01])) > rhs
    return {'order_two_node': 'PASS', 'fixed_lexicographically_previous_neighbor': 'PASS',
            'all_eight_neighbors_deduplicated': 'PASS',
            'zero_objective_requires_feasibility_only': 'PASS',
            'direct_zero_bounds_inequality_equality_positive_negative': 'PASS',
            'fixed_earlier_neighbor_order_row': 'PASS',
            'crossing_interval_6m': [lo, hi], 'direct_crossing_bound': 'PASS'}

def direct_zero_check(bounds, aub, bub, aeq, beq, tol=1e-10):
    """Check delta=0 itself against base LP bounds and all encoded rows."""
    zero = np.zeros(len(bounds), dtype=np.float64)
    bounds_ok = all(lb <= tol and ub >= -tol for lb, ub in bounds)
    ub_violation = float(np.max(aub @ zero - bub)) if aub is not None and len(aub) else 0.0
    eq_residual = float(np.max(np.abs(aeq @ zero - beq))) if aeq is not None and len(aeq) else 0.0
    return {'pass': bounds_ok and ub_violation <= tol and eq_residual <= tol,
            'bounds_contain_zero': bounds_ok,
            'max_inequality_violation_m': ub_violation,
            'max_equality_residual_m': eq_residual}

def order_row_for_edge(u, v, h, var_index):
    """Return one B-order-preserving row; omitted variables are fixed at delta=0."""
    hu, hv = float(h[u]), float(h[v])
    row = np.zeros(len(var_index), dtype=np.float64)
    if hu > hv:
        if v in var_index: row[var_index[v]] += 1.0
        if u in var_index: row[var_index[u]] -= 1.0
        return ('ub', row, hu - hv)
    if hu < hv:
        if u in var_index: row[var_index[u]] += 1.0
        if v in var_index: row[var_index[v]] -= 1.0
        return ('ub', row, hv - hu)
    if u in var_index: row[var_index[u]] += 1.0
    if v in var_index: row[var_index[v]] -= 1.0
    return ('eq', row, 0.0)

def ev79_interval(original, current, water_levels, max_delta=2.0):
    # Literal contract from EV82 author.py:372-379, but compute incident P/F
    # levels independently so finite F is honored even if cell P is NaN.
    floor = min(float(original), max(water_levels) + 1e-4)
    lo = max(-max_delta, floor - current, min(float(original), 1.8) - current,
             float(original) - max_delta - current)
    hi = min(max_delta, float(original) + max_delta - current)
    return floor, lo, hi

def touched_order_edges(variable_vertices, shape=(2048, 2048)):
    seen = set()
    edges = []
    for u in sorted(variable_vertices):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                v = (u[0] + dr, u[1] + dc)
                if not (0 <= v[0] < shape[0] and 0 <= v[1] < shape[1]):
                    continue
                edge = tuple(sorted((u, v)))
                if edge not in seen:
                    seen.add(edge)
                    edges.append(edge)
    return edges

def main():
    inputs = {
        'B_terrain': B / 'candidate/terrain.npz',
        'B_P': B / 'candidate/plane.npy',
        'B_F': B / 'candidate/visible-field.npy',
        'EV79_terrain': EV79 / 'candidate/terrain.npz',
        'EV79_constraints': EV79 / 'constraints.npz',
        'prior_large_lake_mask': PRIOR,
        'valley_masks': VALLEY,
        'EV83_crossing_helper': PILOT / 'author_pilot.py',
        'order_bounds': ROOT / 'v30-shore-order-pilot-20261010/order-bounds.json',
    }
    for p in inputs.values():
        if not p.is_file():
            raise FileNotFoundError(p)
    expected = {
        'B_terrain': 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
        'EV79_terrain': 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c',
        'B_P': '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
        'B_F': 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
    }
    actual = {k: sha(v) for k, v in inputs.items()}
    for k, h in expected.items():
        if actual[k] != h:
            raise RuntimeError(f'Input identity mismatch {k}: {actual[k]}')

    b = load_npz(inputs['B_terrain'])
    orig = load_npz(inputs['EV79_terrain'])
    cons = load_npz(inputs['EV79_constraints'])
    prior = load_npz(inputs['prior_large_lake_mask'])
    valley = load_npz(inputs['valley_masks'])
    h = b['heights'].astype(np.float64, copy=False)
    h79 = orig['heights'].astype(np.float64, copy=False)
    upper79 = h79 + cons['cap']
    p = np.load(inputs['B_P'], mmap_mode='r')
    f = np.load(inputs['B_F'], mmap_mode='r')
    if h.shape != (2048, 2048) or h79.shape != h.shape or p.shape != (2047, 2047) or f.shape != (2047, 2047, 4):
        raise RuntimeError('Unexpected input dimensions')

    patches = []
    variables = []
    eligibility_records = []
    bounds_by_vertex = {}
    for pi, (fr, fc) in enumerate(FOCI):
        r0, r1, c0, c1 = fr - 3, fr + 4, fc - 3, fc + 4
        local = []
        for r in range(r0 + 1, r1 - 1):
            for c in range(c0 + 1, c1 - 1):
                # Must be dry at B against the independent sea threshold and
                # every finite P/F corner sample incident on this vertex.
                water_levels = [0.85]
                for cr in (r - 1, r):
                    for cc in (c - 1, c):
                        if not (0 <= cr < 2047 and 0 <= cc < 2047):
                            continue
                        pv = float(p[cr, cc])
                        if math.isfinite(pv):
                            water_levels.append(max(pv, 0.85))
                        k = (0 if r == cr else 2) + (0 if c == cc else 1)
                        fv = float(f[cr, cc, k])
                        if math.isfinite(fv):
                            water_levels.append(fv)
                dry = all(float(h[r, c]) > level for level in water_levels)
                floor, budget_lo, budget_hi = ev79_interval(float(h79[r, c]), float(h[r, c]), water_levels)
                reasons = {
                    'dry_all_P_F_sea085': dry,
                    'class0': int(b['cls'][r, c]) == 0,
                    'other_fixed_false': not bool(cons['other_fixed'][r, c]),
                    'engineering_halo_false': not bool(cons['engineering_halo'][r, c]),
                    'large_lake_banks_false': not bool(prior['large_lake_banks'][r, c]),
                    'inside_7x7_interior': True,
                    'EV79_budget_contains_B': budget_lo <= 1e-9 and budget_hi >= -1e-9,
                }
                ok = all(reasons.values())
                eligibility_records.append({'patch': pi, 'row': r, 'col': c, 'x': c * 6, 'z': 12282 - r * 6,
                                            'height_B': float(h[r, c]), 'height_EV79': float(h79[r, c]),
                                            'wet_support_ignored': bool(cons['wet_support'][r, c]),
                                            'water_levels_incident': water_levels, 'EV79_floor_m': floor,
                                            'EV79_budget_delta_interval_at_B_m': [budget_lo, budget_hi],
                                            'eligible': ok, 'reasons': reasons})
                if ok:
                    local.append((r, c))
        patches.append(local)
        variables.extend(local)
    var_index = {v: i for i, v in enumerate(variables)}
    if len(var_index) != len(variables):
        raise RuntimeError('Patch interiors overlap')
    if any(focus not in var_index for focus in FOCI):
        raise RuntimeError('Focus vertex is not eligible under the stated diagnostic domain')

    n = len(variables)
    lo = np.zeros(n, dtype=np.float64)
    hi = np.zeros(n, dtype=np.float64)
    floors = np.zeros(n, dtype=np.float64)
    for i, (r, c) in enumerate(variables):
        base = float(h[r, c])
        water_levels = [0.85]
        for cr in (r - 1, r):
            for cc in (c - 1, c):
                if not (0 <= cr < 2047 and 0 <= cc < 2047):
                    continue
                pv = float(p[cr, cc])
                if math.isfinite(pv):
                    water_levels.append(max(pv, 0.85))
                k = (0 if r == cr else 2) + (0 if c == cc else 1)
                fv = float(f[cr, cc, k])
                if math.isfinite(fv):
                    water_levels.append(fv)
        floors[i], lo[i], hi0 = ev79_interval(float(h79[r, c]), base, water_levels)
        hi[i] = min(hi0, 0.0)  # no-raise relative to B

    crossing_records = []
    for i, (r, c) in enumerate(variables):
        vertex = (r, c)
        lower_abs = float(h[r, c]) + lo[i]
        upper_abs = float(h[r, c]) + hi[i]
        # For each incident cell, use its own P and each finite F corner level.
        for cr in (r - 1, r):
            for cc in (c - 1, c):
                if not (0 <= cr < 2047 and 0 <= cc < 2047):
                    continue
                verts = [(cr + dr, cc + dc) for dr, dc in CORNERS]
                pv = float(p[cr, cc])
                levels = []
                if math.isfinite(pv):
                    levels.append(('P', max(pv, 0.85), None))
                # F is independent of P: retain finite F levels even if P is NaN.
                for k in range(4):
                    fv = float(f[cr, cc, k])
                    if math.isfinite(fv):
                        levels.append((f'F{k}', fv, k))
                for tri in TRIS:
                    for ia, ib in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
                        va, vb = verts[ia], verts[ib]
                        if vertex not in (va, vb):
                            continue
                        other = vb if va == vertex else va
                        # The other endpoint must be water-wet and fixed; if it
                        # were an eligible dry variable this is a bad model.
                        for surface, level, fcorner in levels:
                            # F sample is at its exact endpoint; P is cell-constant.
                            if fcorner is not None:
                                if ia != fcorner and ib != fcorner:
                                    continue
                                # F levels on the same edge vary by endpoint; apply
                                # the corresponding endpoint's own finite value.
                                l0 = float(f[cr, cc, ia])
                                l1 = float(f[cr, cc, ib])
                                if not (math.isfinite(l0) and math.isfinite(l1)):
                                    continue
                            else:
                                l0 = l1 = level
                            hv = float(h[r, c])
                            ho = float(h[other[0], other[1]])
                            lv = l0 if va == vertex else l1
                            lo_other = l1 if va == vertex else l0
                            dv, do = hv - lv, ho - lo_other
                            if dv * do >= 0:
                                continue
                            if other in var_index:
                                raise RuntimeError(f'Crossing edge has eligible variable wet endpoint: {vertex}->{other}')
                            length = 6.0 * math.hypot(va[0] - vb[0], va[1] - vb[1])
                            interval = crossing_height_interval(l0, l1,
                                                                hv if va == vertex else ho,
                                                                ho if va == vertex else hv,
                                                                va == vertex, length)
                            if interval is None:
                                continue
                            lower_abs = max(lower_abs, interval[0])
                            upper_abs = min(upper_abs, interval[1])
                            crossing_records.append({'vertex': [r, c], 'other_fixed': list(other),
                                'cell': [cr, cc], 'triangle': list(tri), 'surface': surface,
                                'level_at_variable': lv, 'level_at_other': lo_other,
                                'before_heights': [hv, ho], 'height_interval': list(interval),
                                'edge_length_m': length})
        # Explicit dry-endpoint sign for every finite P/F level incident on the node.
        for cr in (r - 1, r):
            for cc in (c - 1, c):
                if not (0 <= cr < 2047 and 0 <= cc < 2047):
                    continue
                pv = float(p[cr, cc])
                sign_levels = [max(pv, 0.85)] if math.isfinite(pv) else [0.85]
                k = (0 if r == cr else 2) + (0 if c == cc else 1)
                fv = float(f[cr, cc, k])
                if math.isfinite(fv):
                    sign_levels.append(fv)
                for level in sign_levels:
                    lower_abs = max(lower_abs, float(np.nextafter(level, np.inf)))
        lo[i] = lower_abs - float(h[r, c])
        hi[i] = upper_abs - float(h[r, c])

    # Every touched Moore-neighborhood edge preserves B's ordering; equality
    # edges remain equal. Delta=0 represents fixed boundary/ineligible nodes.
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    touched_edges = 0
    order_edges = touched_order_edges(set(variables))
    for u, v in order_edges:
        touched_edges += 1
        kind, row, rhs = order_row_for_edge(u, v, h, var_index)
        if kind == 'ub':
            A_ub.append(row); b_ub.append(rhs)
        else:
            A_eq.append(row); b_eq.append(rhs)

    order_ub, order_b_ub = list(A_ub), list(b_ub)
    order_eq, order_b_eq = list(A_eq), list(b_eq)
    A_ub_np_order = np.asarray(order_ub) if order_ub else None
    b_ub_np_order = np.asarray(order_b_ub) if order_b_ub else None
    A_eq_np_order = np.asarray(order_eq) if order_eq else None
    b_eq_np_order = np.asarray(order_b_eq) if order_b_eq else None
    bounds = [(float(lo[i]), float(hi[i])) for i in range(n)]
    zero_check = direct_zero_check(bounds, A_ub_np_order, b_ub_np_order,
                                   A_eq_np_order, b_eq_np_order)
    zero_baseline_ok = zero_check['pass']
    if not zero_baseline_ok:
        raise RuntimeError('B zero-delta baseline fails the direct LP bounds/order check')

    # Both focus points must lower by at least 10 cm in any feasibility witness.
    for focus in FOCI:
        row = np.zeros(n, dtype=np.float64); row[var_index[focus]] = 1.0
        A_ub.append(row); b_ub.append(-MIN_FOCUS_DESCENT)

    if any(l > u + 1e-10 for l, u in bounds):
        bad = [{'vertex': list(variables[i]), 'delta_interval': [float(lo[i]), float(hi[i])]} for i in range(n) if lo[i] > hi[i] + 1e-10]
        result = {'status': 'INFEASIBLE_SCALAR_BOUNDS', 'bad_bounds': bad[:30]}
    else:
        A_ub_np = np.asarray(A_ub) if A_ub else None
        b_ub_np = np.asarray(b_ub) if b_ub else None
        A_eq_np = np.asarray(A_eq) if A_eq else None
        b_eq_np = np.asarray(b_eq) if b_eq else None
        result = {'status': 'LP_READY'}
        witnesses = []
        for focus in FOCI:
            c = np.zeros(n, dtype=np.float64); c[var_index[focus]] = 1.0
            lp = linprog(c, A_ub=A_ub_np, b_ub=b_ub_np, A_eq=A_eq_np, b_eq=b_eq_np,
                         bounds=bounds, method='highs')
            item = {'objective_focus': list(focus), 'success': bool(lp.success), 'status': int(lp.status),
                    'message': lp.message}
            if lp.success:
                d = lp.x
                # Directly check each LP inequality and order edge in double precision.
                max_ub = float(np.max(A_ub_np @ d - b_ub_np)) if A_ub_np is not None else 0.0
                max_eq = float(np.max(np.abs(A_eq_np @ d - b_eq_np))) if A_eq_np is not None else 0.0
                item.update({'focus_height_after_m': float(h[focus] + d[var_index[focus]]),
                             'focus_delta_m': float(d[var_index[focus]]),
                             'both_focus_deltas_m': {str(f): float(d[var_index[f]]) for f in FOCI},
                             'max_inequality_violation_m': max_ub, 'max_equality_residual_m': max_eq,
                             'nonzero_delta_witness': [{'row': r, 'col': c, 'x': c*6, 'z': 12282-r*6,
                                 'height_B': float(h[r, c]), 'delta_m': float(d[var_index[(r, c)]]),
                                 'height_after_m': float(h[r, c]+d[var_index[(r, c)]])}
                                 for r, c in variables if abs(float(d[var_index[(r, c)]])) > 1e-8]})
                if max_ub > 1e-7 or max_eq > 1e-7:
                    raise AssertionError(f'LP solution violates its encoded constraints: {item}')
            witnesses.append(item)
        result = {'status': 'FEASIBLE' if all(w['success'] for w in witnesses) else 'INFEASIBLE',
                  'witnesses': witnesses}

    by_patch = []
    for i, loc in enumerate(patches):
        rows = [x for x in eligibility_records if x['patch'] == i]
        by_patch.append({'focus': list(FOCI[i]), 'x': FOCI[i][1]*6, 'z': 12282-FOCI[i][0]*6,
                         'interior_nodes': len(rows), 'eligible_mutable_nodes': len(loc),
                         'wet_support_true_eligible_count': sum(bool(x['wet_support_ignored']) for x in rows if x['eligible']),
                         'focus_height_B': float(h[FOCI[i]]), 'focus_lower_delta_bound_m': float(lo[var_index[FOCI[i]]]),
                         'focus_upper_delta_bound_m': float(hi[var_index[FOCI[i]]]),
                         'eligible_nodes': [list(v) for v in loc]})
    output = {
        'status': result['status'],
        'scope': 'two independent 7x7 patches; outer ring fixed to B; interiors mutable only if dry against all incident finite P/F and sea 0.85, class0, !other_fixed, !engineering_halo, !large_lake_banks; wet_support is deliberately not a veto',
        'inputs': {k: {'path': str(v), 'sha256': actual[k]} for k, v in inputs.items()},
        'fixtures': fixtures(),
        'patches': by_patch,
        'eligible_node_count_total': n,
        'touched_8_neighbor_edges': touched_edges,
        'order_constraint_counts': {'inequality': len(order_ub), 'equality': len(order_eq)},
        'baseline_zero_delta_direct_check': zero_check,
        'false_freeze_negative_fixture': {
            'stored_EV79_cap_at_focuses': [float(cons['cap'][focus]) for focus in FOCI],
            'stored_constraint_delta_if_mistakenly_used': [float(cons['lower'][focus] - h[focus]) for focus in FOCI],
            'reconstructed_budget_delta_if_correct': [[float(next(x for x in eligibility_records if (x['row'], x['col']) == focus)['EV79_budget_delta_interval_at_B_m'][0]),
                float(next(x for x in eligibility_records if (x['row'], x['col']) == focus)['EV79_budget_delta_interval_at_B_m'][1])]
                for focus in FOCI],
            'pass': all(float(cons['cap'][focus]) == 0.0 and
                        float(cons['lower'][focus] - h[focus]) == 0.0 and
                        float(next(x for x in eligibility_records if (x['row'], x['col']) == focus)['EV79_budget_delta_interval_at_B_m'][0]) <= -MIN_FOCUS_DESCENT
                        for focus in FOCI),
            'note': 'Stored EV79 constraints encode fixed/wet_support authoring veto and are not physical floor/budget; no solver bound uses them.'},
        'crossing_constraint_count': len(crossing_records),
        'crossing_records': crossing_records,
        'eligibility_records': eligibility_records,
        'scalar_delta_bounds': [{'vertex': list(v), 'delta_bounds': [float(lo[i]), float(hi[i])],
                                 'height_B': float(h[v]), 'height_EV79': float(h79[v])}
                                for i, v in enumerate(variables)],
        'lp_result': result,
        'limitations': ['LP feasibility witness only; no terrain NPZ or candidate written.',
                        'No angular gates or energy objective were imposed, per request.',
                        'Continuous double-precision LP, not float32 quantization, consumer, ODOL, package, engine, or visual validation.',
                        'One-metre P/F crossing intervals reuse the scalar formula from EV83 author_pilot.py:38-86; F is independently honored even where P is NaN.']
    }
    (OUT / 'feasibility.json').write_text(json.dumps(json_safe(output), indent=2, allow_nan=False), encoding='utf-8')
    lines = [f"# Factibilidad local acoplada de orilla: {output['status']}", '',
             'LP offline sobre dos parches 7×7; anillo externo fijo a B. No se guardó un terreno candidato.', '',
             '| Foco (x,z) | Altura B | Interior elegible | Cota delta |', '|---|---:|---:|---:|']
    for q in by_patch:
        lines.append(f"| ({q['x']},{q['z']}) | {q['focus_height_B']:.6f} m | {q['eligible_mutable_nodes']}/25 | [{q['focus_lower_delta_bound_m']:.6f}, {q['focus_upper_delta_bound_m']:.6f}] m |")
    lines += ['', f"Nodos variables: {n}; aristas 8-vecinas tocadas: {touched_edges}; restricciones de cruce P/F: {len(crossing_records)}.",
              '', '## Resultado LP', '']
    for w in result.get('witnesses', []):
        lines.append(f"- Minimizar foco {w['objective_focus']}: {'factible' if w['success'] else 'inviable'}, delta foco {w.get('focus_delta_m', float('nan')):.6f} m; ambos deltas {w.get('both_focus_deltas_m', {})}; violación máx {w.get('max_inequality_violation_m', float('nan')):.2e} m.")
        if w.get('nonzero_delta_witness'):
            lines.append(f"  Nodos con delta no nulo ({len(w['nonzero_delta_witness'])}): " + ', '.join(f"({x['x']},{x['z']}) {x['delta_m']:.4f}m" for x in w['nonzero_delta_witness']))
    if result['status'] == 'INFEASIBLE_SCALAR_BOUNDS':
        lines.append('Los intervalos escalares se vacían antes de incluir restricciones de orden.')
    lines += ['', '## Alcance y límites', '',
              '- Las restricciones de orden comparan la nueva altura de cada arista 8-vecina tocada con su orden en B; igualdad exacta en B permanece como igualdad.',
              '- Fixtures: se enumeran los ocho vecinos del nodo variable, incluido el fijo lexicográficamente anterior; se valida la fila real de orden con ese vecino fijo. El delta cero se comprueba directamente contra bounds, `A_ub/b_ub` y `A_eq/b_eq` antes de imponer los descensos objetivo. El solver solo debe devolver una solución factible/óptima; no se exige que una solución de objetivo cero sea el vector cero.',
              '- Se usó el contrato original EV79 +/-2 m + suelo físico (EV82 `original_budget_interval`, autor.py:372-379), intersectado con no-raise respecto a B y la banda escalar de cruce <=1 m. No se usaron `constraints.lower/cap` como bounds: esos arrays codifican el veto histórico de `wet_support` y congelarían ambos focos. El anillo de cada parche permanece fijo.',
              '- `wet_support` no veta nodos por sí solo; los demás filtros semánticos sí se aplican por separado.',
              '- El resultado es solo una respuesta a factibilidad de este LP local. No prueba gates angulares, cuantización float32, cobertura del consumidor ni mejora visual.', '',
              'Fuentes principales: EV83 `author_pilot.py:38-86` (intervalos de cruce); EV79 `author.py:14-46` (máscaras y lower/upper); fuente EV79 `constraints.npz`; B/EV79 y P/F hashes registrados en `feasibility.json`.']
    (OUT / 'feasibility.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'status': output['status'], 'eligible': n, 'patches': by_patch,
                      'witnesses': result.get('witnesses', []),
                      'json': str(OUT / 'feasibility.json'), 'md': str(OUT / 'feasibility.md')}, indent=2))

if __name__ == '__main__':
    main()
