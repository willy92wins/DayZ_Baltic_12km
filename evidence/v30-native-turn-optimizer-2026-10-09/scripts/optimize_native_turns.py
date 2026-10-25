"""One bounded pilot: optimize the actual native contour, not a target mask."""
from pathlib import Path
import json, time
import numpy as np
from scipy.optimize import minimize
from discover_native_turns import B, B9, B10, B12, sha, positions, stats


def bounds_for(ids, h, field, plane):
    base=h.ravel()[ids]; lower=base-2.; upper=base+2.
    physical_wet=np.zeros(len(ids),bool); pmax=np.full(len(ids),-np.inf)
    for slot,(dr,dc) in enumerate(((0,0),(0,1),(1,0),(1,1))):
        rr,cc=np.divmod(ids,2048); r,c=rr-dr,cc-dc
        ok=(r>=0)&(r<2047)&(c>=0)&(c<2047); j=np.flatnonzero(ok)
        j=j[np.isfinite(plane[r[j],c[j]])]
        pp=plane[r[j],c[j]]; ff=field[r[j],c[j],slot]; dd=base[j]-ff
        pmax[j]=np.maximum(pmax[j],pp); physical_wet[j]|=base[j]<pp
        eps=np.minimum(abs(dd)*.5,1e-4)
        dry=dd>0; wet=dd<0; zero=dd==0
        lower[j[dry]]=np.maximum(lower[j[dry]],ff[dry]+eps[dry])
        upper[j[wet]]=np.minimum(upper[j[wet]],ff[wet]-eps[wet])
        lower[j[zero]]=base[j[zero]]; upper[j[zero]]=base[j[zero]]
    lower[physical_wet]=np.maximum(lower[physical_wet],np.minimum(base[physical_wet],1.))
    upper[physical_wet]=np.minimum(upper[physical_wet],base[physical_wet])
    dry=~physical_wet
    floor=np.minimum(base,np.fmax(1.8,pmax+.0501))
    lower[dry]=np.maximum(lower[dry],floor[dry])
    assert np.all(lower<=base+1e-10) and np.all(upper>=base-1e-10)
    return lower-base,upper-base,physical_wet


def face_constraints(ids,h):
    lookup={int(v):i for i,v in enumerate(ids)}; cells=set()
    for index in ids:
        r,c=divmod(int(index),2048)
        cells.update((rr,cc) for rr in (r-1,r) for cc in (c-1,c) if 0<=rr<2047 and 0<=cc<2047)
    faces=[]
    for r,c in sorted(cells):
        a=r*2048+c; d=a+2049
        for b in (a+1,a+2048):
            if any(i in lookup for i in (a,b,d)):faces.append((a,b,d))
    faces=np.array(faces); G=np.zeros((len(faces),2,len(ids)))
    for k,face in enumerate(faces):
        for axis,(a,b) in enumerate(((face[0],face[1]),(face[1],face[2]))):
            if int(a) in lookup:G[k,axis,lookup[int(a)]]-=1
            if int(b) in lookup:G[k,axis,lookup[int(b)]]+=1
    old=h.ravel()[faces]; old=np.stack((old[:,1]-old[:,0],old[:,2]-old[:,1]),axis=1)
    radius=np.maximum(np.sum(old**2,axis=1),(6*np.tan(np.deg2rad(35)))**2)
    def fun(x):
        grad=old+np.einsum('ijk,k->ij',G,x)
        return radius-np.sum(grad**2,axis=1)
    def jac(x):
        grad=old+np.einsum('ijk,k->ij',G,x)
        return -2*np.einsum('ij,ijk->ik',grad,G)
    return fun,jac,faces


def main():
    source=B10/'measured-bank-bed-r2/terrain.npz'; assert sha(source)=='e7daa6c62cde457b666507ec7eae7e6d16015ad714028585fdb352ace678e52c'
    fp=B12/'preserved-field.npy'; assert sha(fp)=='7a5d0900533670a1e533965b36a6dcf28be2715f96f94ccbfbe6a846bdf98e37'
    terrain=dict(np.load(source)); h=terrain['heights'].astype(float); field=np.load(fp); plane=np.load(B10/'frozen-field-reference/plane.npy')
    result=h.copy(); reports={}; all_ids=[]
    for reach in ('R1','R2'):
        graph=json.loads((B/(reach+'-graph.json')).read_text()); masks=np.load(B/(reach+'-constraints.npz'))
        proposed=masks['movable']; lo,hi,wet=bounds_for(proposed,h,field,plane); keep=hi-lo>1e-8
        ids=proposed[keep];lo=lo[keep];hi=hi[keep]; all_ids.extend(ids.tolist())
        endpoint_ids=np.array([n['ids'] for n in graph['nodes']]); water=np.array([n['water'] for n in graph['nodes']]); xy=np.array([n['xz'] for n in graph['nodes']])
        depths=h.ravel()[endpoint_ids]-water
        lookup={int(v):i for i,v in enumerate(ids)}; J=np.zeros((*depths.shape,len(ids)))
        for k,pair in enumerate(endpoint_ids):
            for side,index in enumerate(pair):
                if int(index) in lookup:J[k,side,lookup[int(index)]]=1
        def contour(x):
            d=depths+np.einsum('ijk,k->ij',J,x); tau=d[:,0]/(d[:,0]-d[:,1])
            return xy[:,0]+tau[:,None]*(xy[:,1]-xy[:,0])
        original=contour(np.zeros(len(ids))); samplers=[]
        for chain in graph['chains']:
            points=original[chain]; length=np.linalg.norm(np.diff(points,axis=0),axis=1).sum()
            if length<=24:continue
            samplers.append((chain,np.arange(0,length,2)/length))
        calls=0; started=time.monotonic(); history=[]; last=np.zeros(len(ids))
        def objective(x):
            nonlocal calls
            calls+=1; points=contour(x); values=[]
            for chain,fraction in samplers:
                p=points[chain]; dist=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
                s=fraction*dist[-1]; q=np.c_[np.interp(s,dist,p[:,0]),np.interp(s,dist,p[:,1])]
                a=q[3:-3]-q[:-6]; b=q[6:]-q[3:-3]
                cosine=np.sum(a*b,axis=1)/np.maximum(np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1),1e-12)
                angle=np.arccos(np.clip(cosine,-1+1e-12,1-1e-12))
                values.extend((angle**2+4*np.maximum(angle-np.pi/6,0)**2).tolist())
            return float(np.mean(values)+.002*np.mean((x/2.)**2))
        constraint,jac,faces=face_constraints(ids,h)
        def callback(x):
            nonlocal last
            last=x.copy();elapsed=time.monotonic()-started
            if len(history)%10==0:print(json.dumps(dict(reach=reach,iteration=len(history)+1,objective=objective(x),seconds=elapsed)),flush=True)
            history.append(dict(iteration=len(history)+1,objective=objective(x),min_slope_constraint=float(constraint(x).min()),seconds=elapsed))
            if elapsed>180:raise TimeoutError('Per-reach 180-second budget reached')
        try:
            fit=minimize(objective,np.zeros(len(ids)),method='SLSQP',jac='2-point',bounds=list(zip(lo,hi)),
                         constraints=[dict(type='ineq',fun=constraint,jac=jac)],callback=callback,
                         options=dict(maxiter=160,ftol=1e-8,disp=False))
            x=fit.x; success=bool(fit.success);message=str(fit.message); nit=int(fit.nit)
        except TimeoutError as error:
            x=last; success=False;message=str(error);nit=len(history)
        result.ravel()[ids]=h.ravel()[ids]+x
        reports[reach]=dict(solver_success=success,message=message,iterations=nit,seconds=time.monotonic()-started,
                            objective_before=objective(np.zeros(len(ids))),objective_after=objective(x),objective_calls=calls,
                            variables=len(ids),bound_frozen=int((~keep).sum()),faces=len(faces),
                            min_slope_constraint=float(constraint(x).min()),max_height_change=float(abs(x).max(initial=0)),
                            bound_lower_active=int((abs(x-lo)<1e-5).sum()),bound_upper_active=int((abs(x-hi)<1e-5).sum()),
                            graph_before=stats(original,graph['chains']),graph_after=stats(contour(x),graph['chains']),history=history)
        print(json.dumps({k:v for k,v in reports[reach].items() if k!='history'},indent=2),flush=True)
    output=B/'candidate-native'; output.mkdir(exist_ok=False)
    terrain['heights']=result.astype(terrain['heights'].dtype); np.savez_compressed(output/'terrain.npz',**terrain)
    np.savez_compressed(output/'variables.npz',ids=np.array(all_ids))
    report=dict(status='CANDIDATE_REQUIRES_INDEPENDENT_CONSUMER',source_sha256=sha(source),terrain_sha256=sha(output/'terrain.npz'),reaches=reports)
    (B/'optimization.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],terrain_sha256=report['terrain_sha256'])),flush=True)


if __name__=='__main__':main()
