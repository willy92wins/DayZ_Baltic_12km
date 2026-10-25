#!/usr/bin/env python
"""EV93 compound selector: local-gate whole deltas, then remove whole units by
deterministic footprint contribution until both global support-hole sums pass.

This module intentionally has no terrain authoring/solver path.  Its execution
entry point is gated on the finalized compound pool and emits a candidate only
after all local rows and the support selection are complete.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import sys
import time
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Callable, Mapping

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

SCHEMA = "ev93.compound-selection.v1"
PLAN = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/crest-extension/EXECUTION_PLAN_V2.md")
PLAN_SHA256 = "8a4afc1e26dc0d816ade9454ee4f4e31c185b03a56c8a9ef5005f468d0cff9b0"
LIMIT_M2 = 1e-7
LAYERS = ("physical", "visible")
G = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010")
ROOT = Path(r"E:/DayZ-Baltic-Build")
CONSUMER = G / "consumer-global/verify_layer.py"
COMPOUND_AUTHOR = G / "crest-extension/author_reused_directions.py"
COMPOUND_AUTHOR_SHA256 = "653900438d832d32f118ea5300850eeaf5e9a0cd4e3f49e7e3e1e64aaa862c2a"
POOL_DEFAULT = G / "crest-extension/quarantine-pool-v3/compound-pool.json"
BASE = Path(r"E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz")
BASE_SHA256 = "f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0"
PREPARED = G / "fairing-layer1/prepared.json"
PREPARED_SHA256 = "765c5a5a778132fce7f1c1d21a59c1220b62443b180238e13ee51a203b3483d4"
LEGACY_RECEIPT = G / "fairing-layer1/authoring.json"
LEGACY_RECEIPT_SHA256 = "97165c9a3fe6ec052d8458a636be2fc9d13c6b87b05ce4491ae5123d13ea3c92"
LEGACY_LEDGER = G / "fairing-layer1/ledger.jsonl"
LEGACY_LEDGER_SHA256 = "dc0a26cc38f55c1a8bb5709e36cfacd41859c3f901aabed15968a56c44832e85"
KNOWN_FAIL = G / "consumer-global/runs/attempt-04/ev93-review.json"
KNOWN_FAIL_SHA256 = "ed9a071d359dc446b5146a255c3ab9f15481c92e24c2169b6da47dd4ad27c0ec"
KNOWN_FAIL_GATES = {"physical_support_holes_lt_1e_7m2", "visible_support_holes_lt_1e_7m2"}
KNOWN_FAIL_CANDIDATE_SHA256 = "37e6d4bd195ee8576bc483a6c24e89cede536d916c2b041d8a6bdc98b13269f3"
POLICY = G / "crest-policy/crest_policy.py"
POLICY_SHA256 = "32ab6e0111886907315a0360322df0ff958f80bebcd6493254a2f0f144a3829e"
REUSE_INVENTORY = G / "crest-extension/reuse-source-inventory.json"
REUSE_INVENTORY_SHA256 = "8b8b9a6e525ee3bd8df59bef18784bafdc921e295ec9ebdb7043eefa4317b042"
EV92_DIR = ROOT / "v30-wide-bank-fairing-pilot-20261010/ev92-damped"
SHAPE = ROOT / "v30-wide-bank-fairing-pilot-20261010/next-method-consumer/shape_contract.py"
SHAPE_SHA256 = "8cd9d0fbea03c05e5ae53a31676d79ec2364be83c055213446f6c8599245d533"
INDEX_RUN = G / "ev93-face-index/runs/20261010T092417Z-63d4cec3"
SELECTED_LOCAL_CONSUMER = G / "crest-extension/verify_selected_composite.py"
SELECTED_LOCAL_CONSUMER_SHA256 = "8cd8f28b7914936bdf86f884b18bd14eb11aeca306f24327851dda340f16a543"
SELECTED_LOCAL_HELPER = G / "crest-extension/verify_composite.py"
SELECTED_LOCAL_HELPER_SHA256 = "88edd6b54d9c7cf05bff546d66c2ad0074ae939e903043790eeae5d42d8ece24"
OUTPUT_DEFAULT = G / "compound-selection/output"
NONZERO_TARGETS = 228
LEGACY_UNITS = 340


def sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_sha(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def atomic_json(path: Path, value) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)
    return hashlib.sha256(raw).hexdigest()


def changed_nodes(base: np.ndarray, composed: np.ndarray) -> set[tuple[int, int]]:
    if base.dtype != np.float32 or composed.dtype != np.float32 or base.shape != composed.shape:
        raise ValueError("base/composed must be matching float32 arrays")
    if not np.isfinite(base).all() or not np.isfinite(composed).all():
        raise ValueError("non-finite terrain values")
    return {tuple(map(int, rc)) for rc in np.argwhere(base != composed)}


def node_owner_map(units: Mapping[str, Mapping], base: np.ndarray):
    """Validate exclusive vertex ownership and construct H from B plus unit rows."""
    h = np.asarray(base, dtype=np.float32).copy()
    owner: dict[tuple[int, int], str] = {}
    declared_owner: dict[tuple[int, int], str] = {}
    unit_nodes: dict[str, set[tuple[int, int]]] = {}
    for unit_id in sorted(units):
        row = units[unit_id]
        nodes = np.asarray(row["variables_rc"], dtype=np.int32)
        values = np.asarray(row["final_float32"], dtype=np.float32)
        if nodes.ndim != 2 or nodes.shape[1] != 2 or values.shape != (len(nodes),):
            raise ValueError(f"malformed delta arrays for {unit_id}")
        node_set = {tuple(map(int, x)) for x in nodes.tolist()}
        if len(node_set) != len(nodes):
            raise ValueError(f"duplicate node in delta {unit_id}")
        if any(r < 0 or c < 0 or r >= base.shape[0] or c >= base.shape[1] for r, c in node_set):
            raise ValueError(f"out-of-grid mutable node in {unit_id}")
        bvals = np.asarray(row["B_values_float32"], dtype=np.float32)
        if bvals.shape != (len(nodes),) or not np.array_equal(bvals, base[tuple(nodes.T)]):
            raise ValueError(f"delta B values differ from pinned baseline for {unit_id}")
        for node, value in zip(nodes.tolist(), values.tolist()):
            key = tuple(map(int, node))
            if key in declared_owner:
                raise ValueError(f"mutable node has multiple owners: {key} / {declared_owner[key]} / {unit_id}")
            declared_owner[key] = unit_id
            h[key] = np.float32(value)
            if np.float32(value) != base[key]:
                owner[key] = unit_id
        unit_nodes[unit_id] = {node for node in node_set if node in owner}
    actual = changed_nodes(base, h)
    if actual != set(owner) or set(owner.values()) != set(units):
        # Units with no changed vertices are invalid as selectable deltas; the
        # compound contract requires nontrivial accepted/derived changes.
        raise ValueError("changed-vertex ownership differs from actual composition")
    return h, owner, unit_nodes


def incident_cells(nodes: set[tuple[int, int]], domain: set[tuple[int, int]]):
    out = set()
    for r, c in nodes:
        for cell in ((r - 1, c - 1), (r - 1, c), (r, c - 1), (r, c)):
            if cell in domain:
                out.add(cell)
    return out


def cell_owners(cell: tuple[int, int], owner: Mapping[tuple[int, int], str]):
    r, c = cell
    corners = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
    return tuple(sorted({owner[n] for n in corners if n in owner}))


def deterministic_order(contribution: Mapping[str, Mapping], unit_qid: Mapping[str, int]):
    """Descending unique-owner physical+visible contribution, then source qid/unit id."""
    if set(contribution) != set(unit_qid):
        raise ValueError("contribution and qid unit inventories differ")
    return sorted(contribution, key=lambda u: (
        -(float(contribution[u]["physical"]) + float(contribution[u]["visible"])),
        int(unit_qid[u]), u))


def greedy_restore_selection(*, base: np.ndarray, units: Mapping[str, Mapping],
                             cell_domain: set[tuple[int, int]],
                             baseline_holes: Mapping[str, Mapping[tuple[int, int], float]],
                             hole_fn: Callable[[np.ndarray, set[tuple[int, int]], str], Mapping],
                             unit_qid: Mapping[str, int], limit_m2: float = LIMIT_M2):
    """Apply whole-unit restore-to-B selection and recompute all incident cells.

    hole_fn receives (current float32 grid, affected cell set, layer) and returns
    exact measured area per requested cell. Static P/F support geometry is owned
    by the caller and is held fixed during this greedy composition pass.
    """
    if not units:
        return {"status": "FAIL_SUPPORT", "reason": "no locally valid units"}
    h, owner, nodes_by_unit = node_owner_map(units, base)
    cell_owner = {cell: cell_owners(cell, owner) for cell in sorted(cell_domain)}
    changed_cells = {cell for cell, owners in cell_owner.items() if owners}
    if changed_cells != cell_domain:
        raise ValueError("support cell domain differs from changed-vertex incidence")
    if not changed_cells:
        raise ValueError("selected pool has no changed support cells")
    current_holes: dict[str, dict[tuple[int, int], float]] = {}
    baseline_sums = {}
    for layer in LAYERS:
        baseline_holes_layer = {cell: float(baseline_holes[layer][cell]) for cell in changed_cells}
        if any(not np.isfinite(x) or x < 0 for x in baseline_holes_layer.values()):
            raise ValueError(f"invalid baseline hole area in {layer}")
        baseline_check = hole_fn(base, changed_cells, layer)
        if set(baseline_check) != changed_cells or any(
                float(baseline_check[cell]) != baseline_holes_layer[cell] for cell in changed_cells):
            raise AssertionError(f"pinned baseline hole cache does not reconstruct exactly for {layer}")
        measured = hole_fn(h, changed_cells, layer)
        if set(measured) != changed_cells:
            raise ValueError(f"initial hole evaluator returned incomplete cells for {layer}")
        current_holes[layer] = {cell: float(measured[cell]) for cell in changed_cells}
        baseline_sums[layer] = sum(baseline_holes_layer[cell] for cell in sorted(changed_cells))
    if not all(baseline_sums[layer] < limit_m2 for layer in LAYERS):
        return {"status": "FAIL_BASE", "baseline_sums_m2": baseline_sums,
                "limit_m2": limit_m2, "candidate": None}

    # Candidate H must be gated by the same independent hole function.
    running = {layer: sum(current_holes[layer][cell] for cell in sorted(changed_cells)) for layer in LAYERS}
    full_candidate_sums = dict(running)
    contribution = {u: {layer: 0.0 for layer in LAYERS} for u in units}
    joint = {layer: 0.0 for layer in LAYERS}
    for cell in sorted(changed_cells):
        owners = cell_owner[cell]
        for layer in LAYERS:
            area = current_holes[layer][cell]
            if len(owners) == 1:
                contribution[owners[0]][layer] += area
            elif len(owners) > 1:
                joint[layer] += area
    order = deterministic_order(contribution, unit_qid)
    excluded: list[str] = []
    trace = []
    for unit_id in order:
        local_cells = incident_cells(nodes_by_unit[unit_id], changed_cells)
        if not local_cells:
            raise ValueError(f"unit has no incident cells in domain: {unit_id}")
        for node in nodes_by_unit[unit_id]:
            h[node] = base[node]
        for layer in LAYERS:
            measured = hole_fn(h, local_cells, layer)
            if set(measured) != local_cells:
                raise ValueError(f"hole evaluator returned incomplete cells for {unit_id}/{layer}")
            for cell in sorted(local_cells):
                area_value = measured[cell]
                area = float(area_value)
                if not np.isfinite(area) or area < 0:
                    raise ValueError(f"invalid recomputed area {unit_id}/{layer}/{cell}")
                running[layer] += area - current_holes[layer][cell]
                current_holes[layer][cell] = area
        excluded.append(unit_id)
        trace.append({"removed_unit_id": unit_id, "recomputed_cells": len(local_cells),
                      "remaining_sums_m2": dict(running)})
        if all(running[layer] < limit_m2 for layer in LAYERS):
            break
    passed = all(running[layer] < limit_m2 for layer in LAYERS)
    if not passed:
        return {"status": "FAIL_SUPPORT", "baseline_sums_m2": baseline_sums,
                "full_pool_sums_m2": full_candidate_sums, "candidate_sums_m2": running, "limit_m2": limit_m2,
                "excluded_unit_ids": excluded, "retained_unit_ids": [u for u in units if u not in excluded],
                "trace": trace, "candidate": None}
    retained = [u for u in sorted(units) if u not in set(excluded)]
    expected = np.asarray(base, dtype=np.float32).copy()
    for unit_id in retained:
        row = units[unit_id]
        nodes = np.asarray(row["variables_rc"], dtype=np.int32)
        values = np.asarray(row["final_float32"], dtype=np.float32)
        for node, value in zip(nodes.tolist(), values.tolist()):
            expected[tuple(map(int, node))] = np.float32(value)
    if not np.array_equal(h, expected):
        raise AssertionError("whole-unit restoration result differs from retained composition")
    return {"status": "SELECTED", "baseline_sums_m2": baseline_sums,
            "full_pool_sums_m2": full_candidate_sums, "candidate_sums_m2": running, "limit_m2": limit_m2,
            "retained_unit_ids": retained, "excluded_unit_ids": excluded,
            "order": order, "unique_contribution_m2": contribution,
            "joint_shared_cell_area_m2": joint, "trace": trace, "candidate": h,
            "cell_owner": cell_owner, "changed_owner": owner}


def finalize_selection_rows(selection: dict[str, Any], unit_rows: dict[str, dict[str, Any]],
                            valid_unit_ids: set[str]) -> tuple[list[str], list[str]]:
    """Make terminal row classes and receipt ID lists agree, fail-closed."""
    status = selection.get("status")
    if status == "SELECTED":
        retained = set(selection.get("retained_unit_ids", []))
        excluded = set(selection.get("excluded_unit_ids", []))
        if retained & excluded or retained | excluded != valid_unit_ids:
            raise AssertionError("support selection did not partition locally valid units")
        nontrivial_crest = [u for u in retained if u.startswith("crest:") and
                            int(unit_rows[u].get("changed_vertices", 0)) > 0]
        if not nontrivial_crest:
            selection["status"] = "FAIL_CREST_RETENTION"
            selection["candidate"] = None
            status = selection["status"]

    if status == "SELECTED":
        retained_set = set(selection.get("retained_unit_ids", []))
        for unit_id in valid_unit_ids:
            if unit_id in retained_set:
                unit_rows[unit_id]["selection_status"] = "retained"
                unit_rows[unit_id]["selection_reason"] = "retained by exact support gate"
            else:
                unit_rows[unit_id]["selection_status"] = "excluded_support"
                unit_rows[unit_id]["selection_reason"] = "whole-unit restore required by global support sums"
    else:
        selection["candidate"] = None
        selection["retained_unit_ids"] = []
        selection["excluded_unit_ids"] = sorted(valid_unit_ids)
        for unit_id in valid_unit_ids:
            unit_rows[unit_id]["selection_status"] = "excluded_support"
            unit_rows[unit_id]["selection_reason"] = str(status or "support gate failed")

    for unit_id, row in unit_rows.items():
        if row.get("local_status") == "FAIL":
            row["selection_status"] = "excluded_local"
            row["selection_reason"] = row.get("local_reason", "local gates failed")
        elif row.get("selection_status") not in ("retained", "excluded_support"):
            raise AssertionError(f"locally valid unit lacks terminal classification: {unit_id}")

    retained_ids = sorted(u for u, row in unit_rows.items()
                          if row.get("selection_status") == "retained")
    excluded_ids = sorted(u for u, row in unit_rows.items()
                          if row.get("selection_status") != "retained")
    if set(retained_ids) | set(excluded_ids) != set(unit_rows) or set(retained_ids) & set(excluded_ids):
        raise AssertionError("terminal row classification is not exhaustive and disjoint")
    if retained_ids != sorted(selection.get("retained_unit_ids", [])):
        raise AssertionError("retained IDs disagree with terminal unit rows")
    return retained_ids, excluded_ids


def write_candidate_npz(path: Path, base_npz: Mapping[str, np.ndarray], candidate: np.ndarray):
    """Write only a verified selected height field, preserving all B metadata arrays."""
    arrays = {key: np.asarray(value).copy() for key, value in base_npz.items()}
    if "heights" not in arrays or arrays["heights"].dtype != np.float32:
        raise ValueError("baseline NPZ does not expose float32 heights")
    if candidate.dtype != np.float32 or candidate.shape != arrays["heights"].shape:
        raise ValueError("candidate shape/dtype differs from baseline")
    arrays["heights"] = candidate.copy()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp.npz")
    np.savez_compressed(tmp, **arrays)
    os.replace(tmp, path)
    return sha256_file(path)


def load_pinned_module(name: str, path: Path, wanted: str):
    got = sha256_file(path)
    if got != wanted:
        raise AssertionError(f"frozen source changed: {path}: {got} != {wanted}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate_source_fail(pool: dict):
    if sha256_file(PLAN) != PLAN_SHA256:
        raise AssertionError("frozen execution plan hash changed")
    source = pool.get("source_global_report")
    if not isinstance(source, dict) or Path(source.get("path", "")).resolve() != KNOWN_FAIL.resolve():
        raise AssertionError("compound pool does not reference the exact reviewed FAIL report")
    if source.get("sha256") != KNOWN_FAIL_SHA256 or sha256_file(KNOWN_FAIL) != KNOWN_FAIL_SHA256:
        raise AssertionError("source global FAIL report SHA mismatch")
    report = json.loads(KNOWN_FAIL.read_text(encoding="utf-8"))
    if report.get("status") != "FAIL_INCREMENTAL_NONREGRESSION":
        raise AssertionError("source report is no longer the exact FAIL status")
    false_gates = {name for name, passed in report.get("gates", {}).items() if passed is False}
    if false_gates != KNOWN_FAIL_GATES or any(v is not True and v is not False for v in report["gates"].values()):
        raise AssertionError(f"source report does not have exactly the two approved failed gates: {false_gates}")
    info = report.get("information", {})
    if info.get("candidate_sha256") not in (None, KNOWN_FAIL_CANDIDATE_SHA256):
        raise AssertionError("attempt-04 report points at a different legacy candidate")
    return report


def validate_pool(pool_path: Path):
    pool_sha = sha256_file(pool_path)
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    if pool.get("schema") != "ev93.compound-pool.v1" or pool.get("status") != "AUTHORED_QUARANTINED":
        raise ValueError("compound pool must be a finalized quarantined v1 pool")
    validate_source_fail(pool)
    if pool.get("base") != {"path": str(BASE.resolve()), "sha256": BASE_SHA256}:
        raise AssertionError("pool baseline reference differs from frozen B")
    if sha256_file(BASE) != BASE_SHA256:
        raise AssertionError("baseline terrain SHA mismatch")
    legacy = pool.get("legacy_source", {})
    expected_legacy = {
        "prepared_path": str(PREPARED.resolve()), "prepared_sha256": PREPARED_SHA256,
        "receipt_path": str(LEGACY_RECEIPT.resolve()), "receipt_sha256": LEGACY_RECEIPT_SHA256,
        "ledger_path": str(LEGACY_LEDGER.resolve()), "ledger_sha256": LEGACY_LEDGER_SHA256,
    }
    if legacy != expected_legacy:
        raise AssertionError("legacy source pins differ from the frozen author output")
    for path, digest in ((PREPARED, PREPARED_SHA256), (LEGACY_RECEIPT, LEGACY_RECEIPT_SHA256),
                         (LEGACY_LEDGER, LEGACY_LEDGER_SHA256), (COMPOUND_AUTHOR, COMPOUND_AUTHOR_SHA256),
                         (REUSE_INVENTORY, REUSE_INVENTORY_SHA256), (POLICY, POLICY_SHA256),
                         (SHAPE, SHAPE_SHA256)):
        if sha256_file(path) != digest:
            raise AssertionError(f"pinned source changed: {path}")
    crest = pool.get("crest_source", {})
    crest_receipt_path = Path(crest.get("receipt_path", ""))
    crest_rows_path = Path(crest.get("target_rows_path", ""))
    crest_ledger_path = Path(crest.get("ledger_path", ""))
    for path, field in ((crest_receipt_path, "receipt_sha256"),
                        (crest_rows_path, "target_rows_sha256"),
                        (crest_ledger_path, "ledger_sha256")):
        if not path.is_file() or sha256_file(path) != crest.get(field):
            raise AssertionError(f"crest {field} does not pin its artifact: {path}")
    crest_receipt = json.loads(crest_receipt_path.read_text(encoding="utf-8"))
    if (crest_receipt.get("schema") != "ev93.crest-extension.quarantine-receipt.v3" or
            crest_receipt.get("status") != "QUARANTINE_POOL_READY_FOR_SELECTOR" or
            crest_receipt.get("author_source_path") != str(COMPOUND_AUTHOR.resolve()) or
            crest_receipt.get("author_source_sha256") != COMPOUND_AUTHOR_SHA256 or
            crest_receipt.get("execution_plan_sha256") != PLAN_SHA256 or
            crest_receipt.get("source_global_report_sha256") != KNOWN_FAIL_SHA256 or
            crest_receipt.get("target_count") != NONZERO_TARGETS or
            crest_receipt.get("processed_count") != NONZERO_TARGETS or
            crest_receipt.get("remaining_count") != 0 or
            crest_receipt.get("source_global_report_false_gates") != sorted(KNOWN_FAIL_GATES) or
            crest_receipt.get("new_solver_calls") != 0):
        raise AssertionError("crest quarantine receipt is incomplete or pins different sources")
    if (crest_receipt.get("target_rows_path") != str(crest_rows_path.resolve()) or
            crest_receipt.get("ledger_path") != str(crest_ledger_path.resolve()) or
            crest_receipt.get("target_rows_sha256") != crest.get("target_rows_sha256") or
            crest_receipt.get("ledger_sha256") != crest.get("ledger_sha256")):
        raise AssertionError("pool and crest receipt target/ledger refs disagree")
    rows = pool.get("rows")
    if not isinstance(rows, list) or len(rows) != LEGACY_UNITS + NONZERO_TARGETS:
        raise ValueError("compound pool must inventory exactly 340 legacy + 228 crest refs")
    if pool.get("expected_counts") != {"legacy_accepted": LEGACY_UNITS, "crest_targets": NONZERO_TARGETS}:
        raise AssertionError("pool expected_counts mismatch")
    seen = set()
    counts = {"legacy": 0, "crest": 0}
    for row in rows:
        origin = row.get("origin")
        qid = int(row.get("queue_id", -1))
        unit_id = f"{origin}:{qid}"
        if origin not in counts or row.get("unit_id") != unit_id or int(row.get("source_qid", -2)) != qid:
            raise ValueError(f"invalid unit identity: {row}")
        if unit_id in seen:
            raise ValueError(f"duplicate compound unit identity: {unit_id}")
        seen.add(unit_id); counts[origin] += 1
        artifact = Path(row.get("artifact_path", ""))
        if not artifact.is_file() or sha256_file(artifact) != row.get("artifact_sha256"):
            raise AssertionError(f"pool row artifact SHA mismatch: {unit_id}")
        source = Path(row.get("source_result_path", ""))
        if not source.is_file() or sha256_file(source) != row.get("source_result_sha256"):
            raise AssertionError(f"pool source result SHA mismatch: {unit_id}")
        if origin == "legacy" and (row.get("state") != "accepted" or
                artifact.resolve() != source.resolve() or artifact.resolve().suffix != ".json"):
            raise AssertionError(f"legacy row is not an accepted immutable result ref: {unit_id}")
        if origin == "crest" and artifact.resolve() == source.resolve():
            raise AssertionError(f"crest target must remain separate from its source result: {unit_id}")
    if counts != {"legacy": LEGACY_UNITS, "crest": NONZERO_TARGETS}:
        raise AssertionError(f"pool origin counts mismatch: {counts}")
    return pool, pool_sha, crest_receipt


def _load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _stencil_hash(stencils):
    raw = json.dumps(stencils, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def crest_local_validation(selected_consumer, selected_context, base, target, target_ref, detail,
                           source_row, source_nodes, source_stencils, source_direction, prepared_sha):
    """Use the pinned independent local verifier for crest rows and cross-check author API output."""
    qid = int(target_ref["queue_id"])
    old, layer, geom, ev91, ev87, cv, shape, ev92, index_module, policy = selected_context
    patch, gates, metrics = selected_consumer.verify_crest_target(
        old, policy, (layer, geom, ev91, ev87, cv, shape, ev92, index_module),
        source_row, target, base, prepared_sha, {qid: detail})
    if patch is None:
        if target.get("state") != "rejected_policy" or gates != {"policy_rule_available": False}:
            raise AssertionError(f"local verifier returned no crest delta outside policy rejection q{qid}")
        return {"local_status": "FAIL", "local_gates": gates,
                "local_metrics": {"policy_rejection_code": target.get("policy_rejection_code")},
                "local_reason": str(target.get("policy_rejection_code"))}, None
    if target.get("state") != "derived_quarantined":
        raise AssertionError(f"local verifier produced delta for non-derived crest q{qid}")
    if (not np.array_equal(np.asarray(patch["nodes"], dtype=np.int32), source_nodes) or
            not np.array_equal(np.asarray(patch["direction"], dtype=np.float32), source_direction) or
            [tuple(x) for x in patch["stencils"]] != [tuple(x) for x in source_stencils]):
        raise AssertionError(f"independent local verifier differs from author source validation q{qid}")
    gates = {str(k): bool(v) for k, v in gates.items()}
    passed = bool(gates) and all(gates.values())
    return {"local_status": "PASS" if passed else "FAIL", "local_gates": gates,
            "local_metrics": metrics,
            "local_reason": None if passed else "one or more independent crest-local gates failed"}, patch
def _apply_one(base, nodes, values):
    out = np.asarray(base, dtype=np.float32).copy()
    out[tuple(np.asarray(nodes, dtype=np.int32).T)] = np.asarray(values, dtype=np.float32)
    return out


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value.resolve())
    if isinstance(value, Fraction):
        return str(value)
    return value


def _holes_for_grid(cv, ev87, heights, p, f, cells, layer, support_by_cell):
    design = cv.make_design(heights, p, f, cells, layer)
    out = {}
    for cell, design_poly in design.items():
        support = support_by_cell[cell]
        if layer == "visible":
            r, c = cell
            xy = ev87.cell_xy(r, c)
            known = []
            for tri in ev87.TRIS:
                ids = np.asarray(tri, dtype=np.int64)
                if np.isfinite(f[r, c, ids]).all():
                    known.append(Polygon(xy[ids]))
            domain = unary_union(known) if known else Polygon()
            design_poly = design_poly.intersection(domain)
            support = support.intersection(domain)
        out[cell] = float(design_poly.difference(support).area)
    return out


def capture_support_once(vl, ev87, cv, index, p, f, cells, logger=None):
    """One pinned face-index query and exact XZ clipping for the local changed-cell set."""
    if not cells:
        raise ValueError("no cells for support scan")
    bitmap = np.zeros((ev87.N - 1, ev87.N - 1), dtype=bool)
    rc = np.asarray(sorted(cells), dtype=np.int32)
    bitmap[rc[:, 0], rc[:, 1]] = True
    all_faces = index.query_window(0, ev87.N - 2, 0, ev87.N - 2)
    selected = vl.rectangle_any(bitmap, all_faces["cell_range_rc"]) & (all_faces["degenerate"] == 0)
    faces = {k: v[selected] for k, v in all_faces.items()}
    support = {layer: {cell: [] for cell in cells} for layer in LAYERS}
    label = {0: "physical", 1: "visible"}
    eps = {"physical": 1e-5, "visible": 2e-5}
    started = time.monotonic()
    for i in range(len(faces["kind"])):
        layer = label[int(faces["kind"][i])]
        xyz = faces["xyz"][i]
        face_poly = Polygon(xyz[:, (0, 2)])
        if face_poly.is_empty or face_poly.area <= 0:
            continue
        coeff = np.asarray(faces["plane_y_xz"][i], dtype=np.float64)
        r0, r1, c0, c1 = map(int, faces["cell_range_rc"][i])
        for r in range(max(0, r0), min(ev87.N - 2, r1) + 1):
            for c in range(max(0, c0), min(ev87.N - 2, c1) + 1):
                cell = (r, c)
                if cell not in cells:
                    continue
                xy = ev87.cell_xy(r, c)
                for tri in ev87.TRIS:
                    ids = np.asarray(tri, dtype=np.int64)
                    piece = face_poly.intersection(Polygon(xy[ids]))
                    if piece.is_empty or piece.area <= 0:
                        continue
                    _, _, target = cv.cell_tri_target(r, c, layer, tri, p, f)
                    if target is None:
                        continue
                    matched = cv.clip_affine_band(piece, coeff - target, eps[layer])
                    if not matched.is_empty:
                        support[layer][cell].append(matched)
        if logger and (i + 1) % 100000 == 0:
            logger("support_scan_progress", face_rows=i + 1,
                   selected_face_rows=len(faces["kind"]), elapsed_s=round(time.monotonic() - started, 1))
    unioned = {layer: {cell: (unary_union(parts) if parts else Polygon())
                       for cell, parts in by_cell.items()}
               for layer, by_cell in support.items()}
    if logger:
        logger("support_scan_complete", scanned_faces=len(faces["kind"]),
               indexed_faces=len(all_faces["kind"]), cells=len(cells),
               elapsed_s=round(time.monotonic() - started, 1))
    return unioned, {"indexed_rows_full_grid": int(len(all_faces["kind"])),
                     "bbox_candidates_intersecting_cells": int(len(faces["kind"])),
                     "target_cells": int(len(cells))}


def _source_readset(pool_path, pool, crest_receipt, rows, vl, ev87, prepared, receipt,
                    entries, ledger, ledger_path):
    expected = vl.expected_dynamic_readset(PREPARED, LEGACY_RECEIPT, prepared, receipt,
        entries, ledger, ledger_path, vl.INDEX_MANIFEST, ev87.MODEL_DIR)
    expected[str(Path(pool_path).resolve())] = sha256_file(pool_path)
    expected[str(COMPOUND_AUTHOR.resolve())] = COMPOUND_AUTHOR_SHA256
    expected[str(POLICY.resolve())] = POLICY_SHA256
    expected[str(REUSE_INVENTORY.resolve())] = REUSE_INVENTORY_SHA256
    expected[str(PLAN.resolve())] = PLAN_SHA256
    expected[str(KNOWN_FAIL.resolve())] = KNOWN_FAIL_SHA256
    expected[str(SELECTED_LOCAL_CONSUMER.resolve())] = SELECTED_LOCAL_CONSUMER_SHA256
    expected[str(SELECTED_LOCAL_HELPER.resolve())] = SELECTED_LOCAL_HELPER_SHA256
    expected[str(BASE.resolve())] = BASE_SHA256
    for ref in (pool["crest_source"],):
        for key in ("receipt_path", "target_rows_path", "ledger_path"):
            path = Path(ref[key]).resolve()
            digest_key = {"receipt_path": "receipt_sha256", "target_rows_path": "target_rows_sha256",
                          "ledger_path": "ledger_sha256"}[key]
            expected[str(path)] = str(ref[digest_key])
    for row in rows:
        for path_key, sha_key in (("artifact_path", "artifact_sha256"),
                                  ("source_result_path", "source_result_sha256")):
            path = Path(row[path_key]).resolve()
            expected[str(path)] = str(row[sha_key])
        if row["origin"] == "legacy":
            obj = json.loads(Path(row["artifact_path"]).read_text(encoding="utf-8"))
            delta = Path(obj["delta_path"]).resolve()
            expected[str(delta)] = str(obj["delta_sha256"])
        else:
            obj = json.loads(Path(row["artifact_path"]).read_text(encoding="utf-8"))
            for path_name, hash_name in (("source_solution_path", "source_solution_sha256"),
                                         ("source_marker_path", "source_marker_sha256")):
                path = Path(obj[path_name]).resolve()
                expected[str(path)] = str(obj[hash_name])
    expected[str(Path(__file__).resolve())] = sha256_file(__file__)
    return expected


def execute_pool(pool_path: Path, out_dir: Path, progress_path: Path | None = None):
    """Run selector once. This entry point is deliberately not called by tests."""
    pool, pool_sha, crest_receipt = validate_pool(Path(pool_path))
    if Path(out_dir).exists() and any(Path(out_dir).iterdir()):
        raise FileExistsError(f"selector output directory is nonempty: {out_dir}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    def log(stage, **fields):
        row = {"elapsed_s": round(time.monotonic() - start, 3), "stage": stage, **fields}
        print(json.dumps(row, sort_keys=True, allow_nan=False), flush=True)
        if progress_path:
            path = Path(progress_path); path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
                stream.flush(); os.fsync(stream.fileno())

    vl = load_pinned_module("ev93_compound_consumer", CONSUMER,
                            "33050881caaf5e75f288d4122222c15eb326bf146c28a4c723760564457b3dc2")
    ev, ev91, ev87, cv, shape, ev92, index_module = vl.load_helpers()
    author = load_pinned_module("ev93_compound_author_source_validator", COMPOUND_AUTHOR,
                                COMPOUND_AUTHOR_SHA256)
    selected_local = load_pinned_module("ev93_compound_selected_local_consumer",
        SELECTED_LOCAL_CONSUMER, SELECTED_LOCAL_CONSUMER_SHA256)
    selected_context = selected_local.loadctx()
    bundle = ev.checked_sources()
    base_npz = bundle["B"]
    base = np.asarray(base_npz["heights"], dtype=np.float32)
    if sha256_file(BASE) != BASE_SHA256:
        raise AssertionError("B changed after pool validation")
    prepared, legacy_receipt, entries, ledger, ledger_path = vl.verify_prepared(PREPARED,
        LEGACY_RECEIPT, base)
    if (legacy_receipt.get("candidate_sha256") != KNOWN_FAIL_CANDIDATE_SHA256 or
            legacy_receipt.get("prepared_sha256") != PREPARED_SHA256 or
            legacy_receipt.get("ledger_sha256") != LEGACY_LEDGER_SHA256):
        raise AssertionError("legacy accepted pool no longer matches the exact attempt-04 source candidate")
    details = vl.validate_detail_hashes(prepared, entries)
    readset = _source_readset(pool_path, pool, crest_receipt, pool["rows"], vl, ev87,
                              prepared, legacy_receipt, entries, ledger, ledger_path)
    if sha256_file(LEGACY_LEDGER) != LEGACY_LEDGER_SHA256:
        raise AssertionError("legacy append-only ledger changed before selector execution")
    source_candidate, _, legacy_patches, _ = vl.reconstruct_candidate(base_npz,
        legacy_receipt, entries, ledger, details, LEGACY_RECEIPT.parent)
    legacy_by_qid = {int(patch["queue_id"]): patch for patch in legacy_patches}
    pool_legacy_ids = {int(row["queue_id"]) for row in pool["rows"] if row["origin"] == "legacy"}
    if pool_legacy_ids != set(legacy_by_qid):
        raise AssertionError("compound legacy qid inventory differs from the frozen 340 accepted deltas")
    inv = json.loads(REUSE_INVENTORY.read_text(encoding="utf-8"))
    if inv.get("status") != "REUSE_SOURCE_INVENTORY_READY" or len(inv.get("reusable_directions", [])) != NONZERO_TARGETS:
        raise AssertionError("pinned reusable-direction inventory is not ready for all 228 crest targets")
    inv_by_qid = {int(row["queue_id"]): row for row in inv["reusable_directions"]}
    prepared_by_qid = {int(row["queue_id"]): row for row in entries}
    target_refs = [row for row in pool["rows"] if row["origin"] == "crest"]
    target_events = _load_jsonl(Path(pool["crest_source"]["target_rows_path"]))
    event_by_qid = {int(row["queue_id"]): row for row in target_events}
    crest_pool_ids = {int(row["queue_id"]) for row in target_refs}
    if (len(event_by_qid) != NONZERO_TARGETS or len(target_refs) != NONZERO_TARGETS or
            crest_pool_ids != set(inv_by_qid) or crest_pool_ids != set(event_by_qid)):
        raise AssertionError("crest target ledger/reference cardinality differs from 228")
    # The author receipt and target JSONL must enumerate the same ordered terminal rows.
    receipt_targets = crest_receipt.get("pool_targets")
    if not isinstance(receipt_targets, list) or len(receipt_targets) != NONZERO_TARGETS:
        raise AssertionError("crest receipt lacks the 228 target reference inventory")
    expected_refs = [{"queue_id": int(x["queue_id"]), "source_qid": int(x["source_qid"]),
        "seed_id": int(x["seed_id"]), "state": x["state"], "path": str(Path(x["artifact_path"]).resolve()),
        "sha256": x["artifact_sha256"], "source_result_path": x["source_result_path"],
        "source_result_sha256": x["source_result_sha256"]} for x in target_refs]
    if canonical_sha(sorted(expected_refs, key=lambda x: int(x["queue_id"]))) != canonical_sha(
            sorted(receipt_targets, key=lambda x: int(x["queue_id"]))):
        raise AssertionError("compound pool crest refs differ from author receipt terminal inventory")

    unit_rows = {}
    unit_payloads = {}
    for row in pool["rows"]:
        origin = row["origin"]; qid = int(row["queue_id"]); unit_id = row["unit_id"]
        if origin == "legacy":
            patch = legacy_by_qid.get(qid)
            if patch is None:
                raise AssertionError(f"legacy pool q{qid} is not accepted by the pinned legacy receipt")
            if Path(row["artifact_path"]).resolve() != Path(ledger[qid]["result_path"]).resolve():
                raise AssertionError(f"legacy pool q{qid} result ref differs from terminal ledger")
            if (int(row["seed_id"]) != int(ledger[qid]["seed_id"]) or
                    row["source_result_sha256"] != ledger[qid]["result_sha256"]):
                raise AssertionError(f"legacy pool q{qid} identity differs from terminal ledger")
            one = _apply_one(base, patch["nodes"], patch["final"])
            validation = vl.verify_local_windows(ev, ev87, shape, ev92, base, one,
                                                  [patch], {qid: details[qid]})
            metrics = validation["metrics"][0]
            passed = bool(validation["gates"][qid])
            local = {"local_status": "PASS" if passed else "FAIL",
                "local_gates": {"ev92_complete_local_contract": passed,
                                **{str(k): bool(v) for k, v in metrics.items()
                                   if isinstance(v, bool)},
                                **{f"shape:{k}": bool(v) for k, v in metrics["shape"]["gates"].items()}},
                "local_metrics": metrics,
                "local_reason": None if passed else "EV92 local gate returned false"}
            payload = {"variables_rc": patch["nodes"], "B_values_float32": patch["B"],
                       "final_float32": patch["final"]}
        else:
            qref = event_by_qid.get(qid)
            if not qref or Path(qref["path"]).resolve() != Path(row["artifact_path"]).resolve() or qref["sha256"] != row["artifact_sha256"]:
                raise AssertionError(f"crest pool q{qid} target ref differs from terminal targets ledger")
            target = json.loads(Path(row["artifact_path"]).read_text(encoding="utf-8"))
            source = inv_by_qid.get(qid)
            prep_row = prepared_by_qid.get(qid)
            if source is None or prep_row is None:
                raise AssertionError(f"crest q{qid} is missing a source inventory or prepared identity")
            if (target.get("source_qid") != qid or target.get("target_queue_id") != qid or
                    target.get("seed_id") != int(row["seed_id"]) or
                    int(source.get("seed_id", -1)) != int(row["seed_id"]) or
                    target.get("source_result_path") != row["source_result_path"] or
                    target.get("source_result_sha256") != row["source_result_sha256"]):
                raise AssertionError(f"crest target/source reference identity mismatch q{qid}")
            source_result, source_nodes, source_stencils, source_direction = author.validate_source_row(
                vl, source, prep_row, base)
            local, patch = crest_local_validation(selected_local, selected_context, base,
                target, row, details[qid], source, source_nodes, source_stencils,
                source_direction, sha256_file(PREPARED))
            payload = None if patch is None else {"variables_rc": patch["nodes"],
                "B_values_float32": patch["B"], "final_float32": patch["final"]}
        local["unit_id"] = unit_id
        local["origin"] = origin
        local["queue_id"] = qid
        local["source_qid"] = int(row["source_qid"])
        local["source_artifact_path"] = str(Path(row["artifact_path"]).resolve())
        local["source_artifact_sha256"] = row["artifact_sha256"]
        local["changed_vertices"] = 0 if payload is None else int(np.count_nonzero(
            np.asarray(payload["final_float32"], dtype=np.float32) !=
            np.asarray(payload["B_values_float32"], dtype=np.float32)))
        changed_rc = [] if payload is None else [list(map(int, rc)) for rc, changed_value in zip(
            np.asarray(payload["variables_rc"], dtype=np.int32).tolist(),
            (np.asarray(payload["final_float32"], dtype=np.float32) !=
             np.asarray(payload["B_values_float32"], dtype=np.float32)).tolist()) if changed_value]
        local["changed_vertices_sha256"] = canonical_sha(changed_rc)
        if local["local_status"] == "PASS":
            if payload is None or local["changed_vertices"] == 0:
                raise AssertionError(f"local PASS has no nontrivial delta: {unit_id}")
            unit_payloads[unit_id] = payload
            local["selection_status"] = "retained_pending_support"
            local["selection_reason"] = "locally valid; awaiting exact global support recomposition"
        else:
            local["selection_status"] = "excluded_local"
            local["selection_reason"] = local["local_reason"]
        unit_rows[unit_id] = json_safe(local)
        if len(unit_rows) % 25 == 0:
            log("local_gate_progress", classified=len(unit_rows), total=len(pool["rows"]))

    valid = {u: payload for u, payload in unit_payloads.items()}
    if not valid:
        selection = {"status": "FAIL_LOCAL", "limit_m2": LIMIT_M2, "candidate": None,
                     "retained_unit_ids": [], "excluded_unit_ids": sorted(unit_rows)}
        support_stats = None
    else:
        h0, owner, nodes_by_unit = node_owner_map(valid, base)
        changed = np.asarray(sorted(changed_nodes(base, h0)), dtype=np.int32)
        cell_domain = vl.affected_cells(ev87, changed)
        if not cell_domain:
            raise AssertionError("locally valid pool produces no affected support cells")
        index = index_module.FaceRangeIndex(INDEX_RUN)
        support, support_stats = capture_support_once(vl, ev87, cv, index,
            bundle["P"], bundle["F"], cell_domain, log)
        baseline_holes = {layer: _holes_for_grid(cv, ev87, base, bundle["P"], bundle["F"],
                              cell_domain, layer, support[layer]) for layer in LAYERS}
        def hole_fn(grid, cells, layer):
            return _holes_for_grid(cv, ev87, grid, bundle["P"], bundle["F"], cells,
                                   layer, support[layer])
        qids = {u: int(unit_rows[u]["source_qid"]) for u in valid}
        selection = greedy_restore_selection(base=base, units=valid,
            cell_domain=cell_domain, baseline_holes=baseline_holes, hole_fn=hole_fn,
            unit_qid=qids, limit_m2=LIMIT_M2)
        index.reverify()
        retained, excluded = finalize_selection_rows(selection, unit_rows, set(valid))

    # Read-set and source identities must remain stable throughout validation and selection.
    drift = {path: {"expected": digest, "actual": sha256_file(path)}
             for path, digest in readset.items() if sha256_file(path) != digest}
    if drift:
        raise AssertionError(f"source read-set changed during selector run: {list(drift)[:5]}")
    if sha256_file(pool_path) != pool_sha:
        raise AssertionError("compound pool changed during selector run")
    if sha256_file(PLAN) != PLAN_SHA256:
        raise AssertionError("execution plan changed during selector run")

    candidate_path = None
    candidate_sha = None
    if selection.get("status") == "SELECTED":
        candidate_path = out_dir / "candidate-terrain.npz"
        with np.load(BASE, allow_pickle=False) as z:
            base_arrays = {key: z[key] for key in z.files}
        candidate_sha = write_candidate_npz(candidate_path, base_arrays, selection["candidate"])
        # Ensure candidate metadata were retained bit-exactly from B.
        with np.load(candidate_path, allow_pickle=False) as z:
            if set(z.files) != set(base_arrays):
                raise AssertionError("candidate NPZ key inventory differs from B")
            for key, value in base_arrays.items():
                if key != "heights" and not np.array_equal(z[key], value, equal_nan=True):
                    raise AssertionError(f"candidate metadata changed from B: {key}")
    if selection.get("status") == "FAIL_LOCAL":
        retained = []
        excluded = sorted(unit_rows)
    elif valid:
        # Recheck receipt lists against final row classes after all support gates.
        retained, excluded = finalize_selection_rows(selection, unit_rows, set(valid))
    else:
        retained = []
        excluded = sorted(unit_rows)
    if set(retained) | set(excluded) != set(unit_rows) or set(retained) & set(excluded):
        raise AssertionError("final selection classification is not exhaustive and disjoint")
    receipt = {
        "schema": SCHEMA, "status": selection.get("status", "INCOMPLETE"),
        "selector_source_path": str(Path(__file__).resolve()), "selector_sha256": sha256_file(__file__),
        "selection_plan_path": str(PLAN.resolve()), "plan_sha256": PLAN_SHA256,
        "compound_pool_path": str(Path(pool_path).resolve()), "compound_pool_sha256": pool_sha,
        "source_global_report_path": str(KNOWN_FAIL.resolve()), "source_global_report_sha256": KNOWN_FAIL_SHA256,
        "base_path": str(BASE.resolve()), "base_sha256": BASE_SHA256,
        "legacy_source": pool["legacy_source"], "crest_source": pool["crest_source"],
        "index_manifest_path": str(vl.INDEX_MANIFEST.resolve()),
        "index_manifest_sha256": sha256_file(vl.INDEX_MANIFEST),
        "index_builder_path": str(vl.INDEX_SOURCE.resolve()),
        "index_builder_sha256": sha256_file(vl.INDEX_SOURCE),
        "source_read_set": readset,
        "population": {"legacy": LEGACY_UNITS, "crest": NONZERO_TARGETS,
                       "locally_considered": len(unit_rows),
                       "locally_valid": sum(x["local_status"] == "PASS" for x in unit_rows.values()),
                       "locally_invalid": sum(x["local_status"] == "FAIL" for x in unit_rows.values())},
        "units": [unit_rows[u] for u in sorted(unit_rows)],
        "retained_unit_ids": retained, "excluded_unit_ids": excluded,
        "support": {"limit_m2_strict": LIMIT_M2,
                    "baseline_sums_m2": selection.get("baseline_sums_m2"),
                    "selected_sums_m2": selection.get("candidate_sums_m2"),
                    "locally_valid_full_pool_sums_m2": selection.get("full_pool_sums_m2"),
                    "index_scan": support_stats,
                    "excluded_whole_unit_order": selection.get("order"),
                    "unique_contribution_m2": selection.get("unique_contribution_m2"),
                    "joint_shared_cell_area_m2": selection.get("joint_shared_cell_area_m2"),
                    "recomposition_trace": selection.get("trace")},
        "candidate": None if candidate_path is None else {
            "path": str(candidate_path.resolve()), "sha256": candidate_sha,
            "metadata_equal_to_B": True},
    }
    receipt = json_safe(receipt)
    receipt_sha = atomic_json(out_dir / "selection.json", receipt)
    log("selection_receipt_written", status=receipt["status"], receipt=str(out_dir / "selection.json"),
        receipt_sha256=receipt_sha, candidate_sha256=candidate_sha,
        retained=len(retained), excluded=len(excluded))
    return receipt


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--execute", action="store_true",
                        help="run the pinned whole-pool selector once; no work occurs without this flag")
    parser.add_argument("--pool", type=Path, default=POOL_DEFAULT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--progress-jsonl", type=Path)
    args = parser.parse_args()
    if args.self_test:
        import unittest
        test_path = Path(__file__).with_name("test_selector.py")
        spec = importlib.util.spec_from_file_location("ev93_compound_selector_tests", test_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        print(json.dumps({"status": "FIXTURES_PASS" if result.wasSuccessful() else "FIXTURES_FAIL",
                          "tests_run": result.testsRun, "failures": len(result.failures),
                          "errors": len(result.errors)}, sort_keys=True))
        return 0 if result.wasSuccessful() else 1
    if not args.execute:
        parser.error("no pool read or selector action occurs without --execute")
    result = execute_pool(args.pool, args.output_dir, args.progress_jsonl)
    print(json.dumps({"status": result["status"],
                      "selection": str((args.output_dir / "selection.json").resolve()),
                      "candidate": result.get("candidate")}, sort_keys=True, allow_nan=False))
    return 0 if result["status"] == "SELECTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())



