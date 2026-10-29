import argparse
import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
ALLOWED_STATES = {"NOT_EVALUATED", "CONTEXT_ONLY_UNCONFIRMED", "FINDING_UNRESOLVED", "MATERIALIZATION_DIFFERENT"}
FIXED_IDS = ["NARVA-VIS-01", "NARVA-VIS-02", "NARVA-VIS-03", "KIT118-VIS-01", "KIT118-VIS-02", "CONT65-VIS-01", "ROAD49-RIVER-VIS-01", "CROSSING-VIS-01", "RELIEF-EAST-VIS-01"]
FIXED_DOMAINS = {"native_candidate": "CONTEXT_ONLY_UNCONFIRMED", "road_model_not_evaluated": "NOT_EVALUATED", "native_or_model_unresolved": "CONTEXT_ONLY_UNCONFIRMED", "model_not_evaluated": "NOT_EVALUATED", "model_road_not_evaluated": "NOT_EVALUATED", "unknown": "NOT_EVALUATED"}
FIXED_CENSUS = [("native_candidate", [2391, 6941]), ("road_model_not_evaluated", [2391, 6941]), ("native_or_model_unresolved", [2391, 6941]), ("model_not_evaluated", [8253, 9038]), ("model_road_not_evaluated", [8253, 9038]), ("model_not_evaluated", [5162, 5865]), ("unknown", [5295.7, 5999.9]), ("road_model_not_evaluated", [4789.51465, 5516.52197]), ("native_candidate", [11790, 2400])]
FIXED_OBSERVED_BUILD = {"mod": "@DayZ_Baltic_EV112_Kit7Nav8Load1", "world_sha256": "f0e0e6b99da08b48f62ee47fa72b8905a5c9843bee4a30cefa18f517ddb1f603", "pilot_sha256": "3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6", "water_sha256": "97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43"}
FIXED_LAYERS = {"NARVA-VIS-01": ["terrain", "visual_models", "water"], "NARVA-VIS-02": ["road_models", "road_corridor", "approaches", "water"], "NARVA-VIS-03": ["terrain", "visual_models", "water"], "KIT118-VIS-01": ["riverbed_models", "terrain", "water"], "KIT118-VIS-02": ["riverbed_models", "road_corridor", "approaches", "water"], "CONT65-VIS-01": ["riverbed_models", "terrain", "water"], "ROAD49-RIVER-VIS-01": ["terrain", "visual_models", "water"], "CROSSING-VIS-01": ["road_corridor", "road_models", "approaches", "water"], "RELIEF-EAST-VIS-01": ["terrain", "visual_models", "water"]}
FIXED_SCOPES = [("forest-dense", "LOCAL_VISUAL_OK"), ("causeway-c0", "LOCAL_VISUAL_OK"), ("road-49", "LOCAL_VISUAL_OK_WITH_PAVING_PENDING_NO_DRIVING_TEST"), ("causeway-c1", "NOT_REVIEWED")]
FB = "evidence/visual-tour-20261027/feedback.json"
KIT = "evidence/visual-tour-20261027/kit118-feedback.json"
C65 = "evidence/visual-tour-20261027/continuous65-feedback.json"
R49 = "evidence/visual-tour-20261027/road49-feedback.json"
CROSS = "evidence/visual-tour-20261027/additional-crossing-feedback.json"
RELIEF = "evidence/visual-tour-20261027/relief-east-feedback.json"
FOREST = "evidence/visual-tour-20261027/forest-feedback.json"
C0 = "evidence/visual-tour-20261027/causeway-c0-feedback.json"
TOUR = "evidence/visual-tour-20261027/tour-ended-20261028.json"
OBS = "evidence/native-shore-census-20261028/observations.json"
CONTRACT_KEYS = {"schema", "status", "case_count", "resolved_count", "c1_verdict", "visual_acceptance", "observed_build", "build_bindings", "cases", "scope_controls", "references", "domain_states", "source_pins"}
BINDING_KEYS = {"path", "sha256", "pointer", "expected_literal"}
SHA_RE = re.compile(r"^[0-9a-f]{64}$")

def _pairs(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate JSON key: {k}")
        out[k] = v
    return out

def strict_loads(data, label="JSON"):
    if not isinstance(data, (bytes, bytearray)) or len(data) > MAX_BYTES:
        raise ValueError(f"{label}: size limit exceeded")
    try:
        text = bytes(data).decode("utf-8")
    except Exception as exc:
        raise ValueError(f"{label}: invalid UTF-8") from exc
    def bad_const(x):
        raise ValueError(f"{label}: non-finite constant {x}")
    def flt(s):
        v = float(s)
        if not math.isfinite(v):
            raise ValueError(f"{label}: non-finite number")
        return v
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=bad_const, parse_float=flt)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"{label}: invalid JSON: {exc}") from exc

def deep_equal(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(deep_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(deep_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, float) and not math.isfinite(a):
        return False
    return a == b

def resolve_pointer(doc, pointer):
    if not isinstance(pointer, str) or (pointer != "" and not pointer.startswith("/")):
        raise ValueError(f"invalid JSON pointer: {pointer!r}")
    if pointer == "":
        return doc
    cur = doc
    for raw in pointer[1:].split("/"):
        if re.search(r"~(?![01])", raw):
            raise ValueError(f"invalid pointer escape: {pointer}")
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, dict):
            if token not in cur:
                raise ValueError(f"pointer not found: {pointer}")
            cur = cur[token]
        elif isinstance(cur, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", token):
                raise ValueError(f"invalid array index in pointer: {pointer}")
            idx = int(token)
            if idx >= len(cur):
                raise ValueError(f"pointer index out of range: {pointer}")
            cur = cur[idx]
        else:
            raise ValueError(f"pointer traverses scalar: {pointer}")
    return cur

def check_rel_path(path):
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path or ":" in path or "\x00" in path:
        raise ValueError(f"unsafe relative path: {path!r}")
    parts = path.split("/")
    if any(p in ("", ".", "..") for p in parts):
        raise ValueError(f"unsafe relative path: {path!r}")
    return path

def read_limited(path, label):
    with open(path, "rb") as fh:
        data = fh.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError(f"{label}: size limit exceeded")
    return data

def _binding_ok(b):
    if not isinstance(b, dict) or set(b) != BINDING_KEYS:
        raise ValueError(f"binding keys invalid: {b!r}")
    check_rel_path(b["path"])
    if not isinstance(b["sha256"], str) or not SHA_RE.match(b["sha256"]):
        raise ValueError("binding sha256 invalid")
    if not isinstance(b["pointer"], str) or not b["pointer"].startswith("/"):
        raise ValueError("binding pointer invalid")

def _unique(bindings, label):
    if not isinstance(bindings, list):
        raise ValueError(f"binding group not a list: {label}")
    seen = set()
    for b in bindings:
        _binding_ok(b)
        key = (b["path"], b["pointer"])
        if key in seen:
            raise ValueError(f"duplicate binding in group {label}: {key}")
        seen.add(key)

def collect_bindings(contract):
    out = []
    out.extend(contract["build_bindings"])
    for c in contract["cases"]:
        out.extend(c["source_bindings"])
        for ev in c["automatic_evidence"]:
            out.extend(ev["bindings"])
    for s in contract["scope_controls"]:
        out.extend(s["source_bindings"])
    for r in contract["references"]:
        out.extend(r["bindings"])
    return out

def _has(bindings, path, pointer, expected):
    return any(b["path"] == path and b["pointer"] == pointer and deep_equal(b["expected_literal"], expected) for b in bindings)

def _primary():
    p = {}
    for i, cid in enumerate(FIXED_IDS[:3]):
        p[cid] = [(FB, f"/findings/{i}/id", cid), (FB, f"/findings/{i}/status", "OPEN"), (FB, "/status", "VISUAL_REJECTED_BY_USER")]
    for i, cid in enumerate(FIXED_IDS[3:5]):
        p[cid] = [(KIT, f"/findings/{i}/id", cid), (KIT, f"/findings/{i}/status", "OPEN"), (KIT, "/status", "VISUAL_REJECTED_BY_USER")]
    p[FIXED_IDS[5]] = [(C65, "/findings/0/id", FIXED_IDS[5]), (C65, "/findings/0/status", "OPEN"), (C65, "/status", "VISUAL_REJECTED_BY_USER")]
    p[FIXED_IDS[6]] = [(R49, "/river_findings/0/id", FIXED_IDS[6]), (R49, "/river_findings/0/status", "VISUAL_REJECTED_BY_USER")]
    p[FIXED_IDS[7]] = [(CROSS, "/id", FIXED_IDS[7]), (CROSS, "/status", "USER_REJECTED_ROAD_INTERRUPTED_BY_RIVER")]
    p[FIXED_IDS[8]] = [(RELIEF, "/id", FIXED_IDS[8]), (RELIEF, "/status", "VISUAL_REJECTED_BY_USER")]
    return p

def _scope_source():
    return {FIXED_IDS[0]: (FB, "/findings/0/observed"), FIXED_IDS[1]: (FB, "/findings/1/observed"), FIXED_IDS[2]: (FB, "/findings/2/observed"), FIXED_IDS[3]: (KIT, "/findings/0/observed"), FIXED_IDS[4]: (KIT, "/findings/1/observed"), FIXED_IDS[5]: (C65, "/findings/0/observed"), FIXED_IDS[6]: (R49, "/river_findings/0/observed"), FIXED_IDS[7]: (CROSS, "/user_follow_up"), FIXED_IDS[8]: (RELIEF, "/observed")}

def validate_fixed(contract):
    if not isinstance(contract, dict) or set(contract) != CONTRACT_KEYS:
        raise ValueError("contract top-level keys invalid")
    if contract["schema"] != "rejection-coverage-contract.v1":
        raise ValueError("contract schema invalid")
    if contract["status"] != "OPEN_HUMAN_REJECTIONS" or type(contract["case_count"]) is not int or contract["case_count"] != 9 or type(contract["resolved_count"]) is not int or contract["resolved_count"] != 0:
        raise ValueError("fixed aggregate status/counts invalid")
    if contract["c1_verdict"] != "NOT_REVIEWED" or contract["visual_acceptance"] != "NOT_GRANTED":
        raise ValueError("fixed c1/visual acceptance invalid")
    if not deep_equal(contract["observed_build"], FIXED_OBSERVED_BUILD):
        raise ValueError("observed build must equal fixed historical build")
    ob = contract["observed_build"]
    if not isinstance(contract["build_bindings"], list) or len(contract["build_bindings"]) != 4:
        raise ValueError("build_bindings must be four")
    _unique(contract["build_bindings"], "build_bindings")
    for ptr, key in [("/mod", "mod"), ("/world_sha256", "world_sha256"), ("/pilot_sha256", "pilot_sha256"), ("/water_sha256", "water_sha256")]:
        if not _has(contract["build_bindings"], FB, ptr, ob[key]):
            raise ValueError("observed build must equal four feedback bindings")
    if not deep_equal(contract["domain_states"], FIXED_DOMAINS):
        raise ValueError("domain_states mismatch")
    cases = contract["cases"]
    if not isinstance(cases, list) or len(cases) != 9 or [c.get("id") if isinstance(c, dict) else None for c in cases] != FIXED_IDS:
        raise ValueError("fixed case IDs/order invalid")
    primary = _primary()
    scope_src = _scope_source()
    for idx, c in enumerate(cases):
        if not isinstance(c, dict) or set(c) != {"id", "human_verdict", "source_bindings", "scope", "location_status", "required_layers", "automatic_evidence"}:
            raise ValueError(f"case keys invalid: {c.get('id') if isinstance(c, dict) else c!r}")
        if c["human_verdict"] != "OPEN_REJECTED" or c["location_status"] != "UNCONFIRMED_CONTEXT_ONLY":
            raise ValueError(f"fixed OPEN/location invalid: {c['id']}")
        if not isinstance(c["scope"], str) or not c["scope"]:
            raise ValueError(f"case scope invalid: {c['id']}")
        if not deep_equal(c["required_layers"], FIXED_LAYERS[c["id"]]):
            raise ValueError(f"required_layers must equal fixed layer set for {c['id']}")
        if not isinstance(c["source_bindings"], list) or not c["source_bindings"] or not isinstance(c["automatic_evidence"], list) or not c["automatic_evidence"]:
            raise ValueError(f"case bindings invalid: {c['id']}")
        _unique(c["source_bindings"], f"case {c['id']}")
        for path, ptr, exp in primary[c["id"]]:
            if not _has(c["source_bindings"], path, ptr, exp):
                raise ValueError(f"primary id/status binding missing for {c['id']}: {ptr}")
        spath, sptr = scope_src[c["id"]]
        if not _has(c["source_bindings"], spath, sptr, c["scope"]):
            raise ValueError(f"scope must come from primary observed pointer {sptr}: {c['id']}")
        domain, position = FIXED_CENSUS[idx]
        census_found = False
        for ev in c["automatic_evidence"]:
            if not isinstance(ev, dict) or set(ev) != {"state", "bindings", "limitation"} or ev["state"] not in ALLOWED_STATES or not isinstance(ev["limitation"], str) or not ev["limitation"] or not isinstance(ev["bindings"], list) or not ev["bindings"]:
                raise ValueError(f"automatic evidence invalid: {c['id']}")
            _unique(ev["bindings"], f"automatic evidence {c['id']}")
            for b in ev["bindings"]:
                if b["path"] == OBS:
                    row = b["pointer"].split("/")
                    if len(row) < 3 or row[1] != str(idx):
                        raise ValueError(f"census binding borrows another row: {c['id']} {b['pointer']}")
                if b["pointer"].endswith("/domain"):
                    dom = b["expected_literal"]
                    if dom not in FIXED_DOMAINS or FIXED_DOMAINS[dom] != ev["state"]:
                        raise ValueError(f"domain->state mismatch: {c['id']}")
            required = [(f"/{idx}/observation", c["id"]), (f"/{idx}/domain", domain), (f"/{idx}/association", "UNCONFIRMED_CONTEXT_ONLY"), (f"/{idx}/approximate_review_position", position)]
            if all(_has(ev["bindings"], OBS, ptr, exp) for ptr, exp in required):
                if ev["state"] != FIXED_DOMAINS[domain]:
                    raise ValueError(f"census state mismatch: {c['id']}")
                census_found = True
        if not census_found:
            raise ValueError(f"native census binding group missing for row {idx}: {c['id']}")
    scopes = contract["scope_controls"]
    if not isinstance(scopes, list) or len(scopes) != 4 or [(s.get("id"), s.get("status")) if isinstance(s, dict) else None for s in scopes] != FIXED_SCOPES:
        raise ValueError("fixed scope controls invalid")
    scope_primary = {
        "forest-dense": [(FOREST, "/status", "LOCAL_VISUAL_OK"), (FOREST, "/global_forest_acceptance", False), (FOREST, "/performance", "NOT_MEASURED"), (TOUR, "/local_visual_ok", ["forest-dense", "causeway-c0"])],
        "causeway-c0": [(C0, "/status", "LOCAL_VISUAL_OK"), (C0, "/driving", "NOT_TESTED"), (C0, "/global_causeway_acceptance", False), (C0, "/global_shore_acceptance", False), (TOUR, "/local_visual_ok", ["forest-dense", "causeway-c0"])],
        "road-49": [(R49, "/road/status", "LOCAL_VISUAL_OK_WITH_PAVING_PENDING"), (R49, "/road/paving", "PENDING"), (R49, "/road/driving", "NOT_TESTED"), (R49, "/road/global_road_acceptance", False), (R49, "/road/bug_005_closed", False), (TOUR, "/road49", "LOCAL_VISUAL_OK_WITH_PAVING_PENDING_NO_DRIVING_TEST")],
        "causeway-c1": [(TOUR, "/c1_verdict", "NOT_REVIEWED"), (TOUR, "/visual_acceptance", "NOT_GRANTED"), (TOUR, "/defect_observations", 9)],
    }
    for s in scopes:
        if not isinstance(s, dict) or set(s) != {"id", "status", "source_bindings", "limitation"} or not isinstance(s["limitation"], str) or not s["limitation"] or not isinstance(s["source_bindings"], list) or not s["source_bindings"]:
            raise ValueError(f"scope control invalid: {s.get('id') if isinstance(s, dict) else s!r}")
        _unique(s["source_bindings"], f"scope {s['id']}")
        for path, ptr, exp in scope_primary[s["id"]]:
            if not _has(s["source_bindings"], path, ptr, exp):
                raise ValueError(f"scope primary/tour binding missing: {s['id']} {ptr}")
    refs = contract["references"]
    if not isinstance(refs, list) or [r.get("kind") if isinstance(r, dict) else None for r in refs] != ["REFERENCE_ONLY", "DIAGNOSTIC_ONLY"]:
        raise ValueError("references kinds invalid")
    for r in refs:
        if not isinstance(r, dict) or set(r) != {"kind", "bindings", "limitation"} or not isinstance(r["limitation"], str) or not r["limitation"] or not isinstance(r["bindings"], list) or not r["bindings"]:
            raise ValueError("reference invalid")
        _unique(r["bindings"], f"reference {r['kind']}")
    pins = contract["source_pins"]
    if not isinstance(pins, dict) or not pins or len(pins) > 12:
        raise ValueError("source_pins invalid")
    for path, sha in pins.items():
        check_rel_path(path)
        if not isinstance(sha, str) or not SHA_RE.match(sha):
            raise ValueError("source pin hash invalid")
    for b in collect_bindings(contract):
        ptr = b["pointer"]
        if ptr.endswith("/association") and b["expected_literal"] != "UNCONFIRMED_CONTEXT_ONLY":
            raise ValueError("association must remain UNCONFIRMED_CONTEXT_ONLY")
        if ptr.endswith(("/absence_proven", "/bridge_detected_in_returned_subset", "/matched_to_user_feature", "/dry_bank_candidate_in_game", "/bug_005_closed")) and b["expected_literal"] is not False:
            raise ValueError(f"fixed false flag violated: {ptr}")
        if "global" in ptr and b["expected_literal"] is not False:
            raise ValueError(f"global acceptance flag must be false: {ptr}")
        if ptr.endswith("/river_source_id") and b["expected_literal"] is not None:
            raise ValueError("river_source_id must remain null")

def verify_sources(root, contract):
    root_r = Path(root).resolve()
    if not root_r.is_dir():
        raise ValueError("root is not a directory")
    pins = contract["source_pins"]
    bindings = collect_bindings(contract)
    if set(pins) != {b["path"] for b in bindings}:
        raise ValueError("source_pins must be exact union of binding paths")
    cache = {}
    for path in pins:
        check_rel_path(path)
        full = (root_r / path).resolve()
        if not full.is_relative_to(root_r) or not full.is_file():
            raise ValueError(f"source missing or escapes root: {path}")
        data = read_limited(full, f"source {path}")
        if hashlib.sha256(data).hexdigest() != pins[path]:
            raise ValueError(f"source hash mismatch: {path}")
        cache[path] = strict_loads(data, f"source {path}")
    for b in bindings:
        if b["sha256"] != pins[b["path"]]:
            raise ValueError(f"binding hash != source pin: {b['path']}")
        actual = resolve_pointer(cache[b["path"]], b["pointer"])
        if not deep_equal(actual, b["expected_literal"]):
            raise ValueError(f"source literal mismatch: {b['path']} {b['pointer']}")
    return cache

def build_ledger(contract, contract_sha256):
    ledger = copy.deepcopy(contract)
    ledger["schema"] = "rejection-coverage-ledger.v1"
    ledger["contract_sha256"] = contract_sha256
    return ledger

def verify_ledger(root, contract, contract_sha256, ledger):
    if not isinstance(ledger, dict) or set(ledger) != CONTRACT_KEYS | {"contract_sha256"}:
        raise ValueError("ledger top-level keys invalid")
    if ledger.get("schema") != "rejection-coverage-ledger.v1" or ledger.get("contract_sha256") != contract_sha256:
        raise ValueError("ledger schema/contract hash invalid")
    if not deep_equal(ledger, build_ledger(contract, contract_sha256)):
        raise ValueError("ledger does not exactly match contract")
    validate_fixed(contract)
    verify_sources(root, contract)
    validate_fixed(ledger_as_contract(ledger))

def ledger_as_contract(ledger):
    c = copy.deepcopy(ledger)
    c.pop("contract_sha256", None)
    c["schema"] = "rejection-coverage-contract.v1"
    return c

def _input_path(root, arg):
    p = Path(arg)
    if p.is_absolute():
        return p
    cand = Path(root) / p
    return cand if cand.exists() or not p.exists() else p

def _output_path(root, arg):
    p = Path(arg)
    return p if p.is_absolute() else Path(root) / p

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--contract", required=True)
    ap.add_argument("--contract-sha256", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)
    try:
        root = Path(args.root)
        cpath = _input_path(root, args.contract)
        data = read_limited(cpath, "contract")
        sha = hashlib.sha256(data).hexdigest()
        if sha != args.contract_sha256:
            raise ValueError("contract sha256 mismatch")
        contract = strict_loads(data, "contract")
        validate_fixed(contract)
        verify_sources(root, contract)
        ledger = build_ledger(contract, sha)
        payload = (json.dumps(ledger, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if len(payload) > MAX_BYTES:
            raise ValueError("ledger too large")
        out = _output_path(root, args.output)
        with open(out, "xb") as fh:
            fh.write(payload)
        saved = read_limited(out, "ledger output")
        if saved != payload:
            raise ValueError("saved ledger bytes differ")
        verify_ledger(root, contract, sha, strict_loads(saved, "ledger"))
        print("VERIFIED_OPEN_HUMAN_REJECTIONS")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
