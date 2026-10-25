import numpy as np
from shapely.geometry import LineString
def turns(xy,closed=False):
    if closed:
        if np.linalg.norm(xy[-1]-xy[0])<1e-6:xy=xy[:-1]
        a=xy-np.roll(xy,1,axis=0);b=np.roll(xy,-1,axis=0)-xy
    else:a=xy[1:-1]-xy[:-2];b=xy[2:]-xy[1:-1]
    return np.arctan2(abs(a[:,0]*b[:,1]-a[:,1]*b[:,0]),np.sum(a*b,axis=1))
def energy(xy,closed=False):
    if closed:return float(np.sum(turns(xy,True)**2))
    if tuple(xy[0])>tuple(xy[-1]):xy=xy[::-1]
    ds=np.r_[0,np.cumsum(np.linalg.norm(np.diff(xy,axis=0),axis=1))];result=[]
    for phase in [0,.25,.5,.75]:
        at=np.arange(phase,ds[-1],1.);q=np.c_[np.interp(at,ds,xy[:,0]),np.interp(at,ds,xy[:,1])];result.append(np.sum(turns(q)**2))
    return float(np.mean(result))
def controls():
    q=np.array([[0.,0],[8,0],[9,2],[5,5],[0,4]]);ref=energy(q,True);variants=[]
    for start in range(len(q)):
        v=np.roll(q,start,axis=0)
        for x in [v,v[::-1]]:variants.append(energy(np.vstack([x,x[0]]),True))
    assert max(abs(x-ref) for x in variants)<1e-12
    square=np.array([[0.,0],[1,0],[1,1],[0,1]]);theta=np.linspace(0,2*np.pi,128,endpoint=False);circle=np.c_[np.cos(theta),np.sin(theta)]
    assert abs(energy(square,True)-np.pi**2)<1e-12 and energy(circle,True)<.04*energy(square,True)
    return dict(closed_start_and_direction_invariant=True,variant_count=len(variants),square_energy=energy(square,True),circle_energy=energy(circle,True))
