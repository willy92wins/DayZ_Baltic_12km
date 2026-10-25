"""Freeze eight visual sites before the first tour run; never edits the map."""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'tools/terrain'))
from v30_common import tri_sample, cell_planes

mission = R / 'missions/BalticV30VisualTourV1.BalticTrial'
out = Path(__file__).parent / 'visual-tour-reference.json'
csv = mission / 'sites.csv'
assert not out.exists() and not csv.exists(), 'Preserve frozen reference'
n = np.load(R / 'tests/terrain_v30/terrain_v30.npz')
h, cls, level = n['heights'], n['cls'], n['level']
planes = cell_planes(cls, level)

# name, requested review XZ, dry view XZ, heading focus XZ, diagnostic water XZ.
# Coast is offshore: its view is on the coast, 231 m from the requested point.
# Causeway is observed from the actual requested low road, facing east.
sites = [
    ('delta', (8600, 9950), (8576, 9950), (8526, 10038), (8526, 10038)),
    ('narva_south', (1062, 4812), (1062, 4836), (1062, 4812), (1062, 4812)),
    ('stream', (3768, 2226), (3768, 2202), (3774, 2226), (3774, 2226)),
    ('lagoon', (5118, 1086), (5142, 1086), (5118, 1086), (5118, 1086)),
    ('coast', (1354, 10244), (1284, 10464), (1354, 10244), (1356, 10242)),
    ('causeway', (7364, 10706), (7364, 10706), (7464, 10706), (7362, 10698)),
    ('hills', (5478, 7344), (5478, 7392), (5478, 7344), (5418, 7050)),
    ('bridge', (2417, 6890), (2283.71362, 6910.41943), (2417, 6890), (2418, 6960)),
]


def sample(xz):
    x, z = xz
    c, r = int(x // 6), int((12282 - z) // 6)
    y, plane = float(tri_sample(h, x, z)), float(planes[r, c])
    return {'xyz': [x, y, z], 'terrain_y': y, 'vertex_class': int(cls[r, c]),
            'vertex_water_mask': bool(n['water'][r, c]),
            'cell_plane_y': plane if math.isfinite(plane) else None}


def vec(xz):
    return f'{xz[0]:.5f} 0 {xz[1]:.5f}'


rows, reference = [], []
for name, target, view, focus, water in sites:
    yaw = math.degrees(math.atan2(focus[0] - view[0], focus[1] - view[1]))
    v = sample(view)
    assert v['terrain_y'] > 1.4 and not v['vertex_water_mask'], (name, v)
    rows.append(f'{name};{vec(view)};{yaw:.5f} 0 0;{vec(target)};{vec(water)}')
    reference.append({'name': name, 'view': v, 'target': sample(target),
                      'near_water': sample(water), 'focus_xz': focus,
                      'orientation_ypr': [yaw, 0, 0],
                      'view_offset_m': math.dist(view, target)})
csv.write_bytes(('\n'.join(rows) + '\n').encode('utf-8'))
result = {
    'schema': 'BALTIC_V30_VISUAL_TOUR_V1', 'world': 'BalticTrial',
    'site_seconds': 45, 'settle_seconds': 8, 'sites': reference,
    'mission_sha256': hashlib.sha256((mission / 'init.c').read_bytes()).hexdigest(),
    'sites_sha256': hashlib.sha256(csv.read_bytes()).hexdigest(),
    'world_pbo_sha256': '69140d41ef4841078a5c159222814490a85832e319977b8b22c18be940e24811',
    'water_pbo_sha256': 'e9b52b8c4fc07df8bc4854dcd9e144e16875af8006221f16efaa6ab95de56681',
    'limits': [
        'Temporary player teleports are visual instrumentation, not traversal evidence.',
        'The mask/plane samples are integration diagnostics derived from the candidate, not independent water-design acceptance.',
        'GetWaterSurfaceHeightNoFakeWave can return an object below the query; inspect bridge samples separately.',
        'A frame is accepted only after verifying its current stage, player position and actual image contents.',
        'Body yaw does not certify client head orientation. Offshore and small-water offsets are explicit.',
    ],
    'api_anchors': ['P:/scripts/1_core/proto/enmath.c:427',
                    'P:/scripts/3_game/entities/object.c:293',
                    'P:/scripts/3_game/entities/object.c:300',
                    'P:/scripts/3_game/entities/object.c:317',
                    'P:/scripts/1_core/proto/ensystem.c:382',
                    'P:/scripts/3_game/global/game.c:1162',
                    'P:/scripts/3_game/weather.c:183'],
}
out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'frozen': str(out), 'sites': len(reference),
                  'mission_sha256': result['mission_sha256'],
                  'sites_sha256': result['sites_sha256']}))
