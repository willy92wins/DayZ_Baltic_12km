import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zlib

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

CODEC = {"name": "zlib", "level": 1, "method": 8, "wbits": 15, "memLevel": 8, "strategy": 0, "dictionary": None, "encoder_flush": 4, "decoder_flush_forbidden": True, "input_chunk_bytes": 65536, "decoder_max_length": 65536, "runtime_version": "1.3.2", "compile_version": "1.3.2", "python_version": "3.12.14"}
CLAIMS = {"map_repaired": False, "build_ready": False, "natural_calibration": False, "human_cases_resolved": 0, "c1": "NOT_REVIEWED", "missing_chain_projection": False, "independent_codec_implementation": False, "audit_security_sandbox": False}
RECORD_SCHEMA = {"header": ["kind", "schema", "contract_sha256", "inventory_sha256", "classification_sha256", "codec", "claims"], "file": ["kind", "index", "path", "classification", "original_bytes", "encoded_bytes", "decoded_bytes", "original_sha256", "encoded_sha256", "decoded_sha256", "eof", "unused_bytes", "unconsumed_bytes", "state"], "final": ["kind", "state", "complete_files", "expected_files", "complete", "totals_by_classification", "reason", "claims"]}

def build_fixture(base, files=None, limits_override=None, inventory_bool=False):
    if files is None:
        files = [( "chain-0000/a.bin", b"\x00\xff\xfe\x7f\x80"), ("chain-0000/b.txt", b"a\nb\n"), ("chain-0850/c.txt", b"a\r\nb\r\n"), ("header.json", b"{}\n")]
    capture = os.path.join(base, "capture")
    meta_dir = os.path.join(base, "meta")
    os.makedirs(capture); os.makedirs(meta_dir)
    classes = []
    for rel, data in files:
        write(os.path.join(capture, *rel.split("/")), data)
        if rel == "header.json":
            classes.append("HEADER_BOUND_ONLY")
        elif rel.startswith("chain-0850/"):
            classes.append("UNVERIFIED_TAIL")
        else:
            classes.append("ACCEPTED_NUMERIC_PREFIX")
    pins = {}
    pins["numeric_contract"] = jwrite(os.path.join(meta_dir, "numeric_contract.json"), {"schema": "q02b3.v1"})
    pins["numeric_guard_source"] = write(os.path.join(meta_dir, "guard.py"), b"# guard bytes only\n")
    pins["runtime"] = jwrite(os.path.join(meta_dir, "runtime.json"), {"sys_version": "3.12.14 test", "executable": sys.executable, "prefix": sys.prefix, "base_prefix": sys.base_prefix, "zlib_origin": "built-in", "zlib_has_file": False, "zlib_compile": "1.3.2", "zlib_runtime": "1.3.2", "apis": {}, "pins": {}, "core_dll_candidates": [], "codec_data_calls": 0, "capture_opened": False, "decompress_state": {}})
    pins["audit_probe"] = write(os.path.join(meta_dir, "audit_probe.py"), b"# probe\n")
    pins["audit_result"] = write(os.path.join(meta_dir, "audit_result.txt"), b"ok\n")
    pins["audit_completion"] = jwrite(os.path.join(meta_dir, "audit_completion.json"), {"rc": 0})
    pins["oracles"] = jwrite(os.path.join(meta_dir, "oracles.json"), {"schema": "q02b4-oracles.v1"})
    pins["derivation"] = write(os.path.join(meta_dir, "README.md"), b"derivation\n")
    prod_out, prod_err = b"", b"REJECTED:totalbytes"
    cons_out, cons_err = b"VERIFIED_PARTIAL\n", b""
    pins["producer_stdout"] = write(os.path.join(meta_dir, "p_stdout"), prod_out)
    pins["producer_stderr"] = write(os.path.join(meta_dir, "p_stderr"), prod_err)
    pins["consumer_stdout"] = write(os.path.join(meta_dir, "c_stdout"), cons_out)
    pins["consumer_stderr"] = write(os.path.join(meta_dir, "c_stderr"), cons_err)
    exe_s = sys.executable.replace(os.sep, "/")
    pins["producer_running_json"] = jwrite(os.path.join(meta_dir, "p_running.json"), {"pid": 1, "birth": 1.0, "started": 1.0, "seconds": 600, "executable": exe_s, "input_sha": H(b"x")})
    pins["consumer_running_json"] = jwrite(os.path.join(meta_dir, "c_running.json"), {"pid": 2, "birth": 1.0, "started": 1.0, "seconds": 900, "executable": exe_s, "input_sha": H(b"y")})
    pins["producer_completion_json"] = jwrite(os.path.join(meta_dir, "p_completion.json"), {"rc": 1, "reason": None, "seconds": 1.0, "peak_rss": 1, "started": 1.0, "finished": 2.0, "identities": {"1": 1.0}, "stdout_sha": H(prod_out), "stderr_sha": H(prod_err)})
    pins["consumer_completion_json"] = jwrite(os.path.join(meta_dir, "c_completion.json"), {"rc": 2, "reason": None, "seconds": 1.0, "peak_rss": 1, "started": 1.0, "finished": 2.0, "identities": {"2": 1.0}, "stdout_sha": H(cons_out), "stderr_sha": H(cons_err)})
    inv_files = []
    for rel, data in files:
        inv_files.append({"path": rel, "bytes": (True if (inventory_bool and rel == files[0][0]) else len(data)), "sha256": H(data)})
    total = sum(len(d) for _r, d in files)
    pins["inventory"] = jwrite(os.path.join(meta_dir, "inventory.json"), {"schema": "inv.v1", "files": inv_files, "total_bytes": total, "producer_completion_sha256": pins["producer_completion_json"]["sha256"], "scope": "saved", "seconds": 1.5})
    pins["numeric_consumer"] = jwrite(os.path.join(meta_dir, "numeric_consumer.json"), {"bindings": {"contract_sha256": pins["numeric_contract"]["sha256"], "npz_sha256": H(b"n"), "oracles_sha256": H(b"o"), "selectors_sha256": H(b"s")}, "claims": {"angle_state": "PENDING_CERTIFIED_ANGLE", "c1": "NOT_REVIEWED", "calibration_ready": False, "controls": 4, "human_cases": {"count": 9, "resolved": 0, "state": "GEOMETRY_UNBOUND"}, "map_repaired": False, "natural_positive_count": 0}, "completed_chains": 850, "coverage_complete": False, "covered_universe": 1, "errors": [], "excluded_count": 0, "query_count": 1, "schema": "q02b3-consumer.v1", "state": "VERIFIED_PARTIAL_NUMERIC_COVERAGE", "state_counts": {"DEFINED": 1}, "universe": 2, "unverified_numeric_count": 0, "unverified_tail": {"chain_id": 850, "files": ["c.txt"]}})
    rows = [{"path": rel, "classification": c} for (rel, _d), c in zip(files, classes)]
    pins["classification"] = jwrite(os.path.join(meta_dir, "classification.json"), {"schema": "cls.v1", "inventory_sha256": pins["inventory"]["sha256"], "consumer_sha256": pins["numeric_consumer"]["sha256"], "order": "inventory", "rows": rows})
    exe_bytes = open(sys.executable, "rb").read()
    limits = {"files": 2618, "individual_original": 16777216, "total_original": 2147483648, "inventory_bytes": 2097152, "all_output_bytes": 2097152, "rss_bytes": 536870912, "workspace_reserved_per_codec_call": 134217728, "encoded_per_file_rule": "2*N+1024", "positive_decoder_cap": "min(65536,max(1,N-decoded_total))", "metadata_total_bytes": 4194304}
    if limits_override:
        limits.update(limits_override)
    contract = {"schema": "q02b4-serialization.v1", "state": "REVISADO_PARA_AUTORIA_DE_MEDICION_GUARDADA", "scope": "SAVED_SERIALIZATION_FEASIBILITY_ONLY", "files": pins, "capture_root": capture, "codec": CODEC, "runtime_images": {"executable": {"path": sys.executable, "sha256": H(exe_bytes), "bytes": len(exe_bytes)}, "_base_executable": {"path": sys.executable, "sha256": H(exe_bytes), "bytes": len(exe_bytes)}, "observed_loaded": []}, "limits": limits, "budgets": {"author_s": 180, "review_s": 120, "suite_s": 90, "measurement_s": 120, "metadata_consumer_s": 60}, "inputs_rule": "x", "allocation_rule": "x", "audit_rule": "x", "record_schema": RECORD_SCHEMA, "serialization": "x", "states": ["SAVED_SERIALIZATION_FEASIBILITY_ONLY", "PARTIAL_SERIALIZATION_DIAGNOSTIC", "INCONCLUSIVE_RESOURCE", "ENCODING_RESOURCE_INCONCLUSIVE", "INPUT_OUT_OF_CONTRACT", "REJECTED_INTEGRITY"], "consumer_scope": "x", "claims": CLAIMS, "numeric_derivation": {"reservation_bytes": 134217728}, "decoder_progress": "x", "encoded_measurement": "x", "time_scope": "x"}
    cpath = os.path.join(base, "contract.json")
    cdata = (json.dumps(contract) + "\n").encode()
    write(cpath, cdata)
    return {"contract": cpath, "contract_sha": H(cdata), "capture": capture, "out": os.path.join(base, "prod"), "cout": os.path.join(base, "cons")}

def run_cli(script, *args):
    return subprocess.run([sys.executable, "-I", os.path.join(QUALITY, script), *args], capture_output=True, text=True, timeout=60)

class Oracles(unittest.TestCase):
    def test_literals(self):
        cases = [(b"", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"), (bytes.fromhex("00fffe7f80"), "abcc6bb095efd05b8dba2411719022a332058f6f2a08cfb9951c7d584062b45b"), (b"a\nb\n", "911169ddaaf146aff539f58c26c489af3b892dff0fe283c1c264c65ae5aa59a2"), (b"a\r\nb\r\n", "58055bdcc73787eb88c78d36f0b4939e9c5dc1c3ad17e25cc85a6833cf1a0cab"), (b"A" * 65537, None), (bytes(range(256)) * 257, None)]
        for data, sha in cases:
            exp = sha or H(data)
            r = measure.roundtrip_bytes(data, exp)
            self.assertEqual(r["original_sha256"], exp); self.assertEqual(r["decoded_sha256"], exp); self.assertEqual(r["decoded_bytes"], len(data)); self.assertTrue(r["eof"])
    def test_decoder_negatives(self):
        data = b"hello world" * 100
        enc = zlib.compress(data, 1)
        for bad, mode in [(enc[:-2], "trunc"), (bytes([enc[0] ^ 1]) + enc[1:], "corrupt"), (enc + enc, "concat")]:
            dec = measure.Decoder(len(data), H(data))
            try:
                dec.feed(bad, 134217728); dec.finish(134217728); self.fail(mode)
            except io.Reject:
                pass
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
    def test_bool_and_unknown_and_pins(self):
        self.assertFalse(io.is_int(True))
        with self.assertRaises(io.Reject):
            io.parse_json_bytes(b'{"a":1,"a":2}')
        with self.assertRaises(io.Reject):
            io.validate_rel_path("../x")
        with self.assertRaises(io.Reject):
            io.validate_rel_path("a\\b")

class Cli(unittest.TestCase):
    def test_producer_consumer_and_zero_capture(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td)
            r = run_cli("measure_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", fx["out"])
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            receipts = os.path.join(fx["out"], "receipts.ndjson"); audit = os.path.join(fx["out"], "audit.json")
            lines = open(receipts, "rb").read().splitlines()
            self.assertEqual(len(lines), 6)
            a = json.loads(open(audit).read()); self.assertTrue(a["selftests"]["forbidden_open_denied"]); self.assertTrue(a["selftests"]["forbidden_import_denied"]); self.assertGreaterEqual(a["counters"]["capture_open_allowed"], 4)
            r2 = run_cli("verify_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", fx["cout"], "--receipts", receipts, "--audit", audit)
            self.assertEqual(r2.returncode, 0, r2.stderr + r2.stdout)
            c = json.loads(open(os.path.join(fx["cout"], "consumer.json")).read())
            self.assertTrue(c["complete"]); self.assertEqual(c["audit"]["capture_attempts"], 0); self.assertEqual(c["state"], "SAVED_SERIALIZATION_FEASIBILITY_ONLY")
    def test_contract_sha_before_parse_and_bool_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td)
            r = run_cli("measure_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", "0" * 64, "--output-dir", fx["out"])
            self.assertNotEqual(r.returncode, 0)
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td, inventory_bool=True)
            r = run_cli("measure_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", fx["out"])
            self.assertNotEqual(r.returncode, 0)
    def test_file_cap_before_read_and_report_cap(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td, limits_override={"individual_original": 4})
            r = run_cli("measure_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", fx["out"])
            self.assertNotEqual(r.returncode, 0)
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td, limits_override={"all_output_bytes": 64})
            r = run_cli("measure_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", fx["out"])
            self.assertNotEqual(r.returncode, 0)
    def test_consumer_truncated_unknown_partial(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td)
            r = run_cli("measure_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", fx["out"])
            self.assertEqual(r.returncode, 0, r.stderr)
            receipts = os.path.join(fx["out"], "receipts.ndjson"); audit = os.path.join(fx["out"], "audit.json")
            data = open(receipts, "rb").read()
            trunc = os.path.join(td, "trunc.ndjson"); open(trunc, "wb").write(data[:-3])
            r2 = run_cli("verify_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", os.path.join(td, "c1"), "--receipts", trunc, "--audit", audit)
            self.assertNotEqual(r2.returncode, 0)
            parts = data.split(b"\n"); partial = b"\n".join(parts[:3]) + b"\n"; ppath = os.path.join(td, "partial.ndjson"); open(ppath, "wb").write(partial)
            r3 = run_cli("verify_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", os.path.join(td, "c2"), "--receipts", ppath, "--audit", audit)
            self.assertEqual(r3.returncode, 0, r3.stderr)
            c = json.loads(open(os.path.join(td, "c2", "consumer.json")).read()); self.assertFalse(c["complete"]); self.assertEqual(c["state"], "PARTIAL_SERIALIZATION_DIAGNOSTIC")
            obj = json.loads(parts[1]); obj["extra"] = 1; bad = b"\n".join([parts[0], (json.dumps(obj)).encode()] + parts[2:])
            bpath = os.path.join(td, "bad.ndjson"); open(bpath, "wb").write(bad)
            r4 = run_cli("verify_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", os.path.join(td, "c3"), "--receipts", bpath, "--audit", audit)
            self.assertNotEqual(r4.returncode, 0)
    def test_changed_and_extra_source(self):
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td)
            open(os.path.join(fx["capture"], "chain-0000", "extra.txt"), "wb").write(b"x")
            r = run_cli("measure_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", fx["out"])
            self.assertNotEqual(r.returncode, 0)
        with tempfile.TemporaryDirectory() as td:
            fx = build_fixture(td)
            open(os.path.join(fx["capture"], "header.json"), "wb").write(b"changed\n")
            r = run_cli("measure_shore_serialization_ev112.py", "--contract", fx["contract"], "--contract-sha", fx["contract_sha"], "--output-dir", fx["out"])
            self.assertNotEqual(r.returncode, 0)

if __name__ == "__main__":
    unittest.main()
