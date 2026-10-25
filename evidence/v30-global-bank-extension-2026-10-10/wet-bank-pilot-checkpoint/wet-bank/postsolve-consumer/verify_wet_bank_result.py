#!/usr/bin/env python
"""Independent post-solve gate for the isolated Oredezh wet-bank experiment.

Reads the one-call result and its unaccepted artifacts. It never writes terrain,
P/F, water objects, or build outputs. A FAIL is terminal for this solve.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import sparse

if sys.flags.optimize:
    raise RuntimeError("postsolve evidence rejects optimized Python")

G = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010")
ROOT = G / "G/wet-bank-pilot"
PREPDIR = ROOT / "prepared-runs/attempt-08"
OUTDIR = ROOT / "solve-once"
RESULT = OUTDIR / "solve-result.json"
SOLUTION = OUTDIR / "solution.npz"
CANDIDATE = OUTDIR / "unaccepted-candidate-terrain.npz"
PREP = PREPDIR / "prepared.npz"
PREP_RECEIPT = PREPDIR / "preparation.json"
PREFLIGHT_REVIEW = PREPDIR / "independent-review.json"
COVERAGE = ROOT / "coverage-consumer/candidate-run-01.json"
COVERAGE_SOURCE = ROOT / "coverage-consumer/check_coverage.py"
BASE = G / "global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz"
CP = G / "global-operator-prototype/face-slope-cone-pilot/pilot.py"
EV87 = Path(r"E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py")
EV88 = Path(r"E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/review-independent/verify_ev88q.py")

PINS = {
    str(PREP): "52409a8d074d15ec068bddc6e9265bc3782e84e9d54582b8a6d7b0a6675a787f",
    str(PREP_RECEIPT): "c582f45f0751e8c24db2672405de4b94c136ee16a9c33d5e4c35a8deee2200ed",
    str(PREFLIGHT_REVIEW): "c9e9946c0ab77bfb090fe1b4ec297a13c52ca8b41926bde8c0275db0feeffaf4",
    str(ROOT / "prepare_wet_bank_matrices.py"): "65e05a6540026b08df7effa53c58534121bb2fa89e116a2ef07ad46ba0edf286",
    str(COVERAGE_SOURCE): "1dc1464b86c0b0c7cd83b2fe5003de1149773dad7d3b2d1396209736fc383a77",
    str(BASE): "40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a",
    str(CP): "d743f5006e0aa6606024a3c3291a74cb52b78f76c1aa5c6dfd95cdd26cdc9d2a",
    str(EV87): "964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27",
    str(EV88): "82a988790e6bdfc0289bcb7c32cb0afd1210e07b264d92731aba266bc5980f78",
}
RESULT_SHA = "35722fa7b8f3235597ed6f82c5263da6320d2d030b3dbef3558728386c4240ca"
SOLUTION_SHA = "1b7a23ebb3c203427f1c77cb8de6becfca750746e47f5494bba6723b0610eab1"
CANDIDATE_SHA = "1c2a6b8b1dce5ed83c6360705e16c10225aa528c96ac02adcf868c554c019652"
COVERAGE_SHA = "f3321ba2b5bb1b551ad931f4d1f01580323410bbb8f8d493514f4c9800c5f6ba"
COVERAGE_SCRIPT_SHA = "1dc1464b86c0b0c7cd83b2fe5003de1149773dad7d3b2d1396209736fc383a77"
GEOM_WINDOW = (855, 870, 1179, 1194)
FOCUS = (862, 1186)
ANG_TOL_DEG = 1e-4


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def readcsr(z, prefix: str):
    return sparse.csr_matrix(
        (z[prefix + "_data"], z[prefix + "_indices"], z[prefix + "_indptr"]),
        shape=tuple(z[prefix + "_shape"]),
    )


def affected_cells(changed: np.ndarray) -> np.ndarray:
    out = np.zeros((changed.shape[0] - 1, changed.shape[1] - 1), dtype=bool)
    for r, c in np.argwhere(changed):
        for rr in (r - 1, r):
            for cc in (c - 1, c):
                if 0 <= rr < out.shape[0] and 0 <= cc < out.shape[1]:
                    out[rr, cc] = True
    return out


def self_test() -> dict:
    # Exact constraint semantics: a tiny negative slack is rejected, and a zero
    # slack is accepted. This prevents a hidden post-quantization tolerance.
    def exact_gate(slack):
        return bool(np.isfinite(slack).all() and np.all(slack >= 0.0))
    require(exact_gate(np.array([0.0, 1.0])), "zero-slack positive fixture failed")
    require(not exact_gate(np.array([-1.879736570842283e-7])), "negative-slack fixture was accepted")
    # Geometry cell incidence includes all four corners of each native cell.
    m = np.zeros((4, 4), dtype=bool); m[1, 1] = True
    cells = affected_cells(m)
    require(int(cells.sum()) == 4 and cells[0, 0] and cells[0, 1] and cells[1, 0] and cells[1, 1],
            "affected-cell incidence fixture failed")
    return {"exact_zero_slack_pass": True, "negative_slack_rejected": True,
            "four_incident_cells_detected": True}


def run() -> dict:
    require(sha(RESULT) == RESULT_SHA, "solve result hash mismatch")
    require(sha(SOLUTION) == SOLUTION_SHA, "solution NPZ hash mismatch")
    require(sha(CANDIDATE) == CANDIDATE_SHA, "candidate NPZ hash mismatch")
    require(sha(COVERAGE) == COVERAGE_SHA, "coverage report hash mismatch")
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    prep_receipt = json.loads(PREP_RECEIPT.read_text(encoding="utf-8"))
    review = json.loads(PREFLIGHT_REVIEW.read_text(encoding="utf-8"))
    coverage = json.loads(COVERAGE.read_text(encoding="utf-8"))
    require(result.get("status") == "UNACCEPTED_WET_BANK_SOLVE_OUTPUT", "unexpected solver terminal status")
    require(result.get("solver", {}).get("status") == "CONVERGED", "solver did not converge")
    require(result.get("readset_stable") is True and result.get("readset_start") == result.get("readset_end"),
            "solver readset is unstable")
    require(review.get("status") == "PASS_WET_BANK_PREFLIGHT_ONLY" and review.get("ready_for_one_solve") is True,
            "the pinned preflight did not authorize the solve")
    require(review.get("prepared_sha256") == PINS[str(PREP)] and review.get("source_sha256") == PINS[str(ROOT / "prepare_wet_bank_matrices.py")],
            "preflight receipt does not bind the prepared/source")
    require(prep_receipt.get("prepared_sha256") == PINS[str(PREP)], "preparation receipt mismatch")
    for path, expected in PINS.items():
        require(sha(Path(path)) == expected, f"pinned input changed: {path}")
    for path, expected in result["readset_start"].items():
        require(result["readset_end"].get(path) == expected, f"solve start/end readset mismatch: {path}")
        require(sha(Path(path)) == expected, f"solve input changed since run: {path}")
    require(result.get("outputs", {}).get("solution.npz") == SOLUTION_SHA, "solver output hash mismatch")
    require(result.get("outputs", {}).get("unaccepted-candidate-terrain.npz") == CANDIDATE_SHA,
            "candidate output hash mismatch")
    require(sha(COVERAGE_SOURCE) == COVERAGE_SCRIPT_SHA, "coverage consumer source changed")
    require(coverage.get("status") == "PASS_LOCAL_COMPILED_WATER_CANDIDATE", "compiled-water coverage did not pass")
    require(coverage.get("prepared_bounds_sha256") == PINS[str(PREP)], "coverage did not use pinned bounds")
    require(coverage.get("source_pins_start") == coverage.get("source_pins_end"), "coverage readset changed")
    cov_sources = coverage.get("source_pins_start", {})
    require(cov_sources.get(str(CANDIDATE)) == CANDIDATE_SHA, "coverage did not bind this candidate")
    require(cov_sources.get(str(COVERAGE_SOURCE)) == COVERAGE_SCRIPT_SHA, "coverage did not bind its checker")
    require(all(coverage.get("coverage", {}).get("gates", {}).values()), "compiled-water coverage has a false gate")

    base_npz = np.load(BASE, allow_pickle=False)
    prep = np.load(PREP, allow_pickle=False)
    sol = np.load(SOLUTION, allow_pickle=False)
    cand = np.load(CANDIDATE, allow_pickle=False)
    try:
        base_h = base_npz["heights"]
        candidate_h = cand["heights"]
        base_ctx = prep["base_heights_context"]
        rc = prep["variables_rc"].astype(np.int64)
        origin = np.array([GEOM_WINDOW[0], GEOM_WINDOW[2]], dtype=np.int64)
        nodes = rc - origin
        require(candidate_h.shape == base_h.shape == (2048, 2048), "full terrain shape mismatch")
        require(candidate_h.dtype == base_h.dtype == np.dtype("float32"), "terrain height dtype mismatch")
        require(base_ctx.dtype == np.dtype("float32") and np.array_equal(
            base_ctx.view(np.uint32), base_h[GEOM_WINDOW[0]:GEOM_WINDOW[1], GEOM_WINDOW[2]:GEOM_WINDOW[3]].view(np.uint32)),
            "prepared baseline context differs from pinned baseline")
        require(np.array_equal(sol["baseline_float32"].view(np.uint32), base_ctx.view(np.uint32)),
                "solution baseline context changed")
        raw_ctx = sol["raw_float32_grid"]
        closed_ctx = sol["closed_float32_grid"]
        require(np.array_equal(candidate_h[GEOM_WINDOW[0]:GEOM_WINDOW[1], GEOM_WINDOW[2]:GEOM_WINDOW[3]].view(np.uint32),
                               closed_ctx.view(np.uint32)), "candidate context differs from closed solution")
        changed_all = candidate_h.view(np.uint32) != base_h.view(np.uint32)
        expected_changed = np.zeros_like(changed_all)
        expected_changed[tuple(rc.T)] = candidate_h[tuple(rc.T)].view(np.uint32) != base_h[tuple(rc.T)].view(np.uint32)
        require(np.array_equal(changed_all, expected_changed), "candidate changed terrain outside the 121-node domain")
        changed_rc = np.argwhere(changed_all)
        require(len(changed_rc) == 114 and len(changed_rc) == int(result["diagnostics"]["changed_vertices"]),
                "changed vertex count mismatch")
        # All non-height data in the candidate must be bit-identical to baseline.
        require(set(cand.files) == set(base_npz.files), "candidate terrain fields differ from baseline")
        metadata_equal = {}
        for key in base_npz.files:
            if key == "heights":
                continue
            metadata_equal[key] = bool(np.array_equal(cand[key], base_npz[key], equal_nan=True))
        require(all(metadata_equal.values()), "candidate changed non-height terrain data")

        x = closed_ctx[tuple(nodes.T)].astype(np.float64)
        raw_x = raw_ctx[tuple(nodes.T)].astype(np.float64)
        lo = prep["lo_absolute_float32_inward"].astype(np.float64)
        hi = prep["hi_absolute_float32_inward"].astype(np.float64)
        bound_slack_lo = x - lo
        bound_slack_hi = hi - x
        bounds_ok = bool(np.all(bound_slack_lo >= 0.0) and np.all(bound_slack_hi >= 0.0))

        Cd = readcsr(prep, "C_d8"); Ccross = readcsr(prep, "C_cross")
        d8_slack = np.asarray(Cd @ x - prep["d_C_d8"], dtype=np.float64).ravel()
        cross_slack = np.asarray(Ccross @ x - prep["d_C_cross"], dtype=np.float64).ravel()
        full_C_slack = np.concatenate((d8_slack, cross_slack))
        cross_meta = json.loads(prep["crossing_rows_json"].tobytes().decode("utf-8"))[:len(cross_slack)]
        require(len(cross_meta) == len(cross_slack), "crossing metadata does not cover all C_cross rows")
        worst_cross = int(np.argmin(cross_slack))
        cross_by_type = Counter()
        cross_by_surface = Counter()
        for meta, slack in zip(cross_meta, cross_slack):
            if slack < 0.0:
                cross_by_type[meta["type"]] += 1
                cross_by_surface[meta["surface"]] += 1

        # Verify saved closed field is exactly the frozen deterministic D8
        # projection of saved raw float32, within the same absolute box.
        cp = load_module("wet_postsolve_pilot", CP)
        closure_mod = cp.load_order_closure()
        flat_lower = base_ctx.ravel().copy(); flat_upper = flat_lower.copy()
        local_ids = np.ravel_multi_index(tuple(nodes.T), base_ctx.shape)
        flat_lower[local_ids] = lo.astype(np.float32)
        flat_upper[local_ids] = hi.astype(np.float32)
        fixed = np.ones(base_ctx.size, dtype=bool); fixed[local_ids] = False
        witnesses = prep["d8_witnesses_local"].astype(np.int64)
        edges = np.column_stack((np.ravel_multi_index(tuple(witnesses[:, 2:].T), base_ctx.shape),
                                 np.ravel_multi_index(tuple(witnesses[:, :2].T), base_ctx.shape)))
        closure = closure_mod.project_order(raw_ctx.ravel(), flat_lower, flat_upper, edges,
                                            baseline=base_ctx.ravel(), fixed=fixed)
        closure_reproduced = np.array_equal(closure["q"].reshape(base_ctx.shape).view(np.uint32),
                                            closed_ctx.view(np.uint32))
        require(closure_reproduced, "saved D8 closure does not reproduce exactly from raw float32")
        A = readcsr(prep, "A")
        rhs = prep["rhs_A"]
        cost = lambda v: 0.5 * float(np.sum((A @ v - rhs) ** 2))
        objective = {"baseline": cost(prep["x0_absolute"]), "raw": cost(raw_x), "closed": cost(x)}
        closure_energy = closure_mod.evaluate_objective_gates(objective["raw"], objective["closed"], objective["baseline"])

        Gmat = readcsr(prep, "G")
        q = (Gmat @ x + prep["k_G"]).reshape(-1, 2)
        cone_excess = np.linalg.norm(q, axis=1) - prep["radii_G"]
        cone_ok = bool(np.all(cone_excess <= 0.0))

        # Independent terrain-surface measurement from EV87/EV88 definitions.
        ev87 = load_module("wet_postsolve_ev87", EV87)
        ev88 = load_module("wet_postsolve_ev88q", EV88)
        before_f64 = base_h.astype(np.float64)
        after_f64 = candidate_h.astype(np.float64)
        before_slopes = ev87.slopes(before_f64)
        after_slopes = ev87.slopes(after_f64)
        affected = affected_cells(changed_all)
        slope_rows = []
        slope_ok = True
        for tri_i, (b, a) in enumerate(zip(before_slopes, after_slopes)):
            limits = np.maximum(35.0, b[affected]) + ANG_TOL_DEG
            current = a[affected]
            excess = current - limits
            local_pass = bool(np.all(excess <= 0.0))
            slope_ok &= local_pass
            slope_rows.append({"triangle": tri_i, "affected_faces": int(current.size),
                               "before_max_deg": float(np.max(b[affected])),
                               "after_max_deg": float(np.max(current)),
                               "max_excess_over_max35_or_base_plus_1e4_deg": float(np.max(excess)),
                               "pass": local_pass})
        before_edges = list(ev87.edge_angles(before_f64)); after_edges = list(ev87.edge_angles(after_f64))
        hinge_rows = []
        p99_ok = True; no_new_over30 = True
        for (kind_b, b), (kind_a, a) in zip(before_edges, after_edges):
            require(kind_b == kind_a, "edge-angle kind ordering changed")
            mask = ev87.incident_any(changed_all, kind_b)
            bv = np.asarray(b[mask], dtype=np.float64); av = np.asarray(a[mask], dtype=np.float64)
            new_over = int(np.count_nonzero((bv <= 30.0) & (av > 30.0)))
            before_p99 = float(np.percentile(bv, 99)) if bv.size else 0.0
            after_p99 = float(np.percentile(av, 99)) if av.size else 0.0
            p99_ok &= after_p99 <= before_p99
            no_new_over30 &= new_over == 0
            hinge_rows.append({"kind": kind_b, "affected_edges": int(av.size),
                               "before_p99_deg": before_p99, "after_p99_deg": after_p99,
                               "new_edges_over_30deg": new_over,
                               "before_max_deg": float(np.max(bv)) if bv.size else 0.0,
                               "after_max_deg": float(np.max(av)) if av.size else 0.0})
        # The pilot pins its target hinge in the prepared hinge list; use that
        # exact kind/anchor instead of substituting a different vertex-local
        # maximum from EV88.
        target_i = int(np.argmax(prep["hinge_angle_before_deg"]))
        target_kind = {0: "diag", 1: "vertical", 2: "horizontal"}[int(prep["hinge_kind"][target_i])]
        target_local = prep["hinge_rc_local"][target_i].astype(int)
        target_global = target_local + np.array([GEOM_WINDOW[0], GEOM_WINDOW[2]])
        before_edge_map = dict(before_edges); after_edge_map = dict(after_edges)
        target_before = float(before_edge_map[target_kind][tuple(target_global)])
        target_after = float(after_edge_map[target_kind][tuple(target_global)])
        require(abs(target_before - float(prep["hinge_angle_before_deg"][target_i])) <= 1e-10,
                "prepared target hinge does not match independently recomputed B")
        focus_drop = target_before - target_after
        focus_pass = bool(focus_drop >= 2.0)

        result_checks = {
            "solve_lineage_and_inputs": True,
            "candidate_is_exact_closed_grid_and_only_variable_nodes_changed": True,
            "non_height_fields_bit_identical": True,
            "float32_physical_bounds_exact": bounds_ok,
            "D8_constraints_exact": bool(np.all(d8_slack >= 0.0)),
            "P_F_sign_and_crossing_constraints_exact": bool(np.all(cross_slack >= 0.0)),
            "native_slope_contract": slope_ok,
            "native_hinge_p99_nonworse": p99_ok,
            "no_new_hinge_over_30deg": no_new_over30,
            "focus_hinge_drop_at_least_2deg": focus_pass,
            "EV93_cones_exact": cone_ok,
            "closure_reproduced_and_energy_budget": bool(closure_reproduced and closure_energy["closure_budget_pass"]),
            "compiled_water_coverage_report_pass": True,
        }
        failures = [k for k, v in result_checks.items() if not v]
        return {
            "schema": "ev94.oredezh-wet-bank-postsolve-review.v1",
            "status": "FAIL_POSTSOLVE_GATES" if failures else "PASS_LOCAL_POSTSOLVE_GATES",
            "accepted": False,
            "scope": "isolated Oredezh wet-bank pilot only; not whole-map, packaged, deployed, or visual acceptance",
            "inputs": {"solve_result": {"path": str(RESULT), "sha256": sha(RESULT)},
                       "solution_npz": {"path": str(SOLUTION), "sha256": sha(SOLUTION)},
                       "candidate_npz": {"path": str(CANDIDATE), "sha256": sha(CANDIDATE)},
                       "prepared_npz": {"path": str(PREP), "sha256": sha(PREP)},
                       "prepared_receipt": {"path": str(PREP_RECEIPT), "sha256": sha(PREP_RECEIPT)},
                       "preflight_review": {"path": str(PREFLIGHT_REVIEW), "sha256": sha(PREFLIGHT_REVIEW)},
                       "coverage_report": {"path": str(COVERAGE), "sha256": sha(COVERAGE)},
                       "coverage_source_sha256": sha(COVERAGE_SOURCE),
                       "source_readset_start_end_stable": result["readset_start"]},
            "solver": {"status": result["solver"]["status"], "iterations": result["solver"]["iteration"],
                       "elapsed_numerical_s": result["elapsed_numerical_s"], "primal": result["solver"]["primal"],
                       "dual": result["solver"]["dual"], "stationarity": result["solver"]["stationarity"],
                       "objective": objective, "reported_objective": result["objective"],
                       "closure": result["closure"], "closure_energy": closure_energy},
            "checks": result_checks,
            "failed_checks": failures,
            "constraints": {"D8": {"rows": int(len(d8_slack)), "min_slack": float(d8_slack.min()),
                                     "negative_count_exact": int(np.count_nonzero(d8_slack < 0.0))},
                            "P_F_sign_and_crossings": {"rows": int(len(cross_slack)),
                                     "min_slack": float(cross_slack.min()),
                                     "negative_count_exact": int(np.count_nonzero(cross_slack < 0.0)),
                                     "negative_by_type": dict(cross_by_type), "negative_by_surface": dict(cross_by_surface),
                                     "worst_row": {"index": worst_cross, "slack": float(cross_slack[worst_cross]),
                                                   "metadata": cross_meta[worst_cross]},
                                     "tolerance": 0.0,
                                     "tolerance_basis": "PLAN/RUN_PROTOCOL require post-quantization recheck; no C-cross tolerance is declared. The -1e-9 check in preparation source applies to baseline feasibility only."},
                            "all_C_min_slack": float(full_C_slack.min()),
                            "bounds": {"pass": bounds_ok, "min_lower_slack": float(bound_slack_lo.min()),
                                       "min_upper_slack": float(bound_slack_hi.min())},
                            "cones": {"pass": cone_ok, "max_norm_excess": float(cone_excess.max()),
                                      "min_margin": float(-cone_excess.max())}},
            "geometry": {"changed_vertices": int(len(changed_rc)), "affected_cells": int(affected.sum()),
                         "slope_faces": slope_rows, "hinges": hinge_rows,
                         "focus": {"focus_rc": list(FOCUS), "target_hinge_kind": target_kind,
                                   "target_hinge_anchor_rc": target_global.tolist(),
                                   "before_deg": target_before, "after_deg": target_after,
                                   "drop_deg": focus_drop, "required_drop_deg": 2.0},
                         "compiled_water": {"report_status": coverage["status"],
                                            "gates": coverage["coverage"]["gates"],
                                            "unknown_face_intersections": len(coverage["coverage"]["unknown_face_intersections"]),
                                            "physical": coverage["coverage"]["metrics"]["physical"],
                                            "visible": coverage["coverage"]["metrics"]["visible"]}},
            "limitations": ["The single negative P/F C_cross residual fails the exact prepared inequality; this consumer does not relax it.",
                            "No visual or in-game verification was performed.",
                            "Water component connectivity and outside-channel extrema were not separately recomputed here."],
        }
    finally:
        for z in (base_npz, prep, sol, cand):
            z.close()


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "postsolve-consumer/postsolve-review.json")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps({"status": "PASS", "fixtures": self_test()}, indent=2))
        return 0
    report = run()
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "failed_checks": report["failed_checks"],
                      "output": str(args.output)}, allow_nan=False))
    return 0 if report["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
