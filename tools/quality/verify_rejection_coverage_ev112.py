import argparse
import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path

LIMIT = 2 * 1024 * 1024
MAX_BYTES = LIMIT
TOP_FIELDS = {"schema", "status", "case_count", "resolved_count", "c1_verdict", "visual_acceptance", "observed_build", "build_bindings", "cases", "scope_controls", "references", "domain_states", "source_pins"}
CASE_ORDER = ("NARVA-VIS-01", "NARVA-VIS-02", "NARVA-VIS-03", "KIT118-VIS-01", "KIT118-VIS-02", "CONT65-VIS-01", "ROAD49-RIVER-VIS-01", "CROSSING-VIS-01", "RELIEF-EAST-VIS-01")
BUILD_TABLE = {"mod": "@DayZ_Baltic_EV112_Kit7Nav8Load1", "world_sha256": "f0e0e6b99da08b48f62ee47fa72b8905a5c9843bee4a30cefa18f517ddb1f603", "pilot_sha256": "3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6", "water_sha256": "97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43"}
STATE_BY_DOMAIN = (("native_candidate", "CONTEXT_ONLY_UNCONFIRMED"), ("road_model_not_evaluated", "NOT_EVALUATED"), ("native_or_model_unresolved", "CONTEXT_ONLY_UNCONFIRMED"), ("model_not_evaluated", "NOT_EVALUATED"), ("model_road_not_evaluated", "NOT_EVALUATED"), ("unknown", "NOT_EVALUATED"))
CENSUS_TABLE = (("native_candidate", [2391, 6941]), ("road_model_not_evaluated", [2391, 6941]), ("native_or_model_unresolved", [2391, 6941]), ("model_not_evaluated", [8253, 9038]), ("model_road_not_evaluated", [8253, 9038]), ("model_not_evaluated", [5162, 5865]), ("unknown", [5295.7, 5999.9]), ("road_model_not_evaluated", [4789.51465, 5516.52197]), ("native_candidate", [11790, 2400]))
LAYER_TABLE = (("NARVA-VIS-01", ("terrain", "visual_models", "water")), ("NARVA-VIS-02", ("road_models", "road_corridor", "approaches", "water")), ("NARVA-VIS-03", ("terrain", "visual_models", "water")), ("KIT118-VIS-01", ("riverbed_models", "terrain", "water")), ("KIT118-VIS-02", ("riverbed_models", "road_corridor", "approaches", "water")), ("CONT65-VIS-01", ("riverbed_models", "terrain", "water")), ("ROAD49-RIVER-VIS-01", ("terrain", "visual_models", "water")), ("CROSSING-VIS-01", ("road_corridor", "road_models", "approaches", "water")), ("RELIEF-EAST-VIS-01", ("terrain", "visual_models", "water")))
ALLOWED_STATES = frozenset(("NOT_EVALUATED", "CONTEXT_ONLY_UNCONFIRMED", "FINDING_UNRESOLVED", "MATERIALIZATION_DIFFERENT"))
P_FEEDBACK = "evidence/visual-tour-20261027/feedback.json"
P_KIT = "evidence/visual-tour-20261027/kit118-feedback.json"
P_C65 = "evidence/visual-tour-20261027/continuous65-feedback.json"
P_R49 = "evidence/visual-tour-20261027/road49-feedback.json"
P_CROSS = "evidence/visual-tour-20261027/additional-crossing-feedback.json"
P_RELIEF = "evidence/visual-tour-20261027/relief-east-feedback.json"
P_FOREST = "evidence/visual-tour-20261027/forest-feedback.json"
P_C0 = "evidence/visual-tour-20261027/causeway-c0-feedback.json"
P_TOUR = "evidence/visual-tour-20261027/tour-ended-20261028.json"
P_OBS = "evidence/native-shore-census-20261028/observations.json"
HASH_TEXT = re.compile(r"^[0-9a-f]{64}$")
INDEX_TEXT = re.compile(r"^(0|[1-9][0-9]*)$")
PRIMARY_TABLE = {}
for _i, _cid in enumerate(CASE_ORDER[:3]):
    PRIMARY_TABLE[_cid] = ((P_FEEDBACK, f"/findings/{_i}/id", _cid), (P_FEEDBACK, f"/findings/{_i}/status", "OPEN"), (P_FEEDBACK, "/status", "VISUAL_REJECTED_BY_USER"))
for _i, _cid in enumerate(CASE_ORDER[3:5]):
    PRIMARY_TABLE[_cid] = ((P_KIT, f"/findings/{_i}/id", _cid), (P_KIT, f"/findings/{_i}/status", "OPEN"), (P_KIT, "/status", "VISUAL_REJECTED_BY_USER"))
PRIMARY_TABLE[CASE_ORDER[5]] = ((P_C65, "/findings/0/id", CASE_ORDER[5]), (P_C65, "/findings/0/status", "OPEN"), (P_C65, "/status", "VISUAL_REJECTED_BY_USER"))
PRIMARY_TABLE[CASE_ORDER[6]] = ((P_R49, "/river_findings/0/id", CASE_ORDER[6]), (P_R49, "/river_findings/0/status", "VISUAL_REJECTED_BY_USER"))
PRIMARY_TABLE[CASE_ORDER[7]] = ((P_CROSS, "/id", CASE_ORDER[7]), (P_CROSS, "/status", "USER_REJECTED_ROAD_INTERRUPTED_BY_RIVER"))
PRIMARY_TABLE[CASE_ORDER[8]] = ((P_RELIEF, "/id", CASE_ORDER[8]), (P_RELIEF, "/status", "VISUAL_REJECTED_BY_USER"))
SCOPE_OBSERVED_TABLE = {CASE_ORDER[0]: (P_FEEDBACK, "/findings/0/observed"), CASE_ORDER[1]: (P_FEEDBACK, "/findings/1/observed"), CASE_ORDER[2]: (P_FEEDBACK, "/findings/2/observed"), CASE_ORDER[3]: (P_KIT, "/findings/0/observed"), CASE_ORDER[4]: (P_KIT, "/findings/1/observed"), CASE_ORDER[5]: (P_C65, "/findings/0/observed"), CASE_ORDER[6]: (P_R49, "/river_findings/0/observed"), CASE_ORDER[7]: (P_CROSS, "/user_follow_up"), CASE_ORDER[8]: (P_RELIEF, "/observed")}
SCOPE_TABLE = (
    ("forest-dense", "LOCAL_VISUAL_OK", ((P_FOREST, "/status", "LOCAL_VISUAL_OK"), (P_FOREST, "/global_forest_acceptance", False), (P_FOREST, "/performance", "NOT_MEASURED"), (P_TOUR, "/local_visual_ok", ["forest-dense", "causeway-c0"]))),
    ("causeway-c0", "LOCAL_VISUAL_OK", ((P_C0, "/status", "LOCAL_VISUAL_OK"), (P_C0, "/driving", "NOT_TESTED"), (P_C0, "/global_causeway_acceptance", False), (P_C0, "/global_shore_acceptance", False), (P_TOUR, "/local_visual_ok", ["forest-dense", "causeway-c0"]))),
    ("road-49", "LOCAL_VISUAL_OK_WITH_PAVING_PENDING_NO_DRIVING_TEST", ((P_R49, "/road/status", "LOCAL_VISUAL_OK_WITH_PAVING_PENDING"), (P_R49, "/road/paving", "PENDING"), (P_R49, "/road/driving", "NOT_TESTED"), (P_R49, "/road/global_road_acceptance", False), (P_R49, "/road/bug_005_closed", False), (P_TOUR, "/road49", "LOCAL_VISUAL_OK_WITH_PAVING_PENDING_NO_DRIVING_TEST"))),
    ("causeway-c1", "NOT_REVIEWED", ((P_TOUR, "/c1_verdict", "NOT_REVIEWED"), (P_TOUR, "/visual_acceptance", "NOT_GRANTED"), (P_TOUR, "/defect_observations", 9))),
)

def _no_duplicates(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError("duplicate JSON key: " + key)
        seen[key] = value
    return seen

def strict_loads(data, label="JSON"):
    if not isinstance(data, (bytes, bytearray)) or len(data) > LIMIT:
        raise ValueError(label + ": size limit exceeded")
    try:
        decoded = bytes(data).decode("utf-8")
    except Exception as exc:
        raise ValueError(label + ": invalid UTF-8") from exc
    def reject_constant(name):
        raise ValueError(label + ": non-finite constant " + name)
    def finite_float(text):
        number = float(text)
        if not math.isfinite(number):
            raise ValueError(label + ": non-finite number")
        return number
    try:
        return json.loads(decoded, object_pairs_hook=_no_duplicates, parse_constant=reject_constant, parse_float=finite_float)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(label + ": invalid JSON") from exc

def deep_equal(left, right):
    stack = [(left, right)]
    while stack:
        a, b = stack.pop()
        if type(a) is not type(b):
            return False
        if isinstance(a, dict):
            if set(a.keys()) != set(b.keys()):
                return False
            stack.extend((a[k], b[k]) for k in a)
        elif isinstance(a, list):
            if len(a) != len(b):
                return False
            stack.extend(zip(a, b))
        elif isinstance(a, float):
            if not math.isfinite(a) or a != b:
                return False
        elif a != b:
            return False
    return True

def resolve_pointer(document, pointer):
    if not isinstance(pointer, str) or (pointer != "" and not pointer.startswith("/")):
        raise ValueError("invalid JSON pointer: %r" % (pointer,))
    current = document
    if pointer == "":
        return current
    segments = pointer[1:].split("/")
    position = 0
    while position < len(segments):
        raw = segments[position]
        position += 1
        cursor = 0
        chars = []
        while cursor < len(raw):
            ch = raw[cursor]
            if ch == "~":
                if cursor + 1 >= len(raw) or raw[cursor + 1] not in "01":
                    raise ValueError("invalid pointer escape: " + pointer)
                chars.append("~" if raw[cursor + 1] == "0" else "/")
                cursor += 2
            else:
                chars.append(ch)
                cursor += 1
        token = "".join(chars)
        if isinstance(current, dict):
            if token not in current:
                raise ValueError("pointer not found: " + pointer)
            current = current[token]
        elif isinstance(current, list):
            if not INDEX_TEXT.match(token):
                raise ValueError("invalid array index in pointer: " + pointer)
            number = int(token)
            if number >= len(current):
                raise ValueError("pointer index out of range: " + pointer)
            current = current[number]
        else:
            raise ValueError("pointer traverses scalar: " + pointer)
    return current

def _read_capped(path, label):
    handle = open(path, "rb")
    try:
        blob = handle.read(LIMIT + 1)
    finally:
        handle.close()
    if len(blob) > LIMIT:
        raise ValueError(label + ": size limit exceeded")
    return blob

def _safe_relative(value):
    if not isinstance(value, str) or value == "" or value.startswith("/") or "\\" in value or ":" in value or "\x00" in value:
        raise ValueError("unsafe relative path: %r" % (value,))
    for piece in value.split("/"):
        if piece in ("", ".", ".."):
            raise ValueError("unsafe relative path: %r" % (value,))
    return value

def _indexed_group(bindings, label):
    if type(bindings) is not list:
        raise ValueError("binding group must be a list: " + label)
    table = {}
    for entry in bindings:
        if type(entry) is not dict or set(entry.keys()) != {"path", "sha256", "pointer", "expected_literal"}:
            raise ValueError("binding keys invalid in " + label)
        _safe_relative(entry["path"])
        if type(entry["sha256"]) is not str or not HASH_TEXT.match(entry["sha256"]):
            raise ValueError("binding sha256 invalid in " + label)
        if type(entry["pointer"]) is not str or not entry["pointer"].startswith("/"):
            raise ValueError("binding pointer invalid in " + label)
        key = entry["path"] + "\x00" + entry["pointer"]
        if key in table:
            raise ValueError("duplicate binding in group " + label)
        table[key] = entry
    return table

def _demand(index, path, pointer, expected, label):
    entry = index.get(path + "\x00" + pointer)
    if entry is None or not deep_equal(entry["expected_literal"], expected):
        raise ValueError("required binding missing: %s %s (%s)" % (path, pointer, label))

def _all_bindings(contract):
    flattened = []
    flattened.extend(contract["build_bindings"])
    for case in contract["cases"]:
        flattened.extend(case["source_bindings"])
        for evidence in case["automatic_evidence"]:
            flattened.extend(evidence["bindings"])
    for control in contract["scope_controls"]:
        flattened.extend(control["source_bindings"])
    for reference in contract["references"]:
        flattened.extend(reference["bindings"])
    return flattened

def validate_fixed(contract):
    if type(contract) is not dict or set(contract.keys()) != TOP_FIELDS:
        raise ValueError("contract top-level keys invalid")
    fixed_scalars = (("schema", "rejection-coverage-contract.v1"), ("status", "OPEN_HUMAN_REJECTIONS"), ("c1_verdict", "NOT_REVIEWED"), ("visual_acceptance", "NOT_GRANTED"))
    for field, wanted in fixed_scalars:
        if contract[field] != wanted:
            raise ValueError("fixed field invalid: " + field)
    if type(contract["case_count"]) is not int or contract["case_count"] != 9:
        raise ValueError("case_count must be int 9")
    if type(contract["resolved_count"]) is not int or contract["resolved_count"] != 0:
        raise ValueError("resolved_count must be int 0")
    if not deep_equal(contract["observed_build"], BUILD_TABLE):
        raise ValueError("observed build must equal fixed historical build")
    if type(contract["build_bindings"]) is not list or len(contract["build_bindings"]) != 4:
        raise ValueError("build_bindings must be four")
    build_index = _indexed_group(contract["build_bindings"], "build_bindings")
    for pointer_name in ("mod", "world_sha256", "pilot_sha256", "water_sha256"):
        _demand(build_index, P_FEEDBACK, "/" + pointer_name, BUILD_TABLE[pointer_name], "observed_build")
    if not deep_equal(contract["domain_states"], dict(STATE_BY_DOMAIN)):
        raise ValueError("domain_states mismatch")
    cases = contract["cases"]
    if type(cases) is not list or len(cases) != 9:
        raise ValueError("cases must be nine")
    layer_by_id = dict(LAYER_TABLE)
    state_by_domain = dict(STATE_BY_DOMAIN)
    for row in range(9):
        case = cases[row]
        wanted_id = CASE_ORDER[row]
        if type(case) is not dict or set(case.keys()) != {"id", "human_verdict", "source_bindings", "scope", "location_status", "required_layers", "automatic_evidence"}:
            raise ValueError("case keys invalid at row %d" % row)
        if case["id"] != wanted_id:
            raise ValueError("fixed case IDs/order invalid")
        if case["human_verdict"] != "OPEN_REJECTED" or case["location_status"] != "UNCONFIRMED_CONTEXT_ONLY":
            raise ValueError("fixed OPEN/location invalid: " + wanted_id)
        if type(case["scope"]) is not str or case["scope"] == "":
            raise ValueError("case scope invalid: " + wanted_id)
        if type(case["required_layers"]) is not list or not deep_equal(case["required_layers"], list(layer_by_id[wanted_id])):
            raise ValueError("required_layers must equal fixed layer set for " + wanted_id)
        if type(case["source_bindings"]) is not list or not case["source_bindings"] or type(case["automatic_evidence"]) is not list or not case["automatic_evidence"]:
            raise ValueError("case bindings invalid: " + wanted_id)
        source_index = _indexed_group(case["source_bindings"], "case " + wanted_id)
        for path, pointer, expected in PRIMARY_TABLE[wanted_id]:
            _demand(source_index, path, pointer, expected, "primary " + wanted_id)
        observed_path, observed_pointer = SCOPE_OBSERVED_TABLE[wanted_id]
        _demand(source_index, observed_path, observed_pointer, case["scope"], "scope from primary observed pointer " + wanted_id)
        wanted_domain, wanted_position = CENSUS_TABLE[row]
        census_ok = False
        for evidence in case["automatic_evidence"]:
            if type(evidence) is not dict or set(evidence.keys()) != {"state", "bindings", "limitation"}:
                raise ValueError("automatic evidence keys invalid: " + wanted_id)
            if evidence["state"] not in ALLOWED_STATES or type(evidence["limitation"]) is not str or evidence["limitation"] == "" or type(evidence["bindings"]) is not list or not evidence["bindings"]:
                raise ValueError("automatic evidence invalid: " + wanted_id)
            group = _indexed_group(evidence["bindings"], "automatic evidence " + wanted_id)
            for entry in evidence["bindings"]:
                if entry["path"] == P_OBS:
                    pieces = entry["pointer"].split("/")
                    if len(pieces) < 3 or pieces[1] != str(row):
                        raise ValueError("census binding borrows another row: %s %s" % (wanted_id, entry["pointer"]))
                if entry["pointer"].endswith("/domain"):
                    domain_value = entry["expected_literal"]
                    if domain_value not in state_by_domain or state_by_domain[domain_value] != evidence["state"]:
                        raise ValueError("domain->state mismatch: " + wanted_id)
            census_entries = (("/" + str(row) + "/observation", wanted_id), ("/" + str(row) + "/domain", wanted_domain), ("/" + str(row) + "/association", "UNCONFIRMED_CONTEXT_ONLY"), ("/" + str(row) + "/approximate_review_position", wanted_position))
            present = 0
            for pointer, expected in census_entries:
                item = group.get(P_OBS + "\x00" + pointer)
                if item is not None and deep_equal(item["expected_literal"], expected):
                    present += 1
            if present == 4:
                if evidence["state"] != state_by_domain[wanted_domain]:
                    raise ValueError("census state mismatch: " + wanted_id)
                census_ok = True
        if not census_ok:
            raise ValueError("native census binding group missing for row %d: %s" % (row, wanted_id))
    controls = contract["scope_controls"]
    if type(controls) is not list or len(controls) != 4:
        raise ValueError("scope controls must be four")
    for position, (control_id, control_status, required) in enumerate(SCOPE_TABLE):
        control = controls[position]
        if type(control) is not dict or set(control.keys()) != {"id", "status", "source_bindings", "limitation"}:
            raise ValueError("scope control keys invalid")
        if control["id"] != control_id or control["status"] != control_status:
            raise ValueError("fixed scope controls invalid")
        if type(control["limitation"]) is not str or control["limitation"] == "" or type(control["source_bindings"]) is not list or not control["source_bindings"]:
            raise ValueError("scope control invalid: " + control_id)
        control_index = _indexed_group(control["source_bindings"], "scope " + control_id)
        for path, pointer, expected in required:
            _demand(control_index, path, pointer, expected, "scope primary/tour " + control_id)
    references = contract["references"]
    if type(references) is not list or len(references) != 2 or type(references[0]) is not dict or type(references[1]) is not dict or references[0].get("kind") != "REFERENCE_ONLY" or references[1].get("kind") != "DIAGNOSTIC_ONLY":
        raise ValueError("references kinds invalid")
    for reference in references:
        if set(reference.keys()) != {"kind", "bindings", "limitation"} or type(reference["limitation"]) is not str or reference["limitation"] == "" or type(reference["bindings"]) is not list or not reference["bindings"]:
            raise ValueError("reference invalid")
        _indexed_group(reference["bindings"], "reference " + reference["kind"])
    pins = contract["source_pins"]
    if type(pins) is not dict or not pins or len(pins) > 12:
        raise ValueError("source_pins invalid")
    for rel, digest in pins.items():
        _safe_relative(rel)
        if type(digest) is not str or not HASH_TEXT.match(digest):
            raise ValueError("source pin hash invalid")
    for entry in _all_bindings(contract):
        pointer = entry["pointer"]
        if pointer.endswith("/association") and entry["expected_literal"] != "UNCONFIRMED_CONTEXT_ONLY":
            raise ValueError("association must remain UNCONFIRMED_CONTEXT_ONLY")
        if pointer.endswith(("/absence_proven", "/bridge_detected_in_returned_subset", "/matched_to_user_feature", "/dry_bank_candidate_in_game", "/bug_005_closed")) and entry["expected_literal"] is not False:
            raise ValueError("fixed false flag violated: " + pointer)
        if "global" in pointer and entry["expected_literal"] is not False:
            raise ValueError("global acceptance flag must be false: " + pointer)
        if pointer.endswith("/river_source_id") and entry["expected_literal"] is not None:
            raise ValueError("river_source_id must remain null")

def verify_sources(root, contract):
    base = Path(root).resolve()
    if not base.is_dir():
        raise ValueError("root is not a directory")
    pins = contract["source_pins"]
    flattened = _all_bindings(contract)
    paths_from_bindings = set()
    for entry in flattened:
        paths_from_bindings.add(entry["path"])
    if set(pins.keys()) != paths_from_bindings:
        raise ValueError("source_pins must be exact union of binding paths")
    documents = {}
    for rel in sorted(pins.keys()):
        _safe_relative(rel)
        target = (base / rel).resolve()
        if not target.is_relative_to(base) or not target.is_file():
            raise ValueError("source missing or escapes root: " + rel)
        blob = _read_capped(target, "source " + rel)
        if hashlib.sha256(blob).hexdigest() != pins[rel]:
            raise ValueError("source hash mismatch: " + rel)
        documents[rel] = strict_loads(blob, "source " + rel)
    for entry in flattened:
        rel = entry["path"]
        if entry["sha256"] != pins[rel]:
            raise ValueError("binding hash != source pin: " + rel)
        found = resolve_pointer(documents[rel], entry["pointer"])
        if not deep_equal(found, entry["expected_literal"]):
            raise ValueError("source literal mismatch: %s %s" % (rel, entry["pointer"]))
    return documents

def expected_ledger(contract, contract_sha256):
    result = copy.deepcopy(contract)
    result["schema"] = "rejection-coverage-ledger.v1"
    result["contract_sha256"] = contract_sha256
    return result

def verify_ledger(root, contract, contract_sha256, ledger):
    validate_fixed(contract)
    verify_sources(root, contract)
    if type(ledger) is not dict or set(ledger.keys()) != TOP_FIELDS | {"contract_sha256"}:
        raise ValueError("ledger top-level keys invalid")
    if ledger.get("schema") != "rejection-coverage-ledger.v1" or ledger.get("contract_sha256") != contract_sha256:
        raise ValueError("ledger schema/contract hash invalid")
    if not deep_equal(ledger, expected_ledger(contract, contract_sha256)):
        raise ValueError("ledger does not exactly match contract")
    derived = copy.deepcopy(ledger)
    derived.pop("contract_sha256")
    derived["schema"] = "rejection-coverage-contract.v1"
    validate_fixed(derived)
    verify_sources(root, derived)

def _located(root, argument):
    candidate = Path(argument)
    if candidate.is_absolute():
        return candidate
    joined = Path(root) / candidate
    return joined if joined.exists() or not candidate.exists() else candidate

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--ledger", required=True)
    options = parser.parse_args(argv)
    try:
        contract_file = _located(options.root, options.contract)
        contract_blob = _read_capped(contract_file, "contract")
        digest = hashlib.sha256(contract_blob).hexdigest()
        if digest != options.contract_sha256:
            raise ValueError("contract sha256 mismatch")
        contract_doc = strict_loads(contract_blob, "contract")
        ledger_file = _located(options.root, options.ledger)
        ledger_blob = _read_capped(ledger_file, "ledger")
        ledger_doc = strict_loads(ledger_blob, "ledger")
        verify_ledger(options.root, contract_doc, digest, ledger_doc)
        print("VERIFIED_OPEN_HUMAN_REJECTIONS")
        return 0
    except Exception as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
