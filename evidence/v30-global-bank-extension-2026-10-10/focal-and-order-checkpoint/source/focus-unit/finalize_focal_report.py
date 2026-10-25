"""Close the gate aggregation defect using the preserved real consumer evidence.

Does not rerun geometry, alter the candidate, or treat the incomplete original
top-level PASS as complete acceptance. Numerical coverage is checked again here.
"""
from pathlib import Path
import copy
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
RAW = HERE / 'consumer-run-01/review.json'
OUT = HERE / 'consumer-run-01/acceptance-supplement.json'
RAW_SHA = 'b9af8d77c2efe342b02012af160a1f8cae44d41d5581be21045da8539116de7e'
CONSUMER_SHA = '5dff923cca7d519ca728c64e821b43c05685f542e1279a85cbd5ccc659557c0a'
CANDIDATE_SHA = '30d0ed33e477846297a17e758e34a51490d54ee809e8b63ec9d69229170d15a1'
MODEL_DIR = Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30')
TOP = set('''eligibility:semantic_protections_clear_except_nonprotective_actual_wet_mask
eligibility:single_node_exactly_within_ev79_budget_and_physical_floor
eligibility:candidate_below_or_equal_EV82_plus_0_5_cap
eligibility:float32_target_is_inside_reconstructed_inward_interval
shape:focus_positive_prominence_reduced_25pct_both_axes
shape:fixed_population_max_prominence_nonworse_both_axes
shape:fixed_population_sum_squares_prominence_nonworse_both_axes
shape:no_new_strict_minima8
shape:no_new_exactly_constant_2x2_windows
objective:strict_total_affected_stencil_plus_fidelity_cost_decrease
P_F_SEA_corner_signs_preserved
original_crossings_valid_and_shift_le_1m
water:unknown_compiled_faces_certified_buried_or_P9_exact
water:unknown_visible_faces_B_H_L32_strictly_above_2e-5m
water:zero_area_unknown_contacts_B_H_L32
water:strict_descent_below_zero_area_contact_bounds
water:contact_bound_and_index_identity_reconciled
terrain:no_new_D8_witness_minima
terrain:slopes_le_max_35deg_or_baseline
terrain:no_new_touched_hinge_over_30_0001deg
terrain:affected_sector_max_nonworse
terrain:existing_population_p99_nonworse
corridor_civil:no_P9_unknown_corridor_cell_corner_changed
corridor_civil:no_road_or_bridge_cell_intersection
corridor_civil:known_corridor_nominal_depth_at_least_0_95m
corridor_civil:high_navigable_bed_floor_1m_if_applicable
verification:local_checks_within_120s
verification:face_index_reverified_before_and_after'''.splitlines())
WATER = set('''no_changed_partial_F_triangles
unknown_F_changed_faces_absent_or_buried_in_B_and_H
no_new_or_worsened_compiled_face_height_violation
physical_nominal_footprint_supported_le_1e_7m2
physical_compiled_residual_outside_height_band_le_0_002m2
visible_nominal_footprint_supported_le_1e_7m2
visible_compiled_residual_outside_height_band_le_0_002m2
no_new_partial_or_unresolved_face_exposure'''.splitlines())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def bounded(v, maximum):
    return type(v) in (float, int) and math.isfinite(v) and 0 <= v <= maximum


def evaluate(report):
    top = report['gates']
    coverage = report['compiled_coverage']
    water = coverage['gates']
    if set(top) != TOP or set(water) != WATER:
        raise ValueError('missing or unexpected gate')
    if any(v is not True for v in [*top.values(), *water.values()]):
        raise ValueError('one or more gates failed or are not boolean true')
    if report['candidate_sha256'] != CANDIDATE_SHA or report['changed_vertices'] != [[840, 370]]:
        raise ValueError('candidate/support differs')
    if coverage['scanned_cells'] != 4 or coverage['changed_support_cells'] != 4:
        raise ValueError('focal support differs')
    for layer in ('physical', 'visible'):
        metrics = coverage['metrics'][layer]
        for key in ('support_hole_total_m2', 'support_hole_max_cell_m2'):
            if set(metrics[key]) != {'B', 'H'} or not all(bounded(v, 1e-7) for v in metrics[key].values()):
                raise ValueError('unsupported nominal water footprint')
        for state in ('B', 'H'):
            residual = metrics[f'exposure_residual_{state}']
            for kind in ('missing', 'growth'):
                for extent in ('total', 'max_cell'):
                    if not bounded(residual[f'{kind}_outside_band_{extent}_m2'], 0.002):
                        raise ValueError('compiled exposure outside accepted band')
        if metrics['height_violation_count'] != {'B': 0, 'candidate': 0}:
            raise ValueError('focal has compiled height violations')
    unknown = coverage['unknown_F']
    intersections = coverage['unknown_face_intersections']
    if unknown['changed_partial'] != 0:
        raise ValueError('changed partial F')
    if (intersections['with_contact_or_exposed_or_unproven_intersection'] != 0
            or intersections['uncertain_examples']
            or intersections['no_visible_face_intersection'] + intersections['with_face_all_intersections_buried']
            != intersections['changed_all_nan_triangles']
            or intersections['changed_all_nan_triangles'] != unknown['changed_all_nan']):
        raise ValueError('unresolved unknown face')
    for state in ('B', 'candidate'):
        if not bounded(intersections[f'minimum_ground_minus_face_{state}_m'], 1e6):
            raise ValueError('unknown visible face not buried')
    violations = coverage['face_violation_nonregression']
    if (violations['pass'] is not True or violations['baseline_count'] != 0
            or violations['candidate_count'] != 0 or violations['new_or_worsened']):
        raise ValueError('compiled face regression')
    if report['input_hashes_start'] != report['input_hashes_end']:
        raise ValueError('original readset drift')
    return {**top, **{f'water:{k}': v for k, v in water.items()}}


def negative_controls(report):
    rejected = 0
    for key in WATER:
        for mutation in ('false', 'missing'):
            bad = copy.deepcopy(report)
            if mutation == 'false':
                bad['compiled_coverage']['gates'][key] = False
            else:
                del bad['compiled_coverage']['gates'][key]
            try:
                evaluate(bad)
            except ValueError:
                rejected += 1
            else:
                raise AssertionError(f'false acceptance: {key}/{mutation}')
    for layer in ('physical', 'visible'):
        for metric in ('support', 'residual'):
            bad = copy.deepcopy(report)
            target = bad['compiled_coverage']['metrics'][layer]
            if metric == 'support':
                target['support_hole_total_m2']['H'] = 1.0001e-7
            else:
                target['exposure_residual_H']['growth_outside_band_total_m2'] = 0.002001
            try:
                evaluate(bad)
            except ValueError:
                rejected += 1
            else:
                raise AssertionError(f'false numerical acceptance: {layer}/{metric}')
    return rejected == 20


def main():
    if OUT.exists():
        raise FileExistsError('fresh supplement only')
    if sha(RAW) != RAW_SHA or sha(HERE / 'verify_focus_1981.py') != CONSUMER_SHA:
        raise ValueError('frozen evidence identity changed')
    report = json.loads(RAW.read_text(encoding='utf-8'))
    gates = evaluate(report)
    if not negative_controls(report):
        raise AssertionError('negative controls incomplete')
    readset = dict(report['input_hashes_start'])
    if len(readset) != 33 or len(report['model_hashes_read']) != 8:
        raise ValueError('readset inventory differs')
    for name, digest in report['model_hashes_read'].items():
        readset[str(MODEL_DIR / name)] = digest
    readset[str(RAW)] = RAW_SHA
    readset[str(Path(__file__).resolve())] = sha(__file__)
    actual = {p: sha(p) for p in readset}
    if actual != readset:
        raise ValueError('live source/model/artefact hash mismatch')
    output = {
        'schema': 'ev93.focal-acceptance-supplement.v1',
        'status': 'PASS_FOCAL_DELTA_OFFLINE_COMPLETE_GATESET',
        'scope': 'single focal delta offline only; no native, visual or full map acceptance',
        'map_status': 'OPEN_INHERITED_MAP_DEFECTS',
        'candidate_sha256': CANDIDATE_SHA,
        'focal_report_path': str(RAW), 'focal_report_sha256': RAW_SHA,
        'original_consumer_sha256': CONSUMER_SHA,
        'original_defect': 'All eight compiled coverage gates executed and were recorded but omitted from the top-level status aggregation. Original source and evidence preserved.',
        'gates': gates,
        'additional_checks': {'coverage_numeric_predicates_reconstructed': True,
            'all_36_gate_names_and_boolean_results_checked': len(gates) == 36,
            'original_before_after_readsets_identical': True,
            'all_33_sources_and_8_models_rehashed': True,
            '20_negative_controls_rejected': True},
        'source_path': str(Path(__file__).resolve()), 'source_sha256': sha(__file__),
        'source_read_set': readset,
        'no_new_geometry_execution': True,
    }
    with OUT.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(output, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({'status': output['status'], 'gates': len(gates), 'sha256': sha(OUT)}))


if __name__ == '__main__':
    main()
