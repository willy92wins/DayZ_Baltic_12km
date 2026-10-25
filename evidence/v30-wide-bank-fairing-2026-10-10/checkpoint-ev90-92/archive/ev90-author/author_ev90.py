"""One EV90 local solve after approved preflight; preserve EV88 and all inputs."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
Q = HERE.parent
OLD = Q/'author/author_ev88q.py'
OLD_SHA = '532373b56c27ec0a04345c1c09a5cc6ff04fef34c04ac2856ce65ceb395162d1'
PRE = Q/'next-method-preflight/preflight.json'
PLAN = Q/'next-method-plan.md'
OUT = HERE/'candidate-terrain.npz'


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(4*1024*1024), b''): h.update(b)
    return h.hexdigest()


def import_author():
    if sha(OLD) != OLD_SHA: raise AssertionError('original author source identity changed')
    # Module import must be reproducible in the Windows spawn worker too.
    sys.path.insert(0, str(OLD.parent))
    import author_ev88q
    return author_ev88q


def inward_bounds(lower, upper):
    l, u = np.asarray(lower, dtype=np.float64), np.asarray(upper, dtype=np.float64)
    if l.shape != u.shape or not np.isfinite(l).all() or not np.isfinite(u).all():
        raise ValueError('finite matching bounds required')
    with np.errstate(over='ignore'):
        x, y = l.astype(np.float32), u.astype(np.float32)
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('bounds not representable as finite float32')
    x = np.where(x.astype(np.float64) < l, np.nextafter(x, np.float32(np.inf)), x)
    y = np.where(y.astype(np.float64) > u, np.nextafter(y, np.float32(-np.inf)), y)
    if np.any(x > y): raise ValueError('empty representable interval')
    return x.astype(np.float64), y.astype(np.float64)


def prepare():
    a = import_author()
    rec = json.loads(PRE.read_text(encoding='utf-8'))
    if rec['status'] != 'PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW':
        raise AssertionError('preflight not ready')
    pins = dict(rec['inputs_sha256'])
    pins.update({str(OLD): OLD_SHA, str(PRE): sha(PRE), str(PLAN): sha(PLAN), str(Path(__file__)): sha(__file__)})
    for p, wanted in pins.items():
        if sha(p) != wanted: raise AssertionError(f'preflight/source pin is stale: {p}')
    if rec['pins']['preflight_script_sha256'] != sha(Q/'next-method-preflight/ev90_preflight.py'):
        raise AssertionError('preflight source hash mismatch')
    if rec['pins']['next_method_plan_sha256'] != sha(PLAN): raise AssertionError('plan mismatch')
    d = rec['domain_and_bound_analysis']
    if not d['both_axes_box_feasible_for_25_percent']: raise AssertionError('no material focus freedom')
    if rec['unknown_field_lower_envelope_checks']['unresolved']:
        raise AssertionError('unknown water geometry not certified')
    local = a.local_inputs()
    nodes = np.asarray(d['eligible_after_face_freeze_nodes'], dtype=np.int32)
    intervals = d['final_float32_intervals_for_eligible_nodes']
    bound_by_node = {tuple(x['node_rc']): x for x in intervals}
    if len(bound_by_node) != len(nodes) or len(set(map(tuple, nodes))) != len(nodes):
        raise AssertionError('duplicate or missing interval/node')
    if not set(map(tuple, nodes)).issubset(set(map(tuple, local['variables']))):
        raise AssertionError('preflight would override semantic protection')
    limits = np.asarray([bound_by_node[tuple(x)]['interval_float32_inward_m'] for x in nodes], dtype=np.float64)
    lower, upper = inward_bounds(limits[:, 0], limits[:, 1])
    if not np.array_equal(lower, limits[:, 0]) or not np.array_equal(upper, limits[:, 1]):
        raise AssertionError('preflight did not freeze inward representable endpoints')
    if np.any(lower >= upper): raise AssertionError('BVLS domain contains fixed or empty intervals')
    local['variables'] = nodes
    matrix, rhs, stencils, weights = a.build_matrix(local)
    metadata = {'status': 'PREPARED_NO_SOLVE', 'source_pins': pins,
                'preflight_path': str(PRE), 'preflight_sha256': pins[str(PRE)],
                'plan_sha256': pins[str(PLAN)], 'author_source_sha256': pins[str(Path(__file__))],
                'variables_rc': nodes.tolist(), 'bounds_float32_inward': limits.tolist(),
                'stencils': [list(x) for x in stencils], 'matrix_shape': list(matrix.shape),
                'matrix_sha256_f64': hashlib.sha256(matrix.astype('<f8').tobytes()).hexdigest(),
                'rhs_sha256_f64': hashlib.sha256(rhs.astype('<f8').tobytes()).hexdigest(),
                'solver': {'method': 'scipy.optimize.lsq_linear/BVLS', 'tol': 1e-10,
                           'max_iter': 1000, 'hard_timeout_s': 120, 'calls': 0}}
    return a, local, matrix, rhs, lower, upper, metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--solve', action='store_true')
    parser.add_argument('--approved-preflight-sha', default='')
    args = parser.parse_args()
    a, local, matrix, rhs, lower, upper, rec = prepare()
    if not args.solve:
        (HERE/'prepared.json').write_text(json.dumps(rec, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({'status': rec['status'], 'variables': len(local['variables']), 'matrix_shape': matrix.shape}))
        return
    if args.approved_preflight_sha != rec['preflight_sha256']:
        raise AssertionError('explicit integrator approval must bind exact preflight')
    marker = HERE/'solve-started.json'
    if OUT.exists() or (HERE/'authoring.json').exists(): raise FileExistsError('candidate/receipt already exists')
    # Exclusive marker prevents repeated calls or a silent parameter sweep after failure.
    with marker.open('x', encoding='utf-8') as f: json.dump(rec, f, indent=2)
    began = time.monotonic()
    result = a.solve_once(matrix, rhs, lower, upper, timeout=120)
    elapsed = time.monotonic()-began
    for p, wanted in rec['source_pins'].items():
        if sha(p) != wanted: raise AssertionError(f'input changed during solve: {p}')
    h = local['b']['heights'].copy()
    quantized = np.asarray(result['x'], dtype=np.float32)
    if not np.isfinite(quantized).all() or np.any(quantized.astype(float) < lower) or np.any(quantized.astype(float) > upper):
        raise AssertionError('final quantized heights violate bounds; no repair allowed')
    for rc, value in zip(local['variables'], quantized): h[tuple(rc)] = value
    output = dict(local['b']); output['heights'] = h
    with OUT.open('xb') as f: np.savez_compressed(f, **output)
    rec.update({'status': 'AUTHORED_PENDING_INDEPENDENT_CONSUMER', 'candidate_path': str(OUT),
                'candidate_sha256': sha(OUT), 'elapsed_solver_s': elapsed,
                'changed_vertices': int(np.count_nonzero(h != local['b']['heights']))})
    rec['solver'].update({k: result[k] for k in ('success', 'status', 'message', 'nit', 'cost')})
    rec['solver']['calls'] = 1
    (HERE/'authoring.json').write_text(json.dumps(rec, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: rec[k] for k in ('status', 'candidate_sha256', 'elapsed_solver_s', 'changed_vertices')}))


if __name__ == '__main__': main()
