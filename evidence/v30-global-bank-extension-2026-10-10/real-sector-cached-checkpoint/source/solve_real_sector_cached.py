#!/usr/bin/env python
"""One bounded real-sector ADMM solve driver; PREPARE is read-only and separate.

The driver does not publish a terrain/map candidate. A converged local solution
is explicitly pending the independent global consumer and civil/water gates.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import math
import os
import sys
import time as _time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(r'E:/DayZ-Baltic-Build')
G = ROOT / 'v30-global-bank-extension-20261010'
HERE = G / 'global-operator-prototype/real-sector-preflight'
PLAN = G / 'global-operator-prototype/PLAN_REAL_SECTOR.md'
AMENDMENT = HERE / 'AMENDMENT_CACHED_TELEMETRY.md'
QUEUE = G / 'queue/queue.json'
EV87 = ROOT / 'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
EV79_DIR = ROOT / 'v30-narva-dry-bank-relief-20261010'
B_DIR = ROOT / 'v30-mixed-bank-incremental-fixed-20261010'
B = B_DIR / 'candidate/terrain.npz'
O = EV79_DIR / 'candidate/terrain.npz'
CONS = EV79_DIR / 'constraints.npz'
PRIOR = ROOT / 'v30-remaining-exact-dry-support-20261009/constraints.npz'
P = EV79_DIR / 'candidate/plane.npy'
F = EV79_DIR / 'candidate/visible-field.npy'
EV82_AUTHOR = B_DIR / 'author.py'
PROTO = G / 'global-operator-prototype/prototype.py'
D8 = G / 'constrained-pilot/d8_sparse_pilot.py'
SOLVER = G / 'global-operator-prototype/admm-quantized-pilot/solve.py'
CLOSURE = G / 'global-operator-prototype/float32-closure-study/float32_closure.py'
PREP_INVENTORY = HERE / 'prepare_inventory.py'
INVENTORY_DIR = HERE / 'inventory-run-02.json'
INVENTORY = INVENTORY_DIR / 'inventory.json'
DOMAIN_REASONS = INVENTORY_DIR / 'domain-reasons.npz'
CIVIL_SCRIPT = HERE / 'civil_inventory.py'
CIVIL_REPORT = HERE / 'civil-run-01.json'
CIVIL_RECEIPT = HERE / 'civil-run-01-receipt.json'
WATER_SCRIPT = HERE / 'prepare_water_footprint.py'
WATER_DIR = HERE / 'water-run-01'
WATER_REPORT = WATER_DIR / 'water-support-mask.json'
WATER_MASK = WATER_DIR / 'water-support-mask.npz'
INDEX_SOURCE = G / 'ev93-face-index/build_face_index.py'
INDEX_RUN = G / 'ev93-face-index/runs/20261010T092417Z-63d4cec3'
INDEX_MANIFEST = INDEX_RUN / 'manifest.json'
INDEX_VERIFICATION = G / 'review-independent/runs/attempt-01/verification.json'
CORRIDORS = Path(r'E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson')
DEPLOY = B_DIR / 'deploy.json'
WRP = B_DIR / 'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'

N = 2048
SEA = 0.85
EPS_WATER = 1e-4
MAX_DELTA = 2.0
WINDOW = (712, 968, 242, 498)  # half-open vertex bounds, 256x256
FOCUS = (840, 370)
NATIVE_TRIANGLES = ((0, 1, 3), (0, 2, 3))  # NW,NE,SW,SE; diagonal NW-SE

PINS = {
    'AMENDMENT': 'd64ad4441348bb2054800851cf7ef19f5f143143d62b93e0659de804b2565f7a',
    'PLAN': '14f02179312bc25caf76a087cc873122caed30f6092464f1c01ac7572d519749',
    'QUEUE': 'cf13887c8de031d65d0a32dab217e8743293103fcd00ea3c07c281c07a6794c9',
    'EV87': '964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
    'B': 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
    'O': 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c',
    'CONS': 'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c',
    'PRIOR': '18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370',
    'P': '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
    'F': 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
    'EV82_AUTHOR': '9b7c5374b7c78c3604bb2763ef8b7b4d16dc4bf18fc57091233ad435876cb74b',
    'PROTO': '5b4b8f08e5205e1f9cc90bcc8e82e61dade45bb82bd22da8ee69303aa4475cc4',
    'D8': '6b5281d9750c30fc5b27171aaec2af59dee88411a66bf5b08e5105866f08252c',
    'SOLVER': '7e8636bf54ba23f7e23bc2f06464100439468da7b4edca85f96c72d0cd40e149',
    'CLOSURE': 'c0c0cc1998a7cd9974ef884706c57a30ab39217057f675fc805b84c1e1a49d16',
    'PREP_INVENTORY': '239e0632046c84d00f7bcb677a16f7bd5245b10a174c0fe3e99a63d4ff90f6e7',
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


def sha(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot import pinned source: {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate_pin_contract(pin_table: dict, source_paths: dict) -> None:
    if set(pin_table) != set(source_paths):
        missing = sorted(set(source_paths) - set(pin_table))
        extra = sorted(set(pin_table) - set(source_paths))
        raise RuntimeError(f'incomplete pin table: missing={missing}, extra={extra}')
    malformed = [label for label, expected in pin_table.items()
                 if not isinstance(expected, str) or len(expected) != 64
                 or any(ch not in '0123456789abcdef' for ch in expected.lower())]
    if malformed:
        raise RuntimeError(f'missing or malformed expected SHA256: {sorted(malformed)}')


def verify_pins() -> dict[str, str]:
    validate_pin_contract(PINS, SOURCE_PATHS)
    result = {}
    bad = []
    for label, path in SOURCE_PATHS.items():
        actual = sha(path)
        result[str(path)] = actual
        expected = PINS.get(label)
        if not isinstance(expected, str) or len(expected) != 64:
            bad.append(f'{label}: missing or malformed expected SHA256')
        elif actual != expected:
            bad.append(f'{label}: {actual} != {expected}')
    if bad:
        raise RuntimeError('pinned source drift: ' + '; '.join(bad))
    return result


SOURCE_PATHS = {
    'AMENDMENT': AMENDMENT,
    'PLAN': PLAN, 'QUEUE': QUEUE, 'EV87': EV87, 'B': B, 'O': O,
    'CONS': CONS, 'PRIOR': PRIOR, 'P': P, 'F': F, 'EV82_AUTHOR': EV82_AUTHOR,
    'PROTO': PROTO, 'D8': D8, 'SOLVER': SOLVER, 'CLOSURE': CLOSURE,
    'PREP_INVENTORY': PREP_INVENTORY, 'INVENTORY': INVENTORY,
    'DOMAIN_REASONS': DOMAIN_REASONS, 'CIVIL_SCRIPT': CIVIL_SCRIPT,
    'CIVIL_REPORT': CIVIL_REPORT, 'CIVIL_RECEIPT': CIVIL_RECEIPT,
    'WATER_SCRIPT': WATER_SCRIPT, 'WATER_REPORT': WATER_REPORT,
    'WATER_MASK': WATER_MASK, 'INDEX_SOURCE': INDEX_SOURCE,
    'INDEX_MANIFEST': INDEX_MANIFEST, 'INDEX_VERIFICATION': INDEX_VERIFICATION,
    'CORRIDORS': CORRIDORS, 'DEPLOY': DEPLOY, 'WRP': WRP,
}


def exact_metadata_equal(a: dict[str, np.ndarray], b: dict[str, np.ndarray]) -> bool:
    if set(a) != set(b):
        return False
    for key in a:
        if key == 'heights':
            continue
        x, y = np.asarray(a[key]), np.asarray(b[key])
        if x.shape != y.shape or x.dtype != y.dtype:
            return False
        if np.ascontiguousarray(x).tobytes() != np.ascontiguousarray(y).tobytes():
            return False
    return True


def incident_vertex_levels(p: np.ndarray, f: np.ndarray, sea: float = SEA) -> np.ndarray:
    """Independent per-vertex max of incident P/F corner levels and SEA."""
    p, f = np.asarray(p, np.float64), np.asarray(f, np.float64)
    if p.ndim != 2 or f.shape != p.shape + (4,):
        raise ValueError('P/F shapes must be cells and cells+(NW,NE,SW,SE)')
    if np.isinf(p).any() or np.isinf(f).any():
        raise ValueError('P/F infinity is invalid; only NaN encodes unknown')
    out = np.full((p.shape[0] + 1, p.shape[1] + 1), sea, np.float64)
    offsets = ((0, 0), (0, 1), (1, 0), (1, 1))
    for corner, (dr, dc) in enumerate(offsets):
        pp = np.where(np.isnan(p), sea, p)
        ff = np.where(np.isnan(f[:, :, corner]), sea, f[:, :, corner])
        level = np.maximum(sea, np.maximum(pp, ff))
        np.maximum(out[dr:dr + p.shape[0], dc:dc + p.shape[1]], level,
                   out=out[dr:dr + p.shape[0], dc:dc + p.shape[1]])
    return out


def inward_absolute_bounds(original: np.ndarray, current: np.ndarray,
                           level: np.ndarray, budget_module, d8_module):
    """EV82 total-budget intervals, with the plan's independent P/F/SEA level."""
    if original.shape != current.shape or current.shape != level.shape:
        raise ValueError('original/current/incident-level shapes differ')
    if not (np.isfinite(original).all() and np.isfinite(current).all()
            and np.isfinite(level).all()):
        raise ValueError('non-finite values in real-sector budget inputs')
    low = np.empty(current.shape, np.float64)
    high = np.empty(current.shape, np.float64)
    floors = np.minimum(original.astype(np.float64), level + EPS_WATER)
    for idx in np.ndindex(current.shape):
        lo_step, hi_step = budget_module.original_budget_interval(
            float(original[idx]), float(current[idx]), float(floors[idx]), MAX_DELTA)
        low[idx] = d8_module.inward32_lower(float(current[idx]) + lo_step)
        high[idx] = d8_module.inward32_upper(float(current[idx]) + hi_step)
    return low, high, floors


def p9_unknown_cells(p_local: np.ndarray, p9_corridor_geojson: dict,
                     cell_r0: int, cell_c0: int, cell_m: float = 6.0,
                     z0: float = 12282.0):
    """Return unknown-P cells with positive-area intersection with signed corridor geometry."""
    from shapely.geometry import box, shape
    from shapely.ops import unary_union
    geometries = [shape(feature['geometry']) for feature in p9_corridor_geojson['features']]
    corridor = unary_union(geometries)
    if p_local.ndim != 2:
        raise ValueError('local P corridor mask must be a 2-D cell array')
    unknown = np.argwhere(np.isnan(p_local))
    cells = []
    for lr, lc in unknown.tolist():
        r, c = cell_r0 + int(lr), cell_c0 + int(lc)
        cell = box(c * cell_m, z0 - (r + 1) * cell_m,
                   (c + 1) * cell_m, z0 - r * cell_m)
        piece = corridor.intersection(cell)
        if not piece.is_empty and piece.area > 0.0:
            cells.append((r, c))
    return cells


def corners_for_cells(cells, window=WINDOW):
    r0, r1, c0, c1 = window
    frozen = np.zeros((r1 - r0, c1 - c0), dtype=bool)
    for r, c in cells:
        for rr, cc in ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)):
            if r0 <= rr < r1 and c0 <= cc < c1:
                frozen[rr - r0, cc - c0] = True
    return frozen


def choose_seed(queue: dict, final_domain: np.ndarray, window=WINDOW):
    """Fixed policy: explicit focus first, else smallest in-window first_layer_id."""
    r0, r1, c0, c1 = window
    focus_id = next((int(x['seed_id']) for x in queue['seeds']
                     if (int(x['row']), int(x['col'])) == FOCUS), None)
    if focus_id is None:
        raise ValueError('explicit focus identity is absent from frozen queue')
    fr, fc = FOCUS
    if r0 <= fr < r1 and c0 <= fc < c1 and final_domain[fr-r0, fc-c0]:
        return {'kind': 'explicit_focus', 'seed_id': focus_id, 'row': fr, 'col': fc}
    survivors = [x for x in queue['seeds'] if x.get('state') == 'first_layer'
                 and r0 <= int(x['row']) < r1 and c0 <= int(x['col']) < c1
                 and final_domain[int(x['row'])-r0, int(x['col'])-c0]]
    if not survivors:
        return None
    selected = min(survivors, key=lambda x: int(x['first_layer_id']))
    return {'kind': 'queue_fallback', 'seed_id': int(selected['seed_id']),
            'first_layer_id': int(selected['first_layer_id']),
            'row': int(selected['row']), 'col': int(selected['col'])}


def json_bytes(value) -> np.ndarray:
    return np.frombuffer(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode('utf-8'), dtype=np.uint8)


def json_safe(value):
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_safe(v) for v in value]
    return value


def write_json_atomic(path: Path, report: dict):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(json_safe(report), sort_keys=True, indent=2,
                              allow_nan=False) + '\n', encoding='utf-8')
    tmp.replace(path)


def _load_archive(path: Path):
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def _save_prepared(path: Path, base_local, nodes, lo, hi, x0, A, rhs, C, d,
                   witnesses, exempt, centers, stencils):
    with path.open('xb') as stream:
        np.savez_compressed(
            stream, base_local=np.asarray(base_local, np.float32),
            nodes_local=np.asarray(nodes, np.int32), lo=np.asarray(lo, np.float64),
            hi=np.asarray(hi, np.float64), x0=np.asarray(x0, np.float64),
            A_data=A.data, A_indices=A.indices, A_indptr=A.indptr,
            A_shape=np.asarray(A.shape, np.int64), rhs=np.asarray(rhs, np.float64),
            C_data=C.data, C_indices=C.indices, C_indptr=C.indptr,
            C_shape=np.asarray(C.shape, np.int64), d=np.asarray(d, np.float64),
            witnesses_json=json_bytes(witnesses), exempt_json=json_bytes(exempt),
            centers_json=json_bytes(centers), stencils_json=json_bytes(stencils))


def build_preflight(out_dir: Path) -> dict:
    """Build deterministic prepared matrices and receipts; does not call a solver."""
    from scipy import sparse
    from shapely.geometry import shape  # ensure GIS runtime has the pinned geometry API
    del shape
    out_dir = Path(out_dir).resolve()
    if out_dir.exists():
        raise FileExistsError(f'preflight output must be fresh: {out_dir}')
    source_before = verify_pins()
    self_path = Path(__file__).resolve()
    self_before = sha(self_path)

    terrain_b = _load_archive(B)
    terrain_o = _load_archive(O)
    cons = _load_archive(CONS)
    prior = _load_archive(PRIOR)
    p = np.load(P, allow_pickle=False)
    f = np.load(F, allow_pickle=False)
    inv = json.loads(INVENTORY.read_text(encoding='utf-8'))
    civil = json.loads(CIVIL_REPORT.read_text(encoding='utf-8'))
    civil_receipt = json.loads(CIVIL_RECEIPT.read_text(encoding='utf-8'))
    water_report = json.loads(WATER_REPORT.read_text(encoding='utf-8'))
    with np.load(DOMAIN_REASONS, allow_pickle=False) as z:
        prior_domain = {k: z[k] for k in z.files}
    with np.load(WATER_MASK, allow_pickle=False) as z:
        water = {k: z[k] for k in z.files}
    queue = json.loads(QUEUE.read_text(encoding='utf-8'))
    corridors = json.loads(CORRIDORS.read_text(encoding='utf-8'))

    if inv.get('status') != 'PREPARED_ELIGIBILITY_INVENTORY_ONLY':
        raise ValueError('inventory status is not the pinned read-only stage')
    if civil_receipt.get('status') != 'PASS_CIVIL_SUPPORT_INVENTORY_READ_ONLY':
        raise ValueError('civil inventory receipt is not PASS')
    if civil_receipt.get('report_sha256') != PINS['CIVIL_REPORT']:
        raise ValueError('civil report receipt hash differs from pinned report')
    if water_report.get('status') != 'WATERSUPPORT_MASK_ONLY':
        raise ValueError('water-support artifact is not the expected mask-only output')
    if water_report.get('mask_artifact', {}).get('sha256') != PINS['WATER_MASK']:
        raise ValueError('water mask report/artifact linkage mismatch')
    if water_report.get('mask_artifact', {}).get('path') != str(WATER_MASK):
        raise ValueError('water mask path is not the pinned run-01 artifact')
    if terrain_b['heights'].shape != (N, N) or terrain_b['heights'].dtype != np.float32:
        raise ValueError('B heights shape/dtype mismatch')
    if terrain_o['heights'].shape != (N, N) or terrain_o['heights'].dtype != np.float32:
        raise ValueError('EV79 heights shape/dtype mismatch')
    if not exact_metadata_equal(terrain_b, terrain_o):
        raise ValueError('EV79/B metadata changed outside the height layer')
    if p.shape != (N-1, N-1) or f.shape != (N-1, N-1, 4):
        raise ValueError('P/F shape mismatch')
    if p.dtype != np.float64 or f.dtype != np.float64 or np.isinf(p).any() or np.isinf(f).any():
        raise ValueError('P/F dtype/infinity contract mismatch')
    r0, r1, c0, c1 = WINDOW
    local_shape = (r1-r0, c1-c0)
    if set(prior_domain) != {'ev87_eligible', 'reason_bits'}:
        raise ValueError('inventory NPZ schema drift')
    if prior_domain['ev87_eligible'].shape != local_shape or prior_domain['reason_bits'].shape != local_shape:
        raise ValueError('inventory local mask dimensions drift')
    if set(water) != {'cell_reasons', 'face_counts', 'vertex_reasons', 'blocked_vertices'}:
        raise ValueError('water mask NPZ schema drift')
    if water['blocked_vertices'].shape != local_shape or water['vertex_reasons'].shape != local_shape:
        raise ValueError('water mask vertex dimensions drift')
    if water['cell_reasons'].shape != (257, 257) or water['face_counts'].shape != (257, 257, 2):
        raise ValueError('water mask incident cell dimensions drift')
    if queue.get('schema') != 'EV93-seed-queue-v1' or len(queue.get('seeds', [])) != 5450:
        raise ValueError('frozen EV87 queue schema/count drift')
    if int(queue.get('counts', {}).get('first_layer', -1)) != 703:
        raise ValueError('frozen first-layer count drift')

    # Link source deploy/WRP/PBO bytes to the same OPRW indexed by EV93.
    ev = load_module('real_sector_ev87', EV87)
    pbo = ev.pbo_guard(DEPLOY, WRP)
    if not all(pbo.get(k) for k in ('expected_world_exact', 'expected_water_exact',
                                    'deployed_oprw_matches_manifest', 'staged_source_wrp_identity_exact')):
        raise RuntimeError('deployed WRP/PBO guard failed')
    manifest = json.loads(INDEX_MANIFEST.read_text(encoding='utf-8'))
    if manifest.get('base_identity', {}).get('terrain_sha256') != PINS['B']:
        raise ValueError('EV93 index base terrain does not match B')
    if manifest.get('base_identity', {}).get('compiled_oprw_sha256') != pbo.get('deployed_oprw_entry_sha256'):
        raise ValueError('EV93 index OPRW differs from deployed PBO payload')
    if water_report.get('pins_start') != water_report.get('pins_end'):
        raise ValueError('water mask producer did not finish with stable pins')
    water_report_pins = water_report.get('pins_start', {})
    for label, path in (('INDEX_SOURCE', INDEX_SOURCE), ('INDEX_MANIFEST', INDEX_MANIFEST),
                        ('PLAN', PLAN), ('INDEX_VERIFICATION', INDEX_VERIFICATION),
                        ('EV87', EV87), ('B', B), ('P', P), ('F', F)):
        if water_report_pins.get(str(path)) != PINS[label]:
            raise ValueError(f'water-mask report is not linked to the expected {label} input')
    if water_report.get('index_load', {}).get('manifest_sha256') != PINS['INDEX_MANIFEST']:
        raise ValueError('water-mask report used a different EV93 face-index manifest')

    # Eligibility is reconstructed independently and compared to both EV87 and saved inventory.
    h_b = terrain_b['heights'].astype(np.float64)
    levels = incident_vertex_levels(p, f, SEA)
    ev_levels = ev.vertex_levels(p, f)
    if not np.array_equal(levels, ev_levels):
        raise AssertionError('independent P/F/SEA vertex levels differ from EV87')
    expected, _ = ev._ev87_eligible(terrain_b, cons, prior, h_b, p, f)
    eligible_ind = ((terrain_b['cls'] == 0) & ~cons['other_fixed'].astype(bool)
                    & ~cons['engineering_halo'].astype(bool)
                    & ~prior['large_lake_banks'].astype(bool) & (h_b > levels))
    if not np.array_equal(expected, eligible_ind):
        raise AssertionError('independent selector differs from pinned EV87')
    eligible = eligible_ind[r0:r1, c0:c1]
    if not np.array_equal(eligible.astype(np.uint8), prior_domain['ev87_eligible']):
        raise AssertionError('saved eligibility inventory differs from reconstructed domain')

    # Validate that cell-reason bits actually induce the saved four-corner water block.
    derived_water_block = np.zeros(local_shape, dtype=bool)
    cr0, cr1, cc0, cc1 = r0-1, r1-1, c0-1, c1-1
    for rr in range(cr0, cr1+1):
        for cc in range(cc0, cc1+1):
            if water['cell_reasons'][rr-cr0, cc-cc0] == 0:
                continue
            for vr, vc in ((rr, cc), (rr, cc+1), (rr+1, cc), (rr+1, cc+1)):
                if r0 <= vr < r1 and c0 <= vc < c1:
                    derived_water_block[vr-r0, vc-c0] = True
    if not np.array_equal(derived_water_block, water['blocked_vertices'].astype(bool)):
        raise AssertionError('water blocked-vertex mask is inconsistent with exact cell reasons')

    # Road/bridge projected cells are conservative support: freeze their four corners.
    civil_cells = set()
    for key in ('road', 'bridge'):
        cells = civil.get(key, {}).get('native_cells_rc_sorted')
        if not isinstance(cells, list):
            raise ValueError(f'civil {key} lacks its frozen native cell list')
        civil_cells.update((int(x[0]), int(x[1])) for x in cells)
    civil_block = corners_for_cells(sorted(civil_cells))
    # Include every native cell touching the vertex window: the extra row/column
    # on the south/east edge is required to freeze all four cell corners.
    p_local = p[r0-1:r1, c0-1:c1]
    if p_local.shape != (257, 257):
        raise AssertionError('P9 cell halo must include all 257x257 touching cells')
    p9_cells = p9_unknown_cells(p_local, corridors, r0-1, c0-1)
    p9_block = corners_for_cells(p9_cells)
    water_block = water['blocked_vertices'].astype(bool)

    # Only this fixed sector needs budget intervals; avoid a Python loop over all 4.2M vertices.
    original_local = terrain_o['heights'][r0:r1, c0:c1]
    current_local = terrain_b['heights'][r0:r1, c0:c1]
    level_local = levels[r0:r1, c0:c1]
    lo, hi, water_floor = inward_absolute_bounds(
        original_local, current_local, level_local,
        load_module('real_sector_ev82', EV82_AUTHOR), load_module('real_sector_d8', D8))
    bounds_ok = np.isfinite(lo) & np.isfinite(hi) & (lo <= hi)
    semantic_reason = ~eligible
    bound_reason = eligible & ~bounds_ok
    final_domain = eligible & bounds_ok & ~water_block & ~civil_block & ~p9_block

    selected_seed = choose_seed(queue, final_domain)
    blocked_reasons = {
        'not_ev87_eligible': int(np.count_nonzero(semantic_reason)),
        'inward_budget_interval_empty_or_nonfinite': int(np.count_nonzero(bound_reason)),
        'water_face_or_PF_contact_partial': int(np.count_nonzero(eligible & water_block)),
        'road_or_bridge_projected_cell': int(np.count_nonzero(eligible & civil_block)),
        'P9_unknown_corridor_cell': int(np.count_nonzero(eligible & p9_block)),
        'overlap_reasons_not_disjoint': True,
    }

    pbo_end = ev.pbo_guard(DEPLOY, WRP)
    if pbo_end != pbo:
        raise RuntimeError('deployed PBO/WRP identity changed during preflight')
    source_end = verify_pins()
    self_end = sha(self_path)
    if source_before != source_end or self_before != self_end:
        raise RuntimeError('source or self changed during real-sector preflight')
    if selected_seed is None:
        out_dir.mkdir(parents=True, exist_ok=False)
        report = {
            'status': 'NO_SURVIVING_SEED', 'scope': 'preflight only; no solver invoked',
            'plan_sha256': PINS['PLAN'], 'source_hashes': source_end,
            'driver_sha256': self_end, 'seed_candidates_remaining': 0,
            'domain_vertices': int(np.count_nonzero(final_domain)),
            'reason_counts_overlap': blocked_reasons, 'p9_unknown_cells': len(p9_cells),
            'civil_cells': len(civil_cells), 'selected_seed': None,
        }
        write_json_atomic(out_dir/'preflight.json', report)
        return report

    # Two-cell local context: all second-difference stencils and D8 halo are complete.
    # Window nodes are local [2:258,2:258]; outside values remain the exact B boundary.
    local_r0, local_r1, local_c0, local_c1 = r0-2, r1+2, c0-2, c1+2
    base_local = terrain_b['heights'][local_r0:local_r1, local_c0:local_c1].copy()
    if base_local.shape != (260, 260):
        raise AssertionError('local Dirichlet context is not 260x260')
    nodes_global = np.argwhere(final_domain) + np.asarray([r0, c0], dtype=np.int32)
    nodes_local = nodes_global - np.asarray([local_r0, local_c0], dtype=np.int32)
    if nodes_local.size and (np.any(nodes_local < 2) or np.any(nodes_local >= 258)):
        raise AssertionError('variable escaped the 2-vertex stencil halo')

    proto = load_module('real_sector_proto', PROTO)
    d8 = load_module('real_sector_d8_build', D8)
    # The pinned D8 builder was authored with synthetic H/W module constants.
    # Bind those globals to this exact local context before invoking its real API.
    d8.H, d8.W = base_local.shape
    stencils = proto.all_stencils(base_local.shape, nodes_local)
    records = proto.row_records(base_local, nodes_local, stencils)
    A, rhs = proto.csr_from_records(records, len(nodes_local))
    C, d, witnesses, exempt, centers = d8.build_d8(base_local, nodes_local)
    nodes_window = nodes_global - np.asarray([r0, c0], dtype=np.int32)
    lo_vars = lo[tuple(nodes_window.T)].astype(np.float64)
    hi_vars = hi[tuple(nodes_window.T)].astype(np.float64)
    x0 = base_local[tuple(nodes_local.T)].astype(np.float64)
    if np.any(lo_vars > hi_vars) or not (np.isfinite(lo_vars).all() and np.isfinite(hi_vars).all()):
        raise AssertionError('selected variable has invalid inward bounds')
    if len(d) and np.min(C @ x0 - d) < -1e-12:
        raise AssertionError('B does not satisfy its own derived D8 rows')
    if len(A.indices) == 0 and len(nodes_local):
        raise AssertionError('objective has variables but no matrix coefficients')

    out_dir.mkdir(parents=True, exist_ok=False)
    prepared_path = out_dir/'prepared.npz'
    _save_prepared(prepared_path, base_local, nodes_local, lo_vars, hi_vars,
                   x0, A, rhs, C, d, witnesses, exempt, centers, stencils)
    # The initial readset check above protects construction; this second check
    # closes the receipt only after prepared matrices have been serialized.
    pbo_final = ev.pbo_guard(DEPLOY, WRP)
    source_final = verify_pins()
    self_final = sha(self_path)
    if pbo_final != pbo or source_final != source_before or self_final != self_before:
        raise RuntimeError('source/PBO readset drifted during prepared-system construction')
    pbo_end, source_end, self_end = pbo_final, source_final, self_final
    report = {
        'status': 'PREFLIGHT_READY_ONLY', 'scope': 'offline real-sector prepared system; solver not called; no terrain candidate',
        'plan_sha256': PINS['PLAN'], 'source_hashes_start': source_before,
        'source_hashes_end': source_end, 'source_readset_stable': True,
        'driver_sha256_start_end': [self_before, self_end],
        'window_vertex_rc_half_open': list(WINDOW),
        'local_context_rc_half_open': [local_r0, local_r1, local_c0, local_c1],
        'selected_seed': selected_seed,
        'selection_policy': 'focus (840,370) first; if frozen/not feasible, minimum frozen first_layer_id surviving all preflight masks; no score search',
        'input_identity': {'B_sha256': PINS['B'], 'EV79_sha256': PINS['O'],
                           'P_sha256': PINS['P'], 'F_sha256': PINS['F'],
                           'OPRW_sha256': pbo['deployed_oprw_entry_sha256'],
                           'world_pbo_sha256': pbo['deployed_world_sha256'],
                           'water_pbo_sha256': pbo['deployed_water_sha256'],
                           'staged_wrp_sha256': pbo['staged_wrp_sha256']},
        'deployed_artifact_guard_start_end': [pbo, pbo_end],
        'eligibility': {'ev87_count': int(eligible.sum()), 'final_variables': int(len(nodes_local)),
                        'water_blocked_vertices': int(water_block.sum()),
                        'civil_cells_union': len(civil_cells), 'civil_blocked_vertices': int(civil_block.sum()),
                        'P9_unknown_cells': len(p9_cells), 'P9_blocked_vertices': int(p9_block.sum()),
                        'reason_counts_overlap': blocked_reasons},
        'budget_definition': {'api_path': str(EV82_AUTHOR), 'api_sha256': PINS['EV82_AUTHOR'],
                              'function': 'original_budget_interval(original=EV79,current=B,water_floor,max_delta=2.0)',
                              'water_floor': 'min(EV79, vertex_levels(P,F,SEA=.85)+1e-4); P and each F corner are independent; NaN maps to SEA, infinity is rejected',
                              'water_floor_api_note': 'does not use EV82 incident_water_floor because that helper suppresses finite F when P is NaN; this follows PLAN_REAL_SECTOR and EV87.vertex_levels',
                              'bounds_are_absolute_candidate_heights_inward_float32': True,
                              'variable_bounds_min_m': float(np.min(lo_vars)), 'variable_bounds_max_m': float(np.max(hi_vars))},
        'system': {'variables': int(len(nodes_local)), 'local_context_shape': list(base_local.shape),
                   'stencils': len(stencils), 'A_shape': list(A.shape), 'A_nnz': int(A.nnz),
                   'D8_rows': int(C.shape[0]), 'D8_nnz': int(C.nnz),
                   'D8_witnesses': len(witnesses), 'D8_exempt_baseline_strict_minima': len(exempt),
                   'fixed_nodes_exact_B': True,
                   'objective': 'EV88 Dxx^2 + Dzz^2 + 2*Dxz^2 with fidelity coefficient .25; all rows touching variables and full fixed B terms',
                   'stencil_source': str(PROTO), 'stencil_source_sha256': PINS['PROTO'],
                   'D8_source': str(D8), 'D8_source_sha256': PINS['D8']},
        'solver_contract': {'source': str(SOLVER), 'source_sha256': PINS['SOLVER'],
                            'closure_sha256': PINS['CLOSURE'], 'single_call_only': True,
                            'wall_seconds': 600, 'peak_working_set_bytes': 1610612736,
                            'min_available_physical_bytes': 3221225472,
                            'postsolve_status_never_accepts_map': 'SOLUTION_PENDING_INDEPENDENT_CONSUMER'},
        'prepared_artifact': {'path': str(prepared_path), 'sha256': sha(prepared_path)},
        'limitations': ['No real preflight was run by this code authoring step.',
                        'No solver was called; this receipt is only the static/prepared-system contract.',
                        'No geometry/render/DayZ acceptance is implied.'],
    }
    write_json_atomic(out_dir/'preflight.json', report)
    return report


class Counters(ctypes.Structure):
    _fields_ = [('cb', ctypes.c_ulong), ('PageFaultCount', ctypes.c_ulong)] + [(name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]


def _cached_process_memory():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    kernel.GetCurrentProcess.argtypes = []
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    psapi.GetProcessMemoryInfo.restype = ctypes.c_int
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return dict(pid=os.getpid(), peak_working_set_bytes=int(counters.PeakWorkingSetSize), working_set_bytes=int(counters.WorkingSetSize), peak_commit_bytes=int(counters.PeakPagefileUsage), method='GetProcessMemoryInfo in solver interpreter')


def _memory_snapshot(solver_module):
    return _cached_process_memory()


def available_physical_bytes() -> int:
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]
    status = MEMORYSTATUSEX()
    status.dwLength = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise ctypes.WinError(ctypes.get_last_error())
    return int(status.ullAvailPhys)


def run_one_solve(preflight_dir: Path, out_dir: Path) -> dict:
    """Explicit one-shot solve mode. Not called by PREPARE or self-tests."""
    preflight_dir, out_dir = Path(preflight_dir).resolve(), Path(out_dir).resolve()
    if out_dir.exists():
        raise FileExistsError(f'solve output must be fresh; retries are forbidden: {out_dir}')
    preflight_path = preflight_dir/'preflight.json'
    prepared_path = preflight_dir/'prepared.npz'
    report = json.loads(preflight_path.read_text(encoding='utf-8'))
    if report.get('status') != 'PREFLIGHT_READY_ONLY':
        raise RuntimeError(f'preflight is not solver-ready: {report.get("status")}')
    if sha(prepared_path) != report.get('prepared_artifact', {}).get('sha256'):
        raise RuntimeError('prepared artifact hash changed')
    if report.get('driver_sha256_start_end', [None, None])[0] != sha(Path(__file__).resolve()):
        raise RuntimeError('driver source changed after preflight')
    current = verify_pins()
    if current != report.get('source_hashes_end'):
        raise RuntimeError('preflight readset drifted before solver')
    ev = load_module('real_sector_ev87_pre_solve', EV87)

    prepared = _load_archive(prepared_path)
    from scipy import sparse
    base = prepared['base_local'].astype(np.float32, copy=False)
    nodes = prepared['nodes_local'].astype(np.int32, copy=False)
    lo, hi = prepared['lo'].astype(np.float64), prepared['hi'].astype(np.float64)
    x0 = prepared['x0'].astype(np.float64)
    A = sparse.csr_matrix((prepared['A_data'], prepared['A_indices'], prepared['A_indptr']),
                          shape=tuple(map(int, prepared['A_shape'])))
    C = sparse.csr_matrix((prepared['C_data'], prepared['C_indices'], prepared['C_indptr']),
                          shape=tuple(map(int, prepared['C_shape'])))
    rhs, d = prepared['rhs'].astype(np.float64), prepared['d'].astype(np.float64)
    witnesses = json.loads(prepared['witnesses_json'].tobytes().decode('utf-8'))

    solver = load_module('real_sector_quantized_solver', SOLVER)
    if sha(SOLVER) != PINS['SOLVER']:
        raise RuntimeError('solver source drift')
    # Measure after prepared matrices and solver module are resident, immediately
    # before creating the one-shot marker and dispatching the actual solve.
    pbo_before_solve = ev.pbo_guard(DEPLOY, WRP)
    if pbo_before_solve != report.get('deployed_artifact_guard_start_end', [None, None])[0]:
        raise RuntimeError('deployed PBO/WRP identity drifted before solver')
    available_before_solver = available_physical_bytes()
    available_sampled_unix = _time.time()
    if available_before_solver < 3221225472:
        raise MemoryError('less than 3 GiB available physical memory before the solver')

    out_dir.mkdir(parents=True, exist_ok=False)
    marker = out_dir/'solver.started'
    with marker.open('x', encoding='ascii') as stream:
        stream.write(json.dumps({'preflight_sha256': sha(preflight_path),
                                 'prepared_sha256': sha(prepared_path),
                                 'driver_sha256': sha(Path(__file__).resolve()),
                                 'started_unix': _time.time()}, sort_keys=True)+'\n')
    log_path = out_dir/'progress.jsonl'
    started_unix = _time.time()
    start = _time.perf_counter()
    max_ws = 0
    last_memory = {}

    class ResourceLimit(RuntimeError):
        pass

    def guarded_clock():
        nonlocal max_ws, last_memory
        now = _time.perf_counter()
        last_memory = _memory_snapshot(solver)
        max_ws = max(max_ws, int(last_memory['peak_working_set_bytes']))
        if now - start > 600.0:
            raise ResourceLimit('600-second wall limit exceeded')
        if int(last_memory['peak_working_set_bytes']) > 1610612736:
            raise ResourceLimit('1.5-GiB solver-interpreter peak working set exceeded')
        return now

    def progress(entry):
        with log_path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(json_safe(entry), sort_keys=True, allow_nan=False)+'\n')

    # The frozen solver calls its own clock in the outer and CG callback guards.
    # Replace only this module's clock reference to enforce memory at those checkpoints.
    original_clock_module = solver.time
    solver.time = SimpleNamespace(perf_counter=guarded_clock)
    result = {'status': 'SOLVER_ERROR', 'scope': 'one solve only; no terrain/map acceptance',
              'pbo_guard_before_solver': pbo_before_solve,
              'solver_pid': int(os.getpid()),
              'available_physical_bytes_before_solver': available_before_solver,
              'available_physical_sampled_unix': available_sampled_unix,
              'preflight_path': str(preflight_path), 'preflight_sha256': sha(preflight_path),
              'prepared_path': str(prepared_path), 'prepared_sha256': sha(prepared_path)}
    try:
        x64, diagnostics, history, state = solver.solve(A, rhs, C, d, lo, hi, x0,
                                                        budget=600.0, progress=progress)
        if diagnostics.get('status') != 'CONVERGED':
            result.update({'status': 'SOLVER_NOT_CONVERGED', 'diagnostics': diagnostics,
                           'history': history})
        else:
            raw = base.copy()
            raw[tuple(nodes.T)] = np.asarray(x64, dtype=np.float32)
            closed, closure_meta = solver.close_float32(solver.load_closure(), base, nodes,
                                                        raw, lo, hi, witnesses)
            checked, check_stats = solver.check_float32(base, nodes, closed[tuple(nodes.T)],
                                                        lo, hi, witnesses)
            base_cost = solver.objective(A, rhs, x0)
            raw_cost = solver.objective(A, rhs, raw[tuple(nodes.T)].astype(np.float64))
            closed_cost = solver.objective(A, rhs, closed[tuple(nodes.T)].astype(np.float64))
            closure_budget = 1e-7 * max(1.0, raw_cost)
            gates = {'float32_check_pass': bool(check_stats.get('pass')),
                     'closure_budget': bool(closed_cost - raw_cost <= closure_budget),
                     'strict_objective_improvement_vs_B': bool(closed_cost < base_cost),
                     'closure_meta_ok': bool(closure_meta.get('ok'))}
            if all(gates.values()):
                result.update({'status': 'SOLUTION_PENDING_INDEPENDENT_CONSUMER',
                               'diagnostics': diagnostics, 'history': history,
                               'closure': closure_meta, 'gates_local_numeric': gates,
                               'float32_check_stats': check_stats,
                               'objective': {'B_affected': base_cost, 'raw_float32': raw_cost,
                                             'closed_float32': closed_cost,
                                             'closure_delta': closed_cost-raw_cost,
                                             'allowed_closure_increase': closure_budget},
                               'changed_local_variables': int(np.count_nonzero(checked[tuple(nodes.T)] != x0)),
                               'candidate_local': checked})
            else:
                result.update({'status': 'REJECTED_LOCAL_NUMERIC_GATES',
                               'diagnostics': diagnostics, 'closure': closure_meta,
                               'gates_local_numeric': gates,
                               'float32_check_stats': check_stats})
        # Preserve continuous and split variables for independent diagnosis, regardless of gate result.
        with (out_dir/'solver-state.npz').open('xb') as stream:
            np.savez_compressed(stream, x64=x64, y_box=state['y_box'], y_d8=state['y_d8'],
                                z_box=state['z_box'], z_d8=state['z_d8'],
                                raw_float32=raw if 'raw' in locals() else np.asarray(x64, np.float32),
                                nodes_local=nodes, lo=lo, hi=hi)
        if 'candidate_local' in result:
            with (out_dir/'candidate-local.npz').open('xb') as stream:
                np.savez_compressed(stream, heights=result.pop('candidate_local'),
                                    nodes_local=nodes, source_B_local=base)
    except Exception as exc:
        result.update({'status': 'RESOURCE_LIMIT' if isinstance(exc, ResourceLimit) else 'SOLVER_EXCEPTION',
                       'error_type': type(exc).__name__, 'error': str(exc)})
    finally:
        solver.time = original_clock_module

    final_memory = _memory_snapshot(solver)
    try:
        pbo_after_solve = ev.pbo_guard(DEPLOY, WRP)
    except Exception as exc:
        pbo_after_solve = {'guard_error': type(exc).__name__, 'message': str(exc)}
    max_ws = max(max_ws, int(final_memory['peak_working_set_bytes']))
    result['resource_measurement'] = {'source': 'GetProcessMemoryInfo inside this GIS Python solver interpreter',
                                      'solver_pid': int(os.getpid()),
                                      'measurement_started_unix': float(started_unix),
                                      'available_physical_bytes_sampled_unix': float(available_sampled_unix),
                                      'peak_working_set_bytes': max_ws,
                                      'working_set_bytes_end': final_memory['working_set_bytes'],
                                      'available_physical_bytes_before_solver': available_before_solver,
                                      'elapsed_seconds': _time.perf_counter()-start,
                                      'limit_violated': max_ws > 1610612736 or _time.perf_counter()-start > 600.0}
    if result['resource_measurement']['limit_violated'] and result['status'] == 'SOLUTION_PENDING_INDEPENDENT_CONSUMER':
        result['status'] = 'RESOURCE_LIMIT'
    result['source_hashes_after'] = verify_pins()
    result['driver_sha256_after'] = sha(Path(__file__).resolve())
    if result['source_hashes_after'] != report.get('source_hashes_end') or result['driver_sha256_after'] != report.get('driver_sha256_start_end', [None,None])[0]:
        result['status'] = 'SOURCE_DRIFT_AFTER_SOLVE'
    result['pbo_guard_after_solver'] = pbo_after_solve
    if pbo_after_solve != pbo_before_solve and result['status'] == 'SOLUTION_PENDING_INDEPENDENT_CONSUMER':
        result['status'] = 'DEPLOYED_ARTIFACT_DRIFT_AFTER_SOLVE'
    state_path = out_dir/'solver-state.npz'
    candidate_path = out_dir/'candidate-local.npz'
    result['solver_state_path'] = str(state_path) if state_path.is_file() else None
    result['solver_state_sha256'] = sha(state_path) if state_path.is_file() else None
    result['candidate_path'] = str(candidate_path) if candidate_path.is_file() else None
    result['candidate_sha256'] = sha(candidate_path) if candidate_path.is_file() else None
    # Never write an accepted/PASS map status here. The candidate is local and consumer-pending only.
    write_json_atomic(out_dir/'solve-result.json', result)
    return result


def fixtures() -> dict:
    assert exact_metadata_equal({'heights': np.asarray([0.0], np.float32),
                                 'meta': np.asarray([np.nan, 3.0], np.float64)},
                                {'heights': np.asarray([1.0], np.float32),
                                 'meta': np.asarray([np.nan, 3.0], np.float64)})
    assert not exact_metadata_equal({'heights': np.asarray([0.0], np.float32),
                                     'meta': np.asarray([1], np.int32)},
                                    {'heights': np.asarray([1.0], np.float32),
                                     'meta': np.asarray([2], np.int32)})
    # Independent P/F corner semantics: finite F still contributes when cell P is unknown.
    p = np.asarray([[np.nan]], np.float64)
    f = np.asarray([[[0.85, 1.25, np.nan, 0.85]]], np.float64)
    levels = incident_vertex_levels(p, f)
    assert levels.shape == (2, 2) and levels[0, 1] == 1.25
    assert levels[0, 0] == SEA and levels[1, 0] == SEA
    try:
        incident_vertex_levels(np.asarray([[np.inf]]), np.zeros((1, 1, 4)))
    except ValueError:
        inf_rejected = True
    else:
        inf_rejected = False
    assert inf_rejected
    try:
        validate_pin_contract({'input': '0' * 64},
                              {'input': Path('unused'), 'required': Path('unused')})
    except RuntimeError:
        missing_pin_rejected = True
    else:
        missing_pin_rejected = False
    assert missing_pin_rejected

    # Seed selection is deterministic and stops cleanly when none survive.
    fake_q = {'seeds': [{'seed_id': 1981, 'row': 840, 'col': 370, 'state': 'pending_overlap'},
                        {'seed_id': 100, 'row': 720, 'col': 250, 'state': 'first_layer', 'first_layer_id': 4},
                        {'seed_id': 101, 'row': 721, 'col': 250, 'state': 'first_layer', 'first_layer_id': 2}]}
    dom = np.zeros((256, 256), bool)
    dom[720-712,250-242] = True; dom[721-712,250-242] = True
    assert choose_seed(fake_q, dom)['first_layer_id'] == 2
    assert choose_seed(fake_q, np.zeros_like(dom)) is None

    # EV82 exact interval semantics are pinned in production; this local fixture checks composition.
    b_mod = load_module('real_sector_test_budget', EV82_AUTHOR)
    d8_mod = load_module('real_sector_test_d8', D8)
    lo, hi = b_mod.original_budget_interval(3.0, 3.0, min(3.0, 2.5+EPS_WATER), 2.0)
    assert abs(lo - (2.5001-3.0)) < 1e-12 and hi == 2.0
    assert float(d8_mod.inward32_lower(1.2501)) >= 1.2501
    assert float(d8_mod.inward32_upper(5.0)) <= 5.0

    # P9 includes the full cell halo at the southeast vertex boundary.
    from shapely.geometry import mapping, box
    p9_cell = (967, 497)
    p9_geom = box(p9_cell[1]*6 + 1, 12282-(p9_cell[0]+1)*6 + 1,
                  p9_cell[1]*6 + 5, 12282-p9_cell[0]*6 - 1)
    p9_local = np.full((257, 257), 0.85, np.float64)
    p9_local[256, 256] = np.nan
    p9_cells = p9_unknown_cells(p9_local, {'features': [{'geometry': mapping(p9_geom)}]}, 711, 241)
    p9_block = corners_for_cells(p9_cells)
    assert p9_cell in p9_cells and p9_block[967-WINDOW[0],497-WINDOW[2]]

    # Small deterministic stencil/D8 integration fixture uses real builders, no solve.
    proto = load_module('real_sector_test_proto', PROTO)
    d8 = load_module('real_sector_test_d8_build', D8)
    base = np.tile(np.arange(12, dtype=np.float32), (12, 1))
    nodes = np.asarray([[5, 5], [5, 6], [6, 5]], np.int32)
    stencils = proto.all_stencils(base.shape, nodes)
    records = proto.row_records(base, nodes, stencils)
    A, rhs = proto.csr_from_records(records, len(nodes))
    C, d, witnesses, _exempt, centers = d8.build_d8(base, nodes)
    assert A.shape[1] == 3 and A.shape[0] == len(records) and len(stencils) > 0
    assert C.shape[1] == 3 and len(centers) >= 3 and len(witnesses) == len(centers)
    assert np.min(C @ base[tuple(nodes.T)].astype(np.float64)-d) >= -1e-12
    # The synthetic D8 module's baked-in H/W must be rebound to the actual context.
    context = np.zeros((260, 260), np.float32)
    d8.H, d8.W = context.shape
    edge_nodes = np.asarray([[257, 257]], np.int32)
    _Cedge, _dedge, _wedge, _eedge, edge_centers = d8.build_d8(context, edge_nodes)
    assert (258, 258) in edge_centers

    # Exercise the frozen solver/closure/check APIs against its already-solved 49-node fixture.
    solver = load_module('real_sector_test_quantized_solver', SOLVER)
    prior = solver.load_prior()
    b0, n0, A0, rhs0, C0, d0, w0, _x0, _centers0, lo0, hi0, x00, _records0 = prior.build_problem('minimum')
    prior_npz = SOLVER.parent/'run-01'/'reference49.npz'
    frozen = _load_archive(prior_npz)
    if not np.array_equal(frozen['baseline'], b0) or not np.array_equal(frozen['nodes_rc'], n0):
        raise AssertionError('frozen 49-node fixture differs from independently rebuilt solver inputs')
    raw_grid = frozen['raw_cast'].copy()
    closed_grid, closure_status = solver.close_float32(solver.load_closure(), b0, n0,
                                                        raw_grid, lo0, hi0, w0)
    checked_grid, float32_stats = solver.check_float32(
        b0, n0, closed_grid[tuple(n0.T)], lo0, hi0, w0)
    assert closure_status.get('ok') and float32_stats.get('pass')
    assert np.array_equal(checked_grid, frozen['candidate'])
    return {'P_nan_F_finite_corner_used': True, 'infinity_rejected': inf_rejected,
            'missing_readset_pin_rejected': missing_pin_rejected,
            'seed_primary_then_min_first_layer_and_zero_stop': True,
            'EV82_interval_and_inward_f32': True,
            'P9_southeast_touching_cell_included': True,
            'D8_builder_rebound_to_260_context': True,
            'frozen_49_solver_closure_check_pipeline': True,
            'real_stencil_D8_builders_integrated_without_solver': True}


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('self-test')
    prep = sub.add_parser('prepare')
    prep.add_argument('--out', type=Path, required=True)
    solve = sub.add_parser('solve')
    solve.add_argument('--preflight', type=Path, required=True)
    solve.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'self-test':
        print(json.dumps(fixtures(), sort_keys=True, allow_nan=False))
        return 0
    if args.command == 'prepare':
        report = build_preflight(args.out)
        print(json.dumps({k: report[k] for k in ('status', 'selected_seed', 'system', 'eligibility') if k in report},
                         sort_keys=True, allow_nan=False))
        return 0 if report['status'] in {'PREFLIGHT_READY_ONLY', 'NO_SURVIVING_SEED'} else 1
    report = run_one_solve(args.preflight, args.out)
    print(json.dumps({k: report.get(k) for k in ('status', 'diagnostics', 'objective', 'resource_measurement')},
                     sort_keys=True, allow_nan=False))
    return 0 if report['status'] in {'SOLUTION_PENDING_INDEPENDENT_CONSUMER', 'NO_SURVIVING_SEED'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
