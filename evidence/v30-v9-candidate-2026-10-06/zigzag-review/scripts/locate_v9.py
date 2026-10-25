"""Project points of the v9 RIVER_80 capture (same pose as v8) onto the v9 terrain (ray march over the heightfield) and
say what water is there and which design geometry it comes from (river or stream ribbon, contour-v2 lake, OSM pond)."""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage
from shapely.geometry import Point, shape

W = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
R = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev')
sys.path.insert(0, str(W / 'tools' / 'terrain'))
from v30_common import grid_xz  # noqa: E402

M = [0.7071067690849304, 0, -0.7071067690849304, 0.4801260530948639, 0.7341374158859253, 0.4801260530948639,
     0.5191137194633484, -0.6790007948875427, 0.5191137194633484, 12012, 80, 1560]
aside, up, d, pos = np.array(M[0:3]), np.array(M[3:6]), np.array(M[6:9]), np.array(M[9:12])
f = 540 / np.tan(np.radians(68.5 / 2))
PTS = {'river_zigzag_bank': [(650, 340), (700, 330), (745, 285), (800, 250), (880, 245), (760, 180), (850, 160)],
       'jagged_pond': [(770, 360), (850, 330), (810, 350)],
       'straight_canal_A': [(200, 340), (350, 320), (440, 270)],
       'w_shape_right': [(1620, 450), (1700, 470), (1760, 430), (1800, 460)],
       'channel_network_right': [(1300, 380), (1400, 360), (1150, 420)],
       'dark_square': [(1900, 230), (1680, 350)],
       'river_lower_left': [(300, 500), (450, 440)]}

t = np.load(sys.argv[1] if len(sys.argv) > 1 else 'E:/DayZ-Baltic-Build/v30-redesign/inland/terrain_inland.npz')
DESIGN = Path(sys.argv[2] if len(sys.argv) > 2 else 'E:/DayZ-Baltic-Build/v30-redesign/design')
h, cls, lev = t['heights'].astype(float), t['cls'], t['level'].astype(float)
x, z = grid_xz()
bodies = json.load(open(DESIGN / 'water_v3.geojson', encoding='utf-8'))['features']
streams = [f_ for f_ in json.load(open(DESIGN / 'streams_candidates.geojson', encoding='utf-8'))['features']
           if f_['properties']['tier_m'] >= 2500]
contour = json.load(open(R / 'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson', encoding='utf-8'))['features']
geoms = ([(f_['properties']['class'] + ':' + str(f_['properties'].get('id') or f_['properties'].get('osm_id') or
                                                    f_['properties'].get('name')), shape(f_['geometry'])) for f_ in bodies]
         + [('stream:' + str(f_['properties'].get('id')), shape(f_['geometry'])) for f_ in streams]
         + [('contour:' + f_['properties']['body'], shape(f_['geometry'])) for f_ in contour])
_, (ir, ic) = ndimage.distance_transform_edt(cls == 0, return_indices=True)


def hit(u, v):
    ray = d + (u - 960) / f * aside + (540 - v) / f * up
    ray = ray / np.linalg.norm(ray)
    for s in np.arange(1.0, 6000.0, 0.5):
        p = pos + s * ray
        if not (0 <= p[0] <= 12282 and 0 <= p[2] <= 12282):
            return p, None
        r, c = int(round((12282 - p[2]) / 6)), int(round(p[0] / 6))
        ground = max(h[r, c], lev[r, c] if np.isfinite(lev[r, c]) else -99)
        if p[1] <= ground:
            return p, (r, c)
    return None, None


out = {}
for name, pts in PTS.items():
    rows = []
    for (u, v) in pts:
        p, rc = hit(u, v)
        if rc is None:
            rows.append({'px': [u, v], 'world': None if p is None else [round(p[0]), round(p[2])], 'note': 'outside the map'})
            continue
        r, c = rc
        wr, wc = ir[r, c], ic[r, c]
        wx, wz = float(x[wr, wc]), float(z[wr, wc])
        src = [k for k, g in geoms if g.distance(Point(wx, wz)) <= 6.0]
        rows.append({'px': [u, v], 'world': [round(p[0]), round(p[2])], 'water_at': [int(wx), int(wz)],
                     'class': int(cls[wr, wc]), 'level': round(float(lev[wr, wc]), 2), 'design_within_6m': src,
                     'edge_m': round(min(wx, wz, 12282 - wx, 12282 - wz))})
    out[name] = rows
print(json.dumps(out, indent=1))
