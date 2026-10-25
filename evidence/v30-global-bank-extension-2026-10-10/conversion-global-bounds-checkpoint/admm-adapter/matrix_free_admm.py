"""CP-compatible ADMM loop using the verified fused matrix-free normal action."""
from __future__ import annotations

from dataclasses import dataclass
import time

import numpy as np
from scipy.sparse.linalg import LinearOperator, cg


CP_RHO = 1.0
CP_ABS_TOL = 1e-10
CP_REL_TOL = 1e-8
CP_MAX_ITERATIONS = 10000
CP_CG_RTOL = 1e-12
CP_CG_ATOL = 1e-13
CP_CG_MAX_ITERATIONS = 1000
CP_RHO_UPDATE_EVERY = 25
CP_RHO_UPDATE_THROUGH = 2000
CP_RHO_BALANCE_RATIO = 10.0
CP_RHO_FACTOR = 2.0
CP_RHO_MIN = 1.0 / 1024.0
CP_RHO_MAX = 1024.0


@dataclass(frozen=True)
class RuntimeLimits:
    """Only resource guards are configurable; algorithm constants stay pinned."""
    numeric_budget_seconds: float = 120.0
    peak_working_set_limit_bytes: int = 1_610_612_736


def _inf_norm(value):
    a = np.asarray(value, dtype=np.float64)
    return float(np.max(np.abs(a), initial=0.0))


def _vector(value, n, name):
    a = np.asarray(value, dtype=np.float64)
    if a.ndim != 1 or a.size != int(n) or not np.isfinite(a).all():
        raise ValueError(f'{name} must be a finite float64-compatible vector of length {n}')
    return a


def _fused_x_system(operators, fused_action, rho):
    if not np.isfinite(rho) or rho <= 0.0:
        raise ValueError('rho must be positive and finite')
    normal = fused_action.linear_operator(float(rho))
    diagonal = np.asarray(fused_action.diagonal(float(rho)), dtype=np.float64)
    if diagonal.shape != (operators.n,) or not np.isfinite(diagonal).all() or np.any(diagonal <= 0.0):
        raise ValueError('fused normal diagonal must be positive finite and match variable count')
    preconditioner = LinearOperator(normal.shape, matvec=lambda v: np.asarray(v, dtype=np.float64) / diagonal,
                                    dtype=np.float64)
    return normal, preconditioner, diagonal


def solve_admm_matrix_free(
    operators,
    fused_action,
    rhs_a,
    radii,
    lo,
    hi,
    x0,
    *,
    project_discs_fn,
    soc_kkt_fn,
    memory_snapshot_fn,
    runtime: RuntimeLimits = RuntimeLimits(),
    progress=None,
):
    """Run the CP ADMM iteration with identical projections and stopping gates.

    ``operators`` is the pinned MatrixFreeOperators API. Affine offsets are
    carried by ``rhs_a``, ``d_c`` and ``k_g``. No CSR matrix or transpose is
    built; the only changed algebraic plumbing is the x-step and its diagonal.
    """
    if not callable(project_discs_fn) or not callable(soc_kkt_fn) or not callable(memory_snapshot_fn):
        raise ValueError('pinned projection, SOC diagnostic, and memory callbacks are required')
    if (not isinstance(runtime, RuntimeLimits) or not np.isfinite(runtime.numeric_budget_seconds) or
            runtime.numeric_budget_seconds <= 0 or int(runtime.peak_working_set_limit_bytes) <= 0):
        raise ValueError('invalid ADMM runtime limits')

    n = int(operators.n)
    rhs_a = _vector(rhs_a, operators.n_a, 'rhs_a')
    d = _vector(operators.d_c, operators.n_c, 'd_c')
    k = _vector(operators.k_g, operators.n_g, 'k_g')
    radii = _vector(radii, operators.n_g // 2, 'radii')
    if operators.n_g % 2 or np.any(radii < 0.0):
        raise ValueError('G rows must form face pairs with nonnegative disc radii')
    lo = _vector(lo, n, 'lo')
    hi = _vector(hi, n, 'hi')
    x = _vector(x0, n, 'x0').copy()
    if np.any(lo > hi):
        raise ValueError('box lower bounds exceed upper bounds')

    started = time.perf_counter()
    next_memory_check = 0.0
    rho = CP_RHO

    def make_system(value):
        return _fused_x_system(operators, fused_action, value)

    normal, preconditioner, diagonal = make_system(rho)
    # Match CP's cached At@rhs: compute A^T rhs once via the pinned adjoint,
    # not once per ADMM iteration.
    target = operators.rmatvec_a(rhs_a)
    zb = np.clip(x, lo, hi)
    cx = operators.matvec_c(x)
    zd = np.maximum(cx, d)
    gx = operators.matvec_g(x) + k
    zs = project_discs_fn(gx.reshape(-1, 2), radii).reshape(-1)
    ub = np.zeros_like(zb)
    ud = np.zeros_like(zd)
    us = np.zeros_like(zs)

    history = []
    rho_updates = []
    status = 'ITERATION_LIMIT'
    diag = {}
    cg_total = 0
    memory_peak_observed = 0

    def guard():
        nonlocal next_memory_check, memory_peak_observed
        elapsed = time.perf_counter() - started
        if elapsed > runtime.numeric_budget_seconds:
            raise TimeoutError('numeric time budget exceeded')
        if elapsed >= next_memory_check:
            snap = memory_snapshot_fn()
            peak = int(snap.get('peak_working_set_bytes', -1))
            if peak < 0:
                raise RuntimeError('memory callback did not return peak_working_set_bytes')
            memory_peak_observed = max(memory_peak_observed, peak)
            if peak > runtime.peak_working_set_limit_bytes:
                raise MemoryError('peak working set exceeded configured limit')
            next_memory_check = elapsed + 1.0

    try:
        for iteration in range(1, CP_MAX_ITERATIONS + 1):
            guard()
            right = target + rho * (zb - ub + operators.rmatvec_c(zd - ud) +
                                    operators.rmatvec_g(zs - us - k))
            callback_count = [0]

            def cg_callback(_):
                callback_count[0] += 1
                guard()

            x, info = cg(normal, right, x0=x, rtol=CP_CG_RTOL, atol=CP_CG_ATOL,
                         maxiter=CP_CG_MAX_ITERATIONS, M=preconditioner, callback=cg_callback)
            cg_total += int(callback_count[0])
            if info:
                raise RuntimeError(f'CG failed info={info} at ADMM iteration={iteration}')

            cx = operators.matvec_c(x)
            gx = operators.matvec_g(x) + k
            oldb, oldd, olds = zb, zd, zs
            zb = np.clip(x + ub, lo, hi)
            zd = np.maximum(cx + ud, d)
            zs = project_discs_fn((gx + us).reshape(-1, 2), radii).reshape(-1)
            ub += x - zb
            ud += cx - zd
            us += gx - zs

            primal = max(_inf_norm(x - zb), _inf_norm(cx - zd), _inf_norm(gx - zs))
            dual_vector = rho * (ub + operators.rmatvec_c(ud) + operators.rmatvec_g(us))
            dual = rho * _inf_norm((zb - oldb) + operators.rmatvec_c(zd - oldd) +
                                   operators.rmatvec_g(zs - olds))
            eps_primal = CP_ABS_TOL + CP_REL_TOL * max(
                _inf_norm(x), _inf_norm(cx), _inf_norm(zb), _inf_norm(zd), _inf_norm(gx), _inf_norm(zs))
            eps_dual = CP_ABS_TOL + CP_REL_TOL * _inf_norm(dual_vector)
            stationarity = _inf_norm(operators.rmatvec_a(operators.matvec_a(x) - rhs_a) + dual_vector)
            diag = {
                'iteration': iteration, 'cg_iterations': cg_total, 'rho': rho,
                'primal': primal, 'dual': dual, 'stationarity': stationarity,
                'eps_primal': eps_primal, 'eps_dual': eps_dual,
            }
            if iteration == 1 or iteration % 200 == 0:
                entry = {**diag, 'elapsed_s': time.perf_counter() - started}
                history.append(entry)
                if progress:
                    progress(entry)
            if primal <= eps_primal and dual <= eps_dual and stationarity <= eps_dual:
                status = 'CONVERGED'
                break

            if iteration % CP_RHO_UPDATE_EVERY == 0 and iteration <= CP_RHO_UPDATE_THROUGH:
                new_rho = rho
                if primal / eps_primal > CP_RHO_BALANCE_RATIO * dual / eps_dual:
                    new_rho = min(CP_RHO_MAX, rho * CP_RHO_FACTOR)
                elif dual / eps_dual > CP_RHO_BALANCE_RATIO * primal / eps_primal:
                    new_rho = max(CP_RHO_MIN, rho / CP_RHO_FACTOR)
                if new_rho != rho:
                    ub *= rho / new_rho
                    ud *= rho / new_rho
                    us *= rho / new_rho
                    rho_updates.append({'iteration': iteration, 'old_rho': rho, 'new_rho': new_rho})
                    rho = new_rho
                    normal, preconditioner, diagonal = make_system(rho)
    except Exception:
        raise

    elapsed = time.perf_counter() - started
    yb, yd, ys = rho * ub, rho * ud, rho * us
    normal_residual = max(
        _inf_norm(zb - np.clip(zb + yb / rho, lo, hi)),
        _inf_norm(zd - np.maximum(zd + yd / rho, d)),
        _inf_norm(zs.reshape(-1, 2) - project_discs_fn((zs + ys).reshape(-1, 2), radii)),
    )
    cone = soc_kkt_fn(zs, ys, radii)
    saved_stationarity = _inf_norm(operators.rmatvec_a(operators.matvec_a(x) - rhs_a) +
                                   operators.rmatvec_c(yd) + operators.rmatvec_g(ys) + yb)
    result = {
        'status': status, **diag, 'elapsed_s': elapsed, 'rho_updates': rho_updates,
        'normal_cone_projection_residual': normal_residual,
        'soc_complementarity': cone, 'saved_stationarity': saved_stationarity,
        'memory_peak_observed_bytes': memory_peak_observed,
        'numeric_budget_seconds': runtime.numeric_budget_seconds,
        'peak_working_set_limit_bytes': runtime.peak_working_set_limit_bytes,
    }
    state = {'y_box': yb, 'y_d8': yd, 'y_face': ys,
             'z_box': zb, 'z_d8': zd, 'z_face': zs}
    return x, result, history, state
