from __future__ import annotations

import hashlib
import importlib.util
import ast
import json
import math
import sys
from pathlib import Path

import numpy as np


BASE = Path(r"E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\G\wet-bank-pilot")
POLISH_DIR = BASE / "postsolve-consumer/float32-component-conversion-v1/robust-f32-design/candidate-only-milp/d8-sign-fix-v1/energy-neighbor-polish-v2-recovery"
RUN = POLISH_DIR / "run-01"
PREP = BASE / "prepared-runs/attempt-08/prepared.npz"
MODEL_SOURCE = BASE / "postsolve-consumer/float32-component-conversion-v1/robust-f32-design/candidate-only-milp/d8-sign-fix-v1/candidate_model.py"
LATTICE_SOURCE = BASE / "postsolve-consumer/float32-component-conversion-v1/robust-f32-design/candidate-only-milp/d8-sign-fix-v1/lattice_milp.py"
OUTPUT = Path(__file__).resolve().parent / "mechanism.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_polisher():
    path = POLISH_DIR / "energy_neighbor_polish.py"
    spec = importlib.util.spec_from_file_location("energy_polish_readonly_v2", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import pinned read-only polish implementation")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def crossing_t(spec, grid):
    endpoints = [tuple(spec.a_rc), tuple(spec.b_rc)]
    levels = [float(spec.level_a), float(spec.level_b)]
    dry = int(spec.dry_endpoint)
    wet = 1 - dry
    dd = float(grid[endpoints[dry]]) - levels[dry]
    dw = float(grid[endpoints[wet]]) - levels[wet]
    return dd / (dd - dw)


def main():
    receipt_path = RUN / "receipt.json"
    ledger_path = RUN / "neighbors.jsonl"
    receipt_sha = sha256(receipt_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema") != "candidate-only-milp.energy-neighbor-polish.v1":
        raise RuntimeError("unexpected recovery receipt schema")
    if (receipt.get("status") != "NO_FEASIBLE_ONE_ULP_NEIGHBOR" or
            receipt.get("eligible_neighbor_count") != 0 or receipt.get("solver_calls") != 0 or
            receipt.get("terrain_written") is not False or receipt.get("polished_diagnostic") is not None):
        # The chained comparison is deliberately avoided below; keep each field explicit.
        raise RuntimeError("recovery receipt is not the complete no-artifact diagnostic")
    if receipt.get("neighbor_count") != 242 or receipt.get("expected_neighbor_count") != 242:
        raise RuntimeError("recovery receipt does not cover all 242 neighbors")
    read0 = receipt.get("source_readset_start")
    read1 = receipt.get("source_readset_end")
    if receipt.get("source_readset_stable") is not True or not isinstance(read0, dict) or read0 != read1:
        raise RuntimeError("recovery input readset is unstable")
    for raw_path, expected in read0.items():
        if sha256(Path(raw_path)) != expected:
            raise RuntimeError(f"readset drift: {raw_path}")
    if sha256(ledger_path) != receipt.get("ledger_sha256"):
        raise RuntimeError("ledger hash differs from recovery receipt")
    rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 242:
        raise RuntimeError("ledger row count mismatch")
    energy_rows = [r for r in rows if r.get("energy_gate") is True]
    if len(energy_rows) != 2 or any(r.get("eligible") is True for r in rows):
        raise RuntimeError("expected exactly two energy-only rows and zero eligible rows")

    polisher = load_polisher()
    real = polisher.prepare_real_inputs()
    wrapper = real["wrapper"]
    model = wrapper.model
    executor = real["executor"]
    data = real["data"]
    base_grid = real["grid"]
    vars_global = real["problem"]["vars_rc"]
    vars_local = real["problem"]["vars_local"]
    energy_cases = []
    crossing_details = []

    for record in energy_rows:
        index, step = int(record["variable_index"]), int(record["step"])
        global_rc = tuple(map(int, vars_global[index]))
        local_rc = tuple(map(int, vars_local[index]))
        source_height = np.float32(base_grid[local_rc])
        toward = np.float32(np.inf if step > 0 else -np.inf)
        candidate_height = np.nextafter(source_height, toward, dtype=np.float32)
        candidate = base_grid.copy()
        candidate[local_rc] = candidate_height
        exact_gates = {k: bool(v) for k, v in model.exact_gates(candidate).items()}
        lattice_vector = polisher.lattice_vector_for_grid(wrapper, candidate)
        try:
            exact_rows_pass, exact_failures = wrapper.exact_rows_pass(lattice_vector)
        except wrapper.base_module.ModelError as exc:
            exact_failures = [polisher.classify_outside_segments(exc, exact_gates)]
            exact_rows_pass = False
        except ValueError as exc:
            if "fixed lattice value mismatch at " in str(exc):
                failure = polisher.classify_fixed_lattice_mismatch(exc, exact_gates)
            elif "lattice value outside segments at " in str(exc):
                failure = polisher.classify_outside_segments(exc, exact_gates)
            else:
                raise
            exact_failures = [failure]
            exact_rows_pass = False
        direct = executor.eval_gates(data, candidate)
        direct_gates = {k: bool(direct[k]) for k in (
            "bounds", "PF_signs", "all_116_direct_crossings", "D8_direct", "face_cones",
            "closure_energy_and_improvement")}
        for key in ("raw_cost", "closed_cost", "baseline_cost"):
            if float(record[key]) != float(direct[key]):
                raise RuntimeError(f"ledger/direct mismatch for {key} at {global_rc}")
        if direct_gates != record["direct_gates"] or exact_gates != record["exact_fraction_gates"]:
            raise RuntimeError(f"ledger/model gate mismatch at {global_rc}")

        delta_cost = float(record["closed_cost"]) - float(record["raw_cost"])
        energy_cases.append({
            "variable_index": index, "global_rc": list(global_rc), "step": step,
            "source_height_m": float(source_height), "neighbor_height_m": float(candidate_height),
            "ulp_delta_m": float(candidate_height - source_height),
            "lower_m": float(data["lo"][index]), "upper_m": float(data["hi"][index]),
            "raw_cost": float(record["raw_cost"]), "neighbor_closed_cost": float(record["closed_cost"]),
            "baseline_cost": float(record["baseline_cost"]), "closed_minus_raw": delta_cost,
            "allowance": float(record["allowance"]), "energy_gate": bool(record["energy_gate"]),
            "exact_rows_pass": bool(exact_rows_pass), "exact_row_failure_count": len(exact_failures),
            "exact_row_failures": exact_failures,
            "exact_fraction_gates": exact_gates, "direct_gates": direct_gates,
        })
        if index == 14 and step == 1:
            for name in exact_failures:
                rowname = str(name.get("name", ""))
                if not rowname.startswith("cross:"):
                    continue
                ci = int(rowname.split(":", 2)[1])
                spec = model.crossings[ci]
                t0 = crossing_t(spec, base_grid)
                t1 = crossing_t(spec, candidate)
                # The edge is a 6 m native edge; convert the t overshoot into along-edge distance.
                overshoot = max(float(spec.t_lower) - t1, 0.0, t1 - float(spec.t_upper))
                crossing_details.append({
                    "crossing_id": ci, "source": str(spec.source),
                    "surface": str(ast.literal_eval(spec.source)[-1]),
                    "edge_local_rc": [list(map(int, spec.a_rc)), list(map(int, spec.b_rc))],
                    "dry_endpoint": int(spec.dry_endpoint),
                    "baseline_t": t0, "candidate_t": t1,
                    "allowed_t": [float(spec.t_lower), float(spec.t_upper)],
                    "overshoot_t": overshoot, "overshoot_m_on_6m_edge": overshoot * 6.0,
                    "failed_row": rowname,
                })

    if len(crossing_details) != 4:
        raise RuntimeError(f"expected four reconstructed P/F crossings, got {len(crossing_details)}")
    if getattr(real["candidate_model_module"], "_energy_polish_solver_calls", 0) != 0:
        raise RuntimeError("analysis unexpectedly invoked MILP solver")
    for raw_path, expected in read0.items():
        if sha256(Path(raw_path)) != expected:
            raise RuntimeError(f"readset drift during analysis: {raw_path}")

    report = {
        "schema": "ev94.energy-neighbor-v2.mechanism-analysis.v1",
        "status": "ANALYSIS_ONLY_NO_CANDIDATE",
        "scope": "two energy-eligible one-node/one-ULP neighbors in the completed 242-row recovery; no solver and no claim about coordinated/multi-node feasibility",
        "inputs": {
            "receipt": {"path": str(receipt_path.resolve()), "sha256": receipt_sha},
            "ledger": {"path": str(ledger_path.resolve()), "sha256": receipt["ledger_sha256"]},
            "polish_source": {"path": str((POLISH_DIR / "energy_neighbor_polish.py").resolve()),
                              "sha256": read0[str((POLISH_DIR / "energy_neighbor_polish.py").resolve())]},
            "plan": {"path": str((POLISH_DIR / "PLAN.md").resolve()),
                     "sha256": read0[str((POLISH_DIR / "PLAN.md").resolve())]},
            "prepared": {"path": str(PREP.resolve()), "sha256": read0[str(PREP.resolve())]},
            "candidate_model_sha256": sha256(MODEL_SOURCE),
            "lattice_model_sha256": sha256(LATTICE_SOURCE),
            "readset_stable": read0 == read1,
        },
        "enumeration": {"neighbors": 242, "energy_gate_pass": 2, "fully_eligible": 0,
                        "rejection_counts_overlap": receipt["rejection_counts"],
                        "solver_calls": 0, "candidate_artifact_written": False},
        "energy_cases": energy_cases,
        "crossing_mechanism": crossing_details,
        "conclusion": "Both lower objective cost enough to pass the energy allowance, but neither is jointly admissible. Raising (858,1184) by one ULP moves the same edge crossing past its baseline endpoint in four exact P/F interval rows. Lowering (863,1189) by one ULP crosses an active lower bound and leaves its float32 segment. Both pass D8; D8 is not the blocker for these two cases.",
        "limits": ["This proves only that the enumerated single-node +/-1 ULP neighbors have no admissible candidate.",
                   "No coordinated neighbor, wider local step, or full feasible-set infeasibility was tested."],
        "analysis_script_sha256": sha256(Path(__file__).resolve()),
    }
    OUTPUT.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    out = main()
    print(json.dumps({"status": out["status"], "energy_cases": out["energy_cases"],
                      "crossing_mechanism": out["crossing_mechanism"],
                      "output": str(OUTPUT)}, indent=2, allow_nan=False))
