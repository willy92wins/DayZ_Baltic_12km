"""Freeze regional probe points against existing GIS; never edit terrain."""
import sys
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import rasterio
import shapefile
from shapely import make_valid, contains_xy, distance, points
from shapely.geometry import shape
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from geo_common import game_xy

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--repo', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args()
if a.out.exists():
    raise ValueError('Fresh output required')
native = a.repo/'tb/narva_trial/narva_tb_dryland_v1.asc'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
if sha(native) != '7832f0a9d05cb472bc419bd6600b3034b07832b14e55e0a86fe1bf6d10c9d5dc':
    raise ValueError('Native height reference changed')
with rasterio.open(native) as ds:
    height = ds.read(1)
with rasterio.open(a.repo/'derived/gis/worldcover_2021_3857.tif') as ds:
    cover = ds.read(1)
geo = json.loads((a.repo/'evidence/georef-v0.json').read_text(encoding='utf-8'))
regions = []
for p in geo['points']:
    x,z = game_xy(p['lon'], p['lat'])
    regions.append({'name':p['name'], 'x':float(x), 'z':float(z), 'source':'georef-v0'})
osm = json.loads((a.repo/'derived/gis/osm_places_wgs84.geojson').read_text(encoding='utf-8'))
towns = {'node/244217868':'Kronstadt', 'node/276637832':'Mshinskaya', 'node/373930564':'Shlisselburg'}
for f in osm['features']:
    ident = f['properties']['osm_id']
    if ident in towns:
        x,z = game_xy(*f['geometry']['coordinates'])
        regions.append({'name':towns[ident], 'x':float(x), 'z':float(z), 'source':ident})
if len(regions) != 11:
    raise ValueError('Missing regional anchors')
samples = {(x,z):'regional-grid' for x in range(192,12288,384) for z in range(192,12288,384)}
for region in regions:
    x,z = round(region['x']/6)*6, round(region['z']/6)*6
    for dx in range(-240,241,120):
        for dz in range(-240,241,120):
            if 0 <= x+dx <= 12282 and 0 <= z+dz <= 12282:
                samples[(x+dx,z+dz)] = region['name']
xy = np.array(sorted(samples))
x,z = xy.T
parts = []
source_hashes = {}
for name in ('ocean','water'):
    p = a.repo/f'derived/tb/source/vectors/{name}.shp'
    source_hashes[name] = sha(p)
    with shapefile.Reader(str(p)) as reader:
        for item in reader.iterShapes():
            parts.append(make_valid(shape(item.__geo_interface__)))
water = unary_union(parts)
inside = contains_xy(water, x+200000, z)
dist = distance(points(x+200000,z),water.boundary)
rows = ((12282-z)/6).astype(int)
cols = (x/6).astype(int)
classes = cover[rows,cols]
dry = (~inside) & (dist>24) & np.isin(classes,[10,20,30,40,50,60])
records = [dict(x=int(px), z=int(pz), region=samples[(int(px),int(pz))],
                native_height=float(height[rr,cc]), worldcover=int(c),
                inside_osm_water=bool(w), distance_water_m=float(dd), dry_interior=bool(d))
           for px,pz,rr,cc,c,w,dd,d in zip(x,z,rows,cols,classes,inside,dist,dry)]
result = {'status':'FROZEN_OFFLINE_REFERENCE_NOT_ENGINE', 'native_sha256':sha(native),
          'source_water_hashes':source_hashes, 'regions':regions, 'samples':records,
          'dry_interior_count':int(dry.sum()),
          'dry_native_at_or_below_previous_sea_max_1m':int((dry & (height[rows,cols]<=1)).sum()),
          'limit':'Stratified point sample, no exact area estimate; prior sea maximum must be remeasured in this runtime.'}
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='samples'},indent=2))
