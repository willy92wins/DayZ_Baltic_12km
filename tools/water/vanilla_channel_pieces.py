"""Vanilla channel piece library: end frames from the ODOL outlines, calibrated against Chernarus.

Pieces: dz/water/streams river_24_* and stream_14_* straights and 10/30 degree curves (the 45/90 degree
stream curves are left out: their outlines fold across the axis). Per piece, LOD0 side vertices are
split by the sign of x and sorted along z; the first pair is the start edge (local -z, downstream in
vanilla) and the last pair the end edge (local +z, upstream). Headings are measured from local +z
towards local +x. The flat level is the highest vertex level (+0.07 m in the straights).

Calibration: every library piece of the vanilla survey is matched to the neighbour whose entry edge best
continues its exit edge. Reported per joint: distance split along and across the exit heading, heading
difference and level offset. Usage:
  vanilla_channel_pieces.py --survey <survey.log> --out <library.json>   (out must not exist)
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import math
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts')
from odol_reader import ODOL  # noqa: E402

DZ = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DZ\water\streams')
SKIP = ('_l45', '_r45', '_l90', '_r90')
BS = chr(92)


def edge(a, b):
    ex, ez = b[0] - a[0], b[2] - a[2]
    n = math.hypot(ex, ez)
    hx, hz = -ez / n, ex / n
    if hz < 0:
        hx, hz = -hx, -hz
    return {'mid': [(a[0] + b[0]) / 2, (a[2] + b[2]) / 2], 'heading_deg': math.degrees(math.atan2(hx, hz)),
            'width': n, 'y': (a[1] + b[1]) / 2}


def library():
    pieces = {}
    for path in sorted(DZ.glob('*.p3d')):
        if any(s in path.stem for s in SKIP):
            continue
        lod = ODOL.from_file(str(path)).lods[0]
        vs = [(v.x, v.y, v.z) for v in lod.vertices]
        left = sorted([v for v in vs if v[0] < 0], key=lambda v: v[2])
        right = sorted([v for v in vs if v[0] > 0], key=lambda v: v[2])
        start, end = edge(left[0], right[0]), edge(left[-1], right[-1])
        tris = []
        for face in lod.faces:
            ids = face.vertex_indices
            tris += [[ids[0], ids[k], ids[k + 1]] for k in range(1, len(ids) - 1)]
        pieces[path.stem] = {'model': 'dz' + BS + 'water' + BS + 'streams' + BS + path.name,
                             'mesh': {'v': [list(v) for v in vs], 'tri': tris},
                             'family': path.stem.split('_')[0], 'width': round(max(v[0] for v in vs) - min(v[0] for v in vs), 3),
                             'flat_y': max(v[1] for v in vs), 'start': start, 'end': end,
                             'turn_deg': end['heading_deg'] - start['heading_deg'],
                             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    return pieces


def vec(t):
    return np.array([float(v) for v in t.strip('<> ').split(',')])


def basis(yaw_deg, up):
    a = math.radians(yaw_deg)
    fh = np.array([math.sin(a), 0.0, math.cos(a)])
    up = up / np.linalg.norm(up)
    fwd = fh - (fh @ up) * up
    fwd /= np.linalg.norm(fwd)
    right = np.cross(up, fwd)
    if right @ np.array([math.cos(a), 0.0, -math.sin(a)]) < 0:
        right = -right
    return right, up, fwd


def calibrate(pieces, survey):
    objs = []
    for line in survey.read_text(encoding='utf-8').splitlines():
        f = line.split(';')
        if f[0] == 'O' and f[2].split(BS)[-1][:-4] in pieces:
            objs.append({'name': f[2].split(BS)[-1][:-4], 'pos': vec(f[3]), 'yaw': float(vec(f[4])[0]), 'up': vec(f[5])})
    for o in objs:
        right, up, fwd = basis(o['yaw'], o['up'])
        for key in ('start', 'end'):
            e = pieces[o['name']][key]
            p = o['pos'] + e['mid'][0] * right + e['y'] * up + e['mid'][1] * fwd
            h = math.radians(e['heading_deg'])
            d = math.sin(h) * right + math.cos(h) * fwd
            o[key] = (p, math.degrees(math.atan2(d[0], d[2])))
    pos = np.array([o['pos'] for o in objs])
    joints = collections.defaultdict(list)
    for i, o in enumerate(objs):
        near = np.where((np.hypot(*(pos - o['pos'])[:, [0, 2]].T) < 40) & (np.arange(len(objs)) != i))[0]
        best = None
        for j in near:
            pa, ha = o['end']
            pb, hb = objs[j]['start']
            dh = abs((ha - hb + 180) % 360 - 180)
            dv = pb - pa
            h = math.radians(ha)
            along = dv[0] * math.sin(h) + dv[2] * math.cos(h)
            across = dv[0] * math.cos(h) - dv[2] * math.sin(h)
            err = math.hypot(along, across) + dh / 4
            if best is None or err < best[0]:
                best = (err, along, across, dh, float(dv[1]), float(np.linalg.norm(dv)))
        if best and best[0] < 12:
            joints[pieces[o['name']]['family']].append(best[1:])
    report = {}
    for fam, rows in joints.items():
        a = np.array(rows)
        report[fam] = {'joints': len(a),
                       'planned_gate_share_within_0_5m_2deg': round(float(((a[:, 4] <= 0.5) & (a[:, 2] <= 2)).mean()), 3),
                       'along_m_p10_p50_p90': np.percentile(a[:, 0], [10, 50, 90]).round(3).tolist(),
                       'across_m_p10_p50_p90': np.percentile(a[:, 1], [10, 50, 90]).round(3).tolist(),
                       'heading_deg_p50_p90': np.percentile(a[:, 2], [50, 90]).round(3).tolist(),
                       'level_m_abs_p50_p90': np.percentile(np.abs(a[:, 3]), [50, 90]).round(3).tolist()}
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--survey', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists(), 'Preserve prior evidence'
    pieces = library()
    report = calibrate(pieces, a.survey)
    frames_ok = all(abs(r['along_m_p10_p50_p90'][1]) <= 0.2 and r['heading_deg_p50_p90'][0] <= 1.0 for r in report.values())
    planned_ok = all(r['planned_gate_share_within_0_5m_2deg'] >= 0.9 for r in report.values())
    out = {'status': 'PASS_PLANNED_GATE' if planned_ok else ('FAIL_PLANNED_GATE_FRAMES_CONSISTENT' if frames_ok else 'FAIL_FRAMES'),
           'pieces': pieces, 'calibration': report,
           'survey_sha256': hashlib.sha256(a.survey.read_bytes()).hexdigest(),
           'notes': ['Planned gate: share of joints within 0.5 m and 2 degrees (3D distance).',
                     'Frames consistent: median along offset <= 0.2 m and median heading difference <= 1 degree.',
                     'Vanilla shifts pieces sideways at joints; the across spread measures that placement, not the frames.']}
    a.out.write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in out.items() if k != 'pieces'}, indent=1))


if __name__ == '__main__':
    main()
