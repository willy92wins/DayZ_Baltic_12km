from pathlib import Path
import json,sys,hashlib,shutil
import numpy as np
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-global-water-risk-2026-10-09'
sys.path.insert(0,str(W/'tools/terrain'));from wrp0wzd import read,write
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=json.loads((E/'last-nominal-pocket-verification.json').read_text());assert ref['status']=='PASS_OFFLINE_LAST_NOMINAL_POCKET'
old=np.load(B/'measured-bank-bed-r1/terrain.npz')['heights'];new=np.load(B/'measured-bank-bed-r2/terrain.npz')['heights']
assert sha(B/'measured-bank-bed-r2/terrain.npz')==ref['terrain_sha256']
src=B/'halo-fix-v3/world/root/dayz_baltic_12km_dev/tb/narva_trial'
dst=B/'halo-fix-v4/world/root/dayz_baltic_12km_dev/tb/narva_trial';shutil.copytree(src,dst,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
a=read(src/'baltic_trial.wrp');assert np.array_equal(a['heights'],old[::-1])
write(dst/'baltic_trial.wrp',a['header'],new[::-1],a['materials'],[o['bytes'] for o in a['objects']],a['terminator'])
b=read(dst/'baltic_trial.wrp');assert np.array_equal(b['heights'],new[::-1]) and all(a[k]==b[k] for k in ('header','materials','terminator'))
assert [o['bytes'] for o in a['objects']]==[o['bytes'] for o in b['objects']]
build=(B/'build_halo_world_r2.ps1').read_text().replace('halo-fix-v3','halo-fix-v4')
build=build.replace("(Join-Path $buildRoot 'water\\temp\\baltic_water_v30')","'E:\\DayZ-Baltic-Build\\v30-global-water-risk-20261009\\halo-fix-v3\\water\\temp\\baltic_water_v30'")
(B/'build_last_pocket_world.ps1').write_text(build)
out=dict(status='LAST_POCKET_WORLD_STAGED',terrain_sha256=ref['terrain_sha256'],world_source_sha256=sha(dst/'baltic_trial.wrp'),objects_exact=True,materials_exact=True,
    changed_vertices=int((old!=new).sum()),water_sha256='4ac3cb01770dbbd825df24bd4e5869869a56188cf40acc17cb882ecb2f86539b')
(E/'last-pocket-world-stage.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
