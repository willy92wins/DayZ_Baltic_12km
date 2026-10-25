"""Replace conservative whole-triangle island support at lake 217 with exact land constraints.

Every triangle/island intersection remains at or above the local water ceiling.
Island interiors at least one cell from the shoreline retain 35 cm freeboard.
Only the lake and its 6 m edge are editable; road vertices remain fixed. Linear
interpolation makes clipped polygon vertices sufficient to bound the whole land
intersection. The preceding uniform 35 cm rim was infeasible with the wet core;
the failed attempts are retained in the evidence directory.
"""
from pathlib import Path
import hashlib,json,math
import numpy as np
import rasterio
from scipy.optimize import linprog
from scipy.sparse import lil_matrix
from shapely import points,prepare
from shapely.geometry import shape,Polygon
from shapely.ops import unary_union
from waterway_common import sample
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'
OUT=ROOT/'tests/regional_foundation_combined_v9'

def vertices(g):
    if g.is_empty:return []
    if hasattr(g,'geoms'):return [p for sub in g.geoms for p in vertices(sub)]
    if g.geom_type=='Polygon':return list(g.exterior.coords)
    if g.geom_type in ('LineString','LinearRing'):return list(g.coords)
    if g.geom_type=='Point':return [(g.x,g.y)]
    raise ValueError(g.geom_type)

def terms(x,z):
    c=x/6;r=(12282-z)/6;ci,ri=min(2046,int(c)),min(2046,int(r));a,b=c-ci,r-ri
    if b<=a:return [(ri,ci,1-a),(ri,ci+1,a-b),(ri+1,ci+1,b)]
    return [(ri,ci,1-b),(ri+1,ci,b-a),(ri+1,ci+1,a)]

def main():
    assert not OUT.exists(),'Fresh candidate required'
    ref=np.load(ROOT/'tests/regional_foundation_combined_v8/reference.npz');h=ref['candidate'].copy()
    prior=np.load(ROOT/'tests/regional_foundation_combined_v4/reference.npz')['candidate']
    fs=json.loads((EV/'water-surfaces-contour-v2.geojson').read_text())['features']
    f=next(f for f in fs if f['properties']['body']=='lake_217');g=shape(f['geometry']);level=f['properties']['level_m']
    area=g.buffer(12);x0,z0,x1,z1=area.bounds
    r0=max(0,math.floor((12282-z1)/6));r1=min(2047,math.ceil((12282-z0)/6))
    c0=max(0,math.floor(x0/6));c1=min(2047,math.ceil(x1/6))
    fixed=set(ref['road_fixed_vertices'].tolist())
    editable=g.buffer(6)
    ids=[(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1) if editable.intersects(points(c*6,12282-r*6)) and r*2048+c not in fixed]
    lookup={v:i for i,v in enumerate(ids)};constraints=[];limits=[]
    def bound(tt,limit):
        row={}
        for r,c,w in tt:
            if (r,c) in lookup:row[lookup[(r,c)]]=row.get(lookup[(r,c)],0)+w
            else:limit-=w*float(h[r,c])
        if row:constraints.append(row);limits.append(limit)
        else:assert limit>=-1e-5,limit
    island_reports=json.loads((EV/'island-support-v7.json').read_text())['islands']
    island_geos=json.loads((EV/'protected-islands-game.json').read_text())['features']
    nearby=[]
    for i,f in enumerate(island_geos):
        land=shape(f['geometry'])
        if not land.intersects(area):continue
        # Shoreline can meet its water level; the island interior retains the
        # full 35 cm freeboard. This prevents an artificial raised rim.
        nearby.append((land,island_reports[i]['adjacent_water_ceiling_m']))
        core_land=land.buffer(-6)
        if not core_land.is_empty:nearby.append((core_land,island_reports[i]['target_m']))
    land_constraints=0
    for r in range(max(0,r0-1),min(2047,r1+1)):
        for c in range(max(0,c0-1),min(2047,c1+1)):
            x,z=c*6,12282-r*6
            for pp in [[(x,z),(x+6,z),(x+6,z-6)],[(x,z),(x+6,z-6),(x,z-6)]]:
                triangle=Polygon(pp)
                for land,target in nearby:
                    overlap=triangle.intersection(land)
                    if overlap.area<=1e-9:continue
                    for px,pz in vertices(overlap):
                        bound([(rr,cc,-w) for rr,cc,w in terms(px,pz)],-target+1e-6)
                        land_constraints+=1
    edges=set()
    for r,c in ids:
        for rr,cc in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
            if 0<=rr<2048 and 0<=cc<2048:edges.add(tuple(sorted([(r,c),(rr,cc)])))
    for a,b in edges:
        bound([(*a,1),(*b,-1)],2.880001);bound([(*b,1),(*a,-1)],2.880001)
    # Same conservative shore-core distance used by the accepted lake-bed
    # design: one native-cell diagonal. A shallower edge is not a boat lane.
    core=g.buffer(-6*np.sqrt(2));prepare(core)
    xx,zz=np.meshgrid(np.arange(math.ceil(x0),x1,1),np.arange(math.ceil(z0),z1,1));p=np.c_[xx.ravel(),zz.ravel()];p=p[core.contains(points(p))]
    for x,z in p:bound(terms(x,z),level-.20)
    matrix=lil_matrix((len(constraints),len(ids)))
    for i,row in enumerate(constraints):
        for j,v in row.items():matrix[i,j]=v
    solution=linprog(np.ones(len(ids)),A_ub=matrix.tocsr(),b_ub=limits,bounds=[(min(float(prior[r,c]),level-1.5),float(h[r,c])) for r,c in ids],method='highs')
    residual=matrix.tocsr()@np.array([h[r,c] for r,c in ids])-limits
    report=dict(status='LP_FEASIBLE_REQUIRES_FULL_GATES' if solution.success else 'FAIL',solver=solution.message,variables=len(ids),constraints=len(constraints),land_constraints=land_constraints,water_core_samples=len(p),current_terrain_maximum_constraint_residual=float(residual.max()))
    if solution.success:
        for (r,c),value in zip(ids,solution.x):h[r,c]=value
        assert np.array_equal(h.ravel()[ref['road_fixed_vertices']],ref['candidate'].ravel()[ref['road_fixed_vertices']])
        OUT.mkdir(parents=True);asc=OUT/'baltic_regional_foundation_v9.asc'
        with asc.open('w',encoding='ascii',newline='\n') as handle:
            handle.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n');np.savetxt(handle,h,fmt='%.9g')
        with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),h)
        data={k:ref[k] for k in ref.files};data.update(candidate=h,changed=h!=ref['base'])
        # Whole-triangle support remains a construction diagnostic, not a hard
        # lower bound after this exact polygon-intersection refinement.
        data['island_support_conservative']=data.pop('island_support');data['island_minimum_conservative']=data.pop('island_minimum')
        np.savez_compressed(OUT/'reference.npz',**data)
        report.update(changed_vertices_from_v8=int((h!=ref['candidate']).sum()),asc_sha256=hashlib.sha256(asc.read_bytes()).hexdigest(),max_lowering_m=float((ref['candidate']-h).max()))
    evidence=EV/('lake-shore-refinement-v9-final.json' if solution.success else 'lake-shore-refinement-v9-shorelevel-fail.json')
    if evidence.exists(): raise ValueError('Preserve previous solver result')
    evidence.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    raise SystemExit(0 if solution.success else 1)
if __name__=='__main__':main()
