"""Freeze eight boat cases against the deployed V9 water/terrain; never launch."""
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
from shapely import STRtree,points
from shapely.geometry import shape,LineString
from shapely.ops import substring
from waterway_common import sample

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ev=ROOT/'evidence/overnight-2026-10-01/regional-boat-v1'
    mission=ROOT/'missions/BalticRegionalBoatV1.BalticTrial'
    if mission.exists() or ev.exists(): raise ValueError('Fresh frozen outputs required')
    asc=ROOT/'tests/regional_foundation_combined_v9/baltic_regional_foundation_v9.asc'
    assert sha(asc)=='335554a6ea06f8546eeac5444aec7597eaf45df18be0c69b0baab48a573947b2'
    h=np.load(asc.parent/'reference.npz')['candidate']
    axes=ROOT/'evidence/regional-foundation-v1/fairways-main-game.json'
    features=json.loads(axes.read_text())['features']
    surface=ROOT/'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson'
    water=json.loads(surface.read_text())['features']
    ocean=ROOT/'evidence/regional-foundation-v1/ocean-game.json'
    geometries=[shape(f['geometry']) for f in water]+[shape(json.loads(ocean.read_text())['features'][0]['geometry'])]
    levels=np.r_[[f['properties']['level_m'] for f in water],.5]
    tree=STRtree(geometries)
    cases=[];rows=[]
    selections=[(30,35,125),(34,8000,8500),(35,2800,3300),(39,0,None)]
    for feature_index,start,end in selections:
        f=features[feature_index];axis=shape(f['geometry'])
        line=substring(axis,start,end if end is not None else axis.length)
        assert line.is_simple and line.length>50
        distances=np.linspace(0,line.length,math.ceil(line.length/4)+1)
        coords=np.array([line.interpolate(s).coords[0] for s in distances],dtype='float32').astype(float)
        dense=np.array([line.interpolate(s).coords[0] for s in np.linspace(0,line.length,math.ceil(line.length/.5)+1)],dtype='float32').astype(float)
        def query(xz):
            hits=tree.query(points(xz),predicate='intersects')
            lev=np.full(len(xz),-np.inf)
            np.maximum.at(lev,hits[0],levels[hits[1]])
            ground=sample(h,xz[:,0]+200000,xz[:,1])
            assert np.all(np.isfinite(lev)) and np.min(lev-ground)>=3
            return lev,ground
        w,g=query(coords);wd,gd=query(dense)
        for reverse in (False,True):
            order=np.arange(len(coords))[::-1] if reverse else np.arange(len(coords))
            case=len(cases)
            for seq,j in enumerate(order):
                rows.append(f'{case};{seq};{coords[j,0]:.9g};{w[j]:.9g};{coords[j,1]:.9g}')
            cases.append(dict(case=case,river=f['properties']['river'],feature_index=feature_index,part=f['properties']['part'],source_start_m=start,source_end_m=end,reverse=reverse,waypoints_xz=coords[order].tolist(),water_levels=w[order].tolist(),source_line_xz=list(line.coords)[::-1] if reverse else list(line.coords),length_m=line.length,minimum_dense_center_depth_m=float(np.min(wd-gd))))
    addon=Path('P:/Mods/@BalticBoatInputProbe/Addons/baltic_boat_input.pbo')
    raw,props,entries=read_pbo(addon)
    source=ROOT/'packages/boat-input-v2b/compiled/baltic_boat_input'
    expected={p.relative_to(source).as_posix():p.read_bytes() for p in source.rglob('*') if p.is_file()}
    assert entries==expected and props['prefix']=='baltic_boat_input'
    deployed={
        'P:/Mods/@DayZ_Baltic_FoundationV9Diag/Addons/narva_trial.pbo':'b99993dacaa1cfda1c18eeb4cb150d61622e31a2f2fce879833eb10386f00348',
        'P:/Mods/@DayZ_Baltic_FoundationV9Diag/Addons/baltic_water.pbo':'f9a5cdf7461ff09e80a102641289513896011a78b090fdbbd1056f9b985898d3',
    }
    for path,value in deployed.items(): assert sha(Path(path))==value,path
    mission.mkdir(parents=True);ev.mkdir(parents=True)
    (mission/'init.c').write_bytes((ROOT/'tools/navigation/regional_boat_init.c').read_bytes())
    (mission/'routes.csv').write_text('\n'.join(rows)+'\n',encoding='ascii')
    deployed[str(addon)]=sha(addon)
    receipt=dict(status='FROZEN_BEFORE_ENGINE',terrain_sha256=sha(asc),terrain=str(asc),inputs={str(p):sha(p) for p in (axes,surface,ocean)},deployment=deployed,mission={str(p):sha(p) for p in mission.iterdir()},cases=cases,criteria=dict(max_sample_dt_s=.8,max_step_m=3,max_health_loss=1,max_axis_distance_m=7,max_endpoint_distance_m=6,max_waypoint_distance_m=7,max_ground_error_m=.002,min_powered_motion_s=5),limits=['Empty boat only','Four selected sectors, not whole rivers','Fresh NM and V10 bridge acceptance are separate'])
    (ev/'reference.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(status=receipt['status'],mission=str(mission),reference=str(ev/'reference.json'),cases=[{k:v for k,v in c.items() if k not in ('waypoints_xz','water_levels','source_line_xz')} for c in cases]),indent=2))

if __name__=='__main__':main()
