"""Check a complete engine log against points/routes frozen before generation.

No point is removed on a miss. Coverage, native height, and path gates are
reported separately; this is not an actor or multiplayer performance test.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / 'evidence/regional-outline-v3/nav-probe-reference.json'


def vector(text):
    value = [float(v) for v in text.strip('<> ').replace(',', ' ').split()]
    if len(value) != 3 or not all(math.isfinite(v) for v in value):
        raise ValueError('Invalid vector')
    return value


def boolean(text):
    if text not in ('true', 'false', '1', '0'):
        raise ValueError('Invalid boolean')
    return text in ('true', '1')


def check(log, reference):
    lines = [v.strip() for v in log.splitlines() if v.strip()]
    header=reference.get('header','BALTIC_OUTLINE_NAV_V3')
    complete=reference.get('complete','BALTIC_OUTLINE_NAV_COMPLETE')
    if lines[:3] != [header, 'world=BalticTrial', 'flags=1;50'] or lines[-1:] != [complete]:
        raise ValueError('Wrong header, world, filter or missing completion')
    samples, queries, paths = {}, {}, {}
    for line in lines[3:-1]:
        fields = line.split(';')
        kind = fields[0]
        if kind == 'D' and len(fields) == 5:
            index = int(fields[1])
            if index in samples:
                raise ValueError('Duplicate sample')
            samples[index] = (vector(fields[2]), boolean(fields[3]), vector(fields[4]))
        elif kind == 'Q' and len(fields) == 6:
            name = fields[1]
            if name in queries:
                raise ValueError('Duplicate query')
            queries[name] = ([boolean(v) for v in fields[2:5]], int(fields[5]))
        elif kind == 'P' and len(fields) == 4:
            name, index = fields[1], int(fields[2])
            if name not in queries or index != len(paths.get(name, [])):
                raise ValueError('Out of order path')
            paths.setdefault(name, []).append(vector(fields[3]))
        else:
            raise ValueError('Unknown or malformed record')
    expected_ids = {p['index'] for p in reference['points']}
    expected_routes = {p['name'] for p in reference['routes']} | {'negative'}
    if set(samples) != expected_ids or set(queries) != expected_routes or not set(paths) <= expected_routes:
        raise ValueError('Missing or extra points/routes')
    failures, groups, maximum_height_error = [], {}, 0
    for point in reference['points']:
        actual, found, sample = samples[point['index']]
        group = groups.setdefault(point['group'], {'total': 0, 'height_pass': 0, 'nav_pass': 0})
        group['total'] += 1
        if actual[0] != point['x'] or actual[2] != point['z']:
            raise ValueError('Requested coordinate differs from frozen point')
        err = abs(actual[1] - point['y'])
        maximum_height_error = max(maximum_height_error, err)
        height_ok = err <= reference['height_tolerance_m']
        nav_distance = math.dist(actual, sample)
        nav_ok = found and nav_distance <= reference['sample_radius_m'] + .002
        group['height_pass'] += int(height_ok)
        group['nav_pass'] += int(nav_ok)
        if not height_ok or not nav_ok:
            failures.append(dict(index=point['index'], group=point['group'], requested=actual,
                                 expected_y=point['y'], height_error_m=err, found=found,
                                 sampled=sample, sample_distance_m=nav_distance))
    route_results = []
    for route in reference['routes']:
        name = route['name']
        flags, count = queries[name]
        vertices = paths.get(name, [])
        if count != len(vertices):
            raise ValueError('Wrong path count')
        length = sum(math.dist(a, b) for a, b in zip(vertices, vertices[1:]))
        endpoints = bool(vertices) and math.dist(vertices[0], route['start']) <= 2 and math.dist(vertices[-1], route['end']) <= 2
        passed = all(flags) and count >= 2 and endpoints and length <= reference['path_max_length_factor'] * math.dist(route['start'], route['end'])
        route_results.append(dict(name=name, passed=bool(passed), flags=flags, count=count,
                                  endpoints_ok=bool(endpoints), length_m=length))
    negative_ok = queries['negative'] == ([False, False, False], 0) and not paths.get('negative')
    gates = dict(heights=all(g['height_pass'] == g['total'] for g in groups.values()),
                 coverage=all(g['nav_pass'] == g['total'] for g in groups.values()),
                 routes=all(v['passed'] for v in route_results), negative_filter=negative_ok)
    return dict(status='PASS_RUNTIME_SAMPLES_AND_PATHS' if all(gates.values()) else 'FAIL',
                gates=gates, groups=groups, sample_count=len(samples), max_height_error_m=maximum_height_error,
                sample_failures=failures, routes=route_results,
                limits=['Fixed samples and short graph paths only; no actors, full-area connectivity or player-load proof.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if hashlib.sha256(REFERENCE.read_bytes()).hexdigest() != '5314d14112f2bbbc70126fd1d34986b16a6b608d5376972bb3a609e3eaed0287':
        raise ValueError('Frozen reference changed')
    ref = json.loads(REFERENCE.read_text(encoding='utf-8'))
    data = args.log.read_bytes()
    try:
        result = check(data.decode('utf-8-sig'), ref)
    except (ValueError, IndexError, KeyError) as error:
        result = dict(status='FAIL', error=str(error))
    result.update(log=str(args.log), log_sha256=hashlib.sha256(data).hexdigest(),
                  reference_sha256=hashlib.sha256(REFERENCE.read_bytes()).hexdigest())
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'].startswith('PASS') else 1)


if __name__ == '__main__':
    main()
