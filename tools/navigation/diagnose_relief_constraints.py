"""Factor-isolation experiment on the v1 constraints; does not export terrain."""
import json
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter
from scipy.ndimage import binary_dilation
from prepare_regional_outline import ease, raster, features
from geo_common import tb_geometry
from shapely.geometry import shape

ROOT=Path(__file__).resolve().parents[2]
ref=np.load(ROOT/'tests/regional_outline_v1/reference.npz')
with rasterio.open(ROOT/'source/baltic_physical_2048_6m.asc') as ds:
    physical=ds.read(1)
x,z=np.meshgrid(np.arange(2048)*6.,12282-np.arange(2048)*6.)
a=np.exp(-.5*(((x-5900)/1700)**2+((z-7950)/1500)**2))
b=np.exp(-.5*(((x-4500)/1700)**2+((z-1100)/1550)**2))
macro=gaussian_filter(np.maximum(physical,0).astype('float64'),9)
uplift=np.maximum(0,macro*(5+15*a+19*b)-ref['base'])
south=(((x-4550)/2150)**2+((z-1750)/1450)**2<=1)&~ref['water']
with rasterio.open(ROOT/'derived/gis/worldcover_2021_3857.tif') as ds:
    cover=ds.read(1)
river=raster([tb_geometry(shape(f['geometry'])).buffer(18) for f in features('rivers')])
fixed=ref['reserve']|ref['spb']|ref['narva']|ref['road_core']|(x<24)|(x>12258)|(z<24)|(z>12258)
cases={'v1_all_constraints':ref['controls'],
       'remove_road_constraint_only':ref['protected'],
       'remove_river_line_constraint_only':fixed|ref['wetlands']|binary_dilation(ref['water']|(cover==80),iterations=3),
       'remove_wetland_constraint_only':fixed|binary_dilation(ref['water']|river|(cover==80),iterations=3),
       'water_polygons_reserve_spb_narva_only':ref['water']|ref['reserve']|ref['spb']|ref['narva']}
result={}
for name,mask in cases.items():
    distance=distance_transform_edt(~mask,sampling=6)
    weight=ease(distance/330)
    h=ref['base']+gaussian_filter(uplift*weight,5)*weight
    result[name]={'protected_fraction':float(mask.mean()),'maximum_m':float(h.max()),
                  'south_max_m':float(h[south].max()),'south_p50_p90_p99_m':np.percentile(h[south],[50,90,99]).tolist(),
                  'south_unprotected_distance_p50_p90_p99_m':np.percentile(distance[south],[50,90,99]).tolist()}
report={'status':'ISOLATION_EXPERIMENT_NOT_TERRAIN','fixed_parameters':'same baseline, source, target field,330m transition and30m smoothing',
        'cases':result,'limit':'Removing protection here is diagnostic only; not authorization to alter a wetland or water body.'}
(ROOT/'evidence/regional-outline-v1/constraint-isolation-expanded.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(report,indent=2))
