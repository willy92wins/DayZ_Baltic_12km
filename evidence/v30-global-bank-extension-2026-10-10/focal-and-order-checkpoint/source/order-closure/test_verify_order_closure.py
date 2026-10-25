from __future__ import annotations

import importlib.util
import itertools
from pathlib import Path

import numpy as np

MODULE_PATH = Path(__file__).with_name('verify_order_closure.py')
spec = importlib.util.spec_from_file_location('verify_order_closure_under_test', MODULE_PATH)
consumer = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(consumer)


def brute_minimal_majorant(raw, lo, hi, edges):
    """Tiny exact enumerator used only by this consumer fixture."""
    r = np.minimum(np.maximum(raw, lo), hi)
    feasible = []
    for values in itertools.product(range(3), repeat=len(raw)):
        q = np.asarray(values, dtype=np.int8)
        if np.any(q < lo) or np.any(q > hi) or np.any(q < r):
            continue
        if any(q[c] < q[w] for c, w in edges):
            continue
        feasible.append(q)
    if not feasible:
        return None
    # The unique least feasible vector is coordinatewise <= every other one.
    minima = [q for q in feasible if all(np.all(q <= other) for other in feasible)]
    assert len(minima) == 1
    return minima[0]


def test_small_graphs_match_exhaustive_feasible_order_box():
    cases = [
        ((0, 1, 2), (0, 0, 0), (2, 2, 2), ((1, 0), (2, 1))),
        ((2, 0, 1), (0, 0, 0), (2, 2, 2), ((1, 0), (2, 1))),
        ((0, 2, 1), (0, 0, 0), (2, 2, 2), ((1, 0), (0, 1))),
        ((1, 0, 2), (0, 0, 1), (2, 1, 2), ((1, 0), (2, 1))),
    ]
    for raw_t, lo_t, hi_t, edges_t in cases:
        raw = np.asarray([raw_t], dtype=np.float32)
        lo = np.asarray([lo_t], dtype=np.float32)
        hi = np.asarray([hi_t], dtype=np.float32)
        edges = np.asarray([[0, c, 0, w] for c, w in edges_t], dtype=np.int32)
        result = consumer.project_order_closure(raw, lo, hi, edges)
        expected = brute_minimal_majorant(raw_t, lo_t, hi_t, edges_t)
        assert expected is not None
        assert tuple(result['heights'][0].astype(int)) == tuple(expected.tolist())
        assert result['correction_bound_pass']


def test_projection_payload_real_predicate_and_mutation_negatives():
    raw = np.asarray([[2, 0, 1]], dtype=np.float32)
    lo = np.zeros_like(raw)
    hi = np.full_like(raw, 2)
    edges = np.asarray([[0, 1, 0, 0], [0, 2, 0, 1]], dtype=np.int32)
    p = consumer.project_order_closure(raw, lo, hi, edges)
    payload = {
        'heights': p['heights'].copy(),
        'clipped_float32': p['clipped_float32'].copy(),
        'upper_propagated': p['upper_propagated'].copy(),
        'witness_edges_rc': edges.copy(),
        'lower_grid': lo.copy(), 'upper_grid': hi.copy(),
    }
    rebuilt, exact = consumer.validate_projection_arrays(payload, raw, lo, hi, edges)
    assert exact and np.array_equal(rebuilt['heights'], payload['heights'])
    payload['heights'][0, 1] = np.float32(0)
    _, exact = consumer.validate_projection_arrays(payload, raw, lo, hi, edges)
    assert not exact
    payload['heights'] = p['heights'].copy()
    payload['clipped_float32'][0, 0] = np.nextafter(payload['clipped_float32'][0, 0], np.float32(-np.inf))
    _, exact = consumer.validate_projection_arrays(payload, raw, lo, hi, edges)
    assert not exact


def test_cost_gate_rejects_large_projection_delta():
    from scipy import sparse
    A = sparse.eye(2, format='csr', dtype=np.float64)
    rhs = np.zeros(2, dtype=np.float64)
    raw = np.asarray([2, 0], dtype=np.float32)
    closed = np.asarray([2, 2], dtype=np.float32)
    base = np.asarray([2, 2], dtype=np.float64)
    report = consumer.closure_cost_report(A, rhs, base, raw, closed)
    assert report['closed'] == report['B']
    assert report['delta'] > report['allowed_delta']
    assert not report['pass']


def test_empty_graph_identity_and_invalid_inputs_fail_closed():
    raw = np.asarray([[1.0, 2.0]], dtype=np.float32)
    edges = np.empty((0, 4), dtype=np.int32)
    identity = consumer.project_order_closure(raw, raw.copy(), raw.copy(), edges)
    assert np.array_equal(identity['heights'], raw)
    bad_edges = np.asarray([[0, 0, 0, 0]], dtype=np.int32)
    try:
        consumer.project_order_closure(raw, np.zeros_like(raw), np.ones_like(raw), bad_edges)
    except ValueError:
        pass
    else:
        raise AssertionError('self-edge was not rejected as duplicate/invalid witness')


def test_candidate_npz_schema_rejects_float_encoded_witness_edges():
    shape=(260,260)
    candidate={
        'heights':np.zeros(shape,np.float32), 'raw_float32':np.zeros(shape,np.float32),
        'clipped_float32':np.zeros(shape,np.float32), 'upper_propagated':np.zeros(shape,np.float32),
        'lower_grid':np.zeros(shape,np.float32), 'upper_grid':np.zeros(shape,np.float32),
        'base_local':np.zeros(shape,np.float32), 'nodes_local':np.asarray([[1,1]],np.int32),
        'lo':np.asarray([0.],np.float64), 'hi':np.asarray([0.],np.float64),
        'witness_edges_rc':np.asarray([[1,1,1,2]],np.int32),
    }
    consumer.validate_candidate_schema(candidate)
    candidate['witness_edges_rc']=candidate['witness_edges_rc'].astype(np.float32)
    try:
        consumer.validate_candidate_schema(candidate)
    except ValueError:
        pass
    else:
        raise AssertionError('float-encoded witness edges passed the NPZ schema gate')


if __name__ == '__main__':
    checks = [test_small_graphs_match_exhaustive_feasible_order_box,
              test_projection_payload_real_predicate_and_mutation_negatives,
              test_cost_gate_rejects_large_projection_delta,
              test_empty_graph_identity_and_invalid_inputs_fail_closed,
              test_candidate_npz_schema_rejects_float_encoded_witness_edges]
    for check in checks:
        check()
    print({'status':'PASS','fixtures':len(checks),'names':[fn.__name__ for fn in checks]})

