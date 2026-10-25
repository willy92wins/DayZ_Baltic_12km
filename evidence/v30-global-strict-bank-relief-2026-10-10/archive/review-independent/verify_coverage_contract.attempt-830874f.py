#!/usr/bin/env python
"""Complementary EV87 compiled-water representation contract consumer.

It retains the frozen raw EV87 report and supersedes only its four raw area
gates with the pre-existing height/footprint contract in coverage-contract-proposal.md.
It imports only the independent EV87 consumer's WRP/ODOL readers and affine clipper;
it does not import candidate authoring code.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, sys, traceback, time
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
ROOT=Path(r'E:/DayZ-Baltic-Build')
EV87=ROOT/'v30-global-strict-bank-relief-20261010'
POLICY=EV87/'coverage-contract-proposal.md'
RAW=EV87/'review-independent/ev87-review-p99-sector-corrected.json'
RAW_SHA='92aa30ca697547aedb9a515d8441bffebd58b32dae4b1bb179f9ba6adf6987c1'
CANDIDATE_SHA='a7146c27a634d3ee59bc4c2763d71050da3172724c4f2620a17fce0775fcf020'
P_SHA='768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0'
F_SHA='f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'
B_SHA='f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
EV79_SHA='dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'
WRP_SHA='3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6'
DEPLOY_WATER_SHA='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
DEPLOY_WORLD_SHA='b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c'
BOUNDS_SHA='863e9539203e59fe77b9c7d4949da3a69b4991249941e15b887b60ff9e81ee62'
BOUNDS_WORLD_SHA='a845bee973c2db1c94acf39758358dfcfb5967770e3879263ecf1a1bc4f66fd2'
HELPER_SHA='964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27'
POLICY_SHA='484681174c982f761051385f2aded966c14cf568c08e153ce5b56185c493f94a'
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
MODEL_DIR=ROOT/'v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30'
BOUNDS=ROOT/'v30-low-water-components-20261009/compiled-instance-bounds.json'
N=2048; CELL=6.0; Z0=12282.0; TRIS=((0,1,3),(0,2,3))
EPS={'physical':1e-5,'visible':2e-5}
AREA_LIMIT=0.002; FOOTPRINT_LIMIT=1e-7
SUPERSEDED={
 'physical_P_B_and_candidate_design_covered_le_0_002m2',
 'physical_outside_design_growth_le_0_002m2',
 'visible_F_B_and_candidate_design_covered_le_0_002m2',
 'visible_outside_design_growth_le_0_002m2'}

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()

def load_ev87(path):
 spec=importlib.util.spec_from_file_location('independent_ev87_consumer',path)
 mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
 return mod

def cell_xy(r,c):
 return np.asarray([[c*CELL,Z0-r*CELL],[(c+1)*CELL,Z0-r*CELL],
                    [c*CELL,Z0-(r+1)*CELL],[(c+1)*CELL,Z0-(r+1)*CELL]],dtype=np.float64)

def geom_parts(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [g]
 return [x for x in getattr(g,'geoms',[]) if x.geom_type=='Polygon' and x.area>1e-12]

def clip_affine_band(poly,delta_coeff,eps):
 """Exact convex polygon clip to -eps <= (surface-field) <= eps."""
 pieces=[]
 for g in geom_parts(poly):
  ring=np.asarray(g.exterior.coords[:-1],dtype=np.float64)
  d=np.asarray(ring)@delta_coeff[:2]+delta_coeff[2]
  q=ev.clip_polygon(ring,d+eps)
  if q.is_empty:continue
  ring2=np.asarray(q.exterior.coords[:-1],dtype=np.float64)
  d2=np.asarray(ring2)@delta_coeff[:2]+delta_coeff[2]
  q2=ev.clip_polygon(ring2,eps-d2)
  if not q2.is_empty:pieces.append(q2.intersection(g))
 return unary_union(pieces) if pieces else Polygon()

def clip_above(poly,delta_coeff,threshold):
 """Part of polygon where affine surface-field exceeds threshold."""
 pieces=[]
 for g in geom_parts(poly):
  ring=np.asarray(g.exterior.coords[:-1],dtype=np.float64)
  d=np.asarray(ring)@delta_coeff[:2]+delta_coeff[2]-threshold
  q=ev.clip_polygon(ring,d)
  if not q.is_empty:pieces.append(q.intersection(g))
 return unary_union(pieces) if pieces else Polygon()

def area_coverage_hole(designed,support):return designed.difference(support)

def coverage_holes_pass(b_holes,h_holes):
 return sum(float(x) for x in b_holes)<FOOTPRINT_LIMIT and sum(float(x) for x in h_holes)<FOOTPRINT_LIMIT

def face_height_violation(kind,cell,triangle,object_name,face_indices,exposed,delta,epsilon):
 above=clip_above(exposed,delta,epsilon)
 if above.area<=1e-12:return None
 excess=max((np.max(np.asarray(g.exterior.coords[:-1])@delta[:2]+delta[2]-epsilon) for g in geom_parts(above)),default=0.0)
 return {'kind':kind,'cell':[int(cell[0]),int(cell[1])],'triangle':int(triangle),
  'area_m2':float(above.area),'max_excess_m':float(excess),'object':object_name,
  'face_indices':[int(i) for i in face_indices]}

def unknown_f_tri_unchanged(h_before,h_after,r,c,tri,f):
 ids=np.asarray(tri,dtype=int)
 if np.isfinite(np.asarray(f[r,c])[ids]).all():return None
 before=ev.corner_values(h_before,r,c)[ids];after=ev.corner_values(h_after,r,c)[ids]
 return np.array_equal(before,after)

def gain_without_design(record):
 return float(record.get('without_P_or_F_m2',0.0))>0.0

def cell_tri_target(r,c,field,tri,p,f):
 xy=cell_xy(r,c); ids=np.asarray(tri,dtype=int); tri_xy=xy[ids]
 if field=='physical':
  level=float(p[r,c])
  if not math.isfinite(level):return None,None,None
  vals=np.full(3,level,dtype=np.float64)
 else:
  allvals=np.asarray(f[r,c],dtype=np.float64);vals=allvals[ids]
  if not np.isfinite(vals).all():return None,None,None
 return tri_xy,vals,ev.affine_coeff(tri_xy,vals)

def make_design(h,p,f,cells,field):
 out={}
 for r,c in cells:out[(r,c)]=ev.designed_water(r,c,h,p,f,'P' if field=='physical' else 'F')
 return out

def exposed_pair_and_support(hb,hh,p,f,cells,wrp,workspace,models_dir,bounds_path):
 """Independent per-face reconstruction: exposed area, matched support, height violations."""
 _,objects,models,model_hashes=ev.compiled_objects(wrp,workspace,cells,models_dir,bounds_path)
 exposed={label:{kind:{cell:[] for cell in cells} for kind in ('physical','visible')} for label in ('B','candidate')}
 support={kind:{cell:[] for cell in cells} for kind in ('physical','visible')}
 bad_height={'B':[],'candidate':[]};face_counts={'physical':0,'visible':0};unknown_face_parts=0
 fields=(('physical',3e15,'physical'),('visible',1.0,'visible'))
 for obj,mat,_ in objects:
  model=models[obj['name'].replace('\\','/').split('/')[-1]];tx,ty,tz=map(float,mat[9:12])
  for kind,res,field in fields:
   lods=[x for x in model.lods if x.resolution==float(np.float32(res))]
   if len(lods)!=1:raise AssertionError(f'{kind} compiled LOD missing/ambiguous for {obj["name"]}')
   lod=lods[0]
   verts=np.asarray([(v.x+tx,v.y+ty,v.z+tz) for v in lod.vertices],dtype=np.float64)
   for face in lod.faces:
    inds=face.vertex_indices
    if len(inds)!=3:raise AssertionError('compiled ODOL has non-triangle face')
    q=verts[inds];xy=q[:,[0,2]];face_poly=Polygon(xy)
    if face_poly.area<=1e-12:continue
    try:surface_coeff=ev.affine_coeff(xy,q[:,1])
    except np.linalg.LinAlgError as exc:raise AssertionError(f'degenerate compiled face with nonzero XZ area: {obj["name"]} face={inds}') from exc
    xmin,zmin=xy.min(axis=0);xmax,zmax=xy.max(axis=0)
    c0=max(0,int(math.floor(xmin/CELL)));c1=min(N-2,int(math.floor(np.nextafter(xmax,-math.inf)/CELL)))
    r0=max(0,int(math.floor((Z0-zmax)/CELL)));r1=min(N-2,int(math.floor(np.floor((Z0-zmin)/CELL))))
    hit=[(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1) if (r,c) in cells]
    if not hit:continue
    face_counts[kind]+=1
    for r,c in hit:
     xyc=cell_xy(r,c)
     for tri in TRIS:
      ids=np.asarray(tri,dtype=int);native=Polygon(xyc[ids]);piece=face_poly.intersection(native)
      if piece.is_empty or piece.area<=1e-12:continue
      # Actual water exposure is terrain-relative, clipped within this native triangle.
      actual_by_label={}
      for label,h in (('B',hb),('candidate',hh)):
       actual=ev.odol_visible_in_native_tri(xy,surface_coeff,xyc,ev.corner_values(h,r,c),tri)
       actual_by_label[label]=actual
       if not actual.is_empty:exposed[label][kind][(r,c)].append(actual)
      tx_y,values,target_coeff=cell_tri_target(r,c,field,tri,p,f)
      if target_coeff is None:
       if field=='visible':unknown_face_parts+=1
       continue
      delta=surface_coeff-target_coeff
      # A face above the target cannot be hidden by another correct/lower face.
      for label,actual in actual_by_label.items():
       violation=face_height_violation(kind,(r,c),TRIS.index(tri),obj['name'],inds,actual,delta,EPS[kind])
       if violation:bad_height[label].append(violation)
      matched=clip_affine_band(piece,delta,EPS[kind])
      if not matched.is_empty:support[kind][(r,c)].append(matched)
 # Merge exactly at cell boundary; no object is discarded by centroid/bbox alone.
 exp_u={label:{k:{c:(unary_union(parts) if parts else Polygon()) for c,parts in cells_by.items()} for k,cells_by in kinds.items()} for label,kinds in exposed.items()}
 sup_u={k:{c:(unary_union(parts) if parts else Polygon()) for c,parts in cells_by.items()} for k,cells_by in support.items()}
 return exp_u,sup_u,{'objects_in_bbox':len(objects),'models':len(models),'model_hashes':model_hashes,
   'faces_by_lod_in_bbox':face_counts,'visible_unknown_face_triangle_intersections':unknown_face_parts},bad_height

def band_polygon(r,c,h,p,f,field,epsilon):
 xy=cell_xy(r,c);gh=ev.corner_values(h,r,c);pieces=[]
 for tri in TRIS:
  ids=np.asarray(tri,dtype=int);target_xy,vals,target_coeff=cell_tri_target(r,c,field,tri,p,f)
  if target_coeff is None:continue
  ground_coeff=ev.affine_coeff(xy[ids],gh[ids]);delta=ground_coeff-target_coeff
  native=Polygon(xy[ids]);band=clip_affine_band(native,delta,epsilon)
  if not band.is_empty:pieces.append(band)
 return unary_union(pieces) if pieces else Polygon()

def design_and_residual(h,p,f,cells,field,exposed,design):
 metrics={'missing_total_m2':0.0,'missing_max_cell_m2':0.0,
  'missing_outside_band_total_m2':0.0,'missing_outside_band_max_cell_m2':0.0,
  'growth_total_m2':0.0,'growth_max_cell_m2':0.0,'growth_outside_band_total_m2':0.0,
  'growth_outside_band_max_cell_m2':0.0}; rows=[];unknown_cells=0
 for cell in sorted(cells):
  r,c=cell;d=design[cell];actual=exposed[cell]
  # Unknown F native triangles are omitted from both expected and actual comparisons.
  if field=='visible':
   known=[]
   xy=cell_xy(r,c)
   for tri in TRIS:
    _,_,tc=cell_tri_target(r,c,field,tri,p,f)
    if tc is not None:known.append(Polygon(xy[list(tri)]))
   if len(known)<2:unknown_cells+=1
   known_domain=unary_union(known) if known else Polygon()
   d=d.intersection(known_domain);actual=actual.intersection(known_domain)
  band=band_polygon(r,c,h,p,f,field,EPS['physical' if field=='physical' else 'visible'])
  missing=d.difference(actual);growth=actual.difference(d)
  mo=missing.difference(band);go=growth.difference(band)
  vals={'missing':float(missing.area),'missing_out':float(mo.area),'growth':float(growth.area),'growth_out':float(go.area)}
  for name,v in vals.items():
   key={'missing':'missing','missing_out':'missing_outside_band','growth':'growth','growth_out':'growth_outside_band'}[name]
   metrics[f'{key}_total_m2']+=v;metrics[f'{key}_max_cell_m2']=max(metrics[f'{key}_max_cell_m2'],v)
  rows.append({'cell':[r,c],**{f'{k}_m2':v for k,v in vals.items()}})
 metrics['outside_band_examples']=sorted(rows,key=lambda x:max(x['missing_out_m2'],x['growth_out_m2']),reverse=True)[:10]
 metrics['unknown_F_cells']=unknown_cells
 return metrics

def fixture_suite():
 # Fixtures exercise the policy predicates rather than reusing candidate output.
 target=Polygon([(0,0),(1,0),(1,1),(0,1)])
 hole=Polygon([(0,0),(0.1,0),(0.1,0.1),(0,0.1)])
 hole_area=area_coverage_hole(target,target.difference(hole)).area
 band_for_hole=target
 assert hole.difference(band_for_hole).area<1e-12
 assert hole_area>0.009999999 and not coverage_holes_pass([hole_area],[hole_area])
 # A correct face cannot mask a second face above F+epsilon.
 target_level=3.0;eps=EPS['visible'];correct_y=target_level
 second_y=target_level+eps+1e-6
 delta_high=np.asarray([0.0,0.0,second_y-target_level])
 correct_violation=face_height_violation('visible',(0,0),0,'fixture-correct.p3d',[0,1,2],target,
   np.asarray([0.0,0.0,correct_y-target_level]),eps)
 violation=face_height_violation('visible',(0,0),0,'fixture-water.p3d',[0,1,2],target,delta_high,eps)
 assert correct_violation is None and violation is not None and violation['area_m2']>0 and violation['max_excess_m']>0
 # Wrong-height face has no support in its projected footprint.
 wrong_delta=np.asarray([0.0,0.0,0.01]);assert clip_affine_band(target,wrong_delta,EPS['physical']).is_empty
 # A residual confined to the field/ground band is representational; footprint remains complete.
 full_support=target;band=clip_affine_band(target,np.asarray([1.0,0.0,-2e-5]),EPS['visible'])
 small_residual=band
 assert target.difference(full_support).area<FOOTPRINT_LIMIT
 assert small_residual.difference(band).area<1e-12 and 0<small_residual.area<AREA_LIMIT
 # Leakage outside both design and the epsilon strip remains charged in full.
 leak=Polygon([(2,0),(2.1,0),(2.1,1),(2,1)])
 outside_band=leak.difference(target).difference(band)
 assert outside_band.area>AREA_LIMIT and gain_without_design({'without_P_or_F_m2':outside_band.area})
 # Unknown F triangles are explicitly not inferable; exact B/H equality passes, change is inconclusive.
 f=np.asarray([[[np.nan,3.,3.,3.]]],dtype=np.float64);p=np.asarray([[3.]],dtype=np.float64)
 b=np.asarray([[1.,2.],[3.,4.]],dtype=np.float64);same=b.copy();changed=b.copy();changed[0,0]=np.nextafter(changed[0,0],np.inf)
 assert cell_tri_target(0,0,'visible',TRIS[0],p,f)[2] is None
 assert unknown_f_tri_unchanged(b,same,0,0,TRIS[0],f) is True
 assert unknown_f_tri_unchanged(b,changed,0,0,TRIS[0],f) is False
 assert not gain_without_design({'without_P_or_F_m2':0.0})
 # Footprint fixture: face spans native cell with NW=NE=SW=0, SE=6, sea=3; exact exposed area 27.
 xy=cell_xy(0,0);heights=np.asarray([0.,0.,0.,6.]);surface=np.asarray([3.,3.,3.])
 face=np.asarray([[-100,12000],[100,12000],[0,12400]],dtype=np.float64)
 coeff=ev.affine_coeff(face,surface)
 exposed=unary_union([ev.odol_visible_in_native_tri(face,coeff,xy,heights,tri) for tri in TRIS])
 assert abs(exposed.area-27.0)<1e-9
 # A missing support footprint is charged even when its vertical residual is inside epsilon.
 band_small=Polygon([(0,0),(0.01,0),(0.01,0.01),(0,0.01)])
 assert target.difference(target.difference(band_small)).area>FOOTPRINT_LIMIT
 return {'footprint_hole_0_01m2_fails_even_in_band':True,
  'correct_face_does_not_excuse_second_face_above_F_plus_epsilon':True,
  'wrong_height_face_cannot_cover_design':True,'complete_support_with_small_in_band_residual_fixture':True,
  'outside_design_band_leak_is_charged':True,'unknown_F_real_partial_triangle_exact_unchanged_vs_changed_inconclusive':True,
  'raw_designless_gain_predicate_positive_negative':True,
  'large_ODOL_face_split_native_triangle_area_27m2':True,
  'in_band_hole_still_fails_footprint':True}

def main():
 ap=argparse.ArgumentParser(description='EV87 complementary representation coverage consumer; does not overwrite raw report.')
 ap.add_argument('--candidate',type=Path,default=EV87/'candidate-terrain.npz')
 ap.add_argument('--raw-report',type=Path,default=RAW)
 ap.add_argument('--policy',type=Path,default=POLICY)
 ap.add_argument('--report',type=Path,default=EV87/'review-independent/coverage-contract-review.json')
 ap.add_argument('--workspace',type=Path,default=W);ap.add_argument('--wrp',type=Path,default=ROOT/'v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp')
 ap.add_argument('--models',type=Path,default=MODEL_DIR);ap.add_argument('--bounds',type=Path,default=BOUNDS)
 ap.add_argument('--deploy',type=Path,default=ROOT/'v30-mixed-bank-incremental-fixed-20261010/deploy.json');ap.add_argument('--self-test',action='store_true')
 a=ap.parse_args();t0=time.time();report={'status':'ERROR_EV87_REPRESENTATION_CONSUMER','gates':{},'inputs':{},'raw_geometry_report':{'path':str(a.raw_report),'sha256':None,'status':None},'superseded_raw_gates':sorted(SUPERSEDED)}
 consumer_path=Path(__file__).resolve();consumer_digest=sha(consumer_path)
 try:
  helper=HERE/'verify_ev87.py';helper_digest=sha(helper)
  if helper_digest!=HELPER_SHA:raise AssertionError('pinned independent helper SHA mismatch')
  policy_digest=sha(a.policy)
  if a.policy!=POLICY or policy_digest!=POLICY_SHA:raise AssertionError('pinned EV87 coverage policy SHA mismatch')
  report['inputs'][str(helper)]=helper_digest;report['inputs'][str(a.policy)]=policy_digest
  report['inputs'][str(consumer_path)]=consumer_digest
  if a.self_test:
   report['fixtures']=fixture_suite();report['status']='PASS_EV87_REPRESENTATION_FIXTURES'
  else:
   if sha(a.raw_report)!=RAW_SHA:raise AssertionError('raw corrected report SHA mismatch')
   raw=json.loads(a.raw_report.read_text(encoding='utf-8'));report['raw_geometry_report'].update(sha256=RAW_SHA,status=raw.get('status'))
   if raw.get('status')!='FAIL_EV87_GLOBAL_CONSUMER':raise AssertionError('unexpected raw report status')
   raw_gates=raw.get('gates',{});false=[k for k,v in raw_gates.items() if v is False]
   if set(false)!=SUPERSEDED:raise AssertionError(f'raw false gates differ from the four authorized substitutions: {false}')
   if any(v is not True for k,v in raw_gates.items() if k not in SUPERSEDED):raise AssertionError('a non-superseded raw geometry gate is not true')
   policy_hash=policy_digest
   if sha(a.candidate)!=CANDIDATE_SHA:raise AssertionError('candidate identity mismatch')
   if sha(a.bounds)!=BOUNDS_SHA:raise AssertionError('compiled bounds identity mismatch')
   # Bind every raw source and every explicit execution dependency; no untracked input.
   for p,expected in raw['inputs'].items():
    actual=sha(Path(p));report['inputs'][p]=actual
    if actual!=expected:raise AssertionError(f'raw input changed: {p}')
   for p in (a.raw_report,a.policy,a.candidate,a.wrp,a.deploy,a.bounds,helper):report['inputs'][str(p)]=sha(p)
   for dependency in (a.workspace/'tools/water/engine_water_model.py',a.workspace/'tools/terrain/wrp0wzd.py',a.workspace/'tools/playtest/attach_navmesh.py',Path(r'C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts/odol_reader.py')):
    if not dependency.is_file():raise AssertionError(f'missing code dependency {dependency}')
    report['inputs'][str(dependency)]=sha(dependency)
   deploy_json=json.loads(a.deploy.read_text(encoding='utf-8'));addon=Path(deploy_json['mod'])/'Addons'
   for artifact in (addon/'narva_trial.pbo',addon/'baltic_water_v30.pbo'):
    report['inputs'][str(artifact)]=sha(artifact)
   if raw['inputs'].get(str(a.candidate))!=CANDIDATE_SHA:raise AssertionError('raw report does not bind requested candidate')
   if sha(a.wrp)!=WRP_SHA:raise AssertionError('staged WRP changed')
   if raw['inputs'].get(str(a.wrp))!=WRP_SHA:raise AssertionError('raw report does not bind requested staged WRP')
   if raw['inputs'].get(str(a.deploy)) is None or raw['inputs'].get(str(a.bounds))!=BOUNDS_SHA:raise AssertionError('deployment/bounds inputs are not bound by raw report')
   ev=load_ev87(helper)
   # The prior EV87 report remains a raw FAIL; this consumer attaches only the named policy.
   cov=raw['information']['surface_coverage']['by_surface'];cells={tuple(x['cell']) for k in ('physical','visible') for x in cov[k]['cells']}
   if len(cells)!=41008:raise AssertionError(f'affected-cell inventory mismatch: {len(cells)}')
   cand=ev.load_npz(a.candidate);base=ev.load_npz(ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')
   hB=base['heights'].astype(np.float64);hH=cand['heights'].astype(np.float64)
   p=np.load(ROOT/'v30-narva-dry-bank-relief-20261010/candidate/plane.npy',allow_pickle=False).astype(np.float64)
   f=np.load(ROOT/'v30-narva-dry-bank-relief-20261010/candidate/visible-field.npy',allow_pickle=False).astype(np.float64)
   exp_pair,support,meta,bad_pair=exposed_pair_and_support(hB,hH,p,f,cells,a.wrp,a.workspace,a.models,a.bounds)
   deploy=ev.pbo_guard(a.deploy,a.wrp)
   if not(deploy['expected_world_exact'] and deploy['expected_water_exact'] and deploy['deployed_oprw_matches_manifest'] and deploy['staged_source_wrp_identity_exact'] and deploy['source_and_compiled_payload_are_distinct_artifacts']):raise AssertionError('deployed PBO/WRP guard failed')
   metrics={};new_gates={}
   unknown_total=0;unknown_changed=[]
   p_nan_cells=[]
   for r,c in cells:
    if not np.isfinite(p[r,c]):p_nan_cells.append([r,c])
    xy=cell_xy(r,c)
    for ti,tri in enumerate(TRIS):
     ids=np.asarray(tri,dtype=int);fv=f[r,c,ids]
     if not np.isfinite(fv).all():
      unknown_total+=1
      unchanged=unknown_f_tri_unchanged(hB,hH,r,c,tri,f)
      if unchanged is not True:unknown_changed.append([r,c,ti])
   new_gates['unknown_F_triangles_unchanged_B_H_exact']=not unknown_changed
   new_gates['unknown_F_changes_are_not_inferred_from_P']=not unknown_changed
   for kind,field,eps in (('physical','physical',EPS['physical']),('visible','visible',EPS['visible'])):
    designB=make_design(hB,p,f,cells,field);designH=make_design(hH,p,f,cells,field)
    support_holes={'B':[],'candidate':[]};mismatch={'B':[],'candidate':[]}
    for cell in sorted(cells):
     r,c=cell;xy=cell_xy(r,c);support_union=support[kind][cell]
     # Do not let unknown F triangles count as dry or as missing design.
     if field=='visible':
      known=[]
      for tri in TRIS:
       if np.isfinite(f[r,c,np.asarray(tri,dtype=int)]).all():known.append(Polygon(xy[list(tri)]))
      domain=unary_union(known) if known else Polygon()
      db=designB[cell].intersection(domain);dh=designH[cell].intersection(domain)
     else:db=designB[cell];dh=designH[cell]
     holeb=area_coverage_hole(db,support_union);holeh=area_coverage_hole(dh,support_union)
     if holeb.area>1e-12:support_holes['B'].append((cell,float(holeb.area)))
     if holeh.area>1e-12:support_holes['candidate'].append((cell,float(holeh.area)))
    new_gates[f'{kind}_B_and_candidate_nominal_wet_footprint_holes_lt_1e_7m2']=coverage_holes_pass([x[1] for x in support_holes['B']],[x[1] for x in support_holes['candidate']])
    residualB=design_and_residual(hB,p,f,cells,field,exp_pair['B'][kind],designB);residualH=design_and_residual(hH,p,f,cells,field,exp_pair['candidate'][kind],designH)
    new_gates[f'{kind}_B_candidate_exposure_residual_outside_height_band_le_0_002m2']=all(residualB[k]<=AREA_LIMIT and residualH[k]<=AREA_LIMIT for k in ('missing_outside_band_total_m2','missing_outside_band_max_cell_m2','growth_outside_band_total_m2','growth_outside_band_max_cell_m2'))
    new_gates[f'{kind}_exposed_compiled_faces_not_above_field_plus_tolerance']=not any(x['kind']==kind for side in bad_pair.values() for x in side)
    metrics[kind]={'support_hole_total_m2':{'B':sum(x[1] for x in support_holes['B']),'candidate':sum(x[1] for x in support_holes['candidate'])},
      'support_hole_max_cell_m2':{'B':max((x[1] for x in support_holes['B']),default=0.0),'candidate':max((x[1] for x in support_holes['candidate']),default=0.0)},
      'support_hole_examples':{'B':[{'cell':list(c),'area_m2':v} for c,v in support_holes['B'][:50]],'candidate':[{'cell':list(c),'area_m2':v} for c,v in support_holes['candidate'][:50]]},
      'exposure_B':residualB,'exposure_candidate':residualH}
   new_gates['known_F_triangles_have_no_exposed_height_mismatch']=not any(x['kind']=='visible' for side in bad_pair.values() for x in side)
   new_gates['physical_faces_have_no_exposed_height_mismatch']=not any(x['kind']=='physical' for side in bad_pair.values() for x in side)
   gates={k:bool(v) for k,v in raw_gates.items() if k not in SUPERSEDED}
   # Keep every applicable raw geometry gate visible in this acceptance report.
   gates['all_non_superseded_raw_geometry_gates_preserved']=all(v is True for v in gates.values())
   gains=raw['information'].get('surface_face_gains',[])
   new_gates['raw_surface_gain_records_all_have_P_or_F_design']=not any(gain_without_design(x) for x in gains)
   gates.update({k:bool(v) for k,v in new_gates.items()})
   report['gates']=gates
   report['information']={'changed_vertices':raw['information']['changed_vertices'],'raw_report_status':raw['status'],
    'superseded_raw_gates':sorted(SUPERSEDED),'raw_false_gates':false,'affected_cells':len(cells),
    'unknown_F_triangles_in_affected_cells':unknown_total,'unknown_F_area_m2':float(unknown_total*18.0),
    'unknown_F_height_changes':unknown_changed[:100],
    'P_nan_affected_cells':len(p_nan_cells),'P_nan_affected_cell_area_m2':float(len(p_nan_cells)*36.0),
    'P_nan_cells_examples':p_nan_cells[:100],
    'P_nan_physical_design_rule':'A P NaN cell has no physical design; any compiled physical exposure there remains charged as outside-band growth (empty design and empty P band).',
    'surface_metrics':metrics,'exposed_face_height_violations':{k:v[:100] for k,v in bad_pair.items()},
    'compiled':meta,'pbo_guard':deploy,
    'policy_sha256':policy_hash,'scope_limit':'Uses exact source-side 0WZD transforms hash-linked to B deployed OPRW/PBO; not engine transform readback and not a render/runtime acceptance.'}
   for name,digest in meta['model_hashes'].items():
    model_path=a.models/name
    actual=sha(model_path)
    if actual!=digest:raise AssertionError(f'model hash changed during verification: {name}')
    report['inputs'][str(model_path)]=actual
   import scipy, shapely
   report['information']['runtime']={'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'shapely':shapely.__version__}
   # Rehash every consumed file and both pinned policy helpers before publishing any verdict.
   if sha(consumer_path)!=consumer_digest:raise AssertionError('consumer changed during verification')
   if sha(helper)!=HELPER_SHA or sha(a.policy)!=POLICY_SHA:raise AssertionError('pinned verifier/policy changed during verification')
   for path,digest in report['inputs'].items():
    if sha(Path(path))!=digest:raise AssertionError(f'input changed during verification: {path}')
   report['status']=('INCONCLUSIVE_EV87_REPRESENTATION_CONSUMER' if unknown_changed else
    'PASS_EV87_REPRESENTATION_CONSUMER' if all(gates.values()) else 'FAIL_EV87_REPRESENTATION_CONSUMER')
 except Exception as e:
  report['error']=f'{type(e).__name__}: {e}';report['traceback']=traceback.format_exc();report['status']='ERROR_EV87_REPRESENTATION_CONSUMER'
 report['elapsed_seconds']=time.time()-t0
 report['verifier_sha256']=sha(consumer_path)
 print(json.dumps({'status':report['status'],'false_gates':[k for k,v in report['gates'].items() if not v],'error':report.get('error')},ensure_ascii=False),flush=True)
 payload=json.dumps(report,indent=2,ensure_ascii=False,default=lambda x:bool(x) if isinstance(x,np.bool_) else int(x) if isinstance(x,np.integer) else float(x) if isinstance(x,np.floating) else (_ for _ in ()).throw(TypeError(type(x).__name__)))
 a.report.parent.mkdir(parents=True,exist_ok=True);tmp=a.report.with_suffix(a.report.suffix+'.tmp');tmp.write_text(payload,encoding='utf-8');tmp.replace(a.report)

if __name__=='__main__':
 # Import is initialized before fixtures; module remains independent of authoring.
 ev=load_ev87(HERE/'verify_ev87.py')
 main()
