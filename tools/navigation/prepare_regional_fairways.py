"""Route main-river fairways around reference islands before carving any terrain.

The river axis is a preference, not permission to erase an island. A bounded
6m-grid A* route uses a120m bank corridor, allowing300m detours wholly in existing
water, then smooths by at most a few metres.
Every resulting line is checked against the actual island polygons.
"""
from collections import defaultdict
import heapq,hashlib,json,math
from pathlib import Path
import sys
import numpy as np
from scipy.ndimage import distance_transform_edt,label
from scipy.spatial import cKDTree
from rasterio.features import rasterize
from affine import Affine
from shapely import make_valid,STRtree
from shapely.geometry import shape,mapping,box,LineString,Point
from shapely.affinity import translate
from shapely.ops import unary_union,linemerge
import shapefile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from geo_common import tb_geometry,save_json
EV=ROOT/'evidence/regional-foundation-v1'
TX=Affine(6,0,-3,0,-6,12285)
FRAME=box(0,0,12282,12282)


def parts(g,kind):
    if g.geom_type==kind:yield g
    elif hasattr(g,'geoms'):
        for child in g.geoms:yield from parts(child,kind)


def grid(geometries):
    return rasterize(((g,1) for g in geometries if not g.is_empty),out_shape=(2048,2048),transform=TX,dtype='uint8',all_touched=True).astype(bool)


def astar(start,goal,allowed,cost):
    if start==goal:return [start]
    gr,gc=divmod(goal,2048)
    def heuristic(node):
        r,c=divmod(node,2048)
        return math.hypot(r-gr,c-gc)
    best={start:0.};previous={};queue=[(heuristic(start),0.,start)]
    while queue:
        _,travel,node=heapq.heappop(queue)
        if travel>best[node]+1e-10:continue
        if node==goal:
            route=[node]
            while route[-1]!=start:route.append(previous[route[-1]])
            return route[::-1]
        r,c=divmod(node,2048)
        for dr,dc in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
            rr,cc=r+dr,c+dc
            if not(0<=rr<2048 and 0<=cc<2048) or not allowed[rr,cc]:continue
            nxt=rr*2048+cc
            length=math.sqrt(2) if dr and dc else 1.
            candidate=travel+length*(float(cost[r,c])+float(cost[rr,cc]))/2
            if candidate<best.get(nxt,float('inf')):
                best[nxt]=candidate;previous[nxt]=node
                heapq.heappush(queue,(candidate+heuristic(nxt),candidate,nxt))
        if len(best)>100000:raise ValueError('A* budget exceeded; route needs a different design')
    raise ValueError('No island-safe route within the allowed corridor')


def main():
    waterpath=ROOT/'derived/gis/osm_water_wgs84.geojson'
    water=[translate(make_valid(tb_geometry(shape(f['geometry']))),xoff=-200000).intersection(FRAME)
           for f in json.loads(waterpath.read_text(encoding='utf-8'))['features']]
    with shapefile.Reader(str(ROOT/'derived/tb/source/vectors/ocean.shp')) as reader:
        ocean=unary_union([translate(make_valid(shape(g.__geo_interface__)),xoff=-200000) for g in reader.iterShapes()]).intersection(FRAME)
    wet=unary_union(water+[ocean])
    islands=[g for g in parts(FRAME.difference(wet),'Polygon') if not g.intersects(FRAME.boundary) and g.area>=36]
    print(f'Protecting {len(islands)} reference islands >= one cell area',flush=True)
    wetmask=grid([wet]);islandmask=grid(islands)
    island_distance=distance_transform_edt(~islandmask)*6
    island_tree=STRtree(islands)
    rivers=json.loads((EV/'main-rivers-game.json').read_text())['features']
    groups=defaultdict(list)
    for f in rivers:groups[f['properties']['group']].append(shape(f['geometry']))
    features=[];reports=[]
    for name,geometries in groups.items():
        union=unary_union(geometries)
        lines=list(parts(linemerge(union) if union.geom_type!='LineString' else union,'LineString'))
        axis=grid([union]);band=grid([union.buffer(120)])
        dist=distance_transform_edt(~axis)*6
        # In a lake/reservoir, prefer a longer in-water detour around islands to
        # carving a new bank route merely to stay near a cartographic centreline.
        safe_wet=distance_transform_edt(wetmask)*6>=24
        allowed=(band|(safe_wet&(dist<=300)))&(island_distance>=30)
        labels,nlabels=label(allowed,structure=np.ones((3,3)))
        rr,cc=np.where(allowed)
        valid_xy=np.column_stack([cc*6,12282-rr*6])
        tree=cKDTree(valid_xy)
        cost=1+(dist/12)**2+.25*(~wetmask)
        component_trees={}
        for li,line in enumerate(lines):
            if line.length<6:continue
            stations=np.linspace(0,line.length,max(2,int(math.ceil(line.length/20))+1))
            source=np.array([line.interpolate(float(s)).coords[0] for s in stations])
            snap,near=tree.query(source)
            component_ids=np.unique(labels[rr[near],cc[near]])
            if len(component_ids)>1:
                options=[]
                diagnostics=[]
                for component in component_ids:
                    key=int(component)
                    if key not in component_trees:
                        member=np.flatnonzero(labels[rr,cc]==key)
                        component_trees[key]=(member,cKDTree(valid_xy[member]))
                    member,ctree=component_trees[key]
                    cd,ci=ctree.query(source)
                    worst=int(np.argmax(cd))
                    diagnostics.append({'component':key,'maximum_shift_m':float(cd.max()),'worst_source_xz':source[worst].tolist(),
                                        'nearest_xz':valid_xy[member[ci[worst]]].tolist()})
                    if cd.max()<=300:options.append((float(np.sum(cd*cd)),cd,member[ci]))
                if not options:
                    save_json(EV/'fairway-component-failure.json',{'river':name,'part':li,'components':diagnostics})
                    np.savez_compressed(EV/'fairway-routing-debug.npz',allowed=allowed,labels=labels,water=wetmask,islands=islandmask,source=source)
                    raise ValueError(f'No single island-safe component for {name}/{li}: {diagnostics}')
                _,snap,near=min(options,key=lambda q:q[0])
            if snap.max()>300:raise ValueError(f'Anchor exceeds bounded water detour: {name}/{li}')
            anchors=(rr[near]*2048+cc[near]).tolist()
            nodes=[]
            for si,(a,b) in enumerate(zip(anchors,anchors[1:])):
                try:
                    step=astar(a,b,allowed,cost)
                except ValueError as error:
                    detail={'status':'FAIL_ROUTE_PLAN','river':name,'part':li,'station_pair':si,
                            'source_anchors':source[si:si+2].tolist(),'snapped_anchors':valid_xy[near[si:si+2]].tolist(),
                            'components':[int(labels.flat[a]),int(labels.flat[b])],'allowed_components':int(nlabels),
                            'message':str(error)}
                    save_json(EV/'fairway-route-failure.json',detail)
                    raise ValueError(json.dumps(detail)) from error
                nodes.extend(step if not nodes else step[1:])
            coords=np.array([[n%2048*6,12282-n//2048*6] for n in nodes],dtype=float)
            if len(coords)<2:continue
            # Keep ends shared; smooth only interior points twice.
            for _ in range(2):coords[1:-1]=(coords[:-2]+2*coords[1:-1]+coords[2:])/4
            unique=np.r_[True,np.linalg.norm(np.diff(coords,axis=0),axis=1)>1e-7]
            coords=coords[unique]
            if len(coords)<2:continue
            route=LineString(coords)
            hits=island_tree.query(route.buffer(20.5),predicate='intersects')
            if len(hits):raise ValueError(f'Fairway support touches a protected island: {name}/{li}')
            deviation=max(Point(p).distance(union) for p in coords)
            outside=route.difference(union.buffer(120))
            if not outside.is_empty and not wet.buffer(.01).covers(outside.buffer(20.5)):
                raise ValueError('Route detour would excavate outside the permitted bank corridor')
            props={'river':name,'part':li,'length_m':route.length,'reference_length_m':line.length,
                   'maximum_axis_offset_m':deviation,'maximum_anchor_shift_m':float(snap.max()),
                   'clear_channel_m':24,'minimum_triangle_support_radius_m':20.5,
                   'status':'DESIGN_ROUTE_NOT_CARVED'}
            features.append({'type':'Feature','properties':props,'geometry':mapping(route)})
            reports.append(props)
        print(f'{name}: {len(lines)} reference chains routed',flush=True)
    save_json(EV/'fairways-main-game.json',{'type':'FeatureCollection','coordinate_system':'local game X/Z metres','features':features})
    save_json(EV/'protected-islands-game.json',{'type':'FeatureCollection','coordinate_system':'local game X/Z metres','features':[
        {'type':'Feature','properties':{'area_m2':g.area},'geometry':mapping(g)} for g in islands]})
    save_json(EV/'fairway-design.json',{'status':'PASS_PLAN_GEOMETRY_NOT_TERRAIN','islands_protected':len(islands),
        'source_water_sha256':hashlib.sha256(waterpath.read_bytes()).hexdigest(),'routes':reports,
        'limits':['The 6m terrain cannot individually represent every sub-cell polygon sliver; those remain in the unchanged source inventory.',
                  '24m channel is a design envelope. Continuous bathymetry, objects, corners and physical boat passage remain unverified.',
                  'Branches are retained; this does not yet prove connected regional travel routes.']})
    print(json.dumps({'routes':len(features),'total_m':sum(r['length_m'] for r in reports),'maximum_axis_offset_m':max(r['maximum_axis_offset_m'] for r in reports)}))


if __name__=='__main__':main()
