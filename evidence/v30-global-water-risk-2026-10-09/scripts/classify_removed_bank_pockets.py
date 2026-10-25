"""Classify disappearing components from BEFORE data, without exempting intended water."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-global-water-risk-2026-10-09'
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import cell_planes
from audit_pond_topology import domain
t=dict(np.load('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008/candidate-c1r3p/terrain_valley.npz'))
w=np.load('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
plane=cell_planes(w['cls'],w['level']);a=domain(t['heights'],plane)
rr,cc=a['cells'];faces=np.stack([np.stack([rr*2048+cc,rr*2048+cc+1,(rr+1)*2048+cc+1],1),np.stack([rr*2048+cc,(rr+1)*2048+cc,(rr+1)*2048+cc+1],1)],1).reshape(-1,3)
levels=np.repeat(plane[rr,cc],2)
r1=json.loads((E/'measured-bank-bed-verification.json').read_text())
declared={p['row']*2048+p['col'] for p in r1['changes'] if p['kind']=='flooded_dry_bank'}
rows=[]
for f in r1['topology']['failed_components']:
    idx=np.flatnonzero(a['labels']==f['component']);ids=faces[idx]
    wet=t['heights'].ravel()[ids]<levels[idx,None]-1e-7
    submerged=np.unique(ids[wet]);allids=np.unique(ids)
    rows.append(dict(**f,triangles=len(idx),bounds=[int(allids.min()%2048)*6,int(12282-(allids.max()//2048)*6),int((allids%2048).max())*6,int(12282-(allids.min()//2048)*6)],
        submerged_vertices=[dict(row=int(i//2048),col=int(i%2048),cls=int(t['cls'].ravel()[i]),height=float(t['heights'].ravel()[i]),declared=int(i) in declared) for i in submerged],
        all_submerged_vertices_declared=all(int(i) in declared for i in submerged),
        no_submerged_source_water_vertices=bool((t['cls'].ravel()[submerged]==0).all()),
        no_engineering_support=not bool((t['reserve']|t['platform']|t['beach']).ravel()[allids].any())))
out=dict(status='CLASSIFIED_BEFORE_DATA_NOT_ACCEPTANCE',components=rows,
    limits=['A dry class alone is not an exemption. Only entire isolated pockets with every submerged vertex in the predeclared native flooding set qualify for proposed removal.','Retain the original failing test result. An explicit corrected product gate is still required.'])
(E/'removed-bank-pocket-classification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
