"""Freeze the repaired observer before launch; preserve coordinates and phase gates."""
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
from v30_common import tri_sample
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
previous=OUT/'wave-reference.json'
ref=copy.deepcopy(json.loads(previous.read_text()))
source=ROOT/'missions/BalticBugRecheckWaterV1.BalticTrial'
assert all(sha(source/name)==value for name,value in ref['files'].items())
terrain=Path('E:/DayZ-Baltic-Build/v30-bug-recheck-20261008/wave-banks-r1/terrain_wave_banks.npz')
assert sha(terrain)=='b363b79dc8b4374a626644da78f110666139d382ee09a38dc7aade46b2e659dc'
before=json.loads((OUT/'wave-verification.json').read_text())
actual={p['id']:p for p in before['results']}
heights=np.load(terrain)['heights'].astype(float)
for point in ref['points']:
    point['before_repair_ground_m']=point['expected_ground_m']
    point['expected_ground_m']=float(tri_sample(heights,point['x'],point['z']))
    point['historical_role']=point['role']
    point['baseline_pond_samples']=actual[point['id']]['pond_true']
    if point['role']=='frozen_shallow_failure' and actual[point['id']]['pond_true']==0:
        point['role']='changed_outline_dry_control'
    if point.get('current_nominal_cell_depth_m') is not None:
        point['current_nominal_cell_depth_m']+=point['before_repair_ground_m']-point['expected_ground_m']
assert {p['id'] for p in ref['points'] if p['role']=='frozen_shallow_failure'}=={362,363,416,524,765,1176,1274}
mission=ROOT/'missions/BalticBugRecheckWaterV2.BalticTrial'
deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
mission.mkdir(exist_ok=False)
code=(source/'init.c').read_text().replace('baltic_bug_recheck_water_v1.log','baltic_bug_recheck_water_v2.log')
code=code.replace('baltic_bug_recheck_water_order_v1.log','baltic_bug_recheck_water_order_v2.log')
# Current 1.29 source: weather.c:158 WindMagnitude aliases WeatherPhenomenon;
# :205 GetWindMagnitude; :52 Set(forecast,time,minDuration); :74 SetLimits.
# SetWindSpeed alone is instantaneous; the V1 calm wind drifted up to 3.895 m/s.
old='    weather.SetWindSpeed(0.1);'
assert code.count(old)==1
code=code.replace(old,'    weather.GetWindMagnitude().SetLimits(0.1, 0.1);\n    weather.GetWindMagnitude().Set(0.1, 0, 3600);')
old='        weather.SetWindSpeed(20);'
assert code.count(old)==1
code=code.replace(old,'        weather.GetWindMagnitude().SetLimits(20, 20);\n        weather.GetWindMagnitude().Set(20, 0, 3600);')
(mission/'init.c').write_text(code,encoding='utf-8',newline='\n')
shutil.copyfile(source/'points.csv',mission/'points.csv')
lint=subprocess.run([sys.executable,'-X','utf8',
    'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(mission)],
    capture_output=True,text=True)
(OUT/'wave-fixed-lint.json').write_text(lint.stdout,encoding='utf-8')
check=json.loads(lint.stdout);assert lint.returncode==0 and not check['errors'] and check['info']['files_scanned']==1
shutil.copytree(mission,deployed)
ref.update(status='FROZEN_REPAIRED_CURRENT_SHORE_OBSERVER',mission=str(mission),deployed_mission=str(deployed),
    terrain_sha256=sha(terrain),parent_reference_sha256=sha(previous),
    baseline_series_sha256=sha(OUT/'wave-runtime.log'),
    files={p.name:sha(p) for p in mission.iterdir()},
    limits=['Seven historical shallow coordinates remain pond in all 302 baseline samples; six moved to dry ground before this fix.',
            'All 17 coordinates retained, with historical_role preserved. Classification frozen before repaired launch.',
            'Both weather phases must meet the original wind/overcast gates; no global visual/navigation acceptance.'])
assert all(sha(deployed/name)==value for name,value in ref['files'].items())
(OUT/'wave-fixed-reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(mission=str(deployed),points=len(ref['points']),samples=ref['samples'],reference_sha256=sha(OUT/'wave-fixed-reference.json'))))
