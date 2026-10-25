"""Reproject source rasters into the approved frame, with no terrain sculpting."""
import hashlib,json
import numpy as np
import rasterio
from rasterio.warp import reproject,Resampling
from geo_common import *

def write_tif(path,array,crs='EPSG:3857',transform=SOURCE_TRANSFORM,nodata=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    with rasterio.open(path,'w',driver='GTiff',height=N,width=N,count=1,dtype=array.dtype,
            crs=crs,transform=transform,nodata=nodata,compress='deflate',tiled=True) as dst:
        dst.write(array,1)

def main():
    contract=coordinate_contract()
    sources=json.loads((EVIDENCE/'source-manifest.json').read_text())['sources']
    info=[]
    for group,dtype,fill,resampling in [('dem','float32',-32767.0,Resampling.average),
                                        ('worldcover','uint8',0,Resampling.nearest)]:
        output=np.full((N,N),fill,dtype=dtype)
        for record in (s for s in sources if s['group']==group):
            p=Path(record['path'])
            assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==record['sha256']
            with rasterio.open(p) as src:
                warped=np.full((N,N),fill,dtype=dtype)
                reproject(source=rasterio.band(src,1),destination=warped,
                    src_nodata=src.nodata,dst_transform=SOURCE_TRANSFORM,dst_crs='EPSG:3857',
                    dst_nodata=fill,resampling=resampling,num_threads=4,warp_mem_limit=128)
                mask=warped!=fill
                output[mask]=warped[mask]
                info.append({'file':p.name,'crs':str(src.crs),'shape':list(src.shape),
                    'bounds':list(src.bounds),'transform':list(src.transform),
                    'nodata':src.nodata,'tags':src.tags(),'output_cells':int(mask.sum())})
            print(f'WARP {group} {p.name}',flush=True)
        if group=='dem':
            write_tif(DERIVED/'gis/dsm_egm2008_3857.tif',output,nodata=fill)
        else:
            write_tif(DERIVED/'gis/worldcover_2021_3857.tif',output,nodata=fill)
        info.append({'group':group,'missing_cells':int((output==fill).sum()),
            'minimum':float(output[output!=fill].min()),'maximum':float(output[output!=fill].max()),
            'resampling':resampling.name})
    save_json(EVIDENCE/'raster-processing.json',info)
    print('RASTERS COMPLETE',flush=True)

if __name__=='__main__':main()
