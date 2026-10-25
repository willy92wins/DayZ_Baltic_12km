from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
from collections import deque
import numpy as np

ROOT = Path(r'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010')
RUN = ROOT / 'global-operator-prototype' / 'admm-adaptive-pilot' / 'run-01'
NPZ = RUN / 'full7440.npz'
POSTHOC = RUN / 'posthoc-array-review-v2.json'
ADAPTIVE = ROOT / 'global-operator-prototype' / 'admm-adaptive-pilot' / 'solve.py'
PRIOR = ROOT / 'constrained-pilot' / 'd8_sparse_pilot.py'
OUT = ROOT / 'global-operator-prototype' / 'float32-closure-study' / 'result-03'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def closure(initial, mutable, lower, upper, edges):
    """Raise float32 centers along witness->center edges, at most one ULP/node."""
    initial = np.asarray(initial, dtype=np.float32)
    if initial.ndim != 1:
        raise ValueError('closure expects a flat float32 height vector')
    current = initial.copy()
    mutable = np.asarray(mutable, dtype=bool)
    lower = np.asarray(lower, dtype=np.float32)
    upper = np.asarray(upper, dtype=np.float32)
    if any(a.shape != initial.shape for a in (mutable, lower, upper)):
        raise ValueError('shape mismatch')
    edges = [(int(w), int(c)) for w, c in edges]
    if any(w < 0 or c < 0 or w >= len(initial) or c >= len(initial) for w, c in edges):
        raise ValueError('edge index out of range')
    one_ulp = np.nextafter(initial, np.float32(np.inf), dtype=np.float32)
    by_witness = [[] for _ in initial]
    for eid, (w, c) in enumerate(edges):
        by_witness[w].append(eid)
    queue = deque(range(len(edges)))
    queued = set(range(len(edges)))
    changed = np.zeros(len(initial), dtype=bool)
    steps = 0
    while queue:
        eid = queue.popleft(); queued.discard(eid)
        w, c = edges[eid]
        if current[c] >= current[w]:
            continue
        if not mutable[c]:
            return current, {'ok': False, 'reason': 'fixed_center', 'edge': eid,
                             'witness': w, 'center': c, 'steps': steps, 'changed': int(changed.sum())}
        required = current[w]
        if required > upper[c]:
            return current, {'ok': False, 'reason': 'upper_bound', 'edge': eid,
                             'witness': w, 'center': c, 'required': float(required),
                             'upper': float(upper[c]), 'steps': steps, 'changed': int(changed.sum())}
        if required > one_ulp[c]:
            return current, {'ok': False, 'reason': 'more_than_one_ulp', 'edge': eid,
                             'witness': w, 'center': c, 'required': float(required),
                             'initial': float(initial[c]), 'one_ulp_limit': float(one_ulp[c]),
                             'steps': steps, 'changed': int(changed.sum())}
        if required < lower[c]:
            return current, {'ok': False, 'reason': 'lower_bound_invariant', 'edge': eid,
                             'witness': w, 'center': c, 'required': float(required),
                             'lower': float(lower[c]), 'steps': steps, 'changed': int(changed.sum())}
        current[c] = required
        changed[c] = True
        steps += 1
        for next_eid in by_witness[c]:
            if next_eid not in queued:
                queue.append(next_eid); queued.add(next_eid)
    bad_bounds = int(np.count_nonzero((current < lower) | (current > upper)))
    bad_edges = [(w, c) for w, c in edges if current[c] < current[w]]
    if bad_bounds or bad_edges:
        return current, {'ok': False, 'reason': 'postcondition', 'bad_bounds': bad_bounds,
                         'bad_edges': len(bad_edges), 'steps': steps, 'changed': int(changed.sum())}
    if np.any(current[~mutable] != initial[~mutable]):
        return current, {'ok': False, 'reason': 'fixed_changed', 'steps': steps,
                         'changed': int(changed.sum())}
    if np.any(current > one_ulp):
        return current, {'ok': False, 'reason': 'ulp_postcondition', 'steps': steps,
                         'changed': int(changed.sum())}
    return current, {'ok': True, 'reason': 'closed', 'steps': steps,
                     'changed': int(changed.sum()), 'bad_bounds': bad_bounds,
                     'bad_edges': 0}


def objective_from_records(records, x):
    total = 0.0
    for entries, target, _key in records:
        residual = sum(float(coef) * float(x[int(i)]) for i, coef in entries) - float(target)
        total += 0.5 * residual * residual
    return total

def synthetic_fixtures():
    def run(h, mut, lo, hi, edges):
        return closure(np.array(h, np.float32), np.array(mut), np.array(lo, np.float32),
                       np.array(hi, np.float32), edges)
    # Chain: one-ULP raise propagates from witness through two dependent centers.
    base = np.array([1.0, 1.0, 1.0], np.float32)
    h = base.copy(); h[0] = np.nextafter(h[0], np.float32(np.inf))
    result, meta = run(h, [False, True, True], [0, 0, 0], [2, 2, 2], [(0, 1), (1, 2)])
    assert meta['ok'] and result.tolist() == [h[0], h[0], h[0]]
    # Compatible cycle closes to a shared level without exceeding each one-ULP ceiling.
    h = np.array([1.0, 1.0], np.float32); h[0] = np.nextafter(h[0], np.float32(np.inf))
    result, meta = run(h, [True, True], [0, 0], [2, 2], [(0, 1), (1, 0)])
    assert meta['ok'] and np.array_equal(result, np.array([h[0], h[0]], np.float32))
    # Fixed center and upper-bound center must fail closed.
    _, fixed = run(h, [True, False], [0, 0], [2, 2], [(0, 1)])
    assert not fixed['ok'] and fixed['reason'] == 'fixed_center'
    _, upper = run(h, [True, True], [0, 0], [2, 1], [(0, 1)])
    assert not upper['ok'] and upper['reason'] == 'upper_bound'
    # More than one ULP is not rounded up or tolerated.
    h = np.array([1.0, 1.0], np.float32); h[0] = np.nextafter(np.nextafter(h[0], np.float32(np.inf)), np.float32(np.inf))
    _, over = run(h, [True, True], [0, 0], [2, 2], [(0, 1)])
    assert not over['ok'] and over['reason'] == 'more_than_one_ulp'
    return {'chain': 'PASS', 'compatible_cycle': 'PASS', 'fixed_block': 'PASS',
            'upper_bound_block': 'PASS', 'over_one_ulp_block': 'PASS'}


def main():
    if OUT.exists():
        raise SystemExit('output already exists; refusing to overwrite')
    fixtures = synthetic_fixtures()
    spec = importlib.util.spec_from_file_location('adaptive_solve_frozen', ADAPTIVE)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    npz_sha = sha(NPZ); prior_hashes = {str(p): sha(p) for p in (NPZ, POSTHOC, ADAPTIVE, PRIOR)}
    with np.load(NPZ) as z:
        base = z['baseline'].copy(); original = z['candidate'].copy()
        nodes = z['nodes_rc'].copy(); lo = z['lower'].copy().astype(np.float32); hi = z['upper'].copy().astype(np.float32)
        centers = z['witness_centers'].copy(); witnesses = z['witness_neighbors'].copy()
        x64 = z['x_float64'].copy()
    mutable_grid = np.zeros(base.shape, bool); mutable_grid[tuple(nodes.T)] = True
    flat_index = np.arange(base.size, dtype=np.int64).reshape(base.shape)
    edge_flat = [(int(flat_index[tuple(w)]), int(flat_index[tuple(c)])) for c, w in zip(centers, witnesses)]
    initial_flat = original.ravel().copy(); mutable_flat = mutable_grid.ravel()
    lower_grid = base.copy(); upper_grid = base.copy()
    lower_grid[tuple(nodes.T)] = lo; upper_grid[tuple(nodes.T)] = hi
    repaired_flat, closure_status = closure(initial_flat, mutable_flat, lower_grid.ravel(), upper_grid.ravel(), edge_flat)
    repaired = repaired_flat.reshape(base.shape)
    # Independently rebuild the objective from the pinned source; no solver call.
    p = mod.load_prior()
    rebuilt = mod.problem(p, 'full7440')
    b2, n2, A, rhs, C, d, witnesses2, *_ = rebuilt
    if not np.array_equal(b2, base) or not np.array_equal(n2, nodes):
        raise AssertionError('NPZ does not match independently rebuilt problem')
    x_initial = original[tuple(nodes.T)].astype(np.float64)
    x_repaired = repaired[tuple(nodes.T)].astype(np.float64)
    objective_before = mod.objective(A, rhs, x_initial)
    objective_after = mod.objective(A, rhs, x_repaired)
    objective_before_records = objective_from_records(rebuilt[-1], x_initial)
    objective_after_records = objective_from_records(rebuilt[-1], x_repaired)
    objective_independent_error = max(abs(objective_before-objective_before_records), abs(objective_after-objective_after_records))
    bad_d8_before = [([int(v) for v in w], [int(v) for v in c]) for c, w in zip(centers, witnesses) if original[tuple(c)] < original[tuple(w)]]
    bad_d8_after = [([int(v) for v in w], [int(v) for v in c]) for c, w in zip(centers, witnesses) if repaired[tuple(c)] < repaired[tuple(w)]]
    bad_bounds = int(np.count_nonzero((x_repaired < lo) | (x_repaired > hi)))
    fixed = ~mutable_grid
    baseline_minima = p.strict_minima(base)
    new_minima = sorted(p.strict_minima(repaired) - baseline_minima)
    ulp_ceiling = np.nextafter(original, np.float32(np.inf), dtype=np.float32)
    over_ulp = int(np.count_nonzero(repaired[mutable_grid] > ulp_ceiling[mutable_grid]))
    changed = np.argwhere(repaired != original)
    # Hash/source TOCTOU check after computation.
    final_hashes = {str(pth): sha(pth) for pth in (NPZ, POSTHOC, ADAPTIVE, PRIOR)}
    report = {
      'status': 'CLOSURE_STUDY_ONLY_NOT_SOLVER_PASS' if closure_status['ok'] else 'CLOSURE_INFEASIBLE_UNDER_ONE_ULP_CONTRACT',
      'scope': 'post-processing study on already-written synthetic full7440 arrays only; no solver run and no terrain/map candidate',
      'source_hashes_start': prior_hashes, 'source_hashes_end': final_hashes,
      'sources_unchanged': prior_hashes == final_hashes, 'input_npz_sha256': npz_sha,
      'synthetic_fixtures': fixtures, 'closure': closure_status,
      'input': {'variables': int(len(nodes)), 'd8_edges': int(len(edge_flat)), 'float32_d8_violations': len(bad_d8_before), 'violation_edges': bad_d8_before[:8]},
      'output': {'changed_vertices': int(len(changed)), 'changed_rc_first20': [[int(v) for v in row] for row in changed[:20].tolist()],
                 'float32_d8_violations': len(bad_d8_after), 'bad_bounds': bad_bounds,
                 'fixed_exact_B': bool(np.array_equal(repaired[fixed], base[fixed])),
                 'new_strict_minima': len(new_minima), 'new_minima_rc_first20': [[int(v) for v in rc] for rc in new_minima[:20]],
                 'more_than_one_ulp_vertices': over_ulp,
                 'objective_before_from_independent_A': objective_before,
                 'objective_after_from_independent_A': objective_after,
                 'objective_before_direct_records': objective_before_records,
                 'objective_after_direct_records': objective_after_records,
                 'independent_objective_max_difference': objective_independent_error,
                 'objective_change': objective_after-objective_before,
                 'objective_still_below_baseline': bool(objective_after < mod.objective(A, rhs, base[tuple(nodes.T)].astype(np.float64))),
                 'max_raise_m': float(np.max((repaired-original).astype(np.float64), initial=0.)),
                 'raised_nodes': int(np.count_nonzero(repaired > original)),
                 'one_ulp_changes': int(np.count_nonzero(repaired[mutable_grid] == ulp_ceiling[mutable_grid])),
                 'raised_values_exactly_match_witness': bool(all(repaired[tuple(c)] == repaired[tuple(w)] for c,w in zip(centers,witnesses) if repaired[tuple(c)] > original[tuple(c)]))},
      'solver_status': 'NOT_INFERRED; previous attempt remains ERROR_REPORT_SERIALIZATION_POSTHOC_ONLY_NO_PASS',
      'interpretation': 'Even a successful closure only repairs the final float32 D8 inequalities in this saved synthetic array. It does not establish solver convergence, does not replace or pass the original 7440-variable run, and is not a map candidate.'}
    if not report['sources_unchanged']:
        report['status'] = 'SOURCE_CHANGED_DURING_STUDY'
    OUT.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(OUT/'closure-result.npz', baseline=base, input_candidate=original,
                        repaired_candidate=repaired, changed_rc=changed.astype(np.int32))
    (OUT/'closure-study.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'closure': closure_status,
                      'input_violations': len(bad_d8_before), 'output_violations': len(bad_d8_after),
                      'changed': len(changed), 'objective_delta': objective_after-objective_before, 'objective_independent_error': objective_independent_error}, indent=2))

if __name__ == '__main__':
    main()




