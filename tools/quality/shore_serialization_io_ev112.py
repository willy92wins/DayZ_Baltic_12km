import hashlib
import json
import math
import os
import sys

HARD = {"files": 2618, "individual_original": 16777216, "total_original": 2147483648, "inventory_bytes": 2097152, "all_output_bytes": 2097152, "rss_bytes": 536870912, "workspace_reserved_per_codec_call": 134217728, "metadata_total_bytes": 4194304}
EXPECTED_CODEC = {"name": "zlib", "level": 1, "method": 8, "wbits": 15, "memLevel": 8, "strategy": 0, "dictionary": None, "encoder_flush": 4, "decoder_flush_forbidden": True, "input_chunk_bytes": 65536, "decoder_max_length": 65536, "runtime_version": "1.3.2", "compile_version": "1.3.2", "python_version": "3.12.14"}
EXPECTED_CLAIMS = {"map_repaired": False, "build_ready": False, "natural_calibration": False, "human_cases_resolved": 0, "c1": "NOT_REVIEWED", "missing_chain_projection": False, "independent_codec_implementation": False, "audit_security_sandbox": False}
EXPECTED_RECORD_SCHEMA = {"header": ["kind", "schema", "contract_sha256", "inventory_sha256", "classification_sha256", "codec", "claims"], "file": ["kind", "index", "path", "classification", "original_bytes", "encoded_bytes", "decoded_bytes", "original_sha256", "encoded_sha256", "decoded_sha256", "eof", "unused_bytes", "unconsumed_bytes", "state"], "final": ["kind", "state", "complete_files", "expected_files", "complete", "totals_by_classification", "reason", "claims"]}
CONTRACT_KEYS = ["schema", "state", "scope", "files", "capture_root", "codec", "runtime_images", "limits", "budgets", "inputs_rule", "allocation_rule", "audit_rule", "record_schema", "serialization", "states", "consumer_scope", "claims", "numeric_derivation", "decoder_progress", "encoded_measurement", "time_scope"]
PIN_NAMES = ["inventory", "numeric_consumer", "numeric_contract", "numeric_guard_source", "runtime", "audit_probe", "audit_result", "audit_completion", "classification", "oracles", "derivation", "producer_running_json", "producer_completion_json", "producer_stdout", "producer_stderr", "consumer_running_json", "consumer_completion_json", "consumer_stdout", "consumer_stderr"]
AUDIT_STARTUP_KEYS = ["kind", "schema", "record", "contract_sha256", "inventory_sha256", "classification_sha256", "runtime_checks", "preloads", "selftests", "counters", "allowed_path_count"]
AUDIT_TERMINAL_KEYS = ["kind", "schema", "record", "state", "contract_sha256", "receipts_sha256", "receipts_bytes", "receipts_records", "complete_files", "expected_files", "counters", "capture_open_allowed", "claims"]
AUDIT_COUNTER_KEYS = ["open_allowed", "open_denied", "import_denied", "capture_open_allowed", "capture_attempts", "write_denied", "fd_denied", "unknown_denied"]
RUNTIME_CHECK_KEYS = ["python_version", "zlib_runtime", "zlib_compile", "executable_pin", "codec_fixed"]
SELFTEST_KEYS = ["hook_installed", "forbidden_open_denied", "forbidden_import_denied"]
PRELOAD_KEYS = ["module", "path", "bytes", "sha256", "origin"]

class Reject(Exception):
    def __init__(self, code, detail=""):
        super().__init__(code + ((":" + detail) if detail else ""))
        self.code = code

def is_int(v):
    return type(v) is int

def is_num(v):
    return type(v) in (int, float) and math.isfinite(v)

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()

def is_sha(v):
    return type(v) is str and len(v) == 64 and all(c in "0123456789abcdef" for c in v)

def require(cond, code, detail=""):
    if not cond:
        raise Reject(code, detail)

def typed_equal(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return set(a.keys()) == set(b.keys()) and all(typed_equal(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(typed_equal(x, y) for x, y in zip(a, b))
    if type(a) is float and not math.isfinite(a):
        return False
    return a == b

def require_typed(a, b, code="REJECTED_INTEGRITY", detail="typed"):
    require(typed_equal(a, b), code, detail)

def exact_keys(obj, keys, code="REJECTED_INTEGRITY"):
    require(type(obj) is dict, code, "not_object")
    require(list(obj.keys()) == list(keys), code, "keys:" + ",".join(map(str, obj.keys())))

def exact_key_set(obj, keys, code="REJECTED_INTEGRITY"):
    require(type(obj) is dict, code, "not_object")
    require(set(obj.keys()) == set(keys), code, "key_set")

def parse_json_bytes(data, code="REJECTED_INTEGRITY"):
    require(type(data) is bytes, code, "bytes")
    try:
        text = data.decode("utf-8")
    except Exception:
        raise Reject(code, "utf8")
    def hook(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                raise Reject(code, "duplicate_key")
            out[k] = v
        return out
    def bad_const(x):
        raise Reject(code, "nonfinite_constant:" + x)
    def finite_float(x):
        v = float(x)
        if not math.isfinite(v):
            raise Reject(code, "nonfinite_float")
        return v
    try:
        obj = json.loads(text, object_pairs_hook=hook, parse_constant=bad_const, parse_float=finite_float)
    except Reject:
        raise
    except Exception:
        raise Reject(code, "json")
    require(type(obj) is dict, code, "top_object")
    return obj

def dump_json(obj):
    return (json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")

def dump_json_obj(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")

def stat_tuple(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)

def stat_tuple_cross(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)

def _lstat_or_none(p):
    try:
        return os.lstat(p)
    except FileNotFoundError:
        return None
    except OSError:
        raise Reject("REJECTED_INTEGRITY", "ancestor_lstat_error:" + str(p))

def _is_reparse_stat(st):
    return bool(getattr(st, "st_file_attributes", 0) & 0x400)

def _is_reparse_path(p):
    st = _lstat_or_none(p)
    if st is None:
        return False
    if os.path.islink(p) or _is_reparse_stat(st):
        return True
    return False

def check_ancestors_no_reparse(path):
    ap = os.path.abspath(path)
    cur = ap
    while True:
        st = _lstat_or_none(cur)
        if st is not None:
            require(not os.path.islink(cur) and not _is_reparse_stat(st), "REJECTED_INTEGRITY", "reparse:" + cur)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return ap

def check_file_no_reparse(path):
    ap = check_ancestors_no_reparse(path)
    st = _lstat_or_none(ap)
    require(st is not None and os.path.isfile(ap) and not os.path.islink(ap), "REJECTED_INTEGRITY", "file:" + ap)
    require(not _is_reparse_stat(st), "REJECTED_INTEGRITY", "reparse_file")
    return ap

def validate_rel_path(p):
    require(type(p) is str and p != "", "REJECTED_INTEGRITY", "rel_path")
    require("\\" not in p and ":" not in p and not p.startswith("/"), "REJECTED_INTEGRITY", "rel_path_sep")
    require(all(ord(c) >= 32 and ord(c) != 127 for c in p), "REJECTED_INTEGRITY", "rel_path_control")
    parts = p.split("/")
    require(all(part not in ("", ".", "..") for part in parts), "REJECTED_INTEGRITY", "rel_path_parts")
    return p

def read_pinned_bytes(path, nbytes, sha, max_bytes=8388608):
    require(is_int(nbytes) and 0 <= nbytes <= max_bytes, "REJECTED_INTEGRITY", "pin_bytes")
    require(is_sha(sha), "REJECTED_INTEGRITY", "pin_sha")
    ap = check_file_no_reparse(path)
    st0 = os.stat(ap)
    require(st0.st_size == nbytes, "REJECTED_INTEGRITY", "pin_size_before")
    h = hashlib.sha256()
    total = 0
    chunks = []
    with open(ap, "rb") as f:
        fst0 = os.fstat(f.fileno())
        require(stat_tuple_cross(fst0) == stat_tuple_cross(st0), "REJECTED_INTEGRITY", "stat_handle")
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            total += len(chunk)
            require(total <= nbytes, "REJECTED_INTEGRITY", "pin_read_over")
            h.update(chunk)
            chunks.append(chunk)
        fst1 = os.fstat(f.fileno())
        require(stat_tuple(fst1) == stat_tuple(fst0), "REJECTED_INTEGRITY", "stat_handle_after")
    st1 = os.stat(ap)
    require(stat_tuple(st1) == stat_tuple(st0), "REJECTED_INTEGRITY", "stat_after_path")
    require(total == nbytes and h.hexdigest() == sha, "REJECTED_INTEGRITY", "pin_sha_mismatch")
    return b"".join(chunks)

def read_limited_bytes(path, max_bytes):
    require(is_int(max_bytes) and max_bytes >= 0, "REJECTED_INTEGRITY", "limited_cap")
    ap = check_file_no_reparse(path)
    st0 = os.stat(ap)
    require(st0.st_size <= max_bytes, "REJECTED_INTEGRITY", "limited_size")
    h = hashlib.sha256()
    total = 0
    chunks = []
    with open(ap, "rb") as f:
        fst0 = os.fstat(f.fileno())
        require(stat_tuple_cross(fst0) == stat_tuple_cross(st0), "REJECTED_INTEGRITY", "stat_handle")
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            total += len(chunk)
            require(total <= max_bytes, "REJECTED_INTEGRITY", "limited_read_over")
            h.update(chunk)
            chunks.append(chunk)
        fst1 = os.fstat(f.fileno())
        require(stat_tuple(fst1) == stat_tuple(fst0), "REJECTED_INTEGRITY", "stat_handle_after_fstat_final")
    st1 = os.stat(ap)
    require(stat_tuple(st1) == stat_tuple(st0), "REJECTED_INTEGRITY", "stat_after")
    return b"".join(chunks), h.hexdigest(), total

def validate_contract_obj(contract, contract_sha):
    exact_keys(contract, CONTRACT_KEYS)
    require(contract["schema"] == "q02b4-serialization.v1", "REJECTED_INTEGRITY", "schema")
    require(contract["state"] == "REVISADO_PARA_AUTORIA_DE_MEDICION_GUARDADA", "REJECTED_INTEGRITY", "state")
    require(contract["scope"] == "SAVED_SERIALIZATION_FEASIBILITY_ONLY", "REJECTED_INTEGRITY", "scope")
    require(type(contract["capture_root"]) is str and contract["capture_root"] != "", "REJECTED_INTEGRITY", "capture_root")
    require_typed(contract["codec"], EXPECTED_CODEC, "REJECTED_INTEGRITY", "codec_fixed")
    require_typed(contract["claims"], EXPECTED_CLAIMS, "REJECTED_INTEGRITY", "claims")
    require_typed(contract["record_schema"], EXPECTED_RECORD_SCHEMA, "REJECTED_INTEGRITY", "record_schema")
    for k in ("inputs_rule", "allocation_rule", "audit_rule", "serialization", "consumer_scope", "decoder_progress", "encoded_measurement", "time_scope"):
        require(type(contract[k]) is str and contract[k] != "", "REJECTED_INTEGRITY", k)
    require(type(contract["states"]) is list and "SAVED_SERIALIZATION_FEASIBILITY_ONLY" in contract["states"], "REJECTED_INTEGRITY", "states")
    exact_key_set(contract["limits"], list(HARD.keys()) + ["encoded_per_file_rule", "positive_decoder_cap"])
    lim = contract["limits"]
    for k, hard in HARD.items():
        require(is_int(lim[k]) and 0 < lim[k] <= hard, "INPUT_OUT_OF_CONTRACT", "limit:" + k)
    require(lim["encoded_per_file_rule"] == "2*N+1024", "REJECTED_INTEGRITY", "encoded_rule")
    require(lim["positive_decoder_cap"] == "min(65536,max(1,N-decoded_total))", "REJECTED_INTEGRITY", "decoder_cap_rule")
    require(lim["workspace_reserved_per_codec_call"] == 134217728, "INPUT_OUT_OF_CONTRACT", "workspace")
    exact_key_set(contract["budgets"], ["author_s", "review_s", "suite_s", "measurement_s", "metadata_consumer_s"])
    for v in contract["budgets"].values():
        require(is_int(v) and v > 0, "REJECTED_INTEGRITY", "budget")
    exact_key_set(contract["files"], PIN_NAMES)
    for name in PIN_NAMES:
        e = contract["files"][name]
        exact_keys(e, ["path", "bytes", "sha256"])
        require(type(e["path"]) is str and e["path"] != "", "REJECTED_INTEGRITY", "pin_path:" + name)
        require(is_int(e["bytes"]) and e["bytes"] >= 0, "REJECTED_INTEGRITY", "pin_bytes:" + name)
        require(is_sha(e["sha256"]), "REJECTED_INTEGRITY", "pin_sha:" + name)
    exact_key_set(contract["runtime_images"], ["executable", "_base_executable", "observed_loaded"])
    for k in ("executable", "_base_executable"):
        e = contract["runtime_images"][k]
        exact_keys(e, ["path", "sha256", "bytes"])
        require(type(e["path"]) is str and is_sha(e["sha256"]) and is_int(e["bytes"]) and e["bytes"] >= 0, "REJECTED_INTEGRITY", "runtime_image")
    require(type(contract["runtime_images"]["observed_loaded"]) is list, "REJECTED_INTEGRITY", "observed_loaded")
    for e in contract["runtime_images"]["observed_loaded"]:
        exact_keys(e, ["path", "bytes", "sha256", "evidence"])
        require(type(e["path"]) is str and is_int(e["bytes"]) and is_sha(e["sha256"]) and type(e["evidence"]) is str, "REJECTED_INTEGRITY", "observed_entry")
    nd = contract["numeric_derivation"]
    require(type(nd) is dict and is_int(nd.get("reservation_bytes")) and nd["reservation_bytes"] == 134217728, "REJECTED_INTEGRITY", "numeric_derivation")
    return contract

def load_contract(contract_path, contract_sha_arg):
    require(is_sha(contract_sha_arg), "REJECTED_INTEGRITY", "contract_sha_arg")
    data, sha, _n = read_limited_bytes(contract_path, 2097152)
    require(sha == contract_sha_arg, "REJECTED_INTEGRITY", "contract_sha_before_parse")
    contract = parse_json_bytes(data)
    validate_contract_obj(contract, contract_sha_arg)
    contract["_contract_sha256"] = contract_sha_arg
    contract["_contract_path"] = os.path.abspath(contract_path)
    return contract

def _validate_completion(obj, stdout_sha, stderr_sha, expected_rc):
    exact_keys(obj, ["rc", "reason", "seconds", "peak_rss", "started", "finished", "identities", "stdout_sha", "stderr_sha"])
    require(is_int(obj["rc"]) and obj["rc"] == expected_rc, "REJECTED_INTEGRITY", "completion_rc")
    require(obj["reason"] is None, "REJECTED_INTEGRITY", "completion_reason")
    require(is_num(obj["seconds"]) and obj["seconds"] >= 0 and is_int(obj["peak_rss"]) and obj["peak_rss"] >= 0 and is_num(obj["started"]) and is_num(obj["finished"]) and obj["finished"] >= obj["started"], "REJECTED_INTEGRITY", "completion_types")
    require(type(obj["identities"]) is dict and len(obj["identities"]) > 0, "REJECTED_INTEGRITY", "completion_identities")
    for k, v in obj["identities"].items():
        require(type(k) is str and k.isdigit() and is_num(v), "REJECTED_INTEGRITY", "completion_identity_types")
    require(obj["stdout_sha"] == stdout_sha and obj["stderr_sha"] == stderr_sha, "REJECTED_INTEGRITY", "completion_stream_sha_forged")
    return obj

def _validate_running(obj):
    exact_keys(obj, ["pid", "birth", "started", "seconds", "executable", "input_sha"])
    require(is_int(obj["pid"]) and obj["pid"] > 0 and is_num(obj["birth"]) and is_num(obj["started"]) and is_int(obj["seconds"]) and obj["seconds"] > 0 and type(obj["executable"]) is str and obj["executable"] != "" and is_sha(obj["input_sha"]), "REJECTED_INTEGRITY", "running")
    require(abs(obj["birth"] - obj["started"]) <= 5.0, "REJECTED_INTEGRITY", "running_birth_window")
    return obj

def _check_running_completion(running, completion, label):
    pid = str(running["pid"])
    require(pid in completion["identities"], "REJECTED_INTEGRITY", label + "_identity_pid")
    require_typed(completion["identities"][pid], running["birth"], "REJECTED_INTEGRITY", label + "_identity_birth")
    require(completion["started"] - 1.0 <= running["started"] <= completion["finished"], "REJECTED_INTEGRITY", label + "_started_window")
    require(completion["started"] - 1.0 <= running["birth"] <= completion["finished"], "REJECTED_INTEGRITY", label + "_birth_window")

def load_metadata(contract):
    files = contract["files"]
    lim = contract["limits"]
    total_meta = 0
    for name in PIN_NAMES:
        e = files[name]
        require(is_int(e["bytes"]) and e["bytes"] <= 4194304, "INPUT_OUT_OF_CONTRACT", "pin_preflight_cap:" + name)
        total_meta += e["bytes"]
        require(total_meta <= lim["metadata_total_bytes"] and total_meta <= HARD["metadata_total_bytes"], "INPUT_OUT_OF_CONTRACT", "metadata_total_preflight")
    require(files["inventory"]["bytes"] <= lim["inventory_bytes"] and files["inventory"]["bytes"] <= HARD["inventory_bytes"], "INPUT_OUT_OF_CONTRACT", "inventory_bytes_preflight_before_read")
    raw = {}
    for name in PIN_NAMES:
        e = files[name]
        raw[name] = read_pinned_bytes(e["path"], e["bytes"], e["sha256"], max_bytes=4194304)
    inv = parse_json_bytes(raw["inventory"])
    exact_keys(inv, ["schema", "files", "total_bytes", "producer_completion_sha256", "scope", "seconds"])
    require(inv["schema"] == "q02b3-saved-inventory.v1" and inv["scope"] == "BOUNDARY_SNAPSHOT_NOT_CONTINUOUS_WATCH" and is_num(inv["seconds"]) and inv["seconds"] >= 0, "REJECTED_INTEGRITY", "inventory_literals")
    require(inv["producer_completion_sha256"] == files["producer_completion_json"]["sha256"], "REJECTED_INTEGRITY", "inventory_completion_pin")
    require(type(inv["files"]) is list and 0 < len(inv["files"]) <= lim["files"], "INPUT_OUT_OF_CONTRACT", "inventory_count")
    require(is_int(inv["total_bytes"]) and 0 <= inv["total_bytes"] <= lim["total_original"], "INPUT_OUT_OF_CONTRACT", "inventory_total")
    seen = set()
    total = 0
    for entry in inv["files"]:
        exact_keys(entry, ["path", "bytes", "sha256"])
        validate_rel_path(entry["path"])
        require(entry["path"] not in seen, "REJECTED_INTEGRITY", "inventory_duplicate")
        seen.add(entry["path"])
        require(is_int(entry["bytes"]) and 0 <= entry["bytes"] <= lim["individual_original"], "INPUT_OUT_OF_CONTRACT", "inventory_file_cap")
        require(is_sha(entry["sha256"]), "REJECTED_INTEGRITY", "inventory_sha")
        total += entry["bytes"]
    require(is_int(total) and typed_equal(total, inv["total_bytes"]), "REJECTED_INTEGRITY", "inventory_total_sum")
    nc = parse_json_bytes(raw["numeric_contract"])
    require(nc.get("schema") == "q02b3.v1" and nc.get("scope") == "NUMERIC_COVERAGE_ONLY", "REJECTED_INTEGRITY", "numeric_contract_literals")
    require(is_sha(nc.get("npz_sha256")), "REJECTED_INTEGRITY", "numeric_contract_npz")
    for k in ("selectors", "oracles"):
        require(type(nc.get(k)) is dict and set(nc[k].keys()) == {"path", "sha256"} and is_sha(nc[k]["sha256"]), "REJECTED_INTEGRITY", "numeric_contract_" + k)
    cls = parse_json_bytes(raw["classification"])
    exact_keys(cls, ["schema", "inventory_sha256", "consumer_sha256", "order", "rows"])
    require(cls["schema"] == "q02b4-classification.v1" and cls["order"] == "exact inventory order", "REJECTED_INTEGRITY", "classification_literals")
    require(cls["inventory_sha256"] == files["inventory"]["sha256"], "REJECTED_INTEGRITY", "classification_inventory_pin")
    require(cls["consumer_sha256"] == files["numeric_consumer"]["sha256"], "REJECTED_INTEGRITY", "classification_consumer_pin")
    require(type(cls["rows"]) is list and len(cls["rows"]) == len(inv["files"]), "REJECTED_INTEGRITY", "classification_rows")
    allowed = {"ACCEPTED_NUMERIC_PREFIX": 0, "UNVERIFIED_TAIL": 1, "HEADER_BOUND_ONLY": 2}
    rank = -1
    header_count = 0
    tail_rows = []
    for i, row in enumerate(cls["rows"]):
        exact_keys(row, ["path", "classification"])
        require(type(row["classification"]) is str and row["path"] == inv["files"][i]["path"], "REJECTED_INTEGRITY", "classification_order")
        require(row["classification"] in allowed, "REJECTED_INTEGRITY", "classification_value")
        r = allowed[row["classification"]]
        require(r >= rank, "REJECTED_INTEGRITY", "classification_sequence")
        rank = r
        if row["classification"] == "UNVERIFIED_TAIL":
            tail_rows.append(row)
        if row["classification"] == "HEADER_BOUND_ONLY":
            header_count += 1
            require(row["path"] == "header.json" and i == len(cls["rows"]) - 1, "REJECTED_INTEGRITY", "classification_header")
    require(header_count == 1, "REJECTED_INTEGRITY", "classification_header_count")
    consumer = parse_json_bytes(raw["numeric_consumer"])
    exact_keys(consumer, ["bindings", "claims", "completed_chains", "coverage_complete", "covered_universe", "errors", "excluded_count", "query_count", "schema", "state", "state_counts", "universe", "unverified_numeric_count", "unverified_tail"])
    require(consumer["schema"] == "q02b3-consumer.v1", "REJECTED_INTEGRITY", "consumer_schema_literal")
    require(consumer["state"] == "VERIFIED_PARTIAL_NUMERIC_COVERAGE", "REJECTED_INTEGRITY", "consumer_state_literal")
    exact_keys(consumer["bindings"], ["contract_sha256", "npz_sha256", "oracles_sha256", "selectors_sha256"])
    require_typed(consumer["bindings"], {"contract_sha256": files["numeric_contract"]["sha256"], "npz_sha256": nc["npz_sha256"], "oracles_sha256": nc["oracles"]["sha256"], "selectors_sha256": nc["selectors"]["sha256"]}, "REJECTED_INTEGRITY", "consumer_bindings_numeric_contract")
    require(type(consumer["errors"]) is list and consumer["errors"] == [], "REJECTED_INTEGRITY", "consumer_errors_empty")
    require(is_int(consumer["unverified_numeric_count"]) and consumer["unverified_numeric_count"] == 0, "REJECTED_INTEGRITY", "consumer_unverified_zero")
    require(type(consumer["coverage_complete"]) is bool and consumer["coverage_complete"] is False, "REJECTED_INTEGRITY", "consumer_coverage_partial")
    for k in ("completed_chains", "covered_universe", "excluded_count", "query_count", "universe"):
        require(is_int(consumer[k]) and consumer[k] >= 0, "REJECTED_INTEGRITY", "consumer_int:" + k)
    require(type(nc.get("expected")) is dict and is_int(nc["expected"].get("universe")), "REJECTED_INTEGRITY", "required_numeric_universe")
    require(consumer["universe"] == nc["expected"]["universe"], "REJECTED_INTEGRITY", "consumer_universe_binding")
    require(consumer["covered_universe"] <= consumer["universe"], "REJECTED_INTEGRITY", "consumer_covered_le_universe")
    require(type(consumer["state_counts"]) is dict and all(type(k) is str and is_int(v) and v >= 0 for k, v in consumer["state_counts"].items()), "REJECTED_INTEGRITY", "consumer_state_counts")
    claim_keys = ("angle_state", "c1", "calibration_ready", "controls", "human_cases", "map_repaired", "natural_positive_count")
    require(all(k in nc for k in claim_keys), "REJECTED_INTEGRITY", "required_numeric_claims")
    require_typed(consumer["claims"], {k:nc[k] for k in claim_keys}, "REJECTED_INTEGRITY", "consumer_claims_binding")
    require(consumer["covered_universe"] == consumer["excluded_count"] + consumer["query_count"] == sum(consumer["state_counts"].values()), "REJECTED_INTEGRITY", "consumer_count_reconciliation")
    exact_keys(consumer["unverified_tail"], ["chain_id", "files"])
    require(is_int(consumer["unverified_tail"]["chain_id"]) and consumer["unverified_tail"]["chain_id"] >= 0, "REJECTED_INTEGRITY", "tail_chain")
    require(type(consumer["unverified_tail"]["files"]) is list and len(consumer["unverified_tail"]["files"]) > 0 and all(type(x) is str and "/" not in x and "\\" not in x for x in consumer["unverified_tail"]["files"]), "REJECTED_INTEGRITY", "tail_files")
    cid = consumer["unverified_tail"]["chain_id"]
    require(consumer["completed_chains"] == cid, "REJECTED_INTEGRITY", "completed_chains_vs_tail")
    accepted_chains = set()
    for row in cls["rows"]:
        if row["classification"] == "ACCEPTED_NUMERIC_PREFIX":
            head, sep, leaf = row["path"].partition("/")
            require(sep == "/" and leaf != "" and len(head) == 10 and head.startswith("chain-") and head[6:].isdigit(), "REJECTED_INTEGRITY", "accepted_chain_path")
            chain = int(head[6:])
            require(0 <= chain < cid, "REJECTED_INTEGRITY", "accepted_outside_numeric_prefix")
            accepted_chains.add(chain)
    require(accepted_chains == set(range(cid)), "REJECTED_INTEGRITY", "accepted_prefix_chain_coverage")
    expected_tail_paths = ["chain-%04d/%s" % (cid, x) for x in consumer["unverified_tail"]["files"]]
    require_typed([r["path"] for r in tail_rows], expected_tail_paths, "REJECTED_INTEGRITY", "classification_tail_exact")
    prod_comp = _validate_completion(parse_json_bytes(raw["producer_completion_json"]), sha256_bytes(raw["producer_stdout"]), sha256_bytes(raw["producer_stderr"]), 1)
    cons_comp = _validate_completion(parse_json_bytes(raw["consumer_completion_json"]), sha256_bytes(raw["consumer_stdout"]), sha256_bytes(raw["consumer_stderr"]), 2)
    prod_run = _validate_running(parse_json_bytes(raw["producer_running_json"]))
    cons_run = _validate_running(parse_json_bytes(raw["consumer_running_json"]))
    _check_running_completion(prod_run, prod_comp, "producer")
    _check_running_completion(cons_run, cons_comp, "consumer")
    require(prod_run["pid"] != cons_run["pid"], "REJECTED_INTEGRITY", "running_pid_distinct")
    runtime = parse_json_bytes(raw["runtime"])
    require(runtime.get("zlib_runtime") == "1.3.2" and runtime.get("zlib_compile") == "1.3.2", "REJECTED_INTEGRITY", "runtime_zlib")
    require(type(runtime.get("sys_version")) is str and runtime["sys_version"].startswith("3.12.14"), "REJECTED_INTEGRITY", "runtime_python")
    require("shore_multiscale_coverage_ev112" not in sys.modules, "REJECTED_INTEGRITY", "numeric_guard_imported")
    return {"raw": raw, "inventory": inv, "classification": cls, "numeric_consumer": consumer, "numeric_contract": nc, "runtime": runtime, "total_meta": total_meta, "producer_running": prod_run, "consumer_running": cons_run, "producer_completion": prod_comp, "consumer_completion": cons_comp}

def check_runtime_images(contract):
    ri = contract["runtime_images"]
    for k in ("executable", "_base_executable"):
        e = ri[k]
        read_pinned_bytes(e["path"], e["bytes"], e["sha256"], max_bytes=33554432)
    for e in ri["observed_loaded"]:
        read_pinned_bytes(e["path"], e["bytes"], e["sha256"], max_bytes=33554432)
    exe = os.path.abspath(sys.executable)
    require(os.path.abspath(ri["executable"]["path"]) == exe, "REJECTED_INTEGRITY", "runtime_executable_path")
    base = getattr(sys, "_base_executable", "") or sys.executable
    require(os.path.abspath(ri["_base_executable"]["path"]) == os.path.abspath(base), "REJECTED_INTEGRITY", "runtime_base_executable_path")

def validate_preloads(preloads):
    require(type(preloads) is list, "REJECTED_INTEGRITY", "preloads_type")
    for r in preloads:
        exact_keys(r, PRELOAD_KEYS)
        require(type(r["module"]) is str and r["module"] != "" and type(r["origin"]) is str, "REJECTED_INTEGRITY", "preload_module")
        require(is_int(r["bytes"]) and r["bytes"] >= 0, "REJECTED_INTEGRITY", "preload_bytes")
        if r["path"] is None:
            require(r["bytes"] == 0 and r["sha256"] is None, "REJECTED_INTEGRITY", "preload_builtin_shape")
        else:
            require(type(r["path"]) is str and is_sha(r["sha256"]), "REJECTED_INTEGRITY", "preload_file_shape")
    return preloads

def validate_counters(counters):
    exact_keys(counters, AUDIT_COUNTER_KEYS)
    for v in counters.values():
        require(is_int(v) and v >= 0, "REJECTED_INTEGRITY", "counter_int")
    return counters

def validate_runtime_checks(rc):
    exact_keys(rc, RUNTIME_CHECK_KEYS)
    for v in rc.values():
        require(v is True, "REJECTED_INTEGRITY", "runtime_check_true_bool")
    return rc

def validate_selftests(st):
    exact_keys(st, SELFTEST_KEYS)
    for v in st.values():
        require(v is True, "REJECTED_INTEGRITY", "selftest_true_bool")
    return st

def parse_audit_ndjson(data, receipts_sha=None, receipts_n=None):
    require(type(data) is bytes and len(data) > 0 and data.endswith(b"\n"), "REJECTED_INTEGRITY", "audit_truncated_line")
    lines = data.split(b"\n")[:-1]
    require(1 <= len(lines) <= 2 and all(x != b"" for x in lines), "REJECTED_INTEGRITY", "audit_ndjson_lines")
    recs = [parse_json_bytes(x) for x in lines]
    startup = recs[0]
    exact_keys(startup, AUDIT_STARTUP_KEYS)
    require(startup["kind"] == "audit" and startup["schema"] == "q02b4-audit.v1" and startup["record"] == "startup", "REJECTED_INTEGRITY", "audit_startup_kind")
    require(is_sha(startup["contract_sha256"]) and is_sha(startup["inventory_sha256"]) and is_sha(startup["classification_sha256"]), "REJECTED_INTEGRITY", "audit_startup_sha")
    validate_runtime_checks(startup["runtime_checks"])
    validate_preloads(startup["preloads"])
    validate_selftests(startup["selftests"])
    validate_counters(startup["counters"])
    require(is_int(startup["allowed_path_count"]) and startup["allowed_path_count"] > 0, "REJECTED_INTEGRITY", "audit_allowed_count")
    require(startup["counters"]["import_denied"] >= 1 and startup["counters"]["open_denied"] >= 1, "REJECTED_INTEGRITY", "audit_startup_counters")
    require(startup["counters"]["capture_open_allowed"] == 0 and startup["counters"]["capture_attempts"] == 0, "REJECTED_INTEGRITY", "startup_before_capture")
    terminal = None
    if len(recs) == 2:
        terminal = recs[1]
        exact_keys(terminal, AUDIT_TERMINAL_KEYS)
        require(terminal["kind"] == "audit" and terminal["schema"] == "q02b4-audit.v1" and terminal["record"] == "terminal", "REJECTED_INTEGRITY", "audit_terminal_kind")
        require(terminal["contract_sha256"] == startup["contract_sha256"], "REJECTED_INTEGRITY", "audit_terminal_contract")
        validate_counters(terminal["counters"])
        require(all(terminal["counters"][k] >= startup["counters"][k] for k in AUDIT_COUNTER_KEYS), "REJECTED_INTEGRITY", "terminal_counters_monotone")
        require(is_int(terminal["receipts_bytes"]) and terminal["receipts_bytes"] >= 0 and is_sha(terminal["receipts_sha256"]), "REJECTED_INTEGRITY", "audit_terminal_receipts")
        require(is_int(terminal["receipts_records"]) and is_int(terminal["complete_files"]) and is_int(terminal["expected_files"]), "REJECTED_INTEGRITY", "audit_terminal_counts")
        require(is_int(terminal["capture_open_allowed"]) and terminal["capture_open_allowed"] == terminal["counters"]["capture_open_allowed"], "REJECTED_INTEGRITY", "audit_terminal_capture_counter")
        require_typed(terminal["claims"], EXPECTED_CLAIMS, "REJECTED_INTEGRITY", "audit_terminal_claims")
        if receipts_sha is not None:
            require(terminal["receipts_sha256"] == receipts_sha and terminal["receipts_bytes"] == receipts_n, "REJECTED_INTEGRITY", "audit_terminal_receipts_binding_stale")
    return startup, terminal

def preload_and_record():
    mods = ["argparse", "hashlib", "json", "os", "sys", "zlib", "pathlib", "stat"]
    for name in mods:
        __import__(name)
    records = []
    seen_paths = set()
    seen_mods = set()
    for name in sorted(sys.modules.keys()):
        if name in seen_mods:
            continue
        seen_mods.add(name)
        mod = sys.modules.get(name)
        if mod is None:
            continue
        f = getattr(mod, "__file__", None)
        if type(f) is not str or not f:
            spec = getattr(mod, "__spec__", None)
            origin = getattr(spec, "origin", None) if spec is not None else None
            records.append({"module": name, "path": None, "bytes": 0, "sha256": None, "origin": str(origin) if origin else "builtin/frozen"})
            continue
        ap = os.path.abspath(f)
        if ap in seen_paths:
            continue
        seen_paths.add(ap)
        require(os.path.isfile(ap), "REJECTED_INTEGRITY", "preload_declared_missing:" + ap)
        size = os.path.getsize(ap)
        require(size <= 8388608, "REJECTED_INTEGRITY", "preload_cap_before_retain:" + ap)
        h = hashlib.sha256()
        total = 0
        with open(ap, "rb") as fh:
            st0 = os.fstat(fh.fileno())
            while True:
                c = fh.read(65536)
                if not c:
                    break
                total += len(c)
                require(total <= 8388608, "REJECTED_INTEGRITY", "preload_read_cap")
                h.update(c)
            st1 = os.fstat(fh.fileno())
            require(stat_tuple(st1) == stat_tuple(st0) and total == size, "REJECTED_INTEGRITY", "preload_stat")
        records.append({"module": name, "path": ap, "bytes": total, "sha256": h.hexdigest(), "origin": "file"})
    records.sort(key=lambda r: (r["path"] or "", r["module"]))
    return records

class AuditState:
    def __init__(self, allowed, capture_root=None):
        self.allowed = {}
        for p, kind in allowed.items():
            self.allowed[os.path.normcase(os.path.abspath(p))] = kind
        self.capture_root = os.path.normcase(os.path.abspath(capture_root)) if capture_root else None
        self.counters = {k: 0 for k in AUDIT_COUNTER_KEYS}
        self.paths_seen = set()
        self.installed = False
    def _under_capture(self, ap):
        return self.capture_root is not None and (ap == self.capture_root or ap.startswith(self.capture_root + os.sep))
    def hook(self, event, args):
        if event == "import":
            self.counters["import_denied"] += 1
            raise PermissionError("import_after_audit_hook")
        if event != "open":
            return
        path = args[0] if len(args) > 0 else None
        mode = args[1] if len(args) > 1 else None
        flags = args[2] if len(args) > 2 else 0
        if type(path) is int or isinstance(path, bool):
            self.counters["fd_denied"] += 1
            self.counters["open_denied"] += 1
            raise PermissionError("open_fd_denied")
        if type(path) is bytes:
            path = os.fsdecode(path)
        if type(path) is not str:
            try:
                path = os.fspath(path)
            except Exception:
                self.counters["open_denied"] += 1
                raise PermissionError("open_path_denied")
        ap = os.path.normcase(os.path.abspath(path))
        if self._under_capture(ap):
            self.counters["capture_attempts"] += 1
        if len(self.paths_seen) < 10000:
            self.paths_seen.add(ap)
        kind = self.allowed.get(ap)
        if kind is None:
            self.counters["unknown_denied"] += 1
            self.counters["open_denied"] += 1
            raise PermissionError("open_unknown_denied:" + ap)
        writing = False
        if type(mode) is str and any(c in mode for c in "wax+"):
            writing = True
        if type(flags) is int and flags & (getattr(os, "O_WRONLY", 1) | getattr(os, "O_RDWR", 2) | getattr(os, "O_CREAT", 64) | getattr(os, "O_APPEND", 1024) | getattr(os, "O_TRUNC", 512)):
            if kind == "output":
                writing = True
            elif type(mode) is str and mode.startswith("r") and "+" not in mode and not (flags & (getattr(os, "O_WRONLY", 1) | getattr(os, "O_RDWR", 2) | getattr(os, "O_APPEND", 1024) | getattr(os, "O_TRUNC", 512))):
                writing = False
            else:
                writing = True if flags & (getattr(os, "O_WRONLY", 1) | getattr(os, "O_RDWR", 2) | getattr(os, "O_APPEND", 1024) | getattr(os, "O_TRUNC", 512)) else writing
        if writing and kind == "input":
            self.counters["write_denied"] += 1
            self.counters["open_denied"] += 1
            raise PermissionError("write_input_denied")
        self.counters["open_allowed"] += 1
        if self._under_capture(ap):
            self.counters["capture_open_allowed"] += 1
    def install(self):
        sys.addaudithook(self.hook)
        self.installed = True

def run_selftests(state, output_dir):
    results = {"hook_installed": bool(state.installed), "forbidden_open_denied": False, "forbidden_import_denied": False}
    before = state.counters["open_denied"]
    try:
        open(os.path.join(os.path.abspath(output_dir), "__selftest_forbidden__.txt"), "rb")
    except PermissionError:
        results["forbidden_open_denied"] = state.counters["open_denied"] > before
    except Exception:
        results["forbidden_open_denied"] = False
    before_i = state.counters["import_denied"]
    candidate = None
    for name in ("csv", "sqlite3", "zipfile", "email"):
        if name not in sys.modules:
            candidate = name
            break
    if candidate is not None:
        try:
            __import__(candidate)
        except PermissionError:
            results["forbidden_import_denied"] = state.counters["import_denied"] > before_i
        except Exception:
            results["forbidden_import_denied"] = False
    return results

def inventory_walk_check(capture_root, inventory):
    root = check_ancestors_no_reparse(capture_root)
    require(os.path.isdir(root), "REJECTED_INTEGRITY", "capture_root_missing")
    expected = {}
    for e in inventory["files"]:
        expected[e["path"]] = e["bytes"]
    found = {}
    stack = [root]
    while stack:
        cur = stack.pop()
        require(not _is_reparse_path(cur), "REJECTED_INTEGRITY", "reparse_ancestor")
        with os.scandir(cur) as it:
            entries = list(it)
        for ent in entries:
            require(not ent.is_symlink(), "REJECTED_INTEGRITY", "symlink_entry")
            try:
                st = ent.stat(follow_symlinks=False)
            except OSError:
                raise Reject("REJECTED_INTEGRITY", "entry_stat_error")
            require(not (getattr(st, "st_file_attributes", 0) & 0x400), "REJECTED_INTEGRITY", "reparse_entry")
            if ent.is_dir(follow_symlinks=False):
                stack.append(ent.path)
            elif ent.is_file(follow_symlinks=False):
                rel = os.path.relpath(ent.path, root).replace(os.sep, "/")
                validate_rel_path(rel)
                require(rel not in found, "REJECTED_INTEGRITY", "duplicate_walk")
                found[rel] = st.st_size
            else:
                raise Reject("REJECTED_INTEGRITY", "special_entry")
    require(set(found.keys()) == set(expected.keys()), "REJECTED_INTEGRITY", "capture_extra_missing")
    for k in expected:
        require(found[k] == expected[k], "REJECTED_INTEGRITY", "capture_size:" + k)
    return found
