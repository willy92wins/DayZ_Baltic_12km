"""Read-only local water/terrain inventory around the native-projected user residual."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy import ndimage
B=Path(__file__).parent;W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/terrain'));from relevel_bodies_v30 import label_bodies
from v30_common import tri_sample
src=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/candidate/terrain.npz');t=dict(np.load(src));h=t['heights'];labels=label_bodies(t['cls'],t['level']);x,z=2718.4852495913565,6812.812873578129
r,c=round((12282-z)/6),round(x/6);rr,cc=np.indices(h.shape);dist=np.hypot(cc*6-x,12282-rr*6-z)
local=(dist<42)&(t['cls']>0);bodies=[]
for ident in np.unique(labels[local]):
 if ident==0:continue
 m=labels==ident;rows,cols=np.nonzero(m);halo=ndimage.binary_dilation(m,structure=np.ones((3,3)),iterations=5)&~m;dry=halo&(t['cls']==0)
 bodies.append(dict(body=int(ident),classes=np.unique(t['cls'][m]).tolist(),level_min=float(t['level'][m].min()),level_max=float(t['level'][m].max()),wet_vertices=int(m.sum()),bounds=[int(cols.min()*6),int(12282-rows.max()*6),int(cols.max()*6),int(12282-rows.min()*6)],bed_min=float(h[m].min()),bed_max=float(h[m].max()),nearest_vertex_m=float(dist[m].min()),dry_bank_min=float(h[dry].min()) if dry.any() else None,dry_bank_median=float(np.median(h[dry])) if dry.any() else None,engineering_vertices_30m=int(((t['reserve']|t['platform'])&(m|halo)).sum()),narva_vertices_30m=int((t['narva']&(m|halo)).sum())))
q=dict(status='READ_ONLY_RESIDUAL_BASIN_DISCOVERY',terrain_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),target=dict(x=x,z=z,ground=float(tri_sample(h.astype(float),x,z)),cls=int(t['cls'][r,c]),narva=bool(t['narva'][r,c]),reserve=bool(t['reserve'][r,c]),platform=bool(t['platform'][r,c])),bodies=sorted(bodies,key=lambda b:b['nearest_vertex_m']),limits=['Body ids group class and rounded nominal levels; not a hydraulic/visible connected-component proof.','No proposed level, terrain or protection change is applied.'])
(B/'discovery.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
