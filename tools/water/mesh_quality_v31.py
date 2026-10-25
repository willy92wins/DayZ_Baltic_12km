"""Independent saved-geometry invariants. No appearance or engine verdict."""
from collections import Counter,defaultdict
import numpy as np
from scipy.spatial import cKDTree


def bidirectional_error(source,compiled):
    a,b=np.asarray(source,float),np.asarray(compiled,float)
    if any(x.ndim!=2 or x.shape[1]!=3 or not len(x) or not np.isfinite(x).all() for x in (a,b)):
        raise ValueError('nonempty finite Nx3 vertices required')
    return dict(compiled_to_source=float(cKDTree(a).query(b)[0].max()),
                source_to_compiled=float(cKDTree(b).query(a)[0].max()))


def closed_component(triangles):
    """Weld equal positions, then require a connected orientable closed 2-manifold.

    A volume sign alone accepts open sheets. Exact welding here is appropriate
    for saved MLOD components which reuse identical positions at shared edges.
    """
    t=np.asarray(triangles,float)
    if t.ndim!=3 or t.shape[1:]!=(3,3) or not len(t) or not np.isfinite(t).all():
        raise ValueError('finite nonempty triangular component required')
    vertices,inverse=np.unique(t.reshape(-1,3),axis=0,return_inverse=True)
    faces=inverse.reshape(-1,3);edges=defaultdict(list);neighbours=defaultdict(set)
    degenerates=int((np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)<=1e-12).sum())
    for fi,face in enumerate(faces):
        for a,b in zip(face,np.roll(face,-1)):
            edges[tuple(sorted((int(a),int(b))))].append((fi,int(a),int(b)))
    wrong_edges=sum(len(rows)!=2 or rows[0][1:]!=rows[1][1:][::-1] for rows in edges.values())
    for rows in edges.values():
        for a in rows:
            neighbours[a[0]].update(b[0] for b in rows if b[0]!=a[0])
    reached=set();todo=[0]
    while todo:
        f=todo.pop()
        if f not in reached:reached.add(f);todo.extend(neighbours[f]-reached)
    shifted=t-vertices.mean(axis=0)
    volume=float(np.einsum('ij,ij->i',shifted[:,0],np.cross(shifted[:,1],shifted[:,2])).sum()/6)
    duplicate_faces=len(faces)-len(Counter(tuple(sorted(f)) for f in faces))
    valid=not wrong_edges and not degenerates and not duplicate_faces and len(reached)==len(faces) and abs(volume)>1e-12
    return dict(closed=bool(valid),bad_edges=int(wrong_edges),degenerate_faces=degenerates,
                duplicate_faces=duplicate_faces,connected_faces=len(reached),faces=len(faces),signed_volume=volume)
