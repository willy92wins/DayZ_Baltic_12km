"""Bounded global smoothing proposal plus exact shoreline plane constraints.

Immutable V10 parent. No import/deploy. Linear constraints are generated from
source polygon intersections, not the diagnostic sample coordinates.
"""
from pathlib import Path
import hashlib,json,math,time,sys
import numpy as np
from scipy.ndimage import gaussian_filter,distance_transform_edt,binary_dilation
from scipy.optimize import linprog
from scipy.sparse import coo_matrix,hstack,vstack,eye,csr_matrix,save_npz
import rasterio
from rasterio.features import rasterize
from affine import Affine
from shapely import STRtree,polygons,intersection,get_coordinates
from shapely.geometry import shape,box
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'
OUT=ROOT/'tests/regional_outline_smoothing_v32'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
TX=Affine(6,0,0,0,-6,12282)

def slope(h):
    a,b,c,d=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
    return np.maximum(np.hypot(b-a,d-b),np.hypot(d-c,c-a))/6

def ease(x):
    x=np.clip(x,0,1);return x*x*x*(10+x*(-15+6*x))

def main():
    assert not OUT.exists(),'Fresh version required';OUT.mkdir(parents=True)
    t0=time.monotonic();source=ROOT/'tests/regional_foundation_combined_v10/reference.npz'
    assert sha(source)=='a43cb0f128c17318207a114f94f08801ff35a81af5d36a4b7e3427dd3d6aca2d'
    ref=np.load(source);base=ref['candidate'];wet=ref['wet']|ref['ocean']
    hashes={'water-surfaces-contour-v2.geojson':'df860f693a1bf0115cb4af65a13cea5f8006a5a21bc9bca1d88276b83802ccdc','ocean-game.json':'c72aaafd6ee35abfcdec180135571e34b9c5eaefb42d3bca1bfbabad6493f757'}
    for name,digest in hashes.items():assert sha(EV/name)==digest
    fs=json.loads((EV/'water-surfaces-contour-v2.geojson').read_text())['features']
    source_geos=[shape(f['geometry']) for f in fs]
    small_lakes=[i for i,f in enumerate(fs) if f['properties']['body'].startswith('lake_') and source_geos[i].buffer(-6*math.sqrt(2)).is_empty]
    lake_indices=[i for i,f in enumerate(fs) if f['properties']['body'].startswith('lake_')]
    geos=[g.buffer(6) if i in lake_indices else g for i,g in enumerate(source_geos)]
    levels=np.array([f['properties']['level_m'] for f in fs]+[1.05])
    (OUT/'shore-transition.json').write_text(json.dumps(dict(status='FROZEN_SHORE_DESIGN',source_hashes=hashes,transition_m=6,bodies=[fs[i]['properties']['body'] for i in lake_indices],scope='all_freshwater_with_marine_floor',marine_floor_m=1.4,small_core_bodies=[fs[i]['properties']['body'] for i in small_lakes],meaning='Dry freeboard begins outside a one-cell shore transition at freshwater lakes; original dry geometry also has a1.4m marine floor. Original water mesh/vector sources remain unchanged.'),indent=2)+'\n')
    ocean=shape(json.loads((EV/'ocean-game.json').read_text())['features'][0]['geometry']);geos.append(ocean)
    union=unary_union(geos);land=box(0,0,12282,12282).difference(union)
    original_union=unary_union(source_geos+[ocean]);original_land=box(0,0,12282,12282).difference(original_union)
    tree=STRtree(geos)
    coastcells=rasterize([(union.boundary,1),(original_union.boundary,1)],out_shape=(2047,2047),transform=TX,dtype='uint8',all_touched=True).astype(bool)
    # Ignore the outer map edge in the coast system; preserve that edge exactly.
    coastcells[:2]=False;coastcells[-2:]=False;coastcells[:,:2]=False;coastcells[:,-2:]=False
    coastverts=np.zeros(base.shape,bool)
    for dr,dc in [(0,0),(0,1),(1,0),(1,1)]:coastverts[dr:2047+dr,dc:2047+dc]|=coastcells
    collar=distance_transform_edt(~coastverts)*6<=30
    edge=np.zeros(base.shape,bool);edge[:2]=True;edge[-2:]=True;edge[:,:2]=True;edge[:,-2:]=True
    fairway=ref['fairway_support'];road=np.zeros(base.shape,bool);road.ravel()[ref['road_fixed_vertices']]=True
    # The native bridge approach delta is exact. No height support under it moves.
    old=np.load(ROOT/'tests/regional_foundation_combined_v9/reference.npz')['candidate'];bridge=base!=old
    fixed=fairway|edge|bridge
    editable=collar&~fixed
    variables=np.flatnonzero(editable);n=len(variables);lookup=np.full(base.size,-1,np.int32);lookup[variables]=np.arange(n)
    print(f'Coast cells {coastcells.sum()}, variables {n}',flush=True)
    # Smooth broad dry relief. A 48m transition protects existing road profiles;
    # the shoreline solve below is allowed to adjust only its explicit collar.
    protect=wet|road|bridge|edge
    weight=ease(distance_transform_edt(~protect)*6/48)
    target=base.astype(float)+(gaussian_filter(base.astype(float),sigma=2)-base)*weight
    # Smooth monotonic lowland uplift: derivative in [0.6484375,1], no new step.
    lift=.15*ease((2.2-target)/.8);target+=lift*((~wet)&(~fixed))
    target=base+np.clip(target-base,-6,6)
    island_support=ref['island_support_conservative']
    target[island_support]=np.maximum(target[island_support],base[island_support])
    target[(~wet)&(~fixed)]=np.maximum(target[(~wet)&(~fixed)],1.4)
    target[fixed]=base[fixed];target[wet&~editable]=base[wet&~editable]
    # Back off only macro changes outside the shoreline solve when their mask
    # transition introduces a slope absent from the V10 baseline.
    varcells=editable[:-1,:-1]|editable[1:,:-1]|editable[:-1,1:]|editable[1:,1:]
    backoffs=[]
    for iteration in range(48):
        bad=(slope(target)>math.tan(math.radians(35.001)))&~varcells
        backoffs.append(int(bad.sum()))
        if not bad.any():break
        v=np.zeros(base.shape,bool)
        for dr,dc in [(0,0),(0,1),(1,0),(1,1)]:v[dr:2047+dr,dc:2047+dc]|=bad
        target[v]=base[v]+.5*(target[v]-base[v])
    assert not bad.any(),'Macro-only slope gate failed'
    macro=target.copy();target[editable]=gaussian_filter(base.astype(float),sigma=2)[editable]
    idx=[];cols=[];vals=[];rhs=[];categories=[];impossible=[]
    fixed_flat=macro.ravel()
    def bound(ids,coeff,limit,category):
        ids=np.asarray(ids,dtype=np.int64);coeff=np.asarray(coeff,dtype=float);j=lookup[ids]
        free=j>=0;limit-=float(coeff[~free]@fixed_flat[ids[~free]])
        if not np.any(free):
            if limit < -1e-6:impossible.append(dict(category=category,residual=-limit))
            return
        row=len(rhs);idx.extend([row]*int(free.sum()));cols.extend(j[free].tolist());vals.extend(coeff[free].tolist());rhs.append(limit);categories.append(category)
    def point_bound(coords,limit,category,upper=False):
        for x,z in coords:
            c=min(2046,max(0,int(x//6)));r=min(2046,max(0,int((12282-z)//6)));a=x/6-c;b=(12282-z)/6-r
            if b<=a:ids=[r*2048+c,r*2048+c+1,(r+1)*2048+c+1];weights=[1-a,a-b,b]
            else:ids=[r*2048+c,(r+1)*2048+c+1,(r+1)*2048+c];weights=[1-b,a,b-a]
            bound(ids,np.array(weights)*(1 if upper else -1),limit if upper else -limit,category)
    # Exact dry intersections of every native shoreline triangle. Adjacent pond
    # level is conservative across one triangle; ocean range uses floor1.4m.
    rr,cc=np.where(coastcells)
    tile_id=(rr//32)*64+cc//32
    tiles=np.unique(tile_id)
    for tile_index,tile in enumerate(tiles):
        select=tile_id==tile;r=rr[select];c=cc[select];x=c*6;z=12282-r*6
        local_land=land.intersection(box(float(x.min()),float(z.min()-6),float(x.max()+6),float(z.max())))
        local_sea_safe_land=original_land.intersection(box(float(x.min()),float(z.min()-6),float(x.max()+6),float(z.max())))
        aa=np.c_[x,z];bb=np.c_[x+6,z];dd=np.c_[x+6,z-6];ee=np.c_[x,z-6]
        for verts in [np.stack([aa,bb,dd],axis=1),np.stack([aa,dd,ee],axis=1)]:
            tris=polygons(verts)
            pairs=tree.query(tris,predicate='intersects');ceil=np.full(len(tris),1.4)
            np.maximum.at(ceil,pairs[0],levels[pairs[1]]+.35)
            clips=intersection(tris,local_land)
            for k,tri in enumerate(tris):
                drypart=clips[k]
                if drypart.area>1e-8:point_bound(get_coordinates(drypart),float(ceil[k]),'dry_plane')
            # Source shoreline remains exact for the global sea floor. The lake
            # freeboard rises over one cell; the pond mesh itself is unchanged.
            sea_clips=intersection(tris,local_sea_safe_land)
            for drypart in sea_clips:
                if drypart.area>1e-8:point_bound(get_coordinates(drypart),1.4,'dry_sea_floor')
        if tile_index%40==0:print(f'Coast tiles {tile_index}/{len(tiles)}, rows {len(rhs)}',flush=True)
    # Standing-water cores: at least15cm depth beyond one native diagonal.
    # Fairway depths have stronger exact protection from the parent.
    for number,f in enumerate(fs):
        if not f['properties']['body'].startswith('lake_'):continue
        core=source_geos[number].buffer(-4.5 if number in small_lakes else -6*math.sqrt(2))
        if core.is_empty:
            p=source_geos[number].representative_point();point_bound([[p.x,p.y]],float(levels[number]-.15),'lake_core',upper=True)
            continue
        cells=rasterize([(core,1)],out_shape=(2047,2047),transform=TX,dtype='uint8',all_touched=True).astype(bool)&varcells
        r,c=np.where(cells)
        if not len(r):continue
        x=c*6;z=12282-r*6;aa=np.c_[x,z];bb=np.c_[x+6,z];dd=np.c_[x+6,z-6];ee=np.c_[x,z-6]
        for verts in [np.stack([aa,bb,dd],axis=1),np.stack([aa,dd,ee],axis=1)]:
            clips=intersection(polygons(verts),core);p=get_coordinates(clips)
            point_bound(p,float(levels[number]-.15),'lake_core',upper=True)
    print(f'Dry/core rows {len(rhs)}, impossible constants {len(impossible)}',flush=True)
    if impossible:
        (OUT/'build.json').write_text(json.dumps(dict(status='INFEASIBLE_FIXED_SHORE_ROWS',impossible_fixed_count=len(impossible),examples=impossible[:50]),indent=2)+'\n')
        raise SystemExit(2)
    base_matrix=coo_matrix((vals,(idx,cols)),shape=(len(rhs),n)).tocsr()
    del idx,cols,vals
    blocks=[base_matrix];right_sides=[np.array(rhs)];counts={k:categories.count(k) for k in set(categories)}
    del rhs,categories
    #16-facet polygon is inside the35degree gradient circle, not outside it.
    r,c=np.where(varcells);a=r*2048+c;b=a+1;d=a+2049;e=a+2048
    cap=math.tan(math.radians(35))*math.cos(math.pi/16)
    for i in range(16):
        theta=i*2*math.pi/16;u,v=math.cos(theta),math.sin(theta)
        for ids,coefs in [(np.c_[a,b,d],[-u,u+v,-v]),(np.c_[a,d,e],[v,u,-u-v])]:
            j=lookup[ids];free=j>=0;coeff=np.broadcast_to(np.array(coefs)/6,ids.shape)
            limits=cap-np.sum(np.where(free,0,coeff*fixed_flat[ids]),axis=1)
            active=free.any(axis=1);j=j[active];free=free[active];coeff=coeff[active]
            count=int(active.sum());ri=np.repeat(np.arange(count)[:,None],3,axis=1)
            blocks.append(coo_matrix((coeff[free],(ri[free],j[free])),shape=(count,n)).tocsr());right_sides.append(limits[active])
            counts['slope']=counts.get('slope',0)+count
    matrix=vstack(blocks,format='csr');rhs=np.concatenate(right_sides);nrows=len(rhs)
    del blocks,right_sides,base_matrix
    save_npz(OUT/'constraints.npz',matrix);np.savez_compressed(OUT/'variables.npz',variables=variables,macro=macro,target=target,editable=editable,coastcells=coastcells,rhs=rhs)
    build=dict(status='BUILT_NOT_SOLVED',source_npz_sha256=sha(source),source_hashes=hashes,variables=n,rows=nrows,category_counts=counts,impossible_fixed_rows=impossible[:50],impossible_fixed_count=len(impossible),macro_backoff_counts=backoffs,build_elapsed_s=time.monotonic()-t0)
    (OUT/'build.json').write_text(json.dumps(build,indent=2)+'\n');print(json.dumps({k:v for k,v in build.items() if k not in ['macro_backoff_counts','impossible_fixed_rows']}),flush=True)
    if impossible:raise SystemExit(2)
    return  # Matrix only; exact island and frozen-point constraints follow.
    ident=eye(n,format='csr');zero=csr_matrix(matrix.shape)
    combined=vstack([hstack([matrix,zero]),hstack([ident,-ident]),hstack([-ident,-ident])],format='csr')
    wanted=target.ravel()[variables]
    lower=base.ravel()[variables].astype(float)-6
    lower=np.where(wet.ravel()[variables],lower,np.maximum(lower,1.4))
    island_variables=island_support.ravel()[variables]
    lower[island_variables]=np.maximum(lower[island_variables],base.ravel()[variables][island_variables])
    upper=base.ravel()[variables].astype(float)+6
    bad_rows=[]
    for first in range(0,len(rhs),250000):
        chunk=matrix[first:first+250000];minimum=chunk.maximum(0)@lower+chunk.minimum(0)@upper
        bad_rows.extend((first+np.flatnonzero(minimum>rhs[first:first+len(minimum)]+1e-7)).tolist())
    selected=matrix[bad_rows]
    assert np.all(selected.data<=1e-9),'An individual non-dry conflict requires separate diagnosis'
    seeds=np.unique(selected.indices);seedgrid=np.zeros(base.shape,bool);seedgrid.ravel()[variables[seeds]]=True
    region=distance_transform_edt(~seedgrid)*6<=48 if len(seeds) else np.zeros(base.shape,bool)
    exception=region.ravel()[variables]&wet.ravel()[variables]
    upper[exception]=base.ravel()[variables][exception]+15
    pre=dict(status='FROZEN_BEFORE_SOLVE',source_npz_sha256=sha(source),seed_vertices=[dict(xz=[int(variables[i]%2048*6),int(12282-variables[i]//2048*6)],height=float(base.ravel()[variables[i]])) for i in seeds],local_exception_vertices=int(exception.sum()),local_exception_radius_m=48,ordinary_delta_limit_m=6,maximum_upward_delta_in_exception_m=15,small_lake_transition_m=6,small_lakes=[fs[i]['properties']['body'] for i in small_lakes],island_vertices_may_not_be_lowered=True)
    (OUT/'pre-solve.json').write_text(json.dumps(pre,indent=2)+'\n')
    np.savez_compressed(OUT/'local-exception.npz',region=region,lo=lower,hi=upper)
    bounds=list(zip(lower,upper))+[(0,None)]*n
    solved=linprog(np.r_[np.zeros(n),np.ones(n)],A_ub=combined,b_ub=np.r_[rhs,wanted,-wanted],bounds=bounds,method='highs',options={'time_limit':300,'threads':1,'primal_feasibility_tolerance':1e-8})
    result={**build,'status':str(solved.message),'solver_success':bool(solved.success),'elapsed_s':time.monotonic()-t0}
    if solved.success:
        candidate=macro.astype('float32');candidate.ravel()[variables]=solved.x[:n].astype('float32')
        repair=(~wet)&(~fixed)&(candidate<np.float32(1.4));candidate[repair]=np.float32(1.4)
        assert np.all(candidate[island_support]>=base[island_support]-1e-5)
        residual=matrix@candidate.ravel()[variables]-rhs;result['max_constraint_violation_m']=float(residual.max())
        if residual.max()>1e-4:result['solver_success']=False;result['status']='FLOAT32_CONSTRAINT_FAILURE'
        else:
            asc=OUT/'baltic_outline_smoothing_v28.asc'
            with asc.open('w',newline='\n') as f:
                f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n');np.savetxt(f,candidate,fmt='%.9g')
            with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),candidate)
            payload={k:ref[k] for k in ref.files};payload.update(candidate=candidate,parent=base,changed=candidate!=base)
            np.savez_compressed(OUT/'reference.npz',**payload)
            result.update(status='CANDIDATE_REQUIRES_INDEPENDENT_GATES',asc_sha256=sha(asc),changed_vertices=int((candidate!=base).sum()),maximum_delta_m=float(abs(candidate-base).max()),maximum_triangle_slope_deg=float(np.degrees(np.arctan(slope(candidate).max()))))
    (OUT/'solve.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['macro_backoff_counts','impossible_fixed_rows']}),flush=True)

if __name__=='__main__':main()
