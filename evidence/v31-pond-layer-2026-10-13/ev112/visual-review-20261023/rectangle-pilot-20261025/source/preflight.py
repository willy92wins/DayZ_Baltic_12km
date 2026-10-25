from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.ndimage import distance_transform_edt,gaussian_filter,label
from scipy.optimize import linprog
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water')]
import despike_v31 as D
import census_pyramids_v31 as P
from repair_guarded_shapes_ev112 import crown_bounds
p=R/'guarded-relief-batch-e-merged/terrain-buried.npz';z=np.load(p);a={k:z[k] for k in z.files};H=a['heights'].astype(float)
free=np.load(R/'guarded-relief-batch-e/domains.npz')['free'];old=np.load(R/'combined-merged/terrain-buried.npz')['heights']
residual=np.zeros_like(H);residual[1:-1,1:-1]=np.maximum(abs(H[1:-1,1:-1]-(H[:-2,1:-1]+H[2:,1:-1])/2),abs(H[1:-1,1:-1]-(H[1:-1,:-2]+H[1:-1,2:])/2))
labels,_=label(residual>.3,structure=np.ones((3,3)));ident=next(int(labels[r,c]) for r,c in np.argwhere(labels[906:911,484:490]>0)+[906,484]);component=labels==ident
coords=np.argwhere(component);r0,c0=coords.min(axis=0);r1,c1=coords.max(axis=0)+1
assert (r0,c0,r1,c1)==(906,484,911,490)
domain=distance_transform_edt(~component)<=4;use_full=domain&free
rr,cc=np.where(domain);sl=np.s_[rr.min()-4:rr.max()+5,cc.min()-4:cc.max()+5]
base=H[sl];use=use_full[sl];prior=gaussian_filter(H,2,mode='nearest')[sl]
floor=np.minimum(H,D.lower_floor(a,np.load(R/'guarded-relief-batch-e-merged/envelope.npy')))
lo=np.maximum(base-.75,floor[sl]);hi=base+.75
pk,pt,*_=P.prominence(H)
peaks=[(r,c,base[r,c]) for r,c in np.argwhere((pk[sl]>.3)&~free[sl])]
pits=[(r,c,base[r,c]) for r,c in np.argwhere((pt[sl]>.3)&~free[sl])]
crown_lo,crown_hi=crown_bounds(base,peaks,pits);lo=np.maximum(lo,crown_lo);hi=np.minimum(hi,crown_hi)
target=np.zeros_like(H,bool);target[r0:r1,c0:c1]=True
# Signed limits per axis. Outside the target, keep a pre-existing fault's
# signed extent but forbid an equally large fault with the opposite sign.
curvature=np.zeros((2,*base.shape))
curvature[0,1:-1,1:-1]=base[1:-1,1:-1]-(base[1:-1,:-2]+base[1:-1,2:])/2
curvature[1,1:-1,1:-1]=base[1:-1,1:-1]-(base[:-2,1:-1]+base[2:,1:-1])/2
curvature_lo=np.minimum(curvature,-.2999);curvature_hi=np.maximum(curvature,.2999)
curvature_lo[:,target[sl]]=-.2999;curvature_hi[:,target[sl]]=.2999
ids=np.full(base.shape,-1,int);ids[use]=np.arange(use.sum());rows=[];upper=[]
for r in range(1,len(base)-1):
    for c in range(1,base.shape[1]-1):
        for axis,(aa,bb) in enumerate([((r,c-1),(r,c+1)),((r-1,c),(r+1,c))]):
            terms=[((r,c),1.),(aa,-.5),(bb,-.5)];row=np.zeros(int(use.sum()));constant=0.
            for q,w in terms:
                if ids[q]>=0:row[ids[q]]+=w
                else:constant+=base[q]*w
            if row.any():
                rows.extend([row,-row]);upper.extend([curvature_hi[axis,r,c]-constant,constant-curvature_lo[axis,r,c]])
            elif not curvature_lo[axis,r,c]-1e-12<=constant<=curvature_hi[axis,r,c]+1e-12:
                raise ValueError('Fixed stencil cannot satisfy contract')
lp=linprog(np.zeros(int(use.sum())),A_ub=np.array(rows),b_ub=np.array(upper),bounds=list(zip(lo[use],hi[use])),method='highs')
out=R/'rectangle-pilot-preflight-c';out.mkdir(exist_ok=False)
np.savez_compressed(out/'fixture.npz',base=base,prior=prior,free=use,floor=lo,ceiling=hi,peak_cap=np.maximum(pk[sl],.2999),pit_cap=np.maximum(pt[sl],.2999),curvature_lower=curvature_lo,curvature_upper=curvature_hi,target=target[sl])
report=dict(status='EXACT_DOMAIN_LINEAR_FEASIBLE' if lp.success else 'EXACT_DOMAIN_LINEAR_INFEASIBLE',terrain_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256((out/'fixture.npz').read_bytes()).hexdigest(),slice=[[int(sl[0].start),int(sl[0].stop)],[int(sl[1].start),int(sl[1].stop)]],component_vertices=int(component.sum()),free_vertices=int(use.sum()),protected_extrema=dict(peaks=len(peaks),pits=len(pits)),previous_D_E_changes_in_domain=int(((H!=old)&domain).sum()),lp_message=lp.message,limits=['Necessary linear stencil feasibility only. Native prominence, slopes and creases not yet solved.','Read-only fixture; E and its deployed PBOs are unchanged.'])
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
