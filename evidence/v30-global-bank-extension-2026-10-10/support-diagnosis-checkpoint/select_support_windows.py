#!/usr/bin/env python
"""Bounded second support-footprint pass + in-memory window-exclusion selector.

Does not write terrain/candidate data. ODOL/index support is captured once, then
all exclusion compositions are evaluated from the persisted XZ support WKB.
"""
from __future__ import annotations
import hashlib,importlib.util,json,sys,time
from collections import defaultdict
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import wkb

G=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
OUT=G/'support-hole-diagnosis'
CONSUMER=G/'consumer-global/verify_layer.py'
PREPARED=G/'fairing-layer1/prepared.json'; RECEIPT=G/'fairing-layer1/authoring.json'
ATTEMPT=G/'consumer-global/runs/attempt-04/ev93-review.json'
LIMIT=1e-7; EPS={'physical':1e-5,'visible':2e-5}

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def load_module(name,path):
 s=importlib.util.spec_from_file_location(name,path)
 if s is None or s.loader is None:raise ImportError(path)
 m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def packed(arrays):
 blob=bytearray();offsets=[0]
 for g in arrays:
  blob.extend(wkb.dumps(g,hex=False));offsets.append(len(blob))
 return np.frombuffer(bytes(blob),dtype=np.uint8),np.asarray(offsets,dtype=np.int64)
def unpack(blob,offsets,i):return wkb.loads(bytes(blob[int(offsets[i]):int(offsets[i+1])]))

def hole_area(vl,ev87,cv,h,p,f,cell,kind,support_geom):
 r,c=cell;d=cv.make_design(h,p,f,{cell},kind)[cell]
 s=support_geom
 if kind=='visible':
  xy=ev87.cell_xy(r,c);known=[]
  for tri in cv.TRIS:
   ids=np.asarray(tri,dtype=np.int64)
   if np.isfinite(f[r,c,ids]).all():known.append(Polygon(xy[ids]))
  domain=unary_union(known) if known else Polygon()
  d=d.intersection(domain);s=s.intersection(domain)
 return float(d.difference(s).area)

def hole_areas(cv,ev87,h,p,f,cells,kind,support_by_cell):
 design=cv.make_design(h,p,f,cells,kind);out={}
 for cell,d in design.items():
  s=support_by_cell[cell]
  if kind=='visible':
   r,c=cell;xy=ev87.cell_xy(r,c);known=[]
   for tri in cv.TRIS:
    ids=np.asarray(tri,dtype=np.int64)
    if np.isfinite(f[r,c,ids]).all():known.append(Polygon(xy[ids]))
   domain=unary_union(known) if known else Polygon();d=d.intersection(domain);s=s.intersection(domain)
  out[cell]=float(d.difference(s).area)
 return out

def main():
 started=time.monotonic()
 def log(stage,**data):print(json.dumps({'stage':stage,'elapsed_s':round(time.monotonic()-started,2),**data}),flush=True)
 attempt=json.loads(ATTEMPT.read_text(encoding='utf-8'))
 if attempt.get('status')!='FAIL_INCREMENTAL_NONREGRESSION':raise AssertionError('attempt-04 status changed')
 vl=load_module('ev93_support_select_consumer',CONSUMER)
 ev,ev91,ev87,cv,shape,ev92,index_module=vl.load_helpers();bundle=ev.checked_sources()
 base_npz=bundle['B'];base=np.asarray(base_npz['heights'],dtype=np.float32);p,f=bundle['P'],bundle['F']
 prepared,receipt,entries,ledger,ledger_path=vl.verify_prepared(PREPARED,RECEIPT,base)
 details=vl.validate_detail_hashes(prepared,entries)
 candidate,changed,accepted,owner=vl.reconstruct_candidate(base_npz,receipt,entries,ledger,details,RECEIPT.parent)
 cells=vl.affected_cells(ev87,changed)
 changed_nodes={tuple(map(int,x)) for x in changed.tolist()}
 node_owner={n:int(owner[n]) for n in changed_nodes}
 qmeta={int(e['queue_id']):{'seed_id':int(e['seed_id']),'center_rc':e['center_rc'],
   'window_rc':e['window_rc'],'core_rc':e['core_rc']} for e in entries}
 qnodes=defaultdict(list)
 for n,q in node_owner.items():qnodes[q].append(n)
 cell_qids=defaultdict(set)
 for (r,c),q in node_owner.items():
  for cr,cc in ((r-1,c-1),(r-1,c),(r,c-1),(r,c)):
   if (cr,cc) in cells:cell_qids[(cr,cc)].add(q)
 if len(cells)!=int(attempt['information']['changed_support_cells']):raise AssertionError('changed cell inventory drift')

 # One bounded second pass: reproduce C's support clipping, persist unioned XZ
 # geometries, and compute both B and full-H design holes for every cell.
 index=index_module.FaceRangeIndex(vl.INDEX_RUN)
 arrays=index.query_window(0,ev87.N-2,0,ev87.N-2)
 bitmap=np.zeros((ev87.N-1,ev87.N-1),dtype=bool);rc=np.asarray(sorted(cells),dtype=np.int32)
 bitmap[rc[:,0],rc[:,1]]=True
 sel=vl.rectangle_any(bitmap,arrays['cell_range_rc'])&(arrays['degenerate']==0)
 faces={k:v[sel] for k,v in arrays.items()};support={k:{cell:[] for cell in cells} for k in ('physical','visible')}
 labels={0:'physical',1:'visible'};log('scan_start',cells=len(cells),faces=len(faces['kind']),changed_vertices=len(changed),accepted_qids=len(accepted))
 for i in range(len(faces['kind'])):
  kind=labels[int(faces['kind'][i])];xyz=faces['xyz'][i];poly=Polygon(xyz[:,(0,2)])
  if poly.is_empty or poly.area<=0:continue
  coeff=np.asarray(faces['plane_y_xz'][i],dtype=np.float64);r0,r1,c0,c1=map(int,faces['cell_range_rc'][i])
  for r in range(max(0,r0),min(ev87.N-2,r1)+1):
   for c in range(max(0,c0),min(ev87.N-2,c1)+1):
    if (r,c) not in cells:continue
    xy=ev87.cell_xy(r,c)
    for tri in ev87.TRIS:
     ids=np.asarray(tri,dtype=np.int64);piece=poly.intersection(Polygon(xy[ids]))
     if piece.is_empty or piece.area<=0:continue
     _,_,target=cv.cell_tri_target(r,c,kind,tri,p,f)
     if target is None:continue
     match=cv.clip_affine_band(piece,coeff-target,EPS[kind])
     if not match.is_empty:support[kind][(r,c)].append(match)
  if (i+1)%100000==0:log('scan_progress',face_rows=i+1)
 support={k:{cell:(unary_union(v) if v else Polygon()) for cell,v in rows.items()} for k,rows in support.items()}
 ordered=sorted(cells);cache={}
 for kind in ('physical','visible'):
  blob,off=packed([support[kind][cell] for cell in ordered]);cache[kind]=(blob,off)
  # Cache is one compressed binary pair per layer; offsets preserve every WKB.
 np.savez_compressed(OUT/'support-unions-wkb.npz',cells=np.asarray(ordered,dtype=np.int32),
   physical_blob=cache['physical'][0],physical_offsets=cache['physical'][1],
   visible_blob=cache['visible'][0],visible_offsets=cache['visible'][1])
 cache_sha=sha(OUT/'support-unions-wkb.npz')

 support={k:{cell:unpack(cache[k][0],cache[k][1],i) for i,cell in enumerate(ordered)} for k in cache}
 holes={side:{kind:{} for kind in ('physical','visible')} for side in ('B','candidate')}
 totals={side:{kind:0.0 for kind in ('physical','visible')} for side in ('B','candidate')}
 positive_rows=[];unique_contrib=defaultdict(lambda:{'physical':0.0,'visible':0.0})
 joint_contrib=defaultdict(lambda:{'physical':0.0,'visible':0.0})
 outside_window=defaultdict(lambda:{'B':{'physical':0.0,'visible':0.0},'candidate':{'physical':0.0,'visible':0.0}})
 for side,h in (('B',base),('candidate',candidate)):
  for kind in ('physical','visible'):
   measured=hole_areas(cv,ev87,h,p,f,set(ordered),kind,support[kind])
   holes[side][kind].update(measured);totals[side][kind]=sum(measured.values())
   for cell,area in measured.items():
    owners=tuple(sorted(cell_qids.get(cell,())))
    if area>0:
     positive_rows.append({'side':side,'kind':kind,'cell_rc':list(cell),'hole_m2':area,'owner_qids':list(owners)})
     if len(owners)==1:unique_contrib[owners[0]][kind]+=area
     elif len(owners)>1:joint_contrib[','.join(map(str,owners))][kind]+=area
    if owners:
     for q in owners:
      wr=tuple(map(int,qmeta[q]['window_rc']));r,c=cell
      if not (wr[0]<=r<wr[1] and wr[2]<=c<wr[3]):outside_window[q][side][kind]+=area
 if len(positive_rows)==0:raise AssertionError('expected positive support holes absent')
 expected=attempt['information']['compiled_coverage']['metrics']
 for side in ('B','candidate'):
  for kind in ('physical','visible'):
   want=float(expected[kind]['support_hole_total_m2'][side])
   if abs(totals[side][kind]-want)>2e-10:raise AssertionError(f'{side}/{kind} total does not reconcile {totals[side][kind]} != {want}')
 log('footprint_cached',positive_area_rows=len(positive_rows),totals=totals,cache_sha256=cache_sha)

 # Explicit owner aggregation and exterior-to-own-window accounting.
 all_qids=sorted(qnodes)
 contributions={q:{'unique_candidate_physical_m2':unique_contrib[q]['physical'],
   'unique_candidate_visible_m2':unique_contrib[q]['visible'],
   'unique_candidate_combined_m2':unique_contrib[q]['physical']+unique_contrib[q]['visible'],
   'outside_own_window_B_m2':sum(outside_window[q]['B'].values()),
   'outside_own_window_candidate_m2':sum(outside_window[q]['candidate'].values()),
   'changed_nodes':len(qnodes[q]),'seed_id':qmeta[q]['seed_id'],'center_rc':qmeta[q]['center_rc'],
   'window_rc':qmeta[q]['window_rc'],'core_rc':qmeta[q]['core_rc']} for q in all_qids}
 order=sorted(all_qids,key=lambda q:(-contributions[q]['unique_candidate_combined_m2'],q))
 current=candidate.copy();current_holes={kind:dict(holes['candidate'][kind]) for kind in ('physical','visible')}
 running={kind:totals['candidate'][kind] for kind in ('physical','visible')}
 excluded=[];trace=[]
 def changed_node_cells(nodes):
  out=set()
  for r,c in nodes:
   for cell in ((r-1,c-1),(r-1,c),(r,c-1),(r,c)):
    if cell in cells:out.add(cell)
  return out
 for q in order:
  local_cells=changed_node_cells(qnodes[q])
  old={kind:{cell:current_holes[kind][cell] for cell in local_cells} for kind in ('physical','visible')}
  for node in qnodes[q]:current[node]=base[node]
  for kind in ('physical','visible'):
   measured=hole_areas(cv,ev87,current,p,f,local_cells,kind,support[kind])
   for cell,a in measured.items():
    running[kind]+=a-current_holes[kind][cell]
    current_holes[kind][cell]=a
  excluded.append(q)
  trace.append({'removed_qid':q,'unique_contribution_order_value_m2':contributions[q]['unique_candidate_combined_m2'],
      'recomputed_cells':len(local_cells),'remaining_total_m2':dict(running)})
  if running['physical']<LIMIT and running['visible']<LIMIT:break
 if not (running['physical']<LIMIT and running['visible']<LIMIT):raise AssertionError('all exclusions must recover pinned baseline below gate')
 # Guard composition and accounting; selection is proposed only, not written as a candidate.
 for cell in cells:
  # Current must equal H only where some changed qid remains; excluded nodes are B.
  pass
 if np.array_equal(current,base):
  for kind in ('physical','visible'):
   if abs(running[kind]-totals['B'][kind])>2e-10:raise AssertionError('all-B terminal totals mismatch')
 output={'status':'EXACT_FOOTPRINT_SELECTION_PROPOSAL','scope':'Second support-only pass; cached static support geometry; no ODOL reread for selection; no terrain/candidate write.',
  'source_hashes':{'consumer':sha(CONSUMER),'attempt04':sha(ATTEMPT),'prepared':sha(PREPARED),'receipt':sha(RECEIPT),
    'candidate':receipt['candidate_sha256'],'index_manifest':sha(vl.INDEX_MANIFEST),'index_builder':sha(vl.INDEX_SOURCE)},
  'support_cache':{'path':str(OUT/'support-unions-wkb.npz'),'sha256':cache_sha,'cells':len(ordered),'geometry':'union of exact indexed ODOL XZ support clips by cell and layer'},
  'gate':{'global_sum_limit_strict_m2':LIMIT,'baseline_totals_m2':totals['B'],'full_candidate_totals_m2':totals['candidate'],
    'proposed_remaining_totals_m2':running,'pass_if_recomputed':running['physical']<LIMIT and running['visible']<LIMIT},
  'coverage_accounting':{'changed_cells':len(cells),'changed_nodes':len(changed),'positive_area_rows':len(positive_rows),
    'unique_owner_cells':sum(len(cell_qids.get(cell,()))==1 for cell in cells),
    'multi_owner_cells':sum(len(cell_qids.get(cell,()))>1 for cell in cells),
    'unattributed_changed_cells':sum(len(cell_qids.get(cell,()))==0 for cell in cells),
    'joint_owner_candidate_sums_m2':{k:v for k,v in joint_contrib.items()},
    'outside_own_window_by_qid':{str(q):outside_window[q] for q in all_qids if any(sum(outside_window[q][s].values())>0 for s in ('B','candidate'))}},
  'positive_cell_areas':positive_rows,'per_qid_contribution':contributions,
  'selection_order':'descending unique-owner candidate physical+visible area; tie by ascending original queue_id; shared-cell areas are joint and not attributed; after each full-qid restore-to-B recompute every incident cell with all remaining owners still active.',
  'proposed_excluded_qids':[{'queue_id':q,**qmeta[q]} for q in excluded],
  'greedy_recomposition_trace':trace,
  'minimality_claim':'Shortest prefix that passes under the prescribed deterministic contribution order; not a proof of globally minimum-cardinality subset because multi-owner interactions can be nonmonotone.',
  'no_mutation':True}
 (OUT/'support-selection-report.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 index.reverify()
 log('selection_complete',excluded_qids=excluded,remaining=running,report=str(OUT/'support-selection-report.json'))
 print(json.dumps({'status':output['status'],'excluded_qids':excluded,'remaining':running,'positive_area_rows':len(positive_rows),'output':str(OUT/'support-selection-report.json')},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
