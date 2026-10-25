#!/usr/bin/env python
"""EV92 interpolation verifier; delegates unchanged gates to frozen EV91 consumer."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import traceback
import numpy as np

Q=Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010')
HERE=Q/'ev92-damped/consumer'
EV92=Q/'ev92-damped'
PLAN=EV92/'plan.md'
AUTHOR_SOURCE=EV92/'author_ev92.py'
PREPARED=EV92/'prepared.json'
CANDIDATE=EV92/'candidate-terrain.npz'
RECEIPT=EV92/'authoring.json'
BASE=Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')
DIRECTION=Q/'ev91-descent/candidate-terrain.npz'
PARENT_PREP=Q/'ev91-descent/prepared.json'
PARENT_RECEIPT=Q/'ev91-descent/authoring.json'
EV91_CONSUMER=Q/'ev91-descent/consumer/verify_ev91.py'
EV91_GATE_REPORT=Q/'ev91-descent/consumer/runs/attempt-02/ev91-review.json'
WET_DIAGNOSTIC=HERE/'runs/ev92-eligible-wet-support-diagnostic.json'
FIXTURE=HERE/'test_ev92_consumer.py'

PINS={
    str(BASE):'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
    str(DIRECTION):'865901ab24aa3736da57847f9112d3c73181085213f89b48ef2e3e7a9f6ee702',
    str(PARENT_PREP):'127b906c1d2a5d2aa09172ed47dac16cd489aae6a2955428a96166a325605877',
    str(PARENT_RECEIPT):'12be9f321eef9ce586e2c6fe43cce3a55cfed83cc9664ea9f14b8747979d5339',
    str(PLAN):'242010094113e888203ca9a995b050887ea7190da9bfe4a3bd2d82e3946f1a43',
    str(AUTHOR_SOURCE):'818376c2fca9123473b862ece174f4277ffebf3568eb8875863e354e7e2fe4fd',
    str(PREPARED):'a2e9f18b1e77db5d3ce90cb4d928464c775167f2e1c0ff99c2776d1cca0e802d',
    str(EV91_CONSUMER):'5e726b93642f5db531193a8f1d85afabd139c7b9ac3afca4479df793afd53668',
    str(EV91_GATE_REPORT):'594b1985cd8b75c5e3b17c3ea5262a162c4e23ea50474051285713ef132df061',
}
EXPECTED_ALPHA=0.6769237551186755
EXPECTED_GATE_COUNT=27
EXPECTED_GATE_KEYS_SHA='8b5fe00ddb0fbb045bfb1c9981aa95cb5b204574683fbb8bc792ff4b15d9ca2e'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()


def canonical_sha(value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def load_npz(path):
    with np.load(path,allow_pickle=False) as z:return {k:z[k] for k in z.files}


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:raise ImportError(f'cannot load module: {path}')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def _stencil_support(kind,r,c):
    if kind=='xx':return ((r,c,1),(r,c+1,-2),(r,c+2,1))
    if kind=='zz':return ((r,c,1),(r+1,c,-2),(r+2,c,1))
    if kind=='xz':return ((r,c,Fraction(-1,4)),(r,c+2,Fraction(1,4)),
                          (r+2,c,Fraction(1,4)),(r+2,c+2,Fraction(-1,4)))
    raise ValueError(f'unknown EV91 stencil kind: {kind}')


def derive_scalar_rule(base_heights,direction_heights,stencils,focus=(840,370)):
    """Independent exact rational moments + plan-prescribed stable energy root."""
    b=np.asarray(base_heights);h=np.asarray(direction_heights)
    if b.dtype!=np.float32 or h.dtype!=np.float32 or b.shape!=(2048,2048) or h.shape!=b.shape:
        raise ValueError('B and H91 must be float32 2048x2048 arrays')
    moments=[Fraction(0),Fraction(0),Fraction(0)]
    for row in stencils:
        kind,r,c=str(row[0]),int(row[1]),int(row[2])
        b_s=Fraction(0);h_s=Fraction(0)
        for rr,cc,coefficient in _stencil_support(kind,r,c):
            b_s+=Fraction(float(b[rr,cc]))*coefficient
            h_s+=Fraction(float(h[rr,cc]))*coefficient
        d_s=h_s-b_s;weight=2 if kind=='xz' else 1
        moments[0]+=weight*b_s*b_s
        moments[1]+=2*weight*b_s*d_s
        moments[2]+=weight*d_s*d_s
    k0,k1,k2=map(float,moments)
    if not (k0>0 and k2>0 and k1<0 and sum(moments)<=Fraction(3,4)*moments[0]):
        raise ValueError('EV91 direction misses the planned energy conditions')
    disc=k1*k1-k2*k0
    if not disc>0:raise ValueError('energy polynomial has no positive discriminant')
    energy_lower=(k0/2.0)/(-k1+math.sqrt(disc))
    r,c=map(int,focus);center_b=Fraction(float(b[r,c]));center_d=Fraction(float(h[r,c]))-center_b
    focus_lower={}
    axes={'EW':((r,c-1),(r,c+1)),'NS':((r-1,c),(r+1,c))}
    for label,neighbors in axes.items():
        prominence=center_b-max(Fraction(float(b[p])) for p in neighbors)
        if prominence<=0:raise ValueError(f'focus baseline has no prominence on {label}')
        target=Fraction(3,4)*prominence;roots=[]
        for p in neighbors:
            start=center_b-Fraction(float(b[p]))
            slope=center_d-(Fraction(float(h[p]))-Fraction(float(b[p])))
            if slope<0:
                root=float((target-start)/slope)
                if 0<=root<=1:roots.append(root)
        if not roots:raise ValueError(f'no planned focus lower bound for {label}')
        focus_lower[label]=min(roots)
    lower=max(energy_lower,focus_lower['EW'],focus_lower['NS'],0.0)
    if not 0<lower<1:raise ValueError('empty EV92 materiality interval')
    alpha=(lower+1.0)/2.0
    return {'energy_moments_fraction':[str(x) for x in moments],
        'energy_moments_float64':[float(x) for x in moments],
        'energy_lower':energy_lower,'focus_lower_by_axis':focus_lower,
        'materiality_lower':lower,'alpha':alpha,
        'rule':'midpoint of materiality interval [max(energy25,focus25EW,focus25NS),1]; not a global feasibility interval'}


def expected_interpolation(base_heights,direction_heights,alpha):
    b=np.asarray(base_heights,dtype=np.float32);h=np.asarray(direction_heights,dtype=np.float32)
    if b.shape!=(2048,2048) or h.shape!=b.shape:raise ValueError('unexpected B/H91 grid shape')
    b64=b.astype(np.float64);d64=h.astype(np.float64)-b64
    return np.asarray(b64+float(alpha)*d64,dtype=np.float32)


def validate_alpha_metadata(prepared,rule,receipt=None):
    if prepared.get('status')!='PREPARED_NO_WRITE':raise AssertionError('EV92 prepared status is not PREPARED_NO_WRITE')
    if prepared.get('scalar_rule')!=rule or float(prepared.get('alpha',float('nan')))!=rule['alpha']:
        raise AssertionError('prepared alpha/scalar rule differs from independent derivation')
    if rule['alpha']!=EXPECTED_ALPHA:raise AssertionError(f'prescribed stable alpha changed: {rule["alpha"]!r}')
    solver=prepared.get('solver',{})
    if solver.get('method')!='analytic_segment_interpolation' or solver.get('calls')!=0:
        raise AssertionError('EV92 prepared metadata claims a solver call or wrong method')
    if receipt is not None:
        if receipt.get('scalar_rule')!=rule or receipt.get('alpha')!=rule['alpha']:
            raise AssertionError('receipt alpha/scalar rule differs from independent derivation')
        s=receipt.get('solver',{})
        if s.get('method')!='analytic_segment_interpolation' or s.get('calls')!=0:
            raise AssertionError('EV92 receipt must report analytic interpolation and calls=0')
    return rule['alpha']


def validate_prepared(prepared, parent_prepared):
    for key in ('variables_rc','bounds_float32_inward','stencils','matrix_shape','guard_rc',
                'solver_bounds_float32','remaining_free_variables','witnesses',
                'baseline_strict_minima_exempt','descent_centers','descent_matrix_shape',
                'descent_matrix_sha256_f64','descent_rhs_sha256_f64'):
        if prepared.get(key)!=parent_prepared.get(key):
            raise AssertionError(f'EV92 altered inherited EV91 domain/guard/D8 field {key}')
    if len(prepared['variables_rc'])!=85 or len(prepared['stencils'])!=350:
        raise AssertionError('EV92 domain/stencil population changed')
    if len(prepared['guard_rc'])!=43 or prepared.get('remaining_free_variables')!=42:
        raise AssertionError('EV92 collar guard/free-variable population changed')
    if prepared.get('matrix_shape')!=[435,85] or prepared.get('descent_matrix_shape')!=[90,85]:
        raise AssertionError('EV92 inherited matrix populations changed')
    if prepared.get('baseline_sha256')!=PINS[str(BASE)] or prepared.get('direction_sha256')!=PINS[str(DIRECTION)]:
        raise AssertionError('EV92 B/direction SHA mismatch')
    if prepared.get('parent_prepared_sha256')!=PINS[str(PARENT_PREP)] or prepared.get('parent_receipt_sha256')!=PINS[str(PARENT_RECEIPT)]:
        raise AssertionError('EV92 parent prepared/receipt SHA mismatch')
    if prepared.get('plan_sha256')!=PINS[str(PLAN)] or prepared.get('author_source_sha256')!=PINS[str(AUTHOR_SOURCE)]:
        raise AssertionError('EV92 plan/author source metadata mismatch')
    if prepared.get('physical_preflight_plan_sha256')!=parent_prepared.get('physical_preflight_plan_sha256'):
        raise AssertionError('EV92 physical preflight identity changed')
    for path,want in prepared.get('source_pins',{}).items():
        if sha(path)!=want:raise AssertionError(f'prepared source pin mismatch: {path}')
    pins=prepared.get('source_pins',{})
    # The prepared authoring manifest cannot self-pin; the standalone EV91
    # consumer/report are frozen by this wrapper and are not author inputs.
    prepared_source_pins={path:want for path,want in PINS.items()
        if path not in (str(PREPARED),str(EV91_CONSUMER),str(EV91_GATE_REPORT))}
    for path,want in prepared_source_pins.items():
        if pins.get(path)!=want:raise AssertionError(f'prepared source-pins omit or change {path}')
    return True


def validate_receipt_metadata(receipt,prepared,rule,candidate_path,candidate_sha,changed_vertices):
    expected={
        'status':'AUTHORED_PENDING_INDEPENDENT_CONSUMER',
        'candidate_path':str(Path(candidate_path).resolve()),
        'candidate_sha256':candidate_sha,
        'plan_sha256':PINS[str(PLAN)],
        'author_source_sha256':PINS[str(AUTHOR_SOURCE)],
        'approved_prepared_sha256':PINS[str(PREPARED)],
        'baseline_sha256':PINS[str(BASE)],
        'direction_sha256':PINS[str(DIRECTION)],
        'parent_prepared_sha256':PINS[str(PARENT_PREP)],
        'parent_receipt_sha256':PINS[str(PARENT_RECEIPT)],
        'changed_vertices':int(changed_vertices),
    }
    for key,want in expected.items():
        got=receipt.get(key)
        if key=='candidate_path' and got is not None:got=str(Path(got).resolve())
        if got!=want:raise AssertionError(f'EV92 receipt field {key} mismatch: {got!r} != {want!r}')
    if receipt.get('source_pins')!=prepared.get('source_pins'):
        raise AssertionError('EV92 receipt source pins differ from prepared source set')
    validate_alpha_metadata(prepared,rule,receipt)
    return True


def validate_candidate_arrays(base,direction,candidate,alpha):
    if set(base)!=set(direction) or set(base)!=set(candidate):
        raise AssertionError('B/H91/H92 NPZ key sets differ')
    b=np.asarray(base['heights']);d=np.asarray(direction['heights']);actual=np.asarray(candidate['heights'])
    if b.dtype!=np.float32 or d.dtype!=np.float32 or actual.dtype!=np.float32 or b.shape!=(2048,2048) or d.shape!=b.shape or actual.shape!=b.shape:
        raise AssertionError('B/H91/H92 heights must be finite float32 2048x2048')
    if not np.isfinite(b).all() or not np.isfinite(d).all() or not np.isfinite(actual).all():
        raise AssertionError('nonfinite interpolation input/output')
    for key in set(base)-{'heights'}:
        if not np.array_equal(direction[key],base[key],equal_nan=True):
            raise AssertionError(f'EV91 direction changed non-height source field {key}')
        if not np.array_equal(candidate[key],base[key],equal_nan=True):
            raise AssertionError(f'EV92 candidate changed non-height source field {key}')
    expected=expected_interpolation(b,d,alpha)
    if not np.array_equal(actual,expected):
        delta=np.argwhere(actual!=expected)
        raise AssertionError(f'candidate differs from exact one-cast interpolation at {len(delta)} vertices')
    changed=int(np.count_nonzero(actual!=b))
    return expected,changed


def validate_final_inputs(prepared,receipt,candidate_path):
    digest=sha(candidate_path)
    if receipt.get('candidate_sha256')!=digest:raise AssertionError('candidate SHA does not match EV92 receipt')
    if Path(receipt.get('candidate_path','')).resolve()!=Path(candidate_path).resolve():
        raise AssertionError('receipt candidate path mismatch')
    base=load_npz(BASE);direction=load_npz(DIRECTION);candidate=load_npz(candidate_path)
    parent_prepared=json.loads(PARENT_PREP.read_text(encoding='utf-8'))
    validate_prepared(prepared,parent_prepared)
    rule=derive_scalar_rule(base['heights'],direction['heights'],prepared['stencils'])
    alpha=validate_alpha_metadata(prepared,rule,receipt)
    expected,changed=validate_candidate_arrays(base,direction,candidate,alpha)
    validate_receipt_metadata(receipt,prepared,rule,candidate_path,digest,changed)
    if receipt.get('changed_vertices')!=changed:raise AssertionError('receipt changed-vertex count mismatch')
    return {'alpha':alpha,'changed_vertices':changed,'candidate_sha256':digest,
        'scalar_rule':rule,'formula':'float32(B_float64 + alpha * (H91_float64 - B_float64)); one final cast',
        'source_hashes':{p:sha(p) for p in PINS}}


def pinned_gate_keys():
    if sha(EV91_GATE_REPORT)!=PINS[str(EV91_GATE_REPORT)]:raise AssertionError('EV91 gate baseline report SHA mismatch')
    report=json.loads(EV91_GATE_REPORT.read_text(encoding='utf-8'))
    keys=sorted(report['gates'])
    if len(keys)!=EXPECTED_GATE_COUNT:raise AssertionError('EV91 gate baseline is not 27 gates')
    digest=canonical_sha(keys)
    if digest!=EXPECTED_GATE_KEYS_SHA:
        raise AssertionError('EV91 gate key baseline changed')
    return keys,digest


@contextmanager
def explicit_ev91_projection(engine,receipt_path,candidate_path,receipt,prepared,rule,changed_vertices):
    """Scoped compatibility projection; restore both old engine bindings in finally."""
    original_validator=engine.verify_authoring_receipt
    original_sidecar=engine.WET_DIAGNOSTIC_PATH
    if not callable(original_validator) or Path(original_sidecar)!=engine.HERE/'runs/ev91-eligible-wet-support-diagnostic.json':
        raise AssertionError('EV91 engine adaptation seam differs from reviewed baseline')
    def projected_validator(actual_receipt_path,actual_candidate_path,pre):
        if Path(actual_receipt_path).resolve()!=Path(receipt_path).resolve() or Path(actual_candidate_path).resolve()!=Path(candidate_path).resolve():
            raise AssertionError('EV91 engine called adapter with unexpected EV92 inputs')
        # Authenticate original H91 provenance with the unchanged EV91 validator.
        parent_record=original_validator(engine.RECEIPT,engine.CANDIDATE,pre)
        projection=dict(parent_record)
        # These are the only three fields consumed downstream as candidate-specific receipt data.
        projection.update({'candidate_path':str(Path(candidate_path).resolve()),
            'candidate_sha256':receipt['candidate_sha256'],'changed_vertices':int(changed_vertices)})
        return projection
    if not callable(original_validator):raise AssertionError('EV91 original receipt verifier is not callable')
    engine.verify_authoring_receipt=projected_validator
    engine.WET_DIAGNOSTIC_PATH=WET_DIAGNOSTIC
    try:
        yield {'adapter':'explicit temporary EV91 receipt projection','projection_fields':['candidate_path','candidate_sha256','changed_vertices'],
            'original_EV91_receipt_authenticated':True,'EV91_gate_function_unchanged':True,
            'wet_support_sidecar_redirected_to_EV92':True,'restored_in_finally':True}
    finally:
        if engine.verify_authoring_receipt is not projected_validator or engine.WET_DIAGNOSTIC_PATH!=WET_DIAGNOSTIC:
            engine.verify_authoring_receipt=original_validator
            engine.WET_DIAGNOSTIC_PATH=original_sidecar
            raise AssertionError('EV91 adapter binding drifted before restoration')
        engine.verify_authoring_receipt=original_validator
        engine.WET_DIAGNOSTIC_PATH=original_sidecar


def evaluate(candidate_path=CANDIDATE,receipt_path=RECEIPT):
    for path,want in PINS.items():
        if sha(path)!=want:raise AssertionError(f'EV92 frozen pin mismatch: {path}')
    prepared=json.loads(PREPARED.read_text(encoding='utf-8'))
    receipt=json.loads(Path(receipt_path).read_text(encoding='utf-8'))
    # Verify parent/provenance and exact interpolation before delegating to expensive full gates.
    base=load_npz(BASE);direction=load_npz(DIRECTION);candidate=load_npz(candidate_path)
    parent_prepared=json.loads(PARENT_PREP.read_text(encoding='utf-8'))
    validate_prepared(prepared,parent_prepared)
    rule=derive_scalar_rule(base['heights'],direction['heights'],prepared['stencils'])
    alpha=validate_alpha_metadata(prepared,rule,receipt)
    _,changed=validate_candidate_arrays(base,direction,candidate,alpha)
    digest=sha(candidate_path)
    validate_receipt_metadata(receipt,prepared,rule,candidate_path,digest,changed)
    extra_inputs={str(Path(__file__).resolve()):sha(Path(__file__).resolve()),str(FIXTURE):sha(FIXTURE),
        str(PLAN):sha(PLAN),str(AUTHOR_SOURCE):sha(AUTHOR_SOURCE),str(PREPARED):sha(PREPARED),
        str(candidate_path):digest,str(receipt_path):sha(receipt_path),str(BASE):sha(BASE),
        str(DIRECTION):sha(DIRECTION),str(PARENT_PREP):sha(PARENT_PREP),str(PARENT_RECEIPT):sha(PARENT_RECEIPT),
        str(EV91_GATE_REPORT):sha(EV91_GATE_REPORT)}
    for path,digest0 in extra_inputs.items():
        if sha(path)!=digest0:raise AssertionError(f'EV92 input changed during interpolation validation: {path}')
    del base,direction,candidate,parent_prepared
    core=load_module('ev91_core_ev92',EV91_CONSUMER)
    original_validator=core.verify_authoring_receipt;original_sidecar=core.WET_DIAGNOSTIC_PATH
    with explicit_ev91_projection(core,receipt_path,candidate_path,receipt,prepared,rule,changed) as adapter_info:
        core_report=core.evaluate(candidate_path,receipt_path)
    if core.verify_authoring_receipt is not original_validator or core.WET_DIAGNOSTIC_PATH!=original_sidecar:
        raise AssertionError('EV91 engine globals were not restored after evaluation')
    expected_keys,key_sha=pinned_gate_keys()
    if sorted(core_report.get('gates',{}))!=expected_keys:
        raise AssertionError('EV91 reused gate key set differs from pinned 27-gate baseline')
    status=core_report.get('status')
    if status=='PASS_EV91_OFFLINE_CONSUMER':out_status='PASS_EV92_OFFLINE_CONSUMER'
    elif status=='FAIL_EV91_OFFLINE_CONSUMER':out_status='FAIL_EV92_OFFLINE_CONSUMER'
    else:out_status='ERROR_EV92_CONSUMER'
    report={**core_report,'status':out_status}
    info=dict(report.get('information',{}))
    info['ev92_interpolation']={'alpha':alpha,'scalar_rule':rule,'candidate_sha256':digest,
        'changed_vertices':changed,'baseline_sha256':PINS[str(BASE)],'direction_sha256':PINS[str(DIRECTION)],
        'parent_prepared_sha256':PINS[str(PARENT_PREP)],'parent_receipt_sha256':PINS[str(PARENT_RECEIPT)],
        'prepared_sha256':PINS[str(PREPARED)],'formula':'float32(B_float64 + alpha * (H91_float64 - B_float64)); one final cast',
        'solver':{'method':'analytic_segment_interpolation','calls':0},
        'adapter':adapter_info,'reused_EV91_gate_count':len(expected_keys),'reused_EV91_gate_keys_sha256':key_sha,
        'claim_limit':'Same frozen EV91 offline gates applied to exact EV92 interpolation; no new global feasibility claim.'}
    report['information']=info
    inputs=dict(report.get('inputs',{}));inputs.update(extra_inputs);report['inputs']=inputs
    for path,digest0 in inputs.items():
        if sha(path)!=digest0:raise AssertionError(f'input changed during EV92 full consumer: {path}')
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--candidate',type=Path,default=CANDIDATE)
    ap.add_argument('--receipt',type=Path,default=RECEIPT)
    ap.add_argument('--output',type=Path,default=HERE/'runs/ev92-review.json')
    args=ap.parse_args();out={'status':'ERROR_EV92_CONSUMER','gates':{},'information':{}}
    try:out=evaluate(args.candidate,args.receipt)
    except Exception as exc:out={'status':'ERROR_EV92_CONSUMER','gates':{},'error':repr(exc),'traceback':traceback.format_exc()}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':out['status'],'false_gates':[k for k,v in out.get('gates',{}).items() if not v],
        'error':out.get('error'),'output':str(args.output)}))
    if out['status']=='ERROR_EV92_CONSUMER':raise SystemExit(2)
    if out['status']!='PASS_EV92_OFFLINE_CONSUMER':raise SystemExit(1)

if __name__=='__main__':main()
