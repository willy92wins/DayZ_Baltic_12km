"""Read-only scalar feasibility of a hinge with three fixed vertices."""
from pathlib import Path
import json,sys
import numpy as np
from scipy.optimize import minimize_scalar

B=Path(__file__).parent;R=B.parent;OLD=R/'v30-volkhov-wet-support-20261009'
sys.path[:0]=[str(R/'v30-native-hinge-finish-20261009'),str(R/'v30-surface-crease-audit-20261009')]
from verify_hinges import face_normals,edges
from audit_native_surface import incident_any
h=np.load(R/'v30-strict-dry-composition-20261009/candidate/terrain.npz')['heights'].astype(float);v=np.load(OLD/'candidate/terrain.npz')['heights'].astype(float);d=np.load(OLD/'domain.npz');free=d['allowed']&~d['core']&~d['fixed'];rows=[]
specs={'diagonal':([(0,0),(0,1),(1,0),(1,1)],[0,1,3],[0,2,3]),'vertical':([(0,0),(0,1),(1,1),(1,2)],[0,1,2],[1,2,3]),'horizontal':([(0,0),(1,0),(1,1),(2,1)],[0,1,2],[1,2,3])}
original=dict(edges(*face_normals(h)));after=dict(edges(*face_normals(v)))
for kind,(offsets,ta,tb) in specs.items():
    rr,cc=np.nonzero(incident_any(free,kind)&(after[kind]>np.maximum(original[kind],10)+1e-7))
    xz=np.array([[c*6,-r*6] for r,c in offsets]);ms=[]
    for tri in [ta,tb]:
        coeff=np.linalg.inv(np.column_stack([xz[tri],np.ones(3)]));m=np.zeros((3,4));m[0,tri]=-coeff[0];m[2,tri]=-coeff[1];ms.append(m)
    for r,c in zip(rr,cc):
        coords=[(r+dr,c+dc) for dr,dc in offsets];var=[i for i,rc in enumerate(coords) if free[rc]]
        if len(var)!=1:continue
        j=var[0];vals=np.array([v[rc] for rc in coords]);lo=h[coords[j]];hi=lo+.425
        def angle(x):
            q=vals.copy();q[j]=x;na=ms[0]@q;nb=ms[1]@q;na[1]=nb[1]=1
            return float(np.degrees(np.arctan2(np.linalg.norm(np.cross(na,nb)),na@nb)))
        opt=minimize_scalar(angle,bounds=(lo,hi),method='bounded',options=dict(xatol=1e-13));minimum=min(angle(lo),angle(hi),float(opt.fun));limit=float(min(original[kind][r,c]+2,max(original[kind][r,c],10)))
        rows.append(dict(kind=kind,row=int(r),col=int(c),before=float(original[kind][r,c]),minimum=minimum,limit=limit,unavoidable_excess=minimum-limit,optimizer_success=bool(opt.success)))
bad=[x for x in rows if x['unavoidable_excess']>1e-9]
report=dict(status='READ_ONLY_SINGLE_FREE_HINGE_FEASIBILITY',single_free_checked=len(rows),strict_infeasible=len(bad),exceeds_existing_consumer_tolerance=sum(x['unavoidable_excess']>1e-4 for x in rows),maximum_unavoidable_excess=max(x['unavoidable_excess'] for x in rows),strict_failures=bad,limits=['Scalar minimum plus endpoints for the fixed surrounding values, not proof about changing all neighbours.','Does not change solver tolerances or author another terrain.'])
(B/'float-feasibility.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='strict_failures'},indent=2));print(json.dumps(sorted(bad,key=lambda x:-x['unavoidable_excess'])[:5],indent=2))
