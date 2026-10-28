"""Height-only obstacle solve. A numerical candidate, never visual acceptance."""
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

def require(ok,why):
    if not bool(ok):raise ValueError(why)

def mesh_edges(triangles):
    t=np.asarray(triangles,int)
    return np.unique(np.sort(np.concatenate((t[:,[0,1]],t[:,[1,2]],t[:,[2,0]])),axis=1),axis=0)

def local_domain(points,triangles,seeds,radius=12.):
    edges=mesh_edges(triangles);length=np.linalg.norm(points[edges[:,0]][:,[0,2]]-points[edges[:,1]][:,[0,2]],axis=1)
    require((length>0).all(),'zero_projected_edge')
    n=len(points);graph=coo_matrix((np.r_[length,length],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(n,n)).tocsr()
    starts=np.unique(triangles[np.asarray(seeds,bool)])
    require(len(starts)>0,'empty_seed_set')
    dist=dijkstra(graph,directed=False,indices=starts,min_only=True,limit=radius)
    return dist<radius,dist

def barycentric(triangle,points):
    t=np.asarray(triangle,float)[:,[0,2]];p=np.asarray(points,float)
    uv=np.linalg.solve((t[1:]-t[0]).T,(p-t[0]).T).T
    raw=np.c_[1-uv.sum(1),uv]
    require(np.isfinite(raw).all() and raw.min()>=-1e-9 and raw.max()<=1+1e-9,'outside_triangle_sample')
    # Only LP coefficient construction; consumer checks original unrounded geometry.
    positive=np.maximum(raw,0);return positive/positive.sum(1)[:,None]

def solve(points,triangles,free,sample_faces,weights,clearance,margin=.03,support_minimum=None):
    p=np.asarray(points,float);t=np.asarray(triangles,int);free=np.asarray(free,bool)
    sf=np.asarray(sample_faces,int);w=np.asarray(weights,float);c=np.asarray(clearance,float)
    require(p.shape==(len(p),3) and free.shape==(len(p),) and len(sf)>0,'input_shape')
    require(w.shape==(len(sf),3) and c.shape==(len(sf),) and np.isfinite(p).all() and np.isfinite(w).all() and np.isfinite(c).all(),'nonfinite_or_sample_shape')
    require((w>=0).all() and np.max(abs(w.sum(1)-1))<1e-12,'weights')
    require((sf>=0).all() and (sf<len(t)).all(),'sample_face')
    lookup=np.full(len(p),-1,int);lookup[free]=np.arange(free.sum());count=int(free.sum())
    support=free[t[sf]];effective=(w*support).sum(1)
    fixed_conflict=(effective==0)&(c>1e-9)
    if fixed_conflict.any():return None,dict(status='INFEASIBLE_FIXED_SUPPORT',samples=np.flatnonzero(fixed_conflict).tolist(),maximum=float(c[fixed_conflict].max()))
    require(count>0,'empty_free_set')
    native_samples=(w*p[t[sf],1]).sum(1)-c
    minimum=float(native_samples.min()) if support_minimum is None else float(support_minimum)
    require(np.isfinite(minimum) and minimum<=float(native_samples.min())+1e-9,'support_minimum')
    # Do not compensate an almost-fixed positive residual by burying a vertex
    # millions of metres. Bound descent by the actual local native support floor.
    floor=float(np.floor((minimum-margin)*512)/512)
    capacity=np.maximum(0,p[:,1]-floor)*free
    required=c+margin*effective;maximum=(w*capacity[t[sf]]).sum(1)
    impossible=required-maximum>1e-9
    if impossible.any():return None,dict(status='INFEASIBLE_DESCENT_ENVELOPE',samples=np.flatnonzero(impossible).tolist(),maximum_unmet=float((required-maximum)[impossible].max()),native_support_minimum=minimum,quantized_support_floor=floor)
    rows=[];cols=[];values=[];rhs=[]
    for ids,ww,cc,ee in zip(t[sf],w,c,effective):
        if ee==0:continue
        ri=len(rhs)
        for vertex,b in zip(ids,ww):
            if free[vertex] and b:rows.append(ri);cols.append(lookup[vertex]);values.append(-b)
        rhs.append(-cc-margin*ee)
    edges=mesh_edges(t)
    for a,b in edges:
        if not (free[a] or free[b]):continue
        length=float(np.linalg.norm(p[a,[0,2]]-p[b,[0,2]]));require(length>0,'zero_edge')
        for sign in (-1.,1.):
            ri=len(rhs)
            for vertex,weight in ((a,sign),(b,-sign)):
                if free[vertex]:rows.append(ri);cols.append(lookup[vertex]);values.append(weight)
            rows.append(ri);cols.append(count);values.append(-length);rhs.append(0.)
    matrix=coo_matrix((values,(rows,cols)),shape=(len(rhs),count+1)).tocsr()
    objective=np.zeros(count+1);objective[-1]=1
    options=dict(time_limit=120,primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9,threads=1)
    bounds=[(0,float(v)) for v in capacity[free]]+[(0,None)]
    one=linprog(objective,A_ub=matrix,b_ub=rhs,bounds=bounds,method='highs',options=options)
    report=dict(phase1_status=int(one.status),phase1_message=one.message,free_vertices=count,samples=len(sf),constraints=len(rhs))
    if not one.success:return None,dict(report,status='INCONCLUSIVE_SOLVER')
    objective[:]=1;objective[-1]=0
    bounds[-1]=(0,float(np.nextafter(one.x[-1],np.inf)))
    two=linprog(objective,A_ub=matrix,b_ub=rhs,bounds=bounds,method='highs',options=options)
    report.update(phase2_status=int(two.status),phase2_message=two.message,optimal_displacement_gradient=float(one.x[-1]))
    if not two.success:return None,dict(report,status='INCONCLUSIVE_LEXICOGRAPHIC_SOLVER')
    out=p.copy();changed_ids=np.flatnonzero(free)[two.x[:count]>1e-9]
    out[changed_ids,1]=np.maximum(floor,np.floor((p[changed_ids,1]-two.x[:count][two.x[:count]>1e-9])*512)/512)
    require(np.array_equal(out[~free],p[~free]) and np.array_equal(out[:,[0,2]],p[:,[0,2]]) and (out[:,1]<=p[:,1]).all(),'candidate_invariants')
    residual=c-(w*(p[t[sf],1]-out[t[sf],1])).sum(1)
    require(float(residual.max())<=1e-9,'postquantization_corridor_failure')
    descent=p[:,1]-out[:,1];gradient=abs(descent[edges[:,0]]-descent[edges[:,1]])/np.linalg.norm(p[edges[:,0]][:,[0,2]]-p[edges[:,1]][:,[0,2]],axis=1)
    report.update(status='NUMERIC_CANDIDATE_PENDING_CONSUMER',maximum_residual=float(residual.max()),changed_vertices=int(np.count_nonzero(descent)),maximum_descent=float(descent.max()),quantized_displacement_gradient=float(gradient.max()),native_support_minimum=minimum,quantized_support_floor=floor)
    return out,report
