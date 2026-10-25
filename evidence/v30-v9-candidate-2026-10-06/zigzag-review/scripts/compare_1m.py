"""Visible water at 0.5 m (terrain on the native triangles below the cell plane, as the engine and the surface draw it)
for several terrains side by side in map windows, with the design outlines over it.
Usage: compare_1m.py OUT.png DESIGN_DIR label=terrain.npz ... -- x0,z0,x1,z1 [x0,z0,x1,z1 ...]"""
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

R = 'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/'
out, design = sys.argv[1], sys.argv[2]
k = sys.argv.index('--')
terrains = [a.split('=', 1) for a in sys.argv[3:k]]
windows = [tuple(float(v) for v in w.split(',')) for w in sys.argv[k + 1:]]
feats = [(f['properties']['class'], shape(f['geometry'])) for f in
         json.load(open(design + '/water_v3.geojson', encoding='utf-8'))['features']]
feats += [('stream', shape(f['geometry'])) for f in json.load(open(design + '/streams_candidates.geojson', encoding='utf-8'))['features']
          if f['properties']['tier_m'] >= 2500]
contour_path = design + '/contour_lakes.geojson'
try:
    contour = json.load(open(contour_path, encoding='utf-8'))['features']
except FileNotFoundError:
    contour = json.load(open(R + 'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson', encoding='utf-8'))['features']
feats += [('lake', shape(f['geometry'])) for f in contour if f['properties']['body'].startswith('lake')]
colors = {'river': 'red', 'stream': 'magenta', 'pond': 'orange', 'lake': 'lime', 'navigable': 'cyan'}
loaded = []
for label, p in terrains:
    t = np.load(p)
    h, cls, lev = t['heights'].astype(np.float64), t['cls'], t['level'].astype(np.float64)
    loaded.append((label, h, cell_planes(cls, lev)))
fig, axes = plt.subplots(len(windows), len(loaded), figsize=(6.2 * len(loaded), 5.6 * len(windows)), squeeze=False)
for wi, (x0, z0, x1, z1) in enumerate(windows):
    X, Z = np.meshgrid(np.arange(x0, x1, 0.5) + 0.25, np.arange(z1, z0, -0.5) - 0.25)
    rows, cols = np.floor((12282 - Z) / 6).astype(int), np.floor(X / 6).astype(int)
    win = box(x0, z0, x1, z1)
    for ti, (label, h, plane) in enumerate(loaded):
        ax = axes[wi, ti]
        h1 = tri_sample(h, X, Z)
        pl = plane[rows, cols]
        water = (np.isfinite(pl) & (h1 < np.nan_to_num(pl, nan=-1e9))) | (h1 < 0.75)
        ax.imshow(np.where(water, 1.0, 0.0), extent=(x0, x1, z0, z1), cmap='Blues', vmin=-0.3, vmax=1.4,
                  interpolation='nearest')
        for gx in np.arange(np.ceil(x0 / 6) * 6, x1, 6):
            ax.axvline(gx, color='k', lw=0.1, alpha=0.35)
        for gz in np.arange(np.ceil(z0 / 6) * 6, z1, 6):
            ax.axhline(gz, color='k', lw=0.1, alpha=0.35)
        for kind, g in feats:
            if kind not in colors or not g.intersects(win):
                continue
            for part in getattr(g, 'geoms', [g]):
                if part.geom_type != 'Polygon':
                    continue
                xs, zs = part.exterior.xy
                ax.plot(xs, zs, color=colors[kind], lw=0.6)
        ax.set_xlim(x0, x1)
        ax.set_ylim(z0, z1)
        ax.set_aspect('equal')
        ax.set_title(f'{label}', fontsize=9)
        ax.tick_params(labelsize=6)
fig.tight_layout()
fig.savefig(out, dpi=100)
