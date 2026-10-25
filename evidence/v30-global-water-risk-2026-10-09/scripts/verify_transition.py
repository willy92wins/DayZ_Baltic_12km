"""Independent invariants for D1, including native physical faces and frozen consumers."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009');E=W/'evidence/v30-global-water-risk-2026-10-09'
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import tri_sample,grid_xz
from verify_roads_v30 import evaluate
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008/candidate-c1r3p/terrain_valley.npz')
dst=B/'candidate-d1/terrain.npz'
t=dict(np.load(src));u=dict(np.load(dst));h=t['heights'].astype(float);v=u['heights'].astype(float)
wet=t['cls']>0;dry=~wet
# Any changed point of a native water-intersecting face fails, including its dry corner.
water_support=np.zeros_like(wet)
for dr,dc in ((0,1),(1,0)):
    face_wet=wet[:-1,:-1]|wet[dr:dr+2047,dc:dc+2047]|wet[1:,1:]
    water_support[:-1,:-1]|=face_wet
    water_support[dr:dr+2047,dc:dc+2047]|=face_wet
    water_support[1:,1:]|=face_wet
structural=t['reserve']|t['platform']|t['beach']
fixed=water_support|structural
fixed[:2]=True;fixed[-2:]=True;fixed[:,:2]=True;fixed[:,-2:]=True
ref=json.loads((W/'evidence/v30-valley-smoothing-2026-10-08/c1r3p-probe-reference.json').read_text())
old_wave=json.loads((W/'evidence/v30-bug-recheck-2026-10-08/wave-fixed-reference.json').read_text())
coords=np.array([[p['x'],p['z']] for p in ref['points']+old_wave['points']])
x,z=grid_xz();r3=(x>=7170)&(x<=7470)&(z>=5630)&(z<=5920)
def slope_fail(a):
    total=0
    for dr,dc in ((0,1),(1,0)):
        def slope(b):
            mid=b[dr:dr+2047,dc:dc+2047]
            return np.hypot(mid-b[:-1,:-1],b[1:,1:]-mid)
        touch=dry[:-1,:-1]|dry[dr:dr+2047,dc:dc+2047]|dry[1:,1:]
        total+=int((touch&(slope(a)>np.maximum(slope(h),6*np.tan(np.deg2rad(35)))+1e-5)).sum())
    return total
def judge(a,full=True):
    changed=a!=h
    checks=dict(finite=bool(np.isfinite(a).all()),no_lowering=not bool((a<h).any()),
        max_raise=float((a-h).max())<=.40001,
        water_faces_exact=not bool((changed&water_support).any()),
        structural_exact=not bool((changed&structural).any()),
        no_remaining_free_lowland=not bool((dry&~fixed&(a<1.8-1e-5)).any()),
        no_unrequested_high_changes=not bool((changed&(h>=1.8-1e-5)).any()),
        r3_exact=not bool((changed&r3).any()),
        historical_consumers_exact=bool(np.max(np.abs(tri_sample(a,coords[:,0],coords[:,1])-tri_sample(h,coords[:,0],coords[:,1])))<1e-6),
        confirmed_residual_at_target=float(tri_sample(a,2718.4852495913565,6812.812873578129))>=1.8-1e-5)
    if full:checks['no_steeper_faces']=slope_fail(a)==0
    return dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks)
result=judge(v)
result['metadata_exact']=all(np.array_equal(t[k],u[k],equal_nan=True) for k in t if k!='heights')
result['roads']=evaluate(v,t['water'].astype(bool))
negative={}
for name,r,c,value in [('residual_restored',912,453,1.52),('bed_moved',912,455,1.5)]:
    a=v.copy();a[r,c]=value;negative[name]=judge(a,False)['status']=='FAIL'
r,c=np.argwhere(structural&dry)[len(np.argwhere(structural&dry))//2]
a=v.copy();a[r,c]+=.1;negative['engineering_changed']=judge(a,False)['status']=='FAIL'
a=v.copy();a[912,453]=np.nan;negative['nonfinite']=judge(a,False)['status']=='FAIL'
negative['unchanged_source_rejected']=judge(h,False)['status']=='FAIL'
result.update(negative=negative,terrain_sha256=sha(dst),source_sha256=sha(src),changed_vertices=int((v!=h).sum()),
    remaining_protected_low_vertices=int((dry&fixed&(v<1.8-1e-5)).sum()),
    residual_before=float(tri_sample(h,2718.4852495913565,6812.812873578129)),
    residual_after=float(tri_sample(v,2718.4852495913565,6812.812873578129)),
    limits=['Protected lowland still open; empirical target does not prove the native shader envelope.',
    'Water faces/physical controls are exact to the C1R3P package that passed 28x62 in engine.'])
result['status']='PASS_OFFLINE_TRANSITION_REPAIR' if result['status']=='PASS' and result['metadata_exact'] and result['roads']['status']=='PASS' and all(negative.values()) else 'FAIL'
(E/'transition-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='roads'},indent=2))
assert result['status']=='PASS_OFFLINE_TRANSITION_REPAIR'
