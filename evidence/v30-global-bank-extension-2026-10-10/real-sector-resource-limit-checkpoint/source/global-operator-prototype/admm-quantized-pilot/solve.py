"""One bounded synthetic ADMM/CG experiment; never writes a map candidate."""
from pathlib import Path
import argparse, ctypes, hashlib, importlib.util, json, os, sys, time
import numpy as np
from scipy.sparse.linalg import LinearOperator, cg
from scipy import sparse

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT.parent.parent / 'constrained-pilot/d8_sparse_pilot.py'
PRIOR_SHA = '6b5281d9750c30fc5b27171aaec2af59dee88411a66bf5b08e5105866f08252c'
REF = PRIOR.parent / 'report.json'
REF_SHA = 'b404f6de63845d055f72fe33ba19fc9cf81f702005d8f7c27df33bab708bb675'
RHO, ABS_TOL, REL_TOL = 1., 1e-10, 1e-8
MAX_ITER = 10000
CLOSURE = ROOT.parent / 'float32-closure-study/float32_closure.py'
CLOSURE_SHA = 'c0c0cc1998a7cd9974ef884706c57a30ab39217057f675fc805b84c1e1a49d16'

def load_closure():
    if sha(CLOSURE) != CLOSURE_SHA: raise AssertionError('Closure source changed')
    sp=importlib.util.spec_from_file_location('lattice_closure',CLOSURE)
    m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
    return m

def close_float32(mod, base, nodes, raw, lo, hi, witnesses):
    if not all(np.isfinite(a).all() for a in (base,raw,lo,hi)):
        raise ValueError('Finite height/bound inputs required')
    if np.any(lo>hi) or not np.array_equal(lo,lo.astype(np.float32).astype(np.float64)) or not np.array_equal(hi,hi.astype(np.float32).astype(np.float64)):
        raise ValueError('Bounds must already be inward representable float32')
    mutable=np.zeros(base.shape,bool);mutable[tuple(nodes.T)]=True
    lower=base.copy();upper=base.copy();lower[tuple(nodes.T)]=lo;upper[tuple(nodes.T)]=hi
    ncols=base.shape[1]
    edges=[(int(w['witness'][0])*ncols+int(w['witness'][1]),int(w['center'][0])*ncols+int(w['center'][1])) for w in witnesses]
    flat,meta=mod.closure(raw.ravel(),mutable.ravel(),lower.ravel(),upper.ravel(),edges)
    result=flat.reshape(base.shape)
    if meta['ok']:
        if np.any(result<raw) or np.any(result>np.nextafter(raw,np.float32(np.inf))):raise AssertionError('Closure violated upward one-ULP contract')
        if not np.array_equal(result[~mutable],base[~mutable]):raise AssertionError('Closure changed fixed values')
    return result,meta

def json_safe(v):
    if isinstance(v,np.generic):return v.item()
    if isinstance(v,dict):return {str(k):json_safe(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [json_safe(x) for x in v]
    return v

def process_memory():
    class Counters(ctypes.Structure):
        _fields_ = [('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong)] + [
            (name,ctypes.c_size_t) for name in ('PeakWorkingSetSize','WorkingSetSize',
            'QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    kernel = ctypes.WinDLL('kernel32',use_last_error=True)
    psapi = ctypes.WinDLL('psapi',use_last_error=True)
    kernel.GetCurrentProcess.argtypes=[];kernel.GetCurrentProcess.restype=ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
    psapi.GetProcessMemoryInfo.restype=ctypes.c_int
    counters=Counters();counters.cb=ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(counters),counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return dict(pid=os.getpid(),peak_working_set_bytes=int(counters.PeakWorkingSetSize),
                working_set_bytes=int(counters.WorkingSetSize),
                peak_commit_bytes=int(counters.PeakPagefileUsage),method='GetProcessMemoryInfo in solver interpreter')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_prior():
    if sha(PRIOR) != PRIOR_SHA or sha(REF) != REF_SHA:
        raise AssertionError('Prior source/report changed')
    sp = importlib.util.spec_from_file_location('d8_prior', PRIOR)
    p = importlib.util.module_from_spec(sp); sp.loader.exec_module(p)
    return p
def inf(x): return float(np.max(np.abs(x), initial=0.))
def objective(A, rhs, x):
    y = A @ x - rhs
    return .5 * float(y @ y)

def check_float32(base, nodes, x, lo, hi, witnesses):
    h = base.copy(); h[tuple(nodes.T)] = np.asarray(x, np.float32)
    values = h[tuple(nodes.T)].astype(np.float64)
    bad_bounds = int(np.count_nonzero((values < lo) | (values > hi)))
    bad_d8 = sum(h[tuple(w['center'])] < h[tuple(w['witness'])] for w in witnesses)
    def minima(a):
        nr, nc = a.shape; mid = a[1:-1, 1:-1]
        mask = np.ones(mid.shape, bool)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr or dc: mask &= mid < a[1+dr:nr-1+dr, 1+dc:nc-1+dc]
        return mask
    new_minima = int(np.count_nonzero(minima(h) & ~minima(base)))
    fixed = np.ones(base.shape, bool); fixed[tuple(nodes.T)] = False
    stats = dict(bounds_bad=bad_bounds, d8_bad=int(bad_d8), new_strict_minima=new_minima,
                 fixed_exact=bool(np.array_equal(h[fixed], base[fixed])),
                 changed_vertices=int(np.count_nonzero(h != base)))
    stats['pass'] = bool(bad_bounds == 0 and bad_d8 == 0 and new_minima == 0 and stats['fixed_exact'])
    return h, stats

def problem(p, mode):
    if mode == 'reference49': return p.build_problem('minimum')
    base = p.make_base('minimum'); nodes = p.choose_variables('full_memory')
    A, rhs, records = p.build_objective(base, nodes)
    C, d, witnesses, exempt, centers = p.build_d8(base, nodes)
    bv = base[tuple(nodes.T)]
    lo = np.array([p.inward32_lower(float(v)-.5) for v in bv], np.float64)
    hi = np.array([p.inward32_upper(float(v)+.5) for v in bv], np.float64)
    return base, nodes, A, rhs, C, d, witnesses, exempt, centers, lo, hi, bv.astype(np.float64), records

def operator(A, C, rho=RHO):
    At, Ct = A.T.tocsr(), C.T.tocsr()
    def mv(v): return At @ (A @ v) + rho * (v + Ct @ (C @ v))
    diag = np.asarray(A.multiply(A).sum(axis=0)).ravel() + rho * (
        1. + np.asarray(C.multiply(C).sum(axis=0)).ravel())
    n = A.shape[1]
    return LinearOperator((n,n), matvec=mv, dtype=np.float64), LinearOperator(
        (n,n), matvec=lambda v:v/diag, dtype=np.float64), At, Ct

def fixtures(p):
    base,nodes,A,rhs,C,d,witnesses,exempt,centers,lo,hi,x0,records = problem(p,'reference49')
    op,pre,At,Ct = operator(A,C)
    explicit = At @ A + RHO * (sparse.eye(len(nodes)) + Ct @ C)
    probe = np.sin(np.arange(len(nodes), dtype=np.float64))
    err = inf(op @ probe - explicit @ probe)
    assert err < 1e-12, err
    # Independent scalar evaluation of the existing stencil records.
    scalar = .5 * sum((sum(v*probe[j] for j,v in terms)-target)**2 for terms,target,_ in records)
    assert abs(scalar-objective(A,rhs,probe)) < 1e-10
    assert check_float32(base,nodes,x0,lo,hi,witnesses)[1]['pass']
    bad = x0.copy(); bad[0] = hi[0] + 1.
    assert check_float32(base,nodes,bad,lo,hi,witnesses)[1]['bounds_bad'] > 0
    ix = {tuple(rc):i for i,rc in enumerate(nodes.tolist())}
    w = next(w for w in witnesses if tuple(w['center']) in ix)
    bad = x0.copy(); bad[ix[tuple(w['center'])]] = float(base[tuple(w['witness'])])-.1
    assert check_float32(base,nodes,bad,lo,hi,witnesses)[1]['d8_bad'] > 0
    return {'operator_max_error':err, 'scalar_functional_equal':True,
            'baseline_float32_pass':True,'bound_negative_detected':True,'d8_negative_detected':True}

def solve(A,rhs,C,d,lo,hi,x0,budget,progress):
    t0=time.perf_counter();rho=RHO;op,pre,At,Ct=operator(A,C,rho)
    x=x0.copy(); zb=np.clip(x,lo,hi); zd=np.maximum(C@x,d)
    ub=np.zeros_like(zb); ud=np.zeros_like(zd); target=At@rhs; cg_total=0
    history=[];updates=[];status='ITERATION_LIMIT';diagnostics={}
    def guard(_=None):
        if time.perf_counter()-t0 > budget: raise TimeoutError('Fixed solve budget exceeded')
    for it in range(1,MAX_ITER+1):
        guard(); count=[0]
        def callback(_x): count[0]+=1; guard()
        right=target+rho*(zb-ub+Ct@(zd-ud))
        x,info=cg(op,right,x0=x,rtol=1e-12,atol=1e-13,maxiter=1000,M=pre,callback=callback)
        cg_total+=count[0]
        if info: raise RuntimeError(f'CG failed: info={info}, ADMM iteration={it}')
        cx=C@x; oldb,oldd=zb,zd
        zb=np.clip(x+ub,lo,hi); zd=np.maximum(cx+ud,d)
        ub+=x-zb; ud+=cx-zd
        primal=max(inf(x-zb),inf(cx-zd))
        dual=rho*inf(zb-oldb+Ct@(zd-oldd))
        eps_primal=ABS_TOL+REL_TOL*max(inf(x),inf(cx),inf(zb),inf(zd))
        dual_vector=rho*(ub+Ct@ud)
        eps_dual=ABS_TOL+REL_TOL*inf(dual_vector)
        stationarity=inf(At@(A@x-rhs)+dual_vector)
        diagnostics=dict(iteration=it,cg_iterations=cg_total,rho=rho,primal=primal,dual=dual,
                         eps_primal=eps_primal,eps_dual=eps_dual,stationarity=stationarity)
        if it==1 or it%200==0:
            entry={**diagnostics,'elapsed_s':time.perf_counter()-t0};history.append(entry)
            progress(entry)
        if primal<=eps_primal and dual<=eps_dual and stationarity<=eps_dual:
            status='CONVERGED';break
        if it%25==0 and it<=2000:
            newrho=rho
            if primal/eps_primal > 10.*dual/eps_dual:newrho=min(1024.,rho*2.)
            elif dual/eps_dual > 10.*primal/eps_primal:newrho=max(1./1024.,rho/2.)
            if newrho!=rho:
                # Keep the unscaled dual multiplier y=rho*u exactly invariant.
                ub*=rho/newrho;ud*=rho/newrho
                updates.append(dict(iteration=it,old_rho=rho,new_rho=newrho))
                rho=newrho;op,pre,At,Ct=operator(A,C,rho)
    state={'y_box':rho*ub,'y_d8':rho*ud,'z_box':zb,'z_d8':zd}
    return x,dict(status=status,elapsed_s=time.perf_counter()-t0,rho_updates=updates,**diagnostics),history,state

def run(out):
    out.mkdir(parents=True,exist_ok=False)
    p=load_prior();closure_mod=load_closure()
    pins={str(x):sha(x) for x in (PRIOR,REF,CLOSURE,Path(__file__),ROOT/'PLAN.md')}
    report={'scope':'SYNTHETIC_ONLY_NO_MAP_CANDIDATE','source_hashes_start':pins,
            'budget':{'rho_initial':RHO,'rho_rule':'normalized residual ratio 10, factor 2, every 25 until 2000 then frozen',
                      'abs_tol':ABS_TOL,'rel_tol':REL_TOL,'max_admm_iterations':MAX_ITER,
                      'cg_rtol':1e-12,'cg_atol':1e-13,'cg_max_iterations':1000,'reference49_s':60,'full7440_s':120},
            'cases':[]}
    path=out/'report.json'
    def save():
        tmp=path.with_suffix('.tmp')
        tmp.write_text(json.dumps(json_safe(report),indent=2,allow_nan=False)+'\n',encoding='utf-8')
        tmp.replace(path)
    def progress(row):
        with (out/'progress.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(row)+'\n')
    try:
        report['fixtures']=fixtures(p)
        report['closure_fixtures']=closure_mod.synthetic_fixtures()
        # Exercise the failed-gate serialization path before solving.
        assert json.loads(json.dumps(json_safe({'pass':np.bool_(False),'count':np.int64(1)})))=={'pass':False,'count':1}
        save()
        for mode,budget in [('reference49',60),('full7440',120)]:
            tbuild=time.perf_counter()
            base,nodes,A,rhs,C,d,witnesses,exempt,centers,lo,hi,x0,records=problem(p,mode)
            build_s=time.perf_counter()-tbuild
            x,solver,history,state=solve(A,rhs,C,d,lo,hi,x0,budget,lambda row:progress({'mode':mode,**row}))
            raw,rawcheck=check_float32(base,nodes,x,lo,hi,witnesses)
            if solver['status']=='CONVERGED':
                h,closure_meta=close_float32(closure_mod,base,nodes,raw,lo,hi,witnesses)
            else:h=raw;closure_meta={'ok':False,'reason':'continuous_solver_not_converged'}
            h,check=check_float32(base,nodes,h[tuple(nodes.T)],lo,hi,witnesses)
            fv=h[tuple(nodes.T)].astype(np.float64)
            cost=objective(A,rhs,x);cost32=objective(A,rhs,fv);costB=objective(A,rhs,x0)
            rawcost=objective(A,rhs,raw[tuple(nodes.T)].astype(np.float64))
            stationarity_saved=inf(A.T@(A@x-rhs)+state['y_box']+C.T@state['y_d8'])
            normal_residual=max(inf(state['z_box']-np.clip(state['z_box']+state['y_box'],lo,hi)),
                                inf(state['z_d8']-np.maximum(state['z_d8']+state['y_d8'],d)))
            variable_set=set(map(tuple,nodes.tolist()));cross=0
            for terms,target,key in records:
                if key[0]=='fidelity':continue
                cols=[c for r,c,k in p.coeffs(*key) if (r,c) in variable_set]
                cross+=int(any(c<64 for c in cols) and any(c>=64 for c in cols))
            checks={'converged':solver['status']=='CONVERGED','float32':check['pass'],
                    'objective_reduced':cost32<costB,'cross_sector_coupling_present':cross>0}
            checks.update(closure_exact=closure_meta['ok'],
                          closure_objective_budget=cost32-rawcost<=1e-7*max(1.,rawcost),
                          saved_dual_stationarity=stationarity_saved<=solver['eps_dual'],
                          projected_normal_cone=normal_residual<=1e-12)
            if mode=='reference49':
                reference=next(c['result'] for c in json.loads(REF.read_text())['calls'] if c['result']['mode']=='minimum')['objective_half_residual_squared']
                checks['reference_objective_agrees']=abs(cost-reference)<=1e-5
            row=dict(mode=mode,variables=len(nodes),build_s=build_s,solver=solver,float32=check,
                     objective64=cost,objective32=cost32,objectiveB=costB,cross_sector_stencils=cross,
                     csr_bytes=int(sum(v.nbytes for m in (A,C) for v in (m.data,m.indices,m.indptr))+rhs.nbytes+d.nbytes),
                     raw_float32=rawcheck,closure=closure_meta,raw_cast_objective=rawcost,
                     saved_dual_stationarity=stationarity_saved,normal_cone_residual=normal_residual,
                     gates=checks,history=history,process_memory=process_memory())
            np.savez_compressed(out/f'{mode}.npz',baseline=base,candidate=h,raw_cast=raw,nodes_rc=nodes,x_float64=x,**state,
                                lower=lo,upper=hi,witness_centers=np.asarray([w['center'] for w in witnesses]),
                                witness_neighbors=np.asarray([w['witness'] for w in witnesses]))
            row['arrays_sha256']=sha(out/f'{mode}.npz');report['cases'].append(row);save()
            if not all(checks.values()):
                report['status']='STOP_FAILED_GATE';break
        else: report['status']='PASS_SYNTHETIC_7440_ONLY'
    except Exception as exc:
        report['status']='STOP_ERROR_OR_TIMEOUT';report['error']=repr(exc)
    report['source_hashes_end']={path:sha(path) for path in pins}
    report['process_memory_end']=process_memory()
    report['sources_unchanged']=report['source_hashes_start']==report['source_hashes_end']
    if not report['sources_unchanged']:report['status']='STOP_SOURCE_CHANGED'
    save();print(json.dumps({'status':report['status'],'cases':len(report['cases']),'report':str(path)}),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();run(args.output)
