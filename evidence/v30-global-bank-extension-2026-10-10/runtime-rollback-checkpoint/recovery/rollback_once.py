"""One-shot EV95 dry rollback; emits only PENDING_INDEPENDENT_CONSUMER."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import threading
import time

import numpy as np

HERE=Path(__file__).resolve().parent
PROTO=HERE.parent
ROOT=PROTO.parent
BASE=ROOT/'build-wide-slope'/'candidate'/'terrain.npz'
RUN=PROTO/'global-dry-unconstrained-screen'/'run-01'
VECTOR=RUN/'unaccepted-continuous-vector.npz'
SCREEN_RECEIPT=RUN/'receipt.json'
SCREEN_DIR=PROTO/'global-dry-unconstrained-screen'
PREP=PROTO/'global-dry-solve'/'prepared-01'
BOUNDS=PREP/'bounds.npz'
BOUNDS_RECEIPT=PREP/'receipt.json'
BOUNDS_REVIEW=PREP/'independent-review.json'
BOUNDS_PLAN=PROTO/'GLOBAL_DRY_SOLVE_PLAN.md'
BOUNDS_PREPARER=PROTO/'prepare_global_dry_bounds.py'
MASKS=PROTO/'global-sizing-ev95'/'run-05'/'masks.npz'
ROUNDING_AUDIT=PROTO/'global-sizing-ev95'/'audit_rounding_direction.py'
EV79=Path(r'E:\DayZ-Baltic-Build\v30-narva-dry-bank-relief-20261010\candidate')
CP=PROTO/'face-slope-cone-pilot'/'pilot.py'
OPDIR=PROTO/'global-structured-operator'
AO_DIR=PROTO/'global-dry-unconstrained-screen'/'a-only'
EV87=Path(r'E:\DayZ-Baltic-Build\v30-global-strict-bank-relief-20261010\review-independent\verify_ev87.py')

PINS={
    BASE:'40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a',
    VECTOR:'f7412e6f14fc8b5e4fdee4230991927fe912ea87febb242caf3447bee89b8fb1',
    SCREEN_RECEIPT:'f66d7d49cfee0d6bb0844210177e5be7810e1d07970d4a404ecbe9f4c257828d',
    BOUNDS:'b0c4499776148b080049a528807e31a62d5fd11ba90fcaae5a7881124cde81fb',
    BOUNDS_RECEIPT:'9e55afb4b736a3b558d3e631c62fa94c98a0ae2bb7da4e5513850375758869f3',
    BOUNDS_REVIEW:'d454b78bf8721a9f6477001bb1e5ba77ed4716fc1fdd03232a6084cc6612bf85',
    BOUNDS_PLAN:'a3ab6e74ca13f723989c1e55b3c474df01274f616acab471089fd5e636cafe8e',
    BOUNDS_PREPARER:'5052a025a853f42d6dde7fb799ffd3776b3b925d7f23de10cf86d2fb48b987bb',
    MASKS:'8f5959308923263538440d29dd93960c5331bc8f13c88b61590380c17d6cdfff',
    ROUNDING_AUDIT:'4878c338027e6febd9c2f813dc99c5d009d369bc898c370c7153f74635dd7784',
    EV79/'terrain.npz':'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c',
    EV79/'plane.npy':'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
    EV79/'visible-field.npy':'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
    CP:'d743f5006e0aa6606024a3c3291a74cb52b78f76c1aa5c6dfd95cdd26cdc9d2a',
    SCREEN_DIR/'screen.py':'1dd4b4fe3b2c081298639e120e95a0ba278aa23a1d81aae7c80850d688dd6459',
    SCREEN_DIR/'PLAN.md':'266850183f9c17d54c8454a6118a00c994dcb64f49abf82d24525d244885527d',
    SCREEN_DIR/'independent-review.json':'70b2a5cfd499eea904527d7548faa026ec4361ae0406551ee22ec120d1fa1611',
    OPDIR/'structured_operator.py':'d3017e58bbae3b71c891fab6892a5bf8d9386ae8a51a451a94c9b05769ac750a',
    OPDIR/'optimized-normal'/'fused_normal.py':'19a3e3a493f643702e66aaf265c705739535d386412f74659369d7746117ffaa',
    OPDIR/'measure_global_actions.py':'a05a5f47b775567105c3e588e7106b4b365b58d259f018dca4f243f57d2da37b',
    AO_DIR/'a_only_operator.py':'f1e8ddd9258f72004ecf34da1284ec0b0c295cb77e5b963ecaf24cf82ff9401f',
    EV87:'964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
}
MAX_SECONDS=600.0
MAX_PEAK_BYTES=3*1024**3
MIN_FREE_BYTES=6*1024**3
CHUNK_ROWS=128


def sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()


def load_pinned_module(path,name,pins):
    path=Path(path)
    data=path.read_bytes()
    actual=hashlib.sha256(data).hexdigest()
    if pins.get(path)!=actual:raise RuntimeError(f'module pin drift: {path}')
    spec=importlib.util.spec_from_loader(name,loader=None,origin=str(path))
    module=importlib.util.module_from_spec(spec);module.__file__=str(path)
    import sys
    sys.modules[name]=module
    exec(compile(data,str(path),'exec'),module.__dict__)
    return module


class Guard:
    def __init__(self,mem,started):
        self.mem=mem;self.started=started;self.failure=None;self.samples=[]
        self.stop=threading.Event();self.thread=threading.Thread(target=self._watch,daemon=True)
    def _watch(self):
        while not self.stop.wait(.25):
            try:self.check()
            except Exception as exc:self.failure=self.failure or f'{type(exc).__name__}: {exc}'
    def check(self,phase=None,chunk=None):
        snap={'seconds':time.perf_counter()-self.started,
              'peak_working_set_bytes':int(self.mem.process_peak_working_set()),
              'available_physical_bytes':int(self.mem.memory_status()['available_physical_bytes'])}
        if phase is not None:snap.update({'phase':phase,'chunk':chunk})
        self.samples.append(snap)
        if snap['seconds']>MAX_SECONDS:raise TimeoutError('600-second whole-run budget exceeded')
        if snap['peak_working_set_bytes']>MAX_PEAK_BYTES:raise MemoryError('3-GiB process peak exceeded')
        if snap['available_physical_bytes']<MIN_FREE_BYTES:raise MemoryError('6-GiB physical-memory reserve breached')
        if self.failure:raise RuntimeError(self.failure)
        return snap
    def close(self):
        self.stop.set();self.thread.join(timeout=2.)


def readset(paths):return {str(Path(p)):sha256_file(p) for p in paths}


def objective_after_float32_cast(operator, solution):
    """Evaluate the original A objective after the exact float32 cast."""
    raw32=np.asarray(solution,dtype=np.float64).astype(np.float32).astype(np.float64)
    residual=operator.matvec_a(raw32)-operator.rhs_a
    return float(np.dot(residual,residual))


def _safe_write_json(path,value):
    tmp=Path(str(path)+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    os.replace(tmp,path)


def _load_base_and_inputs():
    with np.load(BASE,allow_pickle=False) as z:
        base_arrays={k:z[k].copy() for k in z.files}
    if 'heights' not in base_arrays:raise ValueError('base terrain missing heights')
    base=base_arrays['heights']
    if base.dtype!=np.float32 or base.shape!=(2048,2048):raise ValueError('unexpected EV95 height dtype/shape')
    with np.load(BOUNDS,allow_pickle=False) as z:
        variables=z['variables_rc'].copy();baseline=z['baseline_values'].copy()
        lo=z['lower_float32'].copy();hi=z['upper_float32'].copy();radii=z['face_radii'].copy()
    with np.load(VECTOR,allow_pickle=False) as z:
        vector_nodes=z['variables_rc'].copy();solution=z['solution_float64'].copy()
    if not np.array_equal(variables,vector_nodes):raise ValueError('screen variable order differs from prepared bounds')
    if variables.dtype!=np.int32 or variables.shape!=(2712136,2):raise ValueError('prepared variable domain shape/dtype mismatch')
    if not np.array_equal(base[variables[:,0],variables[:,1]].astype(np.float64),baseline):raise ValueError('prepared baseline does not match EV95 heights')
    if lo.dtype!=np.float32 or hi.dtype!=np.float32 or lo.shape!=baseline.shape or hi.shape!=baseline.shape:raise ValueError('bad inward box arrays')
    if np.any(lo>hi) or np.any(baseline<lo) or np.any(baseline>hi):raise ValueError('EV95 baseline is not inside every inward box')
    if radii.dtype!=np.float64 or radii.shape!=(8380418,):raise ValueError('bad per-triangle radius array')
    return base_arrays,base,variables,baseline,lo,hi,radii,solution


def run(review_sha256):
    started=time.perf_counter()
    source=Path(__file__).resolve();core=HERE/'rollback_core.py';tests=HERE/'test_rollback_core.py'
    wrapper_tests=HERE/'test_rollback_once_fixture.py'
    plan=HERE/'PLAN.md';review=HERE/'independent-review.json';fixture_report=HERE/'fixture-report.json'
    if not __debug__:raise RuntimeError('optimized Python is forbidden')
    if sha256_file(review)!=review_sha256.lower():raise ValueError('independent-review SHA mismatch')
    review_doc=json.loads(review.read_text(encoding='utf-8-sig'))
    required={'status':'PASS_GLOBAL_DRY_ROLLBACK_PREFLIGHT','source_sha256':sha256_file(source),
              'core_sha256':sha256_file(core),'plan_sha256':sha256_file(plan),
              'tests_sha256':sha256_file(tests),'fixture_report_sha256':sha256_file(fixture_report)}
    for key,value in required.items():
        if review_doc.get(key)!=value:raise ValueError(f'unreviewed {key}')
    for p,digest in PINS.items():
        if sha256_file(p)!=digest:raise ValueError(f'input pin drift: {p}')
    screen=json.loads(SCREEN_RECEIPT.read_text(encoding='utf-8-sig'))
    bounds_doc=json.loads(BOUNDS_RECEIPT.read_text(encoding='utf-8-sig'))
    bounds_review=json.loads(BOUNDS_REVIEW.read_text(encoding='utf-8-sig'))
    if screen.get('status')!='COMPLETE_OBJECTIVE_DIAGNOSTIC_UNACCEPTED' or screen.get('vector_sha256')!=PINS[VECTOR]:
        raise ValueError('original screen receipt does not bind the unaccepted vector')
    if Path(screen.get('vector_path','')).resolve()!=VECTOR.resolve():raise ValueError('screen receipt vector path mismatch')
    if screen.get('source_readset_start')!=screen.get('source_readset_end'):
        raise ValueError('original screen receipt records source drift')
    for path,digest in screen.get('source_readset_start',{}).items():
        if PINS.get(Path(path))!=digest:raise ValueError(f'original screen readset pin is not present/current: {path}')
    if bounds_doc.get('status')!='PREPARED_GLOBAL_DRY_BOUNDS_NO_SOLVE' or bounds_doc.get('artifact_sha256')!=PINS[BOUNDS]:
        raise ValueError('prepared bounds receipt mismatch')
    if Path(bounds_doc.get('artifact','')).resolve()!=BOUNDS.resolve():raise ValueError('prepared bounds artifact path mismatch')
    if bounds_doc.get('variables')!=2712136 or bounds_doc.get('faces')!=8380418 or bounds_doc.get('baseline_feasible') is not True:
        raise ValueError('prepared bounds receipt domain/baseline mismatch')
    if bounds_doc.get('readset_start')!=bounds_doc.get('readset_end'):
        raise ValueError('prepared bounds receipt records source drift')
    for path,digest in bounds_doc.get('readset_start',{}).items():
        if PINS.get(Path(path))!=digest:raise ValueError(f'prepared bounds input pin is not present/current: {path}')
    if bounds_review.get('status')!='PASS_PREPARATION_REVIEW_NO_SOLVE':
        raise ValueError('bounds do not have the expected independent preparation review')
    if (Path(bounds_review.get('receipt_path','')).resolve()!=BOUNDS_RECEIPT.resolve() or
        Path(bounds_review.get('bounds_path','')).resolve()!=BOUNDS.resolve()):
        raise ValueError('bounds review receipt/artifact path mismatch')
    if bounds_review.get('bounds_sha256')!=PINS[BOUNDS] or bounds_review.get('receipt_sha256')!=PINS[BOUNDS_RECEIPT]:
        raise ValueError('bounds review does not bind the pinned prepared data')
    if (bounds_review.get('plan_sha256')!=PINS[BOUNDS_PLAN] or
        bounds_review.get('preparer_sha256')!=PINS[BOUNDS_PREPARER] or
        bounds_review.get('rounding_helper_sha256')!=PINS[ROUNDING_AUDIT] or
        bounds_review.get('operator_reference_sha256')!=PINS[OPDIR/'structured_operator.py'] or
        bounds_review.get('cp_reference_sha256')!=PINS[CP]):
        raise ValueError('bounds independent review does not bind its plan/preparer/operator references')
    fixture_doc=json.loads(fixture_report.read_text(encoding='utf-8-sig'))
    fixture_expected={'status':'PASS_SMALL_MONOTONIC_ROLLBACK_FIXTURES',
        'source_hashes':{'PLAN.md':sha256_file(plan),'rollback_core.py':sha256_file(core),
                         'rollback_once.py':sha256_file(source),'test_rollback_core.py':sha256_file(tests),
                         'test_rollback_once_fixture.py':sha256_file(wrapper_tests)}}
    if fixture_doc.get('status')!=fixture_expected['status'] or fixture_doc.get('source_hashes')!=fixture_expected['source_hashes']:
        raise ValueError('fixture report does not bind the current plan/source/tests')
    oracles=fixture_doc.get('oracles',{})
    if (fixture_doc.get('fixture_count')!=15 or oracles.get('EV87_sha256')!=PINS[EV87] or
        oracles.get('D8_sha256')!=PINS[OPDIR/'structured_operator.py'] or
        fixture_doc.get('global_run_executed') is not False or fixture_doc.get('terrain_written') is not False):
        raise ValueError('fixture report oracle/scope metadata mismatch')
    read_paths=[*PINS,source,core,tests,wrapper_tests,plan,fixture_report,review]
    start_set=readset(read_paths)

    # All review and resource gates pass before creating the unique run folder.
    mem=load_pinned_module(OPDIR/'measure_global_actions.py','rollback_memory',PINS)
    available=int(mem.memory_status()['available_physical_bytes'])
    if available<MIN_FREE_BYTES+MAX_PEAK_BYTES:raise MemoryError('admission requires 6-GiB reserve plus the 3-GiB cap')
    out=HERE/'run-01'
    out.mkdir(exist_ok=False)
    receipt={'schema':'global-dry-rollback.run.v1','status':'STARTED','source_path':str(source),
             'source_sha256':sha256_file(source),'core_path':str(core),'core_sha256':sha256_file(core),
             'plan_sha256':sha256_file(plan),'review_path':str(review),'review_sha256':review_sha256.lower(),
             'source_readset_start':start_set,'terrain_written':False,'candidate_path':None,
             'acceptance_status':'PENDING_INDEPENDENT_CONSUMER'}
    _safe_write_json(out/'started.json',receipt)
    guard=Guard(mem,started);guard.thread.start();history=[];pending_candidate=None;candidate_path_written=None
    try:
        guard.check('load',0)
        base_arrays,base,variables,baseline,lo,hi,radii,solution=_load_base_and_inputs()
        candidate=base.copy()
        clipped=load_pinned_module(core,'rollback_core_run',PINS|{core:receipt['core_sha256']})
        values=clipped.clip_solution_float32(solution,lo,hi)
        candidate[variables[:,0],variables[:,1]]=values

        opmod=load_pinned_module(AO_DIR/'a_only_operator.py','rollback_a_only',PINS)
        op=opmod.build_a_only(base.astype(np.float64),variables)
        guard.check('a_only_build',0)
        base_residual=op.matvec_a(baseline)-op.rhs_a
        cost_baseline=float(np.dot(base_residual,base_residual))
        del base_residual
        if not np.isfinite(cost_baseline):raise ValueError('baseline objective is non-finite')
        expected_baseline=float(screen['objective_baseline'])
        if abs(cost_baseline-expected_baseline)>1e-8*max(1.0,abs(expected_baseline)):
            raise RuntimeError('A-only baseline objective differs from reviewed original screen')
        raw32_cost=objective_after_float32_cast(op,solution)
        del solution,values
        expected_raw32=float(screen['objective_raw32'])
        if abs(raw32_cost-expected_raw32)>1e-8*max(1.0,abs(expected_raw32)):
            raise RuntimeError('A-only raw-float32 objective differs from reviewed original screen')
        centers,witnesses=clipped.d8_witness_arrays_chunked(base,128,lambda p,a,b:guard.check(p,a))
        guard.check('d8_witnesses',0)
        progress={'round':0,'changed_nodes':int(np.count_nonzero(candidate!=base))}
        print(json.dumps({'progress':progress}),flush=True)
        round_index=0
        while True:
            round_index+=1
            chunk_count=0
            def check_chunk(family,r0,r1):
                nonlocal chunk_count
                chunk_count+=1
                snap=guard.check(family,r0)
                if chunk_count==1 or chunk_count%16==0 or r1==2047:
                    item={'round':round_index,'chunk':chunk_count,'family':family,'rows':[int(r0),int(r1)],
                          'changed_nodes':int(np.count_nonzero(candidate!=base)),**snap}
                    history.append(item);print(json.dumps({'progress':item}),flush=True)
            candidate,changed,failures=clipped.rollback_round(base,candidate,centers,witnesses,radii,CHUNK_ROWS,check_chunk)
            guard.check('round_complete',round_index)
            failures.update({'round':round_index,'changed_nodes':int(np.count_nonzero(changed))})
            history.append(failures);print(json.dumps({'round_result':failures}),flush=True)
            if not (failures['d8_bad_rows'] or failures['face_bad_cells'] or failures['new_over30']):break
            if failures.get('changed_after',0)>=failures.get('changed_before',0):raise RuntimeError('nonterminal rollback did not reduce changed nodes')

        changed_values=candidate[variables[:,0],variables[:,1]].astype(np.float64)
        final_residual=op.matvec_a(changed_values)-op.rhs_a
        cost_final=float(np.dot(final_residual,final_residual));del final_residual
        if not np.isfinite(cost_final):raise ValueError('final objective is non-finite')
        changed_count=int(np.count_nonzero(candidate!=base))
        if cost_final>=cost_baseline:
            receipt.update({'status':'NO_OBJECTIVE_IMPROVEMENT','objective_baseline':cost_baseline,
                            'objective_final_float32':cost_final,'changed_vertices':changed_count,
                            'rounds':round_index,'candidate_path':None,
                            'acceptance_status':'NO_OBJECTIVE_IMPROVEMENT'})
        else:
            # Preserve all non-height NPZ arrays exactly as read from EV95.
            temp=out/'candidate-terrain.pending.npz'
            pending_candidate=temp
            with temp.open('wb') as f:np.savez_compressed(f,**{**base_arrays,'heights':candidate})
            guard.check('candidate_write',0)
            with np.load(pending_candidate,allow_pickle=False) as z:
                if not np.array_equal(z['heights'],candidate):raise RuntimeError('candidate height readback mismatch')
                for key,value in base_arrays.items():
                    if key!='heights' and (z[key].dtype!=value.dtype or z[key].shape!=value.shape or z[key].tobytes()!=value.tobytes()):
                        raise RuntimeError(f'non-height terrain array changed: {key}')
            guard.check('before_candidate_publish',0)
            publish_set=readset(read_paths)
            if publish_set!=start_set:raise RuntimeError('source drift before candidate publish')
            guard.check('after_publish_source_check',0)
            candidate_path=out/'candidate-terrain.npz';os.replace(pending_candidate,candidate_path)
            candidate_path_written=candidate_path;pending_candidate=None
            receipt['terrain_written']=True
            receipt.update({'status':'PENDING_INDEPENDENT_CONSUMER','objective_baseline':cost_baseline,
                            'objective_final_float32':cost_final,'objective_improvement':cost_baseline-cost_final,
                            'changed_vertices':changed_count,'rounds':round_index,
                            'candidate_path':str(candidate_path),'candidate_sha256':sha256_file(candidate_path),
                            'acceptance_status':'PENDING_INDEPENDENT_CONSUMER'})
        guard.check('pre_final_readset',0)
    except Exception as exc:
        receipt.update({'status':'TERMINAL_ROLLBACK_FAILURE','error':f'{type(exc).__name__}: {exc}',
                        'candidate_path':None,'acceptance_status':'INCOMPLETE'})
    finally:
        guard.close()
        try:
            guard.check('final_guard',0)
            end_set=readset(read_paths)
            guard.check('post_final_readset',0)
        except Exception as exc:
            end_set=None
            receipt.update({'status':'TERMINAL_FINAL_GUARD_FAILURE','final_error':f'{type(exc).__name__}: {exc}',
                            'candidate_path':None,'acceptance_status':'INCOMPLETE'})
        receipt.update({'elapsed_seconds':time.perf_counter()-started,'source_readset_end':end_set,
                        'source_readset_equal':start_set==end_set,'peak_working_set_bytes':max((s['peak_working_set_bytes'] for s in guard.samples),default=0),
                        'minimum_available_physical_bytes':min((s['available_physical_bytes'] for s in guard.samples),default=None),
                        'watchdog_failure':guard.failure,'progress':history})
        if end_set is not None and start_set!=end_set:
            receipt.update({'status':'TERMINAL_SOURCE_DRIFT','candidate_path':None,'acceptance_status':'INCOMPLETE'})
        if receipt.get('status') not in ('PENDING_INDEPENDENT_CONSUMER','NO_OBJECTIVE_IMPROVEMENT'):
            for owned in (pending_candidate,candidate_path_written):
                if owned is not None and Path(owned).exists():Path(owned).unlink()
            if candidate_path_written is not None:
                receipt['terrain_written']=False
            receipt.pop('candidate_sha256',None)
            receipt['candidate_path']=None
        _safe_write_json(out/'receipt.json',receipt)
    print(json.dumps(receipt,indent=2),flush=True)
    return receipt


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--review-sha256',required=True)
    args=parser.parse_args()
    result=run(args.review_sha256)
    return 0 if result.get('status') in ('PENDING_INDEPENDENT_CONSUMER','NO_OBJECTIVE_IMPROVEMENT') else 1


if __name__=='__main__':raise SystemExit(main())
