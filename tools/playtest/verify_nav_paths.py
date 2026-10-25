"""Verify server graph routes and independent roadway/navmesh samples at Narva."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def vec(value):
    if not value.startswith('<') or not value.endswith('>'):
        raise ValueError('Vector syntax')
    result = tuple(float(v.strip()) for v in value[1:-1].split(','))
    if len(result) != 3 or not all(math.isfinite(v) for v in result):
        raise ValueError('Nonfinite vector')
    return result


def verify(text):
    lines = text.splitlines()
    if lines[0] != 'BALTIC_NAV_PATHS_V1' or lines[-1] != 'BALTIC_NAV_PATHS_COMPLETE':
        raise ValueError('Incomplete observer')
    if lines[1:3] != ['world=BalticTrial', 'flags=1;50']:
        raise ValueError('Wrong world or measured walking filter')
    queries, points, samples = {}, {}, {}
    for line in lines[3:-1]:
        row = line.split(';')
        kind, label = row[:2]
        if kind == 'Q':
            if label in queries or len(row) != 10:
                raise ValueError('Duplicate/malformed query')
            queries[label] = row
        elif kind in ('P', 'R'):
            group = points if kind == 'P' else samples
            index = int(row[2])
            group.setdefault(label, {})
            if index in group[label]:
                raise ValueError('Duplicate sample')
            group[label][index] = row
        else:
            raise ValueError('Unexpected observer row')
    expected = {'west_local', 'east_local', 'west_east', 'east_west', 'negative_no_polygons'}
    if set(queries) != expected:
        raise ValueError('Missing or unexpected query')
    report = {}
    for label in expected - {'negative_no_polygons'}:
        row = queries[label]
        if row[4:6] != ['true', 'true'] or row[8] != 'true':
            raise ValueError(f'{label}: path or endpoint not found')
        count = int(row[9])
        pts = points.get(label, {})
        if count < 2 or set(pts) != set(range(count)):
            raise ValueError(f'{label}: incomplete waypoints')
        a, b = vec(row[6]), vec(row[7])
        if math.dist(a, vec(row[2])) > 2.001 or math.dist(b, vec(row[3])) > 2.001:
            raise ValueError(f'{label}: endpoint snapped too far')
        path = [vec(pts[i][3]) for i in range(count)]
        if math.dist(path[0], a) > 1 or math.dist(path[-1], b) > 1:
            raise ValueError(f'{label}: partial path')
        length = sum(math.dist(p, q) for p, q in zip(path, path[1:]))
        if length > (10 if label.endswith('local') else 90):
            raise ValueError(f'{label}: excessive detour')
        report[label] = {'waypoints': count, 'length_m': length}
        if label in ('west_east', 'east_west'):
            for x, y, z in path:
                lateral = (x-2417.143)*0.152104866 + (z-6889.885)*0.988364361
                if abs(lateral) > 2.5:
                    raise ValueError(f'{label}: path leaves bridge corridor')
            rows = samples.get(label, {})
            if set(rows) != set(range(61)):
                raise ValueError(f'{label}: missing roadway samples')
            bridge_y, errors = [], []
            for i in range(61):
                r = rows[i]
                if len(r) != 6 or r[4] != 'true':
                    raise ValueError(f'{label}/{i}: navmesh gap')
                requested, sampled = vec(r[3]), vec(r[5])
                delta = math.dist(requested, sampled)
                if delta > .801:
                    raise ValueError(f'{label}/{i}: navigation differs from roadway by {delta:.6f}m; local acceptance is 0.8m, not an asserted API radius contract')
                errors.append(delta)
                projection = (requested[0]-2417.143)*.988364361-(requested[2]-6889.885)*.152104866
                if abs(projection) <= 12.5:
                    if not 1.99 <= requested[1] <= 2.03 or not 1.7 <= sampled[1] <= 2.6:
                        raise ValueError(f'{label}/{i}: wrong bridge height')
                    bridge_y.append(sampled[1])
            if len(bridge_y) < 24:
                raise ValueError('Insufficient bridge coverage')
            report[label].update(samples=61, bridge_samples=len(bridge_y),
                                 nav_bridge_y_range_m=[min(bridge_y), max(bridge_y)],
                                 max_roadway_nav_distance_m=max(errors))
    neg = queries['negative_no_polygons']
    if neg[4:6] != ['false', 'false'] or neg[8:10] != ['false', '0'] or points.get('negative_no_polygons'):
        raise ValueError('Negative filter did not reject the route')
    return {'status': 'PASS_GRAPH_AND_SAMPLED_BRIDGE', 'routes': report,
            'negative_filter': 'PASS_NO_POLYGONS',
            'limits': ['Graph queries and surface samples only; no infected/animal traversal or CE/load test.']}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--log', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    args = ap.parse_args()
    raw = args.log.read_bytes()
    try:
        result = verify(raw.decode('utf-8-sig'))
    except ValueError as error:
        result = {'status': 'FAIL_NAVIGATION_ACCEPTANCE', 'reason': str(error),
                  'log_sha256': hashlib.sha256(raw).hexdigest(),
                  'limits': ['Read-only graph/surface probe; this does not establish an actor traversal failure.']}
        args.out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(result, indent=2))
        raise SystemExit(1)
    result['log_sha256'] = hashlib.sha256(raw).hexdigest()
    args.out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
