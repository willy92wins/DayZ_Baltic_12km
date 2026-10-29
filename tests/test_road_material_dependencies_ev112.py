"""Synthetic-only tests for EV112 road material dependencies.
No real/vanilla files are loaded; modules are loaded by path.
"""
import copy
import hashlib
import importlib.util
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod); return mod

prod = load("road_material_dependencies_ev112", "tools/quality/road_material_dependencies_ev112.py")
cons = load("verify_road_material_dependencies_ev112", "tools/quality/verify_road_material_dependencies_ev112.py")

TEX1 = "dz\\structures\\roads\\parts\\data\\asf1_dashedline_nohq.paa"
TEX2 = "dz\\structures\\roads\\parts\\data\\asf1_dashedline_sm.paa"
TEX3 = "dz\\structures\\roads\\parts\\data\\asf2_dashedline_nohq.paa"
TEX4 = "dz\\structures\\roads\\parts\\data\\asf2_dashedline_sm.paa"

def make_text(specular="60", tex_a=TEX1, tex_b=TEX2, newline=True, sep="\n"):
    def vec(name, vals):
        return f"{name}[]={{{','.join(vals)}}};"
    def stage(name, tex):
        lines = [f'class {name}{{', f' texture="{tex}";', ' uvSource="tex";', " class uvTransform{", "  " + vec("aside", ["1", "0", "0"]), "  " + vec("up", ["0", "1", "0"]), "  " + vec("dir", ["0", "0", "1"]), "  " + vec("pos", ["0", "0", "0"]), " }; ", "};"]
        return sep.join(lines)
    lines = [vec("ambient", ["1", "1", "1", "1"]), vec("diffuse", ["1", "1", "1", "1"]), vec("forcedDiffuse", ["0", "0", "0", "0"]), vec("emmisive", ["0", "0", "0", "0"]), vec("specular", ["0.5", "0.5", "0.5", "1"]), f"specularPower={specular};", 'PixelShaderID="Normal";', 'VertexShaderID="Basic";', stage("Stage1", tex_a), stage("Stage2", tex_b)]
    text = sep.join(lines)
    if newline:
        text += sep if sep in ("\n",) else "\n"
    return text.encode("ascii")

def sha(b):
    return hashlib.sha256(b).hexdigest()

def build_pbo(entries):
    # entries: list of (name, mime, payload)
    out = bytearray(); offset_placeholder = []
    for name, mime, payload in entries:
        out += name.encode() + b"\0" + struct.pack("<5I", mime, 0, 0, 0, len(payload))
    out += b"\0" + struct.pack("<5I", 0, 0, 0, 0, 0)
    payload_start = len(out)
    for name, mime, payload in entries:
        out += payload
    return bytes(out), payload_start

class LexerParserTests(unittest.TestCase):
    def test_whitespace_crlf_eof(self):
        data = make_text(sep="\r\n")
        p = prod.parse_rvmat(data)
        self.assertEqual(p["inventory"], {"assignments": 20, "classes": 4, "strings": 6, "vec3": 8, "vec4": 5, "scalar": 1, "semicolons": 24})
        self.assertTrue(p["eof_newline"])
        p2 = prod.parse_rvmat(make_text(newline=False))
        self.assertFalse(p2["eof_newline"]); self.assertEqual(p2["eof_state"], "no_newline")
        spaced = make_text().replace(b";", b"  ;  ")
        self.assertEqual(prod.parse_rvmat(spaced)["inventory"]["assignments"], 20)
    def test_literal_backslash_paths_preserved(self):
        data = make_text(tex_a=r"a\nb\rc\td.paa", tex_b=TEX2)
        p = prod.parse_rvmat(data)
        ref = p["texture_refs"][0]
        self.assertEqual(ref["raw_virtual_path"], r"a\nb\rc\td.paa")
        self.assertIn("\\n", ref["raw_virtual_path"])  # backslash+n, not newline
        self.assertNotIn("\n", ref["raw_virtual_path"])
    def test_unknown_comment_macro(self):
        self.assertEqual(prod.parse_rvmat(make_text())["inventory"]["assignments"], 20)
        for bad in (make_text() + b"// comment\n", make_text() + b"#define X 1\n", b"/*x*/" + make_text()):
            with self.assertRaisesRegex(prod.RvmatError, "unsupported_syntax"):
                prod.parse_rvmat(bad)
    def test_bad_numbers(self):
        self.assertEqual(prod.parse_rvmat(make_text())["inventory"]["assignments"], 20)
        for bad in (b"specularPower=1.;", b"specularPower=.5;", b"specularPower=1e5;", b"specularPower=-1;", b"specularPower=+1;"):
            data = make_text().replace(b"specularPower=60;", bad)
            with self.assertRaisesRegex(prod.RvmatError, "bad_number|unsupported_syntax"):
                prod.parse_rvmat(data)
    def test_duplicate_and_unknown_and_vectorwrong(self):
        self.assertEqual(prod.parse_rvmat(make_text())["inventory"]["assignments"], 20)
        dup = make_text().replace(b"diffuse[]={1,1,1,1};", b"diffuse[]={1,1,1,1};diffuse[]={1,1,1,1};")
        with self.assertRaisesRegex(prod.RvmatError, "duplicate_assignment"):
            prod.parse_rvmat(dup)
        unk = make_text().replace(b"PixelShaderID", b"UnknownID")
        with self.assertRaisesRegex(prod.RvmatError, "unknown_assignment"):
            prod.parse_rvmat(unk)
        wrong = make_text().replace(b"ambient[]={1,1,1,1}", b"ambient[]={1,1,1}")
        with self.assertRaisesRegex(prod.RvmatError, "wrong_type"):
            prod.parse_rvmat(wrong)
        extra = make_text() + b"extra[]={1};"
        with self.assertRaisesRegex(prod.RvmatError, "unknown_assignment"):
            prod.parse_rvmat(extra)
    def test_consumer_declarative_matches_producer(self):
        data = make_text(specular="130", tex_a=TEX3, tex_b=TEX4)
        p = prod.parse_rvmat(data); c = cons.declarative_parse(data)
        # Build saved-shaped dict from producer parse.
        saved = {"assignments": p["assignments"], "classes": p["classes"], "texture_refs": p["texture_refs"], "tokens": p["tokens"], "inventory": p["inventory"], "semicolons": p["semicolons"], "eof_newline": p["eof_newline"], "eof_state": p["eof_state"]}
        self.assertTrue(cons.compare_parsed(c, saved))
    def test_consumer_rejects_missing_stage_unchanged_text(self):
        data = make_text(); p = prod.parse_rvmat(data)
        saved = {"assignments": [a for a in p["assignments"] if not a["path"].startswith("Stage2")], "classes": [c for c in p["classes"] if not c.startswith("Stage2")], "texture_refs": p["texture_refs"][:1], "tokens": p["tokens"], "inventory": p["inventory"], "semicolons": p["semicolons"], "eof_newline": p["eof_newline"], "eof_state": p["eof_state"]}
        c = cons.declarative_parse(data)
        with self.assertRaisesRegex(ValueError, "parsed_mismatch"):
            cons.compare_parsed(c, saved)
    def test_consumer_rejects_tampered_ignored_shifted_duplicate(self):
        data = make_text(); p = prod.parse_rvmat(data); c = cons.declarative_parse(data)
        base = {"assignments": copy.deepcopy(p["assignments"]), "classes": p["classes"], "texture_refs": p["texture_refs"], "tokens": p["tokens"], "inventory": p["inventory"], "semicolons": p["semicolons"], "eof_newline": p["eof_newline"], "eof_state": p["eof_state"]}
        tampered = copy.deepcopy(base); tampered["assignments"][0]["value"] = ["9", "1", "1", "1"]; tampered["assignments"][0]["raw_lexemes"] = ["9", "1", "1", "1"]
        with self.assertRaisesRegex(ValueError, "parsed_mismatch"):
            cons.compare_parsed(c, tampered)
        shifted = copy.deepcopy(base); shifted["assignments"][6]["string_start"] += 1
        with self.assertRaisesRegex(ValueError, "parsed_mismatch"):
            cons.compare_parsed(c, shifted)
        dup = copy.deepcopy(base); dup["assignments"].append(copy.deepcopy(dup["assignments"][0]))
        with self.assertRaisesRegex(ValueError, "parsed_mismatch"):
            cons.compare_parsed(c, dup)
        extra_tok = copy.deepcopy(base); extra_tok["tokens"] = extra_tok["tokens"][:-1]
        with self.assertRaisesRegex(ValueError, "parsed_mismatch"):
            cons.compare_parsed(c, extra_tok)
    def test_token_coverage_extra_bytes(self):
        self.assertEqual(prod.parse_rvmat(make_text())["inventory"]["assignments"], 20)
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED"):
            cons.scan_tokens(make_text() + b"@")
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED"):
            cons.declarative_parse(make_text().replace(b"Stage2", b"StageX"))

class RangeAndPboTests(unittest.TestCase):
    def test_synthetic_pbo_fixture(self):
        payload = b"PAADATA"
        blob, start = build_pbo([("parts/data/x.paa", 0, payload), ("parts/data/y.paa", 0, b"ZZ")])
        self.assertEqual(blob[start:start + len(payload)], payload)
        entries = [{"name": "parts/data/x.paa", "mime": 0, "size": len(payload), "offset": start}]
        found = prod.find_entry(entries, "dz/structures/roads/parts/data/x.paa", "dz/structures/roads")
        self.assertEqual(found["size"], len(payload))
    def test_prefix_missing_wrong_provider_samename(self):
        self.assertEqual(prod.parse_rvmat(make_text())["inventory"]["assignments"], 20)
        entries = [{"name": "parts/data/x.paa", "mime": 0, "size": 1, "offset": 0}]
        with self.assertRaisesRegex(ValueError, "prefix_mismatch_or_wrong_provider"):
            prod.find_entry(entries, "other/parts/data/x.paa", "dz/structures/roads")
        with self.assertRaisesRegex(ValueError, "prefix_missing"):
            prod.strip_pbo_prefix("dz/structures/roads/parts/data/x.paa", "")
        with self.assertRaisesRegex(ValueError, "prefix_mismatch_or_wrong_provider"):
            prod.find_entry(entries, "dz/other/x.paa", "dz/structures/roads")
        with self.assertRaisesRegex(ValueError, "prefix_mismatch_or_wrong_provider"):
            prod.find_entry(entries, "dz/structures/other/parts/data/x.paa", "dz/structures/roads")
    def test_mime_range_bounds_zero_limits(self):
        def leaf(mime=0, size=10, off=0):
            return {"virtual_path": "dz/structures/roads/a.paa", "entry": {"name": "a.paa", "mime": mime, "size": size, "offset": off}, "sha256": "0" * 64, "output": "leaves/a.paa"}
        good = [leaf(size=10, off=i * 10) for i in range(4)]
        self.assertTrue(prod.validate_range_leaves(good, 1000))
        bad = copy.deepcopy(good); bad[0]["entry"]["mime"] = 1
        with self.assertRaisesRegex(ValueError, "mime_not_zero"):
            prod.validate_range_leaves(bad, 1000)
        bad2 = copy.deepcopy(good); bad2[0]["entry"]["size"] = 0
        with self.assertRaisesRegex(ValueError, "range_size_not_positive"):
            prod.validate_range_leaves(bad2, 1000)
        bad3 = copy.deepcopy(good); bad3[0]["entry"]["offset"] = 9999
        with self.assertRaisesRegex(ValueError, "range_out_of_bounds"):
            prod.validate_range_leaves(bad3, 1000)
        bad4 = copy.deepcopy(good); bad4[0]["entry"]["size"] = 16777217
        with self.assertRaisesRegex(ValueError, "range_over_16MiB"):
            prod.validate_range_leaves(bad4, 99999999)
        with self.assertRaisesRegex(ValueError, "leaf_mime_not_zero"):
            cons.validate_ranges(bad)
        bad5 = copy.deepcopy(good); bad5[0]["entry"]["offset"] = 995
        with self.assertRaisesRegex(ValueError, "leaf_range_out_of_bounds"):
            cons.validate_ranges(bad5, file_size=1000)
    def test_hash_and_stat_identity_ctime_ignored(self):
        a = {"dev": 1, "ino": 2, "size": 3, "mtime_ns": 4, "ctime_ns": 5}
        b = dict(a); b["ctime_ns"] = 99
        # Cross path/handle ignores ctime; same-API pairs are identical here.
        self.assertTrue(prod.compare_stat_snapshots(a, b, a, b))
        c = dict(a); c["size"] = 99
        with self.assertRaisesRegex(ValueError, "stat_mismatch:path_handle_after:size"):
            prod.compare_stat_snapshots(a, b, c, b)
        d = dict(a); d["ctime_ns"] = 12345
        with self.assertRaisesRegex(ValueError, "stat_mismatch:path_before_after:ctime_ns"):
            prod.compare_stat_snapshots(a, a, d, a)
        e = dict(a); e["mtime_ns"] = 777
        with self.assertRaisesRegex(ValueError, "stat_mismatch"):
            prod.compare_stat_snapshots(a, a, e, e)
        self.assertIn("ctime_ns", prod.stat_snapshot(__import__("os").stat(__file__)))
        with self.assertRaisesRegex(ValueError, "payload_hash"):
            prod.check_range_bytes(b"x", sha(b"y"))
    def test_output_exists_exclusive(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "out.json"; prod.write_json_exclusive(p, {"a": 1})
            with self.assertRaises(FileExistsError):
                prod.write_json_exclusive(p, {"a": 2})
    def test_dropped_edge_and_comutated_manifest(self):
        refs = [{"virtual_path": normalize} for normalize in ("dz/structures/roads/parts/data/a.paa", "dz/structures/roads/parts/data/b.paa", "dz/structures/roads/parts/data/c.paa", "dz/structures/roads/parts/data/d.paa")]
        leaves = [{"virtual_path": r["virtual_path"], "entry": {"mime": 0, "size": 1, "offset": 0}} for r in refs]
        self.assertTrue(cons.validate_leaf_set(refs, leaves))
        dropped = leaves[:3]
        with self.assertRaisesRegex(ValueError, "leaves_not_exactly_extracted_texture_refs"):
            cons.validate_leaf_set(refs, dropped)
        mutated = copy.deepcopy(leaves); mutated[0]["virtual_path"] = "dz/structures/roads/parts/data/arbitrary.paa"
        with self.assertRaisesRegex(ValueError, "leaves_not_exactly_extracted_texture_refs"):
            cons.validate_leaf_set(refs, mutated)
    def test_stub_contract_synthetic_pins(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td); f = td / "x.bin"; f.write_bytes(b"synthetic")
            pin = {"path": str(f), "sha256": sha(b"synthetic"), "size": 9}
            got = prod.verify_pinned_file(pin["path"], pin["sha256"], pin["size"])
            self.assertEqual(got["sha256"], pin["sha256"])
            contract = {"schema": "ROAD_B4A3_V1", "sources": {"stub": pin}}
            cj = td / "contract.json"; cj.write_text(json.dumps(contract), encoding="utf-8")
            self.assertEqual(sha(cj.read_bytes()), sha(cj.read_bytes()))
            with self.assertRaisesRegex(ValueError, "pinned_sha_mismatch"):
                prod.verify_pinned_file(pin["path"], "0" * 64, pin["size"])
    def test_source_table_compare_order(self):
        live_e = [{"name": "a.paa", "mime": 0, "size": 1, "offset": 10}, {"name": "b.paa", "mime": 0, "size": 2, "offset": 11}]
        src = {"properties": {"prefix": "dz/structures/roads"}, "entries": live_e}
        self.assertTrue(prod.compare_live_to_source_table({"prefix": "dz/structures/roads"}, live_e, src, "dz/structures/roads"))
        reordered = {"properties": {"prefix": "dz/structures/roads"}, "entries": list(reversed(live_e))}
        with self.assertRaisesRegex(ValueError, "pbo_entries_mismatch_order_or_content"):
            prod.compare_live_to_source_table({"prefix": "dz/structures/roads"}, live_e, reordered, "dz/structures/roads")
        self.assertTrue(prod.compare_live_to_source_table({"prefix": "dz/structures/roads", "b": "2", "a": "1"}, live_e, {"properties": {"a": "1", "b": "2", "prefix": "dz/structures/roads"}, "entries": live_e}, "dz/structures/roads"))
        missing_mime = {"properties": {"prefix": "dz/structures/roads"}, "entries": [{"name": "a.paa", "size": 1, "offset": 10}, live_e[1]]}
        with self.assertRaisesRegex(ValueError, "source_table_entry_missing_or_extra_field"):
            prod.compare_live_to_source_table({"prefix": "dz/structures/roads"}, live_e, missing_mime, "dz/structures/roads")
        bool_size = {"properties": {"prefix": "dz/structures/roads"}, "entries": [dict(live_e[0], size=True), live_e[1]]}
        with self.assertRaisesRegex(ValueError, "source_table_entry_field_not_int:size"):
            prod.compare_live_to_source_table({"prefix": "dz/structures/roads"}, live_e, bool_size, "dz/structures/roads")
        wrong_prefix = {"properties": {"prefix": "dz/other"}, "entries": live_e}
        with self.assertRaisesRegex(ValueError, "source_table_prefix_mismatch"):
            prod.compare_live_to_source_table({"prefix": "dz/other"}, live_e, wrong_prefix, "dz/structures/roads")

HELPER_CODE = chr(10).join(["import hashlib, json", "HEADER_SIZE = 131072", "def pbo_table(f, file_size):", "    f.seek(0); raw = f.read(HEADER_SIZE); obj = json.loads(raw.decode('utf-8').strip())", "    return obj['properties'], obj['entries']", "def read_payload(f, entry, digest):", "    f.seek(int(entry['offset'])); data = f.read(int(entry['size']))", "    if hashlib.sha256(data).hexdigest() != digest: raise ValueError('payload_hash')", "    return data", ""])

def _file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            c = f.read(1048576)
            if not c: break
            h.update(c)
    return h.hexdigest()

class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._td = tempfile.TemporaryDirectory(); td = Path(cls._td.name); cls.td = td
        payloads = [b"PAALEAF1", b"PAALEAF2xx", b"PAALEAF3yyy", b"PAALEAF4zzzz"]
        texs = [TEX1, TEX2, TEX3, TEX4]; rels = [prod.strip_pbo_prefix(t, "dz/structures/roads") for t in texs]
        header_size = 131072; off = header_size; entries = []
        for rel, pay in zip(rels, payloads):
            entries.append({"name": rel, "mime": 0, "size": len(pay), "offset": off}); off += len(pay)
        for i in range(497):
            entries.append({"name": f"parts/data/placeholder_{i:03d}.paa", "mime": 0, "size": 0, "offset": off})
        props = {"prefix": "dz/structures/roads"}
        pbo_path = td / "synthetic.pbo"
        header = json.dumps({"properties": props, "entries": entries}).encode("utf-8")
        assert len(header) <= header_size
        with open(pbo_path, "wb") as f:
            f.write(header + b" " * (header_size - len(header)))
            for pay in payloads: f.write(pay)
            f.truncate(318217469)
        pbo_sha = _file_sha(pbo_path); pbo_size = 318217469
        def pin(path):
            data = Path(path).read_bytes(); return {"path": str(path), "sha256": sha(data), "size": len(data)}
        def write_pin(name, data):
            p = td / name; p.write_bytes(data); return pin(p)
        text1 = make_text(); t1p = td / "road1.rvmat"; t1p.write_bytes(text1)
        text2 = make_text(specular="130", tex_a=TEX3, tex_b=TEX4); t2p = td / "road2.rvmat"; t2p.write_bytes(text2)
        catalog = [{"name": e['name'], "normalized_name": e['name'], "category": "synthetic", "mime": 0, "size": e['size'], "sha256": sha(payloads[i] if i < 4 else b'')} for i, e in enumerate(entries)]
        sources = {"models": write_pin("models.bin", b"MODELS-SYNTH"), "catalog": write_pin("catalog.json", json.dumps(catalog).encode("utf-8")), "source_table": write_pin("source_table.json", json.dumps({"properties": props, "entries": entries}).encode("utf-8")), "helper": write_pin("helper_stub.py", HELPER_CODE.encode("utf-8")), "python": write_pin("python.bin", b"PYTHON-SYNTH")}
        saved_assets = []
        for i in range(8):
            pp = write_pin(f"asset{i}.bin", f"asset-{i}".encode("utf-8")); saved_assets.append({"virtual_path": f"dz/structures/roads/asset{i}.paa", "path": pp["path"], "sha256": pp["sha256"], "size": pp["size"]})
        leaves = [{"virtual_path": tex, "entry": dict(entries[i]), "sha256": sha(payloads[i]), "output": "leaves/" + rels[i].rsplit("/", 1)[-1]} for i, tex in enumerate(texs)]
        cls.contract = {"schema": "ROAD_B4A3_V1", "sources": sources, "texts": [{"id": "road1", "path": str(t1p), "sha256": sha(text1), "size": len(text1), "specular_power": "60"}, {"id": "road2", "path": str(t2p), "sha256": sha(text2), "size": len(text2), "specular_power": "130"}], "saved_assets": saved_assets, "leaves": leaves, "pbo": {"path": str(pbo_path), "sha256": pbo_sha, "size": pbo_size, "prefix": "dz/structures/roads"}, "inventory": {"assignments": 20, "classes": 4, "strings": 6, "vec3": 8, "vec4": 5, "scalar": 1, "semicolons": 24}, "limits": {"range_bytes": 16777216, "total_ranges": 67108864}, "output": str(td / "out"), "attempt_marker": str(td / "attempt.marker"), "scope": "three_road_models", "build_ready": False, "provider_ambiguity": "NOT_TESTED", "native_resolution": "NOT_TESTED"}
        cls.pbo_path = str(pbo_path)
        cpath = td / "contract.json"; cpath.write_text(json.dumps(cls.contract), encoding="utf-8"); cls.contract_path = str(cpath); cls.contract_sha = sha(cpath.read_bytes())
        cls.prod_rc = prod.main(["--contract", cls.contract_path, "--contract-sha", cls.contract_sha])
        assert cls.prod_rc == 0, cls.prod_rc
        cls.report_path = td / "out" / "report.json"; cls.report_sha = sha(cls.report_path.read_bytes()); cls.report = json.loads(cls.report_path.read_bytes().decode("utf-8"))
        assert json.loads(json.dumps(cls.report)) == cls.report
    @classmethod
    def tearDownClass(cls):
        cls._td.cleanup()
    def _bad(self, pattern, mutate_report=None, mutate_contract=None):
        c = copy.deepcopy(self.contract); r = copy.deepcopy(self.report)
        if mutate_report: mutate_report(r)
        if mutate_contract: mutate_contract(c)
        # JSON removes in-memory aliases: co-mutate both redundant representations
        # so the independent source/table guard, rather than equality alone, fires.
        r['range_copies'] = copy.deepcopy(r['leaves'])
        with self.assertRaisesRegex(ValueError, pattern):
            cons.verify(c, self.contract_sha, r, self.report_sha, str(self.report_path))
    def test_e2e_consumer_verify_main_and_no_pbo_open(self):
        import builtins
        import io
        from unittest import mock
        verdict_path = self.td / "verdict.json"
        orig_open = builtins.open; orig_stat = Path.stat; pbo_path = self.pbo_path
        def guarded_open(file, *a, **k):
            if str(file) == pbo_path: raise AssertionError("consumer_opened_pbo")
            return orig_open(file, *a, **k)
        def guarded_stat(self_path, *a, **k):
            if str(self_path) == pbo_path: raise AssertionError("consumer_stat_pbo")
            return orig_stat(self_path, *a, **k)
        with mock.patch("builtins.open", guarded_open), mock.patch("io.open", guarded_open), mock.patch.object(Path, "stat", guarded_stat):
            verdict = cons.verify(copy.deepcopy(self.contract), self.contract_sha, copy.deepcopy(self.report), self.report_sha, str(self.report_path))
            self.assertEqual(verdict["status"], cons.SUCCESS); self.assertFalse(verdict["pbo_reopened"])
            rc = cons.main(["--contract", self.contract_path, "--contract-sha", self.contract_sha, "--report", str(self.report_path), "--report-sha", self.report_sha, "--output", str(verdict_path)])
            self.assertEqual(rc, 0)
            rc2 = cons.main(["--contract", self.contract_path, "--contract-sha", self.contract_sha, "--report", str(self.report_path), "--report-sha", self.report_sha, "--output", str(verdict_path)])
            self.assertEqual(rc2, 2)
    def test_producer_marker_existing(self):
        with tempfile.TemporaryDirectory() as td2:
            marker = Path(td2) / "marker"; marker.write_text("x", encoding="utf-8")
            tiny = {"attempt_marker": str(marker), "output": str(Path(td2) / "out")}; cp = Path(td2) / "c.json"; cp.write_text(json.dumps(tiny), encoding="utf-8")
            self.assertEqual(prod.main(["--contract", str(cp), "--contract-sha", sha(cp.read_bytes())]), 2)
    def test_catalog_real_shape_and_redundant_copy_mutant(self):
        rows = json.loads(Path(self.contract['sources']['catalog']['path']).read_bytes())
        self.assertEqual(len(prod.catalog_leaf_rows(rows)), 501)
        with self.assertRaisesRegex(ValueError, 'catalog_shape_exact'):
            prod.catalog_leaf_rows({'entries': rows})
        broken = copy.deepcopy(rows); broken[0]['normalized_name'] = 'wrong.paa'
        with self.assertRaisesRegex(ValueError, 'catalog_normalized_name'):
            prod.catalog_leaf_rows(broken)
        r = copy.deepcopy(self.report); r['range_copies'][0]['entry']['offset'] += 1
        with self.assertRaisesRegex(ValueError, 'range_copies_not_leaves'):
            cons.verify(self.contract, self.contract_sha, r, self.report_sha, str(self.report_path))
    def test_mutants_report_and_contract(self):
        self._bad("report_pbo_properties_mismatch_source_table", lambda r: r["pbo"].update(properties={"prefix": "dz/structures/roads", "x": "1"}))
        self._bad("pbo_prefix_mismatch", lambda r: r["pbo"].update(prefix="dz/other"))
        self._bad("report_pbo_entries_count_mismatch", lambda r: r["pbo"].update(entries_count=500))
        self._bad("pbo_stat_before_after_mismatch:path:mtime_ns", lambda r: [r["pbo"]["stat_after"][api].update(mtime_ns=r["pbo"]["stat_after"][api]["mtime_ns"] + 1) for api in ("path", "handle")])
        self._bad("pbo_stat_before_after_mismatch:path:ctime_ns", lambda r: r["pbo"]["stat_after"]["path"].update(ctime_ns=r["pbo"]["stat_after"]["path"]["ctime_ns"] + 1))
        self._bad("pin_meta_shape:source:models", lambda r: r["sources"]["models"]["before"].pop("sha256"))
        self._bad("catalog_pins_mismatch", lambda r: r["catalog_pins"].update(source_table_sha256="0" * 64))
        self._bad("leaf_entry_mismatch_source_table", lambda r: r["leaves"][0]["entry"].update(name="parts/data/wrong.paa"))
        self._bad("leaves_not_exactly_extracted_texture_refs", lambda r: r["leaves"][0].update(virtual_path="dz/structures/roads/parts/data/arbitrary.paa"))
        self._bad("leaf_entry_mismatch_source_table", lambda r: r["leaves"][0]["entry"].update(offset=r["leaves"][0]["entry"]["offset"] + 1))
        self._bad("leaf_texture_ref_mismatch", lambda r: r["leaves"][0]["texture_ref"].update(string_start=r["leaves"][0]["texture_ref"]["string_start"] + 1))
        self._bad("leaf_copy_size_mismatch", lambda r: r["leaves"][0].update(copy_size=r["leaves"][0]["copy_size"] + 1))
        self._bad("leaf_entry_mismatch_source_table", lambda r: r["leaves"][0]["entry"].update(offset=r["leaves"][0]["entry"]["offset"] + 8), lambda c: c["leaves"][0]["entry"].update(offset=c["leaves"][0]["entry"]["offset"] + 8))
        self._bad("report_source_pin_mismatch:models", lambda r: r["sources"]["models"].update(sha256="0" * 64))
        self._bad("sha_mismatch", lambda r: None, lambda c: c["sources"]["models"].update(sha256="0" * 64))
        self._bad("report_status_not_success", lambda r: r.update(status="PASS"))
        self._bad("report_scope_build_ready", lambda r: r.update(build_ready=True))
        self._bad("leaf_output_escape", lambda r: r["leaves"][0].update(output="../escape.paa"))
        self._bad("leaf_output_escape", lambda r: r["leaves"][0].update(output="/abs/escape.paa"))

if __name__ == "__main__":
    unittest.main()
