"""Q03B producer: bind saved scene arrays to pinned metadata. No native exposure."""
from __future__ import annotations
import argparse, sys
from collections import Counter
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
SURF = "deployed-surface-prototypes-20261028"; PILOTD = "pilot-visible-surface-extraction-20261028"; GEOD = "geometry-payload-discovery-resolved-20261028"
PILOT_PBO_KEY = r"P:\Mods\@DayZ_Baltic_EV112_Kit7Nav8Load1\Addons\baltic_stream_pilot.pbo"
PILOT_MANIFEST_LITERAL = r"evidence\deployed-surface-prototypes-20261028\artifact-hashes.json"

def norm_name(s):
    req_str(s, "REJECTED_NAME", "model name")
    ioq.require(all(32 <= ord(c) < 128 for c in s), "REJECTED_NAME", f"non-ASCII/control name {s!r}")
    t = s.replace("\\", "/").strip("/").lower()
    ioq.require(bool(t) and all(p not in ("", ".", "..") for p in t.split("/")), "REJECTED_NAME", f"bad normalized name {s!r}")
    ioq.require(not (len(t) >= 2 and t[1] == ":"), "REJECTED_NAME", "drive in name")
    ioq.require(not any(p.endswith(":") for p in t.split("/")), "REJECTED_NAME", "drive component in name")
    return t
def _sep_for(base): return "\\" if ("\\" in str(base) or ":" in str(base)) else "/"
def _join(base, rel):
    sep = _sep_for(base); return str(base).rstrip("\\/") + sep + rel.replace("/", sep)
def _worktree_root(c):
    ioq.require("surface_manifest" in c["pins"], "REJECTED_EPOCH_LINK", "surface_manifest pin required to derive worktree root")
    p = str(c["pins"]["surface_manifest"]["path"]); sep = _sep_for(p)
    parts = p.replace("\\", "/").rstrip("/").split("/")
    ioq.require(parts[-3:] == ["evidence", "deployed-surface-prototypes-20261028", "artifact-hashes.json"], "REJECTED_EPOCH_LINK", "surface_manifest path suffix")
    return sep.join(parts[:-3])
def _subpin(pin): return {"path": pin["path"], "sha256": pin["sha256"], "bytes": pin["bytes"]}
def load_contract(contract_path, external_sha):
    data = contract_bytes(contract_path, external_sha); c = parse_json(data, "contract")
    req_keys(c, CONTRACT_KEYS, "REJECTED_CONTRACT_KEYS", "contract")
    ioq.require(c["schema"] == "q03b-saved-scene-binding-r1", "REJECTED_CONTRACT_SCHEMA", "schema")
    ioq.require(c["claims"] == CLAIMS, "REJECTED_CLAIM_FIELD", "claims must be exactly five false claims")
    req_keys(c["epoch"], {"wrp_compiled","wrp_editable","pilot_pbo","kind"}, "REJECTED_CONTRACT_KEYS", "epoch")
    req_keys(c["expected"], {"source_models","vegetation_models_not_saved","prototype_models","proxy_only_models","instances","prototype_faces","roadway","water_visual","conditional_proxy","ambiguous","degenerate","proxy_paths","pilot_models","human_resolved","C1"}, "REJECTED_CONTRACT_KEYS", "expected")
    ioq.require(c["expected"]["human_resolved"] == 0 and c["expected"]["C1"] == "NOT_REVIEWED", "REJECTED_CLAIM_FIELD", "human cases remain open")
    for k in ("json_bytes","json_total_bytes","npz_stored_bytes","archive_expanded_bytes","total_expanded_bytes","npy_header_bytes","zip_members","output_bytes","max_dimension","max_dimensions","read_chunk_bytes"):
        ioq.require(k in c["limits"], "REJECTED_CONTRACT_KEYS", f"limits.{k}")
    ioq.require(int(c["limits"]["npy_header_bytes"]) == 16384, "REJECTED_CONTRACT_KEYS", "npy_header_bytes cap is 16384")
    return c, sha256_bytes(data)

def check_epoch_links(c, surface_inputs, pilot_inputs):
    epoch = c["epoch"]; root = c["source_root"]; wt = _worktree_root(c)
    sp = surface_inputs.get("source_pins")
    ioq.require(isinstance(sp, dict), "REJECTED_EPOCH_LINK", "surface source_pins must be object")
    compiled = _join(root, "package-kit7-fc-world-20261026/compiled/narva_trial/baltic_trial.wrp")
    editable = _join(root, "stage-kit7-fc-20261026/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp")
    for key, want, code in ((compiled, epoch["wrp_compiled"], "REJECTED_EPOCH_WRONG"), (editable, epoch["wrp_editable"], "REJECTED_EPOCH_WRONG"), (PILOT_PBO_KEY, epoch["pilot_pbo"], "REJECTED_EPOCH_WRONG_PBO")):
        ioq.require(key in sp, "REJECTED_EPOCH_LINK", f"missing exact epoch pin {key}")
        ioq.require(sp[key] == want, code, f"epoch mismatch {key}")
    discovery_key = _join(wt, "evidence/deployed-geometry-discovery-20261028/artifact-hashes.json")
    ioq.require(discovery_key in sp, "REJECTED_EPOCH_LINK", "missing discovery manifest source_pin")
    # artifact_manifest_sha256 is the discovery manifest (5e1d...), NOT the
    # surface artifact manifest (f4be...); compare to that exact source_pin.
    ioq.require(surface_inputs.get("artifact_manifest_sha256") == sp[discovery_key], "REJECTED_EPOCH_LINK", "artifact_manifest_sha256 must equal discovery manifest source_pin")
    sel_rel = GEOD + "/selected-instances.npz"; sel_abs = _join(root, sel_rel)
    sel_arr = next((a for a in c["arrays"] if a.get("relative") == sel_rel), None)
    ioq.require(sel_arr is not None, "REJECTED_EPOCH_LINK", "selected array entry")
    ioq.require(sp.get(sel_abs) == sel_arr["sha256"], "REJECTED_SELECTED_PIN", "surface source_pins[selected path]")
    da = surface_inputs.get("discovery_artifacts")
    ioq.require(isinstance(da, dict) and sel_rel in da, "REJECTED_SELECTED_PIN", "discovery_artifacts[selected]")
    e = da[sel_rel]; req_keys(e, {"sha256","bytes"}, "REJECTED_SELECTED_PIN", "discovery selected entry")
    ioq.require(e["sha256"] == sel_arr["sha256"] and int(e["bytes"]) == int(sel_arr["bytes"]), "REJECTED_SELECTED_PIN", "selected discovery artifact sha/bytes")
    pp = pilot_inputs.get("pins")
    ioq.require(isinstance(pp, dict), "REJECTED_EPOCH_LINK", "pilot pins must be object (dict), not list")
    surf_inputs_abs = _join(root, SURF + "/inputs.json"); inst_abs = _join(root, SURF + "/instances.npz")
    inst_arr = next((a for a in c["arrays"] if a.get("relative") == SURF + "/instances.npz"), None)
    ioq.require(inst_arr is not None, "REJECTED_EPOCH_LINK", "instances array entry")
    reqs = [(PILOT_MANIFEST_LITERAL, c["pins"]["surface_manifest"]["sha256"], "REJECTED_EPOCH_LINK"), (surf_inputs_abs, c["pins"][SURF + "/inputs.json"]["sha256"], "REJECTED_EPOCH_WRONG_POSE_PIN"), (inst_abs, inst_arr["sha256"], "REJECTED_EPOCH_WRONG_POSE_PIN")]
    for key, want, code in reqs:
        ioq.require(key in pp, "REJECTED_EPOCH_LINK", f"missing required pilot pin {key}")
        ioq.require(pp[key] == want, code, f"pilot pin link {key}")

def validate_meta(meta, verts, sections_by_index, name_to_index):
    ioq.require(ioq.descr_json(meta.dtype) == META_DESCR, "REJECTED_META_DESCR", "META descr")
    ioq.require(meta.dtype.itemsize == 35, "REJECTED_META_ITEMSIZE", "META itemsize must be 35")
    ioq.require(np.all(np.isfinite(meta["planarity_m"])), "REJECTED_META_FINITE", "planarity")
    ioq.require(np.all(np.isfinite(verts)), "REJECTED_META_FINITE", "prototype vertices finite")
    ioq.require(np.all(meta["kind"] <= 2), "REJECTED_META_KIND", "kind")
    ioq.require(np.all((meta["vertices"] >= 3) & (meta["vertices"] <= 4)), "REJECTED_META_VERTICES", "vertices count")
    ioq.require(np.all(meta["face"] >= 0), "REJECTED_SOURCE_FACE_RANGE", "face>=0")
    kind = meta["kind"]; flags = meta["flags"]
    ioq.require(np.all(meta["proxy"][kind < 2] == -1), "REJECTED_PROXY_SENTINEL", "proxy sentinel -1 for kind<2")
    ioq.require(np.all((meta["proxy"][kind == 2] >= 0) & (meta["proxy"][kind == 2] <= 6)), "REJECTED_PROXY_SENTINEL", "proxy 0..6 for kind2")
    ioq.require(np.all(((flags & 1) != 0) == (kind == 2)), "REJECTED_META_FLAGS", "flags bit1 proxy must agree with kind2")
    # Padding rows beyond each face's vertex count must be exactly +0.0 bytes;
    # valid vertices (including a legit zero vertex) keep their signed bytes.
    nv = meta["vertices"].astype(np.int64)
    col = np.arange(4)[None, :]; padded = verts[col >= nv[:, None]]
    if padded.size: ioq.require(np.all(padded == 0) and not np.any(np.signbit(padded)), "REJECTED_NONZERO_PADDING", "prototype padding must be +0.0")
    limits = {}; sections = {}
    for idx, row in sections_by_index.items():
        for lod in row.get("lods", []):
            limits[(idx, int(lod["index"]))] = int(lod["faces"]); sections[(idx, int(lod["index"]))] = {int(s["index"]) for s in lod.get("sections", [])}
    sm = meta["source_model"]; ld = meta["lod"]; fc = meta["face"]; sc = meta["section"]
    lim = np.array([limits.get((int(a), int(b)), -1) for a, b in zip(sm.tolist(), ld.tolist())], dtype=np.int64)
    ioq.require(np.all(lim >= 0), "REJECTED_SOURCE_LOD_RANGE", "source_model/lod not in model-sections")
    ioq.require(np.all(fc < lim), "REJECTED_SOURCE_FACE_RANGE", "face >= lod.faces")
    oksec = np.array([int(s) in sections.get((int(a), int(b)), set()) for a, b, s in zip(sm.tolist(), ld.tolist(), sc.tolist())], dtype=bool)
    ioq.require(np.all(oksec), "REJECTED_SOURCE_SECTION_RANGE", "section not in lod")
    return name_to_index

def check_proxy_routes(meta, proxy_paths, sec_by, name_to_index):
    ioq.require(len(proxy_paths) <= 7, "REJECTED_PROXY_COUNT_DISAGREEMENT", "proxy_paths")
    for r in proxy_paths:
        ioq.require(int(r["root_model"]) in sec_by and int(r["source_model"]) in sec_by, "REJECTED_PROXY_MISSING_SOURCE", "route root/source in sections")
        slots = r["slots"]; ioq.require(isinstance(slots, list) and len(slots) >= 1, "REJECTED_PROXY_ROUTE", "slots")
        seen = set(); cur_target = None
        for j, pair in enumerate(slots):
            ioq.require(isinstance(pair, list) and len(pair) == 2 and is_int(pair[0]) and is_int(pair[1]), "REJECTED_PROXY_ROUTE", "slot pair")
            mi, slot = int(pair[0]), int(pair[1])
            ioq.require(mi not in seen, "REJECTED_PROXY_ROUTE_CYCLE", "cycle/repeat in route"); seen.add(mi)
            if cur_target is not None: ioq.require(mi == cur_target, "REJECTED_LOST_PROXY_ROUTE", "slot chain does not join to next model")
            ioq.require(mi in sec_by, "REJECTED_PROXY_MISSING_SOURCE", "slot model missing")
            proxies = sec_by[mi].get("proxies", [])
            ioq.require(0 <= slot < len(proxies), "REJECTED_PROXY_MISSING_SOURCE", "slot index")
            entry = proxies[slot]; cur_target = None
            if is_int(entry): cur_target = int(entry)
            elif isinstance(entry, str):
                nn = norm_name(entry); ioq.require(nn in name_to_index, "REJECTED_PROXY_MISSING_SOURCE", "proxy name target"); cur_target = name_to_index[nn]
            elif isinstance(entry, dict):
                for kk in ("model", "source_model", "index", "target"):
                    if kk in entry and is_int(entry[kk]): cur_target = int(entry[kk]); break
                if cur_target is None and "name" in entry:
                    nn = norm_name(entry["name"]); ioq.require(nn in name_to_index, "REJECTED_PROXY_MISSING_SOURCE", "proxy name target"); cur_target = name_to_index[nn]
        if cur_target is not None: ioq.require(cur_target == int(r["source_model"]), "REJECTED_LOST_PROXY_ROUTE", "route chain must end at source_model")
    if np.any(meta["kind"] == 2):
        routes = proxy_paths
        for mdl, src, px in {(int(a), int(b), int(p)) for a, b, p in zip(meta["model"].tolist(), meta["source_model"].tolist(), meta["proxy"].tolist()) if True}:
            pass
        k2 = meta[meta["kind"] == 2]
        for mdl, src, px in zip(k2["model"].tolist(), k2["source_model"].tolist(), k2["proxy"].tolist()):
            ioq.require(0 <= int(px) < len(routes), "REJECTED_LOST_PROXY_ROUTE", "kind2 proxy index has no route")
            rt = routes[int(px)]
            ioq.require(int(rt["root_model"]) == int(mdl) and int(rt["source_model"]) == int(src), "REJECTED_LOST_PROXY_ROUTE", "route root/source must equal meta model/source_model")

def pilot_check(arrays, spec, limits):
    for g in GROUPS:
        want = int(spec["faces"][g])
        ioq.require(arrays[g].shape == (want, 4, 3) and arrays[g].dtype.str == "<f8", "REJECTED_PILOT_SHAPE", g)
        ioq.require(np.all(np.isfinite(arrays[g])), "REJECTED_PILOT_FINITE", g)
        ioq.require(arrays[g + "_n"].shape == (want,) and arrays[g + "_n"].dtype.str == "|u1", "REJECTED_PILOT_SHAPE", g+"_n")
        ioq.require(arrays[g + "_flags"].shape == (want,) and arrays[g + "_flags"].dtype.str == "|u1", "REJECTED_PILOT_SHAPE", g+"_flags")
        ioq.require(arrays[g + "_source_ids"].shape == (want, 2) and arrays[g + "_source_ids"].dtype.str == "<i4", "REJECTED_PILOT_SHAPE", g+"_source_ids")
        n = arrays[g + "_n"].astype(np.int64)
        ioq.require(np.all((n == 3) | (n == 4)), "REJECTED_PILOT_N", "face_n must be 3 or 4")
        v = arrays[g]
        for i, ni in enumerate(n.tolist()):
            if ni < 4: ioq.require(v[i, ni:, :].tobytes() == b"\x00" * int((4-ni)*3*8), "REJECTED_NONZERO_PADDING", f"{g}[{i}] padding must be +0.0")
    grid = arrays["source_grid"]
    ioq.require(grid.ndim == 3 and grid.shape[2] == 3 and grid.dtype.str == "<f8" and np.all(np.isfinite(grid)), "REJECTED_PILOT_GRID", "source_grid")
    nrows, mcols = int(grid.shape[0]), int(grid.shape[1])
    ioq.require(nrows >= 2 and mcols >= 2, "REJECTED_PILOT_GRID", "grid >=2x2")
    tri = arrays["source_triangles"]
    ioq.require(tri.ndim == 2 and tri.shape[1] == 3 and tri.dtype.str in ("<i4","<i8"), "REJECTED_PILOT_TRIANGLES", "source_triangles signed i4/i8")
    B = int(tri.shape[0])
    ioq.require(B == int(spec["faces"]["bed"]), "REJECTED_PILOT_GRID_BOUND", "source_triangles rows B must equal spec faces.bed")
    ioq.require(nrows * mcols <= 3 * B, "REJECTED_PILOT_GRID_BOUND", "n*m <= 3B")
    ioq.require(np.all((tri >= 0) & (tri < nrows * mcols)), "REJECTED_PILOT_TRIANGLE_RANGE", "triangle index")
    rows = (tri // mcols); cols = (tri % mcols)
    if B:
        for name, got, ex in (("body_row_min", arrays["body_row_min"], rows.min(axis=1)), ("body_row_max", arrays["body_row_max"], rows.max(axis=1)), ("body_col_min", arrays["body_col_min"], cols.min(axis=1)), ("body_col_max", arrays["body_col_max"], cols.max(axis=1))):
            ioq.require(got.shape == (B,) and got.dtype.str in ("<i4","<i8"), "REJECTED_PILOT_EXTREMA", name)
            ioq.require(np.array_equal(got.astype(np.int64), ex), "REJECTED_PILOT_EXTREMA", name + " mismatch per triangle")
    cat = arrays["source_category"]
    ioq.require(cat.dtype.str == "<U9", "REJECTED_CATEGORY_DTYPE", "source_category must be <U9 exactly, no casting")
    ioq.require(cat.shape == (B,), "REJECTED_CATEGORY_COUNT", "source_category length B")
    vals = [str(x) for x in cat.tolist()]
    ioq.require(all(v in ("BODY", "CAP_START", "CAP_END") for v in vals), "REJECTED_SOURCE_CATEGORY_UNKNOWN", "category alphabet")
    regions = spec.get("source_regions", {})
    ioq.require(set(regions) <= {"BODY","CAP_START","CAP_END"}, "REJECTED_SOURCE_CATEGORY_UNKNOWN", "source_regions alphabet")
    ioq.require(sum(int(v) for v in regions.values()) == B, "REJECTED_CATEGORY_COUNT", "source_regions sum != B")
    for k, v in regions.items(): ioq.require(vals.count(k) == int(v), "REJECTED_CATEGORY_COUNT", f"category {k}")
    for name in ("npz_start", "cap_before", "cap_after"):
        a = arrays[name]; ioq.require(a.shape == () and a.dtype.str == "<i4", "REJECTED_PILOT_SCALAR", name)
    ioq.require(int(arrays["npz_start"]) >= 0, "REJECTED_NPZ_START_NEGATIVE", "npz_start>=0 global")
    ioq.require(int(arrays["cap_before"]) in (0, 8) and int(arrays["cap_after"]) in (0, 8), "REJECTED_CAPS", "caps each 0 or 8")
    ioq.require(nrows - int(arrays["cap_before"]) - int(arrays["cap_after"]) >= 2, "REJECTED_CAPS_REMOVE_BODY", "caps remove body")
    bf = arrays["bed_source_face"]
    ioq.require(bf.shape == (B,) and bf.dtype.str == "<i4", "REJECTED_PILOT_SHAPE", "bed_source_face")
    ioq.require(sorted(int(x) for x in bf.tolist()) == list(range(B)), "REJECTED_BED_SOURCE_FACE_PERMUTATION", "bed_source_face must be a permutation of 0..B-1")

def build_report(contract_path, external_sha):
    c, csha = load_contract(contract_path, external_sha); lim = c["limits"]; exp = c["expected"]; pins = c["pins"]
    root = c["source_root"]
    for key in (SURF+"/inputs.json", SURF+"/model-catalog.json", SURF+"/model-sections.json", SURF+"/proxy-paths.json", SURF+"/report.json", PILOTD+"/inputs.json", PILOTD+"/models.json", PILOTD+"/report.json", "surface_manifest", "pilot_manifest"):
        ioq.require(key in pins, "REJECTED_PIN_LOOKUP", key)
    objs = {}; sources = []; json_total = 0
    for k, pin in pins.items():
        req_keys(pin, {"path","sha256","bytes"}, "REJECTED_PIN_SCHEMA", k)
        # Authorized roots: source_root for source files, or the exact
        # manifest pin paths themselves; no fallback paths.
        pth = str(pin["path"])
        if k not in ("surface_manifest", "pilot_manifest"):
            ioq.require(pth.startswith(str(root)), "REJECTED_PIN_LOOKUP", f"pin outside source_root {k}")
        data = read_snapshot(pth, int(lim["json_bytes"])); check_pin(data, _subpin(pin), k)
        json_total += len(data); ioq.require(json_total <= int(lim["json_total_bytes"]), "REJECTED_SIZE_CAP", "json_total_bytes")
        objs[k] = parse_json(data, k); sources.append({"path": pth, "sha256": pin["sha256"], "bytes": int(pin["bytes"]), "kind": "json", "members": []})
    catalog = objs[SURF+"/model-catalog.json"]; sections = objs[SURF+"/model-sections.json"]; proxy_paths = objs[SURF+"/proxy-paths.json"]
    surface_inputs = objs[SURF+"/inputs.json"]; pilot_inputs = objs[PILOTD+"/inputs.json"]; pilot_models = objs[PILOTD+"/models.json"]; pilot_report = objs[PILOTD+"/report.json"]; surface_report = objs[SURF+"/report.json"]
    ioq.require(isinstance(catalog, list) and isinstance(sections, list) and isinstance(proxy_paths, list) and isinstance(pilot_models, list), "REJECTED_METADATA_SCHEMA", "catalog/sections/proxy/models must be lists")
    req_keys(surface_inputs, {"source_pins","discovery_artifacts","artifact_manifest_sha256","script_sha256","reader"}, "REJECTED_METADATA_FIELD", "surface inputs")
    req_keys(pilot_inputs, {"pins","script_sha256"}, "REJECTED_METADATA_FIELD", "pilot inputs")
    check_epoch_links(c, surface_inputs, pilot_inputs)
    for row in catalog: req_keys(row, {"index","name","instances","group"}, "REJECTED_METADATA_FIELD", "catalog row")
    for row in sections: req_keys(row, {"name","index","lods","proxies","center"}, "REJECTED_METADATA_FIELD", "model-sections row")
    for row in proxy_paths: req_keys(row, {"root_model","slots","source_model"}, "REJECTED_METADATA_FIELD", "proxy-paths row")
    cat_idx = [int(r["index"]) for r in catalog]
    ioq.require(len(cat_idx) == len(set(cat_idx)), "REJECTED_CATALOG_DUPLICATE", "catalog index")
    ioq.require(len({norm_name(r["name"]) for r in catalog}) == len(catalog), "REJECTED_CATALOG_DUPLICATE", "catalog name")
    sec_by = {int(r["index"]): r for r in sections}
    ioq.require(len(sec_by) == len(sections), "REJECTED_SECTIONS_DUPLICATE", "sections index")
    name_to_index = {}
    for r in sections:
        nn = norm_name(r["name"]); ioq.require(nn not in name_to_index, "REJECTED_SECTIONS_DUPLICATE", "sections canonical name"); name_to_index[nn] = int(r["index"])
    # Cross-check manifest overlaps against contract pins/arrays.
    pin_by_rel = {k: v for k, v in pins.items()}; arr_by_rel = {a["relative"]: a for a in c["arrays"]}
    for mk in ("surface_manifest", "pilot_manifest"):
        man = objs[mk]; ioq.require(isinstance(man, dict), "REJECTED_METADATA_FIELD", mk)
        for rel, ent in man.items():
            if isinstance(ent, dict) and rel in pin_by_rel: ioq.require(ent.get("sha256") == pin_by_rel[rel]["sha256"] and int(ent.get("bytes", -1)) == int(pin_by_rel[rel]["bytes"]), "REJECTED_EPOCH_LINK", f"manifest {rel}")
            if isinstance(ent, dict) and rel in arr_by_rel: ioq.require(ent.get("sha256") == arr_by_rel[rel]["sha256"] and int(ent.get("bytes", -1)) == int(arr_by_rel[rel]["bytes"]), "REJECTED_EPOCH_LINK", f"manifest {rel}")
    npz_sources = {}; member_count = 0; arrays_by_kind = {}; total_expanded = 0; pilot_entries = {}
    for a in c["arrays"]:
        req_keys(a, {"path","relative","kind","sha256","bytes","expanded_bound"}, "REJECTED_ARRAY_SCHEMA", "array entry")
        ioq.require(str(a["path"]) == _join(root, a["relative"]) or str(a["path"]).startswith(str(root)), "REJECTED_PIN_LOOKUP", a["relative"])
        npz_sources[a["relative"]] = {"path": str(a["path"]), "sha256": a["sha256"], "bytes": int(a["bytes"]), "kind": "npz", "members": []}
        if a["kind"] == "pilot": pilot_entries[a["relative"]] = a
    ioq.require(len(pilot_entries) + 3 == len(c["arrays"]), "REJECTED_ARRAY_KIND", "core+pilot arrays")
    for a in c["arrays"]:
        if a["kind"] == "pilot": continue
        data = read_snapshot(a["path"], int(lim["npz_stored_bytes"])); check_pin(data, _subpin(a), a["relative"])
        schema = c["npz_schemas"][a["kind"]]
        members = schema["members"] if "members" in schema else c["npz_schemas"]["instances"]["members"]
        arrs, meta = load_npz(data, members, lim, a["relative"], expanded_bound=int(a["expanded_bound"]))
        total_expanded += sum(int(m["itemsize"]) * int(np.prod(m["shape"])) + int(m["header_bytes"]) + 12 for m in meta)
        ioq.require(total_expanded <= int(lim["total_expanded_bytes"]), "REJECTED_ZIP_EXPANDED_CAP", "total_expanded_bytes")
        arrays_by_kind[a["kind"]] = arrs; npz_sources[a["relative"]]["members"] = meta; member_count += len(meta)
        del data
    ioq.require(set(arrays_by_kind) == {"prototypes","instances","selected"}, "REJECTED_ARRAY_KIND", "core arrays")
    proto = arrays_by_kind["prototypes"]; meta_arr = proto["meta"]; verts = proto["vertices"]
    pschema = c["npz_schemas"]["prototypes"]
    if "shape" in pschema.get("vertices", {}): ioq.require(verts.shape == tuple(pschema["vertices"]["shape"]) and verts.dtype.str == pschema["vertices"]["dtype"], "REJECTED_WRONG_SHAPE", "prototypes vertices")
    if "shape" in pschema.get("meta", {}): ioq.require(meta_arr.shape == tuple(pschema["meta"]["shape"]), "REJECTED_WRONG_SHAPE", "prototypes meta")
    if "descr" in pschema.get("meta", {}): ioq.require(ioq.descr_json(meta_arr.dtype) == [[str(x[0]), str(x[1])] for x in pschema["meta"]["descr"]], "REJECTED_META_DESCR", "contract META descr")
    validate_meta(meta_arr, verts, sec_by, name_to_index)
    ins = arrays_by_kind["instances"]; sel = arrays_by_kind["selected"]
    ischema = c["npz_schemas"].get("instances", {})
    if ischema.get("shapes"):
        for col, shp in ischema["shapes"].items(): ioq.require(ins[col].shape == tuple(shp), "REJECTED_WRONG_SHAPE", f"instances.{col}")
    N = int(ins["ids"].shape[0]) if ins["ids"].ndim == 1 else -1
    ioq.require(ins["ids"].ndim == 1 and ins["model_index"].shape == (N,) and ins["matrix"].shape == (N, 12) and ins["norm"].shape == (N, 3) and ins["determinant"].shape == (N,) and ins["nonorthogonality"].shape == (N,), "REJECTED_WRONG_SHAPE", "instances shapes exact (n,12) matrix")
    for col in ("ids", "model_index", "matrix"):
        ioq.require(col in sel and ins[col].dtype.str == sel[col].dtype.str and ins[col].shape == sel[col].shape and ins[col].tobytes(order="C") == sel[col].tobytes(order="C"), "REJECTED_SELECTED_MISMATCH", col)
    for col in ("ids", "model_index"):
        d = ins[col].dtype; ioq.require(d.kind in "iu" and d.itemsize in (4, 8) and d.str[0] in "<|=", "REJECTED_INSTANCE_DTYPE", col)
    ioq.require(ins["matrix"].dtype.kind == "f" and ins["matrix"].dtype.itemsize in (4, 8) and ins["matrix"].dtype.str[0] in "<|=" and np.all(np.isfinite(ins["matrix"])), "REJECTED_INSTANCE_DTYPE", "matrix finite f4/f8")
    for m in ("norm", "determinant", "nonorthogonality"):
        ioq.require(ins[m].dtype.str == "<f8" and np.all(np.isfinite(ins[m])), "REJECTED_INSTANCE_METRIC", m)
    ioq.require(np.all(np.isfinite(ins["norm"])), "REJECTED_INSTANCE_METRIC", "norm finite")
    ids = ins["ids"].astype(np.int64); midx = ins["model_index"].astype(np.int64)
    ioq.require(len(set(ids.tolist())) == len(ids), "REJECTED_DUPLICATE_INSTANCE_ID", "ids unique")
    cat_set = set(cat_idx); by_idx = {int(r["index"]): r for r in catalog}
    ioq.require(set(midx.tolist()) <= cat_set, "REJECTED_MISMATCHED_INSTANCE_MODEL", "instance model_index not in catalog")
    counts = Counter(int(x) for x in midx.tolist())
    nonveg = {int(r["index"]) for r in catalog if r["group"] != "vegetation_not_inspected"}
    veg = cat_set - nonveg
    for r in catalog:
        idx = int(r["index"]); req_int(r["instances"], "REJECTED_METADATA_FIELD", "catalog.instances")
        if idx in nonveg: ioq.require(counts.get(idx, 0) == int(r["instances"]), "REJECTED_INSTANCE_COUNT", f"catalog {idx} instances {r['instances']} != saved {counts.get(idx,0)}")
    meta_models = set(int(x) for x in np.unique(meta_arr["model"]).tolist()); meta_src = set(int(x) for x in np.unique(meta_arr["source_model"]).tolist())
    ioq.require(meta_models == nonveg, "REJECTED_META_MODEL_SET", "meta model must equal exact nonvegetation catalog set")
    ioq.require(meta_src == set(sec_by), "REJECTED_META_SOURCE_SET", "meta source_model != model-sections index set")
    proxy_only = sorted(meta_src - cat_set); not_saved = sorted(cat_set - meta_models)
    ioq.require(set(not_saved) == veg and all(by_idx[i]["group"] == "vegetation_not_inspected" for i in not_saved), "REJECTED_NOT_SAVED_VEGETATION", "NOT_SAVED must be exactly vegetation")
    ioq.require(len(catalog) == int(exp["source_models"]), "REJECTED_OMITTED_CATALOG_MODEL", "source_models count")
    ranges = {}; mdl = meta_arr["model"].astype(np.int64); start = 0
    for i in range(1, len(mdl) + 1):
        if i == len(mdl) or mdl[i] != mdl[start]: ranges.setdefault(int(mdl[start]), []).append([int(start), int(i)]); start = i
    ambiguous = int(np.sum((meta_arr["flags"] & 2) != 0)); degenerate = int(np.sum((meta_arr["flags"] & 4) != 0))
    ioq.require(ambiguous == int(exp["ambiguous"]) and degenerate == int(exp["degenerate"]), "REJECTED_COVERAGE", "ambiguous/degenerate from flags bits 2/4")
    ioq.require(int(exp["prototype_faces"]) == len(meta_arr), "REJECTED_PROTOTYPE_FACES", "faces")
    ioq.require(int(exp["roadway"]) == int(np.sum(meta_arr["kind"] == 0)) and int(exp["water_visual"]) == int(np.sum(meta_arr["kind"] == 1)) and int(exp["conditional_proxy"]) == int(np.sum(meta_arr["kind"] == 2)), "REJECTED_KIND_COUNT", "kind counts")
    ioq.require(len(proxy_paths) == int(exp["proxy_paths"]), "REJECTED_PROXY_COUNT_DISAGREEMENT", "proxy_paths")
    check_proxy_routes(meta_arr, proxy_paths, sec_by, name_to_index)
    if isinstance(surface_report, dict):
        for key, val in (("models", len(meta_models)+len(proxy_only)), ("instances", N), ("prototype_faces", len(meta_arr)), ("roadway_faces", int(np.sum(meta_arr["kind"]==0))), ("water_faces", int(np.sum(meta_arr["kind"]==1))), ("conditional_proxy_faces", int(np.sum(meta_arr["kind"]==2))), ("ambiguous_faces", ambiguous), ("degenerate_faces", degenerate)):
            if key in surface_report: ioq.require(int(surface_report[key]) == int(val), "REJECTED_COVERAGE", f"surface report {key}")
    models = []
    for idx in sorted(cat_set | set(proxy_only)):
        if idx in by_idx:
            row = by_idx[idx]; saved = idx in meta_models; layers = []; lstatus = {}
            if saved:
                ks = sorted({int(x) for x in np.unique(meta_arr["kind"][mdl == idx]).tolist()})
                for k in ks:
                    ln = "roadway" if k == 0 else "water_visual" if k == 1 else "conditional_proxy"; layers.append(ln); lstatus[ln] = "CONDITIONAL" if k == 2 else "RAW_UNCERTIFIED"
            frame = "NOT_SAVED" if not saved else ("CONDITIONAL" if layers and all(v == "CONDITIONAL" for v in lstatus.values()) else "RAW_UNCERTIFIED")
            models.append({"index": idx, "name": row["name"], "group": row["group"], "instance_count": int(counts.get(idx, 0)), "layers": layers, "layer_status": lstatus, "frame": frame, "prototype_ranges": ranges.get(idx, []), "status": "SAVED" if saved else "NOT_SAVED"})
        else:
            srow = sec_by[idx]; layers = ["conditional_proxy"] if idx in meta_src else []
            models.append({"index": idx, "name": srow["name"], "group": None, "instance_count": 0, "layers": layers, "layer_status": {"conditional_proxy": "CONDITIONAL"} if layers else {}, "frame": "CONDITIONAL", "prototype_ranges": ranges.get(idx, []), "status": "PROXY_ONLY"})
    ioq.require(len(models) == int(exp["source_models"]) + int(exp["proxy_only_models"]), "REJECTED_TERMINAL_MODELS", "terminal rows")
    ioq.require(len(pilot_models) == int(exp["pilot_models"]), "REJECTED_PILOT_COUNT_ZERO", "pilot count from models.json")
    ioq.require(len(pilot_models) > 0, "REJECTED_PILOT_COUNT_ZERO", "pilot count zero")
    for spec in c["pilot_specs"]:
        match = [r for r in pilot_models if r.get("file") == spec.get("file")]
        ioq.require(len(match) == 1, "REJECTED_PILOT_ARCHIVE", "contract pilot_specs must match models.json row")
        for kk in ("model","model_index","instance_id","site","station","file","faces","ambiguous_faces","unmapped_bed_faces","source_regions","checks"):
            if kk in spec: ioq.require(spec[kk] == match[0].get(kk), "REJECTED_PILOT_SPEC_MISMATCH", f"pilot spec {kk} vs models.json")
    sites = Counter(str(r["site"]) for r in pilot_models)
    if isinstance(pilot_report, dict) and "sites" in pilot_report: ioq.require(dict(sites) == pilot_report["sites"], "REJECTED_PILOT_SITE_COUNT", "sites from models.json vs pilot report.sites")
    if isinstance(pilot_report, dict) and "models" in pilot_report: ioq.require(int(pilot_report["models"]) == len(pilot_models), "REJECTED_PILOT_COUNT_ZERO", "pilot report models")
    ioq.require(len({r["model_index"] for r in pilot_models}) == len(pilot_models) and len({r["instance_id"] for r in pilot_models}) == len(pilot_models) and len({r["model"] for r in pilot_models}) == len(pilot_models), "REJECTED_PILOT_UNIQUE", "pilot uniqueness")
    pilots = []; schema_pilot = c["npz_schemas"]["pilot"]
    for spec in pilot_models:
        mi = int(spec["model_index"]); iid = int(spec["instance_id"])
        ioq.require(mi in by_idx, "REJECTED_PILOT_SPEC_MISMATCH", "pilot model_index in catalog")
        ioq.require(norm_name(spec["model"]) == norm_name(by_idx[mi]["name"]), "REJECTED_PILOT_SPEC_MISMATCH", "spec model vs catalog name at model_index")
        rows = np.where((midx == mi) & (ids == iid))[0]
        ioq.require(len(rows) == 1, "REJECTED_PILOT_TWO_INSTANCES", f"pilot {spec.get('model')} matching pose must be exactly one")
        ioq.require(int(counts.get(mi, 0)) == 1, "REJECTED_PILOT_TWO_INSTANCES", f"pilot model {mi} must have exactly one saved instance")
        rel = PILOTD + "/" + str(spec["file"])
        ioq.require(rel in pilot_entries, "REJECTED_PILOT_ARCHIVE", f"exact archive {rel}")
        a = pilot_entries[rel]
        if "sha256" in spec: ioq.require(spec["sha256"] == a["sha256"], "REJECTED_PILOT_ARCHIVE", "models.json sha vs contract array")
        data = read_snapshot(a["path"], int(lim["npz_stored_bytes"])); check_pin(data, _subpin(a), rel)
        members = [g + s for g in GROUPS for s in ("", "_n", "_flags", "_source_ids")] + list(schema_pilot.get("extra_members", []))
        arrs, pmeta = load_npz(data, members, lim, rel, expanded_bound=int(a["expanded_bound"])); del data
        total_expanded += sum(int(m["itemsize"]) * int(np.prod(m["shape"])) + int(m["header_bytes"]) + 12 for m in pmeta)
        ioq.require(total_expanded <= int(lim["total_expanded_bytes"]), "REJECTED_ZIP_EXPANDED_CAP", "total_expanded_bytes")
        pilot_check(arrs, spec, lim)
        npz_sources[rel]["members"] = pmeta; member_count += len(pmeta)
        vals = [str(x) for x in arrs["source_category"].tolist()]
        pilots.append({"model": spec["model"], "model_index": mi, "instance_id": iid, "site": spec["site"], "archive": rel, "pose_row": int(rows[0]), "world_frame": "ALREADY_WORLD_UNCERTIFIED", "arrays": {m["name"]: m["data_sha256"] for m in pmeta}, "categories": {k: vals.count(k) for k in sorted(set(vals))}, "historical_checks": spec.get("checks", {})})
        del arrs, pmeta  # release per-pilot before next
    for a in c["arrays"]: sources.append(npz_sources[a["relative"]])
    coverage = {"source_models": len(catalog), "prototype_models": len(meta_models) + len(proxy_only), "proxy_only_models": len(proxy_only), "vegetation_models_not_saved": len(not_saved), "instances": int(len(ids)), "prototype_faces": int(len(meta_arr)), "roadway": int(np.sum(meta_arr["kind"]==0)), "water_visual": int(np.sum(meta_arr["kind"]==1)), "conditional_proxy": int(np.sum(meta_arr["kind"]==2)), "ambiguous": ambiguous, "degenerate": degenerate, "proxy_paths": len(proxy_paths), "pilot_models": len(pilots), "human_resolved": 0, "member_count": int(member_count)}
    for k in ("source_models","prototype_models","proxy_only_models","vegetation_models_not_saved","instances","prototype_faces","roadway","water_visual","conditional_proxy","ambiguous","degenerate","proxy_paths","pilot_models","human_resolved"):
        ioq.require(coverage[k] == int(exp[k]), "REJECTED_COVERAGE", k)
    routes = [{"root_model": r["root_model"], "slots": r["slots"], "source_model": r["source_model"], "engine_binding": "UNKNOWN", "section_index": "UNKNOWN"} for r in proxy_paths]
    report = {"schema": "q03b-saved-scene-binding-report-v1", "contract_sha256": csha, "status": "VERIFIED_SAVED_SCENE_BINDING_ONLY", "claims": dict(CLAIMS), "coverage": coverage, "sources": sources, "models": models, "pilots": pilots, "proxy_routes": routes, "limitations": ["no native acceptance", "no current precedence", "no exposure evaluation", "no globally complete faces", "no geometry repair", "human_resolved=0", "C1=NOT_REVIEWED", "world frame not certified"]}
    ioq.require(list(report.keys()) == list(c["output_schema"]["report_keys"]) or set(report.keys()) == set(c["output_schema"]["report_keys"]), "REJECTED_REPORT_KEYS", "report keys")
    return report
def produce(contract, contract_sha, output):
    out = new_output(output)
    try:
        report = build_report(contract, contract_sha); atomic_write_json(out, "report.json", report); return 0
    except Reject as e: atomic_write_json(out, "failure.json", failure_obj(e)); return 1
    except Inconclusive as e: atomic_write_json(out, "failure.json", failure_obj(e)); return 2
    except Exception as e:
        exc = Inconclusive("INCONCLUSIVE_SOURCE_IO", f"{type(e).__name__}: {e}"); atomic_write_json(out, "failure.json", failure_obj(exc)); return 2
def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--contract", required=True); ap.add_argument("--contract-sha", required=True); ap.add_argument("--output", required=True)
    a = ap.parse_args(argv); return produce(a.contract, a.contract_sha, a.output)
if __name__ == "__main__": raise SystemExit(main())
