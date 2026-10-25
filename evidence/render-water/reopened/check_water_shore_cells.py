"""Static subcell sampling of reference-water loss; not a game observation."""
from pathlib import Path
import hashlib
import json
import numpy as np
import rasterio
import shapefile
from shapely import make_valid, contains_xy, distance, points
from shapely.geometry import shape, box
from shapely.ops import unary_union

workspace = Path(__file__).resolve().parent.parent
repo = Path('P:/DayZ_Baltic_12km_dev')
out = workspace / 'work/water-extent/shore-subcell-v1'
out.mkdir(exist_ok=False)
native = [repo / 'tb/narva_trial/narva_tb_export_v2.asc',
          repo / 'tb/narva_trial/narva_tb_dryland_v1.asc']
rasters = []
for path in native:
    with rasterio.open(path) as source:
        rasters.append(source.read(1))
parts = []
domain = box(201300, 6000, 203700, 8400)
for name in ('water', 'ocean'):
    with shapefile.Reader(str(repo / f'derived/tb/source/vectors/{name}.shp')) as reader:
        for item in reader.iterShapes(bbox=domain.bounds):
            clipped = make_valid(shape(item.__geo_interface__)).intersection(domain)
            if not clipped.is_empty:
                parts.append(clipped)
water = unary_union(parts)
# Cell-centred 1.5 m samples. The native terrain remains 6 m, NW-SE diagonal.
step = 1.5
x, north = np.meshgrid(np.arange(1500 + step / 2, 3500, step),
                       np.arange(6200 + step / 2, 8200, step))
inside = contains_xy(water, x + 200000, north)
x, north = x[inside], north[inside]
colf, rowf = x / 6, 2047 - north / 6
col, row = colf.astype(int), rowf.astype(int)
u, v = colf - col, rowf - row
def sample(height):
    nw, ne = height[row, col], height[row, col+1]
    sw, se = height[row+1, col], height[row+1, col+1]
    return np.where(u >= v, (1-u)*nw + (u-v)*ne + v*se,
                    (1-v)*nw + u*se + (v-u)*sw)
before, after = map(sample, rasters)
assert np.min(after-before) >= -.00001
results = []
for level in (.5, .75, 1.0):
    old_wet, new_wet = before < level, after < level
    loss = old_wet & ~new_wet
    distances = distance(points(x[loss] + 200000, north[loss]), water.boundary)
    results.append({'static_plane_m': level,
                    'reference_water_samples': int(len(x)),
                    'previously_below_plane': int(old_wet.sum()),
                    'after_below_plane': int(new_wet.sum()),
                    'lost_samples': int(loss.sum()),
                    'approximate_lost_area_m2': float(loss.sum()*step*step),
                    'deepest_loss_inside_reference_water_m': float(distances.max()) if len(distances) else 0,
                    'lost_samples_more_than_12m_inside_water': int((distances > 12).sum()),
                    'worst_locations': [{'x': float(x[loss][i]), 'north': float(north[loss][i]),
                                         'inside_water_m': float(distances[i]),
                                         'terrain_before_m': float(before[loss][i]),
                                         'terrain_after_m': float(after[loss][i])}
                                        for i in np.argsort(distances)[-5:][::-1]]})
report = {'status': 'STATIC_SHORELINE_SAMPLING_ONLY', 'grid_step_m': step,
          'core': [1500, 6200, 3500, 8200],
          'native_sha256': [hashlib.sha256(p.read_bytes()).hexdigest() for p in native],
          'results': results,
          'limits': ['1.5 m point sampling of native triangular terrain against three static planes; approximate area, no exact polygons.',
                     'No claim of channel connectivity, in-game wetness, waves, swimming or elevated water validation.',
                     'Loss inside reference-water cells must be reviewed before regional rollout.']}
(out / 'analysis.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
