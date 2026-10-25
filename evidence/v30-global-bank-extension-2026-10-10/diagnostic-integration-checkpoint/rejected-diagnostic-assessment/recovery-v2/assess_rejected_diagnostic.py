#!/usr/bin/env python
"""Read-only physical/shape assessment of one rejected lattice diagnostic.
This is never a terrain candidate and never returns an acceptance status.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, sys
from pathlib import Path
import numpy as np
import shapely

if sys.flags.optimize:
    raise RuntimeError('optimized Python is not accepted for evidence runs')

G = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
ROOT = G / 'G/wet-bank-pilot'
PREP_DIR = ROOT / 'prepared-runs/attempt-08'
PREP = PREP_DIR / 'prepared.npz'
PREP_RECEIPT = PREP_DIR / 'preparation.json'
PREFLIGHT_REVIEW = PREP_DIR / 'independent-review.json'
BASE = G / 'global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz'
PREVIOUS_SOLVE = ROOT / 'solve-once/solution.npz'
PREVIOUS_RESULT = ROOT / 'solve-once/solve-result.json'
PREVIOUS_CANDIDATE = ROOT / 'solve-once/unaccepted-candidate-terrain.npz'
HELPER = ROOT / 'postsolve-consumer/diagnostic-polish-consumer-v1/verify_polished_diagnostic.py'
HELPER_TESTS = HELPER.parent / 'test_polished_diagnostic.py'
COVERAGE_MODULE = G / 'consumer-global/verify_layer.py'
COVERAGE_CHECK = ROOT / 'coverage-consumer/check_coverage.py'
DIAG_DIR = ROOT / 'postsolve-consumer/float32-component-conversion-v1/robust-f32-design/candidate-only-milp/d8-sign-fix-v1'
DIAG_PLAN = DIAG_DIR / 'PLAN.md'
DIAG_MODEL = DIAG_DIR / 'candidate_model.py'
DIAG_DRIVER = DIAG_DIR / 'run_candidate_once.py'
DIAG_CONTROL = DIAG_DIR / 'check_baseline_control.py'
DIAG_CONTROL_RECEIPT = DIAG_DIR / 'baseline-control.json'
DIAG_RECEIPT = DIAG_DIR / 'real-run-01/receipt.json'
DIAGNOSTIC = DIAG_DIR / 'real-run-01/rejected-diagnostic.npz'
P_PATH = G / 'build-focal/candidate/plane.npy'
F_PATH = G / 'build-focal/candidate/visible-field.npy'
PBO_WATER = Path(r'P:/Mods/@DayZ_Baltic_EV95_WideBankPreviewV1/Addons/baltic_water_v30.pbo')
PBO_WORLD = PBO_WATER.with_name('narva_trial.pbo')
STAGE = G / 'build-wide-slope/stage.json'
DEPLOY = G / 'build-wide-slope/deploy.json'
EV87 = Path(r'E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py')
EV88 = Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/review-independent/verify_ev88q.py')
CIVIL = G / 'global-operator-prototype/global-civil-ev95/run-01/inventory.json'
INDEX_MANIFEST = G / 'ev93-face-index/runs/20261010T092417Z-63d4cec3/manifest.json'
INDEX_BUILDER = G / 'ev93-face-index/build_face_index.py'
INDEX_RUN = INDEX_MANIFEST.parent
DESIGN = Path(r'E:/DayZ-Baltic-Build/v30-v11/design/water_v3.geojson')

# Static byte identities copied from the pinned previous consumer or real receipt.
PINNED = {
    HELPER: '94867bf0fe27f6297edfff6dba183deb5e9d3383967ba5dab5ee4ad0a57ac8ef',
    HELPER_TESTS: '66ea4c1cd8b491eb83ab425586076215728d44fb9f208d8b7341be55ce0b1e4a',
    COVERAGE_MODULE: '33050881caaf5e75f288d4122222c15eb326bf146c28a4c723760564457b3dc2',
    COVERAGE_CHECK: '1dc1464b86c0b0c7cd83b2fe5003de1149773dad7d3b2d1396209736fc383a77',
    DIAG_PLAN: 'ad1596d1735c938ec7e151f3fc82208b8c2f443e1aa342f21d8c05351e88e3ad',
    DIAG_MODEL: '23186f47d70730d2f617c0635a7f37b68472d5f287b728811372ae7a47a9e244',
    DIAG_DRIVER: '6292685b6a2dcddb69d7fdddb09c30338917ec413afc4626e7283c4485918fbe',
    DIAG_CONTROL: 'feb34c291d545aee37d908d17a9f147cb8a830915a1298aef550265d720250ae',
    DIAG_CONTROL_RECEIPT: '7cf95dd2061efaf6014ed09149388d171c4b6bc021ee2cefa111c2db2206d068',
    DIAG_RECEIPT: 'f540fb0e8672886c8c70a2af7c8d6ae16c3698ce7d0392e97d9ccc2d50e00902',
    DIAGNOSTIC: '2209df7542098403ceda8e27e87c91935a9832527f04663fdf8f5d8ac70149ae',
    PREP: '52409a8d074d15ec068bddc6e9265bc3782e84e9d54582b8a6d7b0a6675a787f',
    PREP_RECEIPT: 'c582f45f0751e8c24db2672405de4b94c136ee16a9c33d5e4c35a8deee2200ed',
    PREFLIGHT_REVIEW: 'c9e9946c0ab77bfb090fe1b4ec297a13c52ca8b41926bde8c0275db0feeffaf4',
    BASE: '40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a',
    PREVIOUS_SOLVE: '1b7a23ebb3c203427f1c77cb8de6becfca750746e47f5494bba6723b0610eab1',
    PREVIOUS_RESULT: '35722fa7b8f3235597ed6f82c5263da6320d2d030b3dbef3558728386c4240ca',
    PREVIOUS_CANDIDATE: '1c2a6b8b1dce5ed83c6360705e16c10225aa528c96ac02adcf868c554c019652',
    P_PATH: '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
    F_PATH: 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
    DESIGN: 'caa333e365c2a4511f839937a9d76a5aa157a0ef925d6ee4b5efcc4ebb38f8a9',
    EV87: '964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
    EV88: '82a988790e6bdfc0289bcb7c32cb0afd1210e07b264d92731aba266bc5980f78',
    CIVIL: 'cdebbbce50644407642e791388e44c40b15499041844607650b885d1bc618856',
    INDEX_MANIFEST: 'c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c',
    INDEX_BUILDER: 'd1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e',
    PBO_WATER: '3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14',
    PBO_WORLD: 'f1a148cab3e7d1d63473f0232a0971d45a9fea04e0fb456f01973235f4644b7d',
    STAGE: 'b04b066d99f9c22a4fffd77c66762d3e9e744dfa2bbf20d8508f076845571dda',
    DEPLOY: 'f5a9c8185812e0b77a804ef9811e0405b5a7969f8ccfc19b85cc29d23cac03ca',
}
WIN = (855, 870, 1179, 1194)
CORE = (857, 868, 1181, 1192)
ANG_TOL_DEG = 1e-4

class Stop(RuntimeError): pass

def sha(path: Path | str) -> str:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
    return h.hexdigest()

def require(ok, message):
    if not bool(ok): raise Stop(message)

def load_json(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def load_module(name, path, expected):
    require(sha(path)==expected, f'module pin mismatch: {path}')
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise ImportError(path)
    mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod)
    require(sha(path)==expected, f'module changed during import: {path}')
    return mod

def hash_readset(mapping, label):
    require(isinstance(mapping,dict) and mapping, f'{label} missing/empty')
    changed=[]
    for p,want in mapping.items():
        actual=sha(Path(p))
        if actual.lower()!=str(want).lower(): changed.append({'path':p,'expected':want,'actual':actual})
    require(not changed, f'{label} drift: {changed[:3]}')
    return len(mapping)

def validate_rejected_envelope(receipt, diagnostic_path, diagnostic_sha):
    validate_rejected_envelope_fields(receipt, diagnostic_path, diagnostic_sha)
    artifact=receipt.get('rejected_diagnostic',{})
    ok=(receipt.get('schema')=='candidate-only-f32-lattice.real-run.v1' and
        receipt.get('status')=='REJECTED_EXACT_POSTGATES' and receipt.get('accepted') is False and
        receipt.get('terrain_written') is False and artifact.get('accepted') is False and
        artifact.get('terrain_written') is False and
        Path(artifact.get('path','')).resolve()==Path(diagnostic_path).resolve() and
        artifact.get('sha256')==diagnostic_sha.lower())
    require(ok,'receipt does not explicitly identify this artifact as rejected and non-terrain')
    require(receipt.get('solver_invoked') is True and receipt.get('solver_status')==0 and
            receipt.get('exact_fraction_rows_pass') is True and
            all(receipt.get('exact_fraction_gates',{}).get(k) is True for k in
                ('bounds','crossings','d8','fixed','shape','signs')),
            'receipt is not the pinned physically-valid rejected diagnostic run')
    gates=receipt.get('direct_executor_gates',{})
    require(gates.get('closure_energy_and_improvement') is False and
            all(v is True for k,v in gates.items() if k!='closure_energy_and_improvement'),
            'expected energy-only rejection is absent or other executor gate already failed')
    read0=receipt.get('source_readset_start'); read1=receipt.get('source_readset_end')
    require(receipt.get('source_readset_stable') is True and isinstance(read0,dict) and isinstance(read1,dict),
            'source readset claim malformed')
    require_readset_subset(read0,read1)
    # The run added source files after initial setup; don't mislabel 12-vs-25 as flat equality.
    n0=hash_readset(receipt.get('input_readset_start'), 'run input_readset_start')
    n1=hash_readset(read1,'run source_readset_end')
    return {'schema':receipt['schema'],'status':receipt['status'],'accepted':False,
            'terrain_written':False,'source_readset_start_count':len(read0),
            'source_readset_end_count':len(read1),'source_readset_added_count':len(set(read1)-set(read0)),
            'input_readset_start_count':n0,'source_readset_end_rehashed_count':n1,
            'readset_semantics':'initial source keys are preserved in the expanded final set; 13 later-read source keys were added, so the maps are not equal'}

def validate_approved_identity(approved, expected):
    links={'approved_plan_sha':'plan','approved_model_sha':'model',
           'approved_driver_sha':'driver','approved_control_sha':'control_receipt'}
    require(set(approved)==set(links), 'approved hash fields differ from the reviewed receipt schema')
    for field,key in links.items():
        require(str(approved.get(field,'')).lower()==str(expected[key]).lower(),
                f'receipt approval link mismatch: {field}')
    return True

def validate_baseline_control(control, expected_model_sha):
    require(control.get('schema')=='candidate-only-milp.real-baseline-matrix-control.v1' and
            control.get('status')=='BASELINE_CONTROL_PASS' and
            control.get('real_solver_invoked') is False and control.get('terrain_written') is False,
            'pinned B positive-control receipt is not a no-solver PASS')
    read0=control.get('inputs',{}).get('source_readset_start')
    read1=control.get('inputs',{}).get('source_readset_end')
    require(control.get('inputs',{}).get('readset_stable') is True and isinstance(read0,dict) and isinstance(read1,dict),
            'baseline-control readset claim malformed')
    require_readset_subset(read0,read1)
    hash_readset(read1,'baseline-control source_readset_end')
    require(read0.get(str(DIAG_MODEL.resolve()))==expected_model_sha,
            'baseline-control receipt does not pin the reviewed candidate model')
    return {'status':control['status'],'real_solver_invoked':False,'source_readset_count':len(read1)}

def validate_identity():
    """Read-only identity gate: validates pins and both receipt links, no geometry."""
    tracked={str(Path(p).resolve()):sha(p) for p in PINNED}
    tracked[str(Path(__file__).resolve())]=sha(Path(__file__))
    for extra in (Path(__file__).with_name('PLAN.md'),Path(__file__).with_name('test_assess_rejected.py')):
        if extra.exists(): tracked[str(extra.resolve())]=sha(extra)
    for p,want in PINNED.items():
        require(tracked[str(Path(p).resolve())].lower()==want.lower(),f'pin mismatch: {p}')
    receipt_sha=tracked[str(DIAG_RECEIPT.resolve())]
    diag_sha=tracked[str(DIAGNOSTIC.resolve())]
    receipt=load_json(DIAG_RECEIPT)
    provenance=validate_rejected_envelope(receipt,DIAGNOSTIC,diag_sha)
    expected={'plan':PINNED[DIAG_PLAN],'model':PINNED[DIAG_MODEL],
              'driver':PINNED[DIAG_DRIVER],'control_receipt':PINNED[DIAG_CONTROL_RECEIPT]}
    validate_approved_identity(receipt.get('approved_hashes',{}),expected)
    control=validate_baseline_control(load_json(DIAG_CONTROL_RECEIPT),expected['model'])
    after={str(Path(p).resolve()):sha(p) for p in PINNED}
    after[str(Path(__file__).resolve())]=sha(Path(__file__))
    for extra in (Path(__file__).with_name('PLAN.md'),Path(__file__).with_name('test_assess_rejected.py')):
        if extra.exists(): after[str(extra.resolve())]=sha(extra)
    require(after==tracked,'identity readset changed during verification')
    require(sha(DIAG_RECEIPT)==receipt_sha and sha(DIAGNOSTIC)==diag_sha,
            'run receipt or diagnostic changed during identity verification')
    return {'status':'READ_ONLY_IDENTITY_PASS','geometry_executed':False,'accepted':False,
            'pins_checked':len(PINNED),'approved_links_checked':len(expected),
            'rejected_run':{'status':receipt['status'],'sha256':receipt_sha,'provenance':provenance},
            'baseline_control':control}

def validate_npz(path, prep, base_h):
    with np.load(path,allow_pickle=False) as z:
        require(set(z.files)=={'context_grid','lattice_m','variables_rc','source_base_context'},
                'rejected diagnostic schema mismatch')
        ctx=z['context_grid'].copy(); lattice=z['lattice_m'].copy()
        vars_rc=z['variables_rc'].copy(); src=z['source_base_context'].copy()
    ctx,changed,coords=validate_diag_arrays(ctx,src,vars_rc,lattice,prep,base_h[WIN[0]:WIN[1],WIN[2]:WIN[3]])
    return ctx,vars_rc,changed,coords,lattice

def validate_diag_arrays(ctx,src,vars_rc,lattice,prep,base_crop):
    expected=np.asarray([(r,c) for r in range(CORE[0],CORE[1]) for c in range(CORE[2],CORE[3])],dtype=np.int32)
    ctx=np.asarray(ctx); src=np.asarray(src); vars_rc=np.asarray(vars_rc); lattice=np.asarray(lattice)
    require(ctx.shape==(15,15) and ctx.dtype==np.float32 and np.isfinite(ctx).all(),'context shape/dtype/finiteness')
    require(src.shape==(15,15) and src.dtype==np.float32 and np.array_equal(src.view(np.uint32),
        np.asarray(prep['base_heights_context'],dtype=np.float32).view(np.uint32)),'source base differs from prepared B')
    require(np.array_equal(src.view(np.uint32),np.asarray(base_crop,dtype=np.float32).view(np.uint32)),'prepared crop differs from EV95 B')
    require(vars_rc.dtype==np.int32 and np.array_equal(vars_rc,expected) and np.array_equal(vars_rc,prep['variables_rc']),
        'variable list is not exact row-major core')
    require(lattice.dtype==np.int64 and lattice.shape==(121,),'lattice shape/dtype')
    core=np.zeros((15,15),bool); local=vars_rc-np.asarray([WIN[0],WIN[2]],dtype=np.int32); core[tuple(local.T)]=True
    require(np.array_equal(ctx.view(np.uint32)[~core],src.view(np.uint32)[~core]),'fixed collar changed')
    changed=ctx.view(np.uint32)!=src.view(np.uint32); coords=np.argwhere(changed)
    require(int(changed.sum())==114 and np.all(core[tuple(coords.T)]),'changed-node count/domain mismatch')
    return ctx,changed,coords

def status_for(other_gates, energy_ok):
    other_ok=all(bool(x) for x in other_gates.values())
    if not energy_ok and not other_ok: return 'DIAGNOSTIC_ASSESSMENT_ENERGY_AND_OTHER_GATES_FAIL'
    if not energy_ok: return 'DIAGNOSTIC_ASSESSMENT_COMPLETE_ENERGY_FAIL'
    if not other_ok: return 'DIAGNOSTIC_ASSESSMENT_OTHER_GATES_FAIL'
    return 'DIAGNOSTIC_ASSESSMENT_NONPROMOTING'

def self_test():
    fake='E:/test/rejected.npz'; sh='a'*64
    good={'schema':'candidate-only-f32-lattice.real-run.v1','status':'REJECTED_EXACT_POSTGATES',
      'accepted':False,'terrain_written':False,'solver_invoked':True,'solver_status':0,
      'exact_fraction_rows_pass':True,'exact_fraction_gates':{k:True for k in ('bounds','crossings','d8','fixed','shape','signs')},
      'direct_executor_gates':{'bounds':True,'closure_energy_and_improvement':False},
      'rejected_diagnostic':{'accepted':False,'terrain_written':False,'path':fake,'sha256':sh}}
    validate_rejected_envelope_fields(good,fake,sh)
    bad=dict(good); bad['accepted']=True
    try: validate_rejected_envelope_fields(bad,fake,sh)
    except ValueError: pass
    else: raise AssertionError('accepted receipt misclassified as rejected')
    bad=dict(good); bad['rejected_diagnostic']=dict(good['rejected_diagnostic'],sha256='b'*64)
    try: validate_rejected_envelope_fields(bad,fake,sh)
    except ValueError: pass
    else: raise AssertionError('wrong diagnostic hash accepted')
    read0={'a':'1','b':'2'}; read1={'a':'1','b':'2','c':'3'}
    require_readset_subset(read0,read1)
    try: require_readset_subset(read0,{'a':'9','b':'2'})
    except ValueError: pass
    else: raise AssertionError('mutated readset accepted')
    gates={'bounds':True,'water':True}
    assert status_for(gates,False)=='DIAGNOSTIC_ASSESSMENT_COMPLETE_ENERGY_FAIL'
    assert status_for({'bounds':True,'water':False},True)=='DIAGNOSTIC_ASSESSMENT_OTHER_GATES_FAIL'
    assert status_for({'bounds':True,'water':False},False)=='DIAGNOSTIC_ASSESSMENT_ENERGY_AND_OTHER_GATES_FAIL'
    return {'rejected_receipt_positive':True,'accepted_receipt_negative':True,
            'hash_mismatch_negative':True,'expanded_readset_positive':True,
            'readset_mutation_negative':True,'energy_fail_nonpromoting':True,
            'other_gate_failure_nonpromoting':True,'combined_energy_and_other_failure':True}

def validate_rejected_envelope_fields(r,path,sh):
    a=r.get('rejected_diagnostic',{})
    if not (r.get('schema')=='candidate-only-f32-lattice.real-run.v1' and r.get('status')=='REJECTED_EXACT_POSTGATES' and
      r.get('accepted') is False and r.get('terrain_written') is False and a.get('accepted') is False and
      a.get('terrain_written') is False and Path(a.get('path','')).resolve()==Path(path).resolve() and a.get('sha256')==sh):
        raise ValueError('not the pinned unaccepted diagnostic')
    if not (r.get('solver_invoked') is True and r.get('solver_status')==0 and
      r.get('exact_fraction_rows_pass') is True and
      all(r.get('exact_fraction_gates',{}).get(k) is True for k in ('bounds','crossings','d8','fixed','shape','signs'))):
        raise ValueError('diagnostic does not bind an exact-fraction-valid solver result')
    gates=r.get('direct_executor_gates',{})
    if not (gates.get('closure_energy_and_improvement') is False and
      all(v is True for k,v in gates.items() if k!='closure_energy_and_improvement')):
        raise ValueError('receipt does not isolate energy as the only direct-executor failure')
    return True

def require_readset_subset(start,end):
    if not (set(start)<=set(end) and all(start[k]==end[k] for k in start)):
        raise ValueError('readset mutation/missing key')

def assess(output: Path):
    identity=validate_identity()
    require(not output.exists(),'refuse to overwrite report')
    start={str(p.resolve()):sha(p) for p in PINNED}
    start[str(Path(__file__).resolve())]=sha(Path(__file__))
    for extra in (Path(__file__).with_name('PLAN.md'),Path(__file__).with_name('test_assess_rejected.py')):
        if extra.exists(): start[str(extra.resolve())]=sha(extra)
    for p,want in PINNED.items(): require(start[str(p.resolve())].lower()==want.lower(),f'pin mismatch: {p}')
    receipt_sha=sha(DIAG_RECEIPT); diag_sha=sha(DIAGNOSTIC)
    require(receipt_sha==PINNED[DIAG_RECEIPT] and diag_sha==PINNED[DIAGNOSTIC],'diagnostic/receipt pin mismatch')
    receipt=load_json(DIAG_RECEIPT)
    provenance=validate_rejected_envelope(receipt,DIAGNOSTIC,diag_sha)
    approved=receipt.get('approved_hashes',{})
    validate_approved_identity(approved,{'plan':PINNED[DIAG_PLAN],'model':PINNED[DIAG_MODEL],
                                         'driver':PINNED[DIAG_DRIVER],
                                         'control_receipt':PINNED[DIAG_CONTROL_RECEIPT]})
    helper=load_module('rejected_diag_helper',HELPER,PINNED[HELPER])
    require(shapely.__version__==helper.EXPECTED_SHAPELY,
            f'Shapely version mismatch: {shapely.__version__} != {helper.EXPECTED_SHAPELY}')
    require(helper.EXPECTED[helper.PREP]==PINNED[PREP] and helper.EXPECTED[helper.BASE]==PINNED[BASE],
            'reused helper source pins differ from this assessment')
    helper_readset={str(Path(p).resolve()):sha(Path(p)) for p in helper.EXPECTED}
    for p,want in helper.EXPECTED.items():
        require(helper_readset[str(Path(p).resolve())].lower()==want.lower(),f'helper dependency pin mismatch: {p}')
    start.update(helper_readset)
    prep_receipt=load_json(PREP_RECEIPT); review=load_json(PREFLIGHT_REVIEW)
    with np.load(PREP,allow_pickle=False) as z: prep={k:z[k] for k in z.files}
    preflight=helper.verify_preflight(prep,prep_receipt,review)
    solve_lineage=helper.verify_previous_solve_lineage(load_json(PREVIOUS_RESULT))
    with np.load(BASE,allow_pickle=False) as z:
        base_h=z['heights'].copy()
    require(base_h.shape==(2048,2048) and base_h.dtype==np.float32 and np.isfinite(base_h).all(),'EV95 baseline malformed')
    ctx,vars_rc,changed_local,changed_local_rc,lattice=validate_npz(DIAGNOSTIC,prep,base_h)
    h_full=base_h.copy(); h_full[WIN[0]:WIN[1],WIN[2]:WIN[3]]=ctx
    changed_full=h_full.view(np.uint32)!=base_h.view(np.uint32)
    changed_rc=np.argwhere(changed_full).astype(np.int32)
    require(len(changed_rc)==114 and np.array_equal(changed_rc,
        np.asarray([(r+WIN[0],c+WIN[2]) for r,c in changed_local_rc],dtype=np.int32)),
        'full-grid in-memory delta differs from diagnostic context')
    core=np.asarray([(r,c) for r in range(CORE[0],CORE[1]) for c in range(CORE[2],CORE[3])],dtype=np.int32)
    local_core=core-np.asarray([WIN[0],WIN[2]],dtype=np.int32)
    for name in ('other_fixed_context','effective_fixed_context','p9_context','road_context'):
        m=np.asarray(prep[name],dtype=bool)
        require(m.shape==(15,15),f'protected mask bad: {name}')
    protected={name:bool(not np.any(changed_local & np.asarray(prep[name],dtype=bool)))
               for name in ('other_fixed_context','effective_fixed_context','p9_context','road_context')}
    core_mask=np.zeros((15,15),dtype=bool); core_mask[tuple(local_core.T)]=True
    fixed_collar=bool(np.array_equal(ctx.view(np.uint32)[~core_mask],
        np.asarray(prep['base_heights_context'],dtype=np.float32).view(np.uint32)[~core_mask]))
    bounds_lo=np.asarray(prep['lo_absolute_float32_inward'],dtype=np.float32)
    bounds_hi=np.asarray(prep['hi_absolute_float32_inward'],dtype=np.float32)
    x=ctx[tuple(local_core.T)]
    bounds=bool(np.all(x>=bounds_lo) and np.all(x<=bounds_hi))
    bedmask=np.asarray([bool(prep['design_interior_context'][r,c] and not prep['shore_boundary_context'][r,c]) for r,c in local_core.tolist()])
    bed=bool(np.all(x[bedmask]>=np.float32(1.0)))
    # Reconstruct local geometry checks independently through pinned, reviewed helper functions.
    ex=load_module('rejected_diag_executor',helper.EXECUTOR,helper.EXPECTED[helper.EXECUTOR])
    real=ex.load_real_inputs()
    pf=helper.direct_pf(ctx,real['cross_specs'],real['sign_specs'],ex)
    d8_ok,d8_min=helper.d8_check(ctx,np.asarray(prep['d8_witnesses_local'],dtype=np.int32))
    gmat=helper.read_csr(prep,'G'); q=(gmat@x.astype(np.float64)+prep['k_G']).reshape(-1,2)
    require(q.shape==(392,2) and np.asarray(prep['radii_G']).shape==(392,), 'face-cone shape/population changed')
    cone_excess=np.linalg.norm(q,axis=1)-np.asarray(prep['radii_G'],dtype=np.float64)
    cones=bool(np.all(cone_excess<=0))
    amat=helper.read_csr(prep,'A'); rhs=np.asarray(prep['rhs_A'],dtype=np.float64)
    x0=np.asarray(prep['x0_absolute'],dtype=np.float64)
    cost=lambda v:0.5*float(np.sum((amat@np.asarray(v,dtype=np.float64)-rhs)**2))
    with np.load(PREVIOUS_SOLVE,allow_pickle=False) as sol:
        raw_ctx=np.asarray(sol['raw_float32_grid'],dtype=np.float32).copy()
    raw_cost=cost(raw_ctx[tuple(local_core.T)])
    candidate_cost=cost(x); baseline_cost=cost(x0)
    allowance=1e-7*max(1.0,raw_cost)
    energy=bool(candidate_cost-raw_cost<=allowance and candidate_cost<baseline_cost)
    m=receipt['direct_executor_metrics']
    require(math.isclose(candidate_cost,float(m['closed_cost']),rel_tol=0.0,abs_tol=1e-9) and
            math.isclose(raw_cost,float(m['raw_cost']),rel_tol=0.0,abs_tol=1e-9) and
            math.isclose(baseline_cost,float(m['baseline_cost']),rel_tol=0.0,abs_tol=1e-9) and
            math.isclose(allowance,float(m['closure_allowance']),rel_tol=0.0,abs_tol=1e-12),
            'independent objective recomputation disagrees with the pinned rejection receipt')
    require(not energy,'the pinned energy FAIL was not independently reproduced; this is not an acceptance path')
    ev87=load_module('rejected_diag_ev87',EV87,PINNED[EV87])
    bctx=np.asarray(prep['base_heights_context'],dtype=np.float64); hctx=ctx.astype(np.float64)
    declared_core=np.zeros((15,15),dtype=bool)
    declared_core[tuple((vars_rc-np.asarray([WIN[0],WIN[2]],dtype=np.int32)).T)]=True
    cell_mask=helper.affected_cells(declared_core)
    changed_cell_mask=helper.affected_cells(changed_local)
    require(int(cell_mask.sum())==144,'the declared 121-node core must have the exact 144 incident cells')
    require(np.all(changed_cell_mask<=cell_mask),'changed-node footprint escaped the declared core cell population')
    slope_rows=[]
    for b,hh in zip(ev87.slopes(bctx),ev87.slopes(hctx)):
        bv=np.asarray(b)[cell_mask]; hv=np.asarray(hh)[cell_mask]
        lim=np.maximum(35.0,bv)+1e-4
        slope_rows.extend(zip(bv.tolist(),hv.tolist(),lim.tolist()))
    slope_ok=all(hh<=lim for _,hh,lim in slope_rows)
    eb=dict(ev87.edge_angles(bctx)); eh=dict(ev87.edge_angles(hctx))
    require(set(eb)=={'diag','vertical','horizontal'} and set(eb)==set(eh), 'hinge family API/population changed')
    hinges={}; p99_ok=True; new30_ok=True
    for kind,vb in eb.items():
        affected=ev87.incident_any(changed_local,kind)
        a=np.asarray(vb)[affected]; z=np.asarray(eh[kind])[affected]
        p0=float(np.percentile(a,99)) if a.size else 0.0; p1=float(np.percentile(z,99)) if z.size else 0.0
        count=int(np.count_nonzero((a<=30.0)&(z>30.0)))
        p99_ok &= p1<=p0; new30_ok &= count==0
        hinges[kind]={'affected_count':int(z.size),'before_p99_deg':p0,'diagnostic_p99_deg':p1,
          'before_max_deg':float(a.max()) if a.size else None,'diagnostic_max_deg':float(z.max()) if z.size else None,'new_over_30deg':count}
    target_i=int(np.argmax(prep['hinge_angle_before_deg']))
    target_kind={0:'diag',1:'vertical',2:'horizontal'}[int(prep['hinge_kind'][target_i])]
    target_rc=tuple(map(int,prep['hinge_rc_local'][target_i]))
    target_before=float(eb[target_kind][target_rc]); target_after=float(eh[target_kind][target_rc])
    focus_drop=target_before-target_after
    focus_ok=focus_drop>=2.0
    channel=np.asarray(prep['design_interior_context'],bool)|np.asarray(prep['shore_boundary_context'],bool)
    minima=helper.local_new_minima(bctx.astype(np.float32),ctx,channel)
    # Indexed ODOL water check is recalculated in memory; no terrain archive is built/written.
    cvmod=load_module('rejected_diag_coverage',COVERAGE_MODULE,PINNED[COVERAGE_MODULE])
    _,_,ev87_loaded,cv,_,_,idxmod=cvmod.load_helpers()
    for p,want in cvmod.PINS.items():
        require(sha(Path(p)).lower()==want.lower(),f'coverage helper dependency pin mismatch: {p}')
        start[str(Path(p).resolve())]=sha(Path(p))
    index=idxmod.FaceRangeIndex(INDEX_RUN)
    for shard in index.manifest['shards']:
        sp=(index.run_dir/shard['path']).resolve(); got=sha(sp)
        require(got==shard['sha256'],f'face-index shard pin mismatch: {sp}')
        start[str(sp)]=got
    face_recheck=helper.compare_face_inventory(index,prep,ev87_loaded)
    topo=helper.exposed_topology(ev87_loaded,prep,bctx,hctx)
    p=np.load(P_PATH,mmap_mode='r',allow_pickle=False); f=np.load(F_PATH,mmap_mode='r',allow_pickle=False)
    local_p9=np.asarray(prep['p9_context'],dtype=bool)
    # Cell-level P9 set is derived from the pinned context; any changed cell in it remains a failure.
    changed_cells=set()
    for r,c in changed_rc.tolist():
        for rr in (r-1,r):
            for cc in (c-1,c):
                if 0<=rr<2047 and 0<=cc<2047: changed_cells.add((rr,cc))
    p9_cells=set()
    for lr in range(14):
        for lc in range(14):
            if local_p9[lr:lr+2,lc:lc+2].any():
                p9_cells.add((lr+WIN[0],lc+WIN[2]))
    p9_untouched=not bool(changed_cells & p9_cells)
    lower=base_h.copy(); lower[tuple(vars_rc.T)]=bounds_lo
    coverage=cvmod.coverage_from_index(ev87_loaded,cv,index,base_h,h_full,lower,{'P':p,'F':f},changed_rc,p9_cells)
    index.reverify()
    ex.source_readset_check(real['source_start'])
    end={str(p.resolve()):sha(p) for p in PINNED}
    # Rehash run lineage once more after all geometry reads.
    prov_end=validate_rejected_envelope(receipt,DIAGNOSTIC,diag_sha)
    require(sha(DIAGNOSTIC)==diag_sha and sha(DIAG_RECEIPT)==receipt_sha,'diagnostic input changed during assessment')
    end.update({str(Path(p).resolve()):sha(Path(p)) for p in helper.EXPECTED})
    end.update({str(Path(p).resolve()):sha(Path(p)) for p in cvmod.PINS})
    end.update({str((index.run_dir/s['path']).resolve()):sha(index.run_dir/s['path']) for s in index.manifest['shards']})
    end[str(Path(__file__).resolve())]=sha(Path(__file__))
    for extra in (Path(__file__).with_name('PLAN.md'),Path(__file__).with_name('test_assess_rejected.py')):
        if extra.exists(): end[str(extra.resolve())]=sha(extra)
    require(start==end,'assessment fixed source readset changed')
    readset_stable=prov_end==provenance
    gates={
      'diagnostic_schema_unaccepted_and_core_only':True,
      'prepared_499_retained_units_and_protections':True,
      'all_121_physical_bounds':bounds,
      'protected_and_civil_context_exact':all(protected.values()) and fixed_collar,
      'channel_bed_floor_ge_1m':bed,
      'direct_PF_signs_and_all_116_crossings':bool(pf['crossing_count']==116 and pf['strict_signs'] and pf['all_116_intervals']),
      'all_150_D8_witnesses':bool(d8_ok),
      'all_392_face_cones':cones,
      'native_slope_contract':slope_ok,
      'affected_hinge_p99_nonworse':bool(p99_ok),
      'no_new_hinge_over_30deg':bool(new30_ok),
      'focus_drop_at_least_2deg':bool(focus_ok),
      'no_new_strict_minimum_outside_channel':bool(minima['no_new_outside_channel_minima']),
      'P9_untouched':bool(p9_untouched),
      'compiled_face_identity_matches_prepared_index':bool(face_recheck['identity_and_geometry_exact']),
      'local_compiled_water_coverage_gates':bool(coverage.get('gates') and all(v is True for v in coverage['gates'].values())),
      'local_compiled_water_topology_unchanged':bool(topo['topology_unchanged']),
      'energy_budget_and_strict_baseline_improvement':False,
      'source_and_run_readsets_rehashed':bool(readset_stable),
    }
    report={'schema':'ev93.rejected-physical-diagnostic-assessment.v1',
      'status':status_for({k:v for k,v in gates.items() if k!='energy_budget_and_strict_baseline_improvement'},energy),
      'accepted':False,'promoted':False,'terrain_written':False,
      'scope':'one explicitly rejected 121-node diagnostic; in-memory height substitution only; no NPZ terrain, build, package, deployment, or runtime',
      'inputs':{'diagnostic':{'path':str(DIAGNOSTIC.resolve()),'sha256':diag_sha},'rejection_receipt':{'path':str(DIAG_RECEIPT.resolve()),'sha256':receipt_sha},
        'prepared_sha256':PINNED[PREP],'base_sha256':PINNED[BASE],'previous_solve_sha256':PINNED[PREVIOUS_SOLVE],
        'source_readset_start_end':provenance,'fixed_readset_start_end':start,'fixed_readset_stable':True},
      'source_solve_lineage':solve_lineage,'identity_only_precheck':identity,
      'preflight':preflight,'provenance':{'receipt':provenance,'exact_fraction_gates':receipt['exact_fraction_gates'],
        'direct_executor_gates':receipt['direct_executor_gates'],'source_readset_start_keys':len(receipt['source_readset_start']),
        'source_readset_end_keys':len(receipt['source_readset_end']),'added_end_keys':sorted(set(receipt['source_readset_end'])-set(receipt['source_readset_start']))},
      'terrain_assessment':{'changed_vertices':int(changed_local.sum()),'candidate_core_count':int(len(vars_rc)),
        'core_incident_cell_count':int(cell_mask.sum()),'changed_incident_cell_count':int(changed_cell_mask.sum()),
        'all_changes_inside_core':True,'fixed_collar_exact':bool(fixed_collar),'metadata':'No terrain archive exists; non-height metadata is inherited in memory from pinned B and was not serialized.'},
      'constraints':{'bounds_ok':bounds,'bounds_min_lower_slack_m':float(np.min(x-bounds_lo)),
        'bounds_min_upper_slack_m':float(np.min(bounds_hi-x)),'D8_ok':bool(d8_ok),'D8_min_slack_m':float(d8_min),
        'cone_ok':cones,'cone_max_excess':float(np.max(cone_excess)),'PF':pf,
        'objective':{'baseline':baseline_cost,'old_raw':raw_cost,'diagnostic':candidate_cost,'closure_allowance':allowance,
          'diagnostic_minus_raw':candidate_cost-raw_cost,'strict_baseline_improvement':candidate_cost<baseline_cost,
          'closure_budget_pass':candidate_cost-raw_cost<=allowance}},
      'shape':{'native_slope_samples':len(slope_rows),'max_slope_deg':max((b for _,b,_ in slope_rows),default=None),
        'hinges':hinges,'focus':{'kind':target_kind,'local_rc':list(target_rc),'before_deg':target_before,'diagnostic_deg':target_after,
          'drop_deg':focus_drop,'required_deg':2.0},'minima':minima},
      'compiled_water':{'gates':coverage.get('gates'),'metrics':coverage.get('metrics'),'unknown_F':coverage.get('unknown_F'),
        'P_unknown_changed_cells':coverage.get('p_unknown_changed_cells'),'face_inventory':face_recheck,'topology':topo,
        'scope':f"{int(cell_mask.sum())} declared-core incident cells; {int(changed_cell_mask.sum())} actually changed-node incident cells; 200 indexed compiled faces are only local and not global water acceptance"},
      'checks':gates,'failed_checks':[k for k,v in gates.items() if not bool(v)],
      'limitations':['Energy remains an explicit FAIL; this report cannot be interpreted as candidate or global acceptance.',
        'Static analytical/indexed geometry only; no visual, dynamic-water, engine, package, or terrain promotion.',
        'Local P-unknown/face results apply only to this 15x15 diagnostic window.']}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8',newline='\n') as f: json.dump(report,f,indent=2,allow_nan=False); f.write('\n')
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--self-test',action='store_true'); ap.add_argument('--identity-only',action='store_true'); ap.add_argument('--output',type=Path)
    a=ap.parse_args()
    if a.self_test: print(json.dumps(self_test(),sort_keys=True)); raise SystemExit(0)
    if a.identity_only: print(json.dumps(validate_identity(),sort_keys=True,allow_nan=False)); raise SystemExit(0)
    if a.output is None: ap.error('real assessment requires a fresh --output path')
    print(json.dumps({'status':assess(a.output)['status'],'accepted':False},allow_nan=False))
