from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
PROTO = HERE.parent
CP_PATH = PROTO / 'face-slope-cone-pilot' / 'pilot.py'
OP_PATH = PROTO / 'global-structured-operator' / 'structured_operator.py'
FUSED_PATH = PROTO / 'global-structured-operator' / 'optimized-normal' / 'fused_normal.py'
MEASUREMENT_PATH = PROTO / 'global-structured-operator' / 'optimized-normal' / 'comparison' / 'run-01' / 'comparison.json'
PLAN_PATH = HERE / 'PLAN.md'
PINS = {
    CP_PATH: 'd743f5006e0aa6606024a3c3291a74cb52b78f76c1aa5c6dfd95cdd26cdc9d2a',
    OP_PATH: 'd3017e58bbae3b71c891fab6892a5bf8d9386ae8a51a451a94c9b05769ac750a',
    FUSED_PATH: '19a3e3a493f643702e66aaf265c705739535d386412f74659369d7746117ffaa',
    MEASUREMENT_PATH: 'db6fa205e2b2b3d824ac07c1ad52d6c54ae6bf12e8b34d1a7093a701f518a965',
}

def pinned_load(path, expected, name):
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise AssertionError(f'{name} pin mismatch: {actual}')
    spec = importlib.util.spec_from_loader(name, loader=None, origin=str(path))
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


op_mod = pinned_load(OP_PATH, PINS[OP_PATH], 'pinned_structured_operator_for_adapter_fixture')
fused_mod = pinned_load(FUSED_PATH, PINS[FUSED_PATH], 'pinned_fused_normal_for_adapter_fixture')
build_operators = op_mod.build_operators
FusedNormalAction = fused_mod.FusedNormalAction
import matrix_free_admm as adapter
from matrix_free_admm import RuntimeLimits, solve_admm_matrix_free


def callback_csr(action, rows, columns):
    dense = np.empty((rows, columns), dtype=np.float64)
    basis = np.zeros(columns, dtype=np.float64)
    for col in range(columns):
        basis.fill(0.0)
        basis[col] = 1.0
        dense[:, col] = action(basis)
    return sparse.csr_matrix(dense)


def inf(a):
    return float(np.max(np.abs(np.asarray(a, dtype=np.float64)), initial=0.0))


def run():
    for path, digest in PINS.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise AssertionError(f'pinned input changed: {path}')
    cp = pinned_load(CP_PATH, PINS[CP_PATH], 'pinned_cp_pilot_for_adapter_fixture')
    cp_settings = {
        'rho': (adapter.CP_RHO, cp.RHO),
        'abs_tol': (adapter.CP_ABS_TOL, cp.ABS_TOL),
        'rel_tol': (adapter.CP_REL_TOL, cp.REL_TOL),
        'max_iterations': (adapter.CP_MAX_ITERATIONS, cp.MAX_ITER),
        'cg_rtol': (adapter.CP_CG_RTOL, cp.CG_RTOL),
        'cg_atol': (adapter.CP_CG_ATOL, cp.CG_ATOL),
        'cg_max_iterations': (adapter.CP_CG_MAX_ITERATIONS, cp.CG_MAXITER),
    }
    if any(float(actual) != float(expected) for actual, expected in cp_settings.values()):
        raise AssertionError(f'adapter algorithm settings drifted from CP: {cp_settings}')
    rr, cc = np.indices((16, 16))
    B = (0.8 * rr + 1.1 * cc + 0.025 * (rr - 7.5) ** 2 +
         0.035 * (cc - 8.0) ** 2 + 0.12 * np.sin((rr + cc) / 2.7)).astype(np.float64)
    nodes = np.column_stack(np.nonzero((rr >= 4) & (rr <= 11) & (cc >= 4) & (cc <= 11))).astype(np.int32)
    operators = build_operators(B, nodes)
    A = callback_csr(operators.matvec_a, operators.n_a, operators.n)
    C = callback_csr(operators.matvec_c, operators.n_c, operators.n)
    G = callback_csr(operators.matvec_g, operators.n_g, operators.n)

    # Active SOC faces are derived from the actual baseline face vectors and
    # tightened for nonzero rows, while zero rows retain a valid small radius.
    baseline_g = operators.matvec_g(B[nodes[:, 0], nodes[:, 1]]) + operators.k_g
    base_pairs = baseline_g.reshape(-1, 2)
    base_norm = np.linalg.norm(base_pairs, axis=1)
    radii = base_norm + 0.02
    active_cell = 7 * 15 + 7
    active_face = active_cell * 2
    radii[active_face] = max(0.1, 0.99 * base_norm[active_face])
    lo = B[nodes[:, 0], nodes[:, 1]] - 0.8
    hi = B[nodes[:, 0], nodes[:, 1]] + 0.8
    x0 = B[nodes[:, 0], nodes[:, 1]].copy()

    rho = 1.0
    fused = FusedNormalAction(operators)
    normal = operators.normal_operator(rho)
    explicit_normal = (A.T @ A + rho * (sparse.eye(operators.n, format='csr') + C.T @ C + G.T @ G)).tocsr()
    probe = np.linspace(-0.7, 0.9, operators.n, dtype=np.float64)
    normal_error = inf(normal @ probe - explicit_normal @ probe)
    diagonal_expected = np.asarray(explicit_normal.diagonal(), dtype=np.float64)
    diagonal_error = inf(fused.diagonal(rho) - diagonal_expected)
    if normal_error > 1e-10 or diagonal_error > 1e-10:
        raise AssertionError({'normal_error': normal_error, 'diagonal_error': diagonal_error})

    budget = 30.0
    x_cp, diag_cp, history_cp, state_cp = cp.solve_admm(
        A, operators.rhs_a, C, operators.d_c, G, operators.k_g,
        radii, lo, hi, x0, budget_s=budget)
    runtime = RuntimeLimits(numeric_budget_seconds=budget)
    x_mf, diag_mf, history_mf, state_mf = solve_admm_matrix_free(
        operators, fused, operators.rhs_a, radii, lo, hi, x0,
        project_discs_fn=cp.project_discs, soc_kkt_fn=cp.soc_kkt,
        memory_snapshot_fn=cp.memory_snapshot, runtime=runtime)

    def objective(x):
        residual = A @ x - operators.rhs_a
        return 0.5 * float(np.dot(residual, residual))

    cp_primal = max(inf(x_cp - state_cp['z_box']), inf(C @ x_cp - state_cp['z_d8']),
                    inf(G @ x_cp + operators.k_g - state_cp['z_face']))
    mf_primal = max(inf(x_mf - state_mf['z_box']), inf(C @ x_mf - state_mf['z_d8']),
                    inf(G @ x_mf + operators.k_g - state_mf['z_face']))
    d8_violation_cp = float(np.max(np.maximum(operators.d_c - C @ x_cp, 0.0), initial=0.0))
    d8_violation_mf = float(np.max(np.maximum(operators.d_c - C @ x_mf, 0.0), initial=0.0))
    bound_violation_cp = float(max(np.max(np.maximum(lo - x_cp, 0.0)), np.max(np.maximum(x_cp - hi, 0.0))))
    bound_violation_mf = float(max(np.max(np.maximum(lo - x_mf, 0.0)), np.max(np.maximum(x_mf - hi, 0.0))))
    face_boundary_cp = int(diag_cp['soc_complementarity']['boundary_faces'])
    face_boundary_mf = int(diag_mf['soc_complementarity']['boundary_faces'])
    cone_metric_differences = {
        key: abs(float(diag_cp['soc_complementarity'][key]) - float(diag_mf['soc_complementarity'][key]))
        for key in ('complementarity_max', 'interior_dual_max', 'boundary_radial_residual_max',
                    'negative_radial_multiplier_max')
    }

    checks = {
        'cp_status': diag_cp['status'], 'matrix_free_status': diag_mf['status'],
        'normal_operator_vs_CSR_max_abs': normal_error,
        'fused_diagonal_vs_CSR_max_abs': diagonal_error,
        'objective_cp': objective(x_cp), 'objective_matrix_free': objective(x_mf),
        'objective_relative_difference': abs(objective(x_cp) - objective(x_mf)) / max(1.0, objective(x_cp)),
        'primal_cp': float(diag_cp['primal']), 'primal_matrix_free': float(diag_mf['primal']),
        'dual_cp': float(diag_cp['dual']), 'dual_matrix_free': float(diag_mf['dual']),
        'stationarity_cp': float(diag_cp['stationarity']), 'stationarity_matrix_free': float(diag_mf['stationarity']),
        'normal_cone_projection_residual_cp': float(diag_cp['normal_cone_projection_residual']),
        'normal_cone_projection_residual_matrix_free': float(diag_mf['normal_cone_projection_residual']),
        'normal_cone_projection_residual_abs_difference': abs(float(diag_cp['normal_cone_projection_residual']) -
                                                              float(diag_mf['normal_cone_projection_residual'])),
        'soc_kkt_metric_abs_differences': cone_metric_differences,
        'solution_max_abs_difference': inf(x_cp - x_mf),
        'box_violation_cp': bound_violation_cp, 'box_violation_matrix_free': bound_violation_mf,
        'D8_violation_cp': d8_violation_cp, 'D8_violation_matrix_free': d8_violation_mf,
        'active_SOC_faces_cp': face_boundary_cp, 'active_SOC_faces_matrix_free': face_boundary_mf,
        'rho_updates_equal': diag_cp['rho_updates'] == diag_mf['rho_updates'],
        'rho_update_count': len(diag_cp['rho_updates']),
        'iterations_cp': int(diag_cp['iteration']), 'iterations_matrix_free': int(diag_mf['iteration']),
    }
    assert diag_cp['status'] == diag_mf['status'] == 'CONVERGED', checks
    assert checks['objective_relative_difference'] < 2e-7, checks
    assert checks['solution_max_abs_difference'] < 2e-5, checks
    assert max(diag_cp['primal'], diag_mf['primal']) <= max(diag_cp['eps_primal'], diag_mf['eps_primal']), checks
    assert max(diag_cp['dual'], diag_mf['dual']) <= max(diag_cp['eps_dual'], diag_mf['eps_dual']), checks
    assert max(diag_cp['stationarity'], diag_mf['stationarity']) <= max(diag_cp['eps_dual'], diag_mf['eps_dual']), checks
    assert max(bound_violation_cp, bound_violation_mf, d8_violation_cp, d8_violation_mf) <= 1e-7, checks
    assert face_boundary_cp > 0 and face_boundary_mf > 0, checks
    assert checks['normal_cone_projection_residual_abs_difference'] < 1e-7, checks
    assert max(cone_metric_differences.values()) < 1e-7, checks

    # Affine offset check for rhs_a, d_c, and k_g is exercised by nonzero fixed
    # terrain around the variable patch and a direct normal-RHS identity.
    zb = x0.copy(); zd = np.maximum(C @ x0, operators.d_c)
    zs = cp.project_discs((G @ x0 + operators.k_g).reshape(-1, 2), radii).reshape(-1)
    ub = np.full(operators.n, 0.013); ud = np.full(operators.n_c, -0.017); us = np.full(operators.n_g, 0.009)
    right_old = A.T @ operators.rhs_a + rho * (zb - ub + C.T @ (zd - ud) + G.T @ (zs - us - operators.k_g))
    target_mf = operators.rmatvec_a(operators.rhs_a)
    right_mf = target_mf + rho * (zb - ub + operators.rmatvec_c(zd - ud) +
                                  operators.rmatvec_g(zs - us - operators.k_g))
    affine_rhs_error = inf(right_old - right_mf)
    assert affine_rhs_error < 1e-10, affine_rhs_error

    try:
        solve_admm_matrix_free(operators, fused, operators.rhs_a[:-1], radii, lo, hi, x0,
                               project_discs_fn=cp.project_discs, soc_kkt_fn=cp.soc_kkt,
                               memory_snapshot_fn=cp.memory_snapshot)
    except ValueError:
        bad_rhs_rejected = True
    else:
        raise AssertionError('adapter accepted a malformed affine A right-hand side')
    try:
        solve_admm_matrix_free(operators, fused, operators.rhs_a, radii, lo, hi, x0,
                               project_discs_fn=cp.project_discs, soc_kkt_fn=cp.soc_kkt,
                               memory_snapshot_fn=lambda: {'peak_working_set_bytes': 2},
                               runtime=RuntimeLimits(numeric_budget_seconds=30.0,
                                                     peak_working_set_limit_bytes=1))
    except MemoryError:
        memory_guard_rejected = True
    else:
        raise AssertionError('adapter ignored configured peak-working-set limit')
    try:
        solve_admm_matrix_free(operators, fused, operators.rhs_a, radii, lo, hi, x0,
                               project_discs_fn=cp.project_discs, soc_kkt_fn=cp.soc_kkt,
                               memory_snapshot_fn=cp.memory_snapshot,
                               runtime=RuntimeLimits(numeric_budget_seconds=1e-300))
    except TimeoutError:
        time_guard_rejected = True
    else:
        raise AssertionError('adapter ignored configured numeric time budget')

    process_memory = cp.memory_snapshot()
    return {
        'status': 'PASS_MATRIX_FREE_ADMM_ADAPTER_FIXTURE',
        'pins': {str(p): h for p, h in PINS.items()},
        'adapter_source': {'path': str(Path(adapter.__file__).resolve()),
                           'sha256': hashlib.sha256(Path(adapter.__file__).read_bytes()).hexdigest()},
        'fixture_source': {'path': str(Path(__file__).resolve()),
                           'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        'plan': {'path': str(PLAN_PATH.resolve()),
                 'sha256': hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest()},
        'shape': list(B.shape), 'variables': int(operators.n),
        'A_rows': int(operators.n_a), 'C_rows': int(operators.n_c), 'G_rows': int(operators.n_g),
        'affine_rhs_max_abs_error': affine_rhs_error,
        'negative_bad_rhs_rejected': bad_rhs_rejected,
        'negative_memory_guard_rejected': memory_guard_rejected,
        'negative_time_guard_rejected': time_guard_rejected,
        'fixture_process_memory_peak_bytes': int(process_memory['peak_working_set_bytes']),
        'checks': checks,
        'limits': {'budget_seconds': budget, 'solver_settings_other_than_budget': 'pinned CP defaults',
                   'global_solver_called': False, 'terrain_written': False,
                   'fixture_peak_includes_both_small_CSR_and_matrix_free_runs': True,
                   'cp_settings_equal': True},
    }


if __name__ == '__main__':
    import json
    print(json.dumps(run(), indent=2, allow_nan=False))
