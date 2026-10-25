from __future__ import annotations
import hashlib, importlib.util, json, math, sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon

ROOT=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/global-operator-prototype/real-sector-preflight')
REPRO=ROOT/'reproduce_focus_1981.py'
OUT=ROOT/'focus-1981-univariable-bound.json'
EXPECTED={
 'B':'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
 'P':'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
 'F':'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
 'manifest':'c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c',
 'index_source':'d1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e',
 'diagnosis':'fe48045d979c665b056265f17dcc231f79dd266860d13076025a2eeadf9b3f87',
}
CELLS=((839,369),(839,370),(840,369),(840,370)); FOCUS=(840,370)
TRIS=((0,1,3),(0,2,3)); CORNERS=((0,0),(0,1),(1,0),(1,1))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 if spec is None or spec.loader is None: raise ImportError(path)
 mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
def barycentric(tri_xy, points):
 mat=np.vstack((np.asarray(tri_xy,dtype=np.float64).T,np.ones(3,dtype=np.float64)))
 rhs=np.vstack((np.asarray(points,dtype=np.float64).T,np.ones(len(points),dtype=np.float64)))
 return np.linalg.solve(mat,rhs).T
def main():
 from time import perf_counter
 start=perf_counter(); repro=load_module('focus_repro_bound_source',REPRO)
 base_readset=repro.source_readset()
 for key,want in EXPECTED.items():
  if base_readset.get(key)!=want: raise AssertionError(f'{key} source pin drift: {base_readset.get(key)} != {want}')
 own_start=sha(Path(__file__).resolve())
 ev=repro.load_module('focus_ev87_bound',repro.EV87_PATH)
 ix=repro.load_module('focus_index_bound',repro.INDEX_SOURCE)
 B=np.load(repro.B_PATH,allow_pickle=False)['heights']
 P=np.load(repro.P_PATH,allow_pickle=False); F=np.load(repro.F_PATH,allow_pickle=False)
 index=ix.FaceRangeIndex(repro.INDEX_RUN)
 faces=index.query_window(839,840,369,370)
 rows=[]; baseline_nonburied=[]; max_candidates=0
 for r,c in CELLS:
  xy=ev.cell_xy(r,c); corner_nodes=[(r+dr,c+dc) for dr,dc in CORNERS]
  gh=ev.corner_values(B,r,c)
  cell_candidates=0
  for i in range(len(faces['kind'])):
   xyz=np.asarray(faces['xyz'][i],dtype=np.float64); face_xz=xyz[:,(0,2)]; poly=Polygon(face_xz)
   if bool(faces['degenerate'][i]):
    if poly.intersects(Polygon(xy[[0,1,3]])) or poly.intersects(Polygon(xy[[0,2,3]])):
     raise AssertionError(f'degenerate face intersects cell {(r,c)}')
    continue
   coeff=np.asarray(faces['plane_y_xz'][i],dtype=np.float64)
   if np.max(np.abs(repro.face_eval(coeff,face_xz)-xyz[:,1]))>2e-6: raise AssertionError('plane mismatch')
   for ti,tri in enumerate(TRIS):
    ids=np.asarray(tri,dtype=np.intp); overlap=poly.intersection(Polygon(xy[ids]))
    if overlap.is_empty: continue
    cell_candidates+=1
    pts=np.asarray(repro.geom_coords(overlap),dtype=np.float64)
    if len(pts)==0: raise AssertionError('intersection without vertices')
    gc=ev.affine_coeff(xy[ids],gh[ids]); clearance=repro.face_eval(gc,pts)-repro.face_eval(coeff,pts)
    tri_nodes=[corner_nodes[j] for j in tri]
    if FOCUS in tri_nodes:
     fi=tri_nodes.index(FOCUS); weights=barycentric(xy[ids],pts)[:,fi]
    else: weights=np.zeros(len(pts),dtype=np.float64)
    if np.min(weights)<-1e-10 or np.max(weights)>1+1e-10: raise AssertionError(f'barycentric out of range {weights}')
    weights=np.where((weights<0)&(weights>=-1e-10),0.0,weights)
    weights=np.where((weights>1)&(weights<=1+1e-10),1.0,weights)
    ratios=[]
    for j,(pt,cl,lam) in enumerate(zip(pts,clearance,weights)):
     if cl<=0: baseline_nonburied.append({'cell_rc':[r,c],'kind':'physical' if int(faces['kind'][i])==0 else 'visible','object_id':int(faces['object_id'][i]),'model_id':int(faces['model_id'][i]),'face_id':int(faces['face_id'][i]),'tri':ti,'point_xz_m':pt.tolist(),'clearance_m':float(cl),'focus_weight':float(lam)})
     if lam>0:
      ratios.append(float(cl/lam))
    row={'cell_rc':[r,c],'kind':'physical' if int(faces['kind'][i])==0 else 'visible','object_id':int(faces['object_id'][i]),'model_id':int(faces['model_id'][i]),'face_id':int(faces['face_id'][i]),'native_triangle':ti,'overlap_geom':overlap.geom_type,'intersection_area_xz_m2':float(overlap.area),'intersection_vertices':len(pts),'minimum_clearance_m':float(np.min(clearance)),'max_focus_barycentric_weight':float(np.max(weights)),'min_focus_bound_m':min(ratios) if ratios else None,'limiting_vertex':({'point_xz_m':pts[int(np.argmin(np.where(weights>0,clearance/np.where(weights>0,weights,1),np.inf)))].tolist(),'clearance_m':float(clearance[int(np.argmin(np.where(weights>0,clearance/np.where(weights>0,weights,1),np.inf)))]),'focus_weight':float(weights[int(np.argmin(np.where(weights>0,clearance/np.where(weights>0,weights,1),np.inf)))])} if ratios else None)}
    rows.append(row)
  max_candidates=max(max_candidates,cell_candidates)
 if not rows: raise AssertionError('no exact face intersections')
 kinds={k:[x for x in rows if x['kind']==k] for k in ('physical','visible')}
 unknown_set={(839,370),(840,370)}
 shoreline_set={(839,369),(840,369)}
 shoreline_summary={}
 for kind,rs in kinds.items():
  shore=[x for x in rs if tuple(x['cell_rc']) in shoreline_set]
  shoreline_summary[kind]={'face_native_triangle_intersections':len(shore),'baseline_nonburied_vertices':sum(1 for x in baseline_nonburied if x['kind']==kind and tuple(x['cell_rc']) in shoreline_set),'minimum_ground_minus_face_m':min((x['minimum_clearance_m'] for x in shore),default=None),'note':'finite P/F shoreline cells; not treated as an all-buried domain; evaluate existing crossing and design-band coverage gates'}
 unknown_set={(839,370),(840,370)}
 unknown_rows=[x for x in rows if tuple(x['cell_rc']) in unknown_set]
 unknown_nonburied=[x for x in baseline_nonburied if tuple(x['cell_rc']) in unknown_set]
 combined=[(x['kind'],x) for x in unknown_rows if x['min_focus_bound_m'] is not None]
 unknown_bounds_by_kind={}
 for kind in ('physical','visible'):
  candidates=[x for x in unknown_rows if x['kind']==kind and x['min_focus_bound_m'] is not None]
  limiter=min(candidates,key=lambda x:x['min_focus_bound_m']) if candidates else None
  unknown_bounds_by_kind[kind]={'face_native_triangle_intersections':sum(1 for x in unknown_rows if x['kind']==kind),'strict_bound_m':(0.0 if any(x['kind']==kind for x in unknown_nonburied) else (limiter['min_focus_bound_m'] if limiter else None)),'limiting_face_triangle':limiter}
 strict_bound=(0.0 if unknown_nonburied else min((x['min_focus_bound_m'] for _,x in combined),default=None))
 qreq_ew=.25*(float(B[840,370])-max(float(B[840,369]),float(B[840,371])))
 qreq_ns=.25*(float(B[840,370])-max(float(B[839,370]),float(B[841,370])))
 ew_high=max(float(B[840,369]),float(B[840,371])); ns_high=max(float(B[839,370]),float(B[841,370]))
 target_h=min(ew_high+.75*(float(B[840,370])-ew_high),ns_high+.75*(float(B[840,370])-ns_high))
 target_h_f32=float(np.nextafter(np.float32(target_h),np.float32(-np.inf)))
 quantized_descent=float(np.float32(B[840,370]))-target_h_f32
 target_prom={'EW':target_h_f32-ew_high,'NS':target_h_f32-ns_high}
 target_reduction={'EW':1.0-target_prom['EW']/(float(B[840,370])-ew_high),'NS':1.0-target_prom['NS']/(float(B[840,370])-ns_high)}
 p=np.asarray(P,dtype=np.float64); f=np.asarray(F,dtype=np.float64)
 # Reproduce each unique P/F edge incident to the focus in the four cells.
 crossing=[]; seen=set()
 for r,c in CELLS:
  xy=ev.cell_xy(r,c); gh=ev.corner_values(B,r,c); node_xy=[(r+dr,c+dc) for dr,dc in CORNERS]
  for tri in TRIS:
   for ai,bi in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
    na,nb=node_xy[ai],node_xy[bi]
    if FOCUS not in (na,nb): continue
    fi=ai if na==FOCUS else bi; oi=bi if fi==ai else ai
    edge=tuple(sorted((na,nb))); length=float(np.linalg.norm(xy[fi]-xy[oi]))
    for name,levels in [('P',np.full(4,float(p[r,c])) if np.isfinite(p[r,c]) else None),('F',f[r,c])]:
     if levels is None or (name=='F' and (not np.isfinite(levels[fi]) or not np.isfinite(levels[oi]))): continue
     q0=float(levels[fi]-gh[fi]); q1=float(levels[oi]-gh[oi])
     if q0*q1>=0: continue
     key=(name,(r,c),edge)
     if key in seen: continue
     seen.add(key)
     t0=q0/(q0-q1)
     def shift(d):
      qd=q0+d
      if qd*q1>=0:return None
      td=qd/(qd-q1)
      return length*abs(td-t0)
     tests={str(float(d)):shift(float(d)) for d in (qreq_ew,qreq_ns,quantized_descent,strict_bound) if d is not None}
     crossing.append({'field':name,'cell_rc':[r,c],'edge_rc':[list(edge[0]),list(edge[1])],'length_m':length,'q_focus_before_m':q0,'q_neighbor_m':q1,'shift_m_by_test_descent':tests})
 index_ok=bool(index.reverify())
 final_readset=repro.source_readset()
 own_end=sha(Path(__file__).resolve())
 if not index_ok or base_readset!=final_readset or own_start!=own_end: raise AssertionError('source/index drift')
 report={'schema':'focus-1981-univariable-clearance-bound.v2','status':'BOUND_DERIVED_LOCAL_ONLY','inputs':{**base_readset,'analysis_script':own_start},'readset_stable':True,'index_reverified':True,'focus_rc':list(FOCUS),'cells_rc':[list(x) for x in CELLS],'candidate_face_records_in_query':len(faces['kind']),'face_native_triangle_intersections':len(rows),'baseline_nonburied_intersection_vertices_all_cells':len(baseline_nonburied),'baseline_nonburied_intersection_vertices_by_cell':{f'{r},{c}':sum(1 for x in baseline_nonburied if x['cell_rc']==[r,c]) for r,c in CELLS},'baseline_nonburied_examples':baseline_nonburied[:6],'buried_PF_unknown_cells_only_rc':[list(x) for x in sorted(unknown_set)],'shoreline_PF_crossing_cells_rc':[list(x) for x in sorted(shoreline_set)],'shoreline_face_diagnostic':shoreline_summary,'buried_unknown_cells_intersection_count':len(unknown_rows),'buried_unknown_cells_baseline_nonburied_vertices':len(unknown_nonburied),'strict_burial_bound_m_unknown_cells_by_surface':unknown_bounds_by_kind,'strict_burial_bound_m_unknown_cells_physical_visible':strict_bound,'focus_only_25pct_required_descent_m':{'EW':qreq_ew,'NS':qreq_ns,'both_axes':max(qreq_ew,qreq_ns)},'float32_focus_target':{'target_height_before_cast_m':target_h,'chosen_float32_height_m':target_h_f32,'descent_m':quantized_descent,'final_prominence_m':target_prom,'reduction_fraction':target_reduction,'strict_burial_margin_remaining_m':(strict_bound-quantized_descent if strict_bound is not None else None)},'focus_only_25pct_feasible_under_burial_bound':bool(strict_bound is not None and quantized_descent<strict_bound),'crossing_shift_tests':crossing,'interpretation':'For each exact face/native-triangle intersection in the two P/F-all-NaN cells, clearance-d*lambda_focus remains affine. The strict buried-area bound is d < min(clearance/lambda_focus) over intersection vertices with lambda_focus>0; lambda=0 imposes no lowering bound. This is a sufficient local bound, not the exact maximum under coverage policy. The other two cells have finite P/F and are existing shoreline; they are assessed by sign/crossing displacement and exact coverage, not forced to constant exposed area.' ,'elapsed_seconds':None}
 report['elapsed_seconds']=__import__('time').perf_counter()-start
 OUT.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 print(json.dumps({'status':report['status'],'faces':len(rows),'bound':strict_bound,'required':report['focus_only_25pct_required_descent_m'],'feasible':report['focus_only_25pct_feasible_under_bound'],'elapsed':report['elapsed_seconds'],'out':str(OUT)},sort_keys=True))
if __name__=='__main__': main()






