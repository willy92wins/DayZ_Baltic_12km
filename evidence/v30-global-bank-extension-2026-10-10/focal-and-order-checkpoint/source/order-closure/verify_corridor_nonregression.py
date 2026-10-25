"""Fresh incremental verdict; preserve the original sector FAIL and open P9 gaps."""
from pathlib import Path
import copy
import hashlib
import json
import math
import argparse

HERE = Path(__file__).resolve().parent
RS = HERE.parent
RAW = HERE / 'consumer-run-01/review.json'
RAW_SHA = 'a9112811a7d23fee0fe94735683174d3d3f67e2200a7519b7633c247b82b10fa'
CANDIDATE = HERE / 'author-run-01/candidate-local.npz'
CANDIDATE_SHA = 'ec1df1c7749fe478f4d5fc943acdc74bb498d68123bf568d07f5aa4d88ae21ba'
OPEN_UNKNOWN = {'Narva_23': 238.74576643431396, 'Luga_0': 752.2621866095913}
GATE_NAMES = set('''P_F_SEA_signs_and_crossings_within_1m
affected_known_P_corridor_depth_ge_0_95m
all_corridor_geometry_covered
bank_interior_p99_and_bracket_counts_nonworse
civil_source_cells_rebuilt_and_fixed
consumer_source_stable
continuation_lineage_exact
fixed_water_civil_P9_exact_B
float32_order_closure_bounds_D8_and_budget
global_slope_and_hinge_nonregression
high_navigable_bed_floor_1m
independent_order_projection_and_receipt_exact
no_new_local_minima
objective_strictly_reduced
pbo_wrp_deployed_identity_stable
physical_bounds_and_float32_admm_kkt
reconstructed_variable_domain_exact
selected_seed_improved
solver_resource_limits
source_readset_stable'''.splitlines())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def evaluate(report):
    require(report['status'] == 'FAIL_ORDER_CLOSURE_SECTOR_OFFLINE', 'preserve original FAIL')
    gates = report['gates']
    require(set(gates) == GATE_NAMES, 'gate inventory changed')
    require(gates['all_corridor_geometry_covered'] is False, 'unexpected original failed gate')
    require(all(v is True for k, v in gates.items() if k != 'all_corridor_geometry_covered'), 'additional original gate failed')
    info = report['information']
    b, h = (info['corridor_depth'][s] for s in ('B', 'H'))
    require(b == h, 'corridor surfaces or metrics differ between B and H')
    require(b['feature_count'] == 19 and len(b['corridors']) == 19, 'corridor population differs')
    require(len({r['id'] for r in b['corridors']}) == 19, 'duplicate corridor ID')
    require(b['all_covered'] is False and b['meets_0_95_everywhere'] is True, 'unexpected baseline condition')
    unknown = {}
    for row in b['corridors']:
        for key in ('area_m2', 'covered_area_m2', 'coverage_error_m2', 'minimum_nominal_depth_m',
                    'unknown_P_area_m2', 'unknown_P_area_changed_between_pair_m2',
                    'unknown_P_area_exact_between_pair_m2', 'unknown_P_max_triangle_vertex_delta_m'):
            require(finite(row[key]) and row[key] >= 0, f'invalid corridor metric {key}')
        require(row['area_m2'] > 0 and row['native_triangles'] > 0, 'empty corridor geometry')
        error = abs(row['covered_area_m2'] - row['area_m2'])
        require(error <= 1e-5 and error == row['coverage_error_m2'], 'geometric coverage changed')
        require(row['minimum_nominal_depth_m'] >= 0.95, 'insufficient known nominal depth')
        require(row['unknown_P_area_changed_between_pair_m2'] == 0.0
                and row['unknown_P_max_triangle_vertex_delta_m'] == 0.0
                and row['unknown_P_area_exact_between_pair_m2'] == row['unknown_P_area_m2'], 'unknown-P terrain changed')
        require(row['full_P_coverage'] is (row['unknown_P_area_m2'] <= 1e-9), 'P availability flag inconsistent')
        if row['unknown_P_area_m2'] > 0:
            unknown[row['id']] = row['unknown_P_area_m2']
    require(unknown == OPEN_UNKNOWN, 'historical P availability footprint differs')
    require(b['global_minimum_nominal_depth_m'] == min(r['minimum_nominal_depth_m'] for r in b['corridors']), 'minimum depth summary differs')
    affected = info['affected_corridor_depth']
    require(affected['pass'] is True and affected['features_with_affected_known_support'] == 0
            and affected['tested_known_triangles'] == 0
            and affected['unknown_area_in_changed_corridor_support_m2'] == 0.0, 'corridor support affected')
    require(len(affected['by_feature']) == 19, 'affected support population differs')
    for row in affected['by_feature']:
        require(row['affected_known_area_m2'] == 0 and row['affected_known_triangles'] == 0
                and row['affected_unknown_P_area_m2'] == 0 and row['triangles'] == [], 'affected corridor triangle')
    require(report['source_hashes_start'] == report['source_hashes_end'], 'source readset drift')
    require(info['artifact_hashes_start'] == info['artifact_hashes_end'], 'artifact drift')
    return {**{k: v for k, v in gates.items() if k != 'all_corridor_geometry_covered'},
            'all_19_corridor_geometries_covered': True,
            'all_known_nominal_depths_at_least_0_95m': True,
            'historical_unknown_P_triangle_surfaces_exact': True,
            'no_changed_corridor_support': True}


def fixtures(report):
    evaluate(report)
    mutations = [
        lambda r: r['gates'].__setitem__('no_new_local_minima', False),
        lambda r: r['information']['corridor_depth']['H']['corridors'][0].__setitem__('unknown_P_max_triangle_vertex_delta_m', 1e-9),
        lambda r: r['information']['corridor_depth']['B']['corridors'][0].__setitem__('minimum_nominal_depth_m', 0.949),
        lambda r: r['information']['corridor_depth']['H']['corridors'][0].__setitem__('coverage_error_m2', 0.001),
        lambda r: r['information']['corridor_depth']['H']['corridors'][0].__setitem__('unknown_P_area_m2', 1),
        lambda r: r['information']['corridor_depth']['H']['corridors'][0].__setitem__('id', 'invalid'),
        lambda r: r['information']['affected_corridor_depth'].__setitem__('tested_known_triangles', 1),
    ]
    for mutate in mutations:
        bad = copy.deepcopy(report)
        mutate(bad)
        try:
            evaluate(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('negative accepted')
    return len(mutations)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    require(args.run and args.report is not None, 'explicit --run --report required')
    require(not args.report.exists(), 'fresh output only')
    require(sha(RAW) == RAW_SHA and sha(CANDIDATE) == CANDIDATE_SHA, 'frozen evidence identity changed')
    raw = json.loads(RAW.read_text(encoding='utf-8'))
    gates = evaluate(raw)
    negatives = fixtures(raw)
    readset = dict(raw['source_hashes_start'])
    info = raw['information']
    artifacts = {'preflight': RS/'preflight-run-03-continuation/preflight.json',
                 'prepared': RS/'preflight-run-03-continuation/prepared.npz',
                 'solve03_rejected_result': RS/'solve-run-03-continuation/solve-result.json',
                 'solver_state': RS/'solve-run-03-continuation/solver-state.npz',
                 'order_closure_receipt': HERE/'author-run-01/receipt.json',
                 'candidate_local': CANDIDATE}
    require(set(artifacts) == set(info['artifact_hashes_start']), 'artifact set differs')
    readset.update({str(p): info['artifact_hashes_start'][k] for k, p in artifacts.items()})
    readset[str(RAW)] = RAW_SHA
    readset[str(HERE/'verify_order_closure.py')] = raw['consumer_sha256']
    readset[str(Path(__file__).resolve())] = sha(__file__)
    readset[str(HERE/'PLAN_CORRIDOR_NONREGRESSION.md')] = sha(HERE/'PLAN_CORRIDOR_NONREGRESSION.md')
    require({p: sha(p) for p in readset} == readset, 'live input/artefact/source drift')
    output = {'schema': 'ev93.order-closure-incremental-nonregression.v1',
              'status': 'PASS_ORDER_CLOSURE_INCREMENTAL_NONREGRESSION',
              'scope': 'same local candidate and actual measured corridor records; no geometry rerun, EV93 composition, build, native or visual acceptance',
              'global_contract_status': 'OPEN_INHERITED_MAP_DEFECTS',
              'p9_status': 'OPEN_INHERITED_P9_COVERAGE', 'open_unknown_P_area_m2': OPEN_UNKNOWN,
              'original_report_path': str(RAW), 'original_report_sha256': RAW_SHA,
              'original_status': raw['status'], 'original_failed_gate_preserved': 'all_corridor_geometry_covered',
              'candidate_path': str(CANDIDATE), 'candidate_sha256': CANDIDATE_SHA,
              'gates': gates, 'negative_controls_rejected': negatives,
              'source_path': str(Path(__file__).resolve()), 'source_sha256': sha(__file__),
              'source_read_set': readset}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(output, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({'status': output['status'], 'gates': len(gates), 'sha256': sha(args.report)}))


if __name__ == '__main__':
    main()
