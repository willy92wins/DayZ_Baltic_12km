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
