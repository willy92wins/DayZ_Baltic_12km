"""Frozen river-axis consumer: detect newly dry intervals, independent of vertex labels."""
from pathlib import Path
import sys,json
import numpy as np
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008');E=W/'evidence/v30-valley-smoothing-2026-10-08'
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import tri_sample
h=np.load('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')['heights']
v=np.load(B/'candidate-b1/terrain_valley.npz')['heights']
water=np.load('E:/DayZ-Baltic-Build/v30-water-visual-fix-20261008/stitched-water/visual_vertex_levels.npy')
axes=json.loads(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/axes.json').read_text())
report={}
for name,a in axes.items():
 s=np.arange(a['s_lo'],a['s_hi'],.5);x=np.interp(s,a['s'],a['x']);z=np.interp(s,a['s'],a['z'])
 wb=tri_sample(water,x,z);before=wb-tri_sample(h,x,z);after=wb-tri_sample(v,x,z)
 lost=(before>.101)&(after<.02)
 intervals=[];on=False
 for i,val in enumerate(np.r_[lost,False]):
  if val and not on:start=i;on=True
  if on and not val:
   end=i-1;intervals.append(dict(s_from=float(s[start]),s_to=float(s[end]),length_m=float(s[end]-s[start]+.5),x=float(x[start]),z=float(z[start]),min_before=float(before[start:i].min()),min_after=float(after[start:i].min())));on=False
 report[name]=dict(samples=len(s),new_exposed_samples=int(lost.sum()),before_min=float(before.min()),after_min=float(after.min()),new_dry_intervals=intervals)
out=dict(status='FAIL_FROZEN_FLOW_SAMPLES' if any(v['new_exposed_samples'] for v in report.values()) else 'PASS_LOCAL_AXIS',reaches=report,scope='Frozen axes from the previous independent channel trial; native triangle interpolation of unchanged visible water and both terrains. No new axes derived from the candidate.',limit='Loss of old wet samples does not by itself prove disconnected water: a shifted channel can leave the frozen axis. Connectivity requires a separate native-polygon component audit. Physical nominal planes require separate checks.')
(E/'flow-continuity-b1.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
