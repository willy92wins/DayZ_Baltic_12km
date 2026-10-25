"""Read-only projected collision discriminator; engine contact remains separate."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import MultiPoint, LineString, Point, mapping
from shapely.ops import unary_union
from audit_assets import ODOL, get_lod, vertices, clip_plane, sha, ROOT


def main():
    ev=ROOT/'evidence/overnight-2026-10-01/narva-pier-discriminator'
    assert not ev.exists()
    model=Path('P:/DZ/structures/roads/bridges/bridge_metal_25.p3d')
    assert sha(model)=='baf79ddd19e08cdcdbec99b15043a319d6b958a1b7884082c2ae069cf3f3cee2'
    lod=get_lod(ODOL.from_file(str(model)),1e13)
    vv=vertices(lod)
    ref=json.loads((ROOT/'tests/narva_bridge_v10/reference.json').read_text())
    route_ref=ROOT/'evidence/overnight-2026-10-01/regional-boat-v1/reference.json'
    assert sha(route_ref)=='a2b77d0fbbd64b0abda36cb322beb51026bd8889ca47b15615c93015da3ce9d2'
    route=LineString(json.loads(route_ref.read_text())['cases'][0]['waypoints_xz'])
    log=ROOT/'evidence/overnight-2026-10-01/regional-boat-v1/runtime-complete/baltic_regional_boat_v1.log'
    assert sha(log)=='5063c2197cbb52b6cb5451deb035a21bcbc9eb889d094783ba9346c3a2d4a979'
    samples={i:np.array([[float(v) for v in r.split(';')[2:8]] for r in log.read_text().splitlines() if r.startswith(f'B;{i};')]) for i in (0,1)}
    # V1 scalar positions are rounded. Bounds below are diagnostic, not mm gates.
    boat_y=np.concatenate([a[:,2] for a in samples.values()])
    slab=[float(boat_y.min()-.5),float(boat_y.max()+1.5)]
    reports=[];features=[]
    for version in ('v9','v10'):
        solids=[]
        for obj in ref['objects']:
            if version=='v9' and obj['existing_id'] is None:continue
            origin=np.array(obj['native_xyz']);origin[1]-=2 if version=='v9' else 0
            rot=np.array(obj['native_rotation']).reshape(3,3)
            # Rows are native model axes; local Z follows the frozen road axis.
            world=vv@rot+origin
            for face in lod.faces:
                poly=[p for p in world[face.vertex_indices]]
                poly=clip_plane(poly,1,slab[0],False)
                poly=clip_plane(poly,1,slab[1],True)
                if len(poly)>1:
                    solids.append(MultiPoint([(p[0],p[2]) for p in poly]).convex_hull)
        obstacle=unary_union(solids)
        hits=route.intersection(obstacle)
        cases=[]
        for ident,a in samples.items():
            p=a[-1,[1,3]]
            cases.append(dict(case=ident,final_rounded_xz=p.tolist(),distance_to_projected_collision_m=Point(p).distance(obstacle)))
        reports.append(dict(version=version,obstacle_bounds=obstacle.bounds,axis_hits_geometry=not hits.is_empty,
                            axis_min_distance_m=route.distance(obstacle),intersection=mapping(hits),cases=cases))
        features.append(dict(type='Feature',properties=dict(kind='projected_collision',version=version),geometry=mapping(obstacle)))
    features.append(dict(type='Feature',properties=dict(kind='frozen_V1_route'),geometry=mapping(route)))
    ev.mkdir()
    result=dict(status='OFFLINE_COLLISION_CANDIDATE_ONLY',model_sha256=sha(model),log_sha256=sha(log),
                world_vertical_slab_m=slab,method='Geometry faces clipped to observed boat vertical band; local axes from native WRP poses; projected XZ union',
                versions=reports,limits=['Projected overlap does not prove an engine contact event.',
                'Boat reference point is not hull boundary; scalar final coordinates are rounded.',
                'V9 three span poses derived by undoing the verified +2m V10 change.'])
    (ev/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    (ev/'collision-and-route.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=features)))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
