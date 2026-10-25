#!/usr/bin/env python
"""EV93 first-layer fairing author. Prepare is read-only; execute is explicit and one-shot."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, os, sys, time, traceback
from pathlib import Path
from fractions import Fraction
import numpy as np

G=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
Q=Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010')
OUT=G/'fairing-layer1'
QUEUE=G/'queue/queue.json'
LEDGER=G/'preflight-segment02/window-ledger.jsonl'
PLAN=G/'author-stage-plan.md'
BASE=Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')
GIS_PY=Path(r'C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe')
EV93_PREFLIGHT=G/'preflight/ev93_preflight_windows.py'
EV88=Q/'author/author_ev88q.py'
EV91=Q/'ev91-descent/author_ev91.py'
EV92=Q/'ev92-damped/author_ev92.py'
EV90=Q/'ev90-author/author_ev90.py'
EV90_PREFLIGHT=Q/'next-method-preflight/ev90_preflight.py'
EV91_PREPARED=Q/'ev91-descent/prepared.json'
SHAPE=Q/'next-method-consumer/shape_contract.py'
EV87_GEOM=Path(r'E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py')
EV88_GEOM=Q/'review-independent/verify_ev88q.py'
INDEX_SOURCE=G/'ev93-face-index/build_face_index.py'
INDEX_MANIFEST=G/'ev93-face-index/runs/20261010T092417Z-63d4cec3/manifest.json'
INDEX_VERIFICATION=G/'review-independent/runs/attempt-01/verification.json'
PILOT_RECEIPT=G/'preflight/pilot-compare.json'
PREFLIGHT_PLAN=G/'preflight-plan.md'
PREFLIGHT_INVENTORY=G/'review-independent/preflight-inventory.json'
PLAN_SHA='2bc641c0ec88954e83a2d10f5a2542357ac8cdc6533456b466e4e71f90df504c'
PINS={
 str(EV93_PREFLIGHT):'a5a8537fa8b9caf092d6ba7b3d55f1f168f15e3541c242cdcc288065cb40c1cc',
 str(EV88):'532373b56c27ec0a04345c1c09a5cc6ff04fef34c04ac2856ce65ceb395162d1',
 str(EV91):'d17e358e9e9e92952e51e008148b534c2fde4a3ae7fe1e4197fdab4215adc9f1',
 str(EV90):'c8ee41f14c332bf9a5849ee7a6454e82043ccc5e06a866bd018df817f819ad7e',
 str(EV90_PREFLIGHT):'5892e917335ca2d8caa427f04f48ba8acbd8e16a5e1b400be596d5dd636afb7f',
 str(EV91_PREPARED):'127b906c1d2a5d2aa09172ed47dac16cd489aae6a2955428a96166a325605877',
 str(EV92):'818376c2fca9123473b862ece174f4277ffebf3568eb8875863e354e7e2fe4fd',
 str(SHAPE):'8cd9d0fbea03c05e5ae53a31676d79ec2364be83c055213446f6c8599245d533',
 str(EV87_GEOM):'964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
 str(EV88_GEOM):'82a988790e6bdfc0289bcb7c32cb0afd1210e07b264d92731aba266bc5980f78',
 str(INDEX_SOURCE):'d1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e',
 str(INDEX_MANIFEST):'c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c',
 str(INDEX_VERIFICATION):'b498e7d68835b199399655451e5e01ac81acb3149dbb9bf882b94858141521d4',
 str(PILOT_RECEIPT):'e462259614c5006c80a18175a124c29e7fceb4ae2cb9230b6912a0431429a185',
 str(PREFLIGHT_PLAN):'44022291bdbeBA62b924b5bf37655f1e8fefd5dee2ba28cd72c71a02ca0049ea'.lower(),
 str(PREFLIGHT_INVENTORY):'bb9099e359e6650ba84929308575c31578f69fb85f532ccc4cf3b7fd8ae0ecc5',
 str(BASE):'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
 str(QUEUE):'cf13887c8de031d65d0a32dab217e8743293103fcd00ea3c07c281c07a6794c9',
 str(PLAN):PLAN_SHA,
}
EXPECTED_ROWS=703
READY='PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW'

class GateReject(Exception):
 """A solve completed but failed an explicitly declared geometry gate."""


def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()

def canonical_bytes(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
def canonical_sha(x):return hashlib.sha256(canonical_bytes(x)).hexdigest()
def atomic_json(path,obj):
 path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_bytes(canonical_bytes(obj)+b'\n');os.replace(tmp,path)
def load_npz(path):
 with np.load(path,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 if spec is None or spec.loader is None:raise ImportError(f'cannot load {path}')
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def require_pins():
 for p,want in PINS.items():
  if not Path(p).is_file() or sha(p)!=want:raise RuntimeError(f'source pin mismatch or missing: {p}')
 if Path(sys.executable).resolve()!=GIS_PY.resolve():raise RuntimeError(f'wrong interpreter: {sys.executable}')
 import scipy
 if scipy.__version__!='1.18.1':raise RuntimeError(f'wrong SciPy runtime {scipy.__version__}')
 return {'python':str(Path(sys.executable).resolve()),'numpy':np.__version__,'scipy':scipy.__version__}
def runtime_modules():
 # EV91.solve_once uses multiprocessing spawn; its module name must be importable by the child.
 for directory in (str(EV91.parent),str(EV90.parent)):
  if directory not in sys.path:sys.path.insert(0,directory)
 import importlib
 ev91=importlib.import_module('author_ev91')
 if Path(ev91.__file__).resolve()!=EV91.resolve() or sha(ev91.__file__)!=PINS[str(EV91)]:raise RuntimeError('canonical EV91 import resolved to the wrong source')
 return (load_module('layer1_ev88',EV88),ev91,
         load_module('layer1_ev92',EV92),load_module('layer1_shape',SHAPE),
         load_module('layer1_ev87geom',EV87_GEOM),load_module('layer1_ev88geom',EV88_GEOM))
def parse_jsonl(path):
 with Path(path).open('r',encoding='utf-8') as f:
  rows=[json.loads(line) for line in f if line.strip()]
 if not rows or rows[0].get('event')!='header':raise ValueError('missing preflight header')
 return rows[0],rows[1:]
def queue_first_layer():
 q=json.loads(QUEUE.read_text(encoding='utf-8'))
 if q.get('status')!='MATERIALIZED_NO_TERRAIN_OR_SOLVER':raise ValueError('queue status mismatch')
 items=[x for x in q['seeds'] if x.get('state')=='first_layer']
 items.sort(key=lambda x:int(x['first_layer_id']))
 if len(items)!=EXPECTED_ROWS:raise ValueError(f'expected {EXPECTED_ROWS} first-layer rows, found {len(items)}')
 return q,items
def normalize_window17(v):
 if len(v)!=4:raise ValueError('window17 must contain four coordinates')
 r0,c0,r1,c1=map(int,v);out=(r0,r1,c0,c1)
 if r1-r0!=17 or c1-c0!=17:raise ValueError(f'not a 17x17 window: {v}')
 return out
def canonical_path_for_detail(ledger_path,entry):
 p=Path(entry['detail_path'])
 if not p.is_absolute():p=Path(ledger_path).parent/p
 if not p.is_file():
  fallback=G/'preflight'/entry['detail_path']
  if not fallback.is_file():raise FileNotFoundError(f'detail missing: {entry["detail_path"]}')
  p=fallback
 if sha(p)!=entry.get('detail_sha256'):raise ValueError(f'detail SHA mismatch q{entry["queue_id"]}')
 return p.resolve()
def validate_complete_ledger(path,queue_items):
 header,events=parse_jsonl(path)
 raw_lines=[line for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
 if header.get('event')!='header' or header.get('queue_sha256')!=sha(QUEUE):raise ValueError('ledger header does not bind pinned queue')
 if header.get('source_sha256')!=PINS[str(EV93_PREFLIGHT)] or header.get('EV91_sha256')!=PINS[str(EV91)]:raise ValueError('ledger source identities mismatch')
 if header.get('EV90_sha256')!=PINS[str(EV90_PREFLIGHT)] or header.get('EV91_prepared_sha256')!=PINS[str(EV91_PREPARED)] or header.get('pilot_sha256')!=PINS[str(PILOT_RECEIPT)]:raise ValueError('ledger preflight prerequisites mismatch')
 if header.get('index_manifest_sha256')!=PINS[str(INDEX_MANIFEST)] or header.get('index_verification_sha256')!=PINS[str(INDEX_VERIFICATION)]:raise ValueError('ledger index identities mismatch')
 if Path(header.get('index_verification_path','')).resolve()!=INDEX_VERIFICATION.resolve():raise ValueError('ledger index verification path mismatch')
 final=events[-1] if events else {}
 if final.get('event')!='final' or final.get('status')!='COMPLETE_READONLY_PREFLIGHT':raise ValueError('preflight ledger has no complete terminal record')
 if final.get('remaining_count')!=0 or final.get('remaining_queue_ids') or final.get('processed_count')!=EXPECTED_ROWS or final.get('error_count')!=0:raise ValueError('preflight final record is incomplete or contains execution errors')
 rows=[x for x in events if x.get('event')=='window']
 resume_indices=[i for i,x in enumerate(events) if x.get('event')=='resume']
 final_indices=[i for i,x in enumerate(events) if x.get('event')=='final']
 if len(resume_indices)!=1 or len(final_indices)!=2:raise ValueError('unexpected resumed-ledger event sequence')
 ri=resume_indices[0];prior=events[final_indices[0]]
 if final_indices[0]+1!=ri or final_indices[1]!=len(events)-1:raise ValueError('resume is not bound between the initial and terminal final records')
 if prior.get('status')!='INCOMPLETE_READONLY_PREFLIGHT' or prior.get('processed_count')!=406 or prior.get('error_count')!=297 or prior.get('remaining_count')!=297:raise ValueError('unexpected initial preflight failure record')
 prior_raw=raw_lines[final_indices[0]+1] # event indices omit the header; physical JSONL lines do not.
 if hashlib.sha256((prior_raw+'\n').encode('utf-8')).hexdigest()!=events[ri].get('prior_final_sha256'):raise ValueError('resume hash does not bind the initial final record')
 byid={}
 for x in rows:byid.setdefault(int(x['queue_id']),[]).append(x)
 if set(byid)!=set(range(EXPECTED_ROWS)):raise ValueError('preflight qids do not cover 0..702')
 # Segment02 preserves the first attempt. Only a prior cap error followed by
 # one resumed terminal row is permitted; all other duplicate histories fail closed.
 for qid,history in byid.items():
  if len(history)==1:continue
  if len(history)!=2 or history[0].get('state')!='PREFLIGHT_ERROR' or history[0].get('detail_path') or history[0].get('detail_sha256') or history[1].get('state')=='PREFLIGHT_ERROR':
   raise ValueError(f'unexpected repeated preflight history q{qid}')
  first_index=next(i for i,x in enumerate(events) if x is history[0])
  later_index=next(i for i,x in enumerate(events) if x is history[1])
  if not first_index<ri<later_index:raise ValueError(f'error/resume/success order invalid q{qid}')
  if history[1].get('detail_path') is None or history[1].get('detail_sha256') is None:raise ValueError(f'resumed row lacks a pinned detail q{qid}')
  byid[qid]=[history[1]]
 prepared=[]
 for qid,item in enumerate(queue_items):
  e=byid[qid][-1]
  if int(item.get('first_layer_id',-1))!=qid or int(e.get('seed_id',-1))!=int(item['seed_id']):raise ValueError(f'queue/ledger identity mismatch at {qid}')
  if list(map(int,e['center_rc']))!=[int(item['row']),int(item['col'])]:raise ValueError(f'center mismatch at {qid}')
  queue_win=normalize_window17(item['window17']);ledger_win=normalize_window17(e['window17'])
  if ledger_win!=queue_win:raise ValueError(f'window coordinate mismatch at {qid}: {ledger_win} vs {queue_win}')
  detail_path=canonical_path_for_detail(path,e)
  detail=json.loads(detail_path.read_text(encoding='utf-8'));pre=detail.get('preflight',{})
  if detail.get('queue_id')!=qid or int(detail.get('seed_id',-1))!=int(item['seed_id']):raise ValueError(f'detail identity mismatch at {qid}')
  outer=normalize_window17(detail['window17']);inner=tuple(map(int,pre.get('window',[])))
  if outer!=queue_win or inner!=queue_win:raise ValueError(f'detail window order/geometry mismatch at {qid}')
  core=tuple(map(int,pre.get('core',[])))
  expected_core=(queue_win[0]+2,queue_win[1]-2,queue_win[2]+2,queue_win[3]-2)
  if core!=expected_core:raise ValueError(f'core mismatch at {qid}')
  state=str(e['state'])
  if state not in (READY,'PREFLIGHT_INFEASIBLE','PREFLIGHT_INCONCLUSIVE'):raise ValueError(f'unsupported terminal preflight state at {qid}: {state}')
  if pre.get('status')!=state:raise ValueError(f'detail/ledger state mismatch at {qid}')
  prepared.append({'queue_id':qid,'seed_id':int(item['seed_id']),'center_rc':list(map(int,e['center_rc'])),'window_rc':list(queue_win),'core_rc':list(core),'detail_path':str(detail_path),'detail_sha256':sha(detail_path),'preflight_state':state})
 if len(prepared)!=EXPECTED_ROWS:raise AssertionError('prepared row total changed')
 inventory=json.loads(PREFLIGHT_INVENTORY.read_text(encoding='utf-8'))
 counts={state:sum(x['preflight_state']==state for x in prepared) for state in (READY,'PREFLIGHT_INFEASIBLE','PREFLIGHT_INCONCLUSIVE')}
 if inventory.get('status')!='PASS_PREFLIGHT_INVENTORY_NOT_TERRAIN_ACCEPTANCE' or inventory.get('ledger_sha256')!=sha(path) or inventory.get('windows')!=EXPECTED_ROWS or inventory.get('state_counts')!=counts:raise ValueError('independent preflight inventory does not reconcile with prepared rows')
 readset=header.get('read_set_sha256',{})
 for p,w in readset.items():
  if not Path(p).is_file() or sha(p)!=w:raise ValueError(f'preflight read-set drift: {p}')
 return header,prepared

def prepared_manifest(ledger_path):
 versions=require_pins();q,items=queue_first_layer();header,entries=validate_complete_ledger(ledger_path,items)
 return {'schema':'ev93-fairing-layer1-prepared-v1','status':'PREPARED_NO_SOLVE','plan_path':str(PLAN),'plan_sha256':sha(PLAN),'author_path':str(Path(__file__).resolve()),'author_sha256':sha(__file__),'queue_path':str(QUEUE),'queue_sha256':sha(QUEUE),'preflight_ledger_path':str(Path(ledger_path).resolve()),'preflight_ledger_sha256':sha(ledger_path),'preflight_header':header,'preflight_final':{'processed_count':EXPECTED_ROWS,'remaining_count':0,'error_count':0},'base_path':str(BASE),'base_sha256':sha(BASE),'runtime':versions,'source_pins':PINS,'entry_count':len(entries),'entries':entries}

def _node_sha(nodes,base):
 h=hashlib.sha256()
 for r,c in nodes:h.update(np.asarray((r,c),dtype='<i4').tobytes());h.update(np.asarray(base[r,c],dtype='<f4').tobytes())
 return h.hexdigest()
def _d8_sha(matrix,rhs):return hashlib.sha256(np.asarray(matrix,dtype='<f8').tobytes()).hexdigest(),hashlib.sha256(np.asarray(rhs,dtype='<f8').tobytes()).hexdigest()
def _f64_sha(values):return hashlib.sha256(np.asarray(values,dtype='<f8').tobytes()).hexdigest()
def stencil_bytes(stencils):return np.frombuffer(canonical_bytes([[str(k),int(r),int(c)] for k,r,c in stencils]),dtype=np.uint8)
def interpolate_float32(base,direction,alpha):
 b=np.asarray(base);h=np.asarray(direction)
 if b.dtype!=np.float32 or h.dtype!=np.float32 or b.shape!=h.shape or not np.isfinite(b).all() or not np.isfinite(h).all():raise ValueError('B/direction must be matching finite float32 arrays')
 if not math.isfinite(float(alpha)) or not 0<float(alpha)<1:raise ValueError('alpha must be strictly between zero and one')
 return np.asarray(b.astype(np.float64)+float(alpha)*(h.astype(np.float64)-b.astype(np.float64)),dtype=np.float32)
def record_solver_direction(local,solved,base,result,attempt_marker):
 nodes=local['nodes'];x=np.asarray(solved['x'],dtype=np.float64)
 if x.shape!=(len(nodes),) or not np.isfinite(x).all():raise RuntimeError('solver returned invalid direction vector')
 b=np.asarray(base['heights'],dtype=np.float32);rc=np.asarray(nodes,dtype=np.int64);hdir=b.copy();hdir[tuple(rc.T)]=x.astype(np.float32)
 local['solution_x']=x;local['direction_grid']=hdir;local['direction32']=hdir
 matrix_sha=_f64_sha(local['A']);rhs_sha=_f64_sha(local['rhs']);d8m,d8d=_d8_sha(local['C'],local['d'])
 marker=Path(attempt_marker);out=marker.with_name(marker.name.removesuffix('.started.json')+'.solution.npz')
 atomic_npz(out,variables_rc=np.asarray(nodes,dtype=np.int32),B_values_float32=b[tuple(rc.T)].astype(np.float32),bounds_float32_inward=np.column_stack((local['lo'],local['hi'])).astype(np.float32),solver_bounds_float32=np.column_stack((local['solverlo'],local['solverhi'])).astype(np.float32),guard_rc=np.asarray(local['guard'],dtype=np.int32),solver_x_float64=x,direction_float32=hdir[tuple(rc.T)].astype(np.float32),stencils_json=stencil_bytes(local['stencils']),descent_witnesses_json=np.frombuffer(canonical_bytes(local['witnesses']),dtype=np.uint8),matrix_shape=np.asarray(local['A'].shape,dtype=np.int32),matrix_sha256_f64=np.frombuffer(matrix_sha.encode('ascii'),dtype=np.uint8),rhs_sha256_f64=np.frombuffer(rhs_sha.encode('ascii'),dtype=np.uint8),d8_matrix_sha256_f64=np.frombuffer(d8m.encode('ascii'),dtype=np.uint8),d8_rhs_sha256_f64=np.frombuffer(d8d.encode('ascii'),dtype=np.uint8))
 result.update({'solver_nit':int(solved['nit']),'solver_cost':float(solved['cost']),'solution_path':str(out),'solution_sha256':sha(out),'variables_count':len(nodes),'guard_rc':np.asarray(local['guard'],dtype=np.int32).tolist(),'stencil_count':len(local['stencils']),'stencils':[[str(k),int(r),int(c)] for k,r,c in local['stencils']],'d8_witnesses':local['witnesses'],'matrix_shape':list(local['A'].shape),'matrix_sha256_f64':matrix_sha,'rhs_sha256_f64':rhs_sha,'d8_matrix_sha256_f64':d8m,'d8_rhs_sha256_f64':d8d,'bounds_float32_inward':np.column_stack((local['lo'],local['hi'])).tolist(),'solver_bounds_float32':np.column_stack((local['solverlo'],local['solverhi'])).tolist(),'solver_x_float64':x.tolist(),'direction_float32':hdir[tuple(rc.T)].tolist()})
 return out
def local_physics(ev87,before,after,window,nodes):
 r0,r1,c0,c1=window;mb=np.zeros((r1-r0,c1-c0),dtype=bool);rr,cc=np.asarray(nodes,dtype=np.int64).T;mb[rr-r0,cc-c0]=True
 crop=(slice(r0,r1),slice(c0,c1));b_local=before[crop];h_local=after[crop]
 # All cells incident to variables are fully inside the 17x17 context because variables are core13.
 cellmask=np.logical_or.reduce((mb[:-1,:-1],mb[:-1,1:],mb[1:,:-1],mb[1:,1:]))
 slopes_b=ev87.slopes(b_local);slopes_h=ev87.slopes(h_local)
 slopes=[(x[cellmask],y[cellmask]) for x,y in zip(slopes_b,slopes_h)]
 if not slopes or not any(x.size for x,_ in slopes):raise RuntimeError('no incident triangles to changed variables')
 slope_bad=[(float(b),float(h)) for x,y in slopes for b,h in zip(x,y) if h>max(35.0,float(b))+1e-4]
 angles_b=dict(ev87.edge_angles(b_local));angles_h=dict(ev87.edge_angles(h_local))
 changed_hinges={}
 for kind in ('diag','vertical','horizontal'):
  affected=np.logical_or.reduce(ev87.edge_vertex_slices(mb,kind))
  vb=angles_b[kind][affected];vh=angles_h[kind][affected]
  if len(vb)==0:continue
  new_steep=np.logical_and(vb<=30.0001,vh>30.0001)
  changed_hinges[kind]={'n':int(len(vb)),'B_max_deg':float(np.max(vb)),'H_max_deg':float(np.max(vh)),'new_over_30_0001':int(np.count_nonzero(new_steep))}
 if any(x['new_over_30_0001'] for x in changed_hinges.values()):raise GateReject('new native hinge exceeds 30.0001 degrees')
 if slope_bad:raise GateReject('local incident triangle slope exceeds max(35,B)+1e-4 degrees')
 return {'incident_triangle_count':int(sum(x.size for x,_ in slopes)),'slope_gate':'PASS','native_hinges':changed_hinges,'hinge_gate':'PASS'}

def reconstruct(entry,prepared,base,mods):
 detail=json.loads(Path(entry['detail_path']).read_text(encoding='utf-8'));pre=detail['preflight'];window=tuple(entry['window_rc']);center=tuple(entry['center_rc'])
 if pre['status']!=READY:raise ValueError('cannot reconstruct non-READY detail')
 domain=pre['domain'];nodes=[tuple(map(int,x)) for x in domain['eligible_after_face_freeze_nodes']]
 if nodes!=sorted(set(nodes)):raise ValueError('eligible variable ordering is not unique row-major')
 intervals=domain['final_float32_intervals_for_eligible_nodes']
 if [tuple(map(int,x['node_rc'])) for x in intervals]!=nodes:raise ValueError('domain intervals do not align exactly to eligible variables')
 lo=np.asarray([x['interval_float32_inward_m'][0] for x in intervals],dtype=np.float32);hi=np.asarray([x['interval_float32_inward_m'][1] for x in intervals],dtype=np.float32)
 if len(nodes)==0 or np.any(~np.isfinite(lo)) or np.any(~np.isfinite(hi)) or np.any(lo>hi):raise ValueError('empty/invalid physical intervals')
 b=np.asarray(base['heights'],dtype=np.float32);r0,r1,c0,c1=window;local={'variables':np.asarray(nodes,dtype=np.int64),'bounds17':window,'B_local':b[r0:r1,c0:c1]}
 A,rhs,stencils,_weights=mods[0].build_matrix(local)
 gd=pre['guard_d8'];guard=mods[1].collar_guard(nodes,stencils,window)
 if [list(x) for x in guard]!=gd['guard_rc'] or len(stencils)!=int(gd['stencil_count']):raise ValueError('guard/stencil reconstruction differs from EV93 preflight')
 if _node_sha(guard,b)!=gd['guard_B_height_values_sha256_f32']:raise ValueError('guard B-value hash differs from preflight')
 C,d,witnesses,exempt,centers=mods[1].descent_constraints(b,nodes);msha,dsha=_d8_sha(C,d)
 if witnesses!=gd['descent_witnesses'] or [list(x) for x in exempt]!=gd['descent_exempt_baseline_centers']:raise ValueError('D8 witnesses/exempt centers differ from preflight')
 if list(C.shape)!=gd['descent_matrix_shape'] or msha!=gd['descent_matrix_sha256_f64'] or dsha!=gd['descent_rhs_sha256_f64']:raise ValueError('D8 constraint hashes differ from preflight')
 x0=np.asarray([b[rc] for rc in nodes],dtype=np.float64)
 if np.any(x0<lo) or np.any(x0>hi) or np.any(C@x0<d):raise ValueError('baseline infeasible under certified intervals/D8')
 guardset=set(guard);solverlo=lo.copy();solverhi=hi.copy();idx={x:i for i,x in enumerate(nodes)}
 for rc in guardset:solverlo[idx[rc]]=solverhi[idx[rc]]=b[rc]
 return {'detail':detail,'window':window,'center':center,'nodes':nodes,'lo':lo,'hi':hi,'solverlo':solverlo,'solverhi':solverhi,'stencils':stencils,'A':A,'rhs':rhs,'C':C,'d':d,'witnesses':witnesses,'guard':guard,'x0':x0}

def verify_solution(local,prepared,mods,base):
 ev88,ev91,ev92,shape,ev87geom,ev88geom=mods;b=np.asarray(base['heights'],dtype=np.float32).copy();
 nodes=local['nodes'];hdir=np.asarray(local['direction_grid'],dtype=np.float32)
 if hdir.shape!=b.shape or not np.isfinite(hdir).all():raise RuntimeError('recorded solver direction grid invalid')
 dv=hdir[tuple(np.asarray(nodes).T)]
 if np.any(dv<local['solverlo']) or np.any(dv>local['solverhi']) or np.any(dv<local['lo']) or np.any(dv>local['hi']):raise GateReject('direction violates physical or solver bounds')
 if any(hdir[rc]!=b[rc] for rc in local['guard']):raise GateReject('direction moved collar guard')
 if not ev91.witnesses_hold(hdir,local['witnesses']):raise GateReject('D8 witnesses fail after float32 direction cast')
 try:rule=ev92.scalar_rule(b,hdir,local['stencils'],focus=local['center'])
 except (ValueError, ArithmeticError) as exc:raise GateReject(f'scalar interpolation rule unavailable: {exc}') from exc
 alpha=float(rule['alpha'])
 r0,r1,c0,c1=local['window']
 final=interpolate_float32(b,hdir,alpha)
 if np.any(final[tuple(np.asarray(nodes).T)]<local['lo']) or np.any(final[tuple(np.asarray(nodes).T)]>local['hi']):raise GateReject('final cast violates physical inward bounds')
 if any(final[rc]!=b[rc] for rc in local['guard']):raise GateReject('final cast moved guard')
 if not ev91.witnesses_hold(final,local['witnesses']):raise GateReject('final cast violates D8 witnesses')
 shape_b=b[r0-1:r1+1,c0-1:c1+1];shape_h=final[r0-1:r1+1,c0-1:c1+1]
 shape_window=(1,shape_b.shape[0]-1,1,shape_b.shape[1]-1);shape_focus=(local['center'][0]-r0+1,local['center'][1]-c0+1)
 shape_report=shape.evaluate_shape(shape_b,shape_h,shape_window,shape_focus)
 shape_report['window']=list(local['window'])
 ro,co=r0-1,c0-1
 for axis in shape_report['axes'].values():
  for item in axis['new_subdominant_or_dominant_maxima']:
   item['rc']=[int(item['rc'][0]+ro),int(item['rc'][1]+co)]
 shape_report['new_minima8']=[[int(r+ro),int(c+co)] for r,c in shape_report['new_minima8']]
 shape_report['new_constant_quads']=[[int(r+ro),int(c+co)] for r,c in shape_report['new_constant_quads']]
 if not all(shape_report['gates'].values()):raise GateReject(f'shape gate failed: {shape_report["gates"]}')
 energy_b=ev92.energy_moments(b,b,local['stencils']);energy_h=ev92.energy_moments(b,final,local['stencils'])
 if sum(energy_h)>Fraction(3,4)*energy_b[0]:raise GateReject('curvature energy reduction below 25 percent')
 focus_b=ev88geom.local_mesh_angles(b,local['center'],radius=2);focus_h=ev88geom.local_mesh_angles(final,local['center'],radius=2)
 hinge_reduction=focus_b['max_incident_hinge_deg']-focus_h['max_incident_hinge_deg']
 if hinge_reduction<2.0:raise GateReject('focus incident hinge reduction below 2 degrees')
 physics=local_physics(ev87geom,b,final,local['window'],nodes)
 # Collar identity includes energy and all native hinges touching the frozen collar.
 collar=set(local['guard']);
 if any(final[rc]!=b[rc] for rc in collar):raise GateReject('collar guard not identical')
 collar_stencils=[]
 for stencil in local['stencils']:
  kind,r,c=stencil
  support={'xx':((r,c),(r,c+1),(r,c+2)),'zz':((r,c),(r+1,c),(r+2,c)),
           'xz':((r,c),(r,c+2),(r+2,c),(r+2,c+2))}[kind]
  if any((r0<=rr<r1 and c0<=cc<c1 and (rr<r0+2 or rr>=r1-2 or cc<c0+2 or cc>=c1-2)) for rr,cc in support):
   collar_stencils.append(stencil)
 collar_energy_b=[ev92.energy_moments(b,b,[stencil])[0] for stencil in collar_stencils]
 collar_energy_h=[ev92.energy_moments(b,final,[stencil])[0] for stencil in collar_stencils]
 if collar_energy_b!=collar_energy_h:raise GateReject('a collar-touching stencil energy changed')
 # Every native hinge whose four-node incidence touches the collar is outside the mutable region.
 cb=np.zeros((r1-r0,c1-c0),dtype=bool)
 for rr in range(r1-r0):
  for cc in range(c1-c0):
   if rr<2 or rr>=r1-r0-2 or cc<2 or cc>=c1-c0-2:cb[rr,cc]=True
 for kind in ('diag','vertical','horizontal'):
  affected=np.logical_or.reduce(ev87geom.edge_vertex_slices(cb,kind))
  hb=dict(ev87geom.edge_angles(b[r0:r1,c0:c1]))[kind][affected]
  hh=dict(ev87geom.edge_angles(final[r0:r1,c0:c1]))[kind][affected]
  if not np.array_equal(hb,hh):raise GateReject(f'collar {kind} hinge changed')
 local.update({'direction32':hdir,'final32':final,'rule':rule,'alpha':alpha,'shape_report':shape_report,'energy_B_fraction':[str(v) for v in energy_b],'energy_H_fraction':[str(v) for v in energy_h],'focus_hinge_B_deg':focus_b['max_incident_hinge_deg'],'focus_hinge_H_deg':focus_h['max_incident_hinge_deg'],'focus_hinge_reduction_deg':hinge_reduction,'physics':physics})
 return local

def atomic_npz(path,**arrays):
 path=Path(path);tmp=path.with_name(path.stem+'.tmp.npz');np.savez_compressed(tmp,**arrays);os.replace(tmp,path)
def append_jsonl(path,obj):
 with Path(path).open('ab') as f:f.write(canonical_bytes(obj)+b'\n');f.flush();os.fsync(f.fileno())
def result_qid(path):
 name=Path(path).name
 prefix='window-';suffix='.json'
 if not name.startswith(prefix) or not name.endswith(suffix):raise ValueError(f'unrecognized result filename: {name}')
 token=name[len(prefix):-len(suffix)]
 if len(token)!=4 or not token.isdigit():raise ValueError(f'unrecognized result qid: {name}')
 return int(token)
def marker_qid(path):
 name=Path(path).name
 prefix='window-';suffix='.started.json'
 if not name.startswith(prefix) or not name.endswith(suffix):raise ValueError(f'unrecognized marker filename: {name}')
 token=name[len(prefix):-len(suffix)]
 if len(token)!=4 or not token.isdigit():raise ValueError(f'unrecognized marker qid: {name}')
 return int(token)
def lock_exclusive(path):
 fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,canonical_bytes({'pid':os.getpid(),'started_utc':time.time()}));os.fsync(fd);return fd

def compose_candidate(base,accepted_results):
 heights=np.asarray(base['heights'])
 if heights.dtype!=np.float32 or heights.ndim!=2 or not np.isfinite(heights).all():raise ValueError('baseline heights must be finite float32 grid')
 out=heights.copy();owners={}
 for result in accepted_results:
  if result.get('state')!='accepted':raise ValueError('composer accepts accepted rows only')
  if sha(result['delta_path'])!=result.get('delta_sha256'):raise ValueError('delta artifact SHA mismatch')
  z=load_npz(result['delta_path']);nodes=np.asarray(z['variables_rc'])
  old=np.asarray(z['B_values_float32']);new=np.asarray(z['final_float32']);bounds=np.asarray(z['bounds_float32_inward'])
  if nodes.dtype!=np.int32 or nodes.ndim!=2 or nodes.shape[1]!=2 or old.shape!=(len(nodes),) or new.shape!=(len(nodes),) or bounds.shape!=(len(nodes),2):raise ValueError('delta array schema mismatch')
  if new.dtype!=np.float32 or old.dtype!=np.float32 or not np.isfinite(new).all() or not np.isfinite(bounds).all():raise ValueError('delta float32 arrays invalid')
  guard={tuple(map(int,x)) for x in z['guard_rc']}
  for i,raw in enumerate(nodes):
   rc=tuple(map(int,raw))
   if not(0<=rc[0]<heights.shape[0] and 0<=rc[1]<heights.shape[1]):raise ValueError('delta node outside B')
   if old[i]!=heights[rc] or new[i]<bounds[i,0] or new[i]>bounds[i,1]:raise ValueError('delta does not match baseline or physical bounds')
   if rc in guard and new[i]!=old[i]:raise ValueError('delta moved a collar guard node')
   if new[i]!=old[i]:
    if rc in owners:raise ValueError(f'overlapping ownership {rc}: {owners[rc]} and {result["queue_id"]}')
    owners[rc]=result['queue_id'];out[rc]=new[i]
 return out,owners

def execute(prepared_path,approved_sha,budget_seconds=600):
 prepared_path=Path(prepared_path);prepared_sha=sha(prepared_path)
 if prepared_sha!=approved_sha:raise ValueError('prepared SHA differs from explicitly approved SHA')
 prepared=json.loads(prepared_path.read_text(encoding='utf-8'))
 if prepared.get('status')!='PREPARED_NO_SOLVE' or prepared.get('entry_count')!=EXPECTED_ROWS:raise ValueError('invalid prepared manifest')
 if prepared.get('author_sha256')!=sha(__file__):raise ValueError('author source differs from prepared manifest')
 if prepared.get('source_pins')!=PINS or prepared.get('plan_sha256')!=sha(PLAN):raise ValueError('prepared source pins or plan changed')
 if sha(QUEUE)!=prepared.get('queue_sha256') or sha(BASE)!=prepared.get('base_sha256') or sha(prepared.get('preflight_ledger_path',''))!=prepared.get('preflight_ledger_sha256'):raise ValueError('prepared input changed after review')
 require_pins();mods=runtime_modules();base=load_npz(BASE);lock=OUT/'execute.lock';lockfd=lock_exclusive(lock);started=time.monotonic();failed=False
 try:
  for e in prepared['entries']:
   qid=int(e['queue_id']);result_path=OUT/f'results/window-{qid:04d}.json';mark=OUT/f'attempts/window-{qid:04d}.started.json'
   if result_path.exists():
    prior=json.loads(result_path.read_text(encoding='utf-8'))
    if prior.get('queue_id')!=qid or prior.get('prepared_sha256')!=prepared_sha or prior.get('preflight_state')!=e['preflight_state'] or prior.get('state') not in ('accepted','rejected','inconclusive','not_authored','timeout','error'):raise RuntimeError(f'invalid prior terminal result q{qid}')
    if prior['state']=='accepted' and (not Path(prior.get('delta_path','')).is_file() or sha(prior['delta_path'])!=prior.get('delta_sha256')):raise RuntimeError(f'prior accepted delta is missing or changed q{qid}')
    if prior['state'] in ('timeout','error'):failed=True
    continue
   if mark.exists():failed=True;break
   if time.monotonic()-started>budget_seconds-125:break
   state=e['preflight_state'];result={'queue_id':qid,'seed_id':e['seed_id'],'center_rc':e['center_rc'],'window_rc':e['window_rc'],'core_rc':e['core_rc'],'preflight_state':state,'solve_calls':0,'state':None,'reason':None,'prepared_sha256':prepared_sha}
   if state!=READY:
    result['state']='inconclusive' if 'INCONCLUSIVE' in state else 'not_authored';result['reason']='preflight state is not READY';atomic_json(result_path,result);append_jsonl(OUT/'ledger.jsonl',{'event':'result','queue_id':qid,'state':result['state'],'result_path':str(result_path),'result_sha256':sha(result_path)});continue
   try:
    local=reconstruct(e,prepared,base,mods);result.update({'window_rc':list(local['window']),'core_rc':e['core_rc']})
   except Exception as exc:
    result.update({'state':'error','reason':f'reconstruction {type(exc).__name__}: {exc}'})
    atomic_json(result_path,result);append_jsonl(OUT/'ledger.jsonl',{'event':'result','queue_id':qid,'state':result['state'],'result_path':str(result_path),'result_sha256':sha(result_path)})
    failed=True;break
   # Exclusive marker is written after reconstruction and immediately before the one solver call.
   try:fd=lock_exclusive(mark);os.close(fd)
   except FileExistsError:failed=True;break
   atomic_json(mark,{'queue_id':qid,'prepared_sha256':prepared_sha,'author_sha256':sha(__file__),'started_monotonic':time.monotonic()})
   result['solve_calls']=1
   try:
    solved=mods[1].solve_once(local['A'],local['rhs'],local['solverlo'].astype(np.float64),local['solverhi'].astype(np.float64),local['C'],local['d'],local['x0'])
   except TimeoutError as exc:result.update({'state':'timeout','reason':str(exc)})
   except Exception as exc:result.update({'state':'error','reason':f'solver {type(exc).__name__}: {exc}'})
   else:
    try:
     record_solver_direction(local,solved,base,result,mark)
     verify_solution(local,prepared,mods,base)
    except GateReject as exc:
     result.update({'state':'rejected','reason':f'final gate {exc}'})
    except Exception as exc:
     result.update({'state':'error','reason':f'post-solve validation {type(exc).__name__}: {exc}'})
    else:
     try:
       npz=OUT/f'deltas/window-{qid:04d}.npz';nodes=np.asarray(local['nodes'],dtype=np.int32)
       atomic_npz(npz,variables_rc=nodes,B_values_float32=base['heights'][tuple(nodes.T)].astype(np.float32),bounds_float32_inward=np.column_stack((local['lo'],local['hi'])).astype(np.float32),solver_bounds_float32=np.column_stack((local['solverlo'],local['solverhi'])).astype(np.float32),guard_rc=np.asarray(local['guard'],dtype=np.int32),direction_float32=local['direction32'][tuple(nodes.T)].astype(np.float32),final_float32=local['final32'][tuple(nodes.T)].astype(np.float32),stencils_json=stencil_bytes(local['stencils']),descent_witnesses_json=np.frombuffer(canonical_bytes(local['witnesses']),dtype=np.uint8))
       result.update({'state':'accepted','reason':None,'solve_calls':1,'delta_path':str(npz),'delta_sha256':sha(npz),'alpha':local['alpha'],'scalar_rule':local['rule'],'shape':local['shape_report'],'energy_B_fraction':local['energy_B_fraction'],'energy_H_fraction':local['energy_H_fraction'],'focus_hinge_reduction_deg':local['focus_hinge_reduction_deg'],'physics':local['physics'],'final_float32':local['final32'][tuple(nodes.T)].tolist()})
     except Exception as exc:result.update({'state':'error','reason':f'delta write {type(exc).__name__}: {exc}'})
   atomic_json(result_path,result);append_jsonl(OUT/'ledger.jsonl',{'event':'result','queue_id':qid,'state':result['state'],'result_path':str(result_path),'result_sha256':sha(result_path)})
   if result['state'] in ('timeout','error'):failed=True;break
  # No retry of started markers. Do not compose if any work is pending or execution failed.
  result_paths=list((OUT/'results').glob('window-*.json'))
  marker_paths=list((OUT/'attempts').glob('window-*.started.json'))
  results={result_qid(p):json.loads(p.read_text(encoding='utf-8')) for p in result_paths}
  markers={marker_qid(p) for p in marker_paths}
  if set(results)-set(range(EXPECTED_ROWS)) or markers-set(range(EXPECTED_ROWS)):raise RuntimeError('result or attempt marker qid outside the prepared queue')
  for qid,x in results.items():
   if x.get('queue_id')!=qid or x.get('prepared_sha256')!=prepared_sha or x.get('preflight_state')!=prepared['entries'][qid]['preflight_state'] or x.get('state') not in ('accepted','rejected','inconclusive','not_authored','timeout','error'):
    raise RuntimeError(f'invalid result contract for q{qid}')
  missing=set(range(EXPECTED_ROWS))-set(results)
  unresolved=missing or failed or any(results.get(i,{}).get('state') in ('timeout','error') for i in range(EXPECTED_ROWS)) or any(i in markers and i not in results for i in markers)
  if unresolved:
   append_jsonl(OUT/'ledger.jsonl',{'event':'final','status':'INCOMPLETE','prepared_sha256':prepared_sha,'classified_results':len(results),'unprocessed_qids':sorted(missing),'candidate_path':None,'reason':'unprocessed, timeout/error, or started marker without terminal result'})
   atomic_json(OUT/'authoring.json',{'status':'INCOMPLETE','prepared_sha256':prepared_sha,'classified_results':len(results),'unprocessed_qids':sorted(missing),'candidate_path':None,'ledger_sha256':sha(OUT/'ledger.jsonl'),'reason':'unprocessed, timeout/error, or started marker without terminal result'})
   return
  accepted=[results[qid] for qid in sorted(results) if results[qid]['state']=='accepted']
  candidate,ownership=compose_candidate(base,accepted)
  out=OUT/'candidate-terrain.npz';arrays={k:v.copy() for k,v in base.items()};arrays['heights']=candidate;atomic_npz(out,**arrays)
  states={s:sum(1 for x in results.values() if x['state']==s) for s in ('accepted','rejected','inconclusive','not_authored','timeout','error')}
  status='AUTHORED_PENDING_GLOBAL_CONSUMER' if sum(states.values())==EXPECTED_ROWS and not states['timeout'] and not states['error'] else 'INCOMPLETE'
  append_jsonl(OUT/'ledger.jsonl',{'event':'final','status':status,'prepared_sha256':prepared_sha,'candidate_path':str(out),'candidate_sha256':sha(out),'result_counts':states})
  atomic_json(OUT/'authoring.json',{'status':status,'candidate_path':str(out),'candidate_sha256':sha(out),'prepared_sha256':prepared_sha,'ledger_sha256':sha(OUT/'ledger.jsonl'),'index_manifest_sha256':PINS[str(INDEX_MANIFEST)],'index_verification_sha256':PINS[str(INDEX_VERIFICATION)],'source_pins':PINS,'result_counts':states,'changed_vertices':int(np.count_nonzero(candidate!=base['heights'])),'owned_vertices':len(ownership),'candidate_is_acceptance':False})
 finally:
  os.close(lockfd);lock.unlink(missing_ok=True)

def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--execute',action='store_true');p.add_argument('--preflight-ledger',type=Path,default=LEDGER);p.add_argument('--approved-prepared-sha');p.add_argument('--budget-seconds',type=int,default=600);a=p.parse_args()
 if a.prepare:
  versions=require_pins();manifest=prepared_manifest(a.preflight_ledger);OUT.mkdir(parents=True,exist_ok=True);dest=OUT/'prepared.json'
  if dest.exists():raise FileExistsError(f'prepared manifest already exists: {dest}')
  atomic_json(dest,manifest);print(json.dumps({'prepared_path':str(dest),'prepared_sha256':sha(dest),'rows':manifest['entry_count'],'runtime':versions},indent=2))
 else:
  if not a.approved_prepared_sha:raise ValueError('--execute requires --approved-prepared-sha')
  for d in ('results','attempts','deltas'): (OUT/d).mkdir(parents=True,exist_ok=True)
  execute(OUT/'prepared.json',a.approved_prepared_sha,a.budget_seconds)
if __name__=='__main__':main()

