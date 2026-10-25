"""Clipped, unscaled48m water pieces using verified vanilla pond materials.

Separate lakes retain their levels. River field is quantized into25mm bands;
this discretization must still pass combined geometry and engine consumers.
"""
from pathlib import Path
import argparse,hashlib,json,math
import numpy as np
from affine import Affine
from rasterio.features import rasterize,shapes
from scipy.ndimage import distance_transform_edt
from shapely import make_valid
from shapely.geometry import shape,box,mapping
from shapely.ops import unary_union
from water_mesh import write_water_mesh,polygons
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'
TX=Affine(6,0,-3,0,-6,12285)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--version',choices=['v1','v2'],default='v1')
    version=parser.parse_args().version
    OUT=ROOT/f'tests/regional_foundation_water_assets_{version}'
    SOURCE=OUT/'source/baltic_water'
    assert not OUT.exists(),'Fresh candidate required'
    SOURCE.mkdir(parents=True)
    if version=='v2':
        report=json.loads((EV/'continuous-water-bands-v2.json').read_text())
        assert report['status']=='PASS_SOURCE_BANDS_ONLY' and not report['bad_joints']
        features=json.loads((EV/'water-surfaces-contour-v2.geojson').read_text())['features']
        surfaces=[(shape(f['geometry']),f['properties']['level_m'],f['properties']['body']) for f in features]
        missing=report['missing_area_m2']
    else:
        surfaces,missing=legacy_surfaces()
    generate(surfaces,missing,OUT,SOURCE,version)

def legacy_surfaces():
    standing=json.loads((EV/'standing-water-game.json').read_text())['features']
    levels=json.loads((EV/'lake-design-levels.json').read_text())['bodies']
    surfaces=[(shape(f['geometry']),levels[i]['design_surface_m'],f'lake_{i:03d}') for i,f in enumerate(standing)]
    lakeunion=unary_union([g for g,_,_ in surfaces])
    river=shape(json.loads((EV/'river-engineering-game.json').read_text())['features'][0]['geometry'])
    river=make_valid(river.difference(lakeunion.buffer(-.03)))
    rm=rasterize([(river,1)],out_shape=(2048,2048),transform=TX,dtype='uint8',all_touched=True).astype(bool)
    hydraulic=np.load(ROOT/'tests/regional_foundation_hydrology_v1/hydraulic-field.npz')['surfaces']
    finite=np.isfinite(hydraulic);_,nearest=distance_transform_edt(~finite,return_indices=True)
    field=hydraulic[tuple(nearest)]
    quantized=np.rint(field/.025).astype('int32')
    bands=[]
    for geom,value in shapes(quantized,mask=rm,transform=TX,connectivity=4):
        g=shape(geom).intersection(river)
        if g.area<1e-6:continue
        bands.append(g);surfaces.append((g,float(value)*.025,f'river_band_{int(value):04d}'))
    missing=river.difference(unary_union(bands)).area
    assert missing<.01,missing
    return surfaces,missing

def generate(surfaces,missing,OUT,SOURCE,version):
    poses=[];models=[];full_written=False;requested_area=0.;piece_area=0.;triangle_count=0
    for bi,(geometry,level,body) in enumerate(surfaces):
        if geometry.is_empty:continue
        requested_area+=geometry.area
        xmin,zmin,xmax,zmax=geometry.bounds
        for x in range(math.floor(xmin/48)*48,math.ceil(xmax/48)*48,48):
            for z in range(math.floor(zmin/48)*48,math.ceil(zmax/48)*48,48):
                tile=box(x-.01,z-.01,x+48.01,z+48.01)
                g=make_valid(geometry.intersection(tile))
                if g.area<1e-6:continue
                origin=(x+24,z+24)
                if geometry.covers(tile):
                    name='full_48'
                    if not full_written:
                        report=write_water_mesh(box(-24.01,-24.01,24.01,24.01),SOURCE/f'{name}.p3d',(0,0),uv_local=True)
                        report['name']=name;models.append(report);full_written=True
                else:
                    name=f'edge_{len(models):05d}'
                    report=write_water_mesh(g,SOURCE/f'{name}.p3d',origin,uv_local=True)
                    report['name']=name;models.append(report)
                poses.append({'id':len(poses)+10000,'model':f'baltic_water\\{name}.p3d','position':[origin[0],level,origin[1]],
                              'body':body,'bounds_xz':list(g.bounds),'area_m2':g.area})
                piece_area+=g.area
        if bi%30==0:print(f'Water body/band {bi+1}/{len(surfaces)}, instances={len(poses)}, models={len(models)}',flush=True)
    for item in models:
        item['sha256']=hashlib.sha256((SOURCE/f"{item['name']}.p3d").read_bytes()).hexdigest()
    (SOURCE/'$PBOPREFIX$').write_text('baltic_water')
    (SOURCE/'config.cpp').write_text('class CfgPatches { class Baltic_Water { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Water"}; }; };\n')
    manifest={'status':'GENERATED_NOT_IMPORTED_OR_ACCEPTED','tile_max_span_m':48.02,'scale':1,'river_quantization_m':.025,
              'instances':poses,'models':models,'requested_area_sum_m2':requested_area,'piece_area_with_overlap_m2':piece_area,
              'missing_river_vector_area_m2':missing,'source_surface_sha256':hashlib.sha256((EV/'lake-design-levels.json').read_bytes()).hexdigest(),
              'limits':['25mm quantization does not itself prove all jumps<=50mm; inspect the actual adjacency.',
                        'No native WRP/navmesh or client acceptance from mesh generation.']}
    manifest['source_surface_sha256']=hashlib.sha256((EV/('water-surfaces-contour-v2.geojson' if version=='v2' else 'lake-design-levels.json')).read_bytes()).hexdigest()
    (EV/f'regional-water-assets-{version}.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'instances':len(poses),'models':len(models),'model_triangles':sum(m['triangles'] for m in models),
                      'missing_river_vector_area_m2':missing,'source':str(SOURCE)},indent=2))

if __name__=='__main__':main()
