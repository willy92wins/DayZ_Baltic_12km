"""Read-only: distinguish wet native support from dry bounding-box padding."""
from pathlib import Path
import json
import numpy as np
from scipy.ndimage import binary_dilation

B=Path(__file__).parent; S=B.parent/'v30-strict-dry-composition-20261009/candidate'
t=np.load(S/'terrain.npz'); h=t['heights'].astype(float)
p=np.load(S/'plane.npy'); f=np.load(S/'visible-field.npy')
d=np.load(B/'domain.npz'); cells=d['cells']; rigid=d['core']; shift=.425
wetcore=np.zeros(h.shape,bool); dryfloor=np.zeros(h.shape,float)
offsets=[(0,0),(0,1),(1,0),(1,1)]
heights=np.stack([h[dr:dr+2047,dc:dc+2047] for dr,dc in offsets],axis=2)
wettri=0; drytri=0
for tri in [(0,1,3),(0,2,3)]:
    diff=np.maximum(p[:,:,None]-heights, f-heights)[:,:,tri]
    wet=cells & (diff.max(axis=2)>1e-8)
    dry=cells & ~wet
    wettri+=int(wet.sum()); drytri+=int(dry.sum())
    for k in tri:
        dr,dc=offsets[k]; sl=np.s_[dr:dr+2047,dc:dc+2047]
        wetcore[sl]|=wet
        need=np.where(dry,np.maximum(0,np.maximum(p,f[:,:,k])+shift-heights[:,:,k]+1e-6),0)
        dryfloor[sl]=np.maximum(dryfloor[sl],need)
assert np.all(~wetcore|rigid)
fixed=d['fixed']; engineering=t['reserve']|t['platform']; adjacent=binary_dilation(fixed,structure=np.ones((3,3)))
worst=json.loads((B/'apron-diagnosis.json').read_text())['worst']
for edge in worst:
    for q in edge['vertices']:
        r,c=q['row'],q['col']; q['required_by_wet_face']=bool(wetcore[r,c]);q['dry_minimum_uplift']=float(dryfloor[r,c])
report=dict(status='READ_ONLY_EXACT_WET_SUPPORT',rigid_box_core=int(rigid.sum()),wet_triangle_core=int(wetcore.sum()),
    unnecessary_dry_rigid=int((rigid&~wetcore).sum()),wet_faces=wettri,dry_faces=drytri,
    wet_core_fixed=int((wetcore&fixed).sum()),dry_floor_fixed=int(((dryfloor>1e-6)&fixed).sum()),
    box_core_adjacent_fixed=int((rigid&adjacent).sum()),wet_core_adjacent_fixed=int((wetcore&adjacent).sum()),
    worst_edges=worst[:5],limits=['Only support discovery; no new terrain, water level or radius authored.','P/F dry triangles still require inequalities to avoid flooding them after the translation.'])
np.savez_compressed(B/'exact-support-discovery.npz',wetcore=wetcore,dry_lower_uplift=dryfloor)
(B/'support-diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
