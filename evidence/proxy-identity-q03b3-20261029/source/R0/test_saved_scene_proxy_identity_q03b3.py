"""Tests against pre-code complete literal expectations; no historical arrays."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("proxy_identity", os.environ["Q03B3_MODULE"])
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
ORACLE_PATH = Path(os.environ["Q03B3_ORACLE"])
ORACLE_SHA = "17667706d7bd0faf641f5e2e53cb2ed15bf620f75a483598d3cd6b8c32343f8c"
CONTRACT_PATH = Path(os.environ["Q03B3_CONTRACT"])
assert hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest() == "8173cc1e756d74c69bd57e4dfd4b706c38cc26dfbbb289d79ce611bc83b77ec3"
assert hashlib.sha256(ORACLE_PATH.read_bytes()).hexdigest() == ORACLE_SHA
O = json.loads(ORACLE_PATH.read_bytes())
ROOT = Path(os.environ["Q03B3_TEST_ROOT"]).resolve()
ROOT.mkdir(parents=True, exist_ok=True)


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.fixture = deepcopy(O)
        self.directory = Path(tempfile.mkdtemp(dir=ROOT)).resolve()

    def tearDown(self):
        if ROOT not in self.directory.parents:
            raise AssertionError("cleanup outside fixture root")
        shutil.rmtree(self.directory)

    def call(self):
        f = self.fixture
        return M.validate_face_routes(f["sections"], f["routes"], f["faces"], f["expected"])

    def rejected(self, case):
        before = deepcopy(self.fixture)
        with self.assertRaises(M.IdentityError) as cm:
            self.call()
        self.assertEqual(cm.exception.code, O["cases"][case])
        self.assertEqual(before, self.fixture, "failed validation mutated input")

    def test_complete_positive_and_independent_expected(self):
        loaded = M.load_fixture(ORACLE_PATH, ORACLE_SHA)
        self.assertEqual(loaded, O)
        result = self.call()
        self.assertEqual(result["status"], "FIXTURE_FACE_ROUTE_IDENTITY_ONLY")
        self.assertEqual(result["faces"], O["expected"]["faces"])
        self.assertEqual(result["models"], O["expected"]["models"])
        self.assertEqual(result["routes"], O["expected"]["routes"])
        self.assertEqual(result["limitations"], O["limitations"])
        self.assertEqual(len(result["faces"]), 5)
        self.assertEqual(result["faces"][2], result["faces"][3])
        # Distinct LODs may own the same face number. Numeric indices are not positions.
        self.assertEqual([result["faces"][i]["lod"] for i in (0, 1)], [7, 19])
        self.assertEqual(self.fixture, O)
        result["faces"][0]["face"] = 999
        result["routes"][0]["slots"][0][0] = 999
        self.assertEqual(self.fixture, O, "returned object aliases source")

    def test_canonical_proxy_name_equivalence_without_suffix_repair(self):
        self.fixture["sections"][0]["proxies"][0]["model"] = "/TEST\\CHILD.P3D/"
        self.assertEqual(self.call()["routes"], O["expected"]["routes"])
        self.fixture["sections"][0]["proxies"][0]["model"] = "test/child"
        self.rejected("no_suffix")

    def test_route_counterexamples(self):
        cases = [
            "wrong_literal_proxy_child", "wrong_root", "discontinuous", "ordinal_outside",
            "ordinal_bool", "unknown_child", "wrong_final_source", "cycle", "empty_slots",
            "unreferenced_bad_route", "reordered_routes",
        ]
        for case in cases:
            self.fixture = deepcopy(O)
            s, r = self.fixture["sections"], self.fixture["routes"]
            if case == "wrong_literal_proxy_child":
                s[0]["proxies"][0]["model"] = "test/unrelated.p3d"
            elif case == "wrong_root":
                r[0]["root_model"] = 3
            elif case == "discontinuous":
                r[1]["slots"][1][0] = 3
            elif case == "ordinal_outside":
                r[0]["slots"][0][1] = 2
            elif case == "ordinal_bool":
                r[0]["slots"][0][1] = False
            elif case == "unknown_child":
                s[0]["proxies"][0]["model"] = "test/missing.p3d"
            elif case == "wrong_final_source":
                r[0]["source_model"] = 5
            elif case == "cycle":
                s[0]["proxies"][0]["model"] = "test/root.p3d"
            elif case == "empty_slots":
                r[0]["slots"] = []
            elif case == "unreferenced_bad_route":
                r[2]["source_model"] = 2
            elif case == "reordered_routes":
                r[0], r[1] = r[1], r[0]
            with self.subTest(case=case):
                self.rejected(case)

    def test_faces_and_complete_multiset_counterexamples(self):
        for case in ["missing_route", "root_face_proxy", "wrong_face_root", "section_outside",
                     "face_outside", "lod_outside", "omitted_face", "compensated_omission"]:
            self.fixture = deepcopy(O)
            f = self.fixture["faces"]
            if case == "missing_route":
                f[2]["proxy"] = 3
            elif case == "root_face_proxy":
                f[0]["proxy"] = 0
            elif case == "wrong_face_root":
                f[2]["model"] = 3
            elif case == "section_outside":
                f[2]["section"] = 0  # Actual index is 9, not array position 0.
            elif case == "face_outside":
                f[2]["face"] = 3
            elif case == "lod_outside":
                f[2]["lod"] = 0  # Actual LOD index is 7.
            elif case == "omitted_face":
                f.pop()
            elif case == "compensated_omission":
                f.pop(); f.append(deepcopy(f[0]))
            with self.subTest(case=case):
                self.rejected(case)

    def test_names_expected_types_and_nested_unknown_keys(self):
        self.fixture["sections"][2]["name"] = "TEST\\CHILD.P3D"
        self.rejected("canonical_collision")
        for name in ["test/../child.p3d", "C:/child.p3d", "test//child.p3d", "test/\x00child.p3d", "test/ñ.p3d"]:
            self.fixture = deepcopy(O)
            self.fixture["sections"][0]["proxies"][0]["model"] = name
            with self.subTest(name=name):
                self.rejected("name_traversal")
        self.fixture = deepcopy(O)
        self.fixture["expected"]["faces"][0]["face"] = True
        self.rejected("expected_bool")
        for depth in ("model", "lod", "section", "proxy", "route", "face", "expected", "expected_route"):
            self.fixture = deepcopy(O)
            f = self.fixture
            targets = {"model": f["sections"][0], "lod": f["sections"][0]["lods"][0],
                       "section": f["sections"][0]["lods"][0]["sections"][0],
                       "proxy": f["sections"][0]["proxies"][0], "route": f["routes"][0],
                       "face": f["faces"][0], "expected": f["expected"],
                       "expected_route": f["expected"]["routes"][0]}
            targets[depth]["unexpected"] = None
            with self.subTest(depth=depth):
                self.rejected("unknown_key")

    def test_literal_face_reordering_preserves_multiset_and_input_order(self):
        self.fixture["faces"].reverse()
        self.assertEqual(self.call()["faces"], self.fixture["faces"])

    def test_fixture_loader_limit_hash_duplicates_and_nonfinite(self):
        p = self.directory / "fixture.json"
        p.write_bytes(b" " * 1048577)
        with patch.object(M.json, "loads", side_effect=AssertionError("parser reached")) as spy:
            with self.assertRaises(M.IdentityError) as cm:
                M.load_fixture(p, "0" * 64)
            self.assertEqual(cm.exception.code, O["cases"]["oversized_json"])
            spy.assert_not_called()
        for case, data in [("duplicate_json_key", b'{"x":1,"x":2}'),
                           ("json_nonfinite", b'{"x":NaN}'),
                           ("json_nonfinite", b'{"x":1e999}'),
                           ("json_nonfinite", b'{"x":-Infinity}')]:
            p.write_bytes(data)
            with self.subTest(case=case), self.assertRaises(M.IdentityError) as cm:
                M.load_fixture(p, hashlib.sha256(data).hexdigest())
            self.assertEqual(cm.exception.code, O["cases"][case])
        with self.assertRaises(M.IdentityError) as cm:
            M.load_fixture(ORACLE_PATH, "0" * 64)
        self.assertEqual(cm.exception.code, O["cases"]["fixture_sha"])

    def test_programming_exception_not_data_rejection(self):
        with patch.object(M, "_validate", side_effect=RuntimeError("test sentinel")):
            self.rejected("unexpected_programming")

    def test_caps_and_representations(self):
        # Test the closed pure API caps; size gates run before traversal.
        for key, maximum in [("sections", 64), ("routes", 64), ("faces", 512)]:
            self.fixture = deepcopy(O)
            self.fixture[key] = [self.fixture[key][0]] * (maximum + 1)
            with self.subTest(key=key), self.assertRaises(M.IdentityError) as cm:
                self.call()
            self.assertEqual(cm.exception.code, "SCHEMA")
        for key in ("center",):
            self.fixture = deepcopy(O)
            self.fixture["sections"][0][key][0] = True
            with self.assertRaises(M.IdentityError) as cm:
                self.call()
            self.assertEqual(cm.exception.code, "SCHEMA")


if __name__ == "__main__":
    unittest.main(verbosity=2)
