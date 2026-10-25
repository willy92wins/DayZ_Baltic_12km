#!/usr/bin/env python
"""Independent v2 consumer for selected EV93 whole-window units."""
import argparse, hashlib, importlib.util, json, math, os, sys, time, traceback
from pathlib import Path
import numpy as np
G=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010'); EXT=G/'crest-extension'; L=G/'fairing-layer1'
BASE=Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')
PREPARED=L/'prepared.json'; LEGACY_RECEIPT=L/'authoring.json'; LEGACY_CANDIDATE=L/'candidate-terrain.npz'
INV=EXT/'reuse-source-inventory.json'; INV_SHA='8b8b9a6e525ee3bd8df59bef18784bafdc921e295ec9ebdb7043eefa4317b042'
PLAN=EXT/'EXECUTION_PLAN_V2.md'; PLAN_SHA='8a4afc1e26dc0d816ade9454ee4f4e31c185b03a56c8a9ef5005f468d0cff9b0'
AUTHOR=EXT/'author_reused_directions.py'; AUTHOR_SHA='653900438d832d32f118ea5300850eeaf5e9a0cd4e3f49e7e3e1e64aaa862c2a'
HELPER=EXT/'verify_composite.py'; HELPER_SHA='88EDD6B54D9C7CF05BFF546D66C2AD0074AE939E903043790EEAE5D42D8ECE24'
EV=G/'consumer-global/verify_layer.py'; EV_SHA='33050881caaf5e75f288d4122222c15eb326bf146c28a4c723760564457b3dc2'
POLICY=G/'crest-policy/crest_policy.py'; POLICY_SHA='32ab6e0111886907315a0360322df0ff958f80bebcd6493254a2f0f144a3829e'
SHAPE=Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/next-method-consumer/shape_contract.py'); SHAPE_SHA='8cd9d0fbea03c05e5ae53a31676d79ec2364be83c055213446f6c8599245d533'
EV92=Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev92-damped/consumer/verify_ev92.py'); EV92_SHA='87b5ee5ee95318f1a8026c4a7459aa06d27c9b69db80f34ad25149293d5fc1df'
ANY=G/'consumer-global/diagnose_any_populations.py'; ANY_SHA='5d35cf1a80fa57673a51c404d8a8f3dddb8403f6c86045c2cea3aa2775b6de93'
KNOWN_FAIL=G/'consumer-global/runs/attempt-04/ev93-review.json'; KNOWN_FAIL_SHA='ed9a071d359dc446b5146a255c3ab9f15481c92e24c2169b6da47dd4ad27c0ec'
KNOWN_LEGACY='37e6d4bd195ee8576bc483a6c24e89cede536d916c2b041d8a6bdc98b13269f3'; FALSE_GATES={'physical_support_holes_lt_1e_7m2','visible_support_holes_lt_1e_7m2'}
SELECTOR=G/'compound-selection/selector.py'; START=0.0
INDEX_MANIFEST=G/'ev93-face-index/runs/20261010T092417Z-63d4cec3/manifest.json'
INDEX_VERIFICATION=G/'review-independent/runs/attempt-01/verification.json'
INDEX_VERIFICATION_SHA='b498e7d68835b199399655451e5e01ac81acb3149dbb9bf882b94858141521d4'
OUTPUT_DEFAULT=EXT/'consumer-runs'

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def cj(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def jload(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def loadmod(n,p,w=None):
 got=sha(p)
 if w and got.lower()!=w.lower():raise AssertionError(f'helper SHA mismatch {p}: {got} != {w}')
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def prog(p,phase,event,**x):
 row={'phase':phase,'event':event,'elapsed_s':round(time.perf_counter()-START,3),**x};line=json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False);print(line,flush=True)
 if p:
  with Path(p).open('a',encoding='utf-8',newline='\n') as f:f.write(line+'\n');f.flush();os.fsync(f.fileno())
def loadctx():
 old=loadmod('ev93_helper_v1',HELPER,HELPER_SHA)
 layer=loadmod('ev93_layer_v2',EV,EV_SHA)
 geom=loadmod('ev93_geom_v2',layer.EV88,layer.PINS[str(layer.EV88)])
 ev91=loadmod('ev93_ev91_v2',layer.EV91,layer.PINS[str(layer.EV91)]); ev87=loadmod('ev93_ev87_v2',layer.EV87,layer.PINS[str(layer.EV87)])
 cv=loadmod('ev93_cv_v2',layer.CV,layer.PINS[str(layer.CV)]); shape=loadmod('ev93_shape_v2',SHAPE,SHAPE_SHA)
 ev92=loadmod('ev93_ev92_v2',EV92,EV92_SHA); idx=loadmod('ev93_index_v2',layer.INDEX_SOURCE,layer.PINS[str(layer.INDEX_SOURCE)]);cv.ev=ev87
 policy=loadmod('ev93_policy_v2',POLICY,POLICY_SHA);return old,layer,geom,ev91,ev87,cv,shape,ev92,idx,policy
def known_fail(path,digest):
 if Path(path).resolve()!=KNOWN_FAIL.resolve() or digest!=KNOWN_FAIL_SHA or sha(path)!=KNOWN_FAIL_SHA:raise AssertionError('source FAIL report pin mismatch')
 d=jload(path);g=d.get('gates',{})
 if d.get('status')!='FAIL_INCREMENTAL_NONREGRESSION' or {k for k,v in g.items() if v is False}!=FALSE_GATES:raise AssertionError('source report is not the exact reviewed two-gate FAIL')
 i=d['information']
 if i.get('candidate_sha256')!=KNOWN_LEGACY or i.get('accepted_windows')!=340 or i.get('changed_vertices')!=20201:raise AssertionError('source FAIL report does not identify frozen legacy composite')
 return d
def validate_pool(pool):
 if pool.get('schema')!='ev93.compound-pool.v1' or pool.get('status')!='AUTHORED_QUARANTINED':raise AssertionError('compound pool status/schema mismatch')
 if pool.get('expected_counts')!={'legacy_accepted':340,'crest_targets':228}:raise AssertionError('compound pool count contract mismatch')
 rows=pool.get('rows',[]); legacy=[r for r in rows if r.get('origin')=='legacy'];crest=[r for r in rows if r.get('origin')=='crest']
 if len(rows)!=568 or len(legacy)!=340 or len(crest)!=228 or len({r.get('unit_id') for r in rows})!=568:raise AssertionError('pool must contain 568 unique origin-namespaced rows')
 for r in rows:
  o=r['origin'];q=int(r['queue_id'])
  if r.get('unit_id')!=f'{o}:{q}' or int(r.get('source_qid',-1))!=q:raise AssertionError('pool unit/source identity mismatch')
  if o=='legacy' and r.get('state')!='accepted':raise AssertionError('legacy source state changed')
  if o=='crest' and r.get('state') not in ('derived_quarantined','rejected_policy'):raise AssertionError('crest row is not quarantined')
 return rows
def validate_selection(poolrows,s):
 if s.get('schema')!='ev93.compound-selection.v1' or s.get('status')!='SELECTED':raise AssertionError('selection is not terminal SELECTED')
 units=s.get('units',[])
 if len(units)!=len(poolrows):raise AssertionError('selection rows incomplete')
 by_id={u.get('unit_id'):u for u in units}
 if len(by_id)!=len(units):raise AssertionError('selection contains duplicate unit rows')
 for p in poolrows:
  u=by_id.get(p.get('unit_id'))
  if u is None:raise AssertionError('selection unit row missing from pool')
  if any(u.get(k)!=p.get(k) for k in ('unit_id','origin','queue_id','source_qid')):raise AssertionError('selection unit differs from pool')
  if Path(u.get('source_artifact_path','')).resolve()!=Path(p['artifact_path']).resolve() or u.get('source_artifact_sha256')!=p['artifact_sha256']:raise AssertionError('selection artifact link differs from pool')
  st=u.get('selection_status');ls=u.get('local_status')
  if st not in ('retained','excluded_local','excluded_support') or ls not in ('PASS','FAIL'):raise AssertionError('invalid selection state')
  if (st=='retained' or st=='excluded_support') and ls!='PASS':raise AssertionError('retained/support-excluded row fails local')
  if st=='excluded_local' and ls!='FAIL':raise AssertionError('local exclusion lacks failure')
 ids=[u['unit_id'] for u in units];ret=s.get('retained_unit_ids',[]);exc=s.get('excluded_unit_ids',[])
 if len(set(ids))!=len(ids) or set(ids)!={p['unit_id'] for p in poolrows}:raise AssertionError('selection identity set incomplete')
 if len(set(ret))!=len(ret) or len(set(exc))!=len(exc) or set(ret)!={u['unit_id'] for u in units if u['selection_status']=='retained'} or set(exc)!={u['unit_id'] for u in units if u['selection_status']!='retained'}:raise AssertionError('retained/excluded lists not exhaustive')
 return units
def validate_pool_sources(pool,pool_path,selection):
 rep=pool.get('source_global_report',{});known_fail(rep.get('path'),rep.get('sha256'))
 if Path(pool.get('base',{}).get('path','')).resolve()!=BASE.resolve() or sha(BASE)!=pool['base']['sha256']:raise AssertionError('pool baseline pin mismatch')
 ls=pool['legacy_source'];cs=pool['crest_source']
 for a,b in [('prepared_path','prepared_sha256'),('receipt_path','receipt_sha256'),('ledger_path','ledger_sha256')]:
  if sha(ls[a])!=ls[b]:raise AssertionError(f'legacy source pin mismatch {a}')
 for a,b in [('receipt_path','receipt_sha256'),('target_rows_path','target_rows_sha256'),('ledger_path','ledger_sha256')]:
  if sha(cs[a])!=cs[b]:raise AssertionError(f'crest source pin mismatch {a}')
 rec=jload(cs['receipt_path'])
 if (rec.get('schema')!='ev93.crest-extension.quarantine-receipt.v3' or
     rec.get('status')!='QUARANTINE_POOL_READY_FOR_SELECTOR' or
     rec.get('author_source_sha256')!=AUTHOR_SHA or rec.get('execution_plan_sha256')!=PLAN_SHA):
  raise AssertionError('quarantine receipt not terminal v3 or source-pinned')
 target_refs=[json.loads(x) for x in Path(cs['target_rows_path']).read_text('utf-8').splitlines() if x.strip()]
 if target_refs!=rec.get('pool_targets'):raise AssertionError('target refs differ from quarantine receipt')
 if selection.get('compound_pool_path') is None or Path(selection['compound_pool_path']).resolve()!=Path(pool_path).resolve():raise AssertionError('selection pool path mismatch')
 if selection.get('compound_pool_sha256')!=sha(pool_path):raise AssertionError('selection pool SHA mismatch')
 if selection.get('selection_plan_path') is None or Path(selection['selection_plan_path']).resolve()!=PLAN.resolve() or selection.get('plan_sha256')!=PLAN_SHA:raise AssertionError('selection plan pin mismatch')
 if Path(selection.get('selector_source_path','')).resolve()!=SELECTOR.resolve() or sha(SELECTOR)!=selection.get('selector_sha256'):raise AssertionError('selector source pin mismatch')
 if Path(selection.get('index_manifest_path','')).resolve()!=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/ev93-face-index/runs/20261010T092417Z-63d4cec3/manifest.json').resolve():raise AssertionError('selection face-index path mismatch')
 return rec

def isolated_legacy_gate(layer,geom,ev87,shape,ev92,base,patch,detail):
 grid=base.copy();grid[tuple(patch['nodes'].T)]=patch['final']
 report=layer.verify_local_windows(geom,ev87,shape,ev92,base,grid,[patch],{int(patch['queue_id']):detail})
 metrics=report['metrics'][0]
 gates={'ev92_complete_local_contract':bool(report['gates'][int(patch['queue_id'])])}
 gates.update({str(k):bool(v) for k,v in metrics.items() if isinstance(v,bool)})
 gates.update({f"shape:{k}":bool(v) for k,v in metrics['shape']['gates'].items()})
 return gates,metrics

def match_local_status(unit,gates):
 expect=unit.get('local_gates')
 if not isinstance(expect,dict) or set(expect)!=set(gates):raise AssertionError(f'local gate names mismatch {unit["unit_id"]}')
 if any(bool(expect[k])!=bool(v) for k,v in gates.items()):raise AssertionError(f'local gate values mismatch {unit["unit_id"]}')
 actual='PASS' if gates and all(gates.values()) else 'FAIL'
 if unit.get('local_status')!=actual:raise AssertionError(f'local status differs from independent check {unit["unit_id"]}')
 return actual

def local_reused_gates_v2(geom,layer,ev87,derive_rule_fn,canonical_sha_fn,shape,policy,base,candidate,
                          invrow,result_row,source_result,nodes,source_b,bounds,
                          solver_bounds,guard,direction,final,stencils,detail):
 """Explicit-owner copy of the frozen local gate math; no dynamic API facade."""
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
 witness_exact=canonical_sha_fn(witnesses)==canonical_sha_fn(pre['guard_d8']['descent_witnesses'])
 witness_pass=all(candidate[tuple(map(int,w['center']))]>=candidate[tuple(map(int,w['witness']))] for w in witnesses)
 d8_hash=(source_result.get('d8_matrix_sha256_f64')==pre['guard_d8']['descent_matrix_sha256_f64'] and
          source_result.get('d8_rhs_sha256_f64')==pre['guard_d8']['descent_rhs_sha256_f64'])
 records=geom.stencil_records(window=(r0,r1,c0,c1),core=(cr0,cr1,cc0,cc1),variables=declared_set)
 expected_keys=[(str(x['key'][0]),int(x['key'][1]),int(x['key'][2])) for x in records]
 stencil_exact=len(stencils)==len(expected_keys) and len(set(stencils))==len(stencils) and set(stencils)==set(expected_keys)
 bcard,hcard,moments,rule=derive_rule_fn(policy,invrow,base,nodes,stencils,direction,sha(PREPARED))
 scalar_exact=(canonical_sha_fn(result_row.get('scalar_rule'))==canonical_sha_fn(rule) and
               float(result_row.get('alpha'))==float(rule['alpha_midpoint']))
 basevals=np.asarray(base[tuple(nodes.T)],np.float32)
 expected_final=(basevals.astype(np.float64)+float(rule['alpha_midpoint'])*
                 (direction.astype(np.float64)-basevals.astype(np.float64))).astype(np.float32)
 final_exact=np.array_equal(expected_final,final) and np.array_equal(candidate[tuple(nodes.T)],final)
 focus=policy.evaluate_focus_after(base,candidate,focus_rc=(r,c))
 crop0,crop1,col0,col1=r0-1,r1+1,c0-1,c1+1
 base_crop=base[crop0:crop1,col0:col1].copy();candidate_crop=candidate[crop0:crop1,col0:col1].copy()
 shape_raw=shape.evaluate_shape(base_crop,candidate_crop,(1,18,1,18),(r-crop0,c-col0))
 shape_new=policy.replace_focus_gate(shape_raw,focus)
 energy_b=layer.stencil_energy_fraction(base,stencils);energy_h=layer.stencil_energy_fraction(candidate,stencils)
 collar_keys={tuple((str(x['key'][0]),int(x['key'][1]),int(x['key'][2]))) for x in records if x['collar']}
 collar=[x for x in stencils if x in collar_keys]
 collar_b=layer.stencil_energy_fraction(base,collar);collar_h=layer.stencil_energy_fraction(candidate,collar)
 local_b=geom.local_mesh_angles(base.astype(np.float64),(r,c),radius=2)
 local_h=geom.local_mesh_angles(candidate.astype(np.float64),(r,c),radius=2)
 hinge_reduction=float(local_b['max_incident_hinge_deg']-local_h['max_incident_hinge_deg'])
 angles_b=dict(ev87.edge_angles(base_crop.astype(np.float64)))
 angles_h=dict(ev87.edge_angles(candidate_crop.astype(np.float64)))
 collar_mask=np.zeros((r1-r0,c1-c0),bool);collar_mask[:2,:]=1;collar_mask[-2:,:]=1;collar_mask[:,:2]=1;collar_mask[:,-2:]=1
 bw=base[r0:r1,c0:c1].astype(np.float64);hw=candidate[r0:r1,c0:c1].astype(np.float64)
 collar_angles_b=dict(ev87.edge_angles(bw));collar_angles_h=dict(ev87.edge_angles(hw))
 collar_angle=[]
 for kind,ab in collar_angles_b.items():
  ah=collar_angles_h[kind];mask=ev87.incident_any(collar_mask,kind)
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

def verify_crest_target(old,policy,ctx,invrow,row,base,prepared_sha,details):
 layer,geom,ev91,ev87,cv,shape,ev92,indexmod=ctx
 qid=int(invrow['queue_id']);src=jload(invrow['result_path'])
 for path,key in ((invrow['result_path'],'result_sha256'),(invrow['solution_path'],'solution_sha256'),(invrow['attempt_marker_path'],'attempt_marker_sha256')):
  if sha(path)!=invrow[key]:raise AssertionError(f'crest source hash mismatch q{qid}')
 nodes,stencils,direction=layer.validate_attempt_artifact(qid,src,base)
 nodes=np.asarray(nodes,np.int32);direction=np.asarray(direction,np.float32)
 stencils=[(str(x[0]),int(x[1]),int(x[2])) for x in stencils]
 if int(row.get('queue_id',-1))!=qid or int(row.get('target_queue_id',-1))!=qid or int(row.get('source_qid',-1))!=qid:raise AssertionError('target qid binding differs')
 checks={'source_result_path':invrow['result_path'],'source_result_sha256':invrow['result_sha256'],
 'source_solution_path':invrow['solution_path'],'source_solution_sha256':invrow['solution_sha256'],
 'source_marker_path':invrow['attempt_marker_path'],'source_marker_sha256':invrow['attempt_marker_sha256'],
 'direction_sha256':invrow['direction_float32_le_sha256'],'stencil_set_sha256':invrow['stencil_set_sha256']}
 for k,v in checks.items():
  if row.get(k)!=v:raise AssertionError(f'crest provenance mismatch q{qid}: {k}')
 if row.get('state')=='rejected_policy':
  try:old.derive_rule(policy,invrow,base,nodes,stencils,direction,prepared_sha)
  except policy.PolicyReject as e:
   if row.get('policy_rejection_code')!=e.code:raise AssertionError('policy rejection code mismatch')
  else:raise AssertionError(f'policy rejection is not reproducible q{qid}')
  if 'alpha' in row or 'final_float32' in row:raise AssertionError('policy rejection includes delta')
  return None,{'policy_rule_available':False},None
 if row.get('state')!='derived_quarantined':raise AssertionError(f'unknown crest target state q{qid}')
 bcard,hcard,moments,rule=old.derive_rule(policy,invrow,base,nodes,stencils,direction,prepared_sha)
 old.verify_scalar_record(row,policy,rule,moments);alpha=float(rule['alpha_midpoint'])
 bvals=np.asarray(base[tuple(nodes.T)],np.float32)
 final=(bvals.astype(np.float64)+alpha*(direction.astype(np.float64)-bvals.astype(np.float64))).astype(np.float32)
 if not np.array_equal(np.asarray(row.get('variables_rc'),np.int32),nodes):raise AssertionError(f'target nodes differ q{qid}')
 if not np.array_equal(np.asarray(row.get('B_values_float32'),np.float32),bvals):raise AssertionError(f'target baseline vector differs q{qid}')
 if not np.array_equal(np.asarray(row.get('direction_float32'),np.float32),direction):raise AssertionError(f'target direction differs q{qid}')
 if not np.array_equal(np.asarray(row.get('final_float32'),np.float32),final):raise AssertionError(f'target final float32 differs q{qid}')
 result=src; b,bounds,solver,guard=old.load_solution_aux(Path(invrow['solution_path']))
 patch={'queue_id':qid,'result':result,'nodes':nodes,'B':b,'bounds':bounds,'solver_bounds':solver,'guard':guard,'direction':direction,'final':final,'stencils':list(stencils)}
 grid=base.copy();grid[tuple(nodes.T)]=final
 gates,metrics=local_reused_gates_v2(geom,layer,ev87,old.derive_rule,old.canonical_sha,shape,policy,
    base,grid,invrow,row,result,nodes,b,bounds,solver,guard,direction,final,list(stencils),details[qid])
 return patch,{k:bool(v) for k,v in gates.items()},metrics
def inv_pins():
 d=jload(INV);yield from d.get('source_pins',{}).items()

def compose_retained(base,retained_patches):
 candidate=np.asarray(base,np.float32).copy();owner={};changed_nodes={}
 for unit,patch in retained_patches:
  uid=unit['unit_id'];nodes=np.asarray(patch['nodes'],np.int32);vals=np.asarray(patch['final'],np.float32)
  if nodes.ndim!=2 or nodes.shape[1]!=2 or len(nodes)!=len(vals):raise AssertionError(f'invalid retained node/value shape {uid}')
  local=[]
  for rc,val in zip(map(tuple,nodes.tolist()),vals.tolist()):
   if rc in owner:raise AssertionError(f'retained node owner collision {rc}: {owner[rc]} / {uid}')
   owner[rc]=uid;candidate[rc]=np.float32(val)
   if candidate[rc]!=base[rc]:local.append(rc)
  digest=cj([list(rc) for rc in sorted(local)])
  if unit.get('changed_vertices')!=len(local) or unit.get('changed_vertices_sha256')!=digest:
   raise AssertionError(f'selection changed-node inventory differs {uid}')
  changed_nodes[uid]=local
 return candidate,owner,changed_nodes

def physical_l32(base,retained_patches,envelope_fn):
 # The patch list is intentionally every retained origin; envelope_fn reads
 # each patch's physical `bounds`, never its solver-only fixed guard bounds.
 return envelope_fn(base,[patch for _,patch in retained_patches])

def pilot_local_wrapper_fixture():
 # Real EV92→EV90 pilot, wired through this consumer's isolated-window adapter.
 old,layer,geom,ev91,ev87,cv,shape,ev92,indexmod,policy=loadctx()
 bnd=geom.checked_sources()['B'];base=np.asarray(bnd['heights'],np.float32)
 prepared=jload(layer.PILOT_PREPARED)
 with np.load(layer.PILOT_DIRECTION,allow_pickle=False) as z:direction_grid=np.asarray(z['heights'],np.float32)
 with np.load(layer.PILOT_FINAL,allow_pickle=False) as z:final_grid=np.asarray(z['heights'],np.float32)
 nodes=np.asarray(prepared['variables_rc'],np.int32);bounds=np.asarray(prepared['bounds_float32_inward'],np.float32)
 solver=np.asarray(prepared['solver_bounds_float32'],np.float32);guard=np.asarray(prepared['guard_rc'],np.int32)
 stencils=[tuple((str(x[0]),int(x[1]),int(x[2]))) for x in prepared['stencils']]
 direction=direction_grid[tuple(nodes.T)].copy();final=final_grid[tuple(nodes.T)].copy()
 pre={'window':list(geom.WINDOW),'core':list(geom.CORE),
      'domain':{'eligible_after_face_freeze_nodes':nodes.tolist(),
                'final_float32_intervals_for_eligible_nodes':[{'node_rc':n.tolist(),'interval_float32_inward_m':v.tolist()} for n,v in zip(nodes,bounds)]},
      'guard_d8':{'guard_rc':guard.tolist(),'descent_witnesses':prepared['witnesses'],
                  'descent_matrix_sha256_f64':prepared['descent_matrix_sha256_f64'],
                  'descent_rhs_sha256_f64':prepared['descent_rhs_sha256_f64']}}
 detail={'queue_id':0,'seed_id':0,'center_rc':[840,370],
         'window17':[geom.WINDOW[0],geom.WINDOW[2],geom.WINDOW[1],geom.WINDOW[3]],'preflight':pre}
 b_energy=[str(x) for x in layer.stencil_energy_moments_fraction(base,base,stencils)]
 h_energy=[str(x) for x in layer.stencil_energy_moments_fraction(base,final_grid,stencils)]
 result={'queue_id':0,'center_rc':[840,370],'state':'accepted','solve_calls':1,
         'alpha':float(prepared['alpha']),'scalar_rule':prepared['scalar_rule'],
         'd8_witnesses':prepared['witnesses'],
         'd8_matrix_sha256_f64':prepared['descent_matrix_sha256_f64'],
         'd8_rhs_sha256_f64':prepared['descent_rhs_sha256_f64'],
         'energy_B_fraction':b_energy,'energy_H_fraction':h_energy}
 patch={'queue_id':0,'result':result,'nodes':nodes,'B':base[tuple(nodes.T)].copy(),'bounds':bounds,
        'solver_bounds':solver,'guard':guard,'direction':direction,'final':final,'stencils':stencils}
 gates,metrics=isolated_legacy_gate(layer,geom,ev87,shape,ev92,base,patch,detail)
 if not gates or not all(gates.values()):raise AssertionError(f'our isolated legacy adapter failed the real pilot: {metrics}')
 return {'real_EV92_pilot_local_gates':gates,'real_EV92_pilot_pass':True}

def real_legacy_q1_fixture():
 # A second real-path smoke uses source legacy qid=1, not the EV92 pilot fixture.
 layer=loadmod('ev93_fixture_layer_q1',EV,EV_SHA)
 geom=loadmod('ev93_fixture_geom_q1',layer.EV88,layer.PINS[str(layer.EV88)])
 ev87=loadmod('ev93_fixture_ev87_q1',layer.EV87,layer.PINS[str(layer.EV87)])
 shape=loadmod('ev93_fixture_shape_q1',SHAPE,SHAPE_SHA)
 ev92=loadmod('ev93_fixture_ev92_q1',EV92,EV92_SHA)
 bundle=geom.checked_sources();base_npz=bundle['B'];base=np.asarray(base_npz['heights'],np.float32)
 prepared,receipt,entries,ledger,ledger_path=layer.verify_prepared(PREPARED,LEGACY_RECEIPT,base)
 details=layer.validate_detail_hashes(prepared,entries)
 _,_,patches,_=layer.reconstruct_candidate(base_npz,receipt,entries,ledger,details,L)
 patch=next(p for p in patches if int(p['queue_id'])==1)
 candidate=base.copy();candidate[tuple(patch['nodes'].T)]=patch['final']
 gates,metrics=isolated_legacy_gate(layer,geom,ev87,shape,ev92,base,patch,details[1])
 if not gates or not all(gates.values()):raise AssertionError(f'real legacy q1 local gates failed: {metrics}')
 return {'real_legacy_qid':1,'real_legacy_q1_pass':True,'legacy_gate_count':len(gates)}

def explicit_api_ownership_fixture():
 old,layer,geom,ev91,ev87,cv,shape,ev92,indexmod,policy=loadctx()
 required=(hasattr(geom,'stencil_records') and hasattr(geom,'local_mesh_angles') and
           hasattr(layer,'stencil_energy_fraction') and hasattr(ev87,'edge_angles'))
 forbidden=(not hasattr(layer,'local_mesh_angles') and not hasattr(geom,'stencil_energy_fraction'))
 if not (required and forbidden):raise AssertionError('geometry/layer API ownership contract drifted')
 base=np.asarray(geom.checked_sources()['B']['heights'],np.float32)
 angles=dict(ev87.edge_angles(base[830:850,360:380].astype(np.float64)))
 angles_again=dict(ev87.edge_angles(base[830:850,360:380].astype(np.float64)))
 if not angles or set(angles)!=set(angles_again) or any(not np.array_equal(angles[k],angles_again[k]) for k in angles):
  raise AssertionError('explicit edge-angle generator materialization is not stable')
 return {'api_owners_explicit':True,'edge_angle_generator_materialized_once_per_grid':True}

def crest_target_smoke_fixture():
 # One real derived direction and one real policy rejection through the new
 # consumer path; this is a bounded smoke, not a candidate/global evaluation.
 pool=jload(EXT/'quarantine-pool-v3/compound-pool.json');rows=validate_pool(pool)
 inv=jload(INV);src={int(x['queue_id']):x for x in inv['reusable_directions']}
 target_rows=[r for r in rows if r['origin']=='crest']
 derived=next(r for r in target_rows if r['state']=='derived_quarantined')
 rejected=next(r for r in target_rows if r['state']=='rejected_policy')
 old,layer,geom,ev91,ev87,cv,shape,ev92,indexmod,policy=loadctx()
 base_npz=geom.checked_sources()['B'];base=np.asarray(base_npz['heights'],np.float32)
 prepared,receipt,entries,ledger,ledger_path=layer.verify_prepared(PREPARED,LEGACY_RECEIPT,base)
 details=layer.validate_detail_hashes(prepared,entries);prepared_sha=sha(PREPARED)
 derived_path=Path(derived['artifact_path']);drow=jload(derived_path)
 dp,dg,dm=verify_crest_target(old,policy,(layer,geom,ev91,ev87,cv,shape,ev92,indexmod),
    src[int(derived['queue_id'])],drow,base,prepared_sha,details)
 if dp is None or not dg or not all(dg.values()):raise AssertionError(f'real derived target local gates failed: {dg}')
 rejected_path=Path(rejected['artifact_path']);rrow=jload(rejected_path)
 rp,rg,rm=verify_crest_target(old,policy,(layer,geom,ev91,ev87,cv,shape,ev92,indexmod),
    src[int(rejected['queue_id'])],rrow,base,prepared_sha,details)
 if rp is not None or rg!={'policy_rule_available':False}:raise AssertionError('real policy reject was not independently classified without a delta')
 return {'real_derived_target_qid':int(derived['queue_id']),'derived_local_gate_count':len(dg),
         'real_derived_target_pass':True,'real_policy_reject_qid':int(rejected['queue_id']),
         'policy_reject_has_no_delta':True}

def fixture_suite():
 # Selection rows may be serialized in a different deterministic order than
 # the source pool; identity is by unit_id, not zip position.
 p=[{'unit_id':'legacy:0','origin':'legacy','queue_id':0,'source_qid':0,
     'artifact_path':'x0','artifact_sha256':'a'},
    {'unit_id':'crest:0','origin':'crest','queue_id':0,'source_qid':0,
     'artifact_path':'x1','artifact_sha256':'b'}]
 u=[{'unit_id':'crest:0','origin':'crest','queue_id':0,'source_qid':0,
     'source_artifact_path':'x1','source_artifact_sha256':'b','selection_status':'excluded_local','local_status':'FAIL'},
    {'unit_id':'legacy:0','origin':'legacy','queue_id':0,'source_qid':0,
     'source_artifact_path':'x0','source_artifact_sha256':'a','selection_status':'retained','local_status':'PASS'}]
 s={'schema':'ev93.compound-selection.v1','status':'SELECTED','units':u,
    'retained_unit_ids':['legacy:0'],'excluded_unit_ids':['crest:0']}
 validate_selection(p,s)
 broken=dict(s);broken['units']=u[:1]
 try:validate_selection(p,broken)
 except AssertionError:missing_rejected=True
 else:raise AssertionError('selection parser accepted a missing unit')
 broken=dict(s);broken['retained_unit_ids']=['legacy:0','crest:0']
 try:validate_selection(p,broken)
 except AssertionError:partition_rejected=True
 else:raise AssertionError('selection parser accepted overlapping retained/excluded partition')
 # Exercise the production physical envelope implementation: solver guard is
 # pinned to B while the independent physical lower bound remains permissive.
 layer=loadmod('ev93_fixture_layer',EV,EV_SHA)
 b=np.full((3,3),3.0,dtype=np.float32)
 patch={'nodes':np.asarray([[1,1],[1,2]],np.int32),
        'bounds':np.asarray([[1.0,3.0],[0.5,3.0]],np.float32),
        'solver_bounds':np.asarray([[3.0,3.0],[3.0,3.0]],np.float32)}
 l32=physical_l32(b,[({'unit_id':'crest:0'},patch)],layer.physical_lower_envelope)
 assert l32[1,1]==np.float32(1.0) and l32[1,2]==np.float32(.5)
 assert patch['solver_bounds'][0,0]==b[1,1] and l32[1,1]!=patch['solver_bounds'][0,0]
 # Production composition helper enforces unique ownership and canonical node hashes.
 nodes=np.asarray([[1,1],[1,2]],np.int32);vals=np.asarray([2.5,2.75],np.float32)
 local=[tuple(x) for x,v in zip(nodes.tolist(),vals) if b[tuple(x)]!=v]
 unit={'unit_id':'legacy:0','changed_vertices':len(local),
       'changed_vertices_sha256':cj([list(x) for x in sorted(local)])}
 h,owner,_=compose_retained(b,[(unit,{'nodes':nodes,'final':vals})])
 assert h[1,1]==vals[0] and h[1,2]==vals[1] and len(owner)==2
 try:compose_retained(b,[(unit,{'nodes':nodes,'final':vals}),(unit,{'nodes':nodes,'final':vals})])
 except AssertionError:overlap_rejected=True
 else:raise AssertionError('composition accepted duplicate ownership')
 pilot=pilot_local_wrapper_fixture()
 legacy_q1=real_legacy_q1_fixture()
 owners=explicit_api_ownership_fixture()
 crest=crest_target_smoke_fixture()
 return {'selection_identity_not_position_based':True,'missing_unit_rejected':missing_rejected,
         'nonexhaustive_partition_rejected':partition_rejected,
         'physical_L32_includes_guarded_bounds_not_solver_pins':True,
         'composition_hash_and_duplicate_owner_checks':True,**pilot,**legacy_q1,**owners,**crest}

def verify_selected(pool_path,selection_path,output_path,progress_path=None):
 global START
 START=time.perf_counter();prog(progress_path,'readset','start')
 for p,w in ((PLAN,PLAN_SHA),(AUTHOR,AUTHOR_SHA),(HELPER,HELPER_SHA),(EV,EV_SHA),(POLICY,POLICY_SHA),(SHAPE,SHAPE_SHA),(EV92,EV92_SHA),(ANY,ANY_SHA),(INV,INV_SHA)):
  if sha(p).lower()!=w.lower():raise AssertionError(f'frozen source pin mismatch: {p}')
 old,layer,geom,ev91,ev87,cv,shape,ev92,indexmod,policy=loadctx()
 pool_path=Path(pool_path).resolve();selection_path=Path(selection_path).resolve();pool=jload(pool_path);selection=jload(selection_path)
 rows=validate_pool(pool);units=validate_selection(rows,selection)
 population=selection.get('population',{})
 if (population.get('legacy')!=340 or population.get('crest')!=228 or
     population.get('locally_considered')!=568 or
     population.get('locally_valid')+population.get('locally_invalid')!=568):
  raise AssertionError('selection population totals do not reconcile to 340/228/568')
 if Path(selection.get('selection_plan_path','')).resolve()!=PLAN.resolve() or selection.get('plan_sha256')!=PLAN_SHA:raise AssertionError('selection plan pin mismatch')
 if (Path(selection.get('source_global_report_path','')).resolve()!=KNOWN_FAIL.resolve() or
     selection.get('source_global_report_sha256')!=KNOWN_FAIL_SHA):raise AssertionError('selection source FAIL report pin mismatch')
 if Path(selection.get('selector_source_path','')).resolve()!=SELECTOR.resolve() or sha(SELECTOR)!=selection.get('selector_sha256'):raise AssertionError('selector implementation pin mismatch')
 if Path(selection.get('base_path','')).resolve()!=BASE.resolve() or selection.get('base_sha256')!=sha(BASE):raise AssertionError('selection baseline pin mismatch')
 validate_pool_sources(pool,pool_path,selection)
 report=known_fail(pool['source_global_report']['path'],pool['source_global_report']['sha256'])
 if selection.get('source_global_report_sha256') not in (None,KNOWN_FAIL_SHA):raise AssertionError('selection source report SHA mismatch')
 bundle=geom.checked_sources();base_npz=bundle['B'];base=np.asarray(base_npz['heights'],np.float32)
 prepared,legacy_receipt,entries,ledger,ledger_path=layer.verify_prepared(PREPARED,LEGACY_RECEIPT,base)
 if sha(PREPARED)!=pool['legacy_source']['prepared_sha256'] or sha(LEGACY_RECEIPT)!=pool['legacy_source']['receipt_sha256']:raise AssertionError('legacy prepared/receipt differs from pool')
 details=layer.validate_detail_hashes(prepared,entries)
 source_composite,legacy_changed,legacy_patches,legacy_owner=layer.reconstruct_candidate(base_npz,legacy_receipt,entries,ledger,details,L)
 with np.load(LEGACY_CANDIDATE,allow_pickle=False) as z: legacy_npz={k:z[k] for k in z.files}
 if sha(LEGACY_CANDIDATE)!=KNOWN_LEGACY or not np.array_equal(source_composite,legacy_npz['heights']):raise AssertionError('frozen legacy composite reconstruction differs')
 legacy_by={int(p['queue_id']):p for p in legacy_patches}; refs_legacy={int(r['queue_id']):r for r in rows if r['origin']=='legacy'}
 if set(legacy_by)!=set(refs_legacy):raise AssertionError('pool legacy population differs from accepted source rows')
 target_receipt=jload(pool['crest_source']['receipt_path'])
 crest_refs={int(r['queue_id']):r for r in rows if r['origin']=='crest'}
 src_inv=jload(INV); source_by={int(r['queue_id']):r for r in src_inv['reusable_directions']}
 if len(crest_refs)!=228 or set(crest_refs)!=set(source_by):raise AssertionError('crest pool qids differ from exact quarantined inventory')
 entries_by={int(r['queue_id']):r for r in entries}; prepared_sha=sha(PREPARED)
 unit_by={u['unit_id']:u for u in units}; retained_ids=set(selection['retained_unit_ids'])
 input_hashes={str(Path(p).resolve()):w for p,w in inv_pins()}
 for p in (PLAN,AUTHOR,HELPER,EV,POLICY,SHAPE,EV92,ANY,INV,PREPARED,LEGACY_RECEIPT,LEGACY_CANDIDATE,pool_path,selection_path):input_hashes[str(Path(p).resolve())]=sha(p)
 for r in (KNOWN_FAIL,Path(pool['crest_source']['receipt_path']),Path(pool['crest_source']['target_rows_path']),Path(pool['crest_source']['ledger_path']),
           SELECTOR,INDEX_MANIFEST,INDEX_VERIFICATION,Path(__file__).resolve()):input_hashes[str(r.resolve())]=sha(r)
 for p,w in layer.PINS.items():input_hashes[str(Path(p).resolve())]=w
 for p,w in src_inv['source_pins'].items():input_hashes[str(Path(p).resolve())]=w
 # Preserve the frozen local-verifier source and all inputs used by selection.
 # This global consumer is a distinct version; it does not rewrite that source.
 for p,w in selection['source_read_set'].items():
  resolved=str(Path(p).resolve())
  if resolved in input_hashes and input_hashes[resolved].lower()!=w.lower():raise AssertionError(f'selection readset disagrees with independent source pin: {p}')
  input_hashes[resolved]=w
 # Validate all legacy refs and independently recompute their isolated gates.
 local_metrics={}; retained_patches=[]; legacy_for_global=[]; patch_by_uid={}; changed_nodes_by_uid={}
 prog(progress_path,'legacy-local','start',units=len(legacy_by))
 for qid,patch in sorted(legacy_by.items()):
  ref=refs_legacy[qid];u=unit_by[ref['unit_id']]
  result=patch['result']; rp=Path(ledger[qid]['result_path'])
  if rp.resolve()!=Path(ref['artifact_path']).resolve() or sha(rp)!=ref['artifact_sha256']:raise AssertionError(f'legacy artifact ref mismatch q{qid}')
  input_hashes[str(rp.resolve())]=ref['artifact_sha256'];input_hashes[str(Path(result['delta_path']).resolve())]=result['delta_sha256']
  for p,k in ((result['solution_path'],'solution_sha256'),(result['attempt_marker_path'],'attempt_marker_sha256')):
   if sha(p)!=result[k]:raise AssertionError(f'legacy solve provenance mismatch q{qid}')
   input_hashes[str(Path(p).resolve())]=result[k]
  gates,metric=isolated_legacy_gate(layer,geom,ev87,shape,ev92,base,patch,details[qid]);state=match_local_status(u,gates)
  local_metrics[u['unit_id']]={'gates':gates,'metrics':metric}
  if u['selection_status']=='retained':
   retained_patches.append((u,patch));legacy_for_global.append(patch);patch_by_uid[u['unit_id']]=patch
  if (qid+1)%50==0:prog(progress_path,'legacy-local','progress',processed=qid+1,total=703)
 prog(progress_path,'legacy-local','complete',accepted=len(legacy_by))
 # Verify every quarantined direction, derive its alpha/cast again, and run local gates on an isolated delta.
 crest_patches={}; policy_rejects=0
 prog(progress_path,'crest-local','start',units=228)
 for qid in sorted(crest_refs):
  ref=crest_refs[qid];row_path=Path(ref['artifact_path']).resolve();
  if sha(row_path)!=ref['artifact_sha256']:raise AssertionError(f'crest target artifact SHA mismatch q{qid}')
  row=jload(row_path);src=source_by[qid];unit=unit_by[ref['unit_id']]
  if row.get('source_result_path')!=ref['source_result_path'] or row.get('source_result_sha256')!=ref['source_result_sha256']:raise AssertionError(f'pool target source result ref mismatch q{qid}')
  input_hashes[str(row_path)]=ref['artifact_sha256']
  patch,gates,metric=verify_crest_target(old,policy,(layer,geom,ev91,ev87,cv,shape,ev92,indexmod),src,row,base,prepared_sha,details)
  if patch is None:
   policy_rejects+=1
   if (unit['selection_status']!='excluded_local' or unit['local_status']!='FAIL' or
       unit.get('local_gates',{}).get('policy_rule_available') is not False or
       any(v is not None and k!='policy_rule_available' for k,v in unit.get('local_gates',{}).items())):
    raise AssertionError(f'policy-rejected target classification differs q{qid}')
   local_metrics[unit['unit_id']]={'gates':gates,'metrics':None}
   continue
  state=match_local_status(unit,gates)
  local_metrics[unit['unit_id']]={'gates':gates,'metrics':metric}
  crest_patches[qid]=patch
  if unit['selection_status']=='retained':
   retained_patches.append((unit,patch));patch_by_uid[unit['unit_id']]=patch
  if (qid+1)%25==0:prog(progress_path,'crest-local','progress',processed=qid+1,total=228)
 prog(progress_path,'crest-local','complete',policy_rejects=policy_rejects)
 if len(local_metrics)!=568:raise AssertionError('not every pool unit received an independent local decision')
 # Whole-window composition from B; rejected/excluded windows contribute no height edits.
 candidate,owner,changed_nodes_by_uid=compose_retained(base,retained_patches)
 changed=np.argwhere(candidate!=base)
 if not len(changed):raise AssertionError('selected candidate is a no-op')
 candref=selection.get('candidate',{});candpath=Path(candref.get('path','')).resolve();candsha=candref.get('sha256')
 if not candpath.is_file() or sha(candpath)!=candsha:raise AssertionError('selection candidate file SHA mismatch')
 with np.load(candpath,allow_pickle=False) as z:candnpz={k:z[k] for k in z.files}
 if set(candnpz)!=set(base_npz):raise AssertionError('candidate NPZ metadata key set differs from B')
 for k in base_npz:
  if k!='heights' and not np.array_equal(candnpz[k],base_npz[k],equal_nan=True):raise AssertionError(f'candidate non-height metadata changed: {k}')
 if not np.array_equal(np.asarray(candnpz['heights'],np.float32),candidate):raise AssertionError('candidate heights differ from B + retained deltas')
 input_hashes[str(candpath)]=candsha

 # Independent whole-map gates. C's helper accepts legacy patches for its
 # EV92 local recheck; physical L32 is separately built from every retained
 # unit, including new crest-policy targets, using inward physical bounds.
 if sha(INDEX_VERIFICATION)!=INDEX_VERIFICATION_SHA:
  raise AssertionError('frozen direct/index verification report SHA mismatch')
 iv=jload(INDEX_VERIFICATION)
 if iv.get('status')!='PASS_INDEX_AND_SAMPLED_EXPOSURE' or iv.get('index_face_count')!=883308:
  raise AssertionError(f'compiled-face index verification is not complete: {iv.get("status")}')
 if selection.get('index_manifest_sha256')!=sha(INDEX_MANIFEST):
  raise AssertionError('selection face-index manifest SHA mismatch')
 if Path(selection.get('index_manifest_path','')).resolve()!=INDEX_MANIFEST.resolve():
  raise AssertionError('selection face-index manifest path mismatch')
 if not (selection.get('support',{}).get('selected_sums_m2') and
         all(float(selection['support']['selected_sums_m2'][k])<1e-7 for k in ('physical','visible'))):
  raise AssertionError('selector did not independently classify support sums below the frozen strict limit')
 index=indexmod.FaceRangeIndex(INDEX_MANIFEST.parent)
 for p,w in index.manifest.get('input_hashes',{}).items():input_hashes[str(Path(p).resolve())]=w
 # C global gates are unmodified. The temporary replacement only supplies
 # their L32 physical lower envelope from all retained units; legacy-only
 # patches still drive C's original EV92 local rule revalidation.
 all_physical_l32=physical_l32(base,retained_patches,layer.physical_lower_envelope)
 original_l32=layer.physical_lower_envelope
 l32_calls=[]
 def all_retained_l32(_base,_legacy_accepted):
  l32_calls.append(1)
  if len(l32_calls)>1:raise AssertionError('unexpected repeated physical L32 request')
  return all_physical_l32
 changed_rc=np.asarray(changed,dtype=np.int32)
 readset_expected=dict(input_hashes)
 readset_start={str(Path(p).resolve()):sha(p) for p in sorted(input_hashes)}
 start_mismatches=[p for p,w in readset_expected.items()
                   if readset_start.get(str(Path(p).resolve()))!=w]
 if start_mismatches:raise AssertionError(f'expected source hashes differ at readset start: {start_mismatches[:8]}')
 prog(progress_path,'global-contract','start',changed_vertices=len(changed),retained_units=len(retained_patches))
 layer.physical_lower_envelope=all_retained_l32
 try:
  global_result=layer.global_contract(geom,ev91,ev87,cv,shape,ev92,index,bundle,base,candidate,
                                      changed_rc,details,legacy_for_global)
 finally:
  layer.physical_lower_envelope=original_l32
 if len(l32_calls)!=1:raise AssertionError(f'global contract requested physical L32 {len(l32_calls)} times')
 prog(progress_path,'global-contract','complete',gates=len(global_result['gates']))
 gates=dict(global_result['gates'])
 # Local validity was recomputed for every pool row above. Retained rows must
 # all pass; excluded rows remain classified but cannot invalidate the result.
 retained_units=[u for u in units if u['selection_status']=='retained']
 if not retained_units or not any(u['origin']=='crest' for u in retained_units):
  raise AssertionError('selection has no nontrivial crest retention')
 if any(local_metrics[u['unit_id']]['gates'] and
        not all(local_metrics[u['unit_id']]['gates'].values()) for u in retained_units):
  raise AssertionError('a retained pool unit failed its independently recomputed local gates')
 gates['all_accepted_window_local_contracts']=all(
  all(local_metrics[u['unit_id']]['gates'].values()) for u in retained_units)
 gates['at_least_one_nontrivial_accepted_window']=bool(len(changed)>0 and retained_units)
 gates['at_least_one_nontrivial_crest_retained']=any(u['origin']=='crest' for u in retained_units)
 gates['compound_pool_and_selection_exhaustive']=True
 gates['selector_support_sums_below_strict_limit']=True
 # Recalculate the ANY-incidence report on the composed candidate. This is a
 # diagnostic only; it is never substituted for C's ALL-incidence gates.
 anymod=loadmod('ev93_any_diagnostic_v2',ANY,ANY_SHA)
 any87,any88=anymod.load_helpers()
 any_report=anymod.verify_candidate(candpath,candsha,any87,any88)
 index.reverify()
 for p,w in sorted(input_hashes.items()):
  if sha(p)!=w:raise AssertionError(f'input changed during independent consume: {p}')
 end_hashes={p:sha(p) for p in readset_start}
 if end_hashes!=readset_start:raise AssertionError('dynamic read-set changed during global gates')
 for p,w in layer.PINS.items():
  if sha(p)!=w:raise AssertionError(f'global consumer pin changed during run: {p}')
 report={
  'status':'PASS_INCREMENTAL_NONREGRESSION' if all(gates.values()) else 'FAIL_INCREMENTAL_NONREGRESSION',
  'gates':gates,
  'information':{
   'global_contract_status':'OPEN_INHERITED_MAP_DEFECTS',
   'source_global_status':'FAIL_INCREMENTAL_NONREGRESSION',
   'source_global_false_gates':sorted(FALSE_GATES),
   'candidate_path':str(candpath),'candidate_sha256':candsha,
   'compound_pool_sha256':sha(pool_path),'selection_sha256':sha(selection_path),
   'pool_units':len(units),'retained_units':len(retained_units),
   'retained_legacy_units':sum(u['origin']=='legacy' for u in retained_units),
   'retained_crest_units':sum(u['origin']=='crest' for u in retained_units),
   'policy_rejected_targets':policy_rejects,
   'changed_vertices':int(len(changed)),'changed_support_cells':global_result['information']['changed_support_cells'],
   'local_metrics':local_metrics,'global_contract':global_result['information'],
   'physical_l32_source':'all retained pool patches, physical bounds, including guarded nodes',
   'legacy_local_recheck':'legacy retained patches only; crest windows independently rechecked above',
   'any_incidence_diagnostic':any_report['diagnostic'],
   'any_diagnostic_acceptance_gate':False,
   'index_verification_sha256':INDEX_VERIFICATION_SHA,
   'consumer_source_path':str(Path(__file__).resolve()),'consumer_source_sha256':input_hashes[str(Path(__file__).resolve())],
   'changed_vertices':int(len(changed)),
   'input_hashes_expected':readset_expected,
   'input_hashes_start':readset_start,'input_hashes_end':end_hashes,
  }}
 return report

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--self-test',action='store_true')
 ap.add_argument('--pool',type=Path)
 ap.add_argument('--selection',type=Path)
 ap.add_argument('--output',type=Path)
 ap.add_argument('--progress-log',type=Path)
 args=ap.parse_args()
 if args.self_test:
  print(json.dumps({'status':'FIXTURES_PASS','fixtures':fixture_suite()},sort_keys=True,allow_nan=False));return
 if not args.pool or not args.selection or not args.output:ap.error('--pool, --selection, and --output are required')
 if args.output.exists():raise FileExistsError(f'refusing to overwrite report: {args.output}')
 args.output.parent.mkdir(parents=True,exist_ok=True)
 report={'status':'ERROR_COMPOUND_CONSUMER','gates':{},'information':{}}
 try:report=verify_selected(args.pool,args.selection,args.output,args.progress_log)
 except Exception as exc:
  report={'status':'ERROR_COMPOUND_CONSUMER','gates':{},'error':repr(exc),'traceback':traceback.format_exc()}
 tmp=args.output.with_suffix(args.output.suffix+'.tmp')
 if tmp.exists():raise FileExistsError(f'refusing pre-existing temp report: {tmp}')
 tmp.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
 tmp.replace(args.output)
 print(json.dumps({'status':report['status'],'false_gates':[k for k,v in report.get('gates',{}).items() if v is False],
                   'error':report.get('error'),'output':str(args.output)},sort_keys=True))
 if report['status']=='ERROR_COMPOUND_CONSUMER':raise SystemExit(2)
 if not all(report['gates'].values()):raise SystemExit(1)

if __name__=='__main__':main()
