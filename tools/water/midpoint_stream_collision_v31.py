"""Opt-in bounded midpoint search; saved-mesh and native acceptance are separate."""
if not __debug__:
    raise RuntimeError('Authoring requires assertions enabled; do not use python -O')
from functools import lru_cache
import math
import time
import numpy as np
from scipy.spatial import QhullError
from compact_stream_collision_v31 import fit_grid, hull_for, triangles


class SearchLimit(RuntimeError):
    """An inconclusive bounded search, never a partial candidate."""


def partition_midpoint(grid, *, max_vertices_per_component, max_faces_per_component,
                       vertical_budget=.015, horizontal_budget=.002,
                       max_states=20000, timeout_s=60.):
    grid=np.asarray(grid,float)
    if grid.ndim!=3 or grid.shape[2]!=3 or min(grid.shape[:2])<2 or not np.isfinite(grid).all():
        raise ValueError('finite bed grid required')
    for value,minimum in ((max_vertices_per_component,6),(max_faces_per_component,8),(max_states,1)):
        if type(value) is not int or value<minimum:raise ValueError('invalid integer search/component limit')
    if any(isinstance(v,bool) or not math.isfinite(v) or v<0 for v in (vertical_budget,horizontal_budget)):
        raise ValueError('finite nonnegative contact budgets required')
    if isinstance(timeout_s,bool) or not math.isfinite(timeout_s) or timeout_s<=0:
        raise ValueError('positive finite timeout required')
    started=time.monotonic();calls=0;decisions={}

    def deadline():
        if time.monotonic()-started>timeout_s:raise SearchLimit('INCONCLUSIVE: midpoint search time limit')

    def fits_caps(part):
        return len(part['points'])<=max_vertices_per_component and len(part['faces'])<=max_faces_per_component

    def cost(parts):
        return len(parts),sum(len(p['faces']) for p in parts),sum(len(p['points']) for p in parts)

    @lru_cache(maxsize=None)
    def solve(r0,r1,c0,c1):
        nonlocal calls
        deadline()
        if calls>=max_states:raise SearchLimit('INCONCLUSIVE: midpoint search state limit')
        calls+=1
        g=grid[r0:r1+1,c0:c1+1]
        try:part=fit_grid(g,vertical_budget,horizontal_budget)
        except QhullError:part=None
        deadline()
        key=(r0,r1,c0,c1)
        if part is not None and fits_caps(part):
            decisions[key]='hull';return (part,)
        n,m=g.shape[:2]
        if n==m==2:
            parts=[];top=g.reshape(-1,3)
            for tri in triangles(n,m):
                points,faces,_,volume=hull_for(top[tri])
                part=dict(points=points,faces=faces,volume=float(volume),roof_upper_error_bound_m=0.,source_triangles=1)
                if not fits_caps(part):raise ValueError('triangular leaf exceeds component limits')
                parts.append(part)
            deadline();decisions[key]='triangles';return tuple(parts)
        choices=[]
        # Stable tie break: row split before column split; first minimum wins.
        if n>2:
            mid=(r0+r1)//2
            choices.append(('row',solve(r0,mid,c0,c1)+solve(mid,r1,c0,c1)))
        if m>2:
            mid=(c0+c1)//2
            choices.append(('column',solve(r0,r1,c0,mid)+solve(r0,r1,mid,c1)))
        axis,parts=min(choices,key=lambda x:cost(x[1]))
        deadline();decisions[key]=axis;return parts

    root=(0,grid.shape[0]-1,0,grid.shape[1]-1)
    parts=solve(*root);deadline()
    if sum(p['source_triangles'] for p in parts)!=2*(grid.shape[0]-1)*(grid.shape[1]-1):
        raise ValueError('source triangle count changed')
    cuts=[]
    def selected(key):
        axis=decisions[key]
        if axis not in ('row','column'):return
        cuts.append(dict(bounds=list(key),axis=axis));r0,r1,c0,c1=key
        if axis=='row':
            mid=(r0+r1)//2;selected((r0,mid,c0,c1));selected((mid,r1,c0,c1))
        else:
            mid=(c0+c1)//2;selected((r0,r1,c0,mid));selected((r0,r1,mid,c1))
    selected(root);deadline()
    return list(parts),dict(states=calls,seconds=time.monotonic()-started,selected_splits=cuts,
        cost=dict(zip(('components','faces','vertices'),cost(parts))),
        max_vertices_per_component=max(len(p['points']) for p in parts),
        max_faces_per_component=max(len(p['faces']) for p in parts),
        limits=dict(max_states=max_states,timeout_s=timeout_s,max_vertices_per_component=max_vertices_per_component,max_faces_per_component=max_faces_per_component),
        scope='Both midpoint cuts at rejected blocks only; not all possible partitions. No engine or FPS acceptance.')
