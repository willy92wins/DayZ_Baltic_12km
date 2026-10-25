from pathlib import Path
import json,hashlib,shutil,sys,subprocess
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-global-water-risk-2026-10-09'
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009');H=B/'halo-fix-v2'
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=Path('P:/Mods/@DayZ_Baltic_ValleySmoothC1R3P/Addons')
assert sha(base/'narva_trial.pbo')=='75adb673ed23ab5b656a162063d6a89cbb2e0a0d99aba82263bf2a54a31e8623'
_,pa,a=read_pbo(base/'narva_trial.pbo');_,pb,b=read_pbo(H/'world/out/narva_trial.pbo')
assert pa==pb and set(a)==set(b)
changed=[k for k in a if a[k]!=b[k]];assert changed==['baltic_trial.wrp'],changed
assert b['baltic_trial.wrp'].startswith(b'OPRW')
dest=Path('P:/Mods/@DayZ_Baltic_HaloFixV1/Addons');dest.mkdir(parents=True,exist_ok=False)
for p in (H/'world/out/narva_trial.pbo',H/'water/packed/baltic_water_v30.pbo'):
    shutil.copyfile(p,dest/p.name);assert sha(p)==sha(dest/p.name)
files={p.name:sha(p) for p in dest.glob('*.pbo')}
(E/'halo-deploy.json').write_text(json.dumps(dict(status='ISOLATED_HALO_PREVIEW_NOT_ACCEPTED',destination=str(dest.parent),files=files,changed_world_entries=changed),indent=2)+'\n')
name='BalticHaloFullWaterV1.BalticTrial';src=B/'missions/BalticNativeFullWaterV1.BalticTrial';mission=B/'missions'/name;mission.mkdir(parents=True,exist_ok=False)
code=(src/'init.c').read_text().replace('BalticNativeFullWaterMission','BalticHaloFullWaterMission').replace('baltic_native_fullwater_v1.log','baltic_halo_fullwater_v1.log')
(mission/'init.c').write_text(code)
for n in ('grid.csv','risks.csv'):shutil.copyfile(src/n,mission/n)
deploy=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/name;shutil.copytree(mission,deploy)
ref=json.loads((E/'native-fullwater-reference.json').read_text());ref.update(pbo=files,mission=str(deploy),files={p.name:sha(p) for p in mission.iterdir()})
assert all(sha(deploy/n)==digest for n,digest in ref['files'].items())
(E/'halo-fullwater-reference.json').write_text(json.dumps(ref,indent=2)+'\n')
verify=(B/'verify_native_fullwater.py').read_text().replace('native-fullwater','halo-fullwater').replace('baltic_native_fullwater','baltic_halo_fullwater').replace('native-physical-anomalies','halo-physical-anomalies')
(B/'verify_halo_fullwater.py').write_text(verify)
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(mission)],capture_output=True,text=True)
got=json.loads(lint.stdout);assert lint.returncode==0 and not got['errors'] and got['info']['files_scanned']==1
(E/'halo-fullwater-lint.json').write_text(lint.stdout)
print(json.dumps(dict(mission=str(deploy),pbo=files,world_other_entries_exact=True,lint='PASS')))
