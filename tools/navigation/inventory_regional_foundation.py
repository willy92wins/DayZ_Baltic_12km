"""Deduplicate water polygons without filling islands; retain every source ID.

Output is an engineering inventory, not accepted water or a terrain edit.
All geometry uses game X/Z metres, not longitude/latitude.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import numpy as np
import rasterio
from rasterio.features import rasterize
from affine import Affine
from shapely import make_valid, STRtree
from shapely.geometry import shape, mapping, box
from shapely.affinity import translate
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
from geo_common import tb_geometry, save_json
from waterway_common import river_group

OUT = ROOT/'evidence/regional-foundation-v1'
FRAME = box(0, 0, 12282, 12282)
TX = Affine(6, 0, -3, 0, -6, 12285)


def polygons(g):
    if g.geom_type == 'Polygon':
        yield g
    elif hasattr(g, 'geoms'):
        for part in g.geoms:
            yield from polygons(part)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--standing-only',action='store_true',help='Exclude tagged rivers/canals before union; suitable for basin level assignment.')
    args=parser.parse_args()
    path = ROOT/'derived/gis/osm_water_wgs84.geojson'
    sources = json.loads(path.read_text(encoding='utf-8'))['features']
    geometries, properties = [], []
    for f in sources:
        if args.standing_only and (f['properties'].get('water') in {'river','canal','stream'} or f['properties'].get('waterway') in {'riverbank','river','canal','stream'}):
            continue
        g = translate(make_valid(tb_geometry(shape(f['geometry']))), xoff=-200000).intersection(FRAME)
        if not g.is_empty:
            geometries.append(g)
            properties.append(f['properties'])
    tree = STRtree(geometries)
    merged = sorted(polygons(unary_union(geometries)), key=lambda g: -g.area)
    print(f'Union: {len(geometries)} sources -> {len(merged)} disjoint polygons', flush=True)
    with rasterio.open(ROOT/'tests/regional_outline_v3/baltic_regional_outline_v3.asc') as ds:
        terrain = ds.read(1)
    large, small = [], []
    for index, g in enumerate(merged):
        ids = tree.query(g, predicate='intersects')
        src = [properties[int(i)] for i in ids if geometries[int(i)].intersection(g).area > .01]
        names = sorted({str(p[k]) for p in src for k in p if k.startswith('name') and p[k]})
        record = {'id':f'water_{index:05d}', 'area_m2':g.area,
                  'source_ids':sorted({p['osm_id'] for p in src}), 'names':names,
                  'types':sorted({str(p.get('water', 'unknown')) for p in src}),
                  'islands_count':len(g.interiors),
                  'islands_area_m2':sum(shape({'type':'Polygon','coordinates':[list(r.coords)]}).area for r in g.interiors)}
        if g.area < 900:
            small.append(record)
            continue
        # Windowed raster sampling at the verified native vertices; no old GIS-centre assumption.
        xmin,zmin,xmax,zmax = g.bounds
        c0=max(0,int(xmin//6)); c1=min(2048,int(xmax//6)+2)
        r0=max(0,int((12282-zmax)//6)); r1=min(2048,int((12282-zmin)//6)+2)
        mask=rasterize([(g,1)],out_shape=(r1-r0,c1-c0),transform=TX*Affine.translation(c0,r0),dtype='uint8').astype(bool)
        values=terrain[r0:r1,c0:c1][mask]
        record['native_vertices']=int(values.size)
        record['terrain_p10_median_p90']=np.percentile(values,[10,50,90]).tolist() if values.size else None
        p=g.representative_point()
        record['representative_xz']=[p.x,p.y]
        record['status']='INVENTORIED_NOT_ENGINEERED'
        large.append({'type':'Feature','properties':record,'geometry':mapping(g)})
    rivers=[]
    for f in json.loads((ROOT/'derived/gis/osm_rivers_wgs84.geojson').read_text(encoding='utf-8'))['features']:
        group=river_group(f['properties'])
        if not group:
            continue
        g=translate(tb_geometry(shape(f['geometry'])),xoff=-200000).intersection(FRAME)
        if g.is_empty:
            continue
        rivers.append({'type':'Feature','properties':dict(f['properties'],group=group),'geometry':mapping(g)})
    prefix='standing-water' if args.standing_only else 'water'
    geometry_name='standing-water-game.json' if args.standing_only else 'water-bodies-game.json'
    save_json(OUT/geometry_name,{'type':'FeatureCollection','coordinate_system':'local game X/Z metres; vertex domain 0..12282','features':large})
    save_json(OUT/'main-rivers-game.json',{'type':'FeatureCollection','coordinate_system':'local game X/Z metres','features':rivers})
    save_json(OUT/f'small-{prefix}-reference.json',small)
    report={'status':'INVENTORY_ONLY','standing_only':args.standing_only,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'source_features':len(sources),'unique_polygons':len(merged),'engineerable_polygons_ge_900m2':len(large),
            'water_union_area_m2':sum(g.area for g in merged),'represented_area_m2':sum(f['properties']['area_m2'] for f in large),
            'small_reference_count':len(small),'small_reference_area_m2':sum(r['area_m2'] for r in small),
            'islands_retained':sum(len(g.interiors) for g in merged),'main_river_features':len(rivers),
            'limitations':['900m2 is an inventory prioritization threshold, not permission to erase smaller water.',
                           'Existing DSM terrain elevation is not bathymetry or accepted water level.',
                           'Union removes overlapping relations; no buffering/simplification or hole removal.',
                           'The unrestricted union represents connected water systems, not single-level lakes.']}
    save_json(OUT/f'{prefix}-inventory.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
