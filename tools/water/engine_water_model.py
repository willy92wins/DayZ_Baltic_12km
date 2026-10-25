"""Engine water surface over roadway water faces (dz/water/streams pieces), as measured in the vanilla channel pilot.

Rule, read from run 8392533a (GetWaterSurfaceHeightNoFakeWave from ground + 50 and GetWaterDepth at ground + 0.01):
  1. candidate faces: those whose WORLD xz bounding box contains the query point;
  2. the query point goes to model space with its own height, through the object's full transform;
  3. a candidate counts when that model point lies inside the face in model xz;
  4. the level is the model y of the face's first vertex, horizontal in model space, returned as the world y of
     (lx, y_first, lz). Over several objects the highest level wins.
Consequences on a pitched piece: a query dy above the surface reads the level dy * sin(pitch) further along the
piece (+6 cm at 2 degrees from 50 m up) and loses water near face edges; the -z skirt reads its bottom (first
vertex at -0.07 m) and the +z skirt the flat level. Horizontal pond planes are outside this model.

Usage (check a readback log against the rule):
  engine_water_model.py --reference <readback-reference.json> --log <readback log> --out <json>
V1 logs (W rows) are checked at the heights they used; V2 logs (W2 rows) against the reference predictions.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts')
from odol_reader import ODOL  # noqa: E402

DZ = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DZ\water\streams')
EPS = 1e-6
_SHAPES = {}


def roadway(piece_type):
    """Vertices and faces of the roadway LOD (resolution 3e15) of a dz/water/streams piece."""
    if piece_type not in _SHAPES:
        lod = [l for l in ODOL.from_file(str(DZ / f'{piece_type}.p3d')).lods if 2.9e15 < l.resolution < 3.1e15][0]
        _SHAPES[piece_type] = (np.array([[v.x, v.y, v.z] for v in lod.vertices]),
                               [list(f.vertex_indices) for f in lod.faces])
    return _SHAPES[piece_type]


def inside(poly, x, z):
    """Point in polygon (xz), edges included."""
    n = len(poly)
    for i in range(n):
        (x1, z1), (x2, z2) = poly[i], poly[(i + 1) % n]
        ex, ez = x2 - x1, z2 - z1
        t = ((x - x1) * ex + (z - z1) * ez) / (ex * ex + ez * ez)
        if 0.0 <= t <= 1.0 and abs((x - x1) * ez - (z - z1) * ex) / (ex * ex + ez * ez) ** 0.5 <= EPS:
            return True
    c = False
    for i in range(n):
        (x1, z1), (x2, z2) = poly[i], poly[(i + 1) % n]
        if (z1 > z) != (z2 > z) and x1 + (z - z1) * (x2 - x1) / (z2 - z1) > x:
            c = not c
    return c


class Piece:
    """One placed piece; matrix = WRP 0WZD record [right*s, up*s, fwd*s, pos]."""

    def __init__(self, piece_type, matrix):
        self.type = piece_type
        m = np.array(matrix[:9], dtype=float).reshape(3, 3)
        self.M = m.T
        self.Minv = np.linalg.inv(self.M)
        self.pos = np.array(matrix[9:], dtype=float)
        self.v, self.faces = roadway(piece_type)
        self.w = self.pos + self.v @ m
        self.box = (self.w[:, 0].min(), self.w[:, 2].min(), self.w[:, 0].max(), self.w[:, 2].max())
        self.face_box = [(self.w[f, 0].min(), self.w[f, 2].min(), self.w[f, 0].max(), self.w[f, 2].max()) for f in self.faces]

    def level(self, x, qy, z):
        """Engine level from this object for a query at (x, qy, z), or None."""
        if not (self.box[0] - EPS <= x <= self.box[2] + EPS and self.box[1] - EPS <= z <= self.box[3] + EPS):
            return None
        best, local = None, None
        for f, b in zip(self.faces, self.face_box):
            if not (b[0] - EPS <= x <= b[2] + EPS and b[1] - EPS <= z <= b[3] + EPS):
                continue
            if local is None:
                local = self.Minv @ (np.array([x, qy, z]) - self.pos)
            if inside([(self.v[i, 0], self.v[i, 2]) for i in f], local[0], local[2]):
                y = float(self.pos[1] + self.M[1] @ np.array([local[0], self.v[f[0], 1], local[2]]))
                best = y if best is None else max(best, y)
        return best

    def visual(self, x, z):
        """Visual (LOD0 = roadway geometry) height over (x, z) and the face index, or None."""
        if not (self.box[0] - EPS <= x <= self.box[2] + EPS and self.box[1] - EPS <= z <= self.box[3] + EPS):
            return None
        for fi, f in enumerate(self.faces):
            if inside([(self.w[i, 0], self.w[i, 2]) for i in f], x, z):
                a, b, c = self.w[f[0]], self.w[f[1]], self.w[f[2]]
                n = np.cross(b - a, c - a)
                return float(a[1] - (n[0] * (x - a[0]) + n[2] * (z - a[2])) / n[1]), fi
        return None


def predict(pieces, x, qy, z):
    hs = [h for h in (p.level(x, qy, z) for p in pieces) if h is not None]
    return max(hs) if hs else None


def top_visual(pieces, x, z):
    """Highest visual surface over (x, z): (height, piece index, zone) with zone flat / skirt+z / skirt-z."""
    best = None
    for k, p in enumerate(pieces):
        r = p.visual(x, z)
        if r and (best is None or r[0] > best[0]):
            zone = 'flat' if all(abs(p.v[i, 1] - p.v[:, 1].max()) < 1e-4 for i in p.faces[r[1]]) else \
                ('skirt+z' if p.v[p.faces[r[1]], 2].mean() > 0 else 'skirt-z')
            best = (r[0], k, zone)
    return best


def is_band(h):
    return abs(h / 0.025 - round(h / 0.025)) < 1e-3


def classify(engine, model, sea):
    """Engine reading against the model: match, pond (a 25 mm pond plane above the vanilla level), dry, or miss."""
    if engine is None:
        return 'missing'
    eng_dry = abs(engine - sea) < 1e-3
    if model is None:
        return 'dry' if eng_dry else ('pond' if is_band(engine) else 'miss_engine_wet')
    if abs(engine - model) <= 2e-3:
        return 'match'
    if is_band(engine) and engine > model:
        return 'pond'
    return 'miss_engine_dry' if eng_dry else 'miss_value'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--reference', type=Path, required=True)
    ap.add_argument('--log', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists(), 'Preserve prior evidence'
    ref = json.loads(a.reference.read_text(encoding='utf-8'))
    pieces = [Piece(p['type'], p['matrix']) for p in ref['pieces']]
    rows = {}
    for line in a.log.read_text(encoding='utf-8').splitlines():
        f = line.split(';')
        if f[0] == 'W':
            rows[int(f[1])] = {'ground': float(f[4]), 'plane': float(f[7]), 'depth': float(f[8])}
        elif f[0] == 'W2':
            rows[int(f[1])] = {'ground': float(f[4]), 'sea': float(f[5]), 'hull': float(f[8]), 'body': float(f[9]),
                               'depth': float(f[10])}
    counts = collections.defaultdict(collections.Counter)
    misses = collections.defaultdict(list)
    for s in ref['samples']:
        r = rows.get(s['index'])
        grp = 'PAD' if s['reach'].startswith('PAD') else s['reach']
        if r is None:
            counts[grp]['missing'] += 1
            continue
        if 'plane' in r:
            checks = [('plane_ground+50', r['plane'], predict(pieces, s['x'], r['ground'] + 50.0, s['z']),
                       r['plane'] if abs(r['plane'] - 0.54) < 0.02 else 0.0)]
        else:
            checks = [('hull', r['hull'], s['model_hull'], r['sea']), ('body', r['body'], s['model_body'], r['sea'])]
        for name, eng, mod, sea in checks:
            c = classify(eng, mod, sea)
            counts[f'{grp}:{name}'][c] += 1
            if c.startswith('miss') and len(misses[f'{grp}:{name}']) < 6:
                misses[f'{grp}:{name}'].append({'s': s['s'], 'offset': s['offset'], 'engine': eng, 'model': mod})
    out = {'counts': {k: dict(v) for k, v in sorted(counts.items())}, 'misses': misses,
           'reference_sha256': hashlib.sha256(a.reference.read_bytes()).hexdigest(),
           'log_sha256': hashlib.sha256(a.log.read_bytes()).hexdigest(),
           'notes': ['match: within 2 mm of the rule; pond: a 25 mm band plane above the vanilla level (not modelled).']}
    a.out.write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(out['counts'], indent=1))


if __name__ == '__main__':
    main()
