"""Producer/parser/range capture for EV112 road-material dependencies.

Offline, standard library only. Never invokes CfgConvert/build/DayZ/git.
Imports the pinned deployed-surface helper by file path only after its
contract hash/size are verified, and uses its pbo_table/read_payload
primitives. On any failure after the exclusive output directory exists,
writes INCONCLUSIVE_DEPENDENCIES and never a passing status.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import struct
import sys
from pathlib import Path

SUCCESS = "SAVED_PILOT_DEPENDENCIES_RESOLVED_ONLY"
FAILURE = "INCONCLUSIVE_DEPENDENCIES"
WS = b" \t\r\n"
SYMBOLS = b"{}[]=,;"
MAX_TEXT = 1048576

class RvmatError(ValueError):
    def __init__(self, message, offset=None):
        super().__init__(message)
        self.offset = offset
        self.reason = message

class DependencyError(RuntimeError):
    def __init__(self, phase, reason):
        super().__init__(f"{phase}: {reason}")
        self.phase = phase
        self.reason = str(reason)

def require(cond, msg):
    if not cond:
        raise ValueError(msg)

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()

def sha256_stream(path, declared_size, cap=268435456):
    st = os.stat(path)
    if st.st_size != declared_size:
        raise ValueError("size_mismatch_before_read")
    if declared_size > cap or declared_size < 0:
        raise ValueError("source_size_over_cap")
    h = hashlib.sha256(); total = 0
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1048576)
            if not chunk:
                break
            total += len(chunk)
            if total > cap:
                raise ValueError("source_size_over_cap")
            h.update(chunk)
    if total != declared_size:
        raise ValueError("size_changed_during_read")
    return h.hexdigest()

def stat_snapshot(st):
    return {"dev": int(st.st_dev), "ino": int(st.st_ino), "size": int(st.st_size), "mtime_ns": int(st.st_mtime_ns), "ctime_ns": int(st.st_ctime_ns)}

_SAME_API_FIELDS = ("dev", "ino", "size", "mtime_ns", "ctime_ns")
_CROSS_FIELDS = ("dev", "ino", "size", "mtime_ns")

def compare_stat_snapshots(before_path, before_handle, after_path, after_handle):
    for a, b, label, fields in ((before_path, before_handle, "path_handle_before", _CROSS_FIELDS), (after_path, after_handle, "path_handle_after", _CROSS_FIELDS), (before_path, after_path, "path_before_after", _SAME_API_FIELDS), (before_handle, after_handle, "handle_before_after", _SAME_API_FIELDS)):
        for k in fields:
            if a[k] != b[k]:
                raise ValueError(f"stat_mismatch:{label}:{k}")
    return True

def verify_pinned_file(path, sha256, size, cap=268435456):
    if isinstance(size, bool) or not isinstance(size, int):
        raise ValueError("pinned_size_not_int")
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"missing_file:{path}")
    st = stat_snapshot(os.stat(p))
    if st["size"] != int(size):
        raise ValueError(f"pinned_size_mismatch:{path}")
    digest = sha256_stream(p, int(size), cap=cap)
    if digest != str(sha256).lower():
        raise ValueError(f"pinned_sha_mismatch:{path}")
    return {"path": str(path), "sha256": digest, "size": int(size), "stat": st}

def read_pinned_bytes(path, sha256, size, cap=MAX_TEXT):
    if int(size) > cap:
        raise ValueError("text_size_over_cap")
    verify_pinned_file(path, sha256, size, cap=cap)
    data = Path(path).read_bytes()
    if len(data) != int(size) or sha256_bytes(data) != str(sha256).lower():
        raise ValueError("text_bytes_not_hashed_bytes")
    return data

def lex_rvmat(data):
    if not isinstance(data, (bytes, bytearray)):
        raise RvmatError("bytes_required", 0)
    data = bytes(data); tokens = []; i = 0; n = len(data)
    while i < n:
        b = data[i]
        if b in WS:
            i += 1; continue
        start = i
        if b == 34:  # quote: terminates at first quote, backslash literal
            j = data.find(b'"', i + 1)
            if j < 0:
                raise RvmatError(f"unterminated_string at {start}", start)
            raw = data[i:j + 1]
            try:
                value = data[i + 1:j].decode("ascii")
            except UnicodeDecodeError:
                raise RvmatError(f"non_ascii_string at {start}", start)
            tokens.append({"kind": "string", "value": value, "start": start, "end": j + 1, "sha256": sha256_bytes(raw)}); i = j + 1; continue
        if (65 <= b <= 90) or (97 <= b <= 122) or b == 95:
            j = i + 1
            while j < n and ((65 <= data[j] <= 90) or (97 <= data[j] <= 122) or (48 <= data[j] <= 57) or data[j] == 95):
                j += 1
            raw = data[i:j]
            tokens.append({"kind": "ident", "value": raw.decode("ascii"), "start": start, "end": j, "sha256": sha256_bytes(raw)}); i = j; continue
        if 48 <= b <= 57:
            j = i
            while j < n and 48 <= data[j] <= 57:
                j += 1
            if j < n and data[j] == 46:
                if j + 1 >= n or not (48 <= data[j + 1] <= 57):
                    raise RvmatError(f"bad_number at {start}", start)
                j += 1
                while j < n and 48 <= data[j] <= 57:
                    j += 1
            if j < n and (data[j] == 46 or data[j] == 95 or (65 <= data[j] <= 90) or (97 <= data[j] <= 122)):
                raise RvmatError(f"bad_number at {start}", start)
            raw = data[i:j]
            tokens.append({"kind": "number", "value": raw.decode("ascii"), "start": start, "end": j, "sha256": sha256_bytes(raw)}); i = j; continue
        if b in SYMBOLS:
            raw = data[i:i + 1]
            tokens.append({"kind": "symbol", "value": chr(b), "start": start, "end": i + 1, "sha256": sha256_bytes(raw)}); i += 1; continue
        raise RvmatError(f"unsupported_syntax at {start}: byte 0x{b:02x}", start)
    return tokens

TOP_ASSIGN = {"ambient": "vec4", "diffuse": "vec4", "forcedDiffuse": "vec4", "emmisive": "vec4", "specular": "vec4", "specularPower": "scalar", "PixelShaderID": "string", "VertexShaderID": "string"}
STAGE_ASSIGN = {"texture": "string", "uvSource": "string"}
UV_ASSIGN = {"aside": "vec3", "up": "vec3", "dir": "vec3", "pos": "vec3"}
SCOPES = {"top": (TOP_ASSIGN, {"Stage1", "Stage2"}), "stage": (STAGE_ASSIGN, {"uvTransform"}), "uv": (UV_ASSIGN, set())}

class _Parser:
    def __init__(self, tokens, data):
        self.toks = tokens; self.i = 0; self.data = data
        self.assignments = []; self.classes = []
    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None
    def next(self, what="token"):
        t = self.peek()
        if t is None:
            raise RvmatError(f"unexpected_eof expecting {what}", len(self.data))
        self.i += 1; return t
    def expect_symbol(self, sym):
        t = self.next(sym)
        if t["kind"] != "symbol" or t["value"] != sym:
            raise RvmatError(f"expected '{sym}' at {t['start']}", t["start"])
        return t
    def expect_ident(self):
        t = self.next("identifier")
        if t["kind"] != "ident":
            raise RvmatError(f"expected identifier at {t['start']}", t["start"])
        return t
    def parse_body(self, prefix, scope):
        allowed_assign, allowed_classes = SCOPES[scope]
        seen_a = set(); seen_c = set()
        while True:
            t = self.peek()
            if t is None or (t["kind"] == "symbol" and t["value"] == "}"):
                return seen_a, seen_c
            if t["kind"] != "ident":
                raise RvmatError(f"unsupported_syntax at {t['start']}", t["start"])
            if t["value"] == "class":
                self.next(); name_tok = self.expect_ident(); name = name_tok["value"]
                if name not in allowed_classes:
                    raise RvmatError(f"unknown_class {name} at {name_tok['start']}", name_tok["start"])
                if name in seen_c:
                    raise RvmatError(f"duplicate_class {name} at {name_tok['start']}", name_tok["start"])
                seen_c.add(name); path = f"{prefix}.{name}" if prefix else name
                self.classes.append(path)
                self.expect_symbol("{")
                child_scope = "stage" if scope == "top" else "uv"
                self.parse_body(path, child_scope)
                self.expect_symbol("}"); self.expect_symbol(";")
            else:
                name_tok = self.next(); name = name_tok["value"]
                if name not in allowed_assign:
                    raise RvmatError(f"unknown_assignment {name} at {name_tok['start']}", name_tok["start"])
                if name in seen_a:
                    raise RvmatError(f"duplicate_assignment {name} at {name_tok['start']}", name_tok["start"])
                seen_a.add(name)
                has_brackets = False
                nt = self.peek()
                if nt and nt["kind"] == "symbol" and nt["value"] == "[":
                    self.next(); self.expect_symbol("]"); has_brackets = True
                self.expect_symbol("=")
                path = f"{prefix}.{name}" if prefix else name
                vt = self.peek()
                if vt is None:
                    raise RvmatError(f"unexpected_eof value at {len(self.data)}", len(self.data))
                if vt["kind"] == "string":
                    tok = self.next(); typ = "string"; value = tok["value"]; raw = [tok["value"]]; s_start, s_end = tok["start"], tok["end"]
                    if has_brackets:
                        raise RvmatError(f"brackets_on_string {name} at {name_tok['start']}", name_tok["start"])
                elif vt["kind"] == "number":
                    tok = self.next(); typ = "scalar"; value = tok["value"]; raw = [tok["value"]]; s_start, s_end = tok["start"], tok["end"]
                    if has_brackets:
                        raise RvmatError(f"brackets_on_scalar {name} at {name_tok['start']}", name_tok["start"])
                elif vt["kind"] == "symbol" and vt["value"] == "{":
                    if not has_brackets:
                        raise RvmatError(f"missing_brackets {name} at {name_tok['start']}", name_tok["start"])
                    self.next(); lexemes = []
                    if self.peek() and self.peek()["kind"] == "symbol" and self.peek()["value"] == "}":
                        raise RvmatError(f"empty_array {name} at {name_tok['start']}", name_tok["start"])
                    while True:
                        num = self.next("number")
                        if num["kind"] != "number":
                            raise RvmatError(f"expected number at {num['start']}", num["start"])
                        lexemes.append(num["value"])
                        sep = self.next(", or }")
                        if sep["kind"] == "symbol" and sep["value"] == ",":
                            continue
                        if sep["kind"] == "symbol" and sep["value"] == "}":
                            break
                        raise RvmatError(f"bad_array_separator at {sep['start']}", sep["start"])
                    typ = "vec4" if len(lexemes) == 4 else "vec3" if len(lexemes) == 3 else "numericarray"
                    value = list(lexemes); raw = list(lexemes); s_start, s_end = vt["start"], sep["end"]
                else:
                    raise RvmatError(f"unsupported_value at {vt['start']}", vt["start"])
                expected = allowed_assign[name]
                if typ != expected:
                    raise RvmatError(f"wrong_type {path}: {typ} != {expected} at {name_tok['start']}", name_tok["start"])
                self.expect_symbol(";")
                entry = {"path": path, "name": name, "type": typ, "value": value, "raw_lexemes": raw, "value_start": s_start, "value_end": s_end}
                if typ == "string":
                    entry["string_start"] = s_start; entry["string_end"] = s_end
                self.assignments.append(entry)

def parse_rvmat(data):
    data = bytes(data); tokens = lex_rvmat(data); p = _Parser(tokens, data)
    seen_a, seen_c = p.parse_body("", "top")
    if p.peek() is not None:
        t = p.peek(); raise RvmatError(f"unconsumed_syntax at {t['start']}", t["start"])
    if seen_a != set(TOP_ASSIGN) or seen_c != {"Stage1", "Stage2"}:
        raise RvmatError("closed_top_structure_mismatch", len(data))
    # Nested closed-structure validation.
    by_scope = {}
    for a in p.assignments:
        parts = a["path"].split("."); scope = ".".join(parts[:-1])
        by_scope.setdefault(scope, set()).add(parts[-1])
    for stage in ("Stage1", "Stage2"):
        if by_scope.get(stage) != {"texture", "uvSource"}:
            raise RvmatError(f"closed_stage_structure_mismatch:{stage}", len(data))
        if by_scope.get(stage + ".uvTransform") != {"aside", "up", "dir", "pos"}:
            raise RvmatError(f"closed_uv_structure_mismatch:{stage}", len(data))
    if set(by_scope) != {"", "Stage1", "Stage2", "Stage1.uvTransform", "Stage2.uvTransform"}:
        raise RvmatError("closed_scope_mismatch", len(data))
    semicolons = sum(1 for t in tokens if t["kind"] == "symbol" and t["value"] == ";")
    inv = {"assignments": len(p.assignments), "classes": len(p.classes), "strings": sum(1 for a in p.assignments if a["type"] == "string"), "vec3": sum(1 for a in p.assignments if a["type"] == "vec3"), "vec4": sum(1 for a in p.assignments if a["type"] == "vec4"), "scalar": sum(1 for a in p.assignments if a["type"] == "scalar"), "semicolons": semicolons}
    refs = []
    for a in p.assignments:
        if a["name"] == "texture" and a["type"] == "string":
            refs.append({"path": a["path"], "raw_virtual_path": a["value"], "virtual_path": normalize_virtual(a["value"]), "string_start": a["string_start"], "string_end": a["string_end"]})
    eof_newline = bool(data.endswith(b"\n"))
    return {"assignments": p.assignments, "classes": list(p.classes), "texture_refs": refs, "tokens": tokens, "inventory": inv, "semicolons": semicolons, "eof_newline": eof_newline, "eof_state": "newline" if eof_newline else "no_newline", "sha256": sha256_bytes(data), "size": len(data)}

def normalize_virtual(p):
    return str(p).replace("\\", "/").lower().strip("/")

def normalize_prefix(p):
    return normalize_virtual(p)

def strip_pbo_prefix(virtual_path, prefix):
    v = normalize_virtual(virtual_path); pre = normalize_prefix(prefix)
    if not pre:
        raise ValueError("prefix_missing")
    if v == pre:
        raise ValueError("prefix_only_path")
    if not v.startswith(pre + "/"):
        raise ValueError("prefix_mismatch_or_wrong_provider")
    return v[len(pre) + 1:]

def find_entry(entries, virtual_path, prefix):
    rel = strip_pbo_prefix(virtual_path, prefix)
    for e in entries:
        name = normalize_virtual(e.get("name", ""))
        candidate = name[len(normalize_prefix(prefix)) + 1:] if name.startswith(normalize_prefix(prefix) + "/") else name
        if candidate == rel:
            return e
    raise ValueError(f"entry_not_found:{rel}")

def validate_output_rel(out_rel):
    r = str(out_rel).replace(chr(92), "/")
    if not r or r.startswith("/") or ".." in r.split("/") or (len(r) > 1 and r[1] == ":"):
        raise ValueError("leaf_output_escape")
    if not r.startswith("leaves/"):
        raise ValueError("leaf_output_not_under_leaves")
    return r

def validate_range_leaves(leaves, file_size, range_cap=16777216, total_cap=67108864):
    if len(leaves) != 4:
        raise ValueError("leaves_must_be_four")
    if isinstance(file_size, bool) or not isinstance(file_size, int):
        raise ValueError("file_size_not_int")
    total = 0
    for leaf in leaves:
        e = leaf.get("entry") or {}
        if set(e.keys()) != {"name", "mime", "size", "offset"}:
            raise ValueError("leaf_entry_missing_or_extra_field")
        for k in ("mime", "size", "offset"):
            if isinstance(e[k], bool) or not isinstance(e[k], int):
                raise ValueError(f"leaf_entry_field_not_int:{k}")
        if int(e["mime"]) != 0:
            raise ValueError("mime_not_zero")
        size = int(e["size"]); off = int(e["offset"])
        if size <= 0:
            raise ValueError("range_size_not_positive")
        if size > range_cap:
            raise ValueError("range_over_16MiB")
        if off < 0 or off + size > int(file_size):
            raise ValueError("range_out_of_bounds")
        validate_output_rel(leaf.get("output", ""))
        total += size
    if total > total_cap:
        raise ValueError("ranges_over_64MiB_total")
    return True

def check_range_bytes(data, expected_sha):
    if sha256_bytes(data) != str(expected_sha).lower():
        raise ValueError("payload_hash")
    return True

def normalize_entry(e, prefix):
    if not isinstance(e, dict) or set(e.keys()) != {"name", "mime", "size", "offset"}:
        raise ValueError("source_table_entry_missing_or_extra_field")
    for k in ("mime", "size", "offset"):
        if isinstance(e[k], bool) or not isinstance(e[k], int):
            raise ValueError(f"source_table_entry_field_not_int:{k}")
    if not isinstance(e["name"], str) or not e["name"]:
        raise ValueError("source_table_entry_name_missing")
    name = normalize_virtual(e["name"])
    pre = normalize_prefix(prefix)
    if name.startswith(pre + "/"):
        name = name[len(pre) + 1:]
    return {"name": name, "mime": int(e["mime"]), "size": int(e["size"]), "offset": int(e["offset"])}

def extract_source_table(obj, prefix):
    if not isinstance(obj, dict) or set(obj.keys()) != {"properties", "entries"}:
        raise ValueError("source_table_shape_exact_properties_entries")
    props = obj["properties"]; raw = obj["entries"]
    if not isinstance(props, dict) or not props:
        raise ValueError("source_table_properties_shape")
    if not isinstance(raw, list):
        raise ValueError("source_table_entries_shape")
    props = {str(k): str(v) for k, v in props.items()}
    prefix_values = [v for k, v in props.items() if str(k).lower() == "prefix"]
    if len(prefix_values) != 1 or normalize_prefix(prefix_values[0]) != normalize_prefix(prefix):
        raise ValueError("source_table_prefix_mismatch")
    return props, [normalize_entry(e, prefix) for e in raw]

def compare_live_to_source_table(live_properties, live_entries, source_obj, prefix):
    s_props, s_entries = extract_source_table(source_obj, prefix)
    l_props = {str(k): str(v) for k, v in dict(live_properties).items()}
    l_entries = [normalize_entry(e, prefix) for e in live_entries]
    if l_props != s_props:
        raise ValueError("pbo_properties_mismatch")
    if l_entries != s_entries:  # list order exact; properties order-insensitive via dict
        raise ValueError("pbo_entries_mismatch_order_or_content")
    return True

def catalog_leaf_rows(obj):
    rows = obj
    if not isinstance(rows, list):
        raise ValueError("catalog_shape_exact")
    out = set()
    for r in rows:
        if not isinstance(r, dict) or set(r.keys()) != {"name", "normalized_name", "category", "mime", "size", "sha256"}:
            raise ValueError("catalog_row_shape")
        if not isinstance(r['name'], str) or not isinstance(r['category'], str) or r['normalized_name'] != normalize_virtual(r['name']):
            raise ValueError('catalog_normalized_name')
        for k in ("mime", "size"):
            if isinstance(r[k], bool) or not isinstance(r[k], int):
                raise ValueError(f"catalog_row_field_not_int:{k}")
        out.add((normalize_virtual(r["name"]), int(r["mime"]), int(r["size"]), str(r["sha256"]).lower()))
    return out

def write_json_exclusive(path, obj):
    path = Path(path)
    with open(path, "x", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, sort_keys=True); f.write("\n")

def load_pinned_helper(contract):
    src = contract["sources"]["helper"]
    verify_pinned_file(src["path"], src["sha256"], src["size"])
    spec = importlib.util.spec_from_file_location("pinned_deployed_surface_inventory_ev112", src["path"])
    if spec is None or spec.loader is None:
        raise ValueError("helper_load_failed")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    if not callable(getattr(mod, "pbo_table", None)) or not callable(getattr(mod, "read_payload", None)):
        raise ValueError("helper_primitives_missing")
    verify_pinned_file(src["path"], src["sha256"], src["size"])
    return mod

def hash_pbo(path, declared_size):
    if isinstance(declared_size, bool) or not isinstance(declared_size, int):
        raise ValueError("pbo_declared_size_not_int")
    st_path_before = stat_snapshot(os.stat(path))
    if st_path_before["size"] != int(declared_size):
        raise ValueError("pbo_size_mismatch")
    h = hashlib.sha256(); total = 0
    with open(path, "rb") as f:
        st_handle_before = stat_snapshot(os.fstat(f.fileno()))
        compare_stat_snapshots(st_path_before, st_handle_before, st_path_before, st_handle_before)
        while True:
            chunk = f.read(1048576)
            if not chunk:
                break
            total += len(chunk); h.update(chunk)
        st_handle_after = stat_snapshot(os.fstat(f.fileno()))
        compare_stat_snapshots(st_path_before, st_handle_before, st_path_before, st_handle_after)
    if total != int(declared_size):
        raise ValueError("pbo_size_changed_during_read")
    st_path_after = stat_snapshot(os.stat(path))
    compare_stat_snapshots(st_path_before, st_handle_before, st_path_after, st_handle_after)
    return h.hexdigest(), st_path_before, st_handle_before, st_path_after

def run(contract, contract_sha):
    # Contract shape.
    if contract.get("schema") != "ROAD_B4A3_V1":
        raise DependencyError("contract", "schema_mismatch")
    for key in ("sources", "texts", "saved_assets", "leaves", "pbo", "inventory", "limits", "output", "attempt_marker", "scope", "build_ready", "provider_ambiguity", "native_resolution"):
        if key not in contract:
            raise DependencyError("contract", f"missing_field:{key}")
    if contract["scope"] != "three_road_models" or contract["build_ready"] is not False:
        raise DependencyError("contract", "scope_or_build_ready_mismatch")
    if contract["provider_ambiguity"] != "NOT_TESTED" or contract["native_resolution"] != "NOT_TESTED":
        raise DependencyError("contract", "not_tested_markers_mismatch")
    limits = contract["limits"]
    range_cap = int(limits.get("range_bytes", 16777216)); total_cap = int(limits.get("total_ranges", 67108864))
    if range_cap != 16777216 or total_cap != 67108864:
        raise DependencyError("contract", "range_limits_mismatch")
    if len(contract["saved_assets"]) != 8 or len(contract["texts"]) != 2 or len(contract["leaves"]) != 4:
        raise DependencyError("contract", "cardinality_mismatch")
    # Phase: source pins before.
    try:
        sources_before = {}
        for label, pin in contract["sources"].items():
            sources_before[label] = verify_pinned_file(pin["path"], pin["sha256"], pin["size"])
        saved_before = [verify_pinned_file(a["path"], a["sha256"], a["size"]) for a in contract["saved_assets"]]
    except Exception as e:
        raise DependencyError("source_pins_before", e)
    # Catalog / source_table / models inherited by hash only (no ODOL reparse).
    try:
        cat_pin = contract["sources"]["catalog"]; st_pin = contract["sources"]["source_table"]
        catalog_obj = json.loads(read_pinned_bytes(cat_pin["path"], cat_pin["sha256"], cat_pin["size"], cap=max(MAX_TEXT, int(cat_pin["size"]))).decode("utf-8"))
        source_obj = json.loads(read_pinned_bytes(st_pin["path"], st_pin["sha256"], st_pin["size"], cap=max(MAX_TEXT, int(st_pin["size"]))).decode("utf-8"))
        cat_rows = catalog_leaf_rows(catalog_obj)
        if len(catalog_obj) != 501:
            raise ValueError('catalog_entry_count')
        for leaf in contract["leaves"]:
            le = normalize_entry(leaf["entry"], contract["pbo"]["prefix"])
            if not any(m == le["mime"] and s == le["size"] and h == str(leaf["sha256"]).lower() and (n == le["name"] or n == normalize_virtual(leaf["virtual_path"])) for n, m, s, h in cat_rows):
                raise ValueError(f"leaf_not_in_catalog_row:{leaf.get('virtual_path')}")
    except DependencyError:
        raise
    except Exception as e:
        raise DependencyError("catalog_source_table", e)
    # Helper after hash verification.
    try:
        helper = load_pinned_helper(contract)
    except Exception as e:
        raise DependencyError("helper", e)
    # Texts: bytes parsed are those hashed.
    parsed_texts = []; all_refs = []
    try:
        for t in contract["texts"]:
            data = read_pinned_bytes(t["path"], t["sha256"], t["size"])
            parsed = parse_rvmat(data)
            if parsed["inventory"] != contract["inventory"]:
                raise ValueError(f"inventory_mismatch:{t['id']}:{parsed['inventory']} != {contract['inventory']}")
            spec = None
            for a in parsed["assignments"]:
                if a["path"] == "specularPower":
                    spec = a["value"]
            if str(spec) != str(t["specular_power"]):
                raise ValueError(f"specular_power_mismatch:{t['id']}")
            parsed_texts.append({"id": t["id"], "path": t["path"], "sha256": t["sha256"], "size": int(t["size"]), "specular_power": t["specular_power"], "inventory": parsed["inventory"], "assignments": parsed["assignments"], "classes": parsed["classes"], "tokens": parsed["tokens"], "texture_refs": parsed["texture_refs"], "eof_newline": parsed["eof_newline"], "eof_state": parsed["eof_state"], "semicolons": parsed["semicolons"]})
            all_refs.extend(parsed["texture_refs"])
    except Exception as e:
        raise DependencyError("rvmat_parse", e)
    # Leaves exactly the extracted texture references.
    try:
        ref_set = {r["virtual_path"] for r in all_refs}
        leaf_set = {normalize_virtual(l["virtual_path"]) for l in contract["leaves"]}
        if len(all_refs) != 4 or ref_set != leaf_set:
            raise ValueError(f"leaf_ref_set_mismatch refs={sorted(ref_set)} leaves={sorted(leaf_set)}")
    except Exception as e:
        raise DependencyError("leaf_reference_set", e)
    # PBO live table.
    pbo = contract["pbo"]; pbo_path = pbo["path"]; prefix = pbo["prefix"]
    if normalize_prefix(prefix) != "dz/structures/roads":
        raise DependencyError("pbo_prefix", "prefix_must_be_dz/structures/roads")
    if int(pbo["size"]) != 318217469:
        raise DependencyError("pbo", "pbo_size_pin_mismatch")
    pbo_stats = {}; live_props = {}; live_entries = []
    try:
        sha_before, sp_b, sh_b, sp_mid = hash_pbo(pbo_path, int(pbo["size"]))
        if sha_before != str(pbo["sha256"]).lower():
            raise ValueError("pbo_sha_before_mismatch")
        with open(pbo_path, "rb") as f:
            sh_table = stat_snapshot(os.fstat(f.fileno()))
            live_props, live_entries = helper.pbo_table(f, int(pbo["size"]))
            sh_table_after = stat_snapshot(os.fstat(f.fileno()))
            compare_stat_snapshots(sh_table, sh_table, sh_table_after, sh_table_after)
        compare_stat_snapshots(sp_b, sh_b, sp_b, sh_table_after)
        compare_live_to_source_table(live_props, live_entries, source_obj, prefix)
        validate_range_leaves(contract["leaves"], int(pbo["size"]), range_cap, total_cap)
        # Exact leaf entries vs live table.
        for leaf in contract["leaves"]:
            e = find_entry(live_entries, leaf["virtual_path"], prefix)
            le = leaf["entry"]
            if normalize_entry(e, prefix)["name"] != normalize_entry(le, prefix)["name"]:
                raise ValueError(f"leaf_entry_name_mismatch:{leaf['virtual_path']}")
            if int(e["mime"]) != int(le["mime"]) or int(e["size"]) != int(le["size"]) or int(e["offset"]) != int(le["offset"]):
                raise ValueError(f"leaf_entry_mismatch:{leaf['virtual_path']}")
    except DependencyError:
        raise
    except Exception as e:
        raise DependencyError("pbo_table", e)
    return locals()

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--contract", required=True); ap.add_argument("--contract-sha", required=True)
    args = ap.parse_args(argv)
    contract_path = Path(args.contract); output_dir = None; marker_done = False
    try:
        raw = contract_path.read_bytes()
    except Exception as e:
        print(json.dumps({"status": FAILURE, "phase": "contract_read", "reason": str(e)})); return 2
    contract_sha = sha256_bytes(raw)
    if contract_sha != str(args.contract_sha).lower():
        print(json.dumps({"status": FAILURE, "phase": "contract_sha", "reason": "contract_sha_mismatch"})); return 2
    try:
        contract = json.loads(raw.decode("utf-8"))
    except Exception as e:
        print(json.dumps({"status": FAILURE, "phase": "contract_parse", "reason": str(e)})); return 2
    # Exclusive attempt marker at exact contract path, consumed even on failure.
    try:
        marker = Path(contract["attempt_marker"]); marker.parent.mkdir(parents=True, exist_ok=True)
        with open(marker, "x", encoding="utf-8", newline="\n") as f:
            json.dump({"contract_sha": contract_sha, "status": "attempted", "output": contract.get("output")}, f, indent=2, sort_keys=True); f.write("\n")
        marker_done = True
    except Exception as e:
        print(json.dumps({"status": FAILURE, "phase": "attempt_marker", "reason": str(e), "contract_sha": contract_sha})); return 2
    # Exclusive output dir.
    try:
        output_dir = Path(contract["output"]); os.mkdir(output_dir)
    except Exception as e:
        print(json.dumps({"status": FAILURE, "phase": "output_dir", "reason": str(e), "contract_sha": contract_sha})); return 2
    try:
        ctx = run(contract, contract_sha)
        helper = ctx["helper"]; contract2 = contract; pbo = contract["pbo"]; prefix = pbo["prefix"]; live_entries = ctx["live_entries"]; live_props = ctx["live_props"]
        # Range extraction: only four ranges, via pinned helper primitive, no full PBO read here.
        leaves_out = []; total_range = 0
        leaves_dir = output_dir / "leaves"; os.mkdir(leaves_dir)
        sp_b = ctx["sp_b"]; sh_b = ctx["sh_b"]
        with open(pbo["path"], "rb") as f:
            sh_extract = stat_snapshot(os.fstat(f.fileno()))
            compare_stat_snapshots(sp_b, sh_b, sp_b, sh_extract)
            for leaf in contract["leaves"]:
                e = find_entry(live_entries, leaf["virtual_path"], prefix)
                entry = {"name": e["name"], "mime": int(e["mime"]), "size": int(e["size"]), "offset": int(e["offset"])}
                data = helper.read_payload(f, entry, str(leaf["sha256"]).lower())
                check_range_bytes(data, leaf["sha256"])
                total_range += len(data)
                out_rel = validate_output_rel(leaf["output"])
                out_path = output_dir / out_rel
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "xb") as out:
                    out.write(data)
                copy_sha = sha256_bytes(out_path.read_bytes()) if out_path.stat().st_size <= 16777216 else sha256_stream(out_path, out_path.stat().st_size)
                if copy_sha != str(leaf["sha256"]).lower():
                    raise DependencyError("range_copy", f"copy_hash_mismatch:{leaf['virtual_path']}")
                ref = next((r for r in ctx["all_refs"] if r["virtual_path"] == normalize_virtual(leaf["virtual_path"])), None)
                leaves_out.append({"virtual_path": leaf["virtual_path"], "normalized_virtual_path": normalize_virtual(leaf["virtual_path"]), "entry": entry, "sha256": leaf["sha256"], "size": int(entry["size"]), "offset": int(entry["offset"]), "output": out_rel, "copy_sha256": copy_sha, "copy_size": int(entry["size"]), "texture_ref": ref})
        if total_range > int(contract["limits"]["total_ranges"]):
            raise DependencyError("range_copy", "total_ranges_over_limit")
        sha_after, sp_a2, sh_a2, sp_a = hash_pbo(pbo["path"], int(pbo["size"]))
        if sha_after != ctx["sha_before"] or sha_after != str(pbo["sha256"]).lower():
            raise DependencyError("pbo_after", "pbo_sha_after_mismatch")
        # Cross path/handle after: re-open handle stat vs path stat.
        with open(pbo["path"], "rb") as f:
            sh_after = stat_snapshot(os.fstat(f.fileno()))
        sp_after = stat_snapshot(os.stat(pbo["path"]))
        compare_stat_snapshots(sp_b, sh_b, sp_after, sh_after)
        # Source pins after; bytes parsed are those hashed (texts re-verified).
        sources_after = {}
        for label, pin in contract["sources"].items():
            sources_after[label] = verify_pinned_file(pin["path"], pin["sha256"], pin["size"])
        saved_after = [verify_pinned_file(a["path"], a["sha256"], a["size"]) for a in contract["saved_assets"]]
        for t in contract["texts"]:
            verify_pinned_file(t["path"], t["sha256"], t["size"])
        report = {
            "schema": "ROAD_MATERIAL_DEPENDENCIES_REPORT_EV112_V1",
            "status": SUCCESS,
            "contract_sha": contract_sha,
            "dependency_scope": contract["scope"], "scope": contract["scope"],
            "build_ready": False, "provider_ambiguity": "NOT_TESTED", "native_resolution": "NOT_TESTED",
            "pbo": {"path": pbo["path"], "sha256": pbo["sha256"], "sha256_before": ctx["sha_before"], "sha256_after": sha_after, "size": int(pbo["size"]), "prefix": prefix, "properties": {str(k): str(v) for k, v in live_props.items()}, "entries_count": len(live_entries), "stat_before": {"path": sp_b, "handle": sh_b}, "stat_after": {"path": sp_after, "handle": sh_after}},
            "sources": {label: {"path": pin["path"], "sha256": pin["sha256"], "size": int(pin["size"]), "before": ctx["sources_before"][label], "after": sources_after[label]} for label, pin in contract["sources"].items()},
            "models_evidence": {"kind": "inherited_by_hash", "models": {"path": contract["sources"]["models"]["path"], "sha256": contract["sources"]["models"]["sha256"], "size": int(contract["sources"]["models"]["size"])}, "catalog": {"path": contract["sources"]["catalog"]["path"], "sha256": contract["sources"]["catalog"]["sha256"], "size": int(contract["sources"]["catalog"]["size"])}, "source_table": {"path": contract["sources"]["source_table"]["path"], "sha256": contract["sources"]["source_table"]["sha256"], "size": int(contract["sources"]["source_table"]["size"])}, "note": "inherited_by_hash_only; ODOL not reparsed; not all 5509 scene models resolved"},
            "catalog_pins": {"catalog_sha256": contract["sources"]["catalog"]["sha256"], "models_sha256": contract["sources"]["models"]["sha256"], "source_table_sha256": contract["sources"]["source_table"]["sha256"]},
            "saved_assets": [{"virtual_path": a["virtual_path"], "path": a["path"], "sha256": a["sha256"], "size": int(a["size"]), "before": ctx["saved_before"][i], "after": saved_after[i]} for i, a in enumerate(contract["saved_assets"])],
            "parsed_texts": ctx["parsed_texts"],
            "leaves": leaves_out, "range_copies": leaves_out,
            "inventory": contract["inventory"], "limits": contract["limits"],
            "limitations": ["three_road_models_only", "provider_ambiguity_NOT_TESTED", "native_resolution_NOT_TESTED", "PAA terminal nodes; internal image format not validated", "models inherited by hash only; ODOL not reparsed", "no claim all 5509 scene models resolved", "no shader or material engine support assumed", "lexical coverage proves subset syntax only"],
        }
        write_json_exclusive(output_dir / "report.json", report)
        print(json.dumps({"status": SUCCESS, "contract_sha": contract_sha, "report": str(output_dir / "report.json")})); return 0
    except DependencyError as e:
        phase, reason = e.phase, e.reason
    except Exception as e:
        phase, reason = "run", str(e)
    # Failure path: inconclusive only, never PASS, no retry.
    try:
        if output_dir is not None and output_dir.is_dir():
            write_json_exclusive(output_dir / "report.json", {"schema": "ROAD_MATERIAL_DEPENDENCIES_REPORT_EV112_V1", "status": FAILURE, "phase": phase, "reason": reason, "contract_sha": contract_sha, "dependency_scope": contract.get("scope"), "scope": contract.get("scope"), "build_ready": False, "provider_ambiguity": "NOT_TESTED", "native_resolution": "NOT_TESTED", "limitations": ["inconclusive; no dependency resolution claimed"]})
    except Exception:
        pass
    print(json.dumps({"status": FAILURE, "phase": phase, "reason": reason, "contract_sha": contract_sha})); return 2

if __name__ == "__main__":
    raise SystemExit(main())
