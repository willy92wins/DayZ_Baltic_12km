"""Read installed vanilla ODOLs; measure a conservative centred boat opening.

All vertices are used in the reader's raw model frame. Vertical differences
within one model cancel its origin offset. No claim about float draft is made.
"""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
READER = Path(r'C:\Users\guill\.agents\skills\dayz-p3d-debinarizer\scripts\odol_reader.py')
sys.path.insert(0, str(READER.parent))
from odol_reader import ODOL


def vertices(lod):
    return np.array([[v.x, v.y, v.z] for v in lod.vertices], dtype=float)


def get_lod(model, resolution):
    found = [lod for lod in model.lods if np.isclose(lod.resolution, resolution, rtol=1e-6)]
    if len(found) != 1:
        raise ValueError(f'Expected one LOD {resolution}, found {len(found)}')
    return found[0]


def clip_plane(poly, axis, bound, keep_less):
    """3D Sutherland-Hodgman, retaining vertical faces as well as deck faces."""
    out = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        da = (bound - a[axis]) * (1 if keep_less else -1)
        db = (bound - b[axis]) * (1 if keep_less else -1)
        if da >= -1e-9:
            out.append(a)
        if (da < 0) != (db < 0):
            out.append(a + (b - a) * da / (da - db))
    return out


def corridor_min_y(lod, half_width, length_axis):
    # Metal/stone length is Z; wooden bridge length is X in these assets.
    vv = vertices(lod)
    pts = []
    for face in lod.faces:
        poly = [p for p in vv[face.vertex_indices]]
        poly = clip_plane(poly, length_axis, -half_width, False)
        poly = clip_plane(poly, length_axis, half_width, True)
        pts.extend(poly)
    if not pts:
        raise ValueError('No collision geometry intersects corridor')
    return float(np.asarray(pts)[:, 1].min())


def deck_at_centre(lod):
    vv = vertices(lod)
    hits = []
    for face in lod.faces:
        pp = vv[face.vertex_indices]
        for i in range(1, len(pp) - 1):
            tri = pp[[0, i, i+1]]
            m = np.vstack([tri[:, 0], tri[:, 2], np.ones(3)])
            if abs(np.linalg.det(m)) < 1e-10:
                continue
            w = np.linalg.solve(m, [0, 0, 1])
            if w.min() >= -1e-7:
                hits.append(float(w @ tri[:, 1]))
    if not hits:
        raise ValueError('No central roadway triangle')
    # Models may carry roadway on more than one horizontal face. The highest
    # central surface is the deck candidate; retain every hit for review.
    return max(hits), sorted(set(hits))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure(path, bridge=False):
    model = ODOL.from_file(str(path))
    if model.lod_errors:
        raise ValueError(model.lod_errors)
    result = {'path': str(path), 'sha256': sha(path), 'parse_mode': model.parse_mode,
              'lods': []}
    for lod in model.lods:
        if len(lod.vertices):
            vv = vertices(lod)
            result['lods'].append({'resolution': lod.resolution, 'vertices': len(vv),
                                  'min_xyz': vv.min(axis=0).tolist(),
                                  'max_xyz': vv.max(axis=0).tolist(),
                                  'extent_xyz': np.ptp(vv, axis=0).tolist()})
    if bridge:
        deck, hits = deck_at_centre(get_lod(model, 3e15))
        geometry = get_lod(model, 1e13)
        length_axis = 0 if path.stem.startswith('bridge_wood') else 2
        result['length_axis'] = 'X' if length_axis == 0 else 'Z'
        result['central_roadway_raw_y'] = deck
        result['central_roadway_hits_raw_y'] = hits
        result['corridors'] = []
        for width in (8, 12, 18, 24, 30, 36):
            low = corridor_min_y(geometry, width/2, length_axis)
            result['corridors'].append({
                'width_m': width, 'collision_min_raw_y': low,
                'lowest_collision_relative_to_deck_m': low - deck,
                'headroom_at_deck_9_water_1_m': 9 - deck + low - 1,
                'deck_required_for_6m_headroom_water_1_m': 7 + deck - low})
    return result


def main():
    boat = Path(r'P:\DZ\vehicles\water\Boat_01\Boat_01.p3d')
    bridges = Path(r'P:\DZ\structures\roads\bridges')
    report = {'method': 'Installed ODOL read-only; collision faces clipped to centred corridor on explicit bridge length axis, across entire road; highest central roadway ray hit. Conservative minimum includes piers.',
              'limitations': ['No runtime floating draft or passengers measured.',
                              'Reader/model frame must be checked against placed engine collider.',
                              'Centred passage only; a side span may differ.'],
              'reader_sha256': sha(READER), 'boat': measure(boat), 'bridges': []}
    for name in ('bridge_metal_25', 'bridge_metal_25_1', 'bridge_wood_25',
                 'bridge_wood_50', 'bridge_wood_50_1', 'bridge_stone_25'):
        report['bridges'].append(measure(bridges / (name + '.p3d'), True))
    dest = ROOT / 'evidence/navigation/vanilla-assets.json'
    dest.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    for bridge in report['bridges']:
        print(Path(bridge['path']).name, 'deck_raw', round(bridge['central_roadway_raw_y'], 3),
              [(x['width_m'], round(x['deck_required_for_6m_headroom_water_1_m'], 3)) for x in bridge['corridors']])


if __name__ == '__main__':
    main()
