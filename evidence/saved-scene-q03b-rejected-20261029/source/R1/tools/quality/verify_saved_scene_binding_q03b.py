"""Q03B consumer: independent semantic walker.

Shares only saved_scene_io_q03b I/O/digest primitives with the producer.
It does not import the producer, its checks, META guards or report builder,
and re-derives the expected report from pinned sources itself. Similar
algorithms are re-declared here independently.
"""
from __future__ import annotations
import argparse, sys
from collections import Counter
from pathlib import Path
import numpy as np
try:
    from tools.quality.saved_scene_io_q03b import Reject, Inconclusive, sha256_bytes, read_snapshot, check_pin, parse_json, contract_bytes, load_npz, new_output, atomic_write_json, failure_obj, req_keys
    from tools.quality import saved_scene_io_q03b as ioq
except Exception:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import saved_scene_io_q03b as ioq
    from saved_scene_io_q03b import Reject, Inconclusive, sha256_bytes, read_snapshot, check_pin, parse_json, contract_bytes, load_npz, new_output, atomic_write_json, failure_obj, req_keys
CLAIMS = {"world_frame_certified": False, "exposure_evaluated": False, "native_acceptance": False, "build_ready": False, "map_repaired": False}
REPORT_KEYS = {"schema","contract_sha256","status","claims","coverage","sources","models","pilots","proxy_routes","limitations"}
CGROUPS = ["bed","water","unknown","road_bed","road_water","road_unknown"]
CSURF = "deployed-surface-prototypes-20261028"; CPILOT = "pilot-visible-surface-extraction-20261028"; CGEO = "geometry-payload-discovery-resolved-20261028"
CPBO = r"P:\Mods\@DayZ_Baltic_EV112_Kit7Nav8Load1\Addons\baltic_stream_pilot.pbo"
CMANIFEST_LIT = r"evidence\deployed-surface-prototypes-20261028\artifact-hashes.json"
CMETA = [["model","<i4"],["source_model","<i4"],["face","<i4"],["section","<i4"],["lod","<i4"],["kind","|u1"],["vertices","|u1"],["flags","|u1"],["proxy","<i4"],["planarity_m","<f8"]]

def strict_equal(a, b, path="$"):
    if type(a) is not type(b): raise Reject("REJECTED_STRICT_TYPE", f"{path}: {type(a).__name__} != {type(b).__name__}")
    if isinstance(a, dict):
        ioq.require(set(a) == set(b), "REJECTED_UNKNOWN_KEY", f"{path} keys differ")
        for k in a: strict_equal(a[k], b[k], path + "." + str(k))
    elif isinstance(a, list):
        ioq.require(len(a) == len(b), "REJECTED_STRICT_LENGTH", path)
        for i, (x, y) in enumerate(zip(a, b)): strict_equal(x, y, f"{path}[{i}]")
    else: ioq.require(a == b, "REJECTED_REPORT_MISMATCH", f"{path}: {a!r} != {b!r}")
def cnorm(s):
    ioq.require(isinstance(s, str) and all(32 <= ord(ch) < 128 for ch in s), "REJECTED_NAME", str(s))
    t = s.replace("\\", "/").strip("/").lower()
    ioq.require(bool(t) and all(p not in ("", ".", "..") for p in t.split("/")) and not (len(t) >= 2 and t[1] == ":"), "REJECTED_NAME", s)
    return t
def csep(base): return "\\" if ("\\" in str(base) or ":" in str(base)) else "/"
def cjoin(base, rel):
    sep = csep(base); return str(base).rstrip("\\/") + sep + rel.replace("/", sep)
def csub(pin): return {"path": pin["path"], "sha256": pin["sha256"], "bytes": pin["bytes"]}

def rebuild(contract_path, external_sha):
    data = contract_bytes(contract_path, external_sha); csha = sha256_bytes(data); c = parse_json(data, "contract")
    ioq.require(c.get("schema") == "q03b-saved-scene-binding-r1", "REJECTED_CONTRACT_SCHEMA", "schema")
    ioq.require(c.get("claims") == CLAIMS, "REJECTED_CLAIM_FIELD", "claims")
    lim = c["limits"]; exp = c["expected"]; pins = c["pins"]; root = c["source_root"]
    for key in (CSURF+"/inputs.json", CSURF+"/model-catalog.json", CSURF+"/model-sections.json", CSURF+"/proxy-paths.json", CSURF+"/report.json", CPILOT+"/inputs.json", CPILOT+"/models.json", CPILOT+"/report.json", "surface_manifest", "pilot_manifest"):
        ioq.require(key in pins, "REJECTED_PIN_LOOKUP", key)
    objs = {}; sources = []; jtot = 0
    for k, pin in pins.items():
        req_keys(pin, {"path","sha256","bytes"}, "REJECTED_PIN_SCHEMA", k)
        if k not in ("surface_manifest", "pilot_manifest"): ioq.require(str(pin["path"]).startswith(str(root)), "REJECTED_PIN_LOOKUP", k)
        raw = read_snapshot(pin["path"], int(lim["json_bytes"])); check_pin(raw, csub(pin), k)
        jtot += len(raw); ioq.require(jtot <= int(lim["json_total_bytes"]), "REJECTED_SIZE_CAP", "json_total")
        objs[k] = parse_json(raw, k); sources.append({"path": str(pin["path"]), "sha256": pin["sha256"], "bytes": int(pin["bytes"]), "kind": "json", "members": []})
    catalog = objs[CSURF+"/model-catalog.json"]; sections = objs[CSURF+"/model-sections.json"]; proxy_paths = objs[CSURF+"/proxy-paths.json"]
    sinputs = objs[CSURF+"/inputs.json"]; pinputs = objs[CPILOT+"/inputs.json"]; pmodels = objs[CPILOT+"/models.json"]; preport = objs[CPILOT+"/report.json"]; sreport = objs[CSURF+"/report.json"]
    ioq.require(isinstance(catalog, list) and isinstance(sections, list) and isinstance(proxy_paths, list) and isinstance(pmodels, list), "REJECTED_METADATA_SCHEMA", "lists")
    req_keys(sinputs, {"source_pins","discovery_artifacts","artifact_manifest_sha256","script_sha256","reader"}, "REJECTED_METADATA_FIELD", "surface inputs")
    req_keys(pinputs, {"pins","script_sha256"}, "REJECTED_METADATA_FIELD", "pilot inputs")
    for row in catalog: req_keys(row, {"index","name","instances","group"}, "REJECTED_METADATA_FIELD", "catalog row")
    for row in sections: req_keys(row, {"name","index","lods","proxies","center"}, "REJECTED_METADATA_FIELD", "sections row")
    for row in proxy_paths: req_keys(row, {"root_model","slots","source_model"}, "REJECTED_METADATA_FIELD", "proxy row")
    # Independent epoch binding with exact literal keys.
    epoch = c["epoch"]; sp = sinputs.get("source_pins"); ioq.require(isinstance(sp, dict), "REJECTED_EPOCH_LINK", "source_pins")
    mp = str(pins["surface_manifest"]["path"]); msep = csep(mp); mparts = mp.replace("\\", "/").rstrip("/").split("/")
    ioq.require(mparts[-3:] == ["evidence", "deployed-surface-prototypes-20261028", "artifact-hashes.json"], "REJECTED_EPOCH_LINK", "manifest suffix")
    wt = msep.join(mparts[:-3])
    for key, want, code in ((cjoin(root, "package-kit7-fc-world-20261026/compiled/narva_trial/baltic_trial.wrp"), epoch["wrp_compiled"], "REJECTED_EPOCH_WRONG"), (cjoin(root, "stage-kit7-fc-20261026/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp"), epoch["wrp_editable"], "REJECTED_EPOCH_WRONG"), (CPBO, epoch["pilot_pbo"], "REJECTED_EPOCH_WRONG_PBO")):
        ioq.require(key in sp and sp[key] == want, code if key in sp else "REJECTED_EPOCH_LINK", key)
    dkey = cjoin(wt, "evidence/deployed-geometry-discovery-20261028/artifact-hashes.json")
    ioq.require(dkey in sp, "REJECTED_EPOCH_LINK", "discovery key")
    ioq.require(sinputs.get("artifact_manifest_sha256") == sp[dkey], "REJECTED_EPOCH_LINK", "artifact_manifest is discovery manifest, not surface manifest")
    arr_by_rel = {a["relative"]: a for a in c["arrays"]}
    sel_rel = CGEO + "/selected-instances.npz"; ioq.require(sel_rel in arr_by_rel, "REJECTED_EPOCH_LINK", "selected array")
    ioq.require(sp.get(cjoin(root, sel_rel)) == arr_by_rel[sel_rel]["sha256"], "REJECTED_SELECTED_PIN", "selected source_pin")
    da = sinputs.get("discovery_artifacts"); ioq.require(isinstance(da, dict) and sel_rel in da and da[sel_rel].get("sha256") == arr_by_rel[sel_rel]["sha256"] and int(da[sel_rel].get("bytes", -1)) == int(arr_by_rel[sel_rel]["bytes"]), "REJECTED_SELECTED_PIN", "discovery selected")
    pp = pinputs.get("pins"); ioq.require(isinstance(pp, dict), "REJECTED_EPOCH_LINK", "pilot pins dict")
    for key, want, code in ((CMANIFEST_LIT, pins["surface_manifest"]["sha256"], "REJECTED_EPOCH_LINK"), (cjoin(root, CSURF+"/inputs.json"), pins[CSURF+"/inputs.json"]["sha256"], "REJECTED_EPOCH_WRONG_POSE_PIN"), (cjoin(root, CSURF+"/instances.npz"), arr_by_rel[CSURF+"/instances.npz"]["sha256"], "REJECTED_EPOCH_WRONG_POSE_PIN")):
        ioq.require(key in pp and pp[key] == want, code if key in pp else "REJECTED_EPOCH_LINK", key)
    sec_by = {int(r["index"]): r for r in sections}; ioq.require(len(sec_by) == len(sections), "REJECTED_SECTIONS_DUPLICATE", "sections")
    name_idx = {}
    for r in sections:
        nn = cnorm(r["name"]); ioq.require(nn not in name_idx, "REJECTED_SECTIONS_DUPLICATE", "section name"); name_idx[nn] = int(r["index"])
    npz_src = {}; member_count = 0; store = {}; tot_exp = 0; pentries = {}
    for a in c["arrays"]:
        req_keys(a, {"path","relative","kind","sha256","bytes","expanded_bound"}, "REJECTED_ARRAY_SCHEMA", "array")
        npz_src[a["relative"]] = {"path": str(a["path"]), "sha256": a["sha256"], "bytes": int(a["bytes"]), "kind": "npz", "members": []}
        if a["kind"] == "pilot": pentries[a["relative"]] = a
    for a in c["arrays"]:
        if a["kind"] == "pilot": continue
        raw = read_snapshot(a["path"], int(lim["npz_stored_bytes"])); check_pin(raw, csub(a), a["relative"])
        sch = c["npz_schemas"][a["kind"]]; mem = sch["members"] if "members" in sch else c["npz_schemas"]["instances"]["members"]
        arrs, meta = load_npz(raw, mem, lim, a["relative"], expanded_bound=int(a["expanded_bound"])); del raw
        tot_exp += sum(int(m["itemsize"]) * int(np.prod(m["shape"])) + int(m["header_bytes"]) + 12 for m in meta)
        ioq.require(tot_exp <= int(lim["total_expanded_bytes"]), "REJECTED_ZIP_EXPANDED_CAP", "total expanded")
        store[a["kind"]] = arrs; npz_src[a["relative"]]["members"] = meta; member_count += len(meta)
    ioq.require(set(store) == {"prototypes","instances","selected"}, "REJECTED_ARRAY_KIND", "core")
    meta_arr = store["prototypes"]["meta"]; verts = store["prototypes"]["vertices"]
    # Independent META guards, re-derived here.
    ioq.require(ioq.descr_json(meta_arr.dtype) == CMETA and meta_arr.dtype.itemsize == 35, "REJECTED_META_DESCR", "meta descr/itemsize")
    ioq.require(np.all(np.isfinite(meta_arr["planarity_m"])) and np.all(np.isfinite(verts)), "REJECTED_META_FINITE", "finite")
    ioq.require(np.all(meta_arr["kind"] <= 2), "REJECTED_META_KIND", "kind")
    ioq.require(np.all((meta_arr["vertices"] >= 3) & (meta_arr["vertices"] <= 4)), "REJECTED_META_VERTICES", "vertices")
    ioq.require(np.all(meta_arr["face"] >= 0), "REJECTED_SOURCE_FACE_RANGE", "face")
    ioq.require(np.all(meta_arr["proxy"][meta_arr["kind"] < 2] == -1), "REJECTED_PROXY_SENTINEL", "sentinel")
    ioq.require(np.all((meta_arr["proxy"][meta_arr["kind"] == 2] >= 0) & (meta_arr["proxy"][meta_arr["kind"] == 2] <= 6)), "REJECTED_PROXY_SENTINEL", "proxy range")
    ioq.require(np.all(((meta_arr["flags"] & 1) != 0) == (meta_arr["kind"] == 2)), "REJECTED_META_FLAGS", "flags proxy bit")
    nv = meta_arr["vertices"].astype(np.int64); cols = np.arange(4)[None, :]; pad = verts[cols >= nv[:, None]]
    if pad.size: ioq.require(np.all(pad == 0) and not np.any(np.signbit(pad)), "REJECTED_NONZERO_PADDING", "prototype padding +0.0")
    limap = {}; secmap = {}
    for idx, row in sec_by.items():
        for lod in row.get("lods", []): limap[(idx, int(lod["index"]))] = int(lod["faces"]); secmap[(idx, int(lod["index"]))] = {int(s["index"]) for s in lod.get("sections", [])}
    ioq.require(all(int(f) < limap.get((int(s), int(l)), -1) for s, l, f in zip(meta_arr["source_model"].tolist(), meta_arr["lod"].tolist(), meta_arr["face"].tolist())), "REJECTED_SOURCE_FACE_RANGE", "face<lod.faces")
    ioq.require(all(int(s2) in secmap.get((int(s), int(l)), set()) for s, l, s2 in zip(meta_arr["source_model"].tolist(), meta_arr["lod"].tolist(), meta_arr["section"].tolist())), "REJECTED_SOURCE_SECTION_RANGE", "section")
    ins, sel = store["instances"], store["selected"]
    nn_inst = int(ins["ids"].shape[0]) if ins["ids"].ndim == 1 else -1
    ioq.require(ins["matrix"].shape == (nn_inst, 12) and ins["model_index"].shape == (nn_inst,) and ins["norm"].shape == (nn_inst, 3) and ins["determinant"].shape == (nn_inst,) and ins["nonorthogonality"].shape == (nn_inst,), "REJECTED_WRONG_SHAPE", "instances (n,12)")
    for col in ("ids", "model_index", "matrix"):
        ioq.require(ins[col].dtype.str == sel[col].dtype.str and ins[col].shape == sel[col].shape and ins[col].tobytes(order="C") == sel[col].tobytes(order="C"), "REJECTED_SELECTED_MISMATCH", col)
    for col in ("ids", "model_index"):
        d = ins[col].dtype; ioq.require(d.kind in "iu" and d.itemsize in (4, 8) and d.str[0] in "<|=", "REJECTED_INSTANCE_DTYPE", col)
    ioq.require(ins["matrix"].dtype.kind == "f" and ins["matrix"].dtype.itemsize in (4, 8) and np.all(np.isfinite(ins["matrix"])), "REJECTED_INSTANCE_DTYPE", "matrix")
    for mm in ("norm", "determinant", "nonorthogonality"): ioq.require(ins[mm].dtype.str == "<f8" and np.all(np.isfinite(ins[mm])), "REJECTED_INSTANCE_METRIC", mm)
    ids = ins["ids"].astype(np.int64); midx = ins["model_index"].astype(np.int64)
    ioq.require(len(set(ids.tolist())) == len(ids), "REJECTED_DUPLICATE_INSTANCE_ID", "ids")
    cat_set = {int(r["index"]) for r in catalog}; by_idx = {int(r["index"]): r for r in catalog}
    ioq.require(set(midx.tolist()) <= cat_set, "REJECTED_MISMATCHED_INSTANCE_MODEL", "model_index")
    counts = Counter(int(x) for x in midx.tolist()); nonveg = {int(r["index"]) for r in catalog if r["group"] != "vegetation_not_inspected"}; veg = cat_set - nonveg
    for r in catalog:
        if int(r["index"]) in nonveg: ioq.require(counts.get(int(r["index"]), 0) == int(r["instances"]), "REJECTED_INSTANCE_COUNT", f"catalog {r['index']}")
    meta_models = {int(x) for x in np.unique(meta_arr["model"]).tolist()}; meta_src = {int(x) for x in np.unique(meta_arr["source_model"]).tolist()}
    ioq.require(meta_models == nonveg, "REJECTED_META_MODEL_SET", "nonvegetation set")
    ioq.require(meta_src == set(sec_by), "REJECTED_META_SOURCE_SET", "source set")
    proxy_only = sorted(meta_src - cat_set); not_saved = sorted(cat_set - meta_models)
    ioq.require(set(not_saved) == veg, "REJECTED_NOT_SAVED_VEGETATION", "NOT_SAVED vegetation only")
    amb = int(np.sum((meta_arr["flags"] & 2) != 0)); deg = int(np.sum((meta_arr["flags"] & 4) != 0))
    ioq.require(amb == int(exp["ambiguous"]) and deg == int(exp["degenerate"]), "REJECTED_COVERAGE", "flags ambiguous/degenerate")
    # Independent proxy-route binding.
    ioq.require(len(proxy_paths) == int(exp["proxy_paths"]), "REJECTED_PROXY_COUNT_DISAGREEMENT", "proxy_paths")
    for r in proxy_paths:
        ioq.require(int(r["root_model"]) in sec_by and int(r["source_model"]) in sec_by, "REJECTED_PROXY_MISSING_SOURCE", "route ends")
        seen = set(); target = None
        for pair in r["slots"]:
            ioq.require(isinstance(pair, list) and len(pair) == 2, "REJECTED_PROXY_ROUTE", "slot")
            mi, slot = int(pair[0]), int(pair[1])
            ioq.require(mi not in seen, "REJECTED_PROXY_ROUTE_CYCLE", "cycle"); seen.add(mi)
            if target is not None: ioq.require(mi == target, "REJECTED_LOST_PROXY_ROUTE", "chain join")
            ioq.require(mi in sec_by and 0 <= slot < len(sec_by[mi].get("proxies", [])), "REJECTED_PROXY_MISSING_SOURCE", "slot")
            e = sec_by[mi]["proxies"][slot]; target = None
            if isinstance(e, int) and not isinstance(e, bool): target = int(e)
            elif isinstance(e, str):
                tn = cnorm(e); ioq.require(tn in name_idx, "REJECTED_PROXY_MISSING_SOURCE", "proxy name"); target = name_idx[tn]
            elif isinstance(e, dict):
                for kk in ("model","source_model","index","target"):
                    if kk in e and isinstance(e[kk], int) and not isinstance(e[kk], bool): target = int(e[kk]); break
        if target is not None: ioq.require(target == int(r["source_model"]), "REJECTED_LOST_PROXY_ROUTE", "chain end")
    k2 = meta_arr[meta_arr["kind"] == 2]
    for mdl, src, px in zip(k2["model"].tolist(), k2["source_model"].tolist(), k2["proxy"].tolist()):
        ioq.require(0 <= int(px) < len(proxy_paths) and int(proxy_paths[int(px)]["root_model"]) == int(mdl) and int(proxy_paths[int(px)]["source_model"]) == int(src), "REJECTED_LOST_PROXY_ROUTE", "kind2 route")
    mdl = meta_arr["model"].astype(np.int64); ranges = {}; start = 0
    for i in range(1, len(mdl) + 1):
        if i == len(mdl) or mdl[i] != mdl[start]: ranges.setdefault(int(mdl[start]), []).append([int(start), int(i)]); start = i
    models = []
    for idx in sorted(cat_set | set(proxy_only)):
        if idx in by_idx:
            row = by_idx[idx]; saved = idx in meta_models; layers = []; lstatus = {}
            if saved:
                for k in sorted({int(x) for x in np.unique(meta_arr["kind"][mdl == idx]).tolist()}):
                    ln = "roadway" if k == 0 else "water_visual" if k == 1 else "conditional_proxy"; layers.append(ln); lstatus[ln] = "CONDITIONAL" if k == 2 else "RAW_UNCERTIFIED"
            frame = "NOT_SAVED" if not saved else ("CONDITIONAL" if layers and all(v == "CONDITIONAL" for v in lstatus.values()) else "RAW_UNCERTIFIED")
            models.append({"index": idx, "name": row["name"], "group": row["group"], "instance_count": int(counts.get(idx, 0)), "layers": layers, "layer_status": lstatus, "frame": frame, "prototype_ranges": ranges.get(idx, []), "status": "SAVED" if saved else "NOT_SAVED"})
        else:
            layers = ["conditional_proxy"] if idx in meta_src else []
            models.append({"index": idx, "name": sec_by[idx]["name"], "group": None, "instance_count": 0, "layers": layers, "layer_status": {"conditional_proxy": "CONDITIONAL"} if layers else {}, "frame": "CONDITIONAL", "prototype_ranges": ranges.get(idx, []), "status": "PROXY_ONLY"})
    ioq.require(len(pmodels) == int(exp["pilot_models"]) and len(pmodels) > 0, "REJECTED_PILOT_COUNT_ZERO", "pilots")
    for spec in c["pilot_specs"]:
        m = [r for r in pmodels if r.get("file") == spec.get("file")]; ioq.require(len(m) == 1, "REJECTED_PILOT_ARCHIVE", "spec in models.json")
        for kk in ("model","model_index","instance_id","site","station","file","faces","ambiguous_faces","unmapped_bed_faces","source_regions","checks"):
            if kk in spec: ioq.require(spec[kk] == m[0].get(kk), "REJECTED_PILOT_SPEC_MISMATCH", kk)
    sites = Counter(str(r["site"]) for r in pmodels)
    if isinstance(preport, dict) and "sites" in preport: ioq.require(dict(sites) == preport["sites"], "REJECTED_PILOT_SITE_COUNT", "sites")
    if isinstance(sreport, dict):
        for key, val in (("models", len(meta_models)+len(proxy_only)), ("instances", nn_inst), ("prototype_faces", len(meta_arr)), ("roadway_faces", int(np.sum(meta_arr["kind"]==0))), ("water_faces", int(np.sum(meta_arr["kind"]==1))), ("conditional_proxy_faces", int(np.sum(meta_arr["kind"]==2))), ("ambiguous_faces", amb), ("degenerate_faces", deg)):
            if key in sreport: ioq.require(int(sreport[key]) == int(val), "REJECTED_COVERAGE", f"surface report {key}")
    pilots = []
    for spec in pmodels:
        mi = int(spec["model_index"]); iid = int(spec["instance_id"])
        ioq.require(mi in by_idx and cnorm(spec["model"]) == cnorm(by_idx[mi]["name"]), "REJECTED_PILOT_SPEC_MISMATCH", "catalog name")
        rows = np.where((midx == mi) & (ids == iid))[0]
        ioq.require(len(rows) == 1 and int(counts.get(mi, 0)) == 1, "REJECTED_PILOT_TWO_INSTANCES", str(spec.get("model")))
        rel = CPILOT + "/" + str(spec["file"]); ioq.require(rel in pentries, "REJECTED_PILOT_ARCHIVE", rel)
        a = pentries[rel]
        if "sha256" in spec: ioq.require(spec["sha256"] == a["sha256"], "REJECTED_PILOT_ARCHIVE", "models sha")
        raw = read_snapshot(a["path"], int(lim["npz_stored_bytes"])); check_pin(raw, csub(a), rel)
        mem = [g + s for g in CGROUPS for s in ("", "_n", "_flags", "_source_ids")] + list(c["npz_schemas"]["pilot"].get("extra_members", []))
        arrs, pmeta = load_npz(raw, mem, lim, rel, expanded_bound=int(a["expanded_bound"])); del raw
        tot_exp += sum(int(m["itemsize"]) * int(np.prod(m["shape"])) + int(m["header_bytes"]) + 12 for m in pmeta)
        ioq.require(tot_exp <= int(lim["total_expanded_bytes"]), "REJECTED_ZIP_EXPANDED_CAP", "total expanded")
        # Independent pilot guards, same scope as producer.
        for g in CGROUPS:
            want = int(spec["faces"][g])
            ioq.require(arrs[g].shape == (want, 4, 3) and arrs[g].dtype.str == "<f8" and np.all(np.isfinite(arrs[g])), "REJECTED_PILOT_SHAPE", g)
            ioq.require(arrs[g+"_n"].shape == (want,) and arrs[g+"_n"].dtype.str == "|u1", "REJECTED_PILOT_SHAPE", g+"_n")
            ioq.require(arrs[g+"_flags"].shape == (want,) and arrs[g+"_flags"].dtype.str == "|u1", "REJECTED_PILOT_SHAPE", g+"_flags")
            ioq.require(arrs[g+"_source_ids"].shape == (want, 2) and arrs[g+"_source_ids"].dtype.str == "<i4", "REJECTED_PILOT_SHAPE", g+"_source_ids")
            nn = arrs[g+"_n"].astype(np.int64); ioq.require(np.all((nn == 3) | (nn == 4)), "REJECTED_PILOT_N", g)
            for i, ni in enumerate(nn.tolist()):
                if ni < 4: ioq.require(arrs[g][i, ni:, :].tobytes() == b"\x00" * int((4-ni)*24), "REJECTED_NONZERO_PADDING", g)
        grid = arrs["source_grid"]; tri = arrs["source_triangles"]; B = int(tri.shape[0])
        ioq.require(grid.ndim == 3 and grid.shape[2] == 3 and grid.dtype.str == "<f8" and np.all(np.isfinite(grid)), "REJECTED_PILOT_GRID", "grid")
        ioq.require(tri.ndim == 2 and tri.shape[1] == 3 and tri.dtype.str in ("<i4","<i8"), "REJECTED_PILOT_TRIANGLES", "tri")
        ioq.require(B == int(spec["faces"]["bed"]), "REJECTED_PILOT_GRID_BOUND", "B == faces.bed")
        ioq.require(int(grid.shape[0]) >= 2 and int(grid.shape[1]) >= 2 and int(grid.shape[0])*int(grid.shape[1]) <= 3*B, "REJECTED_PILOT_GRID_BOUND", "grid bound")
        ioq.require(np.all((tri >= 0) & (tri < int(grid.shape[0])*int(grid.shape[1]))), "REJECTED_PILOT_TRIANGLE_RANGE", "tri range")
        r_ = tri // int(grid.shape[1]); co = tri % int(grid.shape[1])
        if B: ioq.require(np.array_equal(arrs["body_row_min"].astype(np.int64), r_.min(axis=1)) and np.array_equal(arrs["body_row_max"].astype(np.int64), r_.max(axis=1)) and np.array_equal(arrs["body_col_min"].astype(np.int64), co.min(axis=1)) and np.array_equal(arrs["body_col_max"].astype(np.int64), co.max(axis=1)), "REJECTED_PILOT_EXTREMA", "extrema")
        for nm in ("body_row_min","body_row_max","body_col_min","body_col_max"): ioq.require(arrs[nm].shape == (B,) and arrs[nm].dtype.str in ("<i4","<i8"), "REJECTED_PILOT_EXTREMA", nm)
        ioq.require(arrs["source_category"].dtype.str == "<U9", "REJECTED_CATEGORY_DTYPE", "U9")
        vals = [str(x) for x in arrs["source_category"].tolist()]
        ioq.require(all(v in ("BODY","CAP_START","CAP_END") for v in vals), "REJECTED_SOURCE_CATEGORY_UNKNOWN", "cat")
        ioq.require(sum(int(v) for v in spec.get("source_regions", {}).values()) == B, "REJECTED_CATEGORY_COUNT", "regions sum")
        for k, v in spec.get("source_regions", {}).items(): ioq.require(vals.count(k) == int(v), "REJECTED_CATEGORY_COUNT", k)
        for nm in ("npz_start","cap_before","cap_after"): ioq.require(arrs[nm].shape == () and arrs[nm].dtype.str == "<i4", "REJECTED_PILOT_SCALAR", nm)
        ioq.require(int(arrs["npz_start"]) >= 0, "REJECTED_NPZ_START_NEGATIVE", "npz_start")
        ioq.require(int(arrs["cap_before"]) in (0, 8) and int(arrs["cap_after"]) in (0, 8), "REJECTED_CAPS", "caps")
        ioq.require(int(grid.shape[0]) - int(arrs["cap_before"]) - int(arrs["cap_after"]) >= 2, "REJECTED_CAPS_REMOVE_BODY", "body")
        bf = arrs["bed_source_face"]; ioq.require(bf.shape == (B,) and bf.dtype.str == "<i4" and sorted(int(x) for x in bf.tolist()) == list(range(B)), "REJECTED_BED_SOURCE_FACE_PERMUTATION", "permutation")
        npz_src[rel]["members"] = pmeta; member_count += len(pmeta)
        pilots.append({"model": spec["model"], "model_index": mi, "instance_id": iid, "site": spec["site"], "archive": rel, "pose_row": int(rows[0]), "world_frame": "ALREADY_WORLD_UNCERTIFIED", "arrays": {m["name"]: m["data_sha256"] for m in pmeta}, "categories": {k: vals.count(k) for k in sorted(set(vals))}, "historical_checks": spec.get("checks", {})})
        del arrs, pmeta
    for a in c["arrays"]: sources.append(npz_src[a["relative"]])
    coverage = {"source_models": len(catalog), "prototype_models": len(meta_models) + len(proxy_only), "proxy_only_models": len(proxy_only), "vegetation_models_not_saved": len(not_saved), "instances": int(len(ids)), "prototype_faces": int(len(meta_arr)), "roadway": int(np.sum(meta_arr["kind"]==0)), "water_visual": int(np.sum(meta_arr["kind"]==1)), "conditional_proxy": int(np.sum(meta_arr["kind"]==2)), "ambiguous": amb, "degenerate": deg, "proxy_paths": len(proxy_paths), "pilot_models": len(pilots), "human_resolved": 0, "member_count": int(member_count)}
    for k in ("source_models","prototype_models","proxy_only_models","vegetation_models_not_saved","instances","prototype_faces","roadway","water_visual","conditional_proxy","ambiguous","degenerate","proxy_paths","pilot_models","human_resolved"):
        ioq.require(coverage[k] == int(exp[k]), "REJECTED_COVERAGE", k)
    return {"schema": "q03b-saved-scene-binding-report-v1", "contract_sha256": csha, "status": "VERIFIED_SAVED_SCENE_BINDING_ONLY", "claims": dict(CLAIMS), "coverage": coverage, "sources": sources, "models": models, "pilots": pilots, "proxy_routes": [{"root_model": r["root_model"], "slots": r["slots"], "source_model": r["source_model"], "engine_binding": "UNKNOWN", "section_index": "UNKNOWN"} for r in proxy_paths], "limitations": ["no native acceptance", "no current precedence", "no exposure evaluation", "no globally complete faces", "no geometry repair", "human_resolved=0", "C1=NOT_REVIEWED", "world frame not certified"]}
def verify(contract, contract_sha, report_path, output):
    out = new_output(output)
    try:
        raw = read_snapshot(report_path, 33554432); report = parse_json(raw, "report")
        req_keys(report, REPORT_KEYS, "REJECTED_UNKNOWN_KEY", "new report")
        ioq.require(report["status"] == "VERIFIED_SAVED_SCENE_BINDING_ONLY", "REJECTED_REPORT_STATUS", "status")
        ioq.require(report["claims"] == CLAIMS, "REJECTED_CLAIM_FIELD", "claims")
        expected = rebuild(contract, contract_sha); strict_equal(report, expected)
        atomic_write_json(out, "report.json", report); return 0
    except Reject as e: atomic_write_json(out, "failure.json", failure_obj(e)); return 1
    except Inconclusive as e: atomic_write_json(out, "failure.json", failure_obj(e)); return 2
    except Exception as e:
        exc = Inconclusive("INCONCLUSIVE_SOURCE_IO", f"{type(e).__name__}: {e}"); atomic_write_json(out, "failure.json", failure_obj(exc)); return 2
def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--contract", required=True); ap.add_argument("--contract-sha", required=True); ap.add_argument("--report", required=True); ap.add_argument("--output", required=True)
    a = ap.parse_args(argv); return verify(a.contract, a.contract_sha, a.report, a.output)
if __name__ == "__main__": raise SystemExit(main())
