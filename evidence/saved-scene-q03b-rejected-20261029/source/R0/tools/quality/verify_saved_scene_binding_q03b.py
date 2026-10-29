"""Q03B consumer: independent semantic walker.

Shares only saved_scene_io_q03b I/O/digest primitives with the producer.
It does not import the producer, its checks, META guards or report builder,
and re-derives the expected report from pinned sources itself.
"""
from __future__ import annotations
import argparse, sys
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
GROUPS = ["bed","water","unknown","road_bed","road_water","road_unknown"]

def strict_equal(a, b, path="$"):
    if type(a) is not type(b): raise Reject("REJECTED_STRICT_TYPE", f"{path}: {type(a).__name__} != {type(b).__name__}")
    if isinstance(a, dict):
        ioq.require(set(a) == set(b), "REJECTED_UNKNOWN_KEY", f"{path} keys differ")
        for k in a: strict_equal(a[k], b[k], path + "." + str(k))
    elif isinstance(a, list):
        ioq.require(len(a) == len(b), "REJECTED_STRICT_LENGTH", path)
        for i, (x, y) in enumerate(zip(a, b)): strict_equal(x, y, f"{path}[{i}]")
    else:
        ioq.require(a == b, "REJECTED_REPORT_MISMATCH", f"{path}: {a!r} != {b!r}")
def norm(s):
    t = str(s).replace("\\", "/").strip("/").lower()
    ioq.require(bool(t) and all(p not in ("", ".", "..") for p in t.split("/")), "REJECTED_NAME", s)
    return t
def rebuild(contract_path, external_sha):
    data = contract_bytes(contract_path, external_sha); csha = sha256_bytes(data); c = parse_json(data, "contract")
    ioq.require(c.get("schema") == "q03b-saved-scene-binding-r1", "REJECTED_CONTRACT_SCHEMA", "schema")
    ioq.require(c.get("claims") == CLAIMS, "REJECTED_CLAIM_FIELD", "claims")
    lim = c["limits"]; exp = c["expected"]; pins = c["pins"]
    catalog = sections = None; proxy_paths = None; surface_inputs = {}; pilot_inputs = {}
    sources = []
    for k, pin in pins.items():
        raw = read_snapshot(pin["path"], lim.get("json_bytes", 16777216)); check_pin(raw, pin, k)
        obj = parse_json(raw, k); base = k.rsplit("/", 1)[-1]
        if base == "model-catalog.json": catalog = obj
        elif base == "model-sections.json": sections = obj
        elif base == "proxy-paths.json": proxy_paths = obj
        elif base == "inputs.json" and "pilot" in k: pilot_inputs = obj
        elif base == "inputs.json": surface_inputs = obj
        sources.append({"path": str(pin["path"]), "sha256": pin["sha256"], "bytes": int(pin["bytes"]), "kind": "json", "members": []})
    ioq.require(isinstance(catalog, list) and isinstance(sections, list) and isinstance(proxy_paths, list), "REJECTED_METADATA_SCHEMA", "lists")
    if surface_inputs: req_keys(surface_inputs, {"source_pins","discovery_artifacts","script_sha256","reader"}, "REJECTED_METADATA_FIELD", "surface inputs")
    if pilot_inputs: req_keys(pilot_inputs, {"pins","script_sha256"}, "REJECTED_METADATA_FIELD", "pilot inputs")
    by_path = {str(p["path"]): p["sha256"] for p in pins.values()} | {str(a["path"]): a["sha256"] for a in c["arrays"]}
    for k, v in (pilot_inputs.get("pins", {}) if isinstance(pilot_inputs, dict) else {}).items():
        if str(k) in by_path: ioq.require(v == by_path[str(k)], "REJECTED_EPOCH_WRONG_POSE_PIN", str(k))
    epoch = c.get("epoch", {})
    for k, v in (surface_inputs.get("source_pins", {}) if isinstance(surface_inputs, dict) else {}).items():
        lk = str(k).lower()
        if "wrp" in lk and "compiled" in lk: ioq.require(v == epoch.get("wrp_compiled"), "REJECTED_EPOCH_WRONG", k)
        if "pilot" in lk and lk.endswith(".pbo"): ioq.require(v == epoch.get("pilot_pbo"), "REJECTED_EPOCH_WRONG_PBO", k)
        if str(k) in by_path: ioq.require(v == by_path[str(k)], "REJECTED_EPOCH_LINK", str(k))
    sec_by = {int(r["index"]): r for r in sections}
    store = {}; pilots_store = {}; member_count = 0
    for a in c["arrays"]:
        raw = read_snapshot(a["path"], lim.get("npz_stored_bytes", 16777216)); check_pin(raw, a, a["relative"])
        sch = c["npz_schemas"][a["kind"]]
        if a["kind"] == "pilot":
            mem = [g + s for g in GROUPS for s in ("", "_n", "_flags", "_source_ids")] + list(sch.get("extra_members", []))
            arrs, meta = load_npz(raw, mem, lim, a["relative"]); pilots_store[a["relative"]] = (arrs, meta)
        else:
            mem = sch["members"] if "members" in sch else c["npz_schemas"]["instances"]["members"]
            arrs, meta = load_npz(raw, mem, lim, a["relative"]); store[a["kind"]] = arrs
        member_count += len(meta); sources.append({"path": str(a["path"]), "sha256": a["sha256"], "bytes": int(a["bytes"]), "kind": "npz", "members": meta})
    meta_arr = store["prototypes"]["meta"]
    ioq.require(meta_arr.dtype.itemsize == 35, "REJECTED_META_ITEMSIZE", "35")
    ioq.require(not meta_arr.dtype.hasobject, "REJECTED_NPY_OBJECT", "meta")
    # Own semantic guards, re-derived here (not imported).
    ioq.require(np.all(meta_arr["face"] >= 0), "REJECTED_SOURCE_FACE_RANGE", "face")
    limap = {}; secmap = {}
    for idx, row in sec_by.items():
        for lod in row.get("lods", []):
            limap[(idx, int(lod["index"]))] = int(lod["faces"]); secmap[(idx, int(lod["index"]))] = {int(s["index"]) for s in lod.get("sections", [])}
    ioq.require(all(int(f) < limap.get((int(s), int(l)), -1) for s, l, f in zip(meta_arr["source_model"].tolist(), meta_arr["lod"].tolist(), meta_arr["face"].tolist())), "REJECTED_SOURCE_FACE_RANGE", "face<lod.faces")
    ioq.require(all(int(s2) in secmap.get((int(s), int(l)), set()) for s, l, s2 in zip(meta_arr["source_model"].tolist(), meta_arr["lod"].tolist(), meta_arr["section"].tolist())), "REJECTED_SOURCE_SECTION_RANGE", "section")
    ioq.require(np.all(meta_arr["proxy"][meta_arr["kind"] < 2] == -1), "REJECTED_PROXY_SENTINEL", "sentinel")
    ins, sel = store["instances"], store["selected"]
    for col in ("ids", "model_index", "matrix"):
        ioq.require(ins[col].dtype == sel[col].dtype and ins[col].shape == sel[col].shape and ins[col].tobytes(order="C") == sel[col].tobytes(order="C"), "REJECTED_SELECTED_MISMATCH", col)
    ids = ins["ids"].astype(np.int64); midx = ins["model_index"].astype(np.int64)
    ioq.require(len(set(ids.tolist())) == len(ids), "REJECTED_DUPLICATE_INSTANCE_ID", "ids")
    cat_set = {int(r["index"]) for r in catalog}; by_idx = {int(r["index"]): r for r in catalog}
    ioq.require(set(midx.tolist()) <= cat_set, "REJECTED_MISMATCHED_INSTANCE_MODEL", "model_index")
    meta_models = {int(x) for x in np.unique(meta_arr["model"]).tolist()}; meta_src = {int(x) for x in np.unique(meta_arr["source_model"]).tolist()}
    ioq.require(meta_src == set(sec_by), "REJECTED_META_SOURCE_SET", "source set")
    proxy_only = sorted(meta_src - cat_set); not_saved = sorted(cat_set - meta_models)
    mdl = meta_arr["model"].astype(np.int64); ranges = {}; start = 0
    for i in range(1, len(mdl) + 1):
        if i == len(mdl) or mdl[i] != mdl[start]: ranges.setdefault(int(mdl[start]), []).append([int(start), int(i)]); start = i
    models = []
    for idx in sorted(cat_set | set(proxy_only)):
        if idx in by_idx:
            row = by_idx[idx]; saved = idx in meta_models; layers = []
            if saved:
                ks = sorted({int(x) for x in np.unique(meta_arr["kind"][mdl == idx]).tolist()})
                layers = ["roadway" if k == 0 else "water_visual" if k == 1 else "conditional_proxy" for k in ks]
            models.append({"index": idx, "name": row["name"], "group": row["group"], "instance_count": int(np.sum(midx == idx)), "layers": layers, "frame": "RAW_UNCERTIFIED" if saved else "NOT_SAVED", "prototype_ranges": ranges.get(idx, []), "status": "SAVED" if saved else "NOT_SAVED"})
        else:
            models.append({"index": idx, "name": sec_by[idx]["name"], "group": None, "instance_count": 0, "layers": ["conditional_proxy"] if idx in meta_models or idx in meta_src else [], "frame": "CONDITIONAL", "prototype_ranges": ranges.get(idx, []), "status": "PROXY_ONLY"})
    specs = c["pilot_specs"]; pilots = []
    ioq.require(len(specs) == int(exp["pilot_models"]), "REJECTED_PILOT_COUNT_ZERO", "pilots")
    for spec in specs:
        rows = np.where((midx == int(spec["model_index"])) & (ids == int(spec["instance_id"])))[0]
        ioq.require(len(rows) == 1, "REJECTED_PILOT_TWO_INSTANCES", str(spec.get("model")))
        key = next((k for k in pilots_store if k.endswith(spec["file"].rsplit("/", 1)[-1]) or k.endswith(spec["file"])), None)
        ioq.require(key is not None, "REJECTED_PILOT_ARCHIVE", spec["file"])
        arrs, pmeta = pilots_store[key]
        for g in GROUPS:
            ioq.require(arrs[g].shape == (int(spec["faces"][g]), 4, 3), "REJECTED_PILOT_SHAPE", g)
            nn = arrs[g + "_n"].astype(np.int64)
            ioq.require(np.all((nn == 3) | (nn == 4)), "REJECTED_PILOT_N", g)
            for i, ni in enumerate(nn.tolist()):
                if ni < 4: ioq.require(arrs[g][i, ni:, :].tobytes() == b"\x00" * int((4-ni)*24), "REJECTED_NONZERO_PADDING", g)
        grid = arrs["source_grid"]; tri = arrs["source_triangles"]; B = int(tri.shape[0])
        ioq.require(int(grid.shape[0]) >= 2 and int(grid.shape[1]) >= 2 and int(grid.shape[0])*int(grid.shape[1]) <= 3*B, "REJECTED_PILOT_GRID_BOUND", "grid")
        ioq.require(str(arrs["source_category"].dtype) == "<U9", "REJECTED_CATEGORY_DTYPE", "U9")
        vals = [str(x) for x in arrs["source_category"].tolist()]
        ioq.require(all(v in ("BODY","CAP_START","CAP_END") for v in vals), "REJECTED_SOURCE_CATEGORY_UNKNOWN", "cat")
        for k, v in spec.get("source_regions", {}).items(): ioq.require(vals.count(k) == int(v), "REJECTED_CATEGORY_COUNT", k)
        ioq.require(int(arrs["npz_start"]) >= 0, "REJECTED_NPZ_START_NEGATIVE", "npz_start")
        ioq.require(int(arrs["cap_before"]) in (0, 8) and int(arrs["cap_after"]) in (0, 8), "REJECTED_CAPS", "caps")
        ioq.require(int(grid.shape[0]) - int(arrs["cap_before"]) - int(arrs["cap_after"]) >= 2, "REJECTED_CAPS_REMOVE_BODY", "body")
        r_ = tri // int(grid.shape[1]); co = tri % int(grid.shape[1])
        ioq.require(np.array_equal(arrs["body_row_min"].astype(np.int64), r_.min(axis=1)) and np.array_equal(arrs["body_row_max"].astype(np.int64), r_.max(axis=1)) and np.array_equal(arrs["body_col_min"].astype(np.int64), co.min(axis=1)) and np.array_equal(arrs["body_col_max"].astype(np.int64), co.max(axis=1)), "REJECTED_PILOT_EXTREMA", "extrema")
        pilots.append({"model": spec["model"], "model_index": int(spec["model_index"]), "instance_id": int(spec["instance_id"]), "site": spec["site"], "archive": key, "pose_row": int(rows[0]), "world_frame": "ALREADY_WORLD_UNCERTIFIED", "arrays": {m["name"]: m["data_sha256"] for m in pmeta}, "categories": {k: vals.count(k) for k in sorted(set(vals))}, "historical_checks": spec.get("checks", {})})
    ioq.require(len(proxy_paths) == int(exp["proxy_paths"]), "REJECTED_PROXY_COUNT_DISAGREEMENT", "proxy_paths")
    for r in proxy_paths:
        seen = set()
        for pair in r["slots"]:
            mi, slot = int(pair[0]), int(pair[1])
            ioq.require(mi not in seen, "REJECTED_PROXY_ROUTE_CYCLE", "cycle"); seen.add(mi)
            ioq.require(mi in sec_by and 0 <= slot < len(sec_by[mi].get("proxies", [])), "REJECTED_PROXY_MISSING_SOURCE", "slot")
    coverage = {"source_models": len(catalog), "prototype_models": len(meta_models) + len(proxy_only), "proxy_only_models": len(proxy_only), "vegetation_models_not_saved": len(not_saved), "instances": int(len(ids)), "prototype_faces": int(len(meta_arr)), "roadway": int(np.sum(meta_arr["kind"]==0)), "water_visual": int(np.sum(meta_arr["kind"]==1)), "conditional_proxy": int(np.sum(meta_arr["kind"]==2)), "ambiguous": int(sum(sum(int(v) for v in s.get("ambiguous_faces", {}).values()) for s in specs)), "degenerate": 0, "proxy_paths": len(proxy_paths), "pilot_models": len(pilots), "human_resolved": 0, "member_count": int(member_count)}
    return {"schema": "q03b-saved-scene-binding-report-v1", "contract_sha256": csha, "status": "VERIFIED_SAVED_SCENE_BINDING_ONLY", "claims": dict(CLAIMS), "coverage": coverage, "sources": sources, "models": models, "pilots": pilots, "proxy_routes": [{"root_model": r["root_model"], "slots": r["slots"], "source_model": r["source_model"], "engine_binding": "UNKNOWN", "section_index": "UNKNOWN"} for r in proxy_paths], "limitations": ["no native acceptance", "no current precedence", "no exposure evaluation", "no globally complete faces", "no geometry repair", "human_resolved=0", "C1=NOT_REVIEWED", "world frame not certified"]}
def verify(contract, contract_sha, report_path, output):
    out = new_output(output)
    try:
        raw = read_snapshot(report_path, 33554432)
        report = parse_json(raw, "report")
        req_keys(report, REPORT_KEYS, "REJECTED_UNKNOWN_KEY", "new report")
        ioq.require(report["status"] == "VERIFIED_SAVED_SCENE_BINDING_ONLY", "REJECTED_REPORT_STATUS", "status")
        ioq.require(report["claims"] == CLAIMS, "REJECTED_CLAIM_FIELD", "claims")
        expected = rebuild(contract, contract_sha)
        strict_equal(report, expected)
        atomic_write_json(out, "report.json", report)
        return 0
    except Reject as e:
        atomic_write_json(out, "failure.json", failure_obj(e)); return 1
    except Inconclusive as e:
        atomic_write_json(out, "failure.json", failure_obj(e)); return 2
    except Exception as e:
        exc = Inconclusive("INCONCLUSIVE_SOURCE_IO", f"{type(e).__name__}: {e}"); atomic_write_json(out, "failure.json", failure_obj(exc)); return 2
def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--contract", required=True); ap.add_argument("--contract-sha", required=True); ap.add_argument("--report", required=True); ap.add_argument("--output", required=True)
    a = ap.parse_args(argv); return verify(a.contract, a.contract_sha, a.report, a.output)
if __name__ == "__main__": raise SystemExit(main())
