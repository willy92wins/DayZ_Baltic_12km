import sys, json, hashlib, math
from pathlib import Path
import numpy as np
W=Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev')
sys.path.insert(0,str(W)); sys.path.insert(0,str(W/'tools'/'terrain')); sys.path.insert(0,r'C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts')
from wrp0wzd import read as read_wrp
from odol_reader import ODOL
OUT=Path(__file__).parent
WRP=Path(r'E:\DayZ-Baltic-Build\v30-remaining-exact-dry-support-20261009\package\world\root\dayz_baltic_12km_dev\tb\narva_trial\baltic_trial.wrp')
MODELS=Path(r'E:\DayZ-Baltic-Build\v30-native-terminal-finish-20261009\package\water\temp\baltic_water_v30')
SRC=Path(r'E:\DayZ-Baltic-Build\v30-frozen-water-stitch-20261009\compile\source\baltic_water_v30')
IDs=[16812770,16812771,16812805,16812815]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def v3(v): return [float(v.x),float(v.y),float(v.z)]
def good_num(x): return float(x) if math.isfinite(float(x)) else str(float(x))
def model_one(obj, wrpobj):
 p=ODOL.from_file(str(obj)); mi=p.model_info
 vec=lambda q: v3(q) if q is not None else None
 lout=[]
 for i,l in enumerate(p.lods):
  if l is None: lout.append({'index':i,'error':p.lod_errors.get(i)}); continue
  verts=np.array([v3(x) for x in l.vertices],dtype=float).reshape((-1,3))
  normals=np.array([v3(x) for x in getattr(l,'normals',[])],dtype=float).reshape((-1,3))
  norm_len=np.linalg.norm(normals,axis=1) if len(normals) else np.array([])
  face_n=[]; slopes=[]
  for f in l.faces:
   ix=f.vertex_indices
   if len(ix)<3 or any(x<0 or x>=len(verts) for x in ix): continue
   a,b,c=verts[ix[:3]]; n=np.cross(b-a,c-a); ln=np.linalg.norm(n)
   if ln>0:
    n=n/ln; face_n.append(n.tolist()); slopes.append(math.degrees(math.acos(min(1,abs(float(n[1]))))))
  mats=[]
  for m in l.materials:
   mats.append({'name':m.material_name,'version':m.version,'pixel_shader':m.pixel_shader,'vertex_shader':m.vertex_shader,'main_light':m.main_light,'fog_mode':m.fog_mode,'surface_file':m.surface_file,'render_flags':m.render_flags,'n_render_flags':m.n_render_flags,'stage_textures':[{'texture':x.texture,'filter_type':x.filter_type,'stage_id':x.stage_id,'use_world_env_map':x.use_world_env_map} for x in m.stage_textures]})
  lout.append({'index':i,'resolution':good_num(l.resolution),'vertices':len(verts),'faces':len(l.faces),'normals':len(normals),'bounds_min':verts.min(axis=0).tolist() if len(verts) else None,'bounds_max':verts.max(axis=0).tolist() if len(verts) else None,'lod_bmin':vec(l.b_min),'lod_bmax':vec(l.b_max),'lod_center':vec(l.b_center),'lod_radius':good_num(l.b_radius),'normal_length_min_max_mean':([float(norm_len.min()),float(norm_len.max()),float(norm_len.mean())] if len(norm_len) else None),'face_slope_deg_min_max_mean':([float(np.min(slopes)),float(np.max(slopes)),float(np.mean(slopes))] if slopes else None),'textures':list(l.textures),'sections':[{'face_lower':s.face_lower,'face_upper':s.face_upper,'texture_index':s.texture_index,'special':s.special,'material_index':s.material_index,'mat_name':s.mat_name} for s in l.sections],'materials':mats,'named_properties':list(l.named_properties)})
 model={k:getattr(mi,k,None) for k in ['special','bounding_sphere','geometry_sphere','remarks','and_hints','or_hints','view_density','auto_center','lock_auto_center','can_occlude','can_be_occluded','allow_animation','force_not_alpha','disable_cover','animated','map_type','mass','inv_mass','armor','geometry_simple','geometry_phys','memory','geometry','geometry_fire','geometry_view','geometry_view_pilot','geometry_view_gunner','geometry_view_cargo','roadway','can_blend','property_class','property_damage','property_frequent']}
 for k in ['aiming_center','bbox_min','bbox_max','bbox_min_visual','bbox_max_visual','bounding_center','geometry_center','center_of_mass']:
  model[k]=vec(getattr(mi,k,None))
 matrix=wrpobj['matrix']
 return {'id':wrpobj['id'],'wrp_model':wrpobj['name'],'compiled_path':str(obj),'compiled_bytes':obj.stat().st_size,'compiled_sha256':sha(obj),'signature_prefix':obj.read_bytes()[:8].hex(),'odol_version':p.version,'parse_mode':p.parse_mode,'n_lods':p.n_lods,'resolutions':[good_num(x) for x in p.resolutions],'lod_errors':p.lod_errors,'model_info':model,'lods':lout,'wrp_matrix_3x3_plus_xyz':matrix,'wrp_position_xyz':matrix[9:12]}
wrp=read_wrp(WRP); lookup={o['id']:o for o in wrp['objects']}
records={str(i):model_one(MODELS/(lookup[i]['name'].split('\\')[-1]),lookup[i]) for i in IDs}
assets={}
asset_candidates={'pond_moss_rvmat':Path(r'P:\DZ\water\ponds\data\pond_moss_1.rvmat'),'normalmap':Path(r'P:\DZ\data\data\normalmap1_dxt5.paa'),'roadway_water':Path(r'P:\DZ\surfaces\data\roadway\water_ext.paa')}
for k,p in asset_candidates.items():
 assets[k]={'path':str(p),'exists':p.exists(),'bytes':p.stat().st_size if p.exists() else None,'sha256':sha(p) if p.exists() else None,'text':p.read_text(errors='replace') if p.suffix.lower()=='.rvmat' and p.exists() else None}
sources={}
for i in IDs:
 p=SRC/f'globalvis_{i}.p3d'
 sources[str(i)]={'path':str(p),'exists':p.exists(),'bytes':p.stat().st_size if p.exists() else None,'sha256':sha(p) if p.exists() else None,'prefix_hex':p.read_bytes()[:16].hex() if p.exists() else None,'magic':p.read_bytes()[:4].decode('ascii','replace') if p.exists() else None}
# Compare equivalent build copies by hash only; no new decode.
variants={}
for base in [Path(r'E:\DayZ-Baltic-Build\v30-frozen-water-stitch-20261009\compile\temp\baltic_water_v30'),Path(r'E:\DayZ-Baltic-Build\v30-frozen-water-stitch-20261009\final\water\temp\baltic_water_v30')]:
 variants[str(base)]={str(i):({'exists':(base/f'globalvis_{i}.p3d').exists(),'bytes':(base/f'globalvis_{i}.p3d').stat().st_size if (base/f'globalvis_{i}.p3d').exists() else None,'sha256':sha(base/f'globalvis_{i}.p3d') if (base/f'globalvis_{i}.p3d').exists() else None}) for i in IDs}
report={'inputs':{'wrp':str(WRP),'wrp_sha256':sha(WRP),'compiled_dir':str(MODELS),'source_mlod_dir':str(SRC),'ids':IDs,'method':'Existing wrp0wzd + ODOL reader, same parsers used by prior spatial audit; no game or package writes.'},'objects':records,'assets':assets,'source_mlod':sources,'compiled_copy_variants':variants}
(OUT/'exact-pairs.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'written':str(OUT/'exact-pairs.json'),'wrp_hash':report['inputs']['wrp_sha256'],'objects':{i:{'model':x['wrp_model'],'position':x['wrp_position_xyz'],'hash':x['compiled_sha256'],'parse':x['parse_mode'],'lods':[(l.get('resolution'),l.get('vertices'),l.get('faces'),l.get('textures'),[m.get('name') for m in l.get('materials',[])]) for l in x['lods'] if 'resolution' in l]} for i,x in records.items()},'assets':assets,'source_mlod':sources},indent=2,ensure_ascii=False))
