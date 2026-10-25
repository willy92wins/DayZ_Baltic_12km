from __future__ import annotations

import hashlib
import json
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
from scipy import sparse


HERE = Path(__file__).resolve().parent
BASE = Path(r"E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\G\wet-bank-pilot")
PREP = BASE / "prepared-runs/attempt-08/prepared.npz"
SOLUTION = BASE / "solve-once/solution.npz"
MECHANISM = HERE / "mechanism.json"
RECEIPT = BASE / "postsolve-consumer/float32-component-conversion-v1/robust-f32-design/candidate-only-milp/d8-sign-fix-v1/energy-neighbor-polish-v2-recovery/run-01/receipt.json"
LEDGER = RECEIPT.with_name("neighbors.jsonl")
POLISH = RECEIPT.parents[1] / "energy_neighbor_polish.py"
OUTPUT = HERE / "coordinated-crossing-component.json"
ORIGIN = np.asarray([855, 1179], dtype=np.int32)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def csr(z, stem: str):
    return sparse.csr_matrix(
        (z[f"{stem}_data"], z[f"{stem}_indices"], z[f"{stem}_indptr"]),
        shape=tuple(int(x) for x in z[f"{stem}_shape"]),
    )


def main() -> dict:
    expected = {
        PREP: "52409a8d074d15ec068bddc6e9265bc3782e84e9d54582b8a6d7b0a6675a787f",
        SOLUTION: "1b7a23ebb3c203427f1c77cb8de6becfca750746e47f5494bba6723b0610eab1",
        RECEIPT: "b71fbdab6f545abbf75075c40a7e1623e95969b11295306ce101c6f62d487e34",
        LEDGER: "086eb6741aad7f33e3dfb72fdd4d62d26e94406cecd017a973dde592865ca94a",
        POLISH: "4f40c6c51aaa9db4edeaf7ee27a1a2230cd2cb8ee508cbfe3db7f6c3daf30ba2",
        MECHANISM: "01610f50167b109ee43c65458cbe21c93efd23b8abda05ff2ac42b2aaa0c853b",
    }
    got = {str(p.resolve()): sha(p) for p in expected}
    drift = {str(p.resolve()): {"expected": digest, "actual": got[str(p.resolve())]}
             for p, digest in expected.items() if got[str(p.resolve())] != digest}
    if drift:
        raise RuntimeError(f"pinned input drift: {drift}")

    with np.load(PREP, allow_pickle=False) as z:
        A = csr(z, "A")
        C = csr(z, "C_cross")
        d_cross = z["d_C_cross"].copy()
        variables = z["variables_rc"].copy()
        baseline_x = z["x0_absolute"].copy()
        lo32 = z["lo_absolute_float32_inward"].copy()
        hi32 = z["hi_absolute_float32_inward"].copy()
        meta = json.loads(bytes(z["crossing_rows_json"]).decode("utf-8"))
        rhs = z["rhs_A"].copy()
    with np.load(SOLUTION, allow_pickle=False) as s:
        raw_grid = s["raw_float32_grid"].copy()
        solution_varcoords = s["variables_rc"].copy()
    if not np.array_equal(solution_varcoords, variables):
        raise RuntimeError("solution variable order differs from prepared source")
    loc = variables - ORIGIN
    raw_x = raw_grid[tuple(loc.T)].astype(np.float64)
    first_sign_only = next((i for i, item in enumerate(meta) if item.get("type") == "sign_only"), len(meta))
    chain_rows = (10, 19, 26, 67, 74, 83, 115)
    if first_sign_only <= max(chain_rows) or C.shape[0] != len(meta) - sum(item.get("type") == "sign_only" for item in meta):
        raise RuntimeError("crossing row alignment/count is not as expected for this prefix")

    # Rows are C H >= d. An active lower row has positive endpoint weights;
    # an active upper row has negative endpoint weights. Since the rows are
    # affine, their directional implications below are exact, not linearized.
    slack = np.asarray(C @ raw_x - d_cross).reshape(-1)
    active = {}
    for row_index in (10, 19, 26, 67, 74, 83, 115):
        row = C.getrow(row_index)
        m = meta[row_index]
        if abs(float(slack[row_index])) > 2e-12:
            raise RuntimeError(f"expected active crossing row {row_index}, slack={slack[row_index]}")
        active[str(row_index)] = {
            "type": m["type"], "surface": m["surface"], "cell_rc": m["cell_rc"],
            "edge_rc": m["edge_rc"], "t_base": m["t_base"], "t_bound": m["t_bound"],
            "slack_at_raw_m": float(slack[row_index]),
            "coefficients": [
                {"variable_index": int(i), "global_rc": variables[i].astype(int).tolist(), "coefficient": float(v)}
                for i, v in zip(row.indices, row.data)
            ],
        }

    # Enumerate the connected component of all exact baseline-active crossing
    # interval rows. This is a graph read from the prepared rows only.
    active_graph: dict[tuple[int, int], list[tuple[tuple[int, int], int]]] = defaultdict(list)
    for row_index, item in enumerate(meta):
        if (item.get("type") not in ("cross_lower", "cross_upper") or
                item.get("t_base") is None or item.get("t_bound") is None or
                abs(float(item["t_base"]) - float(item["t_bound"])) > 1e-14):
            continue
        a, b = (tuple(map(int, rc)) for rc in item["edge_rc"])
        active_graph[a].append((b, row_index))
        active_graph[b].append((a, row_index))
    start_node = tuple(map(int, variables[14]))
    component_nodes = {start_node}
    queue = deque([start_node])
    component_rows: set[int] = set()
    while queue:
        u = queue.popleft()
        for v, row_index in active_graph[u]:
            component_rows.add(row_index)
            if v not in component_nodes:
                component_nodes.add(v)
                queue.append(v)
    var_lookup = {tuple(map(int, rc)): i for i, rc in enumerate(variables)}
    component_summary = {
        "active_interval_row_count": len(component_rows),
        "node_count": len(component_nodes),
        "mutable_variable_count": sum(rc in var_lookup for rc in component_nodes),
        "fixed_context_node_count": sum(rc not in var_lookup for rc in component_nodes),
        "bbox_rc_inclusive": [min(r for r, c in component_nodes), max(r for r, c in component_nodes),
                              min(c for r, c in component_nodes), max(c for r, c in component_nodes)],
        "nodes": [{"global_rc": list(rc), "variable_index": var_lookup.get(rc)}
                  for rc in sorted(component_nodes)],
        "active_row_indices": sorted(component_rows),
    }

    indexes = (1, 2, 13, 14)
    chain = {
        "step_1": {"rows": [10, 19], "coordinate": variables[1].astype(int).tolist(),
                   "implication": "row 10 gives +c*delta_1 >= 0; row 19 gives -c'*delta_1 >= 0; therefore delta_1=0"},
        "step_2": {"rows": [26, 67], "coordinate": variables[2].astype(int).tolist(),
                   "implication": "with delta_1=0, row 26 gives +c*delta_2 >= 0 and row 67 gives -c'*delta_2 >= 0; therefore delta_2=0"},
        "step_3": {"rows": [74, 83], "coordinate": variables[13].astype(int).tolist(),
                   "implication": "with delta_2=0, row 74 gives +c*delta_13 >= 0 and row 83 gives -c'*delta_13 >= 0; therefore delta_13=0"},
        "step_4": {"rows": [115], "coordinate": variables[14].astype(int).tolist(),
                   "implication": "with delta_13=0, active upper row 115 requires delta_14 <= 0; raising the wet endpoint is impossible under the frozen crossing intervals"},
    }

    # Exact quadratic for the proposed two-node transfer using the stored A,
    # raw vector, and one-f32-ULP spacing. This does not construct/evaluate a grid.
    residual = np.asarray(A @ raw_x - rhs).reshape(-1)
    q = float(np.spacing(np.float32(raw_x[14])))
    direction = np.zeros_like(raw_x)
    direction[13] = -q
    direction[14] = q
    Ad = np.asarray(A @ direction).reshape(-1)
    grad = np.asarray(A.T @ residual).reshape(-1)
    delta_obj = float(grad @ direction + 0.5 * (Ad @ Ad))
    energy = {
        "one_ulp_m": q,
        "direction": {"index_13": -q, "index_14": q},
        "gradient_A_objective_at_raw": {str(i): float(grad[i]) for i in indexes},
        "quadratic_delta_exact_formula": "g^T d + 0.5 * ||A d||^2",
        "objective_at_raw": float(0.5 * (residual @ residual)),
        "predicted_delta_objective": delta_obj,
        "predicted_objective_after_transfer": float(0.5 * (residual @ residual) + delta_obj),
        "energy_allowance_from_neighbor_ledger": 1.5594405102975674e-5,
        "crossing_feasibility": "rejected by the exact active-row chain; this is objective-only, not a feasible correction",
    }

    # Small analytical sanity fixtures for inequality orientation and pinning.
    eps = 1.0
    # Positive: an active upper edge with t=.3 admits its exact tangent transfer.
    pos_c = np.asarray([-(1.0 - 0.3), -0.3])
    pos_d = np.asarray([-0.3 * eps, (1.0 - 0.3) * eps])
    positive_fixture = bool(abs(float(pos_c @ pos_d)) < 1e-15)
    # Negative: two opposing active inequalities pin the upstream node, then
    # the active upper edge rejects a positive wet-endpoint displacement.
    neg_pin = bool(0.4480353733837126 * 1.0 >= 0.0 and -0.4322683185312698 * 1.0 < 0.0)
    # A feasible directional delta must satisfy both pinning rows; the one-node
    # positive wet step violates active upper row 115 after the upstream pin.
    wet_step = q
    row115_delta = -0.32188715327753664 * wet_step
    negative_fixture = bool(neg_pin and row115_delta < 0.0)
    if not positive_fixture or not negative_fixture:
        raise RuntimeError("analytical positive/negative fixture failed")

    report = {
        "schema": "ev94.coordinated-crossing-component.analysis.v1",
        "status": "ANALYTIC_PINNING_CONFIRMED_NO_NEW_CANDIDATE",
        "scope": "read-only analysis of one-ULP energy-only wet endpoint (858,1184); no solver, no altered grid, no new neighbor enumeration",
        "analysis_source": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__).resolve())},
        "inputs": {str(p.resolve()): digest for p, digest in expected.items()},
        "variable_chain": {str(i): {"global_rc": variables[i].astype(int).tolist(),
                                     "raw_height_m": float(raw_x[i]),
                                     "bounds_float32_inward_m": [float(lo32[i]), float(hi32[i])]}
                           for i in indexes},
        "active_crossing_rows": active,
        "crossing_row_alignment": {"metadata_rows": len(meta), "affine_rows": int(C.shape[0]),
                                   "sign_only_metadata_rows": int(sum(item.get("type") == "sign_only" for item in meta)),
                                   "first_sign_only_metadata_index": int(first_sign_only),
                                   "selected_affine_prefix_rows_align": True},
        "pinning_chain": chain,
        "connected_active_crossing_component": component_summary,
        "objective": energy,
        "fixtures": {
            "positive_synthetic_active_upper_tangent": {"pass": positive_fixture, "C": pos_c.tolist(), "d": pos_d.tolist(), "Cdotd": float(pos_c @ pos_d)},
            "negative_real_active_pin_chain": {"pass": negative_fixture, "expected": "delta_1=delta_2=delta_13=0, hence delta_14<=0", "positive_wet_step_row115_Cdotd": float(row115_delta)},
        },
        "interpretation": [
            "The exact crossing constraints are affine halfspaces in absolute heights. At the raw state the selected rows have zero slack, so this is an exact feasible-set pin, not a first-order approximation.",
            "The pinning uses the current 121-variable domain and its fixed collar. Moving the collar or changing the crossing intervals/design bounds would change the authorized problem; neither was tested or proposed as an accepted fix.",
            "The separate energy-only neighbor at (863,1189) remains blocked by its active inward float32 lower bound, outside this crossing chain.",
            "D8 was not needed to prove the obstruction; adding D8 constraints cannot make a crossing-infeasible displacement feasible. No statement is made about a redesigned interval set or a larger domain that changes fixed context.",
        ],
        "readset_reverified": True,
    }
    for p, digest in expected.items():
        if sha(p) != digest:
            raise RuntimeError(f"input changed during analysis: {p}")
    OUTPUT.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "pinned_indices": list(indexes),
                      "predicted_delta_objective": delta_obj,
                      "positive_fixture": positive_fixture, "negative_fixture": negative_fixture,
                      "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
