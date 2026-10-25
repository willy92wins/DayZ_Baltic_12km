from __future__ import annotations
import hashlib, json, math, sys, time
from pathlib import Path
import numpy as np

G=Path(r'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010')
W=Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
ROOT=Path(r'E:\DayZ-Baltic-Build')
AUDIT=G/'unknown-p-audit'/'unknown-p-audit.json'
TERRAIN=Path(r'E:\DayZ-Baltic-Build\v30-v11\terrain_v30\terrain_v30.npz')
CORRIDORS=Path(r'E:\DayZ-Baltic-Build\v30-v11\06-evidence\corridors.geojson')
CIVIL=G/'global-operator-prototype'/'real-sector-preflight'/'civil-run-01.json'
MASK=G/'global-operator-prototype'/'real-sector-preflight'/'water-run-01'/'water-support-mask.npz'
MASK_META=MASK.with_suffix('.json')
STAGE=G/'build-focal'/'stage.json'
DEPLOY=G/'build-focal'/'deploy.json'
OPRW=G/'build-focal'/'op_rw_verification.json'
INDEX=G/'ev93-face-index'/'runs'/'20261010T092417Z-63d4cec3'/'manifest.json'
P3D=Path(r'P:\DZ\structures\roads\bridges\bridge_metal_25.p3d')
ODOL_READER=Path(r'C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts\odol_reader.py')
BUILDER=W/'tools'/'water'/'build_water_pieces_v30.py'
COMMON=W/'tools'/'terrain'/'v30_common.py'
CIVIL_SOURCE=G/'global-operator-prototype'/'real-sector-preflight'/'civil_inventory.py'
EXPECTED={
 str(AUDIT):'a51f09fabc575866d5b650b572cf22b83c071c1b653a9201d0fc93c146c96c38',
 str(CORRIDORS):'28866a8cf6ff57f2f825228046164ef939bc22bca9948eb96fe2463da46af343',
 str(STAGE):'cc394869cf45f60315eea5b13a99b2f79d80135bee5ee32879b3900ecaa86610',
 str(INDEX):'c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c',
 str(P3D):'baf79ddd19e08cdcdbec99b15043a319d6b958a1b7884082c2ae069cf3f3cee2',
}
WATER_PBO=Path(r'P:\Mods\@DayZ_Baltic_EV94_FocalBankPreviewV1\Addons\baltic_water_v30.pbo')
WATER_PBO_SHA='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
SEA_CUT=0.80
WET_CLASSES=(2,3,5,6,7)
CELL=6.0; Z0=12282.0

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
 return h.hexdigest()
def pins(paths): return {str(p):sha(p) for p in paths}
def cell_bbox(r,c): return [c*CELL,Z0-(r+1)*CELL,(c+1)*CELL,Z0-r*CELL]
def bbox_gap(a,b):
 dx=max(a[0]-b[2],b[0]-a[2],0.0); dz=max(a[1]-b[3],b[1]-a[3],0.0)
 return math.hypot(dx,dz),dx,dz

def run():
 t0=time.perf_counter()
 paths=[AUDIT,TERRAIN,CORRIDORS,CIVIL,MASK,MASK_META,STAGE,DEPLOY,OPRW,INDEX,P3D,ODOL_READER,BUILDER,COMMON,CIVIL_SOURCE,WATER_PBO]
 start=pins(paths)
 for p,want in EXPECTED.items():
  got=sha(p)
  if got!=want: raise RuntimeError(f'input pin mismatch {p}: {got}')
 if sha(WATER_PBO)!=WATER_PBO_SHA: raise RuntimeError('EV94 water PBO pin mismatch')
 audit=json.load(open(AUDIT,encoding='utf-8')); civil_doc=json.load(open(CIVIL,encoding='utf-8')); civil=civil_doc['bridge']
 stage=json.load(open(STAGE,encoding='utf-8')); deploy=json.load(open(DEPLOY,encoding='utf-8')); oprw=json.load(open(OPRW,encoding='utf-8')); index=json.load(open(INDEX,encoding='utf-8'))
 if stage['status']!='STAGED_EV94_HEIGHTS_ONLY' or stage['objects']!=18033 or not stage['objects_and_materials_exact']:
  raise RuntimeError('stage WRP identity not exact EV94')
 if stage['source_wrp_sha256']!=index['base_identity']['wrp_source_sha256']:
  raise RuntimeError('civil/index source WRP differs from EV94 source WRP')
 if deploy['files'].get('baltic_water_v30.pbo')!=WATER_PBO_SHA or not deploy['water_pbo_exact'] or not oprw['water_pbo_exact_to_baseline']:
  raise RuntimeError('EV94 water PBO identity not exact')
 if civil['wrp_object_count']!=9 or len(civil['objects'])!=9: raise RuntimeError('civil report not nine object records')
 # The terrain_v30 class raster is used only as a source-metadata diagnostic.
 sys.path.insert(0,str(ODOL_READER.parent))
 from odol_reader import ODOL as ODOLModel
 model=ODOLModel.from_file(str(P3D)); vv=[]
 for lod in model.lods:
  if lod.faces: vv.extend([[v.x,v.y,v.z] for v in lod.vertices])
 local_vertices=np.asarray(vv,dtype=np.float64)
 with np.load(TERRAIN) as t:
  cls=t['cls']; level=t['level']; water=t['water']; beach=t['beach']; narva=t['narva']; reserve=t['reserve']; platform=t['platform']
 # Compute the exact builder cell-plane array from its pinned current helper, once.
 sys.path.insert(0,str(COMMON.parent))
 from v30_common import cell_planes, POND_CLASSES
 if tuple(POND_CLASSES)!=WET_CLASSES: raise RuntimeError('class rule changed')
 planes=cell_planes(cls,level,band=0.025,sea_cut=SEA_CUT)
 mask=np.load(MASK); mm=json.load(open(MASK_META,encoding='utf-8'))
 mr0,_,mc0,_=mm['window_vertex_rc_half_open']; bridge_cells={tuple(x) for x in civil['native_cells_rc_sorted']}
 features={f['properties']['river']:f for f in json.load(open(CORRIDORS,encoding='utf-8'))['features'] if f['properties'].get('river') in ('Narva_23','Luga_0')}
 results={}
 for river in ('Narva_23','Luga_0'):
  cells=audit['results'][river]['physical']['cells']; cell_rows=[]; classes_area={}; eligible_corner_area=0.; noeligible_area=0.; plane_area=0.; mask_area={}; flag_area={k:0. for k in ('water','beach','narva','reserve','platform')}; corner_samples=[]
  for raw in cells.values():
   r,c=int(raw['row']),int(raw['col']); area=sum(float(x['unknown_area_m2']) for x in raw['triangles'].values())
   if area<=0: continue
   corners=[(r,c),(r,c+1),(r+1,c),(r+1,c+1)]
   cc=np.asarray([cls[y,x] for y,x in corners]); lv=np.asarray([level[y,x] for y,x in corners],dtype=np.float64)
   wet=np.isin(cc,WET_CLASSES)&(np.nan_to_num(lv,nan=-1.0)>SEA_CUT)
   finite_plane=bool(np.isfinite(planes[r,c]))
   if wet.any(): eligible_corner_area+=area
   else: noeligible_area+=area
   if finite_plane: plane_area+=area
   for k,v in zip(map(int,cc),[0.25]*4): classes_area[str(k)]=classes_area.get(str(k),0.0)+area*v
   for flag,arr in [('water',water),('beach',beach),('narva',narva),('reserve',reserve),('platform',platform)]:
    if all(bool(arr[y,x]) for y,x in corners): flag_area[flag]+=area
   if river=='Narva_23' and mr0<=r<mr0+mask['cell_reasons'].shape[0] and mc0<=c<mc0+mask['cell_reasons'].shape[1]:
    rb=int(mask['cell_reasons'][r-mr0,c-mc0]); key=str(rb); mask_area[key]=mask_area.get(key,0)+area
   else: mask_area['outside_mask_window']=mask_area.get('outside_mask_window',0)+area
   cell_rows.append({'rc':[r,c],'xy_bbox_m':cell_bbox(r,c),'unknown_corridor_area_m2':area,'corner_classes_NW_NE_SW_SE':cc.astype(int).tolist(),'corner_levels_m_NW_NE_SW_SE':[float(x) for x in lv],'wet_corner_count_by_builder_cutoff':int(wet.sum()),'cell_planes_finite_by_v30_common':finite_plane,'flags_all4corners_true':{k:bool(all(arr[y,x] for y,x in corners)) for k,arr in [('water',water),('beach',beach),('narva',narva),('reserve',reserve),('platform',platform)]},'water_support_reason_bits':None if river=='Luga_0' or not(mr0<=r<mr0+mask['cell_reasons'].shape[0] and mc0<=c<mc0+mask['cell_reasons'].shape[1]) else int(mask['cell_reasons'][r-mr0,c-mc0])})
  allcells={tuple(x['rc']) for x in cell_rows}
  xz=[x['xy_bbox_m'] for x in cell_rows]; region=[min(x[0] for x in xz),min(x[1] for x in xz),max(x[2] for x in xz),max(x[3] for x in xz)]
  overlap=sorted(allcells&bridge_cells) if river=='Narva_23' else []
  features_result=[]
  for obj in civil['objects']:
   matrix=np.asarray(obj['wrp_matrix12'],dtype=np.float64); pos=matrix[9:12]
   # Vertex envelope computed from every face-bearing LOD, as a conservative AABB.
   world=pos[None,:]+local_vertices@matrix[:9].reshape(3,3); xzv=world[:,(0,2)]
   bb=[float(xzv[:,0].min()),float(xzv[:,1].min()),float(xzv[:,0].max()),float(xzv[:,1].max())]
   gap,dx,dz=bbox_gap(region,bb)
   features_result.append({'object_id':obj['wrp_object_id'],'name':obj['wrp_name'],'world_xz_aabb_all_facebearing_lod_vertices_m':bb,'unknown_cell_envelope_aabb_disjoint':not (region[0]<=bb[2] and bb[0]<=region[2] and region[1]<=bb[3] and bb[1]<=region[3]),'aabb_gap_m':gap,'gap_x_m':dx,'gap_z_m':dz})
  results[river]={'corridor_feature_properties':features[river]['properties'],'unknown_area_m2':sum(x['unknown_corridor_area_m2'] for x in cell_rows),'unknown_cell_count':len(cell_rows),'unknown_cell_envelope_xz_m':region,'area_weighted_corner_class_fraction':{k:v/sum(x['unknown_corridor_area_m2'] for x in cell_rows) for k,v in classes_area.items()},'corner_level_range_m':[min(q for x in cell_rows for q in x['corner_levels_m_NW_NE_SW_SE']),max(q for x in cell_rows for q in x['corner_levels_m_NW_NE_SW_SE'])],'area_with_any_builder_eligible_wet_corner_m2':eligible_corner_area,'area_with_zero_builder_eligible_wet_corners_m2':noeligible_area,'area_in_cells_where_exact_v30_common_cell_planes_is_finite_m2':plane_area,'area_by_all4_vertex_flags_m2':flag_area,'area_by_water_support_reason_m2':mask_area,'cells':cell_rows,'intersection_with_civil_projected_bridge_cells_rc':overlap,'bridge_objects':features_result,'closest_bridge_aabb_gap_m':min(x['aabb_gap_m'] for x in features_result)}
  if river=='Narva_23' and (eligible_corner_area!=0 or plane_area!=0):
   raise AssertionError('Narva expected source-metadata checks changed; inspect instead of auto-classifying')
 # Hash all inputs again to detect concurrent drift.
 end=pins(paths)
 if start!=end: raise RuntimeError('readset changed during context pass')
 report={'schema':'ev94.unknown-p-corridor-context.v1','status':'COMPLETE_CONTEXT_ONLY','identity':{'stage_objects':stage['objects'],'stage_objects_and_materials_exact':stage['objects_and_materials_exact'],'index_water_objects':index['object_count'],'index_wrp_source_sha256':index['base_identity']['wrp_source_sha256'],'stage_wrp_source_sha256':stage['source_wrp_sha256'],'water_pbo_sha256':sha(WATER_PBO),'water_pbo_exact':bool(deploy['water_pbo_exact'] and oprw['water_pbo_exact_to_baseline']),'class_npz_sha256':sha(TERRAIN)},'compiled_face_audit':{'path':str(AUDIT),'sha256':sha(AUDIT),'P_unknown_m2':audit['classification']['P_unknown_total_m2'],'physical_face_m2':audit['classification']['physical_compiled_face_union_m2'],'visible_face_m2':audit['classification']['visible_compiled_face_union_m2'],'no_face_physical_m2':audit['classification']['physical_no_face_gap_m2'],'no_face_visible_m2':audit['classification']['visible_no_face_gap_m2']},'class_rule_source':{'build_water_pieces_v30.py':sha(BUILDER),'v30_common.py':sha(COMMON),'rule':'POND_CLASSES=(2,3,5,6,7), cell plane finite iff any corner class is in set and level>0.80m; <=0.80m is excluded from pond pieces/assigned to engine sea per build_water_pieces source text. The class NPZ is a source-metadata diagnostic, not a byte-proven derivation input of deployed PBO.'},'water_support_mask':{'path':str(MASK),'sha256':sha(MASK),'json_path':str(MASK_META),'json_sha256':sha(MASK_META),'window_vertex_rc_half_open':mm['window_vertex_rc_half_open'],'scope':'Narva sector only; it is a protection/contact mask and explicitly excludes P9 reconstruction and does not declare runtime water.'},'civil_inventory':{'path':str(CIVIL),'sha256':sha(CIVIL),'source_path':str(CIVIL_SOURCE),'source_sha256':sha(CIVIL_SOURCE),'object_count':civil['wrp_object_count'],'coverage_policy':civil['coverage_policy'],'limitations':civil['limitations'],'bridge_model_sha256':sha(P3D),'odol_reader_sha256':sha(ODOL_READER),'model_all_facebearing_vertex_count':len(local_vertices),'model_local_bounds_xyz_m':[local_vertices.min(axis=0).tolist(),local_vertices.max(axis=0).tolist()]},'results':results,'readset_start':start,'readset_end':end,'readset_unchanged':start==end,'elapsed_seconds':time.perf_counter()-t0,'interpretation_limits':['P remains NaN/unknown; metadata class and engine sea fallback do not replace P or prove runtime surface/depth.','A zero compiled-face area is a geometric coverage result only inside these corridor∩unknown-P patches.','Bridge P3D bounds are all face-bearing LOD vertex AABBs; disjointness excludes these nine objects, not arbitrary runtime water suppression.','Civil bridge cells are sector-scoped; for Luga the full transformed bridge AABBs, not the cell list, establish separation.','The 18,024 indexed water objects are the exact name-selected water set; the nine civil bridge WRP records are separate object classes, not a missing water-object count.']}
 out=G/'unknown-p-audit'/'corridor-domain-context.json'
 out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({'status':report['status'],'out':str(out),'sha256':sha(out),'elapsed_s':report['elapsed_seconds'],'results':{k:{'unknown_area_m2':v['unknown_area_m2'],'class_fractions':v['area_weighted_corner_class_fraction'],'no_wet_corner_area':v['area_with_zero_builder_eligible_wet_corners_m2'],'plane_finite_area':v['area_in_cells_where_exact_v30_common_cell_planes_is_finite_m2'],'flags':v['area_by_all4_vertex_flags_m2'],'mask':v['area_by_water_support_reason_m2'],'bridge_overlap_cells':v['intersection_with_civil_projected_bridge_cells_rc'],'nearest_bridge_gap_m':v['closest_bridge_aabb_gap_m']} for k,v in results.items()}},indent=2))

if __name__=='__main__': run()




