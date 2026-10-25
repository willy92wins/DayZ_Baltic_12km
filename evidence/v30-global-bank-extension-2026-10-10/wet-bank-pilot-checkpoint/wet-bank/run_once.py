"""One reviewed local Oredezh solve. Writes unaccepted offline artifacts only."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,sys,time,traceback
from pathlib import Path
if sys.flags.optimize:raise RuntimeError('Evidence runner rejects optimized Python')
import numpy as np
from scipy import sparse
ROOT=Path(__file__).resolve().parent
G=ROOT.parent.parent
CP=G/'global-operator-prototype/face-slope-cone-pilot/pilot.py'
CP_SHA='d743f5006e0aa6606024a3c3291a74cb52b78f76c1aa5c6dfd95cdd26cdc9d2a'
BASE=G/'global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz'
BASE_SHA='40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def readcsr(z,p):
    return sparse.csr_matrix((z[p+'_data'],z[p+'_indices'],z[p+'_indptr']),shape=tuple(z[p+'_shape']))
def run(a):
    if a.out.resolve()!=(ROOT/'solve-once').resolve():raise ValueError('Only the fixed one-call output directory is allowed')
    if a.out.exists():raise FileExistsError('One-call output already exists; no second solve')
    if sha(a.review)!=a.review_sha256:raise ValueError('Review changed')
    review=json.loads(a.review.read_text(encoding='utf-8'))
    if review.get('status')!='PASS_WET_BANK_PREFLIGHT_ONLY' or review.get('ready_for_one_solve') is not True:
        raise ValueError('No independent ready-for-one-solve verdict')
    if not review.get('checks') or not all(v is True for v in review['checks'].values()):raise ValueError('Review gates failed')
    expected=review['prepared_sha256']
    if sha(a.prepared)!=expected:raise ValueError('Prepared changed since review')
    if sha(CP)!=CP_SHA or sha(BASE)!=BASE_SHA:raise ValueError('Solver or baseline changed')
    prep_receipt=a.prepared.with_name('preparation.json')
    author_receipt=json.loads(prep_receipt.read_text(encoding='utf-8'))
    if author_receipt['prepared_sha256']!=expected:raise ValueError('Prepared receipt mismatch')
    source=ROOT/'prepare_wet_bank_matrices.py'
    if sha(source)!=author_receipt['source_code_hashes']['prepare_wet_bank_matrices.py']:raise ValueError('Preparation source changed')
    if review['source_sha256']!=sha(source):raise ValueError('Reviewed preparation source mismatch')
    pins={str(p):sha(p) for p in (a.review,a.prepared,prep_receipt,source,CP,BASE,Path(__file__),ROOT/'RUN_PROTOCOL.md')}
    spec=importlib.util.spec_from_file_location('wet_cone_solver',CP)
    cp=importlib.util.module_from_spec(spec);sys.modules[spec.name]=cp;spec.loader.exec_module(cp)
    closure_mod=cp.load_order_closure();pins[str(cp.ORDER_CLOSURE)]=cp.ORDER_CLOSURE_SHA
    with np.load(a.prepared,allow_pickle=False) as z:
        A=readcsr(z,'A');C=readcsr(z,'C');Gmat=readcsr(z,'G')
        rhs=z['rhs_A'];d=z['d_C'];k=z['k_G'];radii=z['radii_G']
        lo=z['lo_absolute_float32_inward'];hi=z['hi_absolute_float32_inward'];x0=z['x0_absolute']
        rc=z['variables_rc'];B=z['base_heights_context'];witness=z['d8_witnesses_local']
    window=np.asarray(author_receipt['geometry']['window_rc_half_open'],dtype=np.int64)
    if window.shape!=(4,) or np.any(window<0):raise ValueError('Invalid context window')
    r0,r1,c0,c1=map(int,window)
    with np.load(BASE,allow_pickle=False) as z:
        base_context=z['heights'][r0:r1,c0:c1]
    if B.dtype!=np.float32 or base_context.shape!=B.shape or not np.array_equal(B.view(np.uint32),base_context.view(np.uint32)):
        raise ValueError('Entire prepared context differs from pinned EV95 baseline')
    origin=window[[0,2]]
    nodes=rc-origin
    if not np.array_equal(x0,B[tuple(nodes.T)].astype(np.float64)):raise ValueError('Local baseline differs')
    if len(nodes)!=121 or A.shape[1]!=121 or C.shape[1]!=121 or Gmat.shape[1]!=121:raise ValueError('Unexpected operator domain')
    # This marker is created before the only numerical call and never removed.
    a.out.mkdir(parents=True,exist_ok=False);started=time.perf_counter()
    (a.out/'invocation.json').write_text(json.dumps({'state':'STARTED_ONE_CALL','pins':pins},indent=2)+'\n',encoding='utf-8')
    try:
        def progress(v):
            with (a.out/'progress.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(v)+'\n')
        numerical=time.perf_counter()
        x,solver,history,state=cp.solve_admm(A,rhs,C,d,Gmat,k,radii,lo.astype(float),hi.astype(float),x0,budget_s=120.,progress=progress)
        raw=B.copy();raw[tuple(nodes.T)]=x.astype(np.float32)
        ids=np.ravel_multi_index(tuple(nodes.T),B.shape)
        lower=B.ravel().copy();upper=lower.copy();fixed=np.ones(B.size,bool)
        lower[ids]=lo;upper[ids]=hi;fixed[ids]=False
        centers=witness[:,:2];neighbors=witness[:,2:]
        edges=np.column_stack((np.ravel_multi_index(tuple(neighbors.T),B.shape),np.ravel_multi_index(tuple(centers.T),B.shape)))
        def guard():
            if time.perf_counter()-numerical>120.:raise TimeoutError('120s total numerical budget exceeded')
            if cp.memory_snapshot()['peak_working_set_bytes']>cp.PEAK_WS_LIMIT:raise MemoryError('Peak WS exceeded')
        closure=closure_mod.project_order(raw.ravel(),lower,upper,edges,baseline=B.ravel(),fixed=fixed,guard=guard)
        closed=closure['q'].reshape(B.shape);guard()
        numerical_elapsed=time.perf_counter()-numerical
        values=closed[tuple(nodes.T)].astype(float)
        cost=lambda v:.5*float(np.sum((A@v-rhs)**2))
        costs={'baseline':cost(x0),'raw_float32':cost(raw[tuple(nodes.T)].astype(float)),'closed_float32':cost(values)}
        energy=closure_mod.evaluate_objective_gates(costs['raw_float32'],costs['closed_float32'],costs['baseline'])
        q=(Gmat@values+k).reshape(-1,2)
        np.savez_compressed(a.out/'solution.npz',variables_rc=rc,baseline_float32=B,
            raw_float32_grid=raw,closed_float32_grid=closed,solution_float64=x,
            closure_clipped=closure['clipped'],closure_upper_propagated=closure['upper_propagated'],**state)
        # Name explicitly records lack of independent post-solve acceptance.
        with np.load(BASE,allow_pickle=False) as z:terrain={name:z[name] for name in z.files}
        terrain['heights'][tuple(rc.T)]=values.astype(np.float32)
        np.savez_compressed(a.out/'unaccepted-candidate-terrain.npz',**terrain)
        after={p:sha(p) for p in pins}
        report={'status':'UNACCEPTED_WET_BANK_SOLVE_OUTPUT','solver':solver,'history':history,
            'objective':costs,'closure_energy':energy,
            'closure':{kk:vv for kk,vv in closure.items() if kk not in ('q','clipped','upper_propagated')},
            'diagnostics':{'closed_C_min_slack':float(np.min(C@values-d)),
                'closed_max_raw_cone_norm_excess':float(np.max(np.linalg.norm(q,axis=1)-radii)),
                'closed_bounds_bad':int(np.count_nonzero((values<lo)|(values>hi))),
                'closed_D8_bad':int(np.count_nonzero(closed[tuple(centers.T)]<closed[tuple(neighbors.T)])),
                'changed_vertices':int(np.count_nonzero(values!=x0))},
            'elapsed_numerical_s':numerical_elapsed,'elapsed_total_s':time.perf_counter()-started,
            'peak_memory':cp.memory_snapshot(),'readset_start':pins,'readset_end':after,'readset_stable':pins==after,
            'outputs':{name:sha(a.out/name) for name in ('solution.npz','unaccepted-candidate-terrain.npz')},
            'limits':['Exactly one solver call, no damping or retry; no P/F, water-object or deployed-world edit.',
                      'Independent shape, signs/crossings, slope, topology and compiled-coverage gates still required.']}
        (a.out/'solve-result.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        print(json.dumps({k:report[k] for k in ('status','objective','diagnostics','elapsed_numerical_s','readset_stable')},allow_nan=False))
    except Exception as e:
        (a.out/'failure.json').write_text(json.dumps({'status':'FAILED_ONE_CALL','error':repr(e),'traceback':traceback.format_exc(),'elapsed_s':time.perf_counter()-started},indent=2)+'\n',encoding='utf-8')
        raise
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepared',type=Path,required=True);p.add_argument('--review',type=Path,required=True)
    p.add_argument('--review-sha256',required=True);p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
