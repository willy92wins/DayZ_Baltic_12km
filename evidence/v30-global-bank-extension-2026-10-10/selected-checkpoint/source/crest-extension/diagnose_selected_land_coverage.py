"""Offline summary of EV93 run-02 changed terrain versus nominal P/F/SEA.

This is diagnostic only. It does not load author code, run a solver, or mutate a
candidate. Local P/F face support follows the frozen EV87 sign/native-face
helpers. SEA is reported separately as the global 0.85 m envelope, not asserted
to be a rendered sea polygon at every map coordinate.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

G = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
EV87 = Path(r'E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py')
EV87_SHA = '964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27'
BASE = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')
BASE_SHA = 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
P_PATH = BASE.parent / 'plane.npy'
P_SHA = '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0'
F_PATH = BASE.parent / 'visible-field.npy'
F_SHA = 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'
SELECTION = G / 'compound-selection/run-02/selection.json'
SELECTION_SHA = '3b22dcc381b34b8d7c3e6641d3c919658f0fe7377594a859e3d5c064cf92ba0b'
OUTPUT = G / 'crest-extension/selected-land-coverage.json'
SEA_MAX_M = 0.85  # EV87 SEA constant; nominal envelope only, not water-object coverage.


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def load_ev87():
    if sha(EV87) != EV87_SHA:
        raise RuntimeError('EV87 source pin changed')
    spec = importlib.util.spec_from_file_location('ev93_selected_land_ev87', EV87)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot import frozen geometry helpers: {EV87}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if float(module.SEA) != SEA_MAX_M:
        raise RuntimeError('SEA envelope differs from the pinned EV87 helper')
    return module


def corner_to_vertex(parts, n):
    out = np.zeros((n, n), dtype=bool)
    for i, (dr, dc) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
        out[dr:dr+n-1, dc:dc+n-1] |= parts[i]
    return out


def p_unknown_vertices(p, n):
    cell_unknown = ~np.isfinite(p)
    out = np.zeros((n, n), dtype=bool)
    for dr, dc in ((0, 0), (0, 1), (1, 0), (1, 1)):
        out[dr:dr+n-1, dc:dc+n-1] |= cell_unknown
    return out


def f_unknown_vertices(f, n):
    out = np.zeros((n, n), dtype=bool)
    for i, (dr, dc) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
        out[dr:dr+n-1, dc:dc+n-1] |= ~np.isfinite(f[:, :, i])
    return out


def surface_state(h, p, f, ev, p_unknown, f_unknown):
    signs = ev.signs_for(h, p, f)
    masks = ev.native_face_masks(signs, f)
    p_support = ev.support_vertices({'P': masks['P']})
    f_support = ev.support_vertices({'F': masks['F']})
    p_below = corner_to_vertex(signs['P'], h.shape[0])
    f_below = corner_to_vertex(signs['F'], h.shape[0])
    sea_below = corner_to_vertex(signs['SEA'], h.shape[0])
    local_support = p_support | f_support
    unknown = p_unknown | f_unknown
    # Integer labels keep the two full-grid classifications small in memory.
    state = np.full(h.shape, 0, dtype=np.uint8)  # known dry, above SEA envelope
    state[unknown] = 3
    state[sea_below & ~local_support & ~unknown] = 4
    state[local_support & ~(p_below | f_below)] = 1
    state[p_below | f_below] = 2
    return {
        'state': state,
        'P_below': p_below,
        'F_below': f_below,
        'SEA_below': sea_below,
        'P_face_support': p_support,
        'F_face_support': f_support,
        'local_face_support': local_support,
        'unknown_P': p_unknown,
        'unknown_F': f_unknown,
    }


def counts_at_nodes(mask, nodes):
    if len(nodes) == 0:
        return 0
    return int(np.count_nonzero(mask[nodes[:, 0], nodes[:, 1]]))


def distributions(values):
    vals = np.asarray(values)
    if vals.size == 0:
        return {'n': 0, 'above30': 0, 'p99_deg': None, 'max_deg': None, 'mean_square_deg2': None}
    return {
        'n': int(vals.size),
        'above30': int(np.count_nonzero(vals > 30.0)),
        'p99_deg': float(np.percentile(vals, 99)),
        'max_deg': float(np.max(vals)),
        'mean_square_deg2': float(np.mean(np.square(vals, dtype=np.float64))),
    }


def main():
    if OUTPUT.exists():
        raise FileExistsError(f'refusing to overwrite diagnostic: {OUTPUT}')
    expected = ((BASE, BASE_SHA), (P_PATH, P_SHA), (F_PATH, F_SHA),
                (SELECTION, SELECTION_SHA), (EV87, EV87_SHA))
    for path, wanted in expected:
        actual = sha(path)
        if actual != wanted:
            raise RuntimeError(f'input pin changed: {path}: {actual} != {wanted}')

    selection = json.loads(SELECTION.read_text(encoding='utf-8'))
    if selection.get('status') != 'SELECTED' or selection.get('schema') != 'ev93.compound-selection.v1':
        raise RuntimeError('run-02 selection is not the pinned SELECTED receipt')
    candidate_path = Path(selection['candidate']['path']).resolve()
    candidate_sha = selection['candidate']['sha256']
    if sha(candidate_path) != candidate_sha:
        raise RuntimeError('selected candidate SHA drift')
    ev = load_ev87()

    with np.load(BASE, allow_pickle=False) as z:
        base_npz = {key: z[key] for key in z.files}
    with np.load(candidate_path, allow_pickle=False) as z:
        candidate_npz = {key: z[key] for key in z.files}
    if set(base_npz) != set(candidate_npz):
        raise RuntimeError('candidate metadata key set differs from B')
    for key in base_npz:
        if key != 'heights' and not np.array_equal(base_npz[key], candidate_npz[key], equal_nan=True):
            raise RuntimeError(f'candidate metadata differs from B: {key}')
    base = np.asarray(base_npz['heights'], dtype=np.float32)
    candidate = np.asarray(candidate_npz['heights'], dtype=np.float32)
    if base.shape != (2048, 2048) or candidate.shape != base.shape:
        raise RuntimeError('terrain grid shape differs from pinned EV82 dimensions')
    changed_mask = candidate != base
    nodes = np.argwhere(changed_mask).astype(np.int32)
    if len(nodes) != int(selection['candidate'].get('changed_vertices', len(nodes))):
        raise RuntimeError('receipt changed-vertex count, if present, disagrees')

    p = np.load(P_PATH, allow_pickle=False).astype(np.float32, copy=False)
    f = np.load(F_PATH, allow_pickle=False).astype(np.float32, copy=False)
    if p.shape != (2047, 2047) or f.shape != (2047, 2047, 4):
        raise RuntimeError(f'P/F shapes changed: P={p.shape}, F={f.shape}')
    pu = p_unknown_vertices(p, 2048)
    fu = f_unknown_vertices(f, 2048)
    state_b = surface_state(base, p, f, ev, pu, fu)
    state_h = surface_state(candidate, p, f, ev, pu, fu)

    state_counts = {}
    state_names = {0: 'dry_known_above_SEA', 1: 'shore_wet_face_support',
                   2: 'below_local_P_or_F', 3: 'unknown_P_or_F', 4: 'SEA_envelope_only'}
    for label, state in (('B', state_b), ('candidate', state_h)):
        state_counts[label] = {
            name: counts_at_nodes(state['state'] == code, nodes)
            for code, name in state_names.items()
        }
    changed_tags = {}
    for label, state in (('B', state_b), ('candidate', state_h)):
        changed_tags[label] = {
            'P_below_at_vertex_sample': counts_at_nodes(state['P_below'], nodes),
            'F_below_at_vertex_sample': counts_at_nodes(state['F_below'], nodes),
            'SEA_below_0_85m_envelope': counts_at_nodes(state['SEA_below'], nodes),
            'P_wet_triangle_support': counts_at_nodes(state['P_face_support'], nodes),
            'F_wet_triangle_support': counts_at_nodes(state['F_face_support'], nodes),
            'P_unknown_incident': counts_at_nodes(state['unknown_P'], nodes),
            'F_unknown_incident': counts_at_nodes(state['unknown_F'], nodes),
            'terrain_water_metadata_flag': counts_at_nodes(base_npz['water'], nodes),
            'terrain_beach_metadata_flag': counts_at_nodes(base_npz['beach'], nodes),
        }

    transition = Counter()
    b_state_nodes = state_b['state'][nodes[:, 0], nodes[:, 1]]
    h_state_nodes = state_h['state'][nodes[:, 0], nodes[:, 1]]
    for before, after in zip(b_state_nodes.tolist(), h_state_nodes.tolist()):
        transition[f'{state_names[int(before)]} -> {state_names[int(after)]}'] += 1

    # Full-map angular residuals, partitioned using B's nominal P/F face support.
    pf_support = state_b['P_face_support'] | state_b['F_face_support']
    unknown = pu | fu
    sea_below = state_b['SEA_below']
    angle_report = {}
    all_angles_b = dict(ev.edge_angles(base.astype(np.float64)))
    all_angles_h = dict(ev.edge_angles(candidate.astype(np.float64)))
    for kind, angle_b in all_angles_b.items():
        angles_b = np.asarray(angle_b)
        if kind not in all_angles_h:
            raise RuntimeError(f'candidate angle family missing: {kind}')
        angles_h = np.asarray(all_angles_h[kind])
        if angles_b.shape != angles_h.shape:
            raise RuntimeError(f'angle shape mismatch for {kind}')
        pf_parts = ev.edge_vertex_slices(pf_support, kind)
        unknown_parts = ev.edge_vertex_slices(unknown, kind)
        sea_parts = ev.edge_vertex_slices(sea_below, kind)
        pf_count = np.sum(np.stack(pf_parts), axis=0)
        unknown_any = np.logical_or.reduce(unknown_parts)
        sea_any = np.logical_or.reduce(sea_parts)
        categories = {
            'all_surface': np.ones(angles_b.shape, dtype=bool),
            'local_PF_support_any': pf_count > 0,
            'shore_mixed_PF_support': (pf_count > 0) & (pf_count < 4),
            'all_four_PF_supported': pf_count == 4,
            'unknown_no_PF_support': (pf_count == 0) & unknown_any,
            'SEA_envelope_only_no_PF_support': (pf_count == 0) & ~unknown_any & sea_any,
            'known_dry_no_PF_support_above_SEA': (pf_count == 0) & ~unknown_any & ~sea_any,
        }
        family = {}
        for name, mask in categories.items():
            before = angles_b[mask]
            after = angles_h[mask]
            family[name] = {
                'baseline': distributions(before),
                'candidate': distributions(after),
                'new_over30': int(np.count_nonzero((angles_b <= 30.0) & (angles_h > 30.0) & mask)),
                'resolved_over30': int(np.count_nonzero((angles_b > 30.0) & (angles_h <= 30.0) & mask)),
                'exact_angle_values_changed': int(np.count_nonzero((angles_b != angles_h) & mask)),
                'max_abs_delta_deg': (float(np.max(np.abs(angles_h[mask] - angles_b[mask])))
                                      if np.any(mask) else None),
            }
        angle_report[kind] = family

    slope_report = {}
    for label, terrain in (('B', base), ('candidate', candidate)):
        slopes = ev.slopes(terrain.astype(np.float64))
        slope_report[label] = {
            'triangle_count': int(sum(x.size for x in slopes)),
            'over35deg_per_triangle_order': [int(np.count_nonzero(x > 35.0)) for x in slopes],
            'max_deg_per_triangle_order': [float(np.max(x)) for x in slopes],
        }

    classes = Counter(map(int, base_npz['cls'][nodes[:, 0], nodes[:, 1]].tolist()))
    changed_cells = np.zeros((2047, 2047), dtype=bool)
    changed_cells |= changed_mask[:-1, :-1]
    changed_cells |= changed_mask[:-1, 1:]
    changed_cells |= changed_mask[1:, :-1]
    changed_cells |= changed_mask[1:, 1:]
    result = {
        'schema': 'ev93.selected-land-coverage-diagnostic.v1',
        'status': 'DIAGNOSTIC_ONLY_OFFLINE',
        'inputs': {
            str(path): {'sha256': wanted} for path, wanted in expected
        } | {str(candidate_path): {'sha256': candidate_sha},
             str(Path(__file__).resolve()): {'sha256': sha(Path(__file__))}},
        'candidate': {'path': str(candidate_path), 'sha256': candidate_sha,
                      'selection_path': str(SELECTION), 'selection_sha256': SELECTION_SHA},
        'counts': {
            'changed_vertices': int(len(nodes)),
            'changed_native_cells_incident': int(np.count_nonzero(changed_cells)),
            'changed_vertices_by_B_class': dict(sorted(classes.items())),
            'exclusive_local_surface_state_B': state_counts['B'],
            'exclusive_local_surface_state_candidate': state_counts['candidate'],
            'B_to_candidate_state_transitions': dict(sorted(transition.items())),
            'nominal_surface_tags_at_changed_vertices': changed_tags,
        },
        'definitions': {
            'P_below_at_vertex_sample': 'EV87 signs_for: finite per-cell physical P level > terrain height at that corner sample; unknown P stays separately counted.',
            'F_below_at_vertex_sample': 'EV87 signs_for: finite per-corner visible F level > terrain height; native face support additionally requires all three F corners finite.',
            'wet_triangle_support': 'EV87 native_face_masks + support_vertices; any triangle with a below-surface corner contributes all its vertices, so this includes dry-side shoreline vertices.',
            'SEA_envelope_only': 'EV87 global SEA constant 0.85 m at a vertex, with no P/F wet-triangle support and no local P/F unknown; not proof that a sea object is rendered at that location.',
            'unknown_P_or_F': 'Any incident cell P missing or corresponding incident F corner missing, unless known P/F contact has higher-priority class; missing metadata is still reported independently in tags.',
            'wet_support_warning': 'Terrain water metadata flag, nominal P/F/SEA contact, triangle support, and EV91 wet-support population are distinct quantities; none is substituted for another here.',
            'shore_mixed_PF_support_hinge': 'A hinge whose four native vertices include 1–3 vertices in the baseline P/F wet-triangle support mask. This is immediate geometric shoreline support, not a distance-band estimate of all dry hillsides.',
            'angle_metrics': 'Exact EV87 edge_angles families on the full 2048 grid; >30 degrees and slope >35 degrees are inherited consumer diagnostics, not new acceptance gates.',
        },
        'full_map_hinge_diagnostics_by_family': angle_report,
        'full_map_triangle_slope_diagnostics': slope_report,
        'limitations': [
            'Offline geometry/statistics only; no DayZ render or visual acceptance.',
            'No face-index rescan or exact ODOL exposure rerun; compiled-face coverage remains the existing consumer result.',
            'SEA is only the pinned nominal 0.85 m global envelope. P/F face masks supply local nominal water support.',
            'The shore hinge group catches immediate mixed support only; dry slopes farther inland remain in dry/unknown groups, not a shoreline-distance band.',
            'Wet-support eligibility was not used as a wet/dry classifier.',
        ],
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'changed_vertices': len(nodes),
                      'output': str(OUTPUT), 'output_sha256': sha(OUTPUT),
                      'hinge_families': list(angle_report)}, sort_keys=True))


if __name__ == '__main__':
    main()
