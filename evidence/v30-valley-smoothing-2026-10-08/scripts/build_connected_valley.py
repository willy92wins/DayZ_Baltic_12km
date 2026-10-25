"""C: connected native sign field, joint contour and slope constraints; LAND180 source."""
from pathlib import Path
import json,sys,hashlib,time
import numpy as np
from scipy import ndimage,sparse
from scipy.optimize import lsq_linear
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008');E=W/'evidence/v30-valley-smoothing-2026-10-08'
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import cell_planes,vertex_plane_bounds,grid_xz
from smooth_dry_relief_v30 import ease
from finish_shores_v30 import discard_steeper_land_faces
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=B/'candidate-land180/terrain_valley.npz'
assert sha(source)=='88914948a3a9a3017b3195642657f0fd4c271475f3dccc1ae751b1f5deb045d1'
out=B/'candidate-c';out.mkdir(exist_ok=False)
t=dict(np.load(source));h=t['heights'].astype(float);ha=np.load(B/'candidate-a/terrain_valley.npz')['heights'].astype(float)
mask=dict(np.load(B/'candidate-a/masks.npz'));fixed=mask['fixed'].copy()
design=np.load(B/'contour-design-c.npz');sd=design['sd'];core=design['core'];interior=design['interior']
oldwet=t['cls']>0;edge=ndimage.binary_dilation(oldwet)&ndimage.binary_dilation(~oldwet)
planes=cell_planes(t['cls'],t['level']);pmin,pmax=vertex_plane_bounds(planes)
water=np.load('E:/DayZ-Baltic-Build/v30-water-visual-fix-20261008/stitched-water/visual_vertex_levels.npy')
# Historical shallow controls keep all native supporting vertices, not just the sampled point.
ref=json.loads((W/'evidence/v30-water-visual-fix-2026-10-08/stitch-probe-reference.json').read_text())
shallow=[]
for p in ref['points']:
 if p['role']!='frozen_shallow_failure':continue
 r=int(np.floor((12282-p['z'])/6));c=int(np.floor(p['x']/6));fixed[r:r+2,c:c+2]=True;shallow.append(p['id'])
historical=json.loads((W/'evidence/v30-bug-recheck-2026-10-08/wave-fixed-reference.json').read_text())
for p in historical['points']:
 r=int(np.floor((12282-p['z'])/6));c=int(np.floor(p['x']/6));fixed[r:r+2,c:c+2]=True
zone=core&interior&~fixed
cls=t['cls'].copy();level=t['level'].copy()
_,nearest=ndimage.distance_transform_edt(~oldwet,return_indices=True)
newwet=np.where(zone,sd<0,oldwet)
nominal=np.where(oldwet,t['level'],t['level'][tuple(nearest)])
cap=np.fmin(np.fmin(pmin-.101,water-.101),nominal-.101)
# A new submerged vertex cannot create a new exception below the agreed 1 m floor.
impossible=zone&newwet&~oldwet&(cap<1.)
newwet[impossible]=False
flip=zone&(oldwet!=newwet)
cls[flip&~newwet]=0;level[flip&~newwet]=np.nan
gain=flip&newwet;cls[gain]=t['cls'][tuple(nearest[:,gain])];level[gain]=nominal[gain]
mask['fixed']=fixed
# Dry valley changes from A are useful; its old shoreline regression is excluded outside this pilot.
base=h+ease(ndimage.distance_transform_edt(~edge,sampling=6.)/24.)*(ha-h)
base[zone]=ha[zone];base[fixed]=h[fixed]
halo=(ndimage.distance_transform_edt(~zone,sampling=6.)<=48)&~fixed
local=(zone|halo)&~fixed
# Fixed centre of the existing watercourse, allowing only the peripheral bank profile to move up.
centre=zone&newwet&(sd<=-6.)
lo=h-2.;hi=h+2.
lo[newwet]=np.maximum(lo[newwet],np.minimum(h[newwet],1.))
lo[gain]=np.maximum(lo[gain],1.)
hi[newwet]=np.minimum(h[newwet]+6.,np.fmax(np.where(oldwet,h,-np.inf),cap)[newwet])
rails=design['flow_rails']
hi[centre|rails]=np.minimum(hi[centre|rails],h[centre|rails])
landfloor=np.fmax(1.4,np.fmax(pmax+.0501,water+.0501))
landfloor=np.where(oldwet,landfloor,np.minimum(h,landfloor))
landfloor=np.maximum(landfloor,np.minimum(h,1.8))
lo[~newwet]=np.maximum(lo[~newwet],landfloor[~newwet])
hi[flip&~newwet]=h[flip&~newwet]+6.
# Outside the local wet footprint, retain A's conservative no-raising-water condition.
hi[oldwet&~zone]=h[oldwet&~zone]
# Keep old first shoreline ring exactly where the visible stitched domain ends.
boundary=edge&~zone
local[boundary]=False;base[boundary]=h[boundary]
bad=local&(hi<lo)
assert not bad.any(),('infeasible height intervals',int(bad.sum()))
local&=(hi-lo>1e-6)
outside=np.load(B/'candidate-a1/terrain_valley.npz')['heights'].astype(float)
outside=np.where(t['cls']==0,np.maximum(outside,np.minimum(h,1.8)),outside)
base[~local]=outside[~local];base[fixed]=h[fixed]
ids=np.flatnonzero(local);n=2048;lookup=np.full(h.size,-1,int);lookup[ids]=np.arange(len(ids))
rows=[];cols=[];values=[];rhs=[]
def add(indices,coeff,value,weight):
 row=len(rhs)
 for i,c in zip(indices,coeff):
  j=lookup[i]
  if j<0:value-=c*base.ravel()[i]
  else:rows.append(row);cols.append(j);values.append(c*weight)
 rhs.append(value*weight)
cross=[]
for dr,dc in ((0,1),(1,0),(1,1)):
 rr,cc=np.mgrid[:n-dr,:n-dc];rb,cb=rr+dr,cc+dc
 m=core[rr,cc]&core[rb,cb]&(newwet[rr,cc]^newwet[rb,cb])&(zone[rr,cc]|zone[rb,cb])
 for ra,ca,rbb,cbb in zip(rr[m],cc[m],rb[m],cb[m]):
  a,b=ra*n+ca,rbb*n+cbb
  da,db=sd[ra,ca],sd[rbb,cbb]
  if da*db>=0:continue  # fixed engineering/depth corner that cannot follow the geometric target
  tau=abs(da)/(abs(da)+abs(db));y=(1-tau)*water[ra,ca]+tau*water[rbb,cbb]
  add([a,b],[1-tau,tau],y,10.);cross.append((a,b,tau,y))
crossrows=len(rhs)
for i in ids:
 add([i],[1.],ha.ravel()[i],.08)
 add([i,i-1,i+1,i-n,i+n],[1,-.25,-.25,-.25,-.25],0,.35)
A=sparse.csr_matrix((values,(rows,cols)),shape=(len(rhs),len(ids)))

from scipy.sparse.linalg import factorized
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
x=np.clip(base.ravel()[ids].astype(float),lower,upper)
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
report=dict(status='JOINT_CONVERGED_PENDING_GATES' if converged else 'SOLVER_NOT_CONVERGED_NOT_ACCEPTABLE',method='ADMM constrained least squares; direct box projection and per-native-face gradient disc, no vertex reversion after class changes',converged=converged,iterations=iteration,history=history,seconds=time.monotonic()-start,variables=len(ids),faces=len(radii),source_sha256=sha(source),terrain_sha256=sha(out/'terrain_valley.npz'),limits=['Connected native C field and no-raising flow rails; independent topology and shape gates required.','Not accepted unless independent geometry and in-game consumers pass.'])
(E/'authoring-c.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='history'},indent=2),flush=True)
