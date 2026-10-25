"""Check native V3 graph against frozen geometry and preselected dry references."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/playtest'))
from verify_nav_paths import vec


def verify(text, ref):
    lines = text.splitlines()
    if lines[:3] != ['BALTIC_NATIVE_NAV_V1', 'world=BalticTrial', 'flags=1;50'] or lines[-1] != 'BALTIC_NATIVE_NAV_COMPLETE':
        raise ValueError('Wrong world/filter or incomplete log')
    queries, points, samples, dry = {}, {}, {}, {}
    for line in lines[3:-1]:
        row = line.split(';')
        if row[0] == 'Q' and len(row) == 10 and row[1] not in queries:
            queries[row[1]] = row
        elif row[0] in ('P', 'R'):
            target = points if row[0] == 'P' else samples
            if len(row) != (4 if row[0] == 'P' else 6):
                raise ValueError('Malformed point/sample')
            group = target.setdefault(row[1], {})
            index = int(row[2])
            if index in group:
                raise ValueError('Duplicate sample')
            group[index] = row
        elif row[0] == 'D' and len(row) == 5 and int(row[1]) not in dry:
            dry[int(row[1])] = row
        else:
            raise ValueError('Unknown, duplicate or malformed row')
    expected = {r[0] for r in ref['routes']} | {'negative_no_polygons'}
    if set(queries) != expected or set(dry) != set(range(len(ref['dry_points']))):
        raise ValueError('Incomplete query/reference set')
    issues, routes, misses = [], {}, []
    cx, cz = ref['bridge_center_xz']
    ax, az = ref['bridge_axis_xz']
    for label, start, end in ref['routes']:
        q = queries[label]
        requested = [vec(q[2]), vec(q[3])]
        for p, distance in zip(requested, [start, end]):
            if math.hypot(p[0]-cx-ax*distance, p[2]-cz-az*distance) > .002:
                raise ValueError('Unexpected bridge request coordinates')
        if q[4:6] != ['true', 'true'] or q[8] != 'true':
            issues.append(f'{label}: missing endpoint/path')
        count = int(q[9])
        pts = points.get(label, {})
        if set(pts) != set(range(count)):
            raise ValueError('Incomplete waypoints')
        path = [vec(pts[i][3]) for i in range(count)]
        length = sum(math.dist(a,b) for a,b in zip(path,path[1:]))
        if len(path) < 2 or length > abs(end-start)*1.5:
            issues.append(f'{label}: missing path/excessive detour')
        if path and (math.dist(path[0],requested[0]) > 2.001 or math.dist(path[-1],requested[1]) > 2.001):
            issues.append(f'{label}: partial or over-snapped endpoints')
        if any(abs((p[0]-cx)*(-az)+(p[2]-cz)*ax)>2.5 for p in path):
            issues.append(f'{label}: path leaves road corridor')
        routes[label] = {'waypoints': count, 'length_m': length}
        if label not in ('west_east', 'east_west'):
            continue
        rows = samples.get(label, {})
        if set(rows) != set(range(121)):
            raise ValueError('Incomplete centerline samples')
        errors, gaps, deck = [], [], []
        for i, row in rows.items():
            p = vec(row[3]); n = vec(row[5])
            distance = start+(end-start)*i/120
            if math.hypot(p[0]-cx-ax*distance,p[2]-cz-az*distance) > .003:
                raise ValueError('Unexpected centerline sampling coordinates')
            if row[4] != 'true':
                gaps.append(i)
                continue
            error = math.dist(p,n)
            errors.append(error)
            if error > .801:
                gaps.append(i)
            if abs(distance) <= 37:
                deck.append(p[1])
                if not 8.99 <= p[1] <= 9.03:
                    issues.append(f'{label}/{i}: physical roadway is not at 9m')
        if gaps:
            issues.append(f'{label}: {len(gaps)} samples fail unchanged 0.8m acceptance')
        routes[label].update(samples=121, failing_indices=gaps, max_roadway_nav_distance_m=max(errors,default=None), physical_deck_y_range=[min(deck),max(deck)] if deck else None)
    neg = queries['negative_no_polygons']
    if neg[4:6] != ['false','false'] or neg[8:] != ['false','0'] or points.get('negative_no_polygons'):
        issues.append('Negative filter failed')
    regions = {}
    for i, p in enumerate(ref['dry_points']):
        row = dry[i]; requested = vec(row[2]); sampled = vec(row[4])
        if math.hypot(requested[0]-p['x'],requested[2]-p['z']) > .002:
            raise ValueError('Regional reference coordinates changed')
        group = regions.setdefault(p['region'], {'total':0,'found_within_2m':0})
        group['total'] += 1
        error = math.dist(requested,sampled) if row[3] == 'true' else None
        if error is None or error > 2.001:
            misses.append({'index':i,'region':p['region'],'requested':requested,'success':row[3],'error_m':error})
        else:
            group['found_within_2m'] += 1
    if misses:
        issues.append(f'{len(misses)} of {len(dry)} frozen dry-reference points have no walking sample within 2m')
    return {'status':'FAIL_NATIVE_NAV_ACCEPTANCE' if issues else 'PASS_NATIVE_NAV_GRAPH_AND_DRY_SAMPLES',
            'issues':issues,'routes':routes,'regional':regions,'regional_misses':misses,
            'limits':['Graph and samples only, no physical actor traversal.','Dry-reference misses need diagnosis: they do not alone establish a terrain defect.']}


if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--log',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--reference',type=Path,default=ROOT/'evidence/navigation/native-nav-reference-v2.json')
    args=ap.parse_args()
    if args.out.exists(): raise ValueError('Fresh output required')
    raw=args.log.read_bytes()
    refpath=args.reference
    try:
        result=verify(raw.decode('utf-8-sig'),json.loads(refpath.read_text()))
    except (ValueError,IndexError,KeyError) as exc:
        result={'status':'FAIL_PROBE_EVIDENCE','reason':str(exc)}
    result.update(log_sha256=hashlib.sha256(raw).hexdigest(),reference_sha256=hashlib.sha256(refpath.read_bytes()).hexdigest())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='regional_misses'},indent=2))
    raise SystemExit(0 if result['status'].startswith('PASS') else 1)
