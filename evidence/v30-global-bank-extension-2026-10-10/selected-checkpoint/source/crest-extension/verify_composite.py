#!/usr/bin/env python
"""Independent verifier for legacy EV93 deltas plus reused one-axis directions.

It validates the source 340-window EV92 path through the frozen layer consumer,
independently reconstructs the 228 scalar blends, then calls that consumer's
global geometry/water contract on the fully composed height field. No author,
solver, PBO builder, or DayZ process is imported.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time
import traceback

import numpy as np

G=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
EXT=G/'crest-extension'; L=G/'fairing-layer1'
BASE=Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')
PREPARED=L/'prepared.json'; LEGACY_RECEIPT=L/'authoring.json'
INVENTORY=EXT/'reuse-source-inventory.json'
INVENTORY_SHA='8b8b9a6e525ee3bd8df59bef18784bafdc921e295ec9ebdb7043eefa4317b042'
POLICY=G/'crest-policy/crest_policy.py'; POLICY_SHA='32ab6e0111886907315a0360322df0ff958f80bebcd6493254a2f0f144a3829e'
CONSUMER=G/'consumer-global/verify_layer.py'; CONSUMER_SHA='33050881caaf5e75f288d4122222c15eb326bf146c28a4c723760564457b3dc2'
ANY_DIAGNOSTIC=G/'consumer-global/diagnose_any_populations.py'
ANY_DIAGNOSTIC_SHA='5d35cf1a80fa57673a51c404d8a8f3ddb8403f6c86045c2cea3aa2775b6de93'
POLICY_PLAN=G/'next-method-crests.md'; POLICY_PLAN_SHA='ba9245134a368870bb4e0090ff36f3c1b91b26b5bc8756d8f0fbf48ddb04ccce'
EXECUTION_PLAN=EXT/'EXECUTION_PLAN.md'; EXECUTION_PLAN_SHA='34d1fcb45a1cb4acea4d67d0831637ac510efbe6b3f72ce79e902fbea75d74ab'
SHAPE=Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/next-method-consumer/shape_contract.py')
SHAPE_SHA='8cd9d0fbea03c05e5ae53a31676d79ec2364be83c055213446f6c8599245d533'
EV92=Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev92-damped/consumer/verify_ev92.py')
EV92_SHA='87b5ee5ee95318f1a8026c4a7459aa06d27c9b69db80f34ad25149293d5fc1df'
TARGET_REASON='final gate scalar interpolation rule unavailable: baseline focus is not prominent on both axes'
PASS_STATUS='PASS_INCREMENTAL_NONREGRESSION'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),
        ensure_ascii=False,allow_nan=False).encode('utf-8')).hexdigest()


def load_json(path): return json.loads(Path(path).read_text(encoding='utf-8'))


def load_module(name,path,wanted):
    actual=sha(path)
    if actual!=wanted:raise AssertionError(f'frozen input changed {path}: {actual} != {wanted}')
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:raise ImportError(f'cannot import {path}')
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod


def progress(log_path, phase, event, **data):
    row={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'elapsed_s':round(time.perf_counter()-START,3),
         'phase':phase,'event':event,**data}
    line=json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False)
    print(line,flush=True)
    if log_path:
        with Path(log_path).open('a',encoding='utf-8',newline='\n') as f:f.write(line+'\n');f.flush();os.fsync(f.fileno())


def load_inputs_and_helpers():
    if sha(INVENTORY)!=INVENTORY_SHA:raise AssertionError('source inventory SHA mismatch')
    inv=load_json(INVENTORY)
    if inv.get('status')!='REUSE_SOURCE_INVENTORY_READY' or len(inv.get('reusable_directions',[]))!=228:
        raise AssertionError('source inventory is incomplete')
    for p,want in inv['source_pins'].items():
        if sha(p)!=want:raise AssertionError(f'inventory input hash mismatch: {p}')
    if sha(EXECUTION_PLAN)!=EXECUTION_PLAN_SHA:raise AssertionError('execution plan SHA mismatch')
    policy=load_module('ev93_crest_policy_verifier',POLICY,POLICY_SHA)
    ev=load_module('ev93_layer_consumer_reused',CONSUMER,CONSUMER_SHA)
    if sha(POLICY_PLAN)!=POLICY_PLAN_SHA or sha(SHAPE)!=SHAPE_SHA or sha(EV92)!=EV92_SHA:
        raise AssertionError('policy dependencies changed')
    helpers=ev.load_helpers()
    return inv,policy,ev,helpers


def verify_pinned_file(path, expected_sha, label):
    actual=sha(path)
    if actual!=expected_sha:raise AssertionError(f'{label} SHA mismatch: {actual} != {expected_sha}')
    return actual


def verify_target_provenance(row, src, qid):
    expected={'source_reason':TARGET_REASON,'source_result_sha256':src['result_sha256'],
        'source_solution_sha256':src['solution_sha256'],'source_marker_sha256':src['attempt_marker_sha256'],
        'direction_sha256':src['direction_float32_le_sha256'],'stencil_set_sha256':src['stencil_set_sha256'],
        'source_result_path':src['result_path'],'source_solution_path':src['solution_path'],
        'source_marker_path':src['attempt_marker_path']}
    if int(row.get('queue_id',-1))!=qid or int(row.get('seed_id',-1))!=int(src['seed_id']) or row.get('center_rc')!=src['center_rc']:
        raise AssertionError(f'target identity mismatch q{qid}')
    for key,value in expected.items():
        if row.get(key)!=value:raise AssertionError(f'target provenance mismatch q{qid}: {key}')
    return True


def verify_scalar_record(row, policy, rule, moments):
    if row.get('policy_id')!=policy.POLICY_ID or row.get('policy_mode')!=rule['policy_mode']:
        raise AssertionError(f'policy identity/mode mismatch q{row.get("queue_id")}')
    if row.get('scalar_rule') is None or canonical_sha(row['scalar_rule'])!=canonical_sha(rule):
        raise AssertionError(f'policy rule does not independently reconstruct q{row.get("queue_id")}')
    if float(row.get('alpha',float('nan')))!=float(rule['alpha_midpoint']) or row.get('energy_moments_fraction')!=[str(x) for x in moments]:
        raise AssertionError(f'alpha/exact moments differ q{row.get("queue_id")}')
    return True


def verify_float32_composition(candidate, nodes, row_final, expected_final, qid):
    nodes=np.asarray(nodes,dtype=np.int32);row_final=np.asarray(row_final,dtype=np.float32)
    expected_final=np.asarray(expected_final,dtype=np.float32)
    if not np.array_equal(row_final,expected_final):raise AssertionError(f'float32 cast mismatch q{qid}')
    if not np.array_equal(np.asarray(candidate[tuple(nodes.T)],np.float32),expected_final):
        raise AssertionError(f'candidate composition mismatch q{qid}')
    return True


def energy_moments(base,nodes,direction,stencils):
    """Consumer-side exact q0/q1/q2 reconstruction from immutable source H."""
    b=np.asarray(base,dtype=np.float32)
    hmap={tuple(map(int,rc)):np.float32(v) for rc,v in zip(nodes.tolist(),direction.tolist())}
    q=[Fraction(0),Fraction(0),Fraction(0)]
    for kind,r,c in stencils:
        if kind=='xx':sup=((r,c,1),(r,c+1,-2),(r,c+2,1))
        elif kind=='zz':sup=((r,c,1),(r+1,c,-2),(r+2,c,1))
        elif kind=='xz':sup=((r,c,Fraction(-1,4)),(r,c+2,Fraction(1,4)),
                             (r+2,c,Fraction(1,4)),(r+2,c+2,Fraction(-1,4)))
        else:raise AssertionError(f'unknown stencil {kind!r}')
        bv=sum((Fraction(float(b[rr,cc]))*coef for rr,cc,coef in sup),Fraction(0))
        hv=sum((Fraction(float(hmap.get((rr,cc),b[rr,cc])))*coef for rr,cc,coef in sup),Fraction(0))
        dv=hv-bv;w=2 if kind=='xz' else 1
        q[0]+=w*bv*bv;q[1]+=2*w*bv*dv;q[2]+=w*dv*dv
    return q


def provenance_for(policy, invrow, prepared_sha):
    return policy.Provenance(
        queue_id=int(invrow['queue_id']),center_rc=tuple(map(int,invrow['center_rc'])),
        baseline_sha256=sha(BASE),prepared_sha256=prepared_sha,
        result_sha256=invrow['result_sha256'],solution_sha256=invrow['solution_sha256'],
        policy_plan_sha256=policy.EXPECTED_PINS['policy_plan_sha256'],
        ev92_sha256=policy.EXPECTED_PINS['ev92_sha256'],
        shape_contract_sha256=policy.EXPECTED_PINS['shape_contract_sha256'],
        policy_module_sha256=sha(POLICY),source_rejection_reason=invrow['reason'])


def derive_rule(policy,invrow,base,nodes,stencils,direction,prepared_sha):
    r,c=map(int,invrow['center_rc']);card_rc=((r,c),(r,c-1),(r,c+1),(r-1,c),(r+1,c))
    hmap={tuple(map(int,rc)):np.float32(v) for rc,v in zip(nodes.tolist(),direction.tolist())}
    bcard=np.asarray([base[rc] for rc in card_rc],dtype=np.float32)
    hcard=np.asarray([hmap.get(rc,base[rc]) for rc in card_rc],dtype=np.float32)
    axes={'EW':float(bcard[0])>max(float(bcard[1]),float(bcard[2])),
          'NS':float(bcard[0])>max(float(bcard[3]),float(bcard[4]))}
    if axes != invrow['active_axes'] or sum(axes.values())!=1:
        raise AssertionError(f'not an exact one-axis source target q{invrow["queue_id"]}')
    moments=energy_moments(base,nodes,direction,stencils)
    lower=policy.energy_lower_from_moments(moments)
    rule=policy.derive_scalar_rule_from_cardinals(bcard,hcard,alpha_energy=lower,
        provenance=provenance_for(policy,invrow,prepared_sha),legacy_rule=None)
    return bcard,hcard,moments,rule


def scalar_formula_fixture(policy):
    b=np.asarray([10,8,8,10,10],dtype=np.float32)
    d=np.asarray([9,8,8,10,10],dtype=np.float32)
    grid=np.full((19,19),10,dtype=np.float32);grid[9,8]=grid[9,10]=8
    nodes=np.asarray([[9,9]],dtype=np.int32);direction=np.asarray([9],dtype=np.float32)
    moments=energy_moments(grid,nodes,direction,[('xx',9,8)])
    ae=policy.energy_lower_from_moments(moments)
    prov=policy.Provenance(0,(9,9),sha(BASE),'a'*64,'b'*64,'c'*64,
        policy.EXPECTED_PINS['policy_plan_sha256'],policy.EXPECTED_PINS['ev92_sha256'],
        policy.EXPECTED_PINS['shape_contract_sha256'],sha(POLICY),TARGET_REASON)
    rule=policy.derive_scalar_rule_from_cardinals(b,d,alpha_energy=ae,provenance=prov)
    alpha=float(rule['alpha_midpoint'])
    final=(grid.astype(np.float64)+alpha*((grid.copy().astype(np.float64))-
             grid.astype(np.float64))).astype(np.float32)
    final[9,9]=np.float32(float(grid[9,9])+alpha*(float(direction[0])-float(grid[9,9])))
    post=policy.evaluate_focus_after_cardinals(b,np.asarray([final[9,9],final[9,8],final[9,10],final[8,9],final[10,9]],np.float32))
    assert 0<alpha<1 and post['pass'] and rule['policy_mode']=='one_active_axis_affine_tail'
    # Negative: changing the source center cardinal changes the independently recomputed alpha.
    bad=d.copy();bad[0]=np.float32(10)
    try: policy.derive_scalar_rule_from_cardinals(b,bad,alpha_energy=ae,provenance=prov)
    except ValueError: rejected=True
    else: raise AssertionError('two-axis branch accepted without legacy rule')
    return {'one_axis_policy_path_passed':True,'two_axis_missing_legacy_rejected':rejected}


def compose_nodes(grid,nodes,final_values,owned):
    for rc,val in zip(np.asarray(nodes,dtype=np.int32).tolist(),np.asarray(final_values,dtype=np.float32).tolist()):
        n=tuple(map(int,rc))
        if n in owned:raise AssertionError(f'duplicate composed ownership {n}')
        owned.add(n);grid[n]=np.float32(val)


def compose_fixture():
    b=np.zeros((8,8),np.float32);legacy=b.copy();legacy[1,1]=1
    target=legacy.copy();owned=set()
    compose_nodes(target,[[4,4],[4,5]],[2,3],owned)
    assert np.array_equal(target,np.asarray([[0,0,0,0,0,0,0,0],[0,1,0,0,0,0,0,0],
      *[[0]*8 for _ in range(2)],[0,0,0,0,2,3,0,0],*[ [0]*8 for _ in range(3)]],dtype=np.float32))
    try:compose_nodes(target,[[4,5]],[7],owned)
    except AssertionError:dup=True
    else:raise AssertionError('overlap fixture failed to reject duplicate mutable owner')
    return {'legacy_and_reused_domains_composed':True,'duplicate_owner_rejected':dup}


def verify_terminal_ledger(events, rows, receipt_status, candidate_sha):
    starts=[x for x in events if x.get('event')=='started']
    targets=[x for x in events if x.get('event')=='target']
    finals=[x for x in events if x.get('event')=='final']
    if len(targets)!=len(rows) or len(finals)!=1:
        raise AssertionError('ledger is not terminal for every prepared row')
    known={'started','target','final'}
    if any(x.get('event') not in known for x in events):raise AssertionError('unknown ledger event')
    seen_started=set()
    for event in events:
        kind=event.get('event');qid=int(event.get('queue_id',-1))
        if kind=='started':seen_started.add(qid)
        elif kind=='target' and qid not in seen_started:raise AssertionError('target result precedes its start marker')
        elif kind=='final' and event is not events[-1]:raise AssertionError('final event is not last')
    if len({int(x['queue_id']) for x in targets})!=len(targets):raise AssertionError('duplicate terminal target event')
    refs=[{'queue_id':int(x['queue_id']),'state':x['state'],'path':str(Path(x['path']).resolve()),'sha256':x['sha256']} for x in rows]
    actual=[{'queue_id':int(x['queue_id']),'state':x['state'],'path':str(Path(x['path']).resolve()),'sha256':x['sha256']} for x in targets]
    if actual!=refs:raise AssertionError('ledger target order or payload differs from receipt rows')
    started_qids={int(x['queue_id']) for x in starts}
    target_qids={int(x['queue_id']) for x in targets}
    if target_qids!=started_qids:raise AssertionError('ledger starts/terminal target population differs')
    final=finals[0]
    if (final.get('processed_count')!=len(rows) or final.get('remaining_count')!=0
            or final.get('candidate_sha256')!=candidate_sha
            or final.get('execution_plan_sha256')!=EXECUTION_PLAN_SHA
            or final.get('status')!=receipt_status):
        raise AssertionError('ledger final event does not certify exact completed composition')
    return {'target_events':len(targets),'started_events':len(starts),'final_events':1}


def ledger_fixture():
    rows=[{'queue_id':1,'state':'accepted','path':'C:/fixture/one.json','sha256':'a'*64},
          {'queue_id':2,'state':'rejected','path':'C:/fixture/two.json','sha256':'b'*64}]
    events=[{'event':'started','queue_id':1},{'event':'target',**rows[0]},
            {'event':'started','queue_id':2},{'event':'target',**rows[1]},
            {'event':'final','processed_count':2,'remaining_count':0,'candidate_sha256':'c'*64,
             'execution_plan_sha256':EXECUTION_PLAN_SHA,'status':'AUTHORED_PENDING_COMPOSITE_CONSUMER'}]
    positive=verify_terminal_ledger(events,rows,'AUTHORED_PENDING_COMPOSITE_CONSUMER','c'*64)
    for bad in (events[:-2],events[:-1]):
        try:verify_terminal_ledger(bad,rows,'AUTHORED_PENDING_COMPOSITE_CONSUMER','c'*64)
        except AssertionError:pass
        else:raise AssertionError('ledger fixture accepted missing row or nonterminal ledger')
    return {'two_row_terminal_ledger_pass':positive,'missing_terminal_row_rejected':True,
            'missing_final_event_rejected':True}


def production_path_negative_fixtures(policy):
    src={'queue_id':4,'seed_id':9,'center_rc':[50,60],'reason':TARGET_REASON,
         'result_sha256':'a'*64,'solution_sha256':'b'*64,'attempt_marker_sha256':'c'*64,
         'direction_float32_le_sha256':'d'*64,'stencil_set_sha256':'e'*64,
         'result_path':'fixture/result.json','solution_path':'fixture/solution.npz',
         'attempt_marker_path':'fixture/started.json'}
    row={'queue_id':4,'seed_id':9,'center_rc':[50,60],'source_reason':TARGET_REASON,
         'source_result_sha256':'a'*64,'source_solution_sha256':'b'*64,'source_marker_sha256':'c'*64,
         'direction_sha256':'d'*64,'stencil_set_sha256':'e'*64,
         'source_result_path':'fixture/result.json','source_solution_path':'fixture/solution.npz',
         'source_marker_path':'fixture/started.json'}
    assert verify_target_provenance(row,src,4)
    provenance_rejections=0
    for field in ('source_result_sha256','source_solution_sha256','source_marker_sha256'):
        bad=dict(row);bad[field]='f'*64
        try:verify_target_provenance(bad,src,4)
        except AssertionError:provenance_rejections+=1
        else:raise AssertionError(f'corrupt {field} passed production provenance verifier')
    with tempfile.TemporaryDirectory(prefix='ev93-negative-hash-') as td:
        files={}
        for name in ('result','solution'):
            p=Path(td)/f'{name}.bin';p.write_text(f'{name}-original',encoding='utf-8')
            files[name]=(p,sha(p));verify_pinned_file(p,files[name][1],f'fixture {name}')
        for name,(p,wanted) in files.items():
            p.write_text(f'{name}-corrupted',encoding='utf-8')
            try:verify_pinned_file(p,wanted,f'fixture {name}')
            except AssertionError:pass
            else:raise AssertionError(f'corrupt {name} artifact passed pinned-file verifier')
        hash_rejection=True
    policy_row={'queue_id':4,'policy_id':policy.POLICY_ID,'policy_mode':'fixture',
        'scalar_rule':{'alpha_midpoint':0.5,'policy_mode':'fixture'},'alpha':0.5,
        'energy_moments_fraction':['1','2','3']}
    assert verify_scalar_record(policy_row,policy,policy_row['scalar_rule'],[1,2,3])
    bad_alpha=dict(policy_row);bad_alpha['alpha']=0.5001
    try:verify_scalar_record(bad_alpha,policy,policy_row['scalar_rule'],[1,2,3])
    except AssertionError:alpha_rejection=True
    else:raise AssertionError('altered scalar alpha passed production verifier')
    nodes=np.asarray([[2,2],[2,3]],np.int32);good=np.asarray([1.25,1.5],np.float32)
    candidate=np.zeros((5,5),np.float32);candidate[tuple(nodes.T)]=good
    assert verify_float32_composition(candidate,nodes,good,good,4)
    bad_cast=good.copy();bad_cast[0]=np.nextafter(bad_cast[0],np.float32(np.inf))
    try:verify_float32_composition(candidate,nodes,bad_cast,good,4)
    except AssertionError:cast_rejection=True
    else:raise AssertionError('altered float32 cast passed production composition verifier')
    bad_composition=candidate.copy();bad_composition[2,3]=np.float32(0)
    try:verify_float32_composition(bad_composition,nodes,good,good,4)
    except AssertionError:composition_rejection=True
    else:raise AssertionError('corrupt candidate composition passed production verifier')
    return {'source_provenance_corruption_rejected':provenance_rejections==3,
        'result_or_solution_file_corruption_rejected':hash_rejection,
        'scalar_alpha_corruption_rejected':alpha_rejection,
        'float32_cast_corruption_rejected':cast_rejection,
        'candidate_composition_corruption_rejected':composition_rejection}


def local_reused_gates(ev,ev87,shape,policy,base,candidate,invrow,result_row,source_result,
                       nodes,source_b,bounds,solver_bounds,guard,direction,final,stencils,detail):
    qid=int(invrow['queue_id']);r,c=map(int,invrow['center_rc'])
    pre=detail['preflight'];r0,r1,c0,c1=map(int,pre['window']);cr0,cr1,cc0,cc1=map(int,pre['core'])
    declared=np.asarray(sorted(tuple(map(int,n)) for n in pre['domain']['eligible_after_face_freeze_nodes']),np.int32)
    node_set={tuple(map(int,x)) for x in nodes.tolist()};declared_set=set(map(tuple,declared.tolist()))
    domain_exact=node_set==declared_set
    interval_map={tuple(map(int,x['node_rc'])):np.asarray(x['interval_float32_inward_m'],np.float32)
                  for x in pre['domain']['final_float32_intervals_for_eligible_nodes']}
    bounds_exact=all(np.array_equal(bounds[i],interval_map.get(tuple(map(int,n)),np.empty(0)))
                     for i,n in enumerate(nodes.tolist()))
    source_b_exact=np.array_equal(source_b,np.asarray(base[tuple(nodes.T)],np.float32))
    guard_expected=np.asarray(pre['guard_d8']['guard_rc'],np.int32)
    guard_exact=np.array_equal(guard,guard_expected)
    solver_expected=bounds.copy();ix={tuple(map(int,n)):i for i,n in enumerate(nodes.tolist())}
    for n in guard_expected.tolist():
        k=tuple(map(int,n))
        if k not in ix:raise AssertionError(f'guard node absent from variables q{qid}')
        solver_expected[ix[k]]=np.float32(base[k])
    solver_bounds_exact=np.array_equal(solver_bounds,solver_expected)
    guard_unchanged=all(candidate[tuple(map(int,n))]==base[tuple(map(int,n))] for n in guard_expected.tolist())
    witnesses=source_result.get('d8_witnesses',[])
    witness_exact=canonical_sha(witnesses)==canonical_sha(pre['guard_d8']['descent_witnesses'])
    witness_pass=all(candidate[tuple(map(int,w['center']))]>=candidate[tuple(map(int,w['witness']))] for w in witnesses)
    d8_hash=(source_result.get('d8_matrix_sha256_f64')==pre['guard_d8']['descent_matrix_sha256_f64'] and
             source_result.get('d8_rhs_sha256_f64')==pre['guard_d8']['descent_rhs_sha256_f64'])
    records=ev.stencil_records(window=(r0,r1,c0,c1),core=(cr0,cr1,cc0,cc1),variables=declared_set)
    expected_keys=[(str(x['key'][0]),int(x['key'][1]),int(x['key'][2])) for x in records]
    stencil_exact=len(stencils)==len(expected_keys) and len(set(stencils))==len(stencils) and set(stencils)==set(expected_keys)
    # Re-derive scalar policy from B and the certified direction source.
    bcard,hcard,moments,rule=derive_rule(policy,invrow,base,nodes,stencils,direction,sha(PREPARED))
    scalar_exact=(canonical_sha(result_row.get('scalar_rule'))==canonical_sha(rule) and
                  float(result_row.get('alpha'))==float(rule['alpha_midpoint']))
    expected_final=np.asarray(np.asarray(base[tuple(nodes.T)],np.float32).astype(np.float64)+
        float(rule['alpha_midpoint'])*(direction.astype(np.float64)-np.asarray(base[tuple(nodes.T)],np.float32).astype(np.float64)),np.float32)
    final_exact=np.array_equal(expected_final,final) and np.array_equal(candidate[tuple(nodes.T)],final)
    focus=policy.evaluate_focus_after(base,candidate,focus_rc=(r,c))
    crop0,crop1,col0,col1=r0-1,r1+1,c0-1,c1+1
    base_crop=base[crop0:crop1,col0:col1].copy();candidate_crop=candidate[crop0:crop1,col0:col1].copy()
    shape_raw=shape.evaluate_shape(base_crop,candidate_crop,(1,18,1,18),(r-crop0,c-col0))
    shape_new=policy.replace_focus_gate(shape_raw,focus)
    energy_b=ev.stencil_energy_fraction(base,stencils);energy_h=ev.stencil_energy_fraction(candidate,stencils)
    collar_keys={tuple((str(x['key'][0]),int(x['key'][1]),int(x['key'][2]))) for x in records if x['collar']}
    collar=[x for x in stencils if x in collar_keys]
    collar_b=ev.stencil_energy_fraction(base,collar);collar_h=ev.stencil_energy_fraction(candidate,collar)
    local_b=ev.local_mesh_angles(base.astype(np.float64),(r,c),radius=2)
    local_h=ev.local_mesh_angles(candidate.astype(np.float64),(r,c),radius=2)
    hinge_reduction=float(local_b['max_incident_hinge_deg']-local_h['max_incident_hinge_deg'])
    angles_b=dict(ev87.edge_angles(base_crop.astype(np.float64)));angles_h=dict(ev87.edge_angles(candidate_crop.astype(np.float64)))
    collar_mask=np.zeros((r1-r0,c1-c0),bool);collar_mask[:2,:]=1;collar_mask[-2:,:]=1;collar_mask[:,:2]=1;collar_mask[:,-2:]=1
    bw=base[r0:r1,c0:c1].astype(np.float64);hw=candidate[r0:r1,c0:c1].astype(np.float64)
    collar_angle=[]
    for kind,ab in ev87.edge_angles(bw).items():
        ah=ev87.edge_angles(hw)[kind];mask=ev87.incident_any(collar_mask,kind)
        vb,vh=ab[mask],ah[mask];collar_angle.append(not vb.size or float(vh.max())<=float(vb.max())+1e-4)
    changed_crop=candidate_crop!=base_crop
    incident=np.logical_or.reduce((changed_crop[:-1,:-1],changed_crop[:-1,1:],changed_crop[1:,:-1],changed_crop[1:,1:]))
    slope_bad=0
    for rr,cc in np.argwhere(incident):
        xy=ev87.cell_xy(int(rr)+crop0,int(cc)+col0)
        gb=ev87.corner_values(base_crop,int(rr),int(cc));gh=ev87.corner_values(candidate_crop,int(rr),int(cc))
        for tri in ev87.TRIS:
            ids=np.asarray(tri,int);cb=ev87.affine_coeff(xy[ids],gb[ids]);ch=ev87.affine_coeff(xy[ids],gh[ids])
            sb=math.degrees(math.atan(np.linalg.norm(cb[:2])));sh=math.degrees(math.atan(np.linalg.norm(ch[:2])))
            slope_bad+=int(sh>max(35.,sb)+1e-4)
    new_hinges={}
    for kind,bang in angles_b.items():
        affected=ev87.incident_any(changed_crop,kind)
        new_hinges[kind]=int(np.count_nonzero((bang<=30.0001)&(angles_h[kind]>30.0001)&affected))
    gates={
      'preflight_domain_exact':domain_exact,'source_B_values_exact':source_b_exact,'inward_bounds_match_preflight':bounds_exact,
      'solver_guard_bounds_exact':solver_bounds_exact,'guard_exact_unchanged':guard_exact and guard_unchanged,
      'd8_witnesses_match_and_hold':witness_exact and witness_pass and d8_hash,
      'stencil_population_exact':stencil_exact,'scalar_policy_exact':scalar_exact,
      'float32_blend_exact':final_exact,'shape_all_original_nonfocus_gates_and_new_focus':all(shape_new['gates'].values()),
      'focus_policy_pass':focus['pass'],'energy25_after_composition':energy_h*4<=energy_b*3,
      'collar_energy_nonworse':collar_h<=collar_b,'focus_hinge_drop_2deg':hinge_reduction>=2.,
      'collar_hinge_nonworse':all(collar_angle),'incident_slopes_capped':slope_bad==0,
      'no_new_hinge_over_30_0001':not any(new_hinges.values()),
    }
    return gates,{'queue_id':qid,'alpha':float(rule['alpha_midpoint']),'energy_B':float(energy_b),
        'energy_H':float(energy_h),'collar_energy_B':float(collar_b),'collar_energy_H':float(collar_h),
        'focus_hinge_reduction_deg':hinge_reduction,'slope_violations':slope_bad,
        'new_hinges_over_30_0001':new_hinges,'shape_gates':shape_new['gates'],'gates':gates}


def validate_composite(receipt_path, output_path, progress_path=None):
    global START
    START=time.perf_counter()
    progress(progress_path,'readset','start')
    inv,policy,ev,helpers=load_inputs_and_helpers()
    initial_hashes=dict(inv['source_pins'])
    initial_hashes[str(INVENTORY.resolve())]=INVENTORY_SHA
    initial_hashes.update({str(POLICY):POLICY_SHA,str(CONSUMER):CONSUMER_SHA,
        str(POLICY_PLAN):POLICY_PLAN_SHA,str(SHAPE):SHAPE_SHA,str(EV92):EV92_SHA,
        str(EXECUTION_PLAN):EXECUTION_PLAN_SHA,
        str(Path(receipt_path).resolve()):sha(receipt_path)})
    receipt=load_json(receipt_path)
    if receipt.get('schema')!='ev93.crest-extension.receipt.v2' or receipt.get('status')!='AUTHORED_PENDING_COMPOSITE_CONSUMER':
        raise AssertionError('extension receipt is not complete/pending composite consumer')
    if (receipt.get('source_inventory_sha256')!=INVENTORY_SHA or receipt.get('policy_sha256')!=POLICY_SHA
            or receipt.get('execution_plan_sha256')!=EXECUTION_PLAN_SHA):
        raise AssertionError('extension receipt does not pin source inventory and policy')
    author_path=Path(receipt.get('author_source_path',''))
    if not author_path.is_file() or sha(author_path)!=receipt.get('author_source_sha256'):
        raise AssertionError('authoring source identity/hash mismatch')
    initial_hashes[str(author_path.resolve())]=receipt['author_source_sha256']
    if not isinstance(receipt.get('global_pass_report_sha256'),str):
        raise AssertionError('extension receipt has no explicit legacy global PASS pin')
    pass_report=Path(receipt['global_pass_report_path'])
    if sha(pass_report)!=receipt['global_pass_report_sha256'] or load_json(pass_report).get('status')!=PASS_STATUS:
        raise AssertionError('legacy global PASS report is missing/stale/not PASS')
    if load_json(pass_report).get('information',{}).get('candidate_sha256')!=inv['source_composite']['sha256']:
        raise AssertionError('global PASS report is not for the exact EV93 legacy composite')
    initial_hashes[str(pass_report.resolve())]=receipt['global_pass_report_sha256']
    progress(progress_path,'readset','verified',source_pins=len(inv['source_pins']),targets=len(inv['reusable_directions']))
    ev,ev91,ev87,cv,shape,ev92,index_module=helpers
    bundle=ev.checked_sources();base_npz=bundle['B'];base=np.asarray(base_npz['heights'],np.float32)
    prepared,legacy_receipt,entries,ledger,ledger_path=ev.verify_prepared(PREPARED,LEGACY_RECEIPT,base)
    details=ev.validate_detail_hashes(prepared,entries)
    source_composite,changed_legacy,legacy_accepted,owner=ev.reconstruct_candidate(
        base_npz,legacy_receipt,entries,ledger,details,L)
    if sha(LEGACY_CANDIDATE)!=inv['source_composite']['sha256']:
        raise AssertionError('legacy composite changed after source inventory')
    with np.load(LEGACY_CANDIDATE,allow_pickle=False) as z:legacy_npz={k:z[k] for k in z.files}
    if not np.array_equal(source_composite,legacy_npz['heights']):
        raise AssertionError('frozen consumer reconstruction differs from legacy composite')
    progress(progress_path,'legacy','verified',accepted_windows=len(legacy_accepted),changed_vertices=len(changed_legacy))
    rows=receipt.get('rows',[])
    expected_state_counts=receipt.get('target_states',{})
    actual_state_counts={s:sum(x.get('state')==s for x in rows)
                         for s in sorted({x.get('state') for x in rows})}
    if expected_state_counts!=actual_state_counts:
        raise AssertionError('target state counts differ from author receipt')
    target_jsonl=Path(receipt.get('target_rows_path',''))
    if sha(target_jsonl)!=receipt.get('target_rows_sha256'):
        raise AssertionError('target rows ledger SHA mismatch')
    jsonl_refs=[json.loads(x) for x in target_jsonl.read_text(encoding='utf-8').splitlines() if x.strip()]
    if jsonl_refs!=rows:
        raise AssertionError('target rows ledger differs from receipt rows')
    initial_hashes[str(target_jsonl.resolve())]=receipt['target_rows_sha256']
    ledger_path=Path(receipt.get('ledger_path',''))
    if not ledger_path.is_file() or sha(ledger_path)!=receipt.get('ledger_sha256'):
        raise AssertionError('append-only author ledger SHA mismatch')
    ledger_events=[json.loads(x) for x in ledger_path.read_text(encoding='utf-8').splitlines() if x.strip()]
    verify_terminal_ledger(ledger_events,rows,receipt.get('status'),receipt.get('candidate_sha256'))
    initial_hashes[str(ledger_path.resolve())]=receipt['ledger_sha256']
    if len(rows)!=228 or len({int(x['queue_id']) for x in rows})!=228:
        raise AssertionError('extension receipt does not classify 228 unique target rows')
    source_by_q={int(x['queue_id']):x for x in inv['reusable_directions']}
    prepared_by_q={int(x['queue_id']):x for x in entries}
    candidate=np.asarray(legacy_npz['heights'],np.float32).copy();target_owned=set();new_details=[];validated_target_rows=[];target_metrics=[];reused_changed=set()
    row_hashes={};result_paths={}
    for i,ref in enumerate(sorted(rows,key=lambda x:int(x['queue_id']))):
        qid=int(ref['queue_id']);src=source_by_q[qid];path=Path(ref['path'])
        if sha(path)!=ref['sha256']:raise AssertionError(f'extension target result SHA mismatch q{qid}')
        row=load_json(path);row_hashes[str(path.resolve())]=sha(path)
        if row.get('queue_id')!=qid or row.get('seed_id')!=src['seed_id'] or row.get('center_rc')!=src['center_rc']:
            raise AssertionError(f'extension target identity mismatch q{qid}')
        verify_target_provenance(row,src,qid)
        result_path=Path(src['result_path']);solution_path=Path(src['solution_path']);marker_path=Path(src['attempt_marker_path'])
        verify_pinned_file(result_path,src['result_sha256'],f'source result q{qid}')
        verify_pinned_file(solution_path,src['solution_sha256'],f'source solution q{qid}')
        verify_pinned_file(marker_path,src['attempt_marker_sha256'],f'source marker q{qid}')
        source_result=load_json(result_path)
        nodes,stencils,direction=ev.validate_attempt_artifact(qid,source_result,base)
        nodes=np.asarray(nodes,np.int32);direction=np.asarray(direction,np.float32)
        overlap=target_owned & set(map(tuple,nodes.tolist()))
        if overlap:raise AssertionError(f'target ownership collision q{qid} at {min(overlap)}')
        target_owned.update(map(tuple,nodes.tolist()))
        validated_target_rows.append(qid)
        if row['state']=='rejected_policy':
            try:
                derive_rule(policy,src,base,nodes,stencils,direction,sha(PREPARED))
            except policy.PolicyReject as exc:
                if exc.code!=row.get('policy_rejection_code'):raise AssertionError(f'policy rejection code changed q{qid}')
            else:raise AssertionError(f'consumer accepts policy-rejected target q{qid}')
            if 'alpha' in row or row.get('final_float32') is not None:raise AssertionError(f'rejected policy row carries a delta q{qid}')
            if not np.array_equal(candidate[tuple(nodes.T)],base[tuple(nodes.T)]):raise AssertionError('rejected policy row changed candidate')
            continue
        bcard,hcard,moments,rule=derive_rule(policy,src,base,nodes,stencils,direction,sha(PREPARED))
        alpha=float(rule['alpha_midpoint'])
        verify_scalar_record(row,policy,rule,moments)
        bnodes=base[tuple(nodes.T)].astype(np.float32)
        expected_final=np.asarray(bnodes.astype(np.float64)+alpha*(direction.astype(np.float64)-bnodes.astype(np.float64)),np.float32)
        final=np.asarray(row.get('final_float32'),np.float32)
        if not np.array_equal(np.asarray(row.get('variables_rc'),np.int32),nodes):
            raise AssertionError(f'final float32 delta differs from source direction q{qid}')
        if not np.array_equal(expected_final,final):raise AssertionError(f'final float32 delta differs from source direction q{qid}')
        r,c=map(int,src['center_rc']);cr=((r,c),(r,c-1),(r,c+1),(r-1,c),(r+1,c))
        hmap={tuple(map(int,rc)):np.float32(v) for rc,v in zip(nodes.tolist(),direction.tolist())}
        after=np.asarray([np.float32(float(base[rc])+alpha*(float(hmap.get(rc,base[rc]))-float(base[rc]))) for rc in cr],np.float32)
        focus_report=policy.evaluate_focus_after_cardinals(bcard,after)
        if canonical_sha(row.get('focus_after_cast'))!=canonical_sha(focus_report):
            raise AssertionError(f'post-cast focus report mismatch q{qid}')
        isolated=base.copy()
        isolated[tuple(nodes.T)]=expected_final
        detail=details[qid]
        r0,r1,c0,c1=map(int,detail['preflight']['window']);crop0,crop1,col0,col1=r0-1,r1+1,c0-1,c1+1
        base_crop=base[crop0:crop1,col0:col1].copy();isolated_crop=base_crop.copy()
        isolated_crop[nodes[:,0]-(crop0),nodes[:,1]-(col0)]=expected_final
        isolated_shape=shape.evaluate_shape(base_crop,isolated_crop,(1,18,1,18),(r-crop0,c-col0))
        isolated_shape=policy.replace_focus_gate(isolated_shape,focus_report)
        isolation_pass=all(isolated_shape['gates'].values())
        expected_state='derived_pending_composite_consumer' if isolation_pass else 'rejected_local_shape'
        if (row.get('state')!=expected_state or bool(row.get('local_shape_pass'))!=isolation_pass or
            row.get('local_shape_nonfocus_gates')!=shape_new_gates(isolated_shape)):
            raise AssertionError(f'local-shape routing does not reconstruct q{qid}')
        if row['state']=='derived_pending_composite_consumer':
            if set(map(tuple,nodes.tolist())) & set(owner):raise AssertionError(f'legacy/reused mutable ownership overlap q{qid}')
            for rc,val in zip(nodes.tolist(),expected_final.tolist()):
                n=tuple(map(int,rc));candidate[n]=np.float32(val)
                if candidate[n]!=base[n]:reused_changed.add(n)
            verify_float32_composition(candidate,nodes,final,expected_final,qid)
            source_b,bounds,solver_bounds,guard=load_solution_aux(Path(src['solution_path']))
            local_gates,metrics=local_reused_gates(ev,ev87,shape,policy,base,candidate,src,row,source_result,
                nodes,source_b,bounds,solver_bounds,guard,direction,expected_final,stencils,detail)
            target_metrics.append(metrics)
            if not all(local_gates.values()):
                row_hashes[f'local-fail-q{qid}']=canonical_sha(local_gates)
        else:
            if not np.array_equal(candidate[tuple(nodes.T)],base[tuple(nodes.T)]):raise AssertionError(f'rejected local target changed q{qid}')
            target_metrics.append({'queue_id':qid,'state':'rejected_local_shape','isolated_shape_gates':isolated_shape['gates']})
        new_details.append((qid,row,src))
        if i%25==0:progress(progress_path,'targets','verified',processed=i+1,total=228)
    progress(progress_path,'composition','reconstructed',derived=sum(x['state']=='derived_pending_composite_consumer' for x in rows),
             rejected=sum(x['state'].startswith('rejected') for x in rows))
    candidate_path=Path(receipt['candidate_path'])
    if sha(candidate_path)!=receipt['candidate_sha256']:raise AssertionError('composed candidate SHA differs from extension receipt')
    initial_hashes[str(candidate_path.resolve())]=receipt['candidate_sha256']
    with np.load(candidate_path,allow_pickle=False) as z:new_npz={k:z[k] for k in z.files}
    if set(new_npz)!=set(legacy_npz):raise AssertionError('composed candidate metadata keys differ from legacy composite')
    for k in legacy_npz:
        if k!='heights' and not np.array_equal(new_npz[k],legacy_npz[k],equal_nan=True):raise AssertionError(f'composed metadata changed: {k}')
    if not np.array_equal(new_npz['heights'],candidate):raise AssertionError('candidate is not exact legacy+reused composition')
    changed=np.argwhere(candidate!=base)
    # Preserve independent C's local checks for all 340 original EV92 acceptances,
    # while its global contract receives the fully composed height grid.
    progress(progress_path,'global','start',changed_vertices=len(changed))
    index=helpers[6].FaceRangeIndex(ev.INDEX_RUN)
    original_coverage=ev.coverage_from_index
    def timed_coverage(*args,**kwargs):
        progress(progress_path,'compiled-coverage','start')
        value=original_coverage(*args,**kwargs)
        progress(progress_path,'compiled-coverage','finished',gates=value.get('gates',{}))
        return value
    ev.coverage_from_index=timed_coverage
    try:
        result=ev.global_contract(*helpers[:6],index,bundle,base,candidate,changed,details,legacy_accepted)
    finally:
        ev.coverage_from_index=original_coverage
    progress(progress_path,'global','finished')
    # Re-hash each file consumed from its original declaration, including every
    # target row and the candidate; do not form this set after evaluation.
    for ref in rows:
        p=Path(ref['path']).resolve();initial_hashes[str(p)]=ref['sha256']
    index.reverify()
    progress(progress_path,'any-populations','start')
    any_diag=load_module('ev93_any_populations_diagnostic',ANY_DIAGNOSTIC,ANY_DIAGNOSTIC_SHA)
    any_ev87,any_ev88=any_diag.load_helpers()
    any_report=any_diag.verify_candidate(candidate_path,receipt['candidate_sha256'],any_ev87,any_ev88)
    initial_hashes.update(any_report['readset_sha256_before'])
    progress(progress_path,'any-populations','finished',scope='diagnostic_only')
    final_hashes={p:sha(p) for p in sorted(initial_hashes)}
    if final_hashes!=initial_hashes:
        bad=[p for p in initial_hashes if final_hashes.get(p)!=initial_hashes[p]]
        raise AssertionError(f'composite-consumer readset changed during run: {bad[:10]}')
    index.reverify()
    target_gate=all(all(x.get('gates',{}).values()) for x in target_metrics if 'gates' in x)
    result['gates']['all_reused_target_local_contracts']=target_gate
    result['gates']['reuse_inventory_complete_and_disjoint']=(len(validated_target_rows)==len(rows)==228 and
        inv['domains_disjoint']['targets_pairwise_mutable_nodes'] and inv['domains_disjoint']['targets_vs_accepted_mutable_nodes'])
    if int(receipt.get('new_solver_calls',-1))!=0:raise AssertionError('extension claims a solver call')
    if len(reused_changed)==0 or not any(x['state']=='derived_pending_composite_consumer' for x in rows):
        result['gates']['at_least_one_reused_nontrivial_delta']=False
    else:result['gates']['at_least_one_reused_nontrivial_delta']=True
    progress(progress_path,'global','contract_complete',changed_vertices=len(changed),false_gates=[k for k,v in result['gates'].items() if not v])
    result['information'].update({'candidate_sha256':receipt['candidate_sha256'],
       'global_contract_status':'OPEN_INHERITED_MAP_DEFECTS','legacy_accepted_windows':len(legacy_accepted),
       'reused_target_count':len(rows),'validated_target_count':len(validated_target_rows),
       'reused_derived_count':sum(x['state']=='derived_pending_composite_consumer' for x in rows),
       'reused_local_metrics':target_metrics,'changed_vertices_vs_B':len(changed),
       'reused_changed_vertices':len(reused_changed),'input_hashes':final_hashes,
       'source_inventory_sha256':INVENTORY_SHA,'crest_policy_sha256':POLICY_SHA,
       'consumer_source_sha256':CONSUMER_SHA})
    result['diagnostics']={'ANY_populations':any_report,
        'ANY_semantics':'diagnostic only; independent populations and overlap are not acceptance gates. Frozen global ALL gates remain unchanged.'}
    result['status']='PASS_INCREMENTAL_NONREGRESSION' if all(result['gates'].values()) else 'FAIL_INCREMENTAL_NONREGRESSION'
    return result


def load_solution_aux(path):
    with np.load(path,allow_pickle=False) as z:
        b=np.asarray(z['B_values_float32'],np.float32);bounds=np.asarray(z['bounds_float32_inward'],np.float32)
        solver=np.asarray(z['solver_bounds_float32'],np.float32);guard=np.asarray(z['guard_rc'],np.int32)
    return b,bounds,solver,guard


def shape_new_gates(shape_report):
    return dict(shape_report['gates'])


def self_test():
    policy=load_module('ev93_crest_policy_test',POLICY,POLICY_SHA)
    return {'scalar_policy':scalar_formula_fixture(policy),'compose':compose_fixture(),
            'ledger':ledger_fixture(),'production_negative_paths':production_path_negative_fixtures(policy)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--receipt',type=Path)
    ap.add_argument('--output',type=Path,default=EXT/'composite-review.json')
    ap.add_argument('--progress-log',type=Path)
    args=ap.parse_args()
    if args.self_test:
        print(json.dumps({'status':'FIXTURES_PASS','fixtures':self_test()},sort_keys=True));return
    if not args.receipt:ap.error('--receipt required outside --self-test')
    try:
        report=validate_composite(args.receipt,args.output,args.progress_log)
    except Exception as exc:
        report={'status':'ERROR_COMPOSITE_CONSUMER','gates':{},'error':repr(exc),'traceback':traceback.format_exc()}
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'false_gates':[k for k,v in report.get('gates',{}).items() if not v],
                      'error':report.get('error'),'output':str(args.output)},sort_keys=True),flush=True)
    if report['status']=='ERROR_COMPOSITE_CONSUMER':raise SystemExit(2)
    if not all(report['gates'].values()):raise SystemExit(1)


if __name__=='__main__':main()
