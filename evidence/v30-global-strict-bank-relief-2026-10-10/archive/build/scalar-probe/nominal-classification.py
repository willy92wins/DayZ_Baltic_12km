from __future__ import annotations
import hashlib, importlib.util, json, math, sys
from pathlib import Path
import numpy as np

ROOT=Path(r'E:/DayZ-Baltic-Build')
BUILD=ROOT/'v30-global-strict-bank-relief-20261010/build'
PROBE=BUILD/'scalar-probe'
WORK=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
WRP=BUILD/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
BOUNDS=ROOT/'v30-low-water-components-20261009/compiled-instance-bounds.json'
MODELS=ROOT/'v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30'
HNPZ=BUILD/'candidate/terrain.npz'
BNPZ=ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
PFILE=BUILD/'candidate/plane.npy'
FFILE=BUILD/'candidate/visible-field.npy'
REF=PROBE/'reference.json'; SERIES=PROBE/'series-review.json'
DEPLOY=BUILD/'deploy.json'
DEPLOYED_WORLD=Path(r'P:/Mods/@DayZ_Baltic_StrictBankPreviewV1/Addons/narva_trial.pbo')
DEPLOYED_WATER=Path(r'P:/Mods/@DayZ_Baltic_StrictBankPreviewV1/Addons/baltic_water_v30.pbo')
OUT=PROBE/'nominal-classification.json'
CELL=6.0; Z0=12282.0; N=2048

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()

def loadmod(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def point_tri(px,pz,xy,tol=1e-9):
 a,b,c=np.asarray(xy,dtype=np.float64)
 v0=b-a;v1=c-a;v2=np.asarray([px,pz])-a
 den=v0[0]*v1[1]-v1[0]*v0[1]
 if abs(den)<1e-14:return None
 u=(v2[0]*v1[1]-v1[0]*v2[1])/den
 v=(v0[0]*v2[1]-v0[1]*v2[0])/den
 if u>=-tol and v>=-tol and u+v<=1+tol:return (1-u-v,u,v)
 return None

def corner_pf(r,c,p,f):
 pv=[];fv=[]
 # Four cells incident to this grid vertex; P is one scalar per cell.
 for rr,cc in ((r,c),(r,c-1),(r-1,c),(r-1,c-1)):
  if 0<=rr<p.shape[0] and 0<=cc<p.shape[1] and np.isfinite(p[rr,cc]):pv.append(float(p[rr,cc]))
 # F corner channels NW, NE, SW, SE for cells at the vertex.
 for rr,cc,ch in ((r,c,0),(r,c-1,1),(r-1,c,2),(r-1,c-1,3)):
  if 0<=rr<f.shape[0] and 0<=cc<f.shape[1] and np.isfinite(f[rr,cc,ch]):fv.append(float(f[rr,cc,ch]))
 return pv,fv

def model_hits(point,objects,bounds_by_id,models):
 x,z=float(point['x']),float(point['z']);candidates=[]
 for o in objects:
  bb=bounds_by_id.get(int(o['id']))
  if bb is None:continue
  x0,z0,x1,z1=bb
  if x0-1e-6<=x<=x1+1e-6 and z0-1e-6<=z<=z1+1e-6:candidates.append((o,bb))
 hits={'physical':[],'visible':[]}
 for o,bb in candidates:
  name=o['name'].replace('\\','/').split('/')[-1];model=models[name]
  m=np.asarray(o['matrix'],dtype=np.float64);rot=m[:9].reshape(3,3)
  if not np.array_equal(rot,np.eye(3)):raise AssertionError(f'non-identity water rotation object={o["id"]}')
  tx,ty,tz=map(float,m[9:12])
  for kind,res in (('physical',3e15),('visible',1.0)):
   lods=[l for l in model.lods if l.resolution==float(np.float32(res))]
   if len(lods)!=1:raise AssertionError(f'{kind} LOD absent/nonunique {name}: {[l.resolution for l in model.lods]}')
   lod=lods[0]
   verts=np.asarray([[v.x+tx,v.y+ty,v.z+tz] for v in lod.vertices],dtype=np.float64)
   for fi,face in enumerate(lod.faces):
    inds=list(face.vertex_indices)
    if len(inds)!=3:raise AssertionError(f'non-triangle {name}:{fi}')
    q=verts[inds];bary=point_tri(x,z,q[:,[0,2]])
    if bary is None:continue
    interp=float(np.asarray(bary)@q[:,1])
    # Engine water model returns the first vertex's model-space y, transformed;
    # identity rotations make this the constant roadway plane of this face.
    engine_level=float(ty+lod.vertices[inds[0]].y)
    hits[kind].append({'object_id':int(o['id']),'model':name,'face_index':int(fi),'face_vertex_indices':inds,
      'level_at_xy_m':interp,'engine_face_level_m':engine_level,
      'object_position_y_m':ty,'face_first_local_y_m':float(lod.vertices[inds[0]].y),
      'barycentric':list(map(float,bary)),'bbox':list(map(float,bb))})
 return candidates,hits

def main():
 ref=json.loads(REF.read_text(encoding='utf-8'));series=json.loads(SERIES.read_text(encoding='utf-8'))
 assert series['status']=='COMPLETE_TEMPORAL_DIAGNOSTIC'
 byid={int(x['id']):x for x in series['points']}
 assert len(ref['points'])==178 and len(byid)==178
 inputs=[Path(__file__),REF,SERIES,PROBE/'snapshot.log',DEPLOY,DEPLOYED_WORLD,DEPLOYED_WATER,HNPZ,BNPZ,PFILE,FFILE,WRP,BOUNDS]
 hashes={str(p):sha(p) for p in inputs}
 deploy=json.loads(DEPLOY.read_text(encoding='utf-8'))
 if hashes[str(DEPLOYED_WORLD)]!=ref['pbo']['narva_trial.pbo'] or hashes[str(DEPLOYED_WATER)]!=ref['pbo']['baltic_water_v30.pbo']:
  raise AssertionError('deployed PBO files do not match the scalar-probe reference')
 if deploy.get('files')!=ref['pbo']:
  raise AssertionError('deploy manifest PBO identities do not match scalar-probe reference')
 h=np.load(HNPZ)['heights'];b=np.load(BNPZ)['heights'];p=np.load(PFILE);f=np.load(FFILE)
 assert h.shape==b.shape==(N,N) and p.shape==f.shape[:2]==(N-1,N-1) and f.shape[2]==4
 sys.path.insert(0,str(WORK/'tools/terrain'));import wrp0wzd
 sys.path.insert(0,str(Path(r'C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts')))
 from odol_reader import ODOL
 world=wrp0wzd.read(WRP)
 water=[o for o in world['objects'] if 'baltic_water_v30' in o['name'].replace('\\','/').lower()]
 assert len(water)==18024
 inv=json.loads(BOUNDS.read_text(encoding='utf-8'))
 assert inv.get('water_sha256')=='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
 bounds={int(o['id']):o['bounds'] for o in inv['objects']};assert len(bounds)==18024
 positives_H={q['id'] for q in series['points'][:162] if q['depth_H_positive_over_2cm_samples']>0}
 positives_B={q['id'] for q in series['points'][:162] if q['depth_B_query_positive_over_2cm_samples']>0}
 assert len(positives_H)==22 and len(positives_B)==12
 selected=sorted(positives_H|positives_B)
 point_byid={int(q['id']):q for q in ref['points']}
 near=[]
 for pid in selected:
  pt=point_byid[pid];x,z=float(pt['x']),float(pt['z'])
  for o in water:
   bb=bounds[int(o['id'])];x0,z0,x1,z1=bb
   if x0-1e-6<=x<=x1+1e-6 and z0-1e-6<=z<=z1+1e-6:near.append(o['name'].replace('\\','/').split('/')[-1])
 unique=sorted(set(near));models={}
 for name in unique:
  path=MODELS/name
  expected=inv.get('models',{}).get(name,{}).get('sha256')
  if not expected or sha(path)!=expected:raise AssertionError(f'compiled ODOL hash mismatch {name}')
  models[name]=ODOL.from_file(str(path))
 rows=[]
 for pid in selected:
  q=point_byid[pid];s=byid[pid];r,c=int(q['row']),int(q['col']);x,z=float(q['x']),float(q['z'])
  h_grid=float(h[r,c]);b_grid=float(b[r,c])
  if abs(h_grid-float(q['H']))>1e-5 or abs(b_grid-float(q['B']))>1e-5:
   raise AssertionError(f'reference height does not match pinned terrain arrays at point {pid}')
  pv,fv=corner_pf(r,c,p,f);hmarginP=float(h[r,c]-max(pv)) if pv else None;bmarginP=float(b[r,c]-max(pv)) if pv else None
  hmarginF=float(h[r,c]-max(fv)) if fv else None;bmarginF=float(b[r,c]-max(fv)) if fv else None
  candidates,hit=model_hits(q,water,bounds,models)
  ph=hit['physical'];vh=hit['visible']
  plev=max((z0['engine_face_level_m'] for z0 in ph),default=None)
  vlev=max((z0['level_at_xy_m'] for z0 in vh),default=None)
  Hpos=bool(s['depth_H_positive_over_2cm_samples']);Bpos=bool(s['depth_B_query_positive_over_2cm_samples'])
  rows.append({'id':pid,'row':r,'col':c,'x_m':x,'z_m':z,'H_m':float(q['H']),'H_grid_m':h_grid,'B_m':float(q['B']),'B_grid_m':b_grid,
   'sea_samples':s['sea_samples'],'pond_samples':s['pond_samples'],'nominal_min_max_m':s['nominal_min_max'],
   'fake_above_nominal_min_max_m':s['fake_above_nominal_min_max'],'fake_above_ground_max_m':s['fake_above_ground_max'],
   'depth_H_min_max_m':s['depth_H_min_max'],'depth_B_query_min_max_m':s['depth_at_old_B_query_min_max'],
   'positive_H_over_2cm':Hpos,'positive_B_query_over_2cm':Bpos,
   'incident_P_values_m':pv,'incident_F_values_m':fv,'H_minus_maxP_m':hmarginP,'B_minus_maxP_m':bmarginP,
   'H_minus_maxF_m':hmarginF,'B_minus_maxF_m':bmarginF,
   'roadway_physical_face_contains_xy':bool(ph),'physical_face_count_at_xy':len(ph),'top_physical_engine_level_m':plev,
   'visual_LOD_face_contains_xy':bool(vh),'visible_face_count_at_xy':len(vh),'top_visible_surface_y_m':vlev,
   'candidate_water_objects_bbox_contains_xy':len(candidates),
   'candidate_models_bbox_contains_xy':sorted({o['name'].replace('\\','/').split('/')[-1] for o,_ in candidates}),
   'physical_face_hits':ph,'visible_face_hits':vh})
 out={'status':'COMPLETE_READ_ONLY_POINT_CLASSIFICATION','scope':'22 H-positive and 12 B-query-positive points among 162 changed probes (union of IDs); exact source-side ODOL LOD point-face tests, no engine/build; not a visual diagnosis.',
  'inputs':hashes,'pbo':ref['pbo'],'source_wrp_sha256':sha(WRP),'source_wrp_objects':len(world['objects']),'water_objects':len(water),
  'bounds_inventory_world_sha256':inv.get('world_sha256'),'bounds_inventory_water_sha256':inv.get('water_sha256'),
  'deployed_compiled_wrp_payload_sha256':deploy.get('compiled_wrp_sha256'),
  'compiled_ODOL_models_sha256':{name:sha(MODELS/name) for name in unique},
  'terrain_candidate_sha256':sha(HNPZ),'B_sha256':sha(BNPZ),'P_sha256':sha(PFILE),'F_sha256':sha(FFILE),
  'positive_H_ids':sorted(positives_H),'positive_B_query_ids':sorted(positives_B),
  'H_positive_no_B_query_ids':sorted(positives_H-positives_B),'B_query_positive_no_H_ids':sorted(positives_B-positives_H),
  'unique_ODOL_models_loaded':len(unique),'rows':rows,
  'interpretation_limits':['P is a scalar plane per cell; F is per-cell-corner NW/NE/SW/SE data. Reported margins are conservative maxima over up to four incident supports, not a single globally continuous surface.','The model-surface hit test uses B staged 0WZD source transforms and hash-verified compiled ODOL roadway/visible LOD geometry; the deployed OPRW transforms were not read back from the engine in this task.','A point hit proves projected face coverage at that coordinate, not a rendered pixel or material identity; bbox-only object matches are explicitly distinguished from face hits.','The temporal depth metric is GetWaterDepth at H+0.01 or B+0.01 and correlates with fake surface; the B query is a height discriminator in the H world, not a second B-world run. No wave maximum is inferred.']}
 OUT.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':out['status'],'positive_H_ids':out['positive_H_ids'],'positive_B_query_ids':out['positive_B_query_ids'],
  'H_no_B':out['H_positive_no_B_query_ids'],'B_no_H':out['B_query_positive_no_H_ids'],
  'roadway_face_hits_H_positive':sum(r['positive_H_over_2cm'] and r['roadway_physical_face_contains_xy'] for r in rows),
  'visible_face_hits_H_positive':sum(r['positive_H_over_2cm'] and r['visual_LOD_face_contains_xy'] for r in rows),
  'roadway_face_hits_B_positive':sum(r['positive_B_query_over_2cm'] and r['roadway_physical_face_contains_xy'] for r in rows),
  'visible_face_hits_B_positive':sum(r['positive_B_query_over_2cm'] and r['visual_LOD_face_contains_xy'] for r in rows),
  'loaded_models':len(unique),'output_sha256':sha(OUT)},indent=2))
if __name__=='__main__':main()
