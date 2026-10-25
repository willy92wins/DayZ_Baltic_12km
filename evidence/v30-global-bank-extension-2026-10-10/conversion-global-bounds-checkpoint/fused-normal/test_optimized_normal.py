from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
from scipy import sparse

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
sys.path.insert(0,str(PARENT))
from structured_operator import build_operators
from fused_normal import FusedNormalAction
import test_structured_operator as ref


def pinned(path,expected,name):
    actual=ref.hashlib.sha256(path.read_bytes()).hexdigest()
    if actual!=expected:
        raise AssertionError(f'{name} pin mismatch: {actual}')
    return ref.load_pinned(path,expected,name)


def maxerr(a,b):
    return float(np.max(np.abs(np.asarray(a)-np.asarray(b)),initial=0.0))


def run():
    ev88=pinned(ref.EV88_PATH,ref.PINS[ref.EV88_PATH],'ev88_optimized_normal_ref')
    cp=pinned(ref.CP_PATH,ref.PINS[ref.CP_PATH],'cp_optimized_normal_ref')
    rng=np.random.default_rng(20261010)
    cases=[]

    # Degenerate row/column dimensions exercise empty xx/zz/xz stencil families.
    for shape in ((1,7),(2,4),(4,2)):
        h,w=shape
        rr,cc=np.indices(shape)
        B=(.2*rr**2-.11*cc+.03*rr*cc).astype(np.float64)
        variable=np.ones(shape,dtype=bool)
        if variable.size>3: variable.flat[1::3]=False
        nodes=np.column_stack(np.nonzero(variable)).astype(np.int32)
        cases.append((f'edge_{h}x{w}',B,nodes))

    # Mixed masks, row-major seam stencils, D8 ties and local minimum exemption.
    h,w=11,132
    rr,cc=np.indices((h,w))
    B=(.17*rr**2-.09*cc+.003*rr*cc+np.sin(cc/7.0)).astype(np.float64)
    B[2:5,62:65]=20.;B[2,62]=B[2,64]=1.;B[3,63]=5.
    B[5:8,62:65]=7.;B[6,63]=0.
    variable=((rr*13+cc*7)%5!=0)
    variable[4,63]=True;variable[6,65]=True;variable[3,63]=True
    variable[2,62]=False;variable[2,64]=True;variable[6,63]=False
    nodes=np.column_stack(np.nonzero(variable)).astype(np.int32)
    cases.append(('mixed_tie_seam',B,nodes))

    # Fully variable interior and random mask verify row masks do not lose active anchors.
    for name,shape,mode in (('fully_variable',(8,9),'all'),('sparse_mask',(9,10),'random')):
        h,w=shape;rr,cc=np.indices(shape)
        B=(.03*rr**2+.07*cc**2-.02*rr*cc+np.cos(rr+cc)).astype(np.float64)
        variable=np.ones(shape,dtype=bool) if mode=='all' else (rng.random(shape)>.43)
        if not variable.any():variable[shape[0]//2,shape[1]//2]=True
        nodes=np.column_stack(np.nonzero(variable)).astype(np.int32)
        cases.append((name,B,nodes))

    case_reports=[]
    for name,B,nodes in cases:
        op=build_operators(B,nodes)
        fast=FusedNormalAction(op)
        stencils,records,A,rhsA,witnesses,exempt,C,d,G,k,*_=ref.references(B,nodes,ev88,cp)
        rho=.73
        x=rng.normal(size=len(nodes))
        csr=(A.T@A+rho*(sparse.eye(len(nodes),format='csr')+C.T@C+G.T@G)).tocsr()
        expected=csr@x
        fused=fast.matvec(x,rho)
        old=op.normal_operator(rho)@x
        a_fused=fast.a_normal(x)
        a_expected=A.T@(A@x)
        diag=np.asarray(csr.diagonal())
        lin=fast.linear_operator(rho)
        y=rng.normal(size=len(nodes))
        adjoint_error=abs(float(np.dot(lin.matvec(x),y)-np.dot(x,lin.rmatvec(y))))
        checks={'fused_vs_csr':maxerr(fused,expected),
                'fused_vs_old_matrix_free':maxerr(fused,old),
                'fused_A_vs_csr':maxerr(a_fused,a_expected),
                'diagonal_vs_csr':maxerr(fast.diagonal(rho),diag),
                'normal_adjoint_abs_error':adjoint_error,
                'xx_anchor_mask_count':int(np.count_nonzero(fast.xx_rows)),
                'xx_anchor_count':int(len(op.xx_rc)),
                'zz_anchor_mask_count':int(np.count_nonzero(fast.zz_rows)),
                'zz_anchor_count':int(len(op.zz_rc)),
                'xz_anchor_mask_count':int(np.count_nonzero(fast.xz_rows)),
                'xz_anchor_count':int(len(op.xz_rc))}
        assert checks['fused_vs_csr']<1e-10, (name,checks)
        assert checks['fused_vs_old_matrix_free']<1e-10, (name,checks)
        assert checks['fused_A_vs_csr']<1e-10, (name,checks)
        assert checks['diagonal_vs_csr']<1e-10, (name,checks)
        assert checks['normal_adjoint_abs_error']<1e-10, (name,checks)
        assert checks['xx_anchor_mask_count']==checks['xx_anchor_count']
        assert checks['zz_anchor_mask_count']==checks['zz_anchor_count']
        assert checks['xz_anchor_mask_count']==checks['xz_anchor_count']
        case_reports.append({'case':name,'shape':list(B.shape),'variables':len(nodes),
                             'A_rows':op.n_a,'C_rows':op.n_c,'G_rows':op.n_g,'checks':checks})

    small=build_operators(np.arange(30,dtype=np.float64).reshape(5,6),
                          np.column_stack(np.nonzero(np.ones((5,6),dtype=bool))).astype(np.int32))
    fn=FusedNormalAction(small)
    negative=[]
    for label,action in (
        ('wrong_length',lambda:fn.matvec(np.zeros(small.n+1),.5)),
        ('nonfinite_x',lambda:fn.matvec(np.full(small.n,np.nan),.5)),
        ('invalid_rho',lambda:fn.matvec(np.zeros(small.n),0.0)),
    ):
        try:action()
        except ValueError:negative.append(label)
        else:raise AssertionError(f'{label} unexpectedly accepted')
    return {'status':'PASS_FUSED_NORMAL_FIXTURES','operator_reference_sha256':ref.hashlib.sha256(
                (PARENT/'structured_operator.py').read_bytes()).hexdigest(),
            'cp_reference_sha256':ref.PINS[ref.CP_PATH],
            'ev88_reference_sha256':ref.PINS[ref.EV88_PATH],
            'cases':case_reports,'negative_cases_rejected':negative,
            'tolerance_abs_max':1e-10,'solver_called':False,'global_benchmark_called':False}


if __name__=='__main__':
    print(json.dumps(run(),indent=2,allow_nan=False))
