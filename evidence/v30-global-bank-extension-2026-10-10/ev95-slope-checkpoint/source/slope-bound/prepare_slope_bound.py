"""Derive one scalar slope bound; preserve all other EV94 prepared arrays."""
from pathlib import Path
import argparse, copy, hashlib, importlib.util, json, math, sys, time
import numpy as np

HERE = Path(__file__).resolve().parent
REB = HERE.parent
PLAN = HERE / 'PLAN_SLOPE_BOUND.md'
ORIGINAL = REB / 'preflight-run-05/preflight.json'
PREPARED = REB / 'preflight-run-05/prepared.npz'
DRIVER = REB / 'solve_ev94.py'
REVIEW = REB / 'consumer/full-run-02.json'
FOCAL = REB.parent / 'focus-unit/author-run-01/candidate-terrain.npz'
PINS = {
    ORIGINAL: 'a6ae4b91cf5ebabbfc57352e4f988150eea2a7506b74a610b6aa4ce79a2bf4d7',
    PREPARED: '2df4ad67280c656025843f6528147a68c03dfcf6ecdfbe9cce2ee4818e15a2eb',
    DRIVER: 'ebb53986d69e4ec080356883db15091983fef3bb01715714177d2d504283abf0',
    REVIEW: '259c87fa01894eb3db409f6087e7cd3b787918e1e08629b4e53ad0fdd2e24030',
    FOCAL: '30d0ed33e477846297a17e758e34a51490d54ee809e8b63ec9d69229170d15a1',
}
TARGET = (900,446)
FACE = ((899,445),(899,446),(900,446))
CONTEXT_ORIGIN = (710,240)

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def check(items):
    out = {}
    for path, wanted in items.items():
        actual = sha(path)
        require(actual == wanted, 'SHA drift: ' + str(path))
        out[str(Path(path).resolve())] = actual
    return out

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

def scalar_interval(nw, ne, baseline, lower, upper, fixed=(True,True)):
    """The slope decreases throughout [baseline, upper] when upper <= NE."""
    require(all(math.isfinite(float(v)) for v in (nw,ne,baseline,lower,upper)), 'Nonfinite heights')
    require(tuple(fixed) == (True,True), 'Two upper vertices must be fixed')
    require(lower <= baseline <= upper <= ne, 'Interval is not feasible/monotone below NE')
    require(float(np.float32(baseline)) == baseline, 'Baseline is not exact float32')
    slope = lambda h: math.degrees(math.atan(math.hypot(ne-nw,ne-h)/6.0))
    old = slope(baseline); end = slope(upper)
    require(end <= old + 1e-12, 'Monotonic slope endpoint failed')
    return float(baseline), {'lower_m':float(baseline), 'upper_m':float(upper),
        'NW_m':float(nw), 'NE_m':float(ne), 'baseline_SE_m':float(baseline),
        'baseline_slope_deg':old, 'upper_endpoint_slope_deg':end,
        'interval_slope_cap_deg':max(35.0,old), 'angular_tolerance_consumed':False,
        'proof':'NE-SE is nonnegative and decreases over the full interval; the other gradient component is fixed.'}

def derive(p):
    rows = np.asarray(p['nodes_local']) + np.asarray(CONTEXT_ORIGIN)
    hits = np.flatnonzero(np.all(rows == TARGET, axis=1))
    require(len(hits) == 1, 'Target must be exactly one mobile variable')
    i = int(hits[0])
    local = [(r-CONTEXT_ORIGIN[0],c-CONTEXT_ORIGIN[1]) for r,c in FACE]
    base = p['base_local']
    nw, ne, se = (float(base[rc]) for rc in local)
    require((nw,ne,se) == (7.2344970703125,3.1139774322509766,2.2943551540374756), 'Frozen face heights differ')
    require(not bool(p['fixed_mask'][local[2]]), 'SE is unexpectedly fixed')
    require(p['lo'][i] == 1.8000000715255737 and p['hi'][i] == 2.7943551540374756, 'Physical interval changed')
    lower, proof = scalar_interval(nw,ne,se,float(p['lo'][i]),float(p['hi'][i]),
                                  [bool(p['fixed_mask'][local[0]]),bool(p['fixed_mask'][local[1]])])
    out = {k:v.copy() for k,v in p.items()}
    out['lo'][i] = lower
    for k in p:
        if k == 'lo':
            require(np.flatnonzero(out[k] != p[k]).tolist() == [i], 'Not exactly one lower bound changed')
        else:
            require(out[k].dtype == p[k].dtype and out[k].shape == p[k].shape
                    and out[k].tobytes() == p[k].tobytes(), 'Array changed: ' + k)
    return out, {'variable_index':i, 'target_rc':list(TARGET), 'face_cell_rc':[899,445],
        'face_kind':'NW_NE_SE', 'fixed_neighbors_rc':[list(FACE[0]),list(FACE[1])],
        'previous_lower_m':float(p['lo'][i]), 'new_lower_m':lower,
        'prepared_arrays_changed':['lo'], 'changed_entries':1, **proof}

def prepare(out):
    started = time.perf_counter()
    require(not out.exists(), 'Fresh output already exists')
    original = read(ORIGINAL)
    require(original['status'] == 'PREFLIGHT_READY_ONLY', 'Original preflight not ready')
    require(original['source_hashes_start'] == original['source_hashes_end'], 'Original readset drift')
    source = dict(original['source_hashes_start'])
    source.update({str(p):digest for p,digest in PINS.items()})
    source[str(PLAN)] = sha(PLAN)
    source[str(Path(__file__).resolve())] = sha(__file__)
    start = check(source)
    unit_start = check(original['selected_units']['unit_readset'])
    review = read(REVIEW)
    require(review['status'] == 'FAIL_EV94_REBASE_SECTOR_OFFLINE'
            and [k for k,v in review['gates'].items() if not v] == ['slope_hinge_global_nonregression']
            and review['information']['geometry']['slope_violation_count_global'] == 1,
            'Failure is not the diagnosed single slope')
    with np.load(PREPARED,allow_pickle=False) as z:
        prior = {k:z[k] for k in z.files}
    p, proof = derive(prior)
    driver = load('ev94_scalar_bound_original_driver',DRIVER)
    base,nodes,lo,hi,x0,fixed,A,rhs,C,d,witnesses,edges = driver.unpack(p)
    projection = load('ev94_scalar_bound_projection',driver.PROJECTION)
    require(sha(driver.PROJECTION) == driver.PINS[driver.PROJECTION], 'Projection source drift')
    lower = base.copy(); upper = base.copy()
    lower[tuple(nodes.T)] = lo; upper[tuple(nodes.T)] = hi
    q = projection.project_order(base.ravel(),lower.ravel(),upper.ravel(),edges,
                                 baseline=base.ravel(),fixed=fixed.ravel())['q'].reshape(base.shape)
    require(q.tobytes() == base.tobytes(), 'Baseline projection changed')
    out.mkdir(parents=True,exist_ok=False)
    prepared = out / 'prepared.npz'
    np.savez_compressed(prepared,**p)
    result = copy.deepcopy(original)
    result.update(schema='ev94.scalar-slope-preflight.v1',
        scope='One scalar slope constraint on the same EV94 problem; no solver or terrain export',
        plan_path=str(PLAN), plan_sha256=sha(PLAN), driver_path=str(Path(__file__).resolve()),
        driver_sha256_start_end=[sha(__file__),sha(__file__)],
        source_hashes_start=start, source_hashes_end=check(start),
        slope_bound=proof, original_preflight={'path':str(ORIGINAL),'sha256':PINS[ORIGINAL]},
        original_prepared={'path':str(PREPARED),'sha256':PINS[PREPARED]},
        prepared_artifact={'path':str(prepared),'sha256':sha(prepared),'size_bytes':prepared.stat().st_size},
        elapsed_seconds=time.perf_counter()-started)
    result['limits']['artifact_bytes_total'] = prepared.stat().st_size
    result['system']['base_projection_zero_correction'] = True
    require(check(unit_start) == unit_start, 'Retained-unit drift')
    require(result['source_hashes_start'] == result['source_hashes_end'], 'Source drift')
    (out/'preflight.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'out':str(out),'slope_bound':proof,
                      'preflight_sha256':sha(out/'preflight.json'),'prepared_sha256':sha(prepared)}))

if __name__ == '__main__':
    if not __debug__: raise RuntimeError('Optimized Python forbidden')
    ap = argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True)
    prepare(ap.parse_args().out.resolve())
