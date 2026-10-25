"""Bounded-memory, monotonic float32 rollback primitives for the EV95 screen."""
from __future__ import annotations

import numpy as np


def clip_solution_float32(solution64, lower32, upper32):
    x=np.asarray(solution64,dtype=np.float64)
    lo=np.asarray(lower32,dtype=np.float32)
    hi=np.asarray(upper32,dtype=np.float32)
    if x.ndim!=1 or lo.shape!=x.shape or hi.shape!=x.shape or not np.isfinite(x).all():
        raise ValueError('solution and inward boxes must be finite same-length vectors')
    if np.any(lo>hi): raise ValueError('inward float32 box is infeasible')
    clipped=np.clip(x,lo.astype(np.float64),hi.astype(np.float64)).astype(np.float32)
    if np.any(clipped<lo) or np.any(clipped>hi):
        raise ValueError('float32 cast escaped the inward box')
    return clipped


def _add_incident_nodes(rollback, changed, r, c, offsets):
    for dr,dc in offsets:
        rr=r+dr; cc=c+dc
        use=changed[rr,cc]
        if np.any(use): rollback[rr[use],cc[use]]=True


def d8_witness_arrays_chunked(base, chunk_rows=128, check=None):
    """Build EV95 non-strict D8 center/witness pairs with bounded temporaries.

    Neighbor offsets are visited lexicographically and a strict improvement
    replaces the current witness, matching structured_operator.d8_witness_arrays.
    """
    b=np.asarray(base,dtype=np.float64)
    if b.ndim!=2 or min(b.shape,default=0)<1 or not np.isfinite(b).all():
        raise ValueError('base must be a finite nonempty grid')
    height,width=b.shape
    best=np.full((height,width),np.inf,dtype=np.float64)
    witness=np.full((height,width),-1,dtype=np.int64)
    offsets=[(dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if (dr,dc)!=(0,0)]
    for r0 in range(0,height,int(chunk_rows)):
        r1=min(height,r0+int(chunk_rows))
        for dr,dc in offsets:
            src0=max(0,r0+dr);src1=min(height,r1+dr)
            dst0=src0-dr;dst1=src1-dr
            c0=max(0,-dc);c1=min(width,width-dc)
            if src0>=src1 or c0>=c1: continue
            dest_r=slice(dst0,dst1); dest_c=slice(c0,c1)
            cand=b[src0:src1,c0+dc:c1+dc]
            cur=best[dest_r,dest_c]
            take=cand<cur
            if np.any(take):
                cur[take]=cand[take]
                rr=np.arange(dst0,dst1,dtype=np.int64)[:,None]
                cc=np.arange(c0,c1,dtype=np.int64)[None,:]
                ids=(rr+dr)*width+(cc+dc)
                wdst=witness[dest_r,dest_c]
                wdst[take]=ids[take]
        if check is not None: check('d8_witness_build',r0,r1)
    centers=np.flatnonzero((witness.ravel()>=0)&(b.ravel()>=best.ravel())).astype(np.int32)
    return centers,witness.ravel()[centers].astype(np.int32)


def rollback_d8(base, candidate, changed, rollback, centers, witnesses, chunk_rows=1_000_000, check=None):
    """Rollback changed endpoints of every failed EV95 minimum witness row."""
    b=np.asarray(base); h=np.asarray(candidate)
    flat=h.ravel(); c=np.asarray(centers,dtype=np.int32); w=np.asarray(witnesses,dtype=np.int32)
    if c.shape!=w.shape or c.ndim!=1: raise ValueError('D8 pair shape mismatch')
    ch=changed.ravel(); rb=rollback.ravel(); bad_total=0
    for s in range(0,len(c),int(chunk_rows)):
        e=min(len(c),s+int(chunk_rows));ci=c[s:e];wi=w[s:e]
        bad=flat[ci]<flat[wi];bad_total+=int(np.count_nonzero(bad))
        if np.any(bad):
            ci=ci[bad];wi=wi[bad]
            rb[ci[ch[ci]]]=True;rb[wi[ch[wi]]]=True
        if check is not None:check('d8_check',s,e)
    return {'bad_rows':bad_total,'rollback_vertices':int(np.count_nonzero(rollback))}


def _face_gradient_pair(h):
    """Return EV95's two raw-height gradients for a cell block in float64."""
    nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
    # Keep the prepared bounds producer's exact sqrt-of-squares operation;
    # np.hypot may round a boundary comparison differently by an ULP.
    g0=np.sqrt((ne-nw)**2+(ne-se)**2)
    g1=np.sqrt((se-sw)**2+(nw-sw)**2)
    return g0,g1


def rollback_face_cones(base, candidate, changed, rollback, radii, chunk_rows=128, check=None):
    """Rollback changed corners of cells whose any prepared triangle radius fails."""
    b=np.asarray(base); h=np.asarray(candidate)
    if b.shape!=h.shape or b.ndim!=2 or changed.shape!=b.shape or rollback.shape!=b.shape:
        raise ValueError('height/mask shape mismatch')
    nr,nc=b.shape[0]-1,b.shape[1]-1
    rad=np.asarray(radii,dtype=np.float64)
    if rad.size!=nr*nc*2 or not np.isfinite(rad).all(): raise ValueError('face radius shape/value mismatch')
    rad=rad.reshape(nr,nc,2)
    bad_total=0
    for r0 in range(0,nr,int(chunk_rows)):
        r1=min(nr,r0+int(chunk_rows))
        hb=h[r0:r1+1,:].astype(np.float64,copy=False)
        g0,g1=_face_gradient_pair(hb)
        bad=(g0>rad[r0:r1,:,0]) | (g1>rad[r0:r1,:,1])
        rr,cc=np.nonzero(bad)
        bad_total+=len(rr)
        if len(rr):
            rr=rr+r0
            _add_incident_nodes(rollback,changed,rr,cc,((0,0),(0,1),(1,0),(1,1)))
        if check is not None:check('face_cones',r0,r1)
    return {'bad_cells':int(bad_total),'rollback_vertices':int(np.count_nonzero(rollback))}


def _triangle_normals_rows(heights64):
    """EV87 triangle normals for a bounded block of grid rows; same operation order."""
    h=np.asarray(heights64,dtype=np.float64)
    nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
    one=np.ones_like(nw)
    a=np.cross(np.stack((6*one,ne-nw,np.zeros_like(nw)),axis=-1),
               np.stack((6*one,se-nw,-6*one),axis=-1))
    b=np.cross(np.stack((6*one,se-nw,-6*one),axis=-1),
               np.stack((np.zeros_like(nw),sw-nw,-6*one),axis=-1))
    a/=np.linalg.norm(a,axis=-1)[...,None]
    b/=np.linalg.norm(b,axis=-1)[...,None]
    return a,b


def _dihedral_degrees(x,y):
    return np.degrees(np.arctan2(np.linalg.norm(np.cross(x,y),axis=-1),np.einsum('ijk,ijk->ij',x,y)))


def rollback_new_hinges_over30(base, candidate, changed, rollback, chunk_rows=128, check=None):
    """Rollback four incident vertices for every newly >30-degree native hinge.

    Uses EV87's NW-SE triangle normals and diag/vertical/horizontal pairings.
    The cell-row chunk carries one following normal row for horizontal hinges;
    no full-map normal or angle families are materialized.
    """
    b=np.asarray(base); h=np.asarray(candidate)
    if b.shape!=h.shape or b.ndim!=2 or changed.shape!=b.shape or rollback.shape!=b.shape:
        raise ValueError('height/mask shape mismatch')
    ncellrows=b.shape[0]-1; total={'diag':0,'vertical':0,'horizontal':0}
    diag_offsets=((0,0),(0,1),(1,0),(1,1))
    vert_offsets=((0,0),(0,1),(1,1),(1,2))
    horiz_offsets=((0,0),(1,0),(1,1),(2,1))
    for r0 in range(0,ncellrows,int(chunk_rows)):
        r1=min(ncellrows,r0+int(chunk_rows))
        row_stop=min(b.shape[0],r1+2)
        ba,bb=_triangle_normals_rows(b[r0:row_stop,:].astype(np.float64,copy=False))
        ha,hb=_triangle_normals_rows(h[r0:row_stop,:].astype(np.float64,copy=False))
        n=r1-r0
        # Diagonal hinges within these cell rows.
        m=(
            (_dihedral_degrees(ba[:n],bb[:n])<=30.0) &
            (_dihedral_degrees(ha[:n],hb[:n])>30.0)
        )
        rr,cc=np.nonzero(m)
        total['diag']+=len(rr)
        if len(rr): _add_incident_nodes(rollback,changed,rr+r0,cc,diag_offsets)
        # Vertical grid edges join A of the left cell to B of the right cell.
        if b.shape[1]>=3:
            m=(
                (_dihedral_degrees(ba[:n,:-1],bb[:n,1:])<=30.0) &
                (_dihedral_degrees(ha[:n,:-1],hb[:n,1:])>30.0)
            )
            rr,cc=np.nonzero(m)
            total['vertical']+=len(rr)
            if len(rr): _add_incident_nodes(rollback,changed,rr+r0,cc,vert_offsets)
        # Horizontal edges join B of an upper cell to A of the lower cell.
        q=min(n,max(0,ba.shape[0]-1))
        if q:
            m=(
                (_dihedral_degrees(bb[:q],ba[1:q+1])<=30.0) &
                (_dihedral_degrees(hb[:q],ha[1:q+1])>30.0)
            )
            rr,cc=np.nonzero(m)
            total['horizontal']+=len(rr)
            if len(rr): _add_incident_nodes(rollback,changed,rr+r0,cc,horiz_offsets)
        if check is not None:check('native_hinges',r0,r1)
    total['new_over30_total']=sum(total.values())
    total['rollback_vertices']=int(np.count_nonzero(rollback))
    return total


def rollback_round(base, candidate, centers, witnesses, radii, chunk_rows=128, check=None):
    """Apply one monotonic rollback pass; return candidate and measured failures."""
    b=np.asarray(base); h=np.asarray(candidate)
    if b.shape!=h.shape or b.ndim!=2: raise ValueError('base/candidate shape mismatch')
    changed=h!=b
    rollback=np.zeros(b.shape,dtype=np.bool_)
    d8=rollback_d8(b,h,changed,rollback,centers,witnesses,check=check)
    face=rollback_face_cones(b,h,changed,rollback,radii,chunk_rows,check)
    hinge=rollback_new_hinges_over30(b,h,changed,rollback,chunk_rows,check)
    failures={'d8_bad_rows':d8['bad_rows'],'face_bad_cells':face['bad_cells'],
              'new_over30':hinge['new_over30_total'],
              'new_over30_by_family':{k:hinge[k] for k in ('diag','vertical','horizontal')}}
    if not (failures['d8_bad_rows'] or failures['face_bad_cells'] or failures['new_over30']):
        return h,changed,failures
    if not np.any(rollback):
        raise RuntimeError('failing constraint has no changed incident vertex')
    before=int(np.count_nonzero(changed))
    h[rollback]=b[rollback]
    after=int(np.count_nonzero(h!=b))
    if after>=before: raise RuntimeError('rollback did not strictly reduce changed-node count')
    failures.update({'rolled_back_vertices':before-after,'changed_before':before,'changed_after':after})
    return h,h!=b,failures


def direct_strict_minima(heights):
    """Interior 8-neighbor strict minima mask, used only for final cross-checks."""
    h=np.asarray(heights)
    if h.ndim!=2: raise ValueError('heights must be 2D')
    center=h[1:-1,1:-1]
    neighbors=(h[:-2,:-2],h[:-2,1:-1],h[:-2,2:],h[1:-1,:-2],
               h[1:-1,2:],h[2:,:-2],h[2:,1:-1],h[2:,2:])
    return np.logical_and.reduce([center<n for n in neighbors])
