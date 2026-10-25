"""Repeat scalar/presence disagreements with controlled order and both weather phases."""
from pathlib import Path
import json,hashlib,shutil,sys,subprocess
import numpy as np
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-global-water-risk-2026-10-09';B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
sys.path.insert(0,str(W/'tools/terrain'));from v30_common import tri_sample
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=json.loads((E/'halo-r2-consumers-reference.json').read_text());points=ref['points'];assert len(points)==120
h=np.load(B/'measured-bank-bed-r1/terrain.npz')['heights']
for n,p in enumerate(json.loads((E/'scalar-wave-contact-classification.json').read_text())['points']):
    points.append(dict(id=9000+n,x=p['x'],z=p['z'],role='diagnostic_query_disagreement',reach='GLOBAL',case='unflagged_positive_depth',expected_ground_m=float(tri_sample(h,p['x'],p['z']))))
assert len(points)==351 and len({p['id'] for p in points})==351
name='BalticScalarTemporalV1.BalticTrial';mission=B/'missions'/name;mission.mkdir(parents=True,exist_ok=False)
code=(B/'missions/BalticHaloConsumersV2.BalticTrial/init.c').read_text().replace('halo_consumers_v2','scalar_temporal_v1').replace('halo_consumers_order_v2','scalar_temporal_order_v1')
code=code.replace('m_Rows.Count() == 120','m_Rows.Count() == 351').replace('END;62;120','END;62;351')
(mission/'init.c').write_text(code);(mission/'points.csv').write_text(''.join(f'{p["id"]};{p["x"]:.9f} 0 {p["z"]:.9f}\n' for p in points))
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(mission)],capture_output=True,text=True)
got=json.loads(lint.stdout);assert lint.returncode==0 and not got['errors'] and got['info']['files_scanned']==1
(E/'scalar-temporal-lint.json').write_text(lint.stdout)
dst=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/name;shutil.copytree(mission,dst)
ref.update(mission=str(dst),files={p.name:sha(p) for p in mission.iterdir()})
assert all(sha(dst/n)==v for n,v in ref['files'].items())
for name,digest in ref['deployed'].items():assert sha(Path(name))==digest
(E/'scalar-temporal-reference.json').write_text(json.dumps(ref,indent=2)+'\n')
verify=(B/'verify_halo_r2_consumers.py').read_text().replace('halo-r2-consumers','scalar-temporal').replace('halo_consumers_v2','scalar_temporal_v1').replace('halo_consumers_order_v2','scalar_temporal_order_v1')
verify=verify.replace('PASS_HALO_CONSUMERS_READBACK','PASS_SCALAR_TEMPORAL_CONTROLS')
verify=verify.replace('28 historical controls plus 25 microgap neighbourhood points, 60 repaired dry-bank neighbourhood points and 7 calibrated points. No maximum wave envelope.','120 R2 controls plus 231 diagnostic scalar disagreements. A control PASS does not accept the diagnostic dry points or maximum-wave envelope.')
(B/'verify_scalar_temporal.py').write_text(verify)
print(json.dumps(dict(mission=str(dst),points=len(points),status='READY_DIAGNOSTIC_TEMPORAL')))
