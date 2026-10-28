"""Offline full native shoreline inventory. Does not alter terrain or launch DayZ."""
import os
for _key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[_key] = '1'
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import LineString

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


shore = module('native_shore_producer', HERE.parent/'water/shore_ramp_v31.py')
verify = module('native_shore_consumer', HERE/'verify_native_shore_census_ev112.py')
patterns = module('native_shore_patterns', HERE/'shape_patterns_ev112.py')
PINS = {
    'terrain': '815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40',
    'footprint': '084171b0e29df5c220f9d5aab42a3dc683a2f70a07579f08cd930dfd109e716b',
    'original': '9d8caf0fb75d2bd34f71b877ecd3f71079898fbc01c28e67ddab0bf8dca50063',
    'candidate': '1e85c73f2232e4d5f60d7f745b7d7a1cabb3c878efb543a4f9146b517faf7c85',
}
OBSERVATIONS = [
    ('NARVA-VIS-01', (2391, 6941), 'native_candidate'),
    ('NARVA-VIS-02', (2391, 6941), 'road_model_not_evaluated'),
    ('NARVA-VIS-03', (2391, 6941), 'native_or_model_unresolved'),
    ('KIT118-VIS-01', (8253, 9038), 'model_not_evaluated'),
    ('KIT118-VIS-02', (8253, 9038), 'model_road_not_evaluated'),
    ('CONT65-VIS-01', (5162, 5865), 'model_not_evaluated'),
    ('ROAD49-RIVER-VIS-01', (5295.7, 5999.9), 'unknown'),
    ('CROSSING-VIS-01', (4789.51465, 5516.52197), 'road_model_not_evaluated'),
    ('RELIEF-EAST-VIS-01', (11790, 2400), 'native_candidate'),
]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(4 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def cross_key_endpoints(assembled):
    endpoints = [(i, side, item['pts'][side], int(item['keys'][side]))
                 for i, item in enumerate(assembled) if not item['closed'] for side in [0, -1]]
    if not endpoints:
        return []
    positions = np.array([item[2] for item in endpoints])
    pairs = cKDTree(positions).query_pairs(1e-6, output_type='ndarray')
    return [dict(chain_a=endpoints[a][0], side_a=endpoints[a][1], chain_b=endpoints[b][0],
                 side_b=endpoints[b][1], point=positions[a].tolist(),
                 key_a=endpoints[a][3], key_b=endpoints[b][3])
            for a, b in pairs if endpoints[a][0] != endpoints[b][0] and endpoints[a][3] != endpoints[b][3]]


def screen(assembled):
    """Cost-limited diagnostic only; exclusions are explicit, never empty PASS."""
    result = []
    pairs_left = 20_000_000
    for index, item in enumerate(assembled):
        started = time.monotonic()
        row = dict(chain=index, closed=item['closed'], closure_turn_evaluated=False,
                   segments=len(item['order']))
        points = item['pts'][:-1] if item['closed'] else item['pts']
        try:
            patterns.path_array(points)
            size = len(LineString(points).simplify(patterns.POLICY['simplification_m'], preserve_topology=False).coords)
            row['simplified_stations'] = size
            if size > 2048 or (size-1)**2 > pairs_left:
                row['status'] = 'NOT_EVALUATED_COST'
            else:
                pairs_left -= (size-1)**2
                row['metrics'] = patterns.route_screen(points)
                row['status'] = 'DIAGNOSTIC_FINDINGS' if row['metrics']['findings'] else 'NO_SCREEN_FINDING_NOT_ACCEPTANCE'
        except ValueError as error:
            row.update(status='DEGENERATE', reason=str(error))
        row['seconds'] = time.monotonic()-started
        result.append(row)
    return result


def bed_effect(h, original_path, candidate_path):
    with np.load(original_path, allow_pickle=False) as data:
        before = {key: data[key] for key in data.files}
    with np.load(candidate_path, allow_pickle=False) as data:
        after = {key: data[key] for key in data.files}
    verify.require(before.keys() == after.keys(), 'bed_field_keys')
    for key in before:
        verify.require(before[key].shape == after[key].shape and
                       np.isfinite(before[key]).all() and np.isfinite(after[key]).all(), 'bed_field_'+key)
    exact = {key: np.array_equal(before[key], after[key]) for key in before if key != 'bed'}
    exact['bed_xz'] = np.array_equal(before['bed'][:, :, [0, 2]], after['bed'][:, :, [0, 2]])
    verify.require(all(exact.values()), 'dry_candidate_invariant')
    output = dict(unchanged=exact, scope='All saved bed vertices including caps. Height difference is not rendered exposure.')
    for name, values in [('original', before), ('candidate', after)]:
        bed = values['bed'].reshape(-1, 3)
        verify.require(((bed[:, [0, 2]] >= 0) & (bed[:, [0, 2]] <= shore.ZTOP)).all(), 'bed_outside_terrain')
        delta = bed[:, 1]-shore.tri_h(h, bed[:, 0], bed[:, 2])
        output[name] = dict(vertices=len(bed), above_native_vertices=int((delta > 0).sum()),
                            delta_quantiles_m=np.quantile(delta, [0, .5, .9, .99, 1]).tolist())
    output['changed_y'] = int((before['bed'][:, :, 1] != after['bed'][:, :, 1]).sum())
    return output


def contexts(seg, assembled, h, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    assignments = np.empty(len(seg['p']), np.int32)
    for index, item in enumerate(assembled):
        assignments[item['order']] = index
    starts = seg['p'][:, 0]
    edges = seg['p'][:, 1]-starts
    squared = (edges*edges).sum(1)
    result = []
    plotted = set()
    for name, centre, domain in OBSERVATIONS:
        t = np.clip(((np.asarray(centre)-starts)*edges).sum(1)/np.where(squared > 0, squared, 1), 0, 1)
        nearest = starts+t[:, None]*edges
        distance = np.linalg.norm(nearest-np.asarray(centre), axis=1)
        ids = np.argsort(distance, kind='stable')
        selected = []
        seen = set()
        for sid in ids:
            cid = int(assignments[sid])
            if cid in seen:
                continue
            seen.add(cid)
            selected.append(dict(chain=cid, segment=int(sid), distance_m=float(distance[sid]), point=nearest[sid].tolist()))
            if len(selected) == 5:
                break
        image_name = f'context-{int(centre[0])}-{int(centre[1])}.png'
        result.append(dict(observation=name, approximate_review_position=list(centre), domain=domain,
                           association='UNCONFIRMED_CONTEXT_ONLY', nearest_native_chains=selected, plot=image_name))
        if image_name in plotted:
            continue
        plotted.add(image_name)
        x, z = centre
        lo, hi = np.maximum([x-220, z-220], 0), np.minimum([x+220, z+220], shore.ZTOP)
        mask = ((seg['p'].max(1) >= lo) & (seg['p'].min(1) <= hi)).all(1)
        r0 = max(0, int((shore.ZTOP-hi[1])//6)); r1 = min(shore.N, int((shore.ZTOP-lo[1])//6)+2)
        c0 = max(0, int(lo[0]//6)); c1 = min(shore.N, int(hi[0]//6)+2)
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.imshow(h[r0:r1, c0:c1], extent=[c0*6-3, (c1-1)*6+3, shore.ZTOP-(r1-1)*6-3, shore.ZTOP-r0*6+3],
                  cmap='terrain', interpolation='nearest', origin='upper')
        ax.add_collection(LineCollection(seg['p'][mask], colors='#0077ff', linewidths=1.2))
        ax.scatter([x], [z], marker='+', c='red', s=70, label='Review position, not defect location')
        ax.set(xlim=(lo[0], hi[0]), ylim=(lo[1], hi[1]), xlabel='X metres', ylabel='Z metres',
               title=name+'\nNative nominal shoreline; models not drawn', aspect='equal')
        ax.legend(fontsize=8)
        fig.tight_layout(); fig.savefig(output/image_name, dpi=140); plt.close(fig)
    return result


def run(paths, output):
    started = time.monotonic()
    output.mkdir(parents=True, exist_ok=False)
    source_files = [Path(__file__), HERE/'verify_native_shore_census_ev112.py',
                    HERE/'shape_patterns_ev112.py', HERE.parent/'water/shore_ramp_v31.py']
    pins = {str(path.resolve()): sha(path) for path in source_files}
    for key, path in paths.items():
        actual = sha(path)
        verify.require(actual == PINS[key], 'input_hash_'+key)
        pins[str(path.resolve())] = actual
    write_json(output/'inputs.json', pins)
    with np.load(paths['terrain'], allow_pickle=False) as data:
        h = data['heights'].astype(np.float64)
    with np.load(paths['footprint'], allow_pickle=False) as data:
        plane, field = data['plane'], data['field']
    verify.inputs(h, plane, field)
    verify.require(h.shape == (2048, 2048), 'production_grid_shape')
    water, pond = shore.corner_water(plane, field)
    parts = [shore.extract_segments(h, water, pond, plane, r0=row, r1=min(row+128, shore.NC))
             for row in range(0, shore.NC, 128)]
    seg = {key: np.concatenate([part[key] for part in parts]) for key in parts[0]}
    del parts, water, pond
    checked_segments = verify.segments(h, plane, field, seg)
    assembled = shore.chain(seg)
    checked_chains = verify.chains(seg, assembled)
    offsets = np.r_[0, np.cumsum([len(item['order']) for item in assembled])]
    point_offsets = np.r_[0, np.cumsum([len(item['pts']) for item in assembled])]
    np.savez_compressed(output/'native-shore.npz', **seg, chain_offsets=offsets,
                        chain_order=np.concatenate([item['order'] for item in assembled]),
                        point_offsets=point_offsets, chain_points=np.concatenate([item['pts'] for item in assembled]),
                        chain_keys=np.concatenate([item['keys'] for item in assembled]),
                        closed=np.array([item['closed'] for item in assembled]))
    # Validate the serialized consumer artifact, not only the live objects.
    with np.load(output/'native-shore.npz', allow_pickle=False) as saved:
        for key, value in seg.items():
            verify.require(np.array_equal(saved[key], value), 'serialized_segment_'+key)
        verify.require(np.array_equal(saved['chain_offsets'], offsets) and
                       np.array_equal(saved['point_offsets'], point_offsets), 'serialized_offsets')
        order_saved, points_saved = saved['chain_order'], saved['chain_points']
        keys_saved, closed_saved = saved['chain_keys'], saved['closed']
        restored = [dict(order=order_saved[offsets[i]:offsets[i+1]],
                         pts=points_saved[point_offsets[i]:point_offsets[i+1]],
                         keys=keys_saved[point_offsets[i]:point_offsets[i+1]],
                         closed=bool(closed_saved[i])) for i in range(len(assembled))]
        verify.chains(seg, restored)
    del restored
    features = [dict(type='Feature', properties=dict(chain=i, closed=item['closed'], segments=len(item['order'])),
                     geometry=dict(type='LineString', coordinates=item['pts'].tolist())) for i, item in enumerate(assembled)]
    write_json(output/'native-shore.geojson', dict(type='FeatureCollection',
               coordinate_system='Local X/Z metres, NOT geographic longitude/latitude', features=features))
    del features
    diagnostics = screen(assembled)
    write_json(output/'chain-diagnostics.json', diagnostics)
    cross_keys = cross_key_endpoints(assembled)
    write_json(output/'cross-key-open-endpoints.json', cross_keys)
    context = contexts(seg, assembled, h, output)
    write_json(output/'observations.json', context)
    bed = bed_effect(h, paths['original'], paths['candidate'])
    discontinuities, maximum_gap = shore.discontinuities(seg)
    verify.require(all(sha(path) == value for path, value in pins.items()), 'inputs_changed')
    report = dict(status='CENSO_DIAGNOSTICO_COMPLETO', map_acceptance=False,
                  cells=(shore.NC**2), faces=2*shore.NC**2,
                  segment_validation=checked_segments, chain_validation=checked_chains,
                  discontinuities=dict(shared_key_gaps=discontinuities, maximum_gap_m=maximum_gap),
                  coincident_open_ends_different_keys=len(cross_keys),
                  screen_status_counts={status: sum(row['status'] == status for row in diagnostics)
                                        for status in sorted({row['status'] for row in diagnostics})},
                  policy=patterns.POLICY, dry_bed_effect=bed, seconds=time.monotonic()-started,
                  limits=['Nominal native terrain/pond/sea only; no model occlusion.',
                          'Screens do not grant naturalness or visual PASS; closed turns not evaluated.',
                          'No bridge, road-water, collision, navigation or RAM acceptance.',
                          'Review positions only; screenshot-to-feature association unconfirmed.'])
    write_json(output/'report.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in PINS:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Output already exists; consumed run is never overwritten.')
    try:
        report = run({key: getattr(args, key) for key in PINS}, args.output)
        print(json.dumps(dict(status=report['status'], segments=report['segment_validation']['segments'], seconds=report['seconds'])))
    except Exception as error:
        if args.output.exists() and not (args.output/'report.json').exists():
            status = 'REJECTED' if isinstance(error, ValueError) else 'INCONCLUSO'
            write_json(args.output/'failure.json', dict(status=status, error_type=type(error).__name__, reason=str(error)))
        raise
