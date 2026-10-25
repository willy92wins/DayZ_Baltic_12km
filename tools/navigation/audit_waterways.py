"""Audit installed heightfield at named reference axes, without claiming bathymetry."""
import json
import numpy as np
import shapefile
from shapely import STRtree, make_valid
from shapely.geometry import shape, LineString, Point
from shapely.ops import unary_union
from waterway_common import ROOT, BASE_SHA, RIVERS, sha, read_base, sample, river_features, river_group, tb_geometry


def main():
    h = read_base()
    polygons = []
    water_hashes = {}
    for name in ('water', 'ocean'):
        path = ROOT / f'derived/tb/source/vectors/{name}.shp'
        water_hashes[name] = sha(path)
        with shapefile.Reader(str(path)) as reader:
            polygons.extend(make_valid(shape(s.__geo_interface__)) for s in reader.iterShapes())
    tree = STRtree(polygons)
    results = []
    for feature in river_features():
        group = river_group(feature['properties'])
        if not group:
            continue
        geom = tb_geometry(shape(feature['geometry']))
        for line in geom.geoms if hasattr(geom, 'geoms') else [geom]:
            for station in np.arange(1, line.length, 12):
                p = line.interpolate(station)
                if not 200006 < p.x < 212276 or not 6 < p.y < 12276:
                    continue
                a = line.interpolate(max(0, station-1)); b = line.interpolate(min(line.length, station+1))
                tangent = np.array([b.x-a.x, b.y-a.y]); tangent /= np.linalg.norm(tangent)
                normal = np.array([-tangent[1], tangent[0]])
                cross = LineString([np.array(p.coords[0])-250*normal, np.array(p.coords[0])+250*normal])
                hits = tree.query(cross, predicate='intersects')
                wet = cross.intersection(unary_union([polygons[i] for i in hits]))
                intervals = list(wet.geoms) if hasattr(wet, 'geoms') else [wet]
                containing = [part for part in intervals if part.geom_type == 'LineString' and part.distance(p) < .001]
                width = max((part.length for part in containing), default=0.)
                ground = float(sample(h, p.x, p.y))
                results.append({'river': group, 'osm_id': feature['properties']['osm_id'],
                    'x': p.x-200000, 'z': p.y, 'station_on_way_m': float(station),
                    'reference_wet_width_m': width, 'width_censored_at_500m': width > 499.99,
                    'ground_y_m': ground, 'depth_if_connected_to_sea_min_0_5_m': .5-ground})
    summary = {}
    for name in sorted({r['river'] for r in results}):
        rows = [r for r in results if r['river'] == name]
        widths = [r['reference_wet_width_m'] for r in rows]
        depths = [r['depth_if_connected_to_sea_min_0_5_m'] for r in rows]
        summary[name] = {'samples': len(rows), 'unique_ways': len({r['osm_id'] for r in rows}),
            'width_p0_p50_p100_m': np.percentile(widths, [0, 50, 100]).tolist(),
            'height_p0_p50_p100_m': np.percentile([r['ground_y_m'] for r in rows], [0, 50, 100]).tolist(),
            'samples_depth_at_least_3m_if_sea': sum(d >= 3 for d in depths),
            'samples_dry_at_sea_min': sum(d <= 0 for d in depths)}
    report = {'status': 'BASELINE_AUDIT_NOT_NAVIGATION_PASS', 'native_sha256': BASE_SHA,
        'river_source_sha256': sha(RIVERS), 'water_source_hashes': water_hashes,
        'limits': ['Samples on axes every12m; not area statistics or continuous passage proof.',
                  'Sea level0.5 is conditional: no assertion that inland elevated water exists.',
                  'Reference wet width measures the single polygon interval containing the axis; islands/gaps excluded.',
                  'Names can include branches; sample counts do not assert a connected route.'],
        'summary': summary, 'samples': results}
    (ROOT / 'evidence/navigation/baseline-waterways.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
