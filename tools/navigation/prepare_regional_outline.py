"""Build an isolated regional landform candidate; protected hydrology stays native."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import rasterio
from rasterio.features import rasterize
from affine import Affine
from scipy.ndimage import gaussian_filter, distance_transform_edt, binary_dilation
import shapefile
from shapely import make_valid
from shapely.geometry import shape, mapping, Point, box
from shapely.affinity import scale
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
sys.path.insert(0, str(ROOT/'tools/playtest'))
from geo_common import tb_geometry
from verify_texture_grid_change import read

NATIVE = ROOT/'tb/narva_navigation_v3/baltic_navigation_native_reopened_v2.wrp'
NATIVE_SHA = '9625ecf593c9c17288942d98ccf06933081bbcaffb367bb307146aa338cf9b5b'
TRANSFORM = Affine(6, 0, 199997, 0, -6, 12285)
OUT = ROOT/'tests/regional_outline_v1'
EV = ROOT/'evidence/regional-outline-v1'


def sha(p):
    with p.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def save(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def raster(geometries):
    return rasterize(((g, 1) for g in geometries if not g.is_empty), out_shape=(2048, 2048),
                     transform=TRANSFORM, dtype='uint8', all_touched=True).astype(bool)


def features(name):
    return json.loads((ROOT/f'derived/gis/osm_{name}_wgs84.geojson').read_text(encoding='utf-8'))['features']


def ease(t):
    t = np.clip(t, 0, 1)
    return t*t*t*(10+t*(-15+6*t))


def main():
    if OUT.exists():
        raise ValueError('Fresh candidate folder required')
    OUT.mkdir(parents=True)
    if sha(NATIVE) != NATIVE_SHA:
        raise ValueError('Native baseline changed')
    before = read(NATIVE)
    base = np.frombuffer(before['heights'], dtype='<f4').reshape(2048, 2048)[::-1].copy()
    with rasterio.open(ROOT/'derived/gis/worldcover_2021_3857.tif') as ds:
        cover = ds.read(1)
    with rasterio.open(ROOT/'source/baltic_physical_2048_6m.asc') as ds:
        physical = ds.read(1)
    cols, rows = np.meshgrid(np.arange(2048), np.arange(2048))
    x, z = cols*6., 12282-rows*6.
    frame = box(200000, 0, 212282, 12282)
    reserves_path = EV/'reserve_wgs84.geojson'
    reserves = json.loads(reserves_path.read_text(encoding='utf-8'))['features']
    reserve_shapes = [make_valid(tb_geometry(shape(f['geometry']))) for f in reserves]
    envelope = scale(Point(208200, 5200).buffer(1, quad_segs=64), xfact=1250, yfact=1400)
    reserve_union = unary_union(reserve_shapes+[envelope]).buffer(60).intersection(frame)
    reserve_mask = raster([reserve_union])
    print('Reserve masks assembled', flush=True)
    # Real polygons and buffered linework, not the colour in a satellite image.
    water_shapes = [make_valid(tb_geometry(shape(f['geometry']))) for f in features('water')]
    with shapefile.Reader(str(ROOT/'derived/tb/source/vectors/ocean.shp')) as reader:
        ocean_shapes = [make_valid(shape(g.__geo_interface__)) for g in reader.iterShapes()]
    water_mask = raster(water_shapes+ocean_shapes)
    river_shapes = [tb_geometry(shape(f['geometry'])) for f in features('rivers')]
    river_mask = raster([g.buffer(18) for g in river_shapes])
    water_support = binary_dilation(water_mask | river_mask | (cover == 80), iterations=3)
    wetlands = binary_dilation(cover == 90, iterations=2)
    fit = json.loads((ROOT/'evidence/narva/evidence/narva-fit.json').read_text())
    cx, cz = fit['bridge_centre_tb']; cx -= 200000
    narva = (x-cx)**2+(z-cz)**2 <= 400**2
    # Preserve the entire SPB reference rectangle for this regional relief pass.
    design = json.loads((ROOT/'evidence/navigation/selective-relief-v1/design.json').read_text(encoding='utf-8'))
    sx, sy, sw, sh = np.array(design['closeup_xywh_km'])*1000
    spb = (x >= sx) & (x <= sx+sw) & (z >= sy) & (z <= sy+sh)
    edges = (x < 24) | (x > 12258) | (z < 24) | (z > 12258)
    protected = water_support | wetlands | reserve_mask | narva | spb | edges
    road_features = [f for f in features('roads') if f['properties'].get('highway') in
                     {'motorway', 'trunk', 'primary', 'motorway_link', 'trunk_link', 'primary_link'}]
    road_shapes = [tb_geometry(shape(f['geometry'])) for f in road_features]
    road_core = raster([g.buffer(15) for g in road_shapes])
    # Keep a broad low corridor for the current road alignment; engineered
    # longitudinal smoothing is a separate layer, never an implicit road PASS.
    controls = protected | road_core
    distance = distance_transform_edt(~controls, sampling=6)
    transition = ease(distance/330.)
    macro = gaussian_filter(np.maximum(physical, 0).astype('float64'), sigma=9)
    a = np.exp(-.5*(((x-5900)/1700)**2+((z-7950)/1500)**2))
    b = np.exp(-.5*(((x-4500)/1700)**2+((z-1100)/1550)**2))
    target = macro*(5 + 15*a + 19*b)
    uplift = np.maximum(0, target-base)*transition
    # A second smoothing preserves broad relief while the exact protection
    # weight brings the delta continuously to zero at all constrained vertices.
    uplift = gaussian_filter(uplift, sigma=5)*transition
    candidate = base.copy()
    active = (uplift >= .001) & ~controls
    candidate[active] = np.round(base[active]+uplift[active], 4).astype('float32')
    changed = candidate != base
    if np.any(changed & controls) or np.any(candidate < base):
        raise ValueError('Protected or lower heights changed')
    if candidate.max() > 205 or not np.isfinite(candidate).all():
        raise ValueError('Candidate outside planned height range')
    asc = OUT/'baltic_regional_outline_v1.asc'
    with asc.open('w', encoding='ascii', newline='\n') as handle:
        handle.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(handle, candidate, fmt='%.9f')
    with rasterio.open(asc) as ds:
        persisted = ds.read(1)
    if not np.array_equal(persisted, candidate):
        raise ValueError('ASCII does not preserve all native float32 heights')
    np.savez_compressed(OUT/'reference.npz', base=base, candidate=candidate, protected=protected,
                        controls=controls, water=water_mask, reserve=reserve_mask,
                        wetlands=wetlands, narva=narva, spb=spb, road_core=road_core,
                        changed=changed)
    with rasterio.open(OUT/'height.tif', 'w', driver='GTiff', height=2048, width=2048,
                       count=1, dtype='float32', transform=TRANSFORM, compress='deflate') as ds:
        ds.write(candidate, 1)
    with rasterio.open(OUT/'delta.tif', 'w', driver='GTiff', height=2048, width=2048,
                       count=1, dtype='float32', transform=TRANSFORM, compress='deflate') as ds:
        ds.write(candidate-base, 1)
    with rasterio.open(OUT/'biome_reservation.tif', 'w', driver='GTiff', height=2048, width=2048,
                       count=1, dtype='uint8', transform=TRANSFORM, compress='deflate') as ds:
        biome = np.zeros_like(cover)
        biome[reserve_mask & (cover == 10)] = 1
        biome[reserve_mask & (cover == 90)] = 2
        biome[reserve_mask & ~np.isin(cover, [10, 90, 80])] = 3
        biome[reserve_mask & water_mask] = 4
        ds.write(biome, 1)
    # This file uses explicitly named engineering CRS; do not feed it to WGS84 tools.
    outline = {'type': 'FeatureCollection', 'coordinate_system': 'TB local engineering metres, origin E200000/N0',
               'features': [{'type': 'Feature', 'properties': {'role': 'reserve_conservation'}, 'geometry': mapping(reserve_union)}]}
    for geom, f in zip(road_shapes, road_features):
        outline['features'].append({'type': 'Feature', 'properties': {**f['properties'], 'role': 'road_reference_not_built'}, 'geometry': mapping(geom)})
    save(EV/'outline_tb.geojson', outline)
    with shapefile.Writer(str(OUT/'reserve_outline'), shapeType=shapefile.POLYLINE) as writer:
        writer.field('role', 'C', 40)
        polys = list(reserve_union.geoms) if hasattr(reserve_union, 'geoms') else [reserve_union]
        for poly in polys:
            for ring in [poly.exterior, *poly.interiors]:
                writer.line([list(ring.coords)]); writer.record('reserve_conservation')
    slope_before = np.degrees(np.arctan(np.hypot(*np.gradient(base, 6))))
    slope_after = np.degrees(np.arctan(np.hypot(*np.gradient(candidate, 6))))
    stats = {}
    for zone in design['zones']:
        xx, yy = zone['centre_game_km']; dx, dy = zone['ellipse_diameters_km']
        area = (((x/1000-xx)/(dx/2))**2+((z/1000-yy)/(dy/2))**2 <= 1) & ~water_mask
        stats[zone['id']] = {'max_height_m': float(candidate[area].max()),
                             'height_p50_p90_p99_m': np.percentile(candidate[area], [50,90,99]).tolist(),
                             'slope_p50_p95_p99_deg': np.percentile(slope_after[area], [50,95,99]).tolist()}
    result = {'status': 'REGIONAL_LANDFORM_CANDIDATE_NOT_IMPORTED_HYDROLOGY_UNFINISHED',
              'native_baseline_sha256': NATIVE_SHA, 'candidate_sha256': sha(asc),
              'reference_sha256': sha(OUT/'reference.npz'), 'reserve_source_sha256': sha(reserves_path),
              'water_source_sha256': sha(ROOT/'derived/gis/osm_water_wgs84.geojson'),
              'roads_source_sha256': sha(ROOT/'derived/gis/osm_roads_wgs84.geojson'),
              'source_shape': [2048, 2048], 'cell_m': 6, 'changed_vertices': int(changed.sum()),
              'maximum_height_m': float(candidate.max()), 'maximum_raise_m': float((candidate-base).max()),
              'all_protected_vertices_exact': bool(np.array_equal(candidate[controls], base[controls])),
              'reserve_conservation_area_km2': reserve_union.area/1e6,
              'reserve_landcover_cells': {str(int(code)): int((reserve_mask & (cover == code)).sum()) for code in np.unique(cover[reserve_mask])},
              'zones': stats, 'road_reference_features': len(road_shapes),
              'source_slope_max_deg': float(slope_before.max()), 'candidate_slope_max_deg': float(slope_after.max()),
              'limits': ['Water levels, beds and road grades are preserved, not newly engineered or accepted.',
                         'Reserve combines OSM main/north with conservative design envelope and60m margin; not a legal boundary.',
                         'Cover classes reserve future biome areas, not tree placement or forest density.',
                         'No native import, new navmesh, runtime or performance acceptance.']}
    save(EV/'preparation.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
