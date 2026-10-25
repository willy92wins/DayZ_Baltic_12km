"""B1: one correction. Solve contour, depth, dry margin and native face slope together."""
from pathlib import Path
import json,time
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import factorized
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
text=(B/'build_contour_valley.py').read_text().replace("out=B/'candidate-b'","out=B/'candidate-b1'")
text=text.replace('ids=np.flatnonzero(local);', "base[~local]=np.load(B/'candidate-a1/terrain_valley.npz')['heights'][~local]\nbase[fixed]=h[fixed]\nids=np.flatnonzero(local);")
scope={};exec(text[:text.index("print('SOLVE'")],scope)
for k in ('E','out','A','rhs','base','ids','lookup','n','h','lo','hi','cls','level','t','fixed','mask','zone','flip','sd','centre','planes','water','sha','source'):
 globals()[k]=scope[k]
# Every native triangle touching current land and a variable gets its full two-component slope bound.
gr=[];gc=[];gv=[];constants=[];radii=[];face_ids=[]
rr,cc=np.mgrid[:2047,:2047]
for dr,dc in ((0,1),(1,0)):
 a=(rr*n+cc).ravel();b=((rr+dr)*n+cc+dc).ravel();c=((rr+1)*n+cc+1).ravel()
 touch=(cls.ravel()[a]==0)|(cls.ravel()[b]==0)|(cls.ravel()[c]==0)
 m=touch&((lookup[a]>=0)|(lookup[b]>=0)|(lookup[c]>=0))
 for ia,ib,ic in zip(a[m],b[m],c[m]):
  i=len(radii);ga=h.ravel()[ib]-h.ravel()[ia];gb=h.ravel()[ic]-h.ravel()[ib]
  radii.append(max(np.hypot(ga,gb),6*np.tan(np.deg2rad(35))))
  face_ids.append((ia,ib,ic))
  for j,(i0,i1) in enumerate(((ia,ib),(ib,ic))):
   const=0.
   for ix,coeff in ((i0,-1.),(i1,1.)):
    col=lookup[ix]
    if col<0:const+=coeff*base.ravel()[ix]
    else:gr.append(2*i+j);gc.append(col);gv.append(coeff)
   constants.append(const)
G=sparse.csr_matrix((gv,(gr,gc)),shape=(len(constants),len(ids)))
c=np.array(constants);radii=np.array(radii);lower=lo.ravel()[ids];upper=hi.ravel()[ids]
AA=(A.T@A).tocsc();ab=A.T@np.array(rhs);M=(sparse.eye(len(ids))+G.T@G).tocsc()
x=np.clip(np.load(B/'candidate-b/terrain_valley.npz')['heights'].ravel()[ids].astype(float),lower,upper)
def project(g):
 a=g.reshape(-1,2);scale=np.minimum(1.,radii/np.maximum(np.linalg.norm(a,axis=1),1e-30))
 return (a*scale[:,None]).ravel()
zb=x.copy();zg=project(G@x+c);ub=np.zeros_like(x);ug=np.zeros_like(c)
rho=2.;solve=factorized(AA+rho*M);history=[];start=time.monotonic();converged=False
print('JOINT',len(ids),'variables',len(radii),'faces',flush=True)
for iteration in range(1,4097):
 x=solve(ab+rho*(zb-ub+G.T@(zg-ug-c)))
 gx=G@x+c;oldb=zb;oldg=zg
 zb=np.clip(x+ub,lower,upper);zg=project(gx+ug)
 ub+=x-zb;ug+=gx-zg
 primal=max(float(np.max(np.abs(x-zb))),float(np.max(np.abs(gx-zg))))
 dual=float(rho*np.max(np.abs(zb-oldb+G.T@(zg-oldg))))
 if iteration%100==0 or (primal<2e-6 and dual<2e-5):
  row=dict(iteration=iteration,primal=primal,dual=dual,rho=rho);history.append(row)
  print(json.dumps(row),flush=True)
 if primal<2e-6 and dual<2e-5:converged=True;break
 if iteration%100==0:
  updated=rho
  if primal>10*dual:updated=min(32.,rho*2)
  elif dual>10*primal:updated=max(.125,rho/2)
  if updated!=rho:
   ub*=rho/updated;ug*=rho/updated;rho=updated;solve=factorized(AA+rho*M)
got=base.copy();got.ravel()[ids]=np.clip(x,lower,upper)
np.savez_compressed(out/'terrain_valley.npz',**dict(t,heights=got.astype(t['heights'].dtype),cls=cls,level=level,water=cls>0))
np.savez_compressed(out/'masks.npz',**mask,edited_shore=zone,reclassified=flip,contour_sd=sd,centre=centre)
np.savez_compressed(out/'frozen_pond_planes.npz',planes=planes,visual_vertex_levels=water)
report=dict(status='JOINT_CONVERGED_PENDING_GATES' if converged else 'SOLVER_NOT_CONVERGED_NOT_ACCEPTABLE',method='ADMM constrained least squares; direct box projection and per-native-face gradient disc, no vertex reversion after class changes',converged=converged,iterations=iteration,history=history,seconds=time.monotonic()-start,variables=len(ids),faces=len(radii),source_sha256=sha(source),terrain_sha256=sha(out/'terrain_valley.npz'),limits=['Same B contour and depth bounds, one correction for post-reversion inconsistency.','Not accepted unless independent geometry and in-game consumers pass.'])
(E/'authoring-b1.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='history'},indent=2),flush=True)
