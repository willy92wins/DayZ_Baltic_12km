from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter,label,binary_dilation
sys.path.insert(0,'E:/DayZ-Baltic-Build/v30-georeferenced-render-audit-20261009')
from trace_native import trace
from analyze_archives import temporal
B=Path(__file__).parent
cal=json.loads((B/'native-projection.json').read_text()); mat=np.array(cal['camera']['matrix']).reshape(4,3); focal=cal['native_focal_px']
py,px=np.mgrid[450:951:2,250:1701:2]; shape=px.shape
cache=B/'native-rays.npz'
if cache.exists():
    ray=np.load(cache); xyz=ray['xyz']; kind=ray['kind']
else:
    h=np.load('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz')['heights']
    f=np.load('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009/preserved-field.npy')
    direction=mat[2]+((px.ravel()-960)/focal)[:,None]*mat[0]-((py.ravel()-540)/focal)[:,None]*mat[1]
    direction/=np.linalg.norm(direction,axis=1)[:,None]
    points,typ,distance=trace(h,f,mat[3],direction,sea=.85)
    xyz=points.reshape((*shape,3));kind=typ.reshape(shape);np.savez_compressed(cache,xyz=xyz,kind=kind)
wet=np.isin(kind,[2,3]);dry=(kind==1)&(xyz[:,:,1]>1.15)&~binary_dilation(wet,iterations=4)
dry&=~((abs(px-960)<16)&(abs(py-540)<16))
control=dry&(py>=850)&(xyz[:,:,1]>=1.799)&~binary_dilation(wet,iterations=12)
assert control.sum()>1000
full_control=np.zeros((1080,1920),bool);full_control[py,px]=control
rows=[];arrays={}
for phase in sys.argv[1:] or ['A-stable']:
    paths=sorted((B/'captures'/phase).glob('*.jpg')); assert len(paths)>=6
    a=np.stack([np.array(Image.open(p).convert('RGB')) for p in paths]);assert a.shape[1:]==(1080,1920,3)
    spread,drift=temporal(a,full_control);score=spread[py,px]
    sky=a[:,40:300,100:1800].astype(int)
    magenta=(sky[:,:,:,0]>sky[:,:,:,1]+65)&(sky[:,:,:,2]>sky[:,:,:,1]+65)&(sky[:,:,:,0]>120)
    assert magenta.sum()==0,phase
    arrays[phase]=score
    rows.append(dict(phase=phase,frames=len(paths),threshold=float(max(2,np.quantile(score[control],.999))),drift=drift.tolist(),control_samples=int(control.sum()),dry_samples=int(dry.sum()),max_dry_range=float(score[dry].max()),sky_magenta_pixels=int(magenta.sum())))
threshold=max(r['threshold'] for r in rows)
cohort=(xyz[:,:,0]>=2658)&(xyz[:,:,0]<=2742)&(xyz[:,:,2]>=6774)&(xyz[:,:,2]<=6846)&dry
for row in rows:
    score=arrays[row['phase']];suspect=dry&(score>threshold);groups,n=label(suspect);out=[]
    for i in range(1,n+1):
        mask=groups==i;count=int(mask.sum())
        if count<8:continue
        points=xyz[mask];coords=np.c_[px[mask],py[mask]]
        out.append(dict(samples=count,screen_bbox=[*coords.min(0).tolist(),*coords.max(0).tolist()],world_center=np.median(points,axis=0).tolist(),range_mean=float(score[mask].mean()),range_max=float(score[mask].max())))
    row.update(shared_threshold=threshold,suspect_samples=int(suspect.sum()),cohort_suspect_samples=int((suspect&cohort).sum()),cohort_dry_samples=int(cohort.sum()),cohort_range_quantiles=np.quantile(score[cohort],[.5,.9,.99,1]).tolist(),components=sorted(out,key=lambda a:a['samples'],reverse=True))
    heat=np.zeros((*shape,3),np.uint8);heat[dry]=[35,65,35];heat[wet]=[35,65,150];heat[suspect]=[255,100,20];Image.fromarray(heat).save(B/(row['phase']+'-heat.png'))
report=dict(status='NATIVE_PROJECTED_TEMPORAL_ANALYSIS',projection_focal_px=focal,rows=rows,limits=['Temporal changes are not alone material identification.','Baseline dry mask is common to all phases; omitted pond interiors excluded from dry comparison.','Grass and cloud shadows may contribute; foreground dry control removes common brightness drift.'])
(B/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');np.savez_compressed(B/'scores.npz',px=px,py=py,dry=dry,cohort=cohort,**arrays)
print(json.dumps([{k:v for k,v in r.items() if k not in ['components','drift']} for r in rows],indent=2))
