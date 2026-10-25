"""One explicit transform for source GIS and local game engineering coordinates."""
from pathlib import Path
import hashlib, json
import numpy as np
from pyproj import Transformer, Geod
from rasterio.transform import from_bounds
from shapely.ops import transform
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'raw'
DERIVED = ROOT / 'derived'
EVIDENCE = ROOT / 'evidence'
N, CELL, SIZE = 2048, 6.0, 12288.0
TB_X, TB_Y = 200000.0, 0.0
WGS_TO_MERC = Transformer.from_crs(4326, 3857, always_xy=True)
MERC_TO_WGS = Transformer.from_crs(3857, 4326, always_xy=True)
APPROVAL = json.loads((EVIDENCE / 'aprobacion.json').read_text(encoding='utf-8'))
assert APPROVAL['status'] == 'USER_APPROVED_GEOGRAPHIC_SCOPE_V0'
POLY = APPROVAL['frame_polygon_lonlat_approximate']
WEST, EAST = min(p[0] for p in POLY), max(p[0] for p in POLY)
SOUTH, NORTH = min(p[1] for p in POLY), max(p[1] for p in POLY)
XMIN, YMIN = WGS_TO_MERC.transform(WEST, SOUTH)
XMAX, YMAX = WGS_TO_MERC.transform(EAST, NORTH)
assert abs((XMAX-XMIN)-(YMAX-YMIN)) < 1e-5
SCALE = SIZE/(XMAX-XMIN)
SOURCE_TRANSFORM = from_bounds(XMIN, YMIN, XMAX, YMAX, N, N)
GAME_TRANSFORM = from_bounds(TB_X, TB_Y, TB_X+SIZE, TB_Y+SIZE, N, N)
GAME_CRS = 'LOCAL_CS["Baltic game engineering coordinates",LOCAL_DATUM["Map frame",0],UNIT["metre",1],AXIS["Easting",EAST],AXIS["Northing",NORTH]]'
BBOX = box(WEST, SOUTH, EAST, NORTH)

def game_xy(lon, lat, z=None):
    x,y = WGS_TO_MERC.transform(lon,lat)
    return (np.asarray(x)-XMIN)*SCALE, (np.asarray(y)-YMIN)*SCALE

def tb_geometry(geom):
    def convert(x,y,z=None):
        xx,yy=game_xy(x,y)
        return xx+TB_X,yy+TB_Y
    return transform(convert,geom)

def save_json(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def coordinate_contract():
    geod=Geod(ellps='WGS84')
    mid_lon,mid_lat=MERC_TO_WGS.transform((XMIN+XMAX)/2,(YMIN+YMAX)/2)
    measurements=[]
    for name,lat in [('south',SOUTH),('centre',mid_lat),('north',NORTH)]:
        _,_,distance=geod.inv(mid_lon-.01,lat,mid_lon+.01,lat)
        gx0,gy0=game_xy(mid_lon-.01,lat);gx1,gy1=game_xy(mid_lon+.01,lat)
        factor=float((gx1-gx0)/distance)
        measurements.append({'latitude':lat,'name':name,'game_m_per_real_m_east_west':factor,'compression':1/factor})
    physical=measurements[1]['game_m_per_real_m_east_west']
    contract={'source_crs':'EPSG:3857','source_bounds':[XMIN,YMIN,XMAX,YMAX],
      'source_bbox_lonlat':[WEST,SOUTH,EAST,NORTH],'source_to_game_scale':SCALE,
      'game_crs_wkt':GAME_CRS,'tb_origin':[TB_X,TB_Y],'game_size_m':SIZE,
      'grid_cells':[N,N],'cell_size_m':CELL,'samples':'cell centres, row zero north',
      'z_physical_factor':physical,'z_comparison_multiplier':3.0,
      'vertical_datum':'Copernicus DSM orthometric metres EGM2008; datum from product documentation, not inferred from horizontal CRS',
      'projection_measurements':measurements,
      'projection_note':'Exact approved Web Mercator silhouette retained by one scalar XY transform. Game axes are engineering metres. Compression in real ground metres varies with latitude; projected metres are not ground distances.',
      'terrain_builder_sampling':'Observed locally with 128x128 at 6m: TB vertex X=xllcorner+col*cellsize; Y=yllcorner+nrows*cellsize-row*cellsize, offset (-3,+3)m from GIS centres. Four UI positives and negatives; six SHP anchors passed. Analytic sampling adapter passed actual TB export; NOT applied to production terrain. Evidence: evidence/tb-registration/.'}
    save_json(EVIDENCE/'coordinate-contract.json',contract)
    return contract

if __name__=='__main__':
    print(json.dumps(coordinate_contract(),indent=2))
