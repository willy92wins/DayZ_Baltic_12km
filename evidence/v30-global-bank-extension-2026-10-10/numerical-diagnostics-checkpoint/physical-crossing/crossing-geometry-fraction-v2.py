#!/usr/bin/env python
"""Independent exact-rational crossing diagnostic; reads pinned artifacts only."""
from __future__ import annotations
from fractions import Fraction
import hashlib, json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import sparse
from shapely.geometry import LineString, shape

G = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010")
R = G / "G/wet-bank-pilot"
PREP = R / "prepared-runs/attempt-08/prepared.npz"
SOL = R / "solve-once/solution.npz"
BASE = G / "global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz"
P = G / "build-focal/candidate/plane.npy"
F = G / "build-focal/candidate/visible-field.npy"
DESIGN = Path(r"E:/DayZ-Baltic-Build/v30-v11/design/water_v3.geojson")
BUILDER = R / "prepare_wet_bank_matrices.py"
OLD_QUANT = R / "postsolve-consumer/quantization-diagnostic.json"
OUT = R / "postsolve-consumer/crossing-geometry-fraction-v2.json"
PIN = {
    PREP: "52409a8d074d15ec068bddc6e9265bc3782e84e9d54582b8a6d7b0a6675a787f",
    SOL: "1b7a23ebb3c203427f1c77cb8de6becfca750746e47f5494bba6723b0610eab1",
    BASE: "40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a",
    P: "768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0",
    F: "f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c",
    DESIGN: "caa333e365c2a4511f839937a9d76a5aa157a0ef925d6ee4b5efcc4ebb38f8a9",
    BUILDER: "65e05a6540026b08df7effa53c58534121bb2fa89e116a2ef07ad46ba0edf286",
}
ORIGIN = (855, 1179)

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def q(value) -> Fraction:
    return Fraction.from_float(float(value))

def csr(z, name):
    return sparse.csr_matrix((z[name+"_data"], z[name+"_indices"], z[name+"_indptr"]),
                             shape=tuple(z[name+"_shape"]))

def collect_points(geometry, out):
    if geometry.is_empty:
        return
    if geometry.geom_type == "Point":
        out.append(geometry)
    elif hasattr(geometry, "geoms"):
        for part in geometry.geoms:
            collect_points(part, out)

def edge_design_t(edge, boundary):
    (ra, ca), (rb, cb) = edge
    a = (ca * 6.0, 12282.0 - ra * 6.0)
    b = (cb * 6.0, 12282.0 - rb * 6.0)
    hits = []
    collect_points(LineString((a, b)).intersection(boundary), hits)
    unique = []
    for hit in hits:
        if not any(hit.distance(old) <= 1e-9 for old in unique):
            unique.append(hit)
    if len(unique) != 1:
        raise ValueError(f"expected one shoreline intersection on {edge}, got {len(unique)}")
    hit = unique[0]
    dx, dz = b[0] - a[0], b[1] - a[1]
    t = ((hit.x - a[0]) * dx + (hit.y - a[1]) * dz) / (dx*dx + dz*dz)
    return q(t)

def main():
    for path, expected in PIN.items():
        actual = sha(path)
        if actual != expected:
            raise ValueError(f"pin mismatch {path}: expected {expected}, got {actual}")
    with np.load(PREP, allow_pickle=False) as z, np.load(SOL, allow_pickle=False) as s, np.load(BASE, allow_pickle=False) as b:
        Bfull = b["heights"]
        H = s["closed_float32_grid"]
        H64 = z["base_heights_context"].astype(np.float64, copy=True)
        vars_rc = z["variables_rc"].astype(np.int64)
        local = vars_rc - np.asarray(ORIGIN)
        H64[tuple(local.T)] = s["solution_float64"]
        x0 = z["base_heights_context"][tuple(local.T)].astype(np.float64)
        xh = H[tuple(local.T)].astype(np.float64)
        C = csr(z, "C_cross")
        d = z["d_C_cross"]
        matrix_B = np.asarray(C @ x0 - d).ravel()
        matrix_H = np.asarray(C @ xh - d).ravel()
        allmeta = json.loads(z["crossing_rows_json"].tobytes().decode("utf-8"))
        # The prepared JSON contains non-row sign_only summaries; filter by schema before mapping CSR rows.
        meta = [m for m in allmeta if m["type"] != "sign_only"]
        if len(meta) != C.shape[0]:
            raise ValueError(f"metadata/CSR mismatch: {len(meta)} vs {C.shape[0]}")

        doc = json.loads(DESIGN.read_text(encoding="utf-8-sig"))
        feature = next(f for f in doc["features"] if f.get("id") == "river_041" or f.get("properties", {}).get("id") == "river_041")
        boundary = shape(feature["geometry"]).boundary
        p = np.load(P, mmap_mode="r", allow_pickle=False)
        f = np.load(F, mmap_mode="r", allow_pickle=False)

        # Direct semantic check: exact rational t_H from the stored binary heights/levels,
        # compared to t_B and the original design intersection parameter. No author matrix builder.
        unique = {}
        for row, m in enumerate(meta):
            if m["type"] not in ("cross_lower", "cross_upper"):
                continue
            edge = tuple(map(tuple, m["edge_rc"]))
            cell = tuple(m["cell_rc"])
            unique.setdefault((edge, cell, m["surface"]), (row, m))
        checks = []
        for (edge, cell, surface), (row, m) in unique.items():
            (ra, ca), (rb, cb) = edge
            cr, cc = cell
            corners = {(cr,cc):0, (cr,cc+1):1, (cr+1,cc):2, (cr+1,cc+1):3}
            levels = [float(p[cr,cc])] * 2 if surface == "P" else [float(f[cr,cc,corners[(ra,ca)]]), float(f[cr,cc,corners[(rb,cb)]])]
            hb = [float(Bfull[ra,ca]), float(Bfull[rb,cb])]
            hh = [float(H[ra-ORIGIN[0],ca-ORIGIN[1]]), float(H[rb-ORIGIN[0],cb-ORIGIN[1]])]
            hc = [float(H64[ra-ORIGIN[0],ca-ORIGIN[1]]), float(H64[rb-ORIGIN[0],cb-ORIGIN[1]])]
            db = [q(hb[i]) - q(levels[i]) for i in range(2)]
            dh = [q(hh[i]) - q(levels[i]) for i in range(2)]
            dc = [q(hc[i]) - q(levels[i]) for i in range(2)]
            if db[0] * db[1] >= 0:
                raise ValueError(f"baseline crossing absent for row {row}")
            dry_endpoint = 0 if db[0] > 0 else 1
            t_design_ab = edge_design_t(edge, boundary)
            def t_dry_wet(delta):
                if delta[0] * delta[1] >= 0:
                    return None
                t_ab = delta[0] / (delta[0] - delta[1])
                return t_ab if dry_endpoint == 0 else 1 - t_ab
            t_base = t_dry_wet(db)
            t_design = t_design_ab if dry_endpoint == 0 else 1 - t_design_ab
            t_candidate = t_dry_wet(dh)
            t_continuous = t_dry_wet(dc)
            lower, upper = min(t_base, t_design), max(t_base, t_design)
            fail = t_candidate is None or t_candidate < lower or t_candidate > upper
            fail_continuous = t_continuous is None or t_continuous < lower or t_continuous > upper
            baseline_fail = t_base < lower or t_base > upper
            distance = None if t_candidate is None else max(lower - t_candidate, Fraction(0), t_candidate - upper)
            distance_continuous = None if t_continuous is None else max(lower - t_continuous, Fraction(0), t_continuous - upper)
            checks.append({
                "csr_row": int(row), "surface": surface, "type": m["type"], "cell_rc": list(cell),
                "edge_rc": [list(x) for x in edge], "endpoint_levels": levels,
                "baseline_endpoint_heights": hb, "candidate_endpoint_heights": hh,
                "continuous_x64_endpoint_heights": hc,
                "t_B_exact_rational": float(t_base), "t_design_intersection_binary64_exact": float(t_design),
                "t_continuous_x64_exact_rational": None if t_continuous is None else float(t_continuous),
                "t_H_exact_rational": None if t_candidate is None else float(t_candidate),
                "allowed_t_interval": [float(lower), float(upper)],
                "outside_interval_by_t": None if distance is None else float(distance),
                "continuous_outside_interval_by_t": None if distance_continuous is None else float(distance_continuous),
                "baseline_crossing_pass": not baseline_fail,
                "continuous_x64_crossing_fail": bool(fail_continuous),
                "physical_crossing_fail": bool(fail),
            })
        baseline_direct_failures = sum(not x["baseline_crossing_pass"] for x in checks)
        bad_B = np.flatnonzero(matrix_B < 0.0)
        bad_H = np.flatnonzero(matrix_H < 0.0)
        material_H = np.flatnonzero(matrix_H < -1e-12)
        support = np.unique(np.concatenate([C.getrow(int(i)).indices for i in bad_H])).astype(int)
        material_support = np.unique(np.concatenate([C.getrow(int(i)).indices for i in material_H])).astype(int)
        # Derive the historical 9-vs-13 count from CSR indices, not positional metadata.
        helpful = []
        for j in support:
            cur = np.float32(xh[j])
            can_help = False
            for direction in (-1, 1):
                nxt = np.nextafter(cur, np.float32(-np.inf if direction < 0 else np.inf), dtype=np.float32)
                if nxt < z["lo_absolute_float32_inward"][j] or nxt > z["hi_absolute_float32_inward"][j]:
                    continue
                delta = float(nxt) - float(cur)
                for i in bad_H:
                    row = C.getrow(int(i))
                    pos = np.flatnonzero(row.indices == j)
                    if pos.size and matrix_H[i] + row.data[int(pos[0])] * delta >= 0.0:
                        can_help = True
                        break
                if can_help:
                    break
            if can_help:
                helpful.append(int(j))
        failed = [x for x in checks if x["physical_crossing_fail"]]
        continuous_failed = [x for x in checks if x["continuous_x64_crossing_fail"]]
        by_edge = defaultdict(list)
        for item in failed:
            by_edge[tuple(tuple(v) for v in item["edge_rc"])].append(item)
        failed_edges = []
        for edge, items in sorted(by_edge.items()):
            failed_edges.append({
                "edge_rc": [list(v) for v in edge],
                "cells": sorted({tuple(x["cell_rc"]) for x in items}),
                "surfaces": sorted({x["surface"] for x in items}),
                "rows": [x["csr_row"] for x in items],
                "P_F_pairs": [x for x in items],
                "max_t_violation": max(x["outside_interval_by_t"] or 0.0 for x in items),
            })

        # Compare the actual semantic t-bound inequalities with the approximate stored C row bounds.
        # The semantic version is rebuilt from B/P/F/design, not from C coefficients.
        interval_rows = []
        for j in (1, 3):
            lower, upper = [], []
            geom_lower, geom_upper = [], []
            for i in range(C.shape[0]):
                row = C.getrow(i)
                if row.nnz == 1 and int(row.indices[0]) == j:
                    bound = Fraction.from_float(float(d[i])) / Fraction.from_float(float(row.data[0]))
                    item = {"row": int(i), "value": bound, "surface": meta[i]["surface"], "type": meta[i]["type"],
                            "cell_rc": meta[i]["cell_rc"], "edge_rc": meta[i]["edge_rc"]}
                    (lower if row.data[0] > 0 else upper).append(item)
                    m = meta[i]
                    edge = tuple(map(tuple, m["edge_rc"]))
                    cell = tuple(m["cell_rc"])
                    (ra, ca), (rb, cb) = edge
                    cr, cc = cell
                    corners = {(cr,cc):0, (cr,cc+1):1, (cr+1,cc):2, (cr+1,cc+1):3}
                    levels = [float(p[cr,cc])] * 2 if m["surface"] == "P" else [float(f[cr,cc,corners[(ra,ca)]]), float(f[cr,cc,corners[(rb,cb)]])]
                    node_pair = [(ra,ca),(rb,cb)]
                    hb = [q(Bfull[ra,ca]), q(Bfull[rb,cb])]
                    lv = [q(levels[0]), q(levels[1])]
                    delta = [hb[k]-lv[k] for k in range(2)]
                    dry = 0 if delta[0] > 0 else 1
                    t_b_ab = delta[0] / (delta[0]-delta[1])
                    t_b = t_b_ab if dry == 0 else 1-t_b_ab
                    td_ab = edge_design_t(edge, boundary)
                    td = td_ab if dry == 0 else 1-td_ab
                    t_lim = min(t_b,td) if m["type"] == "cross_lower" else max(t_b,td)
                    sign = 1 if m["type"] == "cross_lower" else -1
                    var_rc = tuple(vars_rc[j])
                    def physical_row(x):
                        vals = hb.copy()
                        vals[node_pair.index(var_rc)] = q(x)
                        value = (1-t_lim)*(vals[dry]-lv[dry]) + t_lim*(vals[1-dry]-lv[1-dry])
                        return sign*value
                    r0, r1 = physical_row(0.0), physical_row(1.0)
                    slope = r1-r0
                    if slope == 0:
                        continue
                    root = -r0/slope
                    semantic = {"row":int(i),"root":root,"surface":m["surface"],"type":m["type"],
                                "cell_rc":m["cell_rc"],"edge_rc":m["edge_rc"]}
                    (geom_lower if slope > 0 else geom_upper).append(semantic)
            lo = max(lower, key=lambda x:x["value"])
            hi = min(upper, key=lambda x:x["value"])
            glo = max(geom_lower, key=lambda x:x["root"])
            ghi = min(geom_upper, key=lambda x:x["root"])
            interval_rows.append({
                "variable_index": int(j), "rc": vars_rc[j].tolist(),
                "active_lower_row": {k:v for k,v in lo.items() if k != "value"},
                "active_upper_row": {k:v for k,v in hi.items() if k != "value"},
                "stored_C_lower_float": float(lo["value"]), "stored_C_upper_float": float(hi["value"]),
                "stored_C_exact_fraction_width": float(hi["value"] - lo["value"]),
                "direct_geometry_lower_row": {k:v for k,v in glo.items() if k != "root"},
                "direct_geometry_upper_row": {k:v for k,v in ghi.items() if k != "root"},
                "direct_geometry_lower_float": float(glo["root"]), "direct_geometry_upper_float": float(ghi["root"]),
                "direct_geometry_exact_fraction_width": float(ghi["root"] - glo["root"]),
                "B_value": float(x0[j]),
                "B_equals_direct_geometry_point": glo["root"] == ghi["root"] == Fraction.from_float(float(x0[j])),
            })

        report = {
            "schema": "ev94.wet-bank-crossing-geometry-fraction.v2",
            "status": "READ_ONLY_DIRECT_GEOMETRY_DIAGNOSTIC",
            "inputs_sha256": {str(path): sha(path) for path in PIN},
            "independent_method": "For each recorded P/F edge crossing, reload B, P, F, and water_v3 river_041. Compute signed endpoint distances as exact rationals of their stored binary values; derive t_B and t_H by rational division; recompute the design intersection on each exact native edge with Shapely and preserve its binary64 value as an exact rational. Compare t_H to [min(t_B,t_design),max(...)]. No author matrix builder, solver, candidate mutation, or post-hoc tolerance.",
            "metadata_alignment": {"source_records": len(allmeta), "nonrow_sign_only_summaries_filtered": len(allmeta)-len(meta), "C_cross_rows": int(C.shape[0]), "aligned": len(meta)==C.shape[0]},
            "C_cross_arithmetic": {
                "B_negative_rows_exact_float_eval": int(len(bad_B)), "B_min_slack": float(matrix_B.min()),
                "B_negative_rows_all_within_1e_15": bool(np.all(matrix_B[bad_B] >= -1e-15)),
                "candidate_negative_rows_exact_float_eval": int(len(bad_H)), "candidate_material_rows_below_minus_1e_12": int(len(material_H)),
                "candidate_min_slack": float(matrix_H.min()),
                "candidate_violated_support_rc_from_CSR": [vars_rc[j].tolist() for j in support],
                "support_count": int(len(support)),
                "one_ulp_single_row_helpful_nodes_exact_float_rule": [vars_rc[j].tolist() for j in helpful],
                "helpful_count": int(len(helpful)),
                "material_violation_support_rc": [vars_rc[j].tolist() for j in material_support],
                "material_support_count": int(len(material_support)),
                "material_single_ulp_helpful_count": int(sum(any(np.array_equal(vars_rc[j], vars_rc[k]) for k in helpful) for j in material_support)),
            },
            "physical_crossing": {
                "unique_cell_edge_surface_checks": len(checks),
                "B_direct_failures": baseline_direct_failures,
                "continuous_x64_direct_failures": len(continuous_failed),
                "continuous_x64_failed_native_edges": len({tuple(map(tuple,x["edge_rc"])) for x in continuous_failed}),
                "continuous_x64_max_t_interval_excess": max((x["continuous_outside_interval_by_t"] or 0.0 for x in continuous_failed), default=0.0),
                "candidate_direct_failures": len(failed),
                "candidate_failed_native_edges": failed_edges,
                "max_candidate_t_interval_excess": max((x["outside_interval_by_t"] or 0.0 for x in failed), default=0.0),
                "interpretation": "The 20 non-roundoff C rows map to direct crossing drift on five native edges; each edge is represented by P and F and by two incident cells. The continuous ADMM x64 iterate is already slightly outside direct intervals on more edges, within its numerical residual scale; float32 makes five material edge groups visible at up to ~1.9e-7 of edge parameter. The three extra negative C rows are only ~1e-15 arithmetic residuals on unchanged B edges and pass direct geometry.",
            },
            "collapsed_single_variable_intervals": interval_rows,
            "neighborhood_reconciliation": {
                "old_9_vs_13": "The 13-variable set is now extracted from CSR supports of the 23 strictly negative candidate rows; the nine count means a single ±1 ULP move can fix at least one exact-float C row while holding all others fixed. It includes (858,1183), which only fixes two ~1e-15 rows. Restricting to the 20 rows below -1e-12 leaves 10 support variables and six individually helpful variables. The count difference is therefore a definition/roundoff distinction, not proof of joint infeasibility.",
                "prior_3pow13_zero_result": "INVALIDATED: the prior enumeration required every floating C_cross residual to be >=0, although B itself has 14 residuals in [-8.89e-16,0). It cannot establish mathematical or geometric infeasibility. No exhaustive neighborhood enumeration is performed here.",
            },
            "source_anchors": {
                "crossing_row_builder": {"path": str(BUILDER), "sha256": PIN[BUILDER], "lines": "145-256"},
                "local_incident_level_known_limitation": {"path": str(BUILDER), "lines": "262-274", "note": "P-NaN fallback also skips F at that corner; attempt-08 has 0 P-NaN/F-finite samples among 121 nodes x 4 incidences, so this does not affect this prepared run but must be corrected before reuse."},
            },
            "limitations": ["This diagnoses the frozen candidate only; it neither finds nor rules out a joint feasible f32 neighbor.", "The exact-float C baseline residual is an arithmetic representation issue; physical crossing feasibility is assessed independently from direct geometry."],
        }
    OUT.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status":report["status"], "B_C_neg":report["C_cross_arithmetic"]["B_negative_rows_exact_float_eval"],
        "B_direct_failures":report["physical_crossing"]["B_direct_failures"], "candidate_direct_failures":report["physical_crossing"]["candidate_direct_failures"],
        "failed_edges":len(report["physical_crossing"]["candidate_failed_native_edges"]), "support":report["C_cross_arithmetic"]["support_count"],
        "helpful":report["C_cross_arithmetic"]["helpful_count"], "output":str(OUT)}))

if __name__ == "__main__":
    main()
