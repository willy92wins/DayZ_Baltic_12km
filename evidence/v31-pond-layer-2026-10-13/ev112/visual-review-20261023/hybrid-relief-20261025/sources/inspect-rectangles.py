from pathlib import Path
from collections import Counter
import json,hashlib
import numpy as np
R=Path(__file__).parent
path=R/'guarded-relief-batch-e-merged/terrain-buried.npz';z=np.load(path);h=z['heights']
mask=np.load(R/'guarded-relief-batch-e/domains.npz');fp=np.load(R/'guarded-relief-batch-e-merged/bury-work/fp0/footprint.npz')
screen=json.loads((R/'guarded-relief-batch-e/shape-screen.json').read_text());rows=[]
for finding in screen['findings']:
    if finding['kind']!='rectangular_terrain_transition':continue
    r0,c0,r1,c1=finding['bbox_rc'];sl=np.s_[r0-4:r1+5,c0-4:c1+5]
    area=h[sl];free=mask['free'][sl]
    domains={key:int(z[key][sl].sum()) for key in z.files if z[key].shape==h.shape and z[key].dtype==bool and z[key][sl].any()}
    rows.append(dict(finding=finding,padded_shape=list(area.shape),heights_m=[float(area.min()),float(area.max())],free_vertices=int(free.sum()),fixed_vertices=int((~free).sum()),shore_vertices=int(mask['shore'][sl].sum()),road_vertices=int(mask['road'][sl].sum()),domains=domains,heights=area.tolist(),free_mask=free.astype(int).tolist()))
report=dict(status='READ_ONLY_RECTANGLE_DIAGNOSIS',terrain_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),rectangles=rows,limits=['Bounding-box context is descriptive, not an edit authorization or proof of root cause.','No heights changed; all existing protections and water topology remain intact.'])
(R/'guarded-relief-batch-e/rectangle-context.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([{k:v for k,v in row.items() if k not in ('heights','free_mask')} for row in rows],indent=2))
