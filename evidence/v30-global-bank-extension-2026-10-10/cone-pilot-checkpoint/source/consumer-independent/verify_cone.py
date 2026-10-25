"""Independent synthetic face-slope-cone consumer; never imports pilot.py.

The verifier rebuilds EV88 rows, D8 witnesses, affine native face gradients,
and native coordinate normals. It is intentionally read-only with respect to
the pilot artifacts. No solver or map build is run by this module.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import tempfile
import time
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent
PROTO = PILOT.parent / "prototype.py"
SOLVER_REF = PILOT.parent / "admm-quantized-pilot" / "solve.py"
EV87 = Path(r"E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py")
PLAN = PILOT / "PLAN.md"
PREFLIGHT_DIR = PILOT / "preflight-recheck-01"
PREFLIGHT = PREFLIGHT_DIR / "preflight.json"
PREPARED = PREFLIGHT_DIR / "prepared.npz"
PREFLIGHT_PLAN = PREFLIGHT_DIR / "PLAN.md"
PREFLIGHT_PILOT = PREFLIGHT_DIR / "pilot.py"
ORDER_CLOSURE = PILOT.parent / "real-sector-preflight" / "order-closure" / "projection.py"
DEFAULT_RUN = PREFLIGHT_DIR / "solve-once"
SHAPE = (64, 128)
RHO0 = 1.0
ABS_TOL = 1e-10
REL_TOL = 1e-8
EXPECTED_FACE_KEY = (32, 63, 0)
STATIC_SOURCE_PINS = {
    str(PROTO): "5b4b8f08e5205e1f9cc90bcc8e82e61dade45bb82bd22da8ee69303aa4475cc4",
    str(SOLVER_REF): "7e8636bf54ba23f7e23bc2f06464100439468da7b4edca85f96c72d0cd40e149",
    str(EV87): "964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27",
    str(PILOT.parent / "real-sector-preflight" / "order-closure" / "projection.py"):
        "a990dc2d33fca4fd2a446b958f0412a2d752a5d3072a85d82058bb634cfaf44b",
    str(PREFLIGHT_PLAN): "0558ad350e578903c09ce1488071af8fe09a661ac87ee7f51883e1dcd0c4a94e",
    str(PILOT / "pilot.py"): "d743f5006e0aa6606024a3c3291a74cb52b78f76c1aa5c6dfd95cdd26cdc9d2a",
}


def sha256(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_pinned_order_closure():
    expected=STATIC_SOURCE_PINS[str(ORDER_CLOSURE)]
    if sha256(ORDER_CLOSURE)!=expected:
        raise ValueError("pinned order-closure source hash mismatch")
    spec=importlib.util.spec_from_file_location("pinned_order_closure_fixture",ORDER_CLOSURE)
    if spec is None or spec.loader is None: raise ImportError("cannot load pinned order-closure API")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    if not callable(getattr(module,"project_order",None)) or not callable(getattr(module,"evaluate_objective_gates",None)):
        raise ImportError("pinned order-closure API signature surface missing")
    return module


def _csr_equal(a: sparse.csr_matrix, b: sparse.csr_matrix, atol: float = 0.0) -> bool:
    if a.shape != b.shape:
        return False
    d = (a - b).tocsr()
    d.eliminate_zeros()
    return d.nnz == 0 if atol == 0 else (not d.nnz or float(np.max(np.abs(d.data))) <= atol)


def ev88_coeffs(kind: str, r: int, c: int):
    if kind == "xx":
        return ((r, c, 1.0), (r, c + 1, -2.0), (r, c + 2, 1.0))
    if kind == "zz":
        return ((r, c, 1.0), (r + 1, c, -2.0), (r + 2, c, 1.0))
    if kind == "xz":
        return ((r, c, -0.25), (r, c + 2, 0.25),
                (r + 2, c, 0.25), (r + 2, c + 2, -0.25))
    raise ValueError(kind)


def enumerate_stencils(shape, variables):
    h, w = map(int, shape)
    vset = set(map(tuple, np.asarray(variables, dtype=np.int32).tolist()))
    out = []
    for r in range(h):
        for c in range(w - 2):
            if any((rr, cc) in vset for rr, cc, _ in ev88_coeffs("xx", r, c)):
                out.append(("xx", r, c))
    for r in range(h - 2):
        for c in range(w):
            if any((rr, cc) in vset for rr, cc, _ in ev88_coeffs("zz", r, c)):
                out.append(("zz", r, c))
    for r in range(h - 2):
        for c in range(w - 2):
            if any((rr, cc) in vset for rr, cc, _ in ev88_coeffs("xz", r, c)):
                out.append(("xz", r, c))
    return out


def build_objective_independent(base, variables):
    """Rebuild EV88 rows from the published functional, not prepared A/rhs."""
    b = np.asarray(base, dtype=np.float64)
    nodes = np.asarray(variables, dtype=np.int32)
    index = {tuple(map(int, rc)): i for i, rc in enumerate(nodes.tolist())}
    stencils = enumerate_stencils(b.shape, nodes)
    records = []
    for kind, r, c in stencils:
        scale = math.sqrt(2.0) if kind == "xz" else 1.0
        entries, fixed = [], 0.0
        for rr, cc, coeff in ev88_coeffs(kind, r, c):
            value = coeff * scale
            j = index.get((rr, cc))
            if j is None:
                fixed += value * float(b[rr, cc])
            else:
                entries.append((j, value))
        records.append((entries, -fixed, (kind, r, c)))
    for j, (r, c) in enumerate(nodes.tolist()):
        records.append(([(j, 0.25)], 0.25 * float(b[r, c]), ("fidelity", r, c)))
    rr, cc, vv = [], [], []
    rhs = np.empty(len(records), np.float64)
    for i, (entries, target, _key) in enumerate(records):
        rhs[i] = target
        for j, value in entries:
            rr.append(i); cc.append(j); vv.append(value)
    A = sparse.csr_matrix((np.asarray(vv, np.float64),
                           (np.asarray(rr, np.int32), np.asarray(cc, np.int32))),
                          shape=(len(records), len(nodes)))
    A.sort_indices()
    return A, rhs, stencils, records


def scalar_objective_independent(base, candidate, variables):
    """Direct full-grid EV88 residual evaluation, independent of the CSR rows."""
    b = np.asarray(base, dtype=np.float64)
    h = np.asarray(candidate, dtype=np.float64)
    nodes = np.asarray(variables, dtype=np.int32)
    terms = []
    vset = set(map(tuple, np.asarray(variables, dtype=np.int32).tolist()))
    nr, nc = h.shape
    for r in range(nr):
        for c in range(nc - 2):
            if any((q[0], q[1]) in vset for q in ev88_coeffs("xx", r, c)):
                terms.append(h[r, c] - 2 * h[r, c + 1] + h[r, c + 2])
    for r in range(nr - 2):
        for c in range(nc):
            if any((q[0], q[1]) in vset for q in ev88_coeffs("zz", r, c)):
                terms.append(h[r, c] - 2 * h[r + 1, c] + h[r + 2, c])
    rt2 = math.sqrt(2.0)
    for r in range(nr - 2):
        for c in range(nc - 2):
            if any((q[0], q[1]) in vset for q in ev88_coeffs("xz", r, c)):
                terms.append(rt2 * (-0.25*h[r,c] + 0.25*h[r,c+2] +
                                    0.25*h[r+2,c] - 0.25*h[r+2,c+2]))
    return 0.5 * (math.fsum(float(v)*float(v) for v in terms) +
                  math.fsum((0.25 * (float(h[r,c])-float(b[r,c])))**2 for r,c in nodes.tolist()))


def rebuild_witnesses(base):
    b = np.asarray(base, dtype=np.float32)
    h, w = b.shape
    witnesses, strict_minima = [], []
    for r in range(h):
        for c in range(w):
            neighbors = [(rr, cc) for rr in range(max(0, r-1), min(h, r+2))
                         for cc in range(max(0, c-1), min(w, c+2)) if (rr,cc)!=(r,c)]
            if not neighbors:
                continue
            value = float(b[r,c])
            low = min(float(b[rr,cc]) for rr,cc in neighbors)
            if value < low:
                strict_minima.append((r,c))
            else:
                # Exact deterministic tie break: lexicographically first lowest neighbor.
                witness = min((rr,cc) for rr,cc in neighbors if float(b[rr,cc]) == low)
                witnesses.append(((r,c), witness))
    return witnesses, np.asarray(strict_minima, np.int32).reshape((-1,2))


def expected_synthetic_baseline():
    """Independent literal reconstruction of the current PLAN synthetic field."""
    nr,nc=SHAPE
    r,c=np.indices(SHAPE,dtype=np.float64)
    source=100.0+0.004*r+0.003*c+0.000025*c*c+1.2*np.exp(-((c-nc*.52)/(nc*.06))**2)
    B=(source-100.0+2.0).astype(np.float32)
    rr,cc=np.indices((7,7),dtype=np.float64)
    B[30:37,61:68]=(2.3-0.3*((rr-3)+(cc-3))).astype(np.float32)
    B[32,63]=np.float32(7.2344970703125)
    B[32,64]=np.float32(3.1139774322509766)
    B[33,64]=np.float32(2.2943551540374756)
    B[33,63]=np.float32(1.95)
    protected=np.zeros(SHAPE,bool)
    protected[:,18:21]=True
    protected[12:17,25:32]=True
    protected[32,63]=True;protected[32,64]=True
    return B,protected


def build_d8_independent(base, variables, witnesses):
    nodes = np.asarray(variables, np.int32)
    index = {tuple(map(int, rc)): i for i, rc in enumerate(nodes.tolist())}
    rr, cc, vv = [], [], []
    d = np.empty(len(witnesses), np.float64)
    for row, (center, witness) in enumerate(witnesses):
        offset = 0.0
        for rc, coef in ((center, 1.0), (witness, -1.0)):
            idx = index.get(tuple(rc))
            if idx is None:
                offset += coef * float(base[tuple(rc)])
            else:
                rr.append(row); cc.append(idx); vv.append(coef)
        d[row] = -offset
    C = sparse.csr_matrix((np.asarray(vv, np.float64),
                           (np.asarray(rr, np.int32), np.asarray(cc, np.int32))),
                          shape=(len(witnesses), len(nodes)))
    C.sort_indices()
    return C, d


def native_face_gradients(height):
    """Physical (dH/dx,dH/dz) per face; x=6c and z=-6r."""
    h = np.asarray(height, dtype=np.float64)
    nw, ne, sw, se = h[:-1,:-1], h[:-1,1:], h[1:,:-1], h[1:,1:]
    q = np.empty((h.shape[0]-1, h.shape[1]-1, 2, 2), np.float64)
    q[:,:,0,0] = ne - nw
    q[:,:,0,1] = ne - se
    q[:,:,1,0] = se - sw
    q[:,:,1,1] = nw - sw
    return q


def native_normal_slopes(height):
    """Compute slopes from 3-D triangle normals, not from a saved gradient/G."""
    h = np.asarray(height, dtype=np.float64)
    nr, nc = h.shape
    slopes = np.empty((nr-1, nc-1, 2), np.float64)
    normals = np.empty((nr-1, nc-1, 2, 3), np.float64)
    for r in range(nr-1):
        z0, z1 = -6.0*r, -6.0*(r+1)
        for c in range(nc-1):
            x0, x1 = 6.0*c, 6.0*(c+1)
            nw=np.array((x0,h[r,c],z0)); ne=np.array((x1,h[r,c+1],z0))
            sw=np.array((x0,h[r+1,c],z1)); se=np.array((x1,h[r+1,c+1],z1))
            # Native terrain diagonal is NW-SE: (NW,NE,SE) and (NW,SE,SW).
            for kind, pts in ((0,(nw,ne,se)),(1,(nw,se,sw))):
                n=np.cross(pts[1]-pts[0],pts[2]-pts[0])
                length=float(np.linalg.norm(n))
                if not math.isfinite(length) or length == 0.0:
                    raise ValueError(f"degenerate native triangle at {(r,c,kind)}")
                normals[r,c,kind]=n/length
                slopes[r,c,kind]=math.degrees(math.atan2(
                    math.hypot(float(n[0]),float(n[2])),abs(float(n[1]))))
    return normals, slopes


def build_face_operator_independent(base, variables):
    b=np.asarray(base,dtype=np.float64); nodes=np.asarray(variables,np.int32)
    index={tuple(map(int,rc)):i for i,rc in enumerate(nodes.tolist())}
    nfaces=2*(b.shape[0]-1)*(b.shape[1]-1)
    rows=[]; cols=[]; vals=[]; k=np.zeros((nfaces,2),np.float64)
    qB=native_face_gradients(b).reshape((-1,2))
    keys=np.empty((nfaces,3),np.int32); radii=np.empty(nfaces,np.float64)
    row=0
    face_terms=[]
    for r in range(b.shape[0]-1):
        for c in range(b.shape[1]-1):
            for kind in (0,1):
                if kind==0:
                    comp=(((r,c+1,1.),(r,c,-1.)),((r,c+1,1.),(r+1,c+1,-1.)))
                else:
                    comp=(((r+1,c+1,1.),(r+1,c,-1.)),((r,c,1.),(r+1,c,-1.)))
                face_terms.append(comp)
                keys[row]=(r,c,kind)
                for j, terms in enumerate(comp):
                    fixed=0.0
                    for rr0,cc0,coef in terms:
                        ix=index.get((rr0,cc0))
                        if ix is None: fixed+=coef*float(b[rr0,cc0])
                        else: rows.append(2*row+j);cols.append(ix);vals.append(coef)
                    k[row,j]=fixed
                radii[row]=max(6*math.tan(math.radians(35.0)),float(np.linalg.norm(qB[row])))
                row+=1
    G=sparse.csr_matrix((np.asarray(vals,np.float64),(np.asarray(rows,np.int32),np.asarray(cols,np.int32))),
                        shape=(2*nfaces,len(nodes)))
    G.sort_indices()
    return G,k.reshape(-1),radii,keys,qB,face_terms


def minima_mask_interior(height):
    a=np.asarray(height)
    if min(a.shape)<3: return np.zeros((0,0),bool)
    mid=a[1:-1,1:-1]; mask=np.ones(mid.shape,bool)
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if dr or dc:
                mask &= mid < a[1+dr:a.shape[0]-1+dr,1+dc:a.shape[1]-1+dc]
    return mask


def project_discs_independent(q,radii):
    v=np.asarray(q,dtype=np.float64).reshape((-1,2)); R=np.asarray(radii,dtype=np.float64)
    norms=np.linalg.norm(v,axis=1); out=v.copy(); mask=norms>R
    out[mask]*=(R[mask]/norms[mask])[:,None]
    return out.reshape(np.asarray(q).shape)


def project_order_independent(raw, lower, upper, edges):
    raw=np.asarray(raw);lo=np.asarray(lower);hi=np.asarray(upper)
    if raw.dtype!=np.float32 or lo.dtype!=np.float32 or hi.dtype!=np.float32 or raw.ndim!=2 or lo.shape!=raw.shape or hi.shape!=raw.shape:
        raise ValueError("closure inputs must be matching float32 rasters")
    if not (np.isfinite(raw).all() and np.isfinite(lo).all() and np.isfinite(hi).all()) or np.any(lo>hi):
        raise ValueError("invalid order-closure raster/bounds")
    e=np.asarray(edges)
    if e.ndim!=2 or e.shape[1]!=4 or e.dtype.kind not in "iu": raise ValueError("bad witness edge schema")
    e=e.astype(np.int32,copy=False);nr,nc=raw.shape
    if len(e) and (np.any(e[:,(0,2)]<0) or np.any(e[:,(0,2)]>=nr) or np.any(e[:,(1,3)]<0) or np.any(e[:,(1,3)]>=nc)):
        raise ValueError("witness edge outside raster")
    if len(e) and (np.any(np.max(np.abs(e[:,:2]-e[:,2:]),axis=1)>1) or np.any(np.all(e[:,:2]==e[:,2:],axis=1))):
        raise ValueError("witness edge is not a distinct D8 pair")
    if len({tuple(row) for row in e.tolist()})!=len(e): raise ValueError("duplicate witness edge")
    U=hi.copy()
    for _ in range(raw.size+1):
        nxt=U.copy()
        if len(e): np.minimum.at(nxt,(e[:,2],e[:,3]),U[e[:,0],e[:,1]])
        if np.array_equal(nxt,U): break
        U=nxt
    else: raise RuntimeError("upper order propagation did not converge")
    if np.any(lo>U): raise ValueError("order bounds infeasible")
    r=np.minimum(np.maximum(raw,lo),U).astype(np.float32,copy=False)
    violations=np.maximum(0.0,r[e[:,2],e[:,3]].astype(np.float64)-r[e[:,0],e[:,1]].astype(np.float64)) if len(e) else np.empty(0)
    V=math.fsum(map(float,violations))
    q=r.copy()
    for _ in range(raw.size+1):
        nxt=q.copy()
        if len(e): np.maximum.at(nxt,(e[:,0],e[:,1]),q[e[:,2],e[:,3]])
        if np.array_equal(nxt,q): break
        q=nxt
    else: raise RuntimeError("forward order closure did not converge")
    if np.any(q<lo) or np.any(q>hi): raise AssertionError("closure escaped box")
    if len(e) and np.any(q[e[:,0],e[:,1]]<q[e[:,2],e[:,3]]): raise AssertionError("closure left D8 violation")
    b=float(np.max(np.abs(r.astype(np.float64)-raw.astype(np.float64)),initial=0.0))
    corr=float(np.max(np.abs(q.astype(np.float64)-raw.astype(np.float64)),initial=0.0))
    return {"upper_propagated":U,"clipped_float32":r,"closed_float32":q,
            "b":b,"V":V,"b_plus_V":b+V,"max_abs_correction":corr,
            "correction_bound_pass":bool(corr<=b+V)}


def closure_objectives(A,rhs,x0,raw,closed):
    def cost(x):
        residual=A@np.asarray(x,np.float64)-rhs
        return 0.5*float(residual@residual)
    c_raw,c_closed,c_B=cost(raw),cost(closed),cost(x0)
    allowed=1e-7*max(1.0,c_raw)
    return {"raw":c_raw,"closed":c_closed,"B":c_B,"delta":c_closed-c_raw,
            "allowed_delta":allowed,"closure_objective_pass":bool(c_closed-c_raw<=allowed),
            "closed_below_B":bool(c_closed<c_B)}


def self_fixtures():
    # Native coordinate normals independently recover planar slopes.
    h=np.fromfunction(lambda r,c: 3.0+0.5*(6*c)-0.25*(-6*r),(4,5),dtype=float).astype(np.float32)
    n,s=native_normal_slopes(h)
    assert np.max(np.abs(s-math.degrees(math.atan(math.hypot(.5,.25)))))<1e-10
    q=native_face_gradients(h)
    assert np.max(np.abs(np.linalg.norm(q,axis=-1)-6*math.hypot(.5,.25)))<2e-6
    # The face-affine operator agrees with the independently built native q.
    nodes=np.column_stack(np.nonzero(np.ones((4,5),bool))).astype(np.int32)
    G,k,R,keys,qB,terms=build_face_operator_independent(h,nodes)
    x=h[tuple(nodes.T)].astype(np.float64)
    got=(G@x+k).reshape((-1,2))
    assert np.max(np.abs(got-q.reshape((-1,2))))<1e-12
    assert np.array_equal(keys[:2],np.asarray([[0,0,0],[0,0,1]],np.int32))
    # Reconstructed EV88 sparse objective agrees with a direct full-grid functional.
    rr,cc=np.indices((7,8),dtype=np.float64)
    base=(2.0+0.125*rr+0.25*cc+0.03125*cc*cc).astype(np.float32)
    variables=np.column_stack(np.nonzero(np.ones(base.shape,bool))).astype(np.int32)
    A,rhs,stencils,_records=build_objective_independent(base,variables)
    trial=base.copy();trial[2,3]=np.float32(trial[2,3]+0.375);trial[4,5]=np.float32(trial[4,5]-0.25)
    direct=scalar_objective_independent(base,trial,variables)
    sparse_cost=.5*float((A@trial[tuple(variables.T)].astype(np.float64)-rhs) @
                         (A@trial[tuple(variables.T)].astype(np.float64)-rhs))
    assert abs(direct-sparse_cost)<1e-11*max(1.,direct)
    # SOC normal-cone positive/negative controls.
    rad=np.array([1.0,1.0]); z=np.array([[1.0,0.0],[0.0,0.0]])
    ygood=np.array([[2.0,0.0],[0.0,0.0]])
    ybad=np.array([[-2.0,0.0],[0.1,0.0]])
    assert np.max(np.abs(z-project_discs_independent(z+ygood,rad)))==0.0
    assert np.max(np.abs(z-project_discs_independent(z+ybad,rad)))>0.0
    good_kkt=_face_kkt(z.reshape(-1),ygood.reshape(-1),rad,2.0,1e-10,1e-10)
    bad_kkt=_face_kkt(z.reshape(-1),ybad.reshape(-1),rad,2.0,1e-10,1e-10)
    assert good_kkt["negative_multiplier_max"]==0.0 and good_kkt["interior_dual_max"]==0.0
    assert bad_kkt["negative_multiplier_max"]>0.0 or bad_kkt["interior_dual_max"]>0.0
    # Float32 direct cast is not silently repaired; closure fixture is exact.
    raw=np.asarray([[3.,1.,2.]],np.float32); lo=np.zeros_like(raw);hi=np.full_like(raw,4.)
    edges=np.asarray([[0,1,0,0],[0,2,0,1]],np.int32)
    cl=project_order_independent(raw,lo,hi,edges)
    assert np.array_equal(cl["closed_float32"],np.asarray([[3.,3.,3.]],np.float32))
    assert cl["max_abs_correction"]<=cl["b_plus_V"]
    pinned=load_pinned_order_closure()
    pinned_edges=np.asarray([[0,0,0,1],[0,1,0,2]],np.int32).reshape((-1,2))
    pinned_result=pinned.project_order(raw.reshape(-1),lo.reshape(-1),hi.reshape(-1),pinned_edges)
    assert np.array_equal(pinned_result["q"].reshape(raw.shape),cl["closed_float32"])
    assert np.array_equal(pinned_result["clipped"].reshape(raw.shape),cl["clipped_float32"])
    assert np.array_equal(pinned_result["upper_propagated"].reshape(raw.shape),cl["upper_propagated"])
    # Compatible cycle closes deterministically; fixed values remain exact.
    cyc=project_order_independent(np.asarray([[1.,2.]],np.float32),np.zeros((1,2),np.float32),
                                  np.full((1,2),3.,np.float32),
                                  np.asarray([[0,1,0,0],[0,0,0,1]],np.int32))
    assert np.array_equal(cyc["closed_float32"],np.asarray([[2.,2.]],np.float32))
    fixed=project_order_independent(np.asarray([[4.,1.,2.]],np.float32),
                                    np.asarray([[0.,0.,2.]],np.float32),
                                    np.asarray([[4.,4.,2.]],np.float32),edges)
    assert np.array_equal(fixed["closed_float32"],np.asarray([[2.,2.,2.]],np.float32))
    # A fixed high witness infeasible with a lower center must reject.
    try:
        project_order_independent(np.asarray([[1.,0.]],np.float32),
                                  np.asarray([[1.,0.]],np.float32),
                                  np.asarray([[1.,0.]],np.float32),
                                  np.asarray([[0,1,0,0]],np.int32))
    except ValueError: pass
    else: raise AssertionError("infeasible fixed/order constraint was accepted")
    # Strict-minimum detector notices a new pit.
    b=np.full((5,5),2.,np.float32); h2=b.copy(); h2[2,2]=1.
    assert np.count_nonzero(minima_mask_interior(h2)&~minima_mask_interior(b))==1
    flat_grid=np.arange(6,dtype=np.float32)
    assert np.array_equal(_reshape_serialized_flat_grid(flat_grid,(2,3),"fixture"),flat_grid.reshape(2,3))
    for malformed in (np.arange(5,dtype=np.float32),np.arange(6,dtype=np.float64)):
        try: _reshape_serialized_flat_grid(malformed,(2,3),"fixture")
        except ValueError: pass
        else: raise AssertionError("malformed flat-grid serialization was accepted")
    face_fixture=np.arange(12,dtype=np.float64).reshape((2,3,2))
    assert np.array_equal(_require_array({"faces":face_fixture},"faces",np.float64,(2,3,2)),face_fixture)
    try: _require_array({"faces":face_fixture.reshape(-1)},"faces",np.float64,(2,3,2))
    except ValueError: pass
    else: raise AssertionError("malformed face-angle shape was accepted")
    return {"status":"PASS","native_normal_planar_slope":True,"face_operator_matches_native":True,
            "ev88_scalar_vs_sparse_objective":True,"soc_positive_negative_kkt":True,
            "order_closure_chain_cycle_fixed":True,"pinned_order_closure_api_agrees":True,
            "infeasible_order_rejected":True,
            "new_strict_minimum_detected":True,"flat_closure_grid_schema_positive_negative":True,
            "face_angle_grid_schema_positive_negative":True}


def _load_npz(path):
    with np.load(path,allow_pickle=False) as z:
        return {k:z[k].copy() for k in z.files}


def _reshape_serialized_flat_grid(value, shape, name):
    """Decode the author's explicitly flattened float32 closure rasters."""
    a=np.asarray(value)
    target=tuple(map(int,shape))
    if a.dtype!=np.dtype(np.float32) or a.ndim!=1 or a.size!=int(np.prod(target)):
        raise ValueError(f"{name} must be a flat float32 vector of exactly {int(np.prod(target))} cells")
    return a.reshape(target)


def _require_array(data, name, dtype, shape):
    a=np.asarray(data[name])
    target=tuple(map(int,shape))
    if a.dtype!=np.dtype(dtype) or a.shape!=target:
        raise ValueError(f"{name} must have dtype {np.dtype(dtype)} and shape {target}; got {a.dtype} {a.shape}")
    return a


def _prepared_matrices(data):
    A=sparse.csr_matrix((data["A_data"],data["A_indices"],data["A_indptr"]),shape=tuple(map(int,data["A_shape"])))
    C=sparse.csr_matrix((data["C_data"],data["C_indices"],data["C_indptr"]),shape=tuple(map(int,data["C_shape"])))
    G=sparse.csr_matrix((data["G_data"],data["G_indices"],data["G_indptr"]),shape=tuple(map(int,data["G_shape"])))
    return A,C,G


def verify_preflight(preflight_path=PREFLIGHT, prepared_path=PREPARED):
    """Validate a fresh preflight without running or importing the author."""
    started=time.time(); report=json.loads(Path(preflight_path).read_text(encoding="utf-8-sig"))
    if report.get("status")!="PREFLIGHT_PASS_NO_SOLVE" or report.get("solve_executed") is not False:
        raise ValueError("preflight status/schema not eligible")
    if report.get("scope")!="SYNTHETIC_ONLY_64x128_NO_REAL_BASE_OR_TERRAIN_CANDIDATE":
        raise ValueError("preflight scope is not the pinned synthetic-only unit")
    if sha256(prepared_path)!=report.get("prepared_sha256"):
        raise ValueError("prepared.npz hash does not match preflight")
    pins=report.get("source_pins_start")
    if not isinstance(pins,dict) or pins!=report.get("source_pins_end"):
        raise ValueError("preflight source pins are incomplete or changed")
    expected_sources=set(STATIC_SOURCE_PINS)
    if set(pins)!=expected_sources: raise ValueError("preflight source set is not the exact six-source contract")
    for p,expected in STATIC_SOURCE_PINS.items():
        if pins.get(p)!=expected: raise ValueError(f"unexpected pinned source version: {p}")
    if sha256(PLAN)!=STATIC_SOURCE_PINS[str(PREFLIGHT_PLAN)]:
        raise ValueError("canonical PLAN differs from preflight snapshot")
    if sha256(PILOT/"pilot.py")!=STATIC_SOURCE_PINS[str(PILOT/"pilot.py")]:
        raise ValueError("canonical pilot.py differs from pinned source")
    if report.get("sources_unchanged") is not True or report.get("preflight_pass") is not True:
        raise ValueError("preflight self-status is not eligible")
    closure_identity=report.get("float32_order_closure_identity",{})
    if (closure_identity.get("source_path")!=str(ORDER_CLOSURE) or
        closure_identity.get("source_sha256")!=STATIC_SOURCE_PINS[str(ORDER_CLOSURE)] or
        closure_identity.get("identity_pass") is not True or
        closure_identity.get("edge_direction")!="(witness,center)"):
        raise ValueError("preflight order-closure identity fixture is absent or mismatched")
    for p,expected in pins.items():
        if sha256(p)!=expected: raise ValueError(f"preflight source drift: {p}")
    d=_load_npz(prepared_path)
    B32=d["baseline_float32"]
    if B32.dtype!=np.float32 or B32.shape!=SHAPE or not np.isfinite(B32).all():
        raise ValueError("baseline float32 invalid")
    B=B32.astype(np.float64)
    protected=np.asarray(d["protected"],bool)
    nodes=np.asarray(d["variables_rc"],np.int32)
    if protected.shape!=SHAPE or nodes.ndim!=2 or nodes.shape[1]!=2: raise ValueError("bad protected/variable schema")
    expected_B,expected_protected=expected_synthetic_baseline()
    if not np.array_equal(B32,expected_B): raise ValueError("synthetic baseline differs from independent PLAN reconstruction")
    if not np.array_equal(protected,expected_protected): raise ValueError("protected layout differs from independent synthetic fixture")
    expected_nodes=np.column_stack(np.nonzero(~protected)).astype(np.int32)
    if not np.array_equal(nodes,expected_nodes): raise ValueError("variables are not exactly the unprotected raster")
    # Rebuild EV88 A/rhs independently and compare sparse contents.
    A,rhs,stencils,records=build_objective_independent(B,nodes)
    savedA=sparse.csr_matrix((d["A_data"],d["A_indices"],d["A_indptr"]),shape=tuple(map(int,d["A_shape"])))
    if not _csr_equal(A,savedA) or not np.array_equal(rhs,d["rhs"]): raise ValueError("prepared EV88 objective differs from independent rebuild")
    try: saved_stencils=json.loads(d["stencils_json"].tobytes().decode("utf-8"))
    except Exception as exc: raise ValueError(f"invalid stencil ledger: {exc}")
    if saved_stencils!=[list(s) for s in stencils]: raise ValueError("stencil list differs from independent enumeration")
    varset=set(map(tuple,nodes.tolist()));cross_stencils=0
    for kind,r,c in stencils:
        if kind=="fidelity": continue
        free_cols=[cc for rr,cc,_coef in ev88_coeffs(kind,r,c) if (rr,cc) in varset]
        if any(c0<64 for c0 in free_cols) and any(c0>=64 for c0 in free_cols): cross_stencils+=1
    if cross_stencils==0: raise ValueError("no EV88 stencil couples free variables across the synthetic sector seam")
    # Rebuild deterministic D8 witness set and matrix.
    witnesses,strict_minima=rebuild_witnesses(B32)
    if not np.array_equal(d["witness_centers_rc"],np.asarray([w[0] for w in witnesses],np.int32)):
        raise ValueError("D8 center sequence mismatch")
    if not np.array_equal(d["witness_neighbors_rc"],np.asarray([w[1] for w in witnesses],np.int32)):
        raise ValueError("D8 witness sequence mismatch")
    if not np.array_equal(d["d8_exempt_strict_minima_rc"],strict_minima): raise ValueError("strict-minimum exception set mismatch")
    C,drhs=build_d8_independent(B,nodes,witnesses)
    savedC=sparse.csr_matrix((d["C_data"],d["C_indices"],d["C_indptr"]),shape=tuple(map(int,d["C_shape"])))
    if not _csr_equal(C,savedC) or not np.array_equal(drhs,d["d8_rhs"]): raise ValueError("prepared D8 rows differ from independent rebuild")
    # Rebuild native gradients, affine G and baseline-safe disc radii.
    G,k,radii,face_keys,qB,face_terms=build_face_operator_independent(B,nodes)
    savedG=sparse.csr_matrix((d["G_data"],d["G_indices"],d["G_indptr"]),shape=tuple(map(int,d["G_shape"])))
    if not _csr_equal(G,savedG) or not np.array_equal(k,d["face_offset_k"]): raise ValueError("prepared face operator differs from independent native-gradient rebuild")
    if not np.array_equal(radii,d["face_radii"]) or not np.array_equal(face_keys,d["face_keys_rc_kind"]): raise ValueError("face radii/key order mismatch")
    if not np.array_equal(qB,d["face_gradients_B"]): raise ValueError("baseline native gradients mismatch")
    baseline_disc_excess=float(np.max(np.linalg.norm(qB,axis=1)-radii,initial=-np.inf))
    if baseline_disc_excess>0.0: raise ValueError("baseline is outside at least one exact face disc")
    normalB,nativeB=native_normal_slopes(B32)
    slope_q=np.degrees(np.arctan2(np.linalg.norm(qB,axis=1)/6.,1.))
    if np.max(np.abs(slope_q-nativeB.reshape(-1)),initial=0.)>1e-10: raise ValueError("native normal and affine gradient slopes disagree")
    x0=B[tuple(nodes.T)]
    lo=np.asarray(d["lower_float32"],np.float32); hi=np.asarray(d["upper_float32"],np.float32)
    expect_lo=np.array([_inward32(float(v)-.5,True) for v in x0],np.float32)
    expect_hi=np.array([_inward32(float(v)+.5,False) for v in x0],np.float32)
    if not np.array_equal(lo,expect_lo) or not np.array_equal(hi,expect_hi): raise ValueError("box bounds do not match inward float32 baseline +/- 0.5")
    if np.any(x0<lo.astype(np.float64)) or np.any(x0>hi.astype(np.float64)): raise ValueError("baseline outside box")
    # Reproduce the discriminating target: lowering mobile SE improves EV88
    # objective, stays D8-feasible, and violates the target face disc.
    target_rc=(33,64); target_ix={tuple(map(int,rc)):i for i,rc in enumerate(nodes.tolist())}[target_rc]
    grad=A.T@(A@x0-rhs)
    if not float(grad[target_ix])>0.0: raise ValueError("target objective gradient no longer favors lowering SE")
    xdown=x0.copy();xdown[target_ix]-=0.01
    qdown=(G@xdown+k).reshape((-1,2)); target_face_ix=int(np.flatnonzero(np.all(face_keys==np.asarray(EXPECTED_FACE_KEY),axis=1))[0])
    target_d8=next(w for w in witnesses if w[0]==target_rc)
    if xdown[target_ix] < float(B[target_d8[1]]): raise ValueError("target lowering probe violates its D8 witness")
    target_lower_cost=0.5*float(np.dot(A@xdown-rhs,A@xdown-rhs))
    base_cost=0.5*float(np.dot(A@x0-rhs,A@x0-rhs))
    if not target_lower_cost<base_cost or np.linalg.norm(qdown[target_face_ix])<=radii[target_face_ix]:
        raise ValueError("target does not independently discriminate objective descent from face cone")
    # Verify source readset again at the end to catch TOCTOU during reconstruction.
    end={p:sha256(p) for p in pins}
    if end!=pins: raise ValueError("source readset changed during preflight reconstruction")
    if sha256(prepared_path)!=report.get("prepared_sha256"): raise ValueError("prepared changed during preflight reconstruction")
    return {"preflight_path":str(Path(preflight_path).resolve()),"preflight_sha256":sha256(preflight_path),
            "prepared_path":str(Path(prepared_path).resolve()),"prepared_sha256":sha256(prepared_path),
            "source_pins":pins,"shape":list(B.shape),"variables":int(len(nodes)),"fixed":int(protected.sum()),
            "stencils":int(len(stencils)),"D8_witnesses":int(len(witnesses)),"strict_minima_exempt":int(len(strict_minima)),
            "faces":int(len(radii)),"A_nnz":int(A.nnz),"C_nnz":int(C.nnz),"G_nnz":int(G.nnz),
            "cross_sector_stencils":int(cross_stencils),"baseline_max_disc_excess":baseline_disc_excess,
            "native_max_slope_B_deg":float(np.max(nativeB)),"elapsed_s":time.time()-started,
            "target_probe":{"gradient_dSE":float(grad[target_ix]),"objective_delta":target_lower_cost-base_cost,
                            "disc_excess_raw_units":float(np.linalg.norm(qdown[target_face_ix])-radii[target_face_ix]),
                            "d8_feasible":True},
            "baseline":B32,"protected":protected,"nodes":nodes,"A":A,"rhs":rhs,"C":C,"d":drhs,
            "G":G,"k":k,"radii":radii,"face_keys":face_keys,"qB":qB,
            "witnesses":witnesses,"lower":lo,"upper":hi,"strict_minima":strict_minima}


def _inward32(value, lower):
    f=np.float32(value)
    if lower and float(f)<value: f=np.nextafter(f,np.float32(np.inf),dtype=np.float32)
    if not lower and float(f)>value: f=np.nextafter(f,np.float32(-np.inf),dtype=np.float32)
    return f


def _face_kkt(z,y,radii,rho,eps_primal,eps_dual):
    pairs=np.asarray(z,np.float64).reshape((-1,2));dual=np.asarray(y,np.float64).reshape((-1,2));R=np.asarray(radii,np.float64)
    projected=project_discs_independent(pairs+dual/float(rho),R)
    projection_res=float(np.max(np.abs(pairs-projected),initial=0.))
    norms=np.linalg.norm(pairs,axis=1);yn=np.linalg.norm(dual,axis=1)
    # Use the frozen ADMM primal tolerance for approximate feasibility
    # classification; the author's 1e-7*max(1,R) label is diagnostic only.
    boundary=np.abs(norms-R)<=eps_primal
    interior=norms<R-eps_primal
    denom=np.einsum('ij,ij->i',pairs,pairs)
    lam=np.divide(np.einsum('ij,ij->i',pairs,dual),denom,out=np.zeros_like(norms),where=denom>0)
    tangent=dual-pairs*lam[:,None]
    return {"projection_residual":projection_res,"interior_dual_max":float(np.max(yn[interior],initial=0.)),
            "negative_multiplier_max":float(np.max(np.maximum(0.,-lam[boundary]),initial=0.)),
            "boundary_tangent_residual_max":float(np.max(np.linalg.norm(tangent[boundary],axis=1),initial=0.)),
            "soc_complementarity_max":float(np.max(np.abs(R*yn-np.einsum('ij,ij->i',pairs,dual)),initial=0.)),
            "feasibility_excess_max":float(np.max(np.maximum(0.,norms-R),initial=0.)),
            "boundary_count":int(boundary.sum()),"interior_count":int(interior.sum()),
            "multipliers":lam,"dual_norms":yn}


def _verify_solution(pre, run_dir):
    """Read-only verifier for the raw+closed schema declared in PLAN.md."""
    run=Path(run_dir); result_path=run/"solve-result.json"; solution_path=run/"solution.npz"
    result=json.loads(result_path.read_text(encoding="utf-8-sig"))
    if result.get("status")!="SYNTHETIC_DIAGNOSTIC_ONLY": raise ValueError("unexpected solve-result status")
    if not result.get("solution_path") or Path(result["solution_path"]).resolve()!=solution_path.resolve(): raise ValueError("solution path mismatch")
    if sha256(solution_path)!=result.get("solution_sha256"): raise ValueError("solution artifact hash mismatch")
    d=_load_npz(solution_path)
    B=pre["baseline"]; nodes=pre["nodes"]; A=pre["A"];rhs=pre["rhs"];C=pre["C"];drhs=pre["d"];G=pre["G"];k=pre["k"];R=pre["radii"]
    required={"solution_float64","baseline_float32","raw_float32_grid","closed_float32_grid",
              "face_gradient_q_raw_operator","face_gradient_q_raw_coordinates","face_radii",
              "face_slopes_raw_deg","face_slopes_closed_deg","closure_clipped","closure_upper_propagated",
              "variables_rc","y_box","y_d8","y_face","z_box","z_d8","z_face"}
    missing=required-set(d)
    if missing: raise ValueError(f"solution arrays missing: {sorted(missing)}")
    x=_require_array(d,"solution_float64",np.float64,(len(nodes),))
    saved_nodes=_require_array(d,"variables_rc",np.int32,nodes.shape)
    if not np.array_equal(saved_nodes,nodes): raise ValueError("serialized variable coordinate order differs from prepared source")
    if not np.isfinite(x).all(): raise ValueError("solution vector contains nonfinite values")
    raw_expected=x.astype(np.float32)
    raw_grid=B.copy();raw_grid[tuple(nodes.T)]=raw_expected
    serialized_baseline=_require_array(d,"baseline_float32",np.float32,B.shape)
    if not np.array_equal(serialized_baseline,B):
        raise ValueError("serialized solution baseline differs from independently pinned preflight")
    serialized_raw=_require_array(d,"raw_float32_grid",np.float32,B.shape)
    if not np.array_equal(serialized_raw,raw_grid):
        raise ValueError("saved raw grid is not the direct float32 cast of x64 over baseline")
    lower=np.broadcast_to(B, B.shape).astype(np.float32,copy=True)
    upper=lower.copy();lower[tuple(nodes.T)]=pre["lower"];upper[tuple(nodes.T)]=pre["upper"]
    edges=np.asarray([[*center,*witness] for center,witness in pre["witnesses"]],np.int32).reshape((-1,4))
    closure=project_order_independent(raw_grid,lower,upper,edges)
    if "closed_float32_grid" not in d:
        raise ValueError("solution missing the planned D8-closed output; raw cast alone is diagnostic")
    closed=_require_array(d,"closed_float32_grid",np.float32,B.shape)
    if not np.array_equal(closed,closure["closed_float32"]): raise ValueError("closed grid differs from independently recomputed D8 closure")
    for key,expected in (("closure_clipped",closure["clipped_float32"]),
                         ("closure_upper_propagated",closure["upper_propagated"])):
        if key not in d: raise ValueError(f"solution lacks serialized closure array: {key}")
        serialized=_reshape_serialized_flat_grid(d[key],B.shape,key)
        if not np.array_equal(serialized,expected): raise ValueError(f"closure serialization mismatch: {key}")
    # Directly recheck exact float32 box/fixed/D8 and no new strict minima.
    fixed=np.ones(B.shape,bool);fixed[tuple(nodes.T)]=False
    bounds_bad=int(np.count_nonzero((closed[tuple(nodes.T)]<pre["lower"])|(closed[tuple(nodes.T)]>pre["upper"])))
    fixed_exact=bool(np.array_equal(closed[fixed],B[fixed]))
    d8_bad=int(np.count_nonzero(closed[edges[:,0],edges[:,1]]<closed[edges[:,2],edges[:,3]]))
    new_minima=int(np.count_nonzero(minima_mask_interior(closed)&~minima_mask_interior(B)))
    # Recompute native coordinate normals for candidate and baseline, never use saved q/angle as authority.
    _nB,slopeB=native_normal_slopes(B)
    _nH,slopeH=native_normal_slopes(closed)
    face_shape=(B.shape[0]-1,B.shape[1]-1,2)
    saved_closed_slopes=_require_array(d,"face_slopes_closed_deg",np.float64,face_shape).reshape(-1)
    if np.max(np.abs(saved_closed_slopes-slopeH.reshape(-1)),initial=0.0)>1e-11:
        raise ValueError("saved closed-slope diagnostic differs from independent triangle normals")
    cap=np.maximum(35.0,slopeB)
    max_angle_excess=float(np.max(slopeH-cap,initial=-np.inf))
    angular_gate=bool(np.all(slopeH<=cap+1e-4))
    qH=native_face_gradients(closed).reshape((-1,2));qB=native_face_gradients(B).reshape((-1,2))
    q_raw_native=native_face_gradients(raw_grid).reshape((-1,2))
    q_raw_operator=(G@raw_expected.astype(np.float64)+k).reshape((-1,2))
    raw_diag_error=0.0
    saved_qop=_require_array(d,"face_gradient_q_raw_operator",np.float64,q_raw_operator.shape)
    saved_qcoord=_require_array(d,"face_gradient_q_raw_coordinates",np.float64,q_raw_native.shape)
    raw_diag_error=max(raw_diag_error,float(np.max(np.abs(saved_qop-q_raw_operator),initial=0.)))
    raw_diag_error=max(raw_diag_error,float(np.max(np.abs(saved_qcoord-q_raw_native),initial=0.)))
    saved_radii=_require_array(d,"face_radii",np.float64,R.shape)
    raw_diag_error=max(raw_diag_error,float(np.max(np.abs(saved_radii-R),initial=0.)))
    _nr,slope_raw=native_normal_slopes(raw_grid)
    saved_raw_slopes=_require_array(d,"face_slopes_raw_deg",np.float64,face_shape).reshape(-1)
    raw_diag_error=max(raw_diag_error,float(np.max(np.abs(saved_raw_slopes-slope_raw.reshape(-1)),initial=0.)))
    if "float32_face_disc_violations" in result.get("checks",{}):
        computed_raw_disc_bad=int(np.count_nonzero(np.linalg.norm(q_raw_native,axis=1)>R))
        if computed_raw_disc_bad!=int(result["checks"]["float32_face_disc_violations"]):
            raise ValueError("author's raw disc-excess diagnostic disagrees with independent calculation")
    exact_disc_bad=int(np.count_nonzero(np.linalg.norm(qH,axis=1)>R))
    max_disc_excess=float(np.max(np.linalg.norm(qH,axis=1)-R,initial=-np.inf))
    # Independent objective on both CSR and the direct full-grid stencil formula.
    x0=B[tuple(nodes.T)].astype(np.float64)
    closed_x=closed[tuple(nodes.T)].astype(np.float64)
    raw_x=raw_grid[tuple(nodes.T)].astype(np.float64)
    def cost(v):
        residual=A@np.asarray(v,np.float64)-rhs
        return .5*float(residual@residual)
    objB,obj64,objraw,objclosed=cost(x0),cost(x),cost(raw_x),cost(closed_x)
    direct_closed=scalar_objective_independent(B,closed,nodes)
    objective_identity=abs(direct_closed-objclosed)<=1e-10*max(1.,objclosed)
    closure_allowance=1e-7*max(1.,objraw)
    closure_objective=bool(objclosed-objraw<=closure_allowance and objclosed<objB)
    # ADMM primal/stationarity and projection/KKT from saved continuous x64 state.
    solver=result.get("solver",{})
    rho=float(solver.get("rho",np.nan))
    yb=_require_array(d,"y_box",np.float64,x.shape); yd=_require_array(d,"y_d8",np.float64,drhs.shape)
    yf=_require_array(d,"y_face",np.float64,(2*len(R),))
    zb=_require_array(d,"z_box",np.float64,x.shape); zd=_require_array(d,"z_d8",np.float64,drhs.shape)
    zf=_require_array(d,"z_face",np.float64,(2*len(R),))
    q64=(G@x+k).reshape((-1,2)); q64_native=native_face_gradients(_height_from_vector64(B,nodes,x)).reshape((-1,2))
    g_native_error=float(np.max(np.abs(q64-q64_native),initial=0.))
    cx=C@x; gx=(G@x+k)
    primal=max(float(np.max(np.abs(x-zb),initial=0.)),float(np.max(np.abs(cx-zd),initial=0.)),float(np.max(np.abs(gx-zf),initial=0.)))
    station=A.T@(A@x-rhs)+yb+C.T@yd+G.T@yf
    stationarity=float(np.max(np.abs(station),initial=0.))
    dualvec=yb+C.T@yd+G.T@yf
    epsp=ABS_TOL+REL_TOL*max(float(np.max(np.abs(x),initial=0.)),float(np.max(np.abs(cx),initial=0.)),
                             float(np.max(np.abs(zb),initial=0.)),float(np.max(np.abs(zd),initial=0.)),
                             float(np.max(np.abs(gx),initial=0.)),float(np.max(np.abs(zf),initial=0.)))
    epsd=ABS_TOL+REL_TOL*float(np.max(np.abs(dualvec),initial=0.))
    # Recompute each projection residual using saved unscaled y and final rho.
    box_proj=np.clip(x+yb/rho,pre["lower"].astype(np.float64),pre["upper"].astype(np.float64))
    d8_proj=np.maximum(cx+yd/rho,drhs)
    face_proj=project_discs_independent(q64+yf.reshape((-1,2))/rho,R)
    normal_res=max(float(np.max(np.abs(zb-box_proj),initial=0.)),float(np.max(np.abs(zd-d8_proj),initial=0.)),
                   float(np.max(np.abs(zf.reshape((-1,2))-face_proj),initial=0.)))
    cone=_face_kkt(zf,yf,R,rho,epsp,epsd)
    # Require the intentional Narva-like face to be active in the final, closed float32 grid.
    target_index=int(np.flatnonzero(np.all(pre["face_keys"]==np.asarray(EXPECTED_FACE_KEY),axis=1))[0])
    target_cap=float(cap.reshape(-1)[target_index]); target_angle=float(slopeH.reshape(-1)[target_index])
    target_lambda=float(cone["multipliers"][target_index]); target_dual=float(cone["dual_norms"][target_index])
    active_face=bool(target_dual>epsd and abs(target_angle-target_cap)<=1e-4)
    time_s=float(solver.get("elapsed_s",np.inf))
    numeric_total=float(result.get("elapsed_numeric_solver_plus_closure_s",np.inf))
    mem=solver.get("peak_memory",{})
    peak=int(mem.get("peak_working_set_bytes",0))
    author_checks=result.get("checks",{})
    checks={
        "solver_converged":solver.get("status")=="CONVERGED",
        "readset_stable":bool(result.get("readset_stable",False)) and result.get("readset_start")==result.get("readset_end") and result.get("readset_start")==pre["source_pins"],
        "artifact_identity":sha256(solution_path)==result.get("solution_sha256"),
        "continuous_primal_residual":primal<=epsp,
        "continuous_stationarity":stationarity<=epsd,
        "projection_normal_cones":normal_res<=epsp,
        "face_soc_kkt":cone["feasibility_excess_max"]<=epsp and cone["projection_residual"]<=epsp and cone["interior_dual_max"]<=epsd and
                       cone["negative_multiplier_max"]<=epsd and cone["boundary_tangent_residual_max"]<=epsd and
                       cone["soc_complementarity_max"]<=epsd*max(1.0,float(np.max(R,initial=0.))),
        "native_gradient_reconstruction":g_native_error<=1e-11,
        "serialized_raw_gradient_diagnostics":raw_diag_error<=1e-11,
        "target_face_active_after_float32":active_face,
        "float32_closed_bounds":bounds_bad==0,
        "fixed_exact":fixed_exact,
        "float32_d8_exact":d8_bad==0,
        "no_new_strict_minima":new_minima==0,
        "native_angular_gate":angular_gate,
        "objective_identity":objective_identity,
        "objective_reduced_vs_B":objclosed<objB,
        "closure_objective_budget":closure_objective,
        "order_correction_bound":closure["correction_bound_pass"],
        "within_120s":numeric_total<=120.0 and author_checks.get("within_total_numeric_budget") is True,
        "within_1_5GiB":peak<=1_610_612_736 and author_checks.get("within_peak_ws_limit") is True,
    }
    # Source/artifact rehash at end, including this consumer and all preflight sources.
    end_hashes={p:sha256(p) for p in pre["source_pins"]}
    stable=end_hashes==pre["source_pins"] and sha256(PREFLIGHT)==pre["preflight_sha256"] and sha256(PREPARED)==pre["prepared_sha256"]
    if not stable: checks["readset_stable"]=False
    return {"status":"PASS_FACE_SLOPE_CONE_SYNTHETIC_ONLY" if all(checks.values()) else "FAIL_FACE_SLOPE_CONE_SYNTHETIC_ONLY",
            "checks":checks,"preflight":{k:v for k,v in pre.items() if k not in {"baseline","protected","nodes","A","rhs","C","d","G","k","radii","face_keys","qB","witnesses","lower","upper","strict_minima"}},
            "solution":{"path":str(solution_path.resolve()),"sha256":sha256(solution_path),"result_path":str(result_path.resolve()),
                        "result_sha256":sha256(result_path),"status":result.get("status"),"solver_status":solver.get("status"),
                        "iterations":solver.get("iteration"),"rho":rho,"elapsed_solver_s":time_s,
                        "elapsed_solver_plus_closure_s":numeric_total,"peak_working_set_bytes":peak},
            "metrics":{"primal_residual":primal,"eps_primal":epsp,"stationarity":stationarity,"eps_dual":epsd,
                        "projection_normal_cone_residual":normal_res,"face_kkt":{k:v for k,v in cone.items() if k not in {"multipliers","dual_norms"}},
                        "native_gradient_max_abs_error":g_native_error,"target_face_key":list(EXPECTED_FACE_KEY),
                        "serialized_raw_diagnostic_max_abs_error":raw_diag_error,
                        "target_angle_deg":target_angle,"target_cap_deg":target_cap,"target_multiplier":target_lambda,
                        "target_dual_norm":target_dual,"new_strict_minima":new_minima,"box_bad":bounds_bad,"D8_bad":d8_bad,
                        "disc_violations_diagnostic_only":exact_disc_bad,"max_disc_excess_raw_units_diagnostic_only":max_disc_excess,
                        "max_native_angular_excess_deg":max_angle_excess,"objective_B":objB,"objective_x64":obj64,
                        "objective_raw_float32":objraw,"objective_closed_float32":objclosed,
                        "objective_float32_minus_x64":objclosed-obj64,"closure_allowance":closure_allowance,
                        "closure_b_plus_V":closure["b_plus_V"],"closure_max_abs_correction":closure["max_abs_correction"],
                        "direct_functional_objective":direct_closed},
            "source_pins_end":end_hashes}


def _height_from_vector(base,nodes,x):
    h=np.asarray(base,dtype=np.float32).copy()
    h[tuple(np.asarray(nodes,dtype=np.int32).T)]=np.asarray(x,dtype=np.float64).astype(np.float32)
    return h.astype(np.float64)


def _height_from_vector64(base,nodes,x):
    h=np.asarray(base,dtype=np.float64).copy()
    h[tuple(np.asarray(nodes,dtype=np.int32).T)]=np.asarray(x,dtype=np.float64)
    return h


def run(preflight_path=PREFLIGHT,prepared_path=PREPARED,run_dir=DEFAULT_RUN,output=None):
    start_pins={str(p):sha256(p) for p in (Path(__file__),PLAN,PILOT/"pilot.py",PROTO,SOLVER_REF,EV87,ORDER_CLOSURE,
                                             PREFLIGHT_PLAN,Path(preflight_path),Path(prepared_path),
                                             Path(run_dir)/"solve-result.json",Path(run_dir)/"solution.npz")}
    pre=verify_preflight(preflight_path,prepared_path)
    report=_verify_solution(pre,run_dir)
    end_pins={p:sha256(p) for p in start_pins}
    if start_pins!=end_pins:
        report["status"]="FAIL_FACE_SLOPE_CONE_SYNTHETIC_ONLY"
        report["checks"]["whole_readset_stable"]=False
    else:
        report["checks"]["whole_readset_stable"]=True
    report["consumer_sha256"]=sha256(__file__)
    report["readset_start"]=start_pins;report["readset_end"]=end_pins
    report["status"]="PASS_FACE_SLOPE_CONE_SYNTHETIC_ONLY" if all(report["checks"].values()) else "FAIL_FACE_SLOPE_CONE_SYNTHETIC_ONLY"
    if output:
        out=Path(output)
        if out.exists(): raise FileExistsError(f"refusing overwrite: {out}")
        out.parent.mkdir(parents=True,exist_ok=True)
        tmp=out.with_suffix(out.suffix+".tmp")
        tmp.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8")
        tmp.replace(out)
    return report


def main():
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--preflight-only",action="store_true")
    mode.add_argument("--run",type=Path)
    ap.add_argument("--preflight",type=Path,default=PREFLIGHT)
    ap.add_argument("--prepared",type=Path,default=PREPARED)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    if args.self_test:
        print(json.dumps(self_fixtures(),indent=2));return 0
    if args.preflight_only:
        data=verify_preflight(args.preflight,args.prepared)
        summary={k:v for k,v in data.items() if not isinstance(v,(np.ndarray,sparse.csr_matrix,list))}
        summary.update({"status":"PASS_PREFLIGHT_RECONSTRUCTION_ONLY","solve_executed":False,
                        "consumer_path":str(Path(__file__).resolve()),"consumer_sha256":sha256(__file__)})
        rendered=json.dumps(summary,indent=2,allow_nan=False,default=str)+"\n"
        if args.output:
            out=Path(args.output)
            if out.exists(): raise FileExistsError(f"refusing overwrite: {out}")
            out.parent.mkdir(parents=True,exist_ok=True)
            tmp=out.with_suffix(out.suffix+".tmp")
            tmp.write_text(rendered,encoding="utf-8")
            tmp.replace(out)
        print(rendered,end="");return 0
    report=run(args.preflight,args.prepared,args.run,args.output)
    print(json.dumps({"status":report["status"],"false_gates":[k for k,v in report["checks"].items() if not v],"output":str(args.output) if args.output else None},indent=2))
    return 0 if report["status"].startswith("PASS_") else 1


if __name__=="__main__":
    raise SystemExit(main())
