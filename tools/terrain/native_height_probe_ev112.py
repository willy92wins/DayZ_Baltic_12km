"""Changed vertices and incident native triangle centroids, with bound evidence.

Uses the unchanged forest-boundary mission as a native SurfaceY producer.
This gate does not accept water, model collision, navigation or visual quality.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import uuid
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'vegetation'))
from eval_forest_boundary_probe_v31 import parse
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'water'))
from streambed_kit_v31 import tri_h


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def points_for_changes(before, after):
    a, b = np.asarray(before), np.asarray(after)
    if a.shape != b.shape or a.ndim != 2 or min(a.shape) < 2 or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('matching finite terrain grids required')
    changed = np.argwhere(a != b)
    if not len(changed):
        raise ValueError('no changed terrain vertices')
    points, cells = [], set()
    north = (b.shape[0] - 1) * 6
    for r, c in changed:
        points.append(dict(id=len(points), kind='changed_vertex', row=int(r), col=int(c),
                           x=int(c * 6), z=int(north - r * 6), ground=float(b[r, c])))
        for rr in (r - 1, r):
            for cc in (c - 1, c):
                if 0 <= rr < b.shape[0] - 1 and 0 <= cc < b.shape[1] - 1:
                    cells.add((int(rr), int(cc)))
    for r, c in sorted(cells):
        corners = [(float(b[r, c]), float(b[r, c + 1]), float(b[r + 1, c + 1])),
                   (float(b[r, c]), float(b[r + 1, c]), float(b[r + 1, c + 1]))]
        for triangle, (dx, dz) in enumerate(((4, 2), (2, 4))):
            points.append(dict(id=len(points), kind='incident_triangle', row=r, col=c, triangle=triangle,
                               x=c * 6 + dx, z=north - r * 6 - dz, ground=sum(corners[triangle]) / 3))
    return points


def csv_text(points):
    return ''.join(f"{p['id']};{p['x']:.9f} 0 {p['z']:.9f}\n" for p in points)


def verify_coverage(before, after, points):
    a, b = np.asarray(before), np.asarray(after)
    if a.shape != b.shape or a.ndim != 2 or min(a.shape) < 2 or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('invalid coverage terrain')
    delta = a != b
    vertices = set(map(tuple, np.argwhere(delta)))
    cells = delta[:-1, :-1] | delta[1:, :-1] | delta[:-1, 1:] | delta[1:, 1:]
    triangles = {(int(r), int(c), t) for r, c in np.argwhere(cells) for t in (0, 1)}
    got_vertices, got_triangles = set(), set()
    if not vertices or not points or [p['id'] for p in points] != list(range(len(points))):
        raise ValueError('empty or invalid coverage IDs')
    for p in points:
        r, c = p['row'], p['col']
        if type(r) is not int or type(c) is not int:
            raise ValueError('noninteger grid coordinate')
        if p['kind'] == 'changed_vertex':
            key = (r, c)
            if key not in vertices or key in got_vertices:
                raise ValueError('unexpected/duplicate changed vertex')
            got_vertices.add(key);dx, dz = 0, 0
        elif p['kind'] == 'incident_triangle':
            key = (r, c, p['triangle'])
            if type(p['triangle']) is not int or key not in triangles or key in got_triangles:
                raise ValueError('unexpected/duplicate incident triangle')
            got_triangles.add(key);dx, dz = ((4, 2), (2, 4))[p['triangle']]
        else:
            raise ValueError('unknown point kind')
        if p['x'] != c * 6 + dx or p['z'] != (b.shape[0] - 1 - r) * 6 - dz:
            raise ValueError('coordinate does not name the declared native point')
    if got_vertices != vertices or got_triangles != triangles:
        raise ValueError('missing changed vertex or incident triangle')
    x = np.array([p['x'] for p in points]);z = np.array([p['z'] for p in points]) + 12282 - (b.shape[0] - 1) * 6
    expected = tri_h(b.astype(float), x, z)
    supplied = np.array([p['ground'] for p in points])
    if not np.isfinite(supplied).all() or not np.allclose(expected, supplied, rtol=0, atol=1e-9):
        raise ValueError('expected height differs from independent native interpolation')
    return dict(changed_vertices=len(vertices), incident_cells=int(cells.sum()), incident_triangles=len(triangles), points=len(points))


def verify_binding(doc):
    if doc.get('schema') != 'ev112-native-height-v1' or not doc.get('points'):
        raise ValueError('missing native height manifest')
    if str(uuid.UUID(doc['survey_id'])) != doc['survey_id']:
        raise ValueError('noncanonical survey id')
    for category in ('inputs', 'packages', 'mission_hashes'):
        expected = doc.get(category)
        if not isinstance(expected, dict) or not expected:
            raise ValueError('empty identity: ' + category)
        for path, digest in expected.items():
            if not Path(path).is_absolute() or sha(path) != digest:
                raise ValueError('changed input: ' + path)
    mission = Path(doc['mission'])
    if set(doc['mission_hashes']) != {str(mission / n) for n in ('init.c', 'points.csv', 'identity.txt')}:
        raise ValueError('incomplete mission identity')
    producer = doc.get('producer')
    if producer not in doc['inputs'] or doc['inputs'][producer] != doc['mission_hashes'][str(mission / 'init.c')]:
        raise ValueError('mission producer differs from bound source')
    if {Path(p).name for p in doc['packages']} != {'narva_trial.pbo', 'baltic_water_v30.pbo', 'baltic_stream_pilot.pbo'} or len(doc['packages']) != 3:
        raise ValueError('incomplete package identity')
    if (mission / 'points.csv').read_text(encoding='ascii') != csv_text(doc['points']):
        raise ValueError('manifest/CSV mismatch')
    if (mission / 'identity.txt').read_text(encoding='ascii').strip() != doc['survey_id']:
        raise ValueError('mission survey mismatch')
    for key in ('terrain_before', 'terrain_after'):
        if doc.get(key) not in doc['inputs']:
            raise ValueError('unbound terrain: ' + key)
    with np.load(doc['terrain_before']) as a, np.load(doc['terrain_after']) as b:
        counts = verify_coverage(a['heights'], b['heights'], doc['points'])
    if counts != doc['counts']:
        raise ValueError('declared coverage count mismatch')


def judge(points, rows):
    if not points or [p['id'] for p in points] != list(range(len(points))) or set(rows) != set(range(len(points))):
        raise ValueError('incomplete or duplicate point coverage')
    failures = []
    maximum = 0.0
    for point in points:
        if point['kind'] not in ('changed_vertex', 'incident_triangle') or not all(math.isfinite(float(point[k])) for k in ('x', 'z', 'ground')):
            raise ValueError('invalid expected native point')
        measured = rows[point['id']]['ground']
        if not math.isfinite(measured):
            raise ValueError('nonfinite measured height')
        delta = abs(measured - point['ground'])
        maximum = max(maximum, delta)
        if delta > .01:
            failures.append(dict(id=point['id'], x=point['x'], z=point['z'], expected=point['ground'], measured=measured, delta_m=delta))
    return dict(status='FAIL' if failures else 'NATIVE_HEIGHT_SAMPLE_PASS', points=len(points), maximum_delta_m=maximum,
                failure_count=len(failures), failures=failures,
                limits=['Every changed source vertex and both centroids of each incident cell, not every point of the compiled surface.',
                        'No model collision, water, navigation, client or visual acceptance.'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('manifest', type=Path)
    ap.add_argument('log', type=Path)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    doc = json.loads(args.manifest.read_text(encoding='utf-8'))
    verify_binding(doc)
    rows = parse(args.log.read_text(encoding='utf-8-sig'), len(doc['points']), doc['survey_id'])
    result = judge(doc['points'], rows)
    result.update(manifest_sha256=sha(args.manifest), log_sha256=sha(args.log), survey_id=doc['survey_id'])
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'failures'}))
    raise SystemExit(result['status'] != 'NATIVE_HEIGHT_SAMPLE_PASS')


if __name__ == '__main__':
    main()
