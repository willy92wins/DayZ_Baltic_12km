from pathlib import Path
import sys,json,hashlib,time
import numpy as np
from PIL import Image,ImageDraw
from scipy.optimize import minimize_scalar
B=Path(__file__).parent;R=Path('E:/DayZ-Baltic-Build/v30-native-material-binding-20261009')
sys.path.insert(0,'E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
from audit_frozen_visual import clip,UNIT
SOURCE=Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz')
PFILE=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy')
FFILE=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009/preserved-field.npy')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 rt=json.loads((R/'runtime.json').read_text());camera=rt['camera']['camera'];matrix=np.array(camera['matrix']).reshape(4,3);pos=matrix[3];rotation=matrix[:3]
 frame=Path(next(r['fullres_path'] for r in rt['captures'] if r['phase']=='moss-marker'));a=np.array(Image.open(frame).convert('RGB')).astype(int);assert a.shape==(1080,1920,3)
 magenta=(a[:,:,0]>a[:,:,1]+65)&(a[:,:,2]>a[:,:,1]+65)&(a[:,:,0]>120)&(a[:,:,2]>120);assert magenta.sum()==16864
 h=np.load(SOURCE)['heights'].astype(float);p=np.load(PFILE);f=np.load(FFILE)
 # Fixed world window includes the six-cohort target and surrounding independent ponds.
 polys=[]
 for r in range(int((12282-6950)/6),int((12282-6450)/6)):
  for c in range(int(2500/6),int(3050/6)):
   if not np.isfinite(p[r,c]):continue
   xyz=np.c_[[c*6,c*6+6,c*6,c*6+6],f[r,c],[12282-r*6,12282-r*6,12276-r*6,12276-r*6]];ground=h[r:r+2,c:c+2].ravel()
   for tri in ([0,1,3],[0,2,3]):
    weights=clip(UNIT,f[r,c,tri]-ground[tri])
    if len(weights)<3:continue
    q=(weights@xyz[tri]-pos)@rotation.T
    if np.min(q[:,2])>1:polys.append(q)
 # Downsample only masks for scalar fitting, full resolution preserved for later consumer.
 factor=2;size=(1920//factor,1080//factor);truth=np.array(Image.fromarray(magenta).resize(size,Image.Resampling.NEAREST))
 yy,xx=np.indices(truth.shape);roi=(yy>=450/factor)&(yy<900/factor)&(xx>=400/factor)&(xx<1600/factor);train=roi&(xx<960/factor);test=roi&~train
 def render(focal):
  im=Image.new('1',size);draw=ImageDraw.Draw(im)
  for q in polys:
   coords=np.c_[(960+focal*q[:,0]/q[:,2])/factor,(540-focal*q[:,1]/q[:,2])/factor]
   draw.polygon([tuple(xy) for xy in coords],fill=1)
  return np.array(im)
 def score(mask,roi):
  tp=int(np.sum(mask&truth&roi));fp=int(np.sum(mask&~truth&roi));fn=int(np.sum(~mask&truth&roi));return dict(tp=tp,fp=fp,fn=fn,iou=tp/max(1,tp+fp+fn),precision=tp/max(1,tp+fp),recall=tp/max(1,tp+fn))
 coarse=[]
 for focal in np.arange(300,1601,40):coarse.append((float(focal),score(render(focal),train)['iou']))
 start=max(coarse,key=lambda row:row[1])[0]
 fit=minimize_scalar(lambda focal:-score(render(focal),train)['iou'],bounds=(max(300,start-40),min(1600,start+40)),method='bounded',options={'xatol':.1,'maxiter':45})
 focal=float(fit.x);pred=render(focal);horiz=960/np.tan(rt['camera']['fov_applied']/2);vertical=540/np.tan(rt['camera']['fov_applied']/2)
 # Use the recorded central ray, not a rounded world target 0.15 mm off-axis.
 target=pos+rotation[2]*50;q=(target-pos)@rotation.T;central=[960+focal*q[0]/q[2],540-focal*q[1]/q[2]];assert np.max(abs(np.array(central)-[960,540]))<.0001
 report=dict(status='ESTIMATED_IMAGE_PROJECTION_NOT_NATIVE_CONFIRMATION',camera=camera,fov_argument=rt['camera']['fov_applied'],estimated_focal_px=focal,train=score(pred,train),holdout=score(pred,test),coarse_scan=coarse,formula_controls={'horizontal':dict(focal=horiz,train=score(render(horiz),train),holdout=score(render(horiz),test)),'vertical':dict(focal=vertical,train=score(render(vertical),train),holdout=score(render(vertical),test))},central_point_px=central,world_polygons=len(polys),inputs={str(path):sha(path) for path in (SOURCE,PFILE,FFILE,frame,R/'runtime.json')},limits=['Waves, foam, occlusion and the color threshold affect the silhouette; native screen-point confirmation remains required.','No new render anomaly or physical flooding is asserted.'])
 (B/'calibration.json').write_text(json.dumps(report,indent=2)+'\n');np.savez_compressed(B/'masks.npz',predicted=pred,marked=truth,train=train,holdout=test)
 # Diagnostic plot is generated data, not an edited source photograph.
 overlay=np.zeros((*truth.shape,3),np.uint8);overlay[pred]=[255,80,30];overlay[truth]=[70,100,255];overlay[pred&truth]=[30,200,70];Image.fromarray(overlay).save(B/'projection-mask-comparison.png')
 print(json.dumps({k:v for k,v in report.items() if k not in ['coarse_scan','camera','inputs']},indent=2))
if __name__=='__main__':main()
