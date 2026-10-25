"""Read-only compiled-water consumer for the Oredezh wet-bank experiment.

This reuses the frozen independent geometric consumer, never the optimizer.
No terrain, package, indexed face or P/F field is written by this program.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
if sys.flags.optimize:
    raise RuntimeError('This evidence consumer requires assertions enabled; optimized Python is rejected.')
import numpy as np

G = Path('E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
PROTO = G/'global-operator-prototype'
HERE = Path(__file__).resolve().parent
BASE = PROTO/'real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz'
CONSUMER = G/'consumer-global/verify_layer.py'
CIVIL = PROTO/'global-civil-ev95/run-01/inventory.json'
P = G/'build-wide-slope/candidate/plane.npy'
F = G/'build-wide-slope/candidate/visible-field.npy'
WATER = Path('P:/Mods/@DayZ_Baltic_EV95_WideBankPreviewV1/Addons/baltic_water_v30.pbo')
WORLD = WATER.with_name('narva_trial.pbo')
STAGE = G/'build-wide-slope/stage.json'
DEPLOY = G/'build-wide-slope/deploy.json'
PINS = {
    BASE:'40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a',
    CONSUMER:'33050881caaf5e75f288d4122222c15eb326bf146c28a4c723760564457b3dc2',
    CIVIL:'cdebbbce50644407642e791388e44c40b15499041844607650b885d1bc618856',
    P:'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
    F:'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
    WATER:'3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14',
    WORLD:'f1a148cab3e7d1d63473f0232a0971d45a9fea04e0fb456f01973235f4644b7d',
    STAGE:'b04b066d99f9c22a4fffd77c66762d3e9e744dfa2bbf20d8508f076845571dda',
    DEPLOY:'f5a9c8185812e0b77a804ef9811e0405b5a7969f8ccfc19b85cc29d23cac03ca',
}
CORE = (857, 868, 1181, 1192)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024), b''): h.update(block)
    return h.hexdigest()

def checked_sources():
    pins = dict(PINS)
    assert sha(CIVIL) == pins[CIVIL], 'civil receipt changed'
    civil = json.loads(CIVIL.read_text(encoding='utf-8'))
    stage = json.loads(STAGE.read_text(encoding='utf-8'))
    deploy = json.loads(DEPLOY.read_text(encoding='utf-8'))
    identity = bool(civil['objects_exact_vs_B'] and civil['object_count'] == 18033
        and stage['objects_and_materials_exact'] and stage['objects'] == 18033
        and stage['terrain_sha256'] == PINS[BASE]
        and stage['baseline_water_pbo_sha256'] == PINS[WATER]
        and deploy['terrain_sha256'] == PINS[BASE]
        and deploy['files']['narva_trial.pbo'] == PINS[WORLD]
        and deploy['files']['baltic_water_v30.pbo'] == PINS[WATER])
    assert identity, 'EV95 deployed/source identity chain disagrees'
    assert civil['source_pins_start'] == civil['source_pins_end']
    pins.update({Path(k):v for k,v in civil['source_pins_start'].items()})
    pins[Path(__file__).resolve()] = sha(__file__)
    actual = {str(k):sha(k) for k in pins}
    assert all(actual[str(k)] == v for k,v in pins.items()), 'source pin drift'
    return actual, identity

def validate_candidate(base, candidate):
    assert candidate.shape == base.shape == (2048,2048), 'full native grid required'
    assert candidate.dtype == base.dtype == np.dtype('float32'), 'float32 heights required'
    assert np.isfinite(candidate).all(), 'nonfinite candidate'
    changed = np.argwhere(candidate.view(np.uint32) != base.view(np.uint32))
    r0,r1,c0,c1 = CORE
    assert all(r0 <= r < r1 and c0 <= c < c1 for r,c in changed), 'outside pilot core changed'
    return changed

def fixtures(cv):
    from shapely.geometry import box
    design = box(0,0,6,6)
    whole = box(0,0,6,6)
    missing = box(0,0,5.99,6)
    assert cv.coverage_holes_pass([design.difference(whole).area], [0.])
    assert not cv.coverage_holes_pass([0.], [design.difference(missing).area])
    assert not cv.coverage_holes_pass([design.difference(missing).area], [0.])
    a = np.zeros((2048,2048), dtype=np.float32)
    assert len(validate_candidate(a,a)) == 0
    b = a.copy(); b[CORE[0],CORE[2]] = 1
    assert len(validate_candidate(a,b)) == 1
    b[0,0] = 1
    try: validate_candidate(a,b)
    except AssertionError: pass
    else: raise AssertionError('outside-core negative was accepted')
    return {'full_support_positive':True, 'missing_support_negative':True,
            'inherited_missing_support_negative':True, 'outside_core_negative':True}

def lower_from_prepared(base, prepared, expected_sha):
    if not prepared or not expected_sha or len(expected_sha)!=64:
        raise ValueError('Candidate requires the independently reviewed prepared NPZ and its SHA256')
    if sha(prepared)!=expected_sha:
        raise ValueError('Prepared bounds SHA256 mismatch')
    with np.load(prepared,allow_pickle=False) as z:
        rc=z['variables_rc']; lo=z['lo_absolute_float32_inward']; hi=z['hi_absolute_float32_inward']
        x0=z['x0_absolute']; lo64=z['lo_absolute_float64'];hi64=z['hi_absolute_float64']
    r0,r1,c0,c1=CORE
    expected=np.asarray([(r,c) for r in range(r0,r1) for c in range(c0,c1)],dtype=np.int32)
    if not np.array_equal(rc,expected):raise ValueError('Prepared variable domain differs from this pilot')
    if lo.dtype!=np.float32 or hi.dtype!=np.float32 or any(v.shape!=(len(rc),) for v in (lo,hi,x0,lo64,hi64)):raise ValueError('Prepared bounds schema')
    if not all(np.isfinite(v).all() for v in (lo,hi,x0,lo64,hi64)) or np.any(lo>hi):raise ValueError('Invalid prepared bounds')
    if not np.array_equal(x0,base[tuple(rc.T)].astype(np.float64)):raise ValueError('Prepared baseline differs from EV95')
    if np.any(lo.astype(float)<lo64) or np.any(hi.astype(float)>hi64):raise ValueError('Prepared bounds are not inward')
    result=base.copy();result[tuple(rc.T)]=lo
    return result

def run(candidate, lower, output, prepared=None, prepared_sha256=None):
    t = time.monotonic()
    assert not output.exists(), 'do not overwrite an evidence receipt'
    if candidate and (not prepared or not prepared_sha256):
        raise ValueError('Candidate requires bounds reconstructed from pinned reviewed prepared data')
    before, identity = checked_sources()
    spec = importlib.util.spec_from_file_location('wet_geometric_consumer', CONSUMER)
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    _,_,ev87,cv,_,_,idxmod = mod.load_helpers()
    before.update({str(k):v for k,v in mod.PINS.items()})
    tests = fixtures(cv)
    with np.load(BASE, allow_pickle=False) as z: hb = z['heights']
    hh = hb.copy()
    if candidate:
        before[str(candidate)] = sha(candidate)
        with np.load(candidate, allow_pickle=False) as z: hh = z['heights']
    changed = validate_candidate(hb,hh)
    # Evaluate all incident cells of the entire possible core even for H==B.
    # Baseline==candidate must never give an empty-domain vacuous PASS.
    r0,r1,c0,c1 = CORE
    evaluated = np.array([(r,c) for r in range(r0,r1) for c in range(c0,c1)],dtype=np.int32)
    lo = hh.copy()
    if candidate:
        before[str(prepared)]=prepared_sha256
        lo=lower_from_prepared(hb,prepared,prepared_sha256)
    if lower:
        before[str(lower)] = sha(lower)
        supplied = np.load(lower,allow_pickle=False)
        assert supplied.shape == hb.shape and supplied.dtype == np.float32 and np.isfinite(supplied).all()
        assert np.array_equal(supplied.view(np.uint32),lo.view(np.uint32)), 'supplied lower is not the exact prepared bound grid'
    assert np.all(lo <= hh), 'lower bound not below candidate'
    index = idxmod.FaceRangeIndex(mod.INDEX_RUN)
    receipt = mod.coverage_from_index(ev87,cv,index,hb,hh,lo,
        {'P':np.load(P,mmap_mode='r'), 'F':np.load(F,mmap_mode='r')},evaluated,set())
    assert receipt['changed_support_cells'] > 0
    index.reverify()
    for shard in index.manifest['shards']:
        before[str(index.run_dir/shard['path'])] = shard['sha256']
    after = {k:sha(k) for k in before}
    receipt['gates']['all_source_pins_stable'] = before == after
    receipt['gates']['candidate_only_inside_core'] = bool(all(CORE[0]<=r<CORE[1] and CORE[2]<=c<CORE[3] for r,c in changed))
    receipt['gates']['EV95_objects_and_deployed_water_same_as_indexed_B'] = identity
    receipt['gates']['nonempty_evaluation_domain'] = receipt['changed_support_cells'] > 0
    if candidate:receipt['gates']['lower_envelope_from_pinned_prepared_bounds'] = sha(prepared)==prepared_sha256
    ok = all(receipt['gates'].values())
    report = {'status':('PASS' if ok else 'FAIL')+'_LOCAL_COMPILED_WATER_'+('CANDIDATE' if candidate else 'BASELINE'),
        'candidate_path':str(candidate) if candidate else None, 'candidate_changed_vertices':len(changed),
        'evaluated_core':list(CORE),'evaluated_potential_vertices':len(evaluated),
        'prepared_bounds_path':str(prepared) if candidate else None,
        'prepared_bounds_sha256':prepared_sha256 if candidate else None,
        'fixtures':tests, 'coverage':receipt,'source_pins_start':before,'source_pins_end':after,
        'elapsed_s':time.monotonic()-t,
        'limits':['Static geometry only; no visual, dynamic-water or whole-map acceptance.',
            'The inherited B bounds/PBO guard is linked to EV95 by exact WRP objects and identical deployed water.',
            'A baseline run tests geometry before optimization; it is not a terrain candidate.',
            'Unknown faces are accepted only with the frozen consumer burial proof; final candidate requires its own run.']}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'gates':receipt['gates'],
        'metrics':receipt['metrics'],'elapsed_s':report['elapsed_s']},allow_nan=False),flush=True)
    if not ok: raise SystemExit(2)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--candidate',type=Path)
    p.add_argument('--lower',type=Path)
    p.add_argument('--prepared',type=Path)
    p.add_argument('--prepared-sha256')
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args(); run(a.candidate,a.lower,a.output,a.prepared,a.prepared_sha256)
