"""Bounded telemetry-only probe; never runs solver or imports its main module."""
from __future__ import annotations

import argparse
import ast
import ctypes
import hashlib
import json
import os
import time
from pathlib import Path

ROOT = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
SOLVER = ROOT / 'global-operator-prototype/admm-quantized-pilot/solve.py'
SOLVER_SHA = '7e8636bf54ba23f7e23bc2f06464100439468da7b4edca85f96c72d0cd40e149'


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load_process_memory(mode: str):
    if sha(SOLVER) != SOLVER_SHA:
        raise AssertionError('frozen solver source hash changed')
    tree = ast.parse(SOLVER.read_text(encoding='utf-8'))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'process_memory')
    cls = next(n for n in fn.body if isinstance(n, ast.ClassDef) and n.name == 'Counters')
    namespace = {'ctypes': ctypes, 'os': os}
    if mode == 'original':
        module = ast.Module(body=[fn], type_ignores=[])
    elif mode == 'cached':
        # The sole change is lifting the exact nested Counters class to module
        # scope; function statements and API remain identical.
        fn_cached = ast.FunctionDef(name=fn.name, args=fn.args,
            body=[node for node in fn.body if node is not cls], decorator_list=fn.decorator_list,
            returns=fn.returns, type_comment=fn.type_comment)
        module = ast.Module(body=[cls, fn_cached], type_ignores=[])
    else:
        raise ValueError(mode)
    exec(compile(ast.fix_missing_locations(module), str(SOLVER), 'exec'), namespace)
    return namespace['process_memory']


def worker(mode: str, iterations: int, hold_seconds: float) -> int:
    before_sha = sha(SOLVER)
    fn = load_process_memory(mode)
    cache_before = len(ctypes._pointer_type_cache)
    t0 = time.perf_counter()
    print(json.dumps({'event': 'started', 'mode': mode, 'pid': os.getpid(),
                      'iterations': iterations, 'solver_sha256': before_sha,
                      'pointer_cache_before': cache_before}), flush=True)
    first = fn()
    last = first
    for _ in range(iterations - 1):
        last = fn()
    elapsed = time.perf_counter() - t0
    cache_after = len(ctypes._pointer_type_cache)
    after_sha = sha(SOLVER)
    expected_fields = {'pid', 'peak_working_set_bytes', 'working_set_bytes',
                       'peak_commit_bytes', 'method'}
    if set(last) != expected_fields or last['pid'] != os.getpid():
        raise AssertionError('process_memory API/result fields changed')
    if before_sha != after_sha or before_sha != SOLVER_SHA:
        raise AssertionError('solver source changed during telemetry probe')
    print(json.dumps({'event': 'finished', 'mode': mode, 'pid': os.getpid(),
        'iterations': iterations, 'elapsed_seconds': elapsed,
        'pointer_cache_before': cache_before, 'pointer_cache_after': cache_after,
        'pointer_cache_delta': cache_after-cache_before,
        'api_fields': sorted(last), 'api_method': last['method'],
        'api_memory_last_call': last, 'solver_sha_start': before_sha,
        'solver_sha_end': after_sha}, sort_keys=True), flush=True)
    # Keep the measured PID alive briefly so the independent parent sampler can
    # observe the post-loop working set even when the probe finishes quickly.
    if hold_seconds > 0:
        time.sleep(hold_seconds)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', choices=('original', 'cached'))
    ap.add_argument('--iterations', type=int, default=10000)
    ap.add_argument('--hold-seconds', type=float, default=1.0)
    args = ap.parse_args()
    if args.worker:
        if args.iterations < 1:
            raise ValueError('iterations must be positive')
        return worker(args.worker, args.iterations, args.hold_seconds)
    raise SystemExit('use the PowerShell parent runner for independent RSS sampling')


if __name__ == '__main__':
    raise SystemExit(main())
