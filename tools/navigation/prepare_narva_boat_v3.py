"""Freeze a navigable Narva lane around bridge piers; preserve V1/V2 failures."""
from pathlib import Path
import copy, hashlib, heapq, json, math
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from shapely import STRtree, points, distance
from shapely.geometry import shape, LineString, mapping
from waterway_common import sample

ROOT = Path(__file__).resolve().parents[2]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ev = ROOT/'evidence/overnight-2026-10-01/narva-boat-v3'
    mission = ROOT/'missions/BalticNarvaBoatV3.BalticTrial'
    assert not ev.exists() and not mission.exists(), 'Fresh outputs required'
    parent = ROOT/'evidence/overnight-2026-10-01/regional-boat-v2/reference.json'
    assert sha(parent) == 'ec24583ac6f362de2b4b1b06a86f9eea809001ad2700f9892c128d717880e64e'
    ref = json.loads(parent.read_text())
    asc = Path(ref['terrain'])
    assert sha(asc) == ref['terrain_sha256']
    with rasterio.open(asc) as ds: h = ds.read(1)
    water_path = ROOT/'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson'
    assert sha(water_path) == 'df860f693a1bf0115cb4af65a13cea5f8006a5a21bc9bca1d88276b83802ccdc'
    water = json.loads(water_path.read_text())['features']
    tree = STRtree([shape(f['geometry']) for f in water])
    levels = np.array([f['properties']['level_m'] for f in water])
    def water_depth(xz):
        hits = tree.query(points(xz), predicate='intersects')
        level = np.full(len(xz), -np.inf)
        np.maximum.at(level, hits[0], levels[hits[1]])
        return level, level - sample(h, xz[:, 0]+200000, xz[:, 1])

    collision_path = ROOT/'evidence/overnight-2026-10-01/narva-pier-discriminator/collision-and-route.geojson'
    collision_data = json.loads(collision_path.read_text())['features']
    collision = shape(next(f['geometry'] for f in collision_data if f['properties'].get('version') == 'v10'))
    axes_path = ROOT/'evidence/regional-foundation-v1/fairways-main-game.json'
    assert sha(axes_path) == '863f3d14e0c0e10c4447b7989a7efbdd1fc48f029cb31ccb8a790d80b7757367'
    axis = shape(json.loads(axes_path.read_text())['features'][30]['geometry'])
    # New endpoints cross the full bridge zone; old V2 ended alongside a pier.
    endpoints = [np.array(axis.interpolate(s).coords[0]) for s in (35, 300)]
    x, z = np.arange(2310., 2511.), np.arange(6800., 7011.)
    xx, zz = np.meshgrid(x, z)
    xz = np.c_[xx.ravel(), zz.ravel()]
    _, depth = water_depth(xz)
    deep = (depth >= 3).reshape(xx.shape)
    shore_clearance = distance_transform_edt(deep)
    obstacle_clearance = distance(points(xz), collision).reshape(xx.shape)
    # One metre raster cushion; final acceptance below uses continuous geometry.
    free = (shore_clearance >= 7) & (obstacle_clearance >= 5)
    start, goal = [tuple(np.round((p-[x[0], z[0]])[::-1]).astype(int)) for p in endpoints]
    assert free[start] and free[goal], 'Frozen endpoints lack design clearance'
    queue = [(0., start)]; cost = {start: 0.}; previous = {}
    while queue:
        _, node = heapq.heappop(queue)
        if node == goal: break
        for dz, dx in ((0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)):
            nxt = (node[0]+dz, node[1]+dx)
            if not (0 <= nxt[0] < len(z) and 0 <= nxt[1] < len(x)): continue
            if not (free[nxt] and free[node[0], nxt[1]] and free[nxt[0], node[1]]): continue
            penalty = 1 + 3/max(1., min(shore_clearance[nxt], obstacle_clearance[nxt]))
            value = cost[node] + math.hypot(dx,dz)*penalty
            if value < cost.get(nxt, math.inf):
                cost[nxt] = value; previous[nxt] = node
                heapq.heappush(queue, (value+math.dist(nxt,goal),nxt))
    assert goal in cost, 'No lane satisfies the frozen width and depth'
    nodes = [goal]
    while nodes[-1] != start: nodes.append(previous[nodes[-1]])
    raw = [[x[p[1]], z[p[0]]] for p in nodes[::-1]]
    raw[0], raw[-1] = endpoints
    lane = LineString(raw).simplify(.7)
    dense = np.array([lane.interpolate(s).coords[0] for s in np.linspace(0,lane.length,math.ceil(lane.length/.25)+1)])
    minimum_collision = lane.distance(collision)
    assert minimum_collision >= 4, minimum_collision
    # Disc samples radius6m at 16 angles; this is sampled depth, not exact solid proof.
    angles = np.linspace(0,2*np.pi,16,endpoint=False)
    offsets = np.vstack([[[0.,0.]], np.c_[np.cos(angles),np.sin(angles)]*6])
    checks = (dense[:,None,:] + offsets[None,:,:]).reshape(-1,2)
    _, checked_depth = water_depth(checks)
    assert np.isfinite(checked_depth).all() and checked_depth.min() >= 3, float(checked_depth.min())
    waypoints = np.array([lane.interpolate(s).coords[0] for s in np.linspace(0,lane.length,math.ceil(lane.length/4)+1)],dtype='float32').astype(float)
    w, waypoint_depth = water_depth(waypoints)
    cases, csv = [], []
    for ident, reverse in enumerate((False, True)):
        order = np.arange(len(waypoints))[::-1] if reverse else np.arange(len(waypoints))
        for seq,j in enumerate(order): csv.append(f'{ident};{seq};{waypoints[j,0]:.9g};{w[j]:.9g};{waypoints[j,1]:.9g}')
        cases.append(dict(case=ident,river='Narva',reverse=reverse,waypoints_xz=waypoints[order].tolist(),water_levels=w[order].tolist(),source_line_xz=list(lane.coords)[::-1] if reverse else list(lane.coords),length_m=lane.length,minimum_dense_center_depth_m=float(water_depth(dense)[1].min())))
    source = ROOT/'tools/navigation/regional_boat_v2_init.c'
    text = source.read_text()
    assert text.count('m_Case >= 8') == 1
    text = text.replace('m_Case >= 8','m_Case >= 2').replace('baltic_regional_boat_v2.log','baltic_narva_boat_v3.log')
    # Keep V2 log schema so the independently controlled verifier is unchanged.
    mission.mkdir(parents=True); ev.mkdir(parents=True)
    (mission/'init.c').write_text(text,encoding='utf-8',newline='\n')
    (mission/'routes.csv').write_text('\n'.join(csv)+'\n',encoding='ascii')
    ref.update(cases=cases, parent_reference_sha256=sha(parent), routes_and_criteria_unchanged=False,
               mission={str(p):sha(p) for p in mission.iterdir()},
               route_change='Only Narva: route around piers, endpoints station35..300; no terrain/object/physics changes',
               limits=['Empty vanilla boat, separate outward/reverse spawns; no crew or turn-around proof.',
                       'Single Narva lane, not all regional rivers; V1/V2 failures preserved.',
                       'Medium-vessel envelope is geometric design only; no chosen asset.',
                       'Native reopen/persistence gate still pending.'])
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
    design = dict(status='FROZEN_OFFLINE_CANDIDATE_NOT_ENGINE_ACCEPTED',inputs={str(p):sha(p) for p in (parent,asc,water_path,axes_path,collision_path,source)},
                  length_m=lane.length, minimum_center_to_projected_collision_m=minimum_collision,
                  depth_samples=len(checks), sampled_depth_disc_radius_m=6.,minimum_sampled_depth_m=float(checked_depth.min()),
                  criteria_unchanged=ref['criteria'], reference_sha256=sha(ev/'reference.json'),
                  limits=['Projected collision slab from previous boat vertical range, not full 3D swept ship.',
                          'Disc samples do not prove a continuous volume; actual engine consumer remains required.'])
    (ev/'design.json').write_text(json.dumps(design,indent=2)+'\n')
    (ev/'route.geojson').write_text(json.dumps(dict(type='Feature',properties={'kind':'Narva_lane_candidate_v3'},geometry=mapping(lane))))
    print(json.dumps(design,indent=2))


if __name__ == '__main__': main()
