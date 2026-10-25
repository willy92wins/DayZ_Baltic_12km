from __future__ import annotations
import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

from structured_operator import build_operators, d8_witness_arrays, validate_domain

ROOT = Path(__file__).resolve().parents[1]
EV88_PATH = ROOT / 'prototype.py'
CP_PATH = ROOT / 'face-slope-cone-pilot' / 'pilot.py'
PINS = {
    EV88_PATH: '5b4b8f08e5205e1f9cc90bcc8e82e61dade45bb82bd22da8ee69303aa4475cc4',
    CP_PATH: 'd743f5006e0aa6606024a3c3291a74cb52b78f76c1aa5c6dfd95cdd26cdc9d2a',
}


def load_pinned(path, expected, name):
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise AssertionError(f'{name} source pin mismatch: {actual}')
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def references(B, nodes, ev88, cp):
    stencils = ev88.all_stencils(B.shape, nodes)
    records = ev88.row_records(B, nodes, stencils)
    A, rhs = ev88.csr_from_records(records, len(nodes))
    witnesses, exempt = cp.d8_witnesses(B)
    C, d = cp.build_d8(B, nodes, witnesses)
    G, k, radii, face_keys, qB, anglesB, direct = cp.build_face_operator(B, nodes)
    return (stencils, records, A, rhs, witnesses, exempt, C, d, G, k,
            radii, face_keys, qB, anglesB, direct)


def adjoint_error(op, seed):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=op.shape[1])
    y = rng.normal(size=op.shape[0])
    lhs = float(np.dot(op.matvec(x), y))
    rhs = float(np.dot(x, op.rmatvec(y)))
    return abs(lhs-rhs)


def run_fixtures():
    ev88 = load_pinned(EV88_PATH, PINS[EV88_PATH], 'ev88_reference')
    cp = load_pinned(CP_PATH, PINS[CP_PATH], 'cp_reference')
    h, w = 11, 132
    rr, cc = np.indices((h,w))
    B = (0.17*rr**2 - 0.09*cc + 0.003*rr*cc + np.sin(cc/7.0)).astype(np.float64)
    # Explicit lexicographic D8 tie, with all other surrounding values higher.
    B[2:5,62:65] = 20.0
    B[2,62] = B[2,64] = 1.0
    B[3,63] = 5.0
    # A strict local minimum is exempt from the D8 rows.
    B[5:8,62:65] = 7.0
    B[6,63] = 0.0

    variable = ((rr*13 + cc*7) % 5 != 0)
    # Include seam-crossing xz stencils and explicit D8 endpoints.
    variable[4,63] = True
    variable[6,65] = True
    variable[3,63] = True
    variable[2,62] = False
    variable[2,64] = True
    variable[6,63] = False
    nodes = np.column_stack(np.nonzero(variable)).astype(np.int32)

    op = build_operators(B, nodes)
    (stencils, records, A, rhsA, witnesses, exempt, C, d, G, k,
     radii, face_keys, qB, anglesB, direct) = references(B, nodes, ev88, cp)
    assert op.n_a == A.shape[0] and op.n_c == C.shape[0] and op.n_g == G.shape[0]
    assert np.array_equal(op.xx_rc, np.asarray([(r,c) for kind,r,c in stencils if kind=='xx'],dtype=np.int32))
    assert np.array_equal(op.zz_rc, np.asarray([(r,c) for kind,r,c in stencils if kind=='zz'],dtype=np.int32))
    assert np.array_equal(op.xz_rc, np.asarray([(r,c) for kind,r,c in stencils if kind=='xz'],dtype=np.int32))
    assert np.array_equal(op.d8_centers, np.asarray([x['center'][0]*w+x['center'][1] for x in witnesses],dtype=np.int32))
    assert np.array_equal(op.d8_witnesses, np.asarray([x['witness'][0]*w+x['witness'][1] for x in witnesses],dtype=np.int32))
    tie = 3*w+63
    tie_row = int(np.flatnonzero(op.d8_centers == tie)[0])
    assert op.d8_witnesses[tie_row] == 2*w+62, 'D8 tie did not choose lexicographically first neighbor'
    assert (6,63) in exempt

    rng = np.random.default_rng(20261010)
    checks = {}
    for probe in range(3):
        x = rng.normal(size=len(nodes))
        ya = rng.normal(size=A.shape[0]); yc = rng.normal(size=C.shape[0]); yg = rng.normal(size=G.shape[0])
        checks[f'probe{probe}_A_matvec'] = float(np.max(np.abs(op.matvec_a(x)-A@x),initial=0.0))
        checks[f'probe{probe}_A_rmatvec'] = float(np.max(np.abs(op.rmatvec_a(ya)-A.T@ya),initial=0.0))
        checks[f'probe{probe}_C_matvec'] = float(np.max(np.abs(op.matvec_c(x)-C@x),initial=0.0))
        checks[f'probe{probe}_C_rmatvec'] = float(np.max(np.abs(op.rmatvec_c(yc)-C.T@yc),initial=0.0))
        checks[f'probe{probe}_G_matvec'] = float(np.max(np.abs(op.matvec_g(x)-G@x),initial=0.0))
        checks[f'probe{probe}_G_rmatvec'] = float(np.max(np.abs(op.rmatvec_g(yg)-G.T@yg),initial=0.0))
    assert max(checks.values()) < 1e-11, checks

    # Deliberate mutants must be caught by the independent CSR fixture.
    seam_x = np.zeros(len(nodes), dtype=np.float64)
    seam_x[np.flatnonzero(np.all(nodes == [4,63],axis=1))[0]] = 1.0
    seam_x[np.flatnonzero(np.all(nodes == [6,65],axis=1))[0]] = -0.5
    seam_ref = A @ seam_x
    seam_actual = op.matvec_a(seam_x)
    assert np.max(np.abs(seam_actual-seam_ref),initial=0.0) < 1e-12
    xzrow = len(op.xx_rc)+len(op.zz_rc)+int(np.flatnonzero(np.all(op.xz_rc==[4,63],axis=1))[0])
    assert abs(seam_actual[xzrow]) > 0.0, 'column-64 seam probe did not reach the cross stencil'
    wrong_g = op.matvec_g(seam_x).copy().reshape(h-1,w-1,4)
    wrong_g[:,:,1] *= -1.0
    assert np.max(np.abs(wrong_g.reshape(-1)-G@seam_x),initial=0.0) > 1e-6, 'z-sign mutant escaped fixture'

    aop, cop, gop = op.operator_a(), op.operator_c(), op.operator_g()
    adjoints = {'A':max(adjoint_error(aop,11),adjoint_error(aop,12)),
                'C':max(adjoint_error(cop,21),adjoint_error(cop,22)),
                'G':max(adjoint_error(gop,31),adjoint_error(gop,32))}
    assert max(adjoints.values()) < 1e-11, adjoints

    diag_a = np.asarray(A.multiply(A).sum(axis=0)).ravel()
    diag_c = np.asarray(C.multiply(C).sum(axis=0)).ravel()
    diag_g = np.asarray(G.multiply(G).sum(axis=0)).ravel()
    diag_errors = {'A':float(np.max(np.abs(op.diag_a-diag_a),initial=0.0)),
                   'C':float(np.max(np.abs(op.diag_c-diag_c),initial=0.0)),
                   'G':float(np.max(np.abs(op.diag_g-diag_g),initial=0.0))}
    assert max(diag_errors.values()) < 1e-12, diag_errors

    rho=.73
    H=A.T@A+rho*(sparse.eye(len(nodes),format='csr')+C.T@C+G.T@G)
    x=rng.normal(size=len(nodes))
    normal_err=float(np.max(np.abs(op.normal_operator(rho)@x-H@x),initial=0.0))
    normal_diag=np.asarray(H.diagonal())
    diag_err=float(np.max(np.abs(op.normal_diagonal(rho)-normal_diag),initial=0.0))
    rhs_a=rng.normal(size=A.shape[0]);zi=rng.normal(size=len(nodes));zc=rng.normal(size=C.shape[0]);zg=rng.normal(size=G.shape[0])
    normal_rhs=op.normal_rhs(rhs_a,zi,zc,zg,rho)
    normal_rhs_ref=A.T@rhs_a+rho*(zi+C.T@zc+G.T@(zg-k))
    rhs_err=float(np.max(np.abs(normal_rhs-normal_rhs_ref),initial=0.0))
    assert normal_err<1e-11 and diag_err<1e-11 and rhs_err<1e-11,(normal_err,diag_err,rhs_err)

    # Invalid-input tests exercise production validation paths.
    negatives=[]
    for label, fn in [
        ('nonfinite_base',lambda:build_operators(np.where(np.indices((3,3))[0]==0,np.nan,0.0),np.array([[1,1]]))),
        ('empty_variables',lambda:build_operators(np.zeros((3,3)),np.empty((0,2),dtype=np.int32))),
        ('duplicate_variables',lambda:build_operators(np.zeros((3,3)),np.array([[1,1],[1,1]],dtype=np.int32))),
        ('unsorted_variables',lambda:build_operators(np.zeros((3,3)),np.array([[2,0],[1,2]],dtype=np.int32))),
        ('outside_variable',lambda:build_operators(np.zeros((3,3)),np.array([[3,0]],dtype=np.int32))),
    ]:
        try: fn()
        except ValueError: negatives.append(label)
        else: raise AssertionError(f'{label} unexpectedly accepted')
    for label, fn in [('wrong_A_length',lambda:op.matvec_a(np.zeros(op.n+1))),
                      ('nonfinite_C_input',lambda:op.matvec_c(np.full(op.n,np.inf))),
                      ('wrong_G_adjoint_length',lambda:op.rmatvec_g(np.zeros(op.n_g-1))),
                      ('invalid_rho',lambda:op.normal_operator(0.0))]:
        try: fn()
        except ValueError: negatives.append(label)
        else: raise AssertionError(f'{label} unexpectedly accepted')

    return {'status':'PASS_MATRIX_FREE_FIXTURES','base_shape':[h,w], 'variables':len(nodes),
            'environment':{'python_executable':sys.executable,'python_version':platform.python_version()},
            'source_pins':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in PINS},
            'operator_source_sha256':hashlib.sha256(Path(__file__).with_name('structured_operator.py').read_bytes()).hexdigest(),
            'A_shape':list(A.shape),'C_shape':list(C.shape),'G_shape':list(G.shape),
            'A_rhs_max_abs':float(np.max(np.abs(op.rhs_a-rhsA),initial=0.0)),
            'C_d_max_abs':float(np.max(np.abs(op.d_c-d),initial=0.0)),
            'G_k_max_abs':float(np.max(np.abs(op.k_g-k),initial=0.0)),
            'operator_max_abs_checks':checks,'adjoint_abs_errors':adjoints,
            'diagonal_abs_errors':diag_errors,'normal_operator_abs_error':normal_err,
            'normal_diagonal_abs_error':diag_err,'normal_rhs_abs_error':rhs_err,
            'negative_cases_rejected':negatives,
            'seam_xz_anchor_present':bool(np.any(np.all(op.xz_rc==[4,63],axis=1)))}


if __name__ == '__main__':
    print(json.dumps(run_fixtures(),indent=2,allow_nan=False))
