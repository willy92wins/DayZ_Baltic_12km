"""One independently identified dry corner under a compiled pond, missed by presence flags."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from shapely.geometry import shape
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-global-water-risk-2026-10-09'
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009');sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import cell_planes,tri_sample
from audit_pond_topology import domain,compare,controls
from audit_fairway_triangles_v30 import records,depths
from verify_roads_v30 import evaluate
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=B/'measured-bank-bed-r1/terrain.npz';assert sha(source)=='28325d0605c3561844477ada9b4c5154926782fd4dd13470c9e68cdaa02ca491'
t=dict(np.load(source));h=t['heights'].astype(float);v=h.copy();row,col=931,375
temporal=json.loads((E/'scalar-temporal-runtime-verification.json').read_text())
p=next(p for p in temporal['series']['results'] if p['id']==9077)
assert p['positive_depth_samples']==62 and p['no_fake_minus_ground']['min']>.59 and p['pond_true']==0
compiled=json.loads((E/'scalar-water-geometry.json').read_text())
cp=next(p for p in compiled if p['point']['x']==2250)
assert any(q['geometry_covers'] and q['native_level_matches'] for q in cp['candidates'])
assert t['cls'][row,col]==0 and not any(t[k][row,col] for k in ('reserve','platform','beach'))
v[row,col]=np.float32(3.35)
water=np.load('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz');plane=cell_planes(water['cls'],water['level'],sea_cut=.51)
old=domain(h,plane);new=domain(v,plane);rr,cc=old['cells'];n=2048
faces=np.stack([np.stack([rr*n+cc,rr*n+cc+1,(rr+1)*n+cc+1],1),np.stack([rr*n+cc,(rr+1)*n+cc,(rr+1)*n+cc+1],1)],1).reshape(-1,3)
depth=np.repeat(plane[rr,cc],2)[:,None]-h.ravel()[faces]
active=old['labels']>=0
invalid=((depth>0)&(faces!=row*n+col)).any(1)
bad=np.bincount(old['labels'][active],weights=invalid[active],minlength=len(old['body_area']))
permitted=set(np.flatnonzero((bad==0)&(old['body_area']>=1)).tolist())
topology,_=compare(h,v,plane)
failures=topology['failed_components'];assert all(p['component'] in permitted and p['area_after']==0 for p in failures),failures
assert all(not ((old['labels']==i)&(new['labels']>=0)).any() for i in permitted)
struct=t['reserve']|t['platform']|t['beach'];navsupport=np.zeros_like(struct);nav=[]
for path in [Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson'),W/'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson']:
    for f in json.loads(path.read_text())['features']:
        if f['properties'].get('kind','corridor24m')!='corridor24m':continue
        rec=records(shape(f['geometry']),plane);navsupport.ravel()[np.unique(rec['ids'])]=True
        a,b=depths(h,rec),depths(v,rec)
        nav.append(dict(name=f['properties'].get('name',f['properties'].get('river')),minimum_before=float(a.min()),minimum_after=float(b.min()),exact=bool(np.array_equal(a,b))))
ref=json.loads((E/'halo-r2-consumers-reference.json').read_text());xy=np.array([[p['x'],p['z']] for p in ref['points']])
def judge(a):
    changes=a!=h
    return dict(scope=bool(changes.sum()==1 and changes[row,col]),source_dry_corner=bool(a[row,col]>=3.34999),
        engineering_exact=not bool((changes&struct).any()),corridor_support_exact=not bool((changes&navsupport).any()),
        wet_beds_exact=not bool((changes&(t['cls']>0)).any()),old_120_controls_exact=bool(np.max(np.abs(tri_sample(a,xy[:,0],xy[:,1])-tri_sample(h,xy[:,0],xy[:,1])))<1e-6))
checks=judge(v);bad_slope=0
for dr,dc in ((0,1),(1,0)):
    def slopes(a):
        mid=a[dr:dr+2047,dc:dc+2047]
        return np.degrees(np.arctan(np.hypot(mid-a[:-1,:-1],a[1:,1:]-mid)/6))
    bad_slope+=int((slopes(v)>np.maximum(slopes(h),35)+1e-4).sum())
checks['slopes']=bad_slope==0;checks['intended_water_topology']=True
roads=evaluate(v,t['water'].astype(bool));checks['roads']=roads['status']=='PASS'
negative=controls();negative['unfixed_pocket_rejected']=not judge(h)['source_dry_corner']
a=v.copy();r,c=np.argwhere(struct)[100];a[r,c]+=.1;negative['engineering_change_rejected']=not judge(a)['engineering_exact']
assert all(checks.values()) and all(negative.values()),checks
out=B/'measured-bank-bed-r2';out.mkdir(exist_ok=False)
np.savez_compressed(out/'terrain.npz',**dict(t,heights=v.astype(t['heights'].dtype)))
u=dict(np.load(out/'terrain.npz'));assert all(np.array_equal(t[k],u[k],equal_nan=True) for k in t if k!='heights')
report=dict(status='PASS_OFFLINE_LAST_NOMINAL_POCKET',source_sha256=sha(source),terrain_sha256=sha(out/'terrain.npz'),checks=checks,negative=negative,
    change=dict(row=row,col=col,x=2250,z=6696,before=float(h[row,col]),after=float(v[row,col]),water_plane=3.),
    predeclared_removable_components=sorted(permitted),removed_components=failures,protected_components=topology['components']-len(permitted),
    navigation=nav,roads=roads,metadata_exact=True,
    limits=['One native persistent positive-depth corner, exact compiled coverage and the only source dry corner below a pond plane.','No change to the 230 intermittent shoreline contacts or the visual-only bridge residual.','Repeat native census and scalar temporal measurement before acceptance.'])
(E/'last-nominal-pocket-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('navigation','roads')},indent=2))
