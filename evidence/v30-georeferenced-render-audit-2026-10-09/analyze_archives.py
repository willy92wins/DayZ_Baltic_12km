"""Conditional georeferenced temporal candidates, never a flooding verdict."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter,label,binary_dilation
from trace_native import trace

B=Path(__file__).parent;R=Path('E:/DayZ-Baltic-Build/v30-low-water-components-20261009')
H=Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz')
F=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009/preserved-field.npy')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def temporal(a,control):
 # Four-pixel Gaussian suppresses individual grass blades and JPEG noise.
 smooth=np.stack([gaussian_filter(v.astype(float),sigma=(4,4,0)) for v in a])
 drift=np.median((smooth-smooth[0])[:,control],axis=1)
 residual=smooth-drift[:,None,None,:]
 spread=np.max(np.ptp(residual,axis=0),axis=2)
 return spread,drift

def main():
 calibration=json.loads((B/'calibration.json').read_text());rot=np.array(calibration['camera']['matrix']).reshape(4,3);pos=rot[3];focal=calibration['estimated_focal_px']
 py,px=np.mgrid[450:951:2,250:1701:2];shape=px.shape
 outputs=[];arrays={};inputs=[H,F,B/'calibration.json',B/'trace_native.py',B/'validate_trace.py'];baseline_control=None
 for name,hfile,ffile,folder in [('A2',H,F,'A2-cycle'),('Bstable',R/'translation/terrain.npz',R/'translation/visible-field.npy','Bstable-cycle')]:
  h=np.load(hfile)['heights'];field=np.load(ffile);classes=[];hits=[]
  for f in (540.,focal,580.):
   directions=rot[2]+((px.ravel()-960)/f)[:,None]*rot[0]-((py.ravel()-540)/f)[:,None]*rot[1]
   directions/=np.linalg.norm(directions,axis=1)[:,None]
   xyz,kind,distance=trace(h,field,pos,directions,sea=.85)
   classes.append(kind.reshape(shape));hits.append(xyz.reshape((*shape,3)))
  kind=classes[1];xyz=hits[1]
  # This is sensitivity over 540..580 focal, not a statistical uncertainty bound.
  stable=np.all(np.array(classes)==1,axis=0)&(xyz[:,:,1]>.85+.3)
  wet=np.any(np.isin(np.array(classes),[2,3]),axis=0)
  stable&=~binary_dilation(wet,iterations=4)
  stable&=~((abs(px-960)<8)&(abs(py-540)<8))
  # This lowland scene has almost no terrain above 3 m. Use the predefined
  # foreground band, high enough above maximum sea and distant from water.
  control=stable&(py>=850)&(xyz[:,:,1]>=1.799)&~binary_dilation(wet,iterations=12)
  assert control.sum()>1000,dict(control=int(control.sum()))
  if baseline_control is None:baseline_control=control.copy()
  else:
   assert np.all(control[baseline_control]),'Baseline reference pixels must also be valid in B'
   control=baseline_control.copy()
  paths=sorted((R/'views'/folder).glob('*.jpg'));assert len(paths)==8
  full=np.stack([np.array(Image.open(p).convert('RGB')) for p in paths]);assert full.shape==(8,1080,1920,3)
  full_control=np.zeros(full.shape[1:3],bool);full_control[py,px]=control
  spread,drift=temporal(full,full_control);score=spread[py,px]
  threshold=max(2.,float(np.quantile(score[control],.999)))
  suspect=stable&(score>threshold)
  groups,n=label(suspect);components=[]
  for i in range(1,n+1):
   mask=groups==i;count=int(mask.sum())
   if count<8:continue
   q=xyz[mask];coords=np.c_[px[mask],py[mask]]
   components.append(dict(grid_pixels=count,estimated_full_pixels=count*4,screen_bbox=[*coords.min(axis=0).tolist(),*coords.max(axis=0).tolist()],world_center=np.median(q,axis=0).tolist(),world_bbox_xz=[float(q[:,0].min()),float(q[:,2].min()),float(q[:,0].max()),float(q[:,2].max())],max_rgb_range=float(score[mask].max()),mean_rgb_range=float(score[mask].mean())))
  components.sort(key=lambda row:row['grid_pixels'],reverse=True)
  results=dict(name=name,status='CONDITIONAL_TEMPORAL_CANDIDATES_NOT_WATER_PROOF',frames=len(paths),sampled_pixels=px.size,stable_dry_samples=int(stable.sum()),control_samples=int(control.sum()),control_p999_rgb_range=float(np.quantile(score[control],.999)),threshold_rgb_range=threshold,suspect_samples=int(suspect.sum()),components=components,global_drift=drift.tolist(),classes={str(k):int((kind==k).sum()) for k in range(4)})
  outputs.append(results);arrays[name+'_xyz']=xyz;arrays[name+'_kind']=kind;arrays[name+'_stable']=stable;arrays[name+'_score']=score;arrays[name+'_wet']=wet
  # Diagnostic data heatmap, no source-photo edits.
  heat=np.zeros((*shape,3),np.uint8);heat[stable]=[35,65,35];heat[wet]=[35,65,150];heat[suspect]=[255,100,20];Image.fromarray(heat).save(B/(name+'-classified-temporal.png'))
  inputs.extend([hfile,ffile,*paths]);print(json.dumps({k:v for k,v in results.items() if k not in ['components','global_drift']}),flush=True)
 # Equal reference pixels and one common threshold are required for the comparison.
 common_threshold=max(row['threshold_rgb_range'] for row in outputs)
 for row in outputs:
  name=row['name'];score=arrays[name+'_score'];stable=arrays[name+'_stable'];xyz=arrays[name+'_xyz'];wet=arrays[name+'_wet']
  suspect=stable&(score>common_threshold);groups,n=label(suspect);components=[]
  for i in range(1,n+1):
   mask=groups==i;count=int(mask.sum())
   if count<8:continue
   q=xyz[mask];coords=np.c_[px[mask],py[mask]]
   components.append(dict(grid_pixels=count,estimated_full_pixels=count*4,screen_bbox=[*coords.min(axis=0).tolist(),*coords.max(axis=0).tolist()],world_center=np.median(q,axis=0).tolist(),world_bbox_xz=[float(q[:,0].min()),float(q[:,2].min()),float(q[:,0].max()),float(q[:,2].max())],max_rgb_range=float(score[mask].max()),mean_rgb_range=float(score[mask].mean())))
  row.update(threshold_rgb_range=common_threshold,suspect_samples=int(suspect.sum()),components=sorted(components,key=lambda v:v['grid_pixels'],reverse=True))
  heat=np.zeros((*shape,3),np.uint8);heat[stable]=[35,65,35];heat[wet]=[35,65,150];heat[suspect]=[255,100,20];Image.fromarray(heat).save(B/(name+'-classified-temporal.png'))
 # Independent positives/negatives on luminance changes, not scene classification.
 reference=np.full((6,64,64,3),100,np.uint8);control=np.ones((64,64),bool);control[20:44,20:44]=False
 spread,_=temporal(reference,control);assert spread.max()==0
 global_only=reference.copy()
 for i in range(6):global_only[i]+=i*3
 spread,_=temporal(global_only,control);assert spread.max()<1e-9
 positive=reference.copy();positive[3:,24:40,24:40]+=25;spread,_=temporal(positive,control);assert spread[32,32]>20 and np.quantile(spread[control],.999)<6
 np.savez_compressed(B/'temporal-maps.npz',px=px,py=py,**arrays)
 report=dict(status='CONDITIONAL_ARCHIVE_ANALYSIS',runs=outputs,common_reference_pixels=int(baseline_control.sum()),common_threshold_rgb_range=common_threshold,controls=['constant_sequence_zero','global_brightness_removed','localized_change_detected','identical_reference_pixels_and_threshold_A_B'],inputs={str(p):sha(p) for p in dict.fromkeys(inputs)},limits=['Projection estimated from a different run; native screen-point confirmation remains required.','540..580 focal sensitivity is not a calibrated confidence interval.','Grass, shadows and material changes can trigger candidates; RGB variation is not proof of water.','These two fixed views do not constitute whole-map coverage or a repaired map.','Archived frame times have not been synchronized to native sea-level samples.'])
 (B/'temporal-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
