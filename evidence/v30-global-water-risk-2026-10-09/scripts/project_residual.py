from pathlib import Path
import numpy as np,json,sys
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import tri_sample
t=np.load('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008/candidate-c1r3p/terrain_valley.npz')
m=np.array([-.9967640042,0,-.08038418,.06680205,.55622053,-.82834548,.04471134,-.83103472,-.55442059]).reshape(3,3)
cam=np.array([2185.,280,7350])
rows=[]
for degrees in (42.5,60.,68.5,75.):
 d=m[2]+m[0]*((324-960)/540*np.tan(np.deg2rad(degrees/2)))+m[1]*((540-116)/540*np.tan(np.deg2rad(degrees/2)))
 lo,hi=0.,1500.
 for _ in range(40):
  a=(lo+hi)/2;p=cam+a*d
  if p[1]>float(tri_sample(t['heights'],p[0],p[2])):lo=a
  else:hi=a
 p=cam+hi*d;r,c=round((12282-p[2])/6),round(p[0]/6)
 rows.append(dict(assumed_vertical_fov=degrees,world=p.tolist(),cell=[r,c],data={k:str(t[k][r,c]) for k in ('cls','heights','reserve','platform','beach')}))
out=dict(status='FOV_UNCERTAIN_NOT_ACCEPTED_AS_COORDINATE',pixel=[324,116],rows=rows)
(W/'evidence/v30-global-water-risk-2026-10-09/residual-projection-hypotheses.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
