"""B: fit the true signed contour, allowing declared local shore reclassification."""
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
source=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
assert sha(source)=='e0d35db0a7a26f9ec055d57f0c9573a1dd2c27911ec8b084274283f5884cffd1'
out=B/'candidate-b';out.mkdir(exist_ok=False)
t=dict(np.load(source));h=t['heights'].astype(float);ha=np.load(B/'candidate-a/terrain_valley.npz')['heights'].astype(float)
mask=dict(np.load(B/'candidate-a/masks.npz'));fixed=mask['fixed'].copy()
design=np.load(B/'contour-design.npz');sd=design['sd'];core=design['core'];interior=design['interior']
oldwet=t['cls']>0;edge=ndimage.binary_dilation(oldwet)&ndimage.binary_dilation(~oldwet)
planes=cell_planes(t['cls'],t['level']);pmin,pmax=vertex_plane_bounds(planes)
water=np.load('E:/DayZ-Baltic-Build/v30-water-visual-fix-20261008/stitched-water/visual_vertex_levels.npy')
# Historical shallow controls keep all native supporting vertices, not just the sampled point.
ref=json.loads((W/'evidence/v30-water-visual-fix-2026-10-08/stitch-probe-reference.json').read_text())
shallow=[]
for p in ref['points']:
 if p['role']!='frozen_shallow_failure':continue
 r=int(np.floor((12282-p['z'])/6));c=int(np.floor(p['x']/6));fixed[r:r+2,c:c+2]=True;shallow.append(p['id'])
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
hi[centre]=np.minimum(hi[centre],h[centre])
landfloor=np.fmax(1.4,np.fmax(pmax+.0501,water+.0501))
landfloor=np.where(oldwet,landfloor,np.minimum(h,landfloor))
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
print('SOLVE',A.shape,flush=True);start=time.monotonic()
fit=lsq_linear(A,np.array(rhs),bounds=(lo.ravel()[ids],hi.ravel()[ids]),tol=1e-8,lsmr_tol=1e-8,max_iter=160)
assert fit.success,fit.message
got=base.copy();got.ravel()[ids]=fit.x;got[fixed]=h[fixed]
got,recovery=discard_steeper_land_faces(got,h,cls)
assert not np.any((got!=h)&fixed)
np.savez_compressed(out/'terrain_valley.npz',**dict(t,heights=got.astype(t['heights'].dtype),cls=cls,level=level,water=cls>0))
np.savez_compressed(out/'masks.npz',**mask,edited_shore=zone,reclassified=flip,contour_sd=sd,centre=centre)
np.savez_compressed(out/'frozen_pond_planes.npz',planes=planes,visual_vertex_levels=water)
x,z=grid_xz();rc=np.argwhere(flip)
changes=[dict(row=int(r),col=int(c),x=float(x[r,c]),z=float(z[r,c]),before_class=int(t['cls'][r,c]),after_class=int(cls[r,c]),before_h=float(h[r,c]),after_h=float(got[r,c])) for r,c in rc]
report=dict(status='B_BUILT_PENDING_CONSUMER_GATES',iterations=fit.nit,variables=len(ids),crossing_rows=crossrows,seconds=time.monotonic()-start,recovery=recovery,source_sha256=sha(source),terrain_sha256=sha(out/'terrain_valley.npz'),frozen_pond_planes_sha256=sha(out/'frozen_pond_planes.npz'),shallow_controls_fixed=shallow,depth_prevents_new_wet=int(impossible.sum()),reclassification=changes,limits=['Local contour redesign; frozen physical pond surface is an explicit input, not recomputed from vertex classification.','No global shore acceptance; road and navigation gates still required.'])
(E/'authoring-b.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('reclassification','limits')},indent=2),flush=True)
