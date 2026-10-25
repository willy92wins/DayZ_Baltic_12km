"""V29 reference outline for the Narva zone (Guillermo, 04-10: V29 rules in Narva): the terrain's own wet vertices,
smoothed with a 9 m Gaussian (sigma 1.5 vertices, as the V30 builder smooths the coast) and cut at 0.5. Signed distance to
that line (- inside the water) replaces sd within --radius of the bridge; elsewhere sd stays as in water_v30.
Usage: narva_v29_outline_v30.py <terrain npz> <out npz> [--radius 600] [--water-v30 PATH]"""
import hashlib
import sys
from pathlib import Path

import numpy as np
import shapely
from scipy.ndimage import gaussian_filter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

R = r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev'
ter, out = Path(sys.argv[1]), Path(sys.argv[2])
radius = float(sys.argv[sys.argv.index('--radius') + 1]) if '--radius' in sys.argv else 600.0
water_v30 = Path(sys.argv[sys.argv.index('--water-v30') + 1]) if '--water-v30' in sys.argv \
    else Path(R) / 'tests/terrain_v30/water_v30.npz'
BRIDGE = np.array([2417.1428225906, 6889.8850822322])
t = np.load(ter)
wet = t['cls'] > 0
N = wet.shape[0]
f = gaussian_filter(wet.astype(np.float64), 1.5)
c0, c1 = int((BRIDGE[0] - radius - 60) / 6), int((BRIDGE[0] + radius + 60) / 6)
r0, r1 = int((12282 - BRIDGE[1] - radius - 60) / 6), int((12282 - BRIDGE[1] + radius + 60) / 6)
sub = f[r0:r1, c0:c1]
xs, zs = np.arange(c0, c1) * 6.0, 12282.0 - np.arange(r0, r1) * 6.0
cs = plt.contour(xs, zs, sub, levels=[0.5])
lines = [shapely.LineString(seg) for seg in cs.allsegs[0] if len(seg) > 1]
edge = shapely.MultiLineString(lines)
w = np.load(water_v30)
sd = w['sd'].astype(np.float32).copy()
c, r = np.meshgrid(np.arange(N), np.arange(N))
x, z = c * 6.0, 12282.0 - r * 6.0
zone = np.hypot(x - BRIDGE[0], z - BRIDGE[1]) <= radius
dist = shapely.distance(edge, shapely.points(x[zone], z[zone]))
inside = f[zone] > 0.5
sd[zone] = np.where(inside, -dist, dist).astype(np.float32)
np.savez_compressed(out, sd=sd)
print('zone vertices', int(zone.sum()), 'inside', int(inside.sum()), 'contour segments', len(lines),
      'sd p10/50/90', np.percentile(sd[zone], [10, 50, 90]).round(1), 'sha', hashlib.sha256(out.read_bytes()).hexdigest()[:16])
