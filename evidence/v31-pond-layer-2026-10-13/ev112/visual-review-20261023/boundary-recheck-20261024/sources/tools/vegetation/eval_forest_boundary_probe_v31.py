"""Fail-closed boundary measurements. A finite survey never proves a whole disc."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import uuid


def parse(text, count, survey_id):
    if type(count) is not int or count <= 0:
        raise ValueError('positive point count required')
    if str(uuid.UUID(survey_id)) != survey_id:
        raise ValueError('canonical survey identity required')
    lines = text.strip().splitlines()
    if len(lines) != count + 4 or lines[:3] != ['BALTIC_FOREST_BOUNDARY_V1;BalticTrial', 'SURVEY;'+survey_id, f'BEGIN;{count}'] or lines[-1] != f'END;{count}':
        raise ValueError('incomplete or unexpected native log')
    rows = {}
    previous = -1
    for line in lines[3:-1]:
        fields = line.split(';')
        if len(fields) != 6 or fields[0] != 'P':
            raise ValueError('invalid row schema')
        i, h, sea, pond, clock = int(fields[1]), float(fields[2]), fields[3], fields[4], int(fields[5])
        if i != len(rows) or i in rows or not math.isfinite(h) or sea not in ('0', '1') or pond not in ('0', '1') or clock < 0 or clock < previous:
            raise ValueError('invalid identity, height, boolean or clock')
        rows[i] = dict(ground=h, sea=sea == '1', pond=pond == '1', clock=clock)
        previous = clock
    return rows


def judge(doc, rows):
    points = doc['points']
    if not points or len(points) != len(rows) or [p['id'] for p in points] != list(range(len(points))) or set(rows) != set(range(len(points))):
        raise ValueError('point coverage mismatch')
    objects = {o['id']: o for o in doc['objects']}
    if not objects or len(objects) != len(doc['objects']):
        raise ValueError('missing/duplicate objects')
    if any(type(o.get('support_required')) is not bool for o in objects.values()):
        raise ValueError('support requirement must be an explicit boolean')
    violations = dict(root=[], support=[], margin_water=[])
    root_seen = set()
    sampled = {i: dict(root=0, support=0, margin=0) for i in objects}
    max_root_error = 0.0
    max_gap = -math.inf
    for p in points:
        if p['object_id'] not in objects or p['kind'] not in ('root', 'support', 'margin') or not all(math.isfinite(float(p[k])) for k in ('x', 'z')):
            raise ValueError('invalid point reference or expectation')
        o, r = objects[p['object_id']], rows[p['id']]
        if not all(math.isfinite(float(o[k])) for k in ('root_y', 'embed')) or o['embed'] < 0:
            raise ValueError('invalid model root/embed')
        sampled[o['id']][p['kind']] += 1
        if p['kind'] == 'root':
            if o['id'] in root_seen:
                raise ValueError('duplicate root')
            root_seen.add(o['id'])
            error = abs(o['root_y'] - r['ground'])
            max_root_error = max(max_root_error, error)
            if error > .005:
                violations['root'].append(dict(point=p['id'], object_id=o['id'], error=error))
        elif p['kind'] == 'support':
            gap = o['root_y'] - o['embed'] - r['ground']
            max_gap = max(max_gap, gap)
            if gap > .01:
                violations['support'].append(dict(point=p['id'], object_id=o['id'], gap=gap))
        elif r['sea'] or r['pond'] or r['ground'] < 1.0:
            # This boundary has no native pond cells. The existing non-pond
            # sea-band contract is h >= 1.0, stricter than sea height 0.75.
            violations['margin_water'].append(dict(point=p['id'], object_id=o['id'], ground=r['ground'], sea=r['sea'], pond=r['pond']))
    if root_seen != set(objects) or any(v['margin'] == 0 or (objects[i]['support_required'] and v['support'] == 0) for i, v in sampled.items()):
        raise ValueError('missing required per-object samples')
    bad = any(violations.values())
    return dict(status='FAIL' if bad else 'SAMPLED_BOUNDARY_CLEAR', objects=len(objects), points=len(points),
                max_root_error=max_root_error, max_sampled_trunk_gap=max_gap if math.isfinite(max_gap) else None,
                counts={k: len(v) for k, v in violations.items()},
                affected_objects={k: sorted({v['object_id'] for v in a}) for k, a in violations.items()},
                violations=violations,
                limits=['All listed roots measured; margins/support are finite samples, not continuous-disc acceptance.',
                        'No inferred boundary clamp, no global forest PASS, no visual or compiled-object acceptance.'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('manifest', type=Path); ap.add_argument('log', type=Path)
    ap.add_argument('--mod', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    doc = json.loads(a.manifest.read_text(encoding='utf-8'))
    expected = doc['mod_sha256']
    if set(expected) != {'narva_trial.pbo', 'baltic_water_v30.pbo', 'baltic_stream_pilot.pbo'}:
        raise ValueError('incomplete deployed artifact identity')
    for name, digest in expected.items():
        if hashlib.sha256((a.mod / 'Addons' / name).read_bytes()).hexdigest() != digest:
            raise ValueError('deployed artifact mismatch: ' + name)
    mission = Path(doc['mission'])
    for name, key in [('init.c', 'init_sha256'), ('points.csv', 'csv_sha256'), ('identity.txt','identity_sha256')]:
        if hashlib.sha256((mission / name).read_bytes()).hexdigest() != doc[key]:
            raise ValueError('mission input mismatch: ' + name)
    expected_csv = ''.join(f"{p['id']};{p['x']:.9f} 0 {p['z']:.9f}\n" for p in doc['points'])
    if (mission / 'points.csv').read_text(encoding='ascii') != expected_csv:
        raise ValueError('manifest coordinates do not match the executed input')
    if (mission / 'identity.txt').read_text(encoding='ascii').strip() != doc['survey_id']:
        raise ValueError('survey identity mismatch')
    result = judge(doc, parse(a.log.read_text(encoding='utf-8-sig'), len(doc['points']), doc['survey_id']))
    result.update(manifest_sha256=hashlib.sha256(a.manifest.read_bytes()).hexdigest(),
                  log_sha256=hashlib.sha256(a.log.read_bytes()).hexdigest(), mod_sha256=expected)
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('violations', 'affected_objects')}, indent=2))
    raise SystemExit(1 if result['status'] == 'FAIL' else 0)


if __name__ == '__main__':
    main()
