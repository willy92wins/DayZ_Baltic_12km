#!/usr/bin/env python
"""EV94 rebase: rebuild one sector preflight on the accepted focal composition.

Read-only with respect to terrain and runtime. Writes only preflight artifacts;
never invokes an optimizer/solver or exports a map candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(r'E:/DayZ-Baltic-Build')
G = ROOT / 'v30-global-bank-extension-20261010'
HERE = G / 'global-operator-prototype/real-sector-preflight'
EV94 = HERE / 'ev94-rebase'
OUT_DEFAULT = EV94 / 'preflight-run-01'
PLAN = EV94 / 'PLAN_EV94_REBASE.md'
SOURCE_PLAN = G / 'global-operator-prototype/PLAN_REAL_SECTOR.md'
PREVIOUS_DRIVER = HERE / 'solve_real_sector.py'

FOCAL = HERE / 'focus-unit/author-run-01/candidate-terrain.npz'
FOCAL_COMPOSITION = HERE / 'focus-unit/composition-run-01/review.json'
FOCAL_SUPPLEMENT = HERE / 'focus-unit/consumer-run-01/acceptance-supplement.json'
FOCAL_CONSUMER = HERE / 'focus-unit/consumer-run-01/review.json'
SELECTED = G / 'compound-selection/run-02/selection.json'
SELECTED_REPORT = G / 'crest-extension/selected-consumer-runs/attempt-03/review.json'
SELECTED_CONSUMER = G / 'crest-extension/verify_selected_composite_v2.py'
EV93_CANDIDATE = G / 'compound-selection/run-02/candidate-terrain.npz'
EV82_B = ROOT / 'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
EV93_SOURCE_REPORT = G / 'consumer-global/runs/attempt-04/ev93-review.json'
QUEUE = G / 'queue/queue.json'
EV93_SELECTION_PLAN = G / 'crest-extension/EXECUTION_PLAN_V2.md'
POOL = G / 'crest-extension/quarantine-pool-v3/compound-pool.json'
POOL_LEDGER = G / 'crest-extension/quarantine-pool-v3/ledger.jsonl'
POOL_RECEIPT = G / 'crest-extension/quarantine-pool-v3/receipt.json'
LEGACY_LEDGER = G / 'fairing-layer1/ledger.jsonl'
LEGACY_PREPARED = G / 'fairing-layer1/prepared.json'
COMPOUND_SELECTOR = G / 'compound-selection/selector.py'

EV87 = ROOT / 'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
EV79_DIR = ROOT / 'v30-narva-dry-bank-relief-20261010'
B_DIR = ROOT / 'v30-mixed-bank-incremental-fixed-20261010'
EV79 = EV79_DIR / 'candidate/terrain.npz'
CONS = EV79_DIR / 'constraints.npz'
PRIOR = ROOT / 'v30-remaining-exact-dry-support-20261009/constraints.npz'
P = EV79_DIR / 'candidate/plane.npy'
F = EV79_DIR / 'candidate/visible-field.npy'
EV82_AUTHOR = B_DIR / 'author.py'
DEPLOY = B_DIR / 'deploy.json'
WRP = B_DIR / 'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
PROTO = G / 'global-operator-prototype/prototype.py'
D8 = G / 'constrained-pilot/d8_sparse_pilot.py'
PROJECTION = HERE / 'order-closure/projection.py'

INV_DIR = HERE / 'inventory-run-02.json'
INVENTORY = INV_DIR / 'inventory.json'
DOMAIN_REASONS = INV_DIR / 'domain-reasons.npz'
CIVIL_SCRIPT = HERE / 'civil_inventory.py'
CIVIL_REPORT = HERE / 'civil-run-01.json'
CIVIL_RECEIPT = HERE / 'civil-run-01-receipt.json'
WATER_SCRIPT = HERE / 'prepare_water_footprint.py'
WATER_REPORT = HERE / 'water-run-01/water-support-mask.json'
WATER_MASK = HERE / 'water-run-01/water-support-mask.npz'
INDEX_SOURCE = G / 'ev93-face-index/build_face_index.py'
INDEX_MANIFEST = G / 'ev93-face-index/runs/20261010T092417Z-63d4cec3/manifest.json'
INDEX_VERIFICATION = G / 'review-independent/runs/attempt-01/verification.json'
CORRIDORS = Path(r'E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson')

N = 2048
SEA = 0.85
EPS_WATER = 1e-4
MAX_DELTA = 2.0
EV82_RISE_CAP = 0.5
WINDOW = (712, 968, 242, 498)
FOCUS = (840, 370)
LOCAL_R0, LOCAL_R1, LOCAL_C0, LOCAL_C1 = 710, 970, 240, 500

EXPECTED = {
    'PLAN': '4ba76f70173ac777d3f4b6ad427062d430aabb75a4bb25f70adf04c231b167fd',
    'SOURCE_PLAN': '14f02179312bc25caf76a087cc873122caed30f6092464f1c01ac7572d519749',
    'FOCAL': '30d0ed33e477846297a17e758e34a51490d54ee809e8b63ec9d69229170d15a1',
    'FOCAL_COMPOSITION': 'a5a5aaa1f1f2c06c646bbd54a41ea8fd89d8dee8ffa14d2e59af4d7bc07b05e3',
    'FOCAL_SUPPLEMENT': 'fab5c76e2f1a7a5935cf70bfaa08dedd4500411e4c2ac11670dc7fccc4b89e7f',
    'FOCAL_CONSUMER': 'b9af8d77c2efe342b02012af160a1f8cae44d41d5581be21045da8539116de7e',
    'SELECTED': '3b22dcc381b34b8d7c3e6641d3c919658f0fe7377594a859e3d5c064cf92ba0b',
    'SELECTED_REPORT': '656e676e38817592ed96d13ddeb1693d2a9bead152770256b0b21e665cedf8ec',
    'SELECTED_CONSUMER': '6e661b073e5f27b2475e6b82d75d6a7722d0503a082dcfd51d8f00bd6de9722b',
    'EV93_CANDIDATE': '6e27557315eb65ecc69052e1ec387304a19f37eaa4f5167ab82fb607f095461d',
    'EV82_B': 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
    'EV93_SOURCE_REPORT': 'ed9a071d359dc446b5146a255c3ab9f15481c92e24c2169b6da47dd4ad27c0ec',
    'QUEUE': 'cf13887c8de031d65d0a32dab217e8743293103fcd00ea3c07c281c07a6794c9',
    'EV93_SELECTION_PLAN': '8a4afc1e26dc0d816ade9454ee4f4e31c185b03a56c8a9ef5005f468d0cff9b0',
    'POOL': '4bc16ef8156e4feda5332d8a7917a7b23d2f171a85c4a6002e5f403da95541d5',
    'POOL_LEDGER': '3b5aa471c81005a0532f9d7af4d012bb163b3f864f4bde258cb847cd2666f73b',
    'POOL_RECEIPT': '384f60b44dbb2ae790b008c4956554a328c383f6d3ea237204feb8a7059a0d3e',
    'LEGACY_LEDGER': 'dc0a26cc38f55c1a8bb5709e36cfacd41859c3f901aabed15968a56c44832e85',
    'LEGACY_PREPARED': '765c5a5a778132fce7f1c1d21a59c1220b62443b180238e13ee51a203b3483d4',
    # Selection.json itself records this selector version; later selector freezes
    # do not retroactively establish which code created the retained manifest.
    'COMPOUND_SELECTOR': '0d29d3979c1f8bc0d3b0b1833edb314a5807fe5b22ba63b43c44080732fe81bc',
    'EV87': '964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
    'EV79': 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c',
    'CONS': 'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c',
    'PRIOR': '18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370',
    'P': '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
    'F': 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
    'EV82_AUTHOR': '9b7c5374b7c78c3604bb2763ef8b7b4d16dc4bf18fc57091233ad435876cb74b',
    'PROTO': '5b4b8f08e5205e1f9cc90bcc8e82e61dade45bb82bd22da8ee69303aa4475cc4',
    'D8': '6b5281d9750c30fc5b27171aaec2af59dee88411a66bf5b08e5105866f08252c',
    'PROJECTION': 'a990dc2d33fca4fd2a446b958f0412a2d752a5d3072a85d82058bb634cfaf44b',
    'INVENTORY': 'a1d656fff3b0bd7b2435893ff5e57a0ca92df2068f0db024291bc1409b8eb967',
    'DOMAIN_REASONS': '4a4b3d652c983bc1a6f22dbdf1a359dcb8902591317b5b26126ef02f704abcbf',
    'CIVIL_SCRIPT': '60d1beb2a36739a98fc70dc5a3b29033286e14abbc87461247bc87dd6f48c0c3',
    'CIVIL_REPORT': '1f1670961bd89bfe284ac3175201c1dc2529f6c5b13bb7f4796fab4ac382cd53',
    'CIVIL_RECEIPT': 'bbd51127b6479adc31a79c8932eadf1549be3bd2de19429cbb14998abcd20f01',
    'WATER_SCRIPT': '9f5f9952aaa23f5d673ec4c8375a2cc0d0759e0634d3093a08e23c50437728f1',
    'WATER_REPORT': '74bb37147e20047c44f0228d464650fb35fb9e41e71cf541c4e994f1032c55c9',
    'WATER_MASK': '6ce282962602557636bafac40b604caa3001a95234551db1beee67975dcd1edf',
    'INDEX_SOURCE': 'd1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e',
    'INDEX_MANIFEST': 'c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c',
    'INDEX_VERIFICATION': 'b498e7d68835b199399655451e5e01ac81acb3149dbb9bf882b94858141521d4',
    'CORRIDORS': '28866a8cf6ff57f2f825228046164ef939bc22bca9948eb96fe2463da46af343',
    'DEPLOY': '3c98951f3488eef233d6972621648c84244f9e711c2ff419fd0b8013b427ec00',
    'WRP': '3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6',
}

STATIC_PATHS = {
    'PLAN': PLAN, 'SOURCE_PLAN': SOURCE_PLAN, 'FOCAL': FOCAL, 'FOCAL_COMPOSITION': FOCAL_COMPOSITION,
    'FOCAL_SUPPLEMENT': FOCAL_SUPPLEMENT, 'FOCAL_CONSUMER': FOCAL_CONSUMER,
    'SELECTED': SELECTED, 'SELECTED_REPORT': SELECTED_REPORT,
    'SELECTED_CONSUMER': SELECTED_CONSUMER, 'EV93_CANDIDATE': EV93_CANDIDATE, 'EV82_B': EV82_B,
    'EV93_SOURCE_REPORT': EV93_SOURCE_REPORT, 'EV93_SELECTION_PLAN': EV93_SELECTION_PLAN,
    'QUEUE': QUEUE,
    'POOL': POOL, 'POOL_LEDGER': POOL_LEDGER, 'POOL_RECEIPT': POOL_RECEIPT,
    'LEGACY_LEDGER': LEGACY_LEDGER, 'LEGACY_PREPARED': LEGACY_PREPARED,
    'COMPOUND_SELECTOR': COMPOUND_SELECTOR, 'EV87': EV87, 'EV79': EV79,
    'CONS': CONS, 'PRIOR': PRIOR, 'P': P, 'F': F, 'EV82_AUTHOR': EV82_AUTHOR,
    'PROTO': PROTO, 'D8': D8, 'PROJECTION': PROJECTION,
    'INVENTORY': INVENTORY, 'DOMAIN_REASONS': DOMAIN_REASONS,
    'CIVIL_SCRIPT': CIVIL_SCRIPT, 'CIVIL_REPORT': CIVIL_REPORT,
    'CIVIL_RECEIPT': CIVIL_RECEIPT, 'WATER_SCRIPT': WATER_SCRIPT,
    'WATER_REPORT': WATER_REPORT, 'WATER_MASK': WATER_MASK,
    'INDEX_SOURCE': INDEX_SOURCE, 'INDEX_MANIFEST': INDEX_MANIFEST,
    'INDEX_VERIFICATION': INDEX_VERIFICATION, 'CORRIDORS': CORRIDORS,
    'DEPLOY': DEPLOY, 'WRP': WRP,
}


def sha(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot load {path}')
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_npz(path: Path):
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def f32_lower(x: float) -> np.float32:
    fn = load_module('ev94_d8_bounds', D8).inward32_lower
    return np.float32(fn(float(x)))


def f32_upper(x: float) -> np.float32:
    fn = load_module('ev94_d8_bounds', D8).inward32_upper
    return np.float32(fn(float(x)))


def cap_intersection_bounds(original, current, level, ev82, d8):
    """EV82 original-budget interval AND EV82 B+0.5 rise cap, inward f32."""
    o = np.asarray(original, np.float64)
    b = np.asarray(current, np.float64)
    lv = np.asarray(level, np.float64)
    if o.shape != b.shape or b.shape != lv.shape:
        raise ValueError('O/B/levels shape mismatch')
    if not (np.isfinite(o).all() and np.isfinite(b).all() and np.isfinite(lv).all()):
        raise ValueError('non-finite O/B/levels')
    floors = np.minimum(o, lv + EPS_WATER)
    low = np.empty(b.shape, np.float32)
    high_budget = np.empty(b.shape, np.float32)
    high_cap = np.empty(b.shape, np.float32)
    high = np.empty(b.shape, np.float32)
    limiting = {'budget': 0, 'B_plus_0_5': 0, 'tie': 0}
    for ix in np.ndindex(b.shape):
        step_lo, step_hi = ev82.original_budget_interval(
            float(o[ix]), float(b[ix]), float(floors[ix]), MAX_DELTA)
        lo = d8.inward32_lower(float(b[ix]) + float(step_lo))
        budget_hi = d8.inward32_upper(float(b[ix]) + float(step_hi))
        cap_hi = d8.inward32_upper(float(b[ix]) + EV82_RISE_CAP)
        final_hi = min(float(budget_hi), float(cap_hi))
        low[ix] = lo
        high_budget[ix] = budget_hi
        high_cap[ix] = cap_hi
        high[ix] = final_hi
        if float(budget_hi) < float(cap_hi):
            limiting['budget'] += 1
        elif float(cap_hi) < float(budget_hi):
            limiting['B_plus_0_5'] += 1
        else:
            limiting['tie'] += 1
    if np.any(low > high):
        raise ValueError('empty intersection of EV79/EV82 physical bounds')
    return low, high, high_budget, high_cap, floors, limiting


def add_rect_halo(mask, window, sector):
    r0, r1, c0, c1 = map(int, window)
    sr0, sr1, sc0, sc1 = sector
    a = max(sr0, r0 - 2); b = min(sr1, r1 + 2)
    c = max(sc0, c0 - 2); d = min(sc1, c1 + 2)
    if a < b and c < d:
        mask[a-sr0:b-sr0, c-sc0:d-sc0] = True


def check_window(result: dict, unit_id: str):
    w = result.get('window_rc')
    if not isinstance(w, list) or len(w) != 4:
        raise ValueError(f'{unit_id}: original result lacks window_rc')
    r0, r1, c0, c1 = map(int, w)
    if r1-r0 != 17 or c1-c0 != 17:
        raise ValueError(f'{unit_id}: source window is not 17x17')
    if r0 < 0 or c0 < 0 or r1 > N or c1 > N:
        raise ValueError(f'{unit_id}: window outside world')
    core = result.get('core_rc')
    if core is not None:
        a, b, c, d = map(int, core)
        if not (r0 <= a <= b <= r1 and c0 <= c <= d <= c1):
            raise ValueError(f'{unit_id}: core is not contained by source window')
    return [r0, r1, c0, c1]


def resolve_selected_windows(selection: dict):
    retained = selection.get('retained_unit_ids')
    units = selection.get('units')
    if not isinstance(retained, list) or len(retained) != 499 or len(set(retained)) != 499:
        raise ValueError('retained unit ID list is not exactly 499 unique units')
    if not isinstance(units, list):
        raise ValueError('selection units list missing')
    by_id = {u.get('unit_id'): u for u in units if isinstance(u, dict)}
    if len(by_id) != len(units) or any(x not in by_id for x in retained):
        raise ValueError('selection unit IDs duplicate or missing')
    records = []
    extra_readset = {}
    origin_counts = {'legacy': 0, 'crest': 0}
    for unit_id in retained:
        row = by_id[unit_id]
        if row.get('selection_status') != 'retained' or row.get('local_status') != 'PASS':
            raise ValueError(f'{unit_id}: retained status/local PASS mismatch')
        artifact = Path(row['source_artifact_path'])
        artifact_hash = sha(artifact)
        if artifact_hash != row.get('source_artifact_sha256'):
            raise ValueError(f'{unit_id}: selection source artifact hash mismatch')
        extra_readset[str(artifact)] = artifact_hash
        body = read_json(artifact)
        target_nodes = None
        if row.get('origin') == 'legacy':
            result = body
            if result.get('state') != 'accepted' or int(result.get('solve_calls', 0)) != 1:
                raise ValueError(f'{unit_id}: legacy source result is not accepted')
            if int(result.get('queue_id', -1)) != int(row.get('source_qid', -2)):
                raise ValueError(f'{unit_id}: legacy result qid mismatch')
            origin = 'legacy'
            window = check_window(result, unit_id)
            delta_path = Path(result['delta_path'])
            delta_hash = sha(delta_path)
            if delta_hash != result.get('delta_sha256'):
                raise ValueError(f'{unit_id}: source delta artifact hash mismatch')
            extra_readset[str(delta_path)] = delta_hash
            with np.load(delta_path, allow_pickle=False) as z:
                if 'variables_rc' not in z.files or 'B_values_float32' not in z.files or 'final_float32' not in z.files:
                    raise ValueError(f'{unit_id}: legacy delta lacks required arrays')
                nodes = np.asarray(z['variables_rc']).copy()
                base_values = np.asarray(z['B_values_float32']).copy()
                final_values = np.asarray(z['final_float32']).copy()
                if 'queue_id' not in z.files or int(z['queue_id'][0]) != int(row.get('source_qid', -2)):
                    raise ValueError(f'{unit_id}: legacy delta qid mismatch')
        elif row.get('origin') == 'crest':
            origin_counts['crest'] += 1
            result_path = Path(body['source_result_path'])
            result_hash = sha(result_path)
            if result_hash != body.get('source_result_sha256'):
                raise ValueError(f'{unit_id}: source result hash mismatch')
            extra_readset[str(result_path)] = result_hash
            result = read_json(result_path)
            if result.get('state') != 'rejected' or result.get('reason') != 'final gate scalar interpolation rule unavailable: baseline focus is not prominent on both axes':
                raise ValueError(f'{unit_id}: crest source was not the exact policy-only rejection')
            if int(result.get('queue_id', -1)) != int(body.get('source_qid', -2)):
                raise ValueError(f'{unit_id}: crest source result qid mismatch')
            if int(body.get('source_qid', -1)) != int(row.get('source_qid', -2)):
                raise ValueError(f'{unit_id}: target/source qid mismatch')
            if body.get('state') != 'derived_quarantined' or int(body.get('solve_calls', -1)) != 0:
                raise ValueError(f'{unit_id}: crest target is not a derived no-solve artifact')
            if body.get('source_state') != result.get('state') or body.get('source_reason') != result.get('reason'):
                raise ValueError(f'{unit_id}: crest target/source terminal metadata mismatch')
            origin = 'crest'
            window = check_window(result, unit_id)
            target_nodes = body.get('variables_rc')
            base_values = body.get('B_values_float32')
            final_values = body.get('final_float32')
            direction = np.asarray(body.get('direction_float32'), dtype=np.float32)
            if not isinstance(target_nodes, list) or not target_nodes:
                raise ValueError(f'{unit_id}: crest target lacks variables_rc')
            nodes = np.asarray(target_nodes, dtype=np.int32)
            base_values = np.asarray(base_values, dtype=np.float32)
            final_values = np.asarray(final_values, dtype=np.float32)
            if direction.shape != base_values.shape or hashlib.sha256(np.asarray(direction, dtype='<f4').tobytes()).hexdigest() != body.get('direction_sha256'):
                raise ValueError(f'{unit_id}: crest direction digest/shape mismatch')
            solution_path = Path(body['source_solution_path'])
            solution_hash = sha(solution_path)
            marker_path = Path(body['source_marker_path'])
            marker_hash = sha(marker_path)
            if solution_hash != body.get('source_solution_sha256') or solution_hash != result.get('solution_sha256'):
                raise ValueError(f'{unit_id}: crest source solution hash mismatch')
            if marker_hash != body.get('source_marker_sha256') or marker_hash != result.get('attempt_marker_sha256'):
                raise ValueError(f'{unit_id}: crest source marker hash mismatch')
            if (str(solution_path) != result.get('solution_path')
                    or str(marker_path) != result.get('attempt_marker_path')):
                raise ValueError(f'{unit_id}: crest target/source artifact paths mismatch')
            with np.load(solution_path, allow_pickle=False) as z:
                required = {'queue_id', 'variables_rc', 'B_values_float32', 'direction_float32'}
                if not required.issubset(z.files):
                    raise ValueError(f'{unit_id}: crest source solution lacks required arrays')
                if int(z['queue_id'][0]) != int(row.get('source_qid', -2)):
                    raise ValueError(f'{unit_id}: crest source solution qid mismatch')
                source_nodes = np.asarray(z['variables_rc'])
                source_base = np.asarray(z['B_values_float32'])
                source_direction = np.asarray(z['direction_float32'])
                if (source_nodes.dtype != np.int32 or source_nodes.shape != nodes.shape
                        or not np.array_equal(source_nodes, nodes)
                        or source_base.dtype != np.float32 or not np.array_equal(source_base, base_values)
                        or source_direction.dtype != np.float32 or not np.array_equal(source_direction, direction)):
                    raise ValueError(f'{unit_id}: crest target arrays differ from pinned source solution')
            extra_readset[str(solution_path)] = solution_hash
            extra_readset[str(marker_path)] = marker_hash
        else:
            raise ValueError(f'{unit_id}: unknown selected unit origin')

        if nodes.ndim != 2 or nodes.shape[1] != 2 or nodes.dtype != np.int32:
            raise ValueError(f'{unit_id}: malformed changed-node coordinates')
        if base_values.shape != final_values.shape or base_values.shape != (len(nodes),):
            raise ValueError(f'{unit_id}: malformed base/final height arrays')
        if len(set(map(tuple, nodes.tolist()))) != len(nodes):
            raise ValueError(f'{unit_id}: duplicate changed-node coordinates')
        if nodes.size and (np.any(nodes[:, 0] < window[0]) or np.any(nodes[:, 0] >= window[1])
                           or np.any(nodes[:, 1] < window[2]) or np.any(nodes[:, 1] >= window[3])):
            raise ValueError(f'{unit_id}: source variable outside declared window')
        changed = final_values != base_values
        changed_rc = nodes[changed].astype(np.int64).tolist()
        changed_hash = hashlib.sha256(json.dumps(changed_rc, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
        if int(np.count_nonzero(changed)) != int(row.get('changed_vertices', -1)) or changed_hash != row.get('changed_vertices_sha256'):
            raise ValueError(f'{unit_id}: selected changed-node digest/count mismatch')
        if origin == 'crest':
            target_array = np.asarray(target_nodes, dtype=np.int32).reshape((-1, 2))
            if sorted(map(tuple, target_array.tolist())) != sorted(map(tuple, nodes.tolist())):
                raise ValueError(f'{unit_id}: crest target variables differ from embedded result variables')
        else:
            origin_counts['legacy'] += 1
        records.append({'unit_id': unit_id, 'origin': origin, 'window_rc': window,
                        'source_artifact_path': str(artifact), 'source_artifact_sha256': artifact_hash,
                        'source_result_path': str(result_path if origin == 'crest' else artifact),
                        'source_result_sha256': str(result_hash if origin == 'crest' else artifact_hash),
                        'delta_path':str(delta_path) if origin == 'legacy' else None,
                        'delta_sha256':delta_hash if origin == 'legacy' else None,
                        'embedded_changed_vertices_sha256':changed_hash,
                        'variable_count': int(len(nodes)),
                        'changed_vertices': int(np.count_nonzero(changed))})
    if origin_counts != {'legacy': 332, 'crest': 167}:
        raise ValueError(f'retained population drift: {origin_counts}')
    return records, extra_readset, origin_counts


def static_paths():
    return STATIC_PATHS


def initial_readset(self_path: Path):
    paths = static_paths()
    out = {}
    for label, p in paths.items():
        actual = sha(p)
        if actual != EXPECTED[label]:
            raise RuntimeError(f'{label} pin drift: {actual} != {EXPECTED[label]}')
        out[str(p)] = actual
    self_sha = sha(self_path)
    return out, self_sha


def load_ev87_module():
    return load_module('ev94_ev87', EV87)


def build_preflight(out_dir: Path):
    start = time.perf_counter()
    out_dir = out_dir.resolve()
    if out_dir.exists():
        raise FileExistsError(f'preflight output must be fresh: {out_dir}')
    self_path = Path(__file__).resolve()
    static_start, self_start = initial_readset(self_path)

    helper = load_module('ev94_preflight_helpers', PREVIOUS_DRIVER)
    terrain_f = load_npz(FOCAL)
    terrain_selected = load_npz(EV93_CANDIDATE)
    terrain_o = load_npz(EV79)
    cons = load_npz(CONS)
    prior = load_npz(PRIOR)
    p = np.load(P, allow_pickle=False)
    f = np.load(F, allow_pickle=False)
    inv = read_json(INVENTORY)
    civil = read_json(CIVIL_REPORT)
    civil_receipt = read_json(CIVIL_RECEIPT)
    water_report = read_json(WATER_REPORT)
    water = load_npz(WATER_MASK)
    selection = read_json(SELECTED)
    selected_report = read_json(SELECTED_REPORT)
    focal_composition = read_json(FOCAL_COMPOSITION)
    focal_supplement = read_json(FOCAL_SUPPLEMENT)
    source_report = read_json(EV93_SOURCE_REPORT)
    corridors = read_json(CORRIDORS)

    # Focal-composition chain: accepted one-node composition over exactly the selected EV93 base.
    if focal_composition.get('status') != 'PASS_FOCAL_COMPOSITION_INCREMENTAL' or focal_composition.get('global_contract_status') != 'OPEN_INHERITED_MAP_DEFECTS':
        raise ValueError('focal composition status/limitations changed')
    if focal_composition.get('candidate_path') != str(FOCAL) or focal_composition.get('candidate_sha256') != EXPECTED['FOCAL']:
        raise ValueError('focal composition points to a different candidate')
    if focal_composition.get('base_candidate_path') != str(EV93_CANDIDATE) or focal_composition.get('base_candidate_sha256') != EXPECTED['EV93_CANDIDATE']:
        raise ValueError('focal composition is not based on the selected EV93 candidate')
    if focal_composition.get('selection_sha256') != EXPECTED['SELECTED'] or focal_composition.get('selected_report_sha256') != EXPECTED['SELECTED_REPORT']:
        raise ValueError('focal composition selection lineage mismatch')
    if focal_supplement.get('status') != 'PASS_FOCAL_DELTA_OFFLINE_COMPLETE_GATESET':
        raise ValueError('focal acceptance supplement status changed')
    if focal_supplement.get('candidate_sha256') != EXPECTED['FOCAL']:
        raise ValueError('focal supplement candidate mismatch')
    if focal_composition.get('supplement_sha256') != EXPECTED['FOCAL_SUPPLEMENT']:
        raise ValueError('focal composition does not bind supplement')
    if selection.get('status') != 'SELECTED' or selection.get('schema') != 'ev93.compound-selection.v1':
        raise ValueError('EV93 selection is not the pinned selected state')
    if selection.get('selector_source_path') != str(COMPOUND_SELECTOR) or selection.get('selector_sha256') != EXPECTED['COMPOUND_SELECTOR']:
        raise ValueError('selector source hash/path does not match the version recorded by selection.json')
    if selection.get('base_path') != str(EV82_B) or selection.get('base_sha256') != EXPECTED['EV82_B']:
        raise ValueError('selection was not based on EV82-B')
    if selection.get('candidate', {}).get('path') != str(EV93_CANDIDATE) or selection.get('candidate', {}).get('sha256') != EXPECTED['EV93_CANDIDATE']:
        raise ValueError('selection source candidate identity mismatch')
    if selected_report.get('status') != 'PASS_INCREMENTAL_NONREGRESSION':
        raise ValueError('selected global consumer report is not a passing selected report')
    if focal_composition.get('selected_report_sha256') != sha(SELECTED_REPORT):
        raise ValueError('selected global consumer report SHA changed')
    raw_gates = source_report.get('gates', {})
    if source_report.get('status') != 'FAIL_INCREMENTAL_NONREGRESSION' or sum(not bool(v) for v in raw_gates.values()) != 2:
        raise ValueError('raw EV93 report no longer matches the two inherited non-regression failures')

    if terrain_f['heights'].shape != (N, N) or terrain_f['heights'].dtype != np.float32:
        raise ValueError('focal height array shape/dtype mismatch')
    if terrain_selected['heights'].shape != (N, N) or terrain_selected['heights'].dtype != np.float32:
        raise ValueError('selected EV93 height shape/dtype mismatch')
    if not helper.exact_metadata_equal(terrain_f, terrain_selected):
        raise ValueError('focal metadata differs from selected EV93 metadata')
    changed = np.argwhere(terrain_f['heights'] != terrain_selected['heights'])
    if changed.tolist() != [[FOCUS[0], FOCUS[1]]]:
        raise ValueError(f'focal composition is not exactly one height: {changed[:10].tolist()}')
    if float(terrain_f['heights'][FOCUS]) != float(np.float32(3.278029680252075)):
        raise ValueError('focal target height changed')
    if not helper.exact_metadata_equal(terrain_f, terrain_o):
        raise ValueError('EV79/focal metadata mismatch outside heights')

    if inv.get('status') != 'PREPARED_ELIGIBILITY_INVENTORY_ONLY':
        raise ValueError('eligibility inventory status mismatch')
    if civil_receipt.get('status') != 'PASS_CIVIL_SUPPORT_INVENTORY_READ_ONLY' or civil_receipt.get('report_sha256') != EXPECTED['CIVIL_REPORT']:
        raise ValueError('civil inventory receipt mismatch')
    if water_report.get('status') != 'WATERSUPPORT_MASK_ONLY' or water_report.get('mask_artifact', {}).get('sha256') != EXPECTED['WATER_MASK']:
        raise ValueError('water-support report/mask mismatch')
    if water_report.get('mask_artifact', {}).get('path') != str(WATER_MASK):
        raise ValueError('water-support mask path mismatch')
    if p.shape != (N-1, N-1) or f.shape != (N-1, N-1, 4):
        raise ValueError('P/F shape mismatch')
    if p.dtype != np.float64 or f.dtype != np.float64 or np.isinf(p).any() or np.isinf(f).any():
        raise ValueError('P/F type/inf contract mismatch')

    # Verify deployed PBO/OPRW and the existing indexed model/readback linkage.
    ev87 = load_ev87_module()
    pbo = ev87.pbo_guard(DEPLOY, WRP)
    required_pbo = ('expected_world_exact', 'expected_water_exact',
                    'deployed_oprw_matches_manifest', 'staged_source_wrp_identity_exact')
    if not all(bool(pbo.get(k)) for k in required_pbo):
        raise RuntimeError(f'PBO/OPRW guard failed: {pbo}')
    manifest = read_json(INDEX_MANIFEST)
    if manifest.get('status') != 'COMPLETE' or int(manifest.get('counts', {}).get('faces', -1)) != 883308:
        raise ValueError('EV93 index completion/count mismatch')
    if manifest.get('base_identity', {}).get('terrain_sha256') != EXPECTED['EV82_B']:
        raise ValueError('face index was built against another terrain')
    if manifest.get('base_identity', {}).get('compiled_oprw_sha256') != pbo.get('deployed_oprw_entry_sha256'):
        raise ValueError('indexed OPRW differs from deployed payload')
    index_verification = read_json(INDEX_VERIFICATION)
    if index_verification.get('status') != 'PASS_INDEX_AND_SAMPLED_EXPOSURE':
        raise ValueError('full index verification is not PASS')
    if index_verification.get('manifest_sha256') != EXPECTED['INDEX_MANIFEST']:
        raise ValueError('index verification points to another manifest')
    for label in ('INDEX_SOURCE', 'INDEX_MANIFEST', 'INDEX_VERIFICATION', 'SOURCE_PLAN', 'EV87', 'EV82_B', 'P', 'F'):
        if water_report.get('pins_start', {}).get(str(STATIC_PATHS[label])) != EXPECTED[label]:
            raise ValueError(f'water mask is not linked to pinned {label}')
    if water_report.get('pins_start') != water_report.get('pins_end'):
        raise ValueError('water mask producer readset was unstable')

    r0, r1, c0, c1 = WINDOW
    local_shape = (r1-r0, c1-c0)
    if set(water) != {'cell_reasons', 'face_counts', 'vertex_reasons', 'blocked_vertices'}:
        raise ValueError('water mask schema changed')
    if water['blocked_vertices'].shape != local_shape or water['cell_reasons'].shape != (257,257):
        raise ValueError('water mask dimensions mismatch')
    if set(np.load(DOMAIN_REASONS, allow_pickle=False).files) != {'ev87_eligible','reason_bits'}:
        raise ValueError('saved domain inventory schema mismatch')

    levels = helper.incident_vertex_levels(p, f, SEA)
    ev_levels = ev87.vertex_levels(p, f)
    if not np.array_equal(levels, ev_levels):
        raise AssertionError('independent P/F/SEA vertex levels differ from EV87')
    h = terrain_f['heights'].astype(np.float64)
    eligible_expected, _ = ev87._ev87_eligible(terrain_f, cons, prior, h, p, f)
    eligible_ind = ((terrain_f['cls'] == 0) & ~cons['other_fixed'].astype(bool)
                    & ~cons['engineering_halo'].astype(bool)
                    & ~prior['large_lake_banks'].astype(bool) & (h > levels))
    if not np.array_equal(eligible_expected, eligible_ind):
        raise AssertionError('EV87 eligibility implementation mismatch')
    eligible = eligible_ind[r0:r1, c0:c1]

    # Reconcile all 499 retained source windows and build exact window+2 collars.
    selected_records, unit_readset, origin_counts = resolve_selected_windows(selection)
    retained_mask = np.zeros(local_shape, dtype=bool)
    retained_core_mask = np.zeros(local_shape, dtype=bool)
    for rec in selected_records:
        add_rect_halo(retained_mask, rec['window_rc'], WINDOW)
        # Store only windows themselves separately for audit; no seed is selected from this mask.
        wr0, wr1, wc0, wc1 = rec['window_rc']
        a=max(r0,wr0); b=min(r1,wr1); c=max(c0,wc0); d=min(c1,wc1)
        if a < b and c < d:
            retained_core_mask[a-r0:b-r0,c-c0:d-c0] = True
    if len(selected_records) != 499 or origin_counts != {'legacy':332,'crest':167}:
        raise AssertionError('retained windows count/origin reconciliation failed')

    # Exact fixed masks: EV87 semantics, water footprint/support, civil, P9, retained windows, explicit focus.
    prior_domain = load_npz(DOMAIN_REASONS)
    water_block = water['blocked_vertices'].astype(bool)
    if water_block.shape != local_shape:
        raise ValueError('water blocked mask shape mismatch')
    civil_cells = set()
    for key in ('road','bridge'):
        items = civil.get(key, {}).get('native_cells_rc_sorted')
        if not isinstance(items, list):
            raise ValueError(f'civil {key} cells missing')
        civil_cells.update((int(x[0]),int(x[1])) for x in items)
    civil_block = helper.corners_for_cells(sorted(civil_cells), WINDOW)
    p_local = p[r0-1:r1, c0-1:c1]
    if p_local.shape != (257,257):
        raise AssertionError('P9 incident-cell context must be 257x257')
    p9_cells = helper.p9_unknown_cells(p_local,corridors,r0-1,c0-1)
    p9_block = helper.corners_for_cells(p9_cells,WINDOW)
    explicit_focus = np.zeros(local_shape,bool)
    explicit_focus[FOCUS[0]-r0,FOCUS[1]-c0]=True
    fixed_reason = {
        'not_ev87_eligible': ~eligible,
        'empty_or_invalid_physical_bounds': np.zeros(local_shape,bool),
        'water_support_or_contact': water_block,
        'civil_road_or_bridge': civil_block,
        'P9_unknown_corridor': p9_block,
        '499_retained_windows_plus_halo2': retained_mask,
        'explicit_focal_pin_840_370': explicit_focus,
    }

    # Sector-only independently rebuilt bounds. Intersect EV79 absolute ±2m and EV82 current+0.5 cap.
    o_local = terrain_o['heights'][r0:r1,c0:c1]
    b_local = terrain_f['heights'][r0:r1,c0:c1]
    level_local = levels[r0:r1,c0:c1]
    ev82 = load_module('ev94_ev82_author', EV82_AUTHOR)
    d8 = load_module('ev94_d8', D8)
    lo, hi, hi_budget, hi_cap, floors, limiting = cap_intersection_bounds(o_local,b_local,level_local,ev82,d8)
    bounds_valid = np.isfinite(lo) & np.isfinite(hi) & (lo <= hi)
    fixed_reason['empty_or_invalid_physical_bounds'] = ~bounds_valid
    fixed = np.zeros(local_shape,bool)
    reason_counts = {}
    for name, mask in fixed_reason.items():
        if mask.shape != local_shape:
            raise AssertionError(f'{name} mask shape mismatch')
        fixed |= mask
        reason_counts[name] = int(mask.sum())
    variables = eligible & bounds_valid & ~fixed
    fixed |= ~variables
    # Explicit focus remains fixed even if the source masks change in a later rerun.
    if variables[FOCUS[0]-r0,FOCUS[1]-c0] or not fixed[FOCUS[0]-r0,FOCUS[1]-c0]:
        raise AssertionError('explicit focal vertex is not fixed')

    selection_queue = read_json(QUEUE)
    if selection_queue.get('schema') != 'EV93-seed-queue-v1' or len(selection_queue.get('seeds',[])) != 5450:
        raise ValueError('EV93 queue identity/count drift')
    helper.WINDOW = WINDOW
    helper.FOCUS = FOCUS
    selected_seed = helper.choose_seed(selection_queue,variables)
    if selected_seed is None:
        seed_status = 'NO_SURVIVING_SEED'
    else:
        seed_status = 'PREFLIGHT_READY_ONLY'

    if selected_seed is None:
        out_dir.mkdir(parents=True,exist_ok=False)
        extra_end={path:sha(path) for path in unit_readset}
        static_end,self_end=initial_readset(self_path)
        pbo_end=ev87.pbo_guard(DEPLOY,WRP)
        if extra_end != unit_readset or static_end != static_start or self_end != self_start or pbo_end != pbo:
            raise RuntimeError('readset changed during terminal no-surviving-seed preflight')
        terminal={'schema':'ev94.rebased-sector-preflight.v1','status':'NO_SURVIVING_SEED',
                  'scope':'read-only; no solver, no matrices, no terrain candidate',
                  'plan_sha256':EXPECTED['PLAN'],'driver_path':str(self_path),
                  'driver_sha256_start_end':[self_start,self_end],
                  'source_hashes_start':static_start,'source_hashes_end':static_end,
                  'selected_unit_readset':unit_readset,'selected_unit_records':selected_records,
                  'selected_unit_origin_counts':origin_counts,'reason_counts_overlap':reason_counts,
                  'ev87_eligible':int(eligible.sum()),'final_variables':int(variables.sum()),
                  'explicit_focus_fixed':True,'selected_seed':None,
                  'deployed_pbo_guard_start_end':[pbo,pbo_end],
                  'solver_called':False,'prepared_matrices_written':False}
        (out_dir/'preflight.json').write_text(json.dumps(terminal,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        return terminal

    # Fresh 260x260 local context with focal composition and fixed two-node Dirichlet edge.
    local_base = terrain_f['heights'][LOCAL_R0:LOCAL_R1,LOCAL_C0:LOCAL_C1].copy()
    if local_base.shape != (260,260):
        raise AssertionError('local context is not 260x260')
    window_variables = np.argwhere(variables) + np.asarray([r0,c0],np.int32)
    nodes_local = window_variables - np.asarray([LOCAL_R0,LOCAL_C0],np.int32)
    if nodes_local.size and (np.any(nodes_local < 2) or np.any(nodes_local >= 258)):
        raise AssertionError('mutable coordinate escaped full two-node stencil halo')
    local_fixed = np.ones(local_base.shape,bool)
    local_fixed[2:258,2:258] = fixed
    if not local_fixed[FOCUS[0]-LOCAL_R0,FOCUS[1]-LOCAL_C0]:
        raise AssertionError('focus lost fixed pin in prepared context')

    # Rebuild EV88 objective and D8 rows against this new base/context only.
    proto = load_module('ev94_proto',PROTO)
    d8.H,d8.W = local_base.shape
    stencils = proto.all_stencils(local_base.shape,nodes_local)
    records = proto.row_records(local_base,nodes_local,stencils)
    A,rhs = proto.csr_from_records(records,len(nodes_local))
    C,d,witnesses,exempt,centers = d8.build_d8(local_base,nodes_local)
    nodes_sector = window_variables - np.asarray([r0,c0],np.int32)
    lo_vars = lo[tuple(nodes_sector.T)].astype(np.float64) if len(nodes_sector) else np.empty(0,np.float64)
    hi_vars = hi[tuple(nodes_sector.T)].astype(np.float64) if len(nodes_sector) else np.empty(0,np.float64)
    x0 = local_base[tuple(nodes_local.T)].astype(np.float64) if len(nodes_local) else np.empty(0,np.float64)
    if np.any(lo_vars > hi_vars) or not (np.isfinite(lo_vars).all() and np.isfinite(hi_vars).all()):
        raise AssertionError('variable bounds invalid')
    if len(d) and np.min(C@x0-d) < -1e-12:
        raise AssertionError('focal composition does not satisfy reconstructed D8 baseline')

    # Smoke the pinned float32 order closure on the feasible baseline (no solution proposal).
    proj = load_module('ev94_order_projection',PROJECTION)
    lower_full = local_base.copy(); upper_full = local_base.copy()
    if len(nodes_local):
        lower_full[tuple(nodes_local.T)] = lo_vars.astype(np.float32)
        upper_full[tuple(nodes_local.T)] = hi_vars.astype(np.float32)
    flat_nodes = {tuple(map(int,rc)):i for i,rc in enumerate(np.ndindex(local_base.shape))}
    edge_rows=[]
    for w in witnesses:
        wr,wc = map(int,w['witness']); cr,cc = map(int,w['center'])
        edge_rows.append((flat_nodes[(wr,wc)],flat_nodes[(cr,cc)]))
    projection = proj.project_order(local_base.ravel().copy(),lower_full.ravel().copy(),upper_full.ravel().copy(),
                                    np.asarray(edge_rows,np.int32).reshape((-1,2)),
                                    baseline=local_base.ravel().copy(),fixed=local_fixed.ravel().copy())
    if (not np.array_equal(projection['q'],local_base.ravel())
            or float(projection['clip_max_abs']) != 0.0
            or float(projection['raw_order_violation_sum_after_clip']) != 0.0
            or float(projection['max_abs_correction']) != 0.0):
        raise AssertionError('pinned closure is not an exact zero correction on feasible focal base')

    out_dir.mkdir(parents=True,exist_ok=False)
    prepared = out_dir/'prepared.npz'
    with prepared.open('xb') as stream:
        np.savez_compressed(stream,
            base_local=local_base.astype(np.float32), nodes_local=nodes_local.astype(np.int32),
            lo=lo_vars, hi=hi_vars, x0=x0, A_data=A.data, A_indices=A.indices,
            A_indptr=A.indptr, A_shape=np.asarray(A.shape,np.int64), rhs=rhs,
            C_data=C.data, C_indices=C.indices, C_indptr=C.indptr,
            C_shape=np.asarray(C.shape,np.int64), d=d,
            witnesses_json=helper.json_bytes(witnesses), exempt_json=helper.json_bytes(exempt),
            centers_json=helper.json_bytes(centers), stencils_json=helper.json_bytes(stencils),
            fixed_mask=local_fixed.astype(np.uint8),
            retained_window_mask=retained_mask.astype(np.uint8), retained_rect_mask=retained_core_mask.astype(np.uint8),
            water_block=water_block.astype(np.uint8), civil_block=civil_block.astype(np.uint8), p9_block=p9_block.astype(np.uint8),
            eligible=eligible.astype(np.uint8), ev79_local=o_local.astype(np.float32),
            level_local=level_local.astype(np.float64), floors_local=floors.astype(np.float64),
            bound_lo_local=lo.astype(np.float32), bound_hi_ev79_ev82_local=hi_budget.astype(np.float32),
            bound_hi_ev82_cap_local=hi_cap.astype(np.float32), bound_hi_final_local=hi.astype(np.float32),
            bounds_valid=bounds_valid.astype(np.uint8),
            focus_explicit_pin=explicit_focus.astype(np.uint8))
    prepared_sha = sha(prepared)
    static_end, self_end = initial_readset(self_path)
    # Rehash every selected row/result/delta used to establish the fixed-window union.
    extra_end = {path: sha(path) for path in unit_readset}
    if extra_end != unit_readset:
        raise RuntimeError('selected source result/artifact/delta drift after preflight')
    if static_end != static_start or self_end != self_start:
        raise RuntimeError('pinned source or preflight script changed during build')
    if sum(p.stat().st_size for p in out_dir.iterdir() if p.is_file()) > 2 * 1024**3:
        raise RuntimeError('preflight artifact output exceeds 2 GiB')
    pbo_end = ev87.pbo_guard(DEPLOY,WRP)
    if pbo_end != pbo:
        raise RuntimeError('PBO/OPRW identity drift during preflight')

    report = {
        'schema':'ev94.rebased-sector-preflight.v1', 'status':seed_status,
        'scope':'read-only rebase prepared on accepted focal composition; solver not called; no terrain candidate',
        'plan_path':str(PLAN),'plan_sha256':EXPECTED['PLAN'], 'driver_path':str(self_path),
        'driver_sha256_start_end':[self_start,self_end], 'source_hashes_start':static_start,
        'source_hashes_end':static_end, 'selected_unit_artifact_count':len(unit_readset),
        'selected_unit_readset_sha256':hashlib.sha256(json.dumps(unit_readset,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        'selected_units':{'count':len(selected_records),'origin_counts':origin_counts,
                          'window_vertices_fixed_by_rectangles':int(retained_core_mask.sum()),
                          'window_plus_chebyshev2_vertices_in_sector':int(retained_mask.sum()),
                          'unit_readset':unit_readset,'records':selected_records},
        'focus_pin':{'rc':list(FOCUS),'value_f32':float(terrain_f['heights'][FOCUS]),'explicitly_fixed':True,
                     'overlap_reasons':[name for name,mask in fixed_reason.items() if bool(mask[FOCUS[0]-r0,FOCUS[1]-c0])]},
        'base_identity':{'focal_path':str(FOCAL),'focal_sha256':EXPECTED['FOCAL'],
                         'EV93_path':str(EV93_CANDIDATE),'EV93_sha256':EXPECTED['EV93_CANDIDATE'],
                         'EV79_path':str(EV79),'EV79_sha256':EXPECTED['EV79'],
                         'focal_changes_vs_EV93':changed.tolist(),
                         'focal_height_vs_EV93_m':float(terrain_f['heights'][FOCUS])-float(terrain_selected['heights'][FOCUS]),
                         'focal_composition_report_sha256':EXPECTED['FOCAL_COMPOSITION'],
                         'focal_supplement_sha256':EXPECTED['FOCAL_SUPPLEMENT'],
                         'selected_composition_report_sha256':EXPECTED['SELECTED_REPORT'],
                         'selection_sha256':EXPECTED['SELECTED']},
        'window_rc_half_open':list(WINDOW),'local_context_rc_half_open':[LOCAL_R0,LOCAL_R1,LOCAL_C0,LOCAL_C1],
        'selection_policy':'focus 840,370 is fixed; choose explicit focus only if it survives mutable domain; otherwise minimum EV93 first_layer_id survivor, independent of solution quality',
        'eligibility':{'ev87_eligible':int(eligible.sum()),'bounds_valid':int(bounds_valid.sum()),
                       'final_variables':int(len(nodes_local)),'fixed_reason_counts_overlap':reason_counts,
                       'water_blocked_vertices':int(water_block.sum()),'civil_cells':len(civil_cells),
                       'civil_blocked_vertices':int(civil_block.sum()),'p9_unknown_cells':len(p9_cells),
                       'p9_blocked_vertices':int(p9_block.sum()),'fixed_union_vertices':int(fixed.sum()),
                       'mutable_focus':bool(variables[FOCUS[0]-r0,FOCUS[1]-c0])},
        'bounds':{'budget_reference':'EV79 original absolute budget ±2.0 m; original_budget_interval recomputed relative to focal B',
                  'physical_cap':'EV82 current-height cap: H <= B_focal + 0.5 m',
                  'floor':'min(EV79, max(SEA=.85, P, each incident F corner)+1e-4), plus min(EV79,1.8), as in EV82 original_budget_interval',
                  'inward_rounding':'lower/upper to float32 lattice using pinned D8 inward32_lower/upper',
                  'upper_limit_counts':limiting,'lo_min':float(lo.min()),'lo_max':float(lo.max()),
                  'hi_ev79_ev82_budget_min':float(hi_budget.min()),'hi_ev82_plus_0_5_min':float(hi_cap.min()),
                  'hi_final_min':float(hi.min()),'hi_final_max':float(hi.max()),
                  'absolute_EV79_delta_min':float((lo-o_local).min()),'absolute_EV79_delta_max':float((hi-o_local).max()),
                  'B_current_plus_0_5_cap_enforced':bool(np.all(hi <= (b_local+EV82_RISE_CAP)))},
        'water_civil_index':{'water_mask_status':water_report['status'],'water_mask_sha256':EXPECTED['WATER_MASK'],
                             'civil_report_sha256':EXPECTED['CIVIL_REPORT'],'civil_receipt_sha256':EXPECTED['CIVIL_RECEIPT'],
                             'index_manifest_sha256':EXPECTED['INDEX_MANIFEST'],'index_verification_sha256':EXPECTED['INDEX_VERIFICATION'],
                             'deployed_pbo_guard_start_end':[pbo,pbo_end],
                             'pbo_oprw_linkage':{'deployed_oprw_entry_sha256':pbo.get('deployed_oprw_entry_sha256'),
                                                 'world_pbo_sha256':pbo.get('deployed_world_sha256'),
                                                 'water_pbo_sha256':pbo.get('deployed_water_sha256'),
                                                 'staged_wrp_sha256':pbo.get('staged_wrp_sha256')}},
        'system':{'variables':len(nodes_local),'stencils':len(stencils),'A_shape':list(A.shape),'A_nnz':int(A.nnz),
                  'D8_shape':list(C.shape),'D8_nnz':int(C.nnz),'D8_witnesses':len(witnesses),
                  'D8_exempt_baseline_strict_minima':len(exempt),'base_satisfies_D8':True,
                  'base_projection_zero_correction':True,'objective':'EV88 Dxx^2 + Dzz^2 + 2*Dxz^2 with fidelity .25; local 260x260 focal context'},
        'prepared_artifact':{'path':str(prepared),'sha256':prepared_sha,'size_bytes':prepared.stat().st_size},
        'limits':{'output_budget_bytes':2*1024**3,'artifact_bytes_total':sum(p.stat().st_size for p in out_dir.iterdir() if p.is_file()),
                  'future_solver_only':{'calls':1,'continuation':False,'max_iterations':20000,'numeric_seconds':600,
                                        'max_peak_working_set_bytes':1610612736,'min_free_physical_bytes':3221225472}},
        'limitations':['Preflight does not run the solver or produce a terrain candidate.',
                       'Selection/focal reports do not imply global map or visual acceptance.',
                       'All 499 accepted windows and two-vertex collars remain fixed at the focal base.'],
        'elapsed_seconds':time.perf_counter()-start,
    }
    tmp=out_dir/'preflight.json.tmp'
    tmp.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    tmp.replace(out_dir/'preflight.json')
    return report


def fixtures():
    # The cap and the original total budget are independent upper constraints.
    assert cap_intersection_bounds(np.array([10.],np.float32),np.array([9.5],np.float32),np.array([.85]),
                                  SimpleBudget(),SimpleD8())[1][0] <= np.float32(10.0)
    # Window expansion is exact Chebyshev radius 2 and clips to the requested sector.
    m=np.zeros((10,10),bool); add_rect_halo(m,[0,17,0,17],(0,10,0,10))
    assert m.all()
    m=np.zeros((10,10),bool); add_rect_halo(m,[5,22,5,22],(0,10,0,10))
    assert int(m.sum()) == 49
    return {'ev82_plus_half_cap_intersection':'PASS','window_radius2_clip':'PASS','explicit_focus_pin':'PASS_BY_CONSTRUCTION'}


class SimpleBudget:
    @staticmethod
    def original_budget_interval(o,b,floor,max_delta):
        lo=max(-max_delta,floor-b,min(o,1.8)-b,o-max_delta-b)
        hi=min(max_delta,o+max_delta-b)
        return lo,hi


class SimpleD8:
    @staticmethod
    def inward32_lower(x):
        y=np.float32(x)
        return np.nextafter(y,np.float32(np.inf),dtype=np.float32) if float(y)<x else y
    @staticmethod
    def inward32_upper(x):
        y=np.float32(x)
        return np.nextafter(y,np.float32(-np.inf),dtype=np.float32) if float(y)>x else y


def main():
    ap=argparse.ArgumentParser()
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--self-test',action='store_true')
    group.add_argument('--selected-rows-smoke',action='store_true')
    group.add_argument('--out',type=Path)
    args=ap.parse_args()
    if args.self_test:
        print(json.dumps({'status':'PASS_EV94_PREFLIGHT_FIXTURES','fixtures':fixtures()},sort_keys=True))
        return 0
    if args.selected_rows_smoke:
        selected = read_json(SELECTED)
        rows, readset, counts = resolve_selected_windows(selected)
        print(json.dumps({'status':'PASS_EV94_SELECTED_ROW_SMOKE','counts':counts,
                          'retained_rows':len(rows),'readset_entries':len(readset),
                          'legacy_examples':[r['unit_id'] for r in rows if r['origin']=='legacy'][:1],
                          'crest_examples':[r['unit_id'] for r in rows if r['origin']=='crest'][:1],
                          'candidate_nodes_total':sum(r['variable_count'] for r in rows),
                          'effective_changed_vertices':sum(r['changed_vertices'] for r in rows)},sort_keys=True))
        return 0
    report=build_preflight(args.out or OUT_DEFAULT)
    print(json.dumps({'status':report['status'],'variables':report.get('system',{}).get('variables',0),
                      'prepared_sha256':report.get('prepared_artifact',{}).get('sha256'),
                      'preflight_path':str((args.out or OUT_DEFAULT)/'preflight.json')},sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
