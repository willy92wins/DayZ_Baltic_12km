"""Numerical reading of captured pixels, no synthesized or edited image output."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
B=Path(__file__).parent
groups={'baseline':['r1-baseline','r1-reset','r1-restored-final'],'wetfloor_zero':['r1-wetfloorzero','r1-wetfloorzero-repeat'],'normal_zero':['r1-normalzero'],'foam_zero':['r1-foamzero']}
points={'native_dry_residual':(324,116,3),'native_dry_residual_halo':(324,116,10),'pond_neighbour':(347,117,3),'river_visible_shore':(620,300,5),'water_sun_control':(958,458,12),'dry_centre_control':(1480,750,12)}
rows=[];images={}
for group,names in groups.items():
 for name in names:
  files=list((B/'views'/name).glob('*.jpg'));assert len(files)==1
  arr=np.asarray(Image.open(files[0]).convert('RGB'),dtype=float);assert arr.shape==(1080,1920,3),arr.shape
  images[name]=arr
  for label,(x,y,radius) in points.items():
   roi=arr[y-radius:y+radius+1,x-radius:x+radius+1];lum=roi@np.array([.299,.587,.114])
   rows.append(dict(phase=group,capture=name,roi=label,center=[x,y],radius=radius,rgb_mean=roi.mean((0,1)).tolist(),lum_mean=float(lum.mean()),lum_std=float(lum.std())))
differences=[]
for label,(x,y,radius) in points.items():
 rois={name:arr[y-radius:y+radius+1,x-radius:x+radius+1] for name,arr in images.items()}
 normal=np.stack([rois[name] for name in groups['baseline']]);zero=np.stack([rois[name] for name in groups['wetfloor_zero']])
 differences.append(dict(roi=label,mean_abs_change=float(np.abs(zero.mean(0)-normal.mean(0)).mean()),
  mean_abs_same_phase_variation=float(np.abs(normal[2]-normal[0]).mean()),
  change_to_same_phase_ratio=float(np.abs(zero.mean(0)-normal.mean(0)).mean()/max(.01,np.abs(normal[2]-normal[0]).mean()))))
report=dict(status='MEASURED_RENDER_MATERIAL_RESPONSE_NOT_GLOBAL_ACCEPTANCE',samples=rows,differences=differences,
 methods=['Full-resolution 1920x1080, identical camera matrix.','Dry residual centre and pond neighbour use EV10 native projection calibration; halo ROI includes uncertain neighbours.','Only RGB/luminance read; no image transformation or semantic pixel classifier.'],
 limits=['Wave phases and elapsed time differ.','A local response is not proof of zero artefacts across the map.','WetFloor also changes legitimate water/shore appearance.'])
(B/'pixel-measurements.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(differences,indent=2))
