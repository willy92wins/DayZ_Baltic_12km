"""Zoom of the visible water at 0.25 m with every vertex labelled (class, height, level) and the design outline.
Usage: zoom_vertices.py TERRAIN.npz OUT.png x0 z0 x1 z1"""
import json
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from shapely.geometry import box, shape  # noqa: E402

sys.path.insert(0, r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees'
                   r'\codex-handoff-review-74f290\tools\terrain')
from v30_common import cell_planes, tri_sample  # noqa: E402

t = np.load(sys.argv[1])
out = sys.argv[2]
x0, z0, x1, z1 = (float(v) for v in sys.argv[3:7])
h, cls, lev = t['heights'].astype(np.float64), t['cls'], t['level'].astype(np.float64)
plane = cell_planes(cls, lev)
X, Z = np.meshgrid(np.arange(x0, x1, 0.25) + 0.125, np.arange(z1, z0, -0.25) - 0.125)
h1 = tri_sample(h, X, Z)
pl = plane[np.floor((12282 - Z) / 6).astype(int), np.floor(X / 6).astype(int)]
water = np.isfinite(pl) & (h1 < np.nan_to_num(pl, nan=-1e9))
fig, ax = plt.subplots(figsize=(13, 9))
ax.imshow(np.where(water, 1.0, 0.0), extent=(x0, x1, z0, z1), cmap='Blues', vmin=-0.3, vmax=1.3, interpolation='nearest')
for gx in np.arange(np.ceil(x0 / 6) * 6, x1 + 0.1, 6):
    ax.axvline(gx, color='k', lw=0.3, alpha=0.5)
for gz in np.arange(np.ceil(z0 / 6) * 6, z1 + 0.1, 6):
    ax.axhline(gz, color='k', lw=0.3, alpha=0.5)
c0, c1 = int(np.ceil(x0 / 6)), int(np.floor(x1 / 6))
r0, r1 = int(np.ceil((12282 - z1) / 6)), int(np.floor((12282 - z0) / 6))
for r in range(r0, r1 + 1):
    for c in range(c0, c1 + 1):
        vx, vz = c * 6.0, 12282.0 - r * 6.0
        k = int(cls[r, c])
        col = {0: 'saddlebrown', 2: 'green', 5: 'red', 6: 'magenta', 7: 'orange'}.get(k, 'k')
        ax.plot(vx, vz, 'o', color=col, ms=4)
        txt = f'{h[r, c]:.2f}' + (f'\n{lev[r, c]:.2f}' if k else '')
        ax.text(vx + 0.3, vz + 0.3, txt, fontsize=6, color=col)
D = 'E:/DayZ-Baltic-Build/v30-redesign/design/'
win = box(x0, z0, x1, z1)
for f in json.load(open(D + 'water_v3.geojson', encoding='utf-8'))['features']:
    g = shape(f['geometry'])
    if g.intersects(win):
        for part in getattr(g, 'geoms', [g]):
            xs, zs = part.exterior.xy
            ax.plot(xs, zs, color='crimson', lw=1.0)
ax.set_xlim(x0, x1)
ax.set_ylim(z0, z1)
ax.set_aspect('equal')
ax.set_title('agua visible (azul, 0,25 m), vértices: tierra marrón / río rojo / estanque naranja (cota y nivel), '
             'contorno de diseño carmesí', fontsize=9)
fig.tight_layout()
fig.savefig(out, dpi=110)
