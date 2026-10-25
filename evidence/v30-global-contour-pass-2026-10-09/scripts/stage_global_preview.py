"""Stage the accepted global source over the exact EV13 world and prepare unchanged seam consumers."""
from pathlib import Path
import json,shutil,sys
import numpy as np

B=Path(__file__).parent
B13=Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
B12=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path.insert(0,str(B13))
from discover_native_turns import W,sha
sys.path.insert(0,str(W/'tools/terrain'))
from wrp0wzd import read,write

result=json.loads((B/'candidate-repaired-verification.json').read_text());assert result['status']=='PASS_GLOBAL_SOURCE'
terrain=B/'candidate-repaired/terrain.npz';assert sha(terrain)==result['candidate_sha256']
source=B13/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
assert sha(source/'baltic_trial.wrp')=='2e4370cdeb5de5294285d793344869aac37d75a82c405fe30d84852152b327fa'
a=read(source/'baltic_trial.wrp');old=np.load(B13/'candidate-feasible/terrain.npz')['heights'];new=np.load(terrain)['heights']
assert np.array_equal(a['heights'],old[::-1])
target=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
shutil.copytree(source,target,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
write(target/'baltic_trial.wrp',a['header'],new[::-1],a['materials'],[o['bytes'] for o in a['objects']],a['terminator'])
got=read(target/'baltic_trial.wrp')
assert np.array_equal(got['heights'],new[::-1]) and [o['bytes'] for o in got['objects']]==[o['bytes'] for o in a['objects']]
assert all(a[k]==got[k] for k in ('header','materials','terminator'))
report=dict(status='GLOBAL_CONTOUR_WORLD_STAGED',terrain_sha256=sha(terrain),world_source_sha256=sha(target/'baltic_trial.wrp'),
            old_world_source_sha256=sha(source/'baltic_trial.wrp'),water_sha256=sha(B13/'package/water/packed/baltic_water_v30.pbo'),
            objects_exact=True,objects=len(got['objects']),materials_exact=True,changed_vertices=int((old!=new).sum()))
(B/'stage.json').write_text(json.dumps(report,indent=2)+'\n')
receipts=[]
for name in ('compile_native_world.ps1','compile_exact_seams.ps1','author_exact_seams.py','verify_exact_seams.py'):
    text=(B13/name).read_text()
    text=text.replace(B13.as_posix(),B.as_posix()).replace(str(B13),str(B))
    text=text.replace("B/'candidate-feasible/terrain.npz'","B/'candidate-repaired/terrain.npz'")
    text=text.replace("B/'candidate-feasible-coverage.json'","B/'initial-coverage.json'")
    text=text.replace("name=f'nativeseam_{r:04}_{c:04}.p3d'","name=f'globalseam_{r:04}_{c:04}.p3d'")
    dest=B/name;assert not dest.exists();dest.write_text(text)
    receipts.append(dict(source=str(B13/name),source_sha256=sha(B13/name),copy=str(dest),copy_sha256=sha(dest)))
# Coverage is already parameterized. Keep exactly the same consumer bytes.
source_consumer=B13/'audit_candidate_coverage.py';shutil.copyfile(source_consumer,B/source_consumer.name)
receipts.append(dict(source=str(source_consumer),source_sha256=sha(source_consumer),copy_sha256=sha(B/source_consumer.name)))
(B/'consumer-reuse.json').write_text(json.dumps(dict(copies=receipts,changes='Only paths, terrain identity and unique model prefix. Geometry and thresholds unchanged.'),indent=2)+'\n')
print(json.dumps(report,indent=2))
