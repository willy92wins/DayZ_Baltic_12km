"""Read-only reference diagnostic; never grants Baltic acceptance."""
import argparse
import json
import math
from pathlib import Path

HEIGHT = .801
BINDING = .011
ENDPOINT_XZ = 2.1


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def number(value):
    result = float(value)
    require(math.isfinite(result), 'Nonfinite number')
    return result


def vector(value):
    result = [number(x) for x in value.replace('<', '').replace('>', '').replace(',', ' ').split()]
    require(len(result) == 3, 'Vector arity')
    return result


def boolean(value):
    require(value in ('0', '1', 'false', 'true'), 'Boolean encoding')
    return value in ('1', 'true')


def distance(a, b, dimensions=(0, 1, 2)):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in dimensions))


def evaluate(text, anchors, probe_id):
    rows = [x.strip().split(';') for x in text.splitlines() if x.strip()]
    require(len(anchors) == 24 and len({a['id'] for a in anchors}) == 24, 'Anchor inventory')
    require(rows and len(rows[0]) == 5, 'Missing header')
    header = rows.pop(0)
    require(header[0] == 'CHERNARUS_NAV_HEIGHT_REFERENCE_V1' and header[1].lower() == 'chernarusplus', 'Wrong world/schema')
    require(header[2:] == [probe_id, '24', '49'], 'UUID/count mismatch')
    aborts = [row for row in rows if row[0] == 'FAIL']
    require(not aborts, 'Engine abort: ' + ';'.join(aborts[-1]) if aborts else '')
    require(rows and rows[-1] == ['END', '49'], 'Incomplete capture')
    rows.pop()
    expected = [(a, side) for a in anchors for side in ('left', 'right')] + [(anchors[0], 'negative')]
    cursor = 0
    results = []
    for anchor, side in expected:
        name = 'negative' if side == 'negative' else anchor['id'] + '_' + side
        require(cursor < len(rows), 'Missing anchor record')
        a = rows[cursor]; cursor += 1
        require(len(a) == 19 and a[:3] == ['A', name, anchor['id']], 'Anchor order/schema')
        require(a[3] == '1' and a[4] == anchor['shape'].lower(), 'Anchor uniqueness/model')
        expected_pos, actual_pos, origin, axis_x, axis_y, axis_z, raw_start, raw_goal = map(vector, a[5:13])
        require(distance(expected_pos, anchor['historical_position']) <= BINDING, 'Locator binding')
        require(distance(actual_pos, anchor['historical_position']) <= .05, 'Current object drift')
        require(distance(origin, actual_pos) <= BINDING, 'Object origin binding')
        scales = [distance(axis, [0, 0, 0]) for axis in (axis_x, axis_y, axis_z)]
        require(min(scales) > 0, 'Degenerate axes')
        determinant = sum(axis_x[i] * (axis_y[(i+1)%3]*axis_z[(i+2)%3]-axis_y[(i+2)%3]*axis_z[(i+1)%3]) for i in range(3))
        require(abs(determinant) > 1e-6, 'Degenerate transform')
        q = 6 if side == 'right' else -6
        for raw, z in ((raw_start, -6), (raw_goal, 6)):
            require(distance(raw, [origin[i]+q*axis_x[i]+z*axis_z[i] for i in range(3)]) <= BINDING, 'Model transform binding')
        start_ground, start_road, goal_ground, goal_road = map(number, a[13:17])
        require(cursor < len(rows), 'Missing query')
        row = rows[cursor]; cursor += 1
        require(len(row) == 10 and row[:2] == ['Q', name], 'Query order/schema')
        sa, sb, found = map(boolean, row[2:5])
        count = int(row[5]); require(0 <= count <= 100000, 'Waypoint count')
        start, goal, sampled_start, sampled_goal = map(vector, row[6:10])
        for point, raw, y in ((start, raw_start, start_road), (goal, raw_goal, goal_road)):
            require(distance(point, [raw[0], y+.2, raw[2]]) <= BINDING, 'Requested endpoint binding')
        require(not found or (sa and sb), 'Path without sampled endpoints')
        points = []
        for index in range(count):
            require(cursor < len(rows), 'Missing waypoint')
            row = rows[cursor]; cursor += 1
            require(len(row) == 7 and row[:3] == ['P', name, str(index)], 'Waypoint order/schema')
            nav, ground, road = map(vector, row[3:6])
            require(distance(nav, ground, (0, 2)) <= BINDING and distance(nav, road, (0, 2)) <= BINDING, 'Surface XZ binding')
            points.append(dict(index=index, nav=nav, ground=ground, road=road, surface=row[6], height_error_m=abs(nav[1]-road[1]), ground_error_m=abs(nav[1]-ground[1]), road_ground_m=road[1]-ground[1]))
        if side == 'negative':
            require(not sa and not sb and not found and count == 0 and sampled_start == sampled_goal == [0, 0, 0], 'NONE negative control failed')
            continue
        comparable = sa and sb and found and count >= 2
        endpoint_errors = None
        if comparable:
            endpoint_errors = [distance(sampled_start, start, (0, 2)), distance(sampled_goal, goal, (0, 2)), distance(points[0]['nav'], start, (0, 2)), distance(points[-1]['nav'], goal, (0, 2))]
            comparable = max(endpoint_errors) <= ENDPOINT_XZ
        violations = [p for p in points if p['height_error_m'] > HEIGHT]
        results.append(dict(name=name, family=anchor['family'], comparable=bool(comparable), sampled=[sa, sb], found=found, waypoint_count=count, endpoint_xz_errors_m=endpoint_errors, scales=scales, endpoint_surfaces=a[17:19], endpoint_road_ground_m=[start_road-start_ground, goal_road-goal_ground], violations=violations, points=points))
    require(cursor == len(rows), 'Unexpected/duplicate records')
    comparable = [r for r in results if r['comparable']]
    all_points = [p for r in comparable for p in r['points']]
    violations = [dict(query=r['name'], **p) for r in comparable for p in r['violations']]
    return dict(status='REFERENCE_HEIGHT_EXCEEDANCES' if violations else ('REFERENCE_NO_HEIGHT_EXCEEDANCES' if comparable else 'INCONCLUSIVE_NO_COMPARABLE_ROUTES'), acceptance_eligible=False, thresholds=dict(height_m=HEIGHT, binding_m=BINDING, endpoint_xz_m=ENDPOINT_XZ), query_count=49, none_control='PASS', comparable_routes=len(comparable), noncomparable_routes=48-len(comparable), height_exceedances=len(violations), max_height_error_m=max((p['height_error_m'] for p in all_points), default=None), raised_waypoints=sum(abs(p['road_ground_m']) > HEIGHT for p in all_points), violations=violations, routes=results, limits=['Read-only diagnostic; no Baltic acceptance or actor proof.', 'Endpoints use current SurfaceRoadY+.2; Baltic uses frozen offline roof/ground+.2.', 'Noncomparable routes and every sampled point are preserved.', 'No raised waypoints means raised-platform comparison is uncovered, not that general observations disappear.'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--anchors', type=Path, required=True)
    parser.add_argument('--probe-id', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = evaluate(args.log.read_text(encoding='utf-8-sig'), json.loads(args.anchors.read_text())['anchors'], args.probe_id)
    except (ValueError, KeyError, IndexError) as exc:
        result = dict(status='INCONCLUSIVE_INVALID_CAPTURE', acceptance_eligible=False, error=str(exc))
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('routes', 'violations')}))
    return 2 if result['status'].startswith('INCONCLUSIVE') else 0


if __name__ == '__main__':
    raise SystemExit(main())
