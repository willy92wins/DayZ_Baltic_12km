"""Validate the frozen V30 native path consumer, including its NONE filter."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def vector(text):
    if not text.startswith('<') or not text.endswith('>'):
        raise ValueError('Bad vector syntax')
    values = [float(v) for v in text[1:-1].split(',')]
    if len(values) != 3 or not all(math.isfinite(v) for v in values):
        raise ValueError('Invalid vector')
    return values


def verify(reference, text):
    rows = text.splitlines()
    cases = {c['name']: c for c in reference['queries']}
    if rows[0] != 'BALTIC_V30_ACCEPTANCE_V1;BalticTrial' or rows[-1] != f'END;{len(cases)}':
        raise ValueError('Wrong world or incomplete consumer')
    queries, paths = {}, {}
    for line in rows[1:-1]:
        f = line.split(';')
        if f[0] == 'Q' and len(f) == 10 and f[1] not in queries:
            if any(v not in ('true', 'false') for v in f[2:5]):
                raise ValueError('Invalid boolean')
            queries[f[1]] = f
        elif f[0] == 'P' and len(f) == 6 and f[1] in queries:
            path = paths.setdefault(f[1], [])
            if int(f[2]) != len(path):
                raise ValueError('Nonsequential waypoints')
            path.append([vector(v) for v in f[3:]])
        else:
            raise ValueError('Duplicate or malformed record')
    if set(queries) != set(cases):
        raise ValueError('Query coverage differs from frozen reference')
    results = []
    for name, case in cases.items():
        f, p = queries[name], paths.get(name, [])
        checks = {'requested_start': math.dist(vector(f[6]), case['start']) < .01,
                  'requested_end': math.dist(vector(f[7]), case['end']) < .01,
                  'waypoint_count': int(f[5]) == len(p)}
        expectation = case.get('expect', 'none' if name == 'negative' else 'path')
        if expectation not in ('none', 'path', 'disconnected'):
            raise ValueError('Unknown path expectation')
        if expectation == 'none':
            checks['none_filter_rejected'] = f[2:5] == ['false'] * 3 and len(p) == 0
        elif expectation == 'disconnected':
            checks['both_land_endpoints_sampled'] = f[2:4] == ['true'] * 2
            checks['sampled_endpoints_near_request'] = math.dist(vector(f[8]), case['start']) <= 2.1 and math.dist(vector(f[9]), case['end']) <= 2.1
            checks['partial_starts_correctly'] = not p or math.dist(p[0][0], case['start']) <= 2.1
            checks['no_complete_walk'] = not p or math.dist(p[-1][0], case['end']) > 2.1
            checks['found_result_has_path'] = f[4] != 'true' or len(p) >= 2
        else:
            checks['found'] = f[2:5] == ['true'] * 3 and len(p) >= 2
            checks['complete_endpoints'] = len(p) >= 2 and math.dist(p[0][0], case['start']) <= 2.1 and math.dist(p[-1][0], case['end']) <= 2.1
        results.append({'name': name, 'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks,
                        'waypoints': len(p), 'length_m': sum(math.dist(a[0], b[0]) for a, b in zip(p, p[1:]))})
    return {'status': 'PASS_NATIVE_V30_PATHS' if all(r['status'] == 'PASS' for r in results) else 'FAIL_NATIVE_V30_PATHS',
            'cases': results, 'limits': reference['limits']}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--reference', type=Path, required=True)
    ap.add_argument('--log', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise ValueError('Preserve existing results')
    reference = json.loads(args.reference.read_text())
    result = verify(reference, args.log.read_text(encoding='utf-8-sig'))
    result['log_sha256'] = hashlib.sha256(args.log.read_bytes()).hexdigest()
    result['reference_sha256'] = hashlib.sha256(args.reference.read_bytes()).hexdigest()
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'].startswith('PASS') else 1)
