from __future__ import annotations
import importlib.util, json, hashlib, itertools, math, sys
from pathlib import Path
import numpy as np

ROOT=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/G/wet-bank-pilot')
HERE=ROOT/'postsolve-consumer/float32-neighborhood-v1'
EXEC=HERE/'executor.py'
OUT=HERE/'real-enumeration-01/compatibility-diagnostic.json'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

spec=importlib.util.spec_from_file_location('f32_neighborhood_executor',EXEC)
ex=importlib.util.module_from_spec(spec); sys.modules[spec.name]=ex; spec.loader.exec_module(ex)
data=ex.load_real_inputs()
baseline_control,raw_control=ex.verify_controls(data)
controls={'baseline_positive_control':baseline_control,'known_raw_negative_control':raw_control}
if not controls['baseline_positive_control']['baseline_116_crossings']:
    raise RuntimeError('baseline direct crossing control failed')
if controls['known_raw_negative_control']['all_116_direct_crossings']:
    raise RuntimeError('known raw negative control unexpectedly passes')
target=np.asarray(data['target_rc'],dtype=np.int32)
local_target=target-np.asarray(ex.ORIGIN,dtype=np.int32)
idx_by_local={tuple(rc):i for i,rc in enumerate(local_target.tolist())}
tidx=np.asarray(data['target_idx'],dtype=np.int32)
target_x=data['raw_x'][tidx]
target_lo=data['lo'][tidx]; target_hi=data['hi'][tidx]
options=ex.build_neighbor_options(target_x,target_lo,target_hi)
B=data['closed']
# Start with exact float32 choices that retain the physical inward box.
domains={}
for i,rc in enumerate(target.tolist()):
    lo,hi=np.float32(target_lo[i]),np.float32(target_hi[i])
    domains[i]={j for j,v in enumerate(options[i]) if np.float32(lo)<=v<=np.float32(hi)}
# Apply all P/F sign-only constraints as unary restrictions to their touched variables.
unary_sign_removed=[]
for si,ss in enumerate(data['sign_specs']):
    ti=idx_by_local.get(tuple(ss.local_rc))
    if ti is None: continue
    for j in tuple(domains[ti]):
        g=B.copy(); g[tuple(local_target[ti])]=options[ti][j]
        if not ex.direct_signs_pass(g,(),(ss,)):
            domains[ti].remove(j); unary_sign_removed.append({'sign_spec':si,'target_index':ti,'option':j})
if any(not d for d in domains.values()): raise RuntimeError('empty unary domain before crossing AC-3')
base_domains={i:set(v) for i,v in domains.items()}

crossings=[]; binary=[]; unary_cross=[]; fixed_only=[]
for ci,cs in enumerate(data['cross_specs']):
    ia=idx_by_local.get(tuple(cs.local_a)); ib=idx_by_local.get(tuple(cs.local_b))
    da=sorted(base_domains[ia]) if ia is not None else [None]
    db=sorted(base_domains[ib]) if ib is not None else [None]
    allowed=[]
    tested=[]
    for oa in da:
      for ob in db:
        g=B.copy()
        if ia is not None: g[tuple(local_target[ia])]=options[ia][oa]
        if ib is not None: g[tuple(local_target[ib])]=options[ib][ob]
        passed=ex.direct_signs_pass(g,(cs,),()) and ex.direct_crossings_pass(g,(cs,))
        tested.append({'a_option':oa,'b_option':ob,'pass':bool(passed)})
        if passed: allowed.append((oa,ob))
    rec={'index':ci,'key':list(cs.key) if isinstance(cs.key,tuple) else cs.key,
         'surface':cs.surface,'cell':list(cs.cell_rc),'edge_rc':[list(cs.edge_rc[0]),list(cs.edge_rc[1])],
         'target_indices':[ia,ib],'tested_pairs':len(tested),'allowed_pairs':len(allowed),
         'allowed_option_pairs':[list(x) for x in allowed]}
    crossings.append(rec)
    if ia is None and ib is None:
        fixed_only.append({'index':ci,'passed':bool(allowed)})
        if not allowed: raise RuntimeError(f'fixed-only crossing failed B at record {ci}')
    elif ia is not None and ib is not None and ia != ib:
        binary.append({'record':ci,'i':ia,'j':ib,'allowed':set(allowed)})
    else:
        i=ia if ia is not None else ib
        good={oa if ia is not None else ob for oa,ob in allowed}
        removed=sorted(domains[i]-good)
        domains[i] &= good
        unary_cross.append({'record':ci,'target_index':i,'allowed_options':sorted(good),'removed_options':removed})
        if not domains[i]:
            OUT.parent.mkdir(parents=True,exist_ok=True)
            raise RuntimeError(f'unary crossing emptied domain at record {ci}, target {i}')

# AC-3 on the binary constraints only; unary/bounds/sign filtering already applied.
queue=[]
for c in binary:
    queue.extend([(c['i'],c['j'],c['record']),(c['j'],c['i'],c['record'])])
removed_log=[]
while queue:
    xi,xj,ri=queue.pop(0)
    c=next(c for c in binary if c['record']==ri)
    relation=c['allowed']
    if xi==c['i']:
        keep={a for a in domains[xi] if any((a,b) in relation for b in domains[xj])}
    else:
        keep={b for b in domains[xi] if any((a,b) in relation for a in domains[xj])}
    removed=domains[xi]-keep
    if removed:
        domains[xi]=keep
        removed_log.append({'target_index':xi,'rc':target[xi].tolist(),'removed_options':sorted(removed),'against_rc':target[xj].tolist(),'record':ri})
        if not keep:
            break
        for c2 in binary:
            if c2['record']==ri: continue
            if c2['i']==xi and c2['j']!=xj: queue.append((c2['j'],xi,c2['record']))
            elif c2['j']==xi and c2['i']!=xj: queue.append((c2['i'],xi,c2['record']))

result={
 'schema':'ev94.wet-bank-f32-neighbor-compatibility.v1',
 'status':'PAIRWISE_COMPATIBILITY_AND_AC3_DIAGNOSTIC',
 'source_executor_sha256':sha(EXEC),
 'enumeration_receipt_sha256':sha(HERE/'real-enumeration-01/receipt.json'),
 'source_inputs':{str(p):sha(p) for p in [ex.PREP,ex.SOL,ex.BASE,ex.P_PATH,ex.F_PATH,ex.DESIGN,ex.FRACTION_DIAG]},
 'controls':controls,
 'target_nodes_rc':target.tolist(),
 'option_steps':[-1,0,1],
 'initial_box_and_sign_domains':{str(i):sorted(v) for i,v in base_domains.items()},
 'unary_sign_removed':unary_sign_removed,
 'crossing_record_count':len(crossings),
 'crossing_records':crossings,
 'empty_compatibility_records':[r['index'] for r in crossings if r['allowed_pairs']==0],
 'binary_constraints':len(binary),
 'unary_crossing_constraints':unary_cross,
 'fixed_only_controls':fixed_only,
 'ac3':{'empty_domains':[{'index':i,'rc':target[i].tolist()} for i,d in domains.items() if not d],
        'remaining_domains':{str(i):sorted(d) for i,d in domains.items()},
        'removed_log':removed_log,'arc_consistency_reached':not any(not d for d in domains.values())},
 'interpretation':'Pairwise exact shoreline crossing compatibility only, with bounds and unary PF sign constraints. Does not include D8, face cones, or closure energy.'}
result['source_readset_start']=data['source_start']
result['source_readset_end']=ex.sha_map(ex.source_paths())
OUT.write_text(json.dumps(result,indent=2,allow_nan=False)+chr(10),encoding='utf-8')
print(json.dumps({'output':str(OUT),'sha256':sha(OUT),'crossing_records':len(crossings),'empty_edges':result['empty_compatibility_records'],'binary_constraints':len(binary),'ac3_empty':result['ac3']['empty_domains'],'domains':result['ac3']['remaining_domains'],'elapsed_scope':'pairwise only'},indent=2))





