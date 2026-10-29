"""Independent saved consumer for EV112 road-material dependencies.

Does NOT import the producer/parser/lexer. Opens NO installed PBO and
never reopens the PBO source; it verifies the saved report, contract
pins, saved sources/assets, the two saved texts (via its own declarative
scanner plus its own token scanner) and the four saved leaf copies.
Expected names/inventory below derive from the frozen brief, not producer.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SUCCESS = "SAVED_PILOT_DEPENDENCIES_RESOLVED_ONLY"
FAILURE = "INCONCLUSIVE_DEPENDENCIES"
EXPECTED_INVENTORY = {"assignments": 20, "classes": 4, "strings": 6, "vec3": 8, "vec4": 5, "scalar": 1, "semicolons": 24}
EXPECTED_TOP = ["ambient", "diffuse", "forcedDiffuse", "emmisive", "specular", "specularPower", "PixelShaderID", "VertexShaderID"]
REPORT_KEYS = {"schema", "status", "contract_sha", "dependency_scope", "scope", "build_ready", "provider_ambiguity", "native_resolution", "pbo", "sources", "models_evidence", "catalog_pins", "saved_assets", "parsed_texts", "leaves", "range_copies", "inventory", "limits", "limitations"}

def sha256_bytes(d):
    return hashlib.sha256(d).hexdigest()

def sha256_stream(path, size):
    if Path(path).stat().st_size != int(size):
        raise ValueError("size_mismatch")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            c = f.read(1048576)
            if not c:
                break
            h.update(c)
    return h.hexdigest()

def verify_pin(path, sha, size):
    if not Path(path).is_file():
        raise ValueError(f"missing:{path}")
    if sha256_stream(path, size) != str(sha).lower():
        raise ValueError(f"sha_mismatch:{path}")

def normalize(p):
    return str(p).replace(chr(92), "/").lower().strip("/")

_STAT_FIELDS = {"dev", "ino", "size", "mtime_ns", "ctime_ns"}
_CROSS_FIELDS = ("dev", "ino", "size", "mtime_ns")
_SAME_FIELDS = ("dev", "ino", "size", "mtime_ns", "ctime_ns")
_LEAF_KEYS = {"virtual_path", "normalized_virtual_path", "entry", "sha256", "size", "offset", "output", "copy_sha256", "copy_size", "texture_ref"}
_ENTRY_KEYS = {"name", "mime", "size", "offset"}
_REF_KEYS = {"path", "raw_virtual_path", "virtual_path", "string_start", "string_end"}

def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)

def _rel_name(name, prefix="dz/structures/roads"):
    n = normalize(name)
    return n[len(prefix) + 1:] if n.startswith(prefix + "/") else n

def _check_stat(snap, label):
    if not isinstance(snap, dict) or set(snap.keys()) != _STAT_FIELDS:
        raise ValueError(f"stat_shape:{label}")
    for k, v in snap.items():
        if not _is_int(v):
            raise ValueError(f"stat_not_int:{label}:{k}")
    return snap

def _check_pin_meta(meta, pin, label):
    if not isinstance(meta, dict) or set(meta.keys()) != {"path", "sha256", "size", "stat"}:
        raise ValueError(f"pin_meta_shape:{label}")
    if meta.get("path") != pin["path"] or meta.get("sha256") != pin["sha256"] or not _is_int(meta.get("size")) or int(meta["size"]) != int(pin["size"]):
        raise ValueError(f"pin_meta_mismatch:{label}")
    _check_stat(meta.get("stat"), label)
    if int(meta["stat"]["size"]) != int(pin["size"]):
        raise ValueError(f"pin_stat_size:{label}")
    return meta

def _compare_pin_before_after(before, after, pin, label):
    _check_pin_meta(before, pin, label + ":before"); _check_pin_meta(after, pin, label + ":after")
    for k in _SAME_FIELDS:
        if before["stat"][k] != after["stat"][k]:
            raise ValueError(f"pin_stat_before_after_mismatch:{label}:{k}")

# --- Own token scanner (independent implementation) ---
_TOKEN_RE = re.compile(r'(?P<ws>[ \t\r\n]+)|(?P<string>"[^"]*")|(?P<ident>[A-Za-z_][A-Za-z0-9_]*)|(?P<number>[0-9]+(?:\.[0-9]+)?)|(?P<symbol>[{}\[\]=,;])')

def scan_tokens(data):
    text = bytes(data)
    try:
        s = text.decode("ascii")
    except UnicodeDecodeError as e:
        raise ValueError(f"non_ascii at {e.start}")
    tokens = []; pos = 0
    while pos < len(s):
        m = _TOKEN_RE.match(s, pos)
        if not m:
            raise ValueError(f"UNSUPPORTED token at {pos}: {s[pos]!r}")
        kind = m.lastgroup; start, end = m.span()
        if kind == "number":
            # Reject 1. / 1e5 / 1.2.3 shapes the regex would partially eat.
            nxt = s[end:end + 1]
            if nxt in (".",) or nxt.isalnum() or nxt == "_":
                raise ValueError(f"bad_number at {start}")
        if kind != "ws":
            raw = text[start:end]
            val = m.group()
            if kind == "string":
                val = val[1:-1]  # backslash literal; first quote terminated
            tokens.append({"kind": kind, "value": val, "start": start, "end": end, "sha256": sha256_bytes(raw)})
        pos = end
    # Byte coverage: every non-whitespace byte covered exactly once, in order.
    covered = []
    for t in tokens:
        covered.extend(range(t["start"], t["end"]))
    if covered != sorted(covered) or len(covered) != len(set(covered)):
        raise ValueError("token_coverage_overlap")
    nonwhite = {i for i, ch in enumerate(s) if ch not in " \t\r\n"}
    if set(covered) != nonwhite:
        raise ValueError("token_coverage_incomplete")
    # Tokens must lexically match source bytes.
    for t in tokens:
        raw = text[t["start"]:t["end"]]
        if sha256_bytes(raw) != t["sha256"]:
            raise ValueError("token_sha_mismatch")
        expect = ('"' + t["value"] + '"') if t["kind"] == "string" else t["value"]
        if raw.decode("ascii") != expect:
            raise ValueError("token_lexical_mismatch")
    return tokens

# --- Own declarative reconstruction (anchored, observed field order) ---
_W = r"[ \t\r\n]*"
_N = r"([0-9]+(?:\.[0-9]+)?)"
_S = r'"([^"]*)"'

def _vec(name, count):
    nums = _W + ("," + _W).join([_N] * count) + _W
    return name + r"\[\]" + _W + "=" + _W + r"\{" + nums + r"\}" + _W + ";"

def _str_assign(name):
    return name + _W + "=" + _W + _S + _W + ";"

def _uv(prefix):
    parts = []
    for nm in ("aside", "up", "dir", "pos"):
        parts.append(_vec(nm, 3))
    return r"class" + _W + r"uvTransform" + _W + r"\{" + _W + _W.join(parts) + _W + r"\}" + _W + ";"

def _stage(name):
    return (r"class" + _W + name + _W + r"\{" + _W + _str_assign("texture") + _W + _str_assign("uvSource") + _W + _uv(name) + _W + r"\}" + _W + ";")

_PATTERN = re.compile(
    r"\A" + _W + _W.join([
        _vec("ambient", 4), _vec("diffuse", 4), _vec("forcedDiffuse", 4), _vec("emmisive", 4), _vec("specular", 4),
        r"specularPower" + _W + "=" + _W + _N + _W + ";",
        _str_assign("PixelShaderID"), _str_assign("VertexShaderID"), _stage("Stage1"), _stage("Stage2")]) + _W + r"\Z")

def declarative_parse(data):
    tokens = scan_tokens(data)
    try:
        text = bytes(data).decode("ascii")
    except UnicodeDecodeError as e:
        raise ValueError(f"non_ascii at {e.start}")
    m = _PATTERN.match(text)
    if not m:
        raise ValueError("UNSUPPORTED: declarative_order_or_structure_mismatch (anchored observed-order pattern; reorder not supported)")
    g = list(m.groups())  # 5*4 vec4 + 1 scalar + 2 strings + per stage (2 strings + 4*3) *2 = 20+1+2+28=51
    if len(g) != 51:
        raise ValueError(f"UNSUPPORTED capture_count {len(g)}")
    idx = 0; assignments = []
    def take(n):
        nonlocal idx
        vals = g[idx:idx + n]; idx += n; return vals
    for nm in ("ambient", "diffuse", "forcedDiffuse", "emmisive", "specular"):
        vals = take(4); assignments.append({"path": nm, "name": nm, "type": "vec4", "value": vals, "raw_lexemes": vals})
    sp = take(1)[0]; assignments.append({"path": "specularPower", "name": "specularPower", "type": "scalar", "value": sp, "raw_lexemes": [sp]})
    for nm in ("PixelShaderID", "VertexShaderID"):
        v = take(1)[0]; assignments.append({"path": nm, "name": nm, "type": "string", "value": v, "raw_lexemes": [v]})
    classes = []
    for stage in ("Stage1", "Stage2"):
        classes.append(stage)
        for nm in ("texture", "uvSource"):
            v = take(1)[0]; assignments.append({"path": f"{stage}.{nm}", "name": nm, "type": "string", "value": v, "raw_lexemes": [v]})
        classes.append(f"{stage}.uvTransform")
        for nm in ("aside", "up", "dir", "pos"):
            vals = take(3); assignments.append({"path": f"{stage}.uvTransform.{nm}", "name": nm, "type": "vec3", "value": vals, "raw_lexemes": vals})
    if idx != 51:
        raise ValueError("capture_consumption_mismatch")
    # String token offsets from own scanner, in source order.
    string_tokens = [t for t in tokens if t["kind"] == "string"]
    if len(string_tokens) != 6:
        raise ValueError("string_token_count_mismatch")
    si = 0; refs = []
    for a in assignments:
        if a["type"] == "string":
            tok = string_tokens[si]; si += 1
            if tok["value"] != a["value"]:
                raise ValueError("string_value_token_mismatch")
            a["string_start"] = tok["start"]; a["string_end"] = tok["end"]; a["value_start"] = tok["start"]; a["value_end"] = tok["end"]
            if a["name"] == "texture":
                refs.append({"path": a["path"], "raw_virtual_path": a["value"], "virtual_path": normalize(a["value"]), "string_start": tok["start"], "string_end": tok["end"]})
    semicolons = sum(1 for t in tokens if t["kind"] == "symbol" and t["value"] == ";")
    inv = {"assignments": len(assignments), "classes": len(classes), "strings": sum(1 for a in assignments if a["type"] == "string"), "vec3": sum(1 for a in assignments if a["type"] == "vec3"), "vec4": sum(1 for a in assignments if a["type"] == "vec4"), "scalar": sum(1 for a in assignments if a["type"] == "scalar"), "semicolons": semicolons}
    if inv != EXPECTED_INVENTORY:
        raise ValueError(f"inventory_mismatch:{inv}")
    return {"assignments": assignments, "classes": classes, "texture_refs": refs, "tokens": tokens, "inventory": inv, "semicolons": semicolons, "eof_newline": bool(bytes(data).endswith(b"\n")), "eof_state": "newline" if bytes(data).endswith(b"\n") else "no_newline"}

def compare_parsed(expected, saved):
    # Exact values/types/paths/offsets; vector values and string offsets included.
    for key in ("classes", "inventory", "semicolons", "eof_newline", "eof_state", "texture_refs", "tokens"):
        if saved.get(key) != expected.get(key):
            raise ValueError(f"parsed_mismatch:{key}")
    sa = saved.get("assignments")
    if not isinstance(sa, list) or len(sa) != len(expected["assignments"]):
        raise ValueError("parsed_mismatch:assignments_count (missing/dropped assignment or Stage)")
    for exp, got in zip(expected["assignments"], sa):
        for key in ("path", "name", "type", "value", "raw_lexemes"):
            if got.get(key) != exp.get(key):
                raise ValueError(f"parsed_mismatch:assignment:{exp.get('path')}:{key}")
        if exp["type"] == "string" and (got.get("string_start") != exp.get("string_start") or got.get("string_end") != exp.get("string_end")):
            raise ValueError(f"parsed_mismatch:string_offset:{exp.get('path')}")
    return True

def validate_leaf_set(texture_refs, leaves):
    refs = {normalize(r["virtual_path"]) for r in texture_refs}
    leaf_paths = [normalize(l.get("virtual_path", "")) for l in leaves]
    if len(leaves) != 4 or len(refs) != 4 or set(leaf_paths) != refs or len(set(leaf_paths)) != 4:
        raise ValueError("leaves_not_exactly_extracted_texture_refs (dropped/co-mutated/arbitrary leaf)")
    return True

def validate_ranges(leaves, range_cap=16777216, total_cap=67108864, file_size=318217469):
    total = 0
    for leaf in leaves:
        e = leaf.get("entry") or leaf
        if not isinstance(e, dict) or set(e.keys()) != _ENTRY_KEYS:
            raise ValueError("leaf_entry_missing_or_extra_field")
        for k in ("mime", "size", "offset"):
            if not _is_int(e[k]):
                raise ValueError(f"leaf_entry_field_not_int:{k}")
        if int(e["mime"]) != 0:
            raise ValueError("leaf_mime_not_zero")
        size = int(e["size"]); off = int(e["offset"])
        if size <= 0 or size > range_cap:
            raise ValueError("leaf_range_size_limit")
        if off < 0 or off + size > int(file_size):
            raise ValueError("leaf_range_out_of_bounds")
        total += size
    if total > total_cap:
        raise ValueError("leaf_ranges_total_limit")
    return True

def verify(contract, contract_sha, report, report_sha, report_path):
    if contract.get("schema") != "ROAD_B4A3_V1":
        raise ValueError("contract_schema")
    for k in ("sources", "texts", "saved_assets", "leaves", "pbo", "inventory", "limits", "output", "attempt_marker", "scope", "build_ready", "provider_ambiguity", "native_resolution"):
        if k not in contract:
            raise ValueError(f"contract_missing:{k}")
    if set(report.keys()) != REPORT_KEYS:
        raise ValueError(f"report_floating_or_missing_fields:{sorted(set(report.keys()) ^ REPORT_KEYS)}")
    if report.get("schema") != "ROAD_MATERIAL_DEPENDENCIES_REPORT_EV112_V1":
        raise ValueError("report_schema")
    if report.get("status") != SUCCESS:
        raise ValueError("report_status_not_success")
    if report.get("contract_sha") != contract_sha:
        raise ValueError("report_contract_sha_mismatch")
    if report.get("build_ready") is not False or report.get("scope") != "three_road_models" or report.get("dependency_scope") != "three_road_models":
        raise ValueError("report_scope_build_ready")
    if report.get("provider_ambiguity") != "NOT_TESTED" or report.get("native_resolution") != "NOT_TESTED":
        raise ValueError("report_not_tested_markers")
    if contract.get("scope") != "three_road_models" or contract.get("build_ready") is not False:
        raise ValueError("contract_scope")
    if report.get("inventory") != EXPECTED_INVENTORY or contract.get("inventory") != EXPECTED_INVENTORY:
        raise ValueError("inventory_pin_mismatch")
    lim = contract.get("limits") or {}
    if int(lim.get("range_bytes", 0)) != 16777216 or int(lim.get("total_ranges", 0)) != 67108864:
        raise ValueError("limits_mismatch")
    if report.get("limits") != contract.get("limits"):
        raise ValueError("report_limits_mismatch")
    # Source pins independently (PBO path deliberately never opened/stat-ed here).
    if not isinstance(contract.get("sources"), dict) or not {"models", "catalog", "source_table", "helper", "python"}.issubset(set(contract["sources"].keys())):
        raise ValueError("contract_sources_keyset_exact")
    if not isinstance(report.get("sources"), dict) or set(report["sources"].keys()) != set(contract["sources"].keys()):
        raise ValueError("report_sources_keyset_exact")
    for label, pin in contract["sources"].items():
        if not isinstance(pin, dict) or set(pin.keys()) != {"path", "sha256", "size"} or not _is_int(pin.get("size")):
            raise ValueError(f"contract_source_pin_shape:{label}")
        verify_pin(pin["path"], pin["sha256"], pin["size"])
        saved = report["sources"].get(label)
        if not isinstance(saved, dict) or set(saved.keys()) != {"path", "sha256", "size", "before", "after"}:
            raise ValueError(f"report_source_shape:{label}")
        if saved.get("path") != pin["path"] or saved.get("sha256") != pin["sha256"] or not _is_int(saved.get("size")) or int(saved["size"]) != int(pin["size"]):
            raise ValueError(f"report_source_pin_mismatch:{label}")
        _compare_pin_before_after(saved.get("before"), saved.get("after"), pin, f"source:{label}")
    if len(contract["saved_assets"]) != 8 or len(report.get("saved_assets") or []) != 8:
        raise ValueError("saved_assets_count")
    for pin, saved in zip(contract["saved_assets"], report["saved_assets"]):
        if not isinstance(pin, dict) or set(pin.keys()) != {"virtual_path", "path", "sha256", "size"} or not _is_int(pin.get("size")):
            raise ValueError("contract_saved_asset_shape")
        verify_pin(pin["path"], pin["sha256"], pin["size"])
        if not isinstance(saved, dict) or set(saved.keys()) != {"virtual_path", "path", "sha256", "size", "before", "after"}:
            raise ValueError("saved_asset_shape")
        if saved.get("virtual_path") != pin["virtual_path"] or saved.get("path") != pin["path"] or saved.get("sha256") != pin["sha256"] or not _is_int(saved.get("size")) or int(saved["size"]) != int(pin["size"]):
            raise ValueError("saved_asset_pin_mismatch")
        _compare_pin_before_after(saved.get("before"), saved.get("after"), pin, "saved_asset")
    # Models inherited by hash only.
    me = report.get("models_evidence") or {}
    if me.get("kind") != "inherited_by_hash":
        raise ValueError("models_evidence_kind")
    if set(me.keys()) != {"kind", "models", "catalog", "source_table", "note"}:
        raise ValueError("models_evidence_shape")
    for sub, label in (("models", "models"), ("catalog", "catalog"), ("source_table", "source_table")):
        pin = contract["sources"][label]; got = me.get(sub) or {}
        if set(got.keys()) != {"path", "sha256", "size"} or got.get("path") != pin["path"] or got.get("sha256") != pin["sha256"] or not _is_int(got.get("size")) or int(got["size"]) != int(pin["size"]):
            raise ValueError(f"models_evidence_pin_mismatch:{label}")
    cp = report.get("catalog_pins") or {}
    if set(cp.keys()) != {"catalog_sha256", "models_sha256", "source_table_sha256"} or cp.get("catalog_sha256") != contract["sources"]["catalog"]["sha256"] or cp.get("models_sha256") != contract["sources"]["models"]["sha256"] or cp.get("source_table_sha256") != contract["sources"]["source_table"]["sha256"]:
        raise ValueError("catalog_pins_mismatch")
    # PBO metadata only: hash/stats as saved, size pin; file NOT reopened.
    pbo_r = report.get("pbo") or {}; pbo_c = contract["pbo"]
    if not isinstance(pbo_c, dict) or set(pbo_c.keys()) != {"path", "sha256", "size", "prefix"} or not _is_int(pbo_c.get("size")):
        raise ValueError("contract_pbo_shape")
    if set(pbo_r.keys()) != {"path", "sha256", "sha256_before", "sha256_after", "size", "prefix", "properties", "entries_count", "stat_before", "stat_after"}:
        raise ValueError("report_pbo_shape")
    if pbo_r.get("path") != pbo_c["path"] or pbo_r.get("sha256") != pbo_c["sha256"] or pbo_r.get("sha256_before") != pbo_c["sha256"] or pbo_r.get("sha256_after") != pbo_c["sha256"] or not _is_int(pbo_r.get("size")) or int(pbo_r.get("size", -1)) != 318217469 or int(pbo_c.get("size", -1)) != 318217469:
        raise ValueError("pbo_saved_hash_size_mismatch")
    if normalize(pbo_c.get("prefix", "")) != "dz/structures/roads" or normalize(pbo_r.get("prefix", "")) != "dz/structures/roads":
        raise ValueError("pbo_prefix_mismatch")
    for side in ("stat_before", "stat_after"):
        st = pbo_r.get(side) or {}
        if set(st.keys()) != {"path", "handle"}:
            raise ValueError(f"pbo_{side}_missing")
        for api in ("path", "handle"):
            _check_stat(st.get(api), f"{side}:{api}")
            if int(st[api]["size"]) != 318217469:
                raise ValueError(f"pbo_stat_size:{side}:{api}")
        for k in _CROSS_FIELDS:
            if st["path"][k] != st["handle"][k]:
                raise ValueError(f"pbo_stat_path_handle_mismatch:{side}:{k}")
    for api in ("path", "handle"):
        for k in _SAME_FIELDS:
            if pbo_r["stat_before"][api][k] != pbo_r["stat_after"][api][k]:
                raise ValueError(f"pbo_stat_before_after_mismatch:{api}:{k}")
    st_pin = contract["sources"]["source_table"]
    st_data = Path(st_pin["path"]).read_bytes()
    if sha256_bytes(st_data) != str(st_pin["sha256"]).lower() or len(st_data) != int(st_pin["size"]):
        raise ValueError("source_table_bytes_not_rehashed")
    st_obj = json.loads(st_data.decode("utf-8"))
    if not isinstance(st_obj, dict) or set(st_obj.keys()) != {"properties", "entries"} or not isinstance(st_obj.get("entries"), list):
        raise ValueError("source_table_shape_exact_properties_entries")
    source_props = {str(k): str(v) for k, v in st_obj["properties"].items()}
    if pbo_r.get("properties") != source_props:
        raise ValueError("report_pbo_properties_mismatch_source_table")
    if not _is_int(pbo_r.get("entries_count")) or int(pbo_r["entries_count"]) != len(st_obj["entries"]):
        raise ValueError("report_pbo_entries_count_mismatch")
    pv = [v for k, v in source_props.items() if str(k).lower() == "prefix"]
    if len(pv) != 1 or normalize(pv[0]) != "dz/structures/roads":
        raise ValueError("source_table_prefix_mismatch")
    source_entries = []
    for e in st_obj["entries"]:
        if not isinstance(e, dict) or set(e.keys()) != _ENTRY_KEYS:
            raise ValueError("source_table_entry_missing_or_extra_field")
        for k in ("mime", "size", "offset"):
            if not _is_int(e[k]):
                raise ValueError(f"source_table_entry_field_not_int:{k}")
        source_entries.append({"name": _rel_name(e["name"]), "mime": int(e["mime"]), "size": int(e["size"]), "offset": int(e["offset"])})
    cat_pin = contract["sources"]["catalog"]
    cat_data = Path(cat_pin["path"]).read_bytes()
    if sha256_bytes(cat_data) != str(cat_pin["sha256"]).lower() or len(cat_data) != int(cat_pin["size"]):
        raise ValueError("catalog_bytes_not_rehashed")
    cat_obj = json.loads(cat_data.decode("utf-8"))
    if not isinstance(cat_obj, list) or len(cat_obj) != 501:
        raise ValueError("catalog_shape_exact")
    catalog_rows = set()
    for r in cat_obj:
        if not isinstance(r, dict) or set(r.keys()) != {"name", "normalized_name", "category", "mime", "size", "sha256"} or not _is_int(r.get("mime")) or not _is_int(r.get("size")):
            raise ValueError("catalog_row_shape")
        if not isinstance(r['name'], str) or not isinstance(r['category'], str) or r['normalized_name'] != normalize(r['name']):
            raise ValueError('catalog_normalized_name')
        catalog_rows.add((_rel_name(r["name"]), int(r["mime"]), int(r["size"]), str(r["sha256"]).lower()))
    # Texts independently reconstructed.
    if len(contract["texts"]) != 2 or len(report.get("parsed_texts") or []) != 2:
        raise ValueError("parsed_texts_count")
    all_refs = []
    for pin, saved in zip(contract["texts"], report["parsed_texts"]):
        verify_pin(pin["path"], pin["sha256"], pin["size"])
        if set(saved.keys()) != {"id", "path", "sha256", "size", "specular_power", "inventory", "assignments", "classes", "tokens", "texture_refs", "eof_newline", "eof_state", "semicolons"}:
            raise ValueError("parsed_text_shape")
        if saved.get("id") != pin["id"] or saved.get("path") != pin["path"] or saved.get("sha256") != pin["sha256"] or not _is_int(saved.get("size")) or int(saved["size"]) != int(pin["size"]):
            raise ValueError("parsed_text_pin_mismatch")
        data = Path(pin["path"]).read_bytes()
        if sha256_bytes(data) != str(pin["sha256"]).lower():
            raise ValueError("parsed_text_bytes_hash")
        expected = declarative_parse(data)
        compare_parsed(expected, saved)
        spec = next((a["value"] for a in expected["assignments"] if a["path"] == "specularPower"), None)
        if str(spec) != str(pin["specular_power"]) or str(saved.get("specular_power")) != str(pin["specular_power"]):
            raise ValueError("specular_power_mismatch")
        all_refs.extend(expected["texture_refs"])
    # Leaves: exactly extracted refs, contract/report agreement, saved copies.
    leaves_c = contract["leaves"]; leaves_r = report.get("leaves") or []
    if report.get("range_copies") != leaves_r:
        raise ValueError("range_copies_not_leaves")
    validate_leaf_set(all_refs, leaves_c); validate_leaf_set(all_refs, leaves_r); validate_ranges(leaves_c); validate_ranges(leaves_r)
    for lc0 in leaves_c:
        if not isinstance(lc0, dict) or set(lc0.keys()) != {"virtual_path", "entry", "sha256", "output"} or not isinstance(lc0.get("entry"), dict) or set(lc0["entry"].keys()) != _ENTRY_KEYS:
            raise ValueError("contract_leaf_shape")
    report_dir = Path(report_path).resolve().parent
    by_vp_c = {normalize(l["virtual_path"]): l for l in leaves_c}
    source_by_rel = {e["name"]: e for e in source_entries}
    ind_refs = {normalize(r["virtual_path"]): r for r in all_refs}
    for lr in leaves_r:
        if not isinstance(lr, dict) or set(lr.keys()) != _LEAF_KEYS:
            raise ValueError("report_leaf_shape_floating_or_missing")
        lc = by_vp_c.get(normalize(lr.get("virtual_path", "")))
        if lc is None:
            raise ValueError("report_leaf_not_in_contract")
        out_r = str(lr.get("output", "")).replace(chr(92), "/")
        if not out_r or out_r.startswith("/") or ".." in out_r.split("/") or (len(out_r) > 1 and out_r[1] == ":") or not out_r.startswith("leaves/"):
            raise ValueError("leaf_output_escape")
        if lr.get("output") != lc.get("output"):
            raise ValueError("report_leaf_output_mismatch")
        if normalize(lr.get("virtual_path", "")) != normalize(lc.get("virtual_path", "")) or lr.get("normalized_virtual_path") != normalize(lr.get("virtual_path", "")):
            raise ValueError("leaf_virtual_path_mismatch")
        rel = _rel_name(lr["virtual_path"])
        if normalize(lr["virtual_path"]) != "dz/structures/roads/" + rel:
            raise ValueError("leaf_virtual_prefix_mismatch")
        src_e = source_by_rel.get(rel)
        if src_e is None:
            raise ValueError("leaf_not_in_source_table")
        for e in (lr.get("entry") or {}, lc.get("entry") or {}):
            if set(e.keys()) != _ENTRY_KEYS or normalize(e.get("name", "")) != src_e["name"] or not _is_int(e.get("mime")) or int(e["mime"]) != src_e["mime"] or not _is_int(e.get("size")) or int(e["size"]) != src_e["size"] or not _is_int(e.get("offset")) or int(e["offset"]) != src_e["offset"]:
                raise ValueError("leaf_entry_mismatch_source_table")
        if lr.get("sha256") != lc["sha256"]:
            raise ValueError("leaf_sha_mismatch_contract")
        if (src_e["name"], src_e["mime"], src_e["size"], str(lc["sha256"]).lower()) not in catalog_rows:
            raise ValueError("leaf_not_in_catalog_row")
        if not _is_int(lr.get("copy_size")) or int(lr["copy_size"]) != src_e["size"]:
            raise ValueError("leaf_copy_size_mismatch")
        if not _is_int(lr.get("size")) or int(lr["size"]) != src_e["size"] or not _is_int(lr.get("offset")) or int(lr["offset"]) != src_e["offset"]:
            raise ValueError("leaf_size_offset_mismatch")
        if int(src_e["offset"]) + int(src_e["size"]) > 318217469:
            raise ValueError("leaf_range_out_of_bounds")
        ref = ind_refs.get(normalize(lr["virtual_path"]))
        if not isinstance(lr.get("texture_ref"), dict) or set(lr["texture_ref"].keys()) != _REF_KEYS or lr["texture_ref"] != ref:
            raise ValueError("leaf_texture_ref_mismatch")
        copy_path = (report_dir / out_r).resolve()
        if report_dir not in copy_path.parents:
            raise ValueError("leaf_output_escape")
        if not copy_path.is_file():
            raise ValueError(f"leaf_copy_missing:{copy_path}")
        if sha256_stream(copy_path, lc["entry"]["size"]) != str(lc["sha256"]).lower():
            raise ValueError("leaf_copy_hash_mismatch")
        if lr.get("copy_sha256") != lc["sha256"]:
            raise ValueError("report_leaf_copy_hash_mismatch")
    lims = report.get("limitations") or []
    if not isinstance(lims, list) or not lims:
        raise ValueError("limitations_missing")
    return {"status": SUCCESS, "contract_sha": contract_sha, "report_sha256": report_sha, "dependency_scope": "three_road_models", "scope": "three_road_models", "build_ready": False, "provider_ambiguity": "NOT_TESTED", "native_resolution": "NOT_TESTED", "parsed_texts": 2, "leaves": 4, "saved_assets": 8, "pbo_reopened": False}

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--contract", required=True); ap.add_argument("--contract-sha", required=True); ap.add_argument("--report", required=True); ap.add_argument("--report-sha", required=True); ap.add_argument("--output", required=True)
    args = ap.parse_args(argv); out = Path(args.output)
    def fail(phase, reason):
        try:
            with open(out, "x", encoding="utf-8", newline="\n") as f:
                json.dump({"status": FAILURE, "phase": phase, "reason": reason}, f, indent=2, sort_keys=True); f.write("\n")
        except Exception:
            pass
        print(json.dumps({"status": FAILURE, "phase": phase, "reason": reason})); return 2
    if out.exists():
        print(json.dumps({"status": FAILURE, "phase": "output", "reason": "output_exists"})); return 2
    try:
        craw = Path(args.contract).read_bytes(); csha = sha256_bytes(craw)
        if csha != str(args.contract_sha).lower():
            return fail("contract_sha", "mismatch")
        contract = json.loads(craw.decode("utf-8"))
        rraw = Path(args.report).read_bytes(); rsha = sha256_bytes(rraw)
        if rsha != str(args.report_sha).lower():
            return fail("report_sha", "mismatch")
        report = json.loads(rraw.decode("utf-8"))
    except Exception as e:
        return fail("read", str(e))
    try:
        verdict = verify(contract, csha, report, rsha, args.report)
    except Exception as e:
        return fail("verify", str(e))
    try:
        with open(out, "x", encoding="utf-8", newline="\n") as f:
            json.dump(verdict, f, indent=2, sort_keys=True); f.write("\n")
    except Exception as e:
        print(json.dumps({"status": FAILURE, "phase": "output", "reason": str(e)})); return 2
    print(json.dumps(verdict)); return 0

if __name__ == "__main__":
    raise SystemExit(main())
