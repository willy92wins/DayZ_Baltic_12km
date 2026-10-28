"""Convex common refinement against native NW-SE terrain and nominal water.
Numerical uncertainty is explicit; positive/negative heights are never rounded.
This module does not itself accept a map, render, or repaired surface.
"""
import math
import numpy as np
OFF=((0,0),(0,1),(1,0),(1,1))
TRI=((0,1,3),(0,2,3))

def require(ok,reason):
    if not bool(ok):raise ValueError(reason)

def cross(a,b):return float(a[0]*b[1]-a[1]*b[0])

def area(p):
    p=np.asarray(p,float)
    if len(p)<3:return 0.
    q=p-p[0]
    return abs(math.fsum(cross(q[i],q[i+1]) for i in range(1,len(p)-1)))*.5

def clip(p,values,positive=True):
    """Half-plane clipping with exact linear edge interpolation; no height epsilon."""
    p=np.asarray(p,float);values=np.asarray(values,float)
    require(values.shape==(len(p),) and np.isfinite(p).all() and np.isfinite(values).all(),'clip_input')
    if not positive:values=-values
    result=[]
    for i in range(len(p)):
        j=(i+1)%len(p);a,b=values[i],values[j]
        if a>=0:result.append(p[i])
        if (a<0<b) or (b<0<a):
            result.append(p[i]+(p[j]-p[i])*(a/(a-b)))
    # Remove only exact repeated neighbours; never weld close coordinates.
    out=[]
    for point in result:
        if not out or not np.array_equal(point,out[-1]):out.append(point)
    if len(out)>1 and np.array_equal(out[0],out[-1]):out.pop()
    return np.asarray(out,float).reshape(-1,2)

def triangle_intersection(p,t):
    t=np.asarray(t,float)
    direction=cross(t[1]-t[0],t[2]-t[0])
    require(direction!=0,'degenerate_clipping_triangle')
    for a,b in zip(t,np.roll(t,-1,axis=0)):
        if not len(p):break
        values=np.array([cross(b-a,z-a) for z in p])*np.sign(direction)
        p=clip(p,values)
    return p

def plane(t,y):
    t,y=np.asarray(t,float),np.asarray(y,float)
    require(t.shape==(3,2) and y.shape==(3,) and np.isfinite(t).all() and np.isfinite(y).all(),'plane_input')
    edges=t[1:]-t[0];det=cross(edges[0],edges[1])
    condition=abs(det)/max(float(np.sum(edges*edges,axis=1).max()),np.finfo(float).tiny)
    require(condition>1e-12,'INCONCLUSIVE_NEAR_DEGENERATE_PROJECTION')
    slope=np.linalg.solve(edges,y[1:]-y[0])
    return t[0],float(y[0]),slope

def evaluate(coeff,p):
    origin,y,slope=coeff
    return y+(np.asarray(p)-origin)@slope

def refine(triangle,h,water_plane,water_field,grid=6.):
    """Return every positive-area triangle/native-face intersection with B/H/W."""
    tri=np.asarray(triangle,float);n=len(h);top=(n-1)*grid
    require(tri.shape==(3,3) and np.isfinite(tri).all(),'bed_triangle')
    xz=tri[:,(0,2)]
    require((xz>=0).all() and (xz<=top).all(),'outside_native_domain')
    bc=plane(xz,tri[:,1])
    lo=xz.min(axis=0);hi=xz.max(axis=0)
    r0=max(0,math.floor((top-hi[1])/grid));r1=min(n-2,math.floor((top-lo[1])/grid))
    c0=max(0,math.floor(lo[0]/grid));c1=min(n-2,math.floor(hi[0]/grid))
    parts=[]
    for r in range(r0,r1+1):
        for c in range(c0,c1+1):
            corners=np.array([[grid*(c+dc),top-grid*(r+dr)] for dr,dc in OFF])
            hv=np.array([h[r+dr,c+dc] for dr,dc in OFF],float)
            has_pond=bool(np.isfinite(water_plane[r,c]))
            wv=water_field[r,c] if has_pond else np.full(4,.75)
            for ti,indices in enumerate(TRI):
                q=corners[list(indices)];p=triangle_intersection(xz.copy(),q);a=area(p)
                if a==0:continue
                hc=plane(q,hv[list(indices)]);wc=plane(q,wv[list(indices)])
                b=evaluate(bc,p);terrain=evaluate(hc,p);water=evaluate(wc,p)
                require(np.isfinite([b,terrain,water]).all(),'nonfinite_surface')
                parts.append(dict(polygon=p,area=a,cell=(r,c,ti),native_triangle=q,bed=b,terrain=terrain,water=water,
                                  bed_plane=bc,terrain_plane=hc,water_coeff=wc,water_kind='POND' if has_pond else 'SEA'))
    expected=area(xz);actual=math.fsum(p['area'] for p in parts)
    require(abs(expected-actual)<=max(1e-9,expected*1e-10),'INCONCLUSIVE_REFINEMENT_AREA_GAP')
    return parts

def sign_regions(part,field):
    """Area on either side of B-H or B-W; extrema include all cut vertices."""
    p=part['polygon'];other=part['terrain_plane'] if field=='terrain' else part['water_coeff']
    diff=part['bed']-part[field]
    positive=clip(p,diff);negative=clip(p,diff,False)
    zero=bool(np.all(diff==0))
    return dict(above_area=0. if zero else area(positive),below_area=0. if zero else area(negative),
                contact_area=part['area'] if zero else 0.,minimum=float(diff.min()),maximum=float(diff.max()),
                above_polygon=positive,below_polygon=negative)
