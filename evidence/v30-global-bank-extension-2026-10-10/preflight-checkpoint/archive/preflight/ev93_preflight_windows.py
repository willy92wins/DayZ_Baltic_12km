from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, sys, time
from pathlib import Path
import numpy as np
ROOT=Path(r'E:/DayZ-Baltic-Build'); EV93=ROOT/'v30-global-bank-extension-20261010'; OUT=EV93/'preflight'
QUEUE=EV93/'queue/queue.json'; PLAN=EV93/'plan.md'; PREFLIGHT_PLAN=EV93/'preflight-plan.md'
INDEX_SOURCE=EV93/'ev93-face-index/build_face_index.py'; INDEX_FIXTURE=EV93/'ev93-face-index/test_face_range_index.py'
INDEX_RUN=EV93/'ev93-face-index/runs/20261010T092417Z-63d4cec3'
INDEX_VERIFICATION=EV93/'review-independent/runs/attempt-01/verification.json'
INDEX_VERIFICATION_SHA256='b498e7d68835b199399655451e5e01ac81acb3149dbb9bf882b94858141521d4'
EV87_SOURCE=ROOT/'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
EV90_PATH=ROOT/'v30-wide-bank-fairing-pilot-20261010/next-method-preflight/ev90_preflight.py'
EV90_REPORT=ROOT/'v30-wide-bank-fairing-pilot-20261010/next-method-preflight/preflight.json'
EV91_AUTHOR=ROOT/'v30-wide-bank-fairing-pilot-20261010/ev91-descent/author_ev91.py'
EV91_GUARD=ROOT/'v30-wide-bank-fairing-pilot-20261010/ev91-descent/collar-guard-preflight.json'
EV91_PREPARED=ROOT/'v30-wide-bank-fairing-pilot-20261010/ev91-descent/prepared.json'
EV88_AUTHOR=ROOT/'v30-wide-bank-fairing-pilot-20261010/author/author_ev88q.py'
PILOT=(840,370); BUDGET=600
PINS={str(PLAN):'ccc018a9e1cc8a51b075a91905b1cbe7d3cdaf72040e51992f2ac55db8ad7e82',
str(PREFLIGHT_PLAN):'44022291bdbeba62b924b5bf37655f1e8fefd5dee2ba28cd72c71a02ca0049ea',
str(INDEX_SOURCE):'d1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e',
str(INDEX_FIXTURE):'c17cbe82ab701e89ba999fec1c9f1e4a00f1a66ecc5658a01941c9e9c55db6ce',
str(EV87_SOURCE):'964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
str(EV90_PATH):'5892e917335ca2d8caa427f04f48ba8acbd8e16a5e1b400be596d5dd636afb7f',
str(EV90_REPORT):'8c8ec80cbb7029f510c832adf90a8871e385fbd8ec52ee5043d5ea24e1099d63',
str(EV91_AUTHOR):'d17e358e9e9e92952e51e008148b534c2fde4a3ae7fe1e4197fdab4215adc9f1',
str(EV91_GUARD):'1f1e68cf1b2358c2bb5d21d9268cfd2f030b46b6d7247227bc55be0efe2fc0df',
str(EV91_PREPARED):'127b906c1d2a5d2aa09172ed47dac16cd489aae6a2955428a96166a325605877',
str(EV88_AUTHOR):'532373b56c27ec0a04345c1c09a5cc6ff04fef34c04ac2856ce65ceb395162d1'}

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 if spec is None or spec.loader is None:raise ImportError(str(path))
 mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
def check_pins():
 return {p:(want,sha(p)) for p,want in PINS.items() if sha(p)!=want}
class WindowScope:
 def __init__(self,ev,center):self.ev=ev;self.center=tuple(map(int,center));self.old=None
 def __enter__(self):
  r,c=self.center;self.old=(self.ev.WINDOW,self.ev.CORE,self.ev.FOCUS)
  self.ev.WINDOW=(r-8,r+9,c-8,c+9);self.ev.CORE=(r-6,r+7,c-6,c+7);self.ev.FOCUS=(r,c);return self.ev
 def __exit__(self,*exc):self.ev.WINDOW,self.ev.CORE,self.ev.FOCUS=self.old;return False
def enumerate_stencils(nodes,window):
 r0,r1,c0,c1=map(int,window);vset={tuple(map(int,x)) for x in nodes};out=[]
 for r in range(r0,r1):
  for c in range(c0,c1-2):
   if any(x in vset for x in ((r,c),(r,c+1),(r,c+2))):out.append(('xx',r,c))
 for r in range(r0,r1-2):
  for c in range(c0,c1):
   if any(x in vset for x in ((r,c),(r+1,c),(r+2,c))):out.append(('zz',r,c))
 for r in range(r0,r1-2):
  for c in range(c0,c1-2):
   if any(x in vset for x in ((r,c),(r,c+2),(r+2,c),(r+2,c+2))):out.append(('xz',r,c))
 return out
def _cell_box(ev,r,c):
 from shapely.geometry import box
 return box(c*ev.CELL,ev.Z0-(r+1)*ev.CELL,(c+1)*ev.CELL,ev.Z0-r*ev.CELL)
def _tri_poly(ev,r,c,tri):
 from shapely.geometry import Polygon
 return Polygon(ev.grid_xy(r,c)[np.asarray(tri,dtype=np.int64)])
def _cells(ev,w):
 r0,r1,c0,c1=w
 return [(r,c) for r in range(r0,r1-1) for c in range(c0,c1-1)]
def _cell_map(m):return {k:sorted([list(map(int,x)) for x in m[k]]) for k in ('physical','visible')}
def scan_face_rows(ev,rows,src,window,model_names):
 """Apply EV90 clipping to EV93 bbox candidates; retain every area > 0.0."""
 from shapely.geometry import Polygon
 r0,r1,c0,c1=window;p,f=src['P'],src['F'];above={'physical':{},'visible':{}};unknown={'physical':{},'visible':{}}
 face_n={'physical':0,'visible':0};exceed={'physical':0,'visible':0};deg_n={'physical':0,'visible':0};objects=set();seen=set()
 cellpoly={};tripoly={}
 for r,c in _cells(ev,window):
  cellpoly[r,c]=_cell_box(ev,r,c)
  for ti,tri in enumerate(ev.TRIS):tripoly[r,c,ti]=_tri_poly(ev,r,c,tri)
 for i in range(len(rows['kind'])):
  kid=int(rows['kind'][i]);kind='physical' if kid==0 else 'visible';oid=int(rows['object_id'][i]);mid=int(rows['model_id'][i]);fid=int(rows['face_id'][i])
  ident=(kid,oid,fid)
  if ident in seen:raise AssertionError(f'duplicate indexed face {ident}')
  seen.add(ident);name=model_names.get(mid);expected=src['object_to_model'].get(oid)
  if name is None or name!=expected:raise AssertionError(f'index object/model mismatch {oid}/{mid}')
  if fid>=src['model_face_counts'][(name,kind)]:raise AssertionError(f'face id outside LOD {name}/{kind}/{fid}')
  xyz=np.asarray(rows['xyz'][i],dtype=np.float64);plane=np.asarray(rows['plane_y_xz'][i],dtype=np.float64);area0=float(rows['area_xz'][i]);deg=bool(rows['degenerate'][i])
  if xyz.shape!=(3,3) or plane.shape!=(3,) or not np.isfinite(xyz).all() or not np.isfinite(plane).all():raise AssertionError('invalid indexed face row')
  if deg!=(area0<=0.):raise AssertionError('degenerate flag/area mismatch')
  if deg:deg_n[kind]+=1;continue
  face=Polygon(xyz[:,(0,2)])
  if not face.is_valid or face.area<=0.:raise AssertionError('positive indexed area is not valid polygon')
  if not math.isclose(float(face.area),area0,rel_tol=0.,abs_tol=1e-12):raise AssertionError('indexed projected area mismatch')
  if np.max(np.abs(xyz[:,(0,2)]@plane[:2]+plane[2]-xyz[:,1]))>1e-8:raise AssertionError('stored affine plane fails vertex interpolation')
  cr0,cr1,cc0,cc1=map(int,rows['cell_range_rc'][i])
  if (cr0,cr1,cc0,cc1)==(-1,-1,-1,-1):continue
  rr0,rr1=max(r0,cr0),min(r1-2,cr1);cc0,cc1=max(c0,cc0),min(c1-2,cc1)
  if rr0>rr1 or cc0>cc1:continue
  for r in range(rr0,rr1+1):
   for c in range(cc0,cc1+1):
    over=face.intersection(cellpoly[r,c])
    if over.is_empty or over.area<=0.:continue
    objects.add(oid);face_n[kind]+=1
    if kind=='physical':
     level=float(p[r,c]);pts=ev.ring_points(over)
     if not math.isfinite(level):
      for ti,tri in enumerate(ev.TRIS):
       piece=over.intersection(tripoly[r,c,ti])
       if piece.is_empty or piece.area<=0.:continue
       unknown[kind].setdefault((r,c),[]).append({'cell':[r,c],'object':name,'face':fid,'triangle':ti,'area_m2':float(piece.area),'reason':'P_NaN_domain','face_plane_coeff_xz':plane.tolist(),'intersection_xz':ev.ring_points(piece).tolist()})
      continue
     ex=float(np.max(pts@plane[:2]+plane[2]-level))
     if ex>ev.EPS[kind]:
      above[kind].setdefault((r,c),[]).append({'cell':[r,c],'object':name,'face':fid,'max_excess_m':ex,'overlap_area_m2':float(over.area),'face_plane_coeff_xz':plane.tolist(),'intersection_xz':ev.ring_points(over).tolist()});exceed[kind]+=1
    else:
     for ti,tri in enumerate(ev.TRIS):
      piece=over.intersection(tripoly[r,c,ti])
      if piece.is_empty or piece.area<=0.:continue
      offsets=np.asarray(tri,dtype=np.int64);fv=np.asarray(f[r,c,offsets],dtype=np.float64);pts=ev.ring_points(piece);tri_xy=ev.grid_xy(r,c)[offsets];area=float(piece.area)
      if not np.isfinite(fv).all():
       h=src['B']['heights'];bh4=np.asarray([h[r,c],h[r,c+1],h[r+1,c],h[r+1,c+1]],dtype=np.float64);g=ev.affine(tri_xy,bh4[list(tri)]);bmax=float(np.max(pts@plane[:2]+plane[2]-ev.eval_aff(g,pts)))
       unknown[kind].setdefault((r,c),[]).append({'cell':[r,c],'object':name,'face':fid,'triangle':ti,'area_m2':area,'reason':'F_unknown_triangle','finite_corner_count':int(np.isfinite(fv).sum()),'B_max_face_minus_ground_m':bmax,'buried_in_B':bmax<=0.,'face_plane_coeff_xz':plane.tolist(),'intersection_xz':pts.tolist()});continue
      fp=ev.affine(tri_xy,fv);ex=float(np.max(pts@plane[:2]+plane[2]-ev.eval_aff(fp,pts)))
      if ex>ev.EPS[kind]:
       above[kind].setdefault((r,c),[]).append({'cell':[r,c],'object':name,'face':fid,'triangle':ti,'max_excess_m':ex,'overlap_area_m2':area,'face_plane_coeff_xz':plane.tolist(),'intersection_xz':pts.tolist()});exceed[kind]+=1
 return {'above_by_kind':above,'unknown_by_kind':unknown,'positive_area_face_cell_tests':face_n,'face_cell_exceedance_count':exceed,'degenerate_candidates_in_window':deg_n,'positive_area_object_count':len(objects),'queried_face_rows':len(rows['kind'])}
def scan_index_window(ev,index,src,center):
 with WindowScope(ev,center):
  r0,r1,c0,c1=ev.WINDOW;rows=index.query_window(r0,r1-2,c0,c1-2)
  model_names={int(m['model_id']):str(m['basename']) for m in index.manifest['models']}
  if sorted(model_names)!=list(range(len(model_names))):raise AssertionError('non-dense EV93 model IDs')
  out=scan_face_rows(ev,rows,src,ev.WINDOW,model_names)
  out['window_vertices_rc_halfopen']=list(ev.WINDOW);out['window_cells_rc_inclusive']=[r0,r1-2,c0,c1-2]
  return out
def prepare_source(ev):
 src=ev.check_linkage_and_load();wrp=src['wrp'];bounds=src['bounds']
 bound_objs={int(o['id']):o for o in bounds['objects']};water=[o for o in wrp['objects'] if 'baltic_water_v30' in o['name'].replace('\\','/').lower()]
 if len(water)!=18024 or len(bound_objs)!=18024:raise AssertionError('B water object count mismatch')
 object_to_model={};models=set()
 for o in water:
  oid=int(o['id']);entry=bound_objs.get(oid)
  if entry is None:raise AssertionError(f'water object absent from bounds {oid}')
  name=o['name'].replace('\\','/').split('/')[-1]
  if entry['model'].lower()!=name.lower():raise AssertionError(f'WRP/bounds model mismatch {oid}')
  m=np.asarray(o['matrix'],dtype=np.float64)
  if m.shape!=(12,) or not np.array_equal(m[:9].reshape(3,3),np.eye(3)):raise AssertionError(f'non-translation water transform {oid}')
  if not np.array_equal(m[[9,11]].astype(np.float32),np.asarray(entry['position'],dtype=np.float32)[[0,2]]):raise AssertionError(f'WRP/bounds XZ mismatch {oid}')
  local=bounds['models'].get(name)
  if local is None:raise AssertionError(f'missing model bounds {name}')
  lb=np.asarray(local['bounds'],dtype=np.float64);tx,tz=float(m[9]),float(m[11]);calc=np.asarray([lb[0]+tx,lb[1]+tz,lb[2]+tx,lb[3]+tz])
  if np.max(np.abs(calc-np.asarray(entry['bounds'],dtype=np.float64)))>1e-4:raise AssertionError(f'model/world bounds mismatch object {oid}')
  object_to_model[oid]=name;models.add(name)
 src['object_to_model']=object_to_model;src['selected_model_names']=models
 stable=dict(src['hashes'])
 for path,key in ((src['world_pbo'],'narva_trial.pbo'),(src['water_pbo'],'baltic_water_v30.pbo')):
  actual=sha(path)
  if actual!=src['deploy']['files'].get(key):raise AssertionError(f'deployed PBO changed after source linkage: {key}')
  stable[str(path)]=actual
 for path in (ev.BOUNDS,ev.WRP):
  actual=sha(path);expected=stable.get(str(path))
  if expected is not None and expected!=actual:raise AssertionError(f'frozen readset changed after initial linkage: {path}')
  stable[str(path)]=expected or actual
 src['stable_hashes']=stable
 return src
def guard_d8(ev,author,nodes,h):
 stencils=enumerate_stencils(nodes,ev.WINDOW)
 if not nodes:
  return {'stencil_count':len(stencils),'guard_rc':[],'guard_count':0,'free_count':0,
   'guard_bounds_exact_B':True,'descent_matrix_shape':[0,0],'descent_witness_count':0,
   'descent_centers_count':0,'descent_exempt_baseline_centers':[],'descent_witnesses':[],
   'descent_witnesses_hold_on_B':True,'guard_B_height_values':[],
   'guard_B_height_values_sha256_f32':hashlib.sha256(b'').hexdigest(),
   'descent_matrix_sha256_f64':hashlib.sha256(b'').hexdigest(),
   'descent_rhs_sha256_f64':hashlib.sha256(b'').hexdigest()}
 guard=[tuple(map(int,x)) for x in author.collar_guard(nodes,stencils,ev.WINDOW)]
 mat,rhs,witnesses,exempt,centers=author.descent_constraints(np.asarray(h,dtype=np.float32),nodes)
 if not author.witnesses_hold(np.asarray(h,dtype=np.float32),witnesses):raise AssertionError('D8 witnesses fail at B')
 return {'stencil_count':len(stencils),'guard_rc':[list(x) for x in guard],'guard_count':len(guard),'free_count':len(nodes)-len(guard),
  'guard_bounds_exact_B':True,'descent_matrix_shape':list(mat.shape),'descent_witness_count':len(witnesses),
  'descent_centers_count':len(centers),'descent_exempt_baseline_centers':[list(x) for x in exempt],
  'descent_witnesses':witnesses,'descent_witnesses_hold_on_B':True,
  'guard_B_height_values':[{'rc':list(x),'height_m':float(np.asarray(h,dtype=np.float32)[x])} for x in guard],
  'guard_B_height_values_sha256_f32':hashlib.sha256(b''.join(np.asarray(x,dtype='<i4').tobytes()+np.asarray([np.asarray(h,dtype=np.float32)[tuple(x)]],dtype='<f4').tobytes() for x in guard)).hexdigest(),
  'descent_matrix_sha256_f64':hashlib.sha256(mat.astype('<f8').tobytes()).hexdigest(),
  'descent_rhs_sha256_f64':hashlib.sha256(rhs.astype('<f8').tobytes()).hexdigest()}

def summarize_window(ev,src,exposure,center,author):
 with WindowScope(ev,center):
  above={k:set(tuple(x) for x in exposure['above_by_kind'][k]) for k in ('physical','visible')}
  unknown={k:set(tuple(x) for x in exposure['unknown_by_kind'][k]) for k in ('physical','visible')}
  p9,p9_features=ev.corridor_p_unknown(src);partial=ev.partial_f_cells(src)
  freeze=set().union(*above.values())|set(p9)|set(partial);domain=ev.reconstruct_domain(src,freeze,above,unknown)
  eligible=domain['eligible_after_face_freeze_nodes']
  guard=guard_d8(ev,author,eligible,src['B']['heights'])
  h=np.asarray(src['B']['heights'],dtype=np.float64)
  lower={tuple(x['node_rc']):float(x['interval_float32_inward_m'][0]) for x in domain['final_float32_intervals_for_eligible_nodes'] if x['interval_float32_inward_m'] is not None}
  guard_nodes={tuple(x) for x in guard['guard_rc']}
  burial={'physical':[],'visible':[]}
  for kind in ('physical','visible'):
   for cell,items in exposure['unknown_by_kind'][kind].items():
    r,c=cell
    for x in items:
     tri=ev.TRIS[x['triangle']];tri_nodes=[(r+ev.OFFSETS[k][0],c+ev.OFFSETS[k][1]) for k in tri]
     touches_guard=any(node in guard_nodes for node in tri_nodes)
     h4=np.asarray([h[r,c],h[r,c+1],h[r+1,c],h[r+1,c+1]])
     for k,node in zip(tri,tri_nodes):
      if node in lower:h4[k]=lower[node]
     tri_xy=ev.grid_xy(r,c)[np.asarray(tri,dtype=np.int64)];g=ev.affine(tri_xy,h4[list(tri)])
     pts=np.asarray(x['intersection_xz'],dtype=np.float64);face=np.asarray(x['face_plane_coeff_xz'],dtype=np.float64)
     delta=float(np.max(ev.eval_aff(face,pts)-ev.eval_aff(g,pts)))
     burial[kind].append({'cell':[r,c],'object':x['object'],'face':x['face'],'triangle':x['triangle'],
      'max_face_minus_minimum_ground_m':delta,'buried':delta<=0.,'P9_exact_B':kind=='physical' and cell in p9,
      'touches_guard':touches_guard})
  unresolved=[x for kind in burial for x in burial[kind] if not x['P9_exact_B'] and not x['buried']]
  inconclusive=bool(domain['F_partial_triangles_touching_originally_eligible_nodes'] or unresolved)
  box=_domain_box_status(domain,h)
  status=_preflight_status(domain,box,guard,inconclusive)
  dkeys=('eligible_before_new_face_freeze_count','new_face_freeze_vertices_core_count','eligible_after_confirmed_above_freeze_only_count','confirmed_above_freeze_vertices_core_count','unknown_field_vertices_touching_core_count','new_face_freeze_vertices_core','eligible_after_face_freeze_count','eligible_after_face_freeze_nodes','final_float32_intervals_for_eligible_nodes','face_freeze_vertices_core_count','F_partial_triangles_touching_originally_eligible_nodes','crossing_F_unknown','crossing_record_count','crossing_interval_empty_nodes','focus_status','focus_interval_float32_inward_m','focus_axes','both_axes_box_feasible_for_25_percent','crossing_records','focus_and_cardinal_neighbor_blockers','unknown_domain_preflight_inconclusive')
  d={k:domain[k] for k in dkeys}
  return {'status':status,'center_rc':list(center),'window':list(ev.WINDOW),'core':list(ev.CORE),
   'above_cells_by_kind':_cell_map(above),'unknown_cells_by_kind':_cell_map(unknown),
   'P9_unknown_cells':sorted([list(x) for x in p9]),'P9_unknown_by_feature':p9_features,
   'partial_F_cells':sorted([list(x) for x in partial]),'freeze_cells_count':len(freeze),
   'domain':d,'box_interval_audit':box,'guard_d8':guard,'burial':burial,
   'unknown_lower_unresolved_count':len(unresolved),
   'unknown_reject_due_to_guard_count':sum(1 for x in unresolved if x['touches_guard'])}

def _model_and_object_linkage(index,src,ev):
 table=index.manifest.get('models',[]);byid={int(x['model_id']):x for x in table}
 if sorted(byid)!=list(range(len(byid))):raise AssertionError('model IDs not dense')
 if {str(x['basename']) for x in table}!=src['selected_model_names']:raise AssertionError('model table differs from source objects')
 counts={};hashes={}
 for rec in table:
  name=str(rec['basename']);path=ev.MODEL_DIR/name;digest=sha(path)
  local=src['bounds']['models'][name].get('sha256')
  if not local or digest!=local or digest!=rec.get('sha256'):raise AssertionError(f'ODOL model identity mismatch {name}')
  hashes[str(path)]=digest
  counts[name,'physical']=int(rec['physical_faces']);counts[name,'visible']=int(rec['visible_faces'])
  if float(rec['physical_resolution'])!=float(np.float32(3e15)) or float(rec['visible_resolution'])!=float(np.float32(1.0)):
   raise AssertionError(f'LOD resolution mismatch {name}')
 src['model_face_counts']=counts
 return hashes

def verify_index_linkage(index,src,ev,model_hashes):
 m=index.manifest;base=m.get('base_identity',{});b=src['bounds'];checks={
  'terrain':base.get('terrain_sha256')==src['deploy'].get('terrain_sha256'),
  'compiled_oprw':base.get('compiled_oprw_sha256')==src['compiled_oprw_sha'],
  'world_pbo':base.get('world_pbo_sha256')==sha(src['world_pbo']),
  'water_pbo':base.get('water_pbo_sha256')==sha(src['water_pbo']),
  'bounds_world':base.get('bounds_world_sha256')==b.get('world_sha256'),
  'bounds_file':base.get('bounds_sha256')==sha(ev.BOUNDS),'wrp_source':base.get('wrp_source_sha256')==sha(ev.WRP)}
 if not all(checks.values()):raise AssertionError(f'EV93 base identity mismatch: {checks}')
 if m.get('builder_source',{}).get('sha256')!=sha(INDEX_SOURCE):raise AssertionError('EV93 builder source not pinned in manifest')
 if m.get('ev90_source',{}).get('sha256')!=sha(EV90_PATH):raise AssertionError('EV90 source pin differs in EV93 manifest')
 if m.get('ev87_source',{}).get('sha256')!=sha(EV87_SOURCE):raise AssertionError('EV87 source pin differs in EV93 manifest')
 objhash=hashlib.sha256(np.asarray(sorted(src['object_to_model']),dtype='<i4').tobytes()).hexdigest()
 if m.get('water_object_ids_sha256')!=objhash or int(m.get('object_count',-1))!=18024:raise AssertionError('EV93 water object identity hash/count mismatch')
 if m.get('counts')!=m.get('observed_counts') or m.get('status')!='COMPLETE':raise AssertionError('EV93 counts/status incomplete')
 expected_inputs=dict(src['hashes']);expected_inputs.update({str(EV90_PATH):sha(EV90_PATH),str(EV87_SOURCE):sha(EV87_SOURCE),str(PLAN):sha(PLAN),str(ev.WRP):sha(ev.WRP),str(ev.BOUNDS):sha(ev.BOUNDS),str(src['world_pbo']):sha(src['world_pbo']),str(src['water_pbo']):sha(src['water_pbo']),**model_hashes})
 for path,want in expected_inputs.items():
  if m.get('input_hashes',{}).get(path)!=want:raise AssertionError(f'EV93 input provenance mismatch: {path}')
 return {'base_identity_checks':checks,'object_count':18024,'object_ids_sha256':objhash,'model_count':len(model_hashes),'index_counts':m['counts']}

def _exposure_signature(exposure):
 out={}
 for kind in ('physical','visible'):
  for family in ('above_by_kind','unknown_by_kind'):
   records=[]
   for cell,items in exposure[family][kind].items():
    for item in items:records.append(json.dumps(item,sort_keys=True,separators=(',',':'),allow_nan=False))
   out[f'{kind}:{family}']=sorted(records)
 return out

def _burial_signature(summary):
 return {k:sorted(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False) for x in summary['burial'][k]) for k in ('physical','visible')}

def _record_direct_pilot_frozen_checks(ev,index,src,author):
 direct= None
 with WindowScope(ev,PILOT):direct=ev.scan_compiled_faces(src)
 indexed=scan_index_window(ev,index,src,PILOT)
 d=summarize_window(ev,src,direct,PILOT,author);i=summarize_window(ev,src,indexed,PILOT,author);diff=[]
 for k in ('above_cells_by_kind','unknown_cells_by_kind','P9_unknown_cells','P9_unknown_by_feature','partial_F_cells'):
  if d[k]!=i[k]:diff.append('class:'+k)
 if _exposure_signature(direct)!=_exposure_signature(indexed):diff.append('exposure_records')
 domain_keys=('eligible_after_face_freeze_nodes','final_float32_intervals_for_eligible_nodes','F_partial_triangles_touching_originally_eligible_nodes','crossing_F_unknown','crossing_interval_empty_nodes','crossing_records','focus_status','focus_interval_float32_inward_m','focus_axes','both_axes_box_feasible_for_25_percent')
 if d['box_interval_audit']!=i['box_interval_audit']:diff.append('domain:box_interval_audit')
 if d['unknown_reject_due_to_guard_count']!=i['unknown_reject_due_to_guard_count']:diff.append('domain:unknown_guard_blockers')
 for k in domain_keys:
  if d['domain'][k]!=i['domain'][k]:diff.append('domain:'+k)
 for k in ('guard_rc','guard_count','free_count','descent_witnesses','descent_witnesses_hold_on_B','descent_matrix_sha256_f64','descent_rhs_sha256_f64'):
  if d['guard_d8'][k]!=i['guard_d8'][k]:diff.append('guard:'+k)
 if _burial_signature(d)!=_burial_signature(i):diff.append('burial_certificates')
 frozen=json.loads(EV90_REPORT.read_text(encoding='utf-8'))['domain_and_bound_analysis']
 for k in ('eligible_after_face_freeze_nodes','final_float32_intervals_for_eligible_nodes','crossing_records'):
  if i['domain'][k]!=frozen[k]:diff.append('EV90_frozen:'+k)
 guard_frozen=json.loads(EV91_GUARD.read_text(encoding='utf-8'));prepared=json.loads(EV91_PREPARED.read_text(encoding='utf-8'))
 if i['guard_d8']['guard_rc']!=guard_frozen['guard']['guard_rc']:diff.append('EV91_frozen:guard')
 if i['guard_d8']['descent_witnesses']!=prepared['witnesses']:diff.append('EV91_frozen:D8')
 return {'status':'PREFLIGHT_INDEX_PILOT_MATCH' if not diff else 'PREFLIGHT_INDEX_PILOT_MISMATCH','diffs':diff,
 'direct':d,'indexed':i,'direct_scan_counts':{k:v for k,v in direct.items() if k not in ('above_by_kind','unknown_by_kind','model_hashes')},
 'indexed_scan_counts':{k:v for k,v in indexed.items() if k not in ('above_by_kind','unknown_by_kind')},
 'frozen_reports':{'EV90':sha(EV90_REPORT),'EV91_guard':sha(EV91_GUARD),'EV91_prepared':sha(EV91_PREPARED)}}

def reverify_source_readset(src,model_hashes,ev):
 paths=dict(src['stable_hashes']);paths.update(model_hashes)
 _assert_path_hashes(paths)
 _,_,entries=src['attach_navmesh'].read_pbo(src['world_pbo'])
 compiled=entries.get('baltic_trial.wrp')
 if not compiled or hashlib.sha256(compiled).hexdigest()!=src['compiled_oprw_sha']:
  raise AssertionError('compiled OPRW changed inside the deployed world PBO during preflight')
 return paths
def _assert_path_hashes(paths):
 for path,want in paths.items():
  if sha(path)!=want:raise AssertionError(f'input changed during preflight: {path}')
def _canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
def _atomic_json(path,value):
 path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp')
 tmp.write_text(json.dumps(_json_safe(value),indent=2,allow_nan=False)+'\n',encoding='utf-8');tmp.replace(path)
def _json_safe(value):
 if isinstance(value,dict):return {str(k):_json_safe(v) for k,v in value.items()}
 if isinstance(value,(list,tuple)):return [_json_safe(v) for v in value]
 if isinstance(value,(float,np.floating)) and not math.isfinite(float(value)):
  return {'nonfinite':'positive_infinity' if float(value)>0 else 'negative_infinity' if float(value)<0 else 'not_a_number'}
 if isinstance(value,np.integer):return int(value)
 if isinstance(value,np.bool_):return bool(value)
 return value
def _domain_box_status(domain,base):
 intervals=domain['final_float32_intervals_for_eligible_nodes'];h=np.asarray(base,dtype=np.float32)
 empty={tuple(map(int,x)) for x in domain.get('crossing_interval_empty_nodes',[])};outside=[]
 for row in intervals:
  rc=tuple(map(int,row['node_rc']));bounds=row['interval_float32_inward_m']
  if bounds is None or len(bounds)!=2 or not (float(bounds[0])<=float(bounds[1])):
   empty.add(rc);continue
  b=float(h[rc]);lo=float(bounds[0]);hi=float(bounds[1])
  if b<lo or b>hi:outside.append({'node_rc':list(rc),'B_float32_m':b,'interval':[lo,hi]})
 return {'eligible_count':len(intervals),'empty_nodes':[list(x) for x in sorted(empty)],'baseline_outside_nodes':outside,
  'box_is_usable':bool(intervals) and not empty and not outside}
def _preflight_status(domain,box,guard,inconclusive):
 if inconclusive:return 'PREFLIGHT_INCONCLUSIVE'
 if (domain['focus_status']!='variable' or not domain['both_axes_box_feasible_for_25_percent']
     or not box['box_is_usable'] or guard['free_count']==0):return 'PREFLIGHT_INFEASIBLE'
 return 'PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW'
def _verified_index_receipt(report_path,index_dir,index):
 path=Path(report_path).resolve();expected=INDEX_VERIFICATION.resolve()
 if path!=expected:raise AssertionError('independent verification must use the pinned EV93 report path')
 if sha(path)!=INDEX_VERIFICATION_SHA256:raise AssertionError('independent verification report hash differs from frozen root review')
 report=json.loads(path.read_text(encoding='utf-8'));m=index.manifest;counts=m.get('counts',{})
 if report.get('status')!='PASS_INDEX_AND_SAMPLED_EXPOSURE':raise AssertionError('independent index verification is not PASS_INDEX_AND_SAMPLED_EXPOSURE')
 checks={
  'index_run':Path(index_dir).resolve()==INDEX_RUN.resolve(),
  'manifest_path':report.get('manifest_path')==str(INDEX_RUN/'manifest.json')==str(index.manifest_path),
  'manifest_sha256':report.get('manifest_sha256')==sha(index.manifest_path),
  'index_face_count':int(report.get('index_face_count',-1))==int(counts.get('faces',-2)),
  'physical_faces':int(report.get('direct_face_counts',{}).get('physical',-1))==int(counts.get('physical',-2)),
  'visible_faces':int(report.get('direct_face_counts',{}).get('visible',-1))==int(counts.get('visible',-2)),
  'source_objects':int(report.get('source_objects',-1))==int(m.get('object_count',-2))==18024,
  'source_models':int(report.get('source_models',-1))==len(m.get('models',[]))==13128,
  'degenerate_counts':report.get('source_degenerate_counts')=={'physical':int(counts.get('degenerate_physical',-1)),'visible':int(counts.get('degenerate_visible',-1))},
  'manifest_complete':m.get('status')=='COMPLETE' and counts==m.get('observed_counts'),
  'sampled_cell_count':len(report.get('sampled_cells',{}))==18,
  'all_sampled_coverage_pass':all(v[k]['pass_existing_0_002m2_coverage_tolerance'] for v in report.get('sampled_cells',{}).values() for k in ('physical','visible')),
 }
 if not all(checks.values()):raise AssertionError(f'independent index verification identity mismatch: {checks}')
 return {'path':str(path),'sha256':sha(path),'status':report['status'],'manifest_path':str(index.manifest_path),
  'manifest_sha256':sha(index.manifest_path),'index_face_count':int(counts['faces']),
  'physical_faces':int(counts['physical']),'visible_faces':int(counts['visible']),
  'object_count':int(m['object_count']),'model_count':len(m['models']),'sampled_cell_count':len(report['sampled_cells']),
  'identity_checks':checks}

def main():
 ap=argparse.ArgumentParser(description='EV93 readonly per-window preflight; no solver or terrain output')
 ap.add_argument('--fixtures',action='store_true');ap.add_argument('--pilot-index',type=Path)
 ap.add_argument('--execute-batch-703',action='store_true');ap.add_argument('--index-run',type=Path);ap.add_argument('--pilot-receipt',type=Path)
 ap.add_argument('--index-verification',type=Path)
 args=ap.parse_args()
 if not (args.fixtures or args.pilot_index or args.execute_batch_703):ap.error('choose --fixtures, --pilot-index, or --execute-batch-703')
 if args.fixtures:print(json.dumps(run_fixtures(),indent=2));return
 if args.pilot_index and args.index_verification is None:ap.error('--pilot-index requires --index-verification')
 if args.execute_batch_703 and (args.pilot_receipt is None or args.index_verification is None):
  ap.error('batch requires --pilot-receipt and --index-verification reviewed by integrator')
 bad=check_pins()
 if bad:raise AssertionError(f'EV93 source pin mismatch: {bad}')
 ev=load_module('ev90_frozen_ev93_window_preflight',EV90_PATH);author=load_module('ev91_guard_d8_ev93',EV91_AUTHOR)
 ev88=load_module('ev88_stencil_fixture_ev93',EV88_AUTHOR)
 if enumerate_stencils([[840,370]],(832,849,362,379))!=ev88.frozen_stencils([[840,370]],(832,849,362,379)):
  raise AssertionError('pilot stencil fixture differs from pinned EV88 helper')
 src=prepare_source(ev);api=load_module('ev93_face_range_index_api',INDEX_SOURCE)
 index_dir=args.pilot_index or args.index_run
 if index_dir is None:ap.error('index run required')
 index=api.FaceRangeIndex(index_dir);model_hashes=_model_and_object_linkage(index,src,ev)
 linkage=verify_index_linkage(index,src,ev,model_hashes)
 if args.pilot_index:
  if args.index_verification is None:ap.error('--pilot-index requires --index-verification')
  verification=_verified_index_receipt(args.index_verification,index_dir,index)
  result=_record_direct_pilot_frozen_checks(ev,index,src,author)
  result.update({'index_run':str(index_dir),'index_manifest_sha256':sha(index.manifest_path),'index_api_sha256':sha(INDEX_SOURCE),
   'ev90_sha256':sha(EV90_PATH),'ev91_author_sha256':sha(EV91_AUTHOR),'ev88_helper_sha256':sha(EV88_AUTHOR),
   'model_hashes_sha256':hashlib.sha256(_canonical(model_hashes)).hexdigest(),'read_set_sha256':dict(src['hashes']),
   'index_linkage':linkage,'index_verification':verification,
   'index_verification_path':verification['path'],'index_verification_sha256':verification['sha256'],
   'scope':'One pilot comparison only; no first-layer batch, optimizer, terrain output, package, or engine.',
   'verifier_sha256':sha(Path(__file__).resolve()),'queue_sha256':sha(QUEUE),'plan_sha256':sha(PLAN),'preflight_plan_sha256':sha(PREFLIGHT_PLAN)})
  index.reverify();reverify_source_readset(src,model_hashes,ev)
  if sha(args.index_verification)!=verification['sha256']:raise AssertionError('independent index verification changed during pilot')
  if check_pins():raise AssertionError('pinned source changed during pilot')
  OUT.mkdir(parents=True,exist_ok=True);path=OUT/'pilot-compare.json';_atomic_json(path,result)
  print(json.dumps({'status':result['status'],'diffs':result['diffs'],'path':str(path),'sha256':sha(path)},indent=2));return
 if not args.execute_batch_703 or args.pilot_receipt is None or args.index_verification is None:
  ap.error('batch requires --pilot-receipt and --index-verification reviewed by integrator')
 verification=_verified_index_receipt(args.index_verification,index_dir,index)
 receipt=json.loads(args.pilot_receipt.read_text(encoding='utf-8'))
 if receipt.get('status')!='PREFLIGHT_INDEX_PILOT_MATCH' or receipt.get('diffs'):raise AssertionError('batch blocked without matching pilot')
 if receipt.get('verifier_sha256')!=sha(Path(__file__).resolve()) or receipt.get('queue_sha256')!=sha(QUEUE) or receipt.get('plan_sha256')!=sha(PLAN) or receipt.get('preflight_plan_sha256')!=sha(PREFLIGHT_PLAN):raise AssertionError('pilot receipt does not bind current source/queue/plans')
 if receipt.get('read_set_sha256')!=src['hashes'] or receipt.get('model_hashes_sha256')!=hashlib.sha256(_canonical(model_hashes)).hexdigest():raise AssertionError('pilot receipt read set differs from current inputs')
 if receipt.get('index_manifest_sha256')!=sha(index.manifest_path) or receipt.get('index_run')!=str(index_dir):raise AssertionError('pilot receipt does not bind exact index run')
 if receipt.get('index_verification')!=verification:raise AssertionError('pilot receipt does not bind exact independent verification report')
 queue=json.loads(QUEUE.read_text(encoding='utf-8'));first=[s for s in queue['seeds'] if s.get('state')=='first_layer']
 if len(first)!=703:raise AssertionError('queue first layer is not 703')
 header={'event':'header','queue_sha256':sha(QUEUE),'index_manifest_sha256':sha(index.manifest_path),
  'index_verification_path':verification['path'],'index_verification_sha256':verification['sha256'],
  'pilot_sha256':sha(args.pilot_receipt),'source_sha256':sha(Path(__file__).resolve()),
  'EV90_sha256':sha(EV90_PATH),'EV91_sha256':sha(EV91_AUTHOR),'EV91_prepared_sha256':sha(EV91_PREPARED),
  'count':703,'budget_seconds':BUDGET,'read_set_sha256':dict(src['hashes']),
  'model_hashes_sha256':hashlib.sha256(_canonical(model_hashes)).hexdigest()}
 OUT.mkdir(parents=True,exist_ok=True);ledger=OUT/'window-ledger.jsonl';done={};prior_errors=set()
 if ledger.exists():
  lines=ledger.read_text(encoding='utf-8').splitlines()
  if not lines or json.loads(lines[0])!=header:raise AssertionError('resume ledger header mismatch')
  for line in lines[1:]:
   rec=json.loads(line)
   if rec.get('event')!='window':continue
   qid=int(rec['queue_id'])
   if rec.get('state')=='PREFLIGHT_ERROR':prior_errors.add(qid);continue
   if qid in done:raise AssertionError(f'duplicate result queue_id={qid}')
   detail=OUT/rec.get('detail_path','')
   if not detail.is_file() or sha(detail)!=rec.get('detail_sha256'):raise AssertionError(f'window detail missing/hash mismatch queue_id={qid}')
   done[qid]=rec
  if lines and json.loads(lines[-1]).get('event')=='final':
   with ledger.open('a',encoding='utf-8',newline='\n') as f:
    f.write(json.dumps({'event':'resume','prior_final_sha256':hashlib.sha256((lines[-1]+'\n').encode('utf-8')).hexdigest()},separators=(',',':'))+'\n')
 else:
  with ledger.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(header,separators=(',',':'))+'\n');f.flush()
 details_dir=OUT/'window-details';details_dir.mkdir(parents=True,exist_ok=True)
 detail_bytes=sum(p.stat().st_size for p in details_dir.glob('*.json'))
 if detail_bytes>200*1024*1024:raise AssertionError('existing window detail exceeds 200 MiB practical cap')
 started=time.monotonic()
 with ledger.open('a',encoding='utf-8',newline='\n') as f:
  for qid,seed in enumerate(first):
   if qid in done:continue
   if time.monotonic()-started>=BUDGET:break
   center=(int(seed['row']),int(seed['col']));t0=time.monotonic()
   try:
    exposure=scan_index_window(ev,index,src,center);summary=summarize_window(ev,src,exposure,center,author)
    detail_value={'queue_id':qid,'seed_id':int(seed['seed_id']),'center_rc':list(center),
     'window17':seed['window17'],'exposure':exposure,'preflight':summary}
    detail_path=details_dir/f'q{qid:04d}.json'
    detail_payload=json.dumps(_json_safe(detail_value),indent=2,allow_nan=False)+'\n'
    detail_new_bytes=len(detail_payload.encode('utf-8'))
    old_detail_bytes=detail_path.stat().st_size if detail_path.exists() else 0
    if detail_bytes-old_detail_bytes+detail_new_bytes>200*1024*1024:raise AssertionError('window detail cap 200 MiB reached')
    tmp=detail_path.with_suffix('.json.tmp');tmp.write_text(detail_payload,encoding='utf-8',newline='\n');tmp.replace(detail_path)
    detail_bytes=detail_bytes-old_detail_bytes+detail_path.stat().st_size
    rec={'event':'window','queue_id':qid,'seed_id':int(seed['seed_id']),'center_rc':list(center),
     'window17':seed['window17'],'state':summary['status'],'detail_path':str(detail_path.relative_to(OUT)),
     'detail_sha256':sha(detail_path),'eligible_count':summary['domain']['eligible_after_face_freeze_count'],
     'empty_interval_count':len(summary['box_interval_audit']['empty_nodes']),
     'baseline_outside_interval_count':len(summary['box_interval_audit']['baseline_outside_nodes']),
     'unknown_lower_unresolved_count':summary['unknown_lower_unresolved_count'],
     'unknown_reject_due_to_guard_count':summary['unknown_reject_due_to_guard_count'],
     'guard_count':summary['guard_d8']['guard_count'],'free_count':summary['guard_d8']['free_count'],
     'D8_witness_count':summary['guard_d8']['descent_witness_count'],
     'D8_witnesses_hold_on_B':summary['guard_d8']['descent_witnesses_hold_on_B']}
   except Exception as exc:
    rec={'event':'window','queue_id':qid,'seed_id':int(seed['seed_id']),'center_rc':list(center),
     'window17':seed.get('window17'),'state':'PREFLIGHT_ERROR','reason':[type(exc).__name__,str(exc)[:500]]}
    prior_errors.add(qid)
   rec['elapsed_s']=round(time.monotonic()-t0,6)
   f.write(json.dumps(_json_safe(rec),separators=(',',':'),allow_nan=False)+'\n');f.flush()
   if rec['state']!='PREFLIGHT_ERROR':done[qid]=rec
  processed=len(done);error_count=len(prior_errors-set(done))
  status='COMPLETE_READONLY_PREFLIGHT' if processed==703 and error_count==0 else 'INCOMPLETE_READONLY_PREFLIGHT'
  final={'event':'final','status':status,'processed_count':processed,'remaining_count':703-processed,
   'remaining_queue_ids':[i for i in range(703) if i not in done],'error_count':error_count,
   'index_manifest_sha256':sha(index.manifest_path),'index_verification_sha256':verification['sha256']}
  f.write(json.dumps(final,separators=(',',':'),allow_nan=False)+'\n');f.flush()
 index.reverify();reverify_source_readset(src,model_hashes,ev)
 if sha(args.index_verification)!=verification['sha256']:raise AssertionError('independent index verification changed during batch')
 if check_pins():raise AssertionError('source changed during read-only batch')
 states={}
 for rec in done.values():states[rec['state']]=states.get(rec['state'],0)+1
 summary={'status':status,'processed_count':processed,'remaining_count':703-processed,'error_count':error_count,
  'state_counts':states,'ledger_sha256':sha(ledger),'source_sha256':sha(Path(__file__).resolve()),
  'index_manifest_sha256':sha(index.manifest_path),'index_verification_path':verification['path'],
  'index_verification_sha256':verification['sha256']}
 _atomic_json(OUT/'window-summary.json',summary);print(json.dumps(summary,indent=2))

def run_fixtures():
 class Dummy: WINDOW=(1,2,3,4);CORE=(5,6,7,8);FOCUS=(9,10)
 d=Dummy();before=(d.WINDOW,d.CORE,d.FOCUS)
 try:
  with WindowScope(d,(840,370)):
   assert (d.WINDOW,d.CORE,d.FOCUS)==((832,849,362,379),(834,847,364,377),(840,370))
   raise RuntimeError('restore fixture')
 except RuntimeError:pass
 assert (d.WINDOW,d.CORE,d.FOCUS)==before
 api=load_module('ev93_face_index_fixture_api',INDEX_SOURCE)
 ranges=np.asarray([[5,5,7,7],[6,8,7,9],[-1,-1,-1,-1]],dtype=np.int32)
 assert np.array_equal(api.query_mask(ranges,(5,5,7,7)),[True,False,False])
 ev=load_module('ev90_ev93_window_fixture',EV90_PATH)
 # Correct split is NW-SE: the raised SE corner belongs to both noncoplanar halves.
 corners=np.asarray([0.,0.,0.,6.]);xy=ev.grid_xy(0,0)
 q0=ev.affine(xy[np.asarray(ev.TRIS[0])],corners[np.asarray(ev.TRIS[0])])
 q1=ev.affine(xy[np.asarray(ev.TRIS[1])],corners[np.asarray(ev.TRIS[1])])
 assert abs(float(ev.eval_aff(q0,np.asarray([[4.,ev.Z0-1.]]))[0])-1.)<1e-12
 assert abs(float(ev.eval_aff(q1,np.asarray([[1.,ev.Z0-5.]]))[0])-1.)<1e-12
 # Smallest positive triangles are retained even below EV87's 1e-12 downstream cutoff.
 tiny=1e-6;xyz=np.asarray([[3.,3.00002,ev.Z0-3.],[3.+tiny,3.00002,ev.Z0-3.],[3.,3.00002,ev.Z0-3.-tiny]],dtype=np.float64)
 from shapely.geometry import Polygon
 area=float(Polygon(xyz[:,(0,2)]).area);assert 0.<area<1e-12
 src={'P':np.full((2,2),3.,dtype=np.float64),'F':np.full((2,2,4),3.,dtype=np.float64),
  'B':{'heights':np.zeros((3,3),dtype=np.float32)},'object_to_model':{1:'fixture.p3d'},
  'model_face_counts':{('fixture.p3d','physical'):2,('fixture.p3d','visible'):2}}
 rows={'kind':np.asarray([0,0],dtype=np.uint8),'object_id':np.asarray([1,1],dtype=np.int32),
  'model_id':np.asarray([0,0],dtype=np.uint32),'face_id':np.asarray([0,1],dtype=np.uint32),
  'xyz':np.asarray([xyz,[[0.,0.,0.],[1.,0.,0.],[2.,0.,0.]]],dtype=np.float64),
  'plane_y_xz':np.asarray([[0.,0.,3.00002],[0.,0.,0.]],dtype=np.float64),
  'area_xz':np.asarray([area,0.],dtype=np.float64),'cell_range_rc':np.asarray([[0,0,0,0],[-1,-1,-1,-1]],dtype=np.int32),
  'degenerate':np.asarray([0,1],dtype=np.uint8)}
 scan=scan_face_rows(ev,rows,src,(0,2,0,2),{0:'fixture.p3d'})
 assert scan['positive_area_face_cell_tests']['physical']==1 and scan['degenerate_candidates_in_window']['physical']==1
 hits=scan['above_by_kind']['physical'][(0,0)]
 assert len(hits)==1 and 0.<hits[0]['overlap_area_m2']<1e-12
 # A face spanning a window boundary is queried from its inclusive cell range, then exact clipping drops zero-area contact.
 assert api.query_mask(np.asarray([[4,5,7,8]],dtype=np.int32),(5,5,8,8))[0]
 assert enumerate_stencils([[840,370]],(832,849,362,379))==load_module('ev88_stencil_fixture_ev93',EV88_AUTHOR).frozen_stencils([[840,370]],(832,849,362,379))
 # The interval gate must reject no variables, empty bounds, and baseline outside the inward-float32 box.
 valid_domain={'final_float32_intervals_for_eligible_nodes':[{'node_rc':[1,1],'interval_float32_inward_m':[0.,1.]}],'crossing_interval_empty_nodes':[]}
 assert _domain_box_status(valid_domain,np.zeros((3,3),dtype=np.float32))['box_is_usable']
 empty_domain={'final_float32_intervals_for_eligible_nodes':[{'node_rc':[1,1],'interval_float32_inward_m':None}],'crossing_interval_empty_nodes':[]}
 assert not _domain_box_status(empty_domain,np.zeros((3,3),dtype=np.float32))['box_is_usable']
 outside_domain={'final_float32_intervals_for_eligible_nodes':[{'node_rc':[1,1],'interval_float32_inward_m':[1.,2.]}],'crossing_interval_empty_nodes':[]}
 assert not _domain_box_status(outside_domain,np.zeros((3,3),dtype=np.float32))['box_is_usable']
 no_vars={'final_float32_intervals_for_eligible_nodes':[],'crossing_interval_empty_nodes':[]}
 assert not _domain_box_status(no_vars,np.zeros((3,3),dtype=np.float32))['box_is_usable']
 assert _json_safe([float('inf'),float('-inf')])==[{'nonfinite':'positive_infinity'},{'nonfinite':'negative_infinity'}]
 class EmptyAuthor:
  def collar_guard(self,*a):raise AssertionError('empty variable set must not call guard helper')
  def descent_constraints(self,*a):raise AssertionError('empty variable set must not call D8 constructor')
 class EmptyEV: WINDOW=(10,11,10,11)
 empty_guard=guard_d8(EmptyEV(),EmptyAuthor(),[],np.zeros((12,12),dtype=np.float32))
 assert empty_guard['guard_count']==0 and empty_guard['free_count']==0 and empty_guard['descent_matrix_shape']==[0,0]
 status_domain={'focus_status':'variable','both_axes_box_feasible_for_25_percent':True}
 assert _preflight_status(status_domain,{'box_is_usable':True},empty_guard,False)=='PREFLIGHT_INFEASIBLE'
 from tempfile import TemporaryDirectory
 with TemporaryDirectory() as td:
  fp=Path(td)/'input.bin';fp.write_bytes(b'identity-a');_assert_path_hashes({str(fp):sha(fp)})
  fp.write_bytes(b'identity-b')
  try:_assert_path_hashes({str(fp):hashlib.sha256(b'identity-a').hexdigest()})
  except AssertionError:pass
  else:raise AssertionError('readset mutation fixture did not fail closed')
 return {'scope_restored_even_on_exception':'PASS','EV93_inclusive_range_query':'PASS','NW_SE_inclined_native_planes':'PASS',
  'tiny_positive_area_retained_without_Ev87_cutoff':'PASS','degenerate_face_retained_but_not_clipped':'PASS',
  'stencil_support_matches_frozen_EV88':'PASS','empty_and_invalid_boxes_rejected':'PASS',
   'nonfinite_report_marker':'PASS','empty_guard_d8_classification':'PASS','no_free_variables_infeasible':'PASS',
   'initial_readset_hash_is_enforced':'PASS'}

if __name__=='__main__':main()






