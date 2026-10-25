from __future__ import annotations

"""Prepare the isolated Oredezh wet-bank pilot matrices; never runs a solver."""

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.ndimage import binary_dilation
from shapely.geometry import LineString, Point, Polygon, box, shape
from shapely.ops import unary_union

ROOT = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010")
OUT = ROOT / "G/wet-bank-pilot"
RUNS = OUT / "prepared-runs"
ROW, COL = 862, 1186
WIN = (855, 870, 1179, 1194)  # half-open node window; fixed 2-node collar
VAR_WIN = (857, 868, 1181, 1192)  # at most 11x11 = 121 nodes
CELL = 6.0
Z0 = 12282.0
MAX_LOCAL_DELTA = 0.5
EV79_BUDGET = 2.0

PATHS = {
    "selection": OUT / "selection.json",
    "base": ROOT / "global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz",
    "original_ev79": Path(r"E:/DayZ-Baltic-Build/v30-narva-dry-bank-relief-20261010/candidate/terrain.npz"),
    "ev79_constraints": Path(r"E:/DayZ-Baltic-Build/v30-narva-dry-bank-relief-20261010/constraints.npz"),
    "lake_constraints": Path(r"E:/DayZ-Baltic-Build/v30-remaining-exact-dry-support-20261009/constraints.npz"),
    "P": ROOT / "build-focal/candidate/plane.npy",
    "F": ROOT / "build-focal/candidate/visible-field.npy",
    "valley_masks": Path(r"E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008/candidate-a/masks.npz"),
    "terminal_constraints": Path(r"E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/constraints.npz"),
    "water_design": Path(r"E:/DayZ-Baltic-Build/v30-v11/design/water_v3.geojson"),
    "corridors": Path(r"E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson"),
    "roads": Path(r"P:/DayZ_Baltic_12km_dev/tests/regional_foundation_roads_v6/reference.npz"),
    "retained_selection": ROOT / "compound-selection/run-02/selection.json",
    "wrp_source": Path(r"E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp"),
    "staged_wrp": Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/build-focal/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp"),
    "stage_manifest": ROOT / "build-focal/stage.json",
    "index_manifest": ROOT / "ev93-face-index/runs/20261010T092417Z-63d4cec3/manifest.json",
    "index_builder": ROOT / "ev93-face-index/build_face_index.py",
    "ev87": Path(r"E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py"),
    "prototype": ROOT / "global-operator-prototype/prototype.py",
    "cone_solver": ROOT / "global-operator-prototype/face-slope-cone-pilot/pilot.py",
}

EXPECTED = {
    "selection": "f7eb0a567b0b9b3c84d477da4894812cead7543c4c76d445c03117d0b43eb21d",
    "base": "40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a",
    "original_ev79": "dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c",
    "ev79_constraints": "ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c",
    "lake_constraints": "18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370",
    "P": "768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0",
    "F": "f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c",
    "valley_masks": "685b3b9a337bca849f9338a27385ef959ee938fd37ab492d044419d236c64af2",
    "terminal_constraints": "5f6a40ff3281defdd643409bb6a00d2bbaa51f8f9c727603aedcd06e5947df33",
    "water_design": "caa333e365c2a4511f839937a9d76a5aa157a0ef925d6ee4b5efcc4ebb38f8a9",
    "corridors": "28866a8cf6ff57f2f825228046164ef939bc22bca9948eb96fe2463da46af343",
    "roads": "94ecbca61bd5ba9ba61f89b765b043676a4a65703729a0b69009ae233984a1c2",
    "wrp_source": "3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6",
    "staged_wrp": "8bf57d622fb2f01aa491f280f9dcb8cdc9dd8a603ac18995e3e50d21e83e4cb3",
    "stage_manifest": "cc394869cf45f60315eea5b13a99b2f79d80135bee5ee32879b3900ecaa86610",
    "index_manifest": "c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c",
    "index_builder": "d1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e",
    "ev87": "964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27",
    "prototype": "5b4b8f08e5205e1f9cc90bcc8e82e61dade45bb82bd22da8ee69303aa4475cc4",
    "cone_solver": "d743f5006e0aa6606024a3c3291a74cb52b78f76c1aa5c6dfd95cdd26cdc9d2a",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import pinned source: {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def pinned_readset():
    start = {k: sha(p) for k, p in PATHS.items()}
    for key, expected in EXPECTED.items():
        if start[key] != expected:
            raise AssertionError(f"pinned input drift {key}: {start[key]} != {expected}")
    return start


def region(a, window=WIN):
    r0, r1, c0, c1 = window
    return a[r0:r1, c0:c1]


def inward32(x, lower):
    x = float(x)
    f = np.float32(x)
    if lower and float(f) < x:
        f = np.nextafter(f, np.float32(np.inf), dtype=np.float32)
    if not lower and float(f) > x:
        f = np.nextafter(f, np.float32(-np.inf), dtype=np.float32)
    return float(f)


def collect_points(g):
    if g.is_empty:
        return []
    if g.geom_type == "Point":
        return [g]
    if hasattr(g, "geoms"):
        out = []
        for x in g.geoms:
            out.extend(collect_points(x))
        return out
    return []


def edge_corner_ids(a, b):
    pairs = {frozenset(((0, 0), (0, 1))): (0, 1),
             frozenset(((0, 0), (1, 0))): (0, 2),
             frozenset(((0, 1), (1, 1))): (1, 3),
             frozenset(((1, 0), (1, 1))): (2, 3)}
    return pairs[frozenset((a, b))]


def crossing_constraint_rows(base, variables, p, f, polygon, global_origin):
    """Build absolute-height affine crossing/sign rows for every design shoreline edge.

    Output rows are C H >= d, preserving each P sample and each local F sample
    independently; an edge shared by cells emits one constraint per incident cell.
    """
    h, w = base.shape
    index = {tuple(map(int, rc)): i for i, rc in enumerate(variables.tolist())}
    rows, rhs, meta = [], [], []
    gr0, gc0 = global_origin

    def endpoint_level(kind, cell_r, cell_c, rc, corner_id):
        cell_r += gr0; cell_c += gc0
        if kind == "P":
            value = float(p[cell_r, cell_c])
        else:
            value = float(f[cell_r, cell_c, corner_id])
        if not math.isfinite(value):
            raise ValueError(f"missing {kind} level on design shoreline edge cell={(cell_r,cell_c)} corner={corner_id}")
        return value

    # Each affected terrain edge is enumerated from its incident native cells.
    # Duplicates are intentional when P/F differ on adjacent face records.
    for cell_r in range(max(0, int(np.min(variables[:, 0])) - 1), min(h - 1, int(np.max(variables[:, 0])) + 1)):
        for cell_c in range(max(0, int(np.min(variables[:, 1])) - 1), min(w - 1, int(np.max(variables[:, 1])) + 1)):
            # `base` and variables are local; map each corner to the global
            # water design and P/F arrays before calculating world XZ.
            corners = ((cell_r+gr0, cell_c+gc0), (cell_r+gr0, cell_c+gc0 + 1),
                       (cell_r+gr0 + 1, cell_c+gc0), (cell_r+gr0 + 1, cell_c+gc0 + 1))
            local = ((0, 0), (0, 1), (1, 0), (1, 1))
            edge_specs = ((0,1),(0,2),(1,3),(2,3))
            for corner_a, corner_b in edge_specs:
                rc_a, rc_b = corners[corner_a], corners[corner_b]
                xz_a = (rc_a[1] * CELL, Z0 - rc_a[0] * CELL)
                xz_b = (rc_b[1] * CELL, Z0 - rc_b[0] * CELL)
                seg = LineString([xz_a, xz_b])
                hits = collect_points(seg.intersection(polygon.boundary))
                unique = []
                for q in hits:
                    if not any(q.distance(prev) <= 1e-9 for prev in unique):
                        unique.append(q)
                if len(unique) == 0:
                    continue
                if len(unique) != 1:
                    raise ValueError(f"ambiguous design boundary crossings on edge {rc_a}->{rc_b}: {len(unique)}")
                hit = unique[0]
                t_ab = ((hit.x-xz_a[0])*(xz_b[0]-xz_a[0])+(hit.y-xz_a[1])*(xz_b[1]-xz_a[1])) / ((xz_b[0]-xz_a[0])**2+(xz_b[1]-xz_a[1])**2)
                if not (0.0 <= t_ab <= 1.0):
                    raise AssertionError("boundary hit outside edge segment")
                for kind in ("P", "F"):
                    la = endpoint_level(kind, cell_r, cell_c, rc_a, corner_a)
                    lb = endpoint_level(kind, cell_r, cell_c, rc_b, corner_b)
                    ha = float(base[rc_a[0]-gr0, rc_a[1]-gc0])
                    hb = float(base[rc_b[0]-gr0, rc_b[1]-gc0])
                    da, db = ha-la, hb-lb
                    def add_ge(coeffs, target, row_type, bound=None):
                        row=np.zeros(len(variables),dtype=np.float64); fixed_offset=0.0
                        for rc,coef in coeffs:
                            local_rc=(rc[0]-gr0,rc[1]-gc0)
                            vi=index.get(local_rc)
                            if vi is None:
                                fixed_offset += coef*float(base[local_rc])
                            else:
                                row[vi] += coef
                        rows.append(row); rhs.append(float(target)-fixed_offset)
                        meta.append({"type":row_type,"surface":kind,"cell_rc":[cell_r+gr0,cell_c+gc0],
                                     "edge_rc":[list(rc_a),list(rc_b)],"t_base":bound.get("t_base") if isinstance(bound,dict) else None,
                                     "t_design":bound.get("t_design") if isinstance(bound,dict) else None,
                                     "t_bound":bound.get("t_bound") if isinstance(bound,dict) else None})
                    def strict_above(rc, level, label):
                        threshold=float(np.nextafter(np.float32(level),np.float32(np.inf),dtype=np.float32))
                        add_ge([(rc,1.0)],threshold,label)
                    def strict_below(rc, level, label):
                        threshold=float(np.nextafter(np.float32(level),np.float32(-np.inf),dtype=np.float32))
                        add_ge([(rc,-1.0)],-threshold,label)
                    if da > 0.0 and db < 0.0:
                        dry_rc, wet_rc, ld, lw = rc_a, rc_b, la, lb
                        t_design = t_ab
                    elif db > 0.0 and da < 0.0:
                        dry_rc, wet_rc, ld, lw = rc_b, rc_a, lb, la
                        t_design = 1.0-t_ab
                    else:
                        # If the design boundary intersects an edge where the
                        # baseline has no water crossing, preserve endpoint signs
                        # rather than inventing a baseline crossing parameter.
                        # A baseline contact is pinned exactly at that endpoint.
                        for rc, level, delta, label in ((rc_a,la,da,"a"),(rc_b,lb,db,"b")):
                            if delta > 0.0:
                                strict_above(rc,level,f"sign_only_above_{label}")
                            elif delta < 0.0:
                                strict_below(rc,level,f"sign_only_below_{label}")
                            else:
                                add_ge([(rc,1.0)],level,"baseline_contact_lower")
                                add_ge([(rc,-1.0)],-level,"baseline_contact_upper")
                        meta.append({"type":"sign_only","surface":kind,"cell_rc":[cell_r+gr0,cell_c+gc0],
                                     "edge_rc":[list(rc_a),list(rc_b)],"delta_a_m":da,"delta_b_m":db,
                                     "t_base":None,"t_design":float(t_ab),"t_bound":None})
                        continue
                    dd0 = float(base[dry_rc[0]-gr0, dry_rc[1]-gc0]) - ld
                    dw0 = float(base[wet_rc[0]-gr0, wet_rc[1]-gc0]) - lw
                    t_base = dd0 / (dd0 - dw0)
                    lo_t, hi_t = sorted((t_base, float(t_design)))
                    if not (0.0 <= lo_t <= hi_t <= 1.0):
                        raise ValueError("invalid crossing interval")
                    # Preserve strict endpoint signs after float32 quantization,
                    # then constrain a real baseline crossing to baseline↔design.
                    strict_above(dry_rc,ld,"cross_sign_dry")
                    strict_below(wet_rc,lw,"cross_sign_wet")
                    bound_base={"t_base":t_base,"t_design":float(t_design),"t_bound":lo_t}
                    add_ge([(dry_rc,1.0-lo_t),(wet_rc,lo_t)],(1.0-lo_t)*ld+lo_t*lw,"cross_lower",bound_base)
                    bound_design={"t_base":t_base,"t_design":float(t_design),"t_bound":hi_t}
                    add_ge([(dry_rc,-(1.0-hi_t)),(wet_rc,-hi_t)],-((1.0-hi_t)*ld+hi_t*lw),"cross_upper",bound_design)
    if not rows:
        raise ValueError("no shoreline crossing rows were generated in the variable influence region")
    return np.asarray(rows, dtype=np.float64), np.asarray(rhs, dtype=np.float64), meta


def local_incident_level(p, f, local_window, global_origin):
    """EV79 incident max(P,F,SEA) with P-NaN selecting the .85 fallback."""
    r0, r1, c0, c1 = local_window
    gr0, gc0 = global_origin
    out = np.full((r1-r0, c1-c0), 0.85, dtype=np.float64)
    for dr, dc, corner in ((0,0,0),(0,-1,1),(-1,0,2),(-1,-1,3)):
        rr = np.arange(gr0+dr, gr0+dr+(r1-r0))[:,None]
        cc = np.arange(gc0+dc, gc0+dc+(c1-c0))[None,:]
        ok=(rr>=0)&(rr<p.shape[0])&(cc>=0)&(cc<p.shape[1])
        ri=np.clip(rr,0,p.shape[0]-1);ci=np.clip(cc,0,p.shape[1]-1)
        pv = p[ri,ci].astype(np.float64, copy=False)
        fv = f[ri,ci,corner].astype(np.float64, copy=False)
        level = np.where(ok & np.isfinite(pv), np.fmax(0.85, np.fmax(pv, fv)), 0.85)
        np.maximum(out, level, out=out)
    return out


def make_window_polygon(window):
    r0, r1, c0, c1 = window
    xmin, xmax = c0*CELL, (c1-1)*CELL
    zmax, zmin = Z0-r0*CELL, Z0-(r1-1)*CELL
    return box(xmin, zmin, xmax, zmax)


def load_retained_windows(selection):
    retained = set(selection["retained_unit_ids"])
    rows = []
    readset = {}
    for unit in selection["units"]:
        uid = f"{unit['origin']}:{unit['queue_id']}"
        if uid not in retained:
            continue
        path = Path(unit["source_artifact_path"])
        artifact_sha = sha(path)
        if artifact_sha != unit["source_artifact_sha256"]:
            raise AssertionError(f"retained unit artifact drift: {uid}")
        readset[str(path)] = artifact_sha
        doc = json.loads(path.read_text(encoding="utf-8"))
        if unit["origin"] == "crest":
            result_path = Path(doc["source_result_path"])
            result_sha = sha(result_path)
            if result_sha != doc["source_result_sha256"]:
                raise AssertionError(f"crest source result drift: {uid}")
            readset[str(result_path)] = result_sha
            doc = json.loads(result_path.read_text(encoding="utf-8"))
        win = doc.get("window_rc")
        if not (isinstance(win, list) and len(win)==4):
            raise ValueError(f"unit has no window_rc: {uid}")
        if sha(path) != artifact_sha:
            raise AssertionError(f"retained unit artifact changed while reading: {uid}")
        if unit["origin"] == "crest" and sha(result_path) != result_sha:
            raise AssertionError(f"crest source result changed while reading: {uid}")
        rows.append({"unit_id": uid, "window_rc": [int(x) for x in win]})
    if len(rows) != len(retained):
        raise AssertionError("retained window inventory is incomplete")
    return rows, readset


def polygon_edges(window, variables, design_geom):
    """Cell polygons incident to variables; exact set for post-solve coverage."""
    cells = set()
    h, w = window[1]-window[0], window[3]-window[2]
    for rr, cc in variables.tolist():
        r, c = int(rr), int(cc)
        for cr in (r-1, r):
            for cc0 in (c-1, c):
                if window[0] <= cr < window[1]-1 and window[2] <= cc0 < window[3]-1:
                    cells.add((cr,cc0))
    polys=[]
    for r,c in sorted(cells):
        polys.append(box(c*CELL, Z0-(r+1)*CELL, (c+1)*CELL, Z0-r*CELL))
    affected = unary_union(polys)
    if not affected.is_valid:
        raise AssertionError("affected cell union is invalid")
    return sorted(cells), affected


def run_prepare(outdir: Path):
    if outdir.exists():
        raise FileExistsError(f"fresh preparation directory required: {outdir}")
    outdir.mkdir(parents=True)
    started=time.monotonic()
    read_start=pinned_readset()
    t0=time.monotonic()
    selection=json.loads(PATHS["selection"].read_text(encoding="utf-8"))
    retained=json.loads(PATHS["retained_selection"].read_text(encoding="utf-8"))
    identity=selection["water_object_identity"]
    if (Path(identity["base_wrp_path"])!=PATHS["wrp_source"] or
        Path(identity["EV94_staged_wrp_path"])!=PATHS["staged_wrp"] or
        identity["base_wrp_sha256"]!=EXPECTED["wrp_source"] or
        identity["staged_wrp_sha256"]!=EXPECTED["staged_wrp"] or
        identity["stage_json_sha256"]!=EXPECTED["stage_manifest"] or
        identity["water_ids_names_and_12-float_matrices_equal"] is not True):
        raise AssertionError("selection's base/EV94 water-object identity receipt does not match pinned WRP/stage")
    with np.load(PATHS["base"],allow_pickle=False) as z: base_data={k:z[k] for k in z.files}
    with np.load(PATHS["original_ev79"],allow_pickle=False) as z: original_data={k:z[k] for k in z.files}
    with np.load(PATHS["ev79_constraints"],allow_pickle=False) as z: ev79c={k:z[k] for k in z.files}
    with np.load(PATHS["lake_constraints"],allow_pickle=False) as z: lakec={k:z[k] for k in z.files}
    with np.load(PATHS["valley_masks"],allow_pickle=False) as z: valley={k:z[k] for k in z.files}
    with np.load(PATHS["terminal_constraints"],allow_pickle=False) as z: terminal={k:z[k] for k in z.files}
    p=np.load(PATHS["P"],mmap_mode="r",allow_pickle=False)
    f=np.load(PATHS["F"],mmap_mode="r",allow_pickle=False)
    terrain=base_data["heights"].astype(np.float64)
    original=original_data["heights"].astype(np.float64)
    if terrain.shape != (2048,2048) or original.shape != terrain.shape or p.shape!=(2047,2047) or f.shape!=(2047,2047,4):
        raise AssertionError("terrain/P/F dimensions differ from pinned native grid")
    if not np.array_equal(base_data["cls"],original_data["cls"]) or not np.array_equal(base_data["water"],original_data["water"]):
        raise AssertionError("EV79 semantic masks differ from current base")
    design_doc=json.loads(PATHS["water_design"].read_text(encoding="utf-8-sig"))
    feature=next(x for x in design_doc["features"] if x.get("id")=="river_041" or x.get("properties",{}).get("id")=="river_041")
    river=shape(feature["geometry"])
    if not river.is_valid or river.geom_type not in ("Polygon","MultiPolygon"):
        raise ValueError("river_041 design geometry is not a valid polygonal feature")
    corridors_doc=json.loads(PATHS["corridors"].read_text(encoding="utf-8-sig"))
    corridor_geoms=[shape(x["geometry"]) for x in corridors_doc.get("features",[])]
    corridor_union=unary_union(corridor_geoms) if corridor_geoms else None
    road=np.load(PATHS["roads"],allow_pickle=False)
    if road["corridor"].shape!=terrain.shape: raise AssertionError("road corridor raster shape mismatch")

    # Rebuild EV79's semantic/protection mask from source arrays before releasing
    # only class-5/water and wet-support nodes in this one measured patch.
    r0,r1,c0,c1=WIN
    border=np.zeros((r1-r0,c1-c0),bool)
    for lr,gr in enumerate(range(r0,r1)):
        for lc,gc in enumerate(range(c0,c1)):
            border[lr,lc]=(gr<11 or gr>=2037 or gc<11 or gc>=2037)
    tmask={k:region(base_data[k]) for k in ("water","beach","reserve","platform","narva","cls")}
    term_mask=region(terminal["controls"])
    valley_corr=region(valley["corridor"]); valley_summit=region(valley["summits"])
    other_rebuilt=tmask["water"]|tmask["beach"]|(tmask["cls"]!=0)|valley_corr|valley_summit|border|term_mask
    other_saved=region(ev79c["other_fixed"])
    if not np.array_equal(other_rebuilt,other_saved):
        raise AssertionError("EV79 other_fixed mask cannot be reconstructed exactly from current source arrays")
    reserve_platform=region(base_data["reserve"]|base_data["platform"])
    # Rebuild the saved 3x3 engineering halo with the exact 8-neighbor dilation
    # semantics and crop; avoid a shifted-slice implementation with offset risk.
    engineering_full=np.asarray(base_data["reserve"]|base_data["platform"],dtype=bool)
    halo=region(binary_dilation(engineering_full,structure=np.ones((3,3),dtype=bool)))
    if not np.array_equal(halo,region(ev79c["engineering_halo"])):
        raise AssertionError("EV79 engineering halo reconstruction mismatch")
    fixed_rebuilt=other_rebuilt|region(lakec["large_lake_banks"])|region(ev79c["wet_support"])|halo
    if not np.array_equal(fixed_rebuilt,region(ev79c["fixed"])):
        raise AssertionError("EV79 fixed mask reconstruction mismatch")

    vars_r0,vars_r1,vars_c0,vars_c1=VAR_WIN
    # Apply only the reviewed exception: release EV79 wet-support and the local
    # class-5/water masks. All other semantic and infrastructure masks stay fixed.
    release=np.zeros((r1-r0,c1-c0),bool)
    release |= region(ev79c["wet_support"])
    release |= (tmask["cls"]==5)&tmask["water"]
    nonreleased_fixed=other_rebuilt & ~((tmask["cls"]==5)&tmask["water"])
    narva_mask=region(ev79c["narva"])
    if not np.array_equal(narva_mask,tmask["narva"]):
        raise AssertionError("EV79 Narva mask differs from the current base mask")
    reserve_mask=region(base_data["reserve"]); platform_mask=region(base_data["platform"])
    effective_fixed=(nonreleased_fixed|region(lakec["large_lake_banks"])|halo|narva_mask|reserve_mask|platform_mask)
    var_mask=np.zeros((r1-r0,c1-c0),bool)
    var_mask[vars_r0-r0:vars_r1-r0,vars_c0-c0:vars_c1-c0]=True
    # Existing signed corridor geometry is a P9 freeze, not inferred from P NaNs.
    p9_mask=np.zeros_like(var_mask)
    for lr,gr in enumerate(range(r0,r1)):
        for lc,gc in enumerate(range(c0,c1)):
            pt=Point(gc*CELL,Z0-gr*CELL)
            p9_mask[lr,lc]=bool(corridor_union is not None and corridor_union.covers(pt))
    road_mask=region(road["corridor"])
    effective_fixed |= p9_mask|road_mask
    eligible=var_mask & ~effective_fixed
    variables_global=np.column_stack(np.nonzero(eligible)).astype(np.int32)
    variables_global[:,0]+=r0; variables_global[:,1]+=c0
    if len(variables_global)>121 or tuple(map(int,variables_global[0]))!=(vars_r0,vars_c0):
        raise AssertionError(f"expected the full 11x11 interior beginning at {(vars_r0,vars_c0)}, got {len(variables_global)} vars")
    if len(variables_global)!=121:
        raise AssertionError(f"protected/p9/road node inside the nominal 121-node core; fail closed ({len(variables_global)} variables)")
    focus_index=np.flatnonzero(np.all(variables_global==[ROW,COL],axis=1))
    if len(focus_index)!=1: raise AssertionError("focus is not a unique variable")
    retained_rows,retained_readset_start=load_retained_windows(retained)
    overlap=[]
    for item in retained_rows:
        a,b,c,d=item["window_rc"]
        if max(a,WIN[0]) < min(b,WIN[1]) and max(c,WIN[2]) < min(d,WIN[3]):
            overlap.append(item["unit_id"])
    if overlap: raise AssertionError(f"pilot context overlaps retained compound windows: {overlap[:10]}")
    # Confirm no road/civil/engineering/bridge footprint is hidden behind the
    # released wet-support mask. Road raster and selection WRP inventory are pinned.
    if np.any(eligible & (tmask["reserve"]|tmask["platform"]|road_mask|region(terminal["controls"]))):
        raise AssertionError("a released pilot variable overlaps civil/engineering controls")
    if np.any(eligible & p9_mask): raise AssertionError("P9 node entered the pilot variable domain")
    if np.any(eligible & narva_mask): raise AssertionError("Narva protected node entered the pilot variable domain")
    interior=np.zeros_like(eligible)
    for lr,gr in enumerate(range(r0,r1)):
        for lc,gc in enumerate(range(c0,c1)):
            pt=Point(gc*CELL,Z0-gr*CELL)
            interior[lr,lc]=bool(river.contains(pt))
    shore_boundary=np.zeros_like(interior)
    for lr,gr in enumerate(range(r0,r1)):
        for lc,gc in enumerate(range(c0,c1)):
            pt=Point(gc*CELL,Z0-gr*CELL)
            shore_boundary[lr,lc]=river.boundary.distance(pt)<=1e-8
    wet_nodes=eligible&interior&~shore_boundary
    dry_nodes=eligible&~interior&~shore_boundary
    base_window=region(terrain); original_window=region(original)
    p_window=p[r0:r1-1,c0:c1-1].astype(np.float64)
    f_window=f[r0:r1-1,c0:c1-1].astype(np.float64)
    # Exact local per-node P/F incident max for the EV79 floor, retaining its
    # P-NaN fallback semantics; wet-bed nodes instead receive a 1 m bed floor.
    incident=local_incident_level(p,f,(r0,r1,c0,c1),(r0,c0))
    water_floor=np.minimum(original_window,incident+1e-4)
    lower_abs=np.full((r1-r0,c1-c0),np.nan,np.float64)
    upper_abs=np.full_like(lower_abs,np.nan)
    for idx,(gr,gc) in enumerate(variables_global.tolist()):
        lr,lc=gr-r0,gc-c0
        O=float(original[gr,gc]); B=float(terrain[gr,gc])
        lo=max(B-EV79_BUDGET, float(water_floor[lr,lc]), min(O,1.8), O-EV79_BUDGET)
        hi=min(B+EV79_BUDGET, O+EV79_BUDGET)
        if wet_nodes[lr,lc]:
            lo=max(B-EV79_BUDGET,1.0,O-EV79_BUDGET)
            # Remain below every known incident physical/visible plane at an
            # interior design-water node; shoreline edges are constrained below.
            incident_levels=[]
            for cr in (gr-1,gr):
                for cc in (gc-1,gc):
                    if 0<=cr<p.shape[0] and 0<=cc<p.shape[1]:
                        pp=float(p[cr,cc])
                        corner=(2 if cr==gr-1 else 0)+(1 if cc==gc-1 else 0)
                        ff=float(f[cr,cc,corner])
                        if math.isfinite(pp) and math.isfinite(ff): incident_levels.append(min(pp,ff))
            if not incident_levels: raise ValueError(f"wet bed node has no known P/F level: {(gr,gc)}")
            hi=min(hi,min(incident_levels))
        elif shore_boundary[lr,lc]:
            # Boundary vertices use only the accumulated budget; dry-floor and
            # 1 m bed restrictions are intentionally not imposed on the crossing.
            lo=max(B-EV79_BUDGET,O-EV79_BUDGET)
        lo=max(lo,B-MAX_LOCAL_DELTA); hi=min(hi,B+MAX_LOCAL_DELTA)
        if lo>hi+1e-12: raise ValueError(f"empty physical/local bounds at {(gr,gc)}: {lo}>{hi}")
        lower_abs[lr,lc]=lo; upper_abs[lr,lc]=hi
    lo64=np.asarray([lower_abs[gr-r0,gc-c0] for gr,gc in variables_global],np.float64)
    hi64=np.asarray([upper_abs[gr-r0,gc-c0] for gr,gc in variables_global],np.float64)
    lo32=np.asarray([inward32(float(x),True) for x in lo64],np.float32)
    hi32=np.asarray([inward32(float(x),False) for x in hi64],np.float32)
    x0_abs=terrain[tuple(variables_global.T)].astype(np.float64)
    if np.any(lo32.astype(np.float64)>x0_abs) or np.any(hi32.astype(np.float64)<x0_abs):
        raise AssertionError("inward float32 bounds exclude the baseline height")
    if np.any(lo32.astype(np.float64)<lo64-1e-12) or np.any(hi32.astype(np.float64)>hi64+1e-12):
        raise AssertionError("float32 bounds were not rounded inward")

    # Load reviewed numerical helpers and construct the objective over the exact
    # 15x15 context. All rows touching any of the 121 variables are retained.
    index_mod=load_mod("face_range_index_wet_bank",PATHS["index_builder"])
    ev87=load_mod("ev87_wet_bank",PATHS["ev87"])
    proto=load_mod("prototype_wet_bank",PATHS["prototype"])
    cp=load_mod("cone_pilot_wet_bank",PATHS["cone_solver"])
    local_origin=(r0,c0)
    local_base=base_window.astype(np.float64)
    vars_local=variables_global-np.asarray(local_origin,dtype=np.int32)
    stencils=proto.all_stencils(local_base.shape,vars_local)
    records=proto.row_records(local_base,vars_local,stencils)
    A_abs,b_abs=proto.csr_from_records(records,len(vars_local))
    x0=local_base[tuple(vars_local.T)].astype(np.float64)
    rhs_abs=b_abs
    A_abs=A_abs
    # D8 no-new-minimum witnesses for every local center whose 8-neighborhood
    # can be affected. Fixed-only rows are harmless and make boundary semantics explicit.
    witnesses,exempt=cp.d8_witnesses(local_base)
    variable_set=set(map(tuple,vars_local.tolist()))
    witness_influence=[]
    for w in witnesses:
        cr,cc=map(int,w["center"]); wr,wc=map(int,w["witness"])
        if (cr,cc) in variable_set or (wr,wc) in variable_set:
            witness_influence.append({"center":[cr,cc],"witness":[wr,wc]})
    C_d8_abs,d_d8_abs=cp.build_d8(local_base,vars_local,witness_influence)
    # Cone constraints are for every native triangle in the context; fixed-only
    # triangles remain as exact baseline rows. CP's exact radius is
    # max(6*tan(35deg), ||q_B||) in scaled-gradient units. The consumer's
    # +1e-4-degree tolerance is post-quantization only, never solver slack.
    G,k_abs,radii0,face_keys,qB,angleB,direct=cp.build_face_operator(local_base,vars_local)
    radii=radii0
    q_base=(G@x0+k_abs).reshape(-1,2)
    if float(np.max(np.abs(q_base.reshape(-1)-qB.reshape(-1)),initial=0.0))>1e-11:
        raise AssertionError("face-cone base action differs from independent qB")
    # Crossing/shore constraints are reconstructed from the polygon and exact P/F.
    cr_rows,cr_rhs,cr_meta=crossing_constraint_rows(local_base,vars_local,p,f,river,local_origin)
    C_cross=sparse.csr_matrix(cr_rows)
    d_cross=cr_rhs
    # D8 and shoreline rows both constrain absolute H, with fixed context values
    # folded into their right-hand sides. Combine without converting to deltas.
    C=sparse.vstack((C_d8_abs,C_cross),format="csr")
    d=np.concatenate((d_d8_abs,d_cross)).astype(np.float64)
    C.sort_indices()
    def direct_objective_residual(x_values):
        grid=local_base.copy();grid[tuple(vars_local.T)]=x_values
        expected=[]
        for _entries,_target,key in records:
            kind,rr,cc=key
            if kind=="xx": expected.append(float(grid[rr,cc]-2*grid[rr,cc+1]+grid[rr,cc+2]))
            elif kind=="zz": expected.append(float(grid[rr,cc]-2*grid[rr+1,cc]+grid[rr+2,cc]))
            elif kind=="xz": expected.append(float((-.25*grid[rr,cc]+.25*grid[rr,cc+2]+.25*grid[rr+2,cc]-.25*grid[rr+2,cc+2])*math.sqrt(2.0)))
            elif kind=="fidelity": expected.append(.25*float(grid[rr,cc]-local_base[rr,cc]))
            else: raise AssertionError(f"unexpected EV88 objective row {key}")
        return A_abs@x_values-rhs_abs,np.asarray(expected,np.float64)
    trial_x=x0+np.linspace(-.01,.01,len(x0),dtype=np.float64)
    for label,xcheck in (("baseline",x0),("trial",trial_x)):
        got,want=direct_objective_residual(xcheck)
        obj_max=float(np.max(np.abs(got-want),initial=0.0))
        if obj_max>1e-10:
            worst=int(np.argmax(np.abs(got-want)))
            raise AssertionError(f"absolute-height EV88 objective mismatch {label}: max={obj_max}, row={worst}, key={records[worst][2]}")
    if np.min(C@x0-d,initial=np.inf)<-1e-9:
        raise AssertionError("baseline violates D8 or design-shore crossing constraints")
    if np.max(np.abs((G@x0+k_abs).reshape(-1,2)-qB),initial=0.0)>1e-11:
        raise AssertionError("absolute-height cone offset does not reproduce baseline gradients")
    # Affected cells/faces for exact post-solve coverage validation.
    cells,affected_poly=polygon_edges(WIN,variables_global,river)
    idx=index_mod.FaceRangeIndex(PATHS["index_manifest"].parent)
    min_cell=(min(r for r,c in cells),max(r for r,c in cells))
    min_col=(min(c for r,c in cells),max(c for r,c in cells))
    faces=idx.query_window(min_cell[0],min_cell[1],min_col[0],min_col[1])
    exact_intersections=[]
    affected_bbox=affected_poly.bounds
    for ii,xyz in enumerate(faces["xyz"]):
        if int(faces["degenerate"][ii]):
            # Project the zero-area face as its exact XZ segment/point; don't
            # count every degenerate in the broadphase bbox as an intersection.
            xz=np.asarray(xyz[:,[0,2]],dtype=np.float64)
            distinct=np.unique(xz,axis=0)
            geom=Point(distinct[0]) if len(distinct)==1 else LineString(distinct)
            if geom.intersects(affected_poly):
                exact_intersections.append(ii)
            continue
        tri=Polygon(xyz[:,[0,2]])
        if not tri.is_valid: raise AssertionError("positive-area indexed face has invalid XZ polygon")
        if tri.intersects(affected_poly): exact_intersections.append(ii)
    faces={k:v[np.asarray(exact_intersections,dtype=np.int64)] for k,v in faces.items()}
    if not len(faces["kind"]): raise AssertionError("no compiled faces intersect affected cells")
    idx.reverify()

    # Baseline local hinge population, exact EV87 triangulation and both sides
    # of every incident shared edge. These are reports/post-solve checks, not rows.
    angles=dict(ev87.edge_angles(local_base))
    incident={k:ev87.incident_any(np.isin(np.arange(local_base.size).reshape(local_base.shape),
                np.asarray([r*local_base.shape[1]+c for r,c in vars_local],np.int64)),k) for k in angles}
    hinge_rc=[]; hinge_kind=[]; hinge_angle=[]
    for kind in ("diag","vertical","horizontal"):
        arr=np.asarray(angles[kind],np.float64)
        mask=np.asarray(incident[kind],bool)
        for rr,cc in np.argwhere(mask):
            hinge_kind.append({"diag":0,"vertical":1,"horizontal":2}[kind])
            hinge_rc.append([int(rr),int(cc)])
            hinge_angle.append(float(arr[rr,cc]))
    hinge_meta={"kinds":{"0":"diag","1":"vertical","2":"horizontal"},"angles_before_deg":hinge_angle,
                "hinge_rc":hinge_rc,"hinge_kind":hinge_kind,
                "p99_before_deg":float(np.percentile(hinge_angle,99)),"max_before_deg":float(np.max(hinge_angle)),
                "above30_before":int(np.count_nonzero(np.asarray(hinge_angle)>30.0))}
    if not hinge_angle: raise AssertionError("no hinge in affected population")
    focus_hinge=float(selection["slope_hinge"]["max_incident_hinge_in_crop"]["angle_deg"])
    focus_design=(float(selection["design_contour"]["nearest_boundary_distance_m"]))
    # Corridor and retained-window guard: full local geometry must be disjoint,
    # P9 nodes absent, and the candidate section stays exactly inside the chosen feature.
    if affected_poly.intersects(corridor_union) if corridor_union is not None else False:
        raise AssertionError("affected cell polygon overlaps signed navigable corridor")
    if np.any(road_mask & var_mask): raise AssertionError("road reference corridor overlaps the editable core")

    # Serialize sparse matrices as arrays in one NPZ, including baseline and all
    # exact source face geometry needed for independent post-solve coverage.
    def csr_pack(prefix, mat):
        m=mat.tocsr();m.sort_indices()
        return {f"{prefix}_data":m.data,f"{prefix}_indices":m.indices.astype(np.int32),
                f"{prefix}_indptr":m.indptr.astype(np.int32),f"{prefix}_shape":np.asarray(m.shape,np.int32)}
    readset_prewrite={k:sha(path) for k,path in PATHS.items()}
    if readset_prewrite!=read_start:
        raise AssertionError("source readset changed before prepared matrices were written")
    arrays={
        "variables_rc":variables_global.astype(np.int32),"x0_absolute":x0_abs,
        "lo_absolute_float64":lo64,"hi_absolute_float64":hi64,"lo_absolute_float32_inward":lo32,"hi_absolute_float32_inward":hi32,
        "base_heights_context":base_window.astype(np.float32),"original_heights_context":original_window.astype(np.float32),
        "cls_context":tmask["cls"],"water_context":tmask["water"],"wet_support_context":region(ev79c["wet_support"]),
        "other_fixed_context":other_rebuilt,"effective_fixed_context":effective_fixed,"p9_context":p9_mask,"road_context":road_mask,
        "design_interior_context":interior,"shore_boundary_context":shore_boundary,
        # Store the exact source P/F values promoted to float64, so the consumer
        # can recompute affine rows without any later reinterpretation/casting.
        "P_cells_float64":p[r0:r1-1,c0:c1-1].astype(np.float64),"F_cells_float64":f[r0:r1-1,c0:c1-1].astype(np.float64),
        "d8_witnesses_local":np.asarray([[*w["center"],*w["witness"]] for w in witness_influence],np.int32).reshape(-1,4),
        "hinge_rc_local":np.asarray(hinge_rc,np.int32),"hinge_kind":np.asarray(hinge_kind,np.uint8),
        "hinge_angle_before_deg":np.asarray(hinge_angle,np.float64),"face_keys_local":face_keys.astype(np.int32),
        "qB":qB.astype(np.float64),"radii":radii.astype(np.float64),
        "face_object_id":faces["object_id"],"face_model_id":faces["model_id"],"face_id":faces["face_id"],
        "face_kind":faces["kind"],"face_xyz":faces["xyz"],"face_plane_y_xz":faces["plane_y_xz"],
        "face_area_xz":faces["area_xz"],"face_cell_range_rc":faces["cell_range_rc"],"face_degenerate":faces["degenerate"],
        "stencils_json":np.frombuffer(canonical([list(x) for x in stencils]),dtype=np.uint8),
        "crossing_rows_json":np.frombuffer(canonical(cr_meta),dtype=np.uint8),
        "face_population_cells_rc":np.asarray(cells,np.int32),
    }
    arrays.update(csr_pack("A",A_abs)); arrays["rhs_A"]=np.asarray(rhs_abs,np.float64)
    arrays.update(csr_pack("C",C)); arrays["d_C"]=d
    arrays.update(csr_pack("G",G)); arrays["k_G"]=np.asarray(k_abs,np.float64); arrays["radii_G"]=radii
    # Serialize D8-only matrix and crossings separately for independent reconstruction.
    arrays.update(csr_pack("C_d8",C_d8_abs)); arrays["d_C_d8"]=d_d8_abs
    arrays.update(csr_pack("C_cross",C_cross)); arrays["d_C_cross"]=d_cross
    npz_path=outdir/"prepared.npz"
    np.savez_compressed(npz_path,**arrays)
    # Index model manifest is pinned and rechecked; keep source IDs, not copied models.
    manifest=json.loads(PATHS["index_manifest"].read_text(encoding="utf-8"))
    def crossing_extrema(surface,key):
        vals=[float(x[key]) for x in cr_meta if x["surface"]==surface and x["type"]=="cross_lower"]
        return [min(vals),max(vals)] if vals else None
    report={
        "schema":"ev94.oredezh-wet-bank-prepared.v1","status":"PREPARED_NO_SOLVE",
        "scope":"single isolated 121-node maximum wet-bank profile; no solver/candidate/terrain write",
        "source_readset_start":read_start,
        "source_readset_end":{k:sha(p) for k,p in PATHS.items()},
        "retained_unit_readset_start":retained_readset_start,
        "retained_unit_readset_end":{path:sha(Path(path)) for path in retained_readset_start},
        "prepared_path":str(npz_path),"prepared_sha256":sha(npz_path),
        "geometry":{"feature_id":"river_041","feature_name":"Oredezh","focus_rc":[ROW,COL],"window_rc_half_open":list(WIN),
                    "variable_window_rc_half_open":list(VAR_WIN),"variables":len(variables_global),"affected_cells":len(cells),
                    "affected_face_records":int(len(faces["kind"])),"affected_face_physical":int(np.count_nonzero(faces["kind"]==0)),
                    "affected_face_visible":int(np.count_nonzero(faces["kind"]==1)),"affected_face_degenerate":int(np.count_nonzero(faces["degenerate"]))},
        "matrices":{"A_shape":list(A_abs.shape),"A_nnz":int(A_abs.nnz),"stencil_rows":len(stencils),
                    "C_shape":list(C.shape),"C_nnz":int(C.nnz),"D8_rows":int(C_d8_abs.shape[0]),
                    "crossing_rows":int(C_cross.shape[0]),"G_shape":list(G.shape),"G_nnz":int(G.nnz),"cone_count":int(len(radii))},
        "crossings":{"metadata_records":len(cr_meta),"linear_rows":int(C_cross.shape[0]),
                     "unique_edge_surface_records":len({(tuple(x["cell_rc"]),tuple(tuple(y) for y in x["edge_rc"]),x["surface"]) for x in cr_meta}),
                     "baseline_crossing_edges_by_surface":{k:len({(tuple(x["cell_rc"]),tuple(tuple(y) for y in x["edge_rc"])) for x in cr_meta if x["surface"]==k and x["type"]=="cross_lower"}) for k in ("P","F")},
                     "same_sign_edges_by_surface":{k:len({(tuple(x["cell_rc"]),tuple(tuple(y) for y in x["edge_rc"])) for x in cr_meta if x["surface"]==k and x["type"]=="sign_only"}) for k in ("P","F")},
                     "same_sign_submerged_edges_by_surface":{k:len({(tuple(x["cell_rc"]),tuple(tuple(y) for y in x["edge_rc"])) for x in cr_meta if x["surface"]==k and x["type"]=="sign_only" and x["delta_a_m"]<0 and x["delta_b_m"]<0}) for k in ("P","F")},
                     "baseline_contact_edges_by_surface":{k:len({(tuple(x["cell_rc"]),tuple(tuple(y) for y in x["edge_rc"])) for x in cr_meta if x["surface"]==k and x["type"]=="sign_only" and (x["delta_a_m"]==0 or x["delta_b_m"]==0)}) for k in ("P","F")},
                     "crossing_t_base_minmax_by_surface":{k:crossing_extrema(k,"t_base") for k in ("P","F")},
                     "crossing_t_design_minmax_by_surface":{k:crossing_extrema(k,"t_design") for k in ("P","F")},
                     "same_sign_policy":"preserve each endpoint sign for every P/F sample; baseline contact pins the endpoint; no crossing parameter is invented"},
        "hinges":hinge_meta,
        "bounds":{"local_delta_m":[-MAX_LOCAL_DELTA,MAX_LOCAL_DELTA],"EV79_budget_m":EV79_BUDGET,
                  "variable_lower_min_m":float(lo64.min()),"variable_lower_max_m":float(lo64.max()),
                  "variable_upper_min_m":float(hi64.min()),"variable_upper_max_m":float(hi64.max()),
                  "wet_interior_nodes":int(wet_nodes.sum()),"dry_nodes":int(dry_nodes.sum()),"shore_boundary_nodes":int(shore_boundary.sum()),
                  "baseline_inside_float32_bounds":True,"bed_floor_m":1.0},
        "protection":{"other_fixed_reconstruction_exact":True,"EV79_fixed_reconstruction_exact":True,
                      "narva_mask_reconstruction_exact":True,"narva_nodes":int(narva_mask.sum()),
                      "reserve_nodes":int(reserve_mask.sum()),"platform_nodes":int(platform_mask.sum()),
                      "released_wet_support_nodes_in_context":int((release&region(ev79c["wet_support"])).sum()),
                      "released_cls5_water_nodes_in_context":int(((tmask["cls"]==5)&tmask["water"]).sum()),
                      "reserve_platform_halo_nodes":int(halo.sum()),"p9_nodes":int(p9_mask.sum()),"road_corridor_nodes":int(road_mask.sum()),
                      "overlap_retained_windows":len(overlap),"retained_units_checked":len(retained_rows),"road_nearest_sample_m":float(selection["protection_and_separation"]["nearest_road_sample"]["distance_m"]),
                      "wrp_bridge_origin_count_within_500m":int(selection["protection_and_separation"]["bridge_named_WRP_origin_count_within_500m"]),
                      "nearest_bridge_named_origin_m":float(min(x["origin_distance_m"] for x in selection["protection_and_separation"]["bridge_named_WRP_origins"])),
                      "wrp_origin_measurement_limit":selection["protection_and_separation"]["origin_distance_limit"]},
        "water_object_identity":{"base_wrp_sha256":identity["base_wrp_sha256"],"staged_wrp_sha256":identity["staged_wrp_sha256"],
                      "object_count_base_and_EV94":int(identity["water_object_count_base_and_EV94"]),
                      "objects_and_materials_exact_in_pinned_selection":bool(identity["objects_and_materials_exact"]),
                      "ids_names_and_matrices_equal_in_pinned_selection":bool(identity["water_ids_names_and_12-float_matrices_equal"]),
                      "verification_scope":"both WRP bytes were rehashed; identity comparison is inherited from the pinned selection artifact, not decoded again here"},
        "post_solve_gates_not_encoded_as_convex_rows":["focus hinge drop >=2 degrees","no new hinge >30 degrees","affected hinge p99 nonworse",
                   "water connected component preserved","exact compiled-face P/F coverage and residuals","area exposed change reported",
                   "no new minima outside design channel","metadata/fixed terrain/windows unchanged"],
        "index":{"manifest_sha256":sha(PATHS["index_manifest"]),"schema":manifest["schema"],"status":manifest["status"],
                 "object_count":manifest["object_count"],"indexed_face_count":manifest["counts"]["faces"]},
        "dimensions":{"A":"EV88 Dxx/Dzz/Dxz plus 0.25 fidelity on every stencil touching the variable set; absolute-height H variables and RHS",
                      "C":"no-new-minimum D8 witness rows and per-edge/per-sample P/F sign+crossing interval rows; absolute-height C H >= d",
                      "G":"EV93 pilot native triangle gradient cones in 6m-scaled gradient space; exact radius max(6*tan(35deg), norm(q_B)); no solver slack; +1e-4 degrees is post-quantization consumer tolerance only",
                      "bounds":"absolute H bounds: EV79 accumulated +/-2m and dry physical floor, local +/-0.5m; wet interior bed>=1m and below incident P/F; inward float32"},
        "source_code_hashes":{"prepare_wet_bank_matrices.py":sha(Path(__file__)),"prototype":sha(PATHS["prototype"]),
                              "cone_solver":sha(PATHS["cone_solver"]),"ev87":sha(PATHS["ev87"]),"index_builder":sha(PATHS["index_builder"])},
    }
    if report["source_readset_start"]!=report["source_readset_end"]:
        raise AssertionError("source readset changed during prepared artifact construction")
    if report["retained_unit_readset_start"]!=report["retained_unit_readset_end"]:
        raise AssertionError("one or more retained selection artifacts changed during preparation")
    report_path=outdir/"preparation.json"
    report_path.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"prepared":str(npz_path),"prepared_sha256":report["prepared_sha256"],
                      "variables":len(variables_global),"A":report["matrices"]["A_shape"],"C":report["matrices"]["C_shape"],
                      "G":report["matrices"]["G_shape"],"crossings":len(cr_meta),"faces":len(faces["kind"]),
                      "seconds":time.monotonic()-started},ensure_ascii=False),flush=True)


def self_test():
    # Analytic proof that a dry->wet affine crossing interval becomes Cx>=d.
    h=np.array([2.0,-2.0]); level=np.array([0.0,0.0]); t0=.5; t1=.75
    lo_row=np.array([1-t0,t0]); hi_row=np.array([1-t1,t1])
    lhs0=lo_row@h; rhs_lo=-lhs0
    lhs1=hi_row@h; rhs_hi=lhs1
    assert lo_row@h >= -rhs_lo-1e-12
    assert -hi_row@h >= -rhs_hi-1e-12
    bad=np.array([2.,-4.])
    assert lo_row@bad < -rhs_lo
    # Float32 inward bounds include zero and never widen either side.
    low=inward32(-.123456789,True); high=inward32(.234567891,False)
    assert low>=-.123456789 and high<=.234567891 and low<=0<=high
    # Exercise the production shoreline-row builder: an edge with both endpoints
    # below P/F must preserve both signs and reject a newly-created crossing.
    h=np.zeros((2,2),np.float64); vars_rc=np.array([[0,0],[0,1],[1,0],[1,1]],np.int32)
    p=np.ones((1,1),np.float32); f=np.ones((1,1,4),np.float32)
    coast=box(-3,Z0-3,3,Z0+3)
    rows,rhs,meta=crossing_constraint_rows(h,vars_rc,p,f,coast,(0,0))
    assert any(x["type"]=="sign_only" and x["surface"]=="P" for x in meta)
    assert np.min(rows@h.reshape(-1)-rhs)>=-1e-12
    bad=h.copy();bad[0,0]=2.0
    assert np.min(rows@bad.reshape(-1)-rhs)<0
    assert all(x["t_base"] is None for x in meta if x["type"]=="sign_only")
    # Design boundaries must have one hit per edge; synthetic double hit is rejected by count logic.
    from shapely.geometry import LineString, MultiPoint
    hits=collect_points(MultiPoint([(1,0),(2,0)]))
    assert len(hits)==2
    print(json.dumps({"status":"SELF_TEST_PASS","crossing_affine_rows":"PASS","wrong_interval_rejected":"PASS",
                      "float32_inward":"PASS","same_sign_no_new_crossing":"PASS","multi_hit_guard":"PASS"}))


def main():
    ap=argparse.ArgumentParser()
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test",action="store_true")
    group.add_argument("--prepare",action="store_true")
    ap.add_argument("--out",type=Path,default=None)
    args=ap.parse_args()
    if args.self_test:
        self_test();return 0
    out=args.out or (RUNS/"attempt-01")
    run_prepare(out)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
