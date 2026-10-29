"""RoadB4A1: stability capture for the seven R0 build inputs.

Discovery only. Reads only the seven exact build paths derived from R0.
Never calls run_discovery, never reads catalogue geometry, never promotes
the known external reference, and never declares INPUTS_MATCH.
"""
import argparse, ctypes, hashlib, json, math, ntpath, os, re, stat, sys, time
from ctypes import wintypes

SCHEMA = "road-build-source-stability.v1"
EXPECTED_HELPER_SHA256 = "2053b3c8d995421cb22b7bc8513f2c88dc6f6d91a5eb47015c84bdfc0179d1e3"
CHUNK = 65536
REPARSE = 0x400
BSL = chr(92)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_CONTRACT_KEYS = {"schema","r0_report","r0_manifest","r0_contract","helper","pins","alias","root","files","external_references","seconds","max_bytes"}
_FILE_KEYS = {"kind","name","path","reference_sha256","reference_format"}

class CaptureDeadline(TimeoutError):
    """Our elapsed-time budget, distinct from an OS read timeout."""

def _is_hex(v):
    return isinstance(v, str) and bool(_HEX64.match(v))

def _reject_constant(v):
    raise ValueError("nonfinite_json:" + str(v))

def _finite_float(v):
    f = float(v)
    if not math.isfinite(f):
        raise ValueError("nonfinite_json")
    return f

def _no_dup(pairs):
    o = {}
    for k, v in pairs:
        if k in o:
            raise ValueError("duplicate_json_key:" + str(k))
        o[k] = v
    return o

def _loads_strict(data, label):
    try:
        text = data.decode("utf-8") if isinstance(data, (bytes, bytearray)) else data
        return json.loads(text, parse_constant=_reject_constant, parse_float=_finite_float, object_pairs_hook=_no_dup)
    except ValueError:
        raise
    except Exception as e:
        raise ValueError("invalid_json:" + label + ":" + str(e)) from e

def _sha_bytes(b):
    return hashlib.sha256(b).hexdigest()

def hash_file(path):
    h = hashlib.sha256(); n = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b: break
            h.update(b); n += len(b)
    return h.hexdigest(), n

def _require_str(o, k):
    v = o.get(k)
    if not isinstance(v, str) or not v or isinstance(v, bool):
        raise ValueError("bad_string_field:" + k)
    return v

def validate_contract(c):
    if not isinstance(c, dict):
        raise ValueError("contract_not_object")
    keys = set(c)
    if keys != _CONTRACT_KEYS:
        raise ValueError("contract_fields_missing_or_unknown:" + ",".join(sorted(keys ^ _CONTRACT_KEYS)))
    if c.get("schema") != SCHEMA:
        raise ValueError("bad_contract_schema")
    for k in ("r0_report","r0_manifest","r0_contract","helper","alias","root"):
        _require_str(c, k)
    if not re.fullmatch(r"[A-Za-z]:/?", c["alias"]):
        raise ValueError("bad_alias")
    pins = c.get("pins")
    if not isinstance(pins, dict) or len(pins) < 6:
        raise ValueError("bad_pins")
    for k, v in pins.items():
        if not isinstance(k, str) or not k or not _is_hex(v):
            raise ValueError("bad_pin_entry")
    for req in (c["r0_report"], c["r0_manifest"], c["r0_contract"], c["helper"]):
        if req not in pins:
            raise ValueError("pin_missing_for:" + req)
    secs = c.get("seconds"); maxb = c.get("max_bytes")
    if isinstance(secs, bool) or not isinstance(secs, (int, float)) or not math.isfinite(float(secs)) or float(secs) <= 0 or float(secs) > 30:
        raise ValueError("bad_seconds_bool_or_nonfinite_or_nonpositive_or_gt_30")
    if isinstance(maxb, bool) or not isinstance(maxb, int) or maxb <= 0 or maxb > 268435456:
        raise ValueError("bad_max_bytes_bool_or_nonpositive_or_gt_268435456")
    files = c.get("files")
    if not isinstance(files, list) or len(files) != 7:
        raise ValueError("files_must_be_exactly_7")
    names = []; paths = []; kinds = {"model": 0, "reference": 0}
    for f in files:
        if not isinstance(f, dict) or set(f) != _FILE_KEYS:
            raise ValueError("file_fields_missing_or_unknown")
        if f["kind"] not in kinds:
            raise ValueError("bad_file_kind")
        kinds[f["kind"]] += 1
        name = _require_str(f, "name"); path = _require_str(f, "path")
        if ntpath.splitdrive(name)[0] or name.startswith(("/", BSL)) or BSL in name or ".." in name.split("/") or name.startswith("./"):
            raise ValueError("bad_relative_name:" + name)
        if not _is_hex(f["reference_sha256"]):
            raise ValueError("bad_reference_sha256")
        if not isinstance(f["reference_format"], str) or not f["reference_format"]:
            raise ValueError("bad_reference_format")
        names.append(name); paths.append(path)
    if kinds != {"model": 3, "reference": 4}:
        raise ValueError("files_must_be_3_models_4_references")
    if len(set(names)) != 7 or len(set(paths)) != 7:
        raise ValueError("duplicate_file_name_or_path")
    ext = c.get("external_references")
    if not isinstance(ext, list) or not ext or any(not isinstance(x, str) or not x for x in ext) or len(set(ext)) != len(ext):
        raise ValueError("bad_external_references")
    return c

def load_contract(contract_path, external_sha):
    if not _is_hex(str(external_sha or "").lower()):
        raise ValueError("bad_external_contract_sha256")
    with open(contract_path, "rb") as f:
        raw = f.read()
    actual = _sha_bytes(raw)
    if actual != str(external_sha).lower():
        raise ValueError("contract_sha256_mismatch_before_json")
    c = _loads_strict(raw, "contract")
    validate_contract(c)
    return c, raw, actual

def _load_helper(helper_bytes, helper_path):
    mod = {"__name__": "_pinned_road_build_discovery_ev112", "__file__": str(helper_path)}
    code = compile(bytes(helper_bytes), str(helper_path), "exec")
    exec(code, mod)
    for fn in ("stat_tuple","ident_tuple","is_link","query_dos_device","expected_mapping","win_norm","detect_format"):
        if not callable(mod.get(fn)):
            raise ValueError("helper_missing_pure_function:" + fn)
    if "run_discovery" in mod:
        pass
    return mod

def _find_key(obj, keys):
    if isinstance(obj, dict):
        for k in keys:
            if k in obj and isinstance(obj[k], str) and obj[k]:
                return obj[k]
        for v in obj.values():
            r = _find_key(v, keys)
            if r is not None: return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find_key(v, keys)
            if r is not None: return r
    return None

def _all_strings(obj, acc=None):
    if acc is None: acc = []
    if isinstance(obj, str): acc.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values(): _all_strings(v, acc)
    elif isinstance(obj, list):
        for v in obj: _all_strings(v, acc)
    return acc

def _alias_values(obj, names):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in names: out.append(v)
            else: out.extend(_alias_values(v, names))
    elif isinstance(obj, list):
        for v in obj: out.extend(_alias_values(v, names))
    return out

def _check_aliases(obj, canonical_key, alias_names, expected, label):
    vals = _alias_values(obj, set(alias_names))
    for v in vals:
        if v != expected:
            raise ValueError(label + "_alias_disagreement:" + canonical_key)

def derive_expected_files(report, contract):
    if not isinstance(report, dict):
        raise ValueError("r0_report_not_object")
    models = report.get("models"); refs = report.get("references")
    if not isinstance(models, list) or len(models) != 3:
        raise ValueError("r0_models_must_be_3")
    if not isinstance(refs, list):
        raise ValueError("r0_references_missing")
    internal = [r for r in refs if isinstance(r, dict) and isinstance(r.get("build"), dict)]
    external = [r for r in refs if isinstance(r, dict) and not isinstance(r.get("build"), dict)]
    if len(internal) != 4:
        raise ValueError("r0_internal_references_must_be_4")
    if [r.get("normalized") for r in external] != list(contract["external_references"]):
        raise ValueError("external_references_changed_or_promoted")
    expected = []
    for m in models:
        b = m.get("build") if isinstance(m, dict) else None
        if not isinstance(b, dict): raise ValueError("r0_model_missing_build")
        name = m.get("model") or b.get("normalized")
        if name != b.get("normalized"): raise ValueError("r0_model_name_build_mismatch")
        sha = m.get("catalog_sha256")
        if not _is_hex(sha or ""): raise ValueError("r0_model_missing_catalog_sha")
        if m.get("pbo_sha256") is not None and m.get("pbo_sha256") != sha: raise ValueError("r0_model_pbo_catalog_disagreement")
        expected.append({"kind":"model","name":name,"path":b.get("path"),"reference_sha256":sha,"reference_format":"UNKNOWN"})
    for r in internal:
        b = r["build"]; name = r.get("normalized")
        if name != b.get("normalized"): raise ValueError("r0_ref_name_build_mismatch")
        sha = r.get("expected_sha256") or r.get("pbo_sha256")
        if not _is_hex(sha or ""): raise ValueError("r0_ref_missing_sha")
        if r.get("pbo_sha256") is not None and r.get("expected_sha256") is not None and r["pbo_sha256"] != r["expected_sha256"]: raise ValueError("r0_ref_pbo_expected_disagreement")
        expected.append({"kind":"reference","name":name,"path":b.get("path"),"reference_sha256":sha,"reference_format":"UNKNOWN"})
    if len({e["name"] for e in expected}) != 7: raise ValueError("r0_derived_duplicate_names")
    by_name = {e["name"]: e for e in expected}
    _norm_root = os.path.normpath(contract["root"])
    cby = {}
    for f in contract["files"]:
        if f["name"] in cby: raise ValueError("contract_duplicate_name")
        cby[f["name"]] = f
        want_path = os.path.join(_norm_root, *f["name"].split("/"))
        if f["path"] != want_path: raise ValueError("contract_path_not_root_plus_name:" + f["name"])
    if set(by_name) != set(cby): raise ValueError("contract_files_omission_or_extra_vs_r0")
    for name, e in by_name.items():
        f = cby[name]
        if f["kind"] != e["kind"] or f["path"] != e["path"] or f["reference_sha256"] != e["reference_sha256"]: raise ValueError("contract_file_mismatch_vs_r0:" + name)
        if f["path"] != os.path.join(_norm_root, *name.split("/")): raise ValueError("r0_build_path_not_exact_root_plus_name:" + name)
    return expected

def _stat_dict(s):
    if s is None: return None
    return {"st_dev":int(s.st_dev),"st_ino":int(s.st_ino),"st_size":int(s.st_size),"st_mtime_ns":int(getattr(s,"st_mtime_ns",int(s.st_mtime*1000000000))),"st_ctime_ns":int(getattr(s,"st_ctime_ns",int(s.st_ctime*1000000000))),"st_mode":int(s.st_mode),"st_file_attributes":int(getattr(s,"st_file_attributes",0) or 0),"st_reparse_tag":int(getattr(s,"st_reparse_tag",0) or 0)}

def _first_mapping(raw):
    if isinstance(raw, (bytes, bytearray)):
        b = bytes(raw)
        if len(b) >= 2 and b[1:2] == b"\x00":
            s = b.decode("utf-16-le", "ignore")
        else:
            s = b.decode("utf-8", "ignore")
    else:
        s = str(raw)
    return s.split("\x00")[0]

def mapping_current(raw, root, helper):
    first = _first_mapping(raw)
    expected = helper["expected_mapping"](root)
    ok = helper["win_norm"](first) == helper["win_norm"](expected)
    return ok, first, expected

def _ancestors(root, name):
    parts = [p for p in name.split("/") if p][:-1]
    out = [root]; cur = root
    for p in parts:
        cur = os.path.join(cur, p); out.append(cur)
    return out

def capture_file(spec, *, helper, root, alias, query_fn, check_deadline, progress, providers=None):
    providers = providers or {}
    lstat_fn = providers.get("lstat", os.lstat); stat_fn = providers.get("stat", os.stat); fstat_fn = providers.get("fstat", os.fstat); open_fn = providers.get("open", open)
    snap = {"kind":spec["kind"],"name":spec["name"],"path":spec["path"],"reference_sha256":spec["reference_sha256"],"reference_format":spec["reference_format"],"status":"IN_PROGRESS","stable":False,"sha256":None,"size":None,"format":"UNKNOWN","prefix16":None,"predicates":[],"ancestors":[],"errors":[]}
    def pred(name, value, **obs):
        snap["predicates"].append({"name":name,"value":bool(value),"observed":obs})
    def err(stage, e):
        snap["errors"].append({"stage":stage,"type":type(e).__name__,"error":str(e)})
    anc_paths = _ancestors(root, spec["name"])
    anc_initial = []; anc_stats = []
    for p in anc_paths:
        try:
            s = lstat_fn(p); anc_stats.append(s); anc_initial.append({"path":p,"stat":_stat_dict(s),"is_link":bool(helper["is_link"](s)),"error":None})
        except OSError as e:
            anc_stats.append(None); anc_initial.append({"path":p,"stat":None,"is_link":None,"error":str(e)}); err("ancestor_initial:"+p, e)
    snap["ancestors"] = anc_initial
    progress(snap); check_deadline()
    if any(a.get("stat") is None or a.get("error") is not None for a in anc_initial):
        snap["status"] = "UNREADABLE"; progress(snap); return snap
    # metadata phase
    try:
        raw_qb = query_fn(alias) if query_fn else None
        okb, cur_b, exp_m = mapping_current(raw_qb, root, helper) if raw_qb is not None else (False, None, helper["expected_mapping"](root))
        snap["mapping_before"] = {"raw_first":cur_b,"expected":exp_m,"matches":bool(okb)}
    except Exception as e:
        snap["mapping_before"] = {"raw_first":None,"expected":helper["expected_mapping"](root),"matches":False}; err("query_dos_device_before", e); okb=False; cur_b=None
    try:
        snap["alias_lstat"] = _stat_dict(lstat_fn(alias))
    except OSError as e:
        snap["alias_lstat"] = None; snap["alias_lstat_error"] = str(e)
    lst = before = None
    try: lst = lstat_fn(spec["path"])
    except FileNotFoundError as e: snap["status"]="MISSING"; err("lstat", e); progress(snap); return snap
    except OSError as e: snap["status"]="UNREADABLE"; err("lstat", e); progress(snap); return snap
    snap["lstat_before"] = _stat_dict(lst)
    if helper["is_link"](lst):
        snap["status"]="UNRESOLVED_LINK"; snap["link"]={"attrs":int(getattr(lst,"st_file_attributes",0) or 0),"reparse_tag":int(getattr(lst,"st_reparse_tag",0) or 0),"is_link":True,"mode":int(lst.st_mode)}; progress(snap); return snap
    if any(a.get("is_link") for a in anc_initial):
        snap["status"]="UNRESOLVED_LINK"; progress(snap); return snap
    try: before = stat_fn(spec["path"])
    except OSError as e: snap["status"]="UNREADABLE"; err("stat_before", e); progress(snap); return snap
    snap["stat_before"] = _stat_dict(before)
    if not stat.S_ISREG(before.st_mode):
        snap["status"]="UNREADABLE"; snap["errors"].append({"stage":"stat_before","type":"NotRegular","error":"not_regular_file"}); progress(snap); return snap
    progress(snap); check_deadline()
    # open + reads: one handle, two seek(0) streaming reads
    fb = fm = fa = None; n1=n2=0; h1=h2=None; prefix = bytearray()
    try:
        progress(snap); check_deadline()
        with open_fn(spec["path"], "rb") as f:
            fb = fstat_fn(f.fileno()); snap["fstat_before"] = _stat_dict(fb)
            progress(snap); check_deadline()
            f.seek(0); hh = hashlib.sha256(); n1 = 0; prefix = bytearray()
            while True:
                b = f.read(CHUNK)
                if not b: break
                if not isinstance(b, (bytes, bytearray)): raise TypeError("read_not_bytes")
                hh.update(b); n1 += len(b); check_deadline()
                if len(prefix) < 16: prefix.extend(b[:16-len(prefix)])
            h1 = hh.hexdigest(); snap["read1"] = {"sha256":h1,"size":n1,"prefix16":bytes(prefix).hex()}
            fm = fstat_fn(f.fileno()); snap["fstat_between"] = _stat_dict(fm)
            progress(snap); check_deadline()
            f.seek(0); hh = hashlib.sha256(); n2 = 0; prefix2 = bytearray()
            while True:
                b = f.read(CHUNK)
                if not b: break
                hh.update(b); n2 += len(b); check_deadline()
                if len(prefix2) < 16: prefix2.extend(b[:16-len(prefix2)])
            h2 = hh.hexdigest(); snap["read2"] = {"sha256":h2,"size":n2,"prefix16":bytes(prefix2).hex()}
            fa = fstat_fn(f.fileno()); snap["fstat_after"] = _stat_dict(fa)
    except CaptureDeadline:
        raise
    except OSError as e:
        snap["status"]="UNREADABLE"; err("open_or_read", e); progress(snap); return snap
    except Exception as e:
        snap["status"]="UNREADABLE"; err("open_or_read", e); progress(snap); return snap
    snap["sha256"] = h2; snap["size"] = n2; snap["prefix16"] = bytes(prefix).hex() if prefix else ""
    try: snap["format"] = helper["detect_format"](spec["name"], bytes(prefix))
    except Exception as e: snap["format"]="UNKNOWN"; err("detect_format", e)
    progress(snap); check_deadline()
    # final phase
    path_after = lst_after = None
    try: path_after = stat_fn(spec["path"]); snap["stat_after"] = _stat_dict(path_after)
    except OSError as e: err("stat_after", e)
    try: lst_after = lstat_fn(spec["path"]); snap["lstat_after"] = _stat_dict(lst_after)
    except OSError as e: err("lstat_after", e)
    anc_final_ok = True
    for i, p in enumerate(anc_paths):
        try:
            s = lstat_fn(p); snap["ancestors"][i]["final_stat"] = _stat_dict(s); snap["ancestors"][i]["final_is_link"] = bool(helper["is_link"](s))
            ok = anc_stats[i] is not None and helper["ident_tuple"](anc_stats[i]) == helper["ident_tuple"](s) and not helper["is_link"](s) and not anc_initial[i].get("is_link")
        except OSError as e:
            snap["ancestors"][i]["final_stat"] = None; snap["ancestors"][i]["final_error"] = str(e); ok=False; err("ancestor_final:"+p, e)
        snap["ancestors"][i]["ident_equal"] = bool(ok)
        anc_final_ok = anc_final_ok and bool(ok)
    try:
        raw_qa = query_fn(alias) if query_fn else None
        oka, cur_a, exp_m2 = mapping_current(raw_qa, root, helper) if raw_qa is not None else (False, None, helper["expected_mapping"](root))
        snap["mapping_after"] = {"raw_first":cur_a,"expected":exp_m2,"matches":bool(oka)}
    except Exception as e:
        snap["mapping_after"] = {"raw_first":None,"expected":helper["expected_mapping"](root),"matches":False}; err("query_dos_device_after", e); oka=False; cur_a=None
    st = helper["stat_tuple"]; it = helper["ident_tuple"]
    # EXACT original _capture_file predicates, plus fstat-between and read-count/hash guards.
    # ctime is compared only within the same API (fstat-vs-fstat via stat_tuple, stat-vs-stat, lstat-vs-lstat).
    pred("fstat_before_eq_fstat_after_stat_tuple_original", fb is not None and fa is not None and st(fb)==st(fa), before=_stat_dict(fb), after=_stat_dict(fa))
    pred("stat_before_ident_fstat_before_original", before is not None and fb is not None and it(before)==it(fb), stat_before=_stat_dict(before), fstat_before=_stat_dict(fb))
    pred("stat_after_ident_fstat_after_original", path_after is not None and fa is not None and it(path_after)==it(fa), stat_after=_stat_dict(path_after), fstat_after=_stat_dict(fa))
    pred("lstat_after_ident_fstat_after_original", lst_after is not None and fa is not None and it(lst_after)==it(fa), lstat_after=_stat_dict(lst_after), fstat_after=_stat_dict(fa))
    pred("lstat_after_not_link_original", lst_after is not None and not helper["is_link"](lst_after), lstat_after=_stat_dict(lst_after))
    pred("fstat_before_eq_fstat_between_stat_tuple", fb is not None and fm is not None and st(fb)==st(fm), before=_stat_dict(fb), between=_stat_dict(fm))
    pred("fstat_between_eq_fstat_after_stat_tuple", fm is not None and fa is not None and st(fm)==st(fa), between=_stat_dict(fm), after=_stat_dict(fa))
    pred("stat_before_eq_stat_after_same_api_stat_tuple", before is not None and path_after is not None and st(before)==st(path_after), before=_stat_dict(before), after=_stat_dict(path_after))
    pred("lstat_before_eq_lstat_after_same_api_stat_tuple", lst is not None and lst_after is not None and st(lst)==st(lst_after), before=_stat_dict(lst), after=_stat_dict(lst_after))
    pred("read1_count_eq_fstat_before_size", fb is not None and n1==int(fb.st_size), read=n1, size=int(fb.st_size) if fb else None)
    pred("read1_count_eq_fstat_between_size", fm is not None and n1==int(fm.st_size), read=n1, size=int(fm.st_size) if fm else None)
    pred("read2_count_eq_fstat_between_size", fm is not None and n2==int(fm.st_size), read=n2, size=int(fm.st_size) if fm else None)
    pred("read2_count_eq_fstat_after_size", fa is not None and n2==int(fa.st_size), read=n2, size=int(fa.st_size) if fa else None)
    pred("read1_sha256_eq_read2_sha256", h1 is not None and h1==h2, read1=h1, read2=h2)
    pred("read1_prefix16_eq_read2_prefix16", snap["read1"]["prefix16"]==snap["read2"]["prefix16"], read1=snap["read1"]["prefix16"], read2=snap["read2"]["prefix16"])
    pred("ancestors_ident_equal_and_not_link", anc_final_ok, ancestors=[{"path":a["path"],"ident_equal":a.get("ident_equal")} for a in snap["ancestors"]])
    pred("mapping_before_matches_expected_current", bool(okb), first=cur_b, expected=snap["mapping_before"]["expected"])
    pred("mapping_after_matches_expected_current", bool(oka), first=cur_a, expected=snap["mapping_after"]["expected"])
    pred("mapping_before_eq_after_current", cur_b is not None and cur_a is not None and helper["win_norm"](cur_b)==helper["win_norm"](cur_a), before=cur_b, after=cur_a)
    stable = all(p["value"] for p in snap["predicates"]) and not snap["errors"]
    snap["stable"] = bool(stable)
    if not stable:
        snap["status"] = "SOURCE_UNSTABLE"
    else:
        snap["status"] = "OK"
        if h2 == spec["reference_sha256"]: snap["reference_status"] = "MATCH"
        elif spec["reference_format"] == "UNKNOWN": snap["reference_status"] = "BYTES_DIFFER_REFERENCE_FORMAT_UNKNOWN"
        elif snap["format"] != "UNKNOWN" and spec["reference_format"] != "UNKNOWN" and snap["format"] != spec["reference_format"]: snap["reference_status"] = "FORMAT_DIFFERS"
        else: snap["reference_status"] = "DIFFER"
    if not stable and "reference_status" not in snap: snap["reference_status"] = "NOT_COMPARED_UNSTABLE"
    progress(snap); check_deadline()
    return snap

def run_stability(contract_path, contract_sha256, out_dir, *, monotonic=time.monotonic, query_dos_device_fn=None, providers=None, helper_sha256_expected=None):
    out = str(out_dir)
    if os.path.exists(out):
        if not os.path.isdir(out) or os.listdir(out): raise ValueError("out_not_fresh_directory")
    else:
        os.makedirs(out)
    partial_path = os.path.join(out, "partial.json"); report_path = os.path.join(out, "report.json")
    state = {"schema":SCHEMA,"status":"IN_PROGRESS","overall":"DISCOVERY_ONLY","source_stability":"INCONCLUSIVE_SOURCE_STABILITY","files":[],"errors":[]}
    def write_partial():
        tmp = json.dumps(state, indent=2, sort_keys=True)
        with open(partial_path, "w", encoding="utf-8") as f:
            f.write(tmp); f.flush(); os.fsync(f.fileno())
    def progress(snap):
        files = [x for x in state["files"] if x.get("name") != snap.get("name")]; files.append(snap); state["files"] = files; write_partial()
    write_partial()
    start = monotonic(); helper_expected = helper_sha256_expected or EXPECTED_HELPER_SHA256
    try:
        contract, contract_raw, contract_actual = load_contract(contract_path, contract_sha256)
        state["contract_sha256"] = contract_actual; write_partial()
        deadline = start + float(contract["seconds"])
        def check_deadline():
            if monotonic() > deadline: raise CaptureDeadline("source_stability_time_budget_exceeded")
        check_deadline()
        # Pin hashes for every pinned file (incl. catalogue) before parsing any pinned JSON.
        pin_actual = {}
        for pth, want in contract["pins"].items():
            got, _n = hash_file(pth)
            pin_actual[pth] = got
            if got != want: raise ValueError("pin_mismatch_before_parse:" + pth)
        check_deadline()
        helper_path = contract["helper"]
        if pin_actual[helper_path] != helper_expected: raise ValueError("helper_not_bound_to_2053_tool")
        with open(helper_path, "rb") as f: helper_bytes = f.read()
        if _sha_bytes(helper_bytes) != pin_actual[helper_path]: raise ValueError("helper_bytes_changed_during_load")
        helper = _load_helper(helper_bytes, helper_path)
        def load_pinned(pth):
            with open(pth, "rb") as f: data = f.read()
            if _sha_bytes(data) != pin_actual[pth]: raise ValueError("pinned_bytes_changed_before_parse:" + pth)
            return _loads_strict(data, pth)
        report0 = load_pinned(contract["r0_report"]); manifest0 = load_pinned(contract["r0_manifest"]); old0 = load_pinned(contract["r0_contract"])
        manifest = manifest0.get("manifest") if isinstance(manifest0, dict) and isinstance(manifest0.get("manifest"), dict) else manifest0
        if not isinstance(manifest, dict): raise ValueError("bad_r0_manifest")
        if manifest.get("report_sha256") != contract["pins"][contract["r0_report"]]: raise ValueError("manifest_report_sha_mismatch")
        if manifest.get("contract_sha256") != contract["pins"][contract["r0_contract"]]: raise ValueError("manifest_contract_sha_mismatch")
        if manifest.get("tool_sha256") != pin_actual[helper_path]: raise ValueError("manifest_tool_sha_mismatch")
        _check_aliases(manifest, "report_sha256", ["report_sha256","report_sha","reportSha256"], contract["pins"][contract["r0_report"]], "manifest")
        _check_aliases(manifest, "contract_sha256", ["contract_sha256","contract_sha","contractSha256"], contract["pins"][contract["r0_contract"]], "manifest")
        _check_aliases(manifest, "tool_sha256", ["tool_sha256","tool_sha","toolSha256"], pin_actual[helper_path], "manifest")
        _check_aliases(report0, "contract_sha256", ["contract_sha256","contract_sha"], contract["pins"][contract["r0_contract"]], "report")
        _check_aliases(report0, "tool_sha256", ["tool_sha256","tool_sha"], pin_actual[helper_path], "report")
        old_root = _find_key(old0, ["build_root","root","buildRoot","source_root"])
        old_alias = _find_key(old0, ["build_alias","alias","buildAlias"])
        if old_root is not None and old_root != contract["root"]: raise ValueError("old_contract_root_mismatch_current_root")
        if old_alias is not None and old_alias != contract["alias"]: raise ValueError("old_contract_alias_mismatch")
        ba = report0.get("build_alias") if isinstance(report0, dict) else None
        if isinstance(ba, str) and ba != contract["alias"]: raise ValueError("r0_report_alias_mismatch")
        if isinstance(ba, dict):
            br = ba.get("root") or ba.get("build_root"); bal = ba.get("alias") or ba.get("build_alias")
            if br is not None and br != contract["root"]: raise ValueError("r0_report_root_mismatch")
            if bal is not None and bal != contract["alias"]: raise ValueError("r0_report_alias_mismatch")
        expected_files = derive_expected_files(report0, contract)
        check_deadline(); write_partial()
        query_fn = query_dos_device_fn if query_dos_device_fn is not None else helper["query_dos_device"]
        snaps = []
        for spec in expected_files:
            snap = capture_file(spec, helper=helper, root=contract["root"], alias=contract["alias"], query_fn=query_fn, check_deadline=check_deadline, progress=progress, providers=providers)
            snaps.append(snap); check_deadline()
        state["files"] = snaps
        # Final immutability re-check: contract again + every pin. Fail closed, no green report.
        again_contract, _n = hash_file(contract_path)
        if again_contract != contract_actual: raise ValueError("contract_changed_during_capture")
        for pth, want in contract["pins"].items():
            got, _n = hash_file(pth)
            if got != want: raise ValueError("pinned_input_changed_during_capture:" + pth)
        state["pins_after"] = pin_actual
        all_stable = len(snaps) == 7 and all(s.get("stable") for s in snaps)
        source_stability = "STABLE_CAPTURE" if all_stable else "INCONCLUSIVE_SOURCE_STABILITY"
        report = {"schema":SCHEMA,"status":"DISCOVERY_ONLY","overall":"DISCOVERY_ONLY","aggregate":"DISCOVERY_ONLY","source_stability":source_stability,"build_ready":False,"pivot":"UNKNOWN","width":"UNKNOWN","accesses":"UNKNOWN","r0_unchanged":True,"r0_chronological_causation":"NOT_CLAIMED","snapshot_scope":"temporal_per_file_not_atomic_global","contract_sha256":contract_actual,"helper_sha256":pin_actual[helper_path],"r0_tool_sha256":pin_actual[helper_path],"format_sample_bytes":16,"r0_report_sha256":contract["pins"][contract["r0_report"]],"r0_manifest_sha256":contract["pins"][contract["r0_manifest"]],"r0_contract_sha256":contract["pins"][contract["r0_contract"]],"pins_before":pin_actual,"pins_after":pin_actual,"files":snaps,"external_references":[{"normalized":x,"status":"UNRESOLVED_EXTERNAL"} for x in contract["external_references"]],"incomplete_coverage":True,"limitations":["external_reference_not_covered","no_atomic_global_snapshot","reverted_change_between_observations_may_be_missed"]}
        state.update({"status":"DISCOVERY_ONLY","source_stability":source_stability,"files":snaps}); write_partial()
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
        return report
    except CaptureDeadline as e:
        state["status"]="DISCOVERY_ONLY"; state["source_stability"]="INCONCLUSIVE_SOURCE_STABILITY"; state["errors"].append({"type":"TimeoutError","error":str(e)}); write_partial()
        report = {"schema":SCHEMA,"status":"DISCOVERY_ONLY","overall":"DISCOVERY_ONLY","aggregate":"DISCOVERY_ONLY","source_stability":"INCONCLUSIVE_SOURCE_STABILITY","build_ready":False,"pivot":"UNKNOWN","width":"UNKNOWN","accesses":"UNKNOWN","r0_unchanged":"NOT_VERIFIED","files":state.get("files",[]),"external_references":[],"incomplete_coverage":True,"errors":state["errors"]}
        # Keep any contract-bound external list if already known is not available here; partial is authoritative on timeout.
        try:
            c2, _r, _a = load_contract(contract_path, contract_sha256); report["external_references"]=[{"normalized":x,"status":"UNRESOLVED_EXTERNAL"} for x in c2["external_references"]]; report["contract_sha256"]=_a
        except Exception: pass
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
        return report
    except Exception as e:
        state["status"]="INCONCLUSIVE_SOURCE_STABILITY"; state["source_stability"]="INCONCLUSIVE_SOURCE_STABILITY"; state["errors"].append({"type":type(e).__name__,"error":str(e)}); write_partial(); raise

def main(argv=None):
    ap = argparse.ArgumentParser(prog="road_source_stability_ev112")
    ap.add_argument("--contract", required=True); ap.add_argument("--contract-sha256", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        r = run_stability(a.contract, a.contract_sha256, a.out)
    except Exception as e:
        print(json.dumps({"status":"INCONCLUSIVE_SOURCE_STABILITY","error":str(e)}), file=sys.stderr); return 2
    print(json.dumps({"status":r.get("status"),"source_stability":r.get("source_stability"),"overall":r.get("overall")}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
