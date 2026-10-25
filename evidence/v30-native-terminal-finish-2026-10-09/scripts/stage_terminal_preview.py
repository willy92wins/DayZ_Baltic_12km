"""Stage exact parent archive content with only verified terminal terrain changes."""
from pathlib import Path
import ast,json,shutil,sys
import numpy as np
B=Path(__file__).parent;PARENT=Path('E:/DayZ-Baltic-Build/v30-global-contour-pass-20261009');B13=Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
sys.path.insert(0,str(B13));from discover_native_turns import W,sha
sys.path.insert(0,str(W/'tools/terrain'));from wrp0wzd import read,write
result=json.loads((B/'verification.json').read_text());assert result['status']=='PASS_GLOBAL_SOURCE'
terrain=B/'candidate/terrain.npz';assert sha(terrain)==result['candidate_sha256']
source=PARENT/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
assert sha(source/'baltic_trial.wrp')=='882e5b4fd0e4eb1122aabb27ac09b725246f699a3c39f20b0197c0fd5af828d2'
a=read(source/'baltic_trial.wrp');old=np.load(PARENT/'candidate-repaired/terrain.npz')['heights'];new=np.load(terrain)['heights'];assert np.array_equal(a['heights'],old[::-1])
target=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial';shutil.copytree(source,target,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
write(target/'baltic_trial.wrp',a['header'],new[::-1],a['materials'],[o['bytes'] for o in a['objects']],a['terminator'])
got=read(target/'baltic_trial.wrp');assert np.array_equal(got['heights'],new[::-1]) and [o['bytes'] for o in got['objects']]==[o['bytes'] for o in a['objects']]
assert all(a[k]==got[k] for k in ('header','materials','terminator'))
report=dict(status='TERMINAL_WORLD_STAGED',terrain_sha256=sha(terrain),world_source_sha256=sha(target/'baltic_trial.wrp'),old_world_source_sha256=sha(source/'baltic_trial.wrp'),water_sha256=sha(PARENT/'package/water/packed/baltic_water_v30.pbo'),objects_exact=True,objects=len(got['objects']),materials_exact=True,changed_vertices=int((old!=new).sum()))
(B/'stage.json').write_text(json.dumps(report,indent=2)+'\n')
receipts=[]
for name in ('compile_native_world.ps1','compile_exact_seams.ps1','author_exact_seams.py','verify_exact_seams.py','package_global_seams.py','deploy_global_preview.py'):
    text=(PARENT/name).read_text().replace(PARENT.as_posix(),B.as_posix()).replace(str(PARENT),str(B))
    text=text.replace("B/'candidate-repaired/terrain.npz'","B/'candidate/terrain.npz'")
    text=text.replace("B/'candidate-repaired-verification.json'","B/'verification.json'")
    text=text.replace("name=f'globalseam_{r:04}_{c:04}.p3d'","name=f'terminalseam_{r:04}_{c:04}.p3d'")
    text=text.replace("B13/'package/water/packed/baltic_water_v30.pbo'",f"Path(r'{PARENT.as_posix()}/package/water/packed/baltic_water_v30.pbo')")
    text=text.replace("B13/'package/world/out/narva_trial.pbo'",f"Path(r'{PARENT.as_posix()}/package/world/out/narva_trial.pbo')")
    text=text.replace('@DayZ_Baltic_GlobalContourV1','@DayZ_Baltic_TerminalContourV1')
    text=text.replace('53,853 terrain vertices and 96 extra seam instances; earlier preview retained.','478 terminal terrain vertices; exact extra seam count in package-seams.json; earlier preview retained.')
    if name.endswith('.py'):ast.parse(text)
    dest=B/name;assert not dest.exists();dest.write_text(text);receipts.append(dict(source=str(PARENT/name),source_sha256=sha(PARENT/name),copy=str(dest),copy_sha256=sha(dest)))
shutil.copyfile(PARENT/'audit_candidate_coverage.py',B/'audit_candidate_coverage.py')
(B/'package-consumer-reuse.json').write_text(json.dumps(receipts,indent=2)+'\n');print(json.dumps(report,indent=2))
