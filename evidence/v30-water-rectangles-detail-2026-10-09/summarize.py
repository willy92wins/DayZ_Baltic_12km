from pathlib import Path
import json,hashlib,re
import numpy as np
from PIL import Image
E=Path(__file__).parent
pre=json.loads((E/'preflight.json').read_text())
hashes={k:hashlib.sha256(Path(p).read_bytes()).hexdigest() for k,p in pre['paths'].items()}
assert hashes==pre['hashes']
log=(E/'native-detail.log').read_text()
phases=[s for s in log.splitlines() if s.startswith('PHASE;')]
assert len(phases)==3 and phases[0].startswith('PHASE;0;') and ';index=4;changed=1;restart=0' in phases[1] and 'requested;index=2;changed=0' in phases[2]
records=json.loads((E/'runtime-records.json').read_text())
assert records['ev74close']['graceful']
rois={'reported_grey':[770,620,860,680],'near_ripple_control':[470,845,575,900],'dry_control':[1280,775,1450,875]}
groups={'A':sorted((E/'A').glob('*.jpg'))[-3:],'B':sorted((E/'B').glob('*.jpg')),'A-return':sorted((E/'A-return').glob('*.jpg'))}
assert all(len(v)==3 for v in groups.values())
stats={}
for name,files in groups.items():
    frames=np.array([np.asarray(Image.open(p).convert('RGB'),dtype=np.float32) for p in files])
    assert frames.shape==(3,1080,1920,3)
    regions={}
    for key,(x0,y0,x1,y1) in rois.items():
        q=frames[:,y0:y1,x0:x1]
        regions[key]=dict(mean_rgb=q.mean(axis=(0,1,2)).tolist(),temporal_range_rgb=float(np.ptp(q,axis=0).mean()),horizontal_abs_gradient=float(abs(np.diff(q,axis=2)).mean()),vertical_abs_gradient=float(abs(np.diff(q,axis=1)).mean()))
    stats[name]=dict(files=[p.name for p in files],regions=regions)
out=dict(status='RECTANGULAR_WATER_DEFECT_PERSISTS_AT_BOTH_DETAIL_SETTINGS',phases=phases,hashes_before=pre['hashes'],hashes_after=hashes,profile_identical=True,camera=[2417,65,6745],look_at=[2417,0,6950],fov_requested=1.1,rois=rois,stats=stats,limits=['These ROI statistics describe pixels, not water identity or a validated automatic defect detector.','Option readback establishes requested2/4/2. No independent native terrain mesh reader establishes the chosen cell LOD at this pose.','Visual boundaries persist; this does not rule out all native terrain culling mechanisms.','First two A frames are invalid loading/menu/magenta and are excluded.','Physical water and frame progress are not render acceptance.'])
(E/'summary.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['stats','rois']},indent=2))
