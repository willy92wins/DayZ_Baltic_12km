from pathlib import Path
import sys,json
import numpy as np
B=Path(__file__).parent;R=B.parent;S=R/'v30-strict-dry-composition-20261009/candidate'
sys.path[:0]=[str(R/'v30-native-hinge-finish-20261009'),str(R/'v30-surface-crease-audit-20261009')]
from verify_hinges import face_normals,edges
from audit_native_surface import incident_all,incident_any
t=np.load(S/'terrain.npz');h=t['heights'].astype(float);v=np.load(B/'candidate/terrain.npz')['heights'].astype(float);d=np.load(B/'domain.npz');u=v-h;rows=[]
offsets={'diagonal':[(0,0),(0,1),(1,0),(1,1)],'vertical':[(0,0),(0,1),(1,1),(1,2)],'horizontal':[(0,0),(1,0),(1,1),(2,1)]}
for (kind,a),(_,b) in zip(edges(*face_normals(h)),edges(*face_normals(v))):
    mask=incident_any(d['allowed'],kind)&~incident_all(d['core'],kind);error=np.where(mask,b-a,-np.inf);indices=np.argpartition(error.ravel(),-5)[-5:]
    for ix in indices:
        r,c=np.unravel_index(ix,error.shape);verts=[]
        for dr,dc in offsets[kind]:
            rr,cc=r+dr,c+dc;verts.append(dict(row=int(rr),col=int(cc),before=float(h[rr,cc]),uplift=float(u[rr,cc]),core=bool(d['core'][rr,cc]),fixed=bool(d['fixed'][rr,cc]),engineering=bool(t['reserve'][rr,cc]|t['platform'][rr,cc]),beach=bool(t['beach'][rr,cc])))
        rows.append(dict(kind=kind,row=int(r),col=int(c),before=float(a[r,c]),after=float(b[r,c]),increment=float(error[r,c]),vertices=verts))
rows.sort(key=lambda x:-x['increment']);report=dict(status='READ_ONLY_APRON_DIAGNOSIS',worst=rows,mechanism_to_test='Quintic distance weights are reset abruptly to zero at other fixed supports; a boundary-aware variational displacement can remove that forced truncation without changing levels or radius.')
(B/'apron-diagnosis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows[:3],indent=2))
