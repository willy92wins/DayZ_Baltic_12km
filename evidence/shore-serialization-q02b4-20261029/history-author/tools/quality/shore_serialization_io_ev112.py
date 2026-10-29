import hashlib
import json
import os
import sys

HARD = {"files": 2618, "individual_original": 16777216, "total_original": 2147483648, "inventory_bytes": 2097152, "all_output_bytes": 2097152, "rss_bytes": 536870912, "workspace_reserved_per_codec_call": 134217728, "metadata_total_bytes": 4194304}
EXPECTED_CODEC = {"name": "zlib", "level": 1, "method": 8, "wbits": 15, "memLevel": 8, "strategy": 0, "dictionary": None, "encoder_flush": 4, "decoder_flush_forbidden": True, "input_chunk_bytes": 65536, "decoder_max_length": 65536, "runtime_version": "1.3.2", "compile_version": "1.3.2", "python_version": "3.12.14"}
EXPECTED_CLAIMS = {"map_repaired": False, "build_ready": False, "natural_calibration": False, "human_cases_resolved": 0, "c1": "NOT_REVIEWED", "missing_chain_projection": False, "independent_codec_implementation": False, "audit_security_sandbox": False}
EXPECTED_RECORD_SCHEMA = {"header": ["kind", "schema", "contract_sha256", "inventory_sha256", "classification_sha256", "codec", "claims"], "file": ["kind", "index", "path", "classification", "original_bytes", "encoded_bytes", "decoded_bytes", "original_sha256", "encoded_sha256", "decoded_sha256", "eof", "unused_bytes", "unconsumed_bytes", "state"], "final": ["kind", "state", "complete_files", "expected_files", "complete", "totals_by_classification", "reason", "claims"]}
CONTRACT_KEYS = ["schema", "state", "scope", "files", "capture_root", "codec", "runtime_images", "limits", "budgets", "inputs_rule", "allocation_rule", "audit_rule", "record_schema", "serialization", "states", "consumer_scope", "claims", "numeric_derivation", "decoder_progress", "encoded_measurement", "time_scope"]
PIN_NAMES = ["inventory", "numeric_consumer", "numeric_contract", "numeric_guard_source", "runtime", "audit_probe", "audit_result", "audit_completion", "classification", "oracles", "derivation", "producer_running_json", "producer_completion_json", "producer_stdout", "producer_stderr", "consumer_running_json", "consumer_completion_json", "consumer_stdout", "consumer_stderr"]

class Reject(Exception):
    def __init__(self, code, detail=""):
        super().__init__(code + ((":" + detail) if detail else ""))
        self.code = code

def is_int(v):
    return type(v) is int

def is_num(v):
    return type(v) in (int, float)

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()

def is_sha(v):
    return type(v) is str and len(v) == 64 and all(c in "0123456789abcdef" for c in v)

def require(cond, code, detail=""):
    if not cond:
        raise Reject(code, detail)

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
    try:
        obj = json.loads(text, object_pairs_hook=hook)
    except Reject:
        raise
    except Exception:
        raise Reject(code, "json")
    require(type(obj) is dict, code, "top_object")
    return obj

def dump_json(obj):
    return (json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")

def dump_json_obj(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

def _is_reparse_path(p):
    try:
        if os.path.islink(p):
            return True
    except Exception:
        return True
    try:
        st = os.lstat(p)
    except Exception:
        return False
    attrs = getattr(st, "st_file_attributes", 0)
    return bool(attrs & 0x400)

def check_ancestors_no_reparse(path):
    ap = os.path.abspath(path)
    cur = ap
    while True:
        if os.path.exists(cur) or os.path.islink(cur):
            require(not _is_reparse_path(cur), "REJECTED_INTEGRITY", "reparse:" + cur)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return ap

def check_file_no_reparse(path):
    ap = check_ancestors_no_reparse(path)
    require(os.path.isfile(ap) and not os.path.islink(ap), "REJECTED_INTEGRITY", "file:" + ap)
    require(not _is_reparse_path(ap), "REJECTED_INTEGRITY", "reparse_file")
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
        require((fst0.st_dev, fst0.st_ino, fst0.st_size) == (st0.st_dev, st0.st_ino, st0.st_size), "REJECTED_INTEGRITY", "stat_handle")
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            total += len(chunk)
            require(total <= nbytes, "REJECTED_INTEGRITY", "pin_read_over")
            h.update(chunk)
            chunks.append(chunk)
        fst1 = os.fstat(f.fileno())
    st1 = os.stat(ap)
    require((fst1.st_dev, fst1.st_ino, fst1.st_size) == (st0.st_dev, st0.st_ino, st0.st_size), "REJECTED_INTEGRITY", "stat_after_handle")
    require((st1.st_dev, st1.st_ino, st1.st_size) == (st0.st_dev, st0.st_ino, st0.st_size), "REJECTED_INTEGRITY", "stat_after_path")
    require(total == nbytes and h.hexdigest() == sha, "REJECTED_INTEGRITY", "pin_sha_mismatch")
    return b"".join(chunks)

def read_limited_bytes(path, max_bytes):
    ap = check_file_no_reparse(path)
    st0 = os.stat(ap)
    require(st0.st_size <= max_bytes, "REJECTED_INTEGRITY", "limited_size")
    h = hashlib.sha256()
    total = 0
    chunks = []
    with open(ap, "rb") as f:
        fst0 = os.fstat(f.fileno())
        require((fst0.st_dev, fst0.st_ino) == (st0.st_dev, st0.st_ino), "REJECTED_INTEGRITY", "stat_handle")
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            total += len(chunk)
            require(total <= max_bytes, "REJECTED_INTEGRITY", "limited_read_over")
            h.update(chunk)
            chunks.append(chunk)
    st1 = os.stat(ap)
    require((st1.st_dev, st1.st_ino, st1.st_size) == (st0.st_dev, st0.st_ino, st0.st_size), "REJECTED_INTEGRITY", "stat_after")
    return b"".join(chunks), h.hexdigest(), total

def validate_contract_obj(contract, contract_sha):
    exact_keys(contract, CONTRACT_KEYS)
    require(contract["schema"] == "q02b4-serialization.v1", "REJECTED_INTEGRITY", "schema")
    require(contract["state"] == "REVISADO_PARA_AUTORIA_DE_MEDICION_GUARDADA", "REJECTED_INTEGRITY", "state")
    require(contract["scope"] == "SAVED_SERIALIZATION_FEASIBILITY_ONLY", "REJECTED_INTEGRITY", "scope")
    require(type(contract["capture_root"]) is str and contract["capture_root"] != "", "REJECTED_INTEGRITY", "capture_root")
    require(contract["codec"] == EXPECTED_CODEC, "REJECTED_INTEGRITY", "codec_fixed")
    require(contract["claims"] == EXPECTED_CLAIMS, "REJECTED_INTEGRITY", "claims")
    require(contract["record_schema"] == EXPECTED_RECORD_SCHEMA, "REJECTED_INTEGRITY", "record_schema")
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
    require(is_num(obj["seconds"]) and is_int(obj["peak_rss"]) and is_num(obj["started"]) and is_num(obj["finished"]), "REJECTED_INTEGRITY", "completion_types")
    require(type(obj["identities"]) is dict and len(obj["identities"]) > 0, "REJECTED_INTEGRITY", "completion_identities")
    require(obj["stdout_sha"] == stdout_sha and obj["stderr_sha"] == stderr_sha, "REJECTED_INTEGRITY", "completion_stream_sha")

def _validate_running(obj):
    exact_keys(obj, ["pid", "birth", "started", "seconds", "executable", "input_sha"])
    require(is_int(obj["pid"]) and is_num(obj["birth"]) and is_num(obj["started"]) and is_int(obj["seconds"]) and type(obj["executable"]) is str and is_sha(obj["input_sha"]), "REJECTED_INTEGRITY", "running")

def load_metadata(contract):
    files = contract["files"]
    lim = contract["limits"]
    total_meta = 0
    raw = {}
    for name in PIN_NAMES:
        e = files[name]
        total_meta += e["bytes"]
        require(total_meta <= lim["metadata_total_bytes"], "INPUT_OUT_OF_CONTRACT", "metadata_total")
        require(total_meta <= HARD["metadata_total_bytes"], "INPUT_OUT_OF_CONTRACT", "metadata_total_hard")
        raw[name] = read_pinned_bytes(e["path"], e["bytes"], e["sha256"], max_bytes=4194304)
    require(files["inventory"]["bytes"] <= lim["inventory_bytes"], "INPUT_OUT_OF_CONTRACT", "inventory_bytes")
    inv = parse_json_bytes(raw["inventory"])
    exact_keys(inv, ["schema", "files", "total_bytes", "producer_completion_sha256", "scope", "seconds"])
    require(type(inv["schema"]) is str and type(inv["scope"]) is str and is_num(inv["seconds"]), "REJECTED_INTEGRITY", "inventory_top")
    require(inv["producer_completion_sha256"] == files["producer_completion_json"]["sha256"], "REJECTED_INTEGRITY", "inventory_completion_pin")
    require(type(inv["files"]) is list and 0 < len(inv["files"]) <= lim["files"], "INPUT_OUT_OF_CONTRACT", "inventory_count")
    require(is_int(inv["total_bytes"]) and inv["total_bytes"] <= lim["total_original"], "INPUT_OUT_OF_CONTRACT", "inventory_total")
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
    require(total == inv["total_bytes"], "REJECTED_INTEGRITY", "inventory_total_sum")
    cls = parse_json_bytes(raw["classification"])
    exact_keys(cls, ["schema", "inventory_sha256", "consumer_sha256", "order", "rows"])
    require(cls["inventory_sha256"] == files["inventory"]["sha256"], "REJECTED_INTEGRITY", "classification_inventory_pin")
    require(cls["consumer_sha256"] == files["numeric_consumer"]["sha256"], "REJECTED_INTEGRITY", "classification_consumer_pin")
    require(type(cls["order"]) is str and type(cls["rows"]) is list and len(cls["rows"]) == len(inv["files"]), "REJECTED_INTEGRITY", "classification_rows")
    allowed = {"ACCEPTED_NUMERIC_PREFIX": 0, "UNVERIFIED_TAIL": 1, "HEADER_BOUND_ONLY": 2}
    rank = -1
    header_count = 0
    for i, row in enumerate(cls["rows"]):
        exact_keys(row, ["path", "classification"])
        require(row["path"] == inv["files"][i]["path"], "REJECTED_INTEGRITY", "classification_order")
        require(row["classification"] in allowed, "REJECTED_INTEGRITY", "classification_value")
        r = allowed[row["classification"]]
        require(r >= rank, "REJECTED_INTEGRITY", "classification_sequence")
        rank = r
        if row["classification"] == "HEADER_BOUND_ONLY":
            header_count += 1
            require(row["path"] == "header.json" and i == len(cls["rows"]) - 1, "REJECTED_INTEGRITY", "classification_header")
    require(header_count == 1, "REJECTED_INTEGRITY", "classification_header_count")
    consumer = parse_json_bytes(raw["numeric_consumer"])
    exact_keys(consumer, ["bindings", "claims", "completed_chains", "coverage_complete", "covered_universe", "errors", "excluded_count", "query_count", "schema", "state", "state_counts", "universe", "unverified_numeric_count", "unverified_tail"])
    require(type(consumer["bindings"]) is dict and consumer["bindings"].get("contract_sha256") == files["numeric_contract"]["sha256"], "REJECTED_INTEGRITY", "consumer_binding")
    require(is_int(consumer["completed_chains"]) and type(consumer["coverage_complete"]) is bool and type(consumer["errors"]) is list, "REJECTED_INTEGRITY", "consumer_types")
    prod_comp = parse_json_bytes(raw["producer_completion_json"])
    cons_comp = parse_json_bytes(raw["consumer_completion_json"])
    _validate_completion(prod_comp, sha256_bytes(raw["producer_stdout"]), sha256_bytes(raw["producer_stderr"]), 1)
    _validate_completion(cons_comp, sha256_bytes(raw["consumer_stdout"]), sha256_bytes(raw["consumer_stderr"]), 2)
    _validate_running(parse_json_bytes(raw["producer_running_json"]))
    _validate_running(parse_json_bytes(raw["consumer_running_json"]))
    runtime = parse_json_bytes(raw["runtime"])
    require(runtime.get("zlib_runtime") == "1.3.2" and runtime.get("zlib_compile") == "1.3.2", "REJECTED_INTEGRITY", "runtime_zlib")
    require(type(runtime.get("sys_version")) is str and runtime["sys_version"].startswith("3.12.14"), "REJECTED_INTEGRITY", "runtime_python")
    require("shore_multiscale_coverage_ev112" not in sys.modules, "REJECTED_INTEGRITY", "numeric_guard_imported")
    return {"raw": raw, "inventory": inv, "classification": cls, "numeric_consumer": consumer, "runtime": runtime, "total_meta": total_meta}

def check_runtime_images(contract):
    ri = contract["runtime_images"]
    for k in ("executable", "_base_executable"):
        e = ri[k]
        read_pinned_bytes(e["path"], e["bytes"], e["sha256"], max_bytes=33554432)
    for e in ri["observed_loaded"]:
        read_pinned_bytes(e["path"], e["bytes"], e["sha256"], max_bytes=33554432)
    exe = os.path.abspath(sys.executable)
    require(os.path.abspath(ri["executable"]["path"]) == exe, "REJECTED_INTEGRITY", "runtime_executable_path")

def preload_and_record():
    mods = ["argparse", "hashlib", "json", "os", "sys", "zlib", "pathlib", "stat"]
    for name in mods:
        __import__(name)
    records = []
    seen = set()
    for name in sorted(sys.modules.keys()):
        mod = sys.modules.get(name)
        if mod is None:
            continue
        f = getattr(mod, "__file__", None)
        if type(f) is not str or not f or f in seen:
            continue
        seen.add(f)
        try:
            ap = os.path.abspath(f)
            if not os.path.isfile(ap):
                continue
            data_len = os.path.getsize(ap)
            if data_len > 8388608:
                continue
            h = hashlib.sha256()
            with open(ap, "rb") as fh:
                while True:
                    c = fh.read(65536)
                    if not c:
                        break
                    h.update(c)
            records.append({"module": name, "path": ap, "bytes": data_len, "sha256": h.hexdigest()})
        except Exception:
            continue
    records.sort(key=lambda r: r["path"])
    return records

class AuditState:
    def __init__(self, allowed, capture_root=None):
        self.allowed = {}
        for p, kind in allowed.items():
            self.allowed[os.path.normcase(os.path.abspath(p))] = kind
        self.capture_root = os.path.normcase(os.path.abspath(capture_root)) if capture_root else None
        self.counters = {"open_allowed": 0, "open_denied": 0, "import_denied": 0, "capture_open_allowed": 0, "capture_attempts": 0, "write_denied": 0, "fd_denied": 0, "unknown_denied": 0}
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
        if type(flags) is int and flags & (getattr(os, "O_WRONLY", 1) | getattr(os, "O_RDWRONLY", 2) | getattr(os, "O_CREAT", 64) | getattr(os, "O_APPEND", 1024) | getattr(os, "O_TRUNC", 512)):
            if type(mode) is str and "r" in mode and "+" not in mode and flags & getattr(os, "O_CREAT", 64) == 0 and flags & (getattr(os, "O_WRONLY", 1) | getattr(os, "O_RDWRONLY", 2)) == 0:
                writing = False
            elif kind == "output":
                writing = True
            elif type(mode) is str and mode.startswith("r") and "+" not in mode:
                writing = False
            else:
                writing = True if flags & (getattr(os, "O_WRONLY", 1) | getattr(os, "O_RDWRONLY", 2) | getattr(os, "O_APPEND", 1024) | getattr(os, "O_TRUNC", 512)) else writing
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
                attrs = getattr(ent.stat(follow_symlinks=False), "st_file_attributes", 0)
            except Exception:
                attrs = 0
            require(not (attrs & 0x400), "REJECTED_INTEGRITY", "reparse_entry")
            if ent.is_dir(follow_symlinks=False):
                stack.append(ent.path)
            elif ent.is_file(follow_symlinks=False):
                rel = os.path.relpath(ent.path, root).replace(os.sep, "/")
                validate_rel_path(rel)
                require(rel not in found, "REJECTED_INTEGRITY", "duplicate_walk")
                found[rel] = ent.stat(follow_symlinks=False).st_size
            else:
                raise Reject("REJECTED_INTEGRITY", "special_entry")
    require(set(found.keys()) == set(expected.keys()), "REJECTED_INTEGRITY", "capture_extra_missing")
    for k in expected:
        require(found[k] == expected[k], "REJECTED_INTEGRITY", "capture_size:" + k)
    return found
