"""Verify the server readback of the vanilla channel pilot against its frozen reference (step 4 gates).

Pieces: found at their origin with the expected shape, direction and up vector within 0.2 degrees and scale within
1e-3. V2 water (W2 rows, gameplay heights): per reach/pad and height, at least 99% of the rows agree with the level
the engine rule predicted before the run (tools/water/engine_water_model.py; within 2 mm, or dry on both sides),
leaving out 25 mm pond planes above the vanilla level; and no hole at the hull height (engine at sea level where a
visual surface stands above the sea). Reported, not gated: engine hull level minus the visual top surface, by zone
(flat, +z skirt, -z skirt). V1 logs (W rows, queried from ground + 50 m) keep their original gates. Usage:
  verify_vanilla_channel_readback.py --reference <json> --log <log> --out <json>
"""
from pathlib import Path
import argparse
import collections
import hashlib
import importlib.util
import json
import math

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('ewm', ROOT / 'tools' / 'water' / 'engine_water_model.py')
ewm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ewm)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def vec(t):
    return np.array([float(v) for v in t.strip('<> ').split(',')])


def angle(a, b):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    return math.degrees(math.acos(max(-1.0, min(1.0, float(a @ b)))))


def v1_water(ref, srow):
    lines_by = collections.defaultdict(list)
    for smp in ref['samples']:
        r = srow.get(smp['index'])
        lines_by[(smp['reach'], smp['offset'] if smp['reach'].startswith('PAD') else round(np.sign(smp['offset'])))].append((smp, r))
    reaches, pads = {}, {}
    for (reach, off), rows in sorted(lines_by.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        rows = sorted(rows, key=lambda t: t[0]['s'])
        if reach.startswith('PAD'):
            inside = [(smp, r) for smp, r in rows if smp['surface'] is not None]
            outside = [(smp, r) for smp, r in rows if smp['surface'] is None]
            ok_in = [abs(r['plane'] - smp['surface']) <= 0.03 for smp, r in inside if r]
            ok_out = [abs(r['plane'] - (smp['ground'] + 0.5)) > 0.2 or r['depth'] <= 0 for smp, r in outside if r]
            pads.setdefault(reach, {})[round(off, 2)] = {'inside': len(inside), 'inside_match': sum(ok_in),
                                                          'outside': len(outside), 'outside_dry': sum(ok_out)}
            continue
        missing = sum(r is None for _, r in rows)
        res = np.array([r['plane'] - smp['surface'] if r and smp['surface'] is not None else np.nan for smp, r in rows])
        wet = [(smp, r) for smp, r in rows if r and smp['surface'] is not None and smp['surface'] > smp['ground'] + 0.02]
        dry_wet = [round(smp['s'], 1) for smp, r in wet if r['depth'] <= 0]
        jumps = np.abs(np.diff(res[np.isfinite(res)])) if np.isfinite(res).sum() > 1 else np.zeros(0)
        key = f'{reach}:{"centre" if off == 0 else ("left" if off > 0 else "right")}'
        reaches[key] = {'samples': len(rows), 'missing': missing, 'expected_wet': len(wet), 'wet_without_depth': len(dry_wet),
                        'wet_without_depth_s': dry_wet[:20],
                        'residual_m_p50_max': [round(float(np.nanmedian(np.abs(res))), 4) if np.isfinite(res).any() else None,
                                               round(float(np.nanmax(np.abs(res))), 4) if np.isfinite(res).any() else None],
                        'max_jump_m': round(float(jumps.max()), 4) if jumps.size else None,
                        'pond_true': sum(1 for _, r in rows if r and r['pond'])}
    reach_ok = all(v['missing'] == 0 and v['wet_without_depth'] == 0 and (v['max_jump_m'] is None or v['max_jump_m'] <= 0.03)
                   for v in reaches.values())
    pad_ok = all(v['inside_match'] == v['inside'] and v['outside_dry'] == v['outside'] for p in pads.values() for v in p.values())
    return {'reach_water': reach_ok, 'pad': pad_ok}, {'reaches': reaches, 'pads': pads}


def v2_water(ref, srow):
    groups = collections.defaultdict(collections.Counter)
    holes = collections.defaultdict(list)
    resid = collections.defaultdict(list)
    misses = collections.defaultdict(list)
    for smp in ref['samples']:
        r = srow.get(smp['index'])
        grp = 'PAD' if smp['reach'].startswith('PAD') else smp['reach']
        for h in ('hull', 'body'):
            c = ewm.classify(r[h] if r else None, smp[f'model_{h}'], r['sea'] if r else 0.0)
            groups[f'{grp}:{h}'][c] += 1
            if c.startswith('miss') and len(misses[f'{grp}:{h}']) < 8:
                misses[f'{grp}:{h}'].append({'s': round(smp['s'], 2), 'offset': smp['offset'], 'engine': r[h], 'model': smp[f'model_{h}']})
        if r and smp['surface'] is not None:
            if abs(r['hull'] - r['sea']) < 1e-3 and smp['surface'] > r['sea'] + 0.01:
                holes[grp].append({'s': round(smp['s'], 2), 'offset': smp['offset'], 'surface': round(smp['surface'], 4)})
            elif not (ewm.is_band(r['hull']) and (smp['model_hull'] is None or r['hull'] > smp['model_hull'] + 2e-3)):
                resid[f'{grp}:{smp["zone"]}'].append(r['hull'] - smp['surface'])
    agreement = {}
    for g, c in sorted(groups.items()):
        n = sum(c.values()) - c['pond']
        agreement[g] = {'counts': dict(c), 'agreement': round((c['match'] + c['dry']) / n, 4) if n else None}
    visual = {}
    for g, v in sorted(resid.items()):
        a = np.abs(np.array(v))
        visual[g] = {'n': len(v), 'abs_p50_p90_max_m': [round(float(np.percentile(a, q)), 4) for q in (50, 90, 100)],
                     'share_le_1cm': round(float((a <= 0.01).mean()), 3), 'signed_p50_m': round(float(np.median(v)), 4)}
    ok_agree = all(v['agreement'] is not None and v['agreement'] >= 0.99 for v in agreement.values())
    ok_holes = not any(holes.values())
    return {'engine_rule_agreement': ok_agree, 'no_hull_holes': ok_holes}, \
        {'agreement': agreement, 'holes': {k: v[:20] for k, v in holes.items()}, 'hole_counts': {k: len(v) for k, v in holes.items()},
         'visual_residual_by_zone': visual, 'misses': misses}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--reference', type=Path, required=True)
    ap.add_argument('--log', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists(), 'Preserve prior evidence'
    ref = json.loads(a.reference.read_text(encoding='utf-8'))
    version = ref.get('version', 1)
    lines = a.log.read_text(encoding='utf-8').splitlines()
    n_p, n_s = len(ref['pieces']), len(ref['samples'])
    tag = 'BALTIC_VANILLA_CHANNEL_PILOT_V2;' if version == 2 else 'BALTIC_VANILLA_CHANNEL_PILOT_V1;'
    header_ok = bool(lines) and lines[0].startswith(tag) and lines[0].endswith(f';{n_p};{n_s}')
    end_ok = bool(lines) and lines[-1] == f'END;{n_p};{n_s}'
    prow, srow = {}, {}
    for line in lines:
        f = line.split(';')
        if f[0] == 'P':
            prow[int(f[1])] = f
        elif f[0] == 'W':
            srow[int(f[1])] = {'ground': float(f[4]), 'sea': f[5] == 'true', 'pond': f[6] == 'true',
                               'plane': float(f[7]), 'depth': float(f[8])}
        elif f[0] == 'W2':
            srow[int(f[1])] = {'ground': float(f[4]), 'sea': float(f[5]), 'is_sea': f[6] == 'true', 'pond': f[7] == 'true',
                               'hull': float(f[8]), 'body': float(f[9]), 'depth': float(f[10])}
    pieces = []
    for p in ref['pieces']:
        f = prow.get(p['index'])
        m = np.array(p['matrix'][:9]).reshape(3, 3)
        if not f or f[2] == 'MISSING':
            pieces.append({'index': p['index'], 'reach': p['reach'], 'found': False})
            continue
        pos, fwd, up, scale = vec(f[3]), vec(f[4]), vec(f[5]), float(f[6])
        pieces.append({'index': p['index'], 'reach': p['reach'], 'found': p['type'] in f[2],
                       'position_error_m': float(np.linalg.norm(pos - np.array(p['matrix'][9:]))),
                       'direction_error_deg': angle(fwd, m[2]), 'up_error_deg': angle(up, m[1]),
                       'scale_error': abs(scale - p['scale'])})
    found = [q for q in pieces if q['found']]
    piece_ok = len(found) == n_p and all(q['position_error_m'] <= 0.05 and q['direction_error_deg'] <= 0.2 and
                                         q['up_error_deg'] <= 0.2 and q['scale_error'] <= 1e-3 for q in found)
    checks, detail = (v2_water if version == 2 else v1_water)(ref, srow)
    checks = {'header': header_ok, 'end': end_ok, 'pieces': piece_ok, **checks}
    status = 'PASS_VANILLA_CHANNEL_READBACK' if all(checks.values()) else 'FAIL_OR_INCOMPLETE'
    worst = sorted(found, key=lambda q: -max(q['direction_error_deg'], q['up_error_deg']))[:5]
    out = {'status': status, 'version': version, 'checks': checks, 'pieces_found': len(found), 'pieces_expected': n_p,
           'worst_pieces': worst,
           'max_errors': {k: round(max(q[k] for q in found), 6) if found else None
                          for k in ('position_error_m', 'direction_error_deg', 'up_error_deg', 'scale_error')},
           **detail, 'reference_sha256': sha(a.reference), 'log_sha256': sha(a.log),
           'limits': ['Server readback of native APIs; no visual or boat result.',
                      'V2 prediction: engine rule of tools/water/engine_water_model.py, frozen in the reference before the run.']}
    a.out.write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in out.items() if k in ('status', 'version', 'checks', 'max_errors')}, indent=1))
    for k in ('agreement', 'hole_counts', 'visual_residual_by_zone'):
        if k in out:
            print(k, json.dumps(out[k])[:2500])


if __name__ == '__main__':
    main()
