"""One fresh bounded solve on the reviewed EV94 preflight; no map export/build.

Only the isolated solver module's iteration budget is changed (10000 -> 20000).
Mathematics and tolerances are byte-pinned. Order closure is the reviewed OC
projection. Success publishes a LOCAL candidate pending independent consumer.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys
import time
from types import SimpleNamespace
import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
RS = HERE.parent
SOLVER = RS.parent / 'admm-quantized-pilot/solve.py'
OC = RS / 'order-closure/author_order_closure.py'
PROJECTION = RS / 'order-closure/projection.py'
PINS = {
    SOLVER: '7e8636bf54ba23f7e23bc2f06464100439468da7b4edca85f96c72d0cd40e149',
    OC: 'b6d70d061425601624baa8bab8825f3d7ca40c01432032123d0b97269e1cb53d',
    PROJECTION: 'a990dc2d33fca4fd2a446b958f0412a2d752a5d3072a85d82058bb634cfaf44b',
}
MAX_ITER = 20000
NUMERIC_S = 600.0
PEAK_BYTES = 1610612736
FREE_BYTES = 3221225472
OUTPUT_BYTES = 2 * 1024 ** 3


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def require(value, message):
    if not value:
        raise ValueError(message)


def check_hashes(readset):
    for path, expected in readset.items():
        require(sha(path) == expected, f'Source drift: {path}')
    return dict(readset)


def read_inputs(path, expected):
    require(sha(path) == expected, 'Preflight SHA mismatch')
    pre = json.loads(path.read_text(encoding='utf-8'))
    require(pre['status'] == 'PREFLIGHT_READY_ONLY', 'Preflight not ready')
    require(pre['source_hashes_start'] == pre['source_hashes_end'], 'Preflight readset drift')
    require(pre['driver_sha256_start_end'][0] == pre['driver_sha256_start_end'][1], 'Preflight driver drift')
    readset = dict(pre['source_hashes_end'])
    readset.update(pre['selected_units']['unit_readset'])
    readset.update({str(k):v for k,v in PINS.items()})
    readset[str(path)] = expected
    readset[pre['driver_path']] = pre['driver_sha256_start_end'][0]
    prepared = Path(pre['prepared_artifact']['path'])
    readset[str(prepared)] = pre['prepared_artifact']['sha256']
    readset[str(Path(__file__).resolve())] = sha(__file__)
    check_hashes(readset)
    require(pre['base_identity']['focal_sha256'] == '30d0ed33e477846297a17e758e34a51490d54ee809e8b63ec9d69229170d15a1', 'Wrong focal base')
    require(pre['selected_units']['count'] == 499 and pre['focus_pin']['explicitly_fixed'], 'Lost retained units/focus')
    require(pre['limits']['future_solver_only'] == {
        'calls':1,'continuation':False,'max_iterations':MAX_ITER,'numeric_seconds':600,
        'max_peak_working_set_bytes':PEAK_BYTES,'min_free_physical_bytes':FREE_BYTES}, 'Budget differs from reviewed preflight')
    with np.load(prepared, allow_pickle=False) as z:
        arrays = {k:z[k] for k in z.files}
    return pre, arrays, readset


def unpack(p):
    base = p['base_local']; nodes = p['nodes_local']; lo = p['lo']; hi = p['hi']; x0 = p['x0']
    require(base.shape == (260,260) and base.dtype == np.float32, 'Wrong local grid')
    require(nodes.ndim == 2 and nodes.shape[1] == 2 and np.issubdtype(nodes.dtype,np.integer), 'Invalid nodes')
    require(len(nodes) > 0 and len(np.unique(nodes,axis=0)) == len(nodes), 'Empty/duplicate nodes')
    require(np.all(nodes>=2) and np.all(nodes<258), 'Missing two-node collar')
    require(lo.shape == hi.shape == x0.shape == (len(nodes),), 'Wrong bounds')
    require(all(np.isfinite(a).all() for a in (base,lo,hi,x0)), 'Nonfinite numeric input')
    require(np.all(lo<=x0) and np.all(x0<=hi), 'Baseline infeasible bounds')
    require(np.array_equal(lo,lo.astype(np.float32).astype(np.float64)) and np.array_equal(hi,hi.astype(np.float32).astype(np.float64)), 'Nonrepresentable bounds')
    require(np.array_equal(x0,base[tuple(nodes.T)].astype(np.float64)), 'x0 is not fresh baseline')
    fixed = np.ones(base.shape,bool); fixed[tuple(nodes.T)] = False
    require(np.array_equal(fixed,p['fixed_mask'].astype(bool)), 'Fixed mask/node mismatch')
    A = sparse.csr_matrix((p['A_data'],p['A_indices'],p['A_indptr']), shape=tuple(p['A_shape']))
    C = sparse.csr_matrix((p['C_data'],p['C_indices'],p['C_indptr']), shape=tuple(p['C_shape']))
    rhs,d = p['rhs'],p['d']
    require(A.shape[1] == C.shape[1] == len(nodes) and rhs.shape == (A.shape[0],) and d.shape == (C.shape[0],), 'Operator shape mismatch')
    require(all(np.isfinite(a).all() for a in (A.data,C.data,rhs,d)), 'Nonfinite operator')
    require(np.min(C@x0-d, initial=0) >= -1e-12, 'Baseline D8 infeasible')
    witnesses = json.loads(p['witnesses_json'].tobytes().decode('utf-8'))
    edges = np.asarray([(int(w['witness'][0])*260+int(w['witness'][1]),int(w['center'][0])*260+int(w['center'][1])) for w in witnesses],np.int64).reshape(-1,2)
    return base,nodes,lo,hi,x0,fixed,A,rhs,C,d,witnesses,edges


def execute(preflight, preflight_sha, out):
    require(not out.exists(), 'Fresh-only output exists')
    out.mkdir(parents=False,exist_ok=False)
    report = {'status':'ERROR','candidate_path':None,'scope':'local solver only, independent consumer required',
              'fresh_start':True,'continuation':False,'preflight_path':str(preflight),'preflight_sha256':preflight_sha,
              'budgets':{'max_iterations':MAX_ITER,'numeric_seconds':NUMERIC_S,'peak_bytes':PEAK_BYTES,'free_bytes':FREE_BYTES},
              'algorithm_override':{'MAX_ITER':{'original':10000,'effective':MAX_ITER}},
              'source_hashes_start':{},'source_hashes_end':{}}
    started = time.perf_counter()
    numeric_start = None
    try:
        pre,p,readset = read_inputs(preflight,preflight_sha)
        report['source_hashes_start'] = readset
        base,nodes,lo,hi,x0,fixed,A,rhs,C,d,witnesses,edges = unpack(p)
        solver = load('ev94_fresh_original_solver',SOLVER)
        oc = load('ev94_fresh_oc_helpers',OC)
        projection = load('ev94_fresh_projection',PROJECTION)
        require(solver.MAX_ITER == 10000 and (solver.RHO,solver.ABS_TOL,solver.REL_TOL) == (1.,1e-10,1e-8), 'Original solver constants changed')
        solver.MAX_ITER = MAX_ITER
        memory_before = oc.get_memory_snapshot()
        report['memory_before'] = memory_before
        require(memory_before['available_physical_bytes'] >= FREE_BYTES, 'Less than 3 GiB available')
        require(memory_before['peak_working_set_bytes'] <= PEAK_BYTES, 'Initial memory budget exceeded')
        numeric_start = time.perf_counter()
        last_check = [numeric_start]; last_memory = [memory_before]
        def guarded_clock():
            now = time.perf_counter()
            if now-last_check[0] >= .25:
                last_memory[0] = oc.get_memory_snapshot(); last_check[0] = now
                if last_memory[0]['peak_working_set_bytes'] > PEAK_BYTES:
                    raise MemoryError('Peak working set exceeds 1.5 GiB')
            if now-numeric_start > NUMERIC_S:
                raise TimeoutError('600 s whole numerical budget exceeded')
            return now
        # Instrument the original guard through its module-local clock only.
        # No global time monkeypatch and no numerical operator change.
        solver.time = SimpleNamespace(perf_counter=guarded_clock)
        def progress(row):
            with (out/'progress.jsonl').open('a',encoding='utf-8') as f:
                f.write(json.dumps(row,allow_nan=False)+'\n')
        x,diag,history,state = solver.solve(A,rhs,C,d,lo,hi,x0,NUMERIC_S,progress)
        report['diagnostics'] = diag
        report['numeric_elapsed_s'] = guarded_clock()-numeric_start
        raw = base.copy(); raw[tuple(nodes.T)] = x.astype(np.float32)
        np.savez_compressed(out/'solver-state.npz',x64=x,raw_float32=raw,nodes_local=nodes,lo=lo,hi=hi,**state)
        report['solver_state_sha256'] = sha(out/'solver-state.npz')
        report['solver_state_path'] = str(out/'solver-state.npz')
        kkt = oc.kkt_report({'diagnostics':diag},A,rhs,C,d,lo,hi,x,state)
        report['kkt'] = kkt
        if diag['status'] != 'CONVERGED' or not kkt['pass']:
            report['status'] = 'REJECTED_CONTINUOUS_GATES'
        else:
            lower=base.copy(); upper=base.copy()
            lower[tuple(nodes.T)]=lo; upper[tuple(nodes.T)]=hi
            closed=projection.project_order(raw.ravel(),lower.ravel(),upper.ravel(),edges,
                                            baseline=base.ravel(),fixed=fixed.ravel(),guard=guarded_clock)
            h=closed['q'].reshape(base.shape)
            _,shape=solver.check_float32(base,nodes,h[tuple(nodes.T)],lo,hi,witnesses)
            cost0=solver.objective(A,rhs,x0)
            rawcost=solver.objective(A,rhs,raw[tuple(nodes.T)].astype(np.float64))
            cost=solver.objective(A,rhs,h[tuple(nodes.T)].astype(np.float64))
            correction=float(np.max(np.abs(h.astype(np.float64)-raw.astype(np.float64)),initial=0))
            bound=float(closed['clip_max_abs']+closed['raw_order_violation_sum_after_clip'])
            report['closure']={k:(v.item() if isinstance(v,np.generic) else v) for k,v in closed.items() if not isinstance(v,np.ndarray)}
            report['float32']=shape
            report['objective']={'base':cost0,'raw':rawcost,'closed':cost,'closure_allowance':1e-7*max(1.,rawcost)}
            gates={'KKT':kkt['pass'],'float32':bool(shape['pass']),
                   'objective_reduced':cost<cost0,'closure_cost_budget':cost-rawcost<=1e-7*max(1.,rawcost),
                   'closure_correction_bound':correction<=bound+1e-15,
                   'fixed_exact':bool(np.array_equal(h[fixed],base[fixed])),
                   'focus_exact':bool(h[130,130]==np.float32(3.278029680252075))}
            report['gates']=gates
            guarded_clock()
            report['memory_after_numeric']=oc.get_memory_snapshot()
            require(report['memory_after_numeric']['peak_working_set_bytes'] <= PEAK_BYTES, 'Final numeric memory budget exceeded')
            report['numeric_elapsed_s']=guarded_clock()-numeric_start
            if all(gates.values()):
                report['status']='LOCAL_CANDIDATE_PENDING_INDEPENDENT_CONSUMER'
                pending=h.copy()
            else:
                report['status']='REJECTED_LOCAL_NUMERIC_GATES'
                pending=None
        report['source_hashes_end']=check_hashes(readset)
        if report['status']=='LOCAL_CANDIDATE_PENDING_INDEPENDENT_CONSUMER':
            np.savez_compressed(out/'candidate-local.npz',candidate=pending,base=base,nodes_local=nodes)
            report['candidate_path']=str(out/'candidate-local.npz')
            report['candidate_sha256']=sha(out/'candidate-local.npz')
        require(sum(p.stat().st_size for p in out.iterdir() if p.is_file())<=OUTPUT_BYTES,'Output exceeds 2 GiB')
    except Exception as exc:
        report['status']='STOP_ERROR_OR_RESOURCE_LIMIT'
        report['error']=repr(exc)
        report['candidate_path']=None
        report['candidate_sha256']=None
    report['wall_s']=time.perf_counter()-started
    (out/'solve-result.json').write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:report.get(k) for k in ('status','error','numeric_elapsed_s','wall_s','candidate_sha256')}))
    return 0 if report['status']=='LOCAL_CANDIDATE_PENDING_INDEPENDENT_CONSUMER' else 2


if __name__=='__main__':
    if not __debug__: raise RuntimeError('Optimized Python is forbidden')
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preflight',type=Path,required=True)
    ap.add_argument('--preflight-sha',required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    raise SystemExit(execute(args.preflight,args.preflight_sha,args.output))
