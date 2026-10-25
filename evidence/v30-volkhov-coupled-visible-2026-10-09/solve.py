from pathlib import Path
import sys,json,time,hashlib
import numpy as np
from scipy.optimize import minimize
import shapely
from shapely.geometry import box
from metrics import turns,energy,controls
B=Path(__file__).parent;R=Path('E:/DayZ-Baltic-Build')
sys.path[:0]=[str(R/'v30-native-turn-optimizer-20261009'),str(R/'v30-surface-crease-audit-20261009')]
from discover_native_turns import graph,positions
from verify_native_turns import geometry
from audit_native_surface import hinges,incident_any
t=dict(np.load(R/'v30-msta-dry-bank-solve-20261009/candidate/terrain.npz'));h=t['heights'].astype(float);p=np.load(R/'v30-isolated-basin-repair-20261009/candidate/plane.npy');f=np.load(R/'v30-isolated-basin-repair-20261009/candidate/visible-field.npy')
r0,c0,r1,c1=1494,2027,1515,2047;cells=[(r,c) for r in range(r0,r1) for c in range(c0,c1) if np.isfinite(p[r,c])];gg=graph(h,f,cells);assert not gg['branch_nodes'] and not gg['exact_zero_support']
rr,cc=np.mgrid[r0:r1+1,c0:c1+1];gids=rr*2048+cc;shape=gids.shape;old=h[rr,cc].ravel();width=shape[1]
gidlocal=lambda ids:(ids//2048-r0)*width+ids%2048-c0
edge_global=np.array([node['ids'] for node in gg['nodes']]);edge=gidlocal(edge_global);water=np.array([node['water'] for node in gg['nodes']]);xy=np.array([node['xz'] for node in gg['nodes']])
chains=gg['chains'];closed=np.array([ch[0]==ch[-1] for ch in chains]);assert sorted(closed.tolist())==[False,True]
pm=np.full(h.shape,.85)
for j,(dr,dc) in enumerate([(0,0),(0,1),(1,0),(1,1)]):
    dest=pm[dr:dr+2047,dc:dc+2047];np.fmax(dest,p,out=dest);np.fmax(dest,f[:,:,j],out=dest)
wet=h<=pm;fixed=np.load(R/'v30-native-terminal-finish-20261009/constraints.npz')['fixed']|wet;allowed=np.zeros(h.shape,bool);allowed[r0+1:r1,c0+1:c1]=True;allowed&=~fixed
free=np.unique(edge.ravel());free=free[allowed[rr.ravel()[free],cc.ravel()[free]]];lower=np.maximum(old[free]-1.5,np.minimum(old[free],1.8));lower=np.maximum(lower,pm[rr.ravel()[free],cc.ravel()[free]]+1e-4);upper=old[free]+1.5
np.savez_compressed(B/'domain.npz',allowed=allowed,fixed=fixed,wet=wet)
def values(x):v=old.copy();v[free]=x;return v
def contour(v):
    depth=v[edge]-water;fraction=depth[:,0]/(depth[:,0]-depth[:,1]);q=xy[:,0]+fraction[:,None]*(xy[:,1]-xy[:,0]);out=[]
    lo=np.array([c0*6+.001,12282-r1*6+.001]);hi=np.array([c1*6-.001,12282-r0*6-.001])
    for ch,isclosed in zip(chains,closed):
        pts=q[ch].copy()
        if not isclosed:
            for i,j in [(0,1),(-1,-2)]:
                step=0.
                for axis in (0,1):
                    if pts[i,axis]<lo[axis]:step=max(step,(lo[axis]-pts[i,axis])/(pts[j,axis]-pts[i,axis]))
                    if pts[i,axis]>hi[axis]:step=max(step,(hi[axis]-pts[i,axis])/(pts[j,axis]-pts[i,axis]))
                pts[i]+=step*(pts[j]-pts[i])
        out.append(pts)
    return out
def energies(v):return np.array([energy(q,c) for q,c in zip(contour(v),closed)])
def angles(v):return np.concatenate([turns(q,c) for q,c in zip(contour(v),closed)])
idx=np.arange(len(old)).reshape(shape);nw=idx[:-1,:-1].ravel();ne=idx[:-1,1:].ravel();sw=idx[1:,:-1].ravel();se=idx[1:,1:].ravel();tris=np.stack([np.c_[nw,ne,se],np.c_[nw,sw,se]],axis=1).reshape(-1,3)
present=np.repeat(np.isfinite(p[r0:r1,c0:c1]).ravel(),2);wt=tris[present];localf=f[r0:r1,c0:c1].reshape(-1,4);wf=np.stack([localf[:,[0,1,3]],localf[:,[0,2,3]]],axis=1).reshape(-1,3)[present];wp=np.repeat(p[r0:r1,c0:c1].ravel(),2)[present,None]
def areas(v):
    result=[]
    for levels in [wp,wf]:
        d=levels-v[wt];count=(d>0).sum(1);total=float((count==3).sum()*18)
        for n in (1,2):
            q=d[count==n]
            for i in range(3):
                mask=q[:,i]>0 if n==1 else q[:,i]<0;a=q[mask,i];b=q[mask,(i+1)%3];c=q[mask,(i+2)%3];frac=a*a/((a-b)*(a-c));total+=float(18*np.sum(frac if n==1 else 1-frac))
        result.append(total)
    return np.array(result)
def slopes(v):a,b,c=v[tris].T;return np.hypot(b-a,c-b)/6
hr0,hc0,hr1,hc1=r0-2,c0-2,min(2048,r1+3),min(2048,c1+3);patch=h[hr0:hr1,hc0:hc1];masks={k:incident_any(allowed[hr0:hr1,hc0:hc1],k) for k,_ in hinges(patch)}
def hinge_square(v):
    a=patch.copy();a[r0-hr0:r1+1-hr0,c0-hc0:c1+1-hc0]=v.reshape(shape);q=np.concatenate([arr[masks[k]] for k,arr in hinges(a)]);return float(np.mean(q*q))
reference=energies(old);target=areas(old);limit=np.maximum(slopes(old),np.tan(np.deg2rad(35)));amax=angles(old).max();hinge_limit=hinge_square(old)
extent=box(c0*6,12282-r1*6,c1*6,12282-r0*6);poly=geometry(h,f,cells);line=shapely.line_merge(poly.boundary.difference(extent.boundary.buffer(.001)));lines=[q for q in getattr(line,'geoms',[line]) if q.geom_type=='LineString' and q.length>24];independent=np.array([energy(np.array(next(line for line in lines if line.is_closed==c).coords),c) for c in closed]);assert np.max(abs(independent-reference))<1e-4
metric=dict(controls=controls(),closed=closed.tolist(),graph_energies=reference.tolist(),geos_energies=independent.tolist(),maximum_error=float(abs(reference-independent).max()));(B/'metric-controls.json').write_text(json.dumps(metric,indent=2)+'\n')
started=time.monotonic()
def callback(x):
    if time.monotonic()-started>120:raise TimeoutError('120 second solve budget')
constraints=[dict(type='eq',fun=lambda x:(areas(values(x))-target)/18),dict(type='ineq',fun=lambda x:.9*reference-1e-4-energies(values(x))),dict(type='ineq',fun=lambda x:amax-angles(values(x))),dict(type='ineq',fun=lambda x:(hinge_limit-hinge_square(values(x)))/hinge_limit),dict(type='ineq',fun=lambda x:limit-slopes(values(x)))]
result=minimize(lambda x:np.mean((x-old[free])**2),old[free],method='SLSQP',bounds=list(zip(lower,upper)),constraints=constraints,callback=callback,options=dict(maxiter=100,ftol=1e-9,disp=False));v=values(result.x);out=h.copy();out[rr,cc]=v.reshape(shape).astype(np.float32);dst=B/'candidate';dst.mkdir(exist_ok=False);np.savez_compressed(dst/'terrain.npz',**(t|dict(heights=out.astype(np.float32))))
report=dict(status='CONVERGED_REQUIRES_INDEPENDENT_CONSUMER' if result.success else 'SOLVER_FAILED_NO_PROMOTION',success=bool(result.success),message=str(result.message),iterations=int(result.nit),variables=len(free),seconds=time.monotonic()-started,energies_before=reference.tolist(),energies_after=energies(v).tolist(),areas_before=target.tolist(),areas_after=areas(v).tolist(),corner_before=float(np.degrees(amax)),corner_after=float(np.degrees(angles(v).max())),rms_before=hinge_limit**.5,rms_after=hinge_square(v)**.5,changed_vertices=int((out!=h).sum()),candidate_sha256=hashlib.sha256((dst/'terrain.npz').read_bytes()).hexdigest())
(B/'solver.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
