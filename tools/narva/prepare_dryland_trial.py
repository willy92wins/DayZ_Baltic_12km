"""Prepare a reversible local Narva land-clearance trial; never edits input files."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np,rasterio,shapefile
from shapely.geometry import shape,box
from shapely.ops import unary_union
from shapely import make_valid,contains_xy,distance,points

ap=argparse.ArgumentParser()
for n in ('repo','observation','out'):ap.add_argument('--'+n,type=Path,required=True)
a=ap.parse_args(); assert not a.out.exists()
observed=json.loads(a.observation.read_text())
assert observed['status']=='FAIL_DRY_LAND_FLOODING' and observed['samples']==441
maximum=observed['sea_readings']['sea_max'];minimum=observed['sea_readings']['sea_min']
assert maximum==1 and minimum==.5, 'Reassess design for a different measured range'
dry_floor=maximum+.25;shore=(maximum+minimum)/2
source=a.repo/'tests/narva_trial_v2/narva_engine_aligned_v2.asc'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)=='1326175fa0a53db2c69fba7e13767a57f7cb4475defaa5d32d8e55fe1a2b4856'
with rasterio.open(source) as ds:base=ds.read(1)
with rasterio.open(a.repo/'derived/gis/worldcover_2021_3857.tif') as ds:cover=ds.read(1)
rr,cc=np.mgrid[:2048,:2048];xx=cc*6.;yy=(2047-rr)*6.
core=[1500,6200,3500,8200];transition=120
outer=box(200000+core[0]-transition,core[1]-transition,200000+core[2]+transition,core[3]+transition)
active=(xx>=core[0]-transition)&(xx<=core[2]+transition)&(yy>=core[1]-transition)&(yy<=core[3]+transition)
parts=[];vector_hashes={}
for name in ('ocean','water'):
    p=a.repo/f'derived/tb/source/vectors/{name}.shp';vector_hashes[name]=sha(p)
    with shapefile.Reader(str(p)) as reader:
        for s in reader.iterShapes(bbox=outer.buffer(60).bounds):
            g=make_valid(shape(s.__geo_interface__)).intersection(outer.buffer(60))
            if not g.is_empty:parts.append(g)
water=unary_union(parts)
inside=contains_xy(water,200000+xx[active],yy[active])
dist=distance(points(200000+xx[active],yy[active]),water.boundary)
dry=(~inside)&(cover[active]!=80)
edge=np.minimum.reduce([xx[active]-(core[0]-transition),core[2]+transition-xx[active],yy[active]-(core[1]-transition),core[3]+transition-yy[active]])
weight=np.clip(edge/transition,0,1)
floor=shore+(dry_floor-shore)*np.clip(dist/12,0,1)
delta_local=np.maximum(0,floor-base[active])*weight*dry
candidate=base.copy();candidate[active]+=delta_local
delta=candidate-base;changed=delta!=0
assert np.all(delta[~active]==0) and np.all(delta>=0)
assert np.all(delta[active][inside|(cover[active]==80)]==0)
protected=(xx>=core[0])&(xx<=core[2])&(yy>=core[1])&(yy<=core[3])
protected_local=protected[active]&dry&(dist>=12)
assert np.all(candidate[active][protected_local]>=dry_floor-.00001)
# Independent frozen flooded sample list must now be above API maximum.
bad=observed['flooded_dry_samples'];predicted=[]
for p in bad:
    r=int((12282-p['north'])/6);c=int(p['x']/6)
    predicted.append(float(candidate[r,c]));assert candidate[r,c]>maximum
# Keep all terrain already at/above deck elevation exactly unchanged.
assert np.all(candidate[base>=2]==base[base>=2])
a.out.mkdir(parents=True)
asc=a.out/'narva_dryland_v1.asc'
with asc.open('w',encoding='ascii',newline='\n') as f:
    f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
    np.savetxt(f,candidate,fmt='%.4f')
with rasterio.open(asc) as ds:roundtrip=ds.read(1)
assert np.max(abs(roundtrip-candidate))<=.000051
assert np.all(roundtrip[~changed]==base[~changed])
np.savez_compressed(a.out/'delta.npz',row=np.where(changed)[0],col=np.where(changed)[1],delta=delta[changed])
result={'status':'PREPARED_NOT_IMPORTED','source_sha256':sha(source),'candidate_sha256':sha(asc),
 'observation_sha256':sha(a.observation),'core_local_bounds_m':core,'transition_m':transition,
 'dry_interior_floor_m':dry_floor,'shore_midpoint_m':shore,'bank_ramp_m':12,
 'changed_vertices':int(changed.sum()),'maximum_raise_m':float(delta.max()),
 'water_vertices_unchanged':True,'outside_sector_unchanged':True,'vertices_at_or_above_2m_unchanged':True,
 'protected_dry_interior_vertices':int(protected_local.sum()),
 'previously_flooded_samples':len(bad),'previously_flooded_sample_predicted_minimum_m':min(predicted),
 'source_water_shp_sha256':vector_hashes,
 'limits':['No native import/render/probe yet; no player traversal.',
 'Only a local height clearance trial, not a final global relief coefficient.',
 'Source water polygons unchanged; interpolated shoreline still requires comparison.',
 'WorldCover water exclusion is conservative and may disagree with OSM locally.']}
(a.out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
