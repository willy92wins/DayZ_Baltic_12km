from __future__ import annotations
import hashlib, importlib.util, json, sys, time
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

D=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/global-operator-prototype/real-sector-preflight')
BASE=Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')
SELECT=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/compound-selection/run-02/selection.json')
SEL_H=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/compound-selection/run-02/candidate-terrain.npz')
PREFLIGHT=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/global-operator-prototype/real-sector-preflight/preflight-run-02/preflight.json')
PREPARED=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/global-operator-prototype/real-sector-preflight/preflight-run-02/prepared.npz')
P=Path(r'E:/DayZ-Baltic-Build/v30-narva-dry-bank-relief-20261010/candidate/plane.npy')
F=Path(r'E:/DayZ-Baltic-Build/v30-narva-dry-bank-relief-20261010/candidate/visible-field.npy')
EV87=Path(r'E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py')
CV=Path(r'E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/review-independent/verify_coverage_contract.py')
IDX=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/ev93-face-index/build_face_index.py')
MANIFEST=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/ev93-face-index/runs/20261010T092417Z-63d4cec3/manifest.json')
INDEX_RUN=MANIFEST.parent
OUT=D/'focus-1981-local-coverage-diagnostic.json'
CELLS=((839,369),(839,370),(840,369),(840,370)); FOCUS=(840,370)
UNK={(839,370),(840,370)}; SHORE={(839,369),(840,369)}
D_DESC=0.45807552337646484
D_OVER_PHYSICAL=2.61210520362854
D_OVER_VISIBLE=2.6246052266322076
EPS={'physical':1e-5,'visible':2e-5}
EXPECTED={
 str(BASE):'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
 str(P):'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
 str(F):'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
 str(EV87):'964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
 str(CV):'214f0eddda08d84ce18c921fcdbe01298f608c9a5c19b7e5246bb9e71df5dc2b',
 str(IDX):'d1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e',
 str(MANIFEST):'c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c',
 str(SELECT):'3b22dcc381b34b8d7c3e6641d3c919658f0fe7377594a859e3d5c064cf92ba0b',
 str(PREFLIGHT):'b7f4295d95b9c2038749b1cda3ec636e4449e77a4847fc87ab1bba81cc97a365',
 str(PREPARED):'8a8a1cf8e9b6906b1aab8053877383d01a92baa5bd2c18b54b1b9e43c8c37a21'
}

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 if not spec or not spec.loader:raise RuntimeError(f'cannot import {path}')
 m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def ar(poly): return 0.0 if poly.is_empty else float(poly.area)
def union_area(polys): return ar(unary_union(polys)) if polys else 0.0
def crossing(q0,q1):
 if q0==0 and q1==0:return None
 if q0==0:return 0.0
 if q1==0:return 1.0
 if (q0<0)==(q1<0):return None
 return float(q0/(q0-q1))
def main():
 t0=time.perf_counter(); own0=sha(Path(__file__).resolve())
 for path,want in EXPECTED.items():
  got=sha(path)
  if got!=want:raise AssertionError(f'PIN DRIFT {path}: {got} != {want}')
 ev=load('local_cov_ev87',EV87); cv=load('local_cov_cv',CV); cv.ev=ev; ixmod=load('local_cov_idx',IDX)
 base=np.load(BASE,allow_pickle=False)['heights']
 p=np.load(P,allow_pickle=False); f=np.load(F,allow_pickle=False)
 sel=json.loads(SELECT.read_text(encoding='utf-8'))
 if sel['candidate']['path']!=str(SEL_H) or sel['candidate']['metadata_equal_to_B'] is not True:raise AssertionError('selection candidate identity/metadata mismatch')
 hsel=np.load(SEL_H,allow_pickle=False)['heights']
 r0,r1,c0,c1=832,849,362,379
 if not np.array_equal(base[r0:r1,c0:c1],hsel[r0:r1,c0:c1]):raise AssertionError('EV93 selection differs from B in focus 17x17; no transfer inference')
 b_local=base[r0:r1,c0:c1]
 pref=json.loads(PREFLIGHT.read_text(encoding='utf-8'))
 if pref['status']!='PREFLIGHT_READY_ONLY' or pref['input_identity']['B_sha256']!=EXPECTED[str(BASE)]:raise AssertionError('preflight identity/status mismatch')
 pzprep=np.load(PREPARED,allow_pickle=False)
 pr0,pr1,pc0,pc1=pref['local_context_rc_half_open']
 if not np.array_equal(base[pr0:pr1,pc0:pc1],pzprep['base_local']):raise AssertionError('preflight base_local differs from pinned B context')
 if float(pzprep['base_local'][FOCUS[0]-pr0,FOCUS[1]-pc0])!=float(base[FOCUS]):raise AssertionError('prepared focus mismatch')
 h=base.copy(); target=float(np.nextafter(np.float32(float(base[FOCUS[0],FOCUS[1]])-D_DESC),np.float32(-np.inf)))
 # Use the previously derived exact target float32, not a second rounding recipe.
 target=3.278029680252075
 h[FOCUS]=np.float32(target)
 over_phys=base.copy(); over_phys[FOCUS]=np.float32(float(base[FOCUS[0],FOCUS[1]])-D_OVER_PHYSICAL)
 over_vis=base.copy(); over_vis[FOCUS]=np.float32(float(base[FOCUS[0],FOCUS[1]])-D_OVER_VISIBLE)
 cells=set(CELLS)
 index=ixmod.FaceRangeIndex(INDEX_RUN)
 # Reuse the verified index's public spatial query, then exact-filter all target cells by polygon intersection.
 faces=index.query_window(min(r for r,c in CELLS),max(r for r,c in CELLS),min(c for r,c in CELLS),max(c for r,c in CELLS))
 target_poly={side:{field:{} for field in ('physical','visible')} for side in ('B','H')}
 for side,ground in [('B',base),('H',h)]:
  for r,c in CELLS:
   target_poly[side]['physical'][(r,c)]=ev.designed_water(r,c,ground,p,f,'P')
   target_poly[side]['visible'][(r,c)]=ev.designed_water(r,c,ground,p,f,'F')
 exp_face={side:{kind:{cell:{} for cell in CELLS} for kind in ('physical','visible')} for side in ('B','H','OVER_PHYSICAL','OVER_VISIBLE')}
 supports={side:{kind:{cell:[] for cell in CELLS} for kind in ('physical','visible')} for side in ('B','H')}
 id_cells={kind:{cell:set() for cell in CELLS} for kind in ('physical','visible')}
 # Use the same native-triangle decomposition, exact ODOL/native intersection and affine clipping APIs as the EV90 consumer.
 for i in range(len(faces['kind'])):
  kind='physical' if int(faces['kind'][i])==0 else 'visible'
  xyz=np.asarray(faces['xyz'][i],dtype=np.float64); face_xy=xyz[:,(0,2)]; face_poly=Polygon(face_xy)
  if bool(faces['degenerate'][i]) or face_poly.is_empty or face_poly.area<=0:continue
  coeff=np.asarray(faces['plane_y_xz'][i],dtype=np.float64)
  key=(int(faces['object_id'][i]),int(faces['model_id'][i]),int(faces['face_id'][i]))
  for r,c in CELLS:
   xy=ev.cell_xy(r,c); ghb=ev.corner_values(base,r,c); ghh=ev.corner_values(h,r,c); ghop=ev.corner_values(over_phys,r,c); ghov=ev.corner_values(over_vis,r,c)
   for ti,tri in enumerate(ev.TRIS):
    ids=np.asarray(tri,dtype=int); native=Polygon(xy[ids]); piece=face_poly.intersection(native)
    if piece.is_empty or piece.area<=0:continue
    id_cells[kind][(r,c)].add(key)
    for side,g in [('B',ghb),('H',ghh),('OVER_PHYSICAL',ghop),('OVER_VISIBLE',ghov)]:
     vis=ev.odol_visible_in_native_tri(face_xy,coeff,xy,g,tri)
     if not vis.is_empty:exp_face[side][kind][(r,c)].setdefault(key,[]).append(vis)
    if kind=='physical': field='physical'
    else: field='visible'
    _,_,tc=cv.cell_tri_target(r,c,field,tri,p,f)
    if tc is not None:
     matched=cv.clip_affine_band(piece,coeff-tc,EPS[kind])
     if not matched.is_empty:
      supports['B'][kind][(r,c)].append(matched);supports['H'][kind][(r,c)].append(matched)
 # Build numerical sign/crossing continuity for all native mesh edges of each known P/F triangle.
 crossing_rows=[]; sign_changed=[]
 for r,c in CELLS:
  g0=ev.corner_values(base,r,c);g1=ev.corner_values(h,r,c); xy=ev.cell_xy(r,c)
  for field,levels in [('P',np.full(4,float(p[r,c])) if np.isfinite(p[r,c]) else None),('F',np.asarray(f[r,c],dtype=np.float64))]:
   if levels is None or (field=='F' and not np.isfinite(levels).all()):continue
   edges=set()
   for tri in ev.TRIS:
    for a,b in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):edges.add(tuple(sorted((int(a),int(b)))))
   for a,b in sorted(edges):
    q0a=float(levels[a]-g0[a]);q0b=float(levels[b]-g0[b]);q1a=float(levels[a]-g1[a]);q1b=float(levels[b]-g1[b])
    s0=(int(np.sign(q0a)),int(np.sign(q0b)));s1=(int(np.sign(q1a)),int(np.sign(q1b)))
    if s0!=s1:sign_changed.append({'field':field,'cell_rc':[r,c],'edge_corner_ids':[a,b],'sign_B':list(s0),'sign_H':list(s1)})
    t0=crossing(q0a,q0b);t1=crossing(q1a,q1b);length=float(np.linalg.norm(xy[a]-xy[b]))
    if t0 is not None or t1 is not None:
     crossing_rows.append({'field':field,'cell_rc':[r,c],'edge_corner_ids':[a,b],'crosses_B':t0 is not None,'crosses_H':t1 is not None,'crossing_shift_m':(None if t0 is None or t1 is None else abs(t1-t0)*length),'B_fraction':t0,'H_fraction':t1,'sign_B':list(s0),'sign_H':list(s1)})
 def summarize(ground,side,kind):
  rows=[]
  for cell in CELLS:
   des=target_poly[side][kind][cell]
   ex_by=exp_face[side][kind][cell]
   face_union=[unary_union(v) for v in ex_by.values() if v]
   exposure_union=unary_union(face_union) if face_union else Polygon()
   sup_list=supports[side][kind][cell]
   sup=unary_union(sup_list) if sup_list else Polygon()
   known=(np.isfinite(p[cell]) if kind=='physical' else np.isfinite(f[cell]).all())
   hole=des.difference(sup) if known else None
   rows.append({'cell_rc':list(cell),'target_known':bool(known),'target_area_m2':ar(des) if known else None,'exposed_area_union_m2':ar(exposure_union),'exposed_area_sum_per_face_m2':sum(ar(x) for x in face_union),'support_union_area_m2':ar(sup),'target_minus_support_hole_m2':ar(hole) if hole is not None else None,'intersecting_faces':len(id_cells[kind][cell]),'exposed_face_count':sum(ar(x)>0 for x in face_union),'exposed_faces':[{'object_id':k[0],'model_id':k[1],'face_id':k[2],'area_m2':ar(unary_union(v))} for k,v in sorted(ex_by.items()) if ar(unary_union(v))>0]})
  known_rows=[x for x in rows if x['target_known']]
  return {'cells':rows,'known_target_area_total_m2':sum(x['target_area_m2'] for x in known_rows),'exposed_area_union_total_m2':sum(x['exposed_area_union_m2'] for x in rows),'support_union_total_m2':sum(x['support_union_area_m2'] for x in rows),'hole_total_m2':sum(x['target_minus_support_hole_m2'] or 0 for x in known_rows),'face_area_sum_total_m2':sum(x['exposed_area_sum_per_face_m2'] for x in rows)}
 summaries={side:{kind:summarize(ground,side,kind) for kind in ('physical','visible')} for side,ground in [('B',base),('H',h)]}
 over_unknown={level:{kind:union_area([poly for cell in UNK for vs in exp_face[level][kind][cell].values() for poly in vs]) for kind in ('physical','visible')} for level in ('OVER_PHYSICAL','OVER_VISIBLE')}
 # area change in known shoreline water fields and separate unexpected exposure into P/F-unknown cells.
 delta={kind:{'target_area_H_minus_B_by_cell':{f'{r},{c}':ar(target_poly['H'][kind][(r,c)])-ar(target_poly['B'][kind][(r,c)]) for r,c in SHORE},'target_area_H_minus_B_total_m2':sum(ar(target_poly['H'][kind][x])-ar(target_poly['B'][kind][x]) for x in SHORE),'exposure_H_minus_B_by_cell':{f'{r},{c}':ar(unary_union([q for vs in exp_face['H'][kind][(r,c)].values() for q in vs]))-ar(unary_union([q for vs in exp_face['B'][kind][(r,c)].values() for q in vs])) for r,c in SHORE}} for kind in ('physical','visible')}
 source_end={p:sha(p) for p in EXPECTED}
 if source_end!={p:want for p,want in EXPECTED.items()}:raise AssertionError('source readset drift')
 if not index.reverify():raise AssertionError('index shard drift')
 own1=sha(Path(__file__).resolve())
 if own0!=own1:raise AssertionError('script drift')
 report={'schema':'focus-1981-local-coverage-diagnostic.v1','status':'LOCAL_DIAGNOSTIC_ONLY','inputs':{**source_end,str(Path(__file__).resolve()):own0},'ev93_local_equals_B':True,'ev93_candidate_path':str(SEL_H),'ev93_candidate_sha256':sel['candidate']['sha256'],'ev93_local_window_rc':[r0,r1,c0,c1],'ev93_changed_vertices_in_local_window':0,'preflight_status':pref['status'],'preflight_context_rc':pref['local_context_rc_half_open'],'preflight_base_local_equals_B':True,'preflight_focus_equals_B':True,'focus_rc':list(FOCUS),'focus_H_height_f32_m':float(h[FOCUS]),'focus_descent_m':float(base[FOCUS]-h[FOCUS]),'cells_rc':[list(x) for x in CELLS],'unknown_PF_cells_rc':[list(x) for x in sorted(UNK)],'existing_shoreline_PF_cells_rc':[list(x) for x in sorted(SHORE)],'target_design_and_support_by_side':summaries,'shoreline_water_area_delta_H_minus_B':delta,'unknown_cell_exposure_H_m2':{kind:sum(ar(unary_union([q for vs in exp_face['H'][kind][cell].values() for q in vs])) for cell in UNK) for kind in ('physical','visible')},'unknown_cell_exposure_overcap_m2':over_unknown,'overcap_test_descent_m':{'physical_bound_plus_0_001':D_OVER_PHYSICAL,'visible_bound_plus_0_001':D_OVER_VISIBLE},'overcap_note':'Over-cap controls test face-uncover detection separately for physical and visible surfaces; diagnostic only, not a candidate/gate.','crossings':{'edge_records':crossing_rows,'sign_changed_edges':sign_changed,'count_records':len(crossing_rows),'count_sign_changed_edges':len(sign_changed),'max_shift_m':max((x['crossing_shift_m'] or 0 for x in crossing_rows),default=0),'all_existing_crossings_preserved':all(x['crosses_B']==x['crosses_H'] for x in crossing_rows)},'geometry_index_rows_in_bbox_query':int(len(faces['kind'])),'index_reverified':True,'elapsed_seconds':time.perf_counter()-t0,'scope_limit':'Only four cells, existing EV93 face index and one in-memory height perturbation; no WRP build, solver, candidate, render, or global acceptance.'}
 # Negative controls: exceeding each independently-derived buried-face cap must reveal the respective static face class.
 if any(report['unknown_cell_exposure_H_m2'][k] > 1e-12 for k in ('physical','visible')):raise AssertionError('proposed H unexpectedly exposes faces in P/F-unknown cells')
 if over_unknown['OVER_PHYSICAL']['physical'] <= 0:raise AssertionError('physical over-cap negative control did not detect exposure')
 if over_unknown['OVER_VISIBLE']['visible'] <= 0:raise AssertionError('visible over-cap negative control did not detect exposure')
 if len(sign_changed) or not report['crossings']['all_existing_crossings_preserved'] or report['crossings']['max_shift_m']>1.0:raise AssertionError('local P/F continuity/crossing gate failed')
 tmp=OUT.with_suffix('.json.tmp');tmp.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8');tmp.replace(OUT)
 print(json.dumps({'status':report['status'],'known_target_area':{s:{k:v['known_target_area_total_m2'] for k,v in x.items()} for s,x in summaries.items()},'holes':{s:{k:v['hole_total_m2'] for k,v in x.items()} for s,x in summaries.items()},'unknown_exposure_H':report['unknown_cell_exposure_H_m2'],'unknown_exposure_overcap':over_unknown,'sign_changed':len(sign_changed),'max_shift':report['crossings']['max_shift_m'],'out':str(OUT)},sort_keys=True))
if __name__=='__main__':main()
