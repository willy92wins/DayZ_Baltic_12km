"""Judge the saved D2 against frozen geometry and native downstream consumers."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from shapely.geometry import shape
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009');E=W/'evidence/v30-global-water-risk-2026-10-09'
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import tri_sample,cell_planes
from audit_fairway_triangles_v30 import records,depths
from verify_roads_v30 import evaluate
from audit_pond_topology import compare,controls,domain
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008/candidate-c1r3p/terrain_valley.npz')
dst=B/'candidate-d2/terrain.npz'
t=dict(np.load(src));u=dict(np.load(dst));h=t['heights'].astype(float);v=u['heights'].astype(float);wet=t['cls']>0
w=np.load('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
plane=cell_planes(w['cls'],w['level']);nav=[];navsupport=np.zeros_like(wet)
for path in [Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson'),W/'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson']:
    for f in json.loads(path.read_text())['features']:
        if f['properties'].get('kind','corridor24m')!='corridor24m':continue
        rec=records(shape(f['geometry']),plane);navsupport.ravel()[np.unique(rec['ids'])]=True
        nav.append(dict(name=f['properties'].get('name',f['properties'].get('river')),faces=rec['faces'],
            depth_before=float(depths(h,rec).min()),depth_after=float(depths(v,rec).min()),
            native_depth_exact=bool(np.array_equal(depths(h,rec),depths(v,rec)))))
refs=[]
for path in [W/'evidence/v30-valley-smoothing-2026-10-08/c1r3p-probe-reference.json',W/'evidence/v30-bug-recheck-2026-10-08/wave-fixed-reference.json']:
    refs+=json.loads(path.read_text())['points']
coords=np.array([[p['x'],p['z']] for p in refs]);struct=t['reserve']|t['platform']|t['beach']
frozen=wet|struct|navsupport
for x,z in coords:
    r=int(np.floor((12282-z)/6));c=int(np.floor(x/6));frozen[r:r+2,c:c+2]=True
frozen[:2]=True;frozen[-2:]=True;frozen[:,:2]=True;frozen[:,-2:]=True
target=json.loads((E/'native-projection.json').read_text())['points'][0]['world']
def judge(a):
    changed=a!=h
    return dict(finite=bool(np.isfinite(a).all()),no_lowering=not bool((a<h).any()),max_raise=bool(np.max(a-h)<=.40001),
        wet_bed_exact=not bool((changed&wet).any()),structural_exact=not bool((changed&struct).any()),
        corridor_support_exact=not bool((changed&navsupport).any()),
        historical_controls_exact=bool(np.max(np.abs(tri_sample(a,coords[:,0],coords[:,1])-tri_sample(h,coords[:,0],coords[:,1])))<1e-6),
        no_unrequested_changes=not bool((changed&((h>=1.8-1e-5)|(h<1.4-1e-6))).any()),
        no_remaining_eligible_lowland=not bool((~frozen&(h>=1.4-1e-6)&(a<1.8-1e-5)).any()),
        confirmed_point_at_target=bool(tri_sample(a,target[0],target[2])>=1.8-1e-5))
checks=judge(v);bad=0
for dr,dc in ((0,1),(1,0)):
    def slope(a):
        mid=a[dr:dr+2047,dc:dc+2047]
        return np.degrees(np.arctan(np.hypot(mid-a[:-1,:-1],a[1:,1:]-mid)/6))
    land=~wet[:-1,:-1]|~wet[dr:dr+2047,dc:dc+2047]|~wet[1:,1:]
    bad+=int((land&(slope(v)>np.maximum(slope(h),35)+1e-4)).sum())
checks['slopes']=bad==0
checks['metadata_exact']=all(np.array_equal(t[k],u[k],equal_nan=True) for k in t if k!='heights')
topology,bad_support=compare(h,v,plane);checks['pond_topology']=topology['status']=='PASS_FROZEN_POND_MODEL'
roads=evaluate(v,t['water'].astype(bool));checks['roads']=roads['status']=='PASS'
negative={}
for name,r,c,value,gate in [('residual_restored',912,453,1.52,'confirmed_point_at_target'),('bed_raised',912,455,1.5,'wet_bed_exact'),('nonfinite',912,453,float('nan'),'finite')]:
    a=v.copy();a[r,c]=value;negative[name]=not judge(a)[gate]
r,c=np.argwhere(struct&~wet)[100];a=v.copy();a[r,c]+=.1;negative['engineering_moved']=not judge(a)['structural_exact']
negative.update(controls())
low=~frozen&(h>=1.4-1e-6)&(v<1.8-1e-5)
r,c=np.nonzero(low)
out=dict(status='PASS_OFFLINE_TRANSITION_REPAIR' if all(checks.values()) and all(negative.values()) else 'FAIL_NOT_FOR_PACKAGING',
    checks=checks,negative=negative,source_sha256=sha(src),terrain_sha256=sha(dst),
    point_before=float(tri_sample(h,target[0],target[2])),point_after=float(tri_sample(v,target[0],target[2])),
    residual_touches_failed_pond_support=bool(bad_support[912:914,453:455].any()),
    unresolved_free_points=[dict(x=int(cc*6),z=int(12282-rr*6),height=float(v[rr,cc])) for rr,cc in zip(r,c)],
    ponds=topology,navigation=nav,roads=roads,
    limits=['The D2 scope is not a whole-map visual envelope.','Discard D2 on any failed product gate; no silent geometric exemption.'])
(E/'d2-verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('ponds','navigation','roads','unresolved_free_points')},indent=2))
assert all(negative.values())
