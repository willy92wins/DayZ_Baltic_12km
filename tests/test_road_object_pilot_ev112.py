import copy
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHOR_PATH = ROOT / "tools" / "quality" / "author_road_object_pilot_ev112.py"
VERIFY_PATH = ROOT / "tools" / "quality" / "verify_road_object_pilot_ev112.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


author = _load("author_road_object_pilot_ev112", AUTHOR_PATH)
consumer = _load("verify_road_object_pilot_ev112", VERIFY_PATH)
TERM_ID = 999
NAMES = [b"dz\\structures\\roads\\parts\\asf1_25.p3d", b"dz\\structures\\roads\\parts\\asf2_25.p3d", b"dz\\structures\\roads\\parts\\asf1_10 100.p3d"]
MATRICES = [[1.0, -0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 10.0, 200.0, 20.0], [0.0, 0.0, -1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 30.0, 200.0, 40.0], [1.0, 0.0, 0.0, 0.0, 0.5, 0.8660253882408142, 0.0, -0.8660253882408142, 0.5, 50.0, 200.0, 60.0]]
OBJECTS_START = 65
GOLDEN_SOURCE_HEX = ("30575a44" "01000000" "01000000" "01000000" "01000000" "0000a040" "0000803f" "0000" "02000000" "04000000" "6d617430" "03000000" "78797a" "00000000" "04000000" "6d617431" "00000000" "0000803f" "00000000" "00000000" "00000000" "0000803f" "00000000" "00000000" "00000000" "0000803f" "00002041" "00004843" "00000000" "0a000000" "20000000" "647a5c" "73747275637475726573" "5c" "726f616473" "5c" "6578697374696e672e703364" "0000803f" "00000000" "00000000" "00000000" "0000803f" "00000000" "00000000" "00000000" "0000803f" "0000a041" "00004843" "00000000" "14000000" "20000000" "647a5c" "73747275637475726573" "5c" "726f616473" "5c" "6578697374696e672e703364" "3412c07f" "7856c0ff" "0100807f" "01000000" "00000000" "00000000" "00000000" "0000803f" "00000000" "00000000" "00000000" "00000000" "e7030000" "00000000")
GOLDEN_SOURCE = bytes.fromhex(GOLDEN_SOURCE_HEX)


def record(ident, raw, matrix=None):
    m = matrix if matrix is not None else [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, float(ident), 200.0, 0.0]
    return struct.pack("<12f", *m) + struct.pack("<II", ident, len(raw)) + raw


def fixture_candidate(source):
    return source[:-56] + b"".join(record(21 + i, NAMES[i], MATRICES[i]) for i in range(3)) + source[-56:]


def make_contract(source, ids=(21, 22, 23), max_id=20, count=2, pins=None, matrices=None, names=None, term=None):
    names = NAMES if names is None else names
    matrices = MATRICES if matrices is None else matrices
    term_bytes = source[-56:] if term is None else term
    return {"schema": "road-object-pilot.v1", "source_path": "source.wrp", "source_sha256": hashlib.sha256(source).hexdigest(), "source_bytes": len(source), "object_count": count, "max_id": max_id, "prefix_bytes": len(source) - 56, "prefix_sha256": hashlib.sha256(source[:-56]).hexdigest(), "terminator_hex": term_bytes.hex(), "objects": [{"name": names[i].decode("ascii"), "raw_name_hex": names[i].hex(), "id": ids[i], "matrix12": list(matrices[i])} for i in range(3)], "pins": {} if pins is None else pins, "status": "SOURCE_RECIPE_ONLY"}


def contract_for_bytes(data):
    c = make_contract(data)
    c["object_count"] = 0
    c["max_id"] = 0
    c["objects"] = [{"name": NAMES[i].decode("ascii"), "raw_name_hex": NAMES[i].hex(), "id": 1 + i, "matrix12": list(MATRICES[i])} for i in range(3)]
    return c


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.source = GOLDEN_SOURCE
        self.contract = make_contract(self.source)
        self.candidate = author.author_bytes(self.source, self.contract)
        self.fixture_candidate = fixture_candidate(self.source)

    def test_golden_fixture_is_handwritten_hex_with_two_materials(self):
        self.assertEqual(len(GOLDEN_SOURCE), 297)
        magic, tx, tz, nx, nz, cell = struct.unpack_from("<4s4If", GOLDEN_SOURCE, 0)
        self.assertEqual((magic, tx, tz, nx, nz, cell), (b"0WZD", 1, 1, 1, 1, 5.0))
        pos = 24 + nx * nz * 4 + tx * tz * 2
        count = struct.unpack_from("<I", GOLDEN_SOURCE, pos)[0]
        pos += 4
        self.assertEqual(count, 2)
        materials = []
        for _ in range(count):
            strings = []
            while True:
                size = struct.unpack_from("<I", GOLDEN_SOURCE, pos)[0]
                pos += 4
                if size == 0:
                    break
                strings.append(GOLDEN_SOURCE[pos:pos + size])
                pos += size
            materials.append(strings)
        self.assertEqual(materials, [[b"mat0", b"xyz"], [b"mat1"]])
        self.assertEqual(pos, OBJECTS_START)
        first_id, first_len = struct.unpack_from("<II", GOLDEN_SOURCE, OBJECTS_START + 48)
        self.assertEqual((first_id, first_len), (10, 32))

    def test_fixture_candidate_decoded_literally(self):
        cand = self.fixture_candidate
        off = len(self.source) - 56
        for i in range(3):
            values = struct.unpack_from("<12f", cand, off)
            self.assertEqual(list(values), MATRICES[i])
            ident, length = struct.unpack_from("<II", cand, off + 48)
            self.assertEqual(ident, 21 + i)
            self.assertEqual(length, len(NAMES[i]))
            self.assertEqual(cand[off + 56:off + 56 + length], NAMES[i])
            off += 56 + length
        self.assertEqual(cand[off:off + 56], self.source[-56:])
        term_id, term_len = struct.unpack_from("<II", cand, off + 48)
        self.assertEqual((term_id, term_len), (TERM_ID, 0))
        self.assertEqual(cand[off:off + 4], bytes.fromhex("3412c07f"))

    def test_positive_candidate_structure(self):
        self.assertTrue(self.candidate.startswith(self.source[:-56]))
        self.assertTrue(self.candidate.endswith(self.source[-56:]))
        self.assertEqual(len(self.candidate), len(self.source) + sum(56 + len(n) for n in NAMES))
        self.assertEqual(self.candidate, self.fixture_candidate)

    def test_positive_verify_report_fixture_candidate(self):
        report = consumer.verify_bytes(self.source, self.fixture_candidate, self.contract)
        self.assertTrue(report["ok"])
        self.assertEqual(report["status"], "CANDIDATE_SOURCE_OFFLINE")
        self.assertEqual(report["candidate_object_count"], 5)
        self.assertEqual(report["added_ids"], [21, 22, 23])

    def test_signed_zero_preserved_bit_exact(self):
        off = len(self.source) - 56 + 4
        self.assertEqual(self.fixture_candidate[off:off + 4], struct.pack("<f", -0.0))
        self.assertEqual(self.candidate[off:off + 4], struct.pack("<f", -0.0))

    def test_verify_rejects_signed_zero_flip(self):
        bad = bytearray(self.fixture_candidate)
        off = len(self.source) - 56 + 4
        bad[off:off + 4] = struct.pack("<f", 0.0)
        with self.assertRaises(ValueError):
            consumer.verify_bytes(self.source, bytes(bad), self.contract)

    def test_int_matrix_values_accepted_when_exact(self):
        c = copy.deepcopy(self.contract)
        c["objects"][0]["matrix12"][9] = 100
        c["objects"][0]["matrix12"][10] = 200
        c["objects"][0]["matrix12"][11] = 300
        cand = author.author_bytes(self.source, c)
        off = len(self.source) - 56 + 36
        self.assertEqual(cand[off:off + 12], struct.pack("<3f", 100.0, 200.0, 300.0))
        report = consumer.verify_bytes(self.source, cand, c)
        self.assertTrue(report["ok"])

    def test_nonexact_f32_rejected_both_validators(self):
        c = copy.deepcopy(self.contract)
        c["objects"][2]["matrix12"][5] = 0.8660254
        c["objects"][2]["matrix12"][7] = -0.8660254
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)
        with self.assertRaises(ValueError):
            consumer.verify_bytes(self.source, self.fixture_candidate, c)

    def test_parse_int_rejects_json_minus_zero_but_not_integers(self):
        self.assertEqual(author._parse_int("100"), 100)
        self.assertEqual(consumer._parse_int("300"), 300)
        with self.assertRaises(ValueError):
            author._parse_int("-0")
        with self.assertRaises(ValueError):
            consumer._parse_int("-0")
        text = json.dumps(self.contract).replace("-0.0", "-0", 1)
        self.assertIn("-0,", text + ",")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "contract.json"
            path.write_text(text, encoding="utf-8")
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):
                author._load_contract(path, sha)
            with self.assertRaises(ValueError):
                consumer._load_contract(path, sha)

    def test_verify_rejects_prefix_mutation(self):
        bad = bytearray(self.fixture_candidate)
        bad[30] ^= 1
        with self.assertRaises(ValueError):
            consumer.verify_bytes(self.source, bytes(bad), self.contract)

    def test_verify_rejects_source_changed_after_authoring(self):
        changed = bytearray(self.source)
        changed[28] ^= 1
        with self.assertRaises(ValueError):
            consumer.verify_bytes(bytes(changed), self.candidate, self.contract)

    def test_verify_rejects_name_mutation(self):
        bad = bytearray(self.fixture_candidate)
        bad[-60] ^= 1
        with self.assertRaises(ValueError):
            consumer.verify_bytes(self.source, bytes(bad), self.contract)

    def test_verify_rejects_terminator_mutation(self):
        bad = bytearray(self.fixture_candidate)
        bad[-10] ^= 1
        with self.assertRaises(ValueError):
            consumer.verify_bytes(self.source, bytes(bad), self.contract)

    def test_verify_rejects_trailing_bytes(self):
        with self.assertRaises(ValueError):
            consumer.verify_bytes(self.source, self.fixture_candidate + b"x", self.contract)

    def test_verify_rejects_truncation_mutants(self):
        for cut in (10, 30, len(self.source) - 56 + 10, len(self.fixture_candidate) - 1):
            with self.assertRaises(ValueError):
                consumer.verify_bytes(self.source, self.fixture_candidate[:cut], self.contract)

    def test_author_rejects_source_hash_mismatch(self):
        c = copy.deepcopy(self.contract)
        c["source_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_author_rejects_mutated_source(self):
        bad = bytearray(self.source)
        bad[28] ^= 1
        with self.assertRaises(ValueError):
            author.author_bytes(bytes(bad), self.contract)

    def test_author_rejects_unknown_key(self):
        c = copy.deepcopy(self.contract)
        c["extra"] = 1
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_author_rejects_missing_key(self):
        c = copy.deepcopy(self.contract)
        del c["pins"]
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_author_rejects_wrong_status(self):
        c = copy.deepcopy(self.contract)
        c["status"] = "OTHER"
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_author_rejects_bool_id(self):
        c = copy.deepcopy(self.contract)
        c["objects"][0]["id"] = True
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_author_rejects_duplicate_contract_ids(self):
        c = copy.deepcopy(self.contract)
        c["objects"][1]["id"] = 21
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_author_rejects_nonsequential_id(self):
        c = copy.deepcopy(self.contract)
        c["objects"][2]["id"] = 99
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_author_rejects_overflow(self):
        c = copy.deepcopy(self.contract)
        c["max_id"] = 4294967295
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_author_rejects_saturated_overflow(self):
        c = copy.deepcopy(self.contract)
        c["max_id"] = 4294967294
        c["objects"][0]["id"] = 4294967295
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_source_with_uintmax_existing_rejects_next_id(self):
        src = bytearray(self.source)
        struct.pack_into("<I", src, OBJECTS_START + 48, 4294967295)
        data = bytes(src)
        c = make_contract(data, ids=(1, 2, 3), max_id=4294967295, count=2)
        with self.assertRaises(ValueError):
            author.author_bytes(data, c)
        with self.assertRaises(ValueError):
            consumer.verify_bytes(data, fixture_candidate(data), c)

    def test_author_rejects_nul_name(self):
        bad = b"dz\\structures\\roads\\parts\\bad\x00.p3d"
        c = make_contract(self.source, names=[bad, NAMES[1], NAMES[2]])
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_author_rejects_parent_name(self):
        bad = b"dz\\structures\\roads\\..\\evil.p3d"
        c = make_contract(self.source, names=[bad, NAMES[1], NAMES[2]])
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_author_rejects_absolute_name(self):
        bad = b"\\evil.p3d"
        c = make_contract(self.source, names=[bad, NAMES[1], NAMES[2]])
        c["objects"][0]["name"] = bad.decode("ascii")
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_rejects_slash_name_both(self):
        bad = b"dz/structures/roads/parts/evil.p3d"
        c = make_contract(self.source, names=[bad, NAMES[1], NAMES[2]])
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)
        with self.assertRaises(ValueError):
            consumer.verify_bytes(self.source, self.fixture_candidate, c)

    def test_rejects_wrong_prefix_name_both(self):
        bad = b"dz\\structures\\other\\evil.p3d"
        c = make_contract(self.source, names=[bad, NAMES[1], NAMES[2]])
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)
        with self.assertRaises(ValueError):
            consumer.verify_bytes(self.source, self.fixture_candidate, c)

    def test_author_rejects_name_raw_mismatch(self):
        c = copy.deepcopy(self.contract)
        c["objects"][0]["name"] = "dz\\structures\\roads\\parts\\other.p3d"
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_author_rejects_matrix_length(self):
        c = copy.deepcopy(self.contract)
        c["objects"][0]["matrix12"] = [0.0] * 11
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_author_rejects_matrix_nan(self):
        c = copy.deepcopy(self.contract)
        c["objects"][0]["matrix12"][0] = float("nan")
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_author_rejects_duplicate_source_ids(self):
        src = bytearray(self.source)
        struct.pack_into("<I", src, OBJECTS_START + 88 + 48, 10)
        data = bytes(src)
        c = make_contract(data, count=2, max_id=10, ids=(11, 12, 13))
        with self.assertRaises(ValueError):
            author.author_bytes(data, c)

    def test_author_rejects_false_terminator_length_zero_midstream(self):
        src = bytearray(self.source)
        struct.pack_into("<I", src, OBJECTS_START + 52, 0)
        data = bytes(src)
        with self.assertRaises(ValueError):
            author.author_bytes(data, contract_for_bytes(data))
        with self.assertRaises(ValueError):
            consumer.verify_bytes(data, fixture_candidate(data), contract_for_bytes(data))

    def test_author_rejects_count_mismatch(self):
        c = copy.deepcopy(self.contract)
        c["object_count"] = 3
        with self.assertRaises(ValueError):
            author.author_bytes(self.source, c)

    def test_author_rejects_bad_magic_with_fresh_hashes(self):
        src = bytearray(self.source)
        src[0:4] = b"XXXX"
        data = bytes(src)
        with self.assertRaises(ValueError):
            author.author_bytes(data, contract_for_bytes(data))

    def test_author_rejects_zero_dimension(self):
        src = bytearray(self.source)
        struct.pack_into("<I", src, 16, 0)
        data = bytes(src)
        with self.assertRaises(ValueError):
            author.author_bytes(data, contract_for_bytes(data))

    def test_author_rejects_bad_cell(self):
        src = bytearray(self.source)
        struct.pack_into("<f", src, 20, -1.0)
        data = bytes(src)
        with self.assertRaises(ValueError):
            author.author_bytes(data, contract_for_bytes(data))

    def test_author_rejects_material_count_out_of_bounds(self):
        src = bytearray(self.source)
        struct.pack_into("<I", src, 30, 4294967295)
        data = bytes(src)
        with self.assertRaises(ValueError):
            author.author_bytes(data, contract_for_bytes(data))

    def test_author_rejects_source_trailing_after_terminator(self):
        data = self.source + b"x"
        with self.assertRaises(ValueError):
            author.author_bytes(data, contract_for_bytes(data))

    def test_author_rejects_terminator_id_collision(self):
        src = bytearray(self.source)
        struct.pack_into("<I", src, len(self.source) - 56 + 48, 21)
        data = bytes(src)
        c = make_contract(data)
        with self.assertRaises(ValueError):
            author.author_bytes(data, c)

    def test_resolve_relative_only_contract_dir(self):
        base = Path("contract_base")
        self.assertEqual(author._resolve("source.wrp", base), base / "source.wrp")
        self.assertEqual(consumer._resolve("source.wrp", base), base / "source.wrp")

    def test_modules_do_not_import_each_other_and_consumer_uses_bytesio(self):
        author_text = AUTHOR_PATH.read_text(encoding="utf-8")
        verify_text = VERIFY_PATH.read_text(encoding="utf-8")
        self.assertNotIn("verify_road_object_pilot", author_text)
        self.assertNotIn("author_road_object_pilot", verify_text)
        self.assertIn("io.BytesIO", verify_text)
        self.assertIn("_CursorReader", verify_text)
        self.assertNotIn("_parse_prefix", verify_text)
        self.assertNotIn("_parse_census", verify_text)


class CliTests(unittest.TestCase):
    def _setup_cli(self, td):
        root = Path(td)
        src_path = root / "source.wrp"
        src_path.write_bytes(GOLDEN_SOURCE)
        recipe = root / "recipe.txt"
        recipe.write_bytes(b"recipe-v1")
        src = src_path.read_bytes()
        pins = {str(src_path): hashlib.sha256(src).hexdigest(), str(recipe): hashlib.sha256(b"recipe-v1").hexdigest()}
        contract = make_contract(src, pins=pins)
        contract["source_path"] = str(src_path)
        cpath = root / "contract.json"
        cpath.write_text(json.dumps(contract), encoding="utf-8")
        sha = hashlib.sha256(cpath.read_bytes()).hexdigest()
        return root, src_path, cpath, sha, contract

    def _run(self, *args):
        return subprocess.run([sys.executable, *args], capture_output=True, text=True, timeout=30)

    def test_cli_author_and_consumer(self):
        with tempfile.TemporaryDirectory() as td:
            root, src_path, cpath, sha, contract = self._setup_cli(td)
            out = root / "out"
            res = self._run(str(AUTHOR_PATH), "--contract", str(cpath), "--contract-sha256", sha, "--output", str(out))
            self.assertEqual(res.returncode, 0, res.stderr)
            report = json.loads(res.stdout)
            self.assertEqual(report["status"], "CANDIDATE_SOURCE_OFFLINE")
            self.assertTrue((out / "candidate.wrp").is_file())
            self.assertFalse((out / "pending.wrp").exists())
            res2 = self._run(str(VERIFY_PATH), "--contract", str(cpath), "--contract-sha256", sha, "--candidate", str(out / "candidate.wrp"))
            self.assertEqual(res2.returncode, 0, res2.stderr)
            self.assertTrue(json.loads(res2.stdout)["ok"])

    def test_cli_author_rejects_existing_output(self):
        with tempfile.TemporaryDirectory() as td:
            root, src_path, cpath, sha, contract = self._setup_cli(td)
            out = root / "out"
            out.mkdir()
            res = self._run(str(AUTHOR_PATH), "--contract", str(cpath), "--contract-sha256", sha, "--output", str(out))
            self.assertNotEqual(res.returncode, 0)
            self.assertFalse((out / "candidate.wrp").exists())

    def test_cli_author_rejects_contract_sha(self):
        with tempfile.TemporaryDirectory() as td:
            root, src_path, cpath, sha, contract = self._setup_cli(td)
            res = self._run(str(AUTHOR_PATH), "--contract", str(cpath), "--contract-sha256", "0" * 64, "--output", str(root / "out"))
            self.assertNotEqual(res.returncode, 0)

    def test_cli_author_rejects_pin_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root, src_path, cpath, sha, contract = self._setup_cli(td)
            (root / "recipe.txt").write_bytes(b"changed")
            res = self._run(str(AUTHOR_PATH), "--contract", str(cpath), "--contract-sha256", sha, "--output", str(root / "out"))
            self.assertNotEqual(res.returncode, 0)

    def test_cli_pin_checked_before_wrp_parse(self):
        with tempfile.TemporaryDirectory() as td:
            root, src_path, cpath, sha, contract = self._setup_cli(td)
            bad = bytearray(src_path.read_bytes())
            bad[0:4] = b"XXXX"
            src_path.write_bytes(bytes(bad))
            res = self._run(str(AUTHOR_PATH), "--contract", str(cpath), "--contract-sha256", sha, "--output", str(root / "out"))
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("pin", res.stderr.lower())

    def test_cli_rejects_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as td:
            root, src_path, cpath, sha, contract = self._setup_cli(td)
            text = cpath.read_text(encoding="utf-8")
            dup = '{"schema":"road-object-pilot.v1",' + text[1:]
            cpath.write_text(dup, encoding="utf-8")
            sha2 = hashlib.sha256(cpath.read_bytes()).hexdigest()
            res = self._run(str(AUTHOR_PATH), "--contract", str(cpath), "--contract-sha256", sha2, "--output", str(root / "out"))
            self.assertNotEqual(res.returncode, 0)

    def test_cli_consumer_rejects_corrupt_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root, src_path, cpath, sha, contract = self._setup_cli(td)
            out = root / "out"
            res = self._run(str(AUTHOR_PATH), "--contract", str(cpath), "--contract-sha256", sha, "--output", str(out))
            self.assertEqual(res.returncode, 0, res.stderr)
            cand = out / "candidate.wrp"
            bad = bytearray(cand.read_bytes())
            bad[40] ^= 1
            cand.write_bytes(bytes(bad))
            res2 = self._run(str(VERIFY_PATH), "--contract", str(cpath), "--contract-sha256", sha, "--candidate", str(cand))
            self.assertNotEqual(res2.returncode, 0)
            diag = json.loads(res2.stderr)
            self.assertFalse(diag["ok"])

    def test_cli_consumer_rejects_truncated_candidate_before_read(self):
        with tempfile.TemporaryDirectory() as td:
            root, src_path, cpath, sha, contract = self._setup_cli(td)
            cand = root / "candidate.wrp"
            cand.write_bytes(fixture_candidate(GOLDEN_SOURCE)[:-1])
            res = self._run(str(VERIFY_PATH), "--contract", str(cpath), "--contract-sha256", sha, "--candidate", str(cand))
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("candidate size mismatch before read", res.stderr)


if __name__ == "__main__":
    unittest.main()
