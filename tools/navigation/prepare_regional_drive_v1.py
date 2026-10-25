"""Freeze six native sedan tests across three existing road corridors."""
from pathlib import Path
import hashlib,json,shutil
import numpy as np
import rasterio
from shapely.geometry import LineString
from waterway_common import sample
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parent=ROOT/'evidence/overnight-2026-10-01/foundation-drive-v3/reference.json'
    source=ROOT/'missions/BalticFoundationDriveV3.BalticTrial/init.c'
    assert sha(source)=='4ecf038741a04d83a99246671f168e2370a013864826ca6b07b1e45c4f2cad84'
    ev=ROOT/'evidence/foundation-followup-2026-10-01/regional-drive-v1'
    mission=ROOT/'missions/BalticRegionalDriveV1.BalticTrial'
    deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
    for p in [ev,mission,deployed]:assert not p.exists(),str(p)
    ref=json.loads(parent.read_text(encoding='utf-8'))
    assert sha(Path(ref['terrain']))==ref['terrain_sha256']
    roads=np.load(ROOT/'tests/regional_foundation_roads_v6/reference.npz')
    chains=json.loads((ROOT/'evidence/regional-foundation-v1/road-grade-chains-v6.json').read_text(encoding='utf-8'))['chains']
    with rasterio.open(ref['terrain']) as ds:h=ds.read(1)
    cases=[];geometry=[]
    for chain,lo,hi,name,speed in [(5,193,427,'coastal_corridor',25),(13,8,362,'hilly_interior',35),(68,954,1484,'southern_corridor',35)]:
        line=LineString(roads['xy'][chains[chain][lo:hi]])
        start=20.;end=min(line.length-20,start+1000)
        stations=np.linspace(start,end,int(np.ceil((end-start)/2))+1)
        xy=np.array([line.interpolate(float(s)).coords[0] for s in stations]);y=sample(h,xy[:,0]+200000,xy[:,1])
        delta=np.gradient(xy,axis=0);normal=np.column_stack([-delta[:,1],delta[:,0]])/np.linalg.norm(delta,axis=1)[:,None]
        across=np.array([sample(h,xy[:,0]+normal[:,0]*v+200000,xy[:,1]+normal[:,1]*v) for v in [-4,0,4]])
        grade=float(np.max(abs(np.diff(y)/np.diff(stations))));cross=float(np.ptp(across,axis=0).max())
        geometry.append(dict(name=name,chain=chain,lo=lo,hi=hi,length_m=end-start,maximum_grade=grade,maximum_cross_height_m=cross,full_width_gate_pass=grade<=.065 and cross<=.03))
        xyz=np.column_stack([xy[:,0],y,xy[:,1]]).astype('float32').astype(float)
        for reverse in [False,True]:cases.append(dict(case=len(cases),name=name,reverse=reverse,route_xyz=(xyz[::-1] if reverse else xyz).tolist(),length_m=end-start,target_speed_kmh=speed))
    code=source.read_text(encoding='utf-8').replace('baltic_foundation_drive_v3','baltic_regional_drive_v1').replace('m_Case>=3','m_Case>=6')
    anchor='                throttle=Math.Clamp(0.1+(6.94444 - speed)*0.25,0,0.5);\n                brake=Math.Clamp((speed - 7.4)*0.2,0,0.5);'
    assert code.count(anchor)==1
    code=code.replace(anchor,'                float desiredSpeed=9.722222;\n                if (m_Case<2) desiredSpeed=6.944444;\n                throttle=Math.Clamp(0.1+(desiredSpeed - speed)*0.25,0,0.5);\n                brake=Math.Clamp((speed - desiredSpeed - 0.455556)*0.2,0,0.5);')
    ev.mkdir();mission.mkdir()
    (mission/'init.c').write_text(code,encoding='utf-8')
    (mission/'routes.csv').write_text(''.join(f"{c['case']};{i};{p[0]:.9g};{p[1]:.9g};{p[2]:.9g}\n" for c in cases for i,p in enumerate(c['route_xyz'])),encoding='ascii')
    shutil.copytree(mission,deployed)
    ref.update(status='FROZEN_DIAGNOSTIC_KNOWN_FULL_WIDTH_GEOMETRY_FAIL',parent_reference_sha256=sha(parent),parent_mission_sha256=sha(source),
        mission={str(p.resolve()):sha(p) for p in mission.iterdir()},deployed_mission=str(deployed),cases=cases,route_geometry=geometry,
        log_name='baltic_regional_drive_v1.log',scope='Six journeys, three distinct prepared road sectors, empty native sedan, 25/35kmh targets; no crossing or whole-network claim.',
        limits=['Full-width 8m geometry FAILED before this run; a physical PASS does not clear that failure.','Six journeys on three distinct terrain sectors; original verifier header/status names are legacy.','Empty sedan only; no human handling, physical road pieces, traffic or multiplayer load.','Wet approaches excluded and still require design/bridges; no change to world/navmesh.'])
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='PREPARED_NOT_RUN',cases=len(cases),geometry=geometry,reference_sha256=sha(ev/'reference.json'))))

if __name__=='__main__':main()
