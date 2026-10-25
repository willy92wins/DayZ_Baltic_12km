"""Design separate lake levels and a continuous main-river hydraulic field.

Fixed lakes/coast/endpoints, harmonic interpolation in river polygons; beds are
distinct from surfaces. A 24m fairway receives full native-triangle support.
No native import or runtime acceptance is implied by this candidate.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import rasterio,shapefile
from rasterio.features import rasterize
from affine import Affine
from scipy.ndimage import distance_transform_edt,label
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree
from shapely import make_valid,points,distance
from shapely.geometry import shape,mapping,box,Point
from shapely.affinity import translate
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from geo_common import tb_geometry,save_json
EV=ROOT/'evidence/regional-foundation-v1'
OUT=ROOT/'tests/regional_foundation_hydrology_v1'
TX=Affine(6,0,-3,0,-6,12285)
FRAME=box(0,0,12282,12282)

def mask(geometry):
    return rasterize([(geometry,1)],out_shape=(2048,2048),transform=TX,dtype='uint8').astype(bool)

def main():
    assert not OUT.exists(),'Fresh candidate required'
    with rasterio.open(ROOT/'tests/regional_outline_v3/baltic_regional_outline_v3.asc') as ds:base=ds.read(1)
    standing=json.loads((EV/'standing-water-game.json').read_text())['features']
    levels=json.loads((EV/'lake-design-levels.json').read_text())['bodies']
    lakegeo=[shape(f['geometry']) for f in standing]
    lakes=unary_union(lakegeo)
    routes=json.loads((EV/'fairways-main-game.json').read_text())['features']
    lines=[shape(f['geometry']) for f in routes]
    axis=unary_union(lines)
    islands=unary_union([shape(f['geometry']) for f in json.loads((EV/'protected-islands-game.json').read_text())['features']])
    with shapefile.Reader(str(ROOT/'derived/tb/source/vectors/ocean.shp')) as reader:
        ocean=unary_union([translate(make_valid(shape(g.__geo_interface__)),xoff=-200000) for g in reader.iterShapes()]).intersection(FRAME)
    sources=json.loads((ROOT/'derived/gis/osm_water_wgs84.geojson').read_text())['features']
    river_sources=[]
    for f in sources:
        p=f['properties']
        if p.get('water') in {'river','canal','stream'} or p.get('waterway') in {'riverbank','river','canal','stream'}:
            g=translate(make_valid(tb_geometry(shape(f['geometry']))),xoff=-200000).intersection(FRAME)
            if not g.is_empty:river_sources.append(g)
    original_river=unary_union(river_sources).intersection(axis.buffer(300))
    river=unary_union([original_river,axis.buffer(32)]).difference(islands).intersection(FRAME)
    # Forty metres of overlap inside each receiving body avoids a dry triangle seam.
    river=river.difference(ocean.buffer(-40)).difference(lakes.buffer(-40))
    river=make_valid(river)
    rm=mask(river);om=mask(ocean);im=mask(islands)
    lake_data=np.load(ROOT/'tests/regional_foundation_water_v2/reference.npz')
    lids=lake_data['lake_ids'];ls=lake_data['surfaces']
    n=int(rm.sum());rr,cc=np.where(rm);idx=np.full(rm.shape,-1,dtype=np.int32);idx[rm]=np.arange(n)
    fixed=np.full(n,np.nan)
    fixed[lids[rm]>=0]=ls[rm][lids[rm]>=0]
    fixed[om[rm]]=.45
    # Upstream free ends retain the inherited physical elevation plus the lake
    # offset. Endpoints at junctions or receiving bodies are not independent dams.
    ends=np.array([p for line in lines for p in (line.coords[0],line.coords[-1])])
    et=cKDTree(ends);anchors=[]
    for i,p in enumerate(ends):
        if len(et.query_ball_point(p,36))>1:continue
        point=Point(p)
        if point.distance(lakes)<48 or point.distance(ocean)<48:continue
        r=int(round((12282-p[1])/6));c=int(round(p[0]/6))
        if not(0<=r<2048 and 0<=c<2048) or not rm[r,c]:continue
        target=float(max(1.4,base[r,c]+1.25))
        near=(rr-r)**2+(cc-c)**2<=4
        fixed[near]=target
        anchors.append({'xz':p.tolist(),'surface_m':target})
    groups,ng=label(rm)
    orphan=[]
    for g in range(1,ng+1):
        member=groups[rm]==g
        if not np.isfinite(fixed[member]).any():
            target=float(max(1.4,np.median(base[rm][member])+1.25))
            fixed[member]=target
            orphan.append({'component':g,'vertices':int(member.sum()),'level_m':target})
    aa=[];bb=[]
    for dr,dc in ((0,1),(1,0)):
        a=idx[:2048-dr,:2048-dc];b=idx[dr:,dc:]
        valid=(a>=0)&(b>=0);aa.append(a[valid]);bb.append(b[valid])
    aa=np.concatenate(aa);bb=np.concatenate(bb)
    adjacency=coo_matrix((np.ones(2*len(aa)),(np.r_[aa,bb],np.r_[bb,aa])),shape=(n,n)).tocsr()
    L=diags(np.asarray(adjacency.sum(axis=1)).ravel())-adjacency
    known=np.isfinite(fixed);unknown=~known
    print(f'Hydraulic field: {n} vertices, {unknown.sum()} unknown, {ng} components',flush=True)
    value=fixed.copy()
    if unknown.any():value[unknown]=spsolve(L[unknown][:,unknown],-L[unknown][:,known]@fixed[known])
    assert np.isfinite(value).all()
    step=np.abs(value[aa]-value[bb]);worst=np.argsort(step)[-10:]
    report={'status':'DESIGN_FIELD_ONLY','river_vertices':n,'components':ng,'unanchored_components':orphan,
            'headwater_anchors':anchors,'max_adjacent_difference_m':float(step.max()),
            'p99_adjacent_difference_m':float(np.percentile(step,99)),
            'steep_edges_over_25mm':int((step>.025).sum()),'worst_edges':[
                {'a_xz':[int(cc[aa[j]]*6),int(12282-rr[aa[j]]*6)],'b_xz':[int(cc[bb[j]]*6),int(12282-rr[bb[j]]*6)],'difference_m':float(step[j])} for j in worst]}
    surfaces=ls.copy();surfaces[rm]=value.astype(np.float32)
    OUT.mkdir(parents=True)
    np.savez_compressed(OUT/'hydraulic-field.npz',base=base,river=rm,lakes=lids,surfaces=surfaces,ocean=om,islands=im)
    save_json(EV/'hydraulic-field-v1.json',report)
    save_json(EV/'river-engineering-game.json',{'type':'FeatureCollection','features':[{'type':'Feature','properties':{'status':'DESIGN_NOT_IMPORTED'},'geometry':mapping(river)}]})
    save_json(EV/'ocean-game.json',{'type':'FeatureCollection','features':[{'type':'Feature','properties':{},'geometry':mapping(ocean)}]})
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
