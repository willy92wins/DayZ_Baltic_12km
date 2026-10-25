"""Check the pre-load site's runtime observations against frozen independent ASC samples."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re


def vector(text):
    if not re.fullmatch(r'<-?\d+\.\d{6},\s*-?\d+\.\d{6},\s*-?\d+\.\d{6}>', text):
        raise ValueError('Precise vector required')
    result = [float(x) for x in text[1:-1].split(',')]
    if not all(map(math.isfinite, result)):
        raise ValueError('Nonfinite vector')
    return result


def verify(text, reference):
    lines = text.splitlines()
    if len(reference['points']) != 101 or len(reference['heights']) != 101:
        raise ValueError('Frozen site count differs')
    if len(lines) != 103 or lines[0] != 'BALTIC_FOUNDATION_LOAD_SITES_V1' or lines[-1] != 'END;true':
        raise ValueError('Wrong header, incomplete sites or failed terminal')
    errors = []
    height_errors = []
    distances = []
    for index, line in enumerate([*lines[2:-1], lines[1]]):
        fields = line.split(';')
        goal = index == 100
        if goal:
            if len(fields) != 5 or fields[0] != 'G':
                raise ValueError('Malformed goal')
            _, position, ground_text, found, sampled = fields
        else:
            if len(fields) != 8 or fields[:2] != ['S', str(index)]:
                raise ValueError('Missing, duplicated or reordered site')
            _, _, position, ground_text, found, sampled, path, count = fields
            if path != 'true' or not count.isdigit() or int(count) < 2:
                errors.append(f'{index}:no_path')
        p, nav = vector(position), vector(sampled)
        ground = float(ground_text)
        if not math.isfinite(ground):
            raise ValueError('Nonfinite ground')
        x, z = reference['points'][index]
        if abs(p[0]-x) > 0.000002 or abs(p[2]-z) > 0.000002:
            errors.append(f'{index}:wrong_site')
        if abs(p[1]-ground-0.05) > 0.00002:
            errors.append(f'{index}:query_height')
        delta = abs(ground-reference['heights'][index])
        height_errors.append(delta)
        if delta > 0.002 or ground < 1.25:
            errors.append(f'{index}:ground')
        distance = math.hypot(nav[0]-p[0], nav[2]-p[2])
        distances.append(distance)
        if found != 'true' or distance > 2.001 or abs(nav[1]-ground) > 0.8:
            errors.append(f'{index}:nav_sample')
    return dict(status='PASS_LOAD_SITES_WALK_QUERIES' if not errors else 'FAIL_LOAD_SITES',
                sites=101, routes=100, issues=errors,
                maximum_ground_error_m=max(height_errors), maximum_nav_displacement_m=max(distances),
                limits=['Pre-load WALK queries and dry heights; not infected locomotion or player capacity.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sites', type=Path, required=True)
    parser.add_argument('--sites-sha256', required=True)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Preserve existing evidence')
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    if sha(args.sites) != args.sites_sha256:
        raise ValueError('Frozen independent sites changed')
    try:
        result = verify(args.log.read_text(encoding='utf-8-sig'), json.loads(args.sites.read_text()))
    except (ValueError, IndexError, KeyError) as exc:
        result = dict(status='FAIL_LOAD_SITES', issues=[str(exc)])
    result.update(sites_sha256=sha(args.sites), log_sha256=sha(args.log))
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'].startswith('PASS_') else 1)
