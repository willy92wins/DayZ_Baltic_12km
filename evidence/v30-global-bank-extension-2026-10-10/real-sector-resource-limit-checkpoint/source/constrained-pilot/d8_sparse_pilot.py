from __future__ import annotations
import hashlib, json, math, multiprocessing as mp, platform, sys, time
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.optimize import Bounds, LinearConstraint, lsq_linear, minimize
import scipy

OUT=Path(__file__).resolve().parent
H,W=64,128
SOLVE_TIMEOUT_S=60
MAX_SOLVER_CALLS=3
EV91=Path(r'E:\DayZ-Baltic-Build\v30-wide-bank-fairing-pilot-20261010\ev91-descent\author_ev91.py')
EV91_VERIFY=Path(r'E:\DayZ-Baltic-Build\v30-wide-bank-fairing-pilot-20261010\ev91-descent\consumer\verify_ev91.py')
EV90=Path(r'E:\DayZ-Baltic-Build\v30-wide-bank-fairing-pilot-20261010\next-method-preflight\ev90_preflight.py')
EV88=Path(r'E:\DayZ-Baltic-Build\v30-wide-bank-fairing-pilot-20261010\author\author_ev88q.py')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def coeffs(k,r,c):
    if k=='xx':return ((r,c,1.),(r,c+1,-2.),(r,c+2,1.))
    if k=='zz':return ((r,c,1.),(r+1,c,-2.),(r+2,c,1.))
    if k=='xz':return ((r,c,-.25),(r,c+2,.25),(r+2,c,.25),(r+2,c+2,-.25))
    raise ValueError(k)

def make_base(case):
    rr,cc=np.indices((H,W),dtype=np.float64)
    # Exact binary fractions give an affine baseline with no rounding-created minima.
    b=(rr/1024.0+cc/2048.0).astype(np.float32)
    if case=='minimum' or case=='minimum_unconstrained':
        # Fixed positive impulse, two cells SW of center (30,64); local active block is 7x7.
        b[28,62]=np.float32(b[28,62]+np.float32(1.0))
    return b

def choose_variables(case):
    if case in {'minimum','minimum_unconstrained','feasible'}:
        # 7x7 active patch embedded in a 64x128 raster; outside nodes are artificial fixed protection.
        return np.asarray([(r,c) for r in range(29,36) for c in range(63,70)],dtype=np.int32)
    if case=='full_memory':
        # Full interior-domain accounting, no solver call; borders fixed to preserve D8 context.
        return np.asarray([(r,c) for r in range(2,H-2) for c in range(2,W-2)],dtype=np.int32)
    raise ValueError(case)

def build_objective(base,nodes):
    index={tuple(map(int,rc)):i for i,rc in enumerate(nodes.tolist())}; records=[]
    for kind,anchors in (
        ('xx',((r,c) for r in range(H) for c in range(W-2))),
        ('zz',((r,c) for r in range(H-2) for c in range(W))),
        ('xz',((r,c) for r in range(H-2) for c in range(W-2)))):
        for r,c in anchors:
            scale=math.sqrt(2.) if kind=='xz' else 1.
            entries=[];fixed=0.
            for rr,cc,k in coeffs(kind,r,c):
                a=k*scale; j=index.get((rr,cc))
                if j is None:fixed+=a*float(base[rr,cc])
                else:entries.append((j,a))
            if entries:records.append((entries,-fixed,(kind,r,c)))
    for i,(r,c) in enumerate(nodes.tolist()):
        records.append(([(i,.25)],.25*float(base[r,c]),('fidelity',r,c)))
    rr=[];cc=[];vv=[];rhs=np.empty(len(records),dtype=np.float64)
    for i,(entries,target,_key) in enumerate(records):
        rhs[i]=target
        for j,v in entries:rr.append(i);cc.append(j);vv.append(v)
    A=sparse.csr_matrix((np.asarray(vv,dtype=np.float64),(np.asarray(rr),np.asarray(cc))),shape=(len(records),len(nodes)))
    A.sort_indices()
    return A,rhs,records

def build_d8(base,nodes):
    b=np.asarray(base,dtype=np.float32); idx={tuple(map(int,x)):i for i,x in enumerate(nodes.tolist())}
    centers=sorted({(int(r+dr),int(c+dc)) for r,c in nodes.tolist() for dr in (-1,0,1) for dc in (-1,0,1)})
    rows=[];cols=[];vals=[];lower=[];witnesses=[];exempt=[]
    for center in centers:
        r,c=center
        if not (0<r<H-1 and 0<c<W-1):raise AssertionError(f'D8 center lacks complete 8-neighbor context: {center}')
        neighbors=[(r+dr,c+dc) for dr in (-1,0,1) for dc in (-1,0,1) if dr or dc]
        witness=min(neighbors,key=lambda rc:(float(b[rc]),rc[0],rc[1]))
        if b[center]<b[witness]:
            exempt.append(list(center));continue
        row=len(lower);fixed=0.;active=False
        for rc,sign in ((center,1.),(witness,-1.)):
            j=idx.get(rc)
            if j is None:fixed+=sign*float(b[rc])
            else:rows.append(row);cols.append(j);vals.append(sign);active=True
        if active:lower.append(-fixed)
        else:
            if fixed<0:raise AssertionError('fixed baseline violates its own B-minimum witness')
            row-=1 # no matrix row; correct the provisional row index only
        witnesses.append({'center':list(center),'witness':list(witness),'linear_row':row if active else None})
    C=sparse.csr_matrix((np.asarray(vals,dtype=np.float64),(np.asarray(rows),np.asarray(cols))),shape=(len(lower),len(nodes)))
    C.sort_indices();d=np.asarray(lower,dtype=np.float64)
    return C,d,witnesses,exempt,centers

def inward32_lower(a):
    x=np.float32(a)
    if float(x)<float(a):x=np.nextafter(x,np.float32(np.inf),dtype=np.float32)
    return x

def inward32_upper(a):
    x=np.float32(a)
    if float(x)>float(a):x=np.nextafter(x,np.float32(-np.inf),dtype=np.float32)
    return x

def build_problem(case):
    b=make_base(case);nodes=choose_variables(case);A,rhs,records=build_objective(b,nodes);C,d,witnesses,exempt,centers=build_d8(b,nodes)
    lo=np.asarray([inward32_lower(float(b[tuple(x)])-.5) for x in nodes],dtype=np.float64)
    hi=np.asarray([inward32_upper(float(b[tuple(x)])+.5) for x in nodes],dtype=np.float64)
    x0=np.asarray([b[tuple(x)] for x in nodes],dtype=np.float64)
    if np.any(x0<lo) or np.any(x0>hi):raise AssertionError('B outside inward bounds')
    if len(d) and np.min(C@x0-d)<-1e-12:raise AssertionError('EV91 D8 baseline is infeasible')
    return b,nodes,A,rhs,C,d,witnesses,exempt,centers,lo,hi,x0,records

def strict_minima(h):
    h=np.asarray(h,dtype=np.float32);center=h[1:-1,1:-1];all_strict=np.ones(center.shape,dtype=bool)
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if dr or dc:all_strict &= center<h[1+dr:H-1+dr,1+dc:W-1+dc]
    rr,cc=np.nonzero(all_strict)
    return {(int(r+1),int(c+1)) for r,c in zip(rr,cc)}

def witness_check(h,witnesses):
    bad=[w for w in witnesses if h[tuple(w['center'])]<h[tuple(w['witness'])]]
    return bad

def reconstruct(b,nodes,x):
    h=b.copy();h[tuple(nodes.T)]=np.asarray(x,dtype=np.float32);return h

def solve_worker(mode,pipe):
    try:
        b,nodes,A,rhs,C,d,witnesses,exempt,centers,lo,hi,x0,records=build_problem(mode)
        calls=1;t0=time.perf_counter()
        if mode=='minimum_unconstrained':
            res=lsq_linear(A,rhs,bounds=(lo,hi),method='trf',tol=1e-10,lsq_solver='lsmr',max_iter=300,verbose=0)
            x=np.asarray(res.x,dtype=np.float64);solver={'method':'scipy.optimize.lsq_linear/trf+lsmr','success':bool(res.success),'status':int(res.status),'message':str(res.message),'iterations':int(res.nit),'optimality':float(res.optimality),'cost':float(res.cost)}
        else:
            Hq=(A.T@A).tocsc()
            def fun(x):
                z=A@x-rhs;return .5*float(z@z)
            def jac(x):return np.asarray(A.T@(A@x-rhs)).reshape(-1)
            def hess(_x):return Hq
            constraints=[LinearConstraint(C,d,np.inf)] if C.shape[0] else []
            res=minimize(fun,x0,method='trust-constr',jac=jac,hess=hess,bounds=Bounds(lo,hi),constraints=constraints,
                options={'sparse_jacobian':True,'factorization_method':'AugmentedSystem','gtol':1e-9,'xtol':1e-10,'maxiter':250,'verbose':0})
            x=np.asarray(res.x,dtype=np.float64);solver={'method':'scipy.optimize.minimize/trust-constr sparse LinearConstraint','success':bool(res.success),'status':int(res.status),'message':str(res.message),'iterations':int(res.nit),'optimality':float(res.optimality),'constraint_violation':float(res.constr_violation),'trust_radius':float(res.tr_radius),'cg_iterations':int(res.cg_niter),'cost':float(res.fun)}
        elapsed=time.perf_counter()-t0
        h=reconstruct(b,nodes,x);bmins=strict_minima(b);hmins=strict_minima(h)
        newmins=sorted(hmins-bmins)
        badw=witness_check(h,witnesses)
        bound_bad=[i for i,v in enumerate(h[tuple(nodes.T)].astype(np.float64)) if v<float(lo[i]) or v>float(hi[i])]
        residual=A@x-rhs;gradient=np.asarray(A.T@residual).reshape(-1)
        fixed=np.ones((H,W),dtype=bool);fixed[tuple(nodes.T)]=False
        result={'mode':mode,'solver_calls':calls,'variables':int(len(nodes)),'objective_rows':int(A.shape[0]),'objective_nnz':int(A.nnz),
            'd8_centers':int(len(centers)),'d8_witnesses':int(len(witnesses)),'d8_exempt_strict_minima':exempt,
            'd8_active_rows':int(C.shape[0]),'d8_nnz':int(C.nnz),'bounds_max_violation':float(max([0.]+[float(lo[i])-float(h[tuple(nodes[i])]) for i in range(len(nodes))]+[float(h[tuple(nodes[i])])-float(hi[i]) for i in range(len(nodes))])),
            'bounds_bad_count':int(len(bound_bad)),'d8_bad_count_after_float32':len(badw),'d8_bad_examples':badw[:8],
            'baseline_strict_minima_count':len(bmins),'candidate_strict_minima_count':len(hmins),'new_strict_minima_count':len(newmins),'new_minima_rc':newmins[:20],
            'fixed_values_exact_B':bool(np.array_equal(h[fixed],b[fixed])),'max_abs_node_change':float(np.max(np.abs(h[tuple(nodes.T)]-b[tuple(nodes.T)]))),
            'residual_l2':float(np.linalg.norm(residual)),'objective_half_residual_squared':float(.5*(residual@residual)),
            'gradient_inf_norm':float(np.linalg.norm(gradient,ord=np.inf)),'linear_d8_min_slack':float(np.min(C@h[tuple(nodes.T)].astype(np.float64)-d)) if len(d) else None,
            'elapsed_solver_seconds':elapsed,'solver':solver}
        pipe.send({'ok':True,'result':result})
    except BaseException as exc:
        pipe.send({'ok':False,'error':repr(exc)})
    finally:pipe.close()

def timed_call(mode):
    ctx=mp.get_context('spawn');recv,send=ctx.Pipe(duplex=False)
    proc=ctx.Process(target=solve_worker,args=(mode,send),daemon=True);proc.start();send.close();proc.join(SOLVE_TIMEOUT_S)
    if proc.is_alive():proc.terminate();proc.join();recv.close();return {'ok':False,'timeout':True,'seconds':SOLVE_TIMEOUT_S,'mode':mode}
    if not recv.poll():recv.close();return {'ok':False,'error':f'worker exited without result, exitcode={proc.exitcode}','mode':mode}
    out=recv.recv();recv.close();return out

def full_grid_memory_probe():
    b=make_base('feasible');nodes=choose_variables('full_memory');A,rhs,records=build_objective(b,nodes);C,d,witnesses,exempt,centers=build_d8(b,nodes)
    raw=int(A.data.nbytes+A.indices.nbytes+A.indptr.nbytes+rhs.nbytes+C.data.nbytes+C.indices.nbytes+C.indptr.nbytes+d.nbytes)
    return {'shape':[H,W],'variables':int(len(nodes)),'objective_rows':int(A.shape[0]),'objective_nnz':int(A.nnz),'d8_centers':int(len(centers)),'d8_active_rows':int(C.shape[0]),'d8_nnz':int(C.nnz),'csr_plus_rhs_bounds_bytes':raw,'csr_plus_rhs_bounds_mib':raw/1024**2,'d8_exemptions':len(exempt),'note':'Measured explicit CSR arrays and RHS only; excludes Python row-build objects and trust-constr internal KKT/factorization peak.'}

def main():
    before={str(p):sha(p) for p in (EV91,EV91_VERIFY,EV90,EV88)}
    # One no-D8 control, its one constrained counterpart, and one feasible constrained case.
    calls=[];budget={'max_solver_calls':MAX_SOLVER_CALLS,'timeout_each_seconds':SOLVE_TIMEOUT_S,'retry_policy':'none; timeout/error stops the sequence'}
    mem=full_grid_memory_probe()
    control=timed_call('minimum_unconstrained');calls.append(control)
    if not control.get('ok') or not control['result']['solver']['success'] or control['result']['new_strict_minima_count']<1:
        report={'status':'STOP_NO_CONTROLLED_NEW_MINIMUM','budget':budget,'calls':calls,'full_grid_memory_probe':mem,'source_hashes_before':before}
        (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2));return
    constrained=timed_call('minimum');calls.append(constrained)
    if not constrained.get('ok') or not constrained['result']['solver']['success'] or constrained['result']['d8_bad_count_after_float32'] or constrained['result']['new_strict_minima_count']:
        report={'status':'STOP_D8_CONSTRAINED_CASE_FAILED','budget':budget,'calls':calls,'full_grid_memory_probe':mem,'source_hashes_before':before}
        (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2));return
    feasible=timed_call('feasible');calls.append(feasible)
    after={str(p):sha(p) for p in (EV91,EV91_VERIFY,EV90,EV88)}
    report={'status':'PASS_SYNTHETIC_PILOT_ONLY' if feasible.get('ok') and feasible['result']['solver']['success'] and feasible['result']['d8_bad_count_after_float32']==0 and feasible['result']['new_strict_minima_count']==0 else 'FEASIBLE_CASE_FAILED_OR_INCONCLUSIVE',
      'scope':'Synthetic 64x128 only. No terrain/map/PBO/game inputs. No 3M-node solve.', 'budget':budget,
      'd8_contract':{'source':'EV91 author_ev91.py descent_constraints lines15-38; verifier independent_d8 lines502-520','centers':'union of each variable node plus its 8 neighbors; complete 8-neighbor context required','witness':'lexicographic minimum by (float32 B height,row,col) among the 8 neighbors','exemption':'center is exempt only when B(center) < B(witness), i.e. baseline strict local minimum','constraint':'H(center) >= H(witness); one linear row if either node is variable, fixed terms moved to RHS; witness checked after float32 cast'},
      'solver_api':{'method':'trust-constr with sparse CSR Hessian, sparse LinearConstraint(C,d,+inf), Bounds, sparse_jacobian=True, AugmentedSystem factorization','GIS_python':sys.executable,'python_version':platform.python_version(),'scipy_version':scipy.__version__,'scipy_path':scipy.__file__,'existing_qp_packages':{'osqp':False,'clarabel':False,'cvxpy':False,'qpsolvers':False},'single_tiny_api_probe_previously_verified':True},
      'full_grid_memory_probe':mem,'calls':calls,'source_hashes_before':before,'source_hashes_after':after,'sources_unchanged':before==after,
      'limitations':['Synthetic active sets are 49-node patches; the 64x128 full-interior matrix is assembled and memory-counted but not solved.','No estimate or PASS is claimed for 3M variables. Need measure trust-constr factorization peak, convergence, feasible-start behavior and exact float32 D8 on representative full geometry before any larger scale.','No P/F, water, slope/hinge, collar, coverage or consumer gates were implemented in this pilot.']}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
