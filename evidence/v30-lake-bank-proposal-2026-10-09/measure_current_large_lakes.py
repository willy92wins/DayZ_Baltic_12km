"""Locate the two deferred lakes by frozen camera coordinates, not drifting body ids."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy import ndimage
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/terrain'));from relevel_bodies_v30 import label_bodies
source=B/'candidate-repaired/terrain.npz';t=dict(np.load(source));h=t['heights'];ids=label_bodies(t['cls'],t['level'])
reports=[]
for name,x,z in [('deferred_269_southwest',622.4,840),('deferred_170_southeast',10436.5,308.2)]:
    r,c=int(round((12282-z)/6)),int(round(x/6));body=int(ids[r,c]);assert body>0
    mask=ids==body;rr,cc=np.nonzero(mask);r0=max(0,rr.min()-14);r1=min(2048,rr.max()+15);c0=max(0,cc.min()-14);c1=min(2048,cc.max()+15)
    m=mask[r0:r1,c0:c1];g=h[r0:r1,c0:c1];cls=t['cls'][r0:r1,c0:c1];dist=ndimage.distance_transform_edt(~m,sampling=6.)
    bank=(dist>0)&(dist<=12)&(cls==0);ring=(dist>12)&(dist<=36)&(cls==0);outer=(dist>36)&(dist<=72)&(cls==0)
    summary=lambda v:dict(count=int(v.size),min=float(v.min()),p10=float(np.percentile(v,10)),p50=float(np.percentile(v,50)),p90=float(np.percentile(v,90)),max=float(v.max()))
    levels=np.unique(t['level'][mask]);assert np.ptp(levels)<.011
    drycorridor=(t['reserve']|t['platform'])[r0:r1,c0:c1]&(dist<=36)
    touching=ndimage.binary_dilation(mask,structure=np.ones((3,3)))&~mask
    neighboring={int(k):int((touching&(t['cls']==k)).sum()) for k in np.unique(t['cls'][touching])}
    level=float(np.median(t['level'][mask]));bank_stats=summary(g[bank]);ring_stats=summary(g[ring])
    reports.append(dict(name=name,current_body_id=body,anchor_xz=[x,z],level_m=level,vertex_area_m2=int(mask.sum())*36,bed=summary(h[mask]),bank_0_12m=bank_stats,ring_12_36m=ring_stats,ring_36_72m=summary(g[outer]),bank_p90_minus_ring_median_m=bank_stats['p90']-ring_stats['p50'],water_minus_ring_median_m=level-ring_stats['p50'],nearby_engineering_vertices=int(drycorridor.sum()),touching_classes=neighboring))
result=dict(status='CURRENT_LAKE_GEOMETRY_DISCOVERY_NOT_LEVEL_APPROVAL',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),lakes=reports,limits=['Ids in historical tables refer to different censuses; location is the stable anchor.', 'Vertex-area and height/ring summaries are geometry diagnostics, not precise shoreline polygon area.', 'No water level or terrain edits. Navigation contacts require separate corridor readback before any lowering.'])
(B/'large-lakes-current.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
