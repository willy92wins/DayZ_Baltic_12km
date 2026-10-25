"""One bounded correction: solve the waterline and valley together on patched ponds."""
from pathlib import Path
import json,sys,hashlib,time
import numpy as np,shapely
from scipy import ndimage,sparse
from scipy.optimize import lsq_linear
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008');E=W/'evidence/v30-valley-smoothing-2026-10-08'
sys.path[:0]=[str(W/'tools/terrain')]
from v30_common import cell_planes,vertex_plane_bounds,grid_xz
from smooth_dry_relief_v30 import ease
from smooth_shore_outline_v30 import smooth_line
from finish_shores_v30 import discard_steeper_land_faces
# Import only pure diagnostic functions, not an import-time run.
text=(B/'measure_waterline.py').read_text();namespace={}
exec(text[:text.index("label=sys.argv")],namespace)
lines_for=namespace['lines_for']
source=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
t=dict(np.load(source));h=t['heights'].astype(float);ha=np.load(B/'candidate-a/terrain_valley.npz')['heights'].astype(float)
mask=np.load(B/'candidate-a/masks.npz');fixed=mask['fixed'];cls=t['cls'];wet=cls>0;dry=cls==0
x,z=grid_xz();n=2048
plane=cell_planes(cls,t['level']);pmin,pmax=vertex_plane_bounds(plane)
water=np.load('E:/DayZ-Baltic-Build/v30-water-visual-fix-20261008/stitched-water/visual_vertex_levels.npy')
edge=ndimage.binary_dilation(wet)&ndimage.binary_dilation(dry)
transition=ease(ndimage.distance_transform_edt(~edge,sampling=6.)/24.)
# Do not create new shoreline regressions outside the already continuous-water pilot.
base=h+transition*(ha-h)
tiles=json.loads((W/'evidence/v30-curved-channel-pilot-2026-10-08/flat-water-authoring.json').read_text())['affected_tiles']
patched=np.zeros((2047,2047),bool)
for tx,tz in tiles:
 r0=max(0,int((12282-(tz+1)*48)/6));r1=min(2047,int((12282-tz*48)/6))
 c0=max(0,tx*8);c1=min(2047,(tx+1)*8)
 patched[r0:r1,c0:c1]|=np.isfinite(plane[r0:r1,c0:c1])
# Full four-cell support stays away from unmodified horizontal models at patch perimeter.
core=np.zeros((2048,2048),bool)
for dr,dc in ((0,0),(0,1),(1,0),(1,1)):core[dr:dr+2047,dc:dc+2047]|=patched
cells=list(zip(*np.nonzero(patched)))
native=lines_for(h,cells)
smoothed=[smooth_line(np.array(g.coords),lambda p:np.full(len(p),18.),4.) for g in native]
segs=np.concatenate([np.stack([g[:-1],g[1:]],axis=1) for g in smoothed])
tree=shapely.STRtree(shapely.linestrings(segs))
local=ndimage.binary_erosion(core,iterations=1)&(ndimage.distance_transform_edt(~edge,sampling=6.)<=24)&~fixed
rw,cw=np.nonzero(core)
_,d=tree.query_nearest(shapely.points(x[rw,cw],z[rw,cw]),return_distance=True,all_matches=False)
sd=np.full(h.shape,np.nan);sd[rw,cw]=np.where(wet[rw,cw],-np.maximum(d,.02),np.maximum(d,.02))
ew=[];el=[];et=[];lv=[]
for dr,dc in ((0,1),(1,0),(1,1)):
 rr,cc=np.mgrid[:n-dr,:n-dc];rb,cb=rr+dr,cc+dc
 valid=core[rr,cc]&core[rb,cb]&(wet[rr,cc]^wet[rb,cb])
 rr,cc,rb,cb=rr[valid],cc[valid],rb[valid],cb[valid]
 wa=wet[rr,cc];ar,ac=np.where(wa,rr,rb),np.where(wa,cc,cb);br,bc=np.where(wa,rb,rr),np.where(wa,cb,cc)
 tau=-sd[ar,ac]/(sd[br,bc]-sd[ar,ac])
 ew.extend((ar*n+ac).tolist());el.extend((br*n+bc).tolist());et.extend(tau.tolist())
 lv.extend(((1-tau)*water[ar,ac]+tau*water[br,bc]).tolist())
ew=np.array(ew);el=np.array(el);et=np.array(et);lv=np.array(lv)
lo=h-2.;hi=h+2.
lo[wet]=np.maximum(lo[wet],np.minimum(h[wet],1.));hi[wet]=h[wet]
dryfloor=np.fmax(np.minimum(h,1.4),np.minimum(h,pmax+.0501))
lo[dry]=np.maximum(lo[dry],dryfloor[dry])
local &= hi-lo>1e-6
ids=np.flatnonzero(local);lookup=np.full(n*n,-1,int);lookup[ids]=np.arange(len(ids))
rows=[];cols=[];data=[];rhs=[]
def equation(indices,coeff,value,weight):
 row=len(rhs);adjusted=value
 for i,c in zip(indices,coeff):
  col=lookup[i]
  if col<0:adjusted-=c*base.ravel()[i]
  else:rows.append(row);cols.append(col);data.append(c*weight)
 rhs.append(adjusted*weight)
for a,b,tau,y in zip(ew,el,et,lv):
 if lookup[a]>=0 or lookup[b]>=0:equation([a,b],[1-tau,tau],y,4.)
crossing_rows=len(rhs)
for i in ids:
 equation([i],[1],ha.ravel()[i],.08)
 equation([i,i-1,i+1,i-n,i+n],[1,-.25,-.25,-.25,-.25],0,.35)
A=sparse.csr_matrix((data,(rows,cols)),shape=(len(rhs),len(ids)))
print('SOLVE',A.shape,flush=True);start=time.monotonic()
sol=lsq_linear(A,np.array(rhs),bounds=(lo.ravel()[ids],hi.ravel()[ids]),method='trf',lsmr_tol=1e-8,max_iter=160,verbose=0)
assert sol.success,sol.message
candidate=base.copy();candidate.ravel()[ids]=sol.x
candidate[fixed]=h[fixed]
candidate,recovery=discard_steeper_land_faces(candidate,h,cls)
out=B/'candidate-a1';out.mkdir(exist_ok=False)
np.savez_compressed(out/'terrain_valley.npz',**dict(t,heights=candidate.astype(t['heights'].dtype)))
np.savez_compressed(out/'masks.npz',**dict(mask),line_variables=local)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
res=(1-et)*(candidate-water).ravel()[ew]+et*(candidate-water).ravel()[el]
report=dict(status='BUILT_SINGLE_CORRECTION_PENDING_GATES',method='Native visible shore smoothed in arc length 18m with 4m displacement bound; shared bounded least-squares plus curvature, frozen physics/engineering constraints',variables=len(ids),crossing_rows=crossing_rows,iterations=sol.nit,solver_success=bool(sol.success),cost=sol.cost,crossing_height_error_p50_p95=np.percentile(np.abs(res),[50,95]).tolist(),face_recovery=recovery,seconds=time.monotonic()-start,output_sha256=sha(out/'terrain_valley.npz'),source_sha256=sha(source),limit='Outside patched ponds, restore exact first shoreline ring and join valley smoothing over 24m. Remaining water is extended only after this representation passes.')
(E/'authoring-a1.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
