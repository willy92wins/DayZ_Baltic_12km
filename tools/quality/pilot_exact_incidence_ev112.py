"""Exact incidence fallback: an area bound selects exact arithmetic, never discards."""
from fractions import Fraction as F
import numpy as np
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def sub(a,b):return (a[0]-b[0],a[1]-b[1])
def rational_polygon(triangles):
    ts=[[(F(float(x)),F(float(z))) for x,z in t] for t in triangles];p=ts[0]
    if not cross(sub(p[1],p[0]),sub(p[2],p[0])):raise ValueError('exact_degenerate_triangle')
    for tri in ts[1:]:
        orientation=cross(sub(tri[1],tri[0]),sub(tri[2],tri[0]))
        if not orientation:raise ValueError('exact_degenerate_triangle')
        sign=1 if orientation>0 else -1
        for a,b in zip(tri,tri[1:]+tri[:1]):
            if not p:break
            vals=[sign*cross(sub(b,a),sub(q,a)) for q in p];out=[]
            for j,q in enumerate(p):
                k=(j+1)%len(p);v,w=vals[j],vals[k]
                if v>=0:out.append(q)
                if v*w<0:
                    t=v/(v-w);delta=sub(p[k],q)
                    out.append((q[0]+t*delta[0],q[1]+t*delta[1]))
            p=[]
            for q in out:
                if not p or q!=p[-1]:p.append(q)
            if len(p)>1 and p[0]==p[-1]:p.pop()
    if len(p)<3:return []
    area=sum(cross(sub(p[j],p[0]),sub(p[j+1],p[0])) for j in range(1,len(p)-1))
    return p if area else []
def positive_pair(a,b):
    v=np.concatenate((a,b))*512
    if not np.isfinite(v).all():raise ValueError('nonfinite_incidence')
    if not np.array_equal(v,np.rint(v)):return bool(rational_polygon((a,b)))
    left=[[int(x) for x in row] for row in v[:3]];right=[[int(x) for x in row] for row in v[3:]]
    for tri in (left,right):
        if not cross(sub(tri[1],tri[0]),sub(tri[2],tri[0])):raise ValueError('exact_degenerate_triangle')
        for p,q in zip(tri,tri[1:]+tri[:1]):
            dx,dz=sub(q,p);axis=(-dz,dx)
            l=[x*axis[0]+z*axis[1] for x,z in left];r=[x*axis[0]+z*axis[1] for x,z in right]
            if min(max(l),max(r))<=max(min(l),min(r)):return False
    return True
def guarded_intersection(bed,native,water,approximate,area):
    source=np.concatenate((bed,native,water))
    bound=64*np.finfo(float).eps*max(1.,float(abs(source).max()))*max(1.,float(np.ptp(source,axis=0).max()))
    if area>bound:return approximate,False,None
    exact=rational_polygon((bed,native,water))
    return np.asarray([(float(x),float(z)) for x,z in exact],float).reshape(-1,2),True,bool(exact)
