"""Separate lake surface design from bed and banks; immutable regional source.

The vertical offset preserves relative inherited water elevations while keeping
low inland water above the measured ocean range. These are game design levels,
not revised real-world survey heights. No water objects or native import here.
"""
import hashlib,json,sys
from pathlib import Path
import numpy as np
import rasterio
from rasterio.features import rasterize
from affine import Affine
from scipy.ndimage import distance_transform_edt
from shapely import points,distance
from shapely.geometry import shape
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from geo_common import save_json
EV=ROOT/'evidence/regional-foundation-v1'
OUT=ROOT/'tests/regional_foundation_water_v2'
TX=Affine(6,0,-3,0,-6,12285)


def main():
    assert not OUT.exists(),'Fresh candidate required'
    source=ROOT/'tests/regional_outline_v3/baltic_regional_outline_v3.asc'
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='3e2f6a9643ba4a8c58a86534c75de6033b7dbdf7a3de5d09a5ea46ff66680ac6'
    with rasterio.open(source) as ds:base=ds.read(1)
    candidate=base.copy()
    original_wet=np.load(ROOT/'tests/regional_outline_v3/reference.npz')['water'].astype(bool)
    bodies=json.loads((EV/'standing-water-game.json').read_text(encoding='utf-8'))['features']
    lake_ids=np.full(base.shape,-1,dtype='int32')
    surfaces=np.full(base.shape,np.nan,dtype='float32')
    shore_support=np.zeros(base.shape,dtype=bool)
    designs=[]
    for bi,feature in enumerate(bodies):
        g=shape(feature['geometry']);props=feature['properties']
        median=props['terrain_p10_median_p90'][1]
        level=round(max(1.4,median+1.25),2)
        xmin,zmin,xmax,zmax=g.bounds
        c0=max(0,int((xmin-84)//6));c1=min(2048,int((xmax+84)//6)+2)
        r0=max(0,int((12282-zmax-84)//6));r1=min(2048,int((12282-zmin+84)//6)+2)
        mask=rasterize([(g,1)],out_shape=(r1-r0,c1-c0),transform=TX*Affine.translation(c0,r0),dtype='uint8').astype(bool)
        if not mask.any():continue
        inside=distance_transform_edt(mask)*6
        outside=distance_transform_edt(~mask)*6
        # Exact boundary distances only where they affect shore/bed; deep interiors saturate.
        near=np.where(np.where(mask,inside,outside)<=84)
        pp=points((near[1]+c0)*6,12282-(near[0]+r0)*6)
        exact=distance(pp,g.boundary)
        d=np.where(mask,inside,outside)
        d[near]=exact
        tile=candidate[r0:r1,c0:c1]
        original=base[r0:r1,c0:c1]
        depth=np.minimum(8.,.25*d)
        tile[mask]=np.minimum(tile[mask],level-depth[mask])
        dry=(~mask)&(~original_wet[r0:r1,c0:c1])&(d<80)
        # Boundary-piece spill is not allowed to create secondary puddles on land.
        t=np.clip((80-d)/40,0,1);weight=t*t*(3-2*t)
        raised=original+np.maximum(0,level+.35-original)*weight
        tile[dry]=np.maximum(tile[dry],raised[dry])
        shore_support[r0:r1,c0:c1]|=dry
        ids=lake_ids[r0:r1,c0:c1]
        if np.any(mask&(ids>=0)):raise ValueError('Deduplicated basins overlap at native sample')
        ids[mask]=bi
        surfaces[r0:r1,c0:c1][mask]=level
        designs.append({'id':props['id'],'index':bi,'names':props['names'],'source_ids':props['source_ids'],
                        'area_m2':g.area,'inherited_surface_median_m':median,'design_surface_m':level,
                        'maximum_design_depth_m':8,'bank_target_freeboard_m':.35,
                        'native_wet_vertices':int(mask.sum()),'islands_retained_in_vector':len(g.interiors)})
        if bi%30==0:print(f'Lake {bi+1}/{len(bodies)} prepared',flush=True)
    changed=candidate!=base
    assert not np.any(changed&~((lake_ids>=0)|shore_support))
    assert np.isfinite(candidate).all()
    OUT.mkdir(parents=True)
    asc=OUT/'baltic_lake_bathymetry_v2.asc'
    with asc.open('w',encoding='ascii',newline='\n') as handle:
        handle.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(handle,candidate,fmt='%.9g')
    with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),candidate)
    np.savez_compressed(OUT/'reference.npz',base=base,candidate=candidate,lake_ids=lake_ids,surfaces=surfaces,shore_support=shore_support,changed=changed)
    save_json(EV/'lake-design-levels.json',{'status':'CANDIDATE_NOT_IMPORTED','vertical_design':'Inherited physical median +1.25m; minimum1.4m. Preserves relative lake levels without placing low lakes below ocean range.',
        'bodies':designs,'candidate_sha256':hashlib.sha256(asc.read_bytes()).hexdigest(),
        'changed_vertices':int(changed.sum()),'maximum_cut_m':float((base-candidate).max()),'maximum_raise_m':float((candidate-base).max()),
        'limits':['Surface heights are gameplay design; DSM is not bathymetry.','Rivers, object footprints and continuous depth still need combined-layer validation.',
                  'Small water references below900m2 are retained for later detail; no claim of complete sub-cell hydrology.']})
    print(json.dumps({'bodies':len(designs),'changed_vertices':int(changed.sum()),'candidate':str(asc)}))


if __name__=='__main__':main()
