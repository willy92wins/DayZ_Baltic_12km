"""Read every unchanged vegetation record; check actual placement origins against altered native cells."""
from pathlib import Path
import json,math,hashlib,sys
import numpy as np
O=Path(__file__).parent;D=O/'water-fix-b';P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(P/'tools/terrain'));from v30_common import tri_sample
ref=json.loads((O.parent/'ev111-wip/forest/ref-v2/livonia-reference-v31.json').read_text())['models']
patch=json.loads((D/'candidate.json').read_text())['patch'];centres=[(p['x'],p['z']) for p in patch];near=[];n=0
src=O/'forest-map-51ae/records.json';digest=hashlib.sha256()
with src.open('rb') as f:
 for line in f:
  digest.update(line);s=line.strip().rstrip(b',')
  if s in (b'[',b']',b''):continue
  v=json.loads(s);m=v['matrix'];key=v['model'].replace('\\','/').lower()
  if key not in ref:key=v['model']
  assert key in ref,key
  bc=ref[key]['bc'];x=m[9]-sum(m[k*3]*bc[k] for k in range(3));z=m[11]-sum(m[k*3+2]*bc[k] for k in range(3))
  distance=min(math.hypot(x-cx,z-cz) for cx,cz in centres)
  if distance<=20:near.append(dict(index=n,model=v['model'],origin=[x,z],distance=distance))
  n+=1
old=np.load(O/'terrain-ev112-c.npz')['heights'];new=np.load(D/'terrain.npz')['heights'];affected=[]
for v in near:
 x,z=v['origin'];b=float(tri_sample(old,[x],[z])[0]);a=float(tri_sample(new,[x],[z])[0]);v.update(old_ground=b,new_ground=a)
 if abs(a-b)>1e-6:affected.append(v)
out=dict(status='PASS_NO_ORIGIN_HEIGHT_CHANGE' if not affected else 'AFFECTED_REQUIRES_RESEATING',records=n,records_sha256=digest.hexdigest(),within20m=near,changed_origin_heights=affected,limits='Only native height at actual placement origins, not full model footprint, normal samples or all forest gates.')
(D/'forest-origin-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='within20m'}),flush=True);print('within20m',len(near),flush=True)
