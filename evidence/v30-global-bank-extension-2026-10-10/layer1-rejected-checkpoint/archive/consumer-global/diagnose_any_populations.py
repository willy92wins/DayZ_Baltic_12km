#!/usr/bin/env python
"""Read-only ANY-incidence diagnostics for the frozen EV93 global candidate.

This is descriptive output only: it adds no acceptance gate and never writes terrain.
A candidate path and independently approved SHA are mandatory for a full report.
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
HERE = ROOT / 'v30-global-bank-extension-20261010/consumer-global'
EV87_PATH = ROOT / 'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
EV88_PATH = ROOT / 'v30-wide-bank-fairing-pilot-20261010/review-independent/verify_ev88q.py'
EXPECTED_EV87_SHA = '964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27'
EXPECTED_EV88_SHA = '82a988790e6bdfc0289bcb7c32cb0afd1210e07b264d92731aba266bc5980f78'
EXPECTED_B_SHA = 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
EXPECTED_WET_SUPPORT_NODES = 65955
NEW_HINGE_THRESHOLD_DEG = 30.0001
FAMILIES = ('diag', 'vertical', 'horizontal')


def sha(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load_module(name: str, path: Path, expected_sha: str):
    actual = sha(path)
    if actual != expected_sha:
        raise AssertionError(f'frozen helper SHA mismatch {path}: {actual} != {expected_sha}')
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot import frozen helper {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def any_incident_vertices(population_mask: np.ndarray, kind: str, ev87) -> np.ndarray:
    """Return hinges with at least one of their four vertices in a node mask."""
    slices = ev87.edge_vertex_slices(np.asarray(population_mask, dtype=bool), kind)
    if len(slices) != 4:
        raise AssertionError(f'{kind} hinge must expose exactly four vertex-incidence masks')
    return np.logical_or.reduce(slices)


def all_incident_vertices(population_mask: np.ndarray, kind: str, ev87) -> np.ndarray:
    """Consumer-reference ALL-four mask, included only to distinguish its scope."""
    slices = ev87.edge_vertex_slices(np.asarray(population_mask, dtype=bool), kind)
    if len(slices) != 4:
        raise AssertionError(f'{kind} hinge must expose exactly four vertex-incidence masks')
    return np.logical_and.reduce(slices)


def run_fixtures(ev87) -> dict:
    """Analytic zero/one/four incidence checks against the production ANY helper."""
    rows = {}
    for kind in FAMILIES:
        target = (1, 1)
        zero = np.zeros((5, 5), dtype=bool)
        single = zero.copy()
        vertices = ev87._ev87_hinge_vertices(kind, *target)
        single[vertices[0]] = True
        four = zero.copy()
        for vertex in vertices:
            four[vertex] = True
        z_any = any_incident_vertices(zero, kind, ev87)
        z_all = all_incident_vertices(zero, kind, ev87)
        s_any = any_incident_vertices(single, kind, ev87)
        s_all = all_incident_vertices(single, kind, ev87)
        f_any = any_incident_vertices(four, kind, ev87)
        f_all = all_incident_vertices(four, kind, ev87)
        checks = {
            'zero_incidence_is_empty': int(z_any.sum()) == 0 and int(z_all.sum()) == 0,
            'one_vertex_incidence_is_in_any': bool(s_any[target]),
            'one_vertex_is_not_all_four': not bool(s_all[target]),
            'four_vertices_are_in_any': bool(f_any[target]),
            'four_vertices_are_all_four': bool(f_all[target]),
            'negative_and_substitution_detected': bool(s_any[target] and not s_all[target]),
        }
        if not all(checks.values()):
            raise AssertionError(f'ANY-incidence fixture failed for {kind}: {checks}')
        rows[kind] = {'checks': checks, 'single_any_count': int(s_any.sum()),
                      'single_all_count': int(s_all.sum()), 'four_any_count': int(f_any.sum()),
                      'four_all_count': int(f_all.sum()), 'target_hinge_rc': list(target)}
    return {'status': 'PASS', 'families': rows}


def summary(ev87, values: np.ndarray) -> dict:
    a = np.asarray(values, dtype=np.float64).ravel()
    if not a.size:
        return {'n': 0, 'p99': None, 'max': None, 'above30': 0, 'mean_square': None}
    # Use the frozen EV87 descriptive summary and bracket selector.
    metrics = ev87.summaries([a])
    q = ev87._ev87_thresholds(a)
    metrics['p99_q0_deg'] = float(q['q0'])
    metrics['p99_q1_deg'] = float(q['q1'])
    return metrics


def compare_angles(ev87, b: np.ndarray, h: np.ndarray, mask: np.ndarray) -> dict:
    bv = np.asarray(b, dtype=np.float64)[mask]
    hv = np.asarray(h, dtype=np.float64)[mask]
    if bv.shape != hv.shape:
        raise AssertionError('B/H angle vectors differ in shape')
    delta = hv - bv
    return {
        'hinges': int(bv.size),
        'B': summary(ev87, bv),
        'H': summary(ev87, hv),
        'improved_strict_count': int(np.count_nonzero(delta < 0.0)),
        'worsened_strict_count': int(np.count_nonzero(delta > 0.0)),
        'unchanged_exact_count': int(np.count_nonzero(delta == 0.0)),
        'delta_H_minus_B_deg': {
            'min': float(delta.min()) if delta.size else None,
            'mean': float(delta.mean()) if delta.size else None,
            'max': float(delta.max()) if delta.size else None,
        },
        'new_over_30_0001_count': int(np.count_nonzero(
            (bv <= NEW_HINGE_THRESHOLD_DEG) & (hv > NEW_HINGE_THRESHOLD_DEG))),
        'threshold_deg': NEW_HINGE_THRESHOLD_DEG,
    }


def population_report(ev87, base_h: np.ndarray, candidate_h: np.ndarray,
                      populations: dict[str, np.ndarray]) -> dict:
    angles_b = dict(ev87.edge_angles(base_h))
    angles_h = dict(ev87.edge_angles(candidate_h))
    if set(angles_b) != set(FAMILIES) or set(angles_h) != set(FAMILIES):
        raise AssertionError('frozen EV87 angle families changed')
    output = {}
    any_masks_by_population = {}
    all_masks_by_population = {}
    for name, node_mask in populations.items():
        mask = np.asarray(node_mask, dtype=bool)
        if mask.shape != base_h.shape:
            raise AssertionError(f'{name} vertex population shape mismatch {mask.shape}')
        by_incidence = {}
        any_masks = {}
        all_masks = {}
        any_b_parts = []
        any_h_parts = []
        all_b_parts = []
        all_h_parts = []
        families = {}
        for kind in FAMILIES:
            any_mask = any_incident_vertices(mask, kind, ev87)
            all_mask = all_incident_vertices(mask, kind, ev87)
            any_masks[kind] = any_mask
            all_masks[kind] = all_mask
            ab = np.asarray(angles_b[kind], dtype=np.float64)[any_mask]
            ah = np.asarray(angles_h[kind], dtype=np.float64)[any_mask]
            lb = np.asarray(angles_b[kind], dtype=np.float64)[all_mask]
            lh = np.asarray(angles_h[kind], dtype=np.float64)[all_mask]
            any_b_parts.append(ab); any_h_parts.append(ah)
            all_b_parts.append(lb); all_h_parts.append(lh)
            families[kind] = {
                'ANY': compare_angles(ev87, angles_b[kind], angles_h[kind], any_mask),
                'ALL_four_comparison': compare_angles(ev87, angles_b[kind], angles_h[kind], all_mask),
            }
        any_b = np.concatenate(any_b_parts) if any_b_parts else np.empty(0, dtype=np.float64)
        any_h = np.concatenate(any_h_parts) if any_h_parts else np.empty(0, dtype=np.float64)
        all_b = np.concatenate(all_b_parts) if all_b_parts else np.empty(0, dtype=np.float64)
        all_h = np.concatenate(all_h_parts) if all_h_parts else np.empty(0, dtype=np.float64)
        output[name] = {
            'population_vertices': int(mask.sum()),
            'ANY': {
                'families': {kind: families[kind]['ANY'] for kind in FAMILIES},
                'aggregate_families_concatenated_once_for_this_population': compare_angles(
                    ev87, any_b, any_h, np.ones(any_b.shape, dtype=bool)),
                'unique_hinges': sum(int(x.sum()) for x in any_masks.values()),
            },
            'ALL_four_comparison': {
                'families': {kind: families[kind]['ALL_four_comparison'] for kind in FAMILIES},
                'aggregate_families_concatenated_once_for_this_population': compare_angles(
                    ev87, all_b, all_h, np.ones(all_b.shape, dtype=bool)),
                'unique_hinges': sum(int(x.sum()) for x in all_masks.values()),
            },
        }
        any_masks_by_population[name] = any_masks
        all_masks_by_population[name] = all_masks
    # Keep overlap arithmetic as compact Boolean masks. The populations are
    # reported independently; a hinge touched by multiple populations is not
    # mislabeled as a set of disjoint observations.
    overlap_any = {}; overlap_all = {}
    for kind in FAMILIES:
        any_incidence = np.stack([any_masks_by_population[name][kind]
                                  for name in populations], axis=0).sum(axis=0, dtype=np.uint8)
        all_incidence = np.stack([all_masks_by_population[name][kind]
                                  for name in populations], axis=0).sum(axis=0, dtype=np.uint8)
        overlap_any[kind] = {
            'unique_union_hinges': int(np.count_nonzero(any_incidence)),
            'sum_of_per_population_memberships_not_a_disjoint_total': int(any_incidence.sum()),
            'hinges_by_number_of_populations': {
                str(n): int(np.count_nonzero(any_incidence == n))
                for n in range(1, len(populations)+1)},
        }
        overlap_all[kind] = {
            'unique_union_hinges': int(np.count_nonzero(all_incidence)),
            'sum_of_per_population_memberships_not_a_disjoint_total': int(all_incidence.sum()),
            'hinges_by_number_of_populations': {
                str(n): int(np.count_nonzero(all_incidence == n))
                for n in range(1, len(populations)+1)},
        }
    any_memberships = sum(v['sum_of_per_population_memberships_not_a_disjoint_total']
                          for v in overlap_any.values())
    all_memberships = sum(v['sum_of_per_population_memberships_not_a_disjoint_total']
                          for v in overlap_all.values())
    return {
        'by_population': output,
        'population_membership_overlap': {
            'ANY': {'by_family': overlap_any,
                    'unique_union_hinges_across_distinct_families': sum(v['unique_union_hinges'] for v in overlap_any.values()),
                    'sum_of_population_memberships_not_a_disjoint_total': any_memberships},
            'ALL_four_comparison': {'by_family': overlap_all,
                    'unique_union_hinges_across_distinct_families': sum(v['unique_union_hinges'] for v in overlap_all.values()),
                    'sum_of_population_memberships_not_a_disjoint_total': all_memberships},
        },
        'families': list(FAMILIES),
    }


def load_helpers():
    ev87 = load_module('ev93_any_diag_ev87', EV87_PATH, EXPECTED_EV87_SHA)
    ev88 = load_module('ev93_any_diag_ev88', EV88_PATH, EXPECTED_EV88_SHA)
    return ev87, ev88


def verify_candidate(path: Path, expected_sha: str, ev87, ev88):
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    if getattr(ev88, 'B_SHA', None) != EXPECTED_B_SHA:
        raise AssertionError('EV88 helper B pin differs from the independently expected EV82-B identity')
    if len(expected_sha) != 64 or any(ch not in '0123456789abcdef' for ch in expected_sha.lower()):
        raise ValueError('--candidate-sha must be a 64-digit SHA256')
    bundle = ev88.checked_sources()
    actual_candidate_sha = sha(path)
    if actual_candidate_sha != expected_sha.lower():
        raise AssertionError(f'candidate SHA mismatch: {actual_candidate_sha} != {expected_sha}')
    with np.load(path, allow_pickle=False) as z:
        candidate_npz = {key: z[key] for key in z.files}
    base_npz = bundle['B']
    if set(candidate_npz) != set(base_npz):
        raise AssertionError('candidate NPZ keys differ from frozen B')
    for key in base_npz:
        if key == 'heights':
            continue
        if not np.array_equal(candidate_npz[key], base_npz[key], equal_nan=True):
            raise AssertionError(f'candidate metadata differs from frozen B: {key}')
    base_h = np.asarray(base_npz['heights'])
    candidate_h = np.asarray(candidate_npz['heights'])
    if base_h.dtype != np.float32 or candidate_h.dtype != np.float32 or base_h.shape != (2048, 2048) or candidate_h.shape != base_h.shape:
        raise AssertionError('B/candidate heights must be matching 2048x2048 float32 arrays')
    if not np.isfinite(base_h).all() or not np.isfinite(candidate_h).all():
        raise AssertionError('B/candidate heights contain nonfinite values')
    cons = bundle['constraints']; prior = bundle['prior']
    eligible, _ = ev87._ev87_eligible(base_npz, cons, prior, base_h,
                                      bundle['P'], bundle['F'])
    populations = ev87._ev87_populations(base_npz, cons)
    populations['wet_support_eligible'] = eligible & cons['wet_support'].astype(bool)
    wet_count = int(populations['wet_support_eligible'].sum())
    if wet_count != EXPECTED_WET_SUPPORT_NODES:
        raise AssertionError(f'eligible wet-support nodes changed: {wet_count} != {EXPECTED_WET_SUPPORT_NODES}')
    for name in ('bank', 'interior', 'wet_support_eligible'):
        if populations[name].dtype != np.bool_ or populations[name].shape != base_h.shape:
            raise AssertionError(f'invalid {name} population mask')
    if np.any(populations['bank'] & populations['interior']) or \
       np.any(populations['bank'] & populations['wet_support_eligible']) or \
       np.any(populations['interior'] & populations['wet_support_eligible']):
        raise AssertionError('frozen vertex populations unexpectedly overlap')
    readset = dict(bundle['hashes'])
    readset[str(EV87_PATH.resolve())] = EXPECTED_EV87_SHA
    readset[str(EV88_PATH.resolve())] = EXPECTED_EV88_SHA
    readset[str(path)] = actual_candidate_sha
    readset[str(Path(__file__).resolve())] = sha(__file__)
    for input_path, expected in readset.items():
        if sha(input_path) != expected:
            raise AssertionError(f'read-set input differs before analysis: {input_path}')
    report = {
        'status': 'DIAGNOSTIC_ONLY_ANY_POPULATIONS',
        'acceptance_gate': False,
        'candidate_path': str(path), 'candidate_sha256': actual_candidate_sha,
        'baseline_path': str(ev88.B_PATH.resolve()), 'baseline_sha256': sha(ev88.B_PATH),
        'helper_pins': {str(EV87_PATH.resolve()): EXPECTED_EV87_SHA,
                        str(EV88_PATH.resolve()): EXPECTED_EV88_SHA},
        'readset_sha256_before': dict(sorted(readset.items())),
        'wet_support_eligible_expected_nodes': EXPECTED_WET_SUPPORT_NODES,
        'metrics_scope': 'Descriptive per-population metrics only; ANY uses at least one of four hinge vertices; ALL_four is reported only as a scope comparison. Hinge memberships across populations overlap and are not summed as disjoint observations.',
        'thresholds': {'new_over_30_deg': NEW_HINGE_THRESHOLD_DEG,
                       'p99': 'frozen EV87 descriptive percentile/brackets; diagnostic only'},
        'diagnostic': population_report(ev87, base_h, candidate_h, populations),
    }
    after = {key: sha(key) for key in sorted(readset)}
    report['readset_sha256_after'] = after
    report['readset_stable'] = after == dict(sorted(readset.items()))
    if not report['readset_stable']:
        raise AssertionError('diagnostic read-set changed during computation')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--candidate-sha')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    ev87, ev88 = load_helpers()
    if args.self_test:
        print(json.dumps({'status': 'FIXTURES_PASS', 'fixtures': run_fixtures(ev87)},
                         sort_keys=True, allow_nan=False))
        return
    if not args.candidate or not args.candidate_sha or not args.output:
        parser.error('full diagnostic requires --candidate, --candidate-sha, and --output')
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(f'refusing to overwrite diagnostic report: {output}')
    report = verify_candidate(args.candidate, args.candidate_sha, ev87, ev88)
    tmp = output.with_name(output.name + '.tmp')
    if tmp.exists():
        raise FileExistsError(f'refusing pre-existing temporary report: {tmp}')
    tmp.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    tmp.replace(output)
    print(json.dumps({'status': report['status'], 'candidate_sha256': report['candidate_sha256'],
                      'populations': {k: v['population_vertices'] for k, v in report['diagnostic']['by_population'].items()},
                      'output': str(output)}, sort_keys=True))


if __name__ == '__main__':
    main()
