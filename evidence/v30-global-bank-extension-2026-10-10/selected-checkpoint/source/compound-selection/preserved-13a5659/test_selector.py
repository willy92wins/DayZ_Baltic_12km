from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

SOURCE = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/compound-selection/selector.py")
spec = importlib.util.spec_from_file_location("ev93_compound_selector_fixture", SOURCE)
selector = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = selector
spec.loader.exec_module(selector)


class SelectionFixtures(unittest.TestCase):
    @staticmethod
    def make_unit(node, value=1.0):
        return {"variables_rc": np.asarray([node], dtype=np.int32),
                "B_values_float32": np.asarray([0.0], dtype=np.float32),
                "final_float32": np.asarray([value], dtype=np.float32)}

    @staticmethod
    def active_corner_count(h, cell):
        r, c = cell
        return int(np.count_nonzero(h[r:r+2, c:c+2]))

    def run_select(self, units, cells, area_fn, baseline=None, qids=None, limit=1e-7):
        base = np.zeros((6, 6), dtype=np.float32)
        baseline = baseline or {layer: {cell: 0.0 for cell in cells} for layer in selector.LAYERS}
        def hole_fn(h, requested, layer):
            return {cell: float(area_fn(h, cell, layer)) for cell in requested}
        return selector.greedy_restore_selection(base=base, units=units, cell_domain=set(cells),
            baseline_holes=baseline, hole_fn=hole_fn,
            unit_qid=qids or {u: int(u.split(":")[-1]) for u in units}, limit_m2=limit)

    def test_global_sum_rejects_individually_subthreshold_cells(self):
        cells = {(0, 0), (0, 2)}
        units = {"legacy:1": self.make_unit((1, 1)), "legacy:2": self.make_unit((1, 3))}
        def area(h, cell, layer):
            node = (1, 1) if cell == (0, 0) else (1, 3)
            return 6e-8 if h[node] else 0.0
        result = self.run_select(units, cells, area)
        self.assertEqual(result["status"], "SELECTED")
        self.assertAlmostEqual(result["candidate_sums_m2"]["physical"], 6e-8, places=18)
        self.assertEqual(result["excluded_unit_ids"], ["legacy:1"])

    def test_shared_cell_is_recomputed_after_whole_unit_restore(self):
        cell = (0, 0)
        units = {"legacy:1": self.make_unit((0, 0)), "crest:1": self.make_unit((0, 1))}
        def area(h, _cell, _layer):
            n = self.active_corner_count(h, cell)
            return {0: 0., 1: 7e-8, 2: 1.5e-7}[n]
        result = self.run_select(units, {cell}, area,
            qids={"legacy:1": 1, "crest:1": 1})
        self.assertEqual(result["status"], "SELECTED")
        self.assertEqual(result["order"], ["crest:1", "legacy:1"])
        self.assertEqual(result["excluded_unit_ids"], ["crest:1"])
        self.assertEqual(result["candidate_sums_m2"]["visible"], 7e-8)
        self.assertEqual(len(result["trace"]), 1)
        self.assertEqual(result["trace"][0]["recomputed_cells"], 1)

    def test_whole_unit_restore_removes_every_owned_node(self):
        cells = {(0, 0), (0, 1)}
        units = {"legacy:4": {"variables_rc": np.asarray([[1, 1], [1, 2]], dtype=np.int32),
            "B_values_float32": np.asarray([0., 0.], dtype=np.float32),
            "final_float32": np.asarray([1., 1.], dtype=np.float32)}}
        def area(h, cell, _layer):
            return 8e-8 if np.any(h[cell[0]:cell[0]+2, cell[1]:cell[1]+2]) else 0.
        result = self.run_select(units, cells, area)
        self.assertEqual(result["status"], "SELECTED")
        self.assertEqual(result["excluded_unit_ids"], ["legacy:4"])
        self.assertTrue(np.array_equal(result["candidate"], np.zeros((6, 6), dtype=np.float32)))

    def test_baseline_failure_stops_without_selection(self):
        cells = {(0, 0)}
        units = {"legacy:1": self.make_unit((0, 0))}
        baseline = {layer: {cell: 1e-7 for cell in cells} for layer in selector.LAYERS}
        result = self.run_select(units, cells, lambda *_: 1e-7, baseline=baseline)
        self.assertEqual(result["status"], "FAIL_BASE")
        self.assertIsNone(result["candidate"])

    def test_contribution_order_tie_breaks_by_source_qid_then_unit(self):
        contribution = {"crest:9": {"physical": 1., "visible": 0.},
                        "legacy:2": {"physical": 1., "visible": 0.},
                        "legacy:1": {"physical": 1., "visible": 0.}}
        qids = {"crest:9": 9, "legacy:2": 2, "legacy:1": 2}
        self.assertEqual(selector.deterministic_order(contribution, qids),
                         ["legacy:1", "legacy:2", "crest:9"])

    def test_multiple_owner_identity_is_origin_scoped(self):
        base = np.zeros((4, 4), dtype=np.float32)
        units = {"legacy:5": self.make_unit((1, 1)), "crest:5": self.make_unit((2, 2))}
        composed, owner, _ = selector.node_owner_map(units, base)
        self.assertEqual(set(owner.values()), {"legacy:5", "crest:5"})
        self.assertEqual(len(selector.changed_nodes(base, composed)), 2)

    def test_mutable_vertex_collision_fails_closed(self):
        base = np.zeros((4, 4), dtype=np.float32)
        units = {"legacy:5": self.make_unit((1, 1)), "crest:5": self.make_unit((1, 1))}
        with self.assertRaisesRegex(ValueError, "multiple owners"):
            selector.node_owner_map(units, base)


if __name__ == "__main__":
    unittest.main(verbosity=2)
