#!/usr/bin/env python
"""Independent, offline consumer for the single Narva focus-height proposal.

The default invocation runs only analytical fixtures.  The candidate is not
read unless --run-candidate is supplied after reviewer approval.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

G = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010")
RS = G / "global-operator-prototype/real-sector-preflight"
HERE = RS / "focus-unit"
PLAN = RS / "PLAN_FOCUS_1981.md"
AUTHOR = RS / "author_focus_1981.py"
BOUND = RS / "focus-1981-univariable-bound.json"
LOCAL_DIAG = RS / "focus-1981-local-coverage-diagnostic.json"
CANDIDATE = HERE / "author-run-01/candidate-terrain.npz"
AUTHOR_RECEIPT = HERE / "author-run-01/receipt.json"
BASE = G / "compound-selection/run-02/candidate-terrain.npz"
EV82_B = Path(r"E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz")
EV79 = Path(r"E:/DayZ-Baltic-Build/v30-narva-dry-bank-relief-20261010/candidate/terrain.npz")
P_PATH = EV79.parent / "plane.npy"
F_PATH = EV79.parent / "visible-field.npy"
CONS = EV79.parent.parent / "constraints.npz"
PRIOR = Path(r"E:/DayZ-Baltic-Build/v30-remaining-exact-dry-support-20261009/constraints.npz")
CORRIDORS = Path(r"E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson")
DECISION = Path(r"C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/evidence/v30-navigation-contract-2026-10-08/decision.json")
CIVIL = RS / "civil-run-01.json"
SELECTED_REVIEW = G / "crest-extension/selected-consumer-runs/attempt-03/review.json"
DEPLOY = G / "build-selected/deploy.json"
WRP = G / "build-selected/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp"
WORLD_PBO = Path(r"P:/Mods/@DayZ_Baltic_EV93_SelectedBankPreviewV1/Addons/narva_trial.pbo")
WATER_PBO = Path(r"P:/Mods/@DayZ_Baltic_EV93_SelectedBankPreviewV1/Addons/baltic_water_v30.pbo")
BOUNDS = Path(r"E:/DayZ-Baltic-Build/v30-low-water-components-20261009/compiled-instance-bounds.json")
MODEL_DIR = Path(r"E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30")
WORKSPACE = Path(r"C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290")

EV88_PATH = Path(r"E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/review-independent/verify_ev88q.py")
EV91_PATH = Path(r"E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev91-descent/consumer/runs/attempt-02/verify_ev91.py")
EV87_PATH = Path(r"E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py")
CV_PATH = Path(r"E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/review-independent/verify_coverage_contract.py")
SHAPE_PATH = Path(r"E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/next-method-consumer/shape_contract.py")
FACE_INDEX_BUILDER = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/ev93-face-index/build_face_index.py")
FACE_INDEX_RUN = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/ev93-face-index/runs/20261010T092417Z-63d4cec3")
FACE_INDEX_MANIFEST = FACE_INDEX_RUN / "manifest.json"
FACE_INDEX_VERIFY = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/review-independent/runs/attempt-01/verification.json")
FACE_INDEX_SOURCE_WRP = Path(r"E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp")
BOUND_DERIVATION = RS / "derive_focus_univariable_bound.py"

PINNED = {
    PLAN: "2ec25fb308cc41334db5ee3d529290473498295d8e7657814b208fbc6f55c4b2",
    AUTHOR: "31be64f4261f5baf282baf68fd573d8584a678a9c9366c029612964c4d15bc8b",
    BOUND: "feccc8ebdb9b9ddbf0a5151e5aa49841ae980682a3c2fdd80287d48cf2eb444a",
    LOCAL_DIAG: "050dae41c0ac5eb69c28e73d7a2bd219ae438009c6a489a6aad98b0b20a60051",
    CANDIDATE: "30d0ed33e477846297a17e758e34a51490d54ee809e8b63ec9d69229170d15a1",
    AUTHOR_RECEIPT: "e9d6dc6b1110721ae26a6b0e90214dbebfbef72af456c2416df4637c116ba018",
    BASE: "6e27557315eb65ecc69052e1ec387304a19f37eaa4f5167ab82fb607f095461d",
    EV82_B: "f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0",
    EV79: "dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c",
    P_PATH: "768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0",
    F_PATH: "f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c",
    CONS: "ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c",
    PRIOR: "18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370",
    CORRIDORS: "28866a8cf6ff57f2f825228046164ef939bc22bca9948eb96fe2463da46af343",
    DECISION: "d510af67cc4016a0ba7192aa01c070d314b9bc7e49b6256ca6ffaf64fc05b843",
    CIVIL: "1f1670961bd89bfe284ac3175201c1dc2529f6c5b13bb7f4796fab4ac382cd53",
    SELECTED_REVIEW: "656e676e38817592ed96d13ddeb1693d2a9bead152770256b0b21e665cedf8ec",
    DEPLOY: "3c8a2d5ec7eaaf62ddd4cd990ea29370649ec88423d8f4a52494db3de3fb450a",
    WRP: "8eff8a159379ebb52144625c3d5faa0c2a9b29712f148806ef6c2e1ba462b1a3",
    WORLD_PBO: "cb4ffc6b7de96c2e9de5c561ac95497b4310ca6f3ae48c6ddab80f6fcd225ab6",
    WATER_PBO: "3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14",
    BOUNDS: "863e9539203e59fe77b9c7d4949da3a69b4991249941e15b887b60ff9e81ee62",
    EV88_PATH: "82a988790e6bdfc0289bcb7c32cb0afd1210e07b264d92731aba266bc5980f78",
    EV91_PATH: "5e726b93642f5db531193a8f1d85afabd139c7b9ac3afca4479df793afd53668",
    EV87_PATH: "964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27",
    CV_PATH: "214f0eddda08d84ce18c921fcdbe01298f608c9a5c19b7e5246bb9e71df5dc2b",
    SHAPE_PATH: "8cd9d0fbea03c05e5ae53a31676d79ec2364be83c055213446f6c8599245d533",
    FACE_INDEX_BUILDER: "d1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e",
    FACE_INDEX_MANIFEST: "c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c",
    FACE_INDEX_VERIFY: "b498e7d68835b199399655451e5e01ac81acb3149dbb9bf882b94858141521d4",
    FACE_INDEX_SOURCE_WRP: "3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6",
    BOUND_DERIVATION: "ffde2a49fbd5ae9106a68eae4dbee27ac5565c05723c0795b6daca9b2dbafc39",
}
PINNED_NAMES = {
    "PLAN": PLAN, "AUTHOR": AUTHOR, "BOUND": BOUND, "LOCAL_DIAG": LOCAL_DIAG,
    "CANDIDATE": CANDIDATE, "AUTHOR_RECEIPT": AUTHOR_RECEIPT, "BASE": BASE,
    "EV82_B": EV82_B, "EV79": EV79, "P_PATH": P_PATH, "F_PATH": F_PATH,
    "CONS": CONS, "PRIOR": PRIOR, "CORRIDORS": CORRIDORS, "DECISION": DECISION,
    "CIVIL": CIVIL, "SELECTED_REVIEW": SELECTED_REVIEW, "DEPLOY": DEPLOY,
    "WRP": WRP, "WORLD_PBO": WORLD_PBO, "WATER_PBO": WATER_PBO,
    "BOUNDS": BOUNDS, "EV88_PATH": EV88_PATH, "EV91_PATH": EV91_PATH,
    "EV87_PATH": EV87_PATH, "CV_PATH": CV_PATH, "SHAPE_PATH": SHAPE_PATH,
    "FACE_INDEX_BUILDER": FACE_INDEX_BUILDER, "FACE_INDEX_MANIFEST": FACE_INDEX_MANIFEST,
    "FACE_INDEX_VERIFY": FACE_INDEX_VERIFY, "FACE_INDEX_SOURCE_WRP": FACE_INDEX_SOURCE_WRP,
    "BOUND_DERIVATION": BOUND_DERIVATION,
}
PINNED.update({name: PINNED[path] for name, path in PINNED_NAMES.items()})

FOCUS = (840, 370)
WINDOW = (832, 849, 362, 379)  # half-open rows, columns
CELLS = {(839, 369), (839, 370), (840, 369), (840, 370)}
TARGET = np.float32(3.278029680252075)
DECISION_VALUES = {"width_m": 24.0, "nominal_corridor_min_depth_m": 0.95,
                   "high_navigable_bed_floor_m": 1.0}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def json_safe(value):
    """Keep tuple-key diagnostic maps and NumPy scalars serializable without dropping data."""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        seq = sorted(value, key=repr) if isinstance(value, set) else value
        return [json_safe(x) for x in seq]
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def load_module(name: str, path: Path, expected: str):
    actual = sha(path)
    if actual != expected:
        raise AssertionError(f"helper source drift: {path}: {actual} != {expected}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_stack():
    ev = load_module("focus_ev88", EV88_PATH, PINNED["EV88_PATH"])
    ev91 = load_module("focus_ev91", EV91_PATH, PINNED["EV91_PATH"])
    ev87 = load_module("focus_ev87", EV87_PATH, PINNED["EV87_PATH"])
    cv = load_module("focus_cv", CV_PATH, PINNED["CV_PATH"])
    shape = load_module("focus_shape", SHAPE_PATH, PINNED["SHAPE_PATH"])
    # Bind the immutable EV93-selected deployed artifacts into the frozen helpers.
    ev.B_PATH, ev.B_SHA = BASE, PINNED["BASE"]
    ev.B_DEPLOY, ev.B_WRP, ev.MODEL_DIR, ev.BOUNDS = DEPLOY, WRP, MODEL_DIR, BOUNDS
    ev87.B_DEPLOY_WORLD_SHA = PINNED["WORLD_PBO"]
    ev87.B_DEPLOY_WATER_SHA = PINNED["WATER_PBO"]
    ev87.B_STAGE_WPR_SHA = PINNED["WRP"]
    ev87.MODEL_DIR = MODEL_DIR
    cv.W, cv.MODEL_DIR, cv.BOUNDS = WORKSPACE, MODEL_DIR, BOUNDS
    cv.ev = ev87
    return ev, ev91, ev87, cv, shape


def readset(include_candidate: bool = True) -> dict[str, str]:
    paths = [p for p in PINNED if isinstance(p, Path)]
    if not include_candidate:
        paths = [p for p in paths if p not in (CANDIDATE, AUTHOR_RECEIPT)]
    paths.append(Path(__file__).resolve())
    out = {str(p): sha(p) for p in paths}
    for p in paths:
        want = PINNED.get(p)
        if want is not None and out[str(p)] != want:
            raise AssertionError(f"pinned input drift: {p}: {out[str(p)]} != {want}")
    return out


def load_bundle() -> dict:
    with np.load(BASE, allow_pickle=False) as z:
        b = {k: z[k] for k in z.files}
    with np.load(EV82_B, allow_pickle=False) as z:
        b82 = {k: z[k] for k in z.files}
    with np.load(EV79, allow_pickle=False) as z:
        e79 = {k: z[k] for k in z.files}
    p = np.load(P_PATH, allow_pickle=False)
    f = np.load(F_PATH, allow_pickle=False)
    with np.load(CONS, allow_pickle=False) as z:
        constraints = {k: z[k] for k in z.files}
    with np.load(PRIOR, allow_pickle=False) as z:
        prior = {k: z[k] for k in z.files}
    corridors = json.loads(CORRIDORS.read_text(encoding="utf-8"))
    selected = json.loads(SELECTED_REVIEW.read_text(encoding="utf-8"))
    if (selected.get("status") != "PASS_INCREMENTAL_NONREGRESSION" or
            selected.get("information", {}).get("candidate_sha256") != PINNED["BASE"] or
            selected.get("information", {}).get("global_contract_status") != "OPEN_INHERITED_MAP_DEFECTS" or
            selected.get("information", {}).get("source_global_status") != "FAIL_INCREMENTAL_NONREGRESSION"):
        raise AssertionError("EV93 selected-base acceptance/identity anchor changed")
    if b["heights"].dtype != np.float32 or b["heights"].shape != (2048, 2048):
        raise AssertionError("selected EV93 base height grid mismatch")
    if p.shape != (2047, 2047) or f.shape != (2047, 2047, 4):
        raise AssertionError("P/F shape mismatch")
    if any(b[k].tobytes() != b82[k].tobytes() for k in b if k != "heights"):
        raise AssertionError("EV93 selected metadata differs from EV82 base")
    if not np.array_equal(b["heights"][WINDOW[0]:WINDOW[1], WINDOW[2]:WINDOW[3]],
                          b82["heights"][WINDOW[0]:WINDOW[1], WINDOW[2]:WINDOW[3]]):
        raise AssertionError("focus window is not exactly EV82 B in selected EV93")
    return {"B": b, "EV82_B": b82, "EV79": e79, "P": p, "F": f,
            "constraints": constraints, "prior": prior, "corridors": corridors}


def candidate_arrays(candidate_path: Path, receipt_path: Path, bundle: dict):
    if sha(candidate_path) != PINNED["CANDIDATE"] or sha(receipt_path) != PINNED["AUTHOR_RECEIPT"]:
        raise AssertionError("single-point author artifact identity mismatch")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("status") != "SINGLE_POINT_AUTHORED_PENDING_CONSUMER":
        raise AssertionError("unexpected author state")
    if receipt.get("base_sha256") != PINNED["BASE"] or receipt.get("candidate_sha256") != PINNED["CANDIDATE"]:
        raise AssertionError("author receipt base/candidate pin mismatch")
    if Path(receipt.get("candidate_path", "")) != candidate_path or Path(receipt.get("base_path", "")) != BASE:
        raise AssertionError("author receipt paths do not match the pinned artifacts")
    start = receipt.get("source_hashes_start", {})
    end = receipt.get("source_hashes_end", {})
    if not start or start != end:
        raise AssertionError("author receipt readset is absent or unstable")
    for path in (BASE, EV82_B, PLAN, AUTHOR, BOUND, LOCAL_DIAG):
        if start.get(str(path)) != PINNED[path]:
            raise AssertionError(f"author receipt does not bind source input: {path}")
    if receipt.get("changed_rc") != [[*FOCUS]] or receipt.get("height_after_m") != float(TARGET):
        raise AssertionError("author receipt does not describe the approved single focus delta")
    with np.load(candidate_path, allow_pickle=False) as z:
        candidate = {k: z[k] for k in z.files}
    base = bundle["B"]
    changed = validate_one_point_arrays(base, candidate, FOCUS, TARGET)
    return candidate, changed, receipt


def validate_one_point_arrays(base: dict, candidate: dict, focus: tuple[int, int], target=None):
    if set(candidate) != set(base):
        raise AssertionError("candidate NPZ keys differ from selected base")
    changed = np.argwhere(candidate["heights"] != base["heights"])
    if not np.array_equal(changed, np.asarray([focus], dtype=np.int64)):
        raise AssertionError(f"candidate is not the one-point delta: {changed[:10].tolist()}")
    if candidate["heights"].dtype != np.float32 or (target is not None and candidate["heights"][focus] != target):
        raise AssertionError("candidate focus value/dtype mismatch")
    for key in base:
        if key != "heights" and (candidate[key].dtype != base[key].dtype or
                                  candidate[key].shape != base[key].shape or
                                  candidate[key].tobytes() != base[key].tobytes()):
            raise AssertionError(f"candidate changed non-height array {key}")
    return changed


def semantic_protections_clear(masks: dict) -> bool:
    # `actually_wet` is an informational footprint mask; the authorized focal
    # bank unit may be near water. Semantic/civil/P9 protections remain hard.
    return all(not masks[name] for name in (
        "other_fixed", "engineering_halo", "large_lake_banks", "reserve",
        "platform", "class_nonzero"))


def local_energy(ev, base_h: np.ndarray, candidate_h: np.ndarray,
                 origin: tuple[int, int] = (0, 0)) -> dict:
    records = ev.stencil_records(window=WINDOW, core=(FOCUS[0], FOCUS[0] + 1,
                                                       FOCUS[1], FOCUS[1] + 1),
                                 variables=[FOCUS])
    by_family = {"Dxx": {"B": 0.0, "H": 0.0}, "Dzz": {"B": 0.0, "H": 0.0},
                 "Dxz": {"B": 0.0, "H": 0.0}}
    counts = {"Dxx": 0, "Dzz": 0, "Dxz": 0}
    for rec in records:
        kind = rec["kind"]
        counts[kind] += 1
        weight = 2.0 if kind == "Dxz" else 1.0
        for label, grid in (("B", base_h), ("H", candidate_h)):
            value = sum(float(coef) * float(grid[(int(node[0]) - origin[0],
                                                  int(node[1]) - origin[1])])
                        for node, coef in zip(rec["nodes"], rec["coeff"]))
            by_family[kind][label] += weight * value * value
    local_focus = (FOCUS[0] - origin[0], FOCUS[1] - origin[1])
    delta = float(candidate_h[local_focus]) - float(base_h[local_focus])
    fidelity = {"B": 0.0, "H": 0.25 * delta * delta}
    total_b = sum(v["B"] for v in by_family.values()) + fidelity["B"]
    total_h = sum(v["H"] for v in by_family.values()) + fidelity["H"]
    return {"gate_strict_total_cost_decrease": bool(total_h < total_b),
            "stencil_count": len(records), "counts_by_family": counts,
            "energy_by_family": by_family, "fidelity_coefficient": 0.25,
            "fidelity_cost": fidelity, "total_cost": {"B": total_b, "H": total_h,
                                                         "delta_H_minus_B": total_h - total_b}}


def validate_domain_and_bounds(ev, bundle, candidate_h):
    domain = ev.reconstruct_domain(bundle)
    r, c = FOCUS
    ir, ic = r - ev.WINDOW[0], c - ev.WINDOW[2]
    core_r, core_c = r - ev.CORE[0], c - ev.CORE[2]
    masks = {name: bool(mask[ir, ic]) for name, mask in domain["masks"].items()}
    # This proposal may move a non-protected dry bank node. No semantic restriction is waived.
    gate_semantic = semantic_protections_clear(masks)
    if not gate_semantic:
        raise AssertionError(f"focus has a non-waivable semantic protection: {masks}")
    if not any(tuple(map(int, x)) == FOCUS for x in domain["variables"]):
        raise AssertionError("focus is not in reconstructed EV88 eligible domain")
    single = dict(domain)
    single["variables"] = np.asarray([FOCUS], dtype=np.int32)
    single["variables_set"] = {FOCUS}
    crossings = ev.reconstruct_crossings(bundle, single)
    lower = float(crossings["lower"][core_r, core_c])
    upper = float(crossings["upper"][core_r, core_c])
    h = float(candidate_h[FOCUS])
    b = float(bundle["B"]["heights"][FOCUS])
    checks = {
        "semantic_protections_clear_except_nonprotective_actual_wet_mask": gate_semantic,
        "single_node_exactly_within_ev79_budget_and_physical_floor": lower <= h <= upper,
        "candidate_below_or_equal_EV82_plus_0_5_cap": h <= b + 0.5,
        "float32_target_is_inside_reconstructed_inward_interval": lower <= float(np.float32(h)) <= upper,
    }
    if not all(checks.values()):
        raise AssertionError(f"focus eligibility/bounds fail: {checks}; bounds={lower, upper}")
    return {"gates": checks, "masks_at_focus": masks, "bounds_m": [lower, upper],
            "crossing_records": len(crossings["records"]),
            "crossing_max_shift_m": 1.0, "crossing_details": crossings["records"]}


def contact_margin_ok(kind: str, margin: float) -> bool:
    """EV91 unknown-face rule: P has a zero floor; F retains its strict 2e-5m margin."""
    if not math.isfinite(float(margin)):
        return False
    return float(margin) >= 0.0 if kind == "physical" else float(margin) > 2e-5


def contact_bound(clearance_m: float, focus_weight: float, kind: str) -> float:
    """Strict maximum descent allowed by one affine zero-area contact vertex."""
    w = float(focus_weight)
    if w <= 1e-12:
        return math.inf
    margin_floor = 0.0 if kind == "physical" else 2e-5
    return (float(clearance_m) - margin_floor) / w


def visible_unknown_clearance_gate(records):
    """Visible unknown-face certification is strict in B, H, and L32."""
    margins = []
    for rec in records:
        states = rec.get("min_clearance_m", {})
        values = [states.get("B"), states.get("candidate"),
                  rec.get("min_clearance_L32_m")]
        if any(v is None or not math.isfinite(float(v)) for v in values):
            return {"pass": False, "minimum_clearance_m": None,
                    "record_count": len(records), "reason": "missing_or_nonfinite_clearance"}
        margins.extend(float(v) for v in values)
    minimum = min(margins) if margins else None
    return {"pass": all(v > 2e-5 for v in margins),
            "minimum_clearance_m": minimum, "record_count": len(records),
            "required_strictly_greater_than_m": 2e-5}


def local_budget_ok(elapsed_seconds: float, budget_seconds: float = 120.0) -> bool:
    return math.isfinite(float(elapsed_seconds)) and 0.0 <= float(elapsed_seconds) <= float(budget_seconds)


def contact_descent_allowed(descent_m: float, strict_bound_m: float) -> bool:
    return math.isfinite(float(descent_m)) and math.isfinite(float(strict_bound_m)) and float(descent_m) < float(strict_bound_m)


def contact_geometry_points(geom):
    """Return every coordinate that can extremize an affine margin on a contact."""
    if geom.is_empty:
        return []
    kind = geom.geom_type
    if kind == "Point":
        return [np.asarray(geom.coords[0], dtype=np.float64)]
    if kind in ("LineString", "LinearRing"):
        return [np.asarray(x, dtype=np.float64) for x in geom.coords]
    if kind == "Polygon":
        out = [np.asarray(x, dtype=np.float64) for x in geom.exterior.coords]
        for ring in geom.interiors:
            out.extend(np.asarray(x, dtype=np.float64) for x in ring.coords)
        return out
    out = []
    for part in getattr(geom, "geoms", []):
        out.extend(contact_geometry_points(part))
    return out


def _face_polygon_and_y(record):
    from shapely.geometry import LineString, Point, Polygon
    xyz = np.asarray(record["xyz"], dtype=np.float64)
    xz = xyz[:, [0, 2]]
    if not int(record["degenerate"]):
        poly = Polygon(xz)
        if not poly.is_valid:
            raise AssertionError("nondegenerate indexed ODOL face has invalid XZ polygon")
        coeff = np.asarray(record["plane_y_xz"], dtype=np.float64)
        if np.max(np.abs((xz @ coeff[:2] + coeff[2]) - xyz[:, 1])) > 2e-7:
            raise AssertionError("indexed ODOL affine plane disagrees with its three vertices")
        return poly, lambda pts: np.asarray(pts, dtype=np.float64) @ coeff[:2] + coeff[2]
    unique = np.unique(xz, axis=0)
    if len(unique) == 1:
        geom = Point(unique[0])
        point_y = float(np.max(xyz[:, 1]))
        return geom, lambda pts: np.full(len(pts), point_y, dtype=np.float64)
    i, j = max(((i, j) for i in range(3) for j in range(i + 1, 3)),
               key=lambda ij: float(np.linalg.norm(xz[ij[1]] - xz[ij[0]])))
    a, b = xz[i], xz[j]
    axis = b - a
    den = float(axis @ axis)
    if den <= 0.0:
        raise AssertionError("degenerate face has no usable XZ segment")
    t_vertices = ((xz - a) @ axis) / den
    projected = a + t_vertices[:, None] * axis
    if np.max(np.linalg.norm(projected - xz, axis=1)) > 1e-8:
        raise AssertionError("degenerate face vertices are not collinear in XZ")
    y0, y1 = float(xyz[i, 1]), float(xyz[j, 1])
    if np.max(np.abs((y0 + t_vertices * (y1 - y0)) - xyz[:, 1])) > 2e-7:
        # A degenerate face has no unique affine plane; max-Y is the conservative surface.
        y_max = float(np.max(xyz[:, 1]))
        y_eval = lambda pts: np.full(len(pts), y_max, dtype=np.float64)
    else:
        y_eval = lambda pts: y0 + (((np.asarray(pts, dtype=np.float64) - a) @ axis) / den) * (y1 - y0)
    return LineString([a, b]), y_eval


def load_contact_index(ev, bundle):
    """Load the COMPLETE frozen face index and prove its water placements match selected EV93."""
    index_mod = load_module("focus_face_range_index", FACE_INDEX_BUILDER,
                            PINNED["FACE_INDEX_BUILDER"])
    index = index_mod.FaceRangeIndex(FACE_INDEX_RUN)
    manifest = index.manifest
    verification = json.loads(FACE_INDEX_VERIFY.read_text(encoding="utf-8"))
    if verification.get("status") != "PASS_INDEX_AND_SAMPLED_EXPOSURE":
        raise AssertionError("pinned index verification is not a PASS")
    if verification.get("manifest_sha256") != PINNED[FACE_INDEX_MANIFEST]:
        raise AssertionError("index verification does not bind the pinned manifest")
    identity = manifest["base_identity"]
    if identity.get("terrain_sha256") != PINNED["EV82_B"]:
        raise AssertionError("face index terrain identity is not EV82-B")
    if identity.get("water_pbo_sha256") != PINNED["WATER_PBO"]:
        raise AssertionError("face index water PBO differs from selected EV93")
    if manifest.get("status") != "COMPLETE" or int(manifest.get("counts", {}).get("faces", -1)) != 883308:
        raise AssertionError("face index is not the pinned complete 883308-face index")
    source_paths = [Path(x) for x in manifest.get("input_hashes", {})
                    if Path(x).name.lower() == "baltic_trial.wrp"]
    if len(source_paths) != 1 or source_paths[0] != FACE_INDEX_SOURCE_WRP:
        raise AssertionError("face-index source WRP path is not the pinned baseline WRP")
    if sha(FACE_INDEX_SOURCE_WRP) != PINNED["FACE_INDEX_SOURCE_WRP"]:
        raise AssertionError("baseline WRP used by the index has drifted")
    if identity.get("wrp_source_sha256") != PINNED["FACE_INDEX_SOURCE_WRP"]:
        raise AssertionError("index manifest WRP source pin mismatch")

    # Check the entire water-object identity, not merely the nearby PBO or XZ bounds.
    wrp_before = ev.load_wrp_api(FACE_INDEX_SOURCE_WRP, WORKSPACE)
    wrp_selected = ev.load_wrp_api(WRP, WORKSPACE)
    filter_water = lambda o: "baltic_water_v30" in o["name"].replace("\\", "/").lower()
    old = {int(o["id"]): o for o in wrp_before["objects"] if filter_water(o)}
    selected = {int(o["id"]): o for o in wrp_selected["objects"] if filter_water(o)}
    if len(old) != 18024 or set(old) != set(selected):
        raise AssertionError("water object ID population differs between indexed WRP and EV93 WRP")
    id_digest = hashlib.sha256(np.asarray(sorted(old), dtype="<i4").tobytes()).hexdigest()
    if manifest.get("water_object_ids_sha256") != id_digest:
        raise AssertionError("complete index water-object ID digest disagrees with its source WRP")
    changed_transforms = []
    for oid in sorted(old):
        a, b = old[oid], selected[oid]
        if (a["name"] != b["name"] or not np.array_equal(
                np.asarray(a["matrix"], dtype=np.float64), np.asarray(b["matrix"], dtype=np.float64))):
            changed_transforms.append(int(oid))
    if changed_transforms:
        raise AssertionError(f"water WRP transforms differ at {len(changed_transforms)} objects")
    if not np.array_equal(bundle["B"]["heights"][839:842, 369:372],
                          bundle["EV82_B"]["heights"][839:842, 369:372]):
        raise AssertionError("EV93 terrain differs from the index baseline on all four contact cells")
    models = {int(row["model_id"]): row for row in manifest["models"]}
    used_ids = set()
    used_model_ids = set()
    for r, c in sorted(CELLS):
        for kind in ("physical", "visible"):
            rows = index.query_cell(r, c, kind=kind)
            used_ids.update(int(x) for x in rows["object_id"])
            for mid in np.unique(rows["model_id"]):
                used_model_ids.add(int(mid))
                model = models[int(mid)]
                model_path = MODEL_DIR / model["basename"]
                if sha(model_path) != model["sha256"]:
                    raise AssertionError(f"indexed compiled ODOL drift: {model_path}")
    return {"index": index, "manifest": manifest,
            "water_object_count": len(old), "water_object_transforms_equal": True,
            "local_index_object_ids": sorted(used_ids),
            "model_count_local": len(used_model_ids),
            "reverified_before_local_checks": bool(index.reverify())}


def verify_zero_area_unknown_contacts(ev87, context, bundle, base_h, candidate_h, physical_lower):
    """Rebuild unknown P/F point/line contacts from EV93's actual indexed water faces."""
    from shapely.geometry import Polygon
    index = context["index"]
    p = np.asarray(bundle["P"], dtype=np.float64)
    f = np.asarray(bundle["F"], dtype=np.float64)
    base_h = np.asarray(base_h, dtype=np.float32)
    candidate_h = np.asarray(candidate_h, dtype=np.float32)
    lower_h = base_h.copy()
    lower_h[FOCUS] = np.float32(physical_lower)
    surfaces = {"B": base_h, "H": candidate_h, "L32": lower_h}
    thresholds = {"physical": 0.0, "visible": 2e-5}
    contacts = []
    counts = {"physical": 0, "visible": 0}
    bound_candidates = {"physical": [], "visible": []}
    for r, c in sorted(CELLS):
        xy = ev87.cell_xy(r, c)
        heights = {label: ev87.corner_values(grid, r, c) for label, grid in surfaces.items()}
        for kind in ("physical", "visible"):
            face_rows = index.query_cell(r, c, kind=kind)
            for ti, tri in enumerate(ev87.TRIS):
                tri_ids = np.asarray(tri, dtype=np.int64)
                if kind == "physical":
                    unknown = not math.isfinite(float(p[r, c]))
                else:
                    unknown = int(np.isfinite(f[r, c, tri_ids]).sum()) < 3
                if not unknown:
                    continue
                native = Polygon(xy[tri_ids])
                ground_coeffs = {label: ev87.affine_coeff(xy[tri_ids], values[tri_ids])
                                 for label, values in heights.items()}
                tri_nodes = ((r,c),(r,c+1),(r+1,c),(r+1,c+1))
                triangle_nodes = tuple(tri_nodes[int(i)] for i in tri_ids)
                focus_corner = triangle_nodes.index(FOCUS) if FOCUS in triangle_nodes else None
                for i in range(len(face_rows["object_id"])):
                    rec = {key: face_rows[key][i] for key in face_rows}
                    face_geom, face_y = _face_polygon_and_y(rec)
                    overlap = face_geom.intersection(native)
                    if overlap.is_empty or float(overlap.area) != 0.0:
                        continue  # Positive-area unknown coverage is checked by EV90/91 coverage gates.
                    pts = contact_geometry_points(overlap)
                    if not pts:
                        continue
                    margins = {}
                    focus_weights = []
                    for pt in pts:
                        weight = 0.0
                        if focus_corner is not None:
                            a = np.column_stack((xy[tri_ids, 0], xy[tri_ids, 1], np.ones(3)))
                            weights = np.linalg.solve(a.T, np.asarray([pt[0], pt[1], 1.0]))
                            weight = float(weights[focus_corner])
                            if weight < -1e-9 or weight > 1.0 + 1e-9:
                                raise AssertionError("contact point has invalid native-triangle barycentric weight")
                            weight = min(1.0, max(0.0, weight))
                        focus_weights.append(weight)
                    for label, coeff in ground_coeffs.items():
                        margins[label] = [float(ev87.eval_affine(coeff, pt[None, :])[0] - face_y(pt[None, :])[0])
                                          for pt in pts]
                    floor = thresholds[kind]
                    bound_values = []
                    for margin, weight in zip(margins["B"], focus_weights):
                        if weight > 1e-12:
                            bound_values.append(contact_bound(margin, weight, kind))
                    if bound_values:
                        bound_candidates[kind].append(min(bound_values))
                    record_pass = all(contact_margin_ok(kind, margin)
                                      for label in ("B", "H", "L32") for margin in margins[label])
                    counts[kind] += 1
                    contacts.append({"kind": kind, "cell_rc": [r, c], "native_triangle": ti,
                        "object_id": int(rec["object_id"]), "model_id": int(rec["model_id"]),
                        "face_id": int(rec["face_id"]), "degenerate_face": bool(rec["degenerate"]),
                        "geometry_type": overlap.geom_type, "contact_vertex_count": len(pts),
                        "margins_m": margins, "min_margins_m": {k: min(v) for k,v in margins.items()},
                        "max_focus_weight": max(focus_weights, default=0.0),
                        "strict_descent_bound_m": min(bound_values) if bound_values else None,
                        "passes_B_H_L32": record_pass})
    desc = float(base_h[FOCUS]) - float(candidate_h[FOCUS])
    bound = json.loads(BOUND.read_text(encoding="utf-8"))
    reported = bound["strict_burial_bound_m_unknown_cells_by_surface"]
    derived = {kind: min(values) if values else None for kind, values in bound_candidates.items()}
    identity_ok = (context["water_object_transforms_equal"] and
        bound.get("inputs", {}).get("manifest") == PINNED["FACE_INDEX_MANIFEST"] and
        bound.get("inputs", {}).get("linked_face_index_verification") == PINNED["FACE_INDEX_VERIFY"] and
        bound.get("inputs", {}).get("linked_WRP") == PINNED["FACE_INDEX_SOURCE_WRP"] and
        bound.get("inputs", {}).get("analysis_script") == PINNED["BOUND_DERIVATION"])
    # Reconcile raw geometric bounds first; apply the visible strict margin only
    # as a separate acceptance bound, never as a tolerance in the comparison.
    reported_raw = {k: float(reported[k]["strict_bound_m"])
                    for k in ("physical", "visible")}
    reconstructed_raw = {
        "physical": derived["physical"],
        "visible": (None if derived["visible"] is None else derived["visible"] + 2e-5),
    }
    raw_bounds_match = all(reconstructed_raw[k] is not None and
        abs(float(reconstructed_raw[k]) - reported_raw[k]) <= 2e-8
        for k in ("physical", "visible"))
    accepted_bounds = {
        "physical": reconstructed_raw["physical"],
        "visible": (None if reconstructed_raw["visible"] is None else
                    reconstructed_raw["visible"] - 2e-5),
    }
    contact_pass = all(row["passes_B_H_L32"] for row in contacts)
    descent_pass = all(accepted_bounds[k] is not None and
                       contact_descent_allowed(desc, float(accepted_bounds[k]))
                       for k in ("physical", "visible"))
    return {"gate_zero_area_unknown_contacts_B_H_L32": bool(contact_pass),
        "gate_strict_descent_below_reconstructed_zero_area_bounds": bool(descent_pass),
        "gate_bound_artifact_matches_actual_index_readset": bool(identity_ok and raw_bounds_match),
        "descent_m": desc, "reconstructed_raw_clearance_bounds_m": reconstructed_raw,
        "accepted_strict_descent_bounds_m": accepted_bounds,
        "bound_artifact_raw_strict_bounds_m": reported_raw,
        "bound_derivation_source_sha256": PINNED["BOUND_DERIVATION"],
        "plan_literal_derivation_sha256_erratum": {
            "plan_literal": "ffde2a49fbd5ae9106a68eae4dbbe27ac5565c05723c0795b6daca9b2dbafc39",
            "actual_pinned_source": PINNED["BOUND_DERIVATION"]},
        "thresholds_m": thresholds, "zero_area_unknown_contact_counts": counts,
        "zero_area_unknown_contacts": contacts,
        "index_identity": {"water_objects_same_ids_and_matrices": context["water_object_transforms_equal"],
            "local_water_object_ids": context["local_index_object_ids"],
            "manifest_sha256": PINNED["FACE_INDEX_MANIFEST"],
            "verification_sha256": PINNED["FACE_INDEX_VERIFY"],
            "index_reverified_before": context["reverified_before_local_checks"]}}


def local_corridor_and_civil(ev91, ev, ev87, bundle, candidate_h):
    cells = set(CELLS)
    p9_cells, _by_feature = ev91.p9_unknown_cells(ev, bundle)
    p9_nodes = {node for r, c in p9_cells for node in ((r,c),(r,c+1),(r+1,c),(r+1,c+1))}
    p9_gate = FOCUS not in p9_nodes
    civ = json.loads(CIVIL.read_text(encoding="utf-8"))
    road = {tuple(x) for x in civ["road"]["native_cells_rc_sorted"]}
    bridge = {tuple(x) for x in civ["bridge"]["native_cells_rc_sorted"]}
    civil_hits = sorted(cells & (road | bridge))
    civil_gate = not civil_hits
    corridor_report = ev91.affected_corridor_depth_report(ev, ev87, bundle, candidate_h, [FOCUS])
    corridor_gate = (corridor_report["unknown_area_in_changed_corridor_support_m2"] == 0.0 and
                     corridor_report["pass"])
    # The 1.0 m high-bed floor is vacuous only if no approved corridor geometry intersects these cells.
    from shapely.geometry import box, shape
    intersects = []
    for i, feature in enumerate(bundle["corridors"]["features"]):
        geom = shape(feature["geometry"])
        for r, c in sorted(cells):
            cellpoly = box(c * ev.CELL, ev.Z0 - (r + 1) * ev.CELL,
                           (c + 1) * ev.CELL, ev.Z0 - r * ev.CELL)
            inter = geom.intersection(cellpoly)
            if not inter.is_empty and inter.area > 0:
                intersects.append({"feature": i, "cell": [r, c], "area_m2": float(inter.area)})
    rr, cc = FOCUS
    x, z = cc * ev.CELL, ev.Z0 - rr * ev.CELL
    in_high_bed_floor = (int(bundle["B"]["cls"][rr,cc]) == 3 and
        float(bundle["B"]["level"][rr,cc]) >= 2.0 and
        math.hypot(x - ev.NARVA_CENTER_XZ[0], z - ev.NARVA_CENTER_XZ[1]) > ev.NARVA_EXCLUSION_M)
    high_bed_floor_gate = (not in_high_bed_floor or float(candidate_h[FOCUS]) >= 1.0)
    return {"gates": {"no_P9_unknown_corridor_cell_corner_changed": p9_gate,
                      "no_road_or_bridge_cell_intersection": civil_gate,
                      "known_corridor_nominal_depth_at_least_0_95m": corridor_gate,
                      "high_navigable_bed_floor_1m_if_applicable": high_bed_floor_gate},
            "p9_unknown_cells_incident_to_focus": sorted([list(x) for x in p9_cells if FOCUS in
                 ((x[0],x[1]),(x[0],x[1]+1),(x[0]+1,x[1]),(x[0]+1,x[1]+1))]),
            "civil_cell_hits": civil_hits, "corridor_cell_intersections": intersects,
            "high_bed_floor_scope_at_focus": in_high_bed_floor,
            "corridor_depth": corridor_report}


def run_candidate(candidate_path: Path = CANDIDATE, receipt_path: Path = AUTHOR_RECEIPT) -> dict:
    readset_start = readset(include_candidate=True)
    ev, ev91, ev87, cv, shape = load_stack()
    bundle = load_bundle()
    candidate, changed_rc, receipt = candidate_arrays(candidate_path, receipt_path, bundle)
    contact_context = load_contact_index(ev87, bundle)
    # The 120-second plan budget is only for candidate-local computations.
    # Hashing inputs and loading/reverifying the full face index are outside it.
    local_started = time.monotonic()
    hb = np.asarray(bundle["B"]["heights"], dtype=np.float32)
    hh = np.asarray(candidate["heights"], dtype=np.float32)
    changed = [(int(r), int(c)) for r, c in changed_rc]

    domain_report = validate_domain_and_bounds(ev, bundle, hh)
    contact_report = verify_zero_area_unknown_contacts(
        ev87, contact_context, bundle, hb, hh, domain_report["bounds_m"][0])
    shape_report = shape.evaluate_shape(hb, hh, WINDOW, FOCUS)
    energy_report = local_energy(ev, hb, hh)
    topology = ev.topology_check(ev, hb, hh, bundle["P"], bundle["F"], CELLS)
    water_geom_gates = {
        "P_F_SEA_corner_signs_preserved": topology["signs_preserved"],
        "original_crossings_valid_and_shift_le_1m": topology["crossings_valid_and_within_1m"],
    }
    d8_centers, d8_witnesses, d8_exempt = ev91.independent_d8(hb, [FOCUS])
    d8 = ev91.check_d8_candidate(hh, d8_witnesses)
    touched_mask = np.zeros(hb.shape, dtype=bool)
    touched_mask[FOCUS] = True

    # Full angle arrays are required by the pinned non-regression p99/sector contract.
    sector = ev.local_sector_stats(ev87, hb, hh, changed)
    p99 = ev.p99_population_gate(ev87, sector["angles_b"], sector["angles_h"], bundle)
    scan = ev91.scan_compiled_fields(ev, ev87, bundle)
    p9_cells, _ = ev91.p9_unknown_cells(ev, bundle)
    partial_cells = ev91.partial_f_cells(ev, bundle)
    one_domain = ev.reconstruct_domain(bundle)
    lower = np.asarray(one_domain["lower"], dtype=np.float64).copy()
    crossings = ev.reconstruct_crossings(bundle, {**one_domain,
        "variables": np.asarray([FOCUS], dtype=np.int32), "variables_set": {FOCUS}})
    one_domain.update({"variables_set": {FOCUS}, "variables": np.asarray([FOCUS], dtype=np.int32),
                       "lower": crossings["lower"], "p9_unknown_cells": set(p9_cells)})
    unknown_certificate = ev91.certify_unknown_faces(ev, ev87, bundle, scan, one_domain, hh)
    unknown_gate = len(unknown_certificate["unresolved"]) == 0
    unknown_visible_l32 = visible_unknown_clearance_gate(
        unknown_certificate["by_kind"]["visible"])
    source_hashes = dict(readset_start)
    coverage = ev91.coverage_contract_ev90(
        ev, ev87, cv, hb, hh, bundle, changed,
        source_hashes,
        set(scan["above"]["physical"]) | set(scan["above"]["visible"]) |
        set(p9_cells) | set(partial_cells))
    corridor_civil = local_corridor_and_civil(ev91, ev, ev87, bundle, hh)

    shape_gates = {f"shape:{k}": bool(v) for k, v in shape_report["gates"].items()}
    water_gates = {f"water:{k}": bool(v) for k, v in coverage["gates"].items()}
    all_gates = {
        **{f"eligibility:{k}": bool(v) for k, v in domain_report["gates"].items()},
        **shape_gates,
        **water_gates,
        "objective:strict_total_affected_stencil_plus_fidelity_cost_decrease": energy_report["gate_strict_total_cost_decrease"],
        **water_geom_gates,
        "water:unknown_compiled_faces_certified_buried_or_P9_exact": unknown_gate,
        "water:unknown_visible_faces_B_H_L32_strictly_above_2e-5m": unknown_visible_l32["pass"],
        "water:zero_area_unknown_contacts_B_H_L32": contact_report["gate_zero_area_unknown_contacts_B_H_L32"],
        "water:strict_descent_below_zero_area_contact_bounds": contact_report["gate_strict_descent_below_reconstructed_zero_area_bounds"],
        "water:contact_bound_and_index_identity_reconciled": contact_report["gate_bound_artifact_matches_actual_index_readset"],
        "terrain:no_new_D8_witness_minima": d8["pass"],
        "terrain:slopes_le_max_35deg_or_baseline": sector["slopes_le_max35_or_B"],
        "terrain:no_new_touched_hinge_over_30_0001deg": sector["no_new_hinges_over_30_touched"],
        "terrain:affected_sector_max_nonworse": sector["affected_sector_max_nonworse"],
        "terrain:existing_population_p99_nonworse": p99["pass"],
        **{f"corridor_civil:{k}": bool(v) for k, v in corridor_civil["gates"].items()},
    }
    if len(d8_exempt) != 0:
        # Exemptions are allowed as reconstructed B minima, but reported; this focus has none.
        all_gates["terrain:no_new_D8_witness_minima"] = d8["pass"]
    if not all_gates:
        raise AssertionError("empty gate set")
    local_elapsed = time.monotonic() - local_started
    all_gates["verification:local_checks_within_120s"] = bool(local_elapsed <= 120.0)
    index_reverified_end = bool(contact_context["index"].reverify())
    all_gates["verification:face_index_reverified_before_and_after"] = bool(
        contact_context["reverified_before_local_checks"] and index_reverified_end)
    readset_end = readset(include_candidate=True)
    if readset_start != readset_end:
        raise AssertionError("input/source readset drifted during verification")
    for path, digest in source_hashes.items():
        if Path(path).is_file() and sha(Path(path)) != digest:
            raise AssertionError(f"late source/model drift: {path}")
    return {
        "status": "PASS_FOCAL_DELTA_OFFLINE" if all(all_gates.values()) else "FAIL_FOCAL_DELTA_OFFLINE",
        "scope": "single focal delta only; not a global map, native runtime, build, or visual acceptance",
        "candidate_sha256": sha(candidate_path), "author_receipt_sha256": sha(receipt_path),
        "base_ev93_sha256": PINNED["BASE"], "baseline_ev82_sha256": PINNED["EV82_B"],
        "changed_vertices": changed, "height_B_m": float(hb[FOCUS]), "height_H_m": float(hh[FOCUS]),
        "delta_m": float(hh[FOCUS] - hb[FOCUS]), "gates": all_gates,
        "shape": shape_report, "objective": energy_report, "eligibility_bounds": domain_report,
        "water_topology": topology, "unknown_compiled_face_certificate": unknown_certificate,
        "unknown_visible_l32_clearance": unknown_visible_l32,
        "zero_area_unknown_contact_certificate": contact_report,
        "compiled_coverage": coverage, "D8": {"centers": len(d8_centers), "witnesses": len(d8_witnesses),
            "baseline_strict_minima_exempt": d8_exempt, "result": d8},
        "terrain": {"new_touched_hinges_over_30_count": sector["new_over30_count_touched"],
            "slope_violation_count_global": sector["slope_violation_count_global"],
            "affected_sectors": sector["sectors"],
            "local_incident_geometry_B": ev.local_mesh_angles(hb, FOCUS, radius=2),
            "local_incident_geometry_H": ev.local_mesh_angles(hh, FOCUS, radius=2)},
        "p99": p99, "corridor_civil": corridor_civil,
        "input_hashes_start": readset_start, "input_hashes_end": readset_end,
        "model_hashes_read": coverage.get("compiled", {}).get("model_hashes", {}),
        "local_checks_elapsed_seconds_excluding_hash_and_index_io": local_elapsed,
        "index_reverified_after_local_checks": index_reverified_end,
        "source_limit": "Offline geometry/compiled ODOL only; no DayZ runtime, render, fake-wave envelope, or visual acceptance.",
    }


def _fixture_energy(ev):
    b = np.zeros((17, 17), dtype=np.float32)
    b[8, 8] = 4.0
    h = b.copy(); h[8, 8] = np.float32(3.0)
    report = local_energy(ev, b, h, origin=(832, 362))
    assert report["gate_strict_total_cost_decrease"]
    assert report["counts_by_family"] == {"Dxx": 3, "Dzz": 3, "Dxz": 4}
    return report


def _contact_gate_fixtures():
    assert contact_margin_ok("physical", 0.0)
    assert contact_margin_ok("physical", 1e-5)
    assert not contact_margin_ok("physical", -1e-6)
    assert contact_margin_ok("visible", 2.0001e-5)
    assert not contact_margin_ok("visible", 2e-5)
    assert not contact_margin_ok("visible", 1e-5)
    physical_bound = 2.61110520362854
    visible_bound = 2.6236052266322076
    target_descent = 3.73610520362854 - float(TARGET)
    assert target_descent < physical_bound and target_descent < visible_bound
    assert not contact_descent_allowed(physical_bound, physical_bound)
    assert not contact_descent_allowed(visible_bound, visible_bound)
    assert local_budget_ok(120.0) and not local_budget_ok(120.000001)
    from shapely.geometry import LineString, Point, Polygon
    assert len(contact_geometry_points(Point(1.0, 2.0))) == 1
    assert len(contact_geometry_points(LineString([(0,0),(1,1)]))) == 2
    assert len(contact_geometry_points(Polygon([(0,0),(1,0),(1,1),(0,0)]))) >= 4
    return {"physical_zero_floor_positive_negative": True,
        "visible_strict_2e-5_positive_negative": True,
        "strict_descent_bound_equal_is_rejected": True,
        "authorized_target_descent_below_both_bound_constants": target_descent,
        "120s_boundary_and_overrun": True,
        "point_line_polygon_contacts": True}


def self_test() -> dict:
    ev, ev91, ev87, cv, shape = load_stack()
    real_readset = readset(include_candidate=False)
    energy = _fixture_energy(ev)
    contact_fixtures = _contact_gate_fixtures()
    before = np.zeros((17, 17), dtype=np.float32); before[8, 8] = 4.0
    after = before.copy(); after[8, 8] = 3.0
    good_shape = shape.evaluate_shape(before, after, (1,16,1,16), (8,8))
    bad = before.copy(); bad[8,8] = np.float32(3.1)
    bad_shape = shape.evaluate_shape(before, bad, (1,16,1,16), (8,8))
    assert all(good_shape["gates"].values())
    assert not bad_shape["gates"]["focus_positive_prominence_reduced_25pct_both_axes"]

    # Exercise both directions of the actual P/F/SEA sign/crossing predicate.
    h0 = np.full((2,2), 3.0, dtype=np.float32); h0[0,0] = 0.5
    hgood = h0.copy(); hgood[0,1] = 2.5
    p = np.full((1,1), 1.0, dtype=np.float64)
    f = np.full((1,1,4), 1.0, dtype=np.float64)
    topo_good = ev.topology_check(ev, h0, hgood, p, f, {(0,0)})
    hbad = h0.copy(); hbad[0,1] = 0.5
    topo_bad = ev.topology_check(ev, h0, hbad, p, f, {(0,0)})
    assert topo_good["signs_preserved"] and topo_good["crossings_valid_and_within_1m"]
    assert not topo_bad["signs_preserved"]

    # Candidate-array validator is exercised on a tiny in-memory delta.
    base = {"heights": before, "meta": np.asarray([1,2], dtype=np.int16)}
    candidate = {"heights": after, "meta": base["meta"].copy()}
    assert np.array_equal(validate_one_point_arrays(base, candidate, (8,8)), [[8,8]])
    candidate["meta"][0] = 3
    try:
        validate_one_point_arrays(base, candidate, (8,8))
    except AssertionError as exc:
        assert "non-height array" in str(exc)
    else:
        raise AssertionError("metadata mutation negative was not rejected")
    assert not semantic_protections_clear({"other_fixed":False,"engineering_halo":False,
        "large_lake_banks":False,"reserve":True,"platform":False,"class_nonzero":False,
        "actually_wet":False})
    # Real-input preflight only: validates the focal semantic masks, physical
    # interval, corridor and civil overlap without loading the authored H.
    bundle = load_bundle()
    base_h = bundle["B"]["heights"]
    real_domain = validate_domain_and_bounds(ev, bundle, base_h)
    real_corridor = local_corridor_and_civil(ev91, ev, ev87, bundle, base_h)
    assert all(real_domain["gates"].values()) and all(real_corridor["gates"].values())
    return {"status": "PASS_FOCUS_CONSUMER_FIXTURES", "fixtures": {
        "affected_stencil_families_and_total_cost": energy,
        "zero_area_contact_and_budget_fixtures": contact_fixtures,
        "shape_positive": good_shape["gates"], "shape_negative_25pct": bad_shape["gates"],
        "water_crossing_positive": {k: topo_good[k] for k in ("signs_preserved", "crossings_valid_and_within_1m")},
        "water_crossing_negative_sign_inversion": {k: topo_bad[k] for k in ("signs_preserved", "crossings_valid_and_within_1m")},
        "metadata_mutation_negative_detected": True,
        "real_source_preflight_without_candidate": {
            "readset_inputs": len(real_readset),
            "masks_at_focus": real_domain["masks_at_focus"],
            "bounds_m": real_domain["bounds_m"],
            "crossing_records": real_domain["crossing_records"],
            "p9_unknown_cells_incident_to_focus": real_corridor["p9_unknown_cells_incident_to_focus"],
            "civil_cell_hits": real_corridor["civil_cell_hits"],
            "corridor_cell_intersections": real_corridor["corridor_cell_intersections"],
            "high_bed_floor_scope_at_focus": real_corridor["high_bed_floor_scope_at_focus"],
            "actual_wet_is_diagnostic_only": real_domain["masks_at_focus"]["actually_wet"],
        },
    }, "fixture_source_hashes": {"consumer": sha(Path(__file__).resolve()),
        "EV88": sha(EV88_PATH), "EV91": sha(EV91_PATH), "EV87": sha(EV87_PATH),
        "coverage": sha(CV_PATH), "shape": sha(SHAPE_PATH)},
       "limitations": ["Does not load or evaluate the real candidate.",
                        "Compiled ODOL, full p99, corridor, P9, and readset gates are wired but not executed here."]}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run-candidate", action="store_true",
                        help="full one-time consumer; run only after independent root review")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    if args.self_test:
        print(json.dumps(json_safe(self_test()), indent=2, allow_nan=False))
        return 0
    if not args.run_candidate:
        parser.error("default is inert; use --self-test or explicitly --run-candidate")
    if args.report is None:
        parser.error("--report is mandatory with --run-candidate")
    try:
        report = run_candidate()
    except Exception as exc:
        report = {"status": "ERROR_FOCAL_DELTA_OFFLINE",
                  "error_type": type(exc).__name__, "error": str(exc),
                  "consumer_source_sha256": sha(Path(__file__).resolve())}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as f:
        json.dump(json_safe(report), f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps(json_safe({"status": report["status"], "gates": report.get("gates", {}),
                                "candidate_sha256": report.get("candidate_sha256")}), indent=2, allow_nan=False))
    return 0 if report["status"] == "PASS_FOCAL_DELTA_OFFLINE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
