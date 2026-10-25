from pathlib import Path
import json,hashlib,shutil,sys,subprocess
import numpy as np
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-global-water-risk-2026-10-09';B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
sys.path[:0]=[str(W/'tools/playtest'),str(W/'tools/terrain')]
from attach_navmesh import read_pbo
from v30_common import tri_sample
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=B/'measured-bank-bed-r2/terrain.npz';t=dict(np.load(source));h=t['heights'];cls=t['cls']
gate=json.loads((E/'last-nominal-pocket-verification.json').read_text());assert gate['status']=='PASS_OFFLINE_LAST_NOMINAL_POCKET' and sha(source)==gate['terrain_sha256']
old=Path('P:/Mods/@DayZ_Baltic_HaloFixV2/Addons');prior=json.loads((E/'halo-r2-deploy.json').read_text())
assert all(sha(old/n)==v for n,v in prior['files'].items())
_,pa,a=read_pbo(old/'narva_trial.pbo');_,pb,b=read_pbo(B/'halo-fix-v4/world/out/narva_trial.pbo')
assert pa==pb and set(a)==set(b) and [k for k in a if a[k]!=b[k]]==['baltic_trial.wrp']
dest=Path('P:/Mods/@DayZ_Baltic_HaloFixV3/Addons');dest.mkdir(parents=True,exist_ok=False)
for p in (B/'halo-fix-v4/world/out/narva_trial.pbo',old/'baltic_water_v30.pbo'):
    shutil.copyfile(p,dest/p.name);assert sha(p)==sha(dest/p.name)
files={p.name:sha(p) for p in dest.glob('*.pbo')}
(E/'halo-r3-deploy.json').write_text(json.dumps(dict(status='ISOLATED_LAST_POCKET_PREVIEW_NOT_ACCEPTED',destination=str(dest.parent),files=files,terrain_sha256=sha(source),water_exact_to_r2=True),indent=2)+'\n')
server=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')
def finish(mission,ref,report):
    lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(mission)],capture_output=True,text=True)
    data=json.loads(lint.stdout);assert lint.returncode==0 and not data['errors'] and data['info']['files_scanned']==1
    (E/(report+'-lint.json')).write_text(lint.stdout)
    dst=server/mission.name;shutil.copytree(mission,dst)
    ref.update(mission=str(dst),files={p.name:sha(p) for p in mission.iterdir()},terrain_sha256=sha(source),pbo=files,deployed={str(p):sha(p) for p in dest.glob('*.pbo')})
    assert all(sha(dst/n)==v for n,v in ref['files'].items())
    (E/(report+'-reference.json')).write_text(json.dumps(ref,indent=2)+'\n');print(json.dumps(dict(mission=str(dst),lint='PASS',pbo=files)))
old=B/'missions/BalticHaloFullWaterV2.BalticTrial';mission=B/'missions/BalticHaloFullWaterV3.BalticTrial';mission.mkdir(parents=True,exist_ok=False)
ref=json.loads((E/'halo-r2-fullwater-reference.json').read_text())
(mission/'init.c').write_text((old/'init.c').read_text().replace('baltic_halo_fullwater_v2','baltic_halo_fullwater_v3').replace(ref['terrain_sha256'],sha(source)))
shutil.copyfile(old/'risks.csv',mission/'risks.csv')
with (mission/'grid.csv').open('w',newline='') as f:
    for r in range(2048):
        for c in range(0,2048,32):
            fields=[]
            for j in range(c,c+32):fields.extend([format(float(h[r,j]),'.9g'),str(int(cls[r,j]))])
            f.write(f'{r};{c};'+';'.join(fields)+'\n')
finish(mission,ref,'halo-r3-fullwater')
verify=(B/'verify_halo_r2_fullwater.py').read_text().replace('halo-r2','halo-r3').replace('baltic_halo_fullwater_v2','baltic_halo_fullwater_v3').replace('measured-bank-bed-r1','measured-bank-bed-r2')
(B/'verify_halo_r3_fullwater.py').write_text(verify)
old=B/'missions/BalticScalarTemporalV1.BalticTrial';mission=B/'missions/BalticScalarTemporalV2.BalticTrial';mission.mkdir(parents=True,exist_ok=False)
ref=json.loads((E/'scalar-temporal-reference.json').read_text())
assert len(ref['points'])==351
for p in ref['points']:
    p['expected_ground_m']=float(tri_sample(h,p['x'],p['z']))
    if p['id']==9077:p['role']='dry_bank';p['case']='repaired_last_nominal_pocket'
(mission/'init.c').write_text((old/'init.c').read_text().replace('scalar_temporal_v1','scalar_temporal_v2').replace('scalar_temporal_order_v1','scalar_temporal_order_v2'))
shutil.copyfile(old/'points.csv',mission/'points.csv');finish(mission,ref,'scalar-r2-temporal')
verify=(B/'verify_scalar_temporal.py').read_text().replace('scalar-temporal','scalar-r2-temporal').replace('scalar_temporal_v1','scalar_temporal_v2').replace('scalar_temporal_order_v1','scalar_temporal_order_v2')
verify=verify.replace('231 diagnostic scalar disagreements','230 diagnostic scalar disagreements plus the repaired persistent pocket')
(B/'verify_scalar_r2_temporal.py').write_text(verify)
