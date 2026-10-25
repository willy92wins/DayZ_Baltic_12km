import sys,json,math
from pathlib import Path
import numpy as np
W=Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev');sys.path.insert(0,str(W));sys.path.insert(0,r'C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts')
from odol_reader import ODOL
p=Path(__file__).with_name('exact-pairs.json');d=json.loads(p.read_text(encoding='utf-8'))
for key,o in d['objects'].items():
 model=Path(o['compiled_path']); raw=ODOL.from_file(str(model))
 for i,l in enumerate(raw.lods):
  if not l or not l.vertices: continue
  V=np.array([[v.x,v.y,v.z] for v in l.vertices],dtype=float); N=np.array([[v.x,v.y,v.z] for v in l.normals],dtype=float)
  ln=np.linalg.norm(N,axis=1); up=np.abs(N[:,1])
  o['lods'][i]['vertex_y_min_max_mean_std']=[float(V[:,1].min()),float(V[:,1].max()),float(V[:,1].mean()),float(V[:,1].std())]
  o['lods'][i]['normal_xyz_component_min_max']=[[float(N[:,j].min()),float(N[:,j].max())] for j in range(3)]
  o['lods'][i]['normal_mean_xyz']=[float(x) for x in N.mean(axis=0)]
  o['lods'][i]['abs_normal_y_quantiles_0_25_50_75_100']=[float(x) for x in np.quantile(up,[0,.25,.5,.75,1])]
  o['lods'][i]['unique_normals_rounded_4dp']=int(len(np.unique(np.round(N,4),axis=0)))
d['spatial_context']={'ev73_roi_world':'E:\\DayZ-Baltic-Build\\v30-water-pixel-calibration-20261010\\roi-world.json','confirmed_grey_roi_ray_samples':345,'grey_roi_first_P_intersections':345,'grey_roi_first_F_intersections':345,'grey_roi_first_terrain_intersections':345,'interpretation':'Context only: first intersections do not classify draw call, shader, or occlusion. ROI sample counts do not directly prove the two analyzed edges.'}
p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
for k,o in d['objects'].items():
 l=o['lods'][0];print(k, 'Y', l['vertex_y_min_max_mean_std'],'Nxyz',l['normal_xyz_component_min_max'],'Nmean',l['normal_mean_xyz'],'absNyQ',l['abs_normal_y_quantiles_0_25_50_75_100'],'uniqueN',l['unique_normals_rounded_4dp'],'slope',l['face_slope_deg_min_max_mean'])
