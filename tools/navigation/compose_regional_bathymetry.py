"""Combine accepted road interiors with separate regional bed/bank engineering.

Design surfaces remain separate from terrain. Main fairway support is wider
than the boat envelope to cover the native NW-SE interpolation triangles.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from rasterio.features import rasterize
from affine import Affine
from shapely import points,distance
from shapely.geometry import shape
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[2]
EV=ROOT/'evidence/regional-foundation-v1'
OUT=ROOT/'tests/regional_foundation_combined_v1'
TX=Affine(6,0,-3,0,-6,12285)

def main():
    assert not OUT.exists(),'Fresh candidate required'
    data=np.load(ROOT/'tests/regional_foundation_hydrology_v1/hydraulic-field.npz')
    base=data['base'];surface=data['surfaces'].copy();ocean=data['ocean'];island=data['islands']
    road=np.load(ROOT/'tests/regional_foundation_roads_v6/reference.npz')
    candidate=road['candidate'].copy()
    river=shape(json.loads((EV/'river-engineering-game.json').read_text())['features'][0]['geometry'])
    lakes=[shape(f['geometry']) for f in json.loads((EV/'standing-water-game.json').read_text())['features']]
    wetgeometry=unary_union(lakes+[river])
    fairways=unary_union([shape(f['geometry']) for f in json.loads((EV/'fairways-main-game.json').read_text())['features']])
    def grid(g):return rasterize([(g,1)],out_shape=(2048,2048),transform=TX,dtype='uint8').astype(bool)
    fairway_support=grid(fairways.buffer(20.5))
    wet=np.isfinite(surface)
    # The ocean needs no custom object. Its measured minimum is0.5m.
    surface[ocean & ~wet]=.5
    surface[ocean]=np.maximum(.5,surface[ocean])
    assert not np.any(fairway_support & ~np.isfinite(surface)),'Fairway leaves known water footprint'
    assert not np.any(fairway_support & island),'Fairway erases an island'
    outside,nearest=distance_transform_edt(~wet,return_indices=True)
    inside=distance_transform_edt(wet)*6
    dry_distance=outside*6
    # Exact shoreline distances near the vector outline, not raster stair steps.
    near=np.where(np.where(wet,inside,dry_distance)<42)
    coordinates=points(near[1]*6,12282-near[0]*6)
    exact=distance(coordinates,wetgeometry.boundary)
    depth_distance=inside.copy();shore_distance=dry_distance.copy()
    iswet=wet[near]
    depth_distance[near[0][iswet],near[1][iswet]]=exact[iswet]
    shore_distance[near[0][~iswet],near[1][~iswet]]=exact[~iswet]
    # Lakes retain broad deep interiors; small shoreline strips taper to zero.
    depth=np.minimum(8.,.25*depth_distance)
    candidate[wet]=np.minimum(candidate[wet],surface[wet]-depth[wet])
    candidate[fairway_support]=np.minimum(candidate[fairway_support],surface[fairway_support]-3.5)
    nearest_surface=surface[tuple(nearest)]
    dry=(~wet)&(~ocean)&(shore_distance<36)
    # Smaller bank support is now possible with clipped model footprints. At
    # the edge use0.35m freeboard, blend over24m beyond the12m support strip.
    t=np.clip((36-shore_distance)/24,0,1);t=t*t*(3-2*t)
    target=base+np.maximum(0,nearest_surface+.35-base)*t
    candidate[dry]=np.maximum(candidate[dry],target[dry])
    assert np.isfinite(candidate).all()
    changed=candidate!=base
    OUT.mkdir(parents=True)
    asc=OUT/'baltic_regional_foundation_v1.asc'
    with asc.open('w',encoding='ascii',newline='\n') as handle:
        handle.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(handle,candidate,fmt='%.9g')
    with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),candidate)
    np.savez_compressed(OUT/'reference.npz',base=base,candidate=candidate,surfaces=surface,wet=wet,ocean=ocean,islands=island,
                        fairway_support=fairway_support,bank_support=dry,changed=changed)
    report={'status':'COMPOSED_NOT_ACCEPTED','asc_sha256':hashlib.sha256(asc.read_bytes()).hexdigest(),
            'changed_vertices':int(changed.sum()),'fairway_support_vertices':int(fairway_support.sum()),
            'minimum_vertex_clearance_m':float(np.min(surface[fairway_support]-candidate[fairway_support])),
            'maximum_cut_m':float((base-candidate).max()),'maximum_raise_m':float((candidate-base).max()),
            'limits':['Native triangles, bank slopes, road junctions and water objects require independent combined-layer checks.']}
    (EV/'combined-foundation-v1.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
