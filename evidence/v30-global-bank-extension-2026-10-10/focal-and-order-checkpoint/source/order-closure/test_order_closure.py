from __future__ import annotations

import importlib.util
import ast
from itertools import combinations, product
from pathlib import Path
import unittest

import numpy as np

MODULE_PATH = Path(__file__).with_name('projection.py')
spec = importlib.util.spec_from_file_location('ev93_order_projection_under_test', MODULE_PATH)
projection = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(projection)
AUTHOR_PATH = Path(__file__).with_name('author_order_closure.py')
author_spec = importlib.util.spec_from_file_location('ev93_order_author_under_test', AUTHOR_PATH)
author = importlib.util.module_from_spec(author_spec)
assert author_spec is not None and author_spec.loader is not None
author_spec.loader.exec_module(author)


def reachability_reference(raw, lo, hi, edges):
    """Independent all-pairs reference for small directed graphs."""
    n = len(raw)
    adj = [[] for _ in range(n)]
    rev = [[] for _ in range(n)]
    for w, c in edges:
        adj[int(w)].append(int(c))
        rev[int(c)].append(int(w))

    def closure(start, graph):
        seen = {start}
        todo = [start]
        while todo:
            u = todo.pop()
            for v in graph[u]:
                if v not in seen:
                    seen.add(v)
                    todo.append(v)
        return seen

    reachable_from = [closure(i, adj) for i in range(n)]
    # U[i] is the smallest upper bound reachable from i along directed edges.
    U = np.asarray([min(float(hi[j]) for j in reachable_from[i]) for i in range(n)],
                   dtype=np.float32)
    r = np.minimum(np.maximum(raw, lo), U).astype(np.float32)
    # q[i] is the maximum clipped value of any ancestor that can reach i.
    q = np.asarray([max(float(r[j]) for j in range(n) if i in reachable_from[j])
                    for i in range(n)], dtype=np.float32)
    return U, r, q


class OrderClosureTests(unittest.TestCase):
    def test_receipt_measurement_uses_defined_post_write_snapshot(self):
        source = AUTHOR_PATH.read_text(encoding='utf-8')
        tree = ast.parse(source)
        loaded = {node.id for node in ast.walk(tree)
                  if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
        assigned = {node.id for node in ast.walk(tree)
                    if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Param))}
        self.assertIn('memory_after_write', assigned)
        self.assertIn('memory_after_write', loaded)
        self.assertNotIn('memory_after', loaded)

    def test_chain_reverse_upper_then_forward_order(self):
        raw = np.asarray([1.5, 0.0, 0.0, 1.0], np.float32)
        lo = np.asarray([0.0, 0.0, 0.0, 1.0], np.float32)
        hi = np.asarray([2.0, 2.0, 2.0, 1.0], np.float32)
        baseline = np.asarray([0.0, 0.0, 0.0, 1.0], np.float32)
        edges = np.asarray([(0, 1), (1, 2), (2, 3)], np.int32)
        result = projection.project_order(raw, lo, hi, edges, baseline=baseline,
                                          fixed=np.asarray([False, False, False, True]))
        np.testing.assert_array_equal(result['upper_propagated'], np.ones(4, np.float32))
        np.testing.assert_array_equal(result['q'], np.ones(4, np.float32))
        self.assertLessEqual(result['max_abs_correction'], result['a_priori_correction_bound'])

    def test_compatible_cycle_uses_component_maximum(self):
        raw = np.asarray([1.25, 1.0], np.float32)
        lo = np.zeros(2, np.float32)
        hi = np.full(2, 2.0, np.float32)
        edges = np.asarray([(0, 1), (1, 0)], np.int32)
        result = projection.project_order(raw, lo, hi, edges,
                                          baseline=np.zeros(2, np.float32))
        np.testing.assert_array_equal(result['q'], np.asarray([1.25, 1.25], np.float32))

    def test_edge_orientation_is_witness_to_center(self):
        raw = np.asarray([1.0, 0.5], np.float32)
        result = projection.project_order(raw, np.zeros(2, np.float32),
                                          np.full(2, 2.0, np.float32),
                                          np.asarray([(0, 1)], np.int32))
        np.testing.assert_array_equal(result['q'], np.asarray([1.0, 1.0], np.float32))

    def test_receipt_edge_schema_is_center_then_witness(self):
        rows = np.asarray([(1, 2, 0, 1)], np.int32)
        edges = author.witness_rc_to_flat_edges(rows, (3, 4))
        np.testing.assert_array_equal(edges, np.asarray([(1, 6)], np.int64))
        raw = np.zeros(12, np.float32); raw[1] = 1.0
        q = projection.project_order(raw, np.zeros(12, np.float32),
                                     np.full(12, 2.0, np.float32), edges)['q']
        self.assertEqual(float(q[6]), 1.0)

    def test_incompatible_bounds_fail_after_reverse_propagation(self):
        with self.assertRaisesRegex(ValueError, 'infeasible box/order bounds'):
            projection.project_order(
                np.asarray([2.0, 0.0], np.float32),
                np.asarray([2.0, 0.0], np.float32),
                np.asarray([2.0, 1.0], np.float32),
                np.asarray([(0, 1)], np.int32))

    def test_baseline_is_required_to_be_feasible_when_supplied(self):
        with self.assertRaisesRegex(ValueError, 'baseline is not a feasible order witness'):
            projection.project_order(
                np.asarray([0.0, 0.0], np.float32), np.zeros(2, np.float32),
                np.full(2, 2.0, np.float32), np.asarray([(0, 1)], np.int32),
                baseline=np.asarray([1.0, 0.0], np.float32))

    def test_fixed_mask_requires_baseline(self):
        with self.assertRaisesRegex(ValueError, 'baseline is required'):
            projection.project_order(np.zeros(1, np.float32), np.zeros(1, np.float32),
                                     np.ones(1, np.float32), np.empty((0, 2), np.int32),
                                     fixed=np.asarray([True]))

    def test_nan_bad_shapes_and_bad_indices_fail_closed(self):
        lo = np.zeros(2, np.float32); hi = np.ones(2, np.float32)
        with self.assertRaisesRegex(ValueError, 'raw must be finite'):
            projection.project_order(np.asarray([np.nan, 0], np.float32), lo, hi,
                                     np.empty((0, 2), np.int32))
        with self.assertRaisesRegex(ValueError, 'flat float32 vector'):
            projection.project_order(np.zeros((1, 2), np.float32), lo, hi,
                                     np.empty((0, 2), np.int32))
        with self.assertRaisesRegex(ValueError, 'outside node domain'):
            projection.project_order(np.zeros(2, np.float32), lo, hi,
                                     np.asarray([(0, 2)], np.int32))
        with self.assertRaisesRegex(ValueError, r'integer \(E,2\)'):
            projection.project_order(np.zeros(2, np.float32), lo, hi,
                                     np.asarray([[0.0, 1.0]]))

    def test_exhaustive_small_graphs_match_reachability_reference(self):
        n = 3
        all_edges = [(w, c) for w in range(n) for c in range(n)]
        lo = np.zeros(n, np.float32)
        hi = np.full(n, 2.0, np.float32)
        # Every directed graph on three nodes, including self loops and cycles.
        for mask in range(1 << len(all_edges)):
            edges = np.asarray([edge for bit, edge in enumerate(all_edges)
                                if mask & (1 << bit)], dtype=np.int32).reshape(-1, 2)
            for vals in product((0.0, 1.0, 2.0), repeat=n):
                raw = np.asarray(vals, np.float32)
                got = projection.project_order(raw, lo, hi, edges, baseline=np.zeros(n, np.float32))
                exp_U, exp_r, exp_q = reachability_reference(raw, lo, hi, edges)
                np.testing.assert_array_equal(got['upper_propagated'], exp_U)
                np.testing.assert_array_equal(got['clipped'], exp_r)
                np.testing.assert_array_equal(got['q'], exp_q)

    def test_preclosure_correction_bound_rejects_corrupted_result(self):
        raw = np.asarray([1.0, 0.0, 0.0], np.float32)
        edges = np.asarray([(0, 1), (1, 2)], np.int32)
        got = projection.project_order(raw, np.zeros(3, np.float32),
                                      np.full(3, 2.0, np.float32), edges)
        self.assertEqual(got['q'].tolist(), [1.0, 1.0, 1.0])
        self.assertLessEqual(got['max_abs_correction'], got['a_priori_correction_bound'])
        corrupted = got['q'].copy()
        corrupted[2] = np.nextafter(corrupted[2], np.float32(np.inf))
        corrupted_delta = float(np.max(np.abs(corrupted.astype(np.float64)-raw.astype(np.float64))))
        self.assertGreater(corrupted_delta, got['a_priori_correction_bound'])

    def test_objective_budget_positive_and_negative(self):
        good = projection.evaluate_objective_gates(100.0, 100.000005, 110.0)
        self.assertTrue(good['closure_budget_pass'])
        self.assertTrue(good['strict_improvement_vs_baseline'])
        bad_budget = projection.evaluate_objective_gates(100.0, 100.00002, 110.0)
        self.assertFalse(bad_budget['closure_budget_pass'])
        no_improvement = projection.evaluate_objective_gates(100.0, 100.000001, 100.000001)
        self.assertTrue(no_improvement['closure_budget_pass'])
        self.assertFalse(no_improvement['strict_improvement_vs_baseline'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
