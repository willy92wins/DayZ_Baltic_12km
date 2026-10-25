"""One bounded correction: existing R3 stream beds need the restored lower plane.

The nature mask froze these beds in the initial shore pass. Preserve all dry
nature vertices and the design perimeter, but apply the authorized water work
inside R3 only. Keep a 0.201 m nominal bed clearance, the existing shallow repair
target; this is not proof of a maximum wave envelope.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008');E=W/'evidence/v30-curved-channel-pilot-2026-10-08'
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import cell_planes,vertex_plane_bounds
from finish_shores_v30 import discard_steeper_land_faces
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=B/'flat-profile/terrain_flat.npz';t=dict(np.load(source));h=t['heights'].astype(float)
base=np.load('E:/DayZ-Baltic-Build/v30-navigation-contract-20261008/terrain_floor.npz')['heights'].astype(float)
axes=json.loads(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/axes.json').read_text())
core=np.zeros(h.shape,bool)
for r,c in axes['R3']['removed_cells']:core[r:r+2,c:c+2]=True
m=dict(np.load(B/'flat-profile/masks.npz'))
nature=np.load(W.parents[2]/'tests/regional_outline_v1/reference.npz')['reserve'].astype(bool)
eligible=core&(t['cls']==6)&nature&~(t['reserve']|t['platform']|m['corridor'])
pmin,_=vertex_plane_bounds(cell_planes(t['cls'],t['level']))
need=eligible&np.isfinite(pmin)&(h>pmin-.201)
candidate=h.copy();candidate[need]=np.maximum(1.,pmin[need]-.201)
candidate,recovery=discard_steeper_land_faces(candidate,base,t['cls'])
delta=candidate-h;changed=delta!=0
diagnostic=dict(status='BED_ONLY_DIAGNOSTIC',requested_vertices=int(need.sum()),applied_vertices=int(changed.sum()),
                face_recovery=recovery,remaining=[dict(row=int(r),col=int(c),old=float(h[r,c]),after=float(candidate[r,c]),pmin=float(pmin[r,c]))
                for r,c in zip(*np.nonzero(need&(candidate>pmin-.2)))])
(E/'flat-bed-only-diagnostic.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
print(json.dumps(diagnostic,indent=2),flush=True)
assert not np.any(changed&~need) and not np.any(changed&(t['cls']==0))
assert not np.any(candidate[need]>pmin[need]-.2)
assert not np.any(candidate[(t['cls']>0)&(base>=1)]<1)
out=B/'flat-profile-r2';out.mkdir()
np.savez_compressed(out/'terrain_flat.npz',**dict(t,heights=candidate.astype(t['heights'].dtype)))
m['allowed']|=eligible;m['frozen']&=~eligible
np.savez_compressed(out/'masks.npz',**m)
report=dict(status='R3_BED_CORRECTION_PENDING_GATES',source=str(source),source_sha256=sha(source),
            output=str(out/'terrain_flat.npz'),output_sha256=sha(out/'terrain_flat.npz'),
            changed_vertices=int(changed.sum()),total_changed_vertices=int((candidate!=base).sum()),
            lowering_max_m=float(-delta.min()),nature_dry_exact=True,metadata_exact=True,
            road_platform_corridor_exact=True,face_recovery=recovery,
            changes=[dict(row=int(r),col=int(c),old=float(h[r,c]),new=float(candidate[r,c]),lower_plane=float(pmin[r,c])) for r,c in zip(*np.nonzero(changed))])
(E/'flat-bed-correction.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='changes'},indent=2))
