"""Narva moats (contour-v2 lake_093/096/099) as lakes: vertices inside each polygon become lake (class 2) at the polygon's
level_m; then the V30 builder's separation rule: a moat vertex next to water of another body more than 0.30 m away in
level becomes land. Heights are not touched (the shore fit shapes the banks and the depth bound).
Usage: narva_moats_v30.py <in terrain npz> <out dir>"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import shape

R = r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev'
MOATS = ('lake_093', 'lake_096', 'lake_099')
src, out = Path(sys.argv[1]), Path(sys.argv[2])
assert not out.exists()
t = dict(np.load(src))
cls, lev = t['cls'].copy(), t['level'].astype(np.float32).copy()
N = cls.shape[0]
feats = {f['properties']['body']: f for f in json.load(open(Path(R) / 'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson',
                                                            encoding='utf-8'))['features']}
moat = np.zeros((N, N), bool)
rep = {'moats': {}}
c, r = np.meshgrid(np.arange(N), np.arange(N))
for name in MOATS:
    g = shape(feats[name]['geometry'])
    level = float(feats[name]['properties']['level_m'])
    minx, miny, maxx, maxy = g.bounds
    win = (c * 6.0 >= minx - 6) & (c * 6.0 <= maxx + 6) & (12282.0 - r * 6.0 >= miny - 6) & (12282.0 - r * 6.0 <= maxy + 6)
    rr, cc = np.nonzero(win)
    ins = shapely.contains_xy(g, cc * 6.0, 12282.0 - rr * 6.0)
    ri, ci = rr[ins], cc[ins]
    before = {'classes': {int(k): int(v) for k, v in zip(*np.unique(cls[ri, ci], return_counts=True))},
              'levels': sorted({round(float(v), 2) for v in lev[ri, ci] if np.isfinite(v)})}
    cls[ri, ci], lev[ri, ci] = 2, level
    moat[ri, ci] = True
    rep['moats'][name] = {'level_m': level, 'vertices': int(ins.sum()), 'before': before}
# separation: moat vertex with an 8-neighbour water vertex of another body whose level differs by more than 0.30 m
wet = cls > 0
lp = np.pad(np.where(wet & ~moat, lev, np.nan), 1, constant_values=np.nan)
to_land = np.zeros((N, N), bool)
for dr in (-1, 0, 1):
    for dc in (-1, 0, 1):
        if dr or dc:
            nb = lp[1 + dr:1 + dr + N, 1 + dc:1 + dc + N]
            to_land |= moat & np.isfinite(nb) & (np.abs(nb - lev) > 0.30)
cls[to_land], lev[to_land] = 0, np.nan
rep['separated_to_land'] = int(to_land.sum())
rep['moat_vertices_final'] = int((moat & ~to_land).sum())
t['cls'], t['level'] = cls, lev
if 'water' in t:
    t['water'] = cls > 0
out.mkdir(parents=True)
np.savez_compressed(out / 'terrain_pilot.npz', **t)
rep['source_sha256'] = hashlib.sha256(src.read_bytes()).hexdigest()
rep['output_sha256'] = hashlib.sha256((out / 'terrain_pilot.npz').read_bytes()).hexdigest()
(out / 'report.json').write_text(json.dumps(rep, indent=1) + '\n', encoding='utf-8')
print(json.dumps(rep, indent=1))
