#!/usr/bin/env python
"""Author one local float32 order closure from the frozen EV93 continuation.

This creates no terrain package and does not claim the rejected parent run
produced a candidate. The real execution is intentionally separate from tests.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
RS = HERE.parent
G = RS.parent
PLAN = RS / 'PLAN_ORDER_CLOSURE.md'
PREFLIGHT = RS / 'preflight-run-03-continuation' / 'preflight.json'
PREPARED = RS / 'preflight-run-03-continuation' / 'prepared.npz'
PARENT_RESULT = RS / 'solve-run-03-continuation' / 'solve-result.json'
PARENT_STATE = RS / 'solve-run-03-continuation' / 'solver-state.npz'
PARENT_DRIVER = RS / 'solve_real_sector_continuation.py'
FROZEN_SOLVER = G / 'admm-quantized-pilot' / 'solve.py'
RESUMABLE_SOLVER = G / 'admm-quantized-pilot' / 'solve_resumable.py'
PROJECTION = HERE / 'projection.py'
OUT = HERE / 'author-run-01'

EXPECTED = {
    'PLAN': '385a95391eba4be1a2777974f9b7b200c7d9e02770174b60ee9ad922d3cb6738',
    'PREFLIGHT': 'bd0f50b709c297cdba1442425e6fc3957b95d67dcc46f7c44d23bd65ae66996d',
    'PREPARED': '8a8a1cf8e9b6906b1aab8053877383d01a92baa5bd2c18b54b1b9e43c8c37a21',
    'PARENT_RESULT': '8345bd1763af30ed7c06f621ab14cc91b6bb79d8359ec76a146b8ef85d767a0c',
    'PARENT_STATE': '8618d5941d7c8b235bedce6ad5e21a0053ec61a2a32c17532fec98ff9db3dfa9',
    'PARENT_DRIVER': '7a8625a43f1610322f1f32bc1d20bbb5b7fcace1e3259bec7577c0c27660e9cb',
    'FROZEN_SOLVER': '7e8636bf54ba23f7e23bc2f06464100439468da7b4edca85f96c72d0cd40e149',
    'RESUMABLE_SOLVER': 'b852af714667e8b07944a97fbdbaba97fe0c2b90c3a555ff9821ef11fe6791d2',
    'PROJECTION': 'a990dc2d33fca4fd2a446b958f0412a2d752a5d3072a85d82058bb634cfaf44b',
}
NUMERIC_LIMIT_S = 120.0
PEAK_WS_LIMIT = 1610612736
MIN_AVAILABLE_PHYSICAL = 3221225472


class ProcessCounters(ctypes.Structure):
    _fields_ = [('cb', ctypes.c_ulong), ('PageFaultCount', ctypes.c_ulong)] + [
        (name, ctypes.c_size_t) for name in (
            'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
            'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]


class MemoryStatus(ctypes.Structure):
    _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
                ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]


def sha(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def source_paths():
    return {
        'PLAN': PLAN, 'PREFLIGHT': PREFLIGHT, 'PREPARED': PREPARED,
        'PARENT_RESULT': PARENT_RESULT, 'PARENT_STATE': PARENT_STATE,
        'PARENT_DRIVER': PARENT_DRIVER, 'FROZEN_SOLVER': FROZEN_SOLVER,
        'RESUMABLE_SOLVER': RESUMABLE_SOLVER, 'PROJECTION': PROJECTION,
        'AUTHOR': Path(__file__).resolve(),
    }


def get_memory_snapshot():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    kernel.GetCurrentProcess.argtypes = []
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(ProcessCounters), ctypes.c_ulong]
    psapi.GetProcessMemoryInfo.restype = ctypes.c_int
    c = ProcessCounters(); c.cb = ctypes.sizeof(c)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(c), c.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    status = MemoryStatus(); status.dwLength = ctypes.sizeof(status)
    kernel.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MemoryStatus)]
    kernel.GlobalMemoryStatusEx.restype = ctypes.c_int
    if not kernel.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise ctypes.WinError(ctypes.get_last_error())
    return {'pid': os.getpid(), 'peak_working_set_bytes': int(c.PeakWorkingSetSize),
            'working_set_bytes': int(c.WorkingSetSize),
            'available_physical_bytes': int(status.ullAvailPhys),
            'method': 'GetProcessMemoryInfo + GlobalMemoryStatusEx'}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot import pinned module {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def witness_rc_to_flat_edges(witness_edges_rc: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """Map stored rows (center_r,center_c,witness_r,witness_c) to w->center IDs."""
    rows = np.asarray(witness_edges_rc)
    if rows.ndim != 2 or rows.shape[1] != 4 or not np.issubdtype(rows.dtype, np.integer):
        raise ValueError('witness_edges_rc must be integer (E,4), center then witness')
    nr, nc = map(int, shape)
    rows = np.asarray(rows, dtype=np.int64)
    if rows.size and (np.any(rows[:, 0] < 0) or np.any(rows[:, 0] >= nr)
                      or np.any(rows[:, 1] < 0) or np.any(rows[:, 1] >= nc)
                      or np.any(rows[:, 2] < 0) or np.any(rows[:, 2] >= nr)
                      or np.any(rows[:, 3] < 0) or np.any(rows[:, 3] >= nc)):
        raise ValueError('witness_edges_rc coordinate outside raster')
    center = rows[:, 0] * nc + rows[:, 1]
    witness = rows[:, 2] * nc + rows[:, 3]
    return np.column_stack((witness, center)).astype(np.int64, copy=False)


def json_dump(path: Path, obj: dict):
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def verify_static_pins():
    actual = {label: sha(path) for label, path in source_paths().items()}
    for label, expected in EXPECTED.items():
        if actual[label] != expected:
            raise RuntimeError(f'{label} SHA drift: {actual[label]} != {expected}')
    return actual


def read_inputs(source_read_set: dict[str, str]):
    pre = json.loads(PREFLIGHT.read_text(encoding='utf-8'))
    parent = json.loads(PARENT_RESULT.read_text(encoding='utf-8'))
    if pre.get('status') != 'PREFLIGHT_READY_ONLY':
        raise RuntimeError('pinned preflight is not ready-only')
    if parent.get('status') != 'REJECTED_LOCAL_NUMERIC_GATES':
        raise RuntimeError('parent result status changed; expected rejected numeric gates')
    if parent.get('candidate_path') is not None or parent.get('candidate_sha256') is not None:
        raise RuntimeError('rejected parent unexpectedly names a candidate')
    if parent.get('diagnostics', {}).get('status') != 'CONVERGED':
        raise RuntimeError('parent continuous solver did not converge')
    expected_refs = {
        str(PREFLIGHT): EXPECTED['PREFLIGHT'], str(PREPARED): EXPECTED['PREPARED'],
        str(PARENT_RESULT): EXPECTED['PARENT_RESULT'], str(PARENT_STATE): EXPECTED['PARENT_STATE'],
    }
    readset = pre.get('source_hashes_end')
    if not isinstance(readset, dict) or not readset:
        raise RuntimeError('preflight source readset missing')
    if readset != parent.get('source_hashes_after'):
        raise RuntimeError('parent and preflight end readsets differ')
    source_read_set.update(readset)
    for path_text, expected in readset.items():
        path = Path(path_text)
        if not path.is_file() or sha(path) != expected:
            raise RuntimeError(f'pinned source readset drift: {path_text}')
    for path_text, expected in expected_refs.items():
        source_read_set[path_text] = expected
    for label, path in source_paths().items():
        source_read_set[str(path)] = sha(path)
    artifact = pre.get('prepared_artifact', {})
    if artifact.get('path') != str(PREPARED) or artifact.get('sha256') != EXPECTED['PREPARED']:
        raise RuntimeError('preflight prepared-artifact binding mismatch')
    if parent.get('preflight_path') != str(PREFLIGHT) or parent.get('preflight_sha256') != EXPECTED['PREFLIGHT']:
        raise RuntimeError('parent does not bind the pinned preflight')
    if parent.get('prepared_path') != str(PREPARED) or parent.get('prepared_sha256') != EXPECTED['PREPARED']:
        raise RuntimeError('parent does not bind the pinned prepared arrays')
    if parent.get('solver_state_path') != str(PARENT_STATE) or parent.get('solver_state_sha256') != EXPECTED['PARENT_STATE']:
        raise RuntimeError('parent does not bind the pinned solver state')
    with np.load(PREPARED, allow_pickle=False) as archive:
        prepared = {key: archive[key] for key in archive.files}
    with np.load(PARENT_STATE, allow_pickle=False) as archive:
        state = {key: archive[key] for key in archive.files}
    return pre, parent, prepared, state


def unpack_prepared(prepared):
    expected_keys = {'base_local', 'nodes_local', 'lo', 'hi', 'x0', 'A_data', 'A_indices',
                     'A_indptr', 'A_shape', 'rhs', 'C_data', 'C_indices', 'C_indptr',
                     'C_shape', 'd', 'witnesses_json'}
    if not expected_keys.issubset(prepared):
        raise RuntimeError(f'prepared archive missing keys: {sorted(expected_keys-set(prepared))}')
    base = np.asarray(prepared['base_local'], dtype=np.float32)
    nodes = np.asarray(prepared['nodes_local'], dtype=np.int32)
    lo64 = np.asarray(prepared['lo'], dtype=np.float64)
    hi64 = np.asarray(prepared['hi'], dtype=np.float64)
    if base.shape != (260, 260) or nodes.ndim != 2 or nodes.shape[1] != 2:
        raise RuntimeError('prepared local base/nodes dimensions changed')
    if len(nodes) != 40512 or lo64.shape != (len(nodes),) or hi64.shape != (len(nodes),):
        raise RuntimeError('prepared variable/bound population changed')
    if not np.array_equal(lo64, lo64.astype(np.float32).astype(np.float64)):
        raise RuntimeError('lower bounds are not exact inward float32 values')
    if not np.array_equal(hi64, hi64.astype(np.float32).astype(np.float64)):
        raise RuntimeError('upper bounds are not exact inward float32 values')
    A = sparse.csr_matrix((prepared['A_data'], prepared['A_indices'], prepared['A_indptr']),
                          shape=tuple(map(int, prepared['A_shape'])))
    C = sparse.csr_matrix((prepared['C_data'], prepared['C_indices'], prepared['C_indptr']),
                          shape=tuple(map(int, prepared['C_shape'])))
    rhs = np.asarray(prepared['rhs'], dtype=np.float64)
    d = np.asarray(prepared['d'], dtype=np.float64)
    x0 = np.asarray(prepared['x0'], dtype=np.float64)
    if (A.shape[1] != len(nodes) or rhs.shape != (A.shape[0],)
            or C.shape != (len(d), len(nodes)) or x0.shape != (len(nodes),)):
        raise RuntimeError('prepared operator dimensions are inconsistent')
    witnesses = json.loads(prepared['witnesses_json'].tobytes().decode('utf-8'))
    if len(witnesses) != 43258:
        raise RuntimeError('prepared D8 witness count changed')
    return base, nodes, lo64, hi64, A, rhs, C, d, x0, witnesses


def reconstruct_state(base, nodes, lo64, hi64, state):
    required = {'x64', 'y_box', 'y_d8', 'z_box', 'z_d8', 'raw_float32', 'nodes_local', 'lo', 'hi'}
    if not required.issubset(state):
        raise RuntimeError(f'parent state missing arrays: {sorted(required-set(state))}')
    if not np.array_equal(nodes, state['nodes_local']):
        raise RuntimeError('parent node order differs from prepared population')
    if not np.array_equal(lo64, state['lo']) or not np.array_equal(hi64, state['hi']):
        raise RuntimeError('parent inward bounds differ from prepared bounds')
    x = np.asarray(state['x64'], dtype=np.float64)
    raw = base.copy()
    raw[tuple(nodes.T)] = x.astype(np.float32)
    raw_saved = np.asarray(state['raw_float32'], dtype=np.float32)
    if raw_saved.shape != base.shape or not np.array_equal(raw, raw_saved):
        raise RuntimeError('parent raw grid is not the direct float32 cast over fixed B')
    for key in ('y_box', 'z_box'):
        if state[key].shape != x.shape or not np.isfinite(state[key]).all():
            raise RuntimeError(f'parent state {key} dimensions/finiteness invalid')
    for key in ('y_d8', 'z_d8'):
        if state[key].shape != (41140,):
            raise RuntimeError(f'parent state {key} has unexpected length')
        if not np.isfinite(state[key]).all():
            raise RuntimeError(f'parent state {key} contains non-finite values')
    return raw


def kkt_report(parent, A, rhs, C, d, lo, hi, x, state):
    diag = parent['diagnostics']
    rho = float(diag['rho'])
    if not math.isfinite(rho) or rho <= 0:
        raise RuntimeError('parent rho invalid')
    yb = np.asarray(state['y_box'], np.float64)
    yd = np.asarray(state['y_d8'], np.float64)
    zb = np.asarray(state['z_box'], np.float64)
    zd = np.asarray(state['z_d8'], np.float64)
    infnorm = lambda v: float(np.max(np.abs(v), initial=0.0))
    primal_box = infnorm(x-zb)
    primal_d8 = infnorm(C@x-zd)
    box_feas = float(max(np.max(lo-x, initial=0.0), np.max(x-hi, initial=0.0)))
    d8_feas = float(np.max(d-C@x, initial=0.0))
    stationarity = np.asarray(A.T@(A@x-rhs)).reshape(-1)+yb+np.asarray(C.T@yd).reshape(-1)
    stationarity_inf = infnorm(stationarity)
    eps_p = 1e-10 + 1e-8*max(infnorm(x), infnorm(C@x), infnorm(zb), infnorm(zd))
    eps_d = 1e-10 + 1e-8*infnorm(yb+np.asarray(C.T@yd).reshape(-1))
    eps_match = (math.isclose(float(diag.get('eps_primal', math.nan)), eps_p, rel_tol=1e-12, abs_tol=1e-18)
                 and math.isclose(float(diag.get('eps_dual', math.nan)), eps_d, rel_tol=1e-12, abs_tol=1e-18))
    dual_sign_bad = int(np.count_nonzero(yd > 1e-12))
    box_normal = infnorm(np.clip(zb+yb/rho, lo, hi)-zb)
    d8_normal = infnorm(np.maximum(zd+yd/rho, d)-zd)
    passed = bool(diag.get('status') == 'CONVERGED' and eps_match
                  and box_feas <= eps_p and d8_feas <= eps_p
                  and primal_box <= eps_p and primal_d8 <= eps_p
                  and stationarity_inf <= eps_d and dual_sign_bad == 0
                  and box_normal <= 1e-10 and d8_normal <= 1e-10)
    return {'pass': passed, 'primal_box_inf': primal_box, 'primal_d8_inf': primal_d8,
            'box_feasibility': box_feas, 'd8_feasibility': d8_feas,
            'stationarity_inf': stationarity_inf, 'd8_dual_positive_count': dual_sign_bad,
            'box_normal_cone_inf': box_normal, 'd8_normal_cone_inf': d8_normal,
            'eps_primal_reconstructed': eps_p, 'eps_dual_reconstructed': eps_d,
            'reported_tolerances_match': eps_match}


def execute() -> int:
    if OUT.exists():
        raise FileExistsError(f'fresh-only output already exists: {OUT}')
    OUT.mkdir(parents=False, exist_ok=False)
    receipt_path = OUT / 'receipt.json'
    started = time.perf_counter()
    started_unix = time.time()
    numeric_start = None
    numeric_elapsed = None
    pending_candidate = None
    status = 'ERROR'
    try:
        source_start = verify_static_pins()
        readset = {}
        pre, parent, prepared, state = read_inputs(readset)
        base, nodes, lo64, hi64, A, rhs, C, d, x0, witnesses = unpack_prepared(prepared)
        x = np.asarray(state['x64'], dtype=np.float64)
        raw = reconstruct_state(base, nodes, lo64, hi64, state)
        memory_before = get_memory_snapshot()
        if memory_before['available_physical_bytes'] < MIN_AVAILABLE_PHYSICAL:
            raise MemoryError('less than 3 GiB available physical memory')
        numeric_start = time.perf_counter()
        deadline = numeric_start + NUMERIC_LIMIT_S

        def guard():
            if time.perf_counter() > deadline:
                raise TimeoutError('120-second numerical operation limit exceeded')
            snap = get_memory_snapshot()
            if snap['peak_working_set_bytes'] > PEAK_WS_LIMIT:
                raise MemoryError('1.5-GiB peak working-set limit exceeded')

        frozen = load_module('ev93_order_closure_frozen_solver', FROZEN_SOLVER)
        mutable = np.zeros(base.shape, dtype=bool)
        mutable[tuple(nodes.T)] = True
        lower_grid = base.copy()
        upper_grid = base.copy()
        lower_grid[tuple(nodes.T)] = lo64.astype(np.float32)
        upper_grid[tuple(nodes.T)] = hi64.astype(np.float32)
        fixed_grid = ~mutable
        edges_rc = np.asarray([(w['center'][0], w['center'][1],
                                w['witness'][0], w['witness'][1]) for w in witnesses], dtype=np.int32)
        projector = load_module('ev93_order_projection_runtime', PROJECTION)
        edges = witness_rc_to_flat_edges(edges_rc, base.shape)
        projected = projector.project_order(
            raw.ravel(), lower_grid.ravel(), upper_grid.ravel(), edges,
            baseline=base.ravel(), fixed=fixed_grid.ravel(), guard=guard)
        guard()
        q = projected['q'].reshape(base.shape)
        clipped = projected['clipped'].reshape(base.shape)
        upper_propagated = projected['upper_propagated'].reshape(base.shape)
        kkt = kkt_report(parent, A, rhs, C, d, lo64, hi64, x, state)
        _, f32_stats = frozen.check_float32(base, nodes, q[tuple(nodes.T)],
                                            lo64, hi64, witnesses)
        raw_values = raw[tuple(nodes.T)].astype(np.float64)
        final_values = q[tuple(nodes.T)].astype(np.float64)
        raw_cost = frozen.objective(A, rhs, raw_values)
        final_cost = frozen.objective(A, rhs, final_values)
        base_cost = frozen.objective(A, rhs, x0)
        objective_gates = load_module('ev93_order_projection_objective', PROJECTION).evaluate_objective_gates(
            raw_cost, final_cost, base_cost)
        allowance = objective_gates['allowance']
        projection_ok = bool(np.all(q >= lower_grid) and np.all(q <= upper_propagated)
                             and np.array_equal(q[fixed_grid], base[fixed_grid])
                             and np.max(np.abs(q.astype(np.float64)-raw.astype(np.float64)), initial=0.0)
                             <= projected['a_priori_correction_bound'])
        gates = {
            'parent_continuous_kkt_reconstructed': kkt['pass'],
            'exact_float32_box_d8_fixed_and_minima': bool(f32_stats.get('pass')),
            'reverse_upper_forward_order_projection': projection_ok,
            'a_priori_b_plus_V_correction_bound': bool(projected['max_abs_correction']
                                                      <= projected['a_priori_correction_bound']),
            'objective_closure_budget': objective_gates['closure_budget_pass'],
            'strict_objective_improvement_vs_B': objective_gates['strict_improvement_vs_baseline'],
            'source_readset_stable': False,
        }
        guard()
        if numeric_start is None:
            raise AssertionError('numeric timer was not started')
        numeric_elapsed = time.perf_counter() - numeric_start
        memory_numeric_end = get_memory_snapshot()
        gates['resource_limits'] = bool(numeric_elapsed <= NUMERIC_LIMIT_S
                                        and memory_numeric_end['peak_working_set_bytes'] <= PEAK_WS_LIMIT)

        # Hash I/O is part of the complete readset check, but not part of the
        # numeric-operation budget defined by the approved plan.
        readset_end = {path_text: sha(path_text) for path_text in readset}
        gates['source_readset_stable'] = readset_end == readset
        source_end = verify_static_pins()
        if source_start != source_end or source_start['AUTHOR'] != sha(Path(__file__).resolve()):
            gates['source_readset_stable'] = False
        status = 'SOLUTION_PENDING_INDEPENDENT_CONSUMER' if all(gates.values()) else 'REJECTED_LOCAL_NUMERIC_GATES'
        candidate_path = OUT / 'candidate-local.npz'
        candidate_sha = None
        if status == 'SOLUTION_PENDING_INDEPENDENT_CONSUMER':
            pending_candidate = OUT / 'candidate-local.npz.pending'
            with pending_candidate.open('xb') as stream:
                np.savez_compressed(
                    stream, heights=q.astype(np.float32, copy=False), raw_float32=raw,
                    clipped_float32=clipped, upper_propagated=upper_propagated,
                    lower_grid=lower_grid, upper_grid=upper_grid, base_local=base,
                    nodes_local=nodes, lo=lo64, hi=hi64, witness_edges_rc=edges_rc)
            memory_after_write = get_memory_snapshot()
            if memory_after_write['peak_working_set_bytes'] > PEAK_WS_LIMIT:
                gates['resource_limits'] = False
                status = 'RESOURCE_LIMIT'
                pending_candidate.unlink()
                pending_candidate = None
            else:
                os.replace(pending_candidate, candidate_path)
                pending_candidate = None
                candidate_sha = sha(candidate_path)
        else:
            memory_after_write = memory_numeric_end
        receipt = {
            'schema': 'ev93.order-closure-author.v1', 'status': status,
            'scope': 'one deterministic local order closure; no terrain/map acceptance',
            'parent': {'result_path': str(PARENT_RESULT), 'result_sha256': EXPECTED['PARENT_RESULT'],
                       'status': parent['status'], 'candidate_path': parent.get('candidate_path'),
                       'candidate_sha256': parent.get('candidate_sha256'),
                       'solver_state_path': str(PARENT_STATE), 'solver_state_sha256': EXPECTED['PARENT_STATE']},
            'preflight': {'path': str(PREFLIGHT), 'sha256': EXPECTED['PREFLIGHT'],
                          'prepared_path': str(PREPARED), 'prepared_sha256': EXPECTED['PREPARED']},
            'source_read_set': readset, 'source_read_set_end': readset_end,
            'author_sources': {str(path): source_start[label] for label, path in source_paths().items()},
            'projection': {k: v for k, v in projected.items() if not isinstance(v, np.ndarray)},
            'objective': {'B_affected': base_cost, 'raw_float32': raw_cost,
                          'closed_float32': final_cost, 'closure_delta': final_cost-raw_cost,
                          'allowed_closure_increase': allowance},
            'kkt': kkt, 'float32_check': f32_stats, 'gates_local_numeric': gates,
            'candidate_path': str(candidate_path) if candidate_sha else None,
            'candidate_sha256': candidate_sha,
            'artifacts': {'candidate_npz_arrays': ['heights', 'raw_float32', 'clipped_float32',
                            'upper_propagated', 'lower_grid', 'upper_grid', 'base_local',
                            'nodes_local', 'lo', 'hi', 'witness_edges_rc']},
            'resource': {'numeric_elapsed_seconds': numeric_elapsed,
                         'numeric_limit_seconds': NUMERIC_LIMIT_S,
                         'peak_working_set_bytes': memory_after_write['peak_working_set_bytes'],
                         'peak_working_set_limit_bytes': PEAK_WS_LIMIT,
                         'available_physical_bytes_before': memory_before['available_physical_bytes'],
                         'minimum_available_physical_bytes': MIN_AVAILABLE_PHYSICAL,
                         'measurement': memory_after_write['method']},
            'timestamps': {'started_unix': started_unix, 'elapsed_total_seconds': time.perf_counter()-started},
        }
        json_dump(receipt_path, receipt)
        print(json.dumps({'status': status, 'candidate_path': receipt['candidate_path'],
                          'candidate_sha256': candidate_sha, 'gates': gates}, sort_keys=True))
        return 0 if status == 'SOLUTION_PENDING_INDEPENDENT_CONSUMER' else 1
    except Exception as exc:
        if pending_candidate is not None and pending_candidate.exists():
            pending_candidate.unlink()
        receipt = {'schema': 'ev93.order-closure-author.v1', 'status': 'ERROR',
                   'scope': 'one deterministic local order closure; no terrain/map acceptance',
                   'error_type': type(exc).__name__, 'error': str(exc),
                   'candidate_path': None, 'candidate_sha256': None,
                   'parent': {'result_path': str(PARENT_RESULT),
                              'result_sha256': EXPECTED['PARENT_RESULT'],
                              'status': 'REJECTED_LOCAL_NUMERIC_GATES',
                              'solver_state_sha256': EXPECTED['PARENT_STATE']},
                   'timestamps': {'elapsed_total_seconds': time.perf_counter()-started}}
        if numeric_start is not None:
            receipt['resource'] = {'numeric_elapsed_seconds': numeric_elapsed if numeric_elapsed is not None
                                   else time.perf_counter()-numeric_start,
                                   'numeric_limit_seconds': NUMERIC_LIMIT_S}
        json_dump(receipt_path, receipt)
        print(json.dumps({'status': 'ERROR', 'error_type': type(exc).__name__,
                          'error': str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true',
                        help='run the one fresh-only numerical authoring attempt')
    args = parser.parse_args(argv)
    if not args.execute:
        parser.error('no action requested; --execute is required (not run during source review)')
    return execute()


if __name__ == '__main__':
    raise SystemExit(main())
