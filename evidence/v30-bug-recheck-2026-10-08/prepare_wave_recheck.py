"""Repeat the historical wave observer on current terrain; retain every coordinate."""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/terrain'))
from v30_common import tri_sample,cell_planes
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
previous=Path('E:/DayZ-Baltic-Build/v30-water-temporal-v3/reference.json')
ref=copy.deepcopy(json.loads(previous.read_text()))
source=ROOT/'missions/BalticV30WaterTemporalV3.BalticTrial'
assert all(sha(source/name)==value for name,value in ref['files'].items())
terrain=Path('E:/DayZ-Baltic-Build/v30-bounded-integration-20261008/combined/terrain_inland.npz')
t=np.load(terrain);h=t['heights'].astype(float);plane=cell_planes(t['cls'],t['level'],sea_cut=.51)
for point in ref['points']:
    point['historical_expected_ground_m']=point['expected_ground_m']
    point['expected_ground_m']=float(tri_sample(h,point['x'],point['z']))
    r,c=int((12282-point['z'])//6),int(point['x']//6)
    p=float(plane[r,c]) if np.isfinite(plane[r,c]) else None
    point['current_nominal_cell_depth_m']=p-point['expected_ground_m'] if p is not None else None
mission=ROOT/'missions/BalticBugRecheckWaterV1.BalticTrial'
deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
mission.mkdir(exist_ok=False)
code=(source/'init.c').read_text().replace('baltic_v30_water_temporal_v3.log','baltic_bug_recheck_water_v1.log')
code=code.replace('baltic_v30_water_order_v3.log','baltic_bug_recheck_water_order_v1.log')
(mission/'init.c').write_text(code,encoding='utf-8',newline='\n')
shutil.copyfile(source/'points.csv',mission/'points.csv')
lint=subprocess.run([sys.executable,'-X','utf8',
    'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(mission)],
    capture_output=True,text=True)
(OUT/'wave-lint.json').write_text(lint.stdout,encoding='utf-8')
check=json.loads(lint.stdout);assert lint.returncode==0 and not check['errors'] and check['info']['files_scanned']==1
shutil.copytree(mission,deployed)
ref.update(status='PREPARED_CURRENT_GEOMETRY_DIAGNOSTIC',mission=str(mission),deployed_mission=str(deployed),
    terrain_sha256=sha(terrain),parent_reference_sha256=sha(previous),
    files={p.name:sha(p) for p in mission.iterdir()},
    limits=['Historical point roles retained for traceability. Points now dry after accepted outline changes are not current wet-water failures.',
            'Use the series to isolate actual water presence and exposure on the still-wet points; no global visual/navigation acceptance.'])
assert all(sha(deployed/name)==value for name,value in ref['files'].items())
(OUT/'wave-reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(mission=str(deployed),points=len(ref['points']),samples=ref['samples'],reference_sha256=sha(OUT/'wave-reference.json'))))
