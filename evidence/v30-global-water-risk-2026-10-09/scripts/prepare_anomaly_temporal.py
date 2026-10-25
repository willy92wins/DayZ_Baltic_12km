"""Bounded native diagnostic of all census anomalies, offsets and calibrated controls."""
from pathlib import Path
import sys,json,hashlib,subprocess,shutil
import numpy as np
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009');E=W/'evidence/v30-global-water-risk-2026-10-09'
sys.path.insert(0,str(W/'tools/terrain'))
from prepare_water_temporal_v30 import SCRIPT,revision_three
from v30_common import tri_sample
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((E/'native-anomaly-classification.json').read_text())['points'];points=[]
for j,p in enumerate(base):
    for suffix,dx,dz in [('exact',0,0),('east',.02,0),('west',-.02,0),('north',0,.02),('south',0,-.02)]:
        points.append(dict(id=len(points),case=j,role=p['reason'],offset=suffix,x=float(p['x'])+dx,z=float(p['z'])+dz,cls=int(p['cls'])))
ref=json.loads((E/'native-fullwater-reference.json').read_text())
for p in ref['points']:points.append(dict(p,id=len(points),role='calibrated_'+str(p.get('label',p.get('name','point'))),offset='exact'))
source=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008/candidate-c1r3p/terrain_valley.npz')
assert sha(source)==ref['terrain_sha256'];h=np.load(source)['heights']
expected=tri_sample(h,np.array([p['x'] for p in points]),np.array([p['z'] for p in points]))
for p,y in zip(points,expected):p['expected_ground']=float(y)
code=revision_three(SCRIPT).replace('TemporalV3','AnomalyTemporalV1').replace('TEMPORAL_V3','ANOMALY_TEMPORAL_V1')
code=code.replace('water_temporal_v3','water_anomaly_temporal_v1').replace('water_order_v3','water_anomaly_order_v1').replace('WATER_ORDER_V3','WATER_ANOMALY_ORDER_V1')
code=code.replace('151','31').replace('302','62').replace('== 17','== '+str(len(points))).replace(';17"',';'+str(len(points))+'"')
name='BalticAnomalyTemporalV1.BalticTrial';dest=B/'missions'/name;dest.mkdir(parents=True,exist_ok=False)
(dest/'init.c').write_text(code)
(dest/'points.csv').write_text(''.join(f'{p["id"]};{p["x"]:.9f} 0 {p["z"]:.9f}\n' for p in points))
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(dest)],capture_output=True,text=True)
r=json.loads(lint.stdout);assert lint.returncode==0 and not r['errors'] and r['info']['files_scanned']==1,lint.stdout
(E/'anomaly-temporal-lint.json').write_text(lint.stdout)
deploy=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/name
shutil.copytree(dest,deploy)
files={p.name:sha(p) for p in dest.iterdir()};assert all(sha(deploy/k)==v for k,v in files.items())
for name,digest in ref['pbo'].items():assert sha(Path('P:/Mods/@DayZ_Baltic_ValleySmoothC1R3P/Addons')/name)==digest
out=dict(status='PREPARED_NOT_RUN',mission=str(deploy),files=files,points=points,terrain_sha256=ref['terrain_sha256'],pbo=ref['pbo'],samples=62,interval_s=2,phases=['31 calm samples','30 s settle','31 storm samples'],
    limits=['API with fake wave is recorded as a native query, not presumed identical to the client sea shader.','0.02 m offsets discriminate seam/overlap width and presence flags; full raster already covered separately.'])
(E/'anomaly-temporal-reference.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(mission=str(deploy),points=len(points),samples=62,lint='PASS')))
