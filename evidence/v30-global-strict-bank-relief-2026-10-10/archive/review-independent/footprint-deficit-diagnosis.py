import hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT=Path(r'E:/DayZ-Baltic-Build')
EV=ROOT/'v30-global-strict-bank-relief-20261010'
REVIEW=EV/'review-independent'
REPORT=REVIEW/'coverage-contract-review.json'
CAND=EV/'candidate-terrain.npz'
B=ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
P=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/plane.npy'
F=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/visible-field.npy'
LEDGER=EV/'queue-ledger.jsonl'; DIRECTIONS=EV/'directions.npz'
CONSUMER=REVIEW/'verify_coverage_contract.py'; HELPER=REVIEW/'verify_ev87.py'
WRP=ROOT/'v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
MODELS=ROOT/'v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30'
BOUNDS=ROOT/'v30-low-water-components-20261009/compiled-instance-bounds.json'
WORKSPACE=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(WORKSPACE/'tools/water'))
from engine_water_model import ODOL
OUT=REVIEW/'footprint-deficit-diagnosis.json'

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
 return h.hexdigest()

def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

def main():
 report=json.loads(REPORT.read_text(encoding='utf-8'))
 # The report's complete support-hole lists are <50 entries; retain all cells above numerical noise.
 cells={}
 for kind in ('physical','visible'):
  holes=report['information']['surface_metrics'][kind]['support_hole_examples']
  bmap={tuple(x['cell']):x['area_m2'] for x in holes['B']}
  hmap={tuple(x['cell']):x['area_m2'] for x in holes['candidate']}
  for cell,area in hmap.items():
   if area>1e-10 or area-bmap.get(cell,0)>1e-10:
    rec=cells.setdefault(cell,{'B':{},'candidate':{}});rec['B'][kind]=bmap.get(cell,0.0);rec['candidate'][kind]=area
 # Pin only concrete inputs used by this local diagnosis.
 paths=[Path(__file__),REPORT,CAND,B,P,F,LEDGER,DIRECTIONS,CONSUMER,HELPER,WRP,BOUNDS]
 input_hashes={str(p):sha(p) for p in paths}
 ev=load(HELPER,'ev87_local'); consumer=load(CONSUMER,'coverage_contract_local');consumer.ev=ev
 b=np.load(B)['heights']; h=np.load(CAND)['heights']; p=np.load(P); f=np.load(F)
 ledger=[json.loads(s) for s in LEDGER.read_text(encoding='utf-8').splitlines()]
 events={x['queue_id']:x for x in ledger if x.get('event')=='patch'}
 directions=np.load(DIRECTIONS)
 cell_corners={}
 patch_at_node={}
 for q,e in events.items():
  if e['state']!='accepted':continue
  vec=directions[e['direction_key']]
  for node,d in zip(e['mutable_nodes'],vec):
   node=tuple(node); patch_at_node.setdefault(node,[]).append({'queue_id':q,'delta_m':float(d),'direction_key':e['direction_key']})
 for cell in cells:
  r,c=cell; corners=[(r,c),(r,c+1),(r+1,c),(r+1,c+1)]
  changed=[]
  for node in corners:
   delta=float(h[node]-b[node])
   if delta!=0.0:changed.append({'node':list(node),'B_m':float(b[node]),'candidate_m':float(h[node]),'delta_m':delta,'patches':patch_at_node.get(node,[])})
  cell_corners[cell]=changed
 # Reconstruct the exact compiled face footprint/support only for this small cell set.
 # Match each model bounds against the small set of target cells individually.
 # A single min/max bbox over map-distant cells would select most of the water world.
 wrp=ev.load_wrp_api(WRP,WORKSPACE)
 inv=json.loads(BOUNDS.read_text(encoding='utf-8'))
 bounds={int(o['id']):o['bounds'] for o in inv['objects']}
 water=[o for o in wrp['objects'] if 'baltic_water_v30' in o['name'].replace('\\','/').lower()]
 chosen=[]
 for obj in water:
  bb=bounds.get(int(obj['id']))
  if bb is None:continue
  bx0,bz0,bx1,bz1=bb
  if any(not (bx1<c*6.0 or bx0>(c+1)*6.0 or bz1<12282.0-(r+1)*6.0 or bz0>12282.0-r*6.0) for r,c in cells):
   matrix=np.asarray(obj['matrix'],dtype=np.float64)
   if not np.array_equal(matrix[:9].reshape(3,3),np.eye(3)):raise AssertionError('non-translation water transform')
   chosen.append((obj,matrix,bb))
 models={};model_hashes={}
 for obj,matrix,bb in chosen:
  name=obj['name'].replace('\\','/').split('/')[-1]
  if name not in models:
   path=MODELS/name; expected=inv.get('models',{}).get(name,{}).get('sha256')
   if not expected or sha(path)!=expected:raise AssertionError(f'compiled model hash mismatch: {name}')
   model_hashes[name]=expected;models[name]=ODOL.from_file(str(path))
 objects=chosen
 tr=( (0,1,3),(0,2,3) ); eps={'physical':1e-5,'visible':2e-5}; details={}
 for cell in sorted(cells):
  r,c=cell; xy=consumer.cell_xy(r,c); cellpoly=Polygon(xy[[0,1,3,2]])
  detail={'B':{},'candidate':{}}
  for label,ground in [('B',b),('candidate',h)]:
   for kind,field,res in [('physical','physical',3e15),('visible','visible',1.0)]:
    design=consumer.make_design(ground,p,f,[cell],field)[cell]
    all_foot=[]; matched=[]; touch=[]; hole_face_hits=[]
    for obj,mat,_ in objects:
     name=obj['name']; model=models[name.replace('\\','/').split('/')[-1]]; tx,ty,tz=map(float,mat[9:12])
     lods=[x for x in model.lods if x.resolution==float(np.float32(res))]
     if len(lods)!=1:continue
     lod=lods[0]
     verts=np.asarray([(v.x+tx,v.y+ty,v.z+tz) for v in lod.vertices],dtype=np.float64)
     for fi,face in enumerate(lod.faces):
      inds=face.vertex_indices
      if len(inds)!=3:continue
      q=verts[inds]
      facepoly=Polygon(q[:,[0,2]])
      if facepoly.is_empty or facepoly.area<=1e-12:continue
      hit=facepoly.intersection(cellpoly)
      if hit.is_empty or hit.area<=1e-12:continue
      all_foot.append(hit)
      touch.append({'object':name,'face_index':int(fi),'face_indices':[int(i) for i in inds],'intersection_m2':float(hit.area)})
      coeff=ev.affine_coeff(q[:,[0,2]],q[:,1])
      for ti,tri in enumerate(tr):
       ids=np.asarray(tri,dtype=int); native=Polygon(xy[ids]); piece=facepoly.intersection(native)
       if piece.is_empty or piece.area<=1e-12:continue
       _,_,target_coeff=consumer.cell_tri_target(r,c,field,tri,p,f)
       if target_coeff is None:continue
       band=consumer.clip_affine_band(piece,coeff-target_coeff,eps[kind])
       if not band.is_empty:matched.append(band)
    footprint=unary_union(all_foot) if all_foot else Polygon()
    matched_u=unary_union(matched) if matched else Polygon()
    hole=design.difference(matched_u)
    outside=hole.difference(footprint)
    if label=='candidate' and not hole.is_empty:
     for obj,mat,_ in objects:
      name=obj['name'];model=models[name.replace('\\','/').split('/')[-1]];tx,ty,tz=map(float,mat[9:12])
      lods=[x for x in model.lods if x.resolution==float(np.float32(res))]
      if len(lods)!=1:continue
      verts=np.asarray([(v.x+tx,v.y+ty,v.z+tz) for v in lods[0].vertices],dtype=np.float64)
      for fi,face in enumerate(lods[0].faces):
       inds=face.vertex_indices
       if len(inds)!=3:continue
       facepoly=Polygon(verts[inds][:,[0,2]])
       if facepoly.is_empty or facepoly.area<=1e-12:continue
       for ti,tri in enumerate(tr):
        ids=np.asarray(tri,dtype=int);native=Polygon(xy[ids]);piece=facepoly.intersection(native)
        hit=piece.intersection(hole)
        if hit.is_empty or hit.area<=1e-12:continue
        _,_,tc=consumer.cell_tri_target(r,c,field,tri,p,f)
        if tc is None:continue
        face_coeff=ev.affine_coeff(verts[inds][:,[0,2]],verts[inds][:,1])
        ring=np.asarray(hit.exterior.coords[:-1],dtype=np.float64)
        diff=ring@((face_coeff-tc)[:2])+(face_coeff-tc)[2]
        hole_face_hits.append({'object':name,'face_index':int(fi),'face_indices':[int(i) for i in inds],
          'native_triangle':ti,'overlap_m2':float(hit.area),
          'distance_hole_to_face_projection_boundary_m':float(facepoly.boundary.distance(hit)),
          'face_minus_nominal_field_min_m':float(np.min(diff)),
          'face_minus_nominal_field_max_m':float(np.max(diff))})
    detail[label][kind]={'design_m2':float(design.area),'matched_support_m2':float(design.intersection(matched_u).area),
      'hole_m2':float(hole.area),'hole_outside_any_face_projection_m2':float(outside.area),
      'hole_inside_face_projection_m2':float(hole.intersection(footprint).area),
      'intersecting_faces':touch,'candidate_hole_face_overlaps':hole_face_hits}
  details[cell]=detail
 out={'status':'DIAGNOSTIC_ONLY','scope':'cells with reported physical/visible support-hole area >1e-10 m2; no full verifier rerun',
   'inputs':input_hashes,'candidate_sha256':input_hashes[str(CAND)],'baseline_B_sha256':input_hashes[str(B)],
   'cell_coordinates_rc':{f'{r},{c}':{'world_center_x_m':(c+0.5)*6.0,'world_center_z_m':12282.0-(r+0.5)*6.0,
       'reported_holes_m2':cells[(r,c)],'changed_corners':cell_corners[(r,c)],'compiled_projection_diagnostics':details[(r,c)]}
       for r,c in sorted(cells)},
   'patch_attribution_rule':'only accepted direction entries aligned to mutable_nodes; corner patch IDs are local candidate contributors, not proof that the patch alone caused a footprint deficit',
   'model_boundary_rule':'a deficit outside the union of all compiled face XZ projections is consistent with a projected model boundary; overlap with a face projection means height/matching or another coverage mechanism needs separate interpretation',
   'compiled_objects_in_local_cell_query':len(objects),'compiled_models_and_sha256':model_hashes,
   'limits':'The prior full report includes all support-hole cells in its <50 examples. This script recomputes projected face/matched support only in those cells; patch attribution is vertex-local. No candidate, policy, consumer, or full-run inputs are modified.'}
 OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({'output':str(OUT),'cells':len(cells),'objects':len(objects),'models':len(models),'candidate_sha256':input_hashes[str(CAND)],'report_sha256':input_hashes[str(REPORT)]},indent=2))

if __name__=='__main__':main()
