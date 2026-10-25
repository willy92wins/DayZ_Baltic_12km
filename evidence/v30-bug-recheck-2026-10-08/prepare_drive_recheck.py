"""Repeat the six accepted routes with current ground and the accepted V3/V4 controllers."""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'tools/navigation'))
from waterway_common import sample

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
old = ROOT/'evidence/foundation-followup-2026-10-01/regional-drive-v3/reference.json'
ref = copy.deepcopy(json.loads(old.read_text()))
asc = Path('E:/DayZ-Baltic-Build/v30-bounded-integration-20261008/combined-reference.asc')
assert sha(asc)=='8f6f76efdf8c5b637e27106a84eba0bbbe9f115026d84d2ce75f611d598aa76b'
with rasterio.open(asc) as ds:
    h = ds.read(1).astype(float)
geometry=[]
for case in ref['cases']:
    route = np.asarray(case['route_xyz'], dtype=np.float32)
    route[:,1] = sample(h,route[:,0].astype(float)+200000,route[:,2].astype(float))
    case['route_xyz'] = route.tolist()
    xy=route[:,[0,2]].astype(float)
    station=np.r_[0,np.cumsum(np.linalg.norm(np.diff(xy,axis=0),axis=1))]
    s=np.linspace(0,station[-1],int(np.ceil(station[-1]))+1)
    q=np.column_stack([np.interp(s,station,xy[:,i]) for i in range(2)])
    tang=np.gradient(q,axis=0);normal=np.column_stack([-tang[:,1],tang[:,0]])/np.linalg.norm(tang,axis=1)[:,None]
    across=np.array([
        sample(h,q[:,0]+v*normal[:,0]+200000,q[:,1]+v*normal[:,1]) for v in np.arange(-4,4.01,.5)])
    geometry.append(dict(case=case['case'], samples=len(q), cross_max_m=float(np.ptp(across,axis=0).max()),
                         grade_max=float((abs(np.diff(across[8]))/np.diff(s)).max())))
source=ROOT/'missions/BalticRegionalDriveV3.BalticTrial/init.c'
assert sha(source)=='904eb01741a47067d2e702e8d8d744945af140f290d9e2f8aba5dccfdc1c6d95'
code=source.read_text().replace('baltic_regional_drive_v3','baltic_bug_recheck_drive_v1')
anchor='                throttle=Math.Clamp(0.1+(desiredSpeed - speed)*0.25,0,0.5);'
assert code.count(anchor)==1
code=code.replace(anchor,anchor+'\n                if (m_Case>=4 && remaining.Length()<8 && speed<0.2) throttle=0.5;')
mission=ROOT/'missions/BalticBugRecheckDriveV1.BalticTrial'
deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
mission.mkdir(exist_ok=False)
(mission/'init.c').write_text(code,encoding='utf-8',newline='\n')
(mission/'routes.csv').write_text(''.join(f"{c['case']};{i};{p[0]:.9g};{p[1]:.9g};{p[2]:.9g}\n"
    for c in ref['cases'] for i,p in enumerate(c['route_xyz'])),encoding='ascii',newline='\n')
lint=subprocess.run([sys.executable,'-X','utf8',
    'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(mission)],
    capture_output=True,text=True)
(OUT/'drive-lint.json').write_text(lint.stdout,encoding='utf-8')
check=json.loads(lint.stdout)
assert lint.returncode==0 and not check['errors'] and check['info']['files_scanned']==1
shutil.copytree(mission,deployed)
world=Path('P:/Mods/@DayZ_Baltic_BoundedSmoothingPreview/Addons/narva_trial.pbo')
probe=Path('P:/Mods/@BalticDriveInputProbe/Addons/baltic_drive_input.pbo')
assert sha(world)=='9768119eb687517957831f126156fb1707c954ebac76b6dc271d57bef33421aa'
assert sha(probe)==ref['input_pbo_sha256']
ref.update(status='FROZEN_CURRENT_TERRAIN_BEFORE_RUNTIME',terrain=str(asc),terrain_sha256=sha(asc),
    mission={str(p):sha(p) for p in mission.iterdir()},deployed_mission=str(deployed),route_geometry=geometry,
    inputs={str(old):sha(old),str(source):sha(source)},log_name='baltic_bug_recheck_drive_v1.log',
    deployment={str(p):sha(p) for p in [world,world.with_name('baltic_water_v30.pbo'),probe]},
    scope='Six frozen coast/hills/south journeys on the current combined preview; 25/35 kmh empty sedan.',
    limits=['Original physical thresholds; V3 controller on cases0-3, accepted V4 terminal assistance on cases4-5.',
            'No whole-network, human-driver or performance acceptance.'])
assert all(sha(deployed/Path(p).name)==digest for p,digest in ref['mission'].items())
(OUT/'drive-reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(mission=str(deployed),geometry=geometry,reference_sha256=sha(OUT/'drive-reference.json')),indent=1))
