"""Separate sea-artifact controls with fixed waterline and engineering supports."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy import ndimage
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008');E=W/'evidence/v30-valley-smoothing-2026-10-08'
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import tri_sample,cell_planes
from finish_shores_v30 import discard_steeper_land_faces
from smooth_dry_relief_v30 import ease
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
label=sys.argv[1] if len(sys.argv)>1 else 'land160'
assert label in ('land160','land180')
target=1.6 if label=='land160' else 1.8
lift=target-1.4
source=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
assert sha(source)=='e0d35db0a7a26f9ec055d57f0c9573a1dd2c27911ec8b084274283f5884cffd1'
t=dict(np.load(source));h=t['heights'].astype(float);wet=t['cls']>0
# All four corners of every water-adjacent cell are exact: the native shoreline cannot move.
touch=wet[:-1,:-1]|wet[1:,:-1]|wet[:-1,1:]|wet[1:,1:]
fixed=t['reserve']|t['platform']|t['beach']|wet
for dr,dc in ((0,0),(0,1),(1,0),(1,1)):fixed[dr:dr+2047,dc:dc+2047]|=touch
fixed[:2]=True;fixed[-2:]=True;fixed[:,:2]=True;fixed[:,-2:]=True
weight=ease(ndimage.distance_transform_edt(~fixed,sampling=6.)/18.)
# C2 monotone remapping. Quintic ease has peak derivative 1.875; a width
# of at least twice the lift keeps the remapped height derivative positive.
width=max(.5,2*lift)
raised=h+lift*ease((1.4+width-h)/width)
raised=np.maximum(raised,np.minimum(target,h+lift))
candidate=h+weight*(raised-h);candidate[fixed]=h[fixed]
candidate,recovery=discard_steeper_land_faces(candidate,h,t['cls'])
out=B/f'candidate-{label}';out.mkdir(exist_ok=False)
np.savez_compressed(out/'terrain_valley.npz',**dict(t,heights=candidate.astype(t['heights'].dtype)))
np.savez_compressed(out/'masks.npz',fixed=fixed,weight=weight)
v=np.load(out/'terrain_valley.npz')['heights'].astype(float);changed=v!=h
points=[(2179.537858,7086.083408),(2281.835241,7203.550968),(2534.5868,7037.5396),(2210.061284,6866.549706)]
checks=dict(metadata_exact=True,all_water_cells_exact=not bool((changed&fixed).any()),only_raises=not bool((v<h).any()),max_raise_bounded=float((v-h).max())<=lift+.0001,finite=bool(np.isfinite(v).all()))
report=dict(status=label.upper()+'_BUILT_PENDING_GATES',target_m=target,checks=checks,changed_vertices=int(changed.sum()),max_raise=float((v-h).max()),recovery=recovery,source_sha256=sha(source),terrain_sha256=sha(out/'terrain_valley.npz'),R1_land_points=[dict(x=x,z=z,before=float(tri_sample(h,x,z)),after=float(tri_sample(v,x,z))) for x,z in points],limits=['The protected water/engineering ring and its 18 m transition can remain below the target.','This is a sea-artifact comparison, not the rejected valley/contour candidates.','Sea parameters and physical/visual water meshes remain identical.'])
(E/f'authoring-{label}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
