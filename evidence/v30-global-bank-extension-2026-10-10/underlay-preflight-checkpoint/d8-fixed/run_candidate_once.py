from __future__ import annotations

import argparse
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
MODEL = HERE / "candidate_model.py"
TESTS = HERE / "test_candidate_model.py"
RUNNER_TESTS = HERE / "test_candidate_runner.py"
CONTROL_SCRIPT = HERE / "check_baseline_control.py"
CONTROL = HERE / "baseline-control.json"
BASE_MODEL = HERE / "lattice_milp.py"
OLD_CONTROL = HERE / "baseline-matrix-control-v2.json"
AUDIT = HERE / "bounds-audit-v4.json"
CONVERTER = HERE.parents[2] / "convert_components.py"
EXECUTOR = HERE.parents[3] / "float32-neighborhood-v1" / "executor.py"
OUT = HERE / "real-run-01"
WALL_LIMIT_SECONDS = 60.0
NODE_LIMIT = 1_000_000
EXPECTED = {
    "plan": "ad1596d1735c938ec7e151f3fc82208b8c2f443e1aa342f21d8c05351e88e3ad",
    "base_model": "2a62d1d73af6d71af97b60b5512787a653a3637d1c54f8eb001c9d905252e396",
    "old_control": "360d2df34cb9f74d1a87f7cdf84eb245703da24b991ed8585a3b9b2c2309e7f5",
    "audit": "831e847292499bef38ebe76b2535b202359b0e0fa9e3b515a345ccf265cd1619",
    "converter": "418016b91cfd84d60eb3f95c99cc043eea164de1afa2548f665d68d616aec876",
    "executor": "9a0dbffc55e9956209083fe4963e2636b6f0174de1dc150bdfa15f070d48149e",
    "tests": "9c44ec86c53c09c8606eed9611149b118052f9519ad58aa2c58c270d2ce37f9d",
    "runner_tests": "558a68fa446dbadf130d1acb8239b5b9d48660ccccbe39311be11f42cd4732fa",
    "control_script": "feb34c291d545aee37d908d17a9f147cb8a830915a1298aef550265d720250ae",
    "control": "7cf95dd2061efaf6014ed09149388d171c4b6bc021ee2cefa111c2db2206d068",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
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
    if sha(path) != expected:
        raise RuntimeError(f"source drift after load: {path}")
    return module


def atomic_json(path: Path, payload):
    temp = path.with_name(path.name + f".{os.getpid()}.tmp")
    temp.write_text(json.dumps(json_safe(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        x = float(value)
        if np.isnan(x): return {"nonfinite": "nan"}
        if np.isposinf(x): return {"nonfinite": "positive_infinity"}
        if np.isneginf(x): return {"nonfinite": "negative_infinity"}
        return x
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value


def source_map(paths):
    return {str(Path(p).resolve()): sha(Path(p)) for p in paths}


def install_solver_invocation_tracker(model_module, receipt):
    """Set solver_invoked only on entry to the actual scipy milp callable."""
    actual_milp = model_module.milp
    calls = 0

    def tracked_milp(*args, **kwargs):
        nonlocal calls
        if calls:
            raise RuntimeError("candidate-only driver attempted more than one HiGHS call")
        calls += 1
        receipt["solver_invoked"] = True
        return actual_milp(*args, **kwargs)

    model_module.milp = tracked_milp
    return tracked_milp


def cleanup_candidate_after_error(out: Path, receipt):
    """Remove any partial/unaccepted local candidate and record verifiable evidence."""
    candidate = out / "candidate-context.npz"
    record = {"path": str(candidate.resolve()), "present_before_cleanup": candidate.exists()}
    if candidate.exists():
        try:
            record["size_bytes_before_cleanup"] = candidate.stat().st_size
            record["sha256_before_cleanup"] = sha(candidate)
            candidate.unlink()
            record["removed"] = not candidate.exists()
            record["present_after_cleanup"] = candidate.exists()
        except Exception as cleanup_exc:
            record["removed"] = False
            record["present_after_cleanup"] = candidate.exists()
            record["cleanup_error"] = f"{type(cleanup_exc).__name__}: {cleanup_exc}"
    else:
        record.update({"removed": True, "present_after_cleanup": False})
    receipt["error_candidate_artifact_cleanup"] = record


def save_rejected_diagnostic(out: Path, grid, lattice_m, variables_rc, source_base_context):
    """Save diagnostic-only solver output; never label it as an accepted candidate."""
    final = out / "rejected-diagnostic.npz"
    temp = out / f"rejected-diagnostic.{os.getpid()}.tmp.npz"
    if final.exists() or temp.exists():
        raise RuntimeError("refuse overwrite of rejected diagnostic artifact")
    with temp.open("xb") as stream:
        np.savez_compressed(stream, context_grid=np.asarray(grid, dtype=np.float32),
                            lattice_m=np.asarray(lattice_m, dtype=np.int64),
                            variables_rc=np.asarray(variables_rc, dtype=np.int32),
                            source_base_context=np.asarray(source_base_context, dtype=np.float32))
    os.replace(temp, final)
    return final


def write_error_receipt(out: Path, receipt, exc, started):
    receipt.update({"status": "ERROR", "accepted": False, "terrain_written": False,
                    "error_type": type(exc).__name__, "error": str(exc),
                    "traceback": traceback.format_exc(),
                    "elapsed_seconds": time.monotonic() - started})
    cleanup_candidate_after_error(out, receipt)
    try:
        atomic_json(out / "receipt.json", receipt)
    except Exception:
        (out / "receipt-write-error.txt").write_text(traceback.format_exc(), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="One-shot candidate-only exact float32-lattice MILP; never promotes output.")
    parser.add_argument("--approved-driver-sha", required=True)
    parser.add_argument("--approved-model-sha", required=True)
    parser.add_argument("--approved-plan-sha", required=True)
    parser.add_argument("--approved-control-sha", required=True)
    args = parser.parse_args(argv)

    # Create-only output prevents an accidental retry; every later failure gets
    # a terminal receipt, including failures before the solver boundary.
    OUT.mkdir(parents=False, exist_ok=False)
    marker = OUT / "invocation.started.json"
    started = time.monotonic()
    receipt = {"schema": "candidate-only-f32-lattice.real-run.v1", "status": "ERROR",
               "accepted": False, "terrain_written": False, "solver_invoked": False,
               "approved_hashes": vars(args), "versions": {"numpy": np.__version__, "scipy": scipy.__version__},
               "output": str(OUT), "source_readset_start": None, "source_readset_end": None}
    try:
        marker.write_text(json.dumps({"pid": os.getpid(), "started_unix": time.time(),
                                      "driver_sha256": sha(Path(__file__))}, sort_keys=True) + "\n", encoding="utf-8")
        static = {"driver": Path(__file__).resolve(), "model": MODEL, "tests": TESTS,
                  "runner_tests": RUNNER_TESTS,
                  "control_script": CONTROL_SCRIPT, "plan": PLAN, "control": CONTROL,
                  "base_model": BASE_MODEL, "old_control": OLD_CONTROL, "audit": AUDIT,
                  "converter": CONVERTER, "executor": EXECUTOR}
        actual = {k: sha(v) for k, v in static.items()}
        approved = {"driver": args.approved_driver_sha.lower(), "model": args.approved_model_sha.lower(),
                    "plan": args.approved_plan_sha.lower(), "control": args.approved_control_sha.lower()}
        for key, expected in EXPECTED.items():
            path_key = {"plan": "plan", "base_model": "base_model", "old_control": "old_control",
                        "audit": "audit", "converter": "converter", "executor": "executor",
                        "tests": "tests", "runner_tests": "runner_tests",
                        "control_script": "control_script", "control": "control"}[key]
            if actual[path_key] != expected:
                raise RuntimeError(f"pinned {key} changed: {actual[path_key]}")
        for key, path_key in (("driver", "driver"), ("model", "model"), ("plan", "plan"), ("control", "control")):
            if actual[path_key] != approved[key]:
                raise RuntimeError(f"review approval mismatch for {key}: {actual[path_key]}")
        if scipy.__version__ != "1.18.1":
            raise RuntimeError(f"SciPy version mismatch: {scipy.__version__}")
        control = json.loads(CONTROL.read_text(encoding="utf-8"))
        if control.get("status") != "BASELINE_CONTROL_PASS" or control.get("real_solver_invoked") is not False:
            raise RuntimeError("pinned B positive-control receipt is not a no-solver PASS")
        control_start = control.get("inputs", {}).get("source_readset_start", {})
        if control_start.get(str(MODEL.resolve())) != actual["model"]:
            raise RuntimeError("B positive-control receipt does not pin the reviewed candidate model")

        read_start = source_map(static.values())
        expected_static = {str(Path(static[k]).resolve()): value for k, value in actual.items()}
        if read_start != expected_static:
            raise RuntimeError("static source readset changed between approval check and run start")
        receipt["source_readset_start"] = read_start
        base = load_pinned("real_candidate_base", BASE_MODEL, EXPECTED["base_model"])
        executor = load_pinned("real_candidate_executor", EXECUTOR, EXPECTED["executor"])
        converter = load_pinned("real_candidate_converter", CONVERTER, EXPECTED["converter"])
        model_module = load_pinned("real_candidate_model", MODEL, approved["model"])
        converter.load_executor = lambda: executor

        # The historical AC-3 propagation empties one domain despite the complete
        # direct crossing model. Skip only that pruning pass; all unary/binary
        # relations remain in the MILP and are checked again with exact fractions.
        original_propagate = converter.propagate
        converter.propagate = lambda domains, relations, subset=None: (dict(domains), {"variable": None, "trace": []})
        try:
            problem = converter._load_real_problem(time.monotonic() + WALL_LIMIT_SECONDS)
        finally:
            converter.propagate = original_propagate
        data = problem["data"]
        receipt["input_readset_start"] = data.get("source_start", {})
        raw_only = []
        other_singletons = []
        for i, mask in problem["domains"].items():
            if int(mask).bit_count() == 1:
                (raw_only if int(mask) == (1 << 1) else other_singletons).append(int(i))
        if other_singletons or len(raw_only) != 2:
            raise RuntimeError(f"domain singleton contract changed: raw={raw_only}, other={other_singletons}")
        crossings = [base.Crossing(tuple(s.local_a), tuple(s.local_b), s.level_a, s.level_b,
                                   int(s.dry_endpoint), s.t_lower, s.t_upper, str(s.key))
                     for s in data["cross_specs"]]
        signs = [base.Sign(tuple(s.local_rc), s.level, int(s.sign), s.baseline, str(s.surface))
                 for s in data["sign_specs"]]
        witnesses = [((int(a), int(b)), (int(c), int(d)))
                     for a, b, c, d in np.asarray(data["witnesses"], dtype=np.int32)]
        model = model_module.CandidateLatticeMILP(base, data["context"], problem["vars_local"],
                                                   data["lo"], data["hi"], problem["x64"],
                                                   crossings=crossings, signs=signs,
                                                   d8_witnesses=witnesses, fixed_indices=raw_only)
        install_solver_invocation_tracker(model_module, receipt)
        elapsed_before_solve = time.monotonic() - started
        remaining = WALL_LIMIT_SECONDS - elapsed_before_solve
        if remaining <= 0:
            raise TimeoutError("60-second one-shot budget expired before HiGHS")
        result = model.solve_once(time_limit=remaining, node_limit=NODE_LIMIT)
        if time.monotonic() - started > WALL_LIMIT_SECONDS:
            raise TimeoutError("60-second one-shot budget exceeded after exact candidate checks")

        grid = np.asarray(result["grid"], dtype=np.float32)
        direct = executor.eval_gates(data, grid)
        if time.monotonic() - started > WALL_LIMIT_SECONDS:
            raise TimeoutError("60-second one-shot budget exceeded during independent direct gates")
        direct_pass = all(bool(direct[k]) for k in (
            "bounds", "PF_signs", "all_116_direct_crossings", "D8_direct",
            "face_cones", "closure_energy_and_improvement"))
        exact_pass = result["status"] == "CANDIDATE_PASS_FRACTION_PENDING_SHAPE_CONSUMER"
        read_end = source_map(static.values())
        for path, expected_hash in data.get("source_start", {}).items():
            if sha(Path(path)) != expected_hash:
                raise RuntimeError(f"input drift during run: {path}")
            read_end[str(Path(path).resolve())] = sha(Path(path))
        expected_readset = receipt["source_readset_start"] | {
            str(Path(p).resolve()): h for p, h in data.get("source_start", {}).items()}
        if read_end != expected_readset:
            raise RuntimeError("source readset changed during one-shot candidate generation")
        if time.monotonic() - started > WALL_LIMIT_SECONDS:
            raise TimeoutError("60-second one-shot budget exceeded during final source verification")

        receipt.update({"solver_status": result.get("solver_status"),
                        "solver_message": result.get("solver_message"),
                        "mip_gap": result.get("mip_gap"), "mip_node_count": result.get("mip_node_count"),
                        "matrix_objective_binary64": result.get("objective_float64"),
                        "exact_l1_units": result.get("exact_l1_units"),
                        "exact_fraction_gates": result.get("exact_fraction_gates"),
                        "exact_fraction_rows_pass": result.get("exact_rows_pass"),
                        "direct_executor_gates": {k: bool(v) for k, v in direct.items()},
                        "direct_executor_metrics": {k: float(v) for k, v in direct.items()
                                                     if isinstance(v, (int, float, np.number)) and not isinstance(v, (bool, np.bool_))},
                        "fixed_raw_only_indices": raw_only,
                        "source_readset_end": read_end,
                        "source_readset_stable": True,
                        "elapsed_seconds": time.monotonic() - started,
                        "optimality_claim": result.get("optimality_claim"),
                        "pending_independent_gates": ["shape extrema/prominence", "global sector metrics", "native/compiled exposure"]})
        if not exact_pass or not direct_pass:
            receipt["status"] = "REJECTED_EXACT_POSTGATES"
            diagnostic = save_rejected_diagnostic(OUT, grid, result["m"], problem["vars_rc"], data["context"])
            receipt["rejected_diagnostic"] = {
                "path": str(diagnostic.resolve()), "sha256": sha(diagnostic),
                "accepted": False, "terrain_written": False,
                "contains": ["context_grid", "lattice_m", "variables_rc", "source_base_context"],
            }
            atomic_json(OUT / "receipt.json", receipt)
            return 2
        candidate_path = OUT / "candidate-context.npz"
        with candidate_path.open("xb") as f:
            np.savez_compressed(f, context_grid=grid, variables_rc=np.asarray(problem["vars_rc"], dtype=np.int32),
                                lattice_m=np.asarray(result["m"], dtype=np.int64),
                                source_base_context=np.asarray(data["context"], dtype=np.float32))
        read_end_after_write = source_map(static.values())
        for path, expected_hash in data.get("source_start", {}).items():
            actual_hash = sha(Path(path))
            if actual_hash != expected_hash:
                raise RuntimeError(f"input drift after candidate artifact write: {path}")
            read_end_after_write[str(Path(path).resolve())] = actual_hash
        if read_end_after_write != expected_readset:
            raise RuntimeError("source readset changed before terminal candidate receipt")
        if time.monotonic() - started > WALL_LIMIT_SECONDS:
            raise TimeoutError("60-second one-shot budget exceeded before terminal candidate receipt")
        receipt.update({"status": "CANDIDATE_PENDING_INDEPENDENT_SHAPE_CONSUMER", "accepted": False,
                        "candidate_path": str(candidate_path), "candidate_sha256": sha(candidate_path),
                        "source_readset_end": read_end_after_write, "source_readset_stable": True,
                        "candidate_shape": list(grid.shape), "candidate_changed_vertices": int(np.count_nonzero(grid.view(np.uint32) != np.asarray(data["context"], dtype=np.float32).view(np.uint32)))})
        atomic_json(OUT / "receipt.json", receipt)
        return 0
    except Exception as exc:
        try:
            if receipt.get("source_readset_start") is not None:
                end = source_map([Path(p) for p in receipt["source_readset_start"]])
                for p in receipt.get("input_readset_start", {}):
                    end[str(Path(p).resolve())] = sha(Path(p))
                receipt["source_readset_end"] = end
                expected = receipt["source_readset_start"] | {
                    str(Path(p).resolve()): h for p, h in receipt.get("input_readset_start", {}).items()}
                receipt["source_readset_stable"] = bool(end == expected)
        except Exception:
            receipt["error_readset_capture"] = traceback.format_exc()
        write_error_receipt(OUT, receipt, exc, started)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
