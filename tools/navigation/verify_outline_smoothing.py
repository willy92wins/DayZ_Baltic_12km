"""Consume an ASC against frozen geometry; never read the optimization matrix."""
from pathlib import Path
import argparse, csv, hashlib, json, math, time
import numpy as np
import rasterio
from rasterio.features import rasterize
from affine import Affine
from shapely import polygons, intersection, get_coordinates, area, STRtree
from shapely.geometry import shape, box, LineString
from shapely.ops import unary_union
from waterway_common import sample
from verify_foundation_islands import minimum_margin as exact_reference_minimum_margin

ROOT=Path(__file__).resolve().parents[2]
EV=ROOT/'evidence/regional-foundation-v1'
TX=Affine(6,0,0,0,-6,12282)
HASHES={'water-surfaces-contour-v2.geojson':'df860f693a1bf0115cb4af65a13cea5f8006a5a21bc9bca1d88276b83802ccdc','ocean-game.json':'c72aaafd6ee35abfcdec180135571e34b9c5eaefb42d3bca1bfbabad6493f757','protected-islands-game.json':'ebc453b8e3b2b95e5f7846d4fba890f69fbbd43f323547780ab41404ed4ffaef','island-support-v7.json':'e51eda3310cf1ee2b5bde588ec60ec89b750ccb73372a3274315d7ea7addff61'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def triangles(h,r,c):
    x=c*6;z=12282-r*6
    positions=[np.c_[x,z],np.c_[x+6,z],np.c_[x+6,z-6],np.c_[x,z-6]]
    heights=[h[r,c],h[r,c+1],h[r+1,c+1],h[r+1,c]]
    for indices in ([0,1,2],[0,2,3]):
        yield np.stack([positions[k] for k in indices],axis=1),np.stack([heights[k] for k in indices],axis=1)

def clipped_plane_values(vertices,heights,geometry):
    """Solve affine planes and evaluate extrema of their clipped polygons."""
    clips=intersection(polygons(vertices),geometry);valid=area(clips)>1e-8
    if not valid.any():return np.array([]),np.array([],int),np.empty((0,2))
    corners=vertices[valid];origin=corners[:,0,:]
    plane=np.linalg.solve(np.concatenate([corners-origin[:,None,:],np.ones((len(corners),3,1))],axis=2),heights[valid,...,None])[...,0]
    points,index=get_coordinates(clips[valid],return_index=True)
    values=(plane[index,:2]*(points-origin[index])).sum(axis=1)+plane[index,2]
    return values,np.flatnonzero(valid)[index],points

def minimum_margin(h,g,target):
    """Conservative affine lower bound; clip only triangles that need it.

    If all three native vertices satisfy the bound, every convex combination
    satisfies it. Large lakes otherwise repeat a large polygon overlay for
    hundreds of thousands of already-deep interior triangles.
    """
    if g.is_empty:return float('inf'),0
    cells=rasterize([(g,1)],out_shape=(2047,2047),transform=TX,all_touched=True,dtype='uint8');rr,cc=np.where(cells);minimum=float('inf');count=0
    for vertices,heights in triangles(h,rr,cc):
        corners=heights.min(axis=1)-target;proven=corners>=-1e-5
        if proven.any():minimum=min(minimum,float(corners[proven].min()));count+=int(proven.sum())*3
        if (~proven).any():
            vals,index,points=clipped_plane_values(vertices[~proven],heights[~proven],g)
            if len(vals):minimum=min(minimum,float((vals-target).min()));count+=len(vals)
    return minimum,count

def basic_checks(h,base,ref,folder):
    delta=h.astype(float)-base;wet=ref['wet']|ref['ocean']
    old=np.load(ROOT/'tests/regional_foundation_combined_v9/reference.npz')['candidate']
    bridge=base!=old
    edge=np.zeros(base.shape,bool);edge[:2]=edge[-2:]=True;edge[:,:2]=edge[:,-2:]=True
    pre=json.loads((folder/'pre-solve.json').read_text())
    # Rebuild the declared local exception from its frozen coordinates, without
    # reading the producer's region array or constraint-variable list.
    yy,xx=np.indices(base.shape);exception=np.zeros(base.shape,bool)
    for p in pre['seed_vertices']:
        x,z=p['xz'];exception|=(xx*6-x)**2+(12282-yy*6-z)**2<=48**2
    exception&=wet
    a=h[:-1,:-1].astype(float);b=h[:-1,1:].astype(float);c=h[1:,:-1].astype(float);d=h[1:,1:].astype(float)
    # Norm of the two affine gradients, independently of LP direction facets.
    slope=np.degrees(np.arctan(np.maximum(np.sqrt((b-a)**2+(d-b)**2),np.sqrt((d-c)**2+(c-a)**2))/6))
    # The design freezes the accepted bridge approaches, including eight dry
    # vertices between1.27 and1.39m. They must retain their source heights.
    required=np.where(bridge,np.minimum(base,1.4),1.4)
    checks=dict(finite=bool(np.isfinite(h).all()),fairway_vertices_exact=np.array_equal(h[ref['fairway_support']],base[ref['fairway_support']]),bridge_delta_vertices_exact=np.array_equal(h[bridge],base[bridge]),map_edge_exact=np.array_equal(h[edge],base[edge]),all_slopes_below_35_01=bool(slope.max()<=35.01),delta_bounds=bool(np.all(delta>=-6.00001)&np.all(delta<=np.where(exception,15.00001,6.00001))),dry_native_freeboard=bool(np.all(h[(~wet)&(~edge)]>=required[(~wet)&(~edge)]-1e-5)))
    stats=dict(changed_vertices=int(np.count_nonzero(delta)),delta_min_m=float(delta.min()),delta_max_m=float(delta.max()),maximum_slope_deg=float(slope.max()),dry_native_minimum_m=float(h[(~wet)&(~edge)].min()))
    return checks,stats

def coast_checks(h,geos,levels):
    water=unary_union(geos);land=box(0,0,12282,12282).difference(water)
    cells=rasterize([(water.boundary,1)],out_shape=(2047,2047),transform=TX,dtype='uint8',all_touched=True).astype(bool)
    cells[:2]=cells[-2:]=False;cells[:,:2]=cells[:,-2:]=False
    r,c=np.where(cells);ids=(r//64)*32+c//64;tree=STRtree(geos)
    minimum=float('inf');bad=0;count=0;examples=[]
    for j,tile in enumerate(np.unique(ids)):
        take=ids==tile;rr,cc=r[take],c[take]
        local=land.intersection(box(float(cc.min()*6),float(12282-rr.max()*6-6),float(cc.max()*6+6),float(12282-rr.min()*6)))
        for vertices,heights in triangles(h,rr,cc):
            pairs=tree.query(polygons(vertices),predicate='intersects');ceiling=np.full(len(rr),1.4)
            np.maximum.at(ceiling,pairs[0],levels[pairs[1]]+.35)
            values,index,points=clipped_plane_values(vertices,heights,local)
            if not len(values):continue
            margin=values-ceiling[index];minimum=min(minimum,float(margin.min()));bad+=int((margin< -1e-5).sum());count+=len(values)
            for k in np.flatnonzero(margin< -1e-5)[:max(0,10-len(examples))]:examples.append(dict(xz=points[k].tolist(),height=float(values[k]),required=float(ceiling[index[k]])))
        if j%40==0:print(f'Independent coast tiles {j}, minimum margin {minimum:.6f}',flush=True)
    return dict(cells=int(cells.sum()),extrema_checked=count,minimum_margin_m=minimum,violations=bad,examples=examples,passed=bad==0)

def lake_checks(h,fs,geos,small_bodies=()):
    records=[]
    for f,g in zip(fs,geos):
        if not f['properties']['body'].startswith('lake_'):continue
        body=f['properties']['body'];core=g.buffer(-4.5 if body in small_bodies else -6*math.sqrt(2));level=f['properties']['level_m']
        if core.is_empty:
            p=g.representative_point();depth=float(level-sample(h,p.x+200000,p.y))
            records.append(dict(body=body,core=False,representative_depth_m=depth,passed=depth>=.15-1e-5));continue
        # minimum_margin on -h proves the upper height bound everywhere in core.
        margin,count=minimum_margin(-h,core,-level+.15)
        records.append(dict(body=body,core=True,minimum_extra_depth_m=margin,extrema_checked=count,passed=margin>=-1e-5))
        if len(records)%40==0:print(f'Lake plane checks {len(records)}',flush=True)
    return dict(passed=all(r.get('passed',True) for r in records),records=records)

def river_checks(h,ref):
    records=[]
    for f in json.loads((EV/'fairways-main-game.json').read_text())['features']:
        line=shape(f['geometry']);s=np.r_[np.arange(.37,line.length,1.37),line.length]
        p=np.array([line.interpolate(float(v)).coords[0] for v in s]);lo=np.maximum(0,s-.05);hi=np.minimum(line.length,s+.05)
        tangent=np.array([line.interpolate(float(v)).coords[0] for v in hi])-np.array([line.interpolate(float(v)).coords[0] for v in lo]);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
        normal=np.c_[-tangent[:,1],tangent[:,0]];q=np.concatenate([p+normal*t for t in np.arange(-12,12.01,2)])
        q=np.clip(q,.01,12281.99);bottom=sample(h,q[:,0]+200000,q[:,1]);surface=sample(ref['surfaces'],q[:,0]+200000,q[:,1]);depth=surface-bottom
        records.append(dict(river=f['properties']['river'],part=f['properties']['part'],samples=len(q),minimum_depth_m=float(np.nanmin(depth)),missing=int((~np.isfinite(depth)).sum()),passed=bool(np.isfinite(depth).all()&np.all(depth>=3-1e-5))))
    return dict(passed=all(r['passed'] for r in records),records=records)

def frozen_runtime_points(h):
    """Preserve the V5 locations/classes/depths, including its shoreline band."""
    manifest=EV/'consumer-reference-v5.json'
    assert sha(manifest)=='78fd406f340efcc8b3de2218ee8b8ae14b25b36ef8bf13eb9d3c206078d21b0c'
    frozen=json.loads(manifest.read_text())
    path=ROOT/'missions/BalticFoundationConsumerV5.BalticTrial/water-points.csv'
    assert sha(path)==frozen['water_file_sha256']
    rows=list(csv.reader(path.read_text().splitlines(),delimiter=';'))
    assert len(rows)==81212
    coords=np.array([[float(v) for v in row[2].split()] for row in rows],dtype='float32').astype(float)
    ground=sample(h,coords[:,0]+200000,coords[:,2]);failures=[];groups={}
    for row,y in zip(rows,ground):
        margin=float(row[4])-y-float(row[5]) if row[0]=='W' else y-1.25
        if not math.isfinite(margin) or margin < -1e-5:
            groups[row[6]]=groups.get(row[6],0)+1
            failures.append(dict(index=int(row[1]),kind=row[0],group=row[6],position=row[2],ground=float(y),margin_m=float(margin)))
    return dict(passed=not failures,total=len(rows),failed=len(failures),failure_groups=groups,examples=failures[:50],source_sha256=sha(path),coordinate_class_depth_changes=0)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
    assert not a.out.exists();t=time.monotonic()
    for name,digest in HASHES.items():assert sha(EV/name)==digest
    source=ROOT/'tests/regional_foundation_combined_v10/reference.npz';assert sha(source)=='a43cb0f128c17318207a114f94f08801ff35a81af5d36a4b7e3427dd3d6aca2d'
    ref=np.load(source);base=ref['candidate']
    with rasterio.open(a.candidate) as ds:
        h=ds.read(1);assert h.shape==(2048,2048);assert ds.transform==Affine(6,0,200000,0,-6,12288)
    checks,stats=basic_checks(h,base,ref,a.candidate.parent)
    print(json.dumps(dict(checks=checks,statistics=stats)),flush=True)
    fs=json.loads((EV/'water-surfaces-contour-v2.geojson').read_text())['features'];geos=[shape(f['geometry']) for f in fs];levels=np.array([f['properties']['level_m'] for f in fs]+[1.05])
    ocean=shape(json.loads((EV/'ocean-game.json').read_text())['features'][0]['geometry'])
    shore=list(geos);small_bodies=[];transition_report=None;marine_floor_required=False
    transition_file=a.candidate.parent/'shore-transition.json'
    if transition_file.exists():
        design=json.loads(transition_file.read_text());assert design['transition_m']==6
        small_bodies=[f['properties']['body'] for f,g in zip(fs,geos) if f['properties']['body'].startswith('lake_') and g.buffer(-6*math.sqrt(2)).is_empty]
        assert len(small_bodies)==23
        if design.get('scope')=='all_freshwater_with_marine_floor':
            expected_bodies=[f['properties']['body'] for f in fs if f['properties']['body'].startswith('lake_')]
            assert set(design['small_core_bodies'])==set(small_bodies) and design['marine_floor_m']==1.4
            marine_floor_required=True
        else:
            expected_bodies=small_bodies
        assert set(design['bodies'])==set(expected_bodies)
        for i,(f,g) in enumerate(zip(fs,geos)):
            if f['properties']['body'] in expected_bodies:shore[i]=g.buffer(6)
        transition_report=dict(bodies=expected_bodies,maximum_transition_m=6,scope='Full local-lake freeboard outside source-lake buffers; original dry geometry has a separate marine floor when all lakes transition.',design_sha256=sha(transition_file))
    coast=coast_checks(h,shore+[ocean],levels);checks['dry_shore_planes']=coast['passed']
    marine_floor=None
    if marine_floor_required:
        marine_floor=coast_checks(h,geos+[ocean],np.full(len(geos)+1,1.05))
        checks['source_dry_land_marine_floor']=marine_floor['passed']
    print('Coast complete; checking freshwater interiors',flush=True)
    lakes=lake_checks(h,fs,geos,small_bodies);checks['whole_lake_core_depth']=lakes['passed']
    rivers=river_checks(h,ref);checks['dense_navigable_cross_sections']=rivers['passed']
    runtime_points=frozen_runtime_points(h);checks['frozen_v5_runtime_samples']=runtime_points['passed']
    islands=[];features=json.loads((EV/'protected-islands-game.json').read_text())['features'];water=json.loads((EV/'island-support-v7.json').read_text())['islands']
    print('River sections complete; checking protected islands',flush=True)
    for i,(f,w) in enumerate(zip(features,water)):
        g=shape(f['geometry']);level=w['adjacent_water_ceiling_m'];shore,n=minimum_margin(h,g,level);core,nc=minimum_margin(h,g.buffer(-6),level+.35);p=g.representative_point();representative=float(sample(h,p.x+200000,p.y)-level)
        islands.append(dict(index=i,shore_margin_m=shore,core_margin_m=core if nc else None,representative_freeboard_m=representative,passed=shore>=-1e-5 and core>=-1e-5 and representative>=.35-1e-5))
        if i%40==0:print(f'Protected island plane checks {i+1}',flush=True)
    checks['protected_island_planes']=all(r['passed'] for r in islands)
    report=dict(status='PASS_OFFLINE_OUTLINE_GEOMETRY' if all(checks.values()) else 'FAIL',candidate_sha256=sha(a.candidate),source_sha256=sha(source),checks=checks,statistics=stats,coast=coast,lakes=lakes,rivers=rivers,islands=islands,shore_transition=transition_report,elapsed_s=time.monotonic()-t,plane_bound_method='Whole triangle when all corners pass; exact clipped affine extrema otherwise. Lake/island minima are conservative lower bounds.',limits=['Independent ASC geometry only; native import, runtime waves, visual smoothing and navmesh remain unverified.','Lake cores exclude an8.485m shoreline band,4.5m for the23approved small-lake transitions; empty cores use a wet representative.','Map outer two vertex rows remain exact; coast proof excludes outer two cells.','Whole-road smoothness remains a separate open gate.'])
    report['frozen_runtime_points']=runtime_points
    report['original_coast_marine_floor']=marine_floor
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('lakes','rivers','islands','frozen_runtime_points')},indent=2),flush=True)
    raise SystemExit(0 if all(checks.values()) else 1)

if __name__=='__main__':main()
