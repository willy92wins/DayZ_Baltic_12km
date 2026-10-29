import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUALITY = os.path.join(ROOT, "tools", "quality")
if QUALITY not in sys.path:
    sys.path.insert(0, QUALITY)
import shore_serialization_io_ev112 as io
import measure_shore_serialization_ev112 as measure

def H(b):
    return hashlib.sha256(b).hexdigest()

def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return {"path": path, "bytes": len(data), "sha256": H(data)}

def jwrite(path, obj):
    return write(path, (json.dumps(obj) + "\n").encode())

def jread(path):
    with open(path, "rb") as f:
        return json.loads(f.read().decode("utf-8"))

CODEC = {"name": "zlib", "level": 1, "method": 8, "wbits": 15, "memLevel": 8, "strategy": 0, "dictionary": None, "encoder_flush": 4, "decoder_flush_forbidden": True, "input_chunk_bytes": 65536, "decoder_max_length": 65536, "runtime_version": "1.3.2", "compile_version": "1.3.2", "python_version": "3.12.14"}
CLAIMS = {"map_repaired": False, "build_ready": False, "natural_calibration": False, "human_cases_resolved": 0, "c1": "NOT_REVIEWED", "missing_chain_projection": False, "independent_codec_implementation": False, "audit_security_sandbox": False}
RECORD_SCHEMA = {"header": ["kind", "schema", "contract_sha256", "inventory_sha256", "classification_sha256", "codec", "claims"], "file": ["kind", "index", "path", "classification", "original_bytes", "encoded_bytes", "decoded_bytes", "original_sha256", "encoded_sha256", "decoded_sha256", "eof", "unused_bytes", "unconsumed_bytes", "state"], "final": ["kind", "state", "complete_files", "expected_files", "complete", "totals_by_classification", "reason", "claims"]}
NC = {"schema": "q02b3.v1", "scope": "NUMERIC_COVERAGE_ONLY", "npz_sha256": H(b"npz-real"), "selectors": {"path": "tests/fixtures/q02b3/selectors.json", "sha256": H(b"sel-real")}, "oracles": {"path": "tests/fixtures/q02b3/oracles-r1.json", "sha256": H(b"ora-real")}, "expected": {"universe": 538390}, "controls": 4, "human_cases": {"count": 9, "state": "GEOMETRY_UNBOUND", "resolved": 0}, "c1": "NOT_REVIEWED", "natural_positive_count": 0, "calibration_ready": False, "angle_state": "PENDING_CERTIFIED_ANGLE", "map_repaired": False}

def build_fixture(base, files=None, limits_override=None, inventory_bool=False):
    if files is None:
        files = [("chain-0000/a.bin", b"\x00\xff\xfe\x7f\x80"), ("chain-0000/b.txt", b"a\nb\n"), ("chain-0850/c.txt", b"a\r\nb\r\n"), ("header.json", b"{}\n")]
    capture = os.path.join(base, "capture")
    meta_dir = os.path.join(base, "meta")
    os.makedirs(capture); os.makedirs(meta_dir)
    classes = []
    for rel, data in files:
        write(os.path.join(capture, *rel.split("/")), data)
        classes.append("HEADER_BOUND_ONLY" if rel == "header.json" else "UNVERIFIED_TAIL" if rel.startswith("chain-0850/") else "ACCEPTED_NUMERIC_PREFIX")
    pins = {}
    pins["numeric_contract"] = jwrite(os.path.join(meta_dir, "numeric_contract.json"), NC)
    pins["numeric_guard_source"] = write(os.path.join(meta_dir, "guard.py"), b"# guard bytes only\n")
    pins["runtime"] = jwrite(os.path.join(meta_dir, "runtime.json"), {"sys_version": "3.12.14 test", "executable": sys.executable, "prefix": sys.prefix, "base_prefix": sys.base_prefix, "zlib_origin": "built-in", "zlib_has_file": False, "zlib_compile": "1.3.2", "zlib_runtime": "1.3.2", "apis": {}, "pins": {}, "core_dll_candidates": [], "codec_data_calls": 0, "capture_opened": False, "decompress_state": {}})
    pins["audit_probe"] = write(os.path.join(meta_dir, "audit_probe.py"), b"# probe\n")
    pins["audit_result"] = write(os.path.join(meta_dir, "audit_result.txt"), b"ok\n")
    pins["audit_completion"] = jwrite(os.path.join(meta_dir, "audit_completion.json"), {"rc": 0})
    pins["oracles"] = jwrite(os.path.join(meta_dir, "oracles.json"), {"schema": "q02b4-oracles.v1", "literal_cases": [{"id": "empty", "hex": "", "sha256": H(b"")}, {"id": "binary", "hex": "00fffe7f80", "sha256": H(bytes.fromhex("00fffe7f80"))}]})
    pins["derivation"] = write(os.path.join(meta_dir, "README.md"), b"derivation\n")
    prod_out, prod_err = b"", b"REJECTED:totalbytes"
    cons_out, cons_err = b"VERIFIED_PARTIAL\n", b""
    pins["producer_stdout"] = write(os.path.join(meta_dir, "p_stdout"), prod_out)
    pins["producer_stderr"] = write(os.path.join(meta_dir, "p_stderr"), prod_err)
    pins["consumer_stdout"] = write(os.path.join(meta_dir, "c_stdout"), cons_out)
    pins["consumer_stderr"] = write(os.path.join(meta_dir, "c_stderr"), cons_err)
    exe_s = sys.executable.replace(os.sep, "/")
    pins["producer_running_json"] = jwrite(os.path.join(meta_dir, "p_running.json"), {"pid": 111, "birth": 1.0, "started": 1.0, "seconds": 600, "executable": exe_s, "input_sha": H(b"prod-input-not-guard")})
    pins["consumer_running_json"] = jwrite(os.path.join(meta_dir, "c_running.json"), {"pid": 222, "birth": 1.0, "started": 1.0, "seconds": 900, "executable": exe_s, "input_sha": H(b"cons-input")})
    pins["producer_completion_json"] = jwrite(os.path.join(meta_dir, "p_completion.json"), {"rc": 1, "reason": None, "seconds": 1.0, "peak_rss": 1, "started": 1.0, "finished": 2.0, "identities": {"111": 1.0}, "stdout_sha": H(prod_out), "stderr_sha": H(prod_err)})
    pins["consumer_completion_json"] = jwrite(os.path.join(meta_dir, "c_completion.json"), {"rc": 2, "reason": None, "seconds": 1.0, "peak_rss": 1, "started": 1.0, "finished": 2.0, "identities": {"222": 1.0}, "stdout_sha": H(cons_out), "stderr_sha": H(cons_err)})
    inv_files = [{"path": rel, "bytes": (True if (inventory_bool and rel == files[0][0]) else len(data)), "sha256": H(data)} for rel, data in files]
    total = sum(len(d) for _r, d in files)
    pins["inventory"] = jwrite(os.path.join(meta_dir, "inventory.json"), {"schema": "inventory-real-keys.v1", "files": inv_files, "total_bytes": total, "producer_completion_sha256": pins["producer_completion_json"]["sha256"], "scope": "saved", "seconds": 1.5})
    consumer_obj = {"bindings": {"contract_sha256": pins["numeric_contract"]["sha256"], "npz_sha256": NC["npz_sha256"], "oracles_sha256": NC["oracles"]["sha256"], "selectors_sha256": NC["selectors"]["sha256"]}, "claims": {"angle_state": "PENDING_CERTIFIED_ANGLE", "c1": "NOT_REVIEWED", "calibration_ready": False, "controls": 4, "human_cases": {"count": 9, "resolved": 0, "state": "GEOMETRY_UNBOUND"}, "map_repaired": False, "natural_positive_count": 0}, "completed_chains": 850, "coverage_complete": False, "covered_universe": 466550, "errors": [], "excluded_count": 26420, "query_count": 440130, "schema": "q02b3-consumer.v1", "state": "VERIFIED_PARTIAL_NUMERIC_COVERAGE", "state_counts": {"DEFINED": 409712, "DEGENERATE": 26420, "INSUFFICIENT_SUPPORT": 30418}, "universe": 538390, "unverified_numeric_count": 0, "unverified_tail": {"chain_id": 850, "files": ["c.txt"]}}
    pins["numeric_consumer"] = jwrite(os.path.join(meta_dir, "numeric_consumer.json"), consumer_obj)
    rows = [{"path": rel, "classification": c} for (rel, _d), c in zip(files, classes)]
    pins["classification"] = jwrite(os.path.join(meta_dir, "classification.json"), {"schema": "classification-real-keys.v1", "inventory_sha256": pins["inventory"]["sha256"], "consumer_sha256": pins["numeric_consumer"]["sha256"], "order": "inventory", "rows": rows})
    with open(sys.executable, "rb") as fh:
        exe_bytes = fh.read()
    limits = {"files": 2618, "individual_original": 16777216, "total_original": 2147483648, "inventory_bytes": 2097152, "all_output_bytes": 2097152, "rss_bytes": 536870912, "workspace_reserved_per_codec_call": 134217728, "encoded_per_file_rule": "2*N+1024", "positive_decoder_cap": "min(65536,max(1,N-decoded_total))", "metadata_total_bytes": 4194304}
    if limits_override:
        limits.update(limits_override)
    base_exe = getattr(sys, "_base_executable", "") or sys.executable
    with open(base_exe, "rb") as fh:
        base_bytes = fh.read()
    contract = {"schema": "q02b4-serialization.v1", "state": "REVISADO_PARA_AUTORIA_DE_MEDICION_GUARDADA", "scope": "SAVED_SERIALIZATION_FEASIBILITY_ONLY", "files": pins, "capture_root": capture, "codec": CODEC, "runtime_images": {"executable": {"path": sys.executable, "sha256": H(exe_bytes), "bytes": len(exe_bytes)}, "_base_executable": {"path": base_exe, "sha256": H(base_bytes), "bytes": len(base_bytes)}, "observed_loaded": []}, "limits": limits, "budgets": {"author_s": 180, "review_s": 120, "suite_s": 90, "measurement_s": 120, "metadata_consumer_s": 60}, "inputs_rule": "x", "allocation_rule": "x", "audit_rule": "x", "record_schema": RECORD_SCHEMA, "serialization": "x", "states": ["SAVED_SERIALIZATION_FEASIBILITY_ONLY", "PARTIAL_SERIALIZATION_DIAGNOSTIC", "INCONCLUSIVE_RESOURCE", "ENCODING_RESOURCE_INCONCLUSIVE", "INPUT_OUT_OF_CONTRACT", "REJECTED_INTEGRITY"], "consumer_scope": "x", "claims": CLAIMS, "numeric_derivation": {"reservation_bytes": 134217728}, "decoder_progress": "x", "encoded_measurement": "x", "time_scope": "x"}
    cpath = os.path.join(base, "contract.json")
    cdata = (json.dumps(contract) + "\n").encode()
    write(cpath, cdata)
    fx = {"contract": cpath, "contract_sha": H(cdata), "capture": capture, "out": os.path.join(base, "prod"), "cout": os.path.join(base, "cons"), "contract_obj": contract, "meta_dir": meta_dir, "files": files}
    return fx

def save_contract(fx):
    data = (json.dumps(fx["contract_obj"]) + "\n").encode()
    with open(fx["contract"], "wb") as f:
        f.write(data)
    fx["contract_sha"] = H(data)
    return fx

def repin_bytes(fx, name, data):
    path = fx["contract_obj"]["files"][name]["path"]
    with open(path, "wb") as f:
        f.write(data)
    fx["contract_obj"]["files"][name].update({"bytes": len(data), "sha256": H(data)})
    return save_contract(fx)

def repin_json(fx, name, obj):
    return repin_bytes(fx, name, (json.dumps(obj) + "\n").encode())

def load_meta(fx):
    contract = io.load_contract(fx["contract"], fx["contract_sha"])
    return io.load_metadata(contract)

def run_cli(script, *args):
    return subprocess.run([sys.executable, "-I", os.path.join(QUALITY, script), *args], capture_output=True, text=True, timeout=60)

def produce(fx):
    r = run_cli("measure_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", fx["out"])
    assert r.returncode == 0, r.stderr + r.stdout
    return os.path.join(fx["out"], "receipts.ndjson"), os.path.join(fx["out"], "audit.json")

def verify_cli(fx, receipts, audit, out):
    return run_cli("verify_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", out, "--receipts", receipts, "--audit", audit)

class Oracles(unittest.TestCase):
    def test_literals_from_pinned_oracles(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td)
            oracles = jread(fx["contract_obj"]["files"]["oracles"]["path"])
            for case in oracles["literal_cases"]:
                data = bytes.fromhex(case["hex"])
                self.assertEqual(H(data), case["sha256"])
                r = measure.roundtrip_bytes(data, case["sha256"])
                self.assertEqual(r["decoded_sha256"], case["sha256"])
            for data in (b"A" * 65537, bytes(range(256)) * 257):
                r = measure.roundtrip_bytes(data, H(data))
                self.assertEqual(r["decoded_bytes"], len(data))
    def test_decoder_empty_chunk_and_buffered_boundary(self):
        data = bytes(range(256)) * 300 + b"tail"
        enc = zlib.compress(data, 1)
        dec = measure.Decoder(len(data), H(data))
        dec.feed(b"", 134217728)
        for i in range(len(enc)):
            dec.feed(enc[i:i+1], 134217728)
            dec.feed(b"", 134217728)
        dec.finish(134217728)
        self.assertEqual(dec.decoded, len(data))
        rt = measure.RoundTrip(len(b"x"), H(b"x"))
        orig = zlib.compressobj
        class EmptyFirst:
            def __init__(self, inner): self.inner = inner; self.first = True
            def compress(self, c):
                if self.first: self.first = False; return b""
                return self.inner.compress(c)
            def flush(self, m): return self.inner.flush(m)
        measure.zlib.compressobj = lambda *a, **k: EmptyFirst(orig(*a, **k))
        try:
            r = measure.roundtrip_bytes(b"hello empty compress piece", H(b"hello empty compress piece"))
            self.assertTrue(r["eof"])
        finally:
            measure.zlib.compressobj = orig
    def test_decoder_negatives_truncated_corrupt_concatenated_overrun(self):
        data = b"hello world" * 100
        enc = zlib.compress(data, 1)
        for bad in (enc[:-2], bytes([enc[0] ^ 1]) + enc[1:], enc + enc):
            dec = measure.Decoder(len(data), H(data))
            with self.assertRaises(io.Reject):
                dec.feed(bad, 134217728); dec.finish(134217728)
        dec = measure.Decoder(2, H(b"hi"))
        with self.assertRaises(io.Reject):
            dec.feed(zlib.compress(b"hello", 1), 134217728)
    def test_encoder_cap_monkeypatch(self):
        orig = zlib.compressobj
        class Fake:
            def compress(self, c): return b"x" * 5000
            def flush(self, m): return b""
        measure.zlib.compressobj = lambda *a, **k: Fake()
        try:
            with self.assertRaises(io.Reject):
                measure.roundtrip_bytes(b"hi", H(b"hi"))
        finally:
            measure.zlib.compressobj = orig
    def test_bool_nan_infinity_typed_equality(self):
        self.assertFalse(io.is_int(True))
        self.assertFalse(io.typed_equal(True, 1))
        self.assertFalse(io.typed_equal({"a": True}, {"a": 1}))
        for bad in (b'{"a":NaN}', b'{"a":Infinity}', b'{"a":1e999}', b'{"a":1,"a":2}'):
            with self.assertRaises(io.Reject):
                io.parse_json_bytes(bad)
        with self.assertRaises(io.Reject):
            io.validate_rel_path("../x")
        with self.assertRaises(io.Reject):
            io.validate_rel_path("a\\b")
    def test_stat_tuple_mtime_ctime_and_read_limited_fstat(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.bin"
            p.write_bytes(b"abc")
            st = os.stat(str(p))
            self.assertEqual(io.stat_tuple(st)[3:], (st.st_mtime_ns, st.st_ctime_ns))
            data, sha, n = io.read_limited_bytes(str(p), 10)
            self.assertEqual((data, sha, n), (b"abc", H(b"abc"), 3))

class MetadataGuards(unittest.TestCase):
    def test_missing_pin_and_inventory_duplicate_metamorphic(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td)
            os.remove(fx["contract_obj"]["files"]["oracles"]["path"])
            with self.assertRaises(io.Reject): load_meta(fx)
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td)
            inv = jread(fx["contract_obj"]["files"]["inventory"]["path"])
            inv["files"].append(dict(inv["files"][0])); inv["total_bytes"] += inv["files"][0]["bytes"]
            repin_json(fx, "inventory", inv)
            with self.assertRaises(io.Reject): load_meta(fx)
    def test_classfalse_and_consumer_state_metamorphic(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td)
            cls = jread(fx["contract_obj"]["files"]["classification"]["path"])
            cls["rows"][0]["classification"] = "UNVERIFIED_TAIL"
            repin_json(fx, "classification", cls)
            with self.assertRaises(io.Reject): load_meta(fx)
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td)
            cons = jread(fx["contract_obj"]["files"]["numeric_consumer"]["path"])
            cons["state"] = "SOMETHING_ELSE"; repin_json(fx, "numeric_consumer", cons)
            fx["contract_obj"]["files"]["classification"]["sha256"] = fx["contract_obj"]["files"]["classification"]["sha256"]
            cls = jread(fx["contract_obj"]["files"]["classification"]["path"]); cls["consumer_sha256"] = fx["contract_obj"]["files"]["numeric_consumer"]["sha256"]; repin_json(fx, "classification", cls)
            with self.assertRaises(io.Reject): load_meta(fx)
    def test_completionforged_co_mutated_and_tail_binding(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td)
            comp = jread(fx["contract_obj"]["files"]["producer_completion_json"]["path"])
            comp["stdout_sha"] = H(b"forged"); repin_json(fx, "producer_completion_json", comp)
            inv = jread(fx["contract_obj"]["files"]["inventory"]["path"]); inv["producer_completion_sha256"] = fx["contract_obj"]["files"]["producer_completion_json"]["sha256"]; repin_json(fx, "inventory", inv)
            cls = jread(fx["contract_obj"]["files"]["classification"]["path"]); cls["inventory_sha256"] = fx["contract_obj"]["files"]["inventory"]["sha256"]; repin_json(fx, "classification", cls)
            with self.assertRaises(io.Reject): load_meta(fx)
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td)
            cons = jread(fx["contract_obj"]["files"]["numeric_consumer"]["path"]); cons["unverified_tail"]["files"] = ["other.txt"]; repin_json(fx, "numeric_consumer", cons)
            cls = jread(fx["contract_obj"]["files"]["classification"]["path"]); cls["consumer_sha256"] = fx["contract_obj"]["files"]["numeric_consumer"]["sha256"]; repin_json(fx, "classification", cls)
            with self.assertRaises(io.Reject): load_meta(fx)
    def test_running_identity_window_and_no_guard_input_assertion(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td)
            meta = load_meta(fx)
            self.assertNotEqual(meta["producer_running"]["input_sha"], fx["contract_obj"]["files"]["numeric_guard_source"]["sha256"])
            run = jread(fx["contract_obj"]["files"]["producer_running_json"]["path"]); run["pid"] = 999; repin_json(fx, "producer_running_json", run)
            with self.assertRaises(io.Reject): load_meta(fx)
    def test_reparse_symlink_ancestor_if_available(self):
        with tempfile.TemporaryDirectory() as td:
            real = Path(td) / "real"; real.mkdir(); (real / "x").write_bytes(b"x")
            link = Path(td) / "link"
            try: os.symlink(str(real), str(link), target_is_directory=True)
            except Exception: self.skipTest("symlink unavailable")
            with self.assertRaises(io.Reject): io.check_file_no_reparse(str(link / "x"))
    def test_nohook_and_no_numeric_imports_and_preload_failclosed(self):
        state = io.AuditState({}, capture_root=None)
        res = io.run_selftests(state, tempfile.gettempdir())
        self.assertFalse(res["hook_installed"])
        self.assertNotIn("shore_multiscale_coverage_ev112", sys.modules)
        with self.assertRaises(io.Reject): io.parse_audit_ndjson(b'{"kind":"audit"}\n')

class Cli(unittest.TestCase):
    def test_producer_consumer_zero_capture_no_npz_wrp_pbo(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td)
            receipts, audit = produce(fx)
            with open(receipts, "rb") as f: lines = f.read().splitlines()
            self.assertEqual(len(lines), 6)
            with open(audit, "rb") as f: audit_lines = f.read().splitlines()
            self.assertEqual(len(audit_lines), 2)
            startup = json.loads(audit_lines[0]); terminal = json.loads(audit_lines[1])
            self.assertEqual(startup["record"], "startup"); self.assertEqual(terminal["record"], "terminal")
            self.assertTrue(all(startup["selftests"].values()))
            self.assertFalse(any((r["path"] or "").lower().endswith((".npz", ".wrp", ".pbo")) for r in startup["preloads"]))
            self.assertGreaterEqual(startup["counters"]["capture_open_allowed"] if "capture_open_allowed" in startup["counters"] else terminal["counters"]["capture_open_allowed"], 4)
            r2 = verify_cli(fx, receipts, audit, fx["cout"])
            self.assertEqual(r2.returncode, 0, r2.stderr + r2.stdout)
            with open(os.path.join(fx["cout"], "consumer.json"), "rb") as f: c = json.loads(f.read())
            self.assertTrue(c["complete"]); self.assertEqual(c["audit"]["capture_attempts"], 0); self.assertEqual(c["state"], "SAVED_SERIALIZATION_FEASIBILITY_ONLY")
    def test_contract_sha_bool_inventory_filecap_reportcap(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td)
            self.assertNotEqual(run_cli("measure_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", "0"*64, "--output-dir", fx["out"]).returncode, 0)
        for kw in ({"inventory_bool": True}, {"limits_override": {"individual_original": 4}}, {"limits_override": {"all_output_bytes": 64}}):
            with tempfile.TemporaryDirectory() as td:
                fx = build_fixture(td, **kw)
                self.assertNotEqual(run_cli("measure_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", fx["out"]).returncode, 0)
    def test_consumer_truncated_partial_no_full_and_audit_truncated(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td); receipts, audit = produce(fx)
            with open(receipts, "rb") as f: data = f.read()
            trunc = os.path.join(td, "trunc.ndjson"); Path(trunc).write_bytes(data[:-3])
            self.assertNotEqual(verify_cli(fx, trunc, audit, os.path.join(td, "c1")).returncode, 0)
            parts = data.split(b"\n"); partial = b"\n".join(parts[:3]) + b"\n"; ppath = os.path.join(td, "partial.ndjson"); Path(ppath).write_bytes(partial)
            startup_only = Path(audit).read_bytes().split(b"\n")[0] + b"\n"; apath = os.path.join(td, "audit_startup.json"); Path(apath).write_bytes(startup_only)
            r3 = verify_cli(fx, ppath, apath, os.path.join(td, "c2"))
            self.assertEqual(r3.returncode, 0, r3.stderr)
            with open(os.path.join(td, "c2", "consumer.json"), "rb") as f: c = json.loads(f.read())
            self.assertFalse(c["complete"]); self.assertEqual(c["state"], "PARTIAL_SERIALIZATION_DIAGNOSTIC")
            bad_audit = os.path.join(td, "audit_bad.json"); Path(bad_audit).write_bytes(Path(audit).read_bytes()[:-3])
            self.assertNotEqual(verify_cli(fx, receipts, bad_audit, os.path.join(td, "c3")).returncode, 0)
            full_no_terminal = verify_cli(fx, receipts, apath, os.path.join(td, "c4"))
            self.assertNotEqual(full_no_terminal.returncode, 0)
    def test_bool_totals_and_false_audit_and_unknown_key_metamorphic(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td); receipts, audit = produce(fx)
            with open(receipts, "rb") as f: parts = f.read().split(b"\n")
            final = json.loads(parts[-2]); final["totals_by_classification"]["ACCEPTED_NUMERIC_PREFIX"]["files"] = True
            parts[-2] = json.dumps(final).encode(); new_data = b"\n".join(parts); new_receipts = os.path.join(td, "bool.ndjson"); Path(new_data_path := new_receipts).write_bytes(new_data)
            alines = Path(audit).read_bytes().splitlines(); term = json.loads(alines[1]); term["receipts_sha256"] = H(new_data); term["receipts_bytes"] = len(new_data); alines[1] = json.dumps(term).encode(); new_audit = os.path.join(td, "audit2.json"); Path(new_audit).write_bytes(b"\n".join(alines) + b"\n")
            self.assertNotEqual(verify_cli(fx, new_receipts, new_audit, os.path.join(td, "cb")).returncode, 0)
            alines2 = Path(audit).read_bytes().splitlines(); st = json.loads(alines2[0]); st["selftests"]["forbidden_open_denied"] = False; alines2[0] = json.dumps(st).encode(); false_audit = os.path.join(td, "audit_false.json"); Path(false_audit).write_bytes(b"\n".join(alines2) + b"\n")
            self.assertNotEqual(verify_cli(fx, receipts, false_audit, os.path.join(td, "cf")).returncode, 0)
            obj = json.loads(parts[1]); obj["extra"] = 1; bad = b"\n".join([parts[0], json.dumps(obj).encode()] + parts[2:]); bpath = os.path.join(td, "bad.ndjson"); Path(bpath).write_bytes(bad)
            self.assertNotEqual(verify_cli(fx, bpath, audit, os.path.join(td, "cu")).returncode, 0)
    def test_stale_audit_other_run_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td); receipts, audit = produce(fx)
            alines = Path(audit).read_bytes().splitlines(); term = json.loads(alines[1]); term["receipts_sha256"] = H(b"other-run"); alines[1] = json.dumps(term).encode(); stale = os.path.join(td, "stale.json"); Path(stale).write_bytes(b"\n".join(alines) + b"\n")
            self.assertNotEqual(verify_cli(fx, receipts, stale, os.path.join(td, "cs")).returncode, 0)
    def test_changed_extra_source(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td); Path(fx["capture"], "chain-0000", "extra.txt").write_bytes(b"x")
            self.assertNotEqual(run_cli("measure_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", fx["out"]).returncode, 0)
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td); Path(fx["capture"], "header.json").write_bytes(b"changed\n")
            self.assertNotEqual(run_cli("measure_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", fx["out"]).returncode, 0)

if __name__ == "__main__":
    unittest.main()
