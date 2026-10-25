from pathlib import Path
from collections import Counter
import hashlib,json

G=Path('E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
LEDGER=G/'preflight-segment02/window-ledger.jsonl'
EXPECTED='63af108d80d7232d8b919c3940da64e76839d8f0d4c74d42ca8d569117913d3a'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    if sha(LEDGER)!=EXPECTED:raise AssertionError('final preflight ledger changed')
    records=[json.loads(x) for x in LEDGER.read_text(encoding='utf-8').splitlines()]
    if records[-1].get('status')!='COMPLETE_READONLY_PREFLIGHT':raise AssertionError('incomplete')
    queue=json.loads((G/'queue/queue.json').read_text(encoding='utf-8'))
    first=[x for x in queue['seeds'] if x['state']=='first_layer']
    if len(first)!=703:raise AssertionError('wrong queue')
    done={}
    for r in records:
        if r.get('event')!='window' or r['state']=='PREFLIGHT_ERROR':continue
        qid=r['queue_id']
        if qid in done:raise AssertionError('duplicate completed result')
        done[qid]=r
    if set(done)!=set(range(703)):raise AssertionError('missing or unknown result')
    states=Counter();reason_counts=Counter();unknown=Counter();populations={}
    nodes_all=set();free_all=set();free_counts=[];details=[];examples=[]
    for qid,row in sorted(done.items()):
        seed=first[qid];p=LEDGER.parent/row['detail_path'];raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row['detail_sha256']:raise AssertionError('detail mismatch')
        d=json.loads(raw);pre=d['preflight'];center=[seed['row'],seed['col']]
        if d['queue_id']!=qid or d['seed_id']!=seed['seed_id'] or d['center_rc']!=center or d['window17']!=seed['window17']:
            raise AssertionError('queue/detail mismatch')
        if pre['center_rc']!=center or pre['status']!=row['state']:raise AssertionError('status/center mismatch')
        r,c=center
        if pre['window']!=[r-8,r+9,c-8,c+9] or pre['core']!=[r-6,r+7,c-6,c+7]:raise AssertionError('window convention mismatch')
        state=row['state'];states[state]+=1
        population=seed.get('population',seed.get('category','unspecified'))
        populations.setdefault(str(population),Counter())[state]+=1
        domain=pre['domain'];guard={tuple(x) for x in pre['guard_d8']['guard_rc']}
        nodes={tuple(x) for x in domain['eligible_after_face_freeze_nodes']};free=nodes-guard
        if not guard<=nodes or len(free)!=pre['guard_d8']['free_count']:raise AssertionError('guard/free mismatch')
        if nodes_all&nodes:raise AssertionError('overlapping variable domains')
        nodes_all.update(nodes)
        reasons=[]
        if state=='PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW':
            free_all.update(free);free_counts.append(len(free))
        else:
            if domain['focus_status']!='variable':reasons.append('focus_fixed')
            if not domain['both_axes_box_feasible_for_25_percent']:reasons.append('focus_box_does_not_prove_25pct_both_axes')
            if pre['box_interval_audit']['empty_nodes']:reasons.append('empty_interval')
            if pre['box_interval_audit']['baseline_outside_nodes']:reasons.append('B_outside_interval')
            if not free:reasons.append('no_free_variables')
            if pre['unknown_lower_unresolved_count']:reasons.append('unknown_faces_not_certified_at_lower_bound')
            if domain['F_partial_triangles_touching_originally_eligible_nodes']:reasons.append('partial_F')
            for reason in reasons:reason_counts[reason]+=1
            examples.append({'queue_id':qid,'seed_id':seed['seed_id'],'center_rc':center,'state':state,'reasons':reasons})
        unknown['unresolved_intersections']+=pre['unknown_lower_unresolved_count']
        details.append({'queue_id':qid,'path':str(p.resolve()),'sha256':row['detail_sha256']})
    result={'status':'PASS_PREFLIGHT_INVENTORY_NOT_TERRAIN_ACCEPTANCE','ledger_sha256':EXPECTED,
        'windows':703,'state_counts':dict(states),'by_population':{k:dict(v) for k,v in populations.items()},
        'nonready_reasons_nonexclusive':dict(reason_counts),'nonready_windows':examples,
        'disjoint_domain_vertices':len(nodes_all),'ready_free_vertices':len(free_all),
        'ready_free_min':min(free_counts),'ready_free_max':max(free_counts),
        'unknown':dict(unknown),'detail_readset':details,
        'limits':'Readonly separable preflight. No coupled solve, terrain correction, engine or map acceptance.'}
    out=Path(__file__).with_name('preflight-inventory.json')
    with out.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:result[k] for k in ('status','windows','state_counts','by_population','nonready_reasons_nonexclusive','disjoint_domain_vertices','ready_free_vertices','ready_free_min','ready_free_max')},indent=2))
    print('sha256='+sha(out))

if __name__=='__main__':main()
