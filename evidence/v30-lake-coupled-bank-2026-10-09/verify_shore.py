from pathlib import Path
import sys,json
import numpy as np
import shapely
from shapely.geometry import LineString
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path[:0]=[str(W/'tools/terrain'),'E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009']
from relevel_bodies_v30 import label_bodies
from verify_native_turns import line_stats

def contours(h,p,mask):
 rr,cc=np.nonzero(mask&np.isfinite(p));out=[]
 xy=np.stack((np.c_[cc*6,12282-rr*6],np.c_[cc*6+6,12282-rr*6],np.c_[cc*6,12276-rr*6],np.c_[cc*6+6,12276-rr*6]),axis=1)
 d=p[rr,cc,None]-np.stack((h[rr,cc],h[rr,cc+1],h[rr+1,cc],h[rr+1,cc+1]),axis=1)
 for tri in ((0,1,3),(0,2,3)):
  use=np.flatnonzero((d[:,tri].min(1)<0)&(d[:,tri].max(1)>0))
  for index in use:
   pts=[]
   for a,b in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
    da,db=d[index,a],d[index,b]
    if da*db<0:pts.append(xy[index,a]+da/(da-db)*(xy[index,b]-xy[index,a]))
    elif da==0:pts.append(xy[index,a])
   pts=np.unique(np.round(pts,6),axis=0)
   if len(pts)==2:out.append(LineString(pts))
 merged=shapely.line_merge(shapely.union_all(out,grid_size=1e-6))
 return [l for l in getattr(merged,'geoms',[merged]) if l.length>24]

def main():
 t=np.load('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz');u=np.load(B/'candidate-repaired/terrain.npz');h=t['heights'].astype(float);v=u['heights'].astype(float);p=np.load('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy');ids=label_bodies(t['cls'],t['level']);reports=[]
 fig,axes=plt.subplots(1,2,figsize=(15,8),layout='constrained')
 for ax,(name,body) in zip(axes,[('southwest',273),('southeast',195)]):
  lake=ids==body;mask=lake[:-1,:-1]|lake[:-1,1:]|lake[1:,:-1]|lake[1:,1:];before=contours(h,p,mask);after=contours(v,p,mask)
  a=line_stats(before);b=line_stats(after);reports.append(dict(name=name,before=a,after=b,hausdorff_m=float(shapely.hausdorff_distance(shapely.union_all(before),shapely.union_all(after)))))
  for lines,color,label in [(before,'#3473c7','Actual'),(after,'#d14124','Candidato')]:
   for k,line in enumerate(lines):ax.plot(*np.array(line.coords).T,color=color,lw=.6,label=label if k==0 else None)
  ax.set_aspect('equal');ax.set_title(name);ax.legend()
 fig.savefig(B/'shore-comparison.png',dpi=130)
 (B/'shore-verification.json').write_text(json.dumps(dict(status='MEASURED_NATIVE_SHORE_COMPARISON',lakes=reports),indent=2)+'\n');print(json.dumps(reports,indent=2))
if __name__=='__main__':main()
