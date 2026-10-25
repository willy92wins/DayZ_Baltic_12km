"""Stage the accepted offline contour pilot over the exact global-water world."""
from pathlib import Path
import json,shutil,sys
import numpy as np
from discover_native_turns import B,B10,B12,W,sha
sys.path.insert(0,str(W/'tools/terrain'))
from wrp0wzd import read,write

verification=json.loads((B/'candidate-feasible-verification.json').read_text())
assert verification['status']=='PASS_SOURCE_TERRAIN'
source=B12/'final/world/root/dayz_baltic_12km_dev/tb/narva_trial'
assert sha(source/'baltic_trial.wrp')=='98b989631bd82588401076d5e54d465fd03acde30511fd3246b321988eed15d0'
terrain=B/'candidate-feasible/terrain.npz';assert sha(terrain)==verification['candidate_sha256']
old=np.load(B10/'measured-bank-bed-r2/terrain.npz')['heights'];new=np.load(terrain)['heights']
a=read(source/'baltic_trial.wrp');assert np.array_equal(a['heights'],old[::-1])
target=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
shutil.copytree(source,target,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
write(target/'baltic_trial.wrp',a['header'],new[::-1],a['materials'],[o['bytes'] for o in a['objects']],a['terminator'])
b=read(target/'baltic_trial.wrp')
assert np.array_equal(b['heights'],new[::-1]) and all(a[k]==b[k] for k in ('header','materials','terminator'))
assert [o['bytes'] for o in a['objects']]==[o['bytes'] for o in b['objects']]
script=(B12/'compile_final_world.ps1').read_text();oldroot="$buildRoot='E:\\DayZ-Baltic-Build\\v30-frozen-water-stitch-20261009\\final'"
assert script.count(oldroot)==1;script=script.replace(oldroot,"$buildRoot='E:\\DayZ-Baltic-Build\\v30-native-turn-optimizer-20261009\\package'")
script=script.replace('Built isolated halo correction world.','Built isolated native-contour world.')
(B/'compile_native_world.ps1').write_text(script)
report=dict(status='NATIVE_CONTOUR_WORLD_STAGED',terrain_sha256=sha(terrain),world_source_sha256=sha(target/'baltic_trial.wrp'),
            old_world_source_sha256=sha(source/'baltic_trial.wrp'),objects_exact=True,object_count=len(b['objects']),materials_exact=True,
            water_sha256=sha(B12/'final/water/packed/baltic_water_v30.pbo'),changed_vertices=int((old!=new).sum()),
            limits=['Coverage audit, compiled archive and engine remain separate.'])
(B/'stage.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
