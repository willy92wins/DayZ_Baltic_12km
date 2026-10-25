"""Inland water bodies that reach into the 60 m map-border band: contour-v2 lakes, design ponds, rivers, streams
(tier >= 2500), for the replayed design and the smoothed one. Area, position, and whether a dropped lake and a
dropped pond are the same water (overlap)."""
import json
import sys
from pathlib import Path

import shapely
from shapely.geometry import shape

R = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev')
M, A = 60.0, 0.05e6
inner = shapely.box(M, M, 12282 - M, 12282 - M)
band = shapely.box(0, 0, 12282, 12282).difference(inner)
contour = json.load(open(R / 'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson', encoding='utf-8'))['features']
lakes = [(f['properties']['body'], shape(f['geometry'])) for f in contour if f['properties']['body'].startswith('lake')]


def side(g):
    x0, z0, x1, z1 = g.bounds
    return ''.join(s for s, c in (('W', x0 < M), ('S', z0 < M), ('E', x1 > 12282 - M), ('N', z1 > 12282 - M)) if c)


out = {}
for name, d in (('replay', 'E:/DayZ-Baltic-Build/v30-replay/design'), ('redesign', 'E:/DayZ-Baltic-Build/v30-redesign/design')):
    bodies = json.load(open(d + '/water_v3.geojson', encoding='utf-8'))['features']
    streams = [f for f in json.load(open(d + '/streams_candidates.geojson', encoding='utf-8'))['features'] if f['properties']['tier_m'] >= 2500]
    ponds = [(f['properties'].get('osm_id') or f['properties'].get('id'), shape(f['geometry'])) for f in bodies if f['properties']['class'] == 'pond']
    rivers = [(f['properties'].get('id') or f['properties'].get('name'), shape(f['geometry'])) for f in bodies if f['properties']['class'] == 'river']
    strs = [(f['properties'].get('id') or f['properties'].get('name'), shape(f['geometry'])) for f in streams]
    rows = []
    for kind, items in (('lake', lakes), ('pond', ponds), ('river', rivers), ('stream', strs)):
        for key, g in items:
            if not g.intersects(band):
                continue
            act = 'drop' if kind in ('lake', 'pond') and g.area < A else 'clip'
            kept = g.intersection(inner).area
            c = g.representative_point()
            rows.append({'kind': kind, 'key': str(key), 'area_m2': round(g.area), 'kept_pct': round(100 * kept / g.area, 1),
                         'action': act, 'side': side(g), 'xz': [round(c.x), round(c.y)]})
    # same water: dropped lake and dropped pond that overlap
    dl = [(k, g) for k, g in lakes if g.intersects(band) and g.area < A]
    dp = [(k, g) for k, g in ponds if g.intersects(band) and g.area < A]
    pairs = [(a, str(b)) for a, ga in dl for b, gb in dp if ga.intersects(gb)]
    out[name] = {'rows': rows, 'lake_pond_overlaps': pairs}
    print(name, len(rows), 'pairs', pairs)
    for r in rows:
        print('  ', r)
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
