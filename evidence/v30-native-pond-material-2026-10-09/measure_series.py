from pathlib import Path
import json
import numpy as np
from PIL import Image
B=Path(__file__).parent
r=json.loads((B/'runtime-working.json').read_text())
rois={'pond_group':(.31,.43,.79,.66),'calibrated_center':(.48,.48,.52,.52),'dry_control':(.12,.80,.27,.94),'large_pond_bank':(.55,.48,.65,.60)}
result={}
for name,uv in rois.items():
 arrays={}
 for phase in ['baseline','wetfloor0','restored']:
  paths=[Path(x['fullres_path']) for x in r['captures'] if x['phase']==phase];assert len(paths)==6
  frames=[]
  for p in paths:
   im=Image.open(p).convert('RGB');w,h=im.size
   rect=(int(uv[0]*w),int(uv[1]*h),int(uv[2]*w),int(uv[3]*h))
   frames.append(np.asarray(im.crop(rect),dtype=np.float32))
  arrays[phase]=np.stack(frames)
 a,b,c=[arrays[x] for x in ['baseline','wetfloor0','restored']]
 both=np.concatenate([a,c])
 # A strong per-pixel response must exceed every sampled original/restored frame.
 light_b=b.mean(-1);light_a=both.mean(-1)
 stable_lighter=light_b.min(0)>light_a.max(0)+5
 result[name]=dict(relative_box=uv,baseline_mean=float(a.mean()),changed_mean=float(b.mean()),restored_mean=float(c.mean()),median_delta_baseline_changed=float(np.abs(np.median(a,0)-np.median(b,0)).mean()),median_delta_baseline_restored=float(np.abs(np.median(a,0)-np.median(c,0)).mean()),changed_lighter_than_all_original_restored_by5_share=float(stable_lighter.mean()),pixels=int(stable_lighter.size))
(B/'pixel-series.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
