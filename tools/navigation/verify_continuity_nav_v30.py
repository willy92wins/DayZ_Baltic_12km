"""Validate the new native graph while retaining historical path controls."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/terrain'))
from verify_v30_acceptance import verify as verify_paths, vector
from v30_common import tri_sample


def verify(reference, text, heights):
    rows = text.splitlines()
    if not rows or rows[0] != reference['header']:
        raise ValueError('Wrong mission/world header')
    normalized = ['BALTIC_V30_ACCEPTANCE_V1;BalticTrial', *rows[1:]]
    result = verify_paths(reference, '\n'.join(normalized))
    errors = []
    heights_by_case = {}
    for row in rows[1:-1]:
        f = row.split(';')
        if f[0] != 'P':
            continue
        nav,ground,road = map(vector,f[3:])
        group = heights_by_case.setdefault(f[1],dict(count=0,max_surface_error_m=0.,max_terrain_error_m=0.))
        group['count'] += 1
        terrain_error = abs(float(tri_sample(heights,nav[0],nav[2]))-ground[1])
        surface_error = abs(nav[1]-road[1])
        group['max_surface_error_m'] = max(group['max_surface_error_m'],surface_error)
        group['max_terrain_error_m'] = max(group['max_terrain_error_m'],terrain_error)
        if any(abs(v[0]-nav[0])>.011 or abs(v[2]-nav[2])>.011 for v in (ground,road)):
            errors.append(f'{f[1]}/{f[2]}: ground/surface coordinates differ')
        # Engine Vector.ToString has rounded coordinates; 1cm includes its
        # interpolation effect on the <=35deg local ground.
        if terrain_error > .011:
            errors.append(f'{f[1]}/{f[2]}: loaded terrain differs from candidate')
        if surface_error > reference['max_waypoint_surface_error_m']:
            errors.append(f'{f[1]}/{f[2]}: nav waypoint too far from physical surface')
    result['height_cases'] = heights_by_case
    result['height_issues'] = errors
    result['status'] = ('PASS_LOCAL_CONTINUITY_NAV_PATHS' if
                        result['status'].startswith('PASS') and not errors else
                        'FAIL_LOCAL_CONTINUITY_NAV_PATHS')
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference',type=Path,required=True)
    ap.add_argument('--log',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a = ap.parse_args(); assert not a.out.exists()
    reference = json.loads(a.reference.read_text())
    terrain = Path(reference['terrain'])
    assert hashlib.sha256(terrain.read_bytes()).hexdigest() == reference['terrain_sha256']
    try:
        result = verify(reference,a.log.read_text(encoding='utf-8-sig'),np.load(terrain)['heights'])
    except (ValueError,IndexError,KeyError) as exc:
        result = dict(status='FAIL_PROBE_EVIDENCE',reason=str(exc))
    result.update(log_sha256=hashlib.sha256(a.log.read_bytes()).hexdigest(),
                  reference_sha256=hashlib.sha256(a.reference.read_bytes()).hexdigest())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','height_cases')},indent=2))
    raise SystemExit(0 if result['status'].startswith('PASS') else 1)


if __name__ == '__main__':
    main()
