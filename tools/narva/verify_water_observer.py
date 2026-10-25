"""Compare authentic Buldozer water reads with unchanged GIS shore references."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np, rasterio, shapefile
from shapely.geometry import shape, box
from shapely.ops import unary_union
from shapely import make_valid, contains_xy, distance, points

ap=argparse.ArgumentParser()
for name in ('repo','log','out'):
    ap.add_argument('--'+name,type=Path,required=True)
ap.add_argument('--native',type=Path)
a=ap.parse_args()
lines=a.log.read_text().splitlines()
assert lines[0]=='BALTIC_WATER_OBSERVER_V1' and lines[-1]=='END_BALTIC_WATER_OBSERVER_V1'
meta=dict(l.split('=',1) for l in lines if '=' in l)
assert set(meta)=={'sea_min','sea_max','sea_now','wave_max','wave_now'}
meta={k:float(v) for k,v in meta.items()}
assert all(np.isfinite(v) for v in meta.values()) and meta['sea_min']<=meta['sea_now']<=meta['sea_max']
records=[l.split(';')[1:] for l in lines if l.startswith('G;')]
assert len(records)==441 and all(len(r)==8 for r in records)
assert all(r[3] in ('true','false') and r[4] in ('true','false') for r in records)
data=np.array([[float(v) if k not in (3,4) else float(v=='true') for k,v in enumerate(r)] for r in records])
assert np.isfinite(data).all()
x,z,h,sea,pond,depth,surface,fake=data.T
expected={(1800+i*60,6300+j*60) for i in range(21) for j in range(21)}
assert len(set(zip(x,z)))==441 and set(zip(x,z))==expected
native=a.native or a.repo/'tb/narva_trial/narva_tb_export_v2.asc'
with rasterio.open(native) as src: height=src.read(1)
col=(x/6).astype(int);row=((12282-z)/6).astype(int)
assert np.max(abs(height[row,col]-h))<=.00501
area=box(201700,6200,203100,7600);parts=[]
for name in ('ocean','water'):
    with shapefile.Reader(str(a.repo/f'derived/tb/source/vectors/{name}.shp')) as reader:
        for s in reader.iterShapes(bbox=area.bounds):
            g=make_valid(shape(s.__geo_interface__)).intersection(area)
            if not g.is_empty: parts.append(g)
water=unary_union(parts); inside=contains_xy(water,x+200000,z)
dist=distance(points(x+200000,z),water.boundary)
with rasterio.open(a.repo/'derived/gis/worldcover_2021_3857.tif') as src: cover=src.read(1)
dry=(~inside)&(cover[row,col]!=80)&(dist>12)
wet=(depth>.02)&(sea.astype(bool))&(~pond.astype(bool))
bad=np.where(dry&wet)[0]
below_max=int((dry&(h<=meta['sea_max'])).sum())
status='PASS_SAMPLED_DRY_INTERIOR'
if below_max:status='FAIL_DRY_LAND_CLEARANCE'
if len(bad):status='FAIL_DRY_LAND_FLOODING'
result={'status':status,
 'log_sha256':hashlib.sha256(a.log.read_bytes()).hexdigest(),'samples':441,'sea_readings':meta,
 'native_source':str(native),'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),
 'terrain_matches_saved_native_max_error_m':float(np.max(abs(height[row,col]-h))),
 'reference_dry_interior_samples':int(dry.sum()),'runtime_wet_dry_interior_samples':len(bad),
 'dry_interior_samples_at_or_below_sea_max':below_max,
 'flooded_dry_samples':[{'x':float(x[i]),'north':float(z[i]),'terrain':float(h[i]),'depth_at_terrain':float(depth[i]),'distance_to_reference_water_m':float(dist[i])} for i in bad],
 'limits':['441 points in Narva, no exhaustive regional traversal or water topology test.',
 'Maximum is API-reported for this Buldozer session; player runtime/config must be checked separately.',
 'Point queries prove positive depth over sampled dry land, not exact flooded polygon area.']}
a.out.parent.mkdir(parents=True,exist_ok=True)
assert not a.out.exists()
a.out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='flooded_dry_samples'},indent=2))
raise SystemExit(0 if status=='PASS_SAMPLED_DRY_INTERIOR' else 1)
