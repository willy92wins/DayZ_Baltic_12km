#!/usr/bin/env python
"""Derive one-axis EV93 scalar blends into a quarantined pool.

This no-solver stage accepts only the exact, reviewed global FAIL source and
publishes target artifacts, never a terrain candidate. Selection and the final
global consumer are separate stages.
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
EXECUTION_PLAN = EXT / 'EXECUTION_PLAN_V2.md'
EXECUTION_PLAN_SHA = '8a4afc1e26dc0d816ade9454ee4f4e31c185b03a56c8a9ef5005f468d0cff9b0'
SHAPE = Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/next-method-consumer/shape_contract.py')
SHAPE_SHA = '8cd9d0fbea03c05e5ae53a31676d79ec2364be83c055213446f6c8599245d533'
EV92 = Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev92-damped/consumer/verify_ev92.py')
EV92_SHA = '87b5ee5ee95318f1a8026c4a7459aa06d27c9b69db80f34ad25149293d5fc1df'
CONSUMER = G / 'consumer-global/verify_layer.py'
CONSUMER_SHA = '33050881caaf5e75f288d4122222c15eb326bf146c28a4c723760564457b3dc2'
TARGET_REASON = 'final gate scalar interpolation rule unavailable: baseline focus is not prominent on both axes'
EXPECTED_TARGET_COUNT = 228
MAX_SECONDS = 600.0
KNOWN_FAIL_REPORT = G / 'consumer-global/runs/attempt-04/ev93-review.json'
KNOWN_FAIL_REPORT_SHA = 'ed9a071d359dc446b5146a255c3ab9f15481c92e24c2169b6da47dd4ad27c0ec'
KNOWN_FAIL_GATES = {'physical_support_holes_lt_1e_7m2','visible_support_holes_lt_1e_7m2'}
KNOWN_LEGACY_CANDIDATE_SHA = '37e6d4bd195ee8576bc483a6c24e89cede536d916c2b041d8a6bdc98b13269f3'
KNOWN_PREPARED_SHA = '765c5a5a778132fce7f1c1d21a59c1220b62443b180238e13ee51a203b3483d4'
KNOWN_LEGACY_RECEIPT_SHA = '97165c9a3fe6ec052d8458a636be2fc9d13c6b87b05ce4491ae5123d13ea3c92'
KNOWN_LEGACY_LEDGER_SHA = 'dc0a26cc38f55c1a8bb5709e36cfacd41859c3f901aabed15968a56c44832e85'
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


def gate_known_global_fail(report_path: Path, report_sha: str, inventory):
    if Path(report_path).resolve()!=KNOWN_FAIL_REPORT.resolve() or report_sha.lower()!=KNOWN_FAIL_REPORT_SHA:
        raise AssertionError('quarantine accepts only the pinned attempt-04 report identity')
    if sha(report_path)!=KNOWN_FAIL_REPORT_SHA:
        raise AssertionError('known FAIL report SHA mismatch')
    report = load_json(report_path)
    if report.get('status')!='FAIL_INCREMENTAL_NONREGRESSION':
        raise AssertionError('quarantine source is not the explicitly reviewed attempt-04 FAIL')
    gates=report.get('gates')
    if not isinstance(gates,dict) or not gates or not all(isinstance(v,bool) for v in gates.values()):
        raise AssertionError('known FAIL report has missing or malformed gates')
    actual_false={k for k,v in gates.items() if not v}
    if actual_false!=KNOWN_FAIL_GATES:
        raise AssertionError(f'global FAIL differs from the two approved support-hole gates: {sorted(actual_false)}')
    info = report.get('information', {})
    if (info.get('candidate_sha256')!=KNOWN_LEGACY_CANDIDATE_SHA
            or info.get('accepted_windows')!=340 or info.get('changed_vertices')!=20201
            or inventory['source_composite']['sha256']!=KNOWN_LEGACY_CANDIDATE_SHA):
        raise AssertionError('known FAIL does not identify the exact frozen 340-window composite')
    hashes=info.get('input_hashes',{})
    ledger=G/'fairing-layer1/ledger.jsonl'
    required={str(LEGACY_CANDIDATE.resolve()):KNOWN_LEGACY_CANDIDATE_SHA,
        str(PREPARED.resolve()):KNOWN_PREPARED_SHA,
        str(LEGACY_RECEIPT.resolve()):KNOWN_LEGACY_RECEIPT_SHA,
        str(ledger.resolve()):KNOWN_LEGACY_LEDGER_SHA}
    if any(hashes.get(p)!=wanted for p,wanted in required.items()):
        raise AssertionError('attempt-04 does not pin the frozen candidate/prepared/receipt/ledger set')
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
        'target_queue_id':qid,'source_qid':qid,
        'seed_id':int(inv_row['seed_id']),'center_rc':list(focus),
        'state':'derived_quarantined', 'solve_calls':0,
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
            or final.get('remaining_count')!=0 or final.get('status')!='QUARANTINE_POOL_READY_FOR_SELECTOR'
            or not isinstance(final.get('pool_digest'),str)):
        raise AssertionError('final ledger event is not a complete v3 quarantine pool')
    return terminal,started,final


def reject_final_pool_reentry(final_event):
    if final_event is not None:
        raise FileExistsError('completed quarantine pool is immutable; refusing receipt/pool rewrite')


def reject_orphan_target(path):
    if Path(path).exists():
        raise FileExistsError(f'orphan target without terminal ledger row requires explicit adjudication: {path}')


def build_receipt(output_dir, inv, report_path, report_sha, terminal_rows,
                  target_order, status, error=None, pool_digest=None):
    out=Path(output_dir).resolve()
    ordered=[terminal_rows[q] for q in target_order if q in terminal_rows]
    target_refs=[{'queue_id':int(x['queue_id']),'source_qid':int(x['queue_id']),
        'seed_id':int(x['seed_id']),'state':x['state'],'path':str(Path(x['path']).resolve()),
        'sha256':x['sha256'],'source_result_path':x['source_result_path'],
        'source_result_sha256':x['source_result_sha256']} for x in ordered]
    target_jsonl=out/'targets.jsonl'
    raw=''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in target_refs).encode('utf-8')
    tmp=target_jsonl.with_name('targets.jsonl.tmp')
    with tmp.open('wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    os.replace(tmp,target_jsonl)
    states={s:sum(x['state']==s for x in target_refs) for s in sorted({x['state'] for x in target_refs})}
    receipt={
        'schema':'ev93.crest-extension.quarantine-receipt.v3','status':status,
        'execution_plan_path':str(EXECUTION_PLAN.resolve()),'execution_plan_sha256':EXECUTION_PLAN_SHA,
        'author_source_path':str(Path(__file__).resolve()),'author_source_sha256':sha(__file__),
        'source_inventory_path':str(INVENTORY.resolve()),'source_inventory_sha256':INVENTORY_SHA,
        'source_base_path':str(BASE.resolve()),'source_base_sha256':sha(BASE),
        'legacy_composite_path':str(LEGACY_CANDIDATE.resolve()),'legacy_composite_sha256':sha(LEGACY_CANDIDATE),
        'legacy_receipt_sha256':sha(LEGACY_RECEIPT),'prepared_sha256':sha(PREPARED),
        'source_global_report_path':str(Path(report_path).resolve()),'source_global_report_sha256':report_sha,
        'source_global_report_status':'FAIL_INCREMENTAL_NONREGRESSION',
        'source_global_report_false_gates':sorted(KNOWN_FAIL_GATES),
        'policy_path':str(POLICY.resolve()),'policy_sha256':POLICY_SHA,
        'policy_plan_sha256':POLICY_PLAN_SHA,'consumer_source_sha256':CONSUMER_SHA,
        'target_count':EXPECTED_TARGET_COUNT,'processed_count':len(target_refs),
        'remaining_count':EXPECTED_TARGET_COUNT-len(target_refs),'target_states':states,
        'new_solver_calls':0,'derived_alpha_count':sum('alpha' in x for x in ordered),
        'selector_local_shape_fail_diagnostic_count':sum(
            x.get('selector_local_shape_diagnostic',{}).get('pass') is False for x in ordered),
        'policy_rejected_count':sum(x['state']=='rejected_policy' for x in ordered),
        'target_rows_path':str(target_jsonl),'target_rows_sha256':sha(target_jsonl),
        'ledger_path':str((out/'ledger.jsonl').resolve()),
        'ledger_sha256':sha(out/'ledger.jsonl') if (out/'ledger.jsonl').exists() else None,
        'pool_targets':target_refs,'pool_digest':pool_digest,
        'semantics':{'pool':'quarantined source-derived directions only; no terrain candidate is published',
            'reused_228':'one exact source direction per row; one policy alpha or explicit policy reject; zero solver calls',
            'global_status':'source global report is known FAIL; no acceptance or selection is implied'},
    }
    if error is not None:receipt['error']=error
    write_json_atomic(out/'receipt.json',receipt)
    return receipt


def write_compound_pool(output_dir, legacy_index, terminal_rows, receipt):
    """Publish selector input refs only; no terrain or selection is made here."""
    out=Path(output_dir).resolve()
    legacy_rows=[]
    for qid in sorted(legacy_index):
        result=legacy_index[qid]
        if result.get('state')!='accepted':
            continue
        path=Path(result['result_path']).resolve(); digest=result['result_sha256']
        if sha(path)!=digest:
            raise AssertionError(f'legacy result changed while making compound pool q{qid}')
        legacy_rows.append({'unit_id':f'legacy:{qid}','origin':'legacy','queue_id':int(qid),
            'source_qid':int(qid),'seed_id':int(result['seed_id']),'state':'accepted',
            'artifact_path':str(path),'artifact_sha256':digest,
            'source_result_path':str(path),'source_result_sha256':digest})
    if len(legacy_rows)!=340:
        raise AssertionError(f'compound pool requires exact 340 legacy accepted refs, got {len(legacy_rows)}')
    crest_rows=[]
    for qid,event in sorted(terminal_rows.items()):
        path=Path(event['path']).resolve(); digest=event['sha256']
        if sha(path)!=digest:
            raise AssertionError(f'quarantine target changed while making compound pool q{qid}')
        row=load_json(path)
        if row.get('state') not in ('derived_quarantined','rejected_policy'):
            raise AssertionError(f'non-quarantine target state q{qid}')
        if row.get('source_qid')!=qid or row.get('target_queue_id')!=qid:
            raise AssertionError(f'target/source queue identity mismatch q{qid}')
        crest_rows.append({'unit_id':f'crest:{qid}','origin':'crest','queue_id':qid,
            'source_qid':qid,'seed_id':int(row['seed_id']),'state':row['state'],
            'artifact_path':str(path),'artifact_sha256':digest,
            'source_result_path':row['source_result_path'],
            'source_result_sha256':row['source_result_sha256']})
    if len(crest_rows)!=EXPECTED_TARGET_COUNT:
        raise AssertionError(f'compound pool lacks quarantine rows: {len(crest_rows)}/{EXPECTED_TARGET_COUNT}')
    source_receipt=out/'receipt.json'
    pool={'schema':'ev93.compound-pool.v1','status':'AUTHORED_QUARANTINED',
        'source_global_report':{'path':receipt['source_global_report_path'],
                                'sha256':receipt['source_global_report_sha256']},
        'base':{'path':receipt['source_base_path'],'sha256':receipt['source_base_sha256']},
        'legacy_source':{'prepared_path':str(PREPARED.resolve()),'prepared_sha256':sha(PREPARED),
            'receipt_path':str(LEGACY_RECEIPT.resolve()),'receipt_sha256':sha(LEGACY_RECEIPT),
            'ledger_path':str((L/'ledger.jsonl').resolve()),'ledger_sha256':sha(L/'ledger.jsonl')},
        'crest_source':{'receipt_path':str(source_receipt),'receipt_sha256':sha(source_receipt),
            'target_rows_path':receipt['target_rows_path'],'target_rows_sha256':receipt['target_rows_sha256'],
            'ledger_path':receipt['ledger_path'],'ledger_sha256':receipt['ledger_sha256']},
        'expected_counts':{'legacy_accepted':340,'crest_targets':EXPECTED_TARGET_COUNT},
        'rows':legacy_rows+crest_rows}
    path=out/'compound-pool.json'
    write_json_atomic(path,pool)
    return path


def compound_pool_fixture():
    with tempfile.TemporaryDirectory(prefix='ev93-compound-pool-fixture-') as td:
        root=Path(td); legacy_index={}; terminal={}
        (root/'receipt.json').write_text('{}\n',encoding='utf-8')
        for qid in range(340):
            rp=root/'legacy'/f'{qid:04d}.json'
            digest=write_json_atomic(rp,{'queue_id':qid,'seed_id':qid,'state':'accepted'})
            legacy_index[qid]={'queue_id':qid,'seed_id':qid,'state':'accepted',
                'result_path':str(rp),'result_sha256':digest}
        for qid in range(EXPECTED_TARGET_COUNT):
            tp=root/'targets'/f'{qid:04d}.json'
            row={'queue_id':qid,'target_queue_id':qid,'source_qid':qid,'seed_id':qid,
                 'state':'derived_quarantined','source_result_path':'source.json',
                 'source_result_sha256':'a'*64}
            digest=write_json_atomic(tp,row)
            terminal[qid]={'queue_id':qid,'seed_id':qid,'state':row['state'],
                'path':str(tp),'sha256':digest,'source_result_path':'source.json',
                'source_result_sha256':'a'*64}
        receipt={'source_global_report_path':'report.json','source_global_report_sha256':'b'*64,
            'source_base_path':'base.npz','source_base_sha256':'c'*64,
            'target_rows_path':'targets.jsonl','target_rows_sha256':'d'*64,
            'ledger_path':'ledger.jsonl','ledger_sha256':'e'*64}
        path=write_compound_pool(root,legacy_index,terminal,receipt)
        pool=load_json(path)
        rows=pool['rows']
        assert len(rows)==568 and pool['expected_counts']=={'legacy_accepted':340,'crest_targets':228}
        assert len({r['unit_id'] for r in rows})==568
        assert sum(r['origin']=='legacy' for r in rows)==340
        assert sum(r['origin']=='crest' for r in rows)==228
        assert all(r['source_qid']==r['queue_id'] for r in rows)
        assert not (root/'candidate-terrain.npz').exists()
    return {'compound_pool_568_refs_and_origin_namespaces_passed':True,
            'quarantine_pool_does_not_publish_candidate':True}


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
        final_completed={'event':'final','status':'QUARANTINE_POOL_READY_FOR_SELECTOR',
            'processed_count':EXPECTED_TARGET_COUNT,'remaining_count':0,'pool_digest':'f'*64,
            'execution_plan_sha256':EXECUTION_PLAN_SHA,'source_global_report_sha256':'e'*64}
        try:reject_final_pool_reentry(final_completed)
        except FileExistsError:reentry_rejected=True
        else:raise AssertionError('completed pool re-entry was not rejected')
        assert not (root/'receipt.json').exists() and not (root/'compound-pool.json').exists()
        orphan=root/'targets'/'window-0008.json'
        write_json_atomic(orphan,{'queue_id':8,'alpha':0.125,'final_float32':[123.0]})
        before=sha(root/'ledger.jsonl')
        try:reject_orphan_target(orphan)
        except FileExistsError:orphan_rejected=True
        else:raise AssertionError('unledgered target with altered alpha was accepted')
        assert sha(root/'ledger.jsonl')==before and not (root/'receipt.json').exists()
    return {'one_active_axis_derived_and_float32_focus_passed':True,'fixed_cardinal_uses_own_baseline':True,
            'zero_active_axes_rejected':flat_rejected,
            'append_only_resume_ledger_roundtrip':True,
            'completed_pool_reentry_rejected_without_rewrite':reentry_rejected,
            'unledgered_target_rejected_without_recovery_or_rewrite':orphan_rejected,
            **compound_pool_fixture()}


def author(report_path: Path, report_sha: str, output_dir: Path, progress_path: Path | None):
    global START
    START=time.perf_counter()
    progress(progress_path,'source-validation','start')
    inv=source_inventory_check()
    gate_known_global_fail(report_path,report_sha,inv)
    progress(progress_path,'source-validation','complete',pinned_files=len(inv['source_pins']))
    output_dir=output_dir.resolve()
    output_dir.mkdir(parents=True,exist_ok=True)
    if (output_dir/'candidate-terrain.npz').exists():
        raise AssertionError('quarantine output directory must not contain a terrain candidate')
    run_path=output_dir/'run.json'
    run_identity={'schema':'ev93.crest-extension.quarantine-run.v3',
        'execution_plan_sha256':EXECUTION_PLAN_SHA,'inventory_sha256':INVENTORY_SHA,
        'source_global_report_path':str(report_path.resolve()),'source_global_report_sha256':report_sha,
        'expected_target_count':EXPECTED_TARGET_COUNT,'author_source_sha256':sha(__file__),
        'policy_sha256':POLICY_SHA,'consumer_source_sha256':CONSUMER_SHA,
        'shape_contract_sha256':SHAPE_SHA,'ev92_source_sha256':EV92_SHA,
        'policy_plan_sha256':POLICY_PLAN_SHA,'source_pins':inv['source_pins']}
    if run_path.exists():
        if load_json(run_path)!=run_identity:
            raise AssertionError('resume identity differs from immutable quarantine run manifest')
    else:
        if any(output_dir.iterdir()):
            raise FileExistsError(f'output directory is nonempty without run manifest: {output_dir}')
        write_json_atomic(run_path,run_identity)
    policy=load_policy(); validator=load_consumer()
    _,_,_,_,shape,_,_=validator.load_helpers()
    with np.load(BASE,allow_pickle=False) as z:
        base=np.asarray(z['heights'],dtype=np.float32)
        base_npz={k:z[k] for k in z.files}
    prepared,legacy_receipt,entries,ledger,ledger_path=validator.verify_prepared(
        PREPARED,LEGACY_RECEIPT,base)
    if sha(CONSUMER)!=CONSUMER_SHA or sha(POLICY)!=POLICY_SHA:
        raise AssertionError('consumer or policy changed during load')
    details=validator.validate_detail_hashes(prepared,entries)
    prepared_by={int(x['queue_id']):x for x in entries}
    # Pin and inspect the known legacy composite as provenance only. This stage
    # never composes it with the quarantine rows or writes a candidate.
    with np.load(LEGACY_CANDIDATE,allow_pickle=False) as z:
        legacy={k:z[k] for k in z.files}
    if set(legacy)!=set(base_npz) or any(not np.array_equal(legacy[k],base_npz[k],equal_nan=True)
                                         for k in base_npz if k!='heights'):
        raise AssertionError('legacy composite changed non-height baseline arrays')
    terminal,started,ledger_final=read_terminal_rows(output_dir)
    reject_final_pool_reentry(ledger_final)
    if ledger_final is not None and ledger_final.get('status')!='QUARANTINE_POOL_READY_FOR_SELECTOR':
        raise AssertionError('existing terminal event is not a v3 quarantine-pool final')
    source_by_q={int(x['queue_id']):x for x in inv['reusable_directions']}
    if set(terminal)-set(source_by_q) or len(terminal)>EXPECTED_TARGET_COUNT:
        raise AssertionError('resume ledger contains unknown or excess target rows')
    for qid,event in terminal.items():
        if int(event.get('seed_id',-1))!=int(source_by_q[qid]['seed_id']):
            raise AssertionError(f'resume terminal seed mismatch q{qid}')
    prepared_sha=sha(PREPARED);policy_sha=sha(POLICY)
    order=[int(x['queue_id']) for x in inv['reusable_directions']]
    progress(progress_path,'source-validation','consumer_inputs_ready',targets=EXPECTED_TARGET_COUNT)
    for pos,invrow in enumerate(inv['reusable_directions']):
        qid=int(invrow['queue_id']);entry=prepared_by[qid]
        if qid in terminal:
            continue
        if ledger_final is not None:
            raise AssertionError('cannot append a target after terminal pool final')
        if time.perf_counter()-START>=MAX_SECONDS:
            return build_receipt(output_dir,inv,report_path,report_sha,terminal,order,'INCOMPLETE',
                {'kind':'deadline','budget_seconds':MAX_SECONDS})
        orphan=output_dir/'targets'/f'window-{qid:04d}.json'
        reject_orphan_target(orphan)
        append_event(output_dir/'ledger.jsonl',{'event':'started','queue_id':qid,
            'seed_id':int(invrow['seed_id']),'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
        row_start=time.perf_counter()
        try:
            result,nodes,stencils,direction=validate_source_row(validator,invrow,entry,base)
            derived=derive_one(invrow,result,nodes,stencils,direction,base,prepared_sha,
                               policy,policy_sha,shape,details)
        except policy.PolicyReject as exc:
            derived={
                'schema':'ev93.crest-extension.target.v1','queue_id':qid,
                'target_queue_id':qid,'source_qid':qid,'seed_id':int(invrow['seed_id']),
                'center_rc':list(map(int,invrow['center_rc'])),'state':'rejected_policy',
                'solve_calls':0,'source_state':'rejected','source_reason':TARGET_REASON,
                'policy_rejection_code':exc.code,'policy_rejection_message':str(exc),
                'source_result_path':invrow['result_path'],'source_result_sha256':invrow['result_sha256'],
                'source_solution_path':invrow['solution_path'],'source_solution_sha256':invrow['solution_sha256'],
                'source_marker_path':invrow['attempt_marker_path'],'source_marker_sha256':invrow['attempt_marker_sha256'],
                'direction_sha256':invrow['direction_float32_le_sha256'],
                'stencil_set_sha256':invrow['stencil_set_sha256'],'new_solver_calls':0}
        except Exception as exc:
            build_receipt(output_dir,inv,report_path,report_sha,terminal,order,'INCOMPLETE',
                {'kind':'worker_error','queue_id':qid,'error':repr(exc)})
            progress(progress_path,'derive-directions','error',queue_id=qid,error=repr(exc))
            raise
        # Shape results are diagnostic only here. The independent selector
        # evaluates the full local contract on B + this exact delta.
        if derived['state']!='rejected_policy':
            derived['source_qid']=qid
            derived['state']='derived_quarantined'
            derived['selector_local_shape_diagnostic']={
                'gates':derived.pop('local_shape_nonfocus_gates'),
                'pass':derived.pop('local_shape_pass')}
        row_path=output_dir/'targets'/f'window-{qid:04d}.json'
        row_sha=write_json_atomic(row_path,derived)
        terminal_event={'event':'target','queue_id':qid,'seed_id':int(invrow['seed_id']),
            'state':derived['state'],'path':str(row_path.resolve()),'sha256':row_sha,
            'source_result_path':derived['source_result_path'],
            'source_result_sha256':derived['source_result_sha256'],
            'elapsed_ms':round((time.perf_counter()-row_start)*1000,3)}
        append_event(output_dir/'ledger.jsonl',terminal_event);terminal[qid]=terminal_event
        if (pos+1)%25==0 or pos+1==EXPECTED_TARGET_COUNT:
            progress(progress_path,'derive-directions','progress',processed=len(terminal),
                total=EXPECTED_TARGET_COUNT,elapsed_row_ms=terminal_event['elapsed_ms'],
                policy_derived=sum(x['state']=='derived_quarantined' for x in terminal.values()),
                policy_rejected=sum(x['state']=='rejected_policy' for x in terminal.values()))
        build_receipt(output_dir,inv,report_path,report_sha,terminal,order,'INCOMPLETE',
            {'kind':'running','budget_seconds':MAX_SECONDS})
        if time.perf_counter()-START>=MAX_SECONDS:
            return build_receipt(output_dir,inv,report_path,report_sha,terminal,order,'INCOMPLETE',
                {'kind':'deadline','budget_seconds':MAX_SECONDS})
    if len(terminal)!=EXPECTED_TARGET_COUNT:
        raise AssertionError(f'quarantine pool incomplete: {len(terminal)}/{EXPECTED_TARGET_COUNT}')
    rows=[load_json(terminal[q]['path']) for q in order]
    if any(row['state'] not in ('derived_quarantined','rejected_policy') for row in rows):
        raise AssertionError('pool contains a non-v3 terminal row state')
    # Freeze every source input again before publishing a pool-ready receipt.
    changed_inputs=[p for p,want in inv['source_pins'].items() if sha(p)!=want]
    if (changed_inputs or sha(INVENTORY)!=INVENTORY_SHA or sha(EXECUTION_PLAN)!=EXECUTION_PLAN_SHA
            or sha(POLICY)!=POLICY_SHA or sha(CONSUMER)!=CONSUMER_SHA
            or sha(report_path)!=report_sha or sha(__file__)!=run_identity['author_source_sha256']):
        raise AssertionError(f'source inputs changed during quarantine authoring: {changed_inputs[:10]}')
    refs=[{'queue_id':int(row['queue_id']),'source_qid':int(row['source_qid']),
           'seed_id':int(row['seed_id']),'state':row['state'],
           'path':str(Path(terminal[int(row['queue_id'])]['path']).resolve()),
           'sha256':terminal[int(row['queue_id'])]['sha256'],
           'source_result_path':row['source_result_path'],
           'source_result_sha256':row['source_result_sha256']} for row in rows]
    pool_digest=canonical_sha(refs)
    expected_final={'event':'final','status':'QUARANTINE_POOL_READY_FOR_SELECTOR',
        'processed_count':len(terminal),'remaining_count':0,'pool_digest':pool_digest,
        'execution_plan_sha256':EXECUTION_PLAN_SHA,'source_global_report_sha256':report_sha}
    if ledger_final is None:
        append_event(output_dir/'ledger.jsonl',expected_final)
    elif ledger_final!=expected_final:
        raise AssertionError('existing final ledger event differs from deterministic quarantine pool')
    receipt=build_receipt(output_dir,inv,report_path,report_sha,terminal,order,
                          'QUARANTINE_POOL_READY_FOR_SELECTOR',pool_digest=pool_digest)
    compound_path=write_compound_pool(output_dir,ledger,terminal,receipt)
    progress(progress_path,'publication','complete',status=receipt['status'],pool_digest=pool_digest,
             compound_pool_path=str(compound_path),compound_pool_sha256=sha(compound_path))
    return receipt

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--execute',action='store_true',help='derive the pinned source directions into a quarantined pool')
    ap.add_argument('--source-global-report',type=Path)
    ap.add_argument('--source-global-sha256')
    ap.add_argument('--output-dir',type=Path,default=EXT/'quarantine-pool-v3')
    ap.add_argument('--progress-log',type=Path,default=EXT/'author-progress.jsonl')
    args=ap.parse_args()
    if args.self_test:
        policy=load_policy();shape=load_module('ev93_shape_fixture',SHAPE,SHAPE_SHA)
        print(json.dumps({'status':'FIXTURES_PASS','fixtures':synthetic_fixture(policy,POLICY_SHA,shape)},sort_keys=True))
        return
    if not args.execute or not args.source_global_report or not args.source_global_sha256:
        ap.error('no work is performed without --execute and the pinned --source-global-report/--source-global-sha256')
    receipt=author(args.source_global_report,args.source_global_sha256,args.output_dir,args.progress_log)
    print(json.dumps({'status':receipt['status'],'pool_digest':receipt.get('pool_digest'),
                      'receipt':str(args.output_dir/'receipt.json'),
                      'compound_pool':str(args.output_dir/'compound-pool.json')},sort_keys=True))


if __name__=='__main__':main()
