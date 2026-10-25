"""Integrate the passing C1 R3 slice and dry relief; restore R1/R2 to LAND180 exactly."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from scipy.ndimage import distance_transform_edt
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008');E=W/'evidence/v30-valley-smoothing-2026-10-08'
sys.path.insert(0,str(W/'tools/terrain'))
from smooth_dry_relief_v30 import ease
from v30_common import grid_xz
slice_label=sys.argv[1] if len(sys.argv)>1 else 'c1'
assert slice_label in ('c1','c1physical')
label='c1r3' if slice_label=='c1' else 'c1r3p'
source=B/'candidate-land180/terrain_valley.npz';slice_source=B/f'candidate-{slice_label}/terrain_valley.npz'
t=dict(np.load(source));c=dict(np.load(slice_source));m=dict(np.load(B/f'candidate-{slice_label}/masks.npz'))
h=t['heights'].astype(float);v=c['heights'].astype(float);x,z=grid_xz()
core=np.load(B/'contour-design.npz')['core']
restore=core&((x<5000)|(x>7900))
distance=distance_transform_edt(~restore,sampling=6.)
weight=ease((distance-24.)/60.)
got=(h+weight*(v-h)).astype(t['heights'].dtype)
R3=core&(x>7000)&(x<7600)
assert np.array_equal(got[R3],c['heights'][R3])
assert np.array_equal(got[distance<=24],t['heights'][distance<=24])
new=dict(t,heights=got)
for key in ('cls','level','water'):new[key]=np.where(R3,c[key],t[key])
m['edited_shore']&=R3;m['reclassified']=(new['cls']!=t['cls'])
m['fixed']|=distance<=24
out=B/f'candidate-{label}';out.mkdir(exist_ok=False)
np.savez_compressed(out/'terrain_valley.npz',**new);np.savez_compressed(out/'masks.npz',**m)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(status='SCOPED_INTEGRATION_PENDING_GATES',method='No new smoothing solve. Exact C1 R3 heights; LAND180 exact on R1/R2 water supports plus 24 m, 60 m quintic transition in dry relief.',source_sha256=sha(source),C1_sha256=sha(slice_source),terrain_sha256=sha(out/'terrain_valley.npz'),changed_vertices=int((got!=t['heights']).sum()),R3_exact=True,R1_R2_restored=True,limits=['Only R3 shore/channel shape is proposed for engine review. R1/R2 remain at the previous geometry and are not fixed by this integration.','C/C1 global FAIL status is retained. Dry relief still needs its independent curvature and slope gates.'])
(E/f'authoring-{label}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
