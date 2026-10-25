"""One constrained fairing solve; no repair or changes to EV90's physical domain."""
from __future__ import annotations
import argparse, hashlib, json, multiprocessing as mp, sys, time
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
Q=HERE.parent
PREVIOUS=Q/'ev90-author/author_ev90.py'
PREVIOUS_SHA='c8ee41f14c332bf9a5849ee7a6454e82043ccc5e06a866bd018df817f819ad7e'
sys.path.insert(0,str(PREVIOUS.parent))
import author_ev90 as old


def descent_constraints(base, nodes):
    b=np.asarray(base,dtype=np.float32)
    nodes=[tuple(map(int,x)) for x in nodes]
    if len(set(nodes))!=len(nodes):raise ValueError('duplicate variable')
    index={rc:i for i,rc in enumerate(nodes)}
    centers=sorted({(r+dr,c+dc) for r,c in nodes for dr in (-1,0,1) for dc in (-1,0,1)})
    rows=[];lower=[];witnesses=[];exempt=[]
    for center in centers:
        r,c=center
        if not (0<r<b.shape[0]-1 and 0<c<b.shape[1]-1):raise ValueError('missing descent context')
        neighbors=[(r+dr,c+dc) for dr in (-1,0,1) for dc in (-1,0,1) if dr or dc]
        witness=min(neighbors,key=lambda rc:(float(b[rc]),rc[0],rc[1]))
        if b[center]<b[witness]:
            exempt.append(list(center));continue
        row=np.zeros(len(nodes),dtype=np.float64);fixed=0.
        for rc,sign in ((center,1.),(witness,-1.)):
            if rc in index:row[index[rc]]+=sign
            else:fixed+=sign*float(b[rc])
        active=bool(np.any(row))
        if active:rows.append(row);lower.append(-fixed)
        elif fixed<0:raise AssertionError('fixed baseline witness is uphill')
        witnesses.append({'center':list(center),'witness':list(witness),'linear_row':len(rows)-1 if active else None})
    matrix=np.asarray(rows,dtype=np.float64).reshape(-1,len(nodes))
    return matrix,np.asarray(lower,dtype=np.float64),witnesses,exempt,centers


def witnesses_hold(heights,witnesses):
    return all(heights[tuple(x['center'])]>=heights[tuple(x['witness'])] for x in witnesses)


def collar_guard(nodes, stencils, window):
    """Freeze the support of every original collar stencil and measured hinge."""
    variables={tuple(map(int,p)) for p in nodes}
    r0,r1,c0,c1=map(int,window)
    collar={(r,c) for r in range(r0,r1) for c in range(c0,c1)
            if r<r0+2 or r>=r1-2 or c<c0+2 or c>=c1-2}
    guard=set()
    def include(support):
        support=set(support)
        if support & collar:guard.update(support & variables)
    for kind,r,c in stencils:
        if kind=='xx':support=((r,c),(r,c+1),(r,c+2))
        elif kind=='zz':support=((r,c),(r+1,c),(r+2,c))
        elif kind=='xz':support=((r,c),(r,c+2),(r+2,c),(r+2,c+2))
        else:raise ValueError('unknown stencil')
        include(support)
    for r in range(r0,r1-1):
        for c in range(c0,c1-1):include(((r,c),(r,c+1),(r+1,c),(r+1,c+1)))
    for r in range(r0,r1-1):
        for c in range(c0,c1-2):include(((r,c),(r,c+1),(r+1,c+1),(r+1,c+2)))
    for r in range(r0,r1-2):
        for c in range(c0,c1-1):include(((r,c),(r+1,c),(r+1,c+1),(r+2,c+1)))
    return sorted(guard)


def _worker(a,rhs,lo,hi,c,d,x0,pipe):
    try:
        import scipy
        from scipy.optimize import minimize,LinearConstraint
        if scipy.__version__!='1.18.1':raise RuntimeError('unexpected solver runtime')
        def objective(x):
            residual=a@x-rhs
            return .5*float(residual@residual)
        def jacobian(x):return a.T@(a@x-rhs)
        result=minimize(objective,x0,method='SLSQP',jac=jacobian,
                        bounds=list(zip(lo,hi)),constraints=LinearConstraint(c,d,np.inf),
                        options={'ftol':1e-10,'maxiter':1000,'disp':False})
        pipe.send({'success':bool(result.success),'status':int(result.status),
                   'message':str(result.message),'nit':int(result.nit),
                   'cost':float(result.fun),'x':result.x.tolist(),'scipy_version':scipy.__version__})
    except BaseException as exc:pipe.send({'error':repr(exc)})
    finally:pipe.close()


def solve_once(a,rhs,lo,hi,c,d,x0):
    ctx=mp.get_context('spawn');recv,send=ctx.Pipe(duplex=False)
    worker=ctx.Process(target=_worker,args=(a,rhs,lo,hi,c,d,x0,send),daemon=True)
    worker.start();send.close();worker.join(120)
    if worker.is_alive():
        worker.terminate();worker.join();raise TimeoutError('single SLSQP worker exceeded120s')
    if not recv.poll():raise RuntimeError('SLSQP worker exited without a result')
    result=recv.recv();recv.close()
    if 'error' in result or not result['success']:raise RuntimeError(str(result))
    return result


def prepare():
    if old.sha(PREVIOUS)!=PREVIOUS_SHA:raise AssertionError('prior author changed')
    _,local,a,rhs,lo,hi,pre=old.prepare()
    base=local['b']['heights'];nodes=local['variables']
    c,d,witnesses,exempt,centers=descent_constraints(base,nodes)
    x0=np.asarray([base[tuple(x)] for x in nodes],dtype=np.float64)
    if np.any(x0<lo) or np.any(x0>hi) or np.any(c@x0<d):
        raise AssertionError('B is not feasible; no different initialization allowed')
    guard=collar_guard(nodes,pre['stencils'],local['bounds17'])
    guard_report=HERE/'collar-guard-preflight.json'
    if old.sha(guard_report)!='1f1e68cf1b2358c2bb5d21d9268cfd2f030b46b6d7247227bc55be0efe2fc0df':
        raise AssertionError('guard preflight changed')
    guard_expected=json.loads(guard_report.read_text(encoding='utf-8'))['guard']['guard_rc']
    if [list(x) for x in guard]!=guard_expected:raise AssertionError('guard differs from independent preflight')
    guards=set(guard);lo=lo.copy();hi=hi.copy()
    for i,node in enumerate(nodes):
        if tuple(node) in guards:lo[i]=hi[i]=x0[i]
    pins=dict(pre['source_pins']);pins[str(HERE/'plan.md')]=old.sha(HERE/'plan.md')
    pins[str(guard_report)]=old.sha(guard_report)
    pins[str(HERE/'collar_guard_preflight.py')]=old.sha(HERE/'collar_guard_preflight.py')
    pins[str(Path(__file__).resolve())]=old.sha(__file__)
    import scipy
    if scipy.__version__!='1.18.1':raise AssertionError('expected verified GIS SciPy1.18.1')
    for name in ('_minimize.py','_constraints.py','_slsqp_py.py'):
        p=Path(scipy.__file__).parent/'optimize'/name;pins[str(p)]=old.sha(p)
    meta={**pre,'status':'PREPARED_NO_SOLVE','source_pins':pins,
          'author_source_sha256':old.sha(__file__),'plan_sha256':old.sha(HERE/'plan.md'),
          'physical_preflight_plan_sha256':pre['plan_sha256'],
          'guard_rc':[list(x) for x in guard],
          'solver_bounds_float32':np.column_stack((lo,hi)).tolist(),
          'remaining_free_variables':int(np.count_nonzero(lo<hi)),
          'witnesses':witnesses,'baseline_strict_minima_exempt':exempt,
          'descent_centers':len(centers),'descent_matrix_shape':list(c.shape),
          'descent_matrix_sha256_f64':hashlib.sha256(c.astype('<f8').tobytes()).hexdigest(),
          'descent_rhs_sha256_f64':hashlib.sha256(d.astype('<f8').tobytes()).hexdigest(),
          'baseline_feasible':True,
          'solver':{'method':'scipy.optimize.minimize/SLSQP','scipy_version':scipy.__version__,
                    'ftol':1e-10,'maxiter':1000,'hard_timeout_s':120,'calls':0}}
    return local,a,rhs,lo,hi,c,d,x0,meta


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--solve',action='store_true')
    parser.add_argument('--approved-prepared-sha',default='');args=parser.parse_args()
    local,a,rhs,lo,hi,c,d,x0,rec=prepare()
    prepared=HERE/'prepared.json'
    if not args.solve:
        prepared.write_text(json.dumps(rec,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':rec['status'],'variables':len(x0),'descent_rows':len(d),
                          'centers':rec['descent_centers'],'witnesses':len(rec['witnesses'])}));return
    if not prepared.is_file() or old.sha(prepared)!=args.approved_prepared_sha:
        raise AssertionError('approval does not bind prepared metadata')
    previous=json.loads(prepared.read_text(encoding='utf-8'))
    if rec!=previous:raise AssertionError('author/plan/domain/matrices changed since preparation')
    out=HERE/'candidate-terrain.npz';receipt=HERE/'authoring.json'
    if out.exists() or receipt.exists():raise FileExistsError('output already exists')
    with (HERE/'solve-started.json').open('x',encoding='utf-8') as f:json.dump(rec,f,indent=2)
    start=time.monotonic();result=solve_once(a,rhs,lo,hi,c,d,x0);elapsed=time.monotonic()-start
    for p,wanted in rec['source_pins'].items():
        if old.sha(p)!=wanted:raise AssertionError(f'input changed during solve:{p}')
    values=np.asarray(result['x'],dtype=np.float32)
    if not np.isfinite(values).all() or np.any(values.astype(float)<lo) or np.any(values.astype(float)>hi):
        raise AssertionError('quantized bound violation; no repair')
    h=local['b']['heights'].copy()
    for node,value in zip(local['variables'],values):h[tuple(node)]=value
    if any(h[tuple(rc)]!=local['b']['heights'][tuple(rc)] for rc in rec['guard_rc']):
        raise AssertionError('quantized collar guard changed; no repair')
    if not witnesses_hold(h,rec['witnesses']):raise AssertionError('quantized descent violation; no repair')
    output=dict(local['b']);output['heights']=h
    with out.open('xb') as f:np.savez_compressed(f,**output)
    rec.update({'status':'AUTHORED_PENDING_INDEPENDENT_CONSUMER','candidate_path':str(out),
                'candidate_sha256':old.sha(out),'elapsed_solver_s':elapsed,
                'changed_vertices':int(np.count_nonzero(h!=local['b']['heights'])),
                'approved_prepared_sha256':args.approved_prepared_sha})
    rec['solver'].update({k:result[k] for k in ('success','status','message','nit','cost')})
    rec['solver']['calls']=1
    receipt.write_text(json.dumps(rec,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:rec[k] for k in ('status','candidate_sha256','changed_vertices','elapsed_solver_s')}))


if __name__=='__main__':main()
