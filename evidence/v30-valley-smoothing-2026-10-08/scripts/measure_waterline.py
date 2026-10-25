"""Native triangular visible-waterline measurements, independent of the smoother."""
from pathlib import Path
import json,sys
import numpy as np,shapely
from shapely.geometry import LineString
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008');E=W/'evidence/v30-valley-smoothing-2026-10-08'
source=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
axes=json.loads(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/axes.json').read_text())
water=np.load('E:/DayZ-Baltic-Build/v30-water-visual-fix-20261008/stitched-water/visual_vertex_levels.npy')
def lines_for(h,cells):
 segs=[]
 for r,c in cells:
  for dr,dc in ((0,1),(1,0)):
   rc=[(r,c),(r+dr,c+dc),(r+1,c+1)]
   xy=np.array([(j*6,12282-i*6) for i,j in rc]);d=np.array([h[i,j]-water[i,j] for i,j in rc]);pts=[]
   for i,j in ((0,1),(1,2),(2,0)):
    if d[i]*d[j]<0:pts.append(tuple(np.round(xy[i]+d[i]/(d[i]-d[j])*(xy[j]-xy[i]),6)))
   if len(pts)==2 and pts[0]!=pts[1]:segs.append(LineString(pts))
 joined=shapely.line_merge(shapely.union_all(segs))
 return [g for g in getattr(joined,'geoms',[joined]) if g.length>24]
def stats(lines):
 angles=[]
 for ln in lines:
  ds=np.arange(0,ln.length,2.);p=np.array([ln.interpolate(d).coords[0] for d in ds])
  if len(p)<10:continue
  a=p[3:-3]-p[:-6];b=p[6:]-p[3:-3]
  angles.extend(np.degrees(np.arccos(np.clip((a*b).sum(1)/np.maximum(np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1),1e-12),-1,1))).tolist())
 v=np.array(angles)
 return dict(lines=len(lines),length_m=sum(g.length for g in lines),samples=len(v),turn_p50=float(np.median(v)),turn_p90=float(np.percentile(v,90)),turn_p95=float(np.percentile(v,95)),turn_over30_share=float(np.mean(v>30)))
label=sys.argv[1] if len(sys.argv)>1 else 'a'
h=np.load(source)['heights'];v=np.load(B/f'candidate-{label}/terrain_valley.npz')['heights']
out={}
for name,ax in axes.items():
 cells=ax['removed_cells'];aa=lines_for(h,cells);bb=lines_for(v,cells)
 out[name]=dict(before=stats(aa),after=stats(bb),hausdorff_m=float(shapely.hausdorff_distance(shapely.union_all(aa),shapely.union_all(bb))))
out['scope']='Only local removed-cell domains R1/R2/R3; stitched native visible plane minus terrain. No quad/bilinear contour and no joining across missing segments.'
(E/f'waterline-{label}.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
