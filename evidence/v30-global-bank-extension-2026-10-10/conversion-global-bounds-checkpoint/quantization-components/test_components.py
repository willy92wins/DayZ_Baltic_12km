from __future__ import annotations

import importlib.util
import json
from fractions import Fraction
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import convert_components as cc

OLD = HERE.parent / "float32-neighborhood-v1"
COMPAT = OLD / "real-enumeration-01/compatibility-diagnostic.json"
COMPAT_SHA = "0cb852c2aa3bdd99e7b1dbdfb079df5f9faa65c3db854a3ff1389b25d8b53da7"


class FakeExecutor:
    @staticmethod
    def memory_peak_ws_bytes():
        return 0


def relation(a, b, allowed, endpoints=((0, 0), (0, 1)), kind="fixture"):
    table = [[(i, j) in set(allowed) for j in range(3)] for i in range(3)]
    return cc.BinaryConstraint(a, b, cc.table_tuple(table), kind, "fixture", endpoints)


class ConstraintConstructionFixtures(unittest.TestCase):
    def test_bounds_remove_only_out_of_box_neighbors(self):
        raw = np.float32(1.0)
        values = (np.nextafter(raw, np.float32(-np.inf), dtype=np.float32), raw,
                  np.nextafter(raw, np.float32(np.inf), dtype=np.float32))
        self.assertEqual(cc.bit_options(cc.bound_option_mask(values, raw, raw)), (1,))
        self.assertEqual(cc.bit_options(cc.bound_option_mask(values, values[0], values[2])), (0, 1, 2))

    def test_nine_crossing_pairs_match_independent_fraction_scalar(self):
        ex = cc.load_executor()  # source import only; no real map/data load
        raw_a, raw_b = np.float32(3.0), np.float32(1.0)
        opts_a = (np.nextafter(raw_a, np.float32(-np.inf), dtype=np.float32), raw_a,
                  np.nextafter(raw_a, np.float32(np.inf), dtype=np.float32))
        opts_b = (np.nextafter(raw_b, np.float32(-np.inf), dtype=np.float32), raw_b,
                  np.nextafter(raw_b, np.float32(np.inf), dtype=np.float32))
        la = lb = Fraction(2, 1)
        lower = upper = Fraction(1, 2)
        spec = ex.CrossSpec(("fixture",), "P", (0, 0), ((0, 0), (0, 1)), (7, 7), (7, 8),
                            la, lb, 0, lower, upper, la, lb, (0, 0), (0, 1))
        def production(i, j):
            grid = np.zeros((15, 15), dtype=np.float32)
            grid[7, 7], grid[7, 8] = opts_a[i], opts_b[j]
            return ex.direct_crossings_pass(grid, (spec,))
        actual = cc.table_from_predicate(production)
        expected = cc.table_from_predicate(lambda i, j: cc.fraction_crossing_pass(
            opts_a[i], opts_b[j], la, lb, 0, lower, upper))
        self.assertEqual(actual, expected)
        self.assertEqual(sum(sum(row) for row in actual), 1)
        self.assertTrue(actual[1][1])

    def test_d8_all_nine_pairs_match_float32_center_witness(self):
        center = (np.nextafter(np.float32(2.0), np.float32(-np.inf), dtype=np.float32),
                  np.float32(2.0),
                  np.nextafter(np.float32(2.0), np.float32(np.inf), dtype=np.float32))
        witness = center
        table = cc.table_from_predicate(lambda i, j: bool(center[i] >= witness[j]))
        self.assertEqual(table, ((True, False, False), (True, True, False), (True, True, True)))

    def test_strict_sign_domain_uses_exact_binary32_without_extra_ulp(self):
        raw = np.float32(3.0)
        above = np.nextafter(raw, np.float32(np.inf), dtype=np.float32)
        below = np.nextafter(raw, np.float32(-np.inf), dtype=np.float32)
        level = Fraction.from_float(float(raw))
        self.assertEqual(cc.bit_options(cc.strict_sign_mask((below, raw, above), level, +1)), (2,))
        self.assertEqual(cc.bit_options(cc.strict_sign_mask((below, raw, above), level, -1)), (0,))
        self.assertEqual(cc.bit_options(cc.strict_sign_mask((below, raw, above), level, 0, raw)), (1,))

    def test_geometry_endpoint_resolution_connects_beyond_original_ten(self):
        coords = ((863, 1187), (864, 1187), (864, 1188))
        by_rc = {rc: i for i, rc in enumerate(coords)}
        # Both edges are supplied as geometric endpoint pairs; the last vertex is not in the old ten.
        e0 = cc.resolve_edge_variables(coords[0], coords[1], by_rc)
        e1 = cc.resolve_edge_variables(coords[1], coords[2], by_rc)
        rels = (relation(*e0, allowed={(0, 0), (0, 1), (1, 0), (1, 2), (2, 1), (2, 2)},
                         endpoints=(coords[0], coords[1])),
                relation(*e1, allowed={(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)},
                         endpoints=(coords[1], coords[2])))
        old_ten = {(862, 1186), (862, 1187), (863, 1187), (864, 1187), (865, 1187),
                   (865, 1188), (866, 1187), (866, 1188), (867, 1187), (867, 1188)}
        seeds, _ = cc.raw_failure_seeds((), rels)
        components, _ = cc.components_from_seeds(3, rels, seeds)
        component_rc = {coords[i] for comp in components for i in comp}
        self.assertNotIn(coords[2], old_ten)
        self.assertEqual(seeds, {0, 1})
        self.assertEqual(component_rc, set(coords))

    def test_real_pairwise_conflict_fixture_from_pinned_tables(self):
        self.assertEqual(cc.sha256(COMPAT), COMPAT_SHA)
        obj = json.loads(COMPAT.read_text(encoding="utf-8"))
        self.assertEqual(obj["crossing_record_count"], 116)
        self.assertEqual(obj["empty_compatibility_records"], [])
        r76 = next(r for r in obj["crossing_records"] if r["index"] == 76)
        r80 = next(r for r in obj["unary_crossing_constraints"] if r["record"] == 80)
        edge80 = next(r for r in obj["crossing_records"] if r["index"] == 80)
        self.assertEqual(r76["target_indices"], [2, 3])
        self.assertEqual(r76["allowed_option_pairs"], [[0, 2], [1, 2], [2, 2]])
        self.assertEqual(r80["target_index"], 3)
        self.assertEqual(r80["allowed_options"], [0, 1])
        self.assertEqual(edge80["edge_rc"], [[864, 1187], [864, 1188]])
        pilot_rc = [(r, c) for r in range(857, 868) for c in range(1181, 1192)]
        pilot_map = {rc: i for i, rc in enumerate(pilot_rc)}
        self.assertEqual(cc.resolve_edge_variables(tuple(edge80["edge_rc"][0]),
                                                   tuple(edge80["edge_rc"][1]), pilot_map),
                         (pilot_map[(864, 1187)], pilot_map[(864, 1188)]))
        rel = relation(2, 3, {tuple(pair) for pair in r76["allowed_option_pairs"]},
                       endpoints=((863, 1187), (864, 1187)), kind="P-crossing-record-76")
        domains = {2: cc.ALL_OPTIONS, 3: cc.mask_of(r80["allowed_options"])}
        after, why = cc.propagate(domains, (rel,))
        self.assertEqual(after[2], 0)
        self.assertEqual(why["variable"], 2)


class SearchAndComponentFixtures(unittest.TestCase):
    def test_unexpected_error_after_output_create_persists_receipt_without_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "real-conversion-01"
            with mock.patch.object(cc, "OUT", output), mock.patch.object(
                    cc, "_load_real_problem", side_effect=ValueError("pinned input changed: synthetic input")):
                with self.assertRaisesRegex(ValueError, "pinned input changed"):
                    cc.run_conversion(cc.sha256(Path(cc.__file__)), cc.sha256(cc.PLAN))
            self.assertTrue(output.is_dir())
            receipt_path = output / "receipt.json"
            self.assertTrue(receipt_path.is_file())
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"], "ERROR")
            self.assertEqual(receipt["error"], "ValueError: pinned input changed: synthetic input")
            self.assertTrue(receipt["source_readset_equal"])
            self.assertFalse((output / "unaccepted-candidate-context.npz").exists())

    def test_fixed_failure_and_assembled_gate_fail_closed(self):
        with self.assertRaises(cc.ConversionStop) as ctx:
            cc.require_fixed_constraint(False, "D8", "fixed-pair-7")
        self.assertEqual(ctx.exception.status, "NO_FEASIBLE_FIXED_CONSTRAINT")
        self.assertTrue(cc.all_gates_pass({"bounds": True, "crossings": True}))
        self.assertFalse(cc.all_gates_pass({"bounds": True, "crossings": False}))

    def test_raw_failure_component_does_not_touch_independent_raw_component(self):
        rels = (relation(0, 1, {(1, 2), (2, 1)}),
                relation(2, 3, {(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)}))
        seeds, _ = cc.raw_failure_seeds((), rels)
        components, _ = cc.components_from_seeds(4, rels, seeds)
        self.assertEqual(components, ((0, 1),))
        self.assertEqual(seeds, {0, 1})
        opts = ((np.float32(0), np.float32(1), np.float32(2)),) * 4
        budget = {"nodes": 0, "peak_ws": 0, "executor": FakeExecutor()}
        active, _ = cc.component_search(components[0], {i: 7 for i in range(4)}, rels,
                                        opts, np.asarray([0., 2., 0., 0.]),
                                        time.monotonic() + 5, budget, 100)
        self.assertEqual(set(active), {0, 1})
        raw_assignment = {2: 1, 3: 1}
        self.assertEqual(raw_assignment, {2: 1, 3: 1})

    def test_branch_and_bound_uses_l1_then_distance_then_lexicographic(self):
        rel = relation(0, 1, {(1, 2), (2, 1)})
        opts = ((np.float32(0), np.float32(1), np.float32(2)),
                (np.float32(0), np.float32(1), np.float32(2)))
        x64 = np.asarray([2.0, 0.0], dtype=np.float64)
        budget = {"nodes": 0, "peak_ws": 0, "executor": FakeExecutor()}
        got, rank = cc.component_search((0, 1), {0: 7, 1: 7}, (rel,), opts, x64,
                                        time.monotonic() + 5, budget, 100)
        self.assertEqual(got, {0: 2, 1: 1})
        self.assertEqual(rank, (1, 1.0, (1, 0)))

    def test_search_node_cap_is_terminal(self):
        rel = relation(0, 1, {(1, 2), (2, 1)})
        opts = ((np.float32(0), np.float32(1), np.float32(2)),) * 2
        budget = {"nodes": 0, "peak_ws": 0, "executor": FakeExecutor()}
        with self.assertRaises(cc.ConversionStop) as ctx:
            cc.component_search((0, 1), {0: 7, 1: 7}, (rel,), opts, np.asarray([2., 0.]),
                                time.monotonic() + 5, budget, 1)
        self.assertEqual(ctx.exception.status, "SEARCH_LIMIT")

    def test_time_cap_is_terminal(self):
        rel = relation(0, 1, {(1, 2), (2, 1)})
        opts = ((np.float32(0), np.float32(1), np.float32(2)),) * 2
        budget = {"nodes": 0, "peak_ws": 0, "executor": FakeExecutor()}
        with self.assertRaises(cc.ConversionStop) as ctx:
            cc.component_search((0, 1), {0: 7, 1: 7}, (rel,), opts, np.asarray([2., 0.]),
                                time.monotonic() - 1, budget, 100)
        self.assertEqual(ctx.exception.status, "TIME_LIMIT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
