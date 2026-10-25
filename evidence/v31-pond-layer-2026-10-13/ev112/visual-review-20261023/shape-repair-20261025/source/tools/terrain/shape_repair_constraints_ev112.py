"""Freeze native triangles supporting the whole +/-4 m road ribbon.

Each polyline segment is sampled at <=1 m. A ribbon point is at most 4 m
from that segment, at most .5 m from its nearest sample along the segment,
and every native triangle corner is within 6*sqrt(2) m of the point.
The conservative radius therefore preserves every triangle used by a road
consumer, including between its stations and near junctions.
"""
import hashlib
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree


def road_vertex_guard(chains, shape=(2048, 2048), cell=6., zmax=12282., half_width=4.):
    if not chains:
        raise ValueError('road reference must not be empty')
    samples=[]
    for p in chains:
        p=np.asarray(p, float)
        if p.ndim!=2 or p.shape[1]!=2 or len(p)<2 or not np.isfinite(p).all():
            raise ValueError('invalid road chain')
        for a,b in zip(p[:-1],p[1:]):
            length=np.linalg.norm(b-a)
            if length<=0:
                raise ValueError('zero length road segment')
            samples.append(a+np.linspace(0,1,int(np.ceil(length))+1)[:,None]*(b-a))
    tree=cKDTree(np.concatenate(samples))
    radius=half_width+cell*np.sqrt(2)+.5+1e-8
    guard=np.zeros(shape,bool)
    for r0 in range(0,shape[0],128):
        rr,cc=np.mgrid[r0:min(r0+128,shape[0]),:shape[1]]
        q=np.c_[cc.ravel()*cell,zmax-rr.ravel()*cell]
        guard[r0:r0+len(rr)]=(tree.query(q)[0]<=radius).reshape(rr.shape)
    return guard


def s3_road_guard():
    # The same frozen polyline source as verify_roads_v30. Its independent
    # coverage hash remains a separate post-candidate gate.
    import verify_roads_v30 as roads
    guard=road_vertex_guard(roads.road_chains())
    root=Path(roads.R)
    paths=[root/'tests/regional_foundation_roads_v6/reference.npz',
           root/'evidence/regional-foundation-v1/road-grade-chains-v6.json']
    return guard,{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
