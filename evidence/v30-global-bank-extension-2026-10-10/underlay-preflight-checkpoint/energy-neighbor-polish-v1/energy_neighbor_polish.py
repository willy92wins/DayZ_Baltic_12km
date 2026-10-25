from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

import numpy as np
import scipy

HERE = Path(__file__).resolve().parent
PLAN = HERE / "PLAN.md"
TESTS = HERE / "test_energy_neighbor_polish.py"
MODEL = HERE.parent / "candidate_model.py"
BASE_MODEL = HERE.parent / "lattice_milp.py"
CONVERTER = HERE.parents[3] / "convert_components.py"
EXECUTOR = HERE.parents[4] / "float32-neighborhood-v1" / "executor.py"
PRIOR_RECEIPT = HERE.parent / "real-run-01" / "receipt.json"
DIAGNOSTIC = HERE.parent / "real-run-01" / "rejected-diagnostic.npz"
OUT = HERE / "run-01"
WALL_SECONDS = 60.0
DIRECT_GATES = ("bounds", "PF_signs", "all_116_direct_crossings", "D8_direct", "face_cones")
EXACT_GATES = ("shape", "fixed", "bounds", "signs", "crossings", "d8")
EXPECTED = {
    "base_model": "2a62d1d73af6d71af97b60b5512787a653a3637d1c54f8eb001c9d905252e396",
    "candidate_model": "23186f47d70730d2f617c0635a7f37b68472d5f287b728811372ae7a47a9e244",
    "converter": "418016b91cfd84d60eb3f95c99cc043eea164de1afa2548f665d68d616aec876",
    "executor": "9a0dbffc55e9956209083fe4963e2636b6f0174de1dc150bdfa15f070d48149e",
    "prior_receipt": "f540fb0e8672886c8c70a2af7c8d6ae16c3698ce7d0392e97d9ccc2d50e00902",
    "diagnostic": "2209df7542098403ceda8e27e87c91935a9832527f04663fdf8f5d8ac70149ae",
    "tests": "7fc46c3b31576713e2f820a0dfa47a3764176f62bb23cbe43fa0934dc5e0480b",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_pinned(name: str, path: Path, expected: str):
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise RuntimeError(f"source pin mismatch before load: {path} {actual}")
    spec = importlib.util.spec_from_loader(name, loader=None, origin=str(path))
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), "exec"), module.__dict__)
    if sha256(path) != expected:
        raise RuntimeError(f"source drift after load: {path}")
    return module


def one_ulp_neighbors(grid, variables_rc):
    """Yield (row-major index, rc, signed step, copied grid) for exactly 2N neighbors."""
    base = np.asarray(grid)
    if base.dtype != np.float32 or base.ndim != 2:
        raise ValueError("grid must be a 2-D float32 array")
    coords = [tuple(map(int, rc)) for rc in np.asarray(variables_rc)]
    if len(set(coords)) != len(coords):
        raise ValueError("variable coordinates must be unique")
    for i, (r, c) in enumerate(coords):
        if not (0 <= r < base.shape[0] and 0 <= c < base.shape[1]):
            raise ValueError(f"variable coordinate outside grid: {(r,c)}")
        current = np.float32(base[r, c])
        if not np.isfinite(current):
            raise ValueError(f"nonfinite source variable at {(r,c)}")
        for step, direction in ((-1, np.float32(-np.inf)), (1, np.float32(np.inf))):
            candidate = base.copy()
            candidate[r, c] = np.nextafter(current, direction, dtype=np.float32)
            yield i, (r, c), step, candidate


def rank_key(record):
    return (float(record["closed_cost"]), int(record["rc"][0]), int(record["rc"][1]), int(record["step"]))


def is_energy_eligible(raw_cost, closed_cost, baseline_cost):
    raw_cost = float(raw_cost)
    closed_cost = float(closed_cost)
    baseline_cost = float(baseline_cost)
    if not all(np.isfinite(v) for v in (raw_cost, closed_cost, baseline_cost)):
        return False, float("nan")
    allowance = 1e-7 * max(1.0, raw_cost)
    return bool(closed_cost - raw_cost <= allowance and closed_cost < baseline_cost), allowance


def candidate_is_eligible(record):
    if not bool(record.get("exact_rows_pass")):
        return False
    exact = record.get("exact_fraction_gates", {})
    direct = record.get("direct_gates", {})
    if not all(exact.get(k) is True for k in EXACT_GATES):
        return False
    if not all(direct.get(k) is True for k in DIRECT_GATES):
        return False
    return bool(record.get("energy_gate"))


def choose_best(records):
    eligible = [r for r in records if candidate_is_eligible(r)]
    return min(eligible, key=rank_key) if eligible else None


def lattice_vector_for_grid(model_wrapper, grid):
    base_mod = model_wrapper.base_module
    lattice = model_wrapper.model
    out = np.empty(len(lattice.variables_rc), dtype=np.int64)
    for i, rc in enumerate(lattice.variables_rc):
        delta = base_mod.frac_f32(np.float32(grid[rc])) - base_mod.frac_f32(lattice.baseline[i])
        units = delta / lattice.quantum
        if units.denominator != 1:
            raise ValueError(f"one-ULP neighbor is outside common lattice at variable {i}: {units}")
        out[i] = int(units)
    return out


def evaluate_grid(model_wrapper, executor, data, grid, raw_cost_expected, baseline_cost_expected):
    exact = {k: bool(v) for k, v in model_wrapper.model.exact_gates(grid).items()}
    m = lattice_vector_for_grid(model_wrapper, grid)
    try:
        rows_pass, row_failures = model_wrapper.exact_rows_pass(m)
    except model_wrapper.base_module.ModelError as exc:
        if "lattice value outside segments" not in str(exc):
            raise
        rows_pass, row_failures = False, [{"name": "outside_float32_domain_segments", "detail": str(exc)}]
    direct = executor.eval_gates(data, grid)
    direct_gates = {k: bool(direct[k]) for k in (*DIRECT_GATES, "closure_energy_and_improvement")}
    raw_cost = float(direct["raw_cost"])
    closed_cost = float(direct["closed_cost"])
    baseline_cost = float(direct["baseline_cost"])
    if raw_cost != float(raw_cost_expected) or baseline_cost != float(baseline_cost_expected):
        raise RuntimeError("pinned raw/baseline objective differs from source diagnostic")
    energy_pass, allowance = is_energy_eligible(raw_cost, closed_cost, baseline_cost)
    if bool(direct["closure_energy_and_improvement"]) != energy_pass:
        raise RuntimeError("local energy formula disagrees with frozen executor gate")
    return {
        "exact_rows_pass": bool(rows_pass), "exact_row_failure_count": len(row_failures),
        "first_exact_row_failures": row_failures[:5], "exact_fraction_gates": exact,
        "direct_gates": direct_gates, "raw_cost": raw_cost, "closed_cost": closed_cost,
        "baseline_cost": baseline_cost, "allowance": float(allowance),
        "energy_gate": bool(energy_pass),
    }


def enumerate_neighbors(grid, variables_rc, evaluator, deadline, on_record=None):
    records = []
    best = None
    best_grid = None
    expected = 2 * len(variables_rc)
    for number, (index, rc, step, candidate) in enumerate(one_ulp_neighbors(grid, variables_rc), start=1):
        if time.monotonic() > deadline:
            raise TimeoutError(f"60-second neighbor budget expired after {number-1}/{expected} checks")
        record = {"variable_index": int(index), "rc": list(rc), "step": int(step),
                  "height_float32": float(candidate[rc]), **evaluator(candidate)}
        record["eligible"] = candidate_is_eligible(record)
        records.append(record)
        if on_record is not None:
            on_record(record)
        if record["eligible"] and (best is None or rank_key(record) < rank_key(best)):
            best = record
            best_grid = candidate
    if len(records) != expected:
        raise AssertionError(f"expected {expected} one-ULP neighbors, evaluated {len(records)}")
    # Recompute from the same records as an internal consistency check.
    chosen = choose_best(records)
    if (None if chosen is None else (chosen["variable_index"], chosen["rc"], chosen["step"])) != \
       (None if best is None else (best["variable_index"], best["rc"], best["step"])):
        raise AssertionError("streaming best candidate disagrees with deterministic record ranking")
    return records, best, best_grid


def json_safe(value):
    if isinstance(value, dict): return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [json_safe(v) for v in value]
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.bool_, bool)): return bool(value)
    if isinstance(value, (np.floating, float)):
        f = float(value)
        if np.isnan(f): return {"nonfinite": "nan"}
        if np.isposinf(f): return {"nonfinite": "positive_infinity"}
        if np.isneginf(f): return {"nonfinite": "negative_infinity"}
        return f
    return value


def atomic_json(path: Path, payload):
    temp = path.with_name(path.name + f".{os.getpid()}.tmp")
    temp.write_text(json.dumps(json_safe(payload), sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def sha_map(paths):
    return {str(Path(p).resolve()): sha256(Path(p)) for p in paths}


def validate_prior_receipt(prior, diagnostic_path: Path):
    """Check this is the preserved D8-fixed rejection whose sole failure is energy."""
    if prior.get("schema") != "candidate-only-f32-lattice.real-run.v1":
        raise RuntimeError("unexpected source receipt schema")
    if prior.get("status") != "REJECTED_EXACT_POSTGATES" or prior.get("accepted") is not False or prior.get("terrain_written") is not False:
        raise RuntimeError("source receipt is not the preserved rejected diagnostic")
    if prior.get("solver_invoked") is not True:
        raise RuntimeError("source receipt does not identify the completed MILP run")
    if prior.get("exact_fraction_rows_pass") is not True:
        raise RuntimeError("source diagnostic failed exact Fraction rows")
    if any(value is not True for value in prior.get("exact_fraction_gates", {}).values()):
        raise RuntimeError("source diagnostic has a failed exact Fraction gate")
    direct = prior.get("direct_executor_gates", {})
    if direct.get("closure_energy_and_improvement") is not False:
        raise RuntimeError("source diagnostic is not the energy-only rejected case")
    if any(value is not True for key, value in direct.items() if key != "closure_energy_and_improvement"):
        raise RuntimeError("source diagnostic has a non-energy direct-gate failure")
    metrics = prior.get("direct_executor_metrics", {})
    raw = metrics.get("raw_cost")
    closed = metrics.get("closed_cost")
    baseline = metrics.get("baseline_cost")
    allowance = metrics.get("closure_allowance")
    if not all(isinstance(v, (int, float)) and np.isfinite(v) for v in (raw, closed, baseline, allowance)):
        raise RuntimeError("source receipt energy metrics are missing or nonfinite")
    if not (closed - raw > allowance and closed < baseline):
        raise RuntimeError("source receipt does not show only a closure-energy allowance miss")
    diag_meta = prior.get("rejected_diagnostic", {})
    if (diag_meta.get("accepted") is not False or diag_meta.get("terrain_written") is not False
            or Path(diag_meta.get("path", "")).resolve() != diagnostic_path.resolve()
            or diag_meta.get("sha256") != EXPECTED["diagnostic"]):
        raise RuntimeError("diagnostic artifact is not linked as the preserved unaccepted input")
    return {"raw_cost": float(raw), "closed_cost": float(closed),
            "baseline_cost": float(baseline), "allowance": float(allowance)}


def validate_static_preflight(approved_script_sha: str, approved_plan_sha: str):
    """Read-only source/receipt pin check; does not load the problem or enumerate neighbors."""
    if sha256(Path(__file__)) != approved_script_sha.lower():
        raise RuntimeError("approved script SHA does not match live source")
    if sha256(PLAN) != approved_plan_sha.lower():
        raise RuntimeError("approved plan SHA does not match live plan")
    expected_static = {TESTS: EXPECTED["tests"], MODEL: EXPECTED["candidate_model"],
        BASE_MODEL: EXPECTED["base_model"], CONVERTER: EXPECTED["converter"],
        EXECUTOR: EXPECTED["executor"], PRIOR_RECEIPT: EXPECTED["prior_receipt"],
        DIAGNOSTIC: EXPECTED["diagnostic"]}
    for path, expected in expected_static.items():
        if sha256(path) != expected:
            raise RuntimeError(f"pinned input changed: {path}")
    prior = json.loads(PRIOR_RECEIPT.read_text(encoding="utf-8"))
    energy = validate_prior_receipt(prior, DIAGNOSTIC)
    return {"status": "STATIC_PINS_AND_ENERGY_ONLY_RECEIPT_PASS",
        "script_sha256": sha256(Path(__file__)), "plan_sha256": sha256(PLAN),
        "prior_receipt_sha256": sha256(PRIOR_RECEIPT),
        "diagnostic_sha256": sha256(DIAGNOSTIC), "energy_metrics": energy,
        "problem_loaded": False, "neighbors_enumerated": False, "solver_calls": 0}


def prepare_real_inputs():
    static_paths = (Path(__file__).resolve(), PLAN, TESTS, MODEL, BASE_MODEL, CONVERTER,
                    EXECUTOR, PRIOR_RECEIPT, DIAGNOSTIC)
    expected_static = {TESTS: EXPECTED["tests"], MODEL: EXPECTED["candidate_model"], BASE_MODEL: EXPECTED["base_model"],
                       CONVERTER: EXPECTED["converter"], EXECUTOR: EXPECTED["executor"],
                       PRIOR_RECEIPT: EXPECTED["prior_receipt"], DIAGNOSTIC: EXPECTED["diagnostic"]}
    for path, expected in expected_static.items():
        if sha256(path) != expected:
            raise RuntimeError(f"pinned input changed: {path}")
    prior = json.loads(PRIOR_RECEIPT.read_text(encoding="utf-8"))
    validate_prior_receipt(prior, DIAGNOSTIC)
    base = load_pinned("energy_polish_base", BASE_MODEL, EXPECTED["base_model"])
    executor = load_pinned("energy_polish_executor", EXECUTOR, EXPECTED["executor"])
    converter = load_pinned("energy_polish_converter", CONVERTER, EXPECTED["converter"])
    candidate_model = load_pinned("energy_polish_candidate_model", MODEL, EXPECTED["candidate_model"])
    candidate_model._energy_polish_solver_calls = 0
    def forbid_solver_call(*_args, **_kwargs):
        candidate_model._energy_polish_solver_calls += 1
        raise RuntimeError("solver invocation is forbidden in neighbor-polish evaluation")
    candidate_model.milp = forbid_solver_call
    # Pin all existing data inputs before the real problem loader reads them.
    for path, expected in prior.get("input_readset_start", {}).items():
        if sha256(Path(path)) != expected:
            raise RuntimeError(f"pinned diagnostic input changed: {path}")
    converter.load_executor = lambda: executor
    old_propagate = converter.propagate
    converter.propagate = lambda domains, relations, subset=None: (dict(domains), {"variable": None, "trace": []})
    try:
        problem = converter._load_real_problem(time.monotonic() + WALL_SECONDS)
    finally:
        converter.propagate = old_propagate
    data = problem["data"]
    if data.get("source_start") != prior.get("input_readset_start"):
        raise RuntimeError("reloaded source readset differs from the rejected diagnostic inputs")
    with np.load(DIAGNOSTIC, allow_pickle=False) as artifact:
        grid = artifact["context_grid"].copy()
        stored_m = artifact["lattice_m"].copy()
        stored_rc = artifact["variables_rc"].copy()
        stored_base = artifact["source_base_context"].copy()
    if grid.dtype != np.float32 or grid.shape != data["context"].shape:
        raise RuntimeError("diagnostic grid dtype/shape mismatch")
    if not np.array_equal(stored_base.view(np.uint32), np.asarray(data["context"], dtype=np.float32).view(np.uint32)):
        raise RuntimeError("diagnostic baseline context does not match loaded input")
    if not np.array_equal(stored_rc, np.asarray(problem["vars_rc"], dtype=np.int32)):
        raise RuntimeError("diagnostic variable coordinate list differs from current prepared problem")
    if stored_m.shape != (121,) or stored_m.dtype != np.int64:
        raise RuntimeError("diagnostic lattice vector must be 121 int64 values")
    if len(problem["vars_local"]) != 121:
        raise RuntimeError(f"expected 121 variables, got {len(problem['vars_local'])}")
    raw_only = []
    other_singletons = []
    for i, mask in problem["domains"].items():
        if int(mask).bit_count() == 1:
            (raw_only if int(mask) == (1 << 1) else other_singletons).append(int(i))
    if other_singletons or len(raw_only) != 2:
        raise RuntimeError(f"singleton contract changed: raw={raw_only}, other={other_singletons}")
    crossings = [base.Crossing(tuple(s.local_a), tuple(s.local_b), s.level_a, s.level_b,
                               int(s.dry_endpoint), s.t_lower, s.t_upper, str(s.key))
                 for s in data["cross_specs"]]
    signs = [base.Sign(tuple(s.local_rc), s.level, int(s.sign), s.baseline, str(s.surface))
             for s in data["sign_specs"]]
    witnesses = [((int(a), int(b)), (int(c), int(d)))
                 for a, b, c, d in np.asarray(data["witnesses"], dtype=np.int32)]
    wrapper = candidate_model.CandidateLatticeMILP(base, data["context"], problem["vars_local"],
        data["lo"], data["hi"], problem["x64"], crossings=crossings, signs=signs,
        d8_witnesses=witnesses, fixed_indices=raw_only)
    if not np.array_equal(wrapper.model.decode_f32(stored_m).view(np.uint32), grid.view(np.uint32)):
        raise RuntimeError("stored lattice vector does not reconstruct the rejected diagnostic grid")
    rows_ok, _ = wrapper.exact_rows_pass(stored_m)
    exact = wrapper.model.exact_gates(grid)
    direct = executor.eval_gates(data, grid)
    if not rows_ok or not all(bool(exact.get(k)) for k in EXACT_GATES):
        raise RuntimeError("starting diagnostic no longer passes exact rational gates")
    if not all(bool(direct[k]) for k in DIRECT_GATES):
        raise RuntimeError("starting diagnostic no longer passes non-energy direct gates")
    if bool(direct["closure_energy_and_improvement"]):
        raise RuntimeError("starting diagnostic unexpectedly passes energy gate")
    metrics = prior.get("direct_executor_metrics", {})
    for key in ("raw_cost", "closed_cost", "baseline_cost"):
        if float(metrics[key]) != float(direct[key]):
            raise RuntimeError(f"starting diagnostic {key} differs from preserved receipt")
    start = sha_map(static_paths)
    for path, expected in expected_static.items():
        if start[str(path.resolve())] != expected:
            raise RuntimeError(f"static input changed after load: {path}")
    expected_inputs = {str(Path(p).resolve()): h for p, h in prior["input_readset_start"].items()}
    for path, expected in expected_inputs.items():
        if sha256(Path(path)) != expected:
            raise RuntimeError(f"dynamic input drift at run start: {path}")
        start[path] = expected
    return {"static_paths": static_paths, "readset_start": start, "input_readset": expected_inputs,
            "prior": prior, "problem": problem, "data": data, "executor": executor,
            "wrapper": wrapper, "candidate_model_module": candidate_model, "grid": grid, "m": stored_m}


def run_enumeration(approved_script_sha: str, approved_plan_sha: str):
    if OUT.exists():
        raise FileExistsError(f"refuse overwrite/retry: {OUT}")
    if sha256(Path(__file__)) != approved_script_sha.lower():
        raise RuntimeError("approved script SHA mismatch")
    if sha256(PLAN) != approved_plan_sha.lower():
        raise RuntimeError("approved plan SHA mismatch")
    if scipy.__version__ != "1.18.1" or np.__version__ != "2.5.3":
        raise RuntimeError(f"numeric runtime changed: numpy={np.__version__} scipy={scipy.__version__}")
    OUT.mkdir(parents=False, exist_ok=False)
    start_time = time.monotonic()
    receipt = {"schema": "candidate-only-milp.energy-neighbor-polish.v1", "status": "ERROR",
               "solver_calls": 0, "accepted": False, "terrain_written": False,
               "approved_script_sha256": approved_script_sha.lower(), "approved_plan_sha256": approved_plan_sha.lower(),
               "output": str(OUT.resolve())}
    marker = OUT / "enumeration.started.json"
    try:
        marker.write_text(json.dumps({"pid": os.getpid(), "started_monotonic": time.monotonic(),
                                      "script_sha256": sha256(Path(__file__))}, sort_keys=True) + "\n", encoding="utf-8")
        real = prepare_real_inputs()
        if real["readset_start"].get(str(Path(__file__).resolve())) != approved_script_sha.lower():
            raise RuntimeError("script readset does not match the approved source SHA")
        if real["readset_start"].get(str(PLAN.resolve())) != approved_plan_sha.lower():
            raise RuntimeError("plan readset does not match the approved plan SHA")
        receipt["source_readset_start"] = real["readset_start"]
        grid = real["grid"]
        variables_local = real["problem"]["vars_local"]
        data, wrapper, executor = real["data"], real["wrapper"], real["executor"]
        raw_cost = float(real["prior"]["direct_executor_metrics"]["raw_cost"])
        baseline_cost = float(real["prior"]["direct_executor_metrics"]["baseline_cost"])
        deadline = start_time + WALL_SECONDS
        def evaluate(candidate):
            result = evaluate_grid(wrapper, executor, data, candidate, raw_cost, baseline_cost)
            result["direct_gates"]["closure_energy_and_improvement"] = bool(result["energy_gate"])
            return result
        log_path = OUT / "neighbors.jsonl"
        with log_path.open("x", encoding="utf-8", newline="\n") as stream:
            def append_record(record):
                line = json.dumps(json_safe(record), sort_keys=True, separators=(",", ":"), allow_nan=False)
                stream.write(line + "\n")
            records, best, best_grid = enumerate_neighbors(grid, variables_local, evaluate, deadline, append_record)
            stream.flush(); os.fsync(stream.fileno())
        if real["candidate_model_module"]._energy_polish_solver_calls != 0:
            raise RuntimeError("unexpected MILP call was intercepted")
        if time.monotonic() > deadline:
            raise TimeoutError("60-second total enumeration deadline exceeded")
        counts = Counter()
        for record in records:
            for key, passed in record["exact_fraction_gates"].items():
                if not passed: counts[f"exact:{key}"] += 1
            if not record["exact_rows_pass"]: counts["exact:rows"] += 1
            for key, passed in record["direct_gates"].items():
                if not passed: counts[f"direct:{key}"] += 1
        if best is None:
            status = "NO_FEASIBLE_ONE_ULP_NEIGHBOR"
        else:
            artifact_path = OUT / "polished-diagnostic.npz"
            temp_artifact = OUT / "polished-diagnostic.tmp.npz"
            with temp_artifact.open("xb") as stream:
                np.savez_compressed(stream, context_grid=best_grid,
                    source_rejected_grid=grid, variables_rc=np.asarray(real["problem"]["vars_rc"], dtype=np.int32),
                    source_lattice_m=np.asarray(real["m"], dtype=np.int64),
                    changed_variable_index=np.asarray(best["variable_index"], dtype=np.int32),
                    changed_step=np.asarray(best["step"], dtype=np.int8),
                    source_diagnostic_sha256=np.asarray(EXPECTED["diagnostic"]))
            os.replace(temp_artifact, artifact_path)
            receipt["polished_diagnostic"] = {"path": str(artifact_path.resolve()), "sha256": sha256(artifact_path),
                "accepted": False, "terrain_written": False, "changed_rc": best["rc"], "step": best["step"]}
            status = "DIAGNOSTIC_NEIGHBOR_UNACCEPTED"
        read_end = sha_map(real["static_paths"])
        for path, expected in real["input_readset"].items():
            actual = sha256(Path(path))
            if actual != expected: raise RuntimeError(f"input changed during enumeration: {path}")
            read_end[path] = actual
        if read_end != real["readset_start"]:
            raise RuntimeError("source readset drift during neighbor enumeration")
        receipt.update({"status": status, "accepted": False, "terrain_written": False,
            "solver_calls": 0, "neighbor_count": len(records), "expected_neighbor_count": 242,
            "eligible_neighbor_count": sum(bool(r["eligible"]) for r in records),
            "rejection_counts": dict(counts), "best_neighbor": best,
            "elapsed_seconds": time.monotonic() - start_time,
            "source_readset_end": read_end, "source_readset_stable": True,
            "ledger_path": str(log_path.resolve()), "ledger_sha256": sha256(log_path),
            "note": "one-node +/- one-ULP diagnostic only; not an accepted terrain candidate"})
        atomic_json(OUT / "receipt.json", receipt)
        return 0 if status == "DIAGNOSTIC_NEIGHBOR_UNACCEPTED" else 2
    except Exception as exc:
        receipt.update({"status": "ERROR", "accepted": False, "terrain_written": False,
            "solver_calls": 0, "error_type": type(exc).__name__, "error": str(exc),
            "traceback": traceback.format_exc(), "elapsed_seconds": time.monotonic() - start_time})
        partial_ledger = OUT / "neighbors.jsonl"
        if partial_ledger.exists():
            with partial_ledger.open("r", encoding="utf-8") as stream:
                line_count = sum(1 for _ in stream)
            receipt["partial_ledger"] = {"path": str(partial_ledger.resolve()),
                "sha256": sha256(partial_ledger), "lines": line_count}
        partial_artifact = OUT / "polished-diagnostic.npz"
        if partial_artifact.exists():
            receipt["polished_diagnostic"] = {"path": str(partial_artifact.resolve()),
                "sha256": sha256(partial_artifact), "accepted": False, "terrain_written": False}
        atomic_json(OUT / "receipt.json", receipt)
        return 3


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bounded one-ULP energy neighbor check; never calls a solver")
    parser.add_argument("--approved-script-sha", required=True)
    parser.add_argument("--approved-plan-sha", required=True)
    parser.add_argument("--preflight-only", action="store_true",
        help="validate pinned source and rejected energy-only receipt without loading the real problem")
    args = parser.parse_args(argv)
    if args.preflight_only:
        try:
            print(json.dumps(validate_static_preflight(args.approved_script_sha,
                args.approved_plan_sha), sort_keys=True, indent=2))
            return 0
        except Exception as exc:
            print(json.dumps({"status": "STATIC_PREFLIGHT_FAIL", "error_type": type(exc).__name__,
                "error": str(exc)}, sort_keys=True, indent=2))
            return 2
    return run_enumeration(args.approved_script_sha, args.approved_plan_sha)


if __name__ == "__main__":
    raise SystemExit(main())
