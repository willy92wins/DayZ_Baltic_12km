from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
R=Path('E:/DayZ-Baltic-Build');B=Path(__file__).parent
sys.path.insert(0,str(R/'v30-georeferenced-render-audit-20261009'))
from trace_native import trace
from analyze_archives import temporal
cal=json.loads((R/'v30-native-projection-ab-20261009/native-projection.json').read_text());mat=np.array(cal['camera']['matrix']).reshape(4,3);focal=cal['native_focal_px'];py,px=np.mgrid[450:951:2,250:1701:2];shape=py.shape
direction=mat[2]+((px.ravel()-960)/focal)[:,None]*mat[0]-((py.ravel()-540)/focal)[:,None]*mat[1];direction/=np.linalg.norm(direction,axis=1)[:,None]
results=[];scores=[];masks=[]
for name,hfile,ffile,folder in [('A',R/'v30-native-hinge-finish-20261009/candidate/terrain.npz',R/'v30-frozen-water-stitch-20261009/preserved-field.npy','A2-cycle'),('translated',R/'v30-low-water-components-20261009/translation/terrain.npz',R/'v30-low-water-components-20261009/translation/visible-field.npy','Bstable-cycle')]:
    h=np.load(hfile)['heights'];f=np.load(ffile);xyz,kind,_=trace(h,f,mat[3],direction,sea=.85);xyz=xyz.reshape((*shape,3));kind=kind.reshape(shape);wet=np.isin(kind,[2,3]);dry=(kind==1)&(xyz[:,:,1]>1.15)&~binary_dilation(wet,iterations=4);dry&=~((abs(px-960)<16)&(abs(py-540)<16));control=dry&(py>=850)&(xyz[:,:,1]>=1.799)&~binary_dilation(wet,iterations=12)
    if name=='A':reference=control.copy()
    else:assert np.all(control[reference]);control=reference
    full_control=np.zeros((1080,1920),bool);full_control[py,px]=control
    paths=sorted((R/'v30-low-water-components-20261009/views'/folder).glob('*.jpg'));assert len(paths)==8
    a=np.stack([np.array(Image.open(p).convert('RGB')) for p in paths]);score,_=temporal(a,full_control);score=score[py,px]
    cohort=dry&(xyz[:,:,0]>=2658)&(xyz[:,:,0]<=2742)&(xyz[:,:,2]>=6774)&(xyz[:,:,2]<=6846)
    threshold=float(max(2,np.quantile(score[control],.999)));scores.append(score);masks.append(cohort)
    results.append(dict(phase=name,threshold=threshold,cohort_dry_samples=int(cohort.sum()),cohort_quantiles=np.quantile(score[cohort],[.5,.9,.99,1]).tolist()))
threshold=max(r['threshold'] for r in results)
for row,score,cohort in zip(results,scores,masks):row.update(shared_threshold=threshold,suspect_cohort_samples=int((cohort&(score>threshold)).sum()),suspect_fraction=float((score[cohort]>threshold).mean()))
report=dict(status='ARCHIVED_TRANSLATION_REVIEW_WITH_NATIVE_CALIBRATION',results=results,limits=['Different terrain height changes screen-to-ground mapping; cohort fractions use the same world rectangle, not identical screen pixels.','Native focal measuredEV48 with same matrix/FOV/game version; archived frames do not contain native projections themselves.','This supports a local mitigation; no automatic level-policy promotion or global closure.'])
(B/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
