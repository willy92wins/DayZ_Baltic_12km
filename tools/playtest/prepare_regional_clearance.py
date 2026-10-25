"""Raise only measured-risk dry terrain, keeping native water and higher land."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.features import rasterize
from affine import Affine
import shapefile
from shapely import make_valid, distance, points, contains_xy, STRtree
from shapely.geometry import shape, LineString
from shapely.ops import unary_union

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
if args.out.exists():
    raise ValueError('Fresh candidate directory required')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
source = args.repo/'tb/narva_trial/narva_tb_dryland_v1.asc'
reference_path = args.repo/'evidence/regional-water/reference-v1.json'
observation_path = args.repo/'evidence/regional-water/baseline-verification-v1.json'
reference = json.loads(reference_path.read_text())
observation = json.loads(observation_path.read_text())
if sha(source) != reference['native_sha256'] or observation['reference_sha256'] != sha(reference_path):
    raise ValueError('Source or frozen reference drift')
if observation['status'] != 'FAIL_DRY_LAND_FLOODING' or observation['sea_readings']['sea_min'] != .5 or observation['sea_readings']['sea_max'] != 1:
    raise ValueError('Design requires the measured flood and sea range')
with rasterio.open(source) as dataset:
    base = dataset.read(1)
cover_path = args.repo/'derived/gis/worldcover_2021_3857.tif'
with rasterio.open(cover_path) as dataset:
    cover = dataset.read(1)
if base.shape != (2048, 2048) or cover.shape != base.shape:
    raise ValueError('Unexpected dimensions')
parts = []
for name in ('ocean', 'water'):
    path = args.repo/f'derived/tb/source/vectors/{name}.shp'
    if sha(path) != reference['source_water_hashes'][name]:
        raise ValueError('Water source drift')
    with shapefile.Reader(str(path)) as reader:
        parts.extend(make_valid(shape(item.__geo_interface__)) for item in reader.iterShapes())
water = unary_union(parts)
# Pixel centers are the observed native vertices, not the original GIS centers.
native_transform = Affine(6, 0, 199997, 0, -6, 12285)
water_mask = rasterize([(water, 1)], out_shape=base.shape, transform=native_transform, dtype='uint8').astype(bool)
dry_cover = np.isin(cover, [10, 20, 30, 40, 50, 60])
rows, cols = np.where((base < 1.25) & dry_cover & ~water_mask)
x, z = 200000 + 6*cols, 12282 - 6*rows
# Exact vector check resolves raster boundary conventions conservatively.
inside = contains_xy(water, x, z)
rows, cols, x, z = (v[~inside] for v in (rows, cols, x, z))
print(f'Candidate dry low vertices: {len(rows)}', flush=True)
boundary = water.boundary
rings = list(boundary.geoms) if hasattr(boundary, 'geoms') else [boundary]
# Index exact segments in short chunks; avoid each point scanning every coast.
# STRtree query_nearest contract: local shapely/strtree.py:358, indices[0] are
# input positions and return_distance reports exact planar geometry distance.
chunks = []
for ring in rings:
    coordinates = list(ring.coords)
    chunks.extend(LineString(coordinates[i:i+33]) for i in range(0, len(coordinates)-1, 32))
tree = STRtree(chunks)
query = points(x, z)
indices, measured = tree.query_nearest(query, max_distance=12, return_distance=True, all_matches=False)
dist = np.full(len(query), 12.0)
dist[indices[0]] = measured
# Compare to the unindexed original geometry on a fixed, spread-out sample.
check = np.unique(np.linspace(0, len(query)-1, 64, dtype=int))
if np.max(abs(dist[check] - np.minimum(distance(query[check], boundary), 12))) > 1e-8:
    raise ValueError('Indexed shore distance differs from original boundary')
print('Exact indexed distances verified against64 unindexed samples', flush=True)
target = .75 + .5*np.clip(dist/12, 0, 1)
candidate = base.copy()
candidate[rows, cols] = np.maximum(base[rows, cols], target)
delta = candidate - base
changed = delta > 0
if np.any(delta < 0) or np.any(changed & water_mask) or np.any(changed & ~dry_cover) or np.any(changed & (base >= 1.25)):
    raise ValueError('Protected vertices changed')
for sample in reference['samples']:
    if sample['dry_interior']:
        row, col = int((12282-sample['z'])/6), int(sample['x']/6)
        if candidate[row, col] < 1.25:
            raise ValueError(f'Frozen dry sample lacks clearance: {sample}')
args.out.mkdir(parents=True)
asc = args.out/'baltic_regional_clearance_v1.asc'
with asc.open('w', encoding='ascii', newline='\n') as handle:
    handle.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
    np.savetxt(handle, candidate, fmt='%.4f')
with rasterio.open(asc) as dataset:
    roundtrip = dataset.read(1)
if np.max(abs(roundtrip-candidate)) > .000051 or np.any(roundtrip[~changed] != base[~changed]):
    raise ValueError('Output changed unaffected vertices or lost precision')
np.savez_compressed(args.out/'delta.npz', row=np.where(changed)[0], col=np.where(changed)[1], delta=delta[changed])
result = dict(status='PREPARED_NOT_IMPORTED', source_sha256=sha(source), candidate_sha256=sha(asc),
              observation_sha256=sha(observation_path), reference_sha256=sha(reference_path),
              worldcover_sha256=sha(cover_path), water_source_hashes=reference['source_water_hashes'],
              changed_vertices=int(changed.sum()), max_raise_m=float(delta.max()),
              dry_floor_m=1.25, shore_floor_m=.75, ramp_m=12,
              water_and_wetland_vertices_unchanged=True, all_vertices_ge_1_25_unchanged=True,
              all_frozen_dry_samples_clear=True,
              limits=['Not native-imported or engine-proven.', 'No new lake surfaces.',
                      'Interpolated shoreline fidelity still needs native/runtime review.'])
(args.out/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
