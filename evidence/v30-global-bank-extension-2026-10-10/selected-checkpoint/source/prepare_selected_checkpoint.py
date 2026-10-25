"""Create a hash-verified, source-only EV93 selected-bank checkpoint.

The checkpoint covers the closed selection, global consumer, policy and
build-selected evidence. The separate global-operator-prototype is excluded
because its real-sector pilot has active writers. Native readback evidence is
required and RPT payloads are referenced by SHA instead of copied. This pack
does not wait for or include that pilot/solver, and native readback is not a
visual/render PASS. The script is not run until the owner reviews this change.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

G = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010").resolve()
W = Path(r"C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290").resolve()
DEST = W / "evidence/v30-global-bank-extension-2026-10-10/selected-checkpoint"
SCOPE_NOTE = G / "selected-checkpoint-scope.md"
SELECTION = G / "compound-selection/run-02/selection.json"
ATTEMPT = G / "crest-extension/selected-consumer-runs/attempt-03"
ATTEMPT_LAUNCH = ATTEMPT / "launch.json"
ATTEMPT_REPORT = ATTEMPT / "review.json"
ATTEMPT_CONSOLE = ATTEMPT / "console.log"
GLOBAL_SOURCE = G / "crest-extension/verify_selected_composite_v2.py"
LOCAL_SOURCE = G / "crest-extension/verify_selected_composite.py"
EXPECTED_GLOBAL_SHA = "6e661b073e5f27b2475e6b82d75d6a7722d0503a082dcfd51d8f00bd6de9722b"
EXPECTED_LOCAL_SHA = "8cd8f28b7914936bdf86f884b18bd14eb11aeca306f24327851dda340f16a543"
EXPECTED_SELECTOR_SHA = "0d29d3979c1f8bc0d3b0b1833edb314a5807fe5b22ba63b43c44080732fe81bc"
EV82 = Path(r"E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010")
BUILD_SELECTED = G / "build-selected"
NATIVE_REFERENCE = BUILD_SELECTED / "native-reference.json"
NATIVE_CAPTURE = BUILD_SELECTED / "native-capture.json"
NATIVE_PROVENANCE = BUILD_SELECTED / "native-run-provenance.json"
NATIVE_VERIFICATION = BUILD_SELECTED / "native-verification.json"
NATIVE_REVIEW = BUILD_SELECTED / "native-independent-review.json"
NATIVE_SNAPSHOT = BUILD_SELECTED / "native-snapshot.log"
NATIVE_COLLECTOR = BUILD_SELECTED / "collect_native_snapshot.py"
BASE_ADDONS = Path(r"P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons")

COPY_ROOTS = (
    "compound-selection",
    "crest-extension",
    "crest-policy",
    "build-selected",
)
COPY_SUFFIXES = {".py", ".md", ".ps1", ".json", ".jsonl", ".log"}
READSET_KEYS = {"source_read_set", "input_hashes", "input_hashes_expected",
                "input_hashes_start", "input_hashes_end"}
SHA_LENGTH = 64
MAX_COPY_FILE_BYTES = 32 * 1024 * 1024
PRUNE_BUILD_SELECTED_TOP_LEVEL = {
    "candidate", "decoded", "distribution", "native-controls", "package", "packed", "surface",
}
TERMINAL_STATUSES = {
    "PASS_INCREMENTAL_NONREGRESSION",
    "FAIL_INCREMENTAL_NONREGRESSION",
    "ERROR_COMPOUND_CONSUMER",
}
TRANSIENT_NAMES = {"progress.jsonl", "console.log"}
JSONL_EVIDENCE_NAMES = {"targets.jsonl", "ledger.jsonl"}
NATIVE_RPT_BASELINE_KEYS = ("EV82", "EV87", "EV93")


def is_reparse_or_junction(path: Path) -> bool:
    """Return true for symlinks, Windows junctions, and other reparse points."""
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    if callable(is_junction) and is_junction():
        return True
    try:
        attributes = path.stat(follow_symlinks=False).st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def walk_files_bounded(root: Path, excluded: dict[str, int]) -> Iterable[Path]:
    """Walk an approved source root without traversing reparse points or generated build trees."""
    root = Path(os.path.abspath(root))
    if is_reparse_or_junction(root):
        raise RuntimeError(f"checkpoint source root is a reparse point: {root}")
    root = root.resolve()
    prune = PRUNE_BUILD_SELECTED_TOP_LEVEL if root == BUILD_SELECTED.resolve() else set()
    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        kept_dirs = []
        for name in dirnames:
            child = current_path / name
            relative_parts = child.relative_to(root).parts
            if len(relative_parts) == 1 and name in prune:
                excluded["generated_tree_pruned"] += 1
                continue
            if is_reparse_or_junction(child):
                excluded["reparse_point_pruned"] += 1
                continue
            kept_dirs.append(name)
        dirnames[:] = kept_dirs
        for name in filenames:
            path = current_path / name
            if is_reparse_or_junction(path):
                excluded["reparse_file_skipped"] += 1
                continue
            yield path.resolve()


def verify_native_evidence() -> dict[str, Any]:
    """Require the fresh, closed native run and return verified RPT references."""
    required = (NATIVE_REFERENCE, NATIVE_CAPTURE, NATIVE_PROVENANCE,
                NATIVE_VERIFICATION, NATIVE_REVIEW, NATIVE_SNAPSHOT, NATIVE_COLLECTOR)
    for path in required:
        if not path.is_file():
            raise RuntimeError(f"native readback evidence is incomplete: {path}")
    ref = read_json(NATIVE_REFERENCE)
    capture = read_json(NATIVE_CAPTURE)
    provenance = read_json(NATIVE_PROVENANCE)
    verification = read_json(NATIVE_VERIFICATION)
    review = read_json(NATIVE_REVIEW)
    run_id = capture.get("run_id")
    if (capture.get("status") != "CAPTURED_FRESH_CLOSED_SNAPSHOT_NOT_YET_VERIFIED" or
            review.get("status") != "PASS_NATIVE_READBACK_PROVENANCE_WITH_INHERITED_RUNTIME_DIAGNOSTICS" or
            run_id != provenance.get("run_identity", {}).get("run_id") or
            run_id != provenance.get("launch", {}).get("run_id") or
            run_id != provenance.get("close", {}).get("run_id") or
            run_id != review.get("run_id")):
        raise RuntimeError("native readback receipts are not a single fresh closed run")
    if verification.get("status") != "PASS_COMPLETE_NATIVE_READBACK" or verification.get("errors"):
        raise RuntimeError("native semantic verification is not a clean terminal PASS")
    if (not provenance.get("snapshot_source_was_absent_before_launch") or
            not provenance.get("close", {}).get("graceful") or
            not provenance.get("close", {}).get("run_retired") or
            not provenance.get("close", {}).get("exit_metrics_valid")):
        raise RuntimeError("native run freshness/lifecycle provenance is incomplete")
    processes = provenance.get("run_identity", {}).get("processes", [])
    if len(processes) != 1 or processes[0].get("role") != "server":
        raise RuntimeError("native readback was not bound to exactly one server process")
    coordination = provenance.get("final_coordination", {})
    if (coordination.get("owner") is not None or coordination.get("occupied") or
            coordination.get("pending_commands") != 0 or
            coordination.get("self", {}).get("state") != "none"):
        raise RuntimeError("native run coordination did not close idle")
    request = provenance.get("request", {})
    if (request.get("mode") != "server" or
            request.get("mission") != ref.get("mission") or
            request.get("extra_mods") != [r"P:\Mods\@DayZ_Baltic_EV93_SelectedBankPreviewV1"]):
        raise RuntimeError("native run mission/mod identity differs from selected EV93 reference")
    source = Path(capture.get("source", ""))
    destination = Path(capture.get("destination", ""))
    source_stat = source.stat()
    created = datetime.fromisoformat(capture["server_created_utc"].replace("Z", "+00:00")).timestamp()
    if (source.resolve() != Path(provenance.get("snapshot_source_precheck", "")).resolve() or
            destination.resolve() != NATIVE_SNAPSHOT.resolve() or
            source_stat.st_ctime < created or source_stat.st_mtime < created):
        raise RuntimeError("native snapshot is stale or does not match the run source")
    expected_hashes = (
        (NATIVE_REFERENCE, capture.get("reference_sha256")),
        (NATIVE_PROVENANCE, capture.get("provenance_sha256")),
        (NATIVE_COLLECTOR, capture.get("collector_sha256")),
        (NATIVE_SNAPSHOT, capture.get("copied_sha256")),
        (BUILD_SELECTED / "runtime-rpt-excerpt.log", capture.get("rpt_excerpt_sha256")),
        (source, capture.get("source_sha256")),
        (Path(capture.get("rpt_path", "")), capture.get("rpt_sha256")),
    )
    for path, digest in expected_hashes:
        if not digest or not path.is_file() or sha256(path).lower() != str(digest).lower():
            raise RuntimeError(f"native readback hash reference is missing or drifted: {path}")
    if (capture.get("source_sha256") != capture.get("copied_sha256") or
            capture.get("source_sha256") != verification.get("runtime_sha256") or
            ref.get("terrain_sha256") != verification.get("terrain_sha256") or
            ref.get("terrain_sha256") != sha256(BUILD_SELECTED / "candidate/terrain.npz")):
        raise RuntimeError("native snapshot or candidate is not bound to the semantic verification")
    if not isinstance(review.get("crosspins"), dict) or not all(review["crosspins"].values()):
        raise RuntimeError("independent native review cross-pins are incomplete")

    rpt_records = review.get("runtime_comparison", {}).get("records", {})
    if set(rpt_records) != set(NATIVE_RPT_BASELINE_KEYS):
        raise RuntimeError("native independent review lacks EV82/EV87/EV93 RPT references")
    rpt_refs = []
    for key in NATIVE_RPT_BASELINE_KEYS:
        record = rpt_records[key]
        path = Path(record.get("rpt_path", ""))
        digest = record.get("rpt_sha256")
        if not path.is_file() or not digest or sha256(path).lower() != str(digest).lower():
            raise RuntimeError(f"native RPT reference is missing or drifted: {path}")
        if key == "EV93" and (path.resolve() != Path(capture["rpt_path"]).resolve() or
                               digest.lower() != capture["rpt_sha256"].lower()):
            raise RuntimeError("EV93 RPT reference differs from the fresh capture receipt")
        rpt_refs.append({"label": key, "path": str(path.resolve()), "kind": "rpt",
                         "copied": False, "size_bytes": path.stat().st_size,
                         "sha256": digest.lower()})
    return {"run_id": run_id, "capture": capture, "verification": verification,
            "review": review, "rpt_references": rpt_refs}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bounded_text_excerpt(path: Path, head_count: int = 12, tail_count: int = 12) -> dict[str, Any]:
    """Read only a bounded UTF-8 excerpt from a potentially large runtime log."""
    from collections import deque

    with path.open("r", encoding="utf-8", errors="replace") as stream:
        head = []
        tail: deque[str] = deque(maxlen=tail_count)
        for index, line in enumerate(stream):
            if index < head_count:
                head.append(line.rstrip("\r\n"))
            tail.append(line.rstrip("\r\n"))
    return {"head_lines": head, "tail_lines": list(tail),
            "head_line_limit": head_count, "tail_line_limit": tail_count}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def resolve_reference(raw: str, owner: Path) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = owner.parent / path
    return path.resolve()


def require_terminal_attempt() -> dict[str, Any]:
    for required in (SELECTION, ATTEMPT_LAUNCH, ATTEMPT_REPORT, ATTEMPT_CONSOLE,
                     GLOBAL_SOURCE, LOCAL_SOURCE):
        if not required.is_file():
            raise RuntimeError(f"checkpoint input is missing; attempt-03 may still be running: {required}")
    selection = read_json(SELECTION)
    launch = read_json(ATTEMPT_LAUNCH)
    report = read_json(ATTEMPT_REPORT)
    if selection.get("schema") != "ev93.compound-selection.v1" or selection.get("status") != "SELECTED":
        raise RuntimeError("run-02 selection is not terminal SELECTED")
    if sha256(GLOBAL_SOURCE) != EXPECTED_GLOBAL_SHA:
        raise RuntimeError("global consumer source no longer matches the pinned v2 source")
    if sha256(LOCAL_SOURCE) != EXPECTED_LOCAL_SHA:
        raise RuntimeError("local verifier source no longer matches the selector pin")
    selector = G / "compound-selection/selector.py"
    if sha256(selector) != EXPECTED_SELECTOR_SHA:
        raise RuntimeError("selector source no longer matches the selected receipt freeze")
    selection_sha = sha256(SELECTION)
    if launch.get("selection_sha256") != selection_sha:
        raise RuntimeError("attempt-03 launch is not bound to the current run-02 selection")
    if launch.get("source_sha256") != EXPECTED_GLOBAL_SHA:
        raise RuntimeError("attempt-03 launch source SHA differs from pinned global v2")
    status = report.get("status")
    if status not in TERMINAL_STATUSES:
        raise RuntimeError(f"attempt-03 report is absent or nonterminal: {status!r}")
    started = datetime.fromisoformat(str(launch.get("started_utc", "")).replace("Z", "+00:00"))
    if started.tzinfo is None:
        raise RuntimeError("attempt-03 launch timestamp has no timezone")
    if ATTEMPT_REPORT.stat().st_mtime < started.timestamp():
        raise RuntimeError("attempt-03 report predates its launch; refusing stale report")
    if ATTEMPT_CONSOLE.stat().st_mtime < started.timestamp():
        raise RuntimeError("attempt-03 console summary predates its launch; refusing stale terminal marker")

    # The consumer prints this summary only after atomically writing review.json.
    final_summary = None
    for line in ATTEMPT_CONSOLE.read_text(encoding="utf-8-sig").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and item.get("output"):
            try:
                if Path(item["output"]).resolve() == ATTEMPT_REPORT.resolve():
                    final_summary = item
            except (OSError, TypeError, ValueError):
                pass
    if not final_summary or final_summary.get("status") != status:
        raise RuntimeError("attempt-03 lacks the consumer's terminal output summary")

    if status != "ERROR_COMPOUND_CONSUMER":
        info = report.get("information")
        if not isinstance(info, dict):
            raise RuntimeError("terminal PASS/FAIL report has no information block")
        candidate = selection.get("candidate")
        if (info.get("selection_sha256") != selection_sha or
                info.get("consumer_source_path") != str(GLOBAL_SOURCE.resolve()) or
                info.get("consumer_source_sha256") != EXPECTED_GLOBAL_SHA or
                not isinstance(candidate, dict) or
                info.get("candidate_sha256") != candidate.get("sha256") or
                resolve_reference(info.get("candidate_path", ""), ATTEMPT_REPORT) !=
                resolve_reference(candidate.get("path", ""), SELECTION)):
            raise RuntimeError("terminal report does not identify the pinned source, selection, and candidate")
        expected = info.get("input_hashes_expected")
        if (not isinstance(expected, dict) or not expected or
                expected != info.get("input_hashes_start") or
                expected != info.get("input_hashes_end")):
            raise RuntimeError("terminal global report readsets are incomplete or inconsistent")
        for raw, digest in expected.items():
            path = resolve_reference(raw, ATTEMPT_REPORT)
            if not path.is_file() or sha256(path).lower() != str(digest).lower():
                raise RuntimeError(f"terminal global report readset does not match disk: {path}")
    return {"selection": selection, "selection_sha256": selection_sha,
            "launch": launch, "report": report, "report_sha256": sha256(ATTEMPT_REPORT),
            "status": status, "global_source_sha256": EXPECTED_GLOBAL_SHA}


def candidate_files() -> tuple[list[Path], dict[str, int]]:
    selected: list[Path] = []
    excluded = {"transient": 0, "binary_reference_only": 0, "unsupported": 0,
                "cache": 0, "oversized_terminal_report_reference_only": 0,
                "oversized_native_snapshot_reference_only": 0,
                "generated_tree_pruned": 0, "reparse_point_pruned": 0,
                "reparse_file_skipped": 0}
    for relative_root in COPY_ROOTS:
        root = G / relative_root
        if not root.is_dir():
            raise RuntimeError(f"checkpoint source root is absent: {root}")
        for path in walk_files_bounded(root, excluded):
            # attempt-03 review.json is a large diagnostic bundle. Its full SHA,
            # size, terminal summary, and readsets are recorded in the manifest.
            if path.resolve() == ATTEMPT_REPORT.resolve():
                excluded["oversized_terminal_report_reference_only"] += 1
                continue
            if "__pycache__" in path.parts or path.suffix.lower() == ".pyc":
                excluded["cache"] += 1
                continue
            if path.name in TRANSIENT_NAMES or path.name.endswith((".tmp", ".lock")):
                excluded["transient"] += 1
                continue
            if path.suffix.lower() in {".npz", ".pbo", ".wrp"}:
                excluded["binary_reference_only"] += 1
                continue
            if path.suffix.lower() not in COPY_SUFFIXES:
                excluded["unsupported"] += 1
                continue
            if path.suffix.lower() == ".jsonl" and path.name not in JSONL_EVIDENCE_NAMES:
                excluded["transient"] += 1
                continue
            if path.stat().st_size > MAX_COPY_FILE_BYTES:
                if path.resolve() == NATIVE_SNAPSHOT.resolve():
                    excluded["oversized_native_snapshot_reference_only"] += 1
                    continue
                raise RuntimeError(f"evidence file exceeds copy bound; classify it explicitly: {path}")
            selected.append(path.resolve())
    if not SCOPE_NOTE.is_file():
        raise RuntimeError(f"checkpoint scope note is missing: {SCOPE_NOTE}")
    selected.extend((SCOPE_NOTE.resolve(), Path(__file__).resolve()))
    required_preserved = (
        BUILD_SELECTED / "preserved-before-native-verifier-pin/prepare_probe.py",
        BUILD_SELECTED / "preserved-before-native-verifier-pin/prepare-probe-run.log",
        BUILD_SELECTED / "preserved-before-nan-metadata/prepare_probe.py",
        BUILD_SELECTED / "preserved-before-nan-metadata/stage.py",
        BUILD_SELECTED / "preserved-before-nan-metadata/stage.log",
    )
    missing_preserved = [path for path in required_preserved if path.resolve() not in selected]
    if missing_preserved:
        raise RuntimeError(f"preserved verifier-pin/NaN failure evidence is missing from checkpoint selection: {missing_preserved}")
    selected = sorted(set(selected), key=lambda p: str(p).casefold())
    return selected, excluded


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        item = json.loads(line)
        if isinstance(item, dict):
            yield item
        else:
            raise ValueError(f"expected JSON object at {path}:{line_no}")


def collect_readsets(path: Path, value: Any, output: list[dict[str, str]]) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in READSET_KEYS and isinstance(nested, dict):
                for raw_path, digest in nested.items():
                    if isinstance(raw_path, str) and isinstance(digest, str) and len(digest) == SHA_LENGTH:
                        output.append({"owner": str(path), "set": key,
                                       "path": str(resolve_reference(raw_path, path)),
                                       "pinned_sha256": digest.lower()})
            collect_readsets(path, nested, output)
    elif isinstance(value, list):
        for nested in value:
            collect_readsets(path, nested, output)


def compact_terminal_summary(terminal: dict[str, Any]) -> dict[str, Any]:
    """Keep the terminal verdict and bounded soil/wet-support diagnostics in the manifest."""
    report = terminal["report"]
    info = report.get("information", {})
    gates = report.get("gates", {})
    global_contract = info.get("global_contract", {})
    wet = global_contract.get("eligible_wet_support_diagnostic", {})
    families = wet.get("hinges_by_family", {})

    def pair_stats(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        return {key: value.get(key) for key in ("n", "mean_square", "p99", "max", "above30")
                if key in value}

    family_summary = {}
    if isinstance(families, dict):
        for family in ("diag", "horizontal", "vertical"):
            item = families.get(family, {})
            if isinstance(item, dict):
                family_summary[family] = {side: pair_stats(item.get(side)) for side in ("B", "H")}

    geometry = global_contract.get("global_geometry", {})
    high_floor = global_contract.get("high_bed_floor", {})
    corridor = global_contract.get("corridor_depth", {})
    compiled = global_contract.get("compiled_coverage", {})
    expected = info.get("input_hashes_expected", {})
    false_gates = sorted(key for key, value in gates.items() if value is not True) if isinstance(gates, dict) else []
    return {
        "status": terminal["status"],
        "report_sha256": terminal["report_sha256"],
        "gate_count": len(gates) if isinstance(gates, dict) else None,
        "false_gates": false_gates,
        "identity": {
            "selection_sha256": info.get("selection_sha256"),
            "candidate_path": info.get("candidate_path"),
            "candidate_sha256": info.get("candidate_sha256"),
            "consumer_source_path": info.get("consumer_source_path"),
            "consumer_source_sha256": info.get("consumer_source_sha256"),
        },
        "readset": {
            "count": len(expected) if isinstance(expected, dict) else None,
            "expected_equals_start_equals_end": (
                isinstance(expected, dict) and expected == info.get("input_hashes_start")
                and expected == info.get("input_hashes_end")),
        },
        "counts": {key: info.get(key) for key in (
            "pool_units", "retained_units", "retained_legacy_units", "retained_crest_units",
            "policy_rejected_targets", "changed_vertices", "changed_support_cells")},
        "global_contract_status": info.get("global_contract_status"),
        "source_global_status_is_ancestry_diagnostic": info.get("source_global_status"),
        "global_geometry": {key: geometry.get(key) for key in (
            "affected_sector_count", "affected_sector_max_nonworse", "new_over30_count_touched",
            "no_new_hinges_over_30_touched", "slope_violation_count_global", "slopes_le_max35_or_B")},
        "high_bed_floor": {key: high_floor.get(key) for key in (
            "baseline_below_1m", "candidate_below_1m", "scope_vertices", "high_bed_floor_1m_pass")},
        "corridor_depth": {side: {key: corridor.get(side, {}).get(key) for key in (
            "feature_count", "global_minimum_nominal_depth_m", "meets_0_95_everywhere")}
            for side in ("B", "H")},
        "compiled_coverage_gates": compiled.get("gates", {}),
        "eligible_wet_support_diagnostic_only": {
            "diagnostic_only": wet.get("diagnostic_only"),
            "scope": wet.get("scope"),
            "eligible_wet_support_nodes": wet.get("eligible_wet_support_nodes"),
            "B": pair_stats(wet.get("B")),
            "H": pair_stats(wet.get("H")),
            "B_bracket_counts": wet.get("B_bracket_counts"),
            "H_bracket_counts": wet.get("H_bracket_counts"),
            "above30_nonworse": wet.get("above30_nonworse"),
            "bracket_counts_nonworse": wet.get("bracket_counts_nonworse"),
            "no_new_over30": wet.get("no_new_over30"),
            "new_over30_count": wet.get("new_over30_count"),
            "hinges_by_family": family_summary,
        },
    }


def collect_binary_references(files: list[Path], readsets: list[dict[str, Any]],
                              terminal: dict[str, Any]) -> list[dict[str, Any]]:
    refs: dict[str, dict[str, Any]] = {}

    def add(path: Path, pinned: str | None = None, owner: str | None = None,
            strict: bool = False) -> None:
        key = str(path.resolve()).casefold()
        entry = refs.setdefault(key, {"path": str(path.resolve()), "kind": path.suffix.lower().lstrip("."),
                                      "copied": False, "pinned_sha256": [],
                                      "strict_pinned_sha256": [], "pin_owners": []})
        if pinned and pinned.lower() not in entry["pinned_sha256"]:
            entry["pinned_sha256"].append(pinned.lower())
        if pinned and strict and pinned.lower() not in entry["strict_pinned_sha256"]:
            entry["strict_pinned_sha256"].append(pinned.lower())
        if owner:
            record = {"owner": owner, "sha256": pinned.lower() if pinned else None, "strict": strict}
            if record not in entry["pin_owners"]:
                entry["pin_owners"].append(record)

    walk_excluded: dict[str, int] = {"generated_tree_pruned": 0, "reparse_point_pruned": 0,
                                    "reparse_file_skipped": 0}
    for relative_root in COPY_ROOTS:
        for path in walk_files_bounded(G / relative_root, walk_excluded):
            if path.suffix.lower() in {".npz", ".pbo", ".wrp"}:
                add(path)
    for item in readsets:
        path = Path(item["path"])
        if path.suffix.lower() in {".npz", ".pbo", ".wrp"}:
            add(path, item["pinned_sha256"], item["owner"], bool(item.get("strict_current")))

    # Fixed B reference assets whose hashes are pinned by build-selected.
    explicit = (
        (EV82 / "candidate/terrain.npz", "f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0"),
        (EV82 / "package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp",
         "3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6"),
        (BASE_ADDONS / "narva_trial.pbo", "b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c"),
        (BASE_ADDONS / "baltic_water_v30.pbo", "3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14"),
    )
    for path, digest in explicit:
        add(path, digest, "build-selected pinned baseline", strict=True)
    candidate = terminal["selection"].get("candidate")
    if not isinstance(candidate, dict):
        raise RuntimeError("selected receipt has no candidate reference for the large-artifact manifest")
    candidate_path = resolve_reference(candidate.get("path", ""), SELECTION)
    if not candidate_path.is_file() or sha256(candidate_path) != candidate.get("sha256"):
        raise RuntimeError("selected candidate NPZ reference is absent or mismatched")
    if candidate_path.suffix.lower() != ".npz":
        raise RuntimeError("selected candidate is not the expected NPZ artifact")
    add(candidate_path, str(candidate["sha256"]), "run-02 selection candidate", strict=True)
    # The native readback was sampled from this exact selected candidate.
    native_ref = read_json(NATIVE_REFERENCE)
    native_candidate = BUILD_SELECTED / "candidate/terrain.npz"
    if not native_candidate.is_file() or sha256(native_candidate) != native_ref.get("terrain_sha256"):
        raise RuntimeError("native readback candidate reference is absent or mismatched")
    add(native_candidate, str(native_ref["terrain_sha256"]), "EV93 native readback candidate", strict=True)

    result = []
    for entry in refs.values():
        path = Path(entry["path"])
        entry["pinned_sha256"] = sorted(entry["pinned_sha256"])
        entry["strict_pinned_sha256"] = sorted(entry["strict_pinned_sha256"])
        entry["exists"] = path.is_file()
        entry["size_bytes"] = path.stat().st_size if path.is_file() else None
        entry["actual_sha256"] = sha256(path) if path.is_file() else None
        entry["pin_matches_actual"] = (None if not entry["pinned_sha256"] or not path.is_file()
                                       else all(x == entry["actual_sha256"] for x in entry["pinned_sha256"]))
        entry["strict_pin_matches_actual"] = (None if not entry["strict_pinned_sha256"] or not path.is_file()
                                               else all(x == entry["actual_sha256"] for x in entry["strict_pinned_sha256"]))
        result.append(entry)
    return sorted(result, key=lambda x: x["path"].casefold())


def create_checkpoint() -> Path:
    terminal = require_terminal_attempt()
    native = verify_native_evidence()
    files, excluded = candidate_files()
    readsets: list[dict[str, str]] = []
    # Preserve the readset references from the oversized report even though the
    # report payload itself is referenced by SHA rather than copied.
    collect_readsets(ATTEMPT_REPORT, terminal["report"], readsets)
    for path in files:
        if path.suffix.lower() == ".json":
            collect_readsets(path, read_json(path), readsets)
        elif path.suffix.lower() == ".jsonl":
            for row in read_jsonl(path):
                collect_readsets(path, row, readsets)
    # Deduplicate exact repeated references while retaining their evidence owners.
    dedup: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for item in readsets:
        key = (item["owner"], item["set"], item["path"].casefold(), item["pinned_sha256"])
        dedup[key] = item
    readsets = list(dedup.values())
    for item in readsets:
        path = Path(item["path"])
        item["exists"] = path.is_file()
        item["actual_sha256"] = sha256(path) if path.is_file() else None
        item["matches_current"] = bool(path.is_file() and item["actual_sha256"] == item["pinned_sha256"])
        owner_rel = str(Path(item["owner"]).resolve().relative_to(G))
        strict = owner_rel == str(SELECTION.relative_to(G)) or (
            owner_rel == str(ATTEMPT_REPORT.relative_to(G)) and terminal["status"] != "ERROR_COMPOUND_CONSUMER")
        item["strict_current"] = strict
        if strict and not item["matches_current"]:
            raise RuntimeError(f"strict current read-set reference is missing or drifted: {path}")

    binary_refs = collect_binary_references(files, readsets, terminal)
    for entry in binary_refs:
        if entry.get("strict_pinned_sha256") and not entry.get("exists"):
            raise RuntimeError(f"pinned large artifact reference is missing: {entry['path']}")
        if entry.get("strict_pinned_sha256") and entry.get("strict_pin_matches_actual") is False:
            raise RuntimeError(f"large artifact reference differs from its pinned SHA: {entry['path']}")
    compiled_wrp_member = {
        "path": str(BASE_ADDONS / "narva_trial.pbo") + "::baltic_trial.wrp",
        "kind": "wrp-member", "copied": False, "exists": (BASE_ADDONS / "narva_trial.pbo").is_file(),
        "size_bytes": None, "actual_sha256": None,
        "pinned_sha256": ["3b12b21d554c6ab75d76c43b5ba902c9a1d49a26516bdd14b16f1a6048ba2539"],
        "strict_pinned_sha256": ["3b12b21d554c6ab75d76c43b5ba902c9a1d49a26516bdd14b16f1a6048ba2539"],
        "member_sha_basis": "EV82 reference-inputs.json compiled_wrp_sha256; container PBO separately hashed",
        "container_path": str(BASE_ADDONS / "narva_trial.pbo"),
        "container_actual_sha256": sha256(BASE_ADDONS / "narva_trial.pbo"),
    }
    if not compiled_wrp_member["exists"]:
        raise RuntimeError("baseline world PBO for compiled WRP member reference is missing")
    binary_refs.append(compiled_wrp_member)
    binary_refs.sort(key=lambda x: x["path"].casefold())
    if not DEST.parent.is_dir():
        DEST.parent.mkdir(parents=True, exist_ok=True)
    if DEST.exists():
        raise FileExistsError(f"refusing to overwrite existing checkpoint: {DEST}")
    stale_staging = list(DEST.parent.glob(DEST.name + ".staging-*"))
    if stale_staging:
        raise FileExistsError(f"inspect previous incomplete checkpoint staging before retry: {stale_staging[0]}")
    staging = DEST.with_name(DEST.name + ".staging-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    if staging.exists():
        raise FileExistsError(f"refusing to overwrite staging path: {staging}")
    snapshot = staging / "source"
    snapshot.mkdir(parents=True)

    copied = []
    total_bytes = 0
    for source in files:
        try:
            relative = source.relative_to(G)
        except ValueError:
            if source == Path(__file__).resolve():
                relative = Path("checkpoint-script") / source.name
            else:
                raise
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        before = sha256(source)
        shutil.copy2(source, target)
        after = sha256(source)
        copied_sha = sha256(target)
        if before != after or before != copied_sha:
            raise RuntimeError(f"source changed during checkpoint copy: {source}")
        size = target.stat().st_size
        total_bytes += size
        copied.append({"source": str(source), "relative_path": str(relative),
                       "sha256": copied_sha, "size_bytes": size})

    manifest = {
        "schema": "ev93.selected-checkpoint.v1",
        "status": "CHECKPOINT_CREATED",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_root": str(G),
        "destination": str(DEST),
        "terminal_global_attempt": {
            "attempt_dir": str(ATTEMPT), "status": terminal["status"],
            "report_path": str(ATTEMPT_REPORT), "report_sha256": terminal["report_sha256"],
            "report_size_bytes": ATTEMPT_REPORT.stat().st_size,
            "report_payload_copied": False,
            "report_payload_reference_only_reason": "large diagnostic JSON; terminal summary and readsets are included in this manifest",
            "launch_path": str(ATTEMPT_LAUNCH), "launch_sha256": sha256(ATTEMPT_LAUNCH),
            "console_terminal_summary_sha256": sha256(ATTEMPT_CONSOLE),
            "selection_path": str(SELECTION), "selection_sha256": terminal["selection_sha256"],
            "global_source_path": str(GLOBAL_SOURCE), "global_source_sha256": terminal["global_source_sha256"],
        },
        "terminal_global_summary": compact_terminal_summary(terminal),
        "scope": {
            "included_roots": list(COPY_ROOTS),
            "excluded_roots": ["global-operator-prototype"],
            "excluded_root_reason": "active real-sector pilot has independent writers and a separate checkpoint",
            "pruned_build_selected_generated_trees": sorted(PRUNE_BUILD_SELECTED_TOP_LEVEL),
            "pruned_tree_reason": "candidate payloads, generated package/distribution trees, and native compiler intermediates are referenced by pinned receipts or excluded as build outputs",
            "does_not_wait_for_solver": True,
            "native_readback": "fresh EV93 server-only physical readback included; not a visual/render PASS",
            "preserved_failures": [
                "build-selected/preserved-before-native-verifier-pin",
                "build-selected/preserved-before-nan-metadata",
            ],
        },
        "native_readback": {
            "run_id": native["run_id"],
            "status": native["verification"]["status"],
            "capture_path": str(NATIVE_CAPTURE),
            "capture_sha256": sha256(NATIVE_CAPTURE),
            "provenance_path": str(NATIVE_PROVENANCE),
            "provenance_sha256": sha256(NATIVE_PROVENANCE),
            "reference_path": str(NATIVE_REFERENCE),
            "reference_sha256": sha256(NATIVE_REFERENCE),
            "verification_path": str(NATIVE_VERIFICATION),
            "verification_sha256": sha256(NATIVE_VERIFICATION),
            "snapshot_path": str(NATIVE_SNAPSHOT),
            "snapshot_sha256": sha256(NATIVE_SNAPSHOT),
            "snapshot_size_bytes": NATIVE_SNAPSHOT.stat().st_size,
            "snapshot_payload_copied": NATIVE_SNAPSHOT.stat().st_size <= MAX_COPY_FILE_BYTES,
            "snapshot_excerpt": (None if NATIVE_SNAPSHOT.stat().st_size <= MAX_COPY_FILE_BYTES
                                 else bounded_text_excerpt(NATIVE_SNAPSHOT)),
            "snapshot_reference_only_reason": (None if NATIVE_SNAPSHOT.stat().st_size <= MAX_COPY_FILE_BYTES
                                               else "runtime snapshot exceeds 32 MiB copy bound; SHA and bounded header/end excerpt retained"),
            "independent_review_path": str(NATIVE_REVIEW),
            "independent_review_sha256": sha256(NATIVE_REVIEW),
            "rpt_references": native["rpt_references"],
            "limits": ["No visual/render or server-client PASS is claimed."],
        },
        "copy_summary": {"file_count": len(copied), "bytes": total_bytes,
                         "estimated_mib": round(total_bytes / (1024 * 1024), 3),
                         "excluded_counts": excluded},
        "copied_files": copied,
        "readset_references": sorted(readsets, key=lambda x: (x["owner"].casefold(), x["set"], x["path"].casefold())),
        "large_artifact_references": binary_refs,
        "transient_policy": {
            "not_copied": ["progress.jsonl", "console.log", "__pycache__/*.pyc", "temporary/lock files",
                            "all NPZ/PBO/WRP payloads", "oversized attempt-03 review.json payload",
                            "native-snapshot.log payload if larger than 32 MiB; retain SHA, size, and bounded head/tail excerpt"],
            "terminal_report_sha_size_summary_and_readsets_are_in_manifest": True,
            "launch_receipts_are_copied": True,
            "binary_payloads_are_referenced_by_path_size_and_SHA_only": True,
            "runtime_rpt_payloads_are_referenced_by_path_size_and_SHA_only": True,
        },
    }
    manifest_path = staging / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
                             encoding="utf-8")
    # Re-read and verify every copied object before publishing the directory.
    for item in copied:
        target = snapshot / item["relative_path"]
        if not target.is_file() or sha256(target) != item["sha256"]:
            raise RuntimeError(f"checkpoint copy verification failed: {target}")
    os.replace(staging, DEST)
    return DEST


if __name__ == "__main__":
    print(create_checkpoint())
