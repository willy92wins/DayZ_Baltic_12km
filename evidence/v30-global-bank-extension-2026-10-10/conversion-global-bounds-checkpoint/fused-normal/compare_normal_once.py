"""One-shot comparison of the frozen old and fused normal actions.

This driver performs exactly one old normal matvec and one fused normal
matvec on the same EV95 operator, vector, and rho. It never runs a solver or
writes terrain. The external independent review must pin this file's final
SHA before --review-sha256 can authorize a run.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import time

import numpy as np

HERE = Path(__file__).resolve().parent
STRUCTURED_DIR = HERE.parent
PROTO = STRUCTURED_DIR.parent
INPUT_H = Path(r'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\build-wide-slope\candidate\terrain.npz')
MASKS = PROTO / 'global-sizing-ev95' / 'run-05' / 'masks.npz'
RECEIPT = PROTO / 'global-sizing-ev95' / 'run-05' / 'preflight.json'
OLD_OPERATOR = STRUCTURED_DIR / 'structured_operator.py'
FUSED = HERE / 'fused_normal.py'
OLD_DRIVER = STRUCTURED_DIR / 'measure_global_actions.py'
FIXTURE_SOURCE = HERE / 'test_optimized_normal.py'
FIXTURE_REPORT = HERE / 'fixture-report.json'
PLAN = HERE / 'PLAN.md'
FUSED_REVIEW = HERE / 'independent-review.json'
OLD_MEASUREMENT = STRUCTURED_DIR / 'measurement' / 'run-01' / 'measurement.json'
OLD_MARKER = STRUCTURED_DIR / 'measurement' / 'run-01' / 'bench-invocation.started.json'
COMPARISON_DIR = HERE / 'comparison'
REVIEW = COMPARISON_DIR / 'independent-review.json'
RUN_DIR = COMPARISON_DIR / 'run-01'
REPORT = RUN_DIR / 'comparison.json'
MARKER = RUN_DIR / 'comparison-invocation.started.json'

PINS = {
    str(INPUT_H): '40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a',
    str(MASKS): '8f5959308923263538440d29dd93960c5331bc8f13c88b61590380c17d6cdfff',
    str(RECEIPT): 'b6507c73af2181860c13a04ed1814a1a508d0448cd9b63520854aad029ae0f95',
    str(OLD_OPERATOR): 'd3017e58bbae3b71c891fab6892a5bf8d9386ae8a51a451a94c9b05769ac750a',
    str(FUSED): '19a3e3a493f643702e66aaf265c705739535d386412f74659369d7746117ffaa',
    str(OLD_DRIVER): 'a05a5f47b775567105c3e588e7106b4b365b58d259f018dca4f243f57d2da37b',
    str(FIXTURE_SOURCE): 'b1fb0161fa4fadc0070eb9fedba5277e8666487ee9ae3f2413a24d57570584b7',
    str(FIXTURE_REPORT): '7be436060c506139655a215d20d5a1bad324ed528c60ff1abf0f7bc637b1b79e',
    str(PLAN): '70a19038895d1ca949c6a27cf5539ac8c62796be96aa9405d1ee52a6c1a0a62d',
    str(FUSED_REVIEW): '8dbf63c155d740dabd3e3d6cefc6da9a613bc7d588b58b5d8cb40b671d5a084d',
    str(OLD_MEASUREMENT): '41af5865c4606f41c930c15b21d5fb5729f20c09305ecb54fee1c6cb6e92d4c0',
    str(OLD_MARKER): '83681729ff893fdbf64a91ebb8104910aac4e1c503d92b3e077236d49c0b71fb',
}

RHO = 8.0
MIN_FREE_BYTES = 6 * 1024**3
NUMERIC_BUDGET_S = 120.0
TOL_ABS = 1e-10
COMPARISON_REVIEW_STATUS = 'PASS_OPTIMIZED_NORMAL_COMPARISON_DRIVER'
FUSED_REVIEW_STATUS = 'SOUND_WITH_DOCUMENTATION_NOTE'


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def rehash_paths(paths):
    return {str(Path(p).resolve()): sha256_file(Path(p)) for p in paths}


def verify_pins(pins):
    observed = {}
    for raw, expected in pins.items():
        path = Path(raw).resolve()
        actual = sha256_file(path)
        if actual != str(expected).lower():
            raise RuntimeError(f'frozen source/input pin mismatch: {path}')
        observed[str(path)] = actual
    return observed


def load_verified_module(path: Path, expected_sha: str, name: str):
    resolved = path.resolve()
    data = resolved.read_bytes()
    actual = sha256_bytes(data)
    if actual != expected_sha.lower():
        raise RuntimeError(f'{name} changed before verified load')
    spec = importlib.util.spec_from_loader(name, loader=None, origin=str(resolved))
    if spec is None:
        raise ImportError(f'cannot construct module spec for {name}')
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(resolved)
    exec(compile(data, str(resolved), 'exec'), module.__dict__)
    return module, actual


def review_gate(path: Path, expected_sha: str, driver_sha: str, readset_start):
    raw = path.resolve().read_bytes()
    actual = sha256_bytes(raw)
    if actual != expected_sha.lower():
        raise RuntimeError('comparison review SHA does not match supplied pin')
    doc = json.loads(raw.decode('utf-8-sig'))
    expected = {
        'schema': 'optimized-normal.comparison-driver-review.v1',
        'status': COMPARISON_REVIEW_STATUS,
        'driver_path': str(Path(__file__).resolve()),
        'driver_sha256': driver_sha,
        'fused_source_sha256': PINS[str(FUSED)],
        'structured_operator_sha256': PINS[str(OLD_OPERATOR)],
        'old_driver_sha256': PINS[str(OLD_DRIVER)],
        'plan_sha256': PINS[str(PLAN)],
        'fixture_source_sha256': PINS[str(FIXTURE_SOURCE)],
        'fixture_report_sha256': PINS[str(FIXTURE_REPORT)],
        'fused_independent_review_sha256': PINS[str(FUSED_REVIEW)],
        'old_measurement_sha256': PINS[str(OLD_MEASUREMENT)],
    }
    for key, value in expected.items():
        if doc.get(key) != value:
            raise RuntimeError(f'independent comparison review mismatch: {key}')
    if doc.get('old_measurement_status') != 'PASS_GLOBAL_MATRIX_FREE_ACTION_MEASUREMENT':
        raise RuntimeError('review does not bind a passing prior action measurement')
    key = str(path.resolve())
    if readset_start.get(key) != actual:
        raise RuntimeError('comparison review differs from initial read-set')
    for raw_path, pin in PINS.items():
        if readset_start.get(str(Path(raw_path).resolve())) != pin:
            raise RuntimeError(f'initial read-set does not bind input: {raw_path}')
    if readset_start.get(str(Path(__file__).resolve())) != driver_sha:
        raise RuntimeError('driver differs from initial read-set')
    return doc, actual


def validate_historical_receipts():
    old = json.loads(OLD_MEASUREMENT.read_text(encoding='utf-8-sig'))
    marker = json.loads(OLD_MARKER.read_text(encoding='utf-8-sig'))
    fused_review = json.loads(FUSED_REVIEW.read_text(encoding='utf-8-sig'))
    sizing = json.loads(RECEIPT.read_text(encoding='utf-8-sig'))
    if old.get('status') != 'PASS_GLOBAL_MATRIX_FREE_ACTION_MEASUREMENT':
        raise RuntimeError('previous matrix-free action receipt is not PASS')
    if old.get('solve_executed') is not False or old.get('terrain_written') is not False:
        raise RuntimeError('previous measurement unexpectedly ran a solver or wrote terrain')
    if marker.get('state') != 'FINISHED' or marker.get('report_sha256') != PINS[str(OLD_MEASUREMENT)]:
        raise RuntimeError('previous measurement marker does not bind its report')
    if fused_review.get('status') != FUSED_REVIEW_STATUS:
        raise RuntimeError('fused operator review status mismatch')
    if fused_review.get('source_sha256') != PINS[str(FUSED)] or fused_review.get('operator_reference_sha256') != PINS[str(OLD_OPERATOR)]:
        raise RuntimeError('fused operator review source identities mismatch')
    if fused_review.get('fixture_report_sha256') != PINS[str(FIXTURE_REPORT)] or fused_review.get('plan_sha256') != PINS[str(PLAN)]:
        raise RuntimeError('fused operator review fixture/plan identities mismatch')
    if sizing.get('status') != 'READ_ONLY_RESOURCE_PREFLIGHT_COMPLETE':
        raise RuntimeError('EV95 resource preflight status mismatch')
    if sizing.get('identity', {}).get('EV95_sha256') != PINS[str(INPUT_H)]:
        raise RuntimeError('EV95 resource preflight does not bind height input')
    if sizing.get('masks_artifact', {}).get('sha256') != PINS[str(MASKS)]:
        raise RuntimeError('EV95 resource preflight does not bind masks')
    # The historical action-measurement report stores counts directly under
    # operator_counts; the sizing receipt nests them under EV95_delta_variable.
    # Cross-check these real schemas before either is used to construct the
    # comparison operator.
    old_counts = old.get('operator_counts')
    sizing_counts = sizing.get('operator_counts', {}).get('EV95_delta_variable')
    if not isinstance(old_counts, dict) or not isinstance(sizing_counts, dict):
        raise RuntimeError('historical receipt operator_counts schema missing')
    if int(old_counts.get('variables', -1)) != int(sizing_counts.get('variables', -2)):
        raise RuntimeError('old measurement and sizing variable counts differ')
    for family in ('A', 'C', 'G'):
        old_family = old_counts.get(family)
        sizing_family = sizing_counts.get(family)
        if not isinstance(old_family, dict) or not isinstance(sizing_family, dict):
            raise RuntimeError(f'historical receipt missing {family} row/nnz counts')
        for field in ('rows', 'nnz'):
            if int(old_family.get(field, -1)) != int(sizing_family.get(field, -2)):
                raise RuntimeError(f'historical receipt {family}.{field} differs between measurement and sizing')
    expected_fixed = 2048 * 2048 - int(old_counts['variables'])
    if int(old_counts.get('fixed_vertices', -1)) != expected_fixed:
        raise RuntimeError('historical measurement fixed-vertex count is inconsistent with the pinned map shape')
    action_counts = old.get('action_counts', {})
    for family in ('A', 'C', 'G'):
        family_actions = action_counts.get(family, {})
        if family_actions.get('matvec') != 1 or family_actions.get('rmatvec') != 1:
            raise RuntimeError(f'historical measurement {family} action count is not exactly one each')
    return old, sizing


def estimate_increment_bytes(n: int, shape, persistent: int, masks_bytes: int):
    h, w = map(int, shape)
    grid = 8 * h * w
    nvec = 8 * int(n)
    # Retained input vector + both action outputs. Fused temporaries are three
    # float64 grids, three anchor masks, and the explicit .0625*x N-vector.
    # The additional 1 GiB is a conservative allowance for old A/C/G callback
    # intermediates and comparison temporaries; it is not a measured peak.
    explicit = persistent + 3 * nvec + 3 * grid + masks_bytes + nvec + 1024**3
    parts = {
        'persistent_operator_arrays': int(persistent),
        'three_full_float64_grids': int(3 * grid),
        'three_N_float64_vectors_x_old_output_new_output': int(3 * nvec),
        'fused_identity_term_0_0625_times_x_transient': int(nvec),
        'fused_boolean_anchor_masks': int(masks_bytes),
        'callback_and_comparison_scratch_reserve': int(1024**3),
    }
    return parts, int(explicit)


def validate_input_data(npz_path: Path, masks_path: Path, sizing_receipt, H, mask):
    shape = (2048, 2048)
    if H.shape != shape or H.dtype != np.float64 or not np.isfinite(H).all():
        raise ValueError('EV95 heights must be finite float64 loaded from the pinned float32 archive')
    if mask.shape != shape or mask.dtype != np.uint8 or np.any((mask != 0) & (mask != 1)):
        raise ValueError('EV95 variable mask shape/dtype/value mismatch')
    counts = sizing_receipt['operator_counts']['EV95_delta_variable']
    n = int(np.count_nonzero(mask))
    if n != int(counts['variables']):
        raise RuntimeError('variable count differs from pinned resource receipt')
    return counts, n


def run_once(review_sha: str):
    if not re.fullmatch(r'[0-9a-fA-F]{64}', review_sha):
        raise ValueError('review SHA must be 64 hexadecimal characters')
    driver_path = Path(__file__).resolve()
    driver_sha = sha256_file(driver_path)
    source_paths = [Path(p) for p in PINS] + [driver_path, REVIEW]
    source_readset_start = rehash_paths(source_paths)
    pinned_start = verify_pins(PINS)
    if any(source_readset_start.get(path) != digest for path, digest in pinned_start.items()):
        raise RuntimeError('pinned inputs changed during initial read-set')
    review_doc, review_hash = review_gate(REVIEW, review_sha, driver_sha, source_readset_start)

    # No implementation bytes are loaded until every data/source pin and the
    # external review binding this driver have passed.
    old_driver, old_driver_sha = load_verified_module(OLD_DRIVER, PINS[str(OLD_DRIVER)], 'verified_old_bench_helpers')
    if old_driver_sha != pinned_start[str(OLD_DRIVER.resolve())]:
        raise RuntimeError('old helper source drifted during verified load')
    fused_mod, fused_sha = load_verified_module(FUSED, PINS[str(FUSED)], 'verified_fused_normal')
    if fused_sha != pinned_start[str(FUSED.resolve())] or not callable(getattr(fused_mod, 'FusedNormalAction', None)):
        raise RuntimeError('fused normal API/hash mismatch')
    build_operators, op_sha = old_driver.load_verified_operator(OLD_OPERATOR, PINS[str(OLD_OPERATOR)])
    if op_sha != pinned_start[str(OLD_OPERATOR.resolve())]:
        raise RuntimeError('structured operator changed during verified load')

    if RUN_DIR.exists() or REPORT.exists() or MARKER.exists():
        raise FileExistsError(f'comparison run is exclusive and already exists: {RUN_DIR}')
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    marker = {
        'schema': 'optimized-normal.one-shot-comparison.v1', 'state': 'STARTED',
        'driver_sha256': driver_sha, 'review_path': str(REVIEW.resolve()), 'review_sha256': review_hash,
        'source_pins': pinned_start, 'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'solver_executed': False, 'terrain_written': False,
    }
    with MARKER.open('x', encoding='utf-8') as f:
        f.write(json.dumps(marker, indent=2, allow_nan=False) + '\n')

    started = time.perf_counter()
    report = {
        'schema': 'optimized-normal.one-shot-comparison.v1', 'status': 'ERROR',
        'solver_executed': False, 'terrain_written': False, 'rho': RHO,
        'calls': {'old_normal': 0, 'fused_normal': 0},
        'source_paths': {key: key for key in source_readset_start},
        'source_readset_start': source_readset_start,
        'driver_sha256': driver_sha, 'review': {'path': str(REVIEW.resolve()), 'sha256': review_hash,
                                                'status': review_doc.get('status')},
        'pins': pinned_start,
    }
    watcher = old_driver.ResourceWatchdog(started).start()
    status = 'ERROR'
    try:
        old_receipt, sizing = validate_historical_receipts()
        with np.load(INPUT_H, allow_pickle=False) as z:
            h32 = z['heights']
        if h32.dtype != np.float32 or h32.shape != (2048, 2048) or not np.isfinite(h32).all():
            raise ValueError('pinned EV95 archive has unexpected height array')
        H = np.asarray(h32, dtype=np.float64)
        del h32
        with np.load(MASKS, allow_pickle=False) as z:
            mask = z['ev95_variable']
        counts, n = validate_input_data(INPUT_H, MASKS, sizing, H, mask)
        variables = np.column_stack(np.nonzero(mask)).astype(np.int32, copy=False)
        del mask
        shape = H.shape
        mem_before = old_driver.memory_status()
        expected_rows = [int(counts['A']['rows']), int(counts['C']['rows']), int(counts['G']['rows']), n]
        arrays, persistent = old_driver.persistent_array_estimate_bytes(shape, n, *expected_rows[:3])
        masks_bytes = 3 * int(np.prod(shape))
        estimate_parts, increment = estimate_increment_bytes(n, shape, persistent, masks_bytes)
        if mem_before['available_physical_bytes'] < old_driver.MIN_FREE_BYTES:
            raise MemoryError('less than 6 GiB physical memory available before operator construction')
        if mem_before['available_physical_bytes'] - increment < old_driver.MIN_FREE_BYTES:
            raise MemoryError('conservative comparison estimate would cross the 6 GiB reserve')
        report['resource_gate'] = {
            'available_before_operator_bytes': mem_before['available_physical_bytes'],
            'required_free_reserve_bytes': old_driver.MIN_FREE_BYTES,
            'estimated_increment_bytes': increment,
            'estimate_parts': estimate_parts,
            'gate_pass': True,
        }
        operator = build_operators(H, variables)
        del H, variables
        watcher.check_boundary('operator construction')
        actual_rows = [operator.n_a, operator.n_c, operator.n_g, operator.n]
        if actual_rows != expected_rows:
            raise RuntimeError(f'operator row/count mismatch: expected={expected_rows}, actual={actual_rows}')
        counts_nnz = old_receipt['operator_counts']
        nnz = old_driver.exact_structural_nnz(operator)
        if nnz != {k: int(counts_nnz[k]['nnz']) for k in ('A', 'C', 'G')}:
            raise RuntimeError(f'operator structural nnz mismatch: {nnz}')

        x = old_driver.deterministic_vector(n, tag=1)
        x_sha, x_norm = old_driver.vector_digest_and_norm(x)
        report['operator'] = {
            'shape': [2048, 2048], 'variables': n,
            'A': {'rows': operator.n_a, 'nnz': nnz['A']},
            'C': {'rows': operator.n_c, 'nnz': nnz['C']},
            'G': {'rows': operator.n_g, 'nnz': nnz['G']},
        }
        report['probe'] = {
            'sha256': x_sha, 'norm': x_norm, 'dtype': 'float64', 'length': n,
            'definition': '((arange(n) mod 4093 + 137) mod 4093 - 2046)/2046',
        }
        report['rho'] = RHO
        old_normal = operator.normal_operator(RHO)
        t0 = time.perf_counter()
        y_old = np.asarray(old_normal.matvec(x), dtype=np.float64)
        old_seconds = time.perf_counter() - t0
        report['calls']['old_normal'] = 1
        if y_old.shape != (n,) or not np.isfinite(y_old).all():
            raise RuntimeError('old normal action returned invalid output')
        old_digest = sha256_bytes(memoryview(np.ascontiguousarray(y_old)).cast('B'))
        old_norm = float(np.linalg.norm(y_old))
        old_dot = float(np.dot(x, y_old))
        if not np.isfinite(old_norm) or not np.isfinite(old_dot):
            raise RuntimeError('old normal output summary is non-finite')
        report['old_normal'] = {
            'calls': 1, 'seconds': old_seconds, 'output_sha256': old_digest,
            'output_norm': old_norm, 'dot_x_output': old_dot,
            'peak_working_set_bytes_after': old_driver.process_peak_working_set(),
            'available_physical_bytes_after': old_driver.memory_status()['available_physical_bytes'],
        }
        watcher.check_boundary('old normal action')

        fused = fused_mod.FusedNormalAction(operator)
        t0 = time.perf_counter()
        y_fused = np.asarray(fused.matvec(x, RHO), dtype=np.float64)
        fused_seconds = time.perf_counter() - t0
        report['calls']['fused_normal'] = 1
        if y_fused.shape != (n,) or not np.isfinite(y_fused).all():
            raise RuntimeError('fused normal action returned invalid output')
        fused_digest = sha256_bytes(memoryview(np.ascontiguousarray(y_fused)).cast('B'))
        fused_norm = float(np.linalg.norm(y_fused))
        fused_dot = float(np.dot(x, y_fused))
        diff = np.empty_like(y_old)
        np.subtract(y_old, y_fused, out=diff)
        np.abs(diff, out=diff)
        max_abs = float(np.max(diff, initial=0.0))
        del diff
        norm_diff = float(np.linalg.norm(y_old - y_fused))
        dot_abs = abs(old_dot - fused_dot)
        report['fused_normal'] = {
            'calls': 1, 'seconds': fused_seconds, 'output_sha256': fused_digest,
            'output_norm': fused_norm, 'dot_x_output': fused_dot,
            'peak_working_set_bytes_after': old_driver.process_peak_working_set(),
            'available_physical_bytes_after': old_driver.memory_status()['available_physical_bytes'],
        }
        report['comparison'] = {
            'same_operator_instance': True, 'same_vector_sha256': x_sha, 'same_rho': RHO,
            'max_abs_difference': max_abs, 'l2_difference': norm_diff,
            'dot_difference_abs': dot_abs, 'absolute_tolerance': TOL_ABS,
            'equivalent_within_tolerance': bool(max_abs <= TOL_ABS),
        }
        report['memory_note'] = {
            'fused_identity_term': 'the expression 0.0625*x allocates one transient N-element float64 vector',
            'transient_bytes_at_EV95_n': int(8 * n),
            'transient_mib_at_EV95_n': float(8 * n / 1024**2),
            'included_in_estimate': True,
        }
        if old_driver.memory_status()['available_physical_bytes'] < old_driver.MIN_FREE_BYTES:
            raise MemoryError('physical-memory reserve fell below 6 GiB after both actions')
        watcher.check_boundary('comparison result')
        if max_abs > TOL_ABS:
            status = 'FAIL_NORMAL_ACTION_MISMATCH'
        else:
            status = 'PASS_OLD_VS_FUSED_NORMAL_COMPARISON'
    except Exception as exc:
        report['error'] = {'type': type(exc).__name__, 'message': str(exc)}
        if isinstance(exc, TimeoutError):
            status = 'ABORT_TIME_BUDGET'
        elif isinstance(exc, MemoryError):
            status = 'ABORT_MEMORY_GUARD'
        elif watcher.failure is not None:
            status = 'ABORT_RESOURCE_WATCHDOG'
        elif status == 'ERROR':
            status = 'ERROR'
    finally:
        report['resource_watchdog'] = watcher.close()
        report['elapsed_total_seconds'] = time.perf_counter() - started
        report['numeric_budget_seconds'] = NUMERIC_BUDGET_S
        report['status'] = status
        try:
            end = rehash_paths(source_paths)
            report['source_readset_end'] = end
            report['source_readset_stable'] = end == source_readset_start
            if not report['source_readset_stable'] and status == 'PASS_OLD_VS_FUSED_NORMAL_COMPARISON':
                report['status'] = 'FAIL_SOURCE_DRIFT'
        except Exception as exc:
            report['source_readset_end_error'] = f'{type(exc).__name__}: {exc}'
            if status == 'PASS_OLD_VS_FUSED_NORMAL_COMPARISON':
                report['status'] = 'FAIL_SOURCE_REHASH'
        try:
            report['process_peak_working_set_bytes'] = old_driver.process_peak_working_set()
        except Exception as exc:
            report['process_peak_working_set_error'] = f'{type(exc).__name__}: {exc}'
            if report['status'] == 'PASS_OLD_VS_FUSED_NORMAL_COMPARISON':
                report['status'] = 'ERROR_PEAK_MEMORY_READ'
        report['finished_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        write_json_atomic(REPORT, report)
        marker['state'] = 'FINISHED'
        marker['finished_utc'] = report['finished_utc']
        marker['report_sha256'] = sha256_file(REPORT)
        write_json_atomic(MARKER, marker)
    return report


def write_json_atomic(path: Path, data):
    tmp = path.with_name(path.name + '.tmp')
    if tmp.exists():
        raise FileExistsError(tmp)
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def self_test():
    x = np.arange(5, dtype=np.float64)
    a = np.array([0.0, 1.0, 2.0, 3.0, 4.0], dtype=np.float64)
    b = a.copy()
    np.subtract(a, b, out=x)
    np.abs(x, out=x)
    assert float(np.max(x, initial=0.0)) == 0.0
    parts, total = estimate_increment_bytes(100, (10, 12), 1000, 3 * 120)
    assert total == sum(parts.values()) and parts['fused_identity_term_0_0625_times_x_transient'] == 800
    print(json.dumps({'status': 'PASS_COMPARISON_DRIVER_SELF_TESTS', 'comparison_fixture': True,
                      'global_operator_loaded': False, 'global_measurement_run': False}, indent=2))


def receipt_check():
    pinned = verify_pins(PINS)
    old, sizing = validate_historical_receipts()
    sizing_counts = sizing['operator_counts']['EV95_delta_variable']
    return {
        'status': 'PASS_REAL_RECEIPT_WIRING',
        'measurement_sha256': PINS[str(OLD_MEASUREMENT)],
        'sizing_preflight_sha256': PINS[str(RECEIPT)],
        'measurement_operator_counts_schema': 'top-level operator_counts',
        'sizing_operator_counts_schema': 'operator_counts.EV95_delta_variable',
        'counts_equal': all(int(old['operator_counts'][k]['rows']) == int(sizing_counts[k]['rows']) and
                            int(old['operator_counts'][k]['nnz']) == int(sizing_counts[k]['nnz'])
                            for k in ('A', 'C', 'G')) and
                       int(old['operator_counts']['variables']) == int(sizing_counts['variables']),
        'fixed_vertices': int(old['operator_counts']['fixed_vertices']),
        'verified_source_pin_count': len(pinned),
        'global_operator_constructed': False,
        'measurement_run_repeated': False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--review-sha256')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--receipt-check', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.receipt_check:
        print(json.dumps(receipt_check(), indent=2, allow_nan=False))
        return
    if not args.review_sha256:
        raise SystemExit('comparison refused: provide independent comparison review SHA256')
    result = run_once(args.review_sha256)
    print(json.dumps({'status': result['status'], 'report': str(REPORT),
                      'elapsed_total_seconds': result.get('elapsed_total_seconds')}, indent=2))
    if result['status'] != 'PASS_OLD_VS_FUSED_NORMAL_COMPARISON':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
