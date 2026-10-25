from pathlib import Path
import sys,json,hashlib,shutil
import numpy as np
B=Path(__file__).parent;R=B.parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
OLD=R/'v30-remaining-exact-dry-support-20261009'
sys.path.insert(0,str(W/'tools/terrain'))
from wrp0wzd import read,write
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
check=json.loads((B/'review-luna/report.json').read_text())
assert check['status']=='PASS_EV79_CONSUMER' and all(check['gates'].values())
assert json.loads((B/'compiled-exposure.json').read_text())['status']=='PASS_COMPILED_EXPOSURE'
assert sha(B/'candidate/terrain.npz')==check['candidate_sha256']
src=OLD/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
dst=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
assert sha(src/'baltic_trial.wrp')=='d89b92af86f3b376e50b2b0d107a94dd94a380f966ca9c666ba9fbc8d95f88d7'
a=read(src/'baltic_trial.wrp');source=np.load(OLD/'candidate/terrain.npz')['heights'];h=np.load(B/'candidate/terrain.npz')['heights']
assert np.array_equal(a['heights'],source[::-1])
shutil.copytree(src,dst,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
write(dst/'baltic_trial.wrp',a['header'],h[::-1],a['materials'],[o['bytes'] for o in a['objects']],a['terminator'])
c=read(dst/'baltic_trial.wrp');assert np.array_equal(c['heights'],h[::-1])
assert len(c['objects'])==len(a['objects'])==18033
assert all(a[k]==c[k] for k in ('header','materials','terminator'))
assert [o['bytes'] for o in a['objects']]==[o['bytes'] for o in c['objects']]
script=(OLD/'compile_native_world.ps1').read_text().replace(str(OLD).replace('/','\\'),str(B).replace('/','\\'))
(B/'compile_native_world.ps1').write_text(script)
report=dict(status='STAGED_EV79_HEIGHTS_ONLY',source_wrp_sha256=sha(src/'baltic_trial.wrp'),staged_wrp_sha256=sha(dst/'baltic_trial.wrp'),terrain_sha256=sha(B/'candidate/terrain.npz'),objects=18033,objects_and_materials_exact=True)
(B/'stage.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
