from pathlib import Path
import sys,json,time,hashlib
import numpy as np
from scipy.optimize import minimize
B=Path(__file__).parent;R=Path('E:/DayZ-Baltic-Build')
t=dict(np.load(R/'v30-native-hinge-finish-20261009/candidate/terrain.npz'));h=t['heights'].astype(float);seed=np.load(R/'v30-native-terminal-topology-20261009/candidate/terrain.npz')['heights'].astype(float);p=np.load(R/'v30-global-water-risk-20261009/frozen-field-reference/plane.npy')
dm=np.load(R/'v30-area-constrained-bank-20261009/domain.npz');allowed=dm['allowed'];fixed=dm['fixed'];r0,c0,r1,c1=589,2027,610,2047;L=3.425
rr,cc=np.mgrid[r0:r1+1,c0:c1+1];gids=rr*2048+cc;shape=gids.shape;old=h[rr,cc].ravel();initial=seed[rr,cc].ravel();xy=np.c_[cc.ravel()*6,12282-rr.ravel()*6]
idx=np.arange(len(old)).reshape(shape);nw=idx[:-1,:-1].ravel();ne=idx[:-1,1:].ravel();sw=idx[1:,:-1].ravel();se=idx[1:,1:].ravel();tris=np.stack([np.c_[nw,ne,se],np.c_[nw,sw,se]],axis=1).reshape(-1,3)
present=np.repeat(np.isfinite(p[r0:r1,c0:c1]).ravel(),2);watertris=tris[present];edges={};segments=[]
for tri in watertris:
    pts=[]
    for a,b in zip(tri,np.roll(tri,-1)):
        if (old[a]<L)!=(old[b]<L):
            e=tuple(sorted((int(a),int(b))));pts.append(edges.setdefault(e,len(edges)))
    if len(pts)==2:segments.append(pts)
edge=np.array(list(edges));adj=[[] for _ in edges]
for a,b in segments:adj[a].append(b);adj[b].append(a)
assert max(map(len,adj))==2
ends=[i for i,x in enumerate(adj) if len(x)==1];assert len(ends)==2
order=[ends[0]];previous=-1
while True:
    opts=[i for i in adj[order[-1]] if i!=previous]
    if not opts:break
    previous,current=order[-1],opts[0];order.append(current)
    assert len(order)<=len(edge)
assert len(order)==len(edge)
free=np.unique(edge.ravel());free=free[allowed[rr.ravel()[free],cc.ravel()[free]]&~fixed[rr.ravel()[free],cc.ravel()[free]]]
tip=(rr.ravel()==600)&(cc.ravel()==2037);free=free[~tip[free]]
sign=old[free]<L;lower=np.maximum(old[free]-1.5,1.);upper=old[free]+1.5;lower[~sign]=np.maximum(lower[~sign],L+1e-4);upper[sign]=np.minimum(upper[sign],L-1e-4)
core=np.zeros(shape,bool)
for row,col,d in zip(dm['rr'],dm['cc'],dm['signed']-float(dm['offset'])):
    if d<=-3:core[row-r0,col-c0]=True
upper[core.ravel()[free]]=np.minimum(upper[core.ravel()[free]],L-.3)
def values(x):
    v=initial.copy();v[free]=x;return v
def points(v):
    a,b=edge.T;f=(L-v[a])/(v[b]-v[a]);return (xy[a]+f[:,None]*(xy[b]-xy[a]))[order]
def angles(pts):
    d=np.diff(pts,axis=0);return np.arctan2(abs(d[:-1,0]*d[1:,1]-d[:-1,1]*d[1:,0]),(d[:-1]*d[1:]).sum(1))
def energy(pts):
    ds=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))];out=[]
    for phase in [0,.25,.5,.75]:
        at=np.arange(phase,ds[-1],1.);sample=np.c_[np.interp(at,ds,pts[:,0]),np.interp(at,ds,pts[:,1])];out.append(np.sum(angles(sample)**2))
    return float(np.mean(out))
def area(v):
    d=L-v[watertris];wet=(d>0).sum(1);total=float((wet==3).sum()*18)
    for count in [1,2]:
        q=d[wet==count]
        for i in range(3):
            mask=(q[:,i]>0) if count==1 else (q[:,i]<0);a=q[mask,i];b=q[mask,(i+1)%3];c=q[mask,(i+2)%3];fraction=a*a/((a-b)*(a-c));total+=float(18*np.sum(fraction if count==1 else 1-fraction))
    return total
def slopes(v):
    a,b,c=v[tris].T
    return np.hypot(b-a,c-b)/6
target=area(old);limit=np.maximum(slopes(old),np.tan(np.deg2rad(35)));amax=float(angles(points(old)).max());start=time.monotonic();calls=0
def objective(x):
    global calls
    calls+=1;v=values(x);return energy(points(v))+.001*np.mean((x-initial[free])**2)
constraints=[{'type':'eq','fun':lambda x:(area(values(x))-target)/18},{'type':'ineq','fun':lambda x:amax-angles(points(values(x)))},{'type':'ineq','fun':lambda x:limit-slopes(values(x))}]
x0=np.clip(initial[free],lower,upper)
result=minimize(objective,x0,method='SLSQP',bounds=list(zip(lower,upper)),constraints=constraints,options={'maxiter':100,'ftol':1e-9,'disp':False})
v=values(result.x);out=seed.copy();out[rr,cc]=v.reshape(shape).astype(np.float32)
report=dict(status='SOLVER_CONVERGED_REQUIRES_INDEPENDENT_CONSUMER' if result.success else 'SOLVER_FAILED_NO_PROMOTION',success=bool(result.success),message=str(result.message),iterations=int(result.nit),evaluations=calls,seconds=time.monotonic()-start,variables=len(free),boundary_nodes=len(edge),area_before=target,area_after=area(v),energy_before=energy(points(old)),energy_seed=energy(points(initial)),energy_after=energy(points(v)),corner_before_deg=float(np.degrees(amax)),corner_after_deg=float(np.degrees(angles(points(v)).max())),minimum_constraint=float(min(np.min(c['fun'](result.x)) for c in constraints[1:])),limits=['One fixed-topology native solve; no parameter sweep.','Output remains unaccepted until independent reconstruction and global conservation gates.'])
dst=B/'candidate';dst.mkdir(exist_ok=False);np.savez_compressed(dst/'terrain.npz',**(t|{'heights':out.astype(np.float32)}));report['candidate_sha256']=hashlib.sha256((dst/'terrain.npz').read_bytes()).hexdigest();np.savez_compressed(B/'solver-domain.npz',rr=rr,cc=cc,free=free,old=old,initial=initial,after=v,edge=edge,order=order)
(B/'solver.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
