"""Which river ends build_v30_water.py --round-river-ends rounds on the v10 design, with the radius it settled on and
the area it took, and a figure of every cut end before and after. Usage: check_river_ends.py OUT.png [R]"""
import importlib.util
import json
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import shapely  # noqa: E402
from shapely.geometry import shape  # noqa: E402

W = r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290'
out, R = sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
argv = sys.argv
sys.argv = ['build_v30_water.py', '--selftest']          # import without the directory arguments
spec = importlib.util.spec_from_file_location('bw', W + r'\tools\terrain\build_v30_water.py')
bw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bw)
sys.argv = argv
inner = shapely.box(60, 60, 12222, 12222)
feats = json.load(open('E:/DayZ-Baltic-Build/v30-v10/design/water_v3.geojson', encoding='utf-8'))['features']
ends = []
for f in feats:
    if f['properties']['class'] != 'river':
        continue
    g = shape(f['geometry'])
    if g.within(inner):
        continue
    clipped = g.intersection(inner)
    for p in [q for q in getattr(clipped, 'geoms', [clipped]) if q.geom_type == 'Polygon' and q.area > 0]:
        rp, n = bw.round_cut_ends(p, inner, R)
        cut = p.boundary.intersection(inner.exterior)
        for s in [c for c in getattr(cut, 'geoms', [cut]) if c.geom_type == 'LineString' and c.length > 0.5]:
            m = s.interpolate(0.5, normalized=True)
            ends.append(dict(river=f['properties'].get('id') or f['properties'].get('name'), cut_m=round(s.length, 1),
                             at=[round(m.x), round(m.y)], rounded_in_part=n, area_taken_m2=round(p.area - rp.area, 1),
                             part=p, rounded=rp))
print(json.dumps([{k: v for k, v in e.items() if k not in ('part', 'rounded')} for e in ends], indent=1, ensure_ascii=False))
fig, axes = plt.subplots(1, len(ends), figsize=(5 * len(ends), 5))
for ax, e in zip(axes if len(ends) > 1 else [axes], ends):
    x, z = e['at']
    w = max(40.0, 2.5 * e['cut_m'])
    for geom, style in ((e['part'], dict(color='#d62728', lw=1.0, ls='--')), (e['rounded'], dict(color='#1f77b4', lw=1.6))):
        for poly in getattr(geom, 'geoms', [geom]):
            xs, ys = poly.exterior.xy
            ax.plot(xs, ys, **style)
    ax.axvline(12222, color='grey', lw=0.8)
    ax.set_xlim(x - 1.6 * w, x + 0.4 * w)
    ax.set_ylim(z - w, z + w)
    ax.set_aspect('equal')
    ax.set_title(f"{e['river']} cut {e['cut_m']} m, taken {e['area_taken_m2']} m2", fontsize=9)
fig.suptitle('river ends at the 60 m border cut: dashed red = straight clip, blue = rounded (--round-river-ends %g)' % R, fontsize=10)
fig.savefig(out, dpi=110, bbox_inches='tight')
print(out)
