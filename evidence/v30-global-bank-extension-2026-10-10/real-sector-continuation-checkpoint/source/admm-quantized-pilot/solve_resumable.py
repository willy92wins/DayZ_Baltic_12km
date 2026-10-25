"""Continuation-only ADMM helper, pinned to the unchanged synthetic solver.

This module does not prepare or write terrain. Its state schema stores the
unscaled dual multipliers y=rho*u so a continuation can reconstruct the exact
scaled variables used by the original ADMM loop.
"""
from __future__ import annotations

import hashlib
import importlib.util
import math
import time
from pathlib import Path

import numpy as np
from scipy.sparse.linalg import cg

ORIGINAL = Path(__file__).with_name('solve.py')
ORIGINAL_SHA256 = '7e8636bf54ba23f7e23bc2f06464100439468da7b4edca85f96c72d0cd40e149'
MAX_CUMULATIVE_ITERATION = 20000
MAX_CUMULATIVE_BUDGET_S = 600.0
MAX_CONTINUATION_BUDGET_S = 300.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load_original():
    actual = sha256(ORIGINAL)
    if actual != ORIGINAL_SHA256:
        raise RuntimeError(f'frozen solver source changed: {actual}')
    spec = importlib.util.spec_from_file_location('ev93_frozen_admm_solver', ORIGINAL)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot load frozen solver: {ORIGINAL}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_closure():
    return load_original().load_closure()


def close_float32(mod, base, nodes, raw, lo, hi, witnesses):
    return load_original().close_float32(mod, base, nodes, raw, lo, hi, witnesses)


def check_float32(base, nodes, x, lo, hi, witnesses):
    return load_original().check_float32(base, nodes, x, lo, hi, witnesses)


def objective(A, rhs, x):
    return load_original().objective(A, rhs, x)


def _counter(value, label, *, minimum=0, maximum=MAX_CUMULATIVE_ITERATION):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f'{label} must be an integer counter')
    value = int(value)
    if value < minimum or value > maximum:
        raise ValueError(f'{label} outside allowed range')
    return value


def _vector(value, n, label):
    array = np.asarray(value)
    if array.shape != (n,) or not np.issubdtype(array.dtype, np.number):
        raise ValueError(f'{label} must be a numeric vector of length {n}')
    array = np.asarray(array, dtype=np.float64)
    if not np.isfinite(array).all():
        raise ValueError(f'{label} contains non-finite values')
    return array.copy()


def validate_state(state, n, m, lo, hi, d):
    """Validate a resumable checkpoint before constructing ADMM variables."""
    required = {'x64', 'y_box', 'y_d8', 'z_box', 'z_d8', 'rho',
                'iteration', 'cg_iterations', 'rho_updates', 'elapsed_s'}
    if not isinstance(state, dict) or not required.issubset(state):
        missing = sorted(required - set(state or {})) if isinstance(state, dict) else sorted(required)
        raise ValueError(f'malformed continuation state; missing={missing}')
    x = _vector(state['x64'], n, 'x64')
    y_box = _vector(state['y_box'], n, 'y_box')
    y_d8 = _vector(state['y_d8'], m, 'y_d8')
    z_box = _vector(state['z_box'], n, 'z_box')
    z_d8 = _vector(state['z_d8'], m, 'z_d8')
    rho = float(state['rho'])
    if not math.isfinite(rho) or rho <= 0.0:
        raise ValueError('rho must be finite and positive')
    iteration = _counter(state['iteration'], 'iteration')
    cg_iterations = _counter(state['cg_iterations'], 'cg_iterations',
                             maximum=MAX_CUMULATIVE_ITERATION * 1000)
    elapsed_s = float(state['elapsed_s'])
    if not math.isfinite(elapsed_s) or elapsed_s < 0.0:
        raise ValueError('elapsed_s must be finite and nonnegative')
    updates = state['rho_updates']
    if not isinstance(updates, list):
        raise ValueError('rho_updates must be a list')
    checked_updates = []
    for row in updates:
        if not isinstance(row, dict) or set(row) != {'iteration', 'old_rho', 'new_rho'}:
            raise ValueError('malformed rho update record')
        at = _counter(row['iteration'], 'rho update iteration', minimum=1)
        old = float(row['old_rho']); new = float(row['new_rho'])
        if at > iteration or not (math.isfinite(old) and math.isfinite(new) and old > 0 and new > 0):
            raise ValueError('invalid rho update record')
        checked_updates.append({'iteration': at, 'old_rho': old, 'new_rho': new})
    if np.any(z_box < lo) or np.any(z_box > hi) or np.any(z_d8 < d):
        raise ValueError('projected ADMM variables are outside their feasible sets')
    return {'x64': x, 'y_box': y_box, 'y_d8': y_d8,
            'z_box': z_box, 'z_d8': z_d8, 'rho': rho,
            'iteration': iteration, 'cg_iterations': cg_iterations,
            'rho_updates': checked_updates, 'elapsed_s': elapsed_s}


def solve(A, rhs, C, d, lo, hi, x0, budget, progress,
          *, state=None, stop_iteration=None):
    """Run the frozen ADMM loop through a global iteration boundary.

    With no state and no stop_iteration this follows the frozen 10,000-step
    default. Continuation beyond that boundary requires an explicit
    stop_iteration in [start_iteration+1, 20,000]. `budget` is cumulative
    solver time across all chunks when a state is supplied.
    """
    frozen = load_original()
    n = A.shape[1]
    m = C.shape[0]
    if A.shape[0] != len(rhs) or C.shape[1] != n:
        raise ValueError('incompatible A/rhs/C dimensions')
    lo = _vector(lo, n, 'lo'); hi = _vector(hi, n, 'hi')
    if np.any(lo > hi):
        raise ValueError('inverted box bounds')
    d = _vector(d, m, 'd')
    x0 = _vector(x0, n, 'x0')
    if not math.isfinite(float(budget)) or float(budget) <= 0:
        raise ValueError('budget must be finite and positive')
    if float(budget) > MAX_CUMULATIVE_BUDGET_S:
        raise ValueError('cumulative solve budget exceeds the authorized 600-second ceiling')
    start = None
    if state is None:
        rho = frozen.RHO
        x = x0.copy(); zb = np.clip(x, lo, hi); zd = np.maximum(C @ x, d)
        ub = np.zeros_like(zb); ud = np.zeros_like(zd)
        iteration0 = 0; cg_total = 0; updates = []; elapsed_before = 0.0
    else:
        start = validate_state(state, n, m, lo, hi, d)
        rho = start['rho']; x = start['x64'].copy()
        zb = start['z_box'].copy(); zd = start['z_d8'].copy()
        # State stores unscaled duals. Reconstruct u before continuing.
        ub = start['y_box'] / rho; ud = start['y_d8'] / rho
        iteration0 = start['iteration']; cg_total = start['cg_iterations']
        updates = list(start['rho_updates']); elapsed_before = start['elapsed_s']
    if stop_iteration is None:
        stop_iteration = frozen.MAX_ITER
    stop_iteration = _counter(stop_iteration, 'stop_iteration', minimum=1)
    if stop_iteration <= iteration0:
        raise ValueError('stop_iteration must be after the initial checkpoint')
    if stop_iteration > MAX_CUMULATIVE_ITERATION:
        raise ValueError('stop_iteration exceeds explicit continuation ceiling')
    if state is None and stop_iteration > frozen.MAX_ITER:
        raise ValueError('extending the default run requires an explicit checkpoint')
    if elapsed_before >= float(budget):
        raise TimeoutError('cumulative solver budget already exhausted')
    if state is not None and float(budget) - elapsed_before > MAX_CONTINUATION_BUDGET_S:
        raise ValueError('continuation may add at most 300 seconds to its checkpoint')

    t0 = time.perf_counter(); op, pre, At, Ct = frozen.operator(A, C, rho)
    target = At @ rhs; status = 'ITERATION_LIMIT'; diagnostics = {}
    history = []; chunk_updates = []

    def guard(_=None):
        if elapsed_before + time.perf_counter() - t0 > float(budget):
            raise TimeoutError('Cumulative solve budget exceeded')

    for it in range(iteration0 + 1, stop_iteration + 1):
        guard(); count = [0]
        def callback(_x):
            count[0] += 1; guard()
        right = target + rho * (zb - ub + Ct @ (zd - ud))
        x, info = cg(op, right, x0=x, rtol=1e-12, atol=1e-13,
                     maxiter=1000, M=pre, callback=callback)
        cg_total += count[0]
        if info:
            raise RuntimeError(f'CG failed: info={info}, ADMM iteration={it}')
        cx = C @ x; oldb, oldd = zb, zd
        zb = np.clip(x + ub, lo, hi); zd = np.maximum(cx + ud, d)
        ub += x - zb; ud += cx - zd
        primal = max(frozen.inf(x-zb), frozen.inf(cx-zd))
        dual = rho * frozen.inf(zb-oldb + Ct @ (zd-oldd))
        eps_primal = frozen.ABS_TOL + frozen.REL_TOL * max(
            frozen.inf(x), frozen.inf(cx), frozen.inf(zb), frozen.inf(zd))
        dual_vector = rho * (ub + Ct @ ud)
        eps_dual = frozen.ABS_TOL + frozen.REL_TOL * frozen.inf(dual_vector)
        stationarity = frozen.inf(At @ (A @ x-rhs) + dual_vector)
        diagnostics = dict(iteration=it, cg_iterations=cg_total, rho=rho,
                           primal=primal, dual=dual, eps_primal=eps_primal,
                           eps_dual=eps_dual, stationarity=stationarity)
        if it == 1 or it % 200 == 0 or it == stop_iteration:
            entry = {**diagnostics,
                     'elapsed_s': elapsed_before + time.perf_counter()-t0}
            history.append(entry); progress(entry)
        if primal <= eps_primal and dual <= eps_dual and stationarity <= eps_dual:
            status = 'CONVERGED'; break
        # Preserve the original global 2,000-iteration rho adaptation boundary.
        if it % 25 == 0 and it <= 2000:
            newrho = rho
            if primal/eps_primal > 10.*dual/eps_dual:
                newrho = min(1024., rho*2.)
            elif dual/eps_dual > 10.*primal/eps_primal:
                newrho = max(1./1024., rho/2.)
            if newrho != rho:
                # Keep the unscaled dual multiplier y=rho*u invariant.
                ub *= rho/newrho; ud *= rho/newrho
                row = dict(iteration=it, old_rho=rho, new_rho=newrho)
                updates.append(row); chunk_updates.append(row)
                rho = newrho; op, pre, At, Ct = frozen.operator(A, C, rho)
    elapsed_total = elapsed_before + time.perf_counter() - t0
    saved = {'x64': x.copy(), 'y_box': rho*ub, 'y_d8': rho*ud,
             'z_box': zb.copy(), 'z_d8': zd.copy(), 'rho': rho,
             'iteration': int(diagnostics['iteration']) if diagnostics else iteration0,
             'cg_iterations': cg_total, 'rho_updates': updates,
             'elapsed_s': elapsed_total}
    diagnostics.update(status=status, elapsed_s=elapsed_total,
                       rho_updates=updates)
    return x, diagnostics, history, saved
