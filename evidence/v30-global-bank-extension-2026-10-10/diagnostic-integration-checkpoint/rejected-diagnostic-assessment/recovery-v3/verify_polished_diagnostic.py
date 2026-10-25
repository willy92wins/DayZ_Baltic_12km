#!/usr/bin/env python
"""Independent, non-promoting consumer for a one-ULP polished diagnostic.

The diagnostic receipt remains explicitly unaccepted. Real inputs are opened only
through explicit compose/verify modes and caller-pinned hashes; self-test is synthetic.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import sys
import time
import unittest
import zipfile

if sys.flags.optimize:
    raise RuntimeError("evidence consumer rejects optimized Python")

import numpy as np
from scipy import sparse
from shapely.geometry import Polygon
from shapely.ops import unary_union
import shapely

G = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010")
ROOT = G / "G/wet-bank-pilot"
HERE = ROOT / "postsolve-consumer/diagnostic-polish-consumer-v1"
PLAN = HERE / "PLAN.md"
TESTS = HERE / "test_polished_diagnostic.py"
PREPDIR = ROOT / "prepared-runs/attempt-08"
PREP = PREPDIR / "prepared.npz"
PREP_RECEIPT = PREPDIR / "preparation.json"
PREFLIGHT_REVIEW = PREPDIR / "independent-review.json"
BASE = G / "global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz"
PREVIOUS_SOLVE = ROOT / "solve-once/solution.npz"
PREVIOUS_RESULT = ROOT / "solve-once/solve-result.json"
PREVIOUS_CANDIDATE = ROOT / "solve-once/unaccepted-candidate-terrain.npz"
EXECUTOR = ROOT / "postsolve-consumer/float32-neighborhood-v1/executor.py"
POLISH_ROOT = ROOT / "postsolve-consumer/float32-component-conversion-v1/robust-f32-design/candidate-only-milp/d8-sign-fix-v1"
P_PATH = G / "build-focal/candidate/plane.npy"
F_PATH = G / "build-focal/candidate/visible-field.npy"
DESIGN = Path(r"E:/DayZ-Baltic-Build/v30-v11/design/water_v3.geojson")
EV87 = Path(r"E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py")
EV88 = Path(r"E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/review-independent/verify_ev88q.py")
COVERAGE_CHECK = ROOT / "coverage-consumer/check_coverage.py"
WATER_CONSUMER = G / "consumer-global/verify_layer.py"
CIVIL = G / "global-operator-prototype/global-civil-ev95/run-01/inventory.json"
INDEX_MANIFEST = G / "ev93-face-index/runs/20261010T092417Z-63d4cec3/manifest.json"
INDEX_BUILDER = G / "ev93-face-index/build_face_index.py"
PBO_WATER = Path(r"P:/Mods/@DayZ_Baltic_EV95_WideBankPreviewV1/Addons/baltic_water_v30.pbo")
PBO_WORLD = PBO_WATER.with_name("narva_trial.pbo")
STAGE = G / "build-wide-slope/stage.json"
DEPLOY = G / "build-wide-slope/deploy.json"

WIN = (855, 870, 1179, 1194)  # [r0,r1) x [c0,c1)
CORE = (857, 868, 1181, 1192)
FOCUS = (862, 1186)
ANG_TOL_DEG = 1e-4
EXPECTED_SHAPELY = "2.1.2"
EXPECTED = {
    PREP: "52409a8d074d15ec068bddc6e9265bc3782e84e9d54582b8a6d7b0a6675a787f",
    PREP_RECEIPT: "c582f45f0751e8c24db2672405de4b94c136ee16a9c33d5e4c35a8deee2200ed",
    PREFLIGHT_REVIEW: "c9e9946c0ab77bfb090fe1b4ec297a13c52ca8b41926bde8c0275db0feeffaf4",
    BASE: "40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a",
    PREVIOUS_SOLVE: "1b7a23ebb3c203427f1c77cb8de6becfca750746e47f5494bba6723b0610eab1",
    PREVIOUS_RESULT: "35722fa7b8f3235597ed6f82c5263da6320d2d030b3dbef3558728386c4240ca",
    PREVIOUS_CANDIDATE: "1c2a6b8b1dce5ed83c6360705e16c10225aa528c96ac02adcf868c554c019652",
    EXECUTOR: "9a0dbffc55e9956209083fe4963e2636b6f0174de1dc150bdfa15f070d48149e",
    P_PATH: "768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0",
    F_PATH: "f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c",
    DESIGN: "caa333e365c2a4511f839937a9d76a5aa157a0ef925d6ee4b5efcc4ebb38f8a9",
    EV87: "964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27",
    EV88: "82a988790e6bdfc0289bcb7c32cb0afd1210e07b264d92731aba266bc5980f78",
    COVERAGE_CHECK: "1dc1464b86c0b0c7cd83b2fe5003de1149773dad7d3b2d1396209736fc383a77",
    WATER_CONSUMER: "33050881caaf5e75f288d4122222c15eb326bf146c28a4c723760564457b3dc2",
    CIVIL: "cdebbbce50644407642e791388e44c40b15499041844607650b885d1bc618856",
    INDEX_MANIFEST: "c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c",
    PBO_WATER: "3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14",
    PBO_WORLD: "f1a148cab3e7d1d63473f0232a0971d45a9fea04e0fb456f01973235f4644b7d",
    STAGE: "b04b066d99f9c22a4fffd77c66762d3e9e744dfa2bbf20d8508f076845571dda",
    DEPLOY: "f5a9c8185812e0b77a804ef9811e0405b5a7969f8ccfc19b85cc29d23cac03ca",
}


class ConsumerStop(RuntimeError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha_readset(paths) -> dict[str, str]:
    return {str(Path(p).resolve()): sha256(Path(p)) for p in sorted(set(map(Path, paths)), key=lambda p: str(p).casefold())}


def require(ok: bool, message: str):
    if not ok:
        raise ConsumerStop(message)


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def fixed_source_readset() -> dict[str, str]:
    require(shapely.__version__ == EXPECTED_SHAPELY,
            f"Shapely version changed: {shapely.__version__} != {EXPECTED_SHAPELY}")
    for path, expected in EXPECTED.items():
        actual = sha256(path)
        require(actual == expected, f"pinned input changed: {path}; {actual} != {expected}")
    return sha_readset([*EXPECTED.keys(), PLAN, Path(__file__), TESTS])


def verify_logical_source_readset(readset: dict, preparer) -> int:
    """Resolve the preparation receipt's logical keys through its pinned producer."""
    paths = getattr(preparer, "PATHS", None)
    expected = getattr(preparer, "EXPECTED", None)
    require(isinstance(paths, dict) and isinstance(expected, dict),
            "pinned preparation module lacks PATHS/EXPECTED maps")
    # The producer intentionally leaves retained_selection outside EXPECTED:
    # it is a data-selected dependency, but its digest is still bound by the
    # pinned preparation receipt and rehashed from PATHS below.
    dynamic_keys = set(paths) - set(expected)
    require(dynamic_keys == {"retained_selection"} and set(readset) == set(paths) and
            set(expected) == set(paths) - dynamic_keys,
            "logical source readset keys differ from pinned producer schema")
    for key in sorted(paths):
        if key in expected:
            require(str(readset[key]).lower() == str(expected[key]).lower(),
                    f"logical source readset expected hash differs: {key}")
        actual = sha256(Path(paths[key]))
        require(actual.lower() == str(readset[key]).lower(),
                f"logical preparation input changed: {key} -> {paths[key]}")
    return len(readset)


def verify_retained_path_readset(readset: dict) -> int:
    """Retained-unit keys are paths (unlike preparation source keys)."""
    require(isinstance(readset, dict) and readset,
            "retained-unit path readset missing/empty")
    for raw_path, expected in readset.items():
        path = Path(raw_path)
        require(path.is_absolute(), f"retained-unit key is not an absolute path: {raw_path}")
        actual = sha256(path)
        require(actual.lower() == str(expected).lower(),
                f"retained-unit input changed: {raw_path}")
    return len(readset)


def verify_preflight(prepared: dict, prep_receipt: dict, review: dict, preparer) -> dict:
    require(prep_receipt.get("status") == "PREPARED_NO_SOLVE", "prepared receipt status mismatch")
    require(prep_receipt.get("prepared_sha256") == EXPECTED[PREP], "prepared receipt SHA mismatch")
    require(review.get("status") == "PASS_WET_BANK_PREFLIGHT_ONLY" and review.get("ready_for_one_solve") is True,
            "independent preflight did not pass")
    require(review.get("prepared_sha256") == EXPECTED[PREP] and review.get("preparation_sha256") == EXPECTED[PREP_RECEIPT],
            "preflight review does not bind the pinned prepared data")
    require(review.get("checks") and all(v is True for v in review["checks"].values()),
            "independent preflight has a false/missing check")
    require(prep_receipt.get("source_readset_start") == prep_receipt.get("source_readset_end"),
            "preparation source readset changed")
    require(prep_receipt.get("retained_unit_readset_start") == prep_receipt.get("retained_unit_readset_end"),
            "retained-unit readset changed")
    retained = prep_receipt.get("retained_unit_readset_start", {})
    require(len(retained) == 666 and prep_receipt["protection"].get("retained_units_checked") == 499,
            "retained population is not the frozen 499-unit contract")
    require(prep_receipt["protection"].get("overlap_retained_windows") == 0 and
            prep_receipt["protection"].get("other_fixed_reconstruction_exact") is True and
            prep_receipt["protection"].get("EV79_fixed_reconstruction_exact") is True and
            prep_receipt["protection"].get("narva_mask_reconstruction_exact") is True,
            "prepared protection/exclusion contract is not exact")
    logical_count = verify_logical_source_readset(prep_receipt["source_readset_start"], preparer)
    verify_logical_source_readset(prep_receipt["source_readset_end"], preparer)
    retained_count = verify_retained_path_readset(prep_receipt["retained_unit_readset_start"])
    verify_retained_path_readset(prep_receipt["retained_unit_readset_end"])
    vars_rc = np.asarray(prepared["variables_rc"])
    expected_rc = np.asarray([(r, c) for r in range(CORE[0], CORE[1]) for c in range(CORE[2], CORE[3])], dtype=np.int32)
    require(vars_rc.dtype == np.int32 and np.array_equal(vars_rc, expected_rc),
            "prepared variable set is not the exact row-major 121-node core")
    require(prepared["base_heights_context"].shape == (15, 15) and
            prepared["base_heights_context"].dtype == np.float32,
            "prepared context shape/dtype mismatch")
    for key in ("other_fixed_context", "effective_fixed_context", "p9_context", "road_context",
                "design_interior_context", "shore_boundary_context"):
        require(key in prepared and prepared[key].shape == (15, 15), f"prepared mask missing/malformed: {key}")
    require(prepared["face_xyz"].shape == (200, 3, 3) and prepared["face_plane_y_xz"].shape == (200, 3) and
            prepared["face_population_cells_rc"].shape == (144, 2),
            "prepared 200-face/144-cell coverage population changed")
    require(prepared["d8_witnesses_local"].shape == (150, 4), "prepared D8 witness population changed")
    require(prepared["radii_G"].shape == (392,), "prepared face-cone population changed")
    return {"logical_source_keys": logical_count, "retained_paths": retained_count, "retained_units": 499,
            "variable_count": int(len(vars_rc)), "prepared_face_count": int(len(prepared["face_xyz"])),
            "prepared_cell_count": int(len(prepared["face_population_cells_rc"]))}


def arrays_from_npz(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def previous_solve_metadata(result: dict, expected_solution_sha: str,
                            expected_candidate_sha: str) -> dict:
    require(result.get("status") == "UNACCEPTED_WET_BANK_SOLVE_OUTPUT" and
            result.get("solver", {}).get("status") == "CONVERGED",
            "pinned source solve is not the expected converged, unaccepted solve")
    require(result.get("readset_stable") is True and
            result.get("readset_start") == result.get("readset_end"),
            "source solve readset is unstable")
    outputs = result.get("outputs", {})
    require(outputs.get("solution.npz") == expected_solution_sha and
            outputs.get("unaccepted-candidate-terrain.npz") == expected_candidate_sha,
            "source solve output hashes do not match the frozen solve lineage")
    return {"status": result["solver"]["status"], "readset": result["readset_start"],
            "outputs": outputs}


def verify_previous_solve_lineage(result: dict, solution_path: Path = PREVIOUS_SOLVE,
                                  candidate_path: Path = PREVIOUS_CANDIDATE) -> dict:
    metadata = previous_solve_metadata(result, EXPECTED[solution_path], EXPECTED[candidate_path])
    require(sha256(solution_path) == EXPECTED[solution_path] and
            sha256(candidate_path) == EXPECTED[candidate_path],
            "source solve output artifact changed")
    readset = metadata["readset"]
    for path, expected in readset.items():
        require(sha256(Path(path)) == expected, f"source solve input changed: {path}")
    return {"status": metadata["status"], "readset_paths": len(readset),
            "solution_sha256": metadata["outputs"]["solution.npz"],
            "unaccepted_candidate_sha256": metadata["outputs"]["unaccepted-candidate-terrain.npz"]}


def validate_polished_diagnostic(diagnostic_path: Path, diagnostic_sha: str,
                                 polish_receipt_path: Path, polish_receipt_sha: str,
                                 prepared: dict, previous_solution: dict) -> tuple[np.ndarray, dict, dict]:
    """Validate the exact one-node ULP diagnostic lineage; never treats it as accepted terrain."""
    require(sha256(diagnostic_path) == diagnostic_sha.lower(), "polished diagnostic SHA mismatch")
    require(sha256(polish_receipt_path) == polish_receipt_sha.lower(), "polish receipt SHA mismatch")
    receipt = load_json(polish_receipt_path)
    read0 = validate_polish_receipt_envelope(receipt, diagnostic_path, diagnostic_sha)
    require(receipt.get("approved_script_sha256") == EXPECTED[POLISH_SOURCE] and
            receipt.get("approved_plan_sha256") == EXPECTED[POLISH_PLAN],
            "receipt does not bind the frozen neighbor-polish source and plan")
    require(receipt.get("neighbor_count") == receipt.get("expected_neighbor_count") == 242 and
            receipt.get("eligible_neighbor_count", 0) >= 1 and
            isinstance(receipt.get("elapsed_seconds"), (int, float)) and
            0.0 <= float(receipt["elapsed_seconds"]) <= 60.0,
            "receipt does not describe the complete 242-neighbor diagnostic enumeration")
    for path, expected in read0.items():
        require(sha256(Path(path)) == expected, f"polish source changed since enumeration: {path}")
    for required_path in (POLISH_SOURCE, POLISH_PLAN, POLISH_TESTS, POLISH_BASE_RECEIPT,
                          POLISH_BASE_DIAGNOSTIC, PREVIOUS_SOLVE):
        resolved = str(required_path.resolve())
        require(read0.get(resolved) == EXPECTED[required_path],
                f"polish receipt readset omits/mismatches required lineage input: {required_path}")
    ledger_path = ledger_path_from_receipt(receipt)
    ledger_info = receipt.get("ledger") or {"path": receipt.get("ledger_path"),
                                             "sha256": receipt.get("ledger_sha256")}
    require(sha256(ledger_path) == ledger_info["sha256"], "polish ledger SHA mismatch")
    rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    chosen = validate_neighbor_ledger(rows)
    best = receipt.get("best_neighbor")
    require(isinstance(best, dict) and best.get("eligible") is True and
            (int(best["variable_index"]), tuple(best["rc"]), int(best["step"])) ==
            (int(chosen["variable_index"]), tuple(chosen["rc"]), int(chosen["step"])) and
            float(best["closed_cost"]) == float(chosen["closed_cost"]),
            "receipt-selected neighbor is not the deterministic minimum eligible ledger row")
    artifact_info = receipt.get("polished_diagnostic", {})
    require(artifact_info.get("accepted") is False and artifact_info.get("terrain_written") is False and
            Path(artifact_info.get("path", "")).resolve() == diagnostic_path.resolve() and
            artifact_info.get("sha256") == diagnostic_sha.lower(),
            "polish receipt does not bind the supplied diagnostic artifact as unaccepted")
    with np.load(diagnostic_path, allow_pickle=False) as z:
        require(set(z.files) == {"context_grid", "source_rejected_grid", "variables_rc", "source_lattice_m",
                                 "changed_variable_index", "changed_step", "source_diagnostic_sha256"},
                "polished diagnostic NPZ schema mismatch")
        candidate = z["context_grid"].copy()
        source = z["source_rejected_grid"].copy()
        variables = z["variables_rc"].copy()
        lattice = z["source_lattice_m"].copy()
        index = int(z["changed_variable_index"])
        step = int(z["changed_step"])
        source_sha = str(z["source_diagnostic_sha256"].item())
    require(candidate.shape == source.shape == (15, 15) and
            candidate.dtype == source.dtype == np.float32 and
            np.isfinite(candidate).all() and np.isfinite(source).all(),
            "polished/source context must be finite float32 15x15")
    require(variables.dtype == np.int32 and np.array_equal(variables, prepared["variables_rc"]),
            "polished diagnostic variable list differs from prepared 121-node core")
    require(lattice.dtype == np.int64 and lattice.shape == (121,), "source lattice vector malformed")
    require(source_sha == EXPECTED[POLISH_BASE_DIAGNOSTIC], "polished artifact source diagnostic pin mismatch")
    with np.load(POLISH_BASE_DIAGNOSTIC, allow_pickle=False) as z:
        source_original = z["context_grid"].copy()
        source_lattice = z["lattice_m"].copy()
        source_variables = z["variables_rc"].copy()
    require(np.array_equal(source.view(np.uint32), source_original.view(np.uint32)) and
            np.array_equal(lattice, source_lattice) and np.array_equal(variables, source_variables),
            "polished diagnostic does not preserve the exact rejected-source context/lattice")
    bctx = np.asarray(prepared["base_heights_context"], dtype=np.float32)
    require(bctx.shape == source.shape == (15, 15) and bctx.dtype == np.float32,
            "prepared baseline context schema mismatch")
    core_mask = np.zeros((15, 15), dtype=bool)
    local_variables = variables - np.asarray([WIN[0], WIN[2]], dtype=np.int32)
    require(np.all((local_variables >= 0) & (local_variables < 15)), "diagnostic variable outside context")
    core_mask[tuple(local_variables.T)] = True
    raw_grid = np.asarray(previous_solution["raw_float32_grid"])
    closed_grid = np.asarray(previous_solution["closed_float32_grid"])
    require(raw_grid.shape == closed_grid.shape == (2048, 2048) and
            raw_grid.dtype == closed_grid.dtype == np.float32 and
            np.array_equal(raw_grid.view(np.uint32), closed_grid.view(np.uint32)),
            "pinned previous raw/closed full-grid diagnostic schema or identity changed")
    require(np.array_equal(source.view(np.uint32)[~core_mask], bctx.view(np.uint32)[~core_mask]),
            "rejected diagnostic changed the 104 fixed collar cells")
    require(np.array_equal(source.view(np.uint32), previous_solution["raw_float32_grid"][WIN[0]:WIN[1], WIN[2]:WIN[3]].view(np.uint32)),
            "rejected-source context differs from pinned prior raw solve")
    rc = validate_one_ulp_context(source, candidate, bctx, variables, index, step)
    require(tuple(map(int, best["rc"])) == rc and
            tuple(map(int, artifact_info.get("changed_rc", []))) == rc and
            int(artifact_info.get("step")) == step == int(best["step"]),
            "receipt and artifact disagree on selected coordinate/ULP step")
    expected = source.copy()
    direction = np.float32(-np.inf if step < 0 else np.inf)
    expected[tuple(np.asarray(rc) - np.asarray([WIN[0], WIN[2]]))] = np.nextafter(
        source[tuple(np.asarray(rc) - np.asarray([WIN[0], WIN[2]]))], direction, dtype=np.float32)
    require(np.array_equal(candidate.view(np.uint32), expected.view(np.uint32)),
            "polished grid is not exactly one selected one-ULP neighbor of the rejected diagnostic")
    require(np.array_equal(candidate.view(np.uint32)[~core_mask], bctx.view(np.uint32)[~core_mask]),
            "polish altered a fixed context/collar node")
    selected_row = next(row for row in rows if int(row["variable_index"]) == index and int(row["step"]) == step)
    require(float(selected_row["height_float32"]) == float(candidate[rc[0]-WIN[0], rc[1]-WIN[2]]) and
            selected_row.get("eligible") is True,
            "selected ledger record does not encode the supplied one-ULP candidate")
    return candidate, receipt, {"ledger_path": str(ledger_path.resolve()),
        "ledger_sha256": ledger_info["sha256"], "ledger_rows": len(rows),
        "selected_variable_index": index, "selected_rc": list(rc), "selected_step": step,
        "selected_cost": float(selected_row["closed_cost"]), "source_readset_count": len(read0)}


def validate_polish_receipt_envelope(receipt: dict, diagnostic_path: Path, diagnostic_sha: str) -> dict:
    require(receipt.get("schema") == "candidate-only-milp.energy-neighbor-polish.v1" and
            receipt.get("status") == "DIAGNOSTIC_NEIGHBOR_UNACCEPTED" and
            receipt.get("accepted") is False and receipt.get("terrain_written") is False and
            receipt.get("solver_calls") == 0, "receipt is not an unaccepted diagnostic-only result")
    artifact = receipt.get("polished_diagnostic", {})
    require(artifact.get("accepted") is False and artifact.get("terrain_written") is False and
            Path(artifact.get("path", "")).resolve() == diagnostic_path.resolve() and
            artifact.get("sha256") == diagnostic_sha.lower(), "receipt does not bind diagnostic artifact")
    read0 = receipt.get("source_readset_start"); read1 = receipt.get("source_readset_end")
    require(receipt.get("source_readset_stable") is True and isinstance(read0, dict) and read0 == read1,
            "diagnostic source readset is absent or unstable")
    return read0


def validate_neighbor_ledger(rows: list[dict]) -> dict:
    require(len(rows) == 242, "polish ledger must contain exactly 242 evaluated neighbors")
    pairs = [(int(row["variable_index"]), int(row["step"])) for row in rows]
    require(len(set(pairs)) == 242 and set(pairs) == {(i, s) for i in range(121) for s in (-1, 1)},
            "polish ledger has a missing/duplicate neighbor")
    eligible = [row for row in rows if row.get("eligible") is True]
    require(eligible, "polish ledger contains no eligible neighbor")
    return min(eligible, key=lambda row: (float(row["closed_cost"]), int(row["rc"][0]),
                                          int(row["rc"][1]), int(row["step"])))


def ledger_path_from_receipt(receipt: dict) -> Path:
    info = receipt.get("ledger") or {"path": receipt.get("ledger_path"),
                                     "sha256": receipt.get("ledger_sha256")}
    require(isinstance(info, dict) and info.get("path") and info.get("sha256"),
            "polish ledger path/hash missing")
    return Path(info["path"])


def validate_one_ulp_context(source: np.ndarray, candidate: np.ndarray, base_context: np.ndarray,
                             variables_rc: np.ndarray, selected_index: int, step: int) -> tuple[int, int]:
    source = np.asarray(source); candidate = np.asarray(candidate); base_context = np.asarray(base_context)
    variables_rc = np.asarray(variables_rc)
    require(source.shape == candidate.shape == base_context.shape == (15, 15) and
            source.dtype == candidate.dtype == base_context.dtype == np.float32 and
            np.isfinite(source).all() and np.isfinite(candidate).all(),
            "one-ULP context input must be finite float32 15x15")
    expected_vars = np.asarray([(r, c) for r in range(CORE[0], CORE[1])
                                for c in range(CORE[2], CORE[3])], dtype=np.int32)
    require(variables_rc.dtype == np.int32 and np.array_equal(variables_rc, expected_vars),
            "one-ULP variables are not the exact row-major 121-node core")
    require(0 <= int(selected_index) < len(variables_rc) and int(step) in (-1, 1),
            "one-ULP selected index/step is invalid")
    local_rc = variables_rc - np.asarray([WIN[0], WIN[2]], dtype=np.int32)
    core_mask = np.zeros((15, 15), dtype=bool); core_mask[tuple(local_rc.T)] = True
    require(np.array_equal(source.view(np.uint32)[~core_mask], base_context.view(np.uint32)[~core_mask]) and
            np.array_equal(candidate.view(np.uint32)[~core_mask], base_context.view(np.uint32)[~core_mask]),
            "fixed collar differs from EV95 baseline")
    expected = source.copy()
    r, c = map(int, local_rc[int(selected_index)])
    direction = np.float32(-np.inf if int(step) < 0 else np.inf)
    expected[r, c] = np.nextafter(source[r, c], direction, dtype=np.float32)
    require(np.array_equal(candidate.view(np.uint32), expected.view(np.uint32)),
            "candidate is not exactly the selected one-node one-ULP neighbor")
    return tuple(map(int, variables_rc[int(selected_index)]))


def npz_keys(zf: zipfile.ZipFile) -> set[str]:
    return {Path(n).stem for n in zf.namelist() if n.endswith(".npy")}


def replace_npz_height_window(base_path: Path, context: np.ndarray, output_path: Path,
                              window: tuple[int, int, int, int]) -> str:
    require(not output_path.exists(), f"refusing to overwrite composed candidate: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(base_path, "r") as source:
        names = source.namelist()
        require("heights.npy" in names, "base archive lacks heights.npy")
        baseline_bytes = source.read("heights.npy")
        heights = np.load(io.BytesIO(baseline_bytes), allow_pickle=False)
        r0, r1, c0, c1 = window
        require(context.shape == (r1-r0, c1-c0) and context.dtype == np.float32,
                "replacement context shape/dtype does not match window")
        heights[r0:r1, c0:c1] = context
        buffer = io.BytesIO(); np.save(buffer, heights, allow_pickle=False)
        new_height_bytes = buffer.getvalue()
        with zipfile.ZipFile(output_path, "x", compression=zipfile.ZIP_DEFLATED) as target:
            for info in source.infolist():
                payload = new_height_bytes if info.filename == "heights.npy" else source.read(info.filename)
                target.writestr(info, payload)
    return sha256(output_path)


def compose_npz(base_path: Path, context: np.ndarray, output_path: Path) -> str:
    with zipfile.ZipFile(base_path, "r") as source:
        heights = np.load(io.BytesIO(source.read("heights.npy")), allow_pickle=False)
    require(heights.shape == (2048, 2048) and heights.dtype == np.float32 and np.isfinite(heights).all(),
            "pinned base height array shape/dtype/finiteness changed")
    with np.load(PREP, allow_pickle=False) as prep:
        base_context = prep["base_heights_context"]
    r0, r1, c0, c1 = WIN
    require(np.array_equal(heights[r0:r1, c0:c1].view(np.uint32), base_context.view(np.uint32)),
            "base window differs from prepared baseline")
    return replace_npz_height_window(base_path, context, output_path, WIN)


def compose_lower(base_path: Path, prepared: dict, output_path: Path) -> str:
    require(not output_path.exists(), f"refusing to overwrite L32 artifact: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with np.load(base_path, allow_pickle=False) as z:
        base_h = z["heights"]
        lower = base_h.copy()
    rc = np.asarray(prepared["variables_rc"], dtype=np.int32)
    lo = np.asarray(prepared["lo_absolute_float32_inward"])
    require(lo.dtype == np.float32 and len(lo) == len(rc) == 121, "L32 bound domain mismatch")
    lower[tuple(rc.T)] = lo
    with output_path.open("xb") as stream:
        np.save(stream, lower, allow_pickle=False)
    return sha256(output_path)


def compose_mode(diagnostic_path: Path, diagnostic_sha: str, polish_receipt_path: Path,
                 polish_receipt_sha: str, composed_path: Path, lower_path: Path,
                 composition_receipt_path: Path, approved_source_sha: str, approved_plan_sha: str):
    require(sha256(Path(__file__)) == approved_source_sha.lower(), "consumer source approval SHA mismatch")
    require(sha256(PLAN) == approved_plan_sha.lower(), "consumer plan approval SHA mismatch")
    require(not composition_receipt_path.exists(), "refusing to overwrite composition receipt")
    require(not composed_path.exists() and not lower_path.exists(), "refusing to overwrite composed artifacts")
    output_set = {p.resolve() for p in (composed_path, lower_path, composition_receipt_path)}
    require(len(output_set) == 3, "composition outputs must have three distinct paths")
    start = fixed_source_readset()
    prep_receipt = load_json(PREP_RECEIPT); review = load_json(PREFLIGHT_REVIEW)
    with np.load(PREP, allow_pickle=False) as z:
        prep = {k: z[k] for k in z.files}
    prep_summary = verify_preflight(prep, prep_receipt, review)
    with np.load(PREVIOUS_SOLVE, allow_pickle=False) as z:
        previous = {k: z[k] for k in ("raw_float32_grid", "closed_float32_grid", "solution_float64")}
    solve_lineage = verify_previous_solve_lineage(load_json(PREVIOUS_RESULT))
    require(sha256(diagnostic_path) == diagnostic_sha.lower() and
            sha256(polish_receipt_path) == polish_receipt_sha.lower(),
            "diagnostic or polish receipt hash mismatch before composition")
    receipt_seed = load_json(polish_receipt_path)
    ledger_path = ledger_path_from_receipt(receipt_seed)
    dynamic_paths = [diagnostic_path, polish_receipt_path, ledger_path]
    dynamic_start = sha_readset(dynamic_paths)
    context, polish_receipt, polish_lineage = validate_polished_diagnostic(
        diagnostic_path, diagnostic_sha, polish_receipt_path, polish_receipt_sha,
        prep, previous)
    base_path = BASE
    composed_sha = compose_npz(base_path, context, composed_path)
    lower_sha = compose_lower(base_path, prep, lower_path)
    end = fixed_source_readset()
    require(start == end, "source readset changed during composition")
    dynamic_end = sha_readset(dynamic_paths)
    require(dynamic_start == dynamic_end, "polished diagnostic, receipt, or ledger changed during composition")
    report = {"schema": "ev94.wet-bank-polished-diagnostic-composition.v1", "status": "COMPOSED_UNACCEPTED",
              "accepted": False, "polished_diagnostic_path": str(diagnostic_path.resolve()),
              "polished_diagnostic_sha256": diagnostic_sha.lower(),
              "polish_receipt_path": str(polish_receipt_path.resolve()),
              "polish_receipt_sha256": polish_receipt_sha.lower(),
              "prepared_path": str(PREP.resolve()), "prepared_sha256": EXPECTED[PREP],
              "composed_candidate_path": str(composed_path.resolve()), "composed_candidate_sha256": composed_sha,
              "lower_path": str(lower_path.resolve()), "lower_sha256": lower_sha,
              "preflight": prep_summary, "source_solve_lineage": solve_lineage,
              "polish_lineage": polish_lineage,
              "source_readset_start": start, "source_readset_end": end,
              "source_readset_stable": True,
              "dynamic_readset_start": dynamic_start, "dynamic_readset_end": dynamic_end,
              "dynamic_readset_stable": True,
              "limitations": ["Composition does not accept the diagnostic candidate.",
                              "Run the pinned compiled-water checker and independent final verifier separately."]}
    composition_receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with composition_receipt_path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2, allow_nan=False); f.write("\n")
    return report


def read_csr(npz, prefix: str):
    return sparse.csr_matrix((npz[prefix + "_data"], npz[prefix + "_indices"], npz[prefix + "_indptr"]),
                             shape=tuple(npz[prefix + "_shape"]))


def d8_check(context: np.ndarray, witnesses: np.ndarray) -> tuple[bool, float]:
    w = np.asarray(witnesses, dtype=np.int32)
    require(w.ndim == 2 and w.shape[1] == 4, "D8 witness matrix malformed")
    slack = np.asarray([context[cr, cc] - context[wr, wc] for cr, cc, wr, wc in w], dtype=np.float32)
    return bool(np.all(slack >= np.float32(0.0))), float(slack.min(initial=np.float32(np.inf)))


def f32_fraction(value) -> Fraction:
    return Fraction.from_float(float(np.float32(value)))


def direct_pf(candidate_context: np.ndarray, cross_specs, sign_specs, executor) -> dict:
    signs_ok = True; sign_failures = []
    for s in cross_specs:
        hd = f32_fraction(candidate_context[executor.local_rc(s.dry_rc)])
        hw = f32_fraction(candidate_context[executor.local_rc(s.wet_rc)])
        if not (hd > s.dry_level and hw < s.wet_level):
            signs_ok = False; sign_failures.append({"kind": "cross_endpoint", "edge": [list(s.dry_rc), list(s.wet_rc)]})
    for i, s in enumerate(sign_specs):
        h32 = np.float32(candidate_context[s.local_rc]); h = f32_fraction(h32)
        valid = ((s.sign > 0 and h > s.level) or (s.sign < 0 and h < s.level) or
                 (s.sign == 0 and h32.view(np.uint32) == s.baseline.view(np.uint32)))
        if not valid:
            signs_ok = False; sign_failures.append({"kind": "sign_only", "index": i, "rc": list(s.rc), "surface": s.surface})
    cross_ok = True; cross_failures = []
    for i, s in enumerate(cross_specs):
        ha = f32_fraction(candidate_context[s.local_a]); hb = f32_fraction(candidate_context[s.local_b])
        da = ha - s.level_a; db = hb - s.level_b
        if da * db >= 0:
            cross_ok = False; cross_failures.append({"index": i, "edge": [list(x) for x in s.edge_rc], "reason": "no strict crossing"})
            continue
        t = da / (da - db)
        tdry = t if s.dry_endpoint == 0 else 1 - t
        if tdry < s.t_lower or tdry > s.t_upper:
            cross_ok = False; cross_failures.append({"index": i, "edge": [list(x) for x in s.edge_rc],
                                                       "t": str(tdry), "range": [str(s.t_lower), str(s.t_upper)]})
    return {"strict_signs": signs_ok, "all_116_intervals": cross_ok,
            "crossing_count": len(cross_specs), "same_sign_sample_count": len(sign_specs),
            "sign_failures": sign_failures, "crossing_failures": cross_failures}


def local_new_minima(before: np.ndarray, after: np.ndarray, channel_mask: np.ndarray) -> dict:
    require(before.shape == after.shape == channel_mask.shape == (15, 15), "local extrema context shape mismatch")
    def minima(h):
        found = set()
        for r in range(1, h.shape[0] - 1):
            for c in range(1, h.shape[1] - 1):
                if channel_mask[r, c]:
                    continue
                nbr = np.asarray([h[r + dr, c + dc] for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                                  if (dr, dc) != (0, 0)], dtype=np.float32)
                if np.all(np.float32(h[r, c]) < nbr):
                    found.add((r, c))
        return found
    bmin, hmin = minima(before), minima(after)
    new = sorted(hmin - bmin)
    outside = ~channel_mask
    bi = np.argwhere(outside)
    bv = before[tuple(bi.T)]; hv = after[tuple(bi.T)]
    def extrema(values, rc):
        lo = np.min(values); hi = np.max(values)
        return {"min": float(lo), "min_rc": rc[np.flatnonzero(values == lo)[0]].tolist(),
                "max": float(hi), "max_rc": rc[np.flatnonzero(values == hi)[0]].tolist()}
    return {"baseline_strict_minima": len(bmin), "candidate_strict_minima": len(hmin),
            "new_strict_minima_rc": [list(x) for x in new], "no_new_outside_channel_minima": not new,
            "outside_channel_baseline_extrema": extrema(bv, bi),
            "outside_channel_candidate_extrema": extrema(hv, bi)}


def affected_cells(changed: np.ndarray) -> np.ndarray:
    out = np.zeros((changed.shape[0] - 1, changed.shape[1] - 1), dtype=bool)
    for r, c in np.argwhere(changed):
        for rr in (r - 1, r):
            for cc in (c - 1, c):
                if 0 <= rr < out.shape[0] and 0 <= cc < out.shape[1]: out[rr, cc] = True
    return out


def compare_npz_metadata(base_path: Path, candidate_path: Path) -> bool:
    with zipfile.ZipFile(base_path, "r") as b, zipfile.ZipFile(candidate_path, "r") as h:
        bnames = {n for n in b.namelist() if n.endswith(".npy")}
        hnames = {n for n in h.namelist() if n.endswith(".npy")}
        require(bnames == hnames, "full terrain archive fields differ from baseline")
        for name in sorted(bnames - {"heights.npy"}):
            require(b.read(name) == h.read(name), f"non-height NPZ member changed: {name}")
    return True


def validate_composed_candidate(context: np.ndarray, composed_path: Path, lower_path: Path,
                                prep: dict) -> dict:
    require(compare_npz_metadata(BASE, composed_path), "non-height NPZ members are not byte-identical to B")
    with np.load(BASE, allow_pickle=False) as b, np.load(composed_path, allow_pickle=False) as h:
        base_h = b["heights"]; candidate_h = h["heights"]
        require(set(b.files) == set(h.files), "terrain metadata key population changed")
        require(base_h.shape == candidate_h.shape == (2048, 2048) and
                base_h.dtype == candidate_h.dtype == np.float32 and np.isfinite(candidate_h).all(),
                "composed terrain shape/dtype/finiteness mismatch")
        r0, r1, c0, c1 = WIN
        require(np.array_equal(candidate_h[r0:r1, c0:c1].view(np.uint32), context.view(np.uint32)),
                "full terrain crop differs from polished diagnostic context")
        diff = candidate_h.view(np.uint32) != base_h.view(np.uint32)
        coords = np.argwhere(diff)
        require(all(CORE[0] <= int(r) < CORE[1] and CORE[2] <= int(c) < CORE[3] for r, c in coords),
                "composed terrain has a changed vertex outside the exact 121-node core")
        rc = np.asarray(prep["variables_rc"], dtype=np.int32)
        node_diff = candidate_h[tuple(rc.T)].view(np.uint32) != base_h[tuple(rc.T)].view(np.uint32)
        require(len(coords) == int(node_diff.sum()), "changed whole-terrain node set differs from 121-core delta")
        with open(lower_path, "rb") as f:
            lower = np.load(f, allow_pickle=False)
        lo = np.asarray(prep["lo_absolute_float32_inward"])
        expected_lower = base_h.copy(); expected_lower[tuple(rc.T)] = lo
        require(lower.shape == base_h.shape and lower.dtype == np.float32 and np.array_equal(lower.view(np.uint32), expected_lower.view(np.uint32)),
                "L32 file differs from the pinned prepared inward lower envelope")
        return {"changed_vertices": int(len(coords)), "metadata_byte_identical": True,
                "core_change_count": int(node_diff.sum()), "lower_matches_prepared": True}


def compare_face_inventory(index, prep: dict, ev87) -> dict:
    vars_rc = np.asarray(prep["variables_rc"], dtype=np.int32)
    expected_cells = set()
    for r, c in vars_rc.tolist():
        for rr in (r - 1, r):
            for cc in (c - 1, c):
                if 0 <= rr < ev87.N - 1 and 0 <= cc < ev87.N - 1: expected_cells.add((rr, cc))
    cell_rows = np.asarray(sorted(expected_cells), dtype=np.int32)
    require(len(cell_rows) == 144 and np.array_equal(cell_rows, np.asarray(prep["face_population_cells_rc"], dtype=np.int32)),
            "144-cell face population is not the exact incidence of the 121-node core")
    keys = {}
    for i in range(len(prep["face_kind"])):
        key = (int(prep["face_kind"][i]), int(prep["face_object_id"][i]),
               int(prep["face_model_id"][i]), int(prep["face_id"][i]))
        require(key not in keys, f"duplicate prepared compiled face key: {key}")
        keys[key] = i
    require(len(keys) == 200, f"prepared face inventory count is {len(keys)}, expected 200")
    observed = {}
    for r, c in cell_rows.tolist():
        for kind_name, kind_code in (("physical", 0), ("visible", 1)):
            queried = index.query_cell(int(r), int(c), kind=kind_name)
            for j in range(len(queried["kind"])):
                key = (int(queried["kind"][j]), int(queried["object_id"][j]),
                       int(queried["model_id"][j]), int(queried["face_id"][j]))
                if key in observed:
                    old = observed[key]
                    for name in ("xyz", "plane_y_xz", "cell_range_rc", "degenerate", "area_xz"):
                        require(np.array_equal(old[name], queried[name][j]), f"face index returned inconsistent {name}: {key}")
                else:
                    observed[key] = {name: queried[name][j].copy()
                                     for name in ("xyz", "plane_y_xz", "cell_range_rc", "degenerate", "area_xz")}
    require(set(observed) == set(keys), "prepared 200 face identities differ from the pinned index cell queries")
    for key, i in keys.items():
        for field, array_name in (("xyz", "face_xyz"), ("plane_y_xz", "face_plane_y_xz"),
                                  ("cell_range_rc", "face_cell_range_rc"), ("degenerate", "face_degenerate"),
                                  ("area_xz", "face_area_xz")):
            require(np.array_equal(observed[key][field], prep[array_name][i]), f"prepared/index {field} mismatch for {key}")
    return {"face_count": len(observed), "cell_count": len(cell_rows), "identity_and_geometry_exact": True}


def polygon_parts(geom):
    if geom.is_empty: return []
    if geom.geom_type == "Polygon": return [geom]
    if hasattr(geom, "geoms"):
        return [p for g in geom.geoms for p in polygon_parts(g)]
    return []


def polygon_topology_signature(geom) -> tuple[int, int]:
    parts = polygon_parts(geom)
    return len(parts), sum(len(p.interiors) for p in parts)


def exposed_topology(ev87, prep: dict, before: np.ndarray, after: np.ndarray) -> dict:
    cell_set = {tuple(map(int, rc)) for rc in np.asarray(prep["face_population_cells_rc"])}
    polygons = {"B": defaultdict(list), "H": defaultdict(list)}
    groups = {(int(kind), int(obj), int(model)) for kind, obj, model in
              zip(prep["face_kind"], prep["face_object_id"], prep["face_model_id"])}
    for i in range(len(prep["face_kind"])):
        if int(prep["face_degenerate"][i]): continue
        kind = int(prep["face_kind"][i]); obj = int(prep["face_object_id"][i]); model = int(prep["face_model_id"][i])
        key = (kind, obj, model)
        xyz = np.asarray(prep["face_xyz"][i], dtype=np.float64)
        face_xy = xyz[:, (0, 2)]
        face = Polygon(face_xy)
        if face.is_empty or not face.is_valid or face.area <= 0: continue
        coeff = np.asarray(prep["face_plane_y_xz"][i], dtype=np.float64)
        r0, r1, c0, c1 = map(int, prep["face_cell_range_rc"][i])
        for r in range(max(0, r0), min(ev87.N - 2, r1) + 1):
            for c in range(max(0, c0), min(ev87.N - 2, c1) + 1):
                if (r, c) not in cell_set: continue
                xy = ev87.cell_xy(r, c)
                for side, grid in (("B", before), ("H", after)):
                    ground = ev87.corner_values(grid, r, c)
                    for tri in ev87.TRIS:
                        piece = ev87.odol_visible_in_native_tri(face_xy, coeff, xy, ground, tri)
                        if not piece.is_empty and piece.area > 0:
                            polygons[side][key].append(piece)
    signatures = {side: {} for side in ("B", "H")}
    unique_by_kind = {side: {0: [], 1: []} for side in ("B", "H")}
    for side in ("B", "H"):
        for key in sorted(groups):
            parts = polygons[side].get(key, [])
            merged = unary_union(parts) if parts else Polygon()
            poly = polygon_parts(merged)
            signatures[side][key] = {"components": len(poly), "holes": sum(len(x.interiors) for x in poly),
                                     "exposed_area_m2": float(merged.area)}
            if not merged.is_empty: unique_by_kind[side][key[0]].append(merged)
    failures = []
    for key in sorted(groups):
        b = signatures["B"][key]; h = signatures["H"][key]
        if (b["components"], b["holes"]) != (h["components"], h["holes"]):
            failures.append({"kind_object_model": list(key), "B": [b["components"], b["holes"]],
                             "H": [h["components"], h["holes"]]})
    totals = {}
    kind_signatures = {"B": {}, "H": {}}
    for kind in (0, 1):
        bg = unary_union(unique_by_kind["B"][kind]) if unique_by_kind["B"][kind] else Polygon()
        hg = unary_union(unique_by_kind["H"][kind]) if unique_by_kind["H"][kind] else Polygon()
        bc, bh = polygon_topology_signature(bg); hc, hh = polygon_topology_signature(hg)
        kind_signatures["B"][kind] = {"components": bc, "holes": bh}
        kind_signatures["H"][kind] = {"components": hc, "holes": hh}
        bs = kind_signatures["B"][kind]; hs = kind_signatures["H"][kind]
        if (bs["components"], bs["holes"]) != (hs["components"], hs["holes"]):
            failures.append({"kind_union": kind, "B": [bs["components"], bs["holes"]],
                             "H": [hs["components"], hs["holes"]]})
        per_obj_b = math.fsum(signatures["B"][k]["exposed_area_m2"] for k in groups if k[0] == kind)
        per_obj_h = math.fsum(signatures["H"][k]["exposed_area_m2"] for k in groups if k[0] == kind)
        totals[{0: "physical", 1: "visible"}[kind]] = {
            "unique_union_area_B_m2": float(bg.area), "unique_union_area_H_m2": float(hg.area),
            "unique_union_delta_H_minus_B_m2": float(hg.area - bg.area),
            "per_object_area_B_sum_m2_may_overlap": per_obj_b,
            "per_object_area_H_sum_m2_may_overlap": per_obj_h,
            "per_object_area_delta_m2_may_overlap": per_obj_h - per_obj_b}
    return {"policy": "DESIGN_LOCAL_PER_OBJECT_AND_KIND_UNION_COMPONENT_AND_HOLE_COUNTS_UNCHANGED",
            "scope": "200 pinned compiled faces clipped to 144 incident cells; not whole-map connectivity",
            "topology_unchanged": not failures, "topology_failures": failures,
            "exposed_area": totals, "object_signatures_B": {str(k): v for k, v in signatures["B"].items()},
            "object_signatures_H": {str(k): v for k, v in signatures["H"].items()},
            "kind_union_signatures_B": {str(k): v for k, v in kind_signatures["B"].items()},
            "kind_union_signatures_H": {str(k): v for k, v in kind_signatures["H"].items()},
            "area_threshold": None, "area_is_informational": True}


def coverage_contract(report: dict, coverage_path: Path, candidate_path: Path, lower_path: Path) -> dict:
    shape = coverage_shape_contract(report, str(candidate_path.resolve()), sha256(candidate_path),
                                    str(lower_path.resolve()), sha256(lower_path),
                                    str(PREP.resolve()), EXPECTED[PREP],
                                    str(COVERAGE_CHECK.resolve()), EXPECTED[COVERAGE_CHECK])
    pins = report["source_pins_start"]
    for path, expected in pins.items(): require(sha256(Path(path)) == expected, f"coverage source changed: {path}")
    return {**shape, "report_sha256": sha256(coverage_path), "source_paths_rehashed": len(pins)}


def coverage_shape_contract(report: dict, candidate_path: str, candidate_sha: str,
                            lower_path: str, lower_sha: str, prepared_path: str,
                            prepared_sha: str, checker_path: str, checker_sha: str) -> dict:
    require(report.get("status") == "PASS_LOCAL_COMPILED_WATER_CANDIDATE", "compiled-water report not PASS")
    require(Path(report.get("candidate_path", "")).resolve() == Path(candidate_path).resolve(), "coverage report candidate path mismatch")
    require(report.get("prepared_bounds_path") and Path(report["prepared_bounds_path"]).resolve() == Path(prepared_path).resolve(),
            "coverage report prepared path mismatch")
    require(report.get("prepared_bounds_sha256") == prepared_sha, "coverage report prepared SHA mismatch")
    require(report.get("candidate_changed_vertices", 0) > 0 and report.get("evaluated_potential_vertices") == 121,
            "coverage report is empty or did not assess the exact core")
    cov = report.get("coverage", {})
    required = {"bounds_inventory_identity_exact", "deployed_pbo_identity_exact", "no_changed_partial_F_triangles",
                "unknown_P_or_F_faces_absent_or_buried_B_H_and_L32_or_P9_exact",
                "no_new_or_worsened_compiled_face_height_violation", "physical_support_holes_lt_1e_7m2",
                "visible_support_holes_lt_1e_7m2", "physical_residual_outside_band_le_0_002m2",
                "visible_residual_outside_band_le_0_002m2", "all_source_pins_stable",
                "candidate_only_inside_core", "EV95_objects_and_deployed_water_same_as_indexed_B",
                "nonempty_evaluation_domain", "lower_envelope_from_pinned_prepared_bounds"}
    gates = cov.get("gates", {})
    require(set(gates) >= required and bool(gates) and all(value is True for value in gates.values()),
            "compiled-water report has a missing or false coverage gate")
    require(report.get("source_pins_start") == report.get("source_pins_end"), "coverage report readset changed")
    pins = report["source_pins_start"]
    require(pins.get(str(Path(candidate_path).resolve())) == candidate_sha, "coverage report does not bind composed terrain")
    require(pins.get(str(Path(lower_path).resolve())) == lower_sha, "coverage report does not bind L32")
    require(pins.get(str(Path(prepared_path).resolve())) == prepared_sha, "coverage report does not bind prepared bounds")
    require(pins.get(str(Path(checker_path).resolve())) == checker_sha, "coverage report used unexpected checker")
    idx = cov.get("index", {})
    require(idx.get("target_cells") == 144 and idx.get("bbox_candidates_intersecting_target_cell_set") == 200,
            "coverage report is not the expected 144-cell/200-face population")
    return {"gates": gates, "coverage_cells": idx["target_cells"],
            "indexed_faces": idx["bbox_candidates_intersecting_target_cell_set"],
            "bound_input_count": 4}


def verify_mode(diagnostic_path: Path, diagnostic_sha: str, polish_receipt_path: Path, polish_receipt_sha: str,
                composed_path: Path, composed_sha: str, lower_path: Path, lower_sha: str,
                composition_receipt_path: Path, composition_receipt_sha: str,
                coverage_path: Path, coverage_sha: str, output_path: Path,
                approved_source_sha: str, approved_plan_sha: str) -> dict:
    require(sha256(Path(__file__)) == approved_source_sha.lower(), "consumer source approval SHA mismatch")
    require(sha256(PLAN) == approved_plan_sha.lower(), "consumer plan approval SHA mismatch")
    require(not output_path.exists(), f"refusing to overwrite final review: {output_path}")
    for path, expected in ((diagnostic_path, diagnostic_sha), (polish_receipt_path, polish_receipt_sha),
                           (composed_path, composed_sha), (lower_path, lower_sha),
                           (composition_receipt_path, composition_receipt_sha), (coverage_path, coverage_sha)):
        require(sha256(path) == expected.lower(), f"input SHA mismatch: {path}")
    receipt_seed = load_json(polish_receipt_path)
    ledger_path = ledger_path_from_receipt(receipt_seed)
    dynamic_paths = [diagnostic_path, polish_receipt_path, ledger_path, composed_path, lower_path,
                     composition_receipt_path, coverage_path]
    dynamic_started = sha_readset(dynamic_paths)
    started = fixed_source_readset()
    prep_receipt = load_json(PREP_RECEIPT); review = load_json(PREFLIGHT_REVIEW)
    with np.load(PREP, allow_pickle=False) as z: prep = {k: z[k] for k in z.files}
    preflight_metrics = verify_preflight(prep, prep_receipt, review)
    with np.load(PREVIOUS_SOLVE, allow_pickle=False) as z:
        previous = {k: z[k] for k in ("raw_float32_grid", "closed_float32_grid", "solution_float64")}
    solve_lineage = verify_previous_solve_lineage(load_json(PREVIOUS_RESULT))
    ex = load_module("wet_complete_frozen_executor", EXECUTOR)
    context, polish_receipt, polish_lineage = validate_polished_diagnostic(
        diagnostic_path, diagnostic_sha, polish_receipt_path, polish_receipt_sha, prep, previous)
    composition = load_json(composition_receipt_path)
    require(composition.get("schema") == "ev94.wet-bank-polished-diagnostic-composition.v1" and
            composition.get("status") == "COMPOSED_UNACCEPTED" and composition.get("accepted") is False,
            "composition receipt is not an unaccepted full-grid composition")
    require(Path(composition.get("polished_diagnostic_path", "")).resolve() == diagnostic_path.resolve() and
            composition.get("polished_diagnostic_sha256") == diagnostic_sha.lower() and
            Path(composition.get("polish_receipt_path", "")).resolve() == polish_receipt_path.resolve() and
            composition.get("polish_receipt_sha256") == polish_receipt_sha.lower() and
            Path(composition.get("composed_candidate_path", "")).resolve() == composed_path.resolve() and
            composition.get("composed_candidate_sha256") == composed_sha.lower() and
            Path(composition.get("lower_path", "")).resolve() == lower_path.resolve() and
            composition.get("lower_sha256") == lower_sha.lower(),
            "composition receipt fields do not match supplied artifacts")
    require(composition.get("source_readset_stable") is True and
            composition.get("source_readset_start") == composition.get("source_readset_end"),
            "composition readset was unstable")
    expected_composition_dynamic = {str(Path(p).resolve()): sha256(Path(p)) for p in
                                    (diagnostic_path, polish_receipt_path, Path(polish_lineage["ledger_path"]))}
    require(composition.get("dynamic_readset_stable") is True and
            composition.get("dynamic_readset_start") == composition.get("dynamic_readset_end") == expected_composition_dynamic,
            "composition dynamic candidate readset is missing or unstable")
    for path, expected in composition["source_readset_start"].items():
        require(sha256(Path(path)) == expected, f"composition source changed: {path}")
    terrain_checks = validate_composed_candidate(context, composed_path, lower_path, prep)
    coverage_report = load_json(coverage_path)
    coverage_checks = coverage_contract(coverage_report, coverage_path, composed_path, lower_path)

    base_context = np.asarray(prep["base_heights_context"], dtype=np.float32)
    changed = context.view(np.uint32) != base_context.view(np.uint32)
    require(np.any(changed), "candidate has no changed height nodes")
    loc_rc = np.asarray(prep["variables_rc"], dtype=np.int32) - np.asarray([WIN[0], WIN[2]], dtype=np.int32)
    candidate_x = context[tuple(loc_rc.T)].astype(np.float64)
    lower = np.asarray(prep["lo_absolute_float32_inward"], dtype=np.float32)
    upper = np.asarray(prep["hi_absolute_float32_inward"], dtype=np.float32)
    bounds = bool(np.all(context[tuple(loc_rc.T)] >= lower) and np.all(context[tuple(loc_rc.T)] <= upper))
    # Every protected/fixed context vertex is unchanged; the core list is the sole variable population.
    core_mask = np.zeros((15, 15), dtype=bool); core_mask[tuple(loc_rc.T)] = True
    fixed_exact = bool(np.array_equal(context.view(np.uint32)[~core_mask], base_context.view(np.uint32)[~core_mask]))
    protected_exact = fixed_exact
    for name in ("other_fixed_context", "effective_fixed_context", "p9_context", "road_context"):
        mask = np.asarray(prep[name], dtype=bool)
        require(not np.any(changed & mask), f"candidate changes protected/fixed mask {name}")
    wet_interior_vars = np.asarray([bool(prep["design_interior_context"][r, c] and
                                          not prep["shore_boundary_context"][r, c]) for r, c in loc_rc.tolist()])
    bed_floor = bool(np.all(candidate_x[wet_interior_vars] >= 1.0))

    real_inputs = ex.load_real_inputs()
    pf = direct_pf(context, real_inputs["cross_specs"], real_inputs["sign_specs"], ex)
    require(pf["crossing_count"] == 116, "P/F checker did not reconstruct the exact 116 crossings")
    witnesses = np.asarray(prep["d8_witnesses_local"], dtype=np.int32)
    require(witnesses.shape == (150, 4), "D8 witness count differs from the reviewed 150 constraints")
    d8_ok, d8_min_slack = d8_check(context, witnesses)
    d8_slack = np.asarray([context[cr, cc] - context[wr, wc] for cr, cc, wr, wc in witnesses], dtype=np.float32)
    Gmat = read_csr(prep, "G"); q = (Gmat @ candidate_x + prep["k_G"]).reshape(-1, 2)
    require(q.shape == (392, 2), "face cone count differs from the reviewed 392 constraints")
    cone_excess = np.linalg.norm(q, axis=1) - np.asarray(prep["radii_G"], dtype=np.float64)
    cones_ok = bool(np.all(cone_excess <= 0.0))
    A = read_csr(prep, "A"); rhs = np.asarray(prep["rhs_A"], dtype=np.float64)
    raw_context = np.asarray(previous["raw_float32_grid"], dtype=np.float32)
    raw_x = raw_context[tuple(loc_rc.T)].astype(np.float64)
    baseline_x = np.asarray(prep["x0_absolute"], dtype=np.float64)
    def cost(x): return 0.5 * float(np.sum((A @ x - rhs) ** 2))
    costs = {"raw": cost(raw_x), "candidate": cost(candidate_x), "baseline": cost(baseline_x)}
    energy_allowance = 1e-7 * max(1.0, costs["raw"])
    energy_ok = bool(costs["candidate"] - costs["raw"] <= energy_allowance and
                     costs["candidate"] < costs["baseline"])

    ev87 = load_module("wet_complete_ev87", EV87)
    before_crop = base_context.astype(np.float64); after_crop = context.astype(np.float64)
    cell_mask = affected_cells(changed)
    slope_pairs = []
    for b, h in zip(ev87.slopes(before_crop), ev87.slopes(after_crop)):
        base_values = b[cell_mask]; candidate_values = h[cell_mask]
        limit = np.maximum(35.0, base_values) + ANG_TOL_DEG
        slope_pairs.extend(zip(base_values.tolist(), candidate_values.tolist(), limit.tolist()))
    slope_ok = all(h <= lim for _, h, lim in slope_pairs)
    edges_b = dict(ev87.edge_angles(before_crop)); edges_h = dict(ev87.edge_angles(after_crop))
    hinge_report = {}; p99_ok = True; no_new_over30 = True
    for kind, angles_b in edges_b.items():
        angles_h = edges_h[kind]
        affected = ev87.incident_any(changed, kind)
        vb, vh = np.asarray(angles_b[affected]), np.asarray(angles_h[affected])
        p99_before = float(np.percentile(vb, 99)) if vb.size else 0.0
        p99_after = float(np.percentile(vh, 99)) if vh.size else 0.0
        new_over30 = int(np.count_nonzero((vb <= 30.0) & (vh > 30.0)))
        p99_ok &= p99_after <= p99_before
        no_new_over30 &= new_over30 == 0
        hinge_report[kind] = {"affected_count": int(vh.size), "before_p99_deg": p99_before,
                              "candidate_p99_deg": p99_after, "new_over_30deg": new_over30,
                              "before_max_deg": float(vb.max()) if vb.size else None,
                              "candidate_max_deg": float(vh.max()) if vh.size else None}
    target_i = int(np.argmax(prep["hinge_angle_before_deg"]))
    target_kind = {0: "diag", 1: "vertical", 2: "horizontal"}[int(prep["hinge_kind"][target_i])]
    target_rc = tuple(map(int, prep["hinge_rc_local"][target_i]))
    target_before = float(edges_b[target_kind][target_rc]); target_after = float(edges_h[target_kind][target_rc])
    require(abs(target_before - float(prep["hinge_angle_before_deg"][target_i])) <= 1e-10,
            "prepared focus hinge does not match EV87 recomputation")
    focus_drop = target_before - target_after
    focus_ok = focus_drop >= 2.0
    channel = np.asarray(prep["design_interior_context"], dtype=bool) | np.asarray(prep["shore_boundary_context"], dtype=bool)
    minima = local_new_minima(base_context, context, channel)

    # Load only small prepared fields and 200-face local geometry; the full-map candidate check above is done first.
    coverage_mod = load_module("wet_complete_coverage_consumer", WATER_CONSUMER)
    _, _, ev87_from_loader, cv, _, _, index_module = coverage_mod.load_helpers()
    require(sha256(COVERAGE_CHECK) == EXPECTED[COVERAGE_CHECK], "compiled-water wrapper source changed")
    index = index_module.FaceRangeIndex(coverage_mod.INDEX_RUN)
    face_recheck = compare_face_inventory(index, prep, ev87_from_loader)
    topology = exposed_topology(ev87_from_loader, prep, before_crop, after_crop)
    index.reverify()
    ex.source_readset_check(real_inputs["source_start"])

    gates = {
        "polished_diagnostic_one_ulp_lineage_exact": True,
        "full_terrain_composition_core_only_and_metadata_exact": True,
        "all_121_bounds_exact": bounds,
        "all_prepared_fixed_and_protected_nodes_exact": protected_exact,
        "interior_channel_bed_floor_ge_1m": bed_floor,
        "all_116_direct_PF_intervals_and_strict_signs": pf["all_116_intervals"] and pf["strict_signs"],
        "all_150_D8_witnesses_exact": d8_ok,
        "all_392_face_cones_exact": cones_ok,
        "inherited_objective_energy_and_strict_baseline_improvement": energy_ok,
        "native_face_slope_contract": slope_ok,
        "affected_hinge_p99_nonworse": p99_ok,
        "no_new_hinge_over_30deg": no_new_over30,
        "focus_hinge_drop_at_least_2deg": focus_ok,
        "no_new_strict_local_minimum_outside_channel": minima["no_new_outside_channel_minima"],
        "compiled_water_coverage_consumer_pass": True,
        "200_compiled_faces_match_index_and_prepared": face_recheck["identity_and_geometry_exact"],
        "local_per_object_water_topology_unchanged_design_policy": topology["topology_unchanged"],
        "source_readset_stable": True,
    }
    end = fixed_source_readset()
    require(started == end, "final consumer fixed source readset changed")
    dynamic_ended = sha_readset(dynamic_paths)
    require(dynamic_started == dynamic_ended, "final consumer artifact readset changed during evaluation")
    solve_lineage = verify_previous_solve_lineage(load_json(PREVIOUS_RESULT))
    ex.source_readset_check(real_inputs["source_start"])
    status = "PASS_LOCAL_STATIC_GATES_PENDING_DESIGN_REVIEW" if all(gates.values()) else "FAIL_LOCAL_STATIC_GATES"
    report = {"schema": "ev94.wet-bank-polished-diagnostic-review.v1", "status": status,
              "accepted": False,
              "scope": "single Oredezh diagnostic polish, one ULP from rejected source, 121-node domain, 144 incident cells, 200 compiled faces; not accepted terrain or whole-map/deployed/visual acceptance",
              "inputs": {"polished_diagnostic": {"path": str(diagnostic_path.resolve()), "sha256": diagnostic_sha.lower()},
                         "polish_receipt": {"path": str(polish_receipt_path.resolve()), "sha256": polish_receipt_sha.lower()},
                         "composed_candidate": {"path": str(composed_path.resolve()), "sha256": composed_sha.lower()},
                         "composition_receipt": {"path": str(composition_receipt_path.resolve()), "sha256": composition_receipt_sha.lower()},
                         "lower": {"path": str(lower_path.resolve()), "sha256": lower_sha.lower()},
                         "coverage_report": {"path": str(coverage_path.resolve()), "sha256": coverage_sha.lower()},
                         "prepared": {"path": str(PREP.resolve()), "sha256": EXPECTED[PREP]},
                         "source_readset_start_end": started,
                         "dynamic_readset_start_end": dynamic_started,
                         "dynamic_readset_stable": True},
              "preflight": preflight_metrics, "source_solve_lineage": solve_lineage,
              "polish_lineage": polish_lineage,
              "coverage": coverage_checks, "terrain": terrain_checks,
              "checks": gates, "failed_checks": [k for k, v in gates.items() if not v],
              "p_f": pf, "constraints": {"D8_min_slack_m": d8_min_slack,
                                           "cone_max_excess": float(cone_excess.max(initial=-np.inf)),
                                           "bounds_min_lower_slack": float(np.min(candidate_x - lower)),
                                           "bounds_min_upper_slack": float(np.min(upper - candidate_x)),
                                           "objective_costs": costs, "closure_allowance": energy_allowance},
              "geometry": {"slope_sample_count": len(slope_pairs), "max_slope_deg": max((h for _, h, _ in slope_pairs), default=None),
                           "focus": {"kind": target_kind, "anchor_local_rc": list(target_rc), "before_deg": target_before,
                                     "candidate_deg": target_after, "drop_deg": focus_drop, "required_drop_deg": 2.0},
                           "hinges": hinge_report, "outside_channel_extrema_and_minima": minima,
                           "compiled_water_faces": face_recheck, "water_topology": topology},
              "limits": ["Exposed area is reported without an invented numerical threshold.",
                         "Water topology is a proposed local design gate and requires root review.",
                         "No visual/in-game verification; this report never promotes terrain."]}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2, allow_nan=False); f.write("\n")
    return report


def self_test():
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_polished_diagnostic.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise ConsumerStop(f"synthetic consumer suite failed: {len(result.failures)} failures, {len(result.errors)} errors")
    return {"synthetic_only": True, "tests_run": result.testsRun, "failures": 0, "errors": 0}


def validate_core_delta(base_context: np.ndarray, candidate_context: np.ndarray, vars_rc: np.ndarray) -> bool:
    if base_context.shape != (15, 15) or candidate_context.shape != (15, 15): return False
    mask = np.zeros((15, 15), dtype=bool)
    origin = np.asarray([WIN[0], WIN[2]])
    loc = np.asarray(vars_rc, dtype=np.int32) - origin
    if np.any(loc < 0) or np.any(loc >= 15): return False
    mask[tuple(loc.T)] = True
    return bool(np.array_equal(base_context.view(np.uint32)[~mask], candidate_context.view(np.uint32)[~mask]))


def cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="mode")
    c = sub.add_parser("compose")
    for key in ("polished-diagnostic", "polish-receipt", "composed-candidate", "lower", "composition-receipt"):
        c.add_argument("--" + key, type=Path, required=True)
    c.add_argument("--polished-diagnostic-sha256", required=True)
    c.add_argument("--polish-receipt-sha256", required=True)
    c.add_argument("--approved-source-sha256", required=True)
    c.add_argument("--approved-plan-sha256", required=True)
    v = sub.add_parser("verify")
    for key in ("polished-diagnostic", "polish-receipt", "composed-candidate", "lower", "composition-receipt", "coverage-report", "output"):
        v.add_argument("--" + key, type=Path, required=True)
    for key in ("polished-diagnostic", "polish-receipt", "composed-candidate", "lower", "composition-receipt", "coverage-report"):
        v.add_argument("--" + key + "-sha256", required=True)
    v.add_argument("--approved-source-sha256", required=True)
    v.add_argument("--approved-plan-sha256", required=True)
    args = parser.parse_args()
    if args.self_test:
        try:
            fixtures = self_test()
        except Exception as exc:
            print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2)); return 1
        print(json.dumps({"status": "PASS", "fixtures": fixtures}, indent=2)); return 0
    if args.mode == "compose":
        report = compose_mode(args.polished_diagnostic, args.polished_diagnostic_sha256, args.polish_receipt,
                              args.polish_receipt_sha256, args.composed_candidate, args.lower,
                              args.composition_receipt, args.approved_source_sha256, args.approved_plan_sha256)
    elif args.mode == "verify":
        report = verify_mode(args.polished_diagnostic, args.polished_diagnostic_sha256, args.polish_receipt,
                             args.polish_receipt_sha256, args.composed_candidate,
                             args.composed_candidate_sha256, args.lower, args.lower_sha256,
                             args.composition_receipt, args.composition_receipt_sha256,
                             args.coverage_report, args.coverage_report_sha256, args.output,
                             args.approved_source_sha256, args.approved_plan_sha256)
    else:
        parser.error("select explicit compose or verify mode; no implicit real run")
    print(json.dumps({"status": report["status"], "accepted": report["accepted"]}, allow_nan=False))
    return 0 if report.get("status", "").startswith(("COMPOSED", "PASS")) else 1


if __name__ == "__main__":
    raise SystemExit(cli())
