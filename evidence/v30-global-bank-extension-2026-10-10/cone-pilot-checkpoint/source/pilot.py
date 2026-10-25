from __future__ import annotations
import argparse
import ctypes
import hashlib
import importlib.util
import json
import math
import os
import time
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import LinearOperator, cg

ROOT = Path(__file__).resolve().parent
PROTO = ROOT.parent
EV88 = PROTO / 'prototype.py'
EV88_SHA = '5b4b8f08e5205e1f9cc90bcc8e82e61dade45bb82bd22da8ee69303aa4475cc4'
SOLVER_REF = PROTO / 'admm-quantized-pilot' / 'solve.py'
SOLVER_REF_SHA = '7e8636bf54ba23f7e23bc2f06464100439468da7b4edca85f96c72d0cd40e149'
EV87 = Path(r'E:\DayZ-Baltic-Build\v30-global-strict-bank-relief-20261010\review-independent\verify_ev87.py')
EV87_SHA = '964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27'
ORDER_CLOSURE = PROTO / 'real-sector-preflight' / 'order-closure' / 'projection.py'
ORDER_CLOSURE_SHA = 'a990dc2d33fca4fd2a446b958f0412a2d752a5d3072a85d82058bb634cfaf44b'
PLAN = ROOT / 'PLAN.md'
ANG_TOL = 1e-4
RHO, ABS_TOL, REL_TOL = 1.0, 1e-10, 1e-8
MAX_ITER, CG_MAXITER = 10000, 1000
CG_RTOL, CG_ATOL = 1e-12, 1e-13
NUMERIC_BUDGET_S = 120.0
PEAK_WS_LIMIT = 1_610_612_736
SECTOR_C = 64

class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [('cb', ctypes.c_ulong), ('PageFaultCount', ctypes.c_ulong)] + [
        (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
        'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
        'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def memory_snapshot() -> dict:
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    kernel.GetCurrentProcess.argtypes = []
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), ctypes.c_ulong]
    psapi.GetProcessMemoryInfo.restype = ctypes.c_int
    c = PROCESS_MEMORY_COUNTERS_EX()
    c.cb = ctypes.sizeof(c)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(c), c.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return {'pid': os.getpid(), 'peak_working_set_bytes': int(c.PeakWorkingSetSize),
            'working_set_bytes': int(c.WorkingSetSize), 'peak_commit_bytes': int(c.PeakPagefileUsage),
            'method': 'GetProcessMemoryInfo / PROCESS_MEMORY_COUNTERS_EX'}


def load_ev88():
    if sha(EV88) != EV88_SHA:
        raise RuntimeError('EV88 prototype pin mismatch')
    spec = importlib.util.spec_from_file_location('ev88_face_cone_pinned', EV88)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_order_closure():
    if sha(ORDER_CLOSURE) != ORDER_CLOSURE_SHA:
        raise RuntimeError('float32 order-closure source pin mismatch')
    spec=importlib.util.spec_from_file_location('pinned_float32_order_closure',ORDER_CLOSURE)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def inward32(value: float, lower: bool) -> float:
    f = np.float32(value)
    if lower and float(f) < value:
        f = np.nextafter(f, np.float32(np.inf), dtype=np.float32)
    if not lower and float(f) > value:
        f = np.nextafter(f, np.float32(-np.inf), dtype=np.float32)
    return float(f)


def synthetic_baseline(shape=(64, 128)):
    if shape != (64, 128):
        raise ValueError('This pilot is pinned to the 64x128 synthetic fixture')
    p = load_ev88()
    B64, protected = p.synthetic(shape)
    B = (B64 - 100.0 + 2.0).astype(np.float32).astype(np.float64)
    # Low synthetic run-out south/east of the target makes the curvature
    # functional pull its mobile SE down; this is fixture geometry only.
    for r in range(30, 37):
        for c in range(61, 68):
            B[r, c] = np.float32(2.3 - 0.3 * ((r-33) + (c-64)))
    # Narva-like single face: NW/NE fixed, SE mobile. Values are synthetic
    # fixtures copied from the diagnosed geometry; no real raster is loaded.
    B[32, 63] = np.float32(7.2344970703125)
    B[32, 64] = np.float32(3.1139774322509766)
    B[33, 64] = np.float32(2.2943551540374756)
    B[33, 63] = np.float32(1.95)
    protected = protected.copy()
    protected[32, 63] = True
    protected[32, 64] = True
    if protected[33, 64]:
        raise AssertionError('Narva-like SE fixture must remain variable')
    nodes = np.column_stack(np.nonzero(~protected)).astype(np.int32)
    return B, protected, nodes


def d8_witnesses(B):
    h, w = B.shape
    witnesses, exempt = [], []
    # Constraint rows are assembled later against variable indexing; these
    # center/witness edges cover every non-strict local-minimum center.
    for r in range(h):
        for c in range(w):
            ns = [(rr, cc) for rr in range(max(0, r-1), min(h, r+2))
                  for cc in range(max(0, c-1), min(w, c+2)) if (rr, cc) != (r, c)]
            if not ns:
                continue
            m = min(float(B[rr, cc]) for rr, cc in ns)
            if float(B[r, c]) < m:
                exempt.append((r,c))
                continue
            witness = min((rr, cc) for rr, cc in ns if float(B[rr, cc]) == m)
            witnesses.append({'center': (r, c), 'witness': witness})
    return witnesses, exempt


def build_d8(B, nodes, witnesses):
    index = {tuple(map(int, rc)): i for i, rc in enumerate(nodes.tolist())}
    rr, cc, vv, d = [], [], [], np.empty(len(witnesses), np.float64)
    for row, item in enumerate(witnesses):
        center, witness = tuple(item['center']), tuple(item['witness'])
        offset = 0.0
        for rc, coef in ((center, 1.0), (witness, -1.0)):
            i = index.get(rc)
            if i is None:
                offset += coef * float(B[rc])
            else:
                rr.append(row); cc.append(i); vv.append(coef)
        d[row] = -offset
    C = sparse.csr_matrix((np.asarray(vv), (np.asarray(rr), np.asarray(cc))), shape=(len(witnesses), len(nodes)))
    C.sort_indices()
    return C, d


def face_components(kind, r, c):
    # Output is 6m-scaled physical gradient (x,z), x=6*c, z=-6*r.
    if kind == 0:  # NW, NE, SE
        return (((r, c+1, 1.), (r, c, -1.)), ((r, c+1, 1.), (r+1, c+1, -1.)))
    if kind == 1:  # NW, SE, SW
        return (((r+1, c+1, 1.), (r+1, c, -1.)), ((r, c, 1.), (r+1, c, -1.)))
    raise ValueError(kind)


def face_gradients_direct(B):
    h, w = B.shape
    out = np.empty((h-1, w-1, 2, 2), np.float64)
    for r in range(h-1):
        for c in range(w-1):
            nw, ne, sw, se = map(float, (B[r,c], B[r,c+1], B[r+1,c], B[r+1,c+1]))
            out[r,c,0] = (ne-nw, ne-se)
            out[r,c,1] = (se-sw, nw-sw)
    return out


def face_slopes_from_q(q):
    return np.degrees(np.arctan2(np.linalg.norm(q, axis=-1) / 6.0, 1.0))


def build_face_operator(B, nodes):
    h, w = B.shape
    index = {tuple(map(int, rc)): i for i, rc in enumerate(nodes.tolist())}
    nfaces = 2 * (h-1) * (w-1)
    rr, cc, vv = [], [], []
    k = np.empty((nfaces, 2), np.float64)
    radii = np.empty(nfaces, np.float64)
    face_keys = np.empty((nfaces, 3), np.int32)
    qB = np.empty((nfaces, 2), np.float64)
    anglesB = np.empty(nfaces, np.float64)
    row = 0
    direct = face_gradients_direct(B)
    for r in range(h-1):
        for c in range(w-1):
            for kind in (0, 1):
                comps = face_components(kind, r, c)
                for j, terms in enumerate(comps):
                    fixed = 0.0
                    for rc_r, rc_c, coef in terms:
                        rc = (rc_r, rc_c)
                        idx = index.get(rc)
                        if idx is None:
                            fixed += coef * float(B[rc])
                        else:
                            rr.append(2*row+j); cc.append(idx); vv.append(coef)
                    k[row, j] = fixed
                qB[row] = direct[r, c, kind]
                anglesB[row] = math.degrees(math.atan2(float(np.linalg.norm(qB[row])) / 6.0, 1.0))
                # Algebraically max(6*tan(35deg), ||q_B||); this avoids an
                # atan->tan round trip that could put B outside its own disc by 1 ulp.
                radii[row] = max(6.0 * math.tan(math.radians(35.0)),
                                 float(np.linalg.norm(qB[row])))
                face_keys[row] = (r, c, kind)
                row += 1
    G = sparse.csr_matrix((np.asarray(vv), (np.asarray(rr), np.asarray(cc))), shape=(2*nfaces, len(nodes)))
    G.sort_indices()
    return G, k.reshape(-1), radii, face_keys, qB, anglesB, direct


def project_discs(q, radii):
    q = np.asarray(q, dtype=np.float64)
    radii = np.asarray(radii, dtype=np.float64).reshape(-1)
    if q.ndim != 2 or q.shape != (len(radii), 2):
        raise ValueError('Expected q shape (n_faces,2) and one radius per face')
    if not np.isfinite(q).all() or not np.isfinite(radii).all() or np.any(radii < 0):
        raise ValueError('Disc projection requires finite vectors and nonnegative radii')
    norms = np.linalg.norm(q, axis=1)
    scale = np.ones_like(norms)
    outside = norms > radii
    positive = outside & (norms > 0)
    scale[positive] = radii[positive] / norms[positive]
    scale[outside & (norms == 0)] = 0.0
    return q * scale[:, None]


def d8_and_box_fixture(B, nodes, lo, hi, witnesses):
    fixed = np.ones(B.shape, dtype=bool); fixed[tuple(nodes.T)] = False
    assert np.array_equal(B[fixed], B[fixed].astype(np.float32).astype(np.float64))
    vals = B[tuple(nodes.T)]
    assert np.all(vals >= lo) and np.all(vals <= hi)
    bad = vals.copy(); bad[0] = hi[0] + 1.0
    assert np.any((bad < lo) | (bad > hi))
    for item in witnesses:
        if B[tuple(item['center'])] < B[tuple(item['witness'])]:
            raise AssertionError('Baseline D8 witness is not feasible')
    return fixed


def projection_fixtures():
    q = np.array([[0.3, 0.4], [3., 4.], [0., 0.], [1., 0.]], np.float64)
    r = np.array([1., 2., 0., 1.])
    z = project_discs(q, r)
    assert np.array_equal(z[0], q[0])
    assert np.allclose(np.linalg.norm(z, axis=1), [0.5, 2., 0., 1.])
    for bad_q, bad_r in ((np.array([[np.nan, 0.]]), [1.]), (np.array([[1., 0.]]), [-1.])):
        try:
            project_discs(bad_q, np.asarray(bad_r))
        except ValueError:
            pass
        else:
            raise AssertionError('invalid disc projection input was accepted')
    return {'inside_unchanged': True, 'outside_radial': True, 'boundary_unchanged': True,
            'zero_radius': True, 'nonfinite_and_negative_rejected': True}


def soc_kkt_fixtures():
    # For q in a closed ball, the ADMM multiplier is outward-normal:
    # q=Proj_K(q+y/rho), with y=lambda*q, lambda>=0 on the boundary.
    rho=2.0
    z=np.array([3.0,4.0,1.0,1.0])
    y=np.array([6.0,8.0,0.0,0.0])
    radii=np.array([5.0,5.0])
    projected=project_discs((z+y/rho).reshape(-1,2),radii).reshape(-1)
    assert np.allclose(projected,z,rtol=0.,atol=1e-14)
    m=soc_kkt(z,y,radii)
    assert m['complementarity_max']<1e-12 and m['interior_dual_max']==0.0
    assert m['boundary_radial_residual_max']<1e-12 and m['negative_radial_multiplier_max']==0.0
    bad_y=np.array([-6.0,-8.0,0.0,0.0])
    bad=soc_kkt(z,bad_y,radii)
    assert bad['negative_radial_multiplier_max']>0.0
    return {'outward_boundary_dual_pass':True,'interior_zero_dual_pass':True,
            'inward_dual_negative_detected':True,'rho':rho}


def build_objective(ev88, B, nodes):
    st = ev88.all_stencils(B.shape, nodes)
    records = ev88.row_records(B, nodes, st)
    A, rhs = ev88.csr_from_records(records, len(nodes))
    return st, records, A, rhs


def baseline_readiness(B, nodes, A, rhs, C, d, witnesses, G, k, radii, face_keys, qB, direct, protected):
    xB = B[tuple(nodes.T)].astype(np.float64)
    d8min = float(np.min(C@xB-d, initial=np.inf))
    assert d8min >= -1e-12, f'baseline violates D8 by {-d8min}'
    assert np.all(xB >= np.array([inward32(float(v)-.5, True) for v in xB]))
    assert np.all(xB <= np.array([inward32(float(v)+.5, False) for v in xB]))
    faceq = (G @ xB + k).reshape(-1, 2)
    max_action = float(np.max(np.abs(faceq-qB), initial=0.0))
    assert max_action < 1e-12, f'Gx+k action mismatch {max_action}'
    q_norm = np.linalg.norm(faceq, axis=1)
    disc_violation = float(np.max(q_norm-radii, initial=-np.inf))
    assert disc_violation <= 1e-12, f'baseline outside face cone by {disc_violation}'
    # Independent 3D-coordinate plane gradient on every triangle.
    coord_err = 0.0
    h,w = B.shape
    for r in range(h-1):
        for c in range(w-1):
            xyz = np.array([[6*c, float(B[r,c]), -6*r],
                            [6*(c+1), float(B[r,c+1]), -6*r],
                            [6*(c+1), float(B[r+1,c+1]), -6*(r+1)],
                            [6*c, float(B[r+1,c]), -6*(r+1)]], np.float64)
            for kind, ids in ((0,(0,1,2)), (1,(0,2,3))):
                pts=xyz[list(ids)]
                mat=np.column_stack((pts[:,0],pts[:,2],np.ones(3)))
                coeff=np.linalg.solve(mat,pts[:,1])
                qcoord=6.0*coeff[:2]
                i=(r*(w-1)+c)*2+kind
                coord_err=max(coord_err,float(np.max(np.abs(qcoord-faceq[i]))))
    assert coord_err < 1e-11, f'coordinate plane gradient mismatch {coord_err}'
    # Independently compare q norms to the source EV87 normal formula over all faces.
    # Cross products below reproduce only the pinned triangle-normal geometry; no
    # such value is consumed as a future acceptance result.
    nw,ne,sw,se=B[:-1,:-1],B[:-1,1:],B[1:,:-1],B[1:,1:]
    one=np.ones_like(nw)
    a=np.cross(np.stack((6*one,ne-nw,np.zeros_like(nw)),axis=-1),
               np.stack((6*one,se-nw,-6*one),axis=-1))
    b=np.cross(np.stack((6*one,se-nw,-6*one),axis=-1),
               np.stack((np.zeros_like(nw),sw-nw,-6*one),axis=-1))
    slopes_ref=np.stack([np.degrees(np.arctan2(np.hypot(a[...,0],a[...,2]),np.abs(a[...,1]))),
                         np.degrees(np.arctan2(np.hypot(b[...,0],b[...,2]),np.abs(b[...,1])))],axis=-1).reshape(-1)
    slope_err=float(np.max(np.abs(face_slopes_from_q(faceq)-slopes_ref),initial=0.0))
    assert slope_err < 1e-11, f'EV87 normal slope formula mismatch {slope_err}'
    # A real free-free xx/zz/xz row must couple variables on both sides of c=64.
    varix={tuple(map(int,rc)):i for i,rc in enumerate(nodes.tolist())}
    seam=None
    for record in (A.tocsr(),):
        del record
    ev88=load_ev88()
    st=ev88.all_stencils(B.shape,nodes)
    for item in st:
        terms=ev88.coeffs(*item)
        cols=[varix[(rr,cc)] for rr,cc,_ in terms if (rr,cc) in varix]
        left=[i for i in cols if int(nodes[i,1])<SECTOR_C]
        right=[i for i in cols if int(nodes[i,1])>=SECTOR_C]
        if left and right:
            seam={'stencil':list(item),'left_rc':nodes[left[0]].tolist(),'right_rc':nodes[right[0]].tolist()}
            break
    assert seam is not None, 'no free-free curvature stencil spans the sector seam'
    # Narva-like interior cell r=32,c=63, triangle0. NW/NE protected; SE mobile.
    target_index=(32*(B.shape[1]-1)+63)*2
    target_rc=(32,63,0)
    assert tuple(face_keys[target_index])==target_rc
    assert protected[32,63] and protected[32,64] and not protected[33,64]
    idx=varix[(33,64)]
    grad=float(np.asarray(A[:,idx].T @ (A@xB-rhs)).reshape(-1)[0])
    q0=faceq[target_index].copy()
    eps=min(.01, float(xB[idx]-inward32(float(xB[idx])-.5,True)),
            max(0.0,float(B[33,64]-B[33,63]))*.25)
    assert eps>1e-7, f'no D8-feasible lowering room for target SE: {eps}'
    xdown=xB.copy();xdown[idx]-=eps
    obj0=.5*float(np.dot(A@xB-rhs,A@xB-rhs))
    objdown=.5*float(np.dot(A@xdown-rhs,A@xdown-rhs))
    qdown=(G@xdown+k).reshape(-1,2)[target_index]
    assert grad>0 and objdown<obj0, f'objective does not favor lowering SE (grad={grad}, delta={objdown-obj0})'
    assert np.linalg.norm(qdown)>radii[target_index]+1e-8, 'lowering SE did not cross face-slope disc'
    # Selected witness for SE verifies the test move is D8 feasible.
    assert xdown[idx] >= B[33,63]-1e-12
    return {'baseline_d8_min_slack':d8min,'baseline_max_disc_violation':disc_violation,
            'G_action_max_abs_error':max_action,'coordinate_gradient_max_abs_error':coord_err,
            'EV87_normal_slope_max_abs_error_degrees':slope_err,'free_free_seam_stencil':seam,
            'target_face_key':list(target_rc),'target_B_slope_deg':float(face_slopes_from_q(qB[target_index:target_index+1])[0]),
            'target_disc_radius_raw_height_units':float(radii[target_index]),'target_objective_gradient_dSE':grad,
            'lowering_probe_delta_height':-eps,'lowering_probe_objective_delta':objdown-obj0,
            'lowering_probe_disc_excess':float(np.linalg.norm(qdown)-radii[target_index]),
            'target_SE_d8_witness_rc':[33,63]}


def preflight():
    for path, expected in ((EV88,EV88_SHA),(SOLVER_REF,SOLVER_REF_SHA),(EV87,EV87_SHA),
                            (ORDER_CLOSURE,ORDER_CLOSURE_SHA)):
        if sha(path)!=expected: raise RuntimeError(f'source pin mismatch: {path}')
    p=load_ev88()
    B, protected, nodes=synthetic_baseline()
    xB=B[tuple(nodes.T)]
    lo=np.array([inward32(float(v)-.5,True) for v in xB],np.float64)
    hi=np.array([inward32(float(v)+.5,False) for v in xB],np.float64)
    st,records,A,rhs=build_objective(p,B,nodes)
    witnesses, exempt=d8_witnesses(B)
    C,d=build_d8(B,nodes,witnesses)
    G,k,radii,face_keys,qB,anglesB,direct=build_face_operator(B,nodes)
    fixture={'radial_projection':projection_fixtures(),'soc_kkt':soc_kkt_fixtures(),
             'x_step_operator':x_step_fixtures()}
    checks=baseline_readiness(B,nodes,A,rhs,C,d,witnesses,G,k,radii,face_keys,qB,direct,protected)
    # Float32 baseline reconstruction and deliberately invalid local test vectors.
    recon=B.copy();recon[tuple(nodes.T)]=xB.astype(np.float32).astype(np.float64)
    assert np.array_equal(recon,B)
    raw=np.array([[1.0,2.0],[3.0,4.0]],np.float32)
    raw[0,0]=np.nextafter(raw[0,0],np.float32(np.inf))
    assert raw.dtype==np.float32 and np.isfinite(raw).all()
    # Radius map remains feasible after the exact baseline float32 round-trip.
    q32=(G@recon[tuple(nodes.T)]+k).reshape(-1,2)
    assert float(np.max(np.linalg.norm(q32,axis=1)-radii))<=1e-12
    closure_mod=load_order_closure()
    base_flat=B.astype(np.float32).ravel()
    lower_flat=base_flat.copy();upper_flat=base_flat.copy();fixed_flat=np.ones(base_flat.shape,bool)
    node_ids=np.ravel_multi_index((nodes[:,0],nodes[:,1]),B.shape)
    fixed_flat[node_ids]=False
    lower_flat[node_ids]=lo.astype(np.float32);upper_flat[node_ids]=hi.astype(np.float32)
    edge_ids=np.column_stack((np.ravel_multi_index((np.asarray([z['witness'][0] for z in witnesses]),
                                                     np.asarray([z['witness'][1] for z in witnesses])),B.shape),
                              np.ravel_multi_index((np.asarray([z['center'][0] for z in witnesses]),
                                                     np.asarray([z['center'][1] for z in witnesses])),B.shape))).astype(np.int64)
    closure_identity=closure_mod.project_order(base_flat,lower_flat,upper_flat,edge_ids,
                                                 baseline=base_flat,fixed=fixed_flat)
    assert np.array_equal(closure_identity['q'],base_flat)
    pins={str(x):sha(x) for x in (EV88,SOLVER_REF,EV87,ORDER_CLOSURE,PLAN,Path(__file__))}
    out=ROOT/'prepared.npz'
    if out.exists() or (ROOT/'preflight.json').exists():
        raise FileExistsError('Preflight outputs already exist; refusing overwrite')
    np.savez_compressed(out,baseline_float32=B.astype(np.float32),protected=protected,
        variables_rc=nodes,lower_float32=lo.astype(np.float32),upper_float32=hi.astype(np.float32),
        A_data=A.data,A_indices=A.indices,A_indptr=A.indptr,A_shape=np.asarray(A.shape),rhs=rhs,
        C_data=C.data,C_indices=C.indices,C_indptr=C.indptr,C_shape=np.asarray(C.shape),d8_rhs=d,
        witness_centers_rc=np.asarray([x['center'] for x in witnesses],np.int32),
        witness_neighbors_rc=np.asarray([x['witness'] for x in witnesses],np.int32),
        d8_exempt_strict_minima_rc=np.asarray(exempt,np.int32).reshape(-1,2),
        G_data=G.data,G_indices=G.indices,G_indptr=G.indptr,G_shape=np.asarray(G.shape),
        face_offset_k=k,face_radii=radii,face_keys_rc_kind=face_keys,face_gradients_B=qB,
        face_slope_B_deg=anglesB,stencils_json=np.frombuffer(json.dumps(st, separators=(',',':')).encode('utf-8'),dtype=np.uint8))
    prepared_sha=sha(out)
    for path, expected in ((EV88,EV88_SHA),(SOLVER_REF,SOLVER_REF_SHA),(EV87,EV87_SHA),
                           (ORDER_CLOSURE,ORDER_CLOSURE_SHA),(PLAN,pins[str(PLAN)]),(Path(__file__),pins[str(Path(__file__))])):
        if sha(path)!=expected: raise RuntimeError(f'source changed during preflight: {path}')
    report={'status':'PREFLIGHT_PASS_NO_SOLVE','scope':'SYNTHETIC_ONLY_64x128_NO_REAL_BASE_OR_TERRAIN_CANDIDATE',
      'source_pins_start':pins,'source_pins_end':{str(x):sha(x) for x in (EV88,SOLVER_REF,EV87,ORDER_CLOSURE,PLAN,Path(__file__))},
      'objective':'EV88 exact xx/zz/xz plus 0.25 fidelity; B is baseline and curvature residuals use exact EV88 row records',
      'constraints':'synthetic B +/-0.5 float32 box; selected deterministic D8 witnesses; all 16,002 native faces constrained by closed discs; exact float32 order closure is pinned and baseline identity-tested',
      'admm_parameters':{'rho':RHO,'abs_tol':ABS_TOL,'rel_tol':REL_TOL,'max_iterations':MAX_ITER,'cg_rtol':CG_RTOL,'cg_atol':CG_ATOL,'cg_max_iterations':CG_MAXITER,'rho_adaptation':'same as pinned EV88 every25 to2000, factor2, normalized residual ratio10','numerical_budget_seconds':NUMERIC_BUDGET_S,'peak_working_set_limit_bytes':PEAK_WS_LIMIT},
      'dimensions':{'shape':list(B.shape),'sectors':[64,64],'variables':len(nodes),'protected':int(protected.sum()),'stencils':len(st),'objective_rows':A.shape[0],'d8_rows':C.shape[0],'d8_exempt_strict_minima':len(exempt),'faces':len(radii),'G_shape':list(G.shape),'G_nnz':G.nnz,'C_nnz':C.nnz,'A_nnz':A.nnz},
      'fixtures':fixture,'checks':checks,'float32_order_closure_identity':{'source_path':str(ORDER_CLOSURE),'source_sha256':ORDER_CLOSURE_SHA,'identity_pass':True,'edge_direction':'(witness,center)'},'prepared_path':str(out),'prepared_sha256':prepared_sha,
      'solve_executed':False,'future_acceptance_warning':'Future independent slope consumer must compute coordinate/normal slopes independently; this G operator is not acceptance authority.'}
    report['sources_unchanged']=report['source_pins_start']==report['source_pins_end']
    report['preflight_pass']=bool(report['sources_unchanged'] and report['sources_unchanged'] and report['status']=='PREFLIGHT_PASS_NO_SOLVE')
    path=ROOT/'preflight.json'
    path.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'preflight_pass':report['preflight_pass'],'prepared_sha256':prepared_sha,'report':str(path)},indent=2))


def inf(x): return float(np.max(np.abs(x),initial=0.0))


def make_x_operator(A,C,G,rho):
    At,Ct,Gt=A.T.tocsr(),C.T.tocsr(),G.T.tocsr()
    def mv(v): return At@(A@v)+rho*(v+Ct@(C@v)+Gt@(G@v))
    diag=np.asarray(A.multiply(A).sum(axis=0)).ravel()+rho*(1.+np.asarray(C.multiply(C).sum(axis=0)).ravel()+np.asarray(G.multiply(G).sum(axis=0)).ravel())
    if not np.isfinite(diag).all() or np.any(diag<=0): raise ValueError('Invalid diagonal preconditioner')
    return LinearOperator((A.shape[1],A.shape[1]),matvec=mv,dtype=np.float64),LinearOperator((A.shape[1],A.shape[1]),matvec=lambda v:v/diag,dtype=np.float64),At,Ct,Gt


def x_step_fixtures():
    # Small explicit Hessian comparison validates the matrix-free ADMM x step
    # and affine-face RHS sign without solving any optimization problem.
    A=sparse.csr_matrix([[1.,-2.],[.25,1.],[0.,.5]])
    C=sparse.csr_matrix([[1.,-1.],[-1.,0.]])
    G=sparse.csr_matrix([[1.,0.],[0.,-1.],[1.,-1.],[0.,1.]])
    k=np.array([.3,-.2,.1,.4]);rho=.75
    op,pre,At,Ct,Gt=make_x_operator(A,C,G,rho)
    explicit=At@A+rho*(sparse.eye(2,format='csr')+Ct@C+Gt@G)
    probe=np.array([.7,-1.2]);err=inf(op@probe-explicit@probe)
    assert err<1e-12
    x=np.array([.2,.8]);zb=x.copy();zd=C@x;zs=G@x+k
    # Choose a synthetic residual target with A.T(Ax-rhs)=0 at x, so the
    # expected normal equation isolates the three split terms and affine k.
    rhs=At@(A@x)+rho*(zb+Ct@zd+Gt@(zs-k))
    assert inf(op@x-rhs)<1e-12
    assert np.isfinite(pre@probe).all()
    return {'matrix_free_vs_explicit_max_abs':err,'affine_offset_normal_equation_max_abs':inf(op@x-rhs),
            'diagonal_preconditioner_finite':True,'rho':rho}


def soc_kkt(z,y,radii):
    pairs=z.reshape(-1,2); dual=y.reshape(-1,2); norms=np.linalg.norm(pairs,axis=1); yn=np.linalg.norm(dual,axis=1)
    boundary=np.abs(norms-radii)<=1e-7*np.maximum(1.,radii)
    interior=norms < radii-1e-7*np.maximum(1.,radii)
    comp=np.abs(radii*yn-np.einsum('ij,ij->i',pairs,dual))
    dual_interior=np.max(yn[interior],initial=0.0)
    dots=np.einsum('ij,ij->i',pairs,dual)
    denom=np.einsum('ij,ij->i',pairs,pairs)
    lam=np.divide(dots,denom,out=np.zeros_like(norms),where=denom>0)
    radial=dual-pairs*lam[:,None]
    return {'complementarity_max':float(np.max(comp,initial=0.0)),
            'interior_dual_max':float(dual_interior),
            'boundary_radial_residual_max':float(np.max(np.abs(radial[boundary]),initial=0.0)),
            'negative_radial_multiplier_max':float(np.max(np.maximum(0.0,-lam[boundary]),initial=0.0)),
            'boundary_faces':int(boundary.sum()),'interior_faces':int(interior.sum())}


def solve_admm(A,rhs,C,d,G,k,radii,lo,hi,x0,budget_s=NUMERIC_BUDGET_S,progress=None):
    """One synthetic ADMM/CG solve; returns diagnostics only, no terrain artifact."""
    t0=time.perf_counter();rho=RHO;next_memory_check=0.0
    op,pre,At,Ct,Gt=make_x_operator(A,C,G,rho)
    x=np.asarray(x0,np.float64).copy();zb=np.clip(x,lo,hi);zd=np.maximum(C@x,d)
    q=(G@x+k).reshape(-1,2);zs=project_discs(q,radii).reshape(-1)
    ub=np.zeros_like(zb);ud=np.zeros_like(zd);us=np.zeros_like(zs);target=At@rhs
    history=[];rho_updates=[];status='ITERATION_LIMIT';diag={};cg_total=0
    def guard():
        nonlocal next_memory_check
        elapsed=time.perf_counter()-t0
        if elapsed>budget_s: raise TimeoutError('120s numeric budget exceeded')
        if elapsed>=next_memory_check:
            snap=memory_snapshot()
            if snap['peak_working_set_bytes']>PEAK_WS_LIMIT:
                raise MemoryError('1.5 GiB peak working-set ceiling exceeded')
            next_memory_check=elapsed+1.0
    for it in range(1,MAX_ITER+1):
        guard();ncb=[0]
        def cb(_): ncb[0]+=1;guard()
        right=target+rho*(zb-ub+Ct@(zd-ud)+Gt@(zs-us-k))
        x,info=cg(op,right,x0=x,rtol=CG_RTOL,atol=CG_ATOL,maxiter=CG_MAXITER,M=pre,callback=cb)
        cg_total+=ncb[0]
        if info: raise RuntimeError(f'CG failed info={info} iteration={it}')
        cx=C@x;gx=G@x+k
        oldb,oldd,olds=zb,zd,zs
        zb=np.clip(x+ub,lo,hi);zd=np.maximum(cx+ud,d)
        zs=project_discs((gx+us).reshape(-1,2),radii).reshape(-1)
        ub+=x-zb;ud+=cx-zd;us+=gx-zs
        primal=max(inf(x-zb),inf(cx-zd),inf(gx-zs))
        dual=rho*inf((zb-oldb)+Ct@(zd-oldd)+Gt@(zs-olds))
        dual_vector=rho*(ub+Ct@ud+Gt@us)
        epsp=ABS_TOL+REL_TOL*max(inf(x),inf(cx),inf(zb),inf(zd),inf(gx),inf(zs))
        epsd=ABS_TOL+REL_TOL*inf(dual_vector)
        station=inf(At@(A@x-rhs)+dual_vector)
        diag={'iteration':it,'cg_iterations':cg_total,'rho':rho,'primal':primal,'dual':dual,'stationarity':station,'eps_primal':epsp,'eps_dual':epsd}
        if it==1 or it%200==0:
            entry={**diag,'elapsed_s':time.perf_counter()-t0};history.append(entry)
            if progress: progress(entry)
        if primal<=epsp and dual<=epsd and station<=epsd:
            status='CONVERGED';break
        if it%25==0 and it<=2000:
            newrho=rho
            if primal/epsp>10*dual/epsd:newrho=min(1024.,rho*2.)
            elif dual/epsd>10*primal/epsp:newrho=max(1./1024.,rho/2.)
            if newrho!=rho:
                ub*=rho/newrho;ud*=rho/newrho;us*=rho/newrho
                rho_updates.append({'iteration':it,'old_rho':rho,'new_rho':newrho})
                rho=newrho;op,pre,At,Ct,Gt=make_x_operator(A,C,G,rho)
    elapsed=time.perf_counter()-t0
    yb,yd,ys=rho*ub,rho*ud,rho*us
    normal=max(inf(zb-np.clip(zb+yb/rho,lo,hi)),inf(zd-np.maximum(zd+yd/rho,d)),
               inf(zs.reshape(-1,2)-project_discs((zs+ys).reshape(-1,2),radii)))
    cone=soc_kkt(zs,ys,radii)
    return x,{'status':status,**diag,'elapsed_s':elapsed,'rho_updates':rho_updates,
              'normal_cone_projection_residual':normal,'soc_complementarity':cone,
              'saved_stationarity':inf(At@(A@x-rhs)+yb+Ct@yd+Gt@ys),
              'peak_memory':memory_snapshot(),'budget_seconds':budget_s,'peak_ws_limit_bytes':PEAK_WS_LIMIT},history,{'y_box':yb,'y_d8':yd,'y_face':ys,'z_box':zb,'z_d8':zd,'z_face':zs}


def run_solve_once():
    report_path=ROOT/'preflight.json';prepared_path=ROOT/'prepared.npz';out=ROOT/'solve-once'
    if not report_path.is_file() or not prepared_path.is_file(): raise RuntimeError('Successful preflight required')
    if out.exists(): raise FileExistsError('solve-once output exists; refusing a second run')
    report=json.loads(report_path.read_text(encoding='utf-8-sig'))
    if report.get('status')!='PREFLIGHT_PASS_NO_SOLVE' or report.get('solve_executed') is not False:
        raise RuntimeError('Preflight report is not eligible for solve')
    if sha(prepared_path)!=report.get('prepared_sha256'): raise RuntimeError('Prepared arrays changed')
    for path,expected in report.get('source_pins_end',{}).items():
        if sha(Path(path))!=expected: raise RuntimeError(f'Pinned source changed: {path}')
    closure_mod=load_order_closure();out.mkdir();started=time.perf_counter()
    try:
        with np.load(prepared_path,allow_pickle=False) as z:
            B=z['baseline_float32'].astype(np.float64);nodes=z['variables_rc'].astype(np.int32)
            lo=z['lower_float32'].astype(np.float64);hi=z['upper_float32'].astype(np.float64)
            A=sparse.csr_matrix((z['A_data'],z['A_indices'],z['A_indptr']),shape=tuple(map(int,z['A_shape'])))
            C=sparse.csr_matrix((z['C_data'],z['C_indices'],z['C_indptr']),shape=tuple(map(int,z['C_shape'])))
            G=sparse.csr_matrix((z['G_data'],z['G_indices'],z['G_indptr']),shape=tuple(map(int,z['G_shape'])))
            rhs=z['rhs'].copy();d=z['d8_rhs'].copy();k=z['face_offset_k'].copy();radii=z['face_radii'].copy()
            centers=z['witness_centers_rc'].copy();neighbors=z['witness_neighbors_rc'].copy()
        x0=B[tuple(nodes.T)].astype(np.float64)
        def progress(row):
            with (out/'progress.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(row,allow_nan=False)+'\n')
        numerical_started=time.perf_counter()
        x,solver,history,state=solve_admm(A,rhs,C,d,G,k,radii,lo,hi,x0,NUMERIC_BUDGET_S,progress)
        baseline32=B.astype(np.float32);raw_grid=baseline32.copy();raw_grid[tuple(nodes.T)]=x.astype(np.float32)
        raw_flat=raw_grid.ravel();base_flat=baseline32.ravel();n_total=base_flat.size
        lower_flat=base_flat.copy();upper_flat=base_flat.copy();fixed_flat=np.ones(n_total,bool)
        node_ids=np.ravel_multi_index((nodes[:,0],nodes[:,1]),B.shape);fixed_flat[node_ids]=False
        lower_flat[node_ids]=lo.astype(np.float32);upper_flat[node_ids]=hi.astype(np.float32)
        edge_ids=np.column_stack((np.ravel_multi_index((neighbors[:,0],neighbors[:,1]),B.shape),
                                  np.ravel_multi_index((centers[:,0],centers[:,1]),B.shape))).astype(np.int64)
        def closure_guard():
            if time.perf_counter()-numerical_started>NUMERIC_BUDGET_S:
                raise TimeoutError('120 s total numeric budget exceeded during float32 D8 closure')
            if memory_snapshot()['peak_working_set_bytes']>PEAK_WS_LIMIT:
                raise MemoryError('1.5 GiB working-set limit exceeded during float32 closure')
        closure_started=time.perf_counter()
        closure=closure_mod.project_order(raw_flat,lower_flat,upper_flat,edge_ids,
            baseline=base_flat,fixed=fixed_flat,guard=closure_guard)
        closed_flat=closure['q'];closed_grid=closed_flat.reshape(B.shape)
        closure_s=time.perf_counter()-closure_started
        raw_values=raw_flat[node_ids].astype(np.float64);closed_values=closed_flat[node_ids].astype(np.float64)
        objective=lambda v:.5*float(np.dot(A@v-rhs,A@v-rhs))
        base_cost=objective(x0);raw_cost=objective(raw_values);closed_cost=objective(closed_values)
        closure_energy=closure_mod.evaluate_objective_gates(raw_cost,closed_cost,base_cost)
        raw_d8_bad=int(np.count_nonzero(raw_grid[tuple(centers.T)]<raw_grid[tuple(neighbors.T)]))
        closed_d8_bad=int(np.count_nonzero(closed_grid[tuple(centers.T)]<closed_grid[tuple(neighbors.T)]))
        raw_bounds_bad=int(np.count_nonzero((raw_values<lo)|(raw_values>hi)))
        closed_bounds_bad=int(np.count_nonzero((closed_values<lo)|(closed_values>hi)))
        qraw=face_gradients_direct(raw_grid.astype(np.float64));qclosed=face_gradients_direct(closed_grid.astype(np.float64))
        qop=(G@raw_values+k).reshape(-1,2)
        raw_norm=np.linalg.norm(qraw.reshape(-1,2),axis=1);closed_norm=np.linalg.norm(qclosed.reshape(-1,2),axis=1)
        raw_angles=face_slopes_from_q(qraw);closed_angles=face_slopes_from_q(qclosed)
        base_angles=face_slopes_from_q(face_gradients_direct(B))
        allowed=np.maximum(base_angles,35.0)+ANG_TOL
        closed_angular_bad=int(np.count_nonzero(closed_angles>allowed))
        result_checks={'solver_converged':solver['status']=='CONVERGED',
          'raw_float32_bounds_bad':raw_bounds_bad,'closed_float32_bounds_bad':closed_bounds_bad,
          'raw_float32_d8_bad':raw_d8_bad,'closed_float32_d8_bad':closed_d8_bad,
          'closed_angular_slope_bad':closed_angular_bad,
          'closure_energy_budget_pass':closure_energy['closure_budget_pass'],
          'strict_improvement_vs_B':closure_energy['strict_improvement_vs_baseline'],
          'G_vs_coordinate_q_max_abs_error':float(np.max(np.abs(qop-qraw.reshape(-1,2)),initial=0.0)),
          'within_total_numeric_budget':time.perf_counter()-numerical_started<=NUMERIC_BUDGET_S,
          'within_peak_ws_limit':memory_snapshot()['peak_working_set_bytes']<=PEAK_WS_LIMIT}
        result={'status':'SYNTHETIC_DIAGNOSTIC_ONLY','solver':solver,'history':history,'checks':result_checks,
          'objective_B':base_cost,'objective_raw_float32':raw_cost,'objective_closed_float32':closed_cost,
          'closure_energy':closure_energy,
          'closure':{key:value for key,value in closure.items() if key not in ('q','clipped','upper_propagated')},
          'closure_seconds':closure_s,'float32_raw_max_slope_deg':float(np.max(raw_angles,initial=0.0)),
          'float32_closed_max_slope_deg':float(np.max(closed_angles,initial=0.0)),
          'float32_raw_disc_excess_count_diagnostic_only':int(np.count_nonzero(raw_norm>radii)),
          'float32_closed_disc_excess_count_diagnostic_only':int(np.count_nonzero(closed_norm>radii)),
          'float32_closed_max_disc_excess_raw_units_diagnostic_only':float(np.max(closed_norm-radii,initial=-np.inf)),
          'acceptance_authority':'NONE_SYNTHETIC_PILOT_ONLY; production slope acceptance belongs to independent consumer',
          'readset_start':report['source_pins_end']}
        result['elapsed_numeric_solver_plus_closure_s']=time.perf_counter()-numerical_started
        np.savez_compressed(out/'solution.npz',baseline_float32=baseline32,raw_float32_grid=raw_grid,
            closed_float32_grid=closed_grid,variables_rc=nodes,solution_float64=x,
            face_gradient_q_raw_operator=qop,face_gradient_q_raw_coordinates=qraw.reshape(-1,2),
            face_radii=radii,face_slopes_raw_deg=raw_angles,face_slopes_closed_deg=closed_angles,
            closure_clipped=closure['clipped'],closure_upper_propagated=closure['upper_propagated'],
            y_box=state['y_box'],y_d8=state['y_d8'],y_face=state['y_face'],
            z_box=state['z_box'],z_d8=state['z_d8'],z_face=state['z_face'])
        result['solution_path']=str(out/'solution.npz');result['solution_sha256']=sha(out/'solution.npz')
        result['readset_end']={path:sha(Path(path)) for path in report['source_pins_end']}
        result['readset_stable']=result['readset_start']==result['readset_end']
        result['elapsed_including_io_s']=time.perf_counter()-started
        result['synthetic_solver_diagnostic_pass']=bool(
          result_checks['solver_converged'] and result_checks['raw_float32_bounds_bad']==0 and
          result_checks['closed_float32_bounds_bad']==0 and result_checks['closed_float32_d8_bad']==0 and
          result_checks['closed_angular_slope_bad']==0 and result_checks['closure_energy_budget_pass'] and
          result_checks['strict_improvement_vs_B'] and result_checks['G_vs_coordinate_q_max_abs_error']<=1e-11 and
          result_checks['within_total_numeric_budget'] and result_checks['within_peak_ws_limit'] and result['readset_stable'])
        result_path=out/'solve-result.json';result_path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        print(json.dumps({'status':result['status'],'synthetic_solver_diagnostic_pass':result['synthetic_solver_diagnostic_pass'],
                          'solution_sha256':result['solution_sha256'],'result':str(result_path)},indent=2))
    except Exception as exc:
        failed={'status':'SYNTHETIC_SOLVE_FAILED','error':repr(exc),'elapsed_s':time.perf_counter()-started,
                'prepared_sha256':sha(prepared_path),'preflight_sha256':sha(report_path),'candidate_or_map_output':False}
        (out/'solve-result.json').write_text(json.dumps(failed,indent=2)+'\n',encoding='utf-8')
        raise


def main():
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--preflight',action='store_true')
    mode.add_argument('--solve-once',action='store_true')
    args=ap.parse_args()
    if args.preflight:
        preflight()
    else:
        run_solve_once()

if __name__=='__main__':
    main()
