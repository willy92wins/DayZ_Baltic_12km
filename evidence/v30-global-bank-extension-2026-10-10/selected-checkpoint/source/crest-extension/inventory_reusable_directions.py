from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

G = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010")
L = G / "fairing-layer1"
OUT = G / "crest-extension/reuse-source-inventory.json"
PREPARED = L / "prepared.json"
RECEIPT = L / "authoring.json"
LEDGER = L / "ledger.jsonl"
BASE = Path(r"E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz")
COMPOSITE = L / "candidate-terrain.npz"
VALIDATOR = G / "consumer-global/pre-symbol-fix/verify_layer.py"
VALIDATOR_SHA256 = "3338b42da8b20a7053676e244276ad8753174301641dd3cc01c1e78c9b744bea"
EXPECTED = {
    str(G / "author-stage-plan.md"): "2bc641c0ec88954e83a2d10f5a2542357ac8cdc6533456b466e4e71f90df504c",
    str(PREPARED): "765c5a5a778132fce7f1c1d21a59c1220b62443b180238e13ee51a203b3483d4",
    str(RECEIPT): "97165c9a3fe6ec052d8458a636be2fc9d13c6b87b05ce4491ae5123d13ea3c92",
    str(LEDGER): "dc0a26cc38f55c1a8bb5709e36cfacd41859c3f901aabed15968a56c44832e85",
    str(BASE): "f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0",
    str(COMPOSITE): "37e6d4bd195ee8576bc483a6c24e89cede536d916c2b041d8a6bdc98b13269f3",
    str(VALIDATOR): VALIDATOR_SHA256,
}
TARGET_REASON = "final gate scalar interpolation rule unavailable: baseline focus is not prominent on both axes"
EXPECTED_TARGETS = 228
EXPECTED_QUEUE = 703


def sha(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path | str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def array_exact(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.dtype != b.dtype or a.shape != b.shape:
        return False
    if np.issubdtype(a.dtype, np.inexact):
        return bool(np.array_equal(a, b, equal_nan=True))
    return bool(np.array_equal(a, b))


def np_scalar(a):
    a = np.asarray(a)
    if a.size != 1:
        raise AssertionError(f"expected one-element scalar array, got shape={a.shape}")
    return a.reshape(-1)[0].item()


def np_ascii(a):
    return bytes(np.asarray(a, dtype=np.uint8).reshape(-1)).decode("ascii")


def load_module(name: str, path: Path, expected_sha: str):
    actual = sha(path)
    if actual != expected_sha:
        raise AssertionError(f"frozen validator SHA mismatch: {actual} != {expected_sha}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import frozen validator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def select_exact_direction_targets(events, result_by_qid, prepared_by_qid):
    """Select only the exact baseline-prominence rejection, fail-closed on its provenance."""
    selected = []
    for event in events:
        if event.get("event") != "result":
            continue
        qid = int(event["queue_id"])
        result = result_by_qid[qid]
        prepared = prepared_by_qid[qid]
        exact = (event.get("state") == "rejected" and result.get("state") == "rejected"
                 and result.get("reason") == TARGET_REASON)
        if not exact:
            continue
        if int(result.get("solve_calls", -1)) != 1:
            raise AssertionError(f"target q{qid} has no single certified prior solve")
        if result.get("preflight_state") not in {"READY", "PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW"}:
            raise AssertionError(f"target q{qid} was not READY in original preflight")
        for key in ("queue_id", "seed_id", "center_rc"):
            if result.get(key) != prepared.get(key):
                raise AssertionError(f"target q{qid} {key} differs across result/prepared")
            # The terminal ledger schema carries queue_id/state/result pins; seed and
            # center are anchored by the prepared row and result JSON, not duplicated.
            if key in event and event.get(key) != prepared.get(key):
                raise AssertionError(f"target q{qid} ledger {key} conflicts with prepared row")
        if not result.get("solution_path") or not result.get("solution_sha256"):
            raise AssertionError(f"target q{qid} has no reusable solution artifact pin")
        selected.append((qid, event, result, prepared))
    return selected


def target_fixture():
    p = {"queue_id": 4, "seed_id": 8, "center_rc": [10, 12], "preflight_state": "READY"}
    ev = {"event": "result", "queue_id": 4, "seed_id": 8, "center_rc": [10, 12], "state": "rejected"}
    good = {**ev, "reason": TARGET_REASON, "solve_calls": 1, "solution_path": "s.npz", "solution_sha256": "a"*64,
            "preflight_state": "READY"}
    selected = select_exact_direction_targets([ev], {4:good}, {4:p})
    assert len(selected) == 1 and selected[0][0] == 4
    other = {**good, "reason": "different rejection"}
    assert select_exact_direction_targets([ev], {4:other}, {4:p}) == []
    bad = {**good, "solve_calls": 0}
    try:
        select_exact_direction_targets([ev], {4:bad}, {4:p})
    except AssertionError:
        pass
    else:
        raise AssertionError("target without a prior solve was accepted")
    return {"exact_reason_selected":True, "other_reason_excluded":True, "uncertified_solve_rejected":True}


def verify_marker(result, qid: int, prepared_sha: str):
    marker_path = Path(result["attempt_marker_path"])
    if not marker_path.is_file() or sha(marker_path) != result.get("attempt_marker_sha256"):
        raise AssertionError(f"attempt marker absent/stale q{qid}")
    marker = load_json(marker_path)
    if marker.get("queue_id") != qid or marker.get("prepared_sha256") != prepared_sha:
        raise AssertionError(f"attempt marker identity mismatch q{qid}")
    return marker_path


def scan_sources() -> dict:
    start_paths = dict(EXPECTED)
    for path, expected in EXPECTED.items():
        if sha(path) != expected.lower():
            raise AssertionError(f"source pin mismatch {path}")
    prepared = load_json(PREPARED)
    receipt = load_json(RECEIPT)
    if prepared.get("status") != "PREPARED_NO_SOLVE" or len(prepared.get("entries", [])) != EXPECTED_QUEUE:
        raise AssertionError("source prepared queue is not the frozen 703-row EV93 queue")
    if (receipt.get("status") != "AUTHORED_PENDING_GLOBAL_CONSUMER"
        or receipt.get("candidate_sha256") != EXPECTED[str(COMPOSITE)]
        or Path(receipt.get("candidate_path", "")).resolve() != COMPOSITE.resolve()):
        raise AssertionError("source layer receipt is not the pinned complete pending-consumer artifact")
    if receipt.get("prepared_sha256") != sha(PREPARED) or receipt.get("ledger_sha256") != sha(LEDGER):
        raise AssertionError("receipt does not pin the source prepared/ledger artifacts")
    if prepared.get("source_pins") != receipt.get("source_pins"):
        raise AssertionError("prepared and receipt source pins differ")
    for p, digest in prepared["source_pins"].items():
        start_paths[p] = digest
        if sha(p) != digest:
            raise AssertionError(f"prepared source pin mismatch: {p}")

    rows = prepared["entries"]
    if [int(x["queue_id"]) for x in rows] != list(range(EXPECTED_QUEUE)):
        raise AssertionError("prepared queue IDs are not complete and ordered")
    prepared_by_qid = {int(x["queue_id"]):x for x in rows}
    events = [json.loads(x) for x in LEDGER.read_text(encoding="utf-8").splitlines() if x.strip()]
    validator = load_module("crest_frozen_layer_validator", VALIDATOR, VALIDATOR_SHA256)
    terminal_rows = validator.validate_author_ledger_history(events, range(EXPECTED_QUEUE), sha(PREPARED))
    if len(terminal_rows) != EXPECTED_QUEUE:
        raise AssertionError("terminal ledger does not classify the complete queue")

    result_by_qid = {}
    result_inputs = {}
    for event in terminal_rows:
        qid = int(event["queue_id"])
        result_path = Path(event["result_path"])
        actual = sha(result_path)
        if actual != event.get("result_sha256"):
            raise AssertionError(f"result file SHA mismatch q{qid}")
        d = load_json(result_path)
        if d.get("queue_id") != qid or d.get("prepared_sha256") != sha(PREPARED):
            raise AssertionError(f"result identity mismatch q{qid}")
        if d.get("state") != event.get("state"):
            raise AssertionError(f"ledger/result state mismatch q{qid}")
        for key in ("seed_id", "center_rc"):
            if d.get(key) != prepared_by_qid[qid].get(key):
                raise AssertionError(f"result/prepared {key} mismatch q{qid}")
            if key in event and event.get(key) != prepared_by_qid[qid].get(key):
                raise AssertionError(f"ledger/prepared {key} mismatch q{qid}")
        result_by_qid[qid] = d
        result_inputs[str(result_path.resolve())] = actual

    actual_counts = {state:sum(x.get("state")==state for x in terminal_rows)
                     for state in ("accepted","rejected","inconclusive","not_authored","timeout","error")}
    if receipt.get("result_counts") != actual_counts:
        raise AssertionError("receipt state counts disagree with full terminal ledger")
    selected = select_exact_direction_targets(terminal_rows, result_by_qid, prepared_by_qid)
    if len(selected) != EXPECTED_TARGETS:
        raise AssertionError(f"exact reusable direction count changed: {len(selected)} != {EXPECTED_TARGETS}")

    with np.load(BASE, allow_pickle=False) as z:
        base_npz = {k:z[k] for k in z.files}
    with np.load(COMPOSITE, allow_pickle=False) as z:
        composite_npz = {k:z[k] for k in z.files}
    if set(base_npz) != set(composite_npz) or base_npz["heights"].dtype != np.float32:
        raise AssertionError("B/composite NPZ schemas or height dtype differ")
    for key in base_npz:
        if key != "heights" and not array_exact(base_npz[key], composite_npz[key]):
            raise AssertionError(f"original 340-delta composite changed non-height array {key}")
    base = np.asarray(base_npz["heights"], dtype=np.float32)
    composite = np.asarray(composite_npz["heights"], dtype=np.float32)
    if base.shape != (2048,2048) or composite.shape != base.shape:
        raise AssertionError("B or source composite height grid shape mismatch")
    changed_original = np.argwhere(composite != base)
    if len(changed_original) != receipt.get("changed_vertices"):
        raise AssertionError("source composite changed-vertex count differs from author receipt")

    accepted_nodes = set()
    accepted_artifact_inputs = {}
    accepted_count = 0
    accepted_mutable_count = 0
    for event in terminal_rows:
        if event.get("state") != "accepted":
            continue
        qid = int(event["queue_id"]); d = result_by_qid[qid]
        path = Path(d["solution_path"])
        digest = sha(path)
        if digest != d.get("solution_sha256"):
            raise AssertionError(f"accepted solution artifact SHA mismatch q{qid}")
        accepted_artifact_inputs[str(path.resolve())] = digest
        with np.load(path, allow_pickle=False) as z:
            if int(np_scalar(z["queue_id"])) != qid or np_ascii(z["prepared_sha256"]) != sha(PREPARED):
                raise AssertionError(f"accepted solution artifact identity mismatch q{qid}")
            nodes = np.asarray(z["variables_rc"], dtype=np.int32)
        local = [tuple(map(int,x)) for x in nodes.tolist()]
        accepted_mutable_count += len(local)
        if len(local) != len(set(local)):
            raise AssertionError(f"duplicate mutable node within accepted q{qid}")
        overlap = accepted_nodes.intersection(local)
        if overlap:
            raise AssertionError(f"accepted source windows overlap in mutable nodes, first={min(overlap)}")
        accepted_nodes.update(local); accepted_count += 1

    validator_base = np.asarray(base,dtype=np.float32)
    target_nodes = set(); target_nonzero = set(); target_pairs = []
    target_artifact_inputs = {}
    active_axis_counts = Counter()
    records = []
    for qid, event, d, entry in selected:
        result_path = Path(event["result_path"])
        result_sha = event["result_sha256"]
        solution_path = Path(d["solution_path"])
        solution_sha = sha(solution_path)
        target_artifact_inputs[str(solution_path.resolve())] = solution_sha
        marker_path = verify_marker(d,qid,sha(PREPARED))
        target_artifact_inputs[str(marker_path.resolve())] = sha(marker_path)
        nodes, stencils, direction = validator.validate_attempt_artifact(qid,d,validator_base)
        nodes = np.asarray(nodes,dtype=np.int32)
        direction = np.asarray(direction,dtype=np.float32)
        node_list = [tuple(map(int,x)) for x in nodes.tolist()]
        node_set = set(node_list)
        if len(node_set) != len(node_list):
            raise AssertionError(f"target variable list duplicates nodes q{qid}")
        if node_set & accepted_nodes:
            raise AssertionError(f"target q{qid} overlaps an accepted mutable domain")
        overlap_prior = target_nodes & node_set
        if overlap_prior:
            raise AssertionError(f"target windows overlap in mutable nodes at {min(overlap_prior)}")
        target_nodes.update(node_set); target_pairs.append(node_set)
        bvalues = base[tuple(nodes.T)]
        changed = direction != bvalues
        target_nonzero.update(tuple(map(int,x)) for x in nodes[changed].tolist())
        r,c = map(int,d["center_rc"])
        cardinal_rc = ((r,c),(r,c-1),(r,c+1),(r-1,c),(r+1,c))
        h_by_node = {tuple(map(int,n)):float(v) for n,v in zip(nodes.tolist(),direction.tolist())}
        base_cardinals = [float(base[rr,cc]) for rr,cc in cardinal_rc]
        dir_cardinals = [h_by_node.get((rr,cc),float(base[rr,cc])) for rr,cc in cardinal_rc]
        ew_active = base_cardinals[0] > max(base_cardinals[1],base_cardinals[2])
        ns_active = base_cardinals[0] > max(base_cardinals[3],base_cardinals[4])
        active_axis_counts[('EW' if ew_active else 'EW0') + ('+NS' if ns_active else '+NS0')] += 1
        records.append({
            "queue_id":qid,"seed_id":int(d["seed_id"]),"center_rc":[r,c],
            "reason":d["reason"],"preflight_state":d["preflight_state"],"solve_calls":1,
            "result_path":str(result_path.resolve()),"result_sha256":result_sha,
            "solution_path":str(solution_path.resolve()),"solution_sha256":solution_sha,
            "attempt_marker_path":str(marker_path.resolve()),"attempt_marker_sha256":sha(marker_path),
            "variables_count":len(nodes),"stencil_count":len(stencils),
            "direction_nonzero_node_count":int(np.count_nonzero(changed)),
            "direction_float32_le_sha256":hashlib.sha256(np.asarray(direction,dtype="<f4").tobytes()).hexdigest(),
            "base_cardinals_float32":[float(x) for x in base_cardinals],
            "direction_cardinals_float32":[float(x) for x in dir_cardinals],
            "active_axes":{"EW":bool(ew_active),"NS":bool(ns_active)},
            "stencil_set_sha256":hashlib.sha256(json.dumps(stencils,separators=(",",":"),ensure_ascii=False).encode("utf-8")).hexdigest(),
        })
    if accepted_count != 340:
        raise AssertionError(f"accepted source delta count changed: {accepted_count}")
    if len(target_nodes) != sum(len(s) for s in target_pairs) or len(accepted_nodes) != accepted_mutable_count:
        raise AssertionError("domain ownership set is not unique")

    input_hashes = dict(start_paths)
    input_hashes.update(result_inputs);input_hashes.update(accepted_artifact_inputs);input_hashes.update(target_artifact_inputs)
    end_hashes = {path:sha(path) for path in sorted(input_hashes)}
    if end_hashes != input_hashes:
        changed=[p for p in input_hashes if end_hashes.get(p)!=input_hashes[p]]
        raise AssertionError(f"source files changed during inventory: {changed[:10]}")
    return {
      "schema":"ev93.reused-direction-source-inventory.v1",
      "status":"REUSE_SOURCE_INVENTORY_READY",
      "source_pins":input_hashes,
      "expected_target_reason":TARGET_REASON,
      "target_count":len(records),"accepted_source_window_count":accepted_count,
      "target_mutable_node_union_count":len(target_nodes),
      "target_nonzero_direction_node_union_count":len(target_nonzero),
      "accepted_mutable_node_union_count":len(accepted_nodes),
      "original_composite_changed_vertex_count":len(changed_original),
      "domains_disjoint":{"targets_pairwise_mutable_nodes":True,"targets_vs_accepted_mutable_nodes":True,
                           "target_overlap_count":0,"accepted_overlap_count":0},
      "active_axis_distribution":dict(sorted(active_axis_counts.items())),
      "authored":False,"alpha_derived":False,"new_solver_calls":0,"candidate_written":False,
      "source_composite":{"path":str(COMPOSITE.resolve()),"sha256":sha(COMPOSITE),
                           "status":"preserve original 340 accepted deltas; this inventory does not modify them"},
      "reusable_directions":records,
    }


def run_self_test():
    result = target_fixture()
    assert result == {"exact_reason_selected":True,"other_reason_excluded":True,"uncertified_solve_rejected":True}
    return result


def main():
    ap=argparse.ArgumentParser(description="Read-only provenance inventory for exactly-rejected EV93 directions")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--output",type=Path,default=OUT)
    args=ap.parse_args()
    if args.self_test:
        print(json.dumps({"status":"FIXTURES_PASS","fixtures":run_self_test()},sort_keys=True));return
    report=scan_sources()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    tmp=args.output.with_suffix(args.output.suffix+".tmp")
    tmp.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    tmp.replace(args.output)
    print(json.dumps({"status":report["status"],"target_count":report["target_count"],
                      "target_nonzero_direction_node_union_count":report["target_nonzero_direction_node_union_count"],
                      "output":str(args.output.resolve()),"sha256":sha(args.output)},sort_keys=True))

if __name__=="__main__":
    main()
