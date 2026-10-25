#!/usr/bin/env python
"""Derive one-axis EV93 scalar blends from frozen rejected directions.

This is a no-solver authoring stage. It is fail-closed on the source composite,
source inventory, and an explicit PASS global-consumer report. It never edits
the EV93 layer-1 artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
from fractions import Fraction

import numpy as np

G = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
L = G / 'fairing-layer1'
EXT = G / 'crest-extension'
BASE = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')
PREPARED = L / 'prepared.json'
LEGACY_RECEIPT = L / 'authoring.json'
LEGACY_CANDIDATE = L / 'candidate-terrain.npz'
INVENTORY = EXT / 'reuse-source-inventory.json'
INVENTORY_SHA = '8b8b9a6e525ee3bd8df59bef18784bafdc921e295ec9ebdb7043eefa4317b042'
POLICY = G / 'crest-policy/crest_policy.py'
POLICY_SHA = '32ab6e0111886907315a0360322df0ff958f80bebcd6493254a2f0f144a3829e'
POLICY_PLAN = G / 'next-method-crests.md'
POLICY_PLAN_SHA = 'ba9245134a368870bb4e0090ff36f3c1b91b26b5bc8756d8f0fbf48ddb04ccce'
EXECUTION_PLAN = EXT / 'EXECUTION_PLAN.md'
EXECUTION_PLAN_SHA = '34d1fcb45a1cb4acea4d67d0831637ac510efbe6b3f72ce79e902fbea75d74ab'
SHAPE = Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/next-method-consumer/shape_contract.py')
SHAPE_SHA = '8cd9d0fbea03c05e5ae53a31676d79ec2364be83c055213446f6c8599245d533'
EV92 = Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev92-damped/consumer/verify_ev92.py')
EV92_SHA = '87b5ee5ee95318f1a8026c4a7459aa06d27c9b69db80f34ad25149293d5fc1df'
CONSUMER = G / 'consumer-global/verify_layer.py'
CONSUMER_SHA = '33050881caaf5e75f288d4122222c15eb326bf146c28a4c723760564457b3dc2'
TARGET_REASON = 'final gate scalar interpolation rule unavailable: baseline focus is not prominent on both axes'
EXPECTED_TARGET_COUNT = 228
MAX_SECONDS = 600.0
START = None


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def progress(log_path, phase, event, **data):
    row={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
         'elapsed_s':round(time.perf_counter()-START,3), 'phase':phase,'event':event,**data}
    line=json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False)
    print(line,flush=True)
    if log_path:
        with Path(log_path).open('a',encoding='utf-8',newline='\n') as f:
            f.write(line+'\n');f.flush();os.fsync(f.fileno())


def load_module(name, path, expected_sha):
    got = sha(path)
    if got != expected_sha:
        raise AssertionError(f'frozen source changed: {path}: {got} != {expected_sha}')
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot load {path}')
    mod = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_policy():
    return load_module('ev93_crest_policy_author', POLICY, POLICY_SHA)


def load_consumer():
    return load_module('ev93_frozen_layer_consumer_author', CONSUMER, CONSUMER_SHA)


def exact_energy_moments(base, nodes, direction, stencils):
    """Exact EV92 q0/q1/q2 over source stencils, using sparse H lookup."""
    b = np.asarray(base, dtype=np.float32)
    node_map = {tuple(map(int, rc)): np.float32(v) for rc, v in zip(nodes.tolist(), direction.tolist())}
    q = [Fraction(0), Fraction(0), Fraction(0)]
    for kind, r, c in stencils:
        if kind == 'xx':
            support = ((r,c,1),(r,c+1,-2),(r,c+2,1))
        elif kind == 'zz':
            support = ((r,c,1),(r+1,c,-2),(r+2,c,1))
        elif kind == 'xz':
            support = ((r,c,Fraction(-1,4)),(r,c+2,Fraction(1,4)),
                       (r+2,c,Fraction(1,4)),(r+2,c+2,Fraction(-1,4)))
        else:
            raise AssertionError(f'unknown frozen stencil kind {kind!r}')
        bv = sum((Fraction(float(b[rr,cc])) * co for rr,cc,co in support), Fraction(0))
        hv = sum((Fraction(float(node_map.get((rr,cc), b[rr,cc]))) * co
                  for rr,cc,co in support), Fraction(0))
        dv = hv - bv
        weight = 2 if kind == 'xz' else 1
        q[0] += weight * bv * bv
        q[1] += 2 * weight * bv * dv
        q[2] += weight * dv * dv
    return q


def interpolate_cardinals(base, card_rc, node_map, alpha):
    """Apply the scalar blend at each cardinal independently; fixed cells stay at their own B value."""
    out=[]
    for rc in card_rc:
        b=np.float32(base[rc])
        if rc in node_map:
            h=np.float32(node_map[rc])
            out.append(np.float32(float(b)+float(alpha)*(float(h)-float(b))))
        else:
            out.append(b)
    return np.asarray(out,dtype=np.float32)


def gate_global_pass(report_path: Path, report_sha: str, inventory):
    if sha(report_path) != report_sha.lower():
        raise AssertionError('explicit global PASS report SHA mismatch')
    report = load_json(report_path)
    if report.get('status') != 'PASS_INCREMENTAL_NONREGRESSION':
        raise AssertionError('global consumer report is not PASS_INCREMENTAL_NONREGRESSION')
    if not isinstance(report.get('gates'),dict) or not report['gates'] or not all(report['gates'].values()):
        raise AssertionError('global PASS report has missing or false acceptance gates')
    info = report.get('information', {})
    if info.get('candidate_sha256') != inventory['source_composite']['sha256']:
        raise AssertionError('global PASS report is not for the exact frozen legacy source composite')
    return report


def source_inventory_check():
    if sha(INVENTORY) != INVENTORY_SHA:
        raise AssertionError('reusable-source inventory changed')
    inv = load_json(INVENTORY)
    if inv.get('status') != 'REUSE_SOURCE_INVENTORY_READY' or len(inv.get('reusable_directions', [])) != EXPECTED_TARGET_COUNT:
        raise AssertionError('reusable-source inventory is incomplete')
    for p, wanted in inv.get('source_pins', {}).items():
        if sha(p) != wanted:
            raise AssertionError(f'inventory source pin mismatch: {p}')
    if sha(EXECUTION_PLAN) != EXECUTION_PLAN_SHA:
        raise AssertionError('execution plan changed from reviewed pin')
    for path, wanted in ((BASE, inv['source_pins'][str(BASE)]),
                         (LEGACY_CANDIDATE, inv['source_composite']['sha256']),
                         (PREPARED, inv['source_pins'][str(PREPARED)]),
                         (LEGACY_RECEIPT, inv['source_pins'][str(LEGACY_RECEIPT)])):
        if sha(path) != wanted:
            raise AssertionError(f'core input pin mismatch: {path}')
    return inv


def validate_source_row(validator, inv_row, prepared_row, base):
    qid = int(inv_row['queue_id'])
    if (qid != int(prepared_row['queue_id']) or int(inv_row['seed_id']) != int(prepared_row['seed_id'])
            or list(map(int, inv_row['center_rc'])) != list(map(int, prepared_row['center_rc']))):
        raise AssertionError(f'prepared identity mismatch q{qid}')
    if prepared_row.get('prepared_sha256') not in (None, sha(PREPARED)):
        raise AssertionError(f'prepared source identity mismatch q{qid}')
    result_path = Path(inv_row['result_path'])
    if sha(result_path) != inv_row['result_sha256']:
        raise AssertionError(f'rejected result changed q{qid}')
    result = load_json(result_path)
    if (result.get('queue_id') != qid or result.get('seed_id') != int(inv_row['seed_id'])
            or result.get('center_rc') != inv_row['center_rc'] or result.get('state') != 'rejected'
            or result.get('reason') != TARGET_REASON or result.get('solve_calls') != 1):
        raise AssertionError(f'not the exact one-solve source rejection q{qid}')
    if result.get('preflight_state') != inv_row['preflight_state']:
        raise AssertionError(f'preflight state changed q{qid}')
    marker = Path(inv_row['attempt_marker_path'])
    if sha(marker) != inv_row['attempt_marker_sha256']:
        raise AssertionError(f'start marker changed q{qid}')
    marker_json = load_json(marker)
    if marker_json.get('queue_id') != qid:
        raise AssertionError(f'start marker identity mismatch q{qid}')
    nodes, stencils, direction = validator.validate_attempt_artifact(qid, result, base)
    if (len(nodes) != inv_row['variables_count'] or len(stencils) != inv_row['stencil_count']
            or hashlib.sha256(np.asarray(direction, dtype='<f4').tobytes()).hexdigest()
               != inv_row['direction_float32_le_sha256']):
        raise AssertionError(f'reusable direction summary changed q{qid}')
    return result, np.asarray(nodes, dtype=np.int32), stencils, np.asarray(direction, dtype=np.float32)


def derive_one(inv_row, result, nodes, stencils, direction, base, prepared_sha,
               policy, policy_module_sha, shape, details):
    qid = int(inv_row['queue_id'])
    focus = tuple(map(int, inv_row['center_rc']))
    card_rc = (focus, (focus[0],focus[1]-1),(focus[0],focus[1]+1),
               (focus[0]-1,focus[1]),(focus[0]+1,focus[1]))
    node_map = {tuple(map(int, rc)): np.float32(v) for rc,v in zip(nodes.tolist(), direction.tolist())}
    bcard = np.asarray([base[rc] for rc in card_rc], dtype=np.float32)
    hcard = np.asarray([node_map.get(rc, base[rc]) for rc in card_rc], dtype=np.float32)
    if bcard.tolist() != inv_row['base_cardinals_float32'] or hcard.tolist() != inv_row['direction_cardinals_float32']:
        raise AssertionError(f'inventory cardinal values differ from source artifact q{qid}')
    active = {
        'EW': float(bcard[0]) > max(float(bcard[1]),float(bcard[2])),
        'NS': float(bcard[0]) > max(float(bcard[3]),float(bcard[4])),
    }
    if active != inv_row['active_axes'] or sum(active.values()) != 1:
        raise AssertionError(f'target is not exactly a one-active-axis source q{qid}')
    moments = exact_energy_moments(base,nodes,direction,stencils)
    alpha_energy = policy.energy_lower_from_moments(moments)
    provenance = policy.Provenance(
        queue_id=qid, center_rc=focus,
        baseline_sha256=sha(BASE), prepared_sha256=prepared_sha,
        result_sha256=inv_row['result_sha256'], solution_sha256=inv_row['solution_sha256'],
        policy_plan_sha256=policy.EXPECTED_PINS['policy_plan_sha256'],
        ev92_sha256=policy.EXPECTED_PINS['ev92_sha256'],
        shape_contract_sha256=policy.EXPECTED_PINS['shape_contract_sha256'],
        policy_module_sha256=policy_module_sha,
        source_rejection_reason=inv_row['reason'])
    rule = policy.derive_scalar_rule_from_cardinals(
        bcard,hcard,alpha_energy=alpha_energy,provenance=provenance,legacy_rule=None)
    alpha = float(rule['alpha_midpoint'])
    bnodes = np.asarray(base[tuple(nodes.T)], dtype=np.float32)
    final = np.asarray(bnodes.astype(np.float64) + alpha *
                       (direction.astype(np.float64)-bnodes.astype(np.float64)), dtype=np.float32)
    after_card = interpolate_cardinals(base,card_rc,node_map,alpha)
    focus_report = policy.evaluate_focus_after_cardinals(bcard,after_card)
    if not focus_report['pass']:
        raise AssertionError(f'policy-derived post-cast focus gate failed q{qid}')
    detail = details[qid]
    r0,r1,c0,c1 = map(int,detail['preflight']['window'])
    base_crop = base[r0-1:r1+1,c0-1:c1+1].copy()
    crop = base_crop.copy()
    for rc,value in zip(nodes.tolist(),final.tolist()):
        crop[int(rc[0])-(r0-1),int(rc[1])-(c0-1)] = value
    shape_report = shape.evaluate_shape(base_crop,crop,(1,18,1,18),
                      (focus[0]-(r0-1),focus[1]-(c0-1)))
    shape_new = policy.replace_focus_gate(shape_report,focus_report)
    return {
        'schema':'ev93.crest-extension.target.v1','queue_id':qid,
        'seed_id':int(inv_row['seed_id']),'center_rc':list(focus),
        'state':'derived_pending_composite_consumer', 'solve_calls':0,
        'source_state':'rejected','source_reason':TARGET_REASON,
        'source_result_path':inv_row['result_path'],'source_result_sha256':inv_row['result_sha256'],
        'source_solution_path':inv_row['solution_path'],'source_solution_sha256':inv_row['solution_sha256'],
        'source_marker_path':inv_row['attempt_marker_path'],'source_marker_sha256':inv_row['attempt_marker_sha256'],
        'direction_sha256':inv_row['direction_float32_le_sha256'],
        'stencil_set_sha256':inv_row['stencil_set_sha256'],
        'alpha':alpha,'alpha_energy':alpha_energy,'energy_moments_fraction':[str(x) for x in moments],
        'policy_id':policy.POLICY_ID,'policy_mode':rule['policy_mode'],'scalar_rule':rule,
        'focus_after_cast':focus_report,
        'local_shape_nonfocus_gates':{k:bool(v) for k,v in shape_new['gates'].items()},
        'local_shape_pass':all(shape_new['gates'].values()),
        'variables_rc':nodes.tolist(),'B_values_float32':bnodes.tolist(),
        'direction_float32':direction.tolist(),'final_float32':final.tolist(),
        'new_solver_calls':0,
    }


def write_json_atomic(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    raw=(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode('utf-8')
    with tmp.open('wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
    return hashlib.sha256(raw).hexdigest()


def append_event(path, event):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    line=json.dumps(event,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n'
    with path.open('a',encoding='utf-8',newline='\n') as f:
        f.write(line);f.flush();os.fsync(f.fileno())


def read_terminal_rows(output_dir):
    ledger=Path(output_dir)/'ledger.jsonl'
    terminal={};started=set();final=None
    if not ledger.exists():return terminal,started,final
    for line_no,line in enumerate(ledger.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip():continue
        event=json.loads(line);kind=event.get('event');qid=int(event.get('queue_id',-1))
        if kind=='started':
            if qid<0 or qid in terminal:raise AssertionError(f'invalid/late started ledger row {line_no}')
            started.add(qid)
        elif kind=='target':
            if qid<0 or qid in terminal:raise AssertionError(f'duplicate terminal ledger row {line_no}')
            terminal[qid]=event
        elif kind=='final':
            if final is not None:raise AssertionError('duplicate final ledger event')
            final=event
        else:raise AssertionError(f'unknown ledger event {kind!r} at {line_no}')
    for qid,event in terminal.items():
        target=Path(event['path'])
        if not target.is_file() or sha(target)!=event.get('sha256'):
            raise AssertionError(f'terminal target file missing/hash mismatch q{qid}')
        row=load_json(target)
        if int(row.get('queue_id',-1))!=qid or row.get('state')!=event.get('state'):
            raise AssertionError(f'terminal target content does not match ledger q{qid}')
    if final is not None and (len(terminal)!=EXPECTED_TARGET_COUNT or final.get('processed_count')!=EXPECTED_TARGET_COUNT
            or final.get('remaining_count')!=0):
        raise AssertionError('final ledger event exists before all target rows are terminal')
    return terminal,started,final


def build_receipt(output_dir, inv, report_path, report_sha, terminal_rows,
                  target_order, status, error=None, candidate_sha=None):
    out=Path(output_dir).resolve()
    ordered=[terminal_rows[q] for q in target_order if q in terminal_rows]
    target_refs=[{'queue_id':int(x['queue_id']),'state':x['state'],
                  'path':str(Path(x['path']).resolve()),'sha256':x['sha256']} for x in ordered]
    target_jsonl=out/'targets.jsonl'
    raw=''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in target_refs).encode('utf-8')
    tmp=target_jsonl.with_name('targets.jsonl.tmp')
    with tmp.open('wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    os.replace(tmp,target_jsonl)
    states={s:sum(x['state']==s for x in target_refs) for s in sorted({x['state'] for x in target_refs})}
    receipt={
        'schema':'ev93.crest-extension.receipt.v2','status':status,
        'execution_plan_path':str(EXECUTION_PLAN.resolve()),'execution_plan_sha256':EXECUTION_PLAN_SHA,
        'author_source_path':str(Path(__file__).resolve()),'author_source_sha256':sha(__file__),
        'source_inventory_path':str(INVENTORY.resolve()),'source_inventory_sha256':INVENTORY_SHA,
        'source_base_path':str(BASE.resolve()),'source_base_sha256':sha(BASE),
        'legacy_composite_path':str(LEGACY_CANDIDATE.resolve()),'legacy_composite_sha256':sha(LEGACY_CANDIDATE),
        'legacy_receipt_sha256':sha(LEGACY_RECEIPT),'prepared_sha256':sha(PREPARED),
        'global_pass_report_path':str(Path(report_path).resolve()),'global_pass_report_sha256':report_sha,
        'policy_path':str(POLICY.resolve()),'policy_sha256':POLICY_SHA,
        'policy_plan_sha256':POLICY_PLAN_SHA,'consumer_source_sha256':CONSUMER_SHA,
        'target_count':EXPECTED_TARGET_COUNT,'processed_count':len(target_refs),
        'remaining_count':EXPECTED_TARGET_COUNT-len(target_refs),'target_states':states,
        'new_solver_calls':0,'derived_alpha_count':sum('alpha' in x for x in ordered),
        'local_shape_rejected_count':sum(x['state']=='rejected_local_shape' for x in ordered),
        'policy_rejected_count':sum(x['state']=='rejected_policy' for x in ordered),
        'target_rows_path':str(target_jsonl),'target_rows_sha256':sha(target_jsonl),
        'ledger_path':str((out/'ledger.jsonl').resolve()),
        'ledger_sha256':sha(out/'ledger.jsonl') if (out/'ledger.jsonl').exists() else None,
        'rows':target_refs,
        'semantics':{'legacy_340_passthrough':'original EV92 composite is the base for this extension; prior deltas are unchanged',
            'reused_228':'one exact source direction per row; one policy alpha or explicit reject; zero solver calls',
            'global_status':'pending independent composed consumer; inherited global defects remain open'},
    }
    if error is not None:receipt['error']=error
    if status=='AUTHORED_PENDING_COMPOSITE_CONSUMER':
        receipt['candidate_path']=str((out/'candidate-terrain.npz').resolve())
        receipt['candidate_sha256']=candidate_sha
        receipt['changed_vertices_total_vs_B']=None
    write_json_atomic(out/'receipt.json',receipt)
    return receipt


def synthetic_fixture(policy, policy_sha, shape):
    # One active EW crest, a real EV92 stencil, exact q moments, then a post-cast check.
    b=np.full((19,19),10,dtype=np.float32);b[9,8]=8;b[9,10]=8
    d=b.copy();d[9,9]=9
    stencil=[('xx',9,8)]
    q=exact_energy_moments(b,np.asarray([[9,9]],dtype=np.int32),np.asarray([9],dtype=np.float32),stencil)
    ae=policy.energy_lower_from_moments(q)
    provenance=policy.Provenance(0,(9,9),sha(BASE),'a'*64,'b'*64,'c'*64,
        policy.EXPECTED_PINS['policy_plan_sha256'],policy.EXPECTED_PINS['ev92_sha256'],
        policy.EXPECTED_PINS['shape_contract_sha256'],policy_sha,TARGET_REASON)
    rule=policy.derive_scalar_rule_from_cardinals(
        np.asarray([10,8,8,10,10],np.float32),np.asarray([9,8,8,10,10],np.float32),
        alpha_energy=ae,provenance=provenance)
    alpha=float(rule['alpha_midpoint'])
    final=(b.astype(np.float64)+alpha*(d.astype(np.float64)-b.astype(np.float64))).astype(np.float32)
    focus=policy.evaluate_focus_after_cardinals(np.asarray([10,8,8,10,10],np.float32),
        np.asarray([final[9,9],final[9,8],final[9,10],final[8,9],final[10,9]],np.float32))
    assert 0<alpha<1 and focus['pass'] and rule['policy_mode']=='one_active_axis_affine_tail'
    # Fixed neighbors must read their own baseline values, not the center.
    fixed_test=np.full((5,5),20,dtype=np.float32);fixed_test[2,2]=10;fixed_test[2,1]=7
    cards=((2,2),(2,1),(2,3),(1,2),(3,2))
    fixed_cards=interpolate_cardinals(fixed_test,cards,{(2,2):np.float32(12)},0.5)
    assert fixed_cards.tolist()==[11.0,7.0,20.0,20.0,20.0]
    # A true flat has no active axis and must be rejected by the production API.
    try:
        flat_prov=policy.Provenance(1,(9,9),sha(BASE),'a'*64,'b'*64,'c'*64,
          policy.EXPECTED_PINS['policy_plan_sha256'],policy.EXPECTED_PINS['ev92_sha256'],
          policy.EXPECTED_PINS['shape_contract_sha256'],policy_sha,TARGET_REASON)
        policy.derive_scalar_rule_from_cardinals(np.ones(5,np.float32),np.zeros(5,np.float32),
            alpha_energy=ae,provenance=flat_prov)
    except ValueError:
        flat_rejected=True
    else:
        raise AssertionError('flat focus fixture unexpectedly produced an alpha')
    with tempfile.TemporaryDirectory(prefix='ev93-author-ledger-fixture-') as td:
        root=Path(td);targets=root/'targets';targets.mkdir()
        (root/'ledger.jsonl').write_text('',encoding='utf-8')
        append_event(root/'ledger.jsonl',{'event':'started','queue_id':7,'seed_id':3})
        terminal_row={'queue_id':7,'seed_id':3,'state':'rejected_policy'}
        target_path=targets/'window-0007.json'
        target_sha=write_json_atomic(target_path,terminal_row)
        append_event(root/'ledger.jsonl',{'event':'target','queue_id':7,'seed_id':3,
            'state':'rejected_policy','path':str(target_path.resolve()),'sha256':target_sha})
        terminal,started,final=read_terminal_rows(root)
        assert set(terminal)=={7} and started=={7} and final is None
    return {'one_active_axis_derived_and_float32_focus_passed':True,'fixed_cardinal_uses_own_baseline':True,
            'zero_active_axes_rejected':flat_rejected,
            'append_only_resume_ledger_roundtrip':True}


def author(report_path: Path, report_sha: str, output_dir: Path, progress_path: Path | None):
    global START
    START=time.perf_counter()
    progress(progress_path,'source-validation','start')
    inv=source_inventory_check()
    gate_global_pass(report_path,report_sha,inv)
    progress(progress_path,'source-validation','complete',pinned_files=len(inv['source_pins']))
    output_dir=output_dir.resolve()
    output_dir.mkdir(parents=True,exist_ok=True)
    run_path=output_dir/'run.json'
    run_identity={'schema':'ev93.crest-extension.run.v1','execution_plan_sha256':EXECUTION_PLAN_SHA,
        'inventory_sha256':INVENTORY_SHA,'global_pass_report_path':str(report_path.resolve()),
        'global_pass_report_sha256':report_sha,'expected_target_count':EXPECTED_TARGET_COUNT,
        'author_source_sha256':sha(__file__),'policy_sha256':POLICY_SHA,
        'consumer_source_sha256':CONSUMER_SHA,'shape_contract_sha256':SHAPE_SHA,
        'ev92_source_sha256':EV92_SHA,'policy_plan_sha256':POLICY_PLAN_SHA,
        'source_pins':inv['source_pins']}
    if run_path.exists():
        if load_json(run_path)!=run_identity:raise AssertionError('resume identity differs from immutable run manifest')
    else:
        if any(output_dir.iterdir()):raise FileExistsError(f'output directory is nonempty without run manifest: {output_dir}')
        write_json_atomic(run_path,run_identity)
    policy=load_policy(); validator=load_consumer()
    ev,ev91,ev87,cv,shape,ev92,index_module=validator.load_helpers()
    with np.load(BASE,allow_pickle=False) as z: base_for_check=np.asarray(z['heights'],np.float32)
    prepared,legacy_receipt,entries,ledger,ledger_path=validator.verify_prepared(
        PREPARED,LEGACY_RECEIPT,base_for_check)
    if sha(CONSUMER)!=CONSUMER_SHA or sha(POLICY)!=POLICY_SHA:
        raise AssertionError('consumer or policy changed during load')
    details=validator.validate_detail_hashes(prepared,entries)
    prepared_by={int(x['queue_id']):x for x in entries}
    base_npz={}
    with np.load(BASE,allow_pickle=False) as z: base_npz={k:z[k] for k in z.files}
    base=np.asarray(base_npz['heights'],dtype=np.float32)
    legacy={}
    with np.load(LEGACY_CANDIDATE,allow_pickle=False) as z: legacy={k:z[k] for k in z.files}
    if set(legacy)!=set(base_npz) or any(not np.array_equal(legacy[k],base_npz[k],equal_nan=True)
                                         for k in base_npz if k!='heights'):
        raise AssertionError('legacy EV93 composite changed non-height baseline arrays')
    candidate=np.asarray(legacy['heights'],dtype=np.float32).copy()
    terminal,started,ledger_final=read_terminal_rows(output_dir)
    source_by_q={int(x['queue_id']):x for x in inv['reusable_directions']}
    if set(terminal)-set(source_by_q) or len(terminal)>EXPECTED_TARGET_COUNT:
        raise AssertionError('resume ledger contains unknown or excess target rows')
    for qid,event in terminal.items():
        if int(event.get('seed_id',-1))!=int(source_by_q[qid]['seed_id']):
            raise AssertionError(f'resume terminal seed mismatch q{qid}')
    rows=[];ownership=set();target_nodes=set();result_hashes={}
    prepared_sha=sha(PREPARED);policy_sha=sha(POLICY)
    progress(progress_path,'source-validation','consumer_inputs_ready',targets=EXPECTED_TARGET_COUNT)
    order=[int(x['queue_id']) for x in inv['reusable_directions']]
    for pos,invrow in enumerate(inv['reusable_directions']):
        qid=int(invrow['queue_id']);entry=prepared_by[qid]
        if qid in terminal:
            event=terminal[qid];row_path=Path(event['path'])
            row=load_json(row_path)
            nodes=np.asarray(row.get('variables_rc',[]),np.int32)
            if len(nodes):
                node_set=set(map(tuple,nodes.tolist()))
                if target_nodes & node_set:raise AssertionError(f'resumed target ownership collision q{qid}')
                target_nodes.update(node_set)
                if row['state']=='derived_pending_composite_consumer':
                    for rc,value in zip(nodes.tolist(),row['final_float32']):
                        n=tuple(map(int,rc))
                        if candidate[n]!=base[n]:raise AssertionError(f'target node is not B before reused composition q{qid}: {n}')
                        if n in ownership:raise AssertionError(f'resumed candidate ownership duplicate {n}')
                        ownership.add(n);candidate[n]=np.float32(value)
            rows.append(row);result_hashes[str(qid)]=invrow['result_sha256']
            continue
        if time.perf_counter()-START>=MAX_SECONDS:
            receipt=build_receipt(output_dir,inv,report_path,report_sha,terminal,order,'INCOMPLETE',
                {'kind':'deadline','budget_seconds':MAX_SECONDS})
            progress(progress_path,'deadline','incomplete',processed=len(terminal),remaining=EXPECTED_TARGET_COUNT-len(terminal))
            return receipt
        # A prior started marker without a terminal result is an interrupted row;
        # it is the only kind of row that may be retried on resume.
        orphan=output_dir/'targets'/f'window-{qid:04d}.json'
        if orphan.exists():
            row=load_json(orphan)
            if (int(row.get('queue_id',-1))!=qid or row.get('seed_id')!=int(invrow['seed_id'])
                    or row.get('source_result_sha256')!=invrow['result_sha256']
                    or row.get('source_solution_sha256')!=invrow['solution_sha256']
                    or row.get('state') not in ('rejected_policy','rejected_local_shape','derived_pending_composite_consumer')):
                raise AssertionError(f'orphan immutable target cannot be safely recovered q{qid}')
            recovered_sha=sha(orphan)
            event={'event':'target','queue_id':qid,'seed_id':int(invrow['seed_id']),
                'state':row['state'],'path':str(orphan.resolve()),'sha256':recovered_sha,
                'elapsed_ms':None,'recovered_orphan':True}
            append_event(output_dir/'ledger.jsonl',event);terminal[qid]=event
            nodes=np.asarray(row.get('variables_rc',[]),np.int32)
            if len(nodes):
                node_set=set(map(tuple,nodes.tolist()))
                if target_nodes & node_set:raise AssertionError(f'recovered target ownership collision q{qid}')
                target_nodes.update(node_set)
                if row['state']=='derived_pending_composite_consumer':
                    for rc,value in zip(nodes.tolist(),row['final_float32']):
                        n=tuple(map(int,rc))
                        if candidate[n]!=base[n]:raise AssertionError(f'recovered target node is not B q{qid}: {n}')
                        if n in ownership:raise AssertionError(f'recovered ownership collision {n}')
                        ownership.add(n);candidate[n]=np.float32(value)
            rows.append(row);result_hashes[str(qid)]=invrow['result_sha256']
            continue
        append_event(output_dir/'ledger.jsonl',{'event':'started','queue_id':qid,
            'seed_id':int(invrow['seed_id']),'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
        row_start=time.perf_counter()
        try:
            result,nodes,stencils,direction=validate_source_row(validator,invrow,entry,base)
        except Exception as exc:
            build_receipt(output_dir,inv,report_path,report_sha,terminal,order,'INCOMPLETE',
                {'kind':'worker_error','queue_id':qid,'error':repr(exc)})
            progress(progress_path,'derive-directions','error',queue_id=qid,error=repr(exc))
            raise
        overlap=target_nodes & set(map(tuple,nodes.tolist()))
        if overlap: raise AssertionError(f'reused windows overlap at {min(overlap)}')
        target_nodes.update(map(tuple,nodes.tolist()))
        try:
            derived=derive_one(invrow,result,nodes,stencils,direction,base,prepared_sha,policy,policy_sha,shape,details)
        except policy.PolicyReject as exc:
            derived={
                'schema':'ev93.crest-extension.target.v1','queue_id':qid,
                'seed_id':int(invrow['seed_id']),'center_rc':list(map(int,invrow['center_rc'])),
                'state':'rejected_policy','solve_calls':0,'source_state':'rejected',
                'source_reason':TARGET_REASON,'policy_rejection_code':exc.code,
                'policy_rejection_message':str(exc),'source_result_path':invrow['result_path'],
                'source_result_sha256':invrow['result_sha256'],'source_solution_path':invrow['solution_path'],
                'source_solution_sha256':invrow['solution_sha256'],'source_marker_path':invrow['attempt_marker_path'],
                'source_marker_sha256':invrow['attempt_marker_sha256'],
                'direction_sha256':invrow['direction_float32_le_sha256'],
                'stencil_set_sha256':invrow['stencil_set_sha256'],'new_solver_calls':0,
            }
        except Exception as exc:
            build_receipt(output_dir,inv,report_path,report_sha,terminal,order,'INCOMPLETE',
                {'kind':'worker_error','queue_id':qid,'error':repr(exc)})
            progress(progress_path,'derive-directions','error',queue_id=qid,error=repr(exc))
            raise
        final=np.asarray(derived.get('final_float32',[]),dtype=np.float32)
        if derived['state']=='rejected_policy':
            pass
        else:
            dnodes=np.asarray(derived['variables_rc'],dtype=np.int32)
            if derived['local_shape_pass']:
                derived['state']='derived_pending_composite_consumer'
            else:
                derived['state']='rejected_local_shape'
        row_path=output_dir/'targets'/f'window-{qid:04d}.json'
        row_sha=write_json_atomic(row_path,derived)
        terminal_event={'event':'target','queue_id':qid,'seed_id':int(invrow['seed_id']),
            'state':derived['state'],'path':str(row_path.resolve()),'sha256':row_sha,
            'elapsed_ms':round((time.perf_counter()-row_start)*1000,3)}
        append_event(output_dir/'ledger.jsonl',terminal_event);terminal[qid]=terminal_event
        if derived['state']=='derived_pending_composite_consumer':
            for rc,value in zip(dnodes.tolist(),final.tolist()):
                n=tuple(map(int,rc))
                if n in ownership:raise AssertionError(f'candidate ownership duplicate {n}')
                if candidate[n]!=base[n]:raise AssertionError(f'reused target overlaps prior composite q{qid}: {n}')
                ownership.add(n);candidate[n]=np.float32(value)
        rows.append(derived);result_hashes[str(qid)]=invrow['result_sha256']
        if (pos+1)%25==0 or pos+1==EXPECTED_TARGET_COUNT:
            progress(progress_path,'derive-directions','progress',processed=len(terminal),total=EXPECTED_TARGET_COUNT,
                     elapsed_row_ms=terminal_event['elapsed_ms'],
                     policy_derived=sum('alpha' in x for x in rows),
                     applied_to_pending_composite=sum(x['state']=='derived_pending_composite_consumer' for x in rows))
        build_receipt(output_dir,inv,report_path,report_sha,terminal,order,'INCOMPLETE',
            {'kind':'running','budget_seconds':MAX_SECONDS})
        if time.perf_counter()-START>=MAX_SECONDS:
            receipt=build_receipt(output_dir,inv,report_path,report_sha,terminal,order,'INCOMPLETE',
                {'kind':'deadline','budget_seconds':MAX_SECONDS})
            progress(progress_path,'deadline','incomplete',processed=len(terminal),remaining=EXPECTED_TARGET_COUNT-len(terminal))
            return receipt
    if len(terminal)!=EXPECTED_TARGET_COUNT:
        raise AssertionError(f'cannot publish candidate: {len(terminal)}/{EXPECTED_TARGET_COUNT} terminal rows')
    rows=[load_json(terminal[q]['path']) for q in order]
    # Rebuild from the frozen legacy composite, then apply only explicitly accepted reused rows.
    with np.load(LEGACY_CANDIDATE,allow_pickle=False) as z:legacy_height=np.asarray(z['heights'],np.float32).copy()
    candidate=legacy_height.copy();ownership=set()
    for row in rows:
        if row['state']!='derived_pending_composite_consumer':continue
        for rc,value in zip(row['variables_rc'],row['final_float32']):
            n=tuple(map(int,rc))
            if n in ownership:raise AssertionError(f'final composition ownership collision {n}')
            if candidate[n]!=base[n]:raise AssertionError(f'final composition target not B before apply {n}')
            ownership.add(n);candidate[n]=np.float32(value)
    changed=np.argwhere(candidate!=base)
    if not any(r['state']=='derived_pending_composite_consumer' for r in rows) or not len(changed):
        terminal_status='NO_CHANGE_NO_POLICY_ACCEPTED'
    else:
        terminal_status='AUTHORED_PENDING_COMPOSITE_CONSUMER'
    out=output_dir.resolve()
    candidate_path=out/'candidate-terrain.npz'
    candidate_npz={k:(candidate if k=='heights' else v) for k,v in legacy.items()}
    if candidate_path.exists():
        candidate_sha=sha(candidate_path)
        with np.load(candidate_path,allow_pickle=False) as prior:
            if set(prior.files)!=set(candidate_npz) or any(not np.array_equal(prior[k],candidate_npz[k],equal_nan=True) for k in candidate_npz):
                raise AssertionError('existing final candidate does not match deterministic completed composition')
    else:
        candidate_tmp=out/'candidate-terrain.npz.tmp'
        with candidate_tmp.open('wb') as f:np.savez(f,**candidate_npz);f.flush();os.fsync(f.fileno())
        candidate_sha=sha(candidate_tmp)
    changed_inputs=[p for p,want in inv['source_pins'].items() if sha(p)!=want]
    if (changed_inputs or sha(INVENTORY)!=INVENTORY_SHA or sha(EXECUTION_PLAN)!=EXECUTION_PLAN_SHA
            or sha(POLICY)!=POLICY_SHA or sha(CONSUMER)!=CONSUMER_SHA or sha(report_path)!=report_sha
            or sha(__file__)!=run_identity['author_source_sha256']):
        if not candidate_path.exists():candidate_tmp.unlink(missing_ok=True)
        raise AssertionError(f'source inputs changed during authoring: {changed_inputs[:10]}')
    if not candidate_path.exists():os.replace(candidate_tmp,candidate_path)
    expected_final={'event':'final','status':terminal_status,'processed_count':len(terminal),
        'remaining_count':0,'candidate_sha256':candidate_sha,'execution_plan_sha256':EXECUTION_PLAN_SHA}
    if ledger_final is None:append_event(output_dir/'ledger.jsonl',expected_final)
    elif ledger_final!=expected_final:raise AssertionError('existing final ledger event differs from completed composition')
    receipt=build_receipt(output_dir,inv,report_path,report_sha,terminal,order,terminal_status,
        candidate_sha=candidate_sha)
    receipt['changed_vertices_total_vs_B']=int(len(np.argwhere(candidate!=base)))
    write_json_atomic(out/'receipt.json',receipt)
    progress(progress_path,'publication','complete',status=terminal_status,candidate_sha256=candidate_sha)
    return receipt


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--execute',action='store_true',help='derive all source windows after verifying an explicit global PASS report')
    ap.add_argument('--global-pass-report',type=Path)
    ap.add_argument('--global-pass-sha256')
    ap.add_argument('--output-dir',type=Path,default=EXT/'derived-composite')
    ap.add_argument('--progress-log',type=Path,default=EXT/'author-progress.jsonl')
    args=ap.parse_args()
    if args.self_test:
        policy=load_policy();shape=load_module('ev93_shape_fixture',SHAPE,SHAPE_SHA)
        print(json.dumps({'status':'FIXTURES_PASS','fixtures':synthetic_fixture(policy,POLICY_SHA,shape)},sort_keys=True))
        return
    if not args.execute or not args.global_pass_report or not args.global_pass_sha256:
        ap.error('no work is performed without --execute and a pinned --global-pass-report/--global-pass-sha256')
    receipt=author(args.global_pass_report,args.global_pass_sha256,args.output_dir,args.progress_log)
    print(json.dumps({'status':receipt['status'],'candidate_sha256':receipt['candidate_sha256'],
                      'receipt':str(args.output_dir/'receipt.json')},sort_keys=True))


if __name__=='__main__':main()
