"""Recheck the original lake-bank consumer on the current terrain, without another terrain proposal."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.ndimage import distance_transform_edt
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/terrain'))
from relevel_bodies_v30 import label_bodies
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/candidate/terrain.npz')
after=Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz')
assert sha(before)=='70f74c9334620c458880f728d3ff15cec7867ffe2bd8bd2e9d5135e1692b7ed5'
assert sha(after)=='fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6'
t=dict(np.load(before));u=dict(np.load(after));h=t['heights'].astype(float);v=u['heights'].astype(float)
assert set(t)==set(u) and all(np.array_equal(t[k],u[k],equal_nan=True) for k in t if k!='heights')
ids=label_bodies(t['cls'],t['level']);prior=json.loads((W/'evidence/v30-lake-bank-proposal-2026-10-09/proposal.json').read_text())
def curvature(a,mask):
    xx=(a[1:-1,:-2]-2*a[1:-1,1:-1]+a[1:-1,2:])/36
    zz=(a[:-2,1:-1]-2*a[1:-1,1:-1]+a[2:,1:-1])/36
    xz=(a[2:,2:]-a[2:,:-2]-a[:-2,2:]+a[:-2,:-2])/144
    return float(np.sqrt(np.mean((xx*xx+zz*zz+2*xz*xz)[mask[1:-1,1:-1]])))
reports=[]
for q in prior['lakes']:
    x,z=q['anchor_xz'];r,c=round((12282-z)/6),round(x/6);body=int(ids[r,c]);assert body==q['body']
    mask=ids==body;dist=distance_transform_edt(~mask,sampling=6)
    bank=(dist>0)&(dist<=36)&(t['cls']==0);ring=(dist>12)&(dist<=36)&(t['cls']==0)
    old=curvature(h,bank);new=curvature(v,bank);assert abs(old-q['before_curvature'])<1e-12
    p90a=float(np.percentile(h[bank],90));p90b=float(np.percentile(v[bank],90))
    reports.append(dict(name=q['name'],historical_nominal_body=body,anchor_xz=[x,z],nominal_level_m=q['level_m'],
        water_vertices_exact=bool(np.array_equal(h[mask],v[mask])),bank_vertices=int(bank.sum()),changed_bank_vertices=int((bank&(h!=v)).sum()),
        before_curvature=old,current_curvature=new,curvature_reduction=1-new/old,before_bank_p90=p90a,current_bank_p90=p90b,
        original_shape_gate=(1-new/old)>=.10 and p90b<=p90a,
        current_water_minus_dry_ring_median_m=q['level_m']-float(np.median(v[ring]))))
result=dict(status='CURRENT_LAKE_RECHECK_NO_POLICY_CHANGE',inputs={str(p):sha(p) for p in [before,after]},lakes=reports,
    limits=['Historical bank consumer reapplied to EV25, not a new smoothing attempt.','Nominal cls/level bodies identify the lake scope only; they do not assert hydraulic connectivity.',
            'The earlier EV19 rejected proposal remains rejected. This recheck neither changes nor approves the two reserved lake levels.'])
(B/'deferred-lakes-current.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
