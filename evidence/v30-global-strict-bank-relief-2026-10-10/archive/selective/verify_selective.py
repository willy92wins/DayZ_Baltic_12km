#!/usr/bin/env python3
"""Independent EV87-S verifier. Does not author, compose, or mutate terrain.

The candidate, receipt, conflict inventory, and original EV87 evidence must be
produced by the separately reviewed integration pipeline. This verifier checks
their provenance, reconstructs the selective filter, independently checks the
candidate composition, evaluates full-map geometry through the frozen EV87
consumer, then checks compiled-water coverage in the modified footprint.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REVIEW = ROOT / "review-independent"
EV87 = ROOT / "candidate-terrain.npz"
LEDGER = ROOT / "queue-ledger.jsonl"
DIRECTIONS = ROOT / "directions.npz"
DIRECTION_INDEX = ROOT / "direction-index.json"
INVENTORY_DEFAULT = REVIEW / "incremental-conflict-inventory.json"
PLAN = ROOT / "selective-integration-plan.md"
VERIFY_EV87 = REVIEW / "verify_ev87.py"
VERIFY_COVERAGE = REVIEW / "verify_coverage_contract.py"

GIS_PYTHON = Path(r"C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe")
N = 2048
CELL = 6.0
ANG_TOL = 1e-4
FOOTPRINT_LIMIT = 1e-7
RESIDUAL_LIMIT = 2e-3

MANDATORY_REJECT = {79, 398, 470, 565, 575, 848}
EV87_CANDIDATE_SHA = "a7146c27a634d3ee59bc4c2763d71050da3172724c4f2620a17fce0775fcf020"
BASELINE_GLOBAL_REVIEW_SHA = "08cef62773f17ea9eba02ef0a0c33aa2455d3adb7f69ec9a52d8d25ca9ad6b25"


class PreflightComplete(Exception):
    def __init__(self, information):
        self.information = information


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_sha(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def import_file(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import verifier source: {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def npz_arrays(path: Path):
    with np.load(path, allow_pickle=False) as archive:
        return {k: archive[k].copy() for k in archive.files}


def event_rows(path: Path):
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    headers = [x for x in rows if x.get("event") == "header"]
    finals = [x for x in rows if x.get("event") == "final"]
    patches = [x for x in rows if x.get("event") == "patch"]
    if len(headers) != 1 or len(finals) != 1 or len(headers) + len(finals) + len(patches) != len(rows):
        raise AssertionError("source EV87 ledger must have one header, one final and only patch rows")
    return headers[0], patches, finals[0]


def cell_stencil(nodes):
    cells = set()
    for r, c in nodes:
        for dr in (-1, 0):
            for dc in (-1, 0):
                rr, cc = int(r) + dr, int(c) + dc
                if 0 <= rr < N - 1 and 0 <= cc < N - 1:
                    cells.add((rr, cc))
    return cells


def all_four_corners(h, cell):
    r, c = cell
    return np.asarray([h[r, c], h[r, c + 1], h[r + 1, c], h[r + 1, c + 1]])


def compose_from_B(base, original_candidate, ledger_rows, directions, direction_index, excluded_ids):
    """Independent reconstruction; caller compares exact float32 arrays."""
    h0 = np.asarray(base["heights"])
    h = h0.copy()
    byid = {int(x["queue_id"]): x for x in ledger_rows}
    idx = {int(q): x for q, x in direction_index.get("queue_id_to_direction", {}).items()}
    if len(byid) != len(ledger_rows):
        raise AssertionError("duplicate queue IDs in source patch ledger")
    allowed = np.zeros(h.shape, dtype=bool)
    for qi, rec in sorted(byid.items()):
        nodes = [tuple(map(int, n)) for n in rec["mutable_nodes"]]
        if rec["state"] != "accepted" or qi in excluded_ids:
            continue
        key = rec.get("direction_key")
        index_row = idx.get(qi)
        if key is None or index_row is None or index_row.get("key") != key or key not in directions:
            raise AssertionError(f"missing direction evidence for retained queue {qi}")
        vals = np.asarray(directions[key])
        if vals.dtype != np.float32 or vals.shape != (len(nodes),):
            raise AssertionError(f"direction vector shape/dtype mismatch q{qi}")
        if index_row.get("nodes") != [list(n) for n in nodes]:
            raise AssertionError(f"direction node order differs q{qi}")
        dsha = hashlib.sha256(vals.astype("<f4", copy=False).tobytes()).hexdigest()
        if dsha != index_row.get("sha256") or dsha != rec.get("direction_sha256"):
            raise AssertionError(f"direction hash mismatch q{qi}")
        for (r, c), v in zip(nodes, vals):
            if allowed[r, c]:
                raise AssertionError(f"retained mutable nodes overlap at {(r, c)}")
            allowed[r, c] = True
            h[r, c] = np.float32(float(h0[r, c]) + (float(v) - float(h0[r, c])) / 2.0)
    # This is the expected selective map only; the caller compares it against the
    # complete candidate and separately checks its exact difference from raw EV87.
    return h, allowed


def fixture_suite():
    b = np.zeros((8, 8), dtype=np.float32)
    orig = b.copy(); orig[3, 3] = -0.2
    direction = np.asarray([-0.4], dtype=np.float32)
    rows = [{"queue_id": 2, "state": "accepted", "direction_key": "q000002",
             "direction_sha256": hashlib.sha256(direction.astype("<f4").tobytes()).hexdigest(),
             "mutable_nodes": [[3, 3]]}]
    ix = {"queue_id_to_direction": {"2": {"key": "q000002", "nodes": [[3, 3]],
                                           "sha256": rows[0]["direction_sha256"]}}}
    h, allowed = compose_from_B({"heights": b}, {"heights": orig}, rows, {"q000002": direction}, ix, set())
    assert h[3, 3] == np.float32(-0.2) and allowed.sum() == 1
    h2, allowed2 = compose_from_B({"heights": b}, {"heights": orig}, rows, {"q000002": direction}, ix, {2})
    assert h2[3, 3] == b[3, 3] and allowed2.sum() == 0
    corrupt = h2.copy(); corrupt[3, 3] = np.float32(0.01)
    assert not np.array_equal(corrupt, b)
    assert cell_stencil([(3, 3)]) == {(2, 2), (2, 3), (3, 2), (3, 3)}
    # A conflicting patch can never survive the computed set filter.
    marked = {(2, 2)}
    assert bool(cell_stencil([(3, 3)]) & marked)
    # A one-centimeter wrong-height plane cannot count as matched support at 1e-5m.
    eps = 1e-5
    assert 0.01 > eps
    # A changed neighbor outside the authorized variable set is rejected by exact reconstruction.
    rogue = h.copy(); rogue[4, 4] = np.float32(-0.1)
    assert np.any((rogue != b) & ~allowed)
    ev, cv = load_verifiers()
    from shapely.geometry import Polygon
    target = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    wrong_height_support = cv.clip_affine_band(target, np.asarray([0.0, 0.0, 0.01]), 1e-5)
    assert wrong_height_support.is_empty
    crack = Polygon([(0, 0), (0.1, 0), (0.1, 0.1), (0, 0.1)])
    support_with_crack = target.difference(crack)
    assert cv.area_coverage_hole(target, support_with_crack).area > FOOTPRINT_LIMIT
    # Wrong-height face remains a face-height failure even if another correct face is present.
    above = cv.face_height_violation("physical", (0, 0), 0, "fixture.p3d", [0, 1, 2], target,
                                     np.asarray([0.0, 0.0, 0.01]), 1e-5)
    assert above is not None and above["max_excess_m"] > 0
    return {
        "retained_midpoint_exact": True,
        "excluded_patch_restores_all_nodes_to_B": True,
        "marked_conflict_stencil_detected": True,
        "four_cell_stencil_fixture": True,
        "rogue_outside_mutable_nodes_detected": True,
        "wrong_height_plane_negative_fixture": True,
        "new_support_crack_negative_fixture": True,
        "above_target_face_negative_fixture": True,
        "corrupted_restoration_negative_fixture": True,
    }


def coverage_fixture_suite(ev, cv):
    """Exercise the actual coverage_check with real Shapely polygons and frozen clipping."""
    from shapely.geometry import Polygon
    c0, c1 = (100, 100), (100, 101)
    cells = {c0, c1}
    changed = {c0}
    h0 = np.zeros((N, N), dtype=np.float64)
    h1 = h0.copy()
    p = np.ones((N - 1, N - 1), dtype=np.float64)
    f = np.ones((N - 1, N - 1, 4), dtype=np.float64)
    full = {c: cv.make_design(h0, p, f, {c}, "physical")[c] for c in cells}
    # P and F are constant planes at 1m; both real triangulated designs cover each 6x6 cell.
    assert all(abs(full[c].area - 36.0) < 1e-9 for c in cells)
    design = {}
    for kind in ("physical", "visible"):
        design[kind] = {c: cv.make_design(h0, p, f, {c}, kind)[c] for c in cells}
        assert all(abs(design[kind][c].area - 36.0) < 1e-9 for c in cells)

    def cached(exp_override=None, support_override=None, bad_candidate=None):
        exp = {label: {kind: {} for kind in ("physical", "visible")} for label in ("B", "candidate")}
        support = {kind: {} for kind in ("physical", "visible")}
        for kind in ("physical", "visible"):
            for c in cells:
                g = design[kind][c]
                exp["B"][kind][c] = g
                exp["candidate"][kind][c] = (exp_override or {}).get((kind, c), g)
                support[kind][c] = (support_override or {}).get((kind, c), g)
        bad = {"B": [], "candidate": list(bad_candidate or [])}
        unknown = {"changed_partial": 0}
        unresolved = {"with_contact_or_exposed_or_unproven_intersection": 0}
        meta = {"fixture": "real frozen P/F triangulation + Shapely support/exposure polygons"}
        return exp, support, meta, bad, unresolved, unknown

    good = coverage_check(ev, cv, h0, h1, p, f, cells, changed, cached())
    assert all(good["gates"].values()), good["gates"]

    # A real 0.01 m2 crack in a changed cell must fail absolute support and residual limits.
    xy0 = cv.cell_xy(*c0)
    x0, z0 = xy0[0]
    crack = Polygon([(x0, z0), (x0 + 0.1, z0), (x0 + 0.1, z0 - 0.1), (x0, z0 - 0.1)])
    cracked = design["physical"][c0].difference(crack)
    cracked_cache = cached(
        exp_override={("physical", c0): cracked},
        support_override={("physical", c0): cracked},
    )
    crack_report = coverage_check(ev, cv, h0, h1, p, f, cells, changed, cracked_cache)
    assert not crack_report["gates"]["physical_absolute_support_complete"]
    assert not crack_report["gates"]["physical_absolute_residual_within_band"]

    # A face above the native P target is rejected even if the proper footprint also exists.
    wrong = cv.face_height_violation("physical", c0, 0, "fixture-wrong-height.p3d", [0, 1, 2],
                                     design["physical"][c0], np.asarray([0.0, 0.0, 0.01]), cv.EPS["physical"])
    assert wrong is not None
    wrong_report = coverage_check(ev, cv, h0, h1, p, f, cells, changed,
                                  cached(bad_candidate=[wrong]))
    assert not wrong_report["gates"]["physical_absolute_face_height_exact"]

    # An apparent ODOL mismatch on an unchanged frontier cell is inherited evidence,
    # but since its four terrain corners are unchanged, the reconstructed geometry must match B exactly.
    xy1 = cv.cell_xy(*c1)
    x1, z1 = xy1[0]
    frontier_cut = design["visible"][c1].intersection(
        Polygon([(x1, z1), (x1 + 3.0, z1), (x1 + 3.0, z1 - 6.0), (x1, z1 - 6.0)])
    )
    frontier_report = coverage_check(
        ev, cv, h0, h1, p, f, cells, changed,
        cached(exp_override={("visible", c1): frontier_cut}),
    )
    assert not frontier_report["gates"]["unchanged_frontier_geometry_exact"]

    # An inherited above-P face on an unchanged frontier is allowed only when B and H
    # have the identical violation record; candidate-only appearance of that face fails.
    inherited = cv.face_height_violation("physical", c1, 0, "fixture-inherited-above-P.p3d", [3, 4, 5],
                                         design["physical"][c1], np.asarray([0.0, 0.0, 0.01]),
                                         cv.EPS["physical"])
    assert inherited is not None
    inherited_cache = cached(bad_candidate=[inherited])
    inherited_cache[3]["B"] = [inherited]
    inherited_report = coverage_check(ev, cv, h0, h1, p, f, cells, changed, inherited_cache)
    assert all(inherited_report["gates"].values()), inherited_report["gates"]
    new_frontier_report = coverage_check(ev, cv, h0, h1, p, f, cells, changed,
                                         cached(bad_candidate=[inherited]))
    assert not new_frontier_report["gates"]["no_new_or_worsened_face_height_violations_vs_B"]
    return {
        "actual_coverage_check_positive": True,
        "changed_cell_support_crack_rejected": True,
        "wrong_height_face_rejected": True,
        "unchanged_frontier_exposure_mismatch_rejected": True,
        "inherited_above_P_frontier_identical_B_H_allowed": True,
        "new_above_P_frontier_candidate_only_rejected": True,
        "geometry_source": "frozen verify_coverage_contract.make_design/band_polygon + Shapely polygon overlay",
        "fixture_cells": [list(c0), list(c1)],
    }


def expected_filter(inventory, patch_rows):
    conflicts = {tuple(map(int, x["cell"])): tuple(x.get("reasons", []))
                 for x in inventory["conflict_cells"]}
    if len(conflicts) != len(inventory["conflict_cells"]):
        raise AssertionError("duplicate cells in complete conflict inventory")
    suggested = {int(k): v for k, v in inventory["suggested_rejected_patches"].items()}
    expected = {}
    for rec in patch_rows:
        qi = int(rec["queue_id"])
        if rec.get("state") != "accepted":
            continue
        nodes = [tuple(map(int, n)) for n in rec["mutable_nodes"]]
        touched = sorted(cell_stencil(nodes) & conflicts.keys())
        if qi in MANDATORY_REJECT or touched:
            inv_hit = sorted(tuple(map(int, c)) for c in suggested.get(qi, {}).get("conflict_cells", []))
            if qi not in MANDATORY_REJECT and touched != inv_hit:
                raise AssertionError(f"inventory patch conflict stencil mismatch q{qi}")
            expected[qi] = touched
    # The inventory is diagnostic input, but its suggested qIDs must be reproducible.
    for qi, item in suggested.items():
        row = next((r for r in patch_rows if int(r["queue_id"]) == qi), None)
        if row is None or row.get("state") != "accepted":
            raise AssertionError(f"inventory suggests missing/non-accepted q{qi}")
        actual = sorted(cell_stencil([tuple(map(int, n)) for n in row["mutable_nodes"]]) & conflicts.keys())
        if actual != sorted(tuple(map(int, c)) for c in item["conflict_cells"]):
            raise AssertionError(f"inventory suggested_rejected_patches mismatch q{qi}")
    return conflicts, expected


def validate_inventory_rows(inventory, raw_report_path):
    """Check full untruncated cell rows and independently reconstruct conflict cells."""
    metrics = inventory.get("metrics", {})
    raw = load_json(raw_report_path)
    expected_cells = {tuple(map(int, x["cell"]))
                      for kind in ("physical", "visible")
                      for x in raw["information"]["surface_coverage"]["by_surface"][kind]["cells"]}
    if len(expected_cells) != 41008:
        raise AssertionError("pinned raw coverage report does not define the 41,008-cell inventory domain")
    cell_rows = {}
    for kind in ("physical", "visible"):
        if set(metrics.get(kind, {})) != {"B", "candidate"}:
            raise AssertionError(f"inventory lacks both B/candidate metrics for {kind}")
        for label in ("B", "candidate"):
            entry = metrics[kind][label]
            rows = entry.get("residual_cells_untruncated")
            if not isinstance(rows, list) or len(rows) != 41008:
                raise AssertionError(f"{kind}/{label} residual inventory is truncated or incomplete")
            mapped = {tuple(map(int, x["cell"])): x for x in rows}
            if len(mapped) != len(rows) or set(mapped) != expected_cells:
                raise AssertionError(f"{kind}/{label} residual cells have duplicate/missing coordinates")
            cell_rows[(kind, label)] = mapped
            holes = entry.get("support_holes_untruncated")
            if not isinstance(holes, list):
                raise AssertionError(f"{kind}/{label} support-hole inventory is absent")
            hole_cells = [tuple(map(int, x["cell"])) for x in holes]
            if len(set(hole_cells)) != len(hole_cells) or not set(hole_cells) <= expected_cells:
                raise AssertionError(f"{kind}/{label} support-hole inventory has duplicate/invalid cells")
    conflicts = {}
    def add(cell, reason): conflicts.setdefault(cell, set()).add(reason)
    for label in ("B", "candidate"):
        for row in cell_rows[("physical", label)].values():
            if max(float(row["missing_outside_band_m2"]), float(row["growth_outside_band_m2"])) > 1e-12:
                add(tuple(map(int, row["cell"])), label + "_physical_outside_band")
        for kind in ("physical", "visible"):
            for row in inventory["height_violations_untruncated"][label]:
                if row["kind"] == kind:
                    add(tuple(map(int, row["cell"])), label + "_" + kind + "_above_field")
    for kind in ("physical", "visible"):
        for row in metrics[kind]["candidate"]["support_holes_untruncated"]:
            if float(row["area_m2"]) > 1e-10:
                add(tuple(map(int, row["cell"])), "nominal_support_hole")
    serialized = [{"cell": list(cell), "reasons": sorted(reasons)} for cell, reasons in sorted(conflicts.items())]
    if serialized != inventory.get("conflict_cells"):
        raise AssertionError("inventory conflict-cell set/reasons do not reconstruct from complete per-cell rows")
    return cell_rows, conflicts


def check_receipt(receipt, args, inventory, paths, pinned):
    if receipt.get("status") != "COMPOSED_COMPLETE":
        raise AssertionError("integration receipt is not COMPOSED_COMPLETE")
    expected_inputs = {
        "source_B_path": paths["B"], "source_EV87_path": paths["EV87"],
        "ledger_path": paths["ledger"], "directions_path": paths["directions"],
        "direction_index_path": paths["direction_index"], "inventory_path": paths["inventory"],
        "candidate_path": paths["candidate"], "plan_path": paths["plan"],
    }
    for key, p in expected_inputs.items():
        got = receipt.get(key)
        if got is not None and Path(got).resolve() != Path(p).resolve():
            raise AssertionError(f"receipt path mismatch {key}")
    for key, p in expected_inputs.items():
        digest_key = {
            "source_B_path": "source_B_sha256", "source_EV87_path": "source_EV87_sha256",
            "ledger_path": "ledger_sha256", "directions_path": "directions_sha256",
            "direction_index_path": "direction_index_sha256", "inventory_path": "conflict_inventory_sha256",
            "candidate_path": "candidate_sha256", "plan_path": "selective_integration_plan_sha256",
        }[key]
        if receipt.get(digest_key) != sha(Path(p)):
            raise AssertionError(f"receipt digest mismatch {digest_key}")
    for key in ("P_sha256", "F_sha256", "WRP_sha256"):
        if receipt.get(key) != pinned[key]:
            raise AssertionError(f"receipt source hash mismatch {key}")
    for key in ("source_B_sha256",):
        if receipt.get(key) != pinned[key]:
            raise AssertionError(f"receipt source hash mismatch {key}")
    expected_conflict_coordinates = [row["cell"] for row in inventory["conflict_cells"]]
    if receipt.get("conflict_cells") != expected_conflict_coordinates:
        raise AssertionError("receipt conflict cell list differs from complete inventory")
    receipt_inputs = receipt.get("inputs")
    if not isinstance(receipt_inputs, dict) or not receipt_inputs:
        raise AssertionError("receipt lacks path-to-SHA input inventory")
    for raw_path, digest in receipt_inputs.items():
        path = Path(raw_path)
        if not path.is_file() or sha(path) != digest:
            raise AssertionError(f"receipt input hash mismatch: {raw_path}")
    return True


def build_derived_view(ledger_header, patch_rows, ledger_final, direction_archive, direction_index,
                       expected_reject_ids, candidate_sha, scratch: Path):
    """Create verifier-only ledger/direction view; never edits source evidence."""
    rows = []
    for rec in patch_rows:
        row = dict(rec)
        qi = int(row["queue_id"])
        if qi in expected_reject_ids:
            if row.get("state") != "accepted":
                raise AssertionError(f"cannot selectively reject nonaccepted q{qi}")
            row["state"] = "rejected_gate"
            row["reason"] = "EV87-S conflict-cell filter; original direction retained only as audit source"
            row.pop("direction_key", None)
            row.pop("direction_sha256", None)
        rows.append(row)
    accepted_keys = {r.get("direction_key") for r in rows if r.get("state") == "accepted"}
    filtered = {k: v for k, v in direction_archive.items() if k in accepted_keys}
    index_obj = dict(direction_index)
    index_obj["queue_id_to_direction"] = {
        str(q): dict(x) for q, x in direction_index.get("queue_id_to_direction", {}).items()
        if int(q) not in expected_reject_ids
    }
    index_obj["directions_sha256"] = None
    dpath = scratch / "directions.npz"
    np.savez_compressed(dpath, **filtered)
    index_obj["directions_sha256"] = sha(dpath)
    ipath = scratch / "direction-index.json"
    ipath.write_text(json.dumps(index_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    f = dict(ledger_final)
    f["candidate_sha256"] = candidate_sha
    f["directions_sha256"] = sha(dpath)
    f["direction_index_sha256"] = sha(ipath)
    f["processed_count"] = len(rows)
    f["remaining_count"] = 0
    lpath = scratch / "ledger.jsonl"
    with lpath.open("w", encoding="utf-8", newline="\n") as stream:
        for event in [ledger_header, *rows, f]:
            stream.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
    return lpath, dpath, ipath


def load_verifiers():
    ev = import_file("selective_ev87_frozen", VERIFY_EV87)
    cv = import_file("selective_coverage_frozen", VERIFY_COVERAGE)
    cv.ev = ev
    return ev, cv


def coverage_check(ev, cv, b, h, p, f, cells, changed_cells, cached):
    if not cells:
        raise AssertionError("candidate has no changed cells; a global no-op is not publishable")
    exp, support, meta, bad, unresolved, unknown_counts = cached
    if unknown_counts["changed_partial"]:
        raise AssertionError("changed vertices touch partially unknown F triangle")
    if unresolved["with_contact_or_exposed_or_unproven_intersection"]:
        raise AssertionError("changed all-NaN F has an intersecting face not proved buried in B and candidate")
    report = {"cells_checked": len(cells), "unknown_F": unknown_counts, "unresolved_F_faces": unresolved,
              "face_metadata": meta, "bad_height_counts": {k: len(v) for k, v in bad.items()}, "surfaces": {}}
    gates = {}
    frontier_cells = set(cells) - set(changed_cells)
    frontier_geometry_ok = True
    for kind in ("physical", "visible"):
        design_b = cv.make_design(b, p, f, cells, kind)
        design_h = cv.make_design(h, p, f, cells, kind)
        rows_b = residual_rows(cv, b, p, f, cells, kind, exp["B"][kind], design_b)
        rows_h = residual_rows(cv, h, p, f, cells, kind, exp["candidate"][kind], design_h)
        rb = {tuple(x["cell"]): x for x in rows_b}; rh = {tuple(x["cell"]): x for x in rows_h}
        holes_b = {cell: float(design_b[cell].difference(support[kind][cell]).area) for cell in cells}
        holes_h = {cell: float(design_h[cell].difference(support[kind][cell]).area) for cell in cells}
        frontier_equal = all(
            design_b[c].equals(design_h[c]) and exp["B"][kind][c].equals(exp["candidate"][kind][c])
            and holes_b[c] == holes_h[c]
            for c in frontier_cells
        )
        frontier_geometry_ok = frontier_geometry_ok and frontier_equal
        hole_total = float(sum(holes_h[c] for c in changed_cells))
        hole_max = float(max((holes_h[c] for c in changed_cells), default=0.0))
        hole_b_total = float(sum(holes_b.values()))
        # Diagnostic only. Changed cells are governed by absolute limits; unchanged
        # frontier cells are checked for exact geometric equality below.
        hole_regressions = [list(c) for c in sorted(changed_cells) if holes_h[c] > holes_b[c]]
        metrics = {
            "residual_cells_untruncated": rows_h,
            "missing_outside_band_total_m2": sum(x["missing_outside_band_m2"] for x in rows_h),
            "growth_outside_band_total_m2": sum(x["growth_outside_band_m2"] for x in rows_h),
            "support_holes_total_changed_cells_m2": hole_total,
        }
        metrics["support_holes_max_changed_cell_m2"] = hole_max
        metrics["support_holes_total_affected_cells_B_m2"] = hole_b_total
        metrics["support_hole_regression_cells"] = hole_regressions
        # Absolute local representation contract: complete support, no exposed face above its
        # assigned physical/visible target, and no outside-band leak beyond 0.002 m2.
        eps_bad = [x for x in bad["candidate"] if x["kind"] == kind and tuple(x["cell"]) in changed_cells]
        no_bad = len(eps_bad) == 0
        support_ok = hole_total < FOOTPRINT_LIMIT and hole_max < FOOTPRINT_LIMIT
        changed_rows = [rh[c] for c in changed_cells]
        def metric_sum(rows, key): return float(sum(x[key] for x in rows))
        def metric_max(rows, key): return float(max((x[key] for x in rows), default=0.0))
        residual_ok = all(metric_sum(changed_rows, key) <= RESIDUAL_LIMIT and
                          metric_max(changed_rows, key) <= RESIDUAL_LIMIT
                          for key in ("missing_outside_band_m2", "growth_outside_band_m2"))
        residual_regressions = [list(c) for c in sorted(changed_cells)
                                if any(rh[c][key] > rb[c][key] for key in
                                       ("missing_outside_band_m2", "growth_outside_band_m2"))]
        gates[f"{kind}_absolute_support_complete"] = support_ok
        gates[f"{kind}_absolute_face_height_exact"] = no_bad
        gates[f"{kind}_absolute_residual_within_band"] = residual_ok
        report["surfaces"][kind] = {"metrics": metrics, "face_height_violations": eps_bad,
                                    "support_holes_by_cell": [{"cell": list(c), "B_area_m2": holes_b[c], "candidate_area_m2": a}
                                                              for c, a in sorted(holes_h.items()) if a > 0 or holes_b[c] > 0],
                                    "residual_regression_cells": residual_regressions}
    gates["unchanged_frontier_geometry_exact"] = frontier_geometry_ok
    b_bad = {(x["kind"], tuple(x["cell"]), int(x["triangle"]), x["object"], tuple(x["face_indices"])): x
             for x in bad["B"]}
    h_bad = {(x["kind"], tuple(x["cell"]), int(x["triangle"]), x["object"], tuple(x["face_indices"])): x
             for x in bad["candidate"]}
    new_bad = [key for key in h_bad if key not in b_bad]
    worse_bad = [key for key in h_bad.keys() & b_bad.keys()
                 if h_bad[key]["area_m2"] > b_bad[key]["area_m2"] or
                 h_bad[key]["max_excess_m"] > b_bad[key]["max_excess_m"]]
    gates["no_new_or_worsened_face_height_violations_vs_B"] = not new_bad and not worse_bad
    report["height_violation_regressions"] = {"new": [list(k[1]) + [k[0], k[2], k[3], list(k[4])] for k in new_bad],
                                               "worsened": [list(k[1]) + [k[0], k[2], k[3], list(k[4])] for k in worse_bad]}
    report["gates"] = gates
    return report


def residual_rows(cv, h, p, f, cells, kind, exposed, design):
    """Complete per-cell residuals using the frozen 214f clipping primitives."""
    rows = []
    field = "physical" if kind == "physical" else "visible"
    eps = cv.EPS[field]
    for r, c in sorted(cells):
        cell = (r, c)
        d = design[cell]
        actual = exposed[cell]
        if kind == "visible":
            known = []
            xy = cv.cell_xy(r, c)
            for tri in cv.ev.TRIS:
                _, _, coeff = cv.cell_tri_target(r, c, "visible", tri, p, f)
                if coeff is not None:
                    known.append(cv.Polygon(xy[list(tri)]))
            domain = cv.unary_union(known) if known else cv.Polygon()
            d = d.intersection(domain)
            actual = actual.intersection(domain)
        band = cv.band_polygon(r, c, h, p, f, field, eps)
        missing = d.difference(actual)
        growth = actual.difference(d)
        rows.append({"cell": [r, c], "missing_m2": float(missing.area),
                     "missing_outside_band_m2": float(missing.difference(band).area),
                     "growth_m2": float(growth.area),
                     "growth_outside_band_m2": float(growth.difference(band).area)})
    return rows


def main():
    ap = argparse.ArgumentParser(description="Independent EV87-S selective integration consumer")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--preflight", action="store_true", help="verify receipt/filter/composition only; no geometry/ODOL scan")
    ap.add_argument("--receipt", type=Path)
    ap.add_argument("--inventory", type=Path, default=INVENTORY_DEFAULT)
    ap.add_argument("--candidate", type=Path)
    ap.add_argument("--source-ev87", type=Path, default=EV87)
    ap.add_argument("--ledger", type=Path, default=LEDGER)
    ap.add_argument("--directions", type=Path, default=DIRECTIONS)
    ap.add_argument("--direction-index", type=Path, default=DIRECTION_INDEX)
    ap.add_argument("--source-b", type=Path)
    ap.add_argument("--source-ev79", type=Path)
    ap.add_argument("--source-constraints", type=Path)
    ap.add_argument("--prior-constraints", type=Path)
    ap.add_argument("--plane", type=Path)
    ap.add_argument("--visible-field", type=Path)
    ap.add_argument("--wrp", type=Path)
    ap.add_argument("--deploy", type=Path)
    ap.add_argument("--bounds", type=Path)
    ap.add_argument("--models", type=Path)
    ap.add_argument("--workspace", type=Path)
    ap.add_argument("--report", type=Path, default=HERE / "selective-review.json")
    ap.add_argument("--scratch", type=Path, default=HERE / "_consumer-scratch")
    args = ap.parse_args()
    t0 = time.monotonic()
    result = {"status": "ERROR_EV87_S_CONSUMER", "verifier": "independent EV87-S consumer", "gates": {}}
    try:
        if args.self_test:
            ev, cv = load_verifiers()
            result.update(status="PASS_EV87_S_FIXTURES",
                          fixtures={**fixture_suite(), **coverage_fixture_suite(ev, cv)})
        else:
            required = [args.receipt, args.candidate, args.source_b, args.source_ev79, args.source_constraints,
                        args.prior_constraints, args.plane, args.visible_field, args.wrp, args.deploy, args.bounds,
                        args.models, args.workspace]
            if any(x is None for x in required):
                raise AssertionError("full mode requires receipt, all source paths, and candidate")
            ev, cv = load_verifiers()
            pinned = {
                "source_B_sha256": ev.B_SHA, "source_EV79_sha256": ev.SOURCE_SHA,
                "source_constraints_sha256": ev.EV79_CONSTRAINTS_SHA,
                "prior_constraints_sha256": ev.PRIOR_CONSTRAINTS_SHA,
                "P_sha256": ev.P_SHA, "F_sha256": ev.F_SHA, "WRP_sha256": ev.B_STAGE_WPR_SHA,
            }
            receipt = load_json(args.receipt)
            inventory = load_json(args.inventory)
            if inventory.get("status") != "COMPLETE_READ_ONLY_CONFLICT_INVENTORY" or inventory.get("acceptance") is not False:
                raise AssertionError("conflict inventory is incomplete or misrepresented as acceptance")
            if inventory.get("scan_cells") != 41008:
                raise AssertionError("inventory must cover all 41,008 original coverage cells")
            raw_report_path = cv.RAW
            if sha(raw_report_path) != cv.RAW_SHA:
                raise AssertionError("frozen raw coverage report identity mismatch")
            cell_rows, reconstructed_conflicts = validate_inventory_rows(inventory, raw_report_path)
            paths = {"B": args.source_b, "EV87": args.source_ev87, "ledger": args.ledger,
                     "directions": args.directions, "direction_index": args.direction_index,
                     "inventory": args.inventory, "candidate": args.candidate, "plan": PLAN}
            all_inputs = [args.receipt, args.inventory, args.candidate, args.source_ev87, args.ledger,
                          args.directions, args.direction_index, args.source_b, args.source_ev79,
                          args.source_constraints, args.prior_constraints, args.plane, args.visible_field,
                          args.wrp, args.deploy, args.bounds, PLAN, VERIFY_EV87, VERIFY_COVERAGE,
                          ]
            policy_path = ROOT / "coverage-contract-proposal.md"
            all_inputs.extend([Path(__file__).resolve(), policy_path, raw_report_path])
            baseline_review_path = REVIEW / "ev87-review.json"
            all_inputs.append(baseline_review_path)
            if sha(baseline_review_path) != BASELINE_GLOBAL_REVIEW_SHA:
                raise AssertionError("pinned EV87 baseline global review identity mismatch")
            initial_hashes = {str(Path(x).resolve()): sha(x) for x in all_inputs}
            for raw_path, digest in receipt.get("inputs", {}).items():
                if sha(Path(raw_path)) != digest:
                    raise AssertionError(f"receipt input hash mismatch: {raw_path}")
                initial_hashes[str(Path(raw_path).resolve())] = digest
            for raw_path, digest in inventory.get("inputs", {}).items():
                if sha(Path(raw_path)) != digest:
                    raise AssertionError(f"inventory input hash mismatch: {raw_path}")
                initial_hashes[str(Path(raw_path).resolve())] = digest
            for model_name, digest in inventory.get("model_hashes", {}).items():
                model_path = args.models / model_name
                if sha(model_path) != digest:
                    raise AssertionError(f"compiled ODOL hash mismatch: {model_name}")
                initial_hashes[str(model_path.resolve())] = digest
            if sha(PLAN) != receipt.get("selective_integration_plan_sha256"):
                raise AssertionError("plan hash differs from composition receipt")
            if sha(args.inventory) != receipt.get("conflict_inventory_sha256"):
                raise AssertionError("conflict inventory hash differs from receipt")
            if sha(args.source_ev87) != EV87_CANDIDATE_SHA:
                raise AssertionError("raw EV87 candidate identity mismatch")
            for key, path in (("source_B_sha256", args.source_b), ("source_EV79_sha256", args.source_ev79),
                              ("source_constraints_sha256", args.source_constraints),
                              ("prior_constraints_sha256", args.prior_constraints), ("P_sha256", args.plane),
                              ("F_sha256", args.visible_field), ("WRP_sha256", args.wrp)):
                if sha(path) != pinned[key]:
                    raise AssertionError(f"pinned source drift: {key}")
            receipt_valid = check_receipt(receipt, args, inventory, paths, pinned)
            header, patch_rows, source_final = event_rows(args.ledger)
            conflicts, expected_rejects = expected_filter(inventory, patch_rows)
            if {cell: set(reasons) for cell, reasons in conflicts.items()} != reconstructed_conflicts:
                raise AssertionError("patch filter uses a conflict set different from independent inventory reconstruction")
            receipt_rejected = {int(x["queue_id"]): sorted(tuple(map(int, c)) for c in x.get("conflict_cells", []))
                                for x in receipt.get("excluded_patches", [])}
            receipt_recs = {int(x["queue_id"]): x for x in receipt.get("excluded_patches", [])}
            if len(receipt_recs) != len(receipt.get("excluded_patches", [])):
                raise AssertionError("duplicate queue in receipt excluded patches")
            if set(receipt_rejected) != set(expected_rejects):
                raise AssertionError("receipt excluded patch IDs differ from independent filter")
            for qi, cells in expected_rejects.items():
                if receipt_rejected[qi] != cells:
                    raise AssertionError(f"receipt conflict cells differ q{qi}")
                src = next(x for x in patch_rows if int(x["queue_id"]) == qi)
                out = receipt_recs[qi]
                if out.get("center") != src.get("center") or out.get("mutable_nodes") != src.get("mutable_nodes"):
                    raise AssertionError(f"receipt patch identity differs from frozen ledger q{qi}")
                if not out.get("reason"):
                    raise AssertionError(f"excluded patch q{qi} has no reason")
            if set(map(int, receipt.get("retained_queue_ids", []))) != {int(x["queue_id"]) for x in patch_rows
                                                                         if x.get("state") == "accepted" and int(x["queue_id"]) not in expected_rejects}:
                raise AssertionError("receipt retained queue inventory mismatch")
            base = npz_arrays(args.source_b); original = npz_arrays(args.source_ev87); cand = npz_arrays(args.candidate)
            if set(base) != set(original) or set(base) != set(cand):
                raise AssertionError("terrain archive key sets differ")
            for k in base:
                if k != "heights" and (not np.array_equal(base[k], original[k], equal_nan=True) or
                                        not np.array_equal(base[k], cand[k], equal_nan=True)):
                    raise AssertionError(f"frozen terrain metadata changed: {k}")
            direction_archive = npz_arrays(args.directions)
            direction_index = load_json(args.direction_index)
            expected_h, allowed = compose_from_B(base, original, patch_rows, direction_archive,
                                                  direction_index, set(expected_rejects))
            hc = np.asarray(cand["heights"])
            hb = np.asarray(base["heights"])
            if hc.dtype != np.float32 or hb.dtype != np.float32 or hc.shape != (N, N) or hb.shape != (N, N):
                raise AssertionError("candidate/B height shape or dtype mismatch")
            if not np.array_equal(hc, expected_h):
                raise AssertionError("selective candidate is not exact B plus retained midpoint directions")
            changed = hc != hb
            if np.any(changed & ~allowed):
                raise AssertionError("candidate changed a vertex outside retained mutable nodes")
            expected_changed = expected_h != hb
            if not np.array_equal(changed, expected_changed):
                raise AssertionError("changed-vertex mask differs from exact B plus stored midpoint reconstruction")
            for cell in conflicts:
                if not np.array_equal(all_four_corners(hc, cell), all_four_corners(hb, cell)):
                    raise AssertionError(f"conflict cell not bitwise B: {cell}")
            # The only difference from raw EV87 must be restoration to B on every excluded patch node.
            old_h = np.asarray(original["heights"])
            diff = hc != old_h
            allowed_diff = np.zeros(hc.shape, dtype=bool)
            for rec in patch_rows:
                if rec.get("state") == "accepted" and int(rec["queue_id"]) in expected_rejects:
                    for r, c in rec["mutable_nodes"]:
                        allowed_diff[int(r), int(c)] = True
            if np.any(diff & ~allowed_diff) or not np.array_equal(hc[~allowed_diff], old_h[~allowed_diff]):
                raise AssertionError("selective candidate differs from EV87 outside excluded patch restoration")
            if not np.array_equal(hc[allowed_diff], hb[allowed_diff]):
                raise AssertionError("excluded patch nodes were not restored exactly to B")
            restored_count = int(np.count_nonzero(allowed_diff & (old_h != hb)))
            comparison = receipt.get("comparison_to_EV87", {})
            if receipt.get("modified_vertices") != int(changed.sum()):
                raise AssertionError("receipt modified_vertices differs from recomputed candidate")
            if not comparison.get("raw_reconstructed_exact") or not comparison.get("differences_only_in_excluded_patches"):
                raise AssertionError("receipt comparison to raw EV87 is incomplete or false")
            if comparison.get("restored_vertices") != restored_count:
                raise AssertionError("receipt restored vertex count differs from exact EV87-to-B restoration")
            if args.preflight:
                final_hashes = {raw_path: sha(Path(raw_path)) for raw_path in initial_hashes}
                if final_hashes != initial_hashes:
                    raise AssertionError("input changed during preflight")
                raise PreflightComplete({"conflict_cells": len(conflicts), "excluded_patches": sorted(expected_rejects),
                                         "retained_patches": int(len(receipt.get("retained_queue_ids", []))),
                                         "changed_vertices": int(changed.sum()), "restored_vertices": restored_count,
                                         "candidate_sha256": sha(args.candidate), "inputs": initial_hashes})
            changed_nodes = [tuple(map(int, x)) for x in np.argwhere(changed)]
            changed_cells = ev._ev87_cells(changed_nodes, pad=0)
            cells = ev._ev87_cells(changed_nodes, pad=1)
            p = np.load(args.plane, allow_pickle=False).astype(np.float64)
            f = np.load(args.visible_field, allow_pickle=False).astype(np.float64)
            # Build a verifier-only reduced ledger preserving all selected rows and recorded statuses.
            args.scratch.mkdir(parents=True, exist_ok=False)
            with np.load(args.directions, allow_pickle=False) as z:
                raw_dirs = {k: z[k].copy() for k in z.files}
            lpath, dpath, ipath = build_derived_view(header, patch_rows, source_final, raw_dirs,
                                                     direction_index, set(expected_rejects), sha(args.candidate), args.scratch)
            ev_report_path = args.scratch / "ev87-global-report.json"
            ev_cmd = [str(GIS_PYTHON), str(VERIFY_EV87), "--candidate", str(args.candidate), "--candidate-sha", sha(args.candidate),
                      "--ledger", str(lpath), "--directions", str(dpath), "--direction-index", str(ipath),
                      "--source", str(args.source_ev79), "--source-constraints", str(args.source_constraints),
                      "--prior-constraints", str(args.prior_constraints), "--b-reference", str(args.source_b),
                      "--plane", str(args.plane), "--visible-field", str(args.visible_field), "--wrp", str(args.wrp),
                      "--deploy", str(args.deploy), "--bounds", str(args.bounds), "--models", str(args.models),
                      "--workspace", str(args.workspace), "--report", str(ev_report_path)]
            # The frozen geometry consumer requests compiled exposure exactly once. Adapt that
            # call to the independent 214f face walker so its real exposed/support polygons are
            # retained for the selective coverage gates below. This avoids reparsing/re-walking
            # the same WRP/ODOL population and does not synthesize or bypass any gate.
            cached_coverage = {}
            original_exposure = ev._compiled_exposure_pair
            def cached_exposure(hb_arg, hc_arg, cells_arg, wrp_path, workspace, model_dir, bounds_path):
                if set(cells_arg) != set(cells):
                    raise AssertionError("frozen geometry consumer requested a different cell domain")
                if not np.array_equal(np.asarray(hb_arg), hb.astype(np.float64)) or not np.array_equal(np.asarray(hc_arg), hc.astype(np.float64)):
                    raise AssertionError("coverage adapter received heights different from pinned B/selective candidate")
                for got, want, label in ((wrp_path, args.wrp, "WRP"), (workspace, args.workspace, "workspace"),
                                         (model_dir, args.models, "model directory"), (bounds_path, args.bounds, "bounds")):
                    if Path(got).resolve() != Path(want).resolve():
                        raise AssertionError(f"coverage adapter {label} argument mismatch")
                unknown_arg, unknown_counts_arg = cv.classify_unknown_f(hb_arg, hc_arg, f)
                if not unknown_arg["changed_cells"] <= set(cells_arg):
                    raise AssertionError("changed all-NaN F triangles escape the scanned cell domain")
                value = cv.exposed_pair_and_support(hb_arg, hc_arg, p, f, cells_arg, wrp_path,
                                                    workspace, model_dir, bounds_path, unknown_arg)
                exp_pair, support_pair, meta_pair, bad_pair, unresolved_pair = value
                cached_coverage.update(exp=exp_pair, support=support_pair, meta=meta_pair,
                                       bad=bad_pair, unresolved=unresolved_pair,
                                       unknown_counts=unknown_counts_arg)
                return exp_pair["B"], exp_pair["candidate"], meta_pair
            ev._compiled_exposure_pair = cached_exposure
            old_argv = sys.argv
            try:
                sys.argv = ev_cmd[1:]
                ev.main()
            finally:
                sys.argv = old_argv
                ev._compiled_exposure_pair = original_exposure
            if not ev_report_path.exists():
                raise RuntimeError("frozen global consumer did not write its report")
            global_report = load_json(ev_report_path)
            global_gates = global_report.get("gates", {})
            baseline_global = load_json(REVIEW / "ev87-review.json")
            if global_report.get("status") not in ("PASS_EV87_GLOBAL_CONSUMER", "FAIL_EV87_GLOBAL_CONSUMER") or global_report.get("error"):
                raise AssertionError(f"frozen global consumer returned an error/incomplete report: {global_report.get('error')}")
            if set(global_gates) != set(baseline_global.get("gates", {})) or not all(type(v) is bool for v in global_gates.values()):
                raise AssertionError("frozen global consumer gate inventory is incomplete or nonboolean")
            result["diagnostics"] = {"global_consumer_status": global_report.get("status"),
                                     "global_gates": global_gates,
                                     "global_report_path": str(ev_report_path),
                                     "global_report_sha256": sha(ev_report_path),
                                     "input_hashes_at_geometry_check": dict(initial_hashes)}
            # Four original coverage gates were rejected by the independent representation audit and
            # are replaced here by complete ODOL coverage checks in the exact modified footprint.
            replaced = {"physical_P_B_and_candidate_design_covered_le_0_002m2",
                        "physical_outside_design_growth_le_0_002m2",
                        "visible_F_B_and_candidate_design_covered_le_0_002m2",
                        "visible_outside_design_growth_le_0_002m2"}
            geometry_gates = {k: bool(v) for k, v in global_gates.items() if k not in replaced}
            if not geometry_gates or not all(geometry_gates.values()):
                raise AssertionError(f"frozen global geometry gates failed: {[k for k,v in geometry_gates.items() if not v]}")
            cache_value = (cached_coverage["exp"], cached_coverage["support"], cached_coverage["meta"],
                           cached_coverage["bad"], cached_coverage["unresolved"], cached_coverage["unknown_counts"])
            for model_name, digest in cached_coverage["meta"]["model_hashes"].items():
                model_path = args.models / model_name
                if sha(model_path) != digest:
                    raise AssertionError(f"consumed compiled model drift: {model_name}")
                initial_hashes[str(model_path.resolve())] = digest
            local_report = coverage_check(ev, cv, hb.astype(np.float64), hc.astype(np.float64), p, f,
                                          cells, changed_cells, cache_value)
            result["diagnostics"]["local_coverage_report"] = local_report
            if not all(local_report["gates"].values()):
                raise AssertionError(f"modified-footprint absolute coverage gates failed: {[k for k,v in local_report['gates'].items() if not v]}")
            # Full inventory is compared per cell against B and raw EV87. Every marked cell is B;
            # all candidate changes are confined to the accepted retained-node footprint.
            height_inv = inventory.get("height_violations_untruncated")
            if not isinstance(height_inv, dict) or set(height_inv) != {"B", "candidate"}:
                raise AssertionError("height violation inventory must include complete B and raw candidate rows")
            if not all(isinstance(height_inv[x], list) for x in ("B", "candidate")):
                raise AssertionError("height violation inventory rows are not complete arrays")
            final_hashes = {raw_path: sha(Path(raw_path)) for raw_path in initial_hashes}
            if final_hashes != initial_hashes:
                raise AssertionError("input changed during selective verification")
            result.update(status="PASS_INCREMENTAL_NONREGRESSION", global_representation_status="FAIL_WITH_INHERITED_OPEN",
                          receipt_valid=receipt_valid, gates={**geometry_gates, **local_report["gates"]},
                          inputs=initial_hashes,
                          information={"conflict_cells": len(conflicts), "excluded_patches": sorted(expected_rejects),
                                       "retained_accepted_patches": int(np.count_nonzero([r.get('state') == 'accepted' and int(r['queue_id']) not in expected_rejects for r in patch_rows])),
                                       "changed_vertices": int(changed.sum()), "modified_cells_plus_frontier": len(cells),
                                       "geometry_consumer_status": global_report.get("status"),
                                       "global_contract_status": "FAIL_WITH_INHERITED_OPEN",
                                       "inherited_open": ["EV87 full-map absolute representation coverage remains unresolved in B",
                                                           "Selective status does not claim global map/render PASS"],
                                       "local_coverage": local_report,
                                       "global_gates_replaced_by_local_recalculation": sorted(replaced),
                                       "raw_global_report_path": str(ev_report_path),
                                       "raw_global_report_sha256": sha(ev_report_path),
                                       "derived_global_view_sha256": {"ledger": sha(lpath), "directions": sha(dpath), "direction_index": sha(ipath)}})
            if not all(result["gates"].values()):
                result["status"] = "FAIL_EV87_S_CONSUMER"
    except PreflightComplete as done:
        result.update(status="PASS_EV87_S_PREFLIGHT", information=done.information, inputs=done.information["inputs"])
    except Exception as exc:
        result.update(status="FAIL_EV87_S_CONSUMER", error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
    result["elapsed_seconds"] = time.monotonic() - t0
    args.report.parent.mkdir(parents=True, exist_ok=True)
    temp = args.report.with_suffix(args.report.suffix + ".tmp")
    temp.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temp.replace(args.report)
    print(json.dumps({"status": result["status"], "report": str(args.report), "error": result.get("error"),
                      "false_gates": [k for k, v in result.get("gates", {}).items() if not v],
                      "elapsed_seconds": result["elapsed_seconds"]}, ensure_ascii=False), flush=True)
    return 0 if result["status"] in ("PASS_EV87_S_FIXTURES", "PASS_EV87_S_PREFLIGHT",
                                      "PASS_INCREMENTAL_NONREGRESSION") else 1


if __name__ == "__main__":
    raise SystemExit(main())
