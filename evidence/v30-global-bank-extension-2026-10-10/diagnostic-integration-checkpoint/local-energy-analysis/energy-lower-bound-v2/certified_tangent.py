"""Exact-rational tangent/dual lower-bound primitives; no LP or terrain solve."""
from __future__ import annotations
from fractions import Fraction
import math
import numpy as np


def Q(v):
    """Treat stored IEEE floats as their exact binary rational value."""
    if isinstance(v, Fraction):
        return v
    if isinstance(v, (int, np.integer)):
        return Fraction(int(v))
    f = float(v)
    if not math.isfinite(f):
        raise ValueError("non-finite scalar")
    return Fraction.from_float(f)


def _add_ge(rows, coeffs, rhs, label):
    row = {int(i): Q(v) for i, v in coeffs.items() if Q(v) != 0}
    rows.append((row, Q(rhs), str(label)))


def build_physical_rows(base_f32, variables_rc, lo_f32, hi_f32,
                        crossings=(), signs=(), d8_witnesses=(), fixed_indices=()):
    """Build exact Mx>=b for physical P/F crossings/signs, D8 and inward box.

    Variables are absolute heights, in the exact order of variables_rc. Every
    non-variable context node is substituted as its pinned float32 baseline.
    Strict signs are weakened to non-strict signs, so this is a safe superset.
    """
    base=np.asarray(base_f32)
    rc=np.asarray(variables_rc,dtype=np.int64)
    lo=np.asarray(lo_f32); hi=np.asarray(hi_f32)
    if base.ndim!=2 or base.dtype!=np.float32 or rc.ndim!=2 or rc.shape[1]!=2:
        raise ValueError("base must be 2-D float32 and variables_rc must be n×2")
    n=len(rc)
    if lo.dtype!=np.float32 or hi.dtype!=np.float32 or lo.shape!=(n,) or hi.shape!=(n,):
        raise ValueError("lo/hi must be float32 vectors aligned with variables")
    if len(set(map(tuple,rc.tolist())))!=n or np.any(lo>hi):
        raise ValueError("duplicate variables or reversed bounds")
    var={tuple(map(int,p)):i for i,p in enumerate(rc.tolist())}
    rows=[]
    def affine_ge(terms,label):
        # terms: [(coefficient, rc, level)] represents sum c*(H_rc-level)>=0.
        coeff={}; constant=Fraction(0)
        for c0,p0,l0 in terms:
            c=Q(c0); p=tuple(map(int,p0)); level=Q(l0)
            if p in var:
                i=var[p]; coeff[i]=coeff.get(i,Fraction(0))+c
                constant-=c*level
            else:
                r,cidx=p
                if not (0<=r<base.shape[0] and 0<=cidx<base.shape[1]):
                    raise ValueError(f"fixed endpoint outside context: {p}")
                constant+=c*(Q(base[p])-level)
        _add_ge(rows,coeff,-constant,label)
    for k,s in enumerate(signs):
        p=tuple(map(int,s.rc)); sign=int(s.sign); level=Q(s.level)
        if sign==0:
            if s.baseline is None: raise ValueError("contact sign has no pinned baseline")
            target=Q(np.float32(s.baseline))
            affine_ge(((1,p,target),),f"sign_contact_lower:{k}")
            affine_ge(((-1,p,target),),f"sign_contact_upper:{k}")
        elif sign==1:
            affine_ge(((1,p,level),),f"sign_above_relaxed:{k}")
        elif sign==-1:
            affine_ge(((-1,p,level),),f"sign_below_relaxed:{k}")
        else: raise ValueError("sign must be -1, 0, or +1")
    for k,s in enumerate(crossings):
        endpoints=(tuple(map(int,s.a_rc)),tuple(map(int,s.b_rc)))
        levels=(Q(s.level_a),Q(s.level_b)); dry=int(s.dry_endpoint)
        if dry not in (0,1): raise ValueError("dry_endpoint must be 0 or 1")
        wet=1-dry; tl=Q(s.t_lower); tu=Q(s.t_upper)
        if not (Fraction(0)<=tl<=tu<=Fraction(1)):
            raise ValueError("crossing interval outside [0,1]")
        # Relax the source strict dry>level / wet<level to non-strict.
        affine_ge(((1,endpoints[dry],levels[dry]),),f"cross_dry_sign_relaxed:{k}")
        affine_ge(((-1,endpoints[wet],levels[wet]),),f"cross_wet_sign_relaxed:{k}")
        # t>=tl: (1-tl)dD + tl*dW >= 0.
        affine_ge(((1-tl,endpoints[dry],levels[dry]),
                   (tl,endpoints[wet],levels[wet])),f"cross_lower:{k}")
        # t<=tu: -(1-tu)dD - tu*dW >= 0.
        affine_ge(((-(1-tu),endpoints[dry],levels[dry]),
                   (-tu,endpoints[wet],levels[wet])),f"cross_upper:{k}")
    for k,(center,witness) in enumerate(d8_witnesses):
        center=tuple(map(int,center)); witness=tuple(map(int,witness))
        affine_ge(((1,center,0),(-1,witness,0)),f"d8_center_ge_witness:{k}")
    fixed=set(map(int,fixed_indices))
    if any(i<0 or i>=n for i in fixed): raise ValueError("fixed index outside variable list")
    for i in sorted(fixed):
        target=Q(base[tuple(map(int,rc[i]))])
        _add_ge(rows,{i:1},target,f"source_fixed_lower:{i}")
        _add_ge(rows,{i:-1},-target,f"source_fixed_upper:{i}")
    for i in range(n):
        _add_ge(rows,{i:1},Q(lo[i]),f"box_lower:{i}")
        _add_ge(rows,{i:-1},-Q(hi[i]),f"box_upper:{i}")
    return rows


def objective_tangent(A_rows, rhs, xref):
    """Return exact J(xref), g=A.T(A*xref-rhs), and tangent intercept."""
    x=[Q(v) for v in xref]
    b=[Q(v) for v in rhs]
    if len(A_rows)!=len(b): raise ValueError("A/rhs row mismatch")
    grad=[Fraction(0) for _ in x]; J=Fraction(0)
    for row,bi in zip(A_rows,b):
        e=-bi
        for j,a in row.items():
            if not (0<=int(j)<len(x)): raise ValueError("A column outside x")
            e+=Q(a)*x[int(j)]
        J+=e*e/2
        for j,a in row.items(): grad[int(j)]+=Q(a)*e
    intercept=J-sum((a*v for a,v in zip(grad,x)),Fraction(0))
    return J,grad,intercept


def dual_tangent_lower_bound(Jref, grad, intercept, rows, lo, hi, multipliers):
    """Exact valid lower bound for min tangent over Mx>=b and lo<=x<=hi.

    `rows` is the physical-row list from build_physical_rows; box rows are
    included for LP construction/readback, while residual minimization uses the
    supplied finite box. Any nonnegative dual vector is valid; optimality is
    not assumed. Negative/nonfinite multipliers fail closed.
    """
    g=[Q(v) for v in grad]; l=[Q(v) for v in lo]; h=[Q(v) for v in hi]
    if len(g)!=len(l) or len(g)!=len(h) or len(rows)!=len(multipliers):
        raise ValueError("certificate dimensions mismatch")
    residual=list(g); dual_rhs=Fraction(0)
    for (row,b,label),lam0 in zip(rows,multipliers):
        lam=Q(lam0)
        if lam<0: raise ValueError(f"negative dual multiplier at {label}")
        dual_rhs+=lam*Q(b)
        for j,a in row.items(): residual[int(j)]-=lam*Q(a)
    box_resid=sum((min(r*li,r*ui) for r,li,ui in zip(residual,l,h)),Fraction(0))
    return Q(intercept)+dual_rhs+box_resid


def csr_rows_from_arrays(data, indices, indptr, shape):
    """Convert canonical CSR storage to exact-rational sparse rows."""
    m,n=map(int,shape); data=np.asarray(data); indices=np.asarray(indices); indptr=np.asarray(indptr)
    if data.ndim!=1 or indices.shape!=data.shape or indptr.shape!=(m+1,) or int(indptr[0])!=0 or int(indptr[-1])!=len(data):
        raise ValueError("malformed CSR arrays")
    rows=[]
    for i in range(m):
        a=int(indptr[i]); z=int(indptr[i+1])
        if np.any(indices[a:z]<0) or np.any(indices[a:z]>=n): raise ValueError("CSR index out of range")
        cols=indices[a:z].astype(int).tolist()
        if len(set(cols))!=len(cols): raise ValueError("CSR row has duplicate columns")
        rows.append({j:Q(v) for j,v in zip(cols,data[a:z]) if Q(v)!=0})
    return rows


def csr_float64_eval_error_bound(A_rows, rhs, lo, hi):
    """Outward error bound for CSR float64 matvec, residual, square, and sum.

    Assumes IEEE-754 binary64 round-to-nearest and finite normal terrain-domain
    magnitudes. Includes an additive least-subnormal allowance per operation;
    rejects bounds approaching overflow. It bounds |J_float64(x)-J_exact(x)|
    uniformly over the closed box, for x represented as float64.
    """
    u=Fraction(1,1<<53); eta=Fraction(1,1<<1074)
    l=[Q(v) for v in lo]; h=[Q(v) for v in hi]
    if len(l)!=len(h): raise ValueError("box shape mismatch")
    rhs=[Q(v) for v in rhs]
    if len(A_rows)!=len(rhs): raise ValueError("A/rhs row mismatch")
    m=len(A_rows)
    def gamma(k):
        ku=int(k)*u
        if ku>=1: raise ValueError("operation count invalid for roundoff bound")
        return ku/(1-ku)
    sum_t_upper=Fraction(0); row_error_sum=Fraction(0); row_ops=0
    for row,b in zip(A_rows,rhs):
        S=Fraction(0)
        for j,a0 in row.items():
            j=int(j); a=abs(Q(a0))
            if not (0<=j<len(l)): raise ValueError("A column outside box")
            S+=a*max(abs(l[j]),abs(h[j]))
        E=S+abs(b); k=len(row); nops=2*k+2
        delta=gamma(nops)*E+nops*eta
        mag=E+delta
        if mag > Q(np.finfo(np.float64).max)/4: raise OverflowError("roundoff bound approaches float64 overflow")
        # Difference exact residual square vs rounded dot/residual/square.
        row_error_sum+=delta*(2*E+delta)+u*mag*mag+(nops+1)*eta
        sum_t_upper+=(1+u)*mag*mag+eta
        row_ops+=nops+2
    total_error=Fraction(1,2)*(row_error_sum+gamma(max(1,m))*sum_t_upper+max(1,m)*eta)
    return total_error


def impossible_for_float_gate(lower_bound, eval_error_bound, threshold_float64):
    """True only when the certified lower bound excludes the rounded gate."""
    lb=Q(lower_bound); err=Q(eval_error_bound); threshold=Q(threshold_float64)
    if err<0: raise ValueError("negative evaluation error bound")
    return lb-err>threshold


