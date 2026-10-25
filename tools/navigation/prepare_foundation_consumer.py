"""Freeze regional water/dry/nav queries before the foundation is loaded in game.

Input coordinates are float32, matching the consumer, before GIS classification.
This does not create any terrain, pond or actor in the running mission.
"""
from pathlib import Path
import argparse,csv
import hashlib
import json
import math
import numpy as np
from scipy.ndimage import distance_transform_edt
from shapely import STRtree, points, prepare
from shapely.geometry import shape, LineString
from shapely.ops import unary_union
from waterway_common import sample

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / 'evidence/regional-foundation-v1'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--terrain-version',default='v9');ap.add_argument('--probe-version',default='v3')
    args=ap.parse_args();tag=args.probe_version
    MISSION=ROOT/f'missions/BalticFoundationConsumer{tag.upper()}.BalticTrial'
    manifest = EV / f'consumer-reference-{tag}.json'
    if manifest.exists():
        raise ValueError('Frozen reference already exists; preserve it')
    asc = ROOT / f'tests/regional_foundation_combined_{args.terrain_version}/baltic_regional_foundation_{args.terrain_version}.asc'
    frozen={'v4':'e305b35fd8b89373de8303fb4b874f7822623e7516ddca0c4dd8d50f231c0816',
            'v8':'3ff3f7739d57cd7e8eee6524cd39a41782fc65ec4bc9903d88362b560860eea1',
            'v9':'335554a6ea06f8546eeac5444aec7597eaf45df18be0c69b0baab48a573947b2'}
    assert sha(asc) == frozen[args.terrain_version]
    ref = np.load(ROOT / f'tests/regional_foundation_combined_{args.terrain_version}/reference.npz')
    old = np.load(ROOT / 'tests/regional_outline_v3/reference.npz')
    h = ref['candidate']
    surfaces = json.loads((EV / 'water-surfaces-contour-v2.geojson').read_text())['features']
    geos = [shape(f['geometry']) for f in surfaces]
    levels = np.array([f['properties']['level_m'] for f in surfaces])
    ocean = shape(json.loads((EV / 'ocean-game.json').read_text())['features'][0]['geometry'])
    tree = STRtree(geos + [ocean])
    surface_levels = np.r_[levels, .5]
    water_union = unary_union(geos + [ocean])
    rows = []
    groups = {}

    def add_many(xz, kind, group, minimum_depth=0):
        xz = np.asarray(xz, dtype='float32').astype('float64')
        xz = np.clip(xz, .01, 12281.99)
        hits = tree.query(points(xz), predicate='intersects')
        water = np.full(len(xz), -np.inf)
        np.maximum.at(water, hits[0], surface_levels[hits[1]])
        ground = sample(h, xz[:, 0]+200000, xz[:, 1])
        if kind == 'W':
            if np.any(~np.isfinite(water)) or np.any(water-ground < minimum_depth):
                raise ValueError(f'Offline reference not navigable: {group}')
        elif np.any(np.isfinite(water)) or np.any(ground < 1.25):
            raise ValueError(f'Dry reference overlaps water: {group}')
        groups[group] = groups.get(group, 0) + len(xz)
        for (x,z), bottom, level in zip(xz, ground, water):
            rows.append([kind, len(rows), f'{x:.9g} 0 {z:.9g}', f'{bottom:.9g}',
                         f'{level:.9g}' if math.isfinite(level) else '0', minimum_depth, group])

    # Every 2 m along all selected channels, five positions across the 24 m width.
    for f in json.loads((EV / 'fairways-main-game.json').read_text())['features']:
        line = shape(f['geometry'])
        along = np.linspace(0, line.length, max(3, int(math.ceil(line.length/2))+1))
        xy = np.array([line.interpolate(float(d)).coords[0] for d in along])
        delta = np.gradient(xy, axis=0)
        normal = np.c_[-delta[:, 1], delta[:, 0]] / np.linalg.norm(delta, axis=1)[:, None]
        add_many(np.concatenate([xy + normal*offset for offset in (-12,-6,0,6,12)]),
                 'W', f"fairway_{f['properties']['river']}_{f['properties']['part']}", 3.0)

    # Sample each standing-water body at its deepest native vertex, well inside it.
    lake_count = 0
    for f,g in zip(surfaces,geos):
        body = f['properties']['body']
        if not body.startswith('lake_'):
            continue
        inner = g.buffer(-1)
        prepare(inner)
        x0,z0,x1,z1 = inner.bounds
        xx,zz = np.meshgrid(np.arange(max(6,math.ceil(x0/6)*6),min(12282,x1),6),
                            np.arange(max(6,math.ceil(z0/6)*6),min(12282,z1),6))
        p = np.c_[xx.ravel(),zz.ravel()]
        p = p[inner.contains(points(p))]
        if not len(p):
            p = np.array([g.representative_point().coords[0]])
        bottom = sample(h,p[:,0]+200000,p[:,1])
        best = np.argsort(bottom)[:min(5,len(p))]
        add_many(p[best], 'W', body, .15)
        lake_count += 1

    island_count = 0
    island_unavailable = []
    for i,f in enumerate(json.loads((EV / 'protected-islands-game.json').read_text())['features']):
        g = shape(f['geometry'])
        inner = g.buffer(-1)
        if inner.is_empty:
            inner = g
        p = np.array([inner.representative_point().coords[0]])
        ground = float(sample(h,p[:,0]+200000,p[:,1])[0])
        if ground < 1.25:
            island_unavailable.append({'index':i,'xz':p[0].tolist(),'ground':ground})
            continue
        add_many(p,'L','protected_island',0)
        island_count += 1

    # Navigation samples selected using the new geometry, before runtime results.
    land = (distance_transform_edt(~ref['wet'])*6 > 24) & (h >= 1.25)
    nav_points, routes = [], []
    for row in range(48,2000,96):
        for col in range(48,2000,96):
            if not land[row,col]:
                continue
            x,z = col*6,12282-row*6
            if water_union.distance(points(x,z)) <= 24:
                continue
            group = 'reserve' if old['reserve'][row,col] else 'spb' if old['spb'][row,col] else 'regional'
            nav_points.append(dict(index=len(nav_points),x=x,z=z,y=float(h[row,col]),group=group))
            add_many([[x,z]],'L','dry_'+group)
    # Preserve the previously proven six summit traverses with NEW expected heights.
    old_nav = json.loads((ROOT/'evidence/regional-outline-v3/nav-probe-reference.json').read_text())
    for route in old_nav['routes']:
        a,b = np.array(route['start']),np.array(route['end'])
        a[1] = sample(h,a[0]+200000,a[2]); b[1] = sample(h,b[0]+200000,b[2])
        assert LineString([a[[0,2]],b[[0,2]]]).distance(water_union)>12,route
        routes.append(dict(name=route['name'],start=a.tolist(),end=b.tolist()))
    # Additional dry traverses in reserve, SPB and the rest of the region.
    for group in ('reserve','spb','regional'):
        count = 0
        for p in [v for v in nav_points if v['group']==group]:
            x,z=p['x'],p['z']; end=[x+120,z]
            if end[0]>=12282 or LineString([[x,z],end]).distance(water_union)<=24:
                continue
            xs=np.linspace(x,x+120,41);ys=sample(h,xs+200000,np.full(41,z))
            if np.max(abs(np.diff(ys))/3)>.35:
                continue
            routes.append(dict(name=f'{group}_{count}',start=[x,p['y'],z],end=[x+120,float(ys[-1]),z]))
            count += 1
            if count==3:break
        assert count==3,(group,count)
    MISSION.mkdir(parents=True,exist_ok=True)
    water_file=MISSION/'water-points.csv'
    with water_file.open('w',newline='',encoding='utf-8') as f:
        csv.writer(f,delimiter=';',lineterminator='\n').writerows(rows)
    nav_file=MISSION/'nav-points.csv'
    with nav_file.open('w',newline='',encoding='utf-8') as f:
        out=csv.writer(f,delimiter=';',lineterminator='\n')
        for p in nav_points:out.writerow(['D',p['index'],f"{p['x']} 0 {p['z']}"])
        for r in routes:out.writerow(['Q',r['name'],' '.join(map(str,r['start'])),' '.join(map(str,r['end']))])
        out.writerow(['Q','negative','6000 0 6000','6060 0 6000'])
    nav_ref=dict(points=nav_points,routes=routes,height_tolerance_m=.06,sample_radius_m=2,path_max_length_factor=3,
                 header='BALTIC_FOUNDATION_NAV_'+tag.upper(),complete='BALTIC_FOUNDATION_NAV_COMPLETE')
    nav_reference=EV/f'foundation-nav-reference-{tag}.json'
    nav_reference.write_text(json.dumps(nav_ref,indent=2)+'\n')
    if tag!='v1':
        code=(ROOT/'missions/BalticFoundationConsumerV1.BalticTrial/init.c').read_text()
        (MISSION/'init.c').write_text(code.replace('_V1','_'+tag.upper()).replace('_v1.log','_'+tag+'.log'),encoding='utf-8',newline='\n')
    result=dict(status='FROZEN_BEFORE_ENGINE',asc_sha256=sha(asc),water_points=len(rows),groups=groups,
                lakes=lake_count,islands=island_count,island_unavailable=island_unavailable,
                nav_points=len(nav_points),nav_routes=len(routes),
                water_file_sha256=sha(water_file),nav_file_sha256=sha(nav_file),
                nav_reference_sha256=sha(nav_reference),mission_sha256=sha(MISSION/'init.c'),
                terrain_version=args.terrain_version,probe_version=tag,
                sources={name:sha(EV/name) for name in ('water-surfaces-contour-v2.geojson','fairways-main-game.json','protected-islands-game.json')},
                height_tolerance_m=.06,pond_surface_tolerance_m=.04,
                limits=['Fixed queries only; physical boats, actors, visual quality and load are separate gates.',
                        'No capacity claim for 80-100 players.'])
    manifest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('groups','sources','island_unavailable')},indent=2))


if __name__=='__main__':main()
