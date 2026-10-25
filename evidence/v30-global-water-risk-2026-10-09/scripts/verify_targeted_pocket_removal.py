"""Keep intended bodies; remove only independently identified dry-vertex flooding pockets."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-global-water-risk-2026-10-09';sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import cell_planes
from audit_pond_topology import domain,controls
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008/candidate-c1r3p/terrain_valley.npz')
dst=B/'measured-bank-bed-r1/terrain.npz';prior=json.loads((E/'measured-bank-bed-verification.json').read_text())
assert sha(src)==prior['source_sha256'] and sha(dst)==prior['terrain_sha256']
t=dict(np.load(src));v=np.load(dst)['heights'];w=np.load('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
manifest=json.loads(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/water/pieces.json').read_text())
plane=cell_planes(w['cls'],w['level'],sea_cut=float(manifest['sea_cutoff_m']))
# Targets come from the baseline engine inventory, predating the candidate.
points=json.loads((E/'native-anomaly-classification.json').read_text())['points']
target=np.zeros_like(t['cls'],dtype=bool)
for p in points:
    if p['reason']=='source_dry_below_neighbor_pond_plane':target[int(p['row']),int(p['col'])]=True
assert target.sum()==9 and (t['cls'][target]==0).all()
a=domain(t['heights'],plane);b=domain(v,plane)
rr,cc=a['cells'];n=t['heights'].shape[1]
faces=np.stack([np.stack([rr*n+cc,rr*n+cc+1,(rr+1)*n+cc+1],1),np.stack([rr*n+cc,(rr+1)*n+cc,(rr+1)*n+cc+1],1)],1).reshape(-1,3)
submerged=t['heights'].ravel()[faces]<np.repeat(plane[rr,cc],2)[:,None]
def eligible(source_class,declared):
    invalid=(submerged&((source_class.ravel()[faces]!=0)|~declared.ravel()[faces])).any(1)
    active=a['labels']>=0
    count=np.bincount(a['labels'][active],weights=invalid[active],minlength=len(a['body_area']))
    return set(np.flatnonzero((count==0)&(a['body_area']>=1)).tolist())
permitted=eligible(t['cls'],target)
assert len(permitted)==8
active=b['labels']>=0
assert not ((a['labels']<0)&active).any(),'unreviewed newly wet triangle'
pairs=np.unique(np.c_[a['labels'][active],b['labels'][active]],axis=0);mapping={}
for i,j in pairs:mapping.setdefault(int(i),[]).append(int(j))
rows=[]
for i,oldarea in enumerate(a['body_area']):
    if oldarea<1:continue
    matched=[j for j in mapping.get(i,[]) if b['body_area'][j]>=1]
    remaining=float(sum(b['body_area'][j] for j in matched))
    if i in permitted:ok=not mapping.get(i,[])
    else:ok=len(matched)==1 and remaining>=.9*oldarea
    rows.append(dict(component=i,action='remove_predeclared_dry_pocket' if i in permitted else 'preserve_intended_water',before_m2=float(oldarea),after_m2=remaining,components_after=len(matched),pass_gate=bool(ok)))
negative=dict(no_inventory_no_exemption=not eligible(t['cls'],np.zeros_like(target)))
fake=t['cls'].copy();fake[target]=7
negative['source_water_never_exempt']=not eligible(fake,target)
negative.update(controls())
checks={k:x for k,x in prior['checks'].items() if k!='pond_topology'}
checks.update(intended_water_topology=all(p['pass_gate'] for p in rows),eight_target_pockets_removed=all(p['after_m2']==0 for p in rows if p['component'] in permitted),negative=all(negative.values()))
assert all(checks.values()),checks
report=dict(status='PASS_OFFLINE_TARGETED_FLOOD_REMOVAL',source_sha256=sha(src),terrain_sha256=sha(dst),checks=checks,negative=negative,
    previous_report_sha256=sha(E/'measured-bank-bed-verification.json'),inventory_sha256=sha(E/'native-anomaly-classification.json'),sea_cutoff_m=float(manifest['sea_cutoff_m']),
    protected_components=sum(p['action']=='preserve_intended_water' for p in rows),removed_components=[p for p in rows if p['component'] in permitted],
    minimum_retained_area_ratio=min(p['after_m2']/p['before_m2'] for p in rows if p['action']=='preserve_intended_water'),
    changes=prior['changes'],limits=['Old blanket topology FAIL retained: it incorrectly protected the eight unwanted dry-only pockets. This gate expressly removes only baseline-native-confirmed dry-vertex pockets, never arbitrary small ponds.','Compiled and native checks remain required; this does not certify the visual sea residual.'])
(E/'targeted-pocket-removal-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('changes','removed_components')},indent=2))
