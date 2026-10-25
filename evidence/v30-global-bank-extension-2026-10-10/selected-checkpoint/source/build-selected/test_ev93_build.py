"""Offline readiness fixtures for the EV93 selected-bank preview adapter."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

import ev93_build_common as common
from ev93_build_common import (
    SELECTED_GLOBAL_CONSUMER_SOURCE, SELECTED_LOCAL_CONSUMER_SOURCE, SELECTOR_SOURCE,
    add_acceptance_manifest, load_accepted_inputs,
)
from prepare_probe import barycentric_height_independent, recalibrated_points, reference_with_points


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ReadinessFixtures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.candidate = self.root / "candidate.npz"
        self.candidate.write_bytes(b"fixture-candidate")
        self.base_path = self.root / "candidate" / "terrain.npz"
        self.base_path.parent.mkdir()
        self.base_path.write_bytes(b"fixture-baseline")
        self.original_ev82 = common.EV82
        self.original_base_sha = common.BASE_TERRAIN_SHA
        common.EV82 = self.root
        common.BASE_TERRAIN_SHA = sha(self.base_path)
        self.input_file = self.root / "pinned-input.json"
        self.input_file.write_text('{"fixture":true}\n', encoding="utf-8")
        self.pool_path = self.root / "compound-pool.json"
        self.pool_path.write_text('{"fixture":"pool"}\n', encoding="utf-8")
        self.receipt_path = self.root / "selection.json"
        self.report_path = self.root / "consumer.json"
        self.selection = {
            "schema": "ev93.compound-selection.v1",
            "status": "SELECTED",
            "selector_source_path": str(SELECTOR_SOURCE.resolve()),
            "selector_sha256": common.SELECTOR_SOURCE_SHA,
            "compound_pool_path": str(self.pool_path.resolve()),
            "compound_pool_sha256": sha(self.pool_path),
            "base_path": str(self.base_path.resolve()),
            "base_sha256": sha(self.base_path),
            "candidate": {"path": str(self.candidate.resolve()), "sha256": sha(self.candidate),
                          "metadata_equal_to_B": True},
            "source_read_set": {str(SELECTOR_SOURCE.resolve()): sha(SELECTOR_SOURCE),
                                str(SELECTED_LOCAL_CONSUMER_SOURCE.resolve()): sha(SELECTED_LOCAL_CONSUMER_SOURCE),
                                str(self.pool_path.resolve()): sha(self.pool_path),
                                str(self.base_path.resolve()): sha(self.base_path)},
            "retained_unit_ids": ["crest:12"], "excluded_unit_ids": ["legacy:8"],
            "units": [{"unit_id": "crest:12", "selection_status": "retained", "changed_vertices": 1},
                      {"unit_id": "legacy:8", "selection_status": "excluded_support"}],
        }
        self.write_selection()
        readset = {
            str(self.input_file.resolve()): sha(self.input_file),
            str(self.pool_path.resolve()): sha(self.pool_path),
            str(self.base_path.resolve()): sha(self.base_path),
            str(self.candidate.resolve()): sha(self.candidate),
            str(self.receipt_path.resolve()): sha(self.receipt_path),
            str(SELECTOR_SOURCE.resolve()): sha(SELECTOR_SOURCE),
            str(SELECTED_LOCAL_CONSUMER_SOURCE.resolve()): sha(SELECTED_LOCAL_CONSUMER_SOURCE),
            str(SELECTED_GLOBAL_CONSUMER_SOURCE.resolve()): sha(SELECTED_GLOBAL_CONSUMER_SOURCE),
        }
        self.report = {
            "status": "PASS_INCREMENTAL_NONREGRESSION",
            "gates": {"geometry": True, "water": True},
            "information": {
                "global_contract_status": "OPEN_INHERITED_MAP_DEFECTS",
                "selection_sha256": sha(self.receipt_path),
                "compound_pool_sha256": self.selection["compound_pool_sha256"],
                "candidate_path": str(self.candidate.resolve()),
                "candidate_sha256": self.selection["candidate"]["sha256"],
                "consumer_source_path": str(SELECTED_GLOBAL_CONSUMER_SOURCE.resolve()),
                "consumer_source_sha256": sha(SELECTED_GLOBAL_CONSUMER_SOURCE),
                "retained_crest_units": 1, "changed_vertices": 4,
                "input_hashes_expected": readset,
                "input_hashes_start": dict(readset),
                "input_hashes_end": dict(readset),
            },
        }
        self.write_report()

    def tearDown(self):
        common.EV82 = self.original_ev82
        common.BASE_TERRAIN_SHA = self.original_base_sha
        self.temp.cleanup()

    def write_selection(self):
        self.receipt_path.write_text(json.dumps(self.selection, sort_keys=True), encoding="utf-8")

    def write_report(self):
        self.report_path.write_text(json.dumps(self.report, sort_keys=True), encoding="utf-8")

    def test_exact_selection_and_consumer_pass_are_accepted(self):
        accepted = load_accepted_inputs(self.receipt_path, self.report_path)
        self.assertEqual(accepted["candidate_sha256"], self.selection["candidate"]["sha256"])
        self.assertEqual(accepted["changed_vertices"], 4)
        self.assertEqual(accepted["retained_crest_units"], 1)
        artifact = add_acceptance_manifest({}, accepted)
        self.assertEqual(artifact["ev93_selection_receipt_sha256"], accepted["receipt_sha256"])
        self.assertEqual(artifact["ev93_compound_pool_sha256"], accepted["compound_pool_sha256"])
        self.assertEqual(artifact["ev93_selector_source_sha256"], accepted["selector_source_sha256"])
        self.assertEqual(artifact["ev93_consumer_source_sha256"], accepted["consumer_source_sha256"])
        self.assertNotIn("ev93_authoring_receipt", artifact)

    def test_wrong_selection_hash_fails_closed(self):
        self.report["information"]["selection_sha256"] = "0" * 64
        self.write_report()
        with self.assertRaisesRegex(ValueError, "exact selection receipt"):
            load_accepted_inputs(self.receipt_path, self.report_path)

    def test_expected_start_end_readsets_must_match(self):
        self.report["information"]["input_hashes_end"][str(self.input_file.resolve())] = "0" * 64
        self.write_report()
        with self.assertRaisesRegex(ValueError, "expected/start/end"):
            load_accepted_inputs(self.receipt_path, self.report_path)

    def test_readset_is_rehashed_after_pass(self):
        self.input_file.write_text("drifted\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "consumer input changed after PASS"):
            load_accepted_inputs(self.receipt_path, self.report_path)

    def test_no_retained_crest_fails_closed(self):
        self.selection["retained_unit_ids"] = ["legacy:8"]
        self.selection["excluded_unit_ids"] = ["crest:12"]
        self.selection["units"][0]["selection_status"] = "excluded_support"
        self.selection["units"][1]["selection_status"] = "retained"
        self.write_selection()
        self.report["information"]["selection_sha256"] = sha(self.receipt_path)
        self.write_report()
        with self.assertRaisesRegex(ValueError, "retained crest"):
            load_accepted_inputs(self.receipt_path, self.report_path)

    def test_candidate_identity_mismatch_fails_closed(self):
        self.selection["candidate"]["sha256"] = "0" * 64
        self.write_selection()
        with self.assertRaisesRegex(ValueError, "candidate path/SHA"):
            load_accepted_inputs(self.receipt_path, self.report_path)

    def test_pool_identity_mismatch_fails_closed(self):
        self.selection["compound_pool_sha256"] = "0" * 64
        self.write_selection()
        with self.assertRaisesRegex(ValueError, "compound pool path/SHA"):
            load_accepted_inputs(self.receipt_path, self.report_path)

    def test_selector_source_identity_is_pinned(self):
        self.selection["selector_sha256"] = "0" * 64
        self.write_selection()
        with self.assertRaisesRegex(ValueError, "reviewed freeze"):
            load_accepted_inputs(self.receipt_path, self.report_path)

    def test_consumer_source_identity_is_pinned(self):
        self.report["information"]["consumer_source_sha256"] = "0" * 64
        self.write_report()
        with self.assertRaisesRegex(ValueError, "global consumer source path/SHA"):
            load_accepted_inputs(self.receipt_path, self.report_path)

    def test_global_report_must_not_be_local_consumer(self):
        self.report["information"]["consumer_source_path"] = str(SELECTED_LOCAL_CONSUMER_SOURCE.resolve())
        self.report["information"]["consumer_source_sha256"] = sha(SELECTED_LOCAL_CONSUMER_SOURCE)
        self.write_report()
        with self.assertRaisesRegex(ValueError, "global consumer source path/SHA"):
            load_accepted_inputs(self.receipt_path, self.report_path)

    def test_global_expected_readset_must_include_selection_sources(self):
        local_path = str(SELECTED_LOCAL_CONSUMER_SOURCE.resolve())
        for key in ("input_hashes_expected", "input_hashes_start", "input_hashes_end"):
            self.report["information"][key].pop(local_path)
        self.write_report()
        with self.assertRaisesRegex(ValueError, "global consumer expected read-set omits"):
            load_accepted_inputs(self.receipt_path, self.report_path)

    def test_global_expected_readset_must_bind_global_source(self):
        global_path = str(SELECTED_GLOBAL_CONSUMER_SOURCE.resolve())
        for key in ("input_hashes_expected", "input_hashes_start", "input_hashes_end"):
            self.report["information"][key].pop(global_path)
        self.write_report()
        with self.assertRaisesRegex(ValueError, "global consumer expected read-set does not bind"):
            load_accepted_inputs(self.receipt_path, self.report_path)

    def test_false_consumer_gate_fails_closed(self):
        self.report["gates"]["water"] = False
        self.write_report()
        with self.assertRaisesRegex(ValueError, "gates"):
            load_accepted_inputs(self.receipt_path, self.report_path)

    def test_nonselected_receipt_fails_closed(self):
        self.selection["status"] = "FAIL_CREST_RETENTION"
        self.write_selection()
        with self.assertRaisesRegex(ValueError, "SELECTED"):
            load_accepted_inputs(self.receipt_path, self.report_path)


class NativeReferenceFixtures(unittest.TestCase):
    def test_point_overlay_serializes_new_ground_and_preserves_water(self):
        baseline = [
            {"id": 0, "x": 3.0, "z": 12279.0, "cls": 1, "expected_ground": 4.0, "expected_water": 0.25},
            {"id": 1, "x": 9.0, "z": 12273.0, "cls": 2, "expected_ground": 6.0},
        ]
        updated = recalibrated_points(baseline, [5.0, 7.0])
        reference = reference_with_points({"points": baseline, "other": "kept"}, updated)
        self.assertEqual([p["expected_ground"] for p in reference["points"]], [5.0, 7.0])
        self.assertEqual(reference["points"][0]["expected_water"], 0.25)
        self.assertNotIn("expected_water", reference["points"][1])
        self.assertEqual(reference["other"], "kept")
        self.assertEqual(baseline[0]["expected_ground"], 4.0)

    def test_independent_triangle_plane_for_both_sides_of_diagonal(self):
        rr, cc = np.mgrid[0:2, 0:2]
        heights = (1.0 + 2.0 * rr + 3.0 * cc).astype(np.float64)
        self.assertAlmostEqual(barycentric_height_independent(heights, 3.0, 12279.0), 3.5)
        self.assertAlmostEqual(barycentric_height_independent(heights, 4.5, 12279.0), 4.25)
        self.assertAlmostEqual(barycentric_height_independent(heights, 1.5, 12280.5), 2.25)


if __name__ == "__main__":
    unittest.main(verbosity=2)
