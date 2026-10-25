"""Before/after figure of the polygon smoothing prototype: design outlines (black) and smoothed (red, sigma 12 m,
shift <= 4 m) in the RIVER_80 area and around the contour lakes and ponds whose outlines turn the most."""
import json
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from shapely.geometry import box, shape  # noqa: E402

sys.path.insert(0, sys.argv[1])
from smooth_polys_proto import smooth_polygon, turning  # noqa: E402

R = 'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/'
D = 'E:/DayZ-Baltic-Build/v30-redesign/design/'
feats = json.load(open(D + 'water_v3.geojson', encoding='utf-8'))['features']
contour = json.load(open(R + 'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson', encoding='utf-8'))['features']
items = ([('lake', shape(f['geometry'])) for f in contour if f['properties']['body'].startswith('lake')]
         + [(f['properties']['class'], shape(f['geometry'])) for f in feats if f['properties']['class'] in ('pond', 'river')])
streams = [shape(f['geometry']) for f in json.load(open(D + 'streams_candidates.geojson', encoding='utf-8'))['features']
           if f['properties']['tier_m'] >= 2500]
# windows: RIVER_80, then the two medium lakes (0.02-0.5 km2) and a pond cluster with the most sharp turns
cand = []
for k, g in items:
    if k == 'lake' and 2e4 < g.area < 5e5:
        t = turning(g)
        if t.size:
            cand.append(((t > 45).mean(), g))
cand.sort(key=lambda c: -c[0])
wins = [('RIVER_80 (sureste)', (11900, 1500, 12250, 1850))]
for share, g in cand[:2]:
    x0, z0, x1, z1 = g.bounds
    pad = 40
    wins.append((f'lago del contorno ({share * 100:.0f} % de giros > 45°)', (x0 - pad, z0 - pad, x1 + pad, z1 + pad)))
ponds = [g for k, g in items if k == 'pond']
pc = max(ponds, key=lambda g: (turning(g) > 45).mean() if turning(g).size else 0)
cx, cz = pc.centroid.x, pc.centroid.y
wins.append(('estanques OSM', (cx - 160, cz - 160, cx + 160, cz + 160)))
fig, axes = plt.subplots(2, 2, figsize=(14, 14))
for ax, (title, (x0, z0, x1, z1)) in zip(axes.ravel(), wins):
    win = box(x0, z0, x1, z1)
    for g in streams:
        if g.intersects(win):
            for p in getattr(g, 'geoms', [g]):
                ax.fill(*p.exterior.xy, color='#c9e3f5', lw=0)
    for k, g in items:
        if not g.intersects(win):
            continue
        for p in getattr(g, 'geoms', [g]):
            if p.geom_type != 'Polygon':
                continue
            ax.plot(*p.exterior.xy, color='k', lw=0.8)
            sp, _ = smooth_polygon(p, 12.0, 4.0)
            for q in getattr(sp, 'geoms', [sp]):
                ax.plot(*q.exterior.xy, color='red', lw=1.0)
    ax.set_xlim(x0, x1)
    ax.set_ylim(z0, z1)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=10)
    ax.tick_params(labelsize=7)
fig.suptitle('Contornos de diseño (negro) y suavizados (rojo: sigma 12 m, desplazamiento <= 4 m, área conservada)', fontsize=12)
fig.tight_layout(rect=(0, 0, 1, 0.97))
fig.savefig(sys.argv[2], dpi=100)
