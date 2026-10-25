"""Local Narva trial using observed native vertex coordinates; no global shift."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np, rasterio, shapefile
from shapely import make_valid, contains_xy, distance, points
from shapely.geometry import shape, box
from shapely.ops import unary_union

ap=argparse.ArgumentParser()
ap.add_argument('--repo',type=Path,required=True)
ap.add_argument('--fit',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
args=ap.parse_args(); args.out.mkdir(parents=True,exist_ok=False)
fit=json.loads(args.fit.read_text()); cx,cy=fit['bridge_centre_tb']; u=np.array(fit['axis_east_unit']); side=np.array([u[1],-u[0]])
source=args.repo/'source/baltic_physical_2048_6m.asc'
with rasterio.open(source) as ds: base=ds.read(1)
rr,cc=np.mgrid[0:2048,0:2048]
# Empirical consumer contract from 289 grid + 289 held-out profile readings.
xx=200000+cc*6.; yy=(2047-rr)*6.
radius=np.hypot(xx-cx,yy-cy); active=radius<48
area=box(cx-80,cy-80,cx+80,cy+80); parts=[]
with shapefile.Reader(str(args.repo/'derived/tb/source/vectors/water.shp')) as reader:
    for s in reader.iterShapes(bbox=area.bounds):
        part=make_valid(shape(s.__geo_interface__)).intersection(area)
        if not part.is_empty: parts.append(part)
water=unary_union(parts)
candidate=base.copy(); inside=contains_xy(water,xx[active],yy[active]); dist=distance(points(xx[active],yy[active]),water.boundary)
target=.1+np.where(inside,-np.minimum(2.,dist*.8),np.minimum(1.4,dist*.45))
blend=np.clip((48-radius[active])/12,0,1)
candidate[active]=base[active]*(1-blend)+target*blend
along=(xx-cx)*u[0]+(yy-cy)*u[1]; across=(xx-cx)*side[0]+(yy-cy)*side[1]
# Extend support beneath bridge ends so interpolation can meet the deck.
pad=(np.abs(along)>=8)&(np.abs(along)<36)&(np.abs(across)<11)&active
lw=np.clip((36-np.abs(along[pad]))/18,0,1); sw=np.clip((11-np.abs(across[pad]))/3,0,1)
pad_in_water=contains_xy(water,xx[pad],yy[pad])
weight=lw*sw*(~pad_in_water)
candidate[pad]=candidate[pad]*(1-weight)+2*weight
# Explicit support triangles for an 8 m wide landing, from each end to 18 m.
# Any support vertex inside source water is left untouched and reported.
dd,ww=np.meshgrid(np.r_[np.arange(-18,-12.49,.25),np.arange(12.5,18.01,.25)],np.arange(-4,4.01,.25))
sx=cx+u[0]*dd+side[0]*ww; sy=cy+u[1]*dd+side[1]*ww
sc=(sx-200000)/6; sr=(12282-sy)/6
ci=np.floor(sc).astype(int); ri=np.floor(sr).astype(int); upper=(sr-ri)<=(sc-ci)
rows=np.concatenate([ri.ravel(),(ri+1).ravel(),np.where(upper,ri,ri+1).ravel()])
cols=np.concatenate([ci.ravel(),(ci+1).ravel(),np.where(upper,ci+1,ci).ravel()])
support=np.unique(np.column_stack([rows,cols]),axis=0); rows,cols=support.T
support_wet=contains_xy(water,xx[rows,cols],yy[rows,cols])
assert np.all(radius[rows,cols]<48)
candidate[rows[~support_wet],cols[~support_wet]]=2

def interp(x,y):
    c=(x-200000)/6.; r=(12282-y)/6.
    ci=np.floor(c).astype(int); ri=np.floor(r).astype(int); a=c-ci; b=r-ri
    z00=candidate[ri,ci]; z10=candidate[ri,ci+1]; z01=candidate[ri+1,ci]; z11=candidate[ri+1,ci+1]
    return np.where(b<=a,z00*(1-a)+z10*(a-b)+z11*b,z00*(1-b)+z01*(b-a)+z11*a)

ends=[]
for d in [-12.5,12.5]:
    width=np.linspace(-4,4,161)
    heights=interp(cx+u[0]*d+side[0]*width,cy+u[1]*d+side[1]*width)
    ends.append({'along_m':d,'sample_width_m':8,'min_m':float(heights.min()),'max_m':float(heights.max()),'max_gap_m':float(np.max(abs(2-heights)))})
delta=candidate-base; changed=delta!=0
assert np.all(delta[radius>=48]==0)
asc=args.out/'narva_engine_aligned_v2.asc'
with asc.open('w',encoding='ascii',newline='\n') as f:
    f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
    np.savetxt(f,candidate,fmt='%.4f')
np.savez_compressed(args.out/'terrain_delta.npz',row=np.where(changed)[0],col=np.where(changed)[1],delta=delta[changed])
manifest={'status':'PREPARED_NOT_IMPORTED','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(asc.read_bytes()).hexdigest(),'modified_nodes':int(changed.sum()),'max_change_m':float(abs(delta).max()),'outside_48m_unchanged':True,'native_vertex_formula':'x=200000+6*col, north=6*(2047-row)','native_interpolation':'NW_SE diagonal in row-down array','water_polygon_buffer_m':0,'approach_nodes_inside_source_water_raised':0,'support_vertices_excluded_inside_water':int(support_wet.sum()),'predicted_bridge_ends':ends,'limits':['Local trial only; engine registration verified only around Narva.','Original regional terrain is not shifted.','Predicted endpoints require native re-probe. Water, collision and traversal remain unvalidated.','Water polygon is unchanged, but sampled shoreline cannot exactly follow sub-cell geometry.']}
(args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
