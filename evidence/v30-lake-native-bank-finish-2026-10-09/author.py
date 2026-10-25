from pathlib import Path
import sys,json,time,hashlib
import numpy as np
from scipy.ndimage import distance_transform_edt
B=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path[:0]=[str(W/'tools/terrain'),'E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009']
from relevel_bodies_v30 import label_bodies
from author_hinges import K,LAMBDA,build_groups,controls
SOURCE=Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz')
PLANE=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy')
FIXED=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/constraints.npz')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 assert not (B/'authoring.json').exists(),'one lake-bank candidate'
 assert sha(SOURCE)=='fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6'
 t=dict(np.load(SOURCE));original=t['heights'].astype(float);h=original.copy();p=np.load(PLANE)
 water_support=np.zeros(h.shape,bool)
 for dr,dc in ((0,0),(0,1),(1,0),(1,1)):water_support[dr:dr+2047,dc:dc+2047]|=np.isfinite(p)
 fixed=np.load(FIXED)['fixed']|water_support|t['water']|t['beach']|(t['cls']!=0)
 fixed[:11]=True;fixed[-11:]=True;fixed[:,:11]=True;fixed[:,-11:]=True
 labels=label_bodies(t['cls'],t['level']);allowed=np.zeros(h.shape,bool);minimum=original.copy();reports=[];banks={}
 for name,x,z in [('southwest',622.4,840.),('southeast',10436.5,308.2)]:
  body=int(labels[round((12282-z)/6),round(x/6)]);assert body>0
  lake=labels==body;dist=distance_transform_edt(~lake,sampling=6);dry=t['cls']==0
  ring=(dist>12)&(dist<=36)&dry;bank=(dist>0)&(dist<=36)&dry;banks[name]=bank
  level=float(np.median(t['level'][lake]));floor=max(1.8,level+.3,float(np.median(original[ring])))
  scope=(dist>0)&(dist<72)&dry&~fixed;allowed|=scope
  fade=np.clip((72-dist)/18,0,1);fade=fade*fade*(3-2*fade)
  minimum[scope]=np.minimum(original[scope],np.maximum(original[scope]-1.5*fade[scope],floor))
  reports.append(dict(name=name,body=body,anchor_xz=[x,z],water_level_m=level,unchanged_water_vertices=int(lake.sum()),dry_floor_m=floor,editable_vertices=int(scope.sum()),bank_vertices=int(bank.sum()),fixed_bank_vertices=int((bank&fixed).sum())))
 np.savez_compressed(B/'constraints.npz',allowed=allowed,fixed=fixed,water_support=water_support,minimum=minimum,**banks)
 groups,coeff=build_groups(h,allowed);flat=h.ravel();base=original.ravel();lower=minimum.ravel();maximum=base
 aa=np.sum(coeff*coeff,axis=1)[None,:];started=time.monotonic();history=[]
 for sweep in range(60):
  largest=0.
  for ids,tri,radius in groups:
   if not len(ids):continue
   grad=LAMBDA*(flat[ids]-base[ids])
   for (dr,dc),w in K.items():grad+=w*flat[ids+dr*2048+dc]
   step=-grad/(K[(0,0)]+LAMBDA);g=np.diff(flat[tri],axis=2);bb=np.sum(g*coeff[None,:,:],axis=2);cc=np.sum(g*g,axis=2)-radius
   disc=np.sqrt(np.maximum(0,bb*bb-aa*cc));lo=np.maximum(((-bb-disc)/aa).max(axis=1),lower[ids]-flat[ids]);hi=np.minimum(((-bb+disc)/aa).min(axis=1),maximum[ids]-flat[ids])
   assert np.max(lo-hi,initial=0)<1e-8
   step=np.clip(step,lo,hi)*(1-1e-10);flat[ids]+=step;largest=max(largest,float(abs(step).max(initial=0)))
  elapsed=time.monotonic()-started;history.append(dict(sweep=sweep+1,max_step_m=largest,seconds=elapsed))
  if sweep%10==0:print(json.dumps(history[-1]),flush=True)
  if largest<.0001 or elapsed>600:break
 v=h.astype(np.float32);target=B/'candidate';target.mkdir(exist_ok=False);np.savez_compressed(target/'terrain.npz',**(t|dict(heights=v)))
 ids=np.flatnonzero(v!=t['heights']);np.savez_compressed(B/'terrain-delta.npz',ids=ids,before=t['heights'].ravel()[ids],after=v.ravel()[ids])
 report=dict(status='CANDIDATE_PENDING_CONSUMER',source_sha256=sha(SOURCE),candidate_sha256=sha(target/'terrain.npz'),constraints_sha256=sha(B/'constraints.npz'),changed_vertices=len(ids),maximum_lowering_m=float((original-v).max()),lakes=reports,history=history,controls=controls())
 (B/'authoring.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='history'},indent=2))
if __name__=='__main__':main()
