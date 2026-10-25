from __future__ import annotations
import json, math, time, hashlib, sys, platform
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import LinearOperator
from scipy.optimize import lsq_linear, minimize, Bounds, LinearConstraint
import scipy

OUT = Path(__file__).resolve().parent
SECTOR = 64

def coeffs(kind, r, c):
    if kind == 'xx': return ((r,c,1.0),(r,c+1,-2.0),(r,c+2,1.0))
    if kind == 'zz': return ((r,c,1.0),(r+1,c,-2.0),(r+2,c,1.0))
    if kind == 'xz': return ((r,c,-.25),(r,c+2,.25),(r+2,c,.25),(r+2,c+2,-.25))
    raise ValueError(kind)

def all_stencils(shape, variables):
    h,w=shape; vset=set(map(tuple,variables.tolist())); out=[]
    # Exact EV88 forward placements. No padding/wrap/extrapolated samples at real raster edges.
    for r in range(h):
        for c in range(w-2):
            if any((rr,cc) in vset for rr,cc,_ in coeffs('xx',r,c)): out.append(('xx',r,c))
    for r in range(h-2):
        for c in range(w):
            if any((rr,cc) in vset for rr,cc,_ in coeffs('zz',r,c)): out.append(('zz',r,c))
    for r in range(h-2):
        for c in range(w-2):
            if any((rr,cc) in vset for rr,cc,_ in coeffs('xz',r,c)): out.append(('xz',r,c))
    return out

def row_records(B, variables, stencils):
    h,w=B.shape; index={tuple(rc):i for i,rc in enumerate(variables.tolist())}; records=[]
    for kind,r,c in stencils:
        scale=math.sqrt(2.0) if kind=='xz' else 1.0
        entries=[]; fixed=0.0
        for rr,cc,k in coeffs(kind,r,c):
            a=k*scale
            i=index.get((rr,cc))
            if i is None: fixed += a*float(B[rr,cc])
            else: entries.append((i,a))
        records.append((entries,-fixed,(kind,r,c)))
    # EV88 fidelity term: coefficient .25, target .25*B.
    for i,(r,c) in enumerate(variables.tolist()): records.append(([(i,.25)],.25*float(B[r,c]),('fidelity',r,c)))
    return records

def csr_from_records(records,n):
    rr=[]; cc=[]; vv=[]; b=np.empty(len(records),np.float64)
    for i,(entries,target,_key) in enumerate(records):
        b[i]=target
        for j,v in entries: rr.append(i); cc.append(j); vv.append(v)
    A=sparse.csr_matrix((np.asarray(vv), (np.asarray(rr),np.asarray(cc))),shape=(len(records),n))
    A.sort_indices()
    return A,b

def matrix_free(records,n):
    # Explicit sparse row records; no dense matrix allocation.
    def mv(x):
        y=np.empty(len(records),np.float64)
        for i,(e,_b,_k) in enumerate(records): y[i]=sum(v*x[j] for j,v in e)
        return y
    def rmv(y):
        x=np.zeros(n,np.float64)
        for i,(e,_b,_k) in enumerate(records):
            yi=y[i]
            for j,v in e: x[j]+=v*yi
        return x
    return LinearOperator((len(records),n),matvec=mv,rmatvec=rmv,dtype=np.float64)

def sector_key(s):
    _kind,r,c=s
    return (r//SECTOR,c//SECTOR)

def synthetic(shape):
    h,w=shape; r,c=np.indices(shape,dtype=np.float64)
    # Smooth monotonic-curved field plus a broad ridge, all entirely synthetic.
    B=100.0+0.004*r+0.003*c+0.000025*c*c+1.2*np.exp(-((c-w*.52)/(w*.06))**2)
    protected=np.zeros(shape,bool)
    # Artificial protections intentionally stay away from the sector seam.
    protected[:,18:21]=True
    protected[12:17,25:32]=True
    return B,protected

def fixture_and_solve():
    shape=(64,128); B,protected=synthetic(shape)
    variables=np.column_stack(np.nonzero(~protected)).astype(np.int32)
    if protected[:,SECTOR-2:SECTOR+2].any(): raise AssertionError('artificial protections overlap sector seam')
    st=all_stencils(shape,variables); records=row_records(B,variables,st); A,b=csr_from_records(records,len(variables))
    buckets={}
    for s in st: buckets.setdefault(sector_key(s),[]).append(s)
    sector_st=[s for k in sorted(buckets) for s in buckets[k]]
    assert len(st)==len(set(st)) and len(sector_st)==len(st) and set(st)==set(sector_st)
    cross=[s for s in st if len({(rr//SECTOR,cc//SECTOR) for rr,cc,_ in coeffs(s[0],s[1],s[2])})>1]
    # Require an actual free-variable coupling across c=64, not just crossing support.
    var_index={tuple(map(int,rc)):i for i,rc in enumerate(variables.tolist())}
    cross_free=[]
    for s in cross:
        entries=[(var_index[(rr,cc)],coef) for rr,cc,coef in coeffs(s[0],s[1],s[2]) if (rr,cc) in var_index]
        if any(int(variables[i,1])<SECTOR for i,_ in entries) and any(int(variables[i,1])>=SECTOR for i,_ in entries):
            cross_free.append((s,entries))
    if not cross_free: raise AssertionError('no EV88 stencil couples free variables across the sector seam')
    hessian=(A.T@A).tocsr()
    coupled_pair=None; hessian_offdiag=0.0
    for _s,entries in cross_free:
        left=[i for i,_ in entries if int(variables[i,1])<SECTOR]
        right=[i for i,_ in entries if int(variables[i,1])>=SECTOR]
        for i in left:
            for j in right:
                value=float(hessian[i,j])
                if abs(value)>1e-12:
                    coupled_pair=(variables[i].tolist(),variables[j].tolist())
                    hessian_offdiag=value
                    break
            if coupled_pair is not None: break
        if coupled_pair is not None: break
    # The functional negative below removes every crossing stencil row.
    sec_records=row_records(B,variables,sector_st); As,bs=csr_from_records(sec_records,len(variables))
    cross_keys={s for s in cross}
    negative_records=[rec for rec in records if rec[2][0]=='fidelity' or rec[2] not in cross_keys]
    An,bn=csr_from_records(negative_records,len(variables))
    # Compare objective values, not just key-set bookkeeping: omitted crossing stencils alter the functional.
    probe=B[~protected].astype(np.float64).copy()
    li=var_index[tuple(coupled_pair[0])];ri=var_index[tuple(coupled_pair[1])]
    probe[li]+=0.37;probe[ri]-=0.29
    objective_global=float(np.linalg.norm(A@probe-b)**2)
    objective_sector=float(np.linalg.norm(As@probe-bs)**2)
    objective_omitted=float(np.linalg.norm(An@probe-bn)**2)
    objective_sector_equal=abs(objective_global-objective_sector)<=1e-10*max(1.0,objective_global)
    omitted_functional_detected=abs(objective_global-objective_omitted)>1e-8
    assert objective_sector_equal and omitted_functional_detected    # Row order is sector-grouped, so compare each canonical stencil row by key.
    global_key_to_row={rec[2]:i for i,rec in enumerate(records)}
    sector_key_to_row={rec[2]:i for i,rec in enumerate(sec_records)}
    assert global_key_to_row.keys()==sector_key_to_row.keys()
    rows_equal=all(np.array_equal(A.getrow(global_key_to_row[k]).toarray(),As.getrow(sector_key_to_row[k]).toarray()) and records[global_key_to_row[k]][1]==sec_records[sector_key_to_row[k]][1] for k in global_key_to_row)
    assert rows_equal
    lo=np.full(len(variables),-0.6); hi=np.full(len(variables),0.6)
    t=time.perf_counter(); g=lsq_linear(A,b,bounds=(B[~protected]-0.6,B[~protected]+0.6),method='trf',tol=1e-8,lsq_solver='lsmr',max_iter=100); tg=time.perf_counter()-t
    t=time.perf_counter(); q=lsq_linear(As,bs,bounds=(B[~protected]-0.6,B[~protected]+0.6),method='trf',tol=1e-8,lsq_solver='lsmr',max_iter=100); ts=time.perf_counter()-t
    # Independent matrix-free action consistency against assembled CSR.
    L=matrix_free(records,len(variables)); x=np.linspace(-.5,.5,len(variables)); y=np.linspace(.1,.9,len(records))
    mv_err=float(np.max(np.abs(L@x-A@x))); rmv_err=float(np.max(np.abs(L.rmatvec(y)-A.T@y)))
    # Curvature response fixtures using exact EV88 coefficients.
    rr,cc=np.indices((9,11),dtype=float)
    profiles={
        'constant':np.full((9,11),7.0),
        'affine_ramp':2+0.7*rr-0.4*cc,
        'monotonic_curved':0.1*cc+0.002*cc**2+0.03*rr,
        'ridge':np.exp(-((cc-5)/1.5)**2),
    }
    response={}
    for name,F in profiles.items():
        ss=[('xx',r,c) for r in range(9) for c in range(9)]+[('zz',r,c) for r in range(7) for c in range(11)]+[('xz',r,c) for r in range(7) for c in range(9)]
        residual=[]
        for kind,r,c in ss:
            scale=math.sqrt(2) if kind=='xz' else 1.0
            residual.append(sum(k*F[ri,ci] for ri,ci,k in coeffs(kind,r,c))*scale)
        response[name]={'sum_sq':float(np.dot(residual,residual)),'max_abs':float(np.max(np.abs(residual)))}
    assert response['constant']['max_abs']<1e-12 and response['affine_ramp']['max_abs']<1e-12
    # Artificially protected elevations are never variables and remain exact after reconstruction.
    candidate=B.copy(); candidate[tuple(variables.T)]=g.x
    assert not any(protected[tuple(rc)] for rc in variables)
    variable_owner_keys=[(int(r)//SECTOR,int(c)//SECTOR,int(r),int(c)) for r,c in variables.tolist()]
    variable_ownership_count=len(set(variable_owner_keys))
    variable_ownership_equals=(variable_ownership_count==len(variables))
    fixed_exact=bool(np.array_equal(candidate[protected],B[protected]))
    assert fixed_exact
    return {
      'shape':list(shape),'sector_cells':SECTOR,'variables':int(len(variables)),'protected_nodes':int(protected.sum()),'protection_layout':'Artificial columns 18:20 and rows 12:16/columns 25:31; no protected nodes within c=62..65 seam neighborhood.',
      'stencils_by_kind':{k:sum(s[0]==k for s in st) for k in ('xx','zz','xz')},'total_stencils':len(st),
      'sector_buckets':{str(k):len(v) for k,v in buckets.items()},'crossing_stencils':len(cross),'crossing_stencils_with_free_variables_on_both_sides':len(cross_free),'free_free_hessian_offdiag':hessian_offdiag,'coupled_variable_pair_rc':coupled_pair,'global_vs_sector_objective_equal':objective_sector_equal,'cropped_cross_stencils_change_functional':omitted_functional_detected,'objective_global':objective_global,'objective_sector_grouped':objective_sector,'objective_with_crossings_omitted':objective_omitted,
      'boundary_anchor_counts':{'xx_at_first_column':sum(k=='xx' and c==0 for k,r,c in st),'xx_at_last_support':sum(k=='xx' and c==shape[1]-3 for k,r,c in st),'zz_at_first_row':sum(k=='zz' and r==0 for k,r,c in st),'xz_at_first_row_or_column':sum(k=='xz' and (r==0 or c==0) for k,r,c in st)},
      'ownership_unique':len(st)==len(set(st)),'variable_ownership_count':variable_ownership_count,'variable_ownership_equals_variables':variable_ownership_equals,'sector_assembly_same_rows':bool(rows_equal),
      'global_solve':{'success':bool(g.success),'cost':float(g.cost),'iterations':int(g.nit),'seconds':tg},
      'sector_grouped_single_global_solve':{'success':bool(q.success),'cost':float(q.cost),'iterations':int(q.nit),'seconds':ts,
                                            'max_solution_abs_diff':float(np.max(np.abs(g.x-q.x)))},
      'matrix_free_max_abs_errors':{'matvec':mv_err,'rmatvec':rmv_err},'profile_checks':response,
      'fixed_values_unchanged':fixed_exact,'max_variable_change_from_B':float(np.max(np.abs(g.x-B[~protected]))),'boundary_rule':'Only forward EV88 stencils wholly inside the raster; no padding, wrap, or extrapolated samples. This is explicit inward/unilateral support at outer raster edges.'
    }

def benchmark(shape):
    B,protected=synthetic(shape); variables=np.column_stack(np.nonzero(~protected)).astype(np.int32)
    t=time.perf_counter(); st=all_stencils(shape,variables); build_st=time.perf_counter()-t
    t=time.perf_counter(); rec=row_records(B,variables,st); A,b=csr_from_records(rec,len(variables)); build_mat=time.perf_counter()-t
    t=time.perf_counter(); op=matrix_free(rec,len(variables)); build_op=time.perf_counter()-t
    x=np.ones(len(variables),np.float64); t=time.perf_counter(); yy=op@x; matvec_s=time.perf_counter()-t
    sparse_bytes=int(A.data.nbytes+A.indices.nbytes+A.indptr.nbytes+b.nbytes)
    # Records use arrays only in CSR for a stable comparable footprint; Python object overhead is excluded and stated.
    return {'shape':list(shape),'variables':int(len(variables)),'stencils':len(st),'rows':A.shape[0],
      'csr_nnz':int(A.nnz),'csr_bytes_including_rhs':sparse_bytes,'csr_build_seconds':build_mat,'stencil_enumeration_seconds':build_st,
      'matrix_free_operator_creation_seconds':build_op,'matrix_free_matvec_seconds':matvec_s,'matvec_output_finite':bool(np.isfinite(yy).all()),
      'memory_note':'CSR byte count includes data, indices, indptr, RHS. Python tuple/list overhead of matrix-free row records is not included.'}

def trust_constr_api_probe():
    # Tiny 2-variable QP only: checks installed SciPy sparse LinearConstraint + Bounds API for box and D8-style inequalities.
    A=sparse.eye(2,format='csr'); target=np.array([2.0,0.0]); C=sparse.csr_matrix([[-1.0,1.0]])
    con=LinearConstraint(C,-np.inf,-0.2); bounds=Bounds(np.zeros(2),np.ones(2))
    def fun(x):
        d=A@x-target; return 0.5*float(d@d)
    def jac(x): return np.asarray(A.T@(A@x-target)).reshape(-1)
    def hess(_x): return A.T@A
    t=time.perf_counter(); res=minimize(fun,np.array([.5,.5]),method='trust-constr',jac=jac,hess=hess,bounds=bounds,
      constraints=[con],options={'sparse_jacobian':True,'gtol':1e-10,'xtol':1e-12,'maxiter':200,'verbose':0}); elapsed=time.perf_counter()-t
    return {'method':'scipy.optimize.minimize(method=trust-constr) + scipy.optimize.Bounds + sparse LinearConstraint',
      'success':bool(res.success),'status':int(res.status),'message':str(res.message),'x':res.x.tolist(),
      'bound_violation':float(max(0,-np.min(res.x),np.max(res.x)-1)),
      'd8_style_linear_constraint_value':float((C@res.x)[0]),'d8_upper':-0.2,'seconds':elapsed,
      'limitations':'Only proves API/feasibility on 2 variables. Does not establish scalability or feasibility for a multi-million-node terrain.'}

def main():
    import scipy.optimize, inspect
    ev88=Path(r'E:\DayZ-Baltic-Build\v30-wide-bank-fairing-pilot-20261010\author\author_ev88q.py')
    prior_code=OUT/'rejected-v1'/'prototype.py'; prior_report=OUT/'rejected-v1'/'prototype-report.json'
    prior_report_data=json.loads(prior_report.read_text(encoding='utf-8'))
    report={'prototype_version':'seam-coupled synthetic v2','prior_artifacts':{'prototype_sha256':hashlib.sha256(prior_code.read_bytes()).hexdigest(),'report_sha256':hashlib.sha256(prior_report.read_bytes()).hexdigest()},
      'prototype_source':{'path':str(Path(__file__).resolve()),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
      'source_identity_comparison':{'prior_ev88_sha256':prior_report_data['ev88_source']['sha256'],'current_ev88_sha256':hashlib.sha256(ev88.read_bytes()).hexdigest(),'ev88_source_unchanged':prior_report_data['ev88_source']['sha256']==hashlib.sha256(ev88.read_bytes()).hexdigest()},
      'scope':'Synthetic analytical prototype only; no map, terrain file, PBO, game, or production solve used.',
      'ev88_source':{'path':str(ev88),'sha256':hashlib.sha256(ev88.read_bytes()).hexdigest(),'hinge_coeffs_line':186,'stencil_enumeration_line':193,'matrix_objective_lines':[335,351]},
      'scipy_api_source_refs':{'LinearConstraint':'scipy/optimize/_constraints.py:139','Bounds':'scipy/optimize/_constraints.py:253','trust_constr_sparse_jacobian':'scipy/optimize/_trustregion_constr/minimize_trustregion_constr.py:149,364-381'},
      'python':sys.executable,'python_version':platform.python_version(),'scipy_version':scipy.__version__,'scipy_path':scipy.__file__,
      'ev88_formula_source':'author_ev88q.py hinge_coeffs/build_matrix: xx=(1,-2,1), zz=(1,-2,1), xz=(-.25,.25,.25,-.25) scaled by sqrt(2); fidelity=.25 per variable.',
      'fixture':fixture_and_solve(),'benchmarks':[benchmark((128,128)),benchmark((256,256))],
      'trust_constr_probe':trust_constr_api_probe(),
      'solver_recommendation':'For box + sparse linear D8 constraints, trust-constr is the SciPy-native API verified here for sparse LinearConstraint and Bounds. A global implementation is not recommended yet: only a 2-variable API probe was run; memory, convergence, and feasibility at terrain scale remain untested. lsq_linear is proven here for synthetic box-only objective, not D8 inequalities.'}
    out=OUT/'prototype-report.json'; out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()






