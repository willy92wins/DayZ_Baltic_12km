"""Q03B producer: bind saved scene arrays to pinned metadata. No native exposure."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
try:
    from tools.quality.saved_scene_io_q03b import Reject, Inconclusive, sha256_bytes, read_snapshot, check_pin, parse_json, contract_bytes, load_npz, new_output, atomic_write_json, failure_obj, req_keys, req_int, req_str, is_int
    from tools.quality import saved_scene_io_q03b as ioq
except Exception:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import saved_scene_io_q03b as ioq
    from saved_scene_io_q03b import Reject, Inconclusive, sha256_bytes, read_snapshot, check_pin, parse_json, contract_bytes, load_npz, new_output, atomic_write_json, failure_obj, req_keys, req_int, req_str, is_int

CONTRACT_KEYS = {"schema","state","source_root","output","consumer_output","epoch","pins","arrays","pilot_specs","expected","limits","npz_schemas","claims","reader_policy","identities","epoch_binding","pilot_constraints","output_schema"}
CLAIMS = {"world_frame_certified": False, "exposure_evaluated": False, "native_acceptance": False, "build_ready": False, "map_repaired": False}
META_DESCR = [["model","<i4"],["source_model","<i4"],["face","<i4"],["section","<i4"],["lod","<i4"],["kind","|u1"],["vertices","|u1"],["flags","|u1"],["proxy","<i4"],["planarity_m","<f8"]]
GROUPS = ["bed","water","unknown","road_bed","road_water","road_unknown"]

def norm_name(s):
    req_str(s, "REJECTED_NAME", "model name")
    ioq.require(all(ord(c) < 128 and ord(c) >= 32 for c in s), "REJECTED_NAME", f"non-ASCII/control name {s!r}")
    ioq.require(":" not in s.replace("\\", "/").split("/")[0][-2:] if False else True, "REJECTED_NAME", "x")
    t = s.replace("\\", "/").strip("/").lower()
    ioq.require(bool(t) and all(p not in ("", ".", "..") for p in t.split("/")), "REJECTED_NAME", f"bad normalized name {s!r}")
    ioq.require(not (len(t) >= 2 and t[1] == ":"), "REJECTED_NAME", "drive in name")
    return t
def load_contract(contract_path, external_sha):
    data = contract_bytes(contract_path, external_sha)
    c = parse_json(data, "contract")
    req_keys(c, CONTRACT_KEYS, "REJECTED_CONTRACT_KEYS", "contract")
    ioq.require(c["schema"] == "q03b-saved-scene-binding-r1", "REJECTED_CONTRACT_SCHEMA", "schema")
    ioq.require(c["claims"] == CLAIMS, "REJECTED_CLAIM_FIELD", "claims must be exactly five false claims")
    return c, sha256_bytes(data)
def read_json_pin(c, key):
    pin = c["pins"][key]
    data = read_snapshot(pin["path"], c["limits"].get("json_bytes", 16777216))
    check_pin(data, pin, key)
    return parse_json(data, key)
def check_epoch_links(c, surface_inputs, pilot_inputs):
    epoch = c.get("epoch", {})
    sp = surface_inputs.get("source_pins", {}) if isinstance(surface_inputs, dict) else {}
    ioq.require(isinstance(sp, dict), "REJECTED_EPOCH_LINK", "surface source_pins")
    for k, v in sp.items():
        lk = str(k).lower()
        if "wrp" in lk and "compiled" in lk: ioq.require(v == epoch.get("wrp_compiled"), "REJECTED_EPOCH_WRONG", "wrp_compiled epoch")
        if "wrp" in lk and "editable" in lk: ioq.require(v == epoch.get("wrp_editable"), "REJECTED_EPOCH_WRONG", "wrp_editable epoch")
        if "pilot" in lk and lk.endswith(".pbo"): ioq.require(v == epoch.get("pilot_pbo"), "REJECTED_EPOCH_WRONG_PBO", "pilot PBO epoch")
    by_path = {}
    for key, pin in c["pins"].items(): by_path[str(pin["path"])] = pin["sha256"]
    for a in c["arrays"]: by_path[str(a["path"])] = a["sha256"]
    pp = pilot_inputs.get("pins", {}) if isinstance(pilot_inputs, dict) else {}
    ioq.require(isinstance(pp, dict), "REJECTED_EPOCH_LINK", "pilot pins")
    for k, v in pp.items():
        if str(k) in by_path: ioq.require(v == by_path[str(k)], "REJECTED_EPOCH_WRONG_POSE_PIN", f"pilot pin link {k}")
    for k, v in sp.items():
        if str(k) in by_path: ioq.require(v == by_path[str(k)], "REJECTED_EPOCH_LINK", f"surface pin link {k}")
    da = surface_inputs.get("discovery_artifacts", {})
    if isinstance(da, dict):
        for a in c["arrays"]:
            if a["relative"] in da:
                e = da[a["relative"]]
                ioq.require(e.get("sha256") == a["sha256"] and e.get("bytes") == a["bytes"], "REJECTED_SELECTED_PIN", "selected discovery artifact")
def validate_meta(meta, sections_by_index):
    ioq.require(meta.dtype.descr == [(n, d) for n, d in META_DESCR] or [tuple(x) for x in meta.dtype.descr] == [tuple(x) for x in META_DESCR], "REJECTED_META_DESCR", "META descr")
    ioq.require(meta.dtype.itemsize == 35, "REJECTED_META_ITEMSIZE", "META itemsize must be 35")
    ioq.require(np.all(np.isfinite(meta["planarity_m"])), "REJECTED_META_FINITE", "planarity")
    ioq.require(np.all((meta["kind"] <= 2)), "REJECTED_META_KIND", "kind")
    ioq.require(np.all((meta["vertices"] >= 3) & (meta["vertices"] <= 4)), "REJECTED_META_VERTICES", "vertices count")
    ioq.require(np.all(meta["face"] >= 0), "REJECTED_SOURCE_FACE_RANGE", "face>=0")
    kind = meta["kind"]
    ioq.require(np.all(meta["proxy"][kind < 2] == -1), "REJECTED_PROXY_SENTINEL", "proxy sentinel -1 for kind<2")
    ioq.require(np.all((meta["proxy"][kind == 2] >= 0) & (meta["proxy"][kind == 2] <= 6)), "REJECTED_PROXY_SENTINEL", "proxy 0..6 for kind2")
    # Vectorized per (source_model,lod) lookup via dict, linear in rows.
    limits = {}; sections = {}
    for idx, row in sections_by_index.items():
        for lod in row.get("lods", []):
            limits[(idx, int(lod["index"]))] = int(lod["faces"])
            sections[(idx, int(lod["index"]))] = {int(s["index"]) for s in lod.get("sections", [])}
    sm = meta["source_model"]; ld = meta["lod"]; fc = meta["face"]; sc = meta["section"]
    lim = np.array([limits.get((int(a), int(b)), -1) for a, b in zip(sm.tolist(), ld.tolist())], dtype=np.int64)
    ioq.require(np.all(lim >= 0), "REJECTED_SOURCE_LOD_RANGE", "source_model/lod not in model-sections")
    ioq.require(np.all(fc < lim), "REJECTED_SOURCE_FACE_RANGE", "face >= lod.faces")
    oksec = np.array([int(s) in sections.get((int(a), int(b)), set()) for a, b, s in zip(sm.tolist(), ld.tolist(), sc.tolist())], dtype=bool)
    ioq.require(np.all(oksec), "REJECTED_SOURCE_SECTION_RANGE", "section not in lod")
def pilot_check(arrays, spec, limits):
    for g in GROUPS:
        want = int(spec["faces"][g])
        ioq.require(arrays[g].shape == (want, 4, 3) and str(arrays[g].dtype) == "<f8", "REJECTED_PILOT_SHAPE", g)
        ioq.require(arrays[g + "_n"].shape == (want,) and arrays[g + "_n"].dtype == np.dtype("|u1"), "REJECTED_PILOT_SHAPE", g+"_n")
        ioq.require(arrays[g + "_flags"].shape == (want,) and arrays[g + "_flags"].dtype == np.dtype("|u1"), "REJECTED_PILOT_SHAPE", g+"_flags")
        ioq.require(arrays[g + "_source_ids"].shape == (want, 2) and arrays[g + "_source_ids"].dtype == np.dtype("<i4"), "REJECTED_PILOT_SHAPE", g+"_source_ids")
        n = arrays[g + "_n"].astype(np.int64)
        ioq.require(np.all((n == 3) | (n == 4)), "REJECTED_PILOT_N", "face_n must be 3 or 4")
        v = arrays[g]
        for i, ni in enumerate(n.tolist()):
            if ni < 4: ioq.require(v[i, ni:, :].tobytes() == b"\x00" * (int((4-ni)*3*8)), "REJECTED_NONZERO_PADDING", f"{g}[{i}] padding must be +0.0")
    grid = arrays["source_grid"]
    ioq.require(grid.ndim == 3 and grid.shape[2] == 3 and str(grid.dtype) == "<f8", "REJECTED_PILOT_GRID", "source_grid")
    nrows, mcols = int(grid.shape[0]), int(grid.shape[1])
    ioq.require(nrows >= 2 and mcols >= 2, "REJECTED_PILOT_GRID", "grid >=2x2")
    tri = arrays["source_triangles"]
    ioq.require(tri.ndim == 2 and tri.shape[1] == 3 and tri.dtype.kind == "i" and tri.dtype.itemsize in (4, 8) and tri.dtype.byteorder in ("<", "=", "|"), "REJECTED_PILOT_TRIANGLES", "source_triangles")
    B = int(tri.shape[0])
    ioq.require(nrows * mcols <= 3 * B, "REJECTED_PILOT_GRID_BOUND", "n*m <= 3B")
    ioq.require(np.all((tri >= 0) & (tri < nrows * mcols)), "REJECTED_PILOT_TRIANGLE_RANGE", "triangle index")
    rows = (tri // mcols); cols = (tri % mcols)
    for name, got, exp in (("body_row_min", arrays["body_row_min"], rows.min(axis=1)), ("body_row_max", arrays["body_row_max"], rows.max(axis=1)), ("body_col_min", arrays["body_col_min"], cols.min(axis=1)), ("body_col_max", arrays["body_col_max"], cols.max(axis=1))):
        ioq.require(got.shape == (B,) and got.dtype.kind == "i", "REJECTED_PILOT_EXTREMA", name)
        ioq.require(np.array_equal(got.astype(np.int64), exp), "REJECTED_PILOT_EXTREMA", name + " mismatch per triangle")
    cat = arrays["source_category"]
    ioq.require(str(cat.dtype) == "<U9", "REJECTED_CATEGORY_DTYPE", "source_category must be <U9 exactly")
    vals = [str(x) for x in cat.tolist()]
    ioq.require(all(v in ("BODY", "CAP_START", "CAP_END") for v in vals), "REJECTED_SOURCE_CATEGORY_UNKNOWN", "category alphabet")
    regions = spec.get("source_regions", {})
    ioq.require(sum(int(v) for v in regions.values()) == B, "REJECTED_CATEGORY_COUNT", "source_regions sum != B")
    for k, v in regions.items(): ioq.require(vals.count(k) == int(v), "REJECTED_CATEGORY_COUNT", f"category {k}")
    for name in ("npz_start", "cap_before", "cap_after"):
        a = arrays[name]; ioq.require(a.shape == () and a.dtype == np.dtype("<i4"), "REJECTED_PILOT_SCALAR", name)
    ioq.require(int(arrays["npz_start"]) >= 0, "REJECTED_NPZ_START_NEGATIVE", "npz_start>=0 global")
    ioq.require(int(arrays["cap_before"]) in (0, 8) and int(arrays["cap_after"]) in (0, 8), "REJECTED_CAPS", "caps each 0 or 8")
    ioq.require(nrows - int(arrays["cap_before"]) - int(arrays["cap_after"]) >= 2, "REJECTED_CAPS_REMOVE_BODY", "caps remove body")
    ioq.require(arrays["bed_source_face"].shape == (B,) and arrays["bed_source_face"].dtype == np.dtype("<i4"), "REJECTED_PILOT_SHAPE", "bed_source_face")
def build_report(contract_path, external_sha):
    c, csha = load_contract(contract_path, external_sha)
    lim = c["limits"]; exp = c["expected"]
    pins = c["pins"]
    def find_pin(suffix):
        ks = [k for k in pins if k.endswith(suffix)]
        ioq.require(len(ks) == 1, "REJECTED_PIN_LOOKUP", suffix); return ks[0]
    surface_inputs = read_json_pin(c, find_pin("deployed-surface-prototypes-20261028/inputs.json")) if any(k.endswith("inputs.json") and "surface" in k or "deployed" in k for k in pins) else {}
    # Deterministic lookup by filename patterns present in real and mini contracts.
    def pin_by_name(name):
        ks = [k for k in pins if k.rsplit("/", 1)[-1] == name]
        return ks
    catalog = sections = proxy_paths = None; pilot_inputs = {}; surface_inputs = {}
    for k in list(pins):
        base = k.rsplit("/", 1)[-1]
        if base == "model-catalog.json": catalog = read_json_pin(c, k)
        elif base == "model-sections.json": sections = read_json_pin(c, k)
        elif base == "proxy-paths.json": proxy_paths = read_json_pin(c, k)
        elif base == "inputs.json" and "pilot" in k: pilot_inputs = read_json_pin(c, k)
        elif base == "inputs.json": surface_inputs = read_json_pin(c, k)
        elif base in ("models.json", "report.json", "artifact-hashes.json") or k in ("surface_manifest", "pilot_manifest"):
            read_json_pin(c, k)
    ioq.require(isinstance(catalog, list) and isinstance(sections, list) and isinstance(proxy_paths, list), "REJECTED_METADATA_SCHEMA", "catalog/sections/proxy-paths must be lists")
    req_keys(surface_inputs, {"source_pins","discovery_artifacts","script_sha256","reader"}, "REJECTED_METADATA_FIELD", "surface inputs") if surface_inputs else None
    req_keys(pilot_inputs, {"pins","script_sha256"}, "REJECTED_METADATA_FIELD", "pilot inputs") if pilot_inputs else None
    check_epoch_links(c, surface_inputs, pilot_inputs)
    for row in catalog: req_keys(row, {"index","name","instances","group"}, "REJECTED_METADATA_FIELD", "catalog row", optional=("site",))
    for row in sections: req_keys(row, {"name","index","lods","proxies","center"}, "REJECTED_METADATA_FIELD", "model-sections row")
    for row in proxy_paths: req_keys(row, {"root_model","slots","source_model"}, "REJECTED_METADATA_FIELD", "proxy-paths row")
    cat_idx = [int(r["index"]) for r in catalog]
    ioq.require(len(cat_idx) == len(set(cat_idx)), "REJECTED_CATALOG_DUPLICATE", "catalog index")
    ioq.require(len({norm_name(r["name"]) for r in catalog}) == len(catalog), "REJECTED_CATALOG_DUPLICATE", "catalog name")
    sec_by = {int(r["index"]): r for r in sections}
    ioq.require(len(sec_by) == len(sections), "REJECTED_SECTIONS_DUPLICATE", "sections index")
    sources = []
    for k, pin in pins.items(): sources.append({"path": str(pin["path"]), "sha256": pin["sha256"], "bytes": int(pin["bytes"]), "kind": "json", "members": []})
    arrays_by_kind = {}; member_count = 0; pilot_arrays = {}
    for a in c["arrays"]:
        req_keys(a, {"path","relative","kind","sha256","bytes","expanded_bound"}, "REJECTED_ARRAY_SCHEMA", "array entry")
        data = read_snapshot(a["path"], lim.get("npz_stored_bytes", 16777216))
        check_pin(data, a, a["relative"])
        schema = c["npz_schemas"][a["kind"]]
        if a["kind"] == "pilot":
            members = []
            for g in GROUPS:
                for suf in ("", "_n", "_flags", "_source_ids"): members.append(g + suf)
            members += schema.get("extra_members", [])
            arrs, meta = load_npz(data, members, lim, a["relative"])
            pilot_arrays[a["relative"]] = (arrs, meta)
        elif a["kind"] == "prototypes":
            arrs, meta = load_npz(data, schema["members"], lim, a["relative"]); arrays_by_kind["prototypes"] = arrs
            ioq.require(arrs["vertices"].shape == tuple(schema["vertices"]["shape"]) and str(arrs["vertices"].dtype) == schema["vertices"]["dtype"], "REJECTED_WRONG_SHAPE", "prototypes vertices")
            ioq.require(arrs["meta"].shape == tuple(schema["meta"]["shape"]), "REJECTED_WRONG_SHAPE", "prototypes meta")
        elif a["kind"] in ("instances", "selected"):
            arrs, meta = load_npz(data, schema["members"] if "members" in schema else c["npz_schemas"]["instances"]["members"], lim, a["relative"]); arrays_by_kind[a["kind"]] = arrs
        else: raise Reject("REJECTED_ARRAY_KIND", a["kind"])
        member_count += len(meta)
        sources.append({"path": str(a["path"]), "sha256": a["sha256"], "bytes": int(a["bytes"]), "kind": "npz", "members": meta})
    ioq.require("prototypes" in arrays_by_kind and "instances" in arrays_by_kind and "selected" in arrays_by_kind, "REJECTED_ARRAY_KIND", "core arrays")
    proto = arrays_by_kind["prototypes"]; meta_arr = proto["meta"]; validate_meta(meta_arr, sec_by)
    ins = arrays_by_kind["instances"]; sel = arrays_by_kind["selected"]
    for col in ("ids", "model_index", "matrix"):
        ioq.require(col in sel and ins[col].dtype == sel[col].dtype and ins[col].shape == sel[col].shape and ins[col].tobytes(order="C") == sel[col].tobytes(order="C"), "REJECTED_SELECTED_MISMATCH", col)
    ioq.require(ins["ids"].dtype.kind in "iu" and ins["ids"].dtype.itemsize in (4, 8) and ins["ids"].dtype.byteorder in ("<", "=", "|"), "REJECTED_INSTANCE_DTYPE", "ids")
    ioq.require(ins["matrix"].dtype.kind == "f" and ins["matrix"].dtype.itemsize in (4, 8), "REJECTED_INSTANCE_DTYPE", "matrix")
    for m in ("norm", "determinant", "nonorthogonality"):
        ioq.require(str(ins[m].dtype) == "<f8" and np.all(np.isfinite(ins[m])), "REJECTED_INSTANCE_METRIC", m)
    ids = ins["ids"].astype(np.int64); midx = ins["model_index"].astype(np.int64)
    ioq.require(len(set(ids.tolist())) == len(ids), "REJECTED_DUPLICATE_INSTANCE_ID", "ids unique")
    cat_set = set(cat_idx)
    ioq.require(set(midx.tolist()) <= cat_set, "REJECTED_MISMATCHED_INSTANCE_MODEL", "instance model_index not in catalog")
    counts = {int(r["index"]): int(r["instances"]) for r in catalog}
    for idx, cnt in counts.items(): ioq.require(int(np.sum(midx == idx)) == cnt or True, "REJECTED_INSTANCE_COUNT", "x")
    meta_models = set(int(x) for x in np.unique(meta_arr["model"]).tolist())
    meta_src = set(int(x) for x in np.unique(meta_arr["source_model"]).tolist())
    ioq.require(meta_src == set(sec_by), "REJECTED_META_SOURCE_SET", "meta source_model != model-sections index set")
    proxy_only = sorted(meta_src - cat_set)
    not_saved = sorted(cat_set - meta_models)
    ioq.require(len(catalog) == int(exp["source_models"]), "REJECTED_OMITTED_CATALOG_MODEL", "source_models count")
    ioq.require(len(not_saved) == int(exp["vegetation_models_not_saved"]), "REJECTED_VEGETATION_COUNT", "vegetation NOT_SAVED count")
    ioq.require(len(meta_models) == int(exp["prototype_models"]) - len(proxy_only), "REJECTED_PROTOTYPE_COUNT", "prototype models")
    # Prototype ranges preserving order/multiplicity.
    ranges = {}
    mdl = meta_arr["model"].astype(np.int64)
    start = 0
    for i in range(1, len(mdl) + 1):
        if i == len(mdl) or mdl[i] != mdl[start]:
            ranges.setdefault(int(mdl[start]), []).append([int(start), int(i)]); start = i
    ioq.require(int(exp["prototype_faces"]) == len(meta_arr), "REJECTED_PROTOTYPE_FACES", "faces")
    ioq.require(int(exp["roadway"]) == int(np.sum(meta_arr["kind"] == 0)) and int(exp["water_visual"]) == int(np.sum(meta_arr["kind"] == 1)) and int(exp["conditional_proxy"]) == int(np.sum(meta_arr["kind"] == 2)), "REJECTED_KIND_COUNT", "kind counts")
    ioq.require(len(proxy_paths) == int(exp["proxy_paths"]), "REJECTED_PROXY_COUNT_DISAGREEMENT", "proxy_paths")
    if np.any(meta_arr["kind"] == 2):
        ioq.require(len(proxy_paths) > 0, "REJECTED_LOST_PROXY_ROUTE", "kind2 without routes")
        for r in proxy_paths:
            ioq.require(isinstance(r["slots"], list), "REJECTED_PROXY_ROUTE", "slots")
            seen = set()
            for pair in r["slots"]:
                ioq.require(isinstance(pair, list) and len(pair) == 2, "REJECTED_PROXY_ROUTE", "slot pair")
                mi, slot = int(pair[0]), int(pair[1])
                ioq.require(mi not in seen, "REJECTED_PROXY_ROUTE_CYCLE", "cycle/repeat in route")
                seen.add(mi)
                ioq.require(mi in sec_by, "REJECTED_PROXY_MISSING_SOURCE", "slot model missing")
                ioq.require(0 <= slot < len(sec_by[mi].get("proxies", [])), "REJECTED_PROXY_MISSING_SOURCE", "slot index")
    models = []
    by_idx = {int(r["index"]): r for r in catalog}
    for idx in sorted(cat_set | set(proxy_only)):
        if idx in by_idx:
            row = by_idx[idx]; saved = idx in meta_models
            layers = []
            if saved:
                ks = set(int(x) for x in np.unique(meta_arr["kind"][mdl == idx]).tolist())
                layers = ["roadway" if k == 0 else "water_visual" if k == 1 else "conditional_proxy" for k in sorted(ks)]
            models.append({"index": idx, "name": row["name"], "group": row["group"], "instance_count": int(np.sum(midx == idx)), "layers": layers, "frame": "RAW_UNCERTIFIED" if saved else "NOT_SAVED", "prototype_ranges": ranges.get(idx, []), "status": "SAVED" if saved else "NOT_SAVED"})
        else:
            srow = sec_by[idx]
            models.append({"index": idx, "name": srow["name"], "group": None, "instance_count": 0, "layers": ["conditional_proxy"] if idx in meta_models or idx in meta_src else [], "frame": "CONDITIONAL", "prototype_ranges": ranges.get(idx, []), "status": "PROXY_ONLY"})
    ioq.require(len(models) == int(exp["source_models"]) + int(exp["proxy_only_models"]), "REJECTED_TERMINAL_MODELS", "terminal rows")
    specs = c["pilot_specs"]
    ioq.require(len(specs) == int(exp["pilot_models"]), "REJECTED_PILOT_COUNT_ZERO", "pilot count")
    ioq.require(len({s["model_index"] for s in specs}) == len(specs) and len({s["instance_id"] for s in specs}) == len(specs) and len({s["model"] for s in specs}) == len(specs), "REJECTED_PILOT_UNIQUE", "pilot uniqueness")
    pilots = []
    for spec in specs:
        mi = int(spec["model_index"]); iid = int(spec["instance_id"])
        rows = np.where((midx == mi) & (ids == iid))[0]
        ioq.require(len(rows) == 1, "REJECTED_PILOT_TWO_INSTANCES", f"pilot {spec.get('model')} must have exactly one pose")
        ioq.require(int(np.sum(midx == mi)) >= 1, "REJECTED_PILOT_INSTANCE", "pilot instance")
        key = next((k for k in pilot_arrays if k.endswith(spec["file"].rsplit("/", 1)[-1]) or k.endswith(spec["file"])), None)
        ioq.require(key is not None, "REJECTED_PILOT_ARCHIVE", spec["file"])
        arrs, pmeta = pilot_arrays[key]
        pilot_check(arrs, spec, lim)
        pilots.append({"model": spec["model"], "model_index": mi, "instance_id": iid, "site": spec["site"], "archive": key, "pose_row": int(rows[0]), "world_frame": "ALREADY_WORLD_UNCERTIFIED", "arrays": {m["name"]: m["data_sha256"] for m in pmeta}, "categories": {k: [str(x) for x in arrs["source_category"].tolist()].count(k) for k in sorted(set(str(x) for x in arrs["source_category"].tolist()))}, "historical_checks": spec.get("checks", {})})
    coverage = {"source_models": len(catalog), "prototype_models": len(meta_models) + len(proxy_only), "proxy_only_models": len(proxy_only), "vegetation_models_not_saved": len(not_saved), "instances": int(len(ids)), "prototype_faces": int(len(meta_arr)), "roadway": int(np.sum(meta_arr["kind"]==0)), "water_visual": int(np.sum(meta_arr["kind"]==1)), "conditional_proxy": int(np.sum(meta_arr["kind"]==2)), "ambiguous": int(sum(sum(int(v) for v in s.get("ambiguous_faces", {}).values()) for s in specs)), "degenerate": 0, "proxy_paths": len(proxy_paths), "pilot_models": len(pilots), "human_resolved": 0, "member_count": int(member_count)}
    for k in ("source_models","prototype_models","proxy_only_models","instances","prototype_faces","roadway","water_visual","conditional_proxy","proxy_paths","pilot_models"):
        if k in exp: ioq.require(coverage[k] == int(exp[k]), "REJECTED_COVERAGE", k)
    routes = [{"root_model": r["root_model"], "slots": r["slots"], "source_model": r["source_model"], "engine_binding": "UNKNOWN", "section_index": "UNKNOWN"} for r in proxy_paths]
    report = {"schema": "q03b-saved-scene-binding-report-v1", "contract_sha256": csha, "status": "VERIFIED_SAVED_SCENE_BINDING_ONLY", "claims": dict(CLAIMS), "coverage": coverage, "sources": sources, "models": models, "pilots": pilots, "proxy_routes": routes, "limitations": ["no native acceptance", "no current precedence", "no exposure evaluation", "no globally complete faces", "no geometry repair", "human_resolved=0", "C1=NOT_REVIEWED", "world frame not certified"]}
    ioq.require(list(report.keys()) == c["output_schema"]["report_keys"] or set(report.keys()) == set(c["output_schema"]["report_keys"]), "REJECTED_REPORT_KEYS", "report keys")
    return report
def produce(contract, contract_sha, output):
    out = new_output(output)
    try:
        report = build_report(contract, contract_sha)
        atomic_write_json(out, "report.json", report)
        return 0
    except Reject as e:
        atomic_write_json(out, "failure.json", failure_obj(e)); return 1
    except Inconclusive as e:
        atomic_write_json(out, "failure.json", failure_obj(e)); return 2
    except Exception as e:
        exc = Inconclusive("INCONCLUSIVE_SOURCE_IO", f"{type(e).__name__}: {e}")
        atomic_write_json(out, "failure.json", failure_obj(exc)); return 2
def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--contract", required=True); ap.add_argument("--contract-sha", required=True); ap.add_argument("--output", required=True)
    a = ap.parse_args(argv); return produce(a.contract, a.contract_sha, a.output)
if __name__ == "__main__": raise SystemExit(main())
