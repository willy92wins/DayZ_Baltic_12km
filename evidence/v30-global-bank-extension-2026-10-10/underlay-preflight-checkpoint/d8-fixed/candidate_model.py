from __future__ import annotations

from fractions import Fraction
import math
import time
from types import SimpleNamespace

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix


def _fraction(value):
    if isinstance(value, Fraction): return value
    if isinstance(value, (int, np.integer)): return Fraction(int(value))
    x=float(value)
    if math.isinf(x): return x
    if not math.isfinite(x): raise ValueError('NaN row bound')
    return Fraction.from_float(x)


def _nearest_finite(value, name):
    q=_fraction(value)
    if isinstance(q,float): return q
    try: out=float(q)
    except OverflowError as exc: raise ValueError(f'{name} overflows binary64') from exc
    if not math.isfinite(out): raise ValueError(f'{name} overflows binary64')
    if q != 0 and out == 0.0: raise ValueError(f'{name} underflows to zero in binary64')
    return out


class CandidateLatticeMILP:
    """Single-call float64 candidate generator; exact postchecks remain authority."""
    def __init__(self, base_module, *args, **kwargs):
        self.base_module=base_module
        self.model=base_module.LatticeMILP(*args, **kwargs)

    def matrix_nearest(self, extra_rows=()):
        """Convert exact rows to nearest float64 in baseline-centered variables.

        Solver variables are y=x-x_B, with the exact feasible baseline at y=0.
        Rows are algebraically translated by a*x_B before float conversion. The
        resulting matrix is still a candidate generator, never a sound oracle.
        """
        rows=[*self.model.rows,*extra_rows]
        origin=self.exact_auxiliary(np.zeros(len(self.model.exprs),dtype=np.int64))
        rr=[];cc=[];vv=[];lb=[];ub=[];names=[]
        for ri,(coeff,lo,hi,name) in enumerate(rows):
            shift=sum((value*origin[j] for j,value in coeff.items()),Fraction(0))
            for j, exact in coeff.items():
                f=_nearest_finite(exact,f'coefficient:{name}:{j}')
                if f != 0.0:
                    rr.append(ri);cc.append(int(j));vv.append(f)
            lq=_fraction(lo);uq=_fraction(hi)
            lower=-math.inf if isinstance(lq,float) and lq==-math.inf else _nearest_finite(lq-shift,f'centered_lower:{name}')
            upper=math.inf if isinstance(uq,float) and uq==math.inf else _nearest_finite(uq-shift,f'centered_upper:{name}')
            if lower>upper: raise ValueError(f'nearest-float row has inverted centered bounds: {name}')
            lb.append(lower);ub.append(upper);names.append(name)
        A=coo_matrix((vv,(rr,cc)),shape=(len(rows),len(self.model.var_lb))).tocsr()
        return A,np.asarray(lb,dtype=np.float64),np.asarray(ub,dtype=np.float64),names

    def centered_origin(self):
        return self.exact_auxiliary(np.zeros(len(self.model.exprs),dtype=np.int64))

    def exact_auxiliary(self, m):
        m=np.asarray(m,dtype=np.int64)
        if m.shape!=(len(self.model.exprs),): raise ValueError('lattice vector shape mismatch')
        x=[Fraction(0) for _ in self.model.var_lb]
        for i,(mi,expr) in enumerate(zip(m,self.model.exprs)):
            if not expr.terms:
                if int(mi)!=expr.constant: raise ValueError(f'fixed lattice value mismatch at {i}')
                continue
            selected=None;selected_k=None
            for seg in expr.segments:
                delta=int(mi)-seg.first_m
                if delta>=0 and delta%seg.stride_m==0:
                    k=delta//seg.stride_m
                    if k<seg.count:
                        selected=seg;selected_k=k;break
            if selected is None: raise ValueError(f'lattice value outside segments at {i}')
            for j,coef in expr.terms.items():
                name=self.model.var_names[j]
                if name.startswith('z_'):
                    x[j]=Fraction(int(selected.exponent_field==int(name.rsplit('e',1)[1])))
                elif name.startswith('k_'):
                    exp=int(name.rsplit('e',1)[1])
                    x[j]=Fraction(selected_k if exp==selected.exponent_field else 0)
                else: raise ValueError(f'unrecognized auxiliary {name}')
        for i,t_idx in self.model.t_indices.items():
            target=(Fraction.from_float(float(self.model.x64[i]))-
                    self.base_module.frac_f32(self.model.baseline[i]))/self.model.quantum
            x[t_idx]=abs(Fraction(int(m[i]))-target)
        return tuple(x)

    def exact_rows_pass(self,m):
        x=self.exact_auxiliary(m)
        failures=[]
        for ri,(coeff,lo,hi,name) in enumerate(self.model.rows):
            lhs=sum((v*x[j] for j,v in coeff.items()),Fraction(0))
            lq=_fraction(lo);uq=_fraction(hi)
            if not (lhs>=lq and lhs<=uq): failures.append({'row':ri,'name':name,'lhs':str(lhs),'lower':str(lq),'upper':str(uq)})
        return not failures,failures

    def solve_once(self,time_limit=60.0,node_limit=1_000_000):
        start=time.monotonic();deadline=start+float(time_limit)
        A,lb,ub,names=self.matrix_nearest()
        origin=self.centered_origin()
        shifted_lb=[];shifted_ub=[]
        for bound,base_value in zip(self.model.var_lb,origin):
            q=_fraction(bound);shifted_lb.append(q if isinstance(q,float) and math.isinf(q) else q-base_value)
        for bound,base_value in zip(self.model.var_ub,origin):
            q=_fraction(bound);shifted_ub.append(q if isinstance(q,float) and math.isinf(q) else q-base_value)
        def finite_bounds(values):
            out=[]
            for value in values:
                if isinstance(value,float) and math.isinf(value): out.append(value)
                else: out.append(_nearest_finite(value,'centered_variable_bound'))
            return np.asarray(out,dtype=np.float64)
        objective=np.asarray(self.model.objective,dtype=np.float64)
        integrality=np.asarray(self.model.integrality,dtype=np.int32)
        bounds=Bounds(finite_bounds(shifted_lb),finite_bounds(shifted_ub))
        constraints=LinearConstraint(A,lb,ub)
        remaining=deadline-time.monotonic()
        if remaining<=0: raise TimeoutError('60-second candidate budget expired while assembling float64 model')
        result=milp(objective,
                    integrality=integrality,
                    bounds=bounds,
                    constraints=constraints,
                    options={'time_limit':remaining,'node_limit':int(node_limit),
                             'mip_rel_gap':0.0,'presolve':True,'disp':False})
        elapsed=time.monotonic()-start
        if elapsed>time_limit: raise TimeoutError(f'candidate budget exceeded: {elapsed:.6f}s')
        if int(result.status)!=0 or result.x is None:
            raise RuntimeError(f'HiGHS did not return optimal incumbent: status={result.status}, message={result.message}')
        absolute=np.asarray(result.x,dtype=np.float64)+np.asarray([float(v) for v in origin],dtype=np.float64)
        m=self.model._decode_m(SimpleNamespace(x=absolute))
        grid=self.model.decode_f32(m)
        row_ok,row_failures=self.exact_rows_pass(m)
        gates=self.model.exact_gates(grid)
        elapsed=time.monotonic()-start
        if elapsed>time_limit: raise TimeoutError(f'candidate budget exceeded during exact postchecks: {elapsed:.6f}s')
        if not row_ok or not all(gates.values()):
            return {'status':'REJECTED_EXACT_POSTGATES','grid':grid,'m':m,
                    'exact_rows_pass':row_ok,'exact_row_failures':row_failures,
                    'exact_fraction_gates':gates,'elapsed_seconds':elapsed,
                    'solver_status':int(result.status),'solver_message':str(result.message),
                    'mip_gap':None if getattr(result,'mip_gap',None) is None else float(result.mip_gap),
                    'mip_node_count':int(getattr(result,'mip_node_count',0) or 0),
                    'objective_float64':float(result.fun)}
        return {'status':'CANDIDATE_PASS_FRACTION_PENDING_SHAPE_CONSUMER','grid':grid,'m':m,
                'exact_rows_pass':True,'exact_row_failures':[],
                'exact_fraction_gates':gates,'exact_l1_units':str(self.model.exact_l1_units(m)),
                'elapsed_seconds':elapsed,'solver_status':int(result.status),
                'solver_message':str(result.message),
                'mip_gap':None if getattr(result,'mip_gap',None) is None else float(result.mip_gap),
                'mip_node_count':int(getattr(result,'mip_node_count',0) or 0),
                'objective_float64':float(result.fun),
                'optimality_claim':'HiGHS optimal for nearest-binary64 candidate model only; not exact-rational optimum'}




