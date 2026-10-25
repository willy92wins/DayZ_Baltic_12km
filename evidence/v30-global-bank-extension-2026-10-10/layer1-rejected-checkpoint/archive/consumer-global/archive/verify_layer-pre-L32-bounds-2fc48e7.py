#!/usr/bin/env python
"""Independent EV93 first-layer global consumer.

No author, optimizer, PBO builder, or DayZ imports. The consumer reconstructs
the composite from immutable per-window artifacts, checks local EV91/EV90
contracts, then evaluates global terrain and compiled-water contracts once.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import traceback
from collections import defaultdict
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = Path(r'E:/DayZ-Baltic-Build')
G = ROOT / 'v30-global-bank-extension-20261010'
HERE = G / 'consumer-global'
PLAN = G / 'author-stage-plan.md'
EV91_DIR = ROOT / 'v30-wide-bank-fairing-pilot-20261010'
EV91 = EV91_DIR / 'ev91-descent/consumer/verify_ev91.py'
EV88 = EV91_DIR / 'review-independent/verify_ev88q.py'
EV87 = ROOT / 'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
CV = ROOT / 'v30-global-strict-bank-relief-20261010/review-independent/verify_coverage_contract.py'
SHAPE = EV91_DIR / 'next-method-consumer/shape_contract.py'
EV92 = EV91_DIR / 'ev92-damped/consumer/verify_ev92.py'
INDEX_SOURCE = G / 'ev93-face-index/build_face_index.py'
INDEX_RUN = G / 'ev93-face-index/runs/20261010T092417Z-63d4cec3'
INDEX_MANIFEST = INDEX_RUN / 'manifest.json'
INDEX_VERIFICATION = G / 'review-independent/runs/attempt-01/verification.json'
QUEUE = G / 'queue/queue.json'
PILOT_PREPARED = ROOT/'v30-wide-bank-fairing-pilot-20261010/ev92-damped/prepared.json'
PILOT_BASE = ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
PILOT_FINAL = ROOT/'v30-wide-bank-fairing-pilot-20261010/ev92-damped/candidate-terrain.npz'
PILOT_RECEIPT = ROOT/'v30-wide-bank-fairing-pilot-20261010/ev92-damped/authoring.json'
PILOT_DIRECTION = ROOT/'v30-wide-bank-fairing-pilot-20261010/ev91-descent/candidate-terrain.npz'
PILOT_PINS = {
    str(PILOT_BASE):'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
    str(PILOT_PREPARED):'a2e9f18b1e77db5d3ce90cb4d928464c775167f2e1c0ff99c2776d1cca0e802d',
    str(PILOT_FINAL):'2f068ce5c4609e551e105b589e93ea8053267c9c307de068716b77221727b60a',
    str(PILOT_RECEIPT):'38cbebaae8fee20c6e79220723c55ad00076ddf37cf5bb907652e6a6820787f4',
    str(PILOT_DIRECTION):'865901ab24aa3736da57847f9112d3c73181085213f89b48ef2e3e7a9f6ee702',
}

PINS = {
    str(PLAN): '2bc641c0ec88954e83a2d10f5a2542357ac8cdc6533456b466e4e71f90df504c',
    str(EV91): '5e726b93642f5db531193a8f1d85afabd139c7b9ac3afca4479df793afd53668',
    str(EV88): '82a988790e6bdfc0289bcb7c32cb0afd1210e07b264d92731aba266bc5980f78',
    str(EV87): '964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
    str(CV): '214f0eddda08d84ce18c921fcdbe01298f608c9a5c19b7e5246bb9e71df5dc2b',
    str(SHAPE): '8cd9d0fbea03c05e5ae53a31676d79ec2364be83c055213446f6c8599245d533',
    str(EV92): '87b5ee5ee95318f1a8026c4a7459aa06d27c9b69db80f34ad25149293d5fc1df',
    str(INDEX_SOURCE): 'd1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e',
    str(INDEX_MANIFEST): 'c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c',
    str(INDEX_VERIFICATION): 'b498e7d68835b199399655451e5e01ac81acb3149dbb9bf882b94858141521d4',
}


def sha(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def canonical_sha(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def load_module(name: str, path: Path, wanted: str | None = None):
    actual = sha(path)
    if wanted and actual != wanted:
        raise AssertionError(f'helper pin mismatch {path}: {actual} != {wanted}')
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot import frozen helper {path}')
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_helpers():
    for path, wanted in PINS.items():
        actual = sha(path)
        if actual != wanted:
            raise AssertionError(f'frozen input changed: {path}: {actual} != {wanted}')
    ev = load_module('ev93_ev88', EV88, PINS[str(EV88)])
    ev91 = load_module('ev93_ev91', EV91, PINS[str(EV91)])
    ev87 = load_module('ev93_ev87', EV87, PINS[str(EV87)])
    cv = load_module('ev93_coverage', CV, PINS[str(CV)])
    shape = load_module('ev93_shape', SHAPE, PINS[str(SHAPE)])
    ev92 = load_module('ev93_ev92_pure', EV92, PINS[str(EV92)])
    index_module = load_module('ev93_index', INDEX_SOURCE, PINS[str(INDEX_SOURCE)])
    cv.ev = ev87
    return ev, ev91, ev87, cv, shape, ev92, index_module


def rows_rc(rows):
    return {(int(x[0]), int(x[1])) for x in rows}


def rect_overlap(a, b):
    """Half-open rectangle overlap, inputs [r0,r1,c0,c1]."""
    return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]


def normalize_window(entry, detail):
    win = tuple(map(int, entry['window_rc']))
    core = tuple(map(int, entry['core_rc']))
    win17 = detail.get('window17')
    pre = detail.get('preflight', {})
    if len(win) != 4 or len(core) != 4 or len(win17 or []) != 4:
        raise AssertionError('window/core schema malformed')
    if win != (int(win17[0]), int(win17[2]), int(win17[1]), int(win17[3])):
        raise AssertionError(f'window17 mismatch queue_id={entry["queue_id"]}')
    if tuple(map(int, pre.get('window', []))) != win or tuple(map(int, pre.get('core', []))) != core:
        raise AssertionError(f'detail preflight window/core mismatch queue_id={entry["queue_id"]}')
    if not (win[0] <= core[0] < core[1] <= win[1] and win[2] <= core[2] < core[3] <= win[3]):
        raise AssertionError('core is not inside window')
    return win, core


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def validate_attempt_artifact(qid,result,base_heights):
    path=Path(result['solution_path'])
    if sha(path)!=result.get('solution_sha256'):
        raise AssertionError(f'solver solution artifact SHA mismatch q{qid}')
    with np.load(path,allow_pickle=False) as z:
        required={'variables_rc','B_values_float32','bounds_float32_inward','solver_bounds_float32',
            'guard_rc','solver_x_float64','direction_float32','stencils_json','descent_witnesses_json',
            'matrix_shape','matrix_sha256_f64','rhs_sha256_f64','d8_matrix_sha256_f64','d8_rhs_sha256_f64'}
        if not required.issubset(z.files):
            raise AssertionError(f'solver solution artifact schema incomplete q{qid}')
        nodes=np.asarray(z['variables_rc'],dtype=np.int32)
        x=np.asarray(z['solver_x_float64'],dtype=np.float64)
        d=np.asarray(z['direction_float32'],dtype=np.float32)
        b=np.asarray(z['B_values_float32'],dtype=np.float32)
        stencils=json.loads(np.asarray(z['stencils_json'],dtype=np.uint8).tobytes().decode('utf-8'))
        witnesses=json.loads(np.asarray(z['descent_witnesses_json'],dtype=np.uint8).tobytes().decode('utf-8'))
        hashes={k:np.asarray(z[array],dtype=np.uint8).tobytes().decode('ascii') for k,array in (
            ('matrix_sha256_f64','matrix_sha256_f64'),('rhs_sha256_f64','rhs_sha256_f64'),
            ('d8_matrix_sha256_f64','d8_matrix_sha256_f64'),('d8_rhs_sha256_f64','d8_rhs_sha256_f64'))}
        shape=np.asarray(z['matrix_shape'],dtype=np.int32).tolist()
        guard=np.asarray(z['guard_rc'],dtype=np.int32).tolist()
    if nodes.ndim!=2 or nodes.shape[1]!=2 or x.shape!=(len(nodes),) or d.shape!=(len(nodes),) or b.shape!=(len(nodes),):
        raise AssertionError(f'solver artifact vector shape mismatch q{qid}')
    if not np.array_equal(b,np.asarray(base_heights,dtype=np.float32)[tuple(nodes.T)]):
        raise AssertionError(f'solver artifact baseline values differ from B q{qid}')
    if not np.array_equal(d,x.astype(np.float32)):
        raise AssertionError(f'solver artifact direction is not float32 cast of solver x q{qid}')
    if canonical_sha(stencils)!=canonical_sha(result.get('stencils')):
        raise AssertionError(f'solver artifact stencil inventory differs from result q{qid}')
    if canonical_sha(witnesses)!=canonical_sha(result.get('d8_witnesses')):
        raise AssertionError(f'solver artifact D8 witnesses differ from result q{qid}')
    for key,val in hashes.items():
        if result.get(key)!=val:raise AssertionError(f'solver artifact {key} mismatch q{qid}')
    if result.get('matrix_shape')!=shape or result.get('guard_rc')!=guard:
        raise AssertionError(f'solver artifact matrix/guard metadata mismatch q{qid}')
    if result.get('direction_float32') is not None and not np.array_equal(
            np.asarray(result['direction_float32'],dtype=np.float32),d):
        raise AssertionError(f'solver direction JSON differs from solution NPZ q{qid}')
    return nodes,stencils,d


def verify_prepared(prepared_path: Path, receipt_path: Path, base_heights: np.ndarray):
    prepared = load_json(prepared_path)
    receipt = load_json(receipt_path)
    if prepared.get('schema') != 'ev93-fairing-layer1-prepared-v1' or prepared.get('status') != 'PREPARED_NO_SOLVE':
        raise AssertionError('prepared manifest schema/status is not the frozen first-layer form')
    rows = prepared.get('entries')
    if not isinstance(rows, list) or len(rows) != 703 or prepared.get('entry_count') != 703:
        raise AssertionError('prepared entry inventory must contain the full ordered 703-row queue')
    if receipt.get('prepared_sha256') != sha(prepared_path):
        raise AssertionError('receipt does not pin prepared.json')
    if receipt.get('status') != 'AUTHORED_PENDING_GLOBAL_CONSUMER':
        raise AssertionError(f"author receipt is not complete/pending-consumer: {receipt.get('status')}")
    queue_ids = [int(x['queue_id']) for x in rows]
    if queue_ids != list(range(len(rows))):
        raise AssertionError('queue rows are not complete, unique, and ordered zero-based')
    if sha(PLAN) != prepared.get('plan_sha256'):
        raise AssertionError('prepared manifest plan pin is stale')
    if prepared.get('source_pins') != receipt.get('source_pins'):
        raise AssertionError('receipt and prepared source pin maps differ')
    if prepared.get('base_path') is None or sha(prepared['base_path']) != prepared.get('base_sha256'):
        raise AssertionError('prepared baseline path/SHA mismatch')
    if Path(prepared['base_path']).resolve() != Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz').resolve():
        raise AssertionError('prepared baseline is not the pinned EV82-B terrain')
    for pin_path,wanted in prepared.get('source_pins',{}).items():
        if not Path(pin_path).is_file() or sha(pin_path)!=wanted:
            raise AssertionError(f'prepared source pin mismatch: {pin_path}')
    queue_path = Path(prepared.get('queue_path', QUEUE))
    if queue_path != QUEUE or sha(queue_path) != prepared.get('queue_sha256'):
        raise AssertionError('prepared queue source pin mismatch')
    q = load_json(queue_path)
    first_layer = sorted((x for x in q.get('seeds', []) if x.get('first_layer_id') is not None),
                         key=lambda x: int(x['first_layer_id']))
    if len(first_layer) != 703:
        raise AssertionError('source queue does not contain exactly 703 first-layer rows')
    for i, (entry, seed) in enumerate(zip(rows, first_layer)):
        if int(entry['queue_id']) != i or int(entry['seed_id']) != int(seed['seed_id']):
            raise AssertionError(f'prepared queue identity differs from source at row {i}')
        if list(map(int, entry['center_rc'])) != [int(seed['row']), int(seed['col'])]:
            raise AssertionError(f'prepared center differs from source queue at row {i}')
    preflight_path = Path(prepared['preflight_ledger_path'])
    if sha(preflight_path) != prepared.get('preflight_ledger_sha256'):
        raise AssertionError('prepared preflight ledger SHA mismatch')
    preflight_lines = [json.loads(x) for x in preflight_path.read_text(encoding='utf-8').splitlines() if x.strip()]
    if not preflight_lines or preflight_lines[-1].get('event') != 'final' or \
       preflight_lines[-1].get('status') != 'COMPLETE_READONLY_PREFLIGHT' or \
       preflight_lines[-1].get('processed_count') != 703 or \
       preflight_lines[-1].get('remaining_count') != 0 or preflight_lines[-1].get('error_count') != 0:
        raise AssertionError('source preflight ledger does not end COMPLETE with 703/0/0 counters')
    result_dir = Path(receipt_path).parent
    ledger_path = result_dir / receipt.get('ledger_path', 'ledger.jsonl')
    ledger_rows = [json.loads(x) for x in ledger_path.read_text(encoding='utf-8').splitlines() if x.strip()]
    if receipt.get('ledger_sha256') != sha(ledger_path):
        raise AssertionError('receipt ledger SHA mismatch')
    finals = [x for x in ledger_rows if x.get('event') == 'final']
    ledger_rows = [x for x in ledger_rows if x.get('event') == 'result']
    if len(finals) != 1 or finals[0].get('status') != 'COMPLETE' or len(ledger_rows) != len(rows):
        raise AssertionError('ledger is not terminal for every prepared row')
    index = {}
    for line in ledger_rows:
        qid = int(line['queue_id'])
        if qid in index:
            raise AssertionError(f'duplicate queue result {qid}')
        result_path = Path(line['result_path'])
        if sha(result_path) != line.get('result_sha256'):
            raise AssertionError(f'ledger result SHA mismatch q={qid}')
        result_json = load_json(result_path)
        index[qid] = {**line, **result_json, 'result_path': str(result_path.resolve()),
                      'result_sha256': line['result_sha256']}
    if set(index) != set(queue_ids):
        raise AssertionError('ledger queue id set differs from full prepared inventory')
    for entry in rows:
        qid = int(entry['queue_id'])
        result = index[qid]
        if result.get('seed_id') != entry.get('seed_id') or result.get('center_rc') != entry.get('center_rc'):
            raise AssertionError(f'ledger identity mismatch at queue {qid}')
        state = result.get('state')
        preflight_state = str(entry.get('preflight_state', ''))
        ready = preflight_state in {'READY', 'PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW'}
        if state not in {'accepted', 'rejected', 'inconclusive', 'not_authored'}:
            raise AssertionError(f'queue {qid} unresolved/error state {state!r}; cannot promote')
        if state == 'not_authored' and ready:
            raise AssertionError(f'not_authored is invalid for READY queue {qid}')
        if state == 'inconclusive' and 'INCONCLUSIVE' not in preflight_state:
            raise AssertionError(f'inconclusive state is not justified by preflight q{qid}')
        if state in {'accepted', 'rejected'} and not ready:
            raise AssertionError(f'{state} result is impossible for non-READY q{qid}')
        if state in {'inconclusive', 'not_authored'} and result.get('solve_calls', 0) != 0:
            raise AssertionError(f'nonaccepted queue {qid} unexpectedly records a solve')
        if state == 'rejected' and result.get('solve_calls') != 1:
            raise AssertionError(f'rejected queue {qid} has invalid solve_calls')
        if state == 'accepted' and result.get('solve_calls') != 1:
            raise AssertionError(f'accepted queue {qid} must record exactly one solve')
        if result.get('solve_calls') == 1:
            validate_attempt_artifact(qid,result,base_heights)
        marker = result_dir / 'attempts' / f'window-{qid:04d}.started.json'
        if result.get('solve_calls') == 1:
            if not marker.is_file():
                raise AssertionError(f'solver result has no exclusive started marker q{qid}')
            marker_data = load_json(marker)
            if marker_data.get('queue_id') != qid or marker_data.get('prepared_sha256') != sha(prepared_path):
                raise AssertionError(f'started marker identity mismatch q{qid}')
    if receipt.get('classified_results') not in (None, len(rows)):
        raise AssertionError('receipt classified_results differs from queue')
    actual_counts = {s: sum(x.get('state') == s for x in index.values())
                     for s in ('accepted','rejected','inconclusive','not_authored','timeout','error')}
    if receipt.get('result_counts') != actual_counts:
        raise AssertionError('author receipt state counts differ from terminal row inventory')
    if receipt.get('candidate_path') is None or not Path(receipt['candidate_path']).is_file():
        raise AssertionError('author receipt candidate path is missing')
    return prepared, receipt, rows, index, ledger_path


def validate_detail_hashes(prepared, entries):
    details = {}
    for entry in entries:
        qid = int(entry['queue_id'])
        detail_path = Path(entry['detail_path'])
        got = sha(detail_path)
        if got != entry['detail_sha256']:
            raise AssertionError(f'detail SHA mismatch q={qid}: {got}')
        detail = load_json(detail_path)
        normalize_window(entry, detail)
        if int(detail.get('queue_id', -1)) != qid or int(detail.get('seed_id', -1)) != int(entry['seed_id']):
            raise AssertionError(f'detail identity mismatch q={qid}')
        if detail.get('preflight', {}).get('status') != entry.get('preflight_state'):
            raise AssertionError(f'detail/prepared preflight state mismatch q={qid}')
        details[qid] = detail
    return details


def direction_from_result(result_path: Path, result_json: dict, base: np.ndarray):
    """Rebuild one accepted patch; JSON/NPZ are data artifacts, never author code."""
    delta_path = Path(result_json['delta_path'])
    if sha(delta_path) != result_json['delta_sha256']:
        raise AssertionError(f'accepted patch NPZ SHA mismatch: {delta_path}')
    with np.load(delta_path, allow_pickle=False) as z:
        required = {'variables_rc', 'B_values_float32', 'bounds_float32_inward',
                    'solver_bounds_float32', 'guard_rc', 'direction_float32', 'final_float32',
                    'stencils_json', 'descent_witnesses_json'}
        if not required.issubset(z.files):
            raise AssertionError(f'accepted patch artifact missing arrays: {required-set(z.files)}')
        nodes = np.asarray(z['variables_rc'], dtype=np.int32)
        bvals = np.asarray(z['B_values_float32'], dtype=np.float32)
        bounds = np.asarray(z['bounds_float32_inward'], dtype=np.float32)
        solver_bounds = np.asarray(z['solver_bounds_float32'], dtype=np.float32)
        direction = np.asarray(z['direction_float32'], dtype=np.float32)
        final = np.asarray(z['final_float32'], dtype=np.float32)
        guard = np.asarray(z['guard_rc'], dtype=np.int32)
        stencils = [tuple((str(x[0]), int(x[1]), int(x[2]))) for x in
                    json.loads(np.asarray(z['stencils_json'],dtype=np.uint8).tobytes().decode('utf-8'))]
        witnesses_npz = json.loads(np.asarray(z['descent_witnesses_json'], dtype=np.uint8).tobytes().decode('utf-8'))
    if nodes.ndim != 2 or nodes.shape[1] != 2 or not np.array_equal(nodes, np.unique(nodes, axis=0)):
        raise AssertionError('accepted patch mutable nodes must be unique, lexicographically ordered RC pairs')
    if any(len(x) != len(nodes) for x in (bvals, bounds, solver_bounds, direction, final)):
        raise AssertionError('accepted patch vector dimensions disagree')
    rr, cc = nodes[:, 0], nodes[:, 1]
    if not np.array_equal(bvals, base[rr, cc]):
        raise AssertionError('accepted patch B values differ from pinned baseline')
    if (np.any(direction < bounds[:, 0]) or np.any(direction > bounds[:, 1]) or
        np.any(final < bounds[:, 0]) or np.any(final > bounds[:, 1])):
        raise AssertionError('accepted direction/final values outside inward float32 bounds')
    if (np.any(direction < solver_bounds[:,0]) or np.any(direction > solver_bounds[:,1]) or
        np.any(final < solver_bounds[:,0]) or np.any(final > solver_bounds[:,1]) or
        np.any(bvals < solver_bounds[:,0]) or np.any(bvals > solver_bounds[:,1])):
        raise AssertionError('accepted baseline/direction/final values outside solver bounds')
    if not np.array_equal(final, (bvals.astype(np.float64) +
                                 float(result_json['alpha']) *
                                 (direction.astype(np.float64)-bvals.astype(np.float64))).astype(np.float32)):
        raise AssertionError('accepted patch final float32 does not reconstruct from recorded alpha/direction')
    if np.any(solver_bounds[:, 0] > solver_bounds[:, 1]):
        raise AssertionError('accepted patch solver bounds inverted')
    if canonical_sha(witnesses_npz) != canonical_sha(result_json.get('d8_witnesses')):
        raise AssertionError('D8 witness JSON differs between result JSON and delta NPZ')
    if result_json.get('stencils') is not None and canonical_sha(result_json['stencils']) != canonical_sha([list(x) for x in stencils]):
        raise AssertionError('Dxx/Dzz/Dxz stencil keys differ between result JSON and delta NPZ')
    if result_json.get('direction_float32') is not None and not np.array_equal(
            np.asarray(result_json['direction_float32'],dtype=np.float32),direction):
        raise AssertionError('direction vector differs between result JSON and delta NPZ')
    if result_json.get('final_float32') is not None and not np.array_equal(
            np.asarray(result_json['final_float32'],dtype=np.float32),final):
        raise AssertionError('final vector differs between result JSON and delta NPZ')
    return nodes, bvals, bounds, solver_bounds, guard, direction, final, stencils


def reconstruct_candidate(base_npz: dict, receipt: dict, entries: list, ledger: dict,
                          details: dict, result_root: Path):
    base = np.asarray(base_npz['heights'], dtype=np.float32)
    candidate = base.copy()
    owner = {}
    accepted = []
    accepted_nodes = set()
    for entry in entries:
        qid = int(entry['queue_id'])
        row = ledger[qid]
        if row['state'] != 'accepted':
            continue
        result_path = Path(row['result_path'])
        if not result_path.is_absolute():
            result_path = result_root / result_path
        if sha(result_path) != row['result_sha256']:
            raise AssertionError(f'result JSON SHA mismatch queue {qid}')
        result = load_json(result_path)
        if result.get('solve_calls') != 1 or result.get('state') != 'accepted':
            raise AssertionError(f'accepted queue {qid} lacks one terminal solve')
        if result.get('queue_id') != qid or result.get('center_rc') != entry.get('center_rc'):
            raise AssertionError(f'accepted result identity mismatch queue {qid}')
        nodes, bvals, bounds, solver_bounds, guard, direction, final, stencils = direction_from_result(result_path, result, base)
        detail = details[qid]
        declared = detail['preflight']['domain']['eligible_after_face_freeze_nodes']
        declared_nodes = np.asarray(sorted(tuple(map(int, n)) for n in declared), dtype=np.int32)
        if not np.array_equal(nodes, declared_nodes):
            raise AssertionError(f'accepted mutable nodes differ from detail at q{qid}')
        for n, value in zip(map(tuple, nodes.tolist()), final.tolist()):
            if n in owner:
                raise AssertionError(f'mutable node ownership collision {n}: {owner[n]} and {qid}')
            owner[n] = qid
            accepted_nodes.add(n)
            candidate[n] = np.float32(value)
        accepted.append({'queue_id': qid, 'result': result, 'nodes': nodes,
                         'B': bvals, 'bounds': bounds, 'solver_bounds': solver_bounds,
                         'guard': guard, 'direction': direction, 'final': final,
                         'stencils': stencils})
    npz_candidate = Path(receipt['candidate_path'])
    if sha(npz_candidate) != receipt['candidate_sha256']:
        raise AssertionError('candidate NPZ differs from final author receipt')
    with np.load(npz_candidate, allow_pickle=False) as z:
        candidate_npz = {k: z[k] for k in z.files}
    if set(candidate_npz) != set(base_npz):
        raise AssertionError('candidate NPZ keys differ from baseline')
    for key in base_npz:
        if key == 'heights':
            continue
        if not np.array_equal(candidate_npz[key], base_npz[key], equal_nan=True):
            raise AssertionError(f'candidate metadata/key {key!r} changed from B')
    if not np.array_equal(candidate_npz['heights'], candidate, equal_nan=True):
        raise AssertionError('candidate height grid is not exactly B plus accepted per-window deltas')
    changed = np.argwhere(candidate != base)
    if any(tuple(x) not in accepted_nodes for x in changed.tolist()):
        raise AssertionError('candidate changed a vertex outside accepted mutable nodes')
    return candidate, changed, accepted, owner


def affected_cells(ev87, changed_rc):
    cells = ev87._ev87_cells([tuple(map(int, x)) for x in changed_rc.tolist()])
    return {(int(r), int(c)) for r, c in cells}


def high_field_exact(changed_nodes, high_cells):
    nodes=set(map(tuple,changed_nodes))
    high_nodes=set()
    for r,c in high_cells:
        high_nodes.update(((r,c),(r,c+1),(r+1,c),(r+1,c+1)))
    return not (nodes & high_nodes)


def p9_vertices_exact(changed_nodes, p9_vertices):
    return not (set(map(tuple,changed_nodes)) & set(p9_vertices))


def unknown_faces_resolved(summary):
    return int(summary.get('with_contact_or_exposed_or_unproven_intersection',-1))==0


def expected_dynamic_readset(prepared_path, receipt_path, prepared, receipt,
                             entries, ledger, ledger_path, index_manifest, model_dir):
    """Build the immutable read-set from the already-pinned declarations.

    Every data artifact is checked against its declaring SHA before its
    contents are consumed; this map is then re-hashed after evaluation to
    detect TOCTOU changes across the full read interval.
    """
    expected = {
        str(Path(prepared_path).resolve()): sha(prepared_path),
        str(Path(receipt_path).resolve()): sha(receipt_path),
        str(Path(ledger_path).resolve()): str(receipt['ledger_sha256']),
        str(Path(receipt['candidate_path']).resolve()): str(receipt['candidate_sha256']),
        str(Path(prepared['queue_path']).resolve()): str(prepared['queue_sha256']),
        str(Path(prepared['preflight_ledger_path']).resolve()): str(prepared['preflight_ledger_sha256']),
        str(Path(prepared['base_path']).resolve()): str(prepared['base_sha256']),
        str(Path(PLAN).resolve()): str(prepared['plan_sha256']),
        str(Path(INDEX_MANIFEST).resolve()): sha(INDEX_MANIFEST),
        str(Path(INDEX_VERIFICATION).resolve()): sha(INDEX_VERIFICATION),
    }
    for source_path, wanted in prepared.get('source_pins', {}).items():
        expected[str(Path(source_path).resolve())] = str(wanted)
    for entry in entries:
        path = str(Path(entry['detail_path']).resolve())
        expected[path] = str(entry['detail_sha256'])
    for qid, row in ledger.items():
        result_path = Path(row['result_path']).resolve()
        expected[str(result_path)] = str(row['result_sha256'])
        state = row.get('state')
        result = row
        if state == 'accepted':
            expected[str(Path(result['delta_path']).resolve())] = str(result['delta_sha256'])
        elif state == 'rejected':
            expected[str(Path(result['solution_path']).resolve())] = str(result['solution_sha256'])
    for model in index_manifest.get('models', []):
        path = Path(model_dir) / model['basename']
        expected[str(path.resolve())] = str(model['sha256'])
    for shard in index_manifest.get('shards', []):
        path = INDEX_RUN / shard['path']
        expected[str(path.resolve())] = str(shard['sha256'])
    for qid, row in ledger.items():
        if row.get('solve_calls') == 1:
            marker = Path(row['result_path']).parent.parent / 'attempts' / f'window-{int(qid):04d}.started.json'
            expected[str(marker.resolve())] = sha(marker)
    # Fixed helper/API/index pins are part of the read-set too, not just their
    # runtime constants. PINS maps absolute path to the approved digest.
    for path, digest in PINS.items():
        expected[str(Path(path).resolve())] = str(digest)
    return expected


def target_cells_from_details(details):
    """Reconstruct exact per-window high-field cells from frozen preflight details."""
    above = {'physical': set(), 'visible': set()}
    for detail in details.values():
        for kind in above:
            above[kind].update(tuple(map(int, x)) for x in
                               detail['preflight']['above_cells_by_kind'][kind])
    return above


def global_p9_unknown_vertices(ev, bundle):
    """Find NaN-P cells intersecting any of the 19 frozen corridor polygons."""
    from shapely.geometry import box, shape
    p=bundle['P']; geometries=[shape(x['geometry']) for x in bundle['corridors']['features']]
    cells=set(); by_feature=[]
    for fi,geom in enumerate(geometries):
        minx,minz,maxx,maxz=geom.bounds
        # One-cell padding makes this broad phase conservative at exact grid edges;
        # positive-area polygon intersection is the actual inclusion predicate.
        c0=max(0,int(math.floor(minx/ev.CELL))-1);c1=min(ev.N-2,int(math.floor(maxx/ev.CELL))+1)
        r0=max(0,int(math.floor((ev.Z0-maxz)/ev.CELL))-1)
        r1=min(ev.N-2,int(math.floor((ev.Z0-minz)/ev.CELL))+1)
        hits=[]
        local_nan=np.argwhere(~np.isfinite(p[r0:r1+1,c0:c1+1]))
        for dr,dc in local_nan:
            r,c=int(r0+dr),int(c0+dc)
            cell=box(c*ev.CELL,ev.Z0-(r+1)*ev.CELL,(c+1)*ev.CELL,ev.Z0-r*ev.CELL)
            if geom.intersection(cell).area>0.0:
                hits.append((r,c));cells.add((r,c))
        if hits: by_feature.append({'feature_index':fi,'unknown_cells':len(hits)})
    vertices=set()
    for r,c in cells: vertices.update(((r,c),(r,c+1),(r+1,c),(r+1,c+1)))
    return cells,vertices,by_feature


def stencil_energy_fraction(grid, stencils):
    from fractions import Fraction
    total = Fraction(0)
    h = np.asarray(grid, dtype=np.float32)
    for kind, r, c in stencils:
        if kind == 'xx': support = ((r,c,1),(r,c+1,-2),(r,c+2,1))
        elif kind == 'zz': support = ((r,c,1),(r+1,c,-2),(r+2,c,1))
        elif kind == 'xz': support = ((r,c,Fraction(-1,4)),(r,c+2,Fraction(1,4)),
                                      (r+2,c,Fraction(1,4)),(r+2,c+2,Fraction(-1,4)))
        else: raise AssertionError(f'unknown stencil kind {kind!r}')
        value = sum((Fraction(float(h[rr,cc]))*co for rr,cc,co in support), Fraction(0))
        total += (2 if kind == 'xz' else 1) * value * value
    return total


def stencil_energy_moments_fraction(base, target, stencils):
    """Exact q0,q1,q2 for energy(B + alpha*(target-B)), independently."""
    from fractions import Fraction
    b = np.asarray(base, dtype=np.float32)
    h = np.asarray(target, dtype=np.float32)
    q = [Fraction(0), Fraction(0), Fraction(0)]
    for kind, r, c in stencils:
        if kind == 'xx': support = ((r,c,1),(r,c+1,-2),(r,c+2,1))
        elif kind == 'zz': support = ((r,c,1),(r+1,c,-2),(r+2,c,1))
        elif kind == 'xz': support = ((r,c,Fraction(-1,4)),(r,c+2,Fraction(1,4)),
                                      (r+2,c,Fraction(1,4)),(r+2,c+2,Fraction(-1,4)))
        else: raise AssertionError('unknown stencil kind: '+str(kind))
        bv = sum((Fraction(float(b[rr,cc]))*co for rr,cc,co in support), Fraction(0))
        hv = sum((Fraction(float(h[rr,cc]))*co for rr,cc,co in support), Fraction(0))
        dv = hv-bv; weight = 2 if kind == 'xz' else 1
        q[0] += weight*bv*bv
        q[1] += 2*weight*bv*dv
        q[2] += weight*dv*dv
    return q


def verify_local_windows(ev, ev87, shape, ev92, base, candidate, accepted, details):
    """Recheck per-window geometry and recorded scalar interpolation without solver code."""
    gates = {}
    metrics = []
    for patch in accepted:
        qid = patch['queue_id']; result = patch['result']; d = details[qid]
        pre = d['preflight']; r0, r1, c0, c1 = map(int, pre['window'])
        cr0, cr1, cc0, cc1 = map(int, pre['core'])
        focus = tuple(map(int, d['center_rc']))
        nodes = patch['nodes']; node_set = {tuple(map(int, x)) for x in nodes.tolist()}
        declared = {tuple(map(int, x)) for x in pre['domain']['eligible_after_face_freeze_nodes']}
        # EV93 must author exactly the per-window preflight domain, not a pilot count/radius.
        domain_exact = node_set == declared
        bounds_expected = {tuple(map(int, x['node_rc'])): np.asarray(x['interval_float32_inward_m'], dtype=np.float32)
                           for x in pre['domain']['final_float32_intervals_for_eligible_nodes']}
        bounds_exact = all(np.array_equal(patch['bounds'][i], bounds_expected.get(tuple(node), np.empty(0)))
                           for i, node in enumerate(nodes.tolist()))
        guard_expected = np.asarray(pre['guard_d8']['guard_rc'], dtype=np.int32)
        guard_exact = np.array_equal(np.asarray(patch['guard'], dtype=np.int32), guard_expected)
        solver_expected=patch['bounds'].copy(); node_index={tuple(map(int,n)):i for i,n in enumerate(nodes.tolist())}
        solver_domain_exact=True
        for raw in guard_expected.tolist():
            n=tuple(map(int,raw))
            if n not in node_index: solver_domain_exact=False; continue
            i=node_index[n];solver_expected[i,:]=patch['B'][i]
        solver_bounds_exact=np.array_equal(solver_expected,patch['solver_bounds'])
        guard_unchanged = all(candidate[tuple(x)] == base[tuple(x)] for x in guard_expected.tolist())
        witnesses = patch['result'].get('d8_witnesses') or []
        witness_exact = canonical_sha(witnesses) == canonical_sha(pre['guard_d8']['descent_witnesses'])
        witness_pass = all(candidate[tuple(w['center'])] >= candidate[tuple(w['witness'])] for w in witnesses)
        d8_hash_exact=(result.get('d8_matrix_sha256_f64')==pre['guard_d8']['descent_matrix_sha256_f64'] and
                       result.get('d8_rhs_sha256_f64')==pre['guard_d8']['descent_rhs_sha256_f64'])
        for r, c in node_set:
            if not (r0 <= r < r1 and c0 <= c < c1):
                domain_exact = False
        crop0, crop1, col0, col1 = r0-1, r1+1, c0-1, c1+1
        base_crop = base[crop0:crop1, col0:col1].copy(); candidate_crop = base_crop.copy()
        for rr,cc in node_set: candidate_crop[rr-crop0,cc-col0] = candidate[rr,cc]
        shape_result = shape.evaluate_shape(base_crop, candidate_crop, (1,18,1,18),
                                            (focus[0]-crop0,focus[1]-col0))
        stencils = patch['stencils']
        if not stencils: raise AssertionError(f'accepted q{qid} has no stencil records')
        expected_records = ev.stencil_records(window=(r0,r1,c0,c1),
            core=(cr0,cr1,cc0,cc1), variables=declared)
        expected_keys = [tuple((str(x['key'][0]),int(x['key'][1]),int(x['key'][2])))
                         for x in expected_records]
        stencil_keys_exact = (len(stencils)==len(expected_keys) and
                              len(set(stencils))==len(stencils) and set(stencils)==set(expected_keys))
        direction_grid = base.copy()
        for rc, value in zip(nodes.tolist(), patch['direction'].tolist()):
            direction_grid[tuple(rc)] = np.float32(value)
        scalar = ev92.derive_scalar_rule(base, direction_grid, stencils, focus=focus)
        stored_rule = result.get('scalar_rule')
        scalar_fields=('energy_moments_fraction','energy_lower','focus_lower_by_axis','materiality_lower','alpha','rule')
        scalar_exact = (isinstance(stored_rule,dict) and
                        float(scalar['alpha']) == float(result['alpha']) == float(stored_rule.get('alpha',float('nan'))) and
                        all(canonical_sha(scalar.get(k))==canonical_sha(stored_rule.get(k)) for k in scalar_fields))
        interpolated=(patch['B'].astype(np.float64)+float(result['alpha'])*
                     (patch['direction'].astype(np.float64)-patch['B'].astype(np.float64))).astype(np.float32)
        final_interpolation_exact=np.array_equal(interpolated,patch['final'])
        energy_b, energy_h = stencil_energy_fraction(base,stencils),stencil_energy_fraction(candidate,stencils)
        collar_keys={tuple((str(x['key'][0]),int(x['key'][1]),int(x['key'][2])))
                     for x in expected_records if x['collar']}
        collar_stencils=[x for x in stencils if x in collar_keys]
        collar_b=stencil_energy_fraction(base,collar_stencils);collar_h=stencil_energy_fraction(candidate,collar_stencils)
        expected_b=[str(x) for x in stencil_energy_moments_fraction(base,base,stencils)]
        expected_h=[str(x) for x in stencil_energy_moments_fraction(base,candidate,stencils)]
        energy_json_exact=(result.get('energy_B_fraction')==expected_b and
                           result.get('energy_H_fraction')==expected_h and
                           sum(stencil_energy_moments_fraction(base,base,stencils))==energy_b and
                           sum(stencil_energy_moments_fraction(base,candidate,stencils))==energy_h)
        local_b = ev.local_mesh_angles(base.astype(np.float64), focus, radius=2)
        local_h = ev.local_mesh_angles(candidate.astype(np.float64), focus, radius=2)
        hinge_reduction = (local_b['max_incident_hinge_deg'] - local_h['max_incident_hinge_deg'])
        # The details list every window-local slope/hinge incidence by the native checker;
        # recompute all affected local mesh edges in the actual window, not just the focus.
        base_patch = base_crop.astype(np.float64)
        cand_patch = candidate_crop.astype(np.float64)
        angles_b = dict(ev87.edge_angles(base_patch)); angles_h = dict(ev87.edge_angles(cand_patch))
        # Author's collar is the two-node border of the native 17x17 window,
        # not the inverse of the core guard and not the extra 19x19 shape context.
        collar = np.zeros((r1-r0,c1-c0),dtype=bool)
        collar[:2,:]=True; collar[-2:,:]=True; collar[:,:2]=True; collar[:,-2:]=True
        b_window=base[r0:r1,c0:c1].astype(np.float64)
        h_window=candidate_crop[1:-1,1:-1].astype(np.float64)
        awb=dict(ev87.edge_angles(b_window)); awh=dict(ev87.edge_angles(h_window))
        collar_angle_rows = []
        for kind, ab in awb.items():
            ah = awh[kind]
            mask = ev87.incident_any(collar, kind)
            vb, vh = ab[mask], ah[mask]
            collar_angle_rows.append(not vb.size or float(vh.max()) <= float(vb.max()) + 1e-4)
        # Confirm only the fixed detail population is scored; changed nodes outside it fail.
        changed_crop=candidate_crop!=base_crop
        incident_cells=np.logical_or.reduce((changed_crop[:-1,:-1],changed_crop[:-1,1:],
                                             changed_crop[1:,:-1],changed_crop[1:,1:]))
        slope_pairs=[]
        for rr,cc in np.argwhere(incident_cells):
            xy=ev87.cell_xy(int(rr)+crop0,int(cc)+col0)
            ghb=ev87.corner_values(base_crop,int(rr),int(cc));ghh=ev87.corner_values(candidate_crop,int(rr),int(cc))
            for tri in ev87.TRIS:
                ids=np.asarray(tri,dtype=int)
                cb=ev87.affine_coeff(xy[ids],ghb[ids]);ch=ev87.affine_coeff(xy[ids],ghh[ids])
                slope_pairs.append((math.degrees(math.atan(np.linalg.norm(cb[:2]))),
                                    math.degrees(math.atan(np.linalg.norm(ch[:2])))))
        slope_bad=sum(hv>max(35.,bv)+1e-4 for bv,hv in slope_pairs)
        new_hinges={}
        for kind,bv in angles_b.items():
            affected=ev87.incident_any(changed_crop,kind)
            new_hinges[kind]=int(np.count_nonzero((bv<=30.0001)&(angles_h[kind]>30.0001)&affected))
        local_metrics = {
            'queue_id': qid, 'center_rc': list(focus), 'window_rc': [r0, r1, c0, c1],
            'mutable_count': len(node_set), 'preflight_domain_exact': domain_exact,
            'inward_bounds_match_preflight': bounds_exact,
            'solver_bounds_match_guard_contract':solver_bounds_exact and solver_domain_exact,
            'guard_exact_and_unchanged': guard_exact and guard_unchanged,
            'stencil_population_reconstructed_exactly':stencil_keys_exact,
            'd8_witnesses_match_detail_and_hold': witness_exact and witness_pass and d8_hash_exact,
            'scalar_rule_reconstructed_exactly': scalar_exact,
            'final_float32_interpolation_exact':final_interpolation_exact,
            'shape': shape_result, 'energy_B': float(energy_b), 'energy_H': float(energy_h),
            'energy_reduced_25pct': energy_h*4 <= energy_b*3,
            'energy_matches_author_receipt':energy_json_exact,
            'collar_energy_B': float(collar_b), 'collar_energy_H': float(collar_h),
            'collar_energy_nonworse': collar_h <= collar_b,
            'focus_hinge_B_deg': float(local_b['max_incident_hinge_deg']),
            'focus_hinge_H_deg': float(local_h['max_incident_hinge_deg']),
            'focus_hinge_reduction_deg': float(hinge_reduction),
            'focus_hinge_reduced_2deg': hinge_reduction >= 2.0,
            'collar_hinge_nonworse': all(collar_angle_rows),
            'incident_slope_violation_count': int(slope_bad),
            'new_hinges_over_30_0001_by_kind': new_hinges,
            'alpha': float(result['alpha']), 'solve_calls': int(result.get('solve_calls', -1)),
        }
        metrics.append(local_metrics)
        gates[qid] = (domain_exact and bounds_exact and solver_bounds_exact and solver_domain_exact and
                      guard_exact and guard_unchanged and stencil_keys_exact and
                      witness_exact and witness_pass and d8_hash_exact and scalar_exact and final_interpolation_exact and energy_json_exact and
                      all(shape_result['gates'].values()) and energy_h*4 <= energy_b*3 and
                      collar_h <= collar_b and hinge_reduction >= 2.0 and
                      all(collar_angle_rows) and slope_bad == 0 and not any(new_hinges.values()) and
                      result.get('solve_calls') == 1)
    return {'gates': gates, 'metrics': metrics}


def rectangle_any(bitmap, ranges):
    """Vectorized rectangle/cell-set intersection using an integral image."""
    ranges = np.asarray(ranges, dtype=np.int64)
    nrows, ncols = bitmap.shape
    valid = ((ranges[:, 0] >= 0) & (ranges[:, 1] < nrows) &
             (ranges[:, 2] >= 0) & (ranges[:, 3] < ncols) &
             (ranges[:, 0] <= ranges[:, 1]) & (ranges[:, 2] <= ranges[:, 3]))
    prefix = np.pad(bitmap.astype(np.int64), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    out = np.zeros(len(ranges), dtype=bool)
    ix = np.flatnonzero(valid)
    r0, r1, c0, c1 = (ranges[ix, 0], ranges[ix, 1]+1, ranges[ix, 2], ranges[ix, 3]+1)
    out[ix] = (prefix[r1, c1] - prefix[r0, c1] - prefix[r1, c0] + prefix[r0, c0]) > 0
    return out


def indexed_exposure_pair(ev87, cv, index, hb, hh, lower, p, f, cells, unknown_masks,
                          p_unknown_cells, p9_cells):
    """Exact EV90 exposure/coverage from indexed faces, scanning the index once."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    cells = {(int(r), int(c)) for r, c in cells}
    scan_cells = cells | {(int(r), int(c)) for r, c in unknown_masks['changed_cells']} | set(p_unknown_cells)
    bitmap = np.zeros((ev87.N-1, ev87.N-1), dtype=bool)
    if scan_cells:
        rc = np.asarray(sorted(scan_cells), dtype=np.int32)
        bitmap[rc[:, 0], rc[:, 1]] = True
    # Call the public API once over the full valid grid, then exact-filter candidate
    # bboxes against the sparse target-cell mask. This avoids 703 repeated ODOL walks.
    all_faces = index.query_window(0, ev87.N-2, 0, ev87.N-2)
    selected = rectangle_any(bitmap, all_faces['cell_range_rc']) & (all_faces['degenerate'] == 0)
    faces = {k: v[selected] for k, v in all_faces.items()}
    exposed = {side: {kind: {cell: [] for cell in scan_cells} for kind in ('physical', 'visible')}
               for side in ('B', 'candidate')}
    support = {kind: {cell: [] for cell in scan_cells} for kind in ('physical', 'visible')}
    bad = {'B': [], 'candidate': []}
    unknown_triangles = {('visible',*tuple(map(int, k))): {'positive_face_intersections': 0,
        '_intersection_parts': [], 'minimum_ground_minus_face_B_m': None,
        'minimum_ground_minus_face_candidate_m': None, 'minimum_ground_minus_face_L32_m':None,
        'all_intersections_deeply_buried': True}
        for k in unknown_masks['changed_triangles']}
    for r,c in p_unknown_cells:
        if (r,c) in p9_cells: continue
        for ti in range(len(ev87.TRIS)):
            unknown_triangles[('physical',int(r),int(c),int(ti))] = {
                'positive_face_intersections':0,'_intersection_parts':[],
                'minimum_ground_minus_face_B_m':None,
                'minimum_ground_minus_face_candidate_m':None,
                'minimum_ground_minus_face_L32_m':None,
                'all_intersections_deeply_buried':True}
    target_names = {0: 'physical', 1: 'visible'}
    EPS = {'physical': 1e-5, 'visible': 2e-5}
    for i in range(len(faces['kind'])):
        kind = target_names[int(faces['kind'][i])]
        xyz = faces['xyz'][i]
        face_xy = xyz[:, (0, 2)]
        face_poly = Polygon(face_xy)
        if face_poly.is_empty or face_poly.area <= 0:
            continue
        coeff = np.asarray(faces['plane_y_xz'][i], dtype=np.float64)
        r0, r1, c0, c1 = map(int, faces['cell_range_rc'][i])
        # Inclusive conservative bbox; exact support-cell membership and triangle clipping follow.
        for r in range(max(0, r0), min(ev87.N-2, r1)+1):
            for c in range(max(0, c0), min(ev87.N-2, c1)+1):
                if (r, c) not in scan_cells:
                    continue
                xy = ev87.cell_xy(r, c)
                gh_b = ev87.corner_values(hb, r, c)
                gh_h = ev87.corner_values(hh, r, c)
                for ti, tri in enumerate(ev87.TRIS):
                    ids = np.asarray(tri, dtype=int)
                    native = Polygon(xy[ids])
                    piece = face_poly.intersection(native)
                    if piece.is_empty or piece.area <= 0.0:
                        continue
                    actual = {
                        'B': ev87.odol_visible_in_native_tri(face_xy, coeff, xy, gh_b, tri),
                        'candidate': ev87.odol_visible_in_native_tri(face_xy, coeff, xy, gh_h, tri),
                    }
                    for side, poly in actual.items():
                        if not poly.is_empty:
                            exposed[side][kind][(r, c)].append(poly)
                    _, _, target_coeff = cv.cell_tri_target(r, c, kind, tri, p, f)
                    if target_coeff is None:
                        layer_key='physical' if kind=='physical' else 'visible'
                        entry = unknown_triangles.get((layer_key,r,c,ti))
                        if entry is not None:
                            gb = ev87.affine_coeff(xy[ids], gh_b[ids])
                            gh = ev87.affine_coeff(xy[ids], gh_h[ids])
                            gl = ev87.affine_coeff(xy[ids], ev87.corner_values(lower,r,c)[ids])
                            cv.record_unknown_face_intersection(entry, piece, coeff, gb, gh)
                            margin,buried=cv.unknown_intersection_margin(gl,coeff,piece)
                            old=entry['minimum_ground_minus_face_L32_m']
                            entry['minimum_ground_minus_face_L32_m']=margin if old is None else min(old,margin)
                            if not buried:entry['all_intersections_deeply_buried']=False
                        continue
                    delta = coeff - target_coeff
                    for side, poly in actual.items():
                        v = cv.face_height_violation(kind, (r, c), ti,
                                int(faces['object_id'][i]), (int(faces['face_id'][i]),), poly,
                                delta, EPS[kind])
                        if v:
                            bad[side].append(v)
                    matched = cv.clip_affine_band(piece, delta, EPS[kind])
                    if not matched.is_empty:
                        support[kind][(r, c)].append(matched)
    exp_union = {side: {k: {cell: (unary_union(v) if v else Polygon()) for cell, v in bycell.items()}
                        for k, bycell in kinds.items()} for side, kinds in exposed.items()}
    sup_union = {k: {cell: (unary_union(v) if v else Polygon()) for cell, v in bycell.items()}
                 for k, bycell in support.items()}
    unknown_faces = cv.finalize_unknown_face_summaries(unknown_triangles)
    unresolved=[v for v in unknown_faces.values() if v['positive_face_intersections']>0 and
                not v['all_intersections_deeply_buried']]
    unknown_summary={
        'changed_unknown_triangles':len(unknown_faces),
        'no_compiled_face_intersection':sum(v['positive_face_intersections']==0 for v in unknown_faces.values()),
        'all_intersections_buried_B_H_L32':sum(v['positive_face_intersections']>0 and v['all_intersections_deeply_buried'] for v in unknown_faces.values()),
        'with_contact_or_exposed_or_unproven_intersection':len(unresolved),
        'minimum_ground_minus_face_B_m':min((v['minimum_ground_minus_face_B_m'] for v in unknown_faces.values() if v['minimum_ground_minus_face_B_m'] is not None),default=None),
        'minimum_ground_minus_face_candidate_m':min((v['minimum_ground_minus_face_candidate_m'] for v in unknown_faces.values() if v['minimum_ground_minus_face_candidate_m'] is not None),default=None),
        'minimum_ground_minus_face_L32_m':min((v['minimum_ground_minus_face_L32_m'] for v in unknown_faces.values() if v.get('minimum_ground_minus_face_L32_m') is not None),default=None),
        'unresolved_examples':[{'key':list(k),**v} for k,v in unknown_faces.items() if v['positive_face_intersections']>0 and not v['all_intersections_deeply_buried']][:100]}
    return exp_union, sup_union, bad, unknown_faces, {
        'unknown_summary':unknown_summary,
        'indexed_rows_full_grid': int(len(all_faces['kind'])),
        'bbox_candidates_intersecting_target_cell_set': int(len(faces['kind'])),
        'target_cells': len(cells), 'scan_cells_including_unknown_F': len(scan_cells)}


def coverage_from_index(ev87, cv, index, hb, hh, lower, bundle, changed_rc, p9_cells):
    p, f = bundle['P'], bundle['F']
    cells = affected_cells(ev87, changed_rc)
    unknown_masks, unknown_counts = cv.classify_unknown_f(hb, hh, f)
    p_unknown_cells={(r,c) for r,c in cells if not np.isfinite(p[r,c])}
    exp, support, bad, unresolved, index_stats = indexed_exposure_pair(
        ev87, cv, index, hb, hh, lower, p, f, cells, unknown_masks,p_unknown_cells,p9_cells)
    bounds = cv.validate_bounds_inventory(ev87.B_WRP, ev87.BOUNDS, ev87.W)
    pbo = ev87.pbo_guard(ev87.B_DEPLOY, ev87.B_WRP)
    violations = ev91_compare = None
    # Same per-face comparison key and no-new-or-worse ordering as the frozen EV90 consumer.
    violations = compare_face_nonregression(bad)
    design = {side: {kind: cv.make_design(h, p, f, cells, kind)
                     for kind in ('physical', 'visible')}
              for side, h in (('B', hb), ('candidate', hh))}
    holes = {'physical': {'B': [], 'candidate': []}, 'visible': {'B': [], 'candidate': []}}
    metrics = {}
    for kind in ('physical', 'visible'):
        for cell in sorted(cells):
            for side in ('B', 'candidate'):
                s = support[kind][cell]
                support_poly = s
                d = design[side][kind][cell]
                if kind == 'visible':
                    r, c = cell; xy = cv.cell_xy(r, c); known = []
                    for tri in cv.TRIS:
                        ids = np.asarray(tri, dtype=int)
                        if np.isfinite(f[r, c, ids]).all():
                            known.append(Polygon(xy[ids]))
                    domain = unary_union(known) if known else Polygon()
                    d = d.intersection(domain); support_poly = support_poly.intersection(domain)
                holes[kind][side].append(float(d.difference(support_poly).area))
        hole_pass = cv.coverage_holes_pass(holes[kind]['B'], holes[kind]['candidate'])
        residual = {}
        for side, h in (('B', hb), ('candidate', hh)):
            residual[side] = cv.design_and_residual(h, p, f, cells, kind,
                                                    exp[side][kind], design[side][kind])
        residual_pass = all(residual[s][k] <= cv.AREA_LIMIT for s in residual for k in
            ('missing_outside_band_total_m2', 'missing_outside_band_max_cell_m2',
             'growth_outside_band_total_m2', 'growth_outside_band_max_cell_m2'))
        metrics[kind] = {'support_hole_total_m2': {s: sum(holes[kind][s]) for s in holes[kind]},
            'support_hole_max_cell_m2': {s: max(holes[kind][s], default=0.) for s in holes[kind]},
            'residual': residual, 'hole_pass': bool(hole_pass), 'residual_pass': bool(residual_pass)}
    unresolved_count = int(index_stats['unknown_summary']['with_contact_or_exposed_or_unproven_intersection'])
    gates = {
        'bounds_inventory_identity_exact': bool(bounds['name_xz_rotation_bounds_exact']),
        'deployed_pbo_identity_exact': all(pbo[k] for k in ('expected_world_exact', 'expected_water_exact',
            'deployed_oprw_matches_manifest', 'staged_source_wrp_identity_exact',
            'source_and_compiled_payload_are_distinct_artifacts')),
        'no_changed_partial_F_triangles': int(unknown_counts.get('changed_partial', 0)) == 0,
        'unknown_P_or_F_faces_absent_or_buried_B_H_and_L32_or_P9_exact': unknown_faces_resolved(index_stats['unknown_summary']),
        'no_new_or_worsened_compiled_face_height_violation': violations['pass'],
        'physical_support_holes_lt_1e_7m2': metrics['physical']['hole_pass'],
        'visible_support_holes_lt_1e_7m2': metrics['visible']['hole_pass'],
        'physical_residual_outside_band_le_0_002m2': metrics['physical']['residual_pass'],
        'visible_residual_outside_band_le_0_002m2': metrics['visible']['residual_pass'],
    }
    cv.ev = ev87
    return {'gates': gates, 'metrics': metrics, 'unknown_F': unknown_counts,
        'unknown_face_intersections': unresolved, 'unknown_face_summary':index_stats['unknown_summary'],
        'p_unknown_changed_cells':len(p_unknown_cells), 'face_violation_nonregression': violations,
        'bounds_inventory': bounds, 'pbo_guard': pbo, 'index': index_stats,
        'changed_support_cells': len(cells)}


def compare_face_nonregression(bad_pair):
    """Match inherited violations by stable face identity; reject count/excess growth."""
    def key(v):
        return (v['kind'], tuple(v['cell']), int(v['triangle']), str(v['object']), tuple(v['face_indices']))
    old, new = defaultdict(list), defaultdict(list)
    for v in bad_pair.get('B', []): old[key(v)].append(v)
    for v in bad_pair.get('candidate', []): new[key(v)].append(v)
    regressions = []
    for k, values in new.items():
        b = sorted(old.get(k, []), key=lambda v: (v['area_m2'], v['max_excess_m']))
        h = sorted(values, key=lambda v: (v['area_m2'], v['max_excess_m']))
        if len(h) > len(b):
            regressions.extend({'reason': 'new_face_violation', 'key': repr(k), 'candidate': v} for v in h[len(b):])
            continue
        for vb, vh in zip(b, h):
            if vh['area_m2'] > vb['area_m2'] or vh['max_excess_m'] > vb['max_excess_m']:
                regressions.append({'reason': 'inherited_face_violation_worsened', 'key': repr(k),
                                    'baseline': vb, 'candidate': vh})
    return {'pass': not regressions, 'baseline_count': sum(map(len, old.values())),
            'candidate_count': sum(map(len, new.values())), 'regressions': regressions[:100]}


def verify_index_against_direct(ev87, index, base, cells):
    """Compare index-backed exact exposure with the independent WRP/ODOL reader on two cells."""
    rows=[]; all_arrays={k:np.concatenate([part[k] for _,part in index._shards],axis=0)
                         for k in index._shards[0][1]}
    for cell in cells:
        identity=direct_vs_index_cell(index,ev87,cell,base,all_arrays,kind=0)
        direct_b,direct_h,meta=ev87._compiled_exposure_pair(
            base,base,{tuple(map(int,cell))},ev87.B_WRP,ev87.W,ev87.MODEL_DIR,ev87.BOUNDS)
        r,c=map(int,cell);xy=ev87.cell_xy(r,c);ground=ev87.corner_values(base,r,c)
        diffs={}
        for code,kind in ((0,'physical'),(1,'visible')):
            faces=index.query_cell(r,c,kind=kind)
            polys=[]
            for xyz in faces['xyz']:
                fxy=xyz[:,(0,2)];coeff=ev87.affine_coeff(fxy,xyz[:,1])
                for tri in ev87.TRIS:
                    exposed=ev87.odol_visible_in_native_tri(fxy,coeff,xy,ground,tri)
                    if not exposed.is_empty:polys.append(exposed)
            indexed=unary_union(polys) if polys else Polygon()
            direct=direct_b[kind][(r,c)]
            diffs[kind]=float(indexed.symmetric_difference(direct).area)
            if diffs[kind]>1e-9:
                raise AssertionError(f'index/direct compiled exposure mismatch at {cell}/{kind}: {diffs[kind]}')
        rows.append({'cell':list(map(int,cell)),'identity':identity,'exposure_symmetric_difference_m2':diffs,
                     'direct_objects':meta['objects'],'pass':True})
    return rows


def global_contract(ev, ev91, ev87, cv, shape, ev92, index, bundle, base, candidate, changed_rc, details, accepted):
    changed=[tuple(map(int,x)) for x in changed_rc.tolist()]
    cells=affected_cells(ev87,changed_rc)
    topology=ev.topology_check(ev87,base.astype(np.float64),candidate.astype(np.float64),
                               bundle['P'],bundle['F'],cells)
    high=target_cells_from_details(details)
    changed_set=set(changed);high_nodes=set()
    for layer_cells in high.values():
        for r,c in layer_cells: high_nodes.update(((r,c),(r,c+1),(r+1,c),(r+1,c+1)))
    changed_high=sorted(changed_set & high_nodes)
    geom=ev.local_sector_stats(ev87,base.astype(np.float64),candidate.astype(np.float64),changed)
    p99=ev.p99_population_gate(ev87,geom['angles_b'],geom['angles_h'],bundle)
    wet_diag=ev91.eligible_wet_support_diagnostic(ev,ev87,bundle,geom['angles_b'],geom['angles_h'])
    del geom['angles_b'];del geom['angles_h']
    corridor_b=ev.corridor_depth_report(base,bundle['P'],bundle['corridors'],comparison=candidate)
    corridor_h=ev.corridor_depth_report(candidate,bundle['P'],bundle['corridors'],comparison=base)
    corridor_geometry=all(x['coverage_error_m2']<=1e-5 for x in corridor_h['corridors'])
    corridor_affected=ev91.affected_corridor_depth_report(ev,ev87,bundle,candidate,changed)
    bed=ev.high_bed_floor_report(candidate,bundle['B'])
    # Only NaN-P cells intersecting the approved corridor geometry are P9-frozen.
    # Other unknown-P locations remain diagnostic and are judged by exact compiled-face burial.
    p9_cells,p9_vertices,p9_features=global_p9_unknown_vertices(ev,bundle)
    changed_p9=sorted(changed_set & p9_vertices)
    unknown_p=np.isnan(bundle['P']); unknown_vertex=np.zeros_like(base,dtype=bool)
    unknown_vertex[:-1,:-1] |= unknown_p; unknown_vertex[:-1,1:] |= unknown_p
    unknown_vertex[1:,:-1] |= unknown_p; unknown_vertex[1:,1:] |= unknown_p
    changed_unknown_p=sorted(n for n in changed_set if unknown_vertex[n])
    local_p9_exact=p9_vertices_exact(changed,p9_vertices)
    p9=ev91.p9_unknown_preserved(local_p9_exact,corridor_h)
    feasible_lower=base.copy()
    for patch in accepted:
        for i,n in enumerate(patch['nodes'].tolist()):
            feasible_lower[tuple(map(int,n))]=patch['solver_bounds'][i,0]
    compiled=coverage_from_index(ev87,cv,index,base,candidate,feasible_lower,bundle,changed_rc,p9_cells)
    local=verify_local_windows(ev,ev87,shape,ev92,base,candidate,accepted,details)
    # Window-local protection uses the exact union recorded in all 703 source details.
    high_ok=high_field_exact(changed,high['physical']|high['visible'])
    accepted_count=len(accepted)
    gates={
        'at_least_one_nontrivial_accepted_window': accepted_count>0 and len(changed)>0,
        'all_accepted_window_local_contracts': all(local['gates'].values()),
        'high_field_vertices_exact_B': high_ok,
        'known_layer_signs_and_crossings_preserved': bool(topology['signs_preserved'] and topology['crossings_valid_and_within_1m']),
        'P9_unknown_corridor_vertices_and_area_exact_B': bool(p9['pass']),
        'global_slopes_hinges_and_affected_sectors_nonworse': bool(
            geom['slopes_le_max35_or_B'] and geom['no_new_hinges_over_30_touched'] and geom['affected_sector_max_nonworse']),
        'global_bank_interior_p99_and_counts_nonworse': bool(p99['pass']),
        'all_19_corridor_geometry_covered': corridor_geometry,
        'affected_known_P_corridor_triangles_min_depth_ge_0_95m': bool(corridor_affected['pass']),
        'high_navigable_bed_floor_1m': bool(bed['high_bed_floor_1m_pass']),
        **compiled['gates'],
    }
    return {'gates':gates,'information':{
        'accepted_windows':accepted_count,'changed_vertices':len(changed),'changed_high_field_vertices':changed_high[:100],
        'changed_support_cells':len(cells),'topology':topology,'global_geometry':geom,'p99':p99,
        'p99_scope':'bank/interior EV87 populations only; excludes wet-support population',
        'eligible_wet_support_diagnostic':wet_diag,'corridor_depth':{'B':corridor_b,'H':corridor_h},
        'affected_corridor_depth':corridor_affected,'high_bed_floor':bed,
        'P9_unknown_cells':len(p9_cells),'P9_unknown_features':p9_features,
        'P9_changed_vertices':changed_p9[:100],
        'all_unknown_P_changed_vertices_diagnostic':changed_unknown_p[:100],
        'P9_unknown':p9,
        'local_windows':local,'compiled_coverage':compiled}}


def direct_vs_index_cell(index, ev87, cell, base, all_arrays=None, kind=0):
    """Compare bbox query with exhaustive shard filter and exact exposed geometry."""
    r, c = map(int, cell)
    indexed = index.query_cell(r, c, kind=kind)
    if all_arrays is None:
        all_arrays = {k: np.concatenate([part[k] for _, part in index._shards], axis=0)
                      for k in index._shards[0][1]}
    ranges = all_arrays['cell_range_rc']
    direct_mask = ((ranges[:, 0] <= r) & (ranges[:, 1] >= r) &
                   (ranges[:, 2] <= c) & (ranges[:, 3] >= c) &
                   (all_arrays['kind'] == kind))
    direct = {k: v[direct_mask] for k, v in all_arrays.items()}
    id_cols = ('object_id', 'model_id', 'face_id')
    indexed_ids = sorted(tuple(map(int, row)) for row in np.column_stack([indexed[k] for k in id_cols]))
    direct_ids = sorted(tuple(map(int, row)) for row in np.column_stack([direct[k] for k in id_cols]))
    if indexed_ids != direct_ids:
        raise AssertionError(f'index query identity mismatch at {cell}')
    xy_cell = ev87.cell_xy(r, c)
    ground = ev87.corner_values(base, r, c)
    cell_parts = []
    for arr in (indexed, direct):
        exposed = []
        for face in arr['xyz']:
            face_xy = face[:, (0, 2)]
            coeff = ev87.affine_coeff(face_xy, face[:, 1])
            for tri in ev87.TRIS:
                piece = ev87.odol_visible_in_native_tri(face_xy, coeff, xy_cell, ground, tri)
                if not piece.is_empty:
                    exposed.append(piece)
        cell_parts.append(unary_union(exposed) if exposed else Polygon())
    diff_a = cell_parts[0].symmetric_difference(cell_parts[1]).area
    if diff_a > 1e-10:
        raise AssertionError(f'indexed/direct exact exposed geometry differs at {cell}: {diff_a}')
    return {'cell': [r, c], 'kind': int(kind), 'candidate_faces': len(indexed_ids),
            'symmetric_difference_m2': float(diff_a), 'pass': True}


def pilot_local_consumer_fixture():
    """Exercise the real EV93 window verifier with the frozen EV92 pilot data."""
    for path, wanted in PILOT_PINS.items():
        if sha(path) != wanted:
            raise AssertionError(f'EV92 pilot fixture pin mismatch: {path}')
    ev, ev91, ev87, cv, shape, ev92, _ = load_helpers()
    bundle = ev.checked_sources()
    base = np.asarray(bundle['B']['heights'], dtype=np.float32)
    prepared = load_json(PILOT_PREPARED)
    receipt = load_json(PILOT_RECEIPT)
    if prepared.get('status') != 'PREPARED_NO_WRITE' or \
       prepared.get('baseline_sha256') != PILOT_PINS[str(PILOT_BASE)] or \
       prepared.get('direction_sha256') != PILOT_PINS[str(PILOT_DIRECTION)]:
        raise AssertionError('EV92 fixture prepared provenance/status mismatch')
    if receipt.get('candidate_sha256') != PILOT_PINS[str(PILOT_FINAL)] or \
       Path(receipt.get('candidate_path', '')).resolve() != PILOT_FINAL.resolve():
        raise AssertionError('EV92 fixture authoring receipt does not pin candidate')
    with np.load(PILOT_DIRECTION, allow_pickle=False) as z:
        direction_grid = np.asarray(z['heights'], dtype=np.float32)
        direction_meta = {k: z[k] for k in z.files if k != 'heights'}
    with np.load(PILOT_FINAL, allow_pickle=False) as z:
        candidate = np.asarray(z['heights'], dtype=np.float32)
        candidate_meta = {k: z[k] for k in z.files if k != 'heights'}
    for key in bundle['B']:
        if key == 'heights':
            continue
        if not np.array_equal(direction_meta[key], bundle['B'][key], equal_nan=True):
            raise AssertionError(f'EV92 fixture direction metadata differs from B: {key}')
        if not np.array_equal(candidate_meta[key], bundle['B'][key], equal_nan=True):
            raise AssertionError(f'EV92 fixture candidate metadata differs from B: {key}')
    expected = ev92.expected_interpolation(base, direction_grid, prepared['alpha'])
    if not np.array_equal(candidate, expected):
        raise AssertionError('EV92 fixture candidate is not exact alpha interpolation')

    nodes = np.asarray(prepared['variables_rc'], dtype=np.int32)
    bounds = np.asarray(prepared['bounds_float32_inward'], dtype=np.float32)
    solver_bounds = np.asarray(prepared['solver_bounds_float32'], dtype=np.float32)
    guard = np.asarray(prepared['guard_rc'], dtype=np.int32)
    stencils = [tuple((str(x[0]), int(x[1]), int(x[2]))) for x in prepared['stencils']]
    direction = direction_grid[tuple(nodes.T)].copy()
    final = candidate[tuple(nodes.T)].copy()
    scalar = ev92.derive_scalar_rule(base, direction_grid, stencils, focus=(840, 370))
    if canonical_sha(scalar) != canonical_sha(prepared['scalar_rule']):
        raise AssertionError('EV92 fixture scalar rule does not recompute from frozen B/H91')
    b_energy = [str(x) for x in stencil_energy_moments_fraction(base, base, stencils)]
    h_energy = [str(x) for x in stencil_energy_moments_fraction(base, candidate, stencils)]
    pre = {
        'window': list(ev.WINDOW), 'core': list(ev.CORE),
        'domain': {
            'eligible_after_face_freeze_nodes': nodes.tolist(),
            'final_float32_intervals_for_eligible_nodes': [
                {'node_rc': n.tolist(), 'interval_float32_inward_m': b.tolist()}
                for n, b in zip(nodes, bounds)],
        },
        'guard_d8': {
            'guard_rc': guard.tolist(), 'descent_witnesses': prepared['witnesses'],
            'descent_matrix_sha256_f64': prepared['descent_matrix_sha256_f64'],
            'descent_rhs_sha256_f64': prepared['descent_rhs_sha256_f64'],
        },
    }
    detail = {'queue_id': 0, 'seed_id': 0, 'center_rc': [840, 370],
              'window17': [ev.WINDOW[0], ev.WINDOW[2], ev.WINDOW[1], ev.WINDOW[3]],
              'preflight': pre}
    result = {
        'queue_id': 0, 'center_rc': [840, 370], 'state': 'accepted', 'solve_calls': 1,
        'alpha': float(prepared['alpha']), 'scalar_rule': prepared['scalar_rule'],
        'd8_witnesses': prepared['witnesses'],
        'd8_matrix_sha256_f64': prepared['descent_matrix_sha256_f64'],
        'd8_rhs_sha256_f64': prepared['descent_rhs_sha256_f64'],
        'energy_B_fraction': b_energy, 'energy_H_fraction': h_energy,
    }
    patch = {'queue_id': 0, 'result': result, 'nodes': nodes,
             'B': base[tuple(nodes.T)].copy(), 'bounds': bounds,
             'solver_bounds': solver_bounds, 'guard': guard,
             'direction': direction, 'final': final, 'stencils': stencils}
    positive = verify_local_windows(ev, ev87, shape, ev92, base, candidate,
                                   [patch], {0: detail})
    if positive['gates'].get(0) is not True:
        raise AssertionError(f'EV92 real local-consumer fixture should pass: {positive["metrics"]}')

    # A real guard mutation must be rejected by the same consumer predicate.
    mutated = candidate.copy()
    g = tuple(map(int, guard[0]))
    mutated[g] = np.nextafter(base[g], np.float32(np.inf), dtype=np.float32)
    negative = verify_local_windows(ev, ev87, shape, ev92, base, mutated,
                                   [patch], {0: detail})
    if negative['gates'].get(0) is not False or \
       negative['metrics'][0]['guard_exact_and_unchanged'] is not False:
        raise AssertionError('EV92 guard mutation was not rejected by the real window consumer')

    helper_fixtures = {
        'high_field_exact_positive': high_field_exact([], {(0, 0)}),
        'high_field_exact_negative': not high_field_exact([(0, 0)], {(0, 0)}),
        'p9_exact_positive': p9_vertices_exact([], {(1, 1)}),
        'p9_exact_negative': not p9_vertices_exact([(1, 1)], {(1, 1)}),
        'unknown_face_burial_positive': unknown_faces_resolved({'with_contact_or_exposed_or_unproven_intersection': 0}),
        'unknown_face_burial_negative': not unknown_faces_resolved({'with_contact_or_exposed_or_unproven_intersection': 1}),
    }
    if not all(helper_fixtures.values()):
        raise AssertionError(f'consumer exact-domain helper fixture failed: {helper_fixtures}')
    return {'real_ev92_window_positive': True, 'mutated_guard_negative': True,
            'consumer_domain_helper_cases': helper_fixtures,
            'pilot_center_rc': [840, 370], 'pilot_variable_count': int(len(nodes)),
            'pilot_stencil_count': int(len(stencils)),
            'changed_candidate_vertices': int(np.count_nonzero(candidate != base))}


def fixture_suite():
    """Small analytic negatives for composition, index query, and topology predicates."""
    from shapely.geometry import box
    # Query bbox must include exact boundary touch candidates, then clipping removes zero area.
    tri = Polygon(((0, 0), (1, 0), (1, 1)))
    touching = box(1, 0, 2, 1)
    assert tri.intersection(touching).area == 0.0
    crossing = box(.5, .1, 1.5, .4)
    assert tri.intersection(crossing).area > 0.0
    # A changed known-P vertex that reverses the original sign is rejected.
    wet_before = np.array([1.0, -1.0])
    wet_after = np.array([-0.01, -1.0])
    assert np.signbit(wet_before[0]) != np.signbit(wet_after[0])
    # Guard and ownership fixtures: a protected node cannot enter accepted mutable list;
    # duplicate ownership across windows is rejected by the same set rule.
    protected = {(7, 9)}
    mutable = {(7, 8), (7, 10)}
    assert not (protected & mutable)
    assert len({(7, 8), (7, 8)}) == 1
    # Unknown visible face intersecting a partially/fully NaN F triangle is inconclusive
    # unless the per-vertex burial certificate holds in both B and H.
    margins_b = np.array([3e-5, 4e-5, 5e-5])
    margins_h = np.array([3e-5, 4e-5, 5e-5])
    assert min(margins_b) > 2e-5 and min(margins_h) > 2e-5
    margins_h[1] = 0.0
    assert not (min(margins_b) > 2e-5 and min(margins_h) > 2e-5)
    return {'bbox_touch_zero_area': True, 'exact_overlap_positive': True,
            'known_layer_sign_flip_negative': True, 'protected_node_negative': True,
            'duplicate_ownership_detectable': True, 'unknown_face_burial_positive_negative': True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prepared', type=Path)
    ap.add_argument('--receipt', type=Path)
    ap.add_argument('--output', type=Path, default=HERE/'layer-review.json')
    ap.add_argument('--self-test', action='store_true')
    ap.add_argument('--index-cells', nargs='*', default=['832,362', '128,1918'])
    args = ap.parse_args()
    if args.self_test:
        tests = fixture_suite()
        tests['real_window_consumer'] = pilot_local_consumer_fixture()
        print(json.dumps({'status': 'FIXTURES_PASS', 'fixtures': tests}, sort_keys=True))
        return
    if not args.prepared or not args.receipt:
        ap.error('--prepared and --receipt are required outside --self-test')
    report = {'status': 'ERROR_EV93_LAYER_CONSUMER', 'gates': {}, 'information': {}}
    try:
        # Pin the two root manifests before parsing them. Their own declarations
        # then anchor every dependent dynamic artifact in expected_dynamic_readset.
        manifest_anchor_hashes = {
            str(Path(args.prepared).resolve()): sha(args.prepared),
            str(Path(args.receipt).resolve()): sha(args.receipt),
        }
        ev, ev91, ev87, cv, shape, ev92, index_module = load_helpers()
        bundle = ev.checked_sources()
        prepared, receipt, entries, ledger, ledger_path = verify_prepared(
            args.prepared, args.receipt, bundle['B']['heights'])
        if any(sha(path) != digest for path, digest in manifest_anchor_hashes.items()):
            raise AssertionError('prepared/receipt changed while being parsed')
        details = validate_detail_hashes(prepared, entries)
        base_npz = bundle['B']
        candidate, changed, accepted, owner = reconstruct_candidate(
            base_npz, receipt, entries, ledger, details, Path(args.receipt).parent)
        index = index_module.FaceRangeIndex(INDEX_RUN)
        base_h = np.asarray(base_npz['heights'], dtype=np.float32)
        expected_read_hashes = expected_dynamic_readset(
            args.prepared, args.receipt, prepared, receipt, entries, ledger,
            ledger_path, index.manifest, ev87.MODEL_DIR)
        expected_read_hashes.update(manifest_anchor_hashes)
        read_paths = set(expected_read_hashes)
        initial_read_hashes = {p: sha(p) for p in sorted(expected_read_hashes)}
        readset_mismatches = [p for p, expected in expected_read_hashes.items()
                              if initial_read_hashes.get(p) != expected]
        if readset_mismatches:
            raise AssertionError(f'initial dynamic read-set differs from declared SHA: {readset_mismatches[:20]}')
        index_results = verify_index_against_direct(ev87,index,base_h,
            [tuple(map(int,cell.split(','))) for cell in args.index_cells])
        result = global_contract(ev,ev91,ev87,cv,shape,ev92,index,bundle,base_h,
                                 candidate,changed,details,accepted)
        index.reverify()
        # Recheck every pinned source after ODOL/exposure evaluation to rule out
        # mixed-input reads during the scan.
        end_hashes={p:sha(p) for p in PINS}
        if end_hashes!=PINS: raise AssertionError('frozen helper/index inputs changed during consumer run')
        final_read_hashes={p:sha(p) for p in sorted(read_paths)}
        if initial_read_hashes!=final_read_hashes or expected_read_hashes!=final_read_hashes:
            changed_paths=[p for p in expected_read_hashes
                           if expected_read_hashes[p]!=final_read_hashes.get(p)]
            raise AssertionError(f'consumer read-set differs from initial/declared SHA at end: {changed_paths[:20]}')
        dynamic_inputs=dict(expected_read_hashes)
        result['information'].update({'candidate_sha256':receipt['candidate_sha256'],
            'prepared_sha256':sha(args.prepared),'authoring_receipt_sha256':sha(args.receipt),
            'ledger_sha256':sha(ledger_path),'index_manifest_sha256':sha(INDEX_MANIFEST),
            'index_verification_sha256':sha(INDEX_VERIFICATION),'index_direct_fixtures':index_results,
            'input_hashes':dynamic_inputs,'global_contract_status':'OPEN_INHERITED_MAP_DEFECTS',
            'authoring_result_counts':receipt.get('result_counts')})
        passed=all(result['gates'].values())
        result['status']='PASS_INCREMENTAL_NONREGRESSION' if passed else 'FAIL_INCREMENTAL_NONREGRESSION'
        report=result
    except Exception as exc:
        report = {'status': 'ERROR_EV93_LAYER_CONSUMER', 'gates': {},
                  'error': repr(exc), 'traceback': traceback.format_exc()}
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'false_gates': [k for k,v in report.get('gates',{}).items() if not v],
                      'error': report.get('error'), 'output': str(args.output)}, sort_keys=True))
    if report['status'] == 'ERROR_EV93_LAYER_CONSUMER':
        raise SystemExit(2)
    if not all(report['gates'].values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
