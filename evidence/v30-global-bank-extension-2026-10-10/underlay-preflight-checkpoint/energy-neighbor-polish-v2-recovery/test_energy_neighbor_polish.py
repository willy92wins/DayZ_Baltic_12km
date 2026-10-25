from __future__ import annotations

import importlib.util
import copy
from pathlib import Path
import sys
import time
import unittest

import numpy as np

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("energy_neighbor_polish_test", HERE / "energy_neighbor_polish.py")
polish = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = polish
SPEC.loader.exec_module(polish)


def record(*, cost=9.0, raw=10.0, baseline=12.0, exact=True, direct=True):
    return {"closed_cost": cost, "raw_cost": raw, "baseline_cost": baseline,
            "exact_rows_pass": exact,
            "exact_fraction_gates": {k: True for k in polish.EXACT_GATES},
            "direct_gates": {k: True for k in polish.DIRECT_GATES},
            "energy_gate": polish.is_energy_eligible(raw, cost, baseline)[0]}


class EnergyNeighborPolishTests(unittest.TestCase):
    def test_real_candidate_lattice_fixed_expression_mismatch_becomes_rejected_record(self):
        base = polish.load_pinned("test_fixed_base", polish.BASE_MODEL, polish.EXPECTED["base_model"])
        cm = polish.load_pinned("test_fixed_candidate", polish.MODEL, polish.EXPECTED["candidate_model"])
        grid = np.array([[2.0]], dtype=np.float32)
        wrapper = cm.CandidateLatticeMILP(base, grid, np.array([[0, 0]], dtype=np.int32),
            np.array([2.0], dtype=np.float32), np.array([2.0], dtype=np.float32),
            np.array([2.0], dtype=np.float64), fixed_indices=(0,))
        neighbor = grid.copy()
        neighbor[0, 0] = np.nextafter(neighbor[0, 0], np.float32(np.inf), dtype=np.float32)
        exact = wrapper.model.exact_gates(neighbor)
        self.assertIs(exact["fixed"], False)
        m = polish.lattice_vector_for_grid(wrapper, neighbor)
        with self.assertRaisesRegex(ValueError, r"fixed lattice value mismatch at 0"):
            wrapper.exact_rows_pass(m)
        failure = polish.classify_fixed_lattice_mismatch(
            ValueError("fixed lattice value mismatch at 0"), exact)
        self.assertEqual(failure, {"name": "fixed_lattice_value_mismatch", "index": 0,
            "detail": "fixed lattice value mismatch at 0"})
        class FakeExecutor:
            def eval_gates(self, _data, _grid):
                return {"raw_cost": 10.0, "closed_cost": 11.0, "baseline_cost": 12.0,
                    "allowance": 0.000001, "bounds": True, "PF_signs": True,
                    "all_116_direct_crossings": True, "D8_direct": True,
                    "face_cones": True, "closure_energy_and_improvement": False}
        record = polish.evaluate_grid(wrapper, FakeExecutor(), {}, neighbor, 10.0, 12.0)
        self.assertFalse(record["exact_rows_pass"])
        self.assertEqual(record["exact_row_failure_count"], 1)
        self.assertEqual(record["first_exact_row_failures"][0]["name"], "fixed_lattice_value_mismatch")

    def test_unknown_value_error_and_mismatched_fixed_flag_still_propagate(self):
        with self.assertRaisesRegex(ValueError, "unrecognized auxiliary"):
            polish.classify_fixed_lattice_mismatch(ValueError("unrecognized auxiliary x"), {"fixed": False})
        with self.assertRaisesRegex(ValueError, "fixed lattice value mismatch"):
            polish.classify_fixed_lattice_mismatch(ValueError("fixed lattice value mismatch at 3"), {"fixed": True})

    def test_real_candidate_lattice_outside_segments_is_a_rejection_for_both_exception_types(self):
        base = polish.load_pinned("test_segments_base", polish.BASE_MODEL, polish.EXPECTED["base_model"])
        cm = polish.load_pinned("test_segments_candidate", polish.MODEL, polish.EXPECTED["candidate_model"])
        grid = np.array([[2.0]], dtype=np.float32)
        hi = np.nextafter(np.float32(2.0), np.float32(np.inf), dtype=np.float32)
        wrapper = cm.CandidateLatticeMILP(base, grid, np.array([[0, 0]], dtype=np.int32),
            np.array([2.0], dtype=np.float32), np.array([hi], dtype=np.float32),
            np.array([2.0], dtype=np.float64))
        neighbor = grid.copy()
        neighbor[0, 0] = np.nextafter(neighbor[0, 0], np.float32(-np.inf), dtype=np.float32)
        exact = wrapper.model.exact_gates(neighbor)
        self.assertIs(exact["bounds"], False)

        class FakeExecutor:
            def eval_gates(self, _data, _grid):
                return {"raw_cost": 10.0, "closed_cost": 11.0, "baseline_cost": 12.0,
                    "bounds": False, "PF_signs": True, "all_116_direct_crossings": True,
                    "D8_direct": True, "face_cones": True,
                    "closure_energy_and_improvement": False}

        # Feed the actual CandidateLatticeMILP an integer lattice point outside its segments.
        original_vector = polish.lattice_vector_for_grid
        polish.lattice_vector_for_grid = lambda _wrapper, _grid: np.array([-1], dtype=np.int64)
        try:
            real_record = polish.evaluate_grid(wrapper, FakeExecutor(), {}, neighbor, 10.0, 12.0)
        finally:
            polish.lattice_vector_for_grid = original_vector
        self.assertFalse(real_record["exact_rows_pass"])
        self.assertEqual(real_record["first_exact_row_failures"][0]["name"], "outside_float32_domain_segments")

        # ModelError is a ValueError subclass, so its specific handler must precede ValueError.
        original = wrapper.exact_rows_pass
        def raise_model_error(_m):
            raise base.ModelError("lattice value outside segments at 0")
        wrapper.exact_rows_pass = raise_model_error
        polish.lattice_vector_for_grid = lambda _wrapper, _grid: np.array([-1], dtype=np.int64)
        try:
            model_error_record = polish.evaluate_grid(wrapper, FakeExecutor(), {}, neighbor, 10.0, 12.0)
        finally:
            polish.lattice_vector_for_grid = original_vector
        self.assertFalse(model_error_record["exact_rows_pass"])
        self.assertEqual(model_error_record["first_exact_row_failures"][0]["index"], 0)
        wrapper.exact_rows_pass = original

        polish.lattice_vector_for_grid = lambda _wrapper, _grid: np.array([-1], dtype=np.int64)
        wrapper.exact_rows_pass = lambda _m: (_ for _ in ()).throw(base.ModelError("unexpected model error"))
        try:
            with self.assertRaisesRegex(base.ModelError, "unexpected model error"):
                polish.evaluate_grid(wrapper, FakeExecutor(), {}, neighbor, 10.0, 12.0)
        finally:
            polish.lattice_vector_for_grid = original_vector

    def test_prior_receipt_pin_predicate_accepts_energy_only_rejection(self):
        prior = {
            "schema": "candidate-only-f32-lattice.real-run.v1",
            "status": "REJECTED_EXACT_POSTGATES", "accepted": False,
            "terrain_written": False, "solver_invoked": True,
            "exact_fraction_rows_pass": True,
            "exact_fraction_gates": {k: True for k in ("bounds", "fixed", "signs", "crossings", "d8", "shape")},
            "direct_executor_gates": {k: True for k in polish.DIRECT_GATES},
            "direct_executor_metrics": {"raw_cost": 10.0, "closed_cost": 10.000002,
                "baseline_cost": 12.0, "closure_allowance": 0.000001},
            "rejected_diagnostic": {"accepted": False, "terrain_written": False,
                "path": "diagnostic.npz", "sha256": polish.EXPECTED["diagnostic"]},
        }
        prior["direct_executor_gates"]["closure_energy_and_improvement"] = False
        prior["direct_executor_gates"]["raw_cost"] = True
        metrics = polish.validate_prior_receipt(prior, Path("diagnostic.npz"))
        self.assertEqual(metrics["allowance"], 0.000001)

    def test_prior_receipt_predicate_rejects_non_energy_failure_and_wrong_artifact(self):
        prior = {
            "schema": "candidate-only-f32-lattice.real-run.v1",
            "status": "REJECTED_EXACT_POSTGATES", "accepted": False,
            "terrain_written": False, "solver_invoked": True,
            "exact_fraction_rows_pass": True,
            "exact_fraction_gates": {k: True for k in ("bounds", "fixed", "signs", "crossings", "d8", "shape")},
            "direct_executor_gates": {k: True for k in polish.DIRECT_GATES},
            "direct_executor_metrics": {"raw_cost": 10.0, "closed_cost": 10.000002,
                "baseline_cost": 12.0, "closure_allowance": 0.000001},
            "rejected_diagnostic": {"accepted": False, "terrain_written": False,
                "path": "diagnostic.npz", "sha256": polish.EXPECTED["diagnostic"]},
        }
        prior["direct_executor_gates"]["closure_energy_and_improvement"] = False
        prior["direct_executor_gates"]["raw_cost"] = True
        bad_gate = copy.deepcopy(prior)
        bad_gate["direct_executor_gates"]["face_cones"] = False
        with self.assertRaises(RuntimeError):
            polish.validate_prior_receipt(bad_gate, Path("diagnostic.npz"))
        with self.assertRaises(RuntimeError):
            polish.validate_prior_receipt(prior, Path("other-diagnostic.npz"))

    def test_generates_exactly_two_single_node_nextafter_neighbors_in_fixed_order(self):
        grid = np.full((3, 4), np.float32(3.0), dtype=np.float32)
        coords = np.asarray([(0, 1), (2, 3)], dtype=np.int32)
        neighbors = list(polish.one_ulp_neighbors(grid, coords))
        self.assertEqual(len(neighbors), 4)
        self.assertEqual([(i, rc, step) for i, rc, step, _ in neighbors], [
            (0, (0, 1), -1), (0, (0, 1), 1), (1, (2, 3), -1), (1, (2, 3), 1)])
        for _, rc, step, candidate in neighbors:
            changed = np.argwhere(candidate.view(np.uint32) != grid.view(np.uint32))
            self.assertEqual(changed.tolist(), [list(rc)])
            expected = np.nextafter(grid[rc], np.float32(-np.inf if step < 0 else np.inf), dtype=np.float32)
            self.assertEqual(candidate[rc].view(np.uint32), expected.view(np.uint32))

    def test_energy_gate_accepts_exact_allowance_and_strict_baseline_improvement(self):
        raw, baseline = 10.0, 12.0
        allowance = 1e-7 * raw
        self.assertEqual(polish.is_energy_eligible(raw, raw + allowance, baseline), (True, allowance))
        self.assertFalse(polish.is_energy_eligible(raw, np.nextafter(raw + allowance, np.inf), baseline)[0])
        self.assertFalse(polish.is_energy_eligible(raw, baseline, baseline)[0])

    def test_all_exact_and_direct_gate_families_are_required(self):
        good = record()
        self.assertTrue(polish.candidate_is_eligible(good))
        bad = record();bad["exact_fraction_gates"]["d8"] = False
        self.assertFalse(polish.candidate_is_eligible(bad))
        bad = record();bad["exact_rows_pass"] = False
        self.assertFalse(polish.candidate_is_eligible(bad))
        bad = record();bad["direct_gates"]["face_cones"] = False
        self.assertFalse(polish.candidate_is_eligible(bad))
        bad = record();bad["energy_gate"] = False
        self.assertFalse(polish.candidate_is_eligible(bad))

    def test_deterministic_minimum_uses_cost_then_row_col_then_step(self):
        rows = [
            {**record(cost=8.5), "rc": [5, 9], "step": -1, "eligible": True},
            {**record(cost=8.4), "rc": [8, 2], "step": 1, "eligible": True},
            {**record(cost=8.4), "rc": [7, 2], "step": 1, "eligible": True},
            {**record(cost=8.4), "rc": [7, 2], "step": -1, "eligible": True},
        ]
        self.assertIs(polish.choose_best(rows), rows[3])

    def test_no_eligible_neighbor_is_terminal_and_does_not_widen(self):
        grid = np.full((2, 2), np.float32(3.0), dtype=np.float32)
        coords = np.asarray([(0, 0)], dtype=np.int32)
        seen = []
        def evaluator(candidate):
            seen.append(candidate.copy())
            r = record(cost=11.0, raw=10.0, baseline=12.0)
            r["energy_gate"], r["allowance"] = polish.is_energy_eligible(10.0, 11.0, 12.0)
            return r
        rows, best, best_grid = polish.enumerate_neighbors(grid, coords, evaluator, time.monotonic() + 5.0)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(seen), 2)
        self.assertIsNone(best)
        self.assertIsNone(best_grid)
        self.assertTrue(all(not x["eligible"] for x in rows))

    def test_nan_cost_fails_closed(self):
        ok, allowance = polish.is_energy_eligible(float("nan"), 1.0, 2.0)
        self.assertFalse(ok)
        self.assertTrue(np.isnan(allowance))


if __name__ == "__main__":
    unittest.main(verbosity=2)
