"""Offline retained-fairway audit; optional separate, bounded bed candidate.

The extremum is evaluated at all vertices of corridor/native-triangle
intersections. The water-plane rule is shared with the V30 pieces: this checks
terrain against that design, not the loaded collision/boat consumer.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import shapely
from affine import Affine
from rasterio.features import rasterize
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
from shapely.geometry import LineString, Point, box, shape
from shapely.ops import substring

from v30_common import cell_planes, tri_sample

ROOT = Path(__file__).resolve().parents[2]
N = 2048
LIMITS = dict(width_m=24.0, depth_m=3.0, tolerance_m=0.01,
              sea_min_m=0.5, endpoint_margin_m=24.0, narva_exclusion_m=620.0,
              repair_target_m=3.05, max_lowering_m=1.0, bed_floor_m=-12.0)
NARVA = (2417.1428225906, 6889.8850822322)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def weights_at(triangles, points):
    # General barycentric linear solve, independent of tri_sample's formula.
    matrix = np.concatenate([triangles.transpose(0, 2, 1),
                             np.ones((len(triangles), 1, 3))], axis=1)
    target = np.column_stack([points, np.ones(len(points))])
    weights = np.linalg.solve(matrix, target[..., None])[..., 0]
    if np.any(weights < -1e-7) or not np.allclose(weights.sum(1), 1, atol=1e-8):
        raise ValueError('Intersection coordinate outside its native triangle')
    return weights


def records(corridor, planes):
    touched = rasterize([(corridor, 1)], out_shape=(N-1, N-1),
                        transform=Affine(6, 0, 0, 0, -6, 12282),
                        all_touched=True, dtype='uint8')
    rows, cols = np.nonzero(touched)
    rc = np.stack([np.column_stack([rows, cols]),
                   np.column_stack([rows, cols+1]),
                   np.column_stack([rows+1, cols]),
                   np.column_stack([rows+1, cols+1])], axis=1)
    verts = np.concatenate([rc[:, [0, 1, 3]], rc[:, [0, 2, 3]]])
    rr, cc = np.tile(rows, 2), np.tile(cols, 2)
    xyz = np.stack([verts[:, :, 1]*6.0, 12282-verts[:, :, 0]*6.0], axis=2)
    clipped = shapely.intersection(shapely.polygons(xyz), corridor)
    keep = shapely.area(clipped) > 1e-9
    verts, rr, cc, xyz, clipped = verts[keep], rr[keep], cc[keep], xyz[keep], clipped[keep]
    pts, owner = shapely.get_coordinates(clipped, return_index=True)
    weights = weights_at(xyz[owner], pts)
    vertex_ids = verts[owner, :, 0]*N + verts[owner, :, 1]
    level = planes[rr[owner], cc[owner]]
    level = np.maximum(np.nan_to_num(level, nan=-np.inf), LIMITS['sea_min_m'])
    return dict(ids=vertex_ids, weights=weights, xz=pts, level=level,
                face=owner, faces=len(verts), cell_rc=np.column_stack([rr[owner], cc[owner]]))


def depths(h, rec):
    return rec['level'] - np.sum(h.ravel()[rec['ids']]*rec['weights'], axis=1)


def describe(h, rec):
    d = depths(h, rec)
    bad = d < LIMITS['depth_m']-LIMITS['tolerance_m']
    k = int(np.argmin(d))
    return dict(faces=rec['faces'], intersection_vertices=len(d),
                failing_faces=int(np.unique(rec['face'][bad]).size),
                min_depth_m=float(d[k]), worst_xz=rec['xz'][k].tolist(),
                worst_cell_rc=rec['cell_rc'][k].tolist())


def controls(h, rec):
    # Analytic affine plane must be reproduced by both triangle halves.
    rows = np.arange(N)[:, None]; cols = np.arange(N)[None, :]
    plane = (0.007*(6*cols) - 0.003*(12282-6*rows) + 2.1)
    got = np.sum(plane.ravel()[rec['ids']]*rec['weights'], axis=1)
    expected = .007*rec['xz'][:, 0] - .003*rec['xz'][:, 1] + 2.1
    assert np.max(np.abs(got-expected)) < 1e-8
    # Compare identical stored heights with float64 arithmetic in both methods.
    # Otherwise float32 subtraction inside tri_sample adds an intermediate ULP.
    sample = tri_sample(h.astype(float), rec['xz'][:, 0], rec['xz'][:, 1])
    independent = np.sum(h.ravel()[rec['ids']]*rec['weights'], axis=1)
    assert np.max(np.abs(sample-independent)) < 1e-7
    # A raised, previously well-submerged face must be rejected.
    d = depths(h, rec)
    index = int(np.argmax(d))
    shallow = h.copy()
    shallow.ravel()[rec['ids'][index]] = rec['level'][index] - .5
    assert depths(shallow, rec)[index] < 1.0
    return dict(affine_max_error_m=float(np.max(np.abs(got-expected))),
                sampler_max_difference_m=float(np.max(np.abs(sample-independent))),
                shallow_obstacle_rejected=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--terrain', type=Path, default=ROOT/'tests/terrain_v30/terrain_v30.npz')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--candidate', type=Path)
    ap.add_argument('--max-lowering-m', type=float, default=1.0,
                    help='Explicit bound for the separately planned offline candidate')
    ap.add_argument('--design', type=Path, default=ROOT/'tests/water_v3',
                    help='Water design folder (navigable_samples.npz, water_v3.geojson)')
    args = ap.parse_args()
    if not np.isfinite(args.max_lowering_m) or args.max_lowering_m <= 0:
        raise ValueError('Finite positive lowering bound required')
    LIMITS['max_lowering_m'] = args.max_lowering_m
    args.out.mkdir(parents=True, exist_ok=True)
    if (args.out/'audit.json').exists() or (args.candidate and args.candidate.exists()):
        raise ValueError('Preserve existing evidence/candidate')
    terrain = np.load(args.terrain)
    h = terrain['heights'].astype(float)
    assert h.shape == (N, N) and np.isfinite(h).all()
    planes = cell_planes(terrain['cls'], terrain['level'].astype(float))
    source = args.design/'navigable_samples.npz'
    design = args.design/'water_v3.geojson'
    samples = np.load(source)
    features = json.loads(design.read_text(encoding='utf-8'))['features']
    approved = {f['properties'].get('id'): shape(f['geometry']) for f in features
                if f['properties']['class'] == 'navigable'}
    domain = box(1e-6, 1e-6, 12282-1e-6, 12282-1e-6)
    domain = domain.difference(Point(NARVA).buffer(LIMITS['narva_exclusion_m'], quad_segs=256))
    reports, all_records, corridor_features = [], {}, []
    for name in samples.files:
        if name not in approved:
            continue
        line = LineString(samples[name][:, 1:3])
        margin = LIMITS['endpoint_margin_m']
        if line.length <= 2*margin:
            reports.append(dict(river=name, excluded='Too short for the preserved endpoint margin', length_m=line.length))
            continue
        corridor = substring(line, margin, line.length-margin).buffer(12, cap_style='flat', join_style='round', quad_segs=32)
        corridor = corridor.intersection(domain)
        if corridor.is_empty or corridor.area < 1e-6:
            reports.append(dict(river=name, excluded='Outside map or in preserved Narva zone', length_m=line.length))
            continue
        rec = records(corridor, planes)
        all_records[name] = rec
        report = dict(river=name, area_m2=float(corridor.area),
                      outside_own_approved_polygon_m2=float(corridor.difference(approved[name]).area), **describe(h, rec))
        reports.append(report)
        corridor_features.append(dict(type='Feature', properties={'river': name}, geometry=shapely.geometry.mapping(corridor)))
        print(json.dumps(report), flush=True)
    assert all_records, 'Empty audit is not a pass'
    checks = {name: controls(h, rec) for name, rec in all_records.items()}
    result = dict(status='FAIL' if any(r.get('failing_faces', 0) for r in reports) else 'PASS_SCOPED_CORRIDORS',
                  limits=LIMITS, inputs={str(p): sha(p) for p in [args.terrain, source, design, Path(__file__)]},
                  method='Exact intersection extrema on each native triangle; polygon buffer approximates circular joins.',
                  exclusions=['24 m per retained axis endpoint; short pieces excluded', 'Narva within 620 m',
                              'Outside native vertex extent', 'Historical Delta Neva axes discarded in V3; new delta not certified'],
                  limitations=['Offline geometry, not boat motion/collision or engine water rendering.',
                               'Water planes follow the existing V30 cell rule; no new engine verification.'],
                  rivers=reports, controls=checks)
    save(args.out/'audit.json', result)
    save(args.out/'corridors.geojson', dict(type='FeatureCollection', features=corridor_features))
    if not args.candidate:
        return 2 if result['status'] == 'FAIL' else 0
    mutable = terrain['water'] & ~terrain['platform'] & ~terrain['narva']
    constraint_ids, constraint_weights, deficits = [], [], []
    for rec in all_records.values():
        d = depths(h, rec)
        bad_faces = np.unique(rec['face'][d < LIMITS['depth_m']-LIMITS['tolerance_m']])
        take = np.isin(rec['face'], bad_faces)
        deficit = LIMITS['repair_target_m']-d[take]
        need = deficit > 0
        constraint_ids.append(rec['ids'][take][need])
        constraint_weights.append(rec['weights'][take][need])
        deficits.append(deficit[need])
    ids, weights, demand = np.concatenate(constraint_ids), np.concatenate(constraint_weights), np.concatenate(deficits)
    if not len(demand):
        save(args.out/'candidate.json', dict(status='NOT_NEEDED'))
        return 0
    variables = np.unique(ids[mutable.ravel()[ids]])
    lookup = np.full(N*N, -1, dtype=np.int32); lookup[variables] = np.arange(len(variables))
    columns = lookup[ids]; eligible = columns >= 0
    rows = np.broadcast_to(np.arange(len(ids))[:, None], ids.shape)
    matrix = coo_matrix((weights[eligible], (rows[eligible], columns[eligible])),
                        shape=(len(ids), len(variables))).tocsr()
    bounds = np.column_stack([np.zeros(len(variables)),
                              np.minimum(LIMITS['max_lowering_m'], h.ravel()[variables]-LIMITS['bed_floor_m'])])
    solve = linprog(np.ones(len(variables)), A_ub=-matrix, b_ub=-demand, bounds=bounds, method='highs')
    if not solve.success:
        save(args.out/'candidate.json', dict(status='INFEASIBLE_UNPROMOTED', reason=solve.message,
                                           variables=len(variables), constraints=len(demand)))
        return 2
    candidate = h.copy(); candidate.ravel()[variables] -= solve.x
    candidate = candidate.astype('float32')
    changed = np.flatnonzero(candidate.ravel() != terrain['heights'].ravel())
    assert np.all(mutable.ravel()[changed]) and len(changed) > 0
    assert np.min(candidate) >= LIMITS['bed_floor_m']-1e-6
    after = {name: describe(candidate, rec) for name, rec in all_records.items()}
    assert all(r['failing_faces'] == 0 for r in after.values()), 'Candidate fails its corridor scope'
    args.candidate.parent.mkdir(parents=True, exist_ok=True)
    with args.candidate.open('xb') as stream:
        np.savez_compressed(stream, **{k: candidate if k == 'heights' else terrain[k] for k in terrain.files})
    readback = np.load(args.candidate)
    assert np.array_equal(readback['heights'], candidate)
    assert all(np.array_equal(readback[k], terrain[k], equal_nan=True) for k in terrain.files if k != 'heights')
    repair = dict(status='OFFLINE_CANDIDATE_NOT_DEPLOYED', file=str(args.candidate), sha256=sha(args.candidate),
                  vertices_changed=len(changed), max_lowering_m=float(np.max(h-candidate)),
                  invariants=dict(all_non_height_arrays_identical=True, only_water_not_road_or_narva=True),
                  changes=[dict(row=int(i//N), col=int(i%N), x=float(i%N*6), z=float(12282-i//N*6),
                                before=float(h.ravel()[i]), after=float(candidate.ravel()[i])) for i in changed],
                  rivers=after, controls={name: controls(candidate, rec) for name, rec in all_records.items()})
    save(args.out/'candidate.json', repair)
    print(json.dumps({k: repair[k] for k in ('status', 'vertices_changed', 'max_lowering_m', 'sha256')}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
