#!/usr/bin/env python
"""Read-only first stage for the Narva sector pilot.

This stage checks pinned inputs, reconstructs EV87 eligibility and inventories
the predeclared focus/queue seeds. It deliberately does not query the ODOL face
index, inspect bridge meshes, construct solver rows, or write terrain.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(r'E:/DayZ-Baltic-Build')
G = ROOT / 'v30-global-bank-extension-20261010'
HERE = G / 'global-operator-prototype/real-sector-preflight'
PLAN = G / 'global-operator-prototype/PLAN_REAL_SECTOR.md'
QUEUE = G / 'queue/queue.json'
EV87 = ROOT / 'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
B = ROOT / 'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
O = ROOT / 'v30-narva-dry-bank-relief-20261010/candidate/terrain.npz'
CONS = ROOT / 'v30-narva-dry-bank-relief-20261010/constraints.npz'
PRIOR = ROOT / 'v30-remaining-exact-dry-support-20261009/constraints.npz'
P = ROOT / 'v30-narva-dry-bank-relief-20261010/candidate/plane.npy'
F = ROOT / 'v30-narva-dry-bank-relief-20261010/candidate/visible-field.npy'

PINS = {
    str(PLAN): '14f02179312bc25caf76a087cc873122caed30f6092464f1c01ac7572d519749',
    str(QUEUE): 'cf13887c8de031d65d0a32dab217e8743293103fcd00ea3c07c281c07a6794c9',
    str(EV87): '964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
    str(B): 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
    str(O): 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c',
    str(CONS): 'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c',
    str(PRIOR): '18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370',
    str(P): '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
    str(F): 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
}

N = 2048
WINDOW = (712, 968, 242, 498)  # half-open vertex bounds: 256 x 256
FOCUS_RC = (840, 370)
EXPECTED_QUEUE = {'all_seeds': 5450, 'first_layer': 703}
EXPECTED_WINDOW_FIRST_LAYER = 11


def sha(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def exact_array_equal_with_nan(a, b) -> bool:
    """Exact identity except that paired NaNs are treated as equal.

    All non-NaN payload bytes must match exactly; NaN positions must match.
    This retains a byte-exact metadata gate while permitting legitimate NaNs.
    """
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or a.dtype != b.dtype:
        return False
    if not np.issubdtype(a.dtype, np.floating):
        return np.ascontiguousarray(a).tobytes() == np.ascontiguousarray(b).tobytes()
    an, bn = np.isnan(a), np.isnan(b)
    if not np.array_equal(an, bn):
        return False
    keep = ~an
    return (np.ascontiguousarray(a[keep]).tobytes()
            == np.ascontiguousarray(b[keep]).tobytes())


def check_pins() -> dict[str, str]:
    actual = {}
    failures = []
    for raw, expected in PINS.items():
        path = Path(raw)
        got = sha(path)
        actual[raw] = got
        if got != expected:
            failures.append(f'{path}: {got} != {expected}')
    if failures:
        raise RuntimeError('input pin mismatch: ' + '; '.join(failures))
    return actual


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot load verified helper: {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def eligibility_mask(cls, other_fixed, engineering_halo, large_lake_banks,
                     height, incident_level):
    """EV87 selector mask, independently expressed for fixtures/readability."""
    arrays = (cls, other_fixed, engineering_halo, large_lake_banks, height, incident_level)
    shapes = {np.asarray(x).shape for x in arrays}
    if len(shapes) != 1:
        raise ValueError(f'eligibility shapes differ: {shapes}')
    if np.isinf(incident_level).any():
        raise ValueError('incident water level contains infinity')
    return ((np.asarray(cls) == 0) & ~np.asarray(other_fixed, dtype=bool)
            & ~np.asarray(engineering_halo, dtype=bool)
            & ~np.asarray(large_lake_banks, dtype=bool)
            & (np.asarray(height) > np.asarray(incident_level)))


def incident_levels(p, f, sea: float = 0.85):
    """Rebuild EV87's per-vertex max over P/F samples and SEA, preserving F if P is NaN."""
    p = np.asarray(p, dtype=np.float64)
    f = np.asarray(f, dtype=np.float64)
    if p.ndim != 2 or f.shape != (*p.shape, 4):
        raise ValueError('P/F dimensions mismatch')
    if np.isinf(p).any() or np.isinf(f).any():
        raise ValueError('P/F contain infinity; only NaN encodes unknown')
    rows, cols = p.shape[0] + 1, p.shape[1] + 1
    out = np.full((rows, cols), float(sea), dtype=np.float64)
    for i, (dr, dc) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
        pv = np.nan_to_num(p, nan=sea)
        fv = np.nan_to_num(f[:, :, i], nan=sea)
        level = np.maximum(float(sea), np.maximum(pv, fv))
        dst = out[dr:dr + p.shape[0], dc:dc + p.shape[1]]
        np.maximum(dst, level, out=dst)
    return out


def reason_bits(cls, other_fixed, engineering_halo, large_lake_banks,
                height, incident_level):
    """Bit 0=class, 1=other_fixed, 2=engineering, 3=large lake, 4=not dry."""
    out = np.zeros(np.asarray(cls).shape, dtype=np.uint8)
    out[np.asarray(cls) != 0] |= 1
    out[np.asarray(other_fixed, dtype=bool)] |= 2
    out[np.asarray(engineering_halo, dtype=bool)] |= 4
    out[np.asarray(large_lake_banks, dtype=bool)] |= 8
    out[np.asarray(height) <= np.asarray(incident_level)] |= 16
    return out


def choose_seed(primary_clear: bool, surviving_first_layer: list[dict]) -> dict | None:
    """Selection rule: explicit focus first; else minimum frozen first_layer_id."""
    if primary_clear:
        return {'kind': 'explicit_focus', 'row': FOCUS_RC[0], 'col': FOCUS_RC[1]}
    if not surviving_first_layer:
        return None
    ids = [int(x['first_layer_id']) for x in surviving_first_layer]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate first_layer_id in surviving queue')
    item = min(surviving_first_layer, key=lambda x: int(x['first_layer_id']))
    return {'kind': 'queue_fallback', **item}


def validate_queue(queue: dict) -> list[dict]:
    if queue.get('schema') != 'EV93-seed-queue-v1':
        raise ValueError(f"unexpected queue schema: {queue.get('schema')!r}")
    seeds = queue.get('seeds')
    if not isinstance(seeds, list) or len(seeds) != EXPECTED_QUEUE['all_seeds']:
        raise ValueError('frozen queue seed count changed')
    if any(int(item.get('seed_id', -1)) != index for index, item in enumerate(seeds)):
        raise ValueError('seed_id no longer matches frozen inventory order')
    if int(queue.get('counts', {}).get('first_layer', -1)) != EXPECTED_QUEUE['first_layer']:
        raise ValueError('frozen first-layer count changed')
    first = [x for x in seeds if x.get('state') == 'first_layer']
    ids = [int(x['first_layer_id']) for x in first]
    if len(first) != EXPECTED_QUEUE['first_layer'] or sorted(ids) != list(range(EXPECTED_QUEUE['first_layer'])):
        raise ValueError('first_layer_id sequence is not the frozen contiguous queue')
    local = [x for x in seeds
             if WINDOW[0] <= int(x['row']) < WINDOW[1]
             and WINDOW[2] <= int(x['col']) < WINDOW[3]
             and (x.get('state') == 'first_layer'
                  or (int(x['row']), int(x['col'])) == FOCUS_RC)]
    local_first = [x for x in local if x.get('state') == 'first_layer']
    if len(local_first) != EXPECTED_WINDOW_FIRST_LAYER:
        raise ValueError(f'window queue inventory changed: {len(local_first)} first-layer seeds')
    focus = [x for x in seeds if (int(x['row']), int(x['col'])) == FOCUS_RC]
    if len(focus) != 1 or int(focus[0]['seed_id']) != 1981 or focus[0].get('state') != 'pending_overlap':
        raise ValueError('explicit focus queue identity/state changed')
    return sorted(local, key=lambda x: int(x['first_layer_id']) if x.get('state') == 'first_layer' else -1)


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        return {key: z[key] for key in z.files}


def _atomic_json(path: Path, value) -> None:
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    tmp.replace(path)


def build_inventory() -> tuple[dict, dict[str, np.ndarray]]:
    self_path = Path(__file__).resolve()
    self_before = sha(self_path)
    readset_before = check_pins()
    base = _load_npz(B)
    original = _load_npz(O)
    cons = _load_npz(CONS)
    prior = _load_npz(PRIOR)
    p = np.load(P, allow_pickle=False)
    f = np.load(F, allow_pickle=False)
    queue = json.loads(QUEUE.read_text(encoding='utf-8'))
    local_queue = validate_queue(queue)

    for name, arrays in (('B', base), ('O', original)):
        if set(arrays) != set(base):
            raise ValueError(f'{name}/B metadata key set differs')
        if arrays['heights'].shape != (N, N) or arrays['heights'].dtype != np.float32:
            raise ValueError(f'{name} height shape/dtype mismatch')
        if name == 'O' and any(not exact_array_equal_with_nan(base[k], arrays[k])
                               for k in base if k != 'heights'):
            raise ValueError('EV79/B non-height metadata or protected arrays differ')
    for key in ('cls', 'reserve', 'platform'):
        if key not in base or base[key].shape != (N, N):
            raise ValueError(f'B missing/invalid {key}')
    for key in ('other_fixed', 'engineering_halo', 'wet_support'):
        if key not in cons or cons[key].shape != (N, N):
            raise ValueError(f'constraints missing/invalid {key}')
    if 'large_lake_banks' not in prior or prior['large_lake_banks'].shape != (N, N):
        raise ValueError('prior constraints missing/invalid large_lake_banks')
    if p.shape != (N - 1, N - 1) or f.shape != (N - 1, N - 1, 4):
        raise ValueError('P/F shape mismatch')
    if np.isinf(p).any() or np.isinf(f).any():
        raise ValueError('P/F contain infinity; only NaN encodes unknown')

    ev = load_module('real_sector_ev87', EV87)
    h = base['heights'].astype(np.float64)
    levels = incident_levels(p, f)
    eligible_ev, levels_ev = ev._ev87_eligible(base, cons, prior, h, p, f)
    if not np.array_equal(levels, levels_ev):
        raise AssertionError('independent P/F incident levels differ from EV87 helper')
    independent = eligibility_mask(base['cls'], cons['other_fixed'], cons['engineering_halo'],
                                   prior['large_lake_banks'], h, levels)
    if not np.array_equal(eligible_ev, independent):
        raise AssertionError('independent eligibility formula differs from EV87 helper')
    r0, r1, c0, c1 = WINDOW
    sl = np.s_[r0:r1, c0:c1]
    local_eligible = independent[sl]
    local_reason = reason_bits(base['cls'][sl], cons['other_fixed'][sl],
                               cons['engineering_halo'][sl], prior['large_lake_banks'][sl],
                               h[sl], levels[sl])
    candidates = []
    fallback = []
    for item in local_queue:
        r, c = int(item['row']), int(item['col'])
        row = {
            'seed_id': int(item['seed_id']),
            'first_layer_id': int(item['first_layer_id']) if item.get('first_layer_id') is not None else None,
            'state': str(item['state']), 'row': r, 'col': c,
            'population_from_frozen_queue': str(item['population']),
            'queue_eligible_claim': True,
            'reconstructed_ev87_eligible': bool(independent[r, c]),
            'field_clearance_m_B': float(h[r, c] - levels[r, c]),
            'wet_support_historical': bool(cons['wet_support'][r, c]),
            'reason_bits': int(local_reason[r-r0, c-c0]),
        }
        candidates.append(row)
        if item.get('state') == 'first_layer' and independent[r, c]:
            fallback.append({'first_layer_id': int(item['first_layer_id']),
                             'seed_id': int(item['seed_id']), 'row': r, 'col': c,
                             'population': str(item['population'])})
    primary = next(x for x in candidates if (x['row'], x['col']) == FOCUS_RC)
    if not primary['reconstructed_ev87_eligible']:
        raise ValueError('EV87 queue focus no longer passes reconstructed eligibility')

    readset_after = check_pins()
    if readset_before != readset_after:
        raise RuntimeError('source readset changed during inventory')
    self_after = sha(self_path)
    if self_before != self_after:
        raise RuntimeError('preflight source changed during inventory')
    report = {
        'status': 'PREPARED_ELIGIBILITY_INVENTORY_ONLY',
        'scope': '256x256 vertex window; no ODOL index, road/bridge geometry, solver rows, or terrain mutation',
        'window_rc_half_open': list(WINDOW),
        'source_hashes_before_after': {'before': readset_before, 'after': readset_after},
        'preflight_source': {'path': str(self_path), 'sha256_before_after': [self_before, self_after]},
        'queue': {'sha256': readset_before[str(QUEUE)], 'schema': queue['schema'],
                  'all_seeds': len(queue['seeds']), 'first_layer': len([x for x in queue['seeds'] if x.get('state') == 'first_layer']),
                  'window_first_layer': len([x for x in local_queue if x.get('state') == 'first_layer'])},
        'eligibility': {'reconstructed_total': int(local_eligible.sum()),
                        'bank_interior_categorization_is_queue_metadata': True,
                        'counts_by_reason_bit_mask': {str(int(k)): int(v) for k, v in zip(*np.unique(local_reason, return_counts=True))}},
        'selection_rule': {
            'primary': {'row': FOCUS_RC[0], 'col': FOCUS_RC[1], 'seed_id': int(primary['seed_id'])},
            'fallback': 'only after exact local geometry gates: minimum first_layer_id among in-window queue first_layer seeds that survive all gates',
            'inventory_order_is_not_a_selection_or_a_dryness_certificate': True,
            'surviving_fallback_candidates_after_field_eligibility_only': fallback,
            'final_choice_status': 'DEFERRED_UNTIL_EXACT_P_F_ODOL_ROAD_BRIDGE_PREFLIGHT',
        },
        'seed_candidates': candidates,
        'reason_bit_legend': {'1': 'cls != 0', '2': 'other_fixed', '4': 'engineering_halo',
                              '8': 'large_lake_banks', '16': 'B height <= max incident P/F/SEA sample'},
        'limits': ['field clearance at a vertex is preliminary only; it does not prove a cell/face is dry',
                   'wet_support is recorded as historical metadata, never treated as water by itself',
                   'no seed can be called final until road, bridge, P/F cell, and compiled-face gates run'],
    }
    arrays_out = {'ev87_eligible': local_eligible.astype(np.uint8),
                  'reason_bits': local_reason.astype(np.uint8)}
    return report, arrays_out


def run_inventory(out: Path) -> None:
    report, arrays = build_inventory()
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    tmp_npz = out / 'domain-reasons.npz.tmp'
    with tmp_npz.open('wb') as f:
        np.savez_compressed(f, **arrays)
    tmp_npz.replace(out / 'domain-reasons.npz')
    _atomic_json(out / 'inventory.json', report)


def fixtures() -> dict:
    cls = np.array([[0, 0, 1, 0]], dtype=np.uint8)
    other = np.array([[False, True, False, False]])
    engineering = np.array([[False, False, False, True]])
    lake = np.zeros_like(other)
    h = np.array([[2.0, 2.0, 3.0, 1.0]])
    level = np.array([[1.0, 1.0, 1.0, 1.0]])
    got = eligibility_mask(cls, other, engineering, lake, h, level)
    assert got.tolist() == [[True, False, False, False]]
    assert choose_seed(False, [{'first_layer_id': 9}, {'first_layer_id': 2}]) == {
        'kind': 'queue_fallback', 'first_layer_id': 2}
    assert choose_seed(True, [{'first_layer_id': 9}]) == {
        'kind': 'explicit_focus', 'row': FOCUS_RC[0], 'col': FOCUS_RC[1]}
    assert choose_seed(False, []) is None
    try:
        choose_seed(False, [{'first_layer_id': 2}, {'first_layer_id': 2}])
    except ValueError:
        duplicate_rejected = True
    else:
        duplicate_rejected = False
    assert duplicate_rejected
    fixture_p = np.array([[np.nan]], dtype=np.float64)
    fixture_f = np.array([[[0.85, 1.25, np.nan, 0.85]]], dtype=np.float64)
    lv = incident_levels(fixture_p, fixture_f)
    assert lv.shape == (2, 2) and np.allclose(lv, [[0.85, 1.25], [0.85, 0.85]])
    try:
        eligibility_mask(cls, other, engineering, lake, h, np.array([[1.0, np.inf, 1.0, 1.0]]))
    except ValueError:
        infinity_rejected = True
    else:
        infinity_rejected = False
    assert infinity_rejected
    return {'eligibility': 'PASS', 'primary_then_min_first_layer_id': 'PASS',
            'empty_and_duplicate_queue_ids': 'PASS', 'F_is_preserved_when_P_is_NaN': 'PASS',
            'infinite_water_level_fails_closed': 'PASS'}


def main() -> int:
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--self-test', action='store_true')
    group.add_argument('--inventory-out', type=Path)
    args = ap.parse_args()
    if args.self_test:
        print(json.dumps({'status': 'PASS_INVENTORY_FIXTURES', 'fixtures': fixtures()}, sort_keys=True))
        return 0
    run_inventory(args.inventory_out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
