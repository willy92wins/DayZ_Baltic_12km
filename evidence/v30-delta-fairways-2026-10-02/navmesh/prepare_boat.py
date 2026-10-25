"""Freeze four physical delta boat routes; retain measured old input controller."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import numpy as np
import rasterio
from shapely.geometry import shape, MultiLineString, LineString
from shapely.ops import linemerge

ROOT=Path('P:/DayZ_Baltic_12km_dev');OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0,str(ROOT/'tools/navigation'))
from waterway_common import sample
source=ROOT/'missions/BalticRegionalBoatV3.BalticTrial/init.c'
assert sha(source)=='66e3515497ece9ace70b782c90acf2bddae378ae854c112f2f473abd6604e1e6'
old=ROOT/'evidence/overnight-2026-10-01/regional-boat-v3/reference.json'
assert sha(old)=='f4d8e84686947a437c88d2328cce9d0c9cac19b9cd5900a22546695e79c93bfb'
probe=Path('P:/Mods/@BalticBoatInputProbe/Addons/baltic_boat_input.pbo')
assert sha(probe)=='c5414ffe385eae5b85e1fe6dfef671db568d50a8eb11c74a3f4346f7c6417b2e'
terrain=Path('E:/DayZ-Baltic-Build/v30-delta-candidate/baltic_terrain_v30.asc')
assert sha(terrain)=='64d4f160b963c28b519a50c9c29564dbe9727facabf7b52d83970eef5b8e6eb4'
with rasterio.open(terrain) as ds:h=ds.read(1)
axes=ROOT/'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson'
features=json.loads(axes.read_text())['features']
lines={f['properties']['name']:shape(f['geometry']) for f in features if f['properties']['kind']=='axis'}
routes=[('Little Neva',linemerge(MultiLineString([lines[n] for n in ['Little Neva','Little Neva way/34348577','Neva way/78518216']]))),
        ('Great Neva',linemerge(MultiLineString([lines[n] for n in ['Great Neva','Neva way/78518216']])))]
cases=[];rows=[]
for name,line in routes:
    assert line.geom_type=='LineString'
    if np.linalg.norm(np.array(line.coords[-1])-[8677.391481895611,10228.008679892795])>.001:line=LineString(list(line.coords)[::-1])
    assert np.linalg.norm(np.array(line.coords[-1])-[8677.391481895611,10228.008679892795])<.001
    pts=np.array([line.interpolate(d).coords[0] for d in np.linspace(0,line.length,int(np.ceil(line.length/4))+1)],dtype=np.float32)
    for reverse in (False,True):
        p=pts[::-1].copy() if reverse else pts.copy();ground=sample(h,p[:,0].astype(float)+200000,p[:,1].astype(float))
        assert (.5-ground).min()>=3.04
        ident=len(cases);levels=[.75]*len(p)
        cases.append(dict(case=ident,river=name,reverse=reverse,waypoints_xz=p.astype(float).tolist(),water_levels=levels,axis_length_m=line.length,minimum_nominal_depth_at_waypoints_m=float((.5-ground).min())))
        rows += [f'{ident};{i};{x:.9g};0.75;{z:.9g}' for i,(x,z) in enumerate(p)]
mission=ROOT/'missions/BalticV30DeltaBoatV1.BalticTrial'
deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
assert not mission.exists() and not deployed.exists() and not (OUT/'boat-reference.json').exists()
code=source.read_text();assert code.count('m_Case >= 8')==1 and code.count('baltic_regional_boat_v3.log')==1
code=code.replace('m_Case >= 8','m_Case >= 4').replace('baltic_regional_boat_v3.log','baltic_v30_delta_boat_v1.log')
for folder in (mission,deployed):
    folder.mkdir();(folder/'init.c').write_bytes(code.encode());(folder/'routes.csv').write_bytes(('\n'.join(rows)+'\n').encode('ascii'))
for name in ('init.c','routes.csv'):assert (mission/name).read_bytes()==(deployed/name).read_bytes()
parent=json.loads(old.read_text())
ref=dict(status='FROZEN_BEFORE_ENGINE',terrain=str(terrain),terrain_sha256=sha(terrain),log_version=2,
    inputs={str(p):sha(p) for p in (axes,source,old)},deployment={str(probe):sha(probe)},
    mission={str(p):sha(p) for p in mission.iterdir()},deployed_mission=str(deployed),cases=cases,criteria=copy.deepcopy(parent['criteria']),
    limits=['Empty vanilla boat, independent forward/reverse spawns; no crew or complete turn acceptance.',
            'Only two delta branches and their real OSM connectors; no other river or medium-vessel acceptance.',
            'Controller and thresholds unchanged; bind exact corrected world PBO/NM in runtime receipt.'])
(OUT/'boat-reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='PREPARED_NOT_RUN',cases=len(cases),lengths_m=[c['axis_length_m'] for c in cases],mission=str(mission)),indent=2))
