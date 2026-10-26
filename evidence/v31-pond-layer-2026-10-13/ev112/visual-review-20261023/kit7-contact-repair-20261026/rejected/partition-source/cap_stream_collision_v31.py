"""Partition a vertical convex collision solid without changing its upper envelope."""
import numpy as np
from scipy.spatial import ConvexHull

def split_roof(points, faces, max_vertices=72, max_faces=140):
    p=np.asarray(points,float);f=np.asarray(faces,int)
    if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all():
        raise ValueError('Finite 3D vertices required')
    if f.ndim!=2 or f.shape[1]!=3 or f.min()<0 or f.max()>=len(p):
        raise ValueError('Triangular indexed faces required')
    if type(max_vertices) is not int or type(max_faces) is not int or max_vertices<6 or max_faces<8:
        raise ValueError('Caps cannot hold a triangular prism')
    original=ConvexHull(p);bottom=float(p[:,1].min())
    tri=p[f];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    # Input MLOD components use inward winding.
    if np.any(np.einsum('ij,ij->i',n,tri.mean(1)-p.mean(0))>=-1e-10):
        raise ValueError('Strictly inward nondegenerate faces required')
    roof=f[n[:,1]<-1e-8]
    if not len(roof):raise ValueError('No roof')
    order=np.lexsort((p[roof].mean(1)[:,2],p[roof].mean(1)[:,0]))
    roof=roof[order]
    def hull(indices):
        top=p[np.unique(np.asarray(indices).ravel())]
        low=top.copy();low[:,1]=bottom
        cloud=np.unique(np.vstack((top,low)),axis=0)
        # Every flattened corner must belong to the original solid. Without
        # this condition a convex overhang would silently acquire a larger base.
        if (cloud@original.equations[:,:3].T+original.equations[:,3]).max()>1e-8:
            raise ValueError('Solid is not vertically extruded down to one flat base')
        h=ConvexHull(cloud);used=h.vertices;lookup=np.full(len(cloud),-1,int);lookup[used]=np.arange(len(used))
        return dict(points=cloud[used],faces=lookup[h.simplices],volume=float(h.volume))
    def fits(part):return len(part['points'])<=max_vertices and len(part['faces'])<=max_faces
    parts=[];pending=[];last=None
    for face in roof:
        trial=hull(pending+[face])
        if fits(trial):pending.append(face);last=trial
        else:
            if not pending:raise ValueError('Single roof triangle exceeds caps')
            parts.append(last);pending=[face];last=hull(pending)
            if not fits(last):raise ValueError('Single roof triangle exceeds caps')
    if pending:parts.append(last)
    if not parts:raise ValueError('Empty partition')
    return parts

