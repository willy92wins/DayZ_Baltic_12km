"""Prepare a reviewable, NOT APPLIED proposal for flat-water shore compatibility."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from scipy.optimize import linprog
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-curved-channel-pilot-2026-10-08'
B=Path(r'E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008')
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import tri_sample
t=dict(np.load(r'E:/DayZ-Baltic-Build/v30-navigation-contract-20261008/terrain_floor.npz'))
h=t['heights'].astype(float);rows=json.loads((E/'flat-samples.json').read_text())
def support(p):
    c=p['x']/6;r=(12282-p['z'])/6;ci=int(c);ri=int(r);fc=c-ci;fr=r-ri
    vals=[(ri,ci,1-fc),(ri,ci+1,fc-fr),(ri+1,ci+1,fr)] if fc>=fr else [(ri,ci,1-fr),(ri+1,ci,fr-fc),(ri+1,ci+1,fc)]
    return [(r,c,v) for r,c,v in vals if v>1e-10]
def state(p):
    return p['old'] is not None and p['old']>p['ground']
def fail(p):
    return p['new'] is not None and (p['new']>p['ground'])!=state(p)
faults=[p for p in rows if fail(p)]
vertices=sorted({(r,c) for p in faults for r,c,v in support(p)})
index={rc:i for i,rc in enumerate(vertices)};n=len(vertices)
A=[];b=[];constraints=[]
for p in rows:
    weights=np.zeros(n)
    for r,c,v in support(p):
        if (r,c) in index:weights[index[(r,c)]]+=v
    if not weights.any() or p['new'] is None:continue
    wet=state(p)
    # Fault locations get 0.201 m margin (existing pond-wave repair target).
    # Other samples retain their original sign; this is not global wave certification.
    target=p['new']+(-.201 if wet else .201) if fail(p) else p['new']+(-1e-6 if wet else 1e-6)
    sign=1 if wet else -1
    A.append(sign*np.r_[weights,-weights]);b.append(sign*(target-p['ground']))
    constraints.append((p,target,wet))
narva=lambda r,c:bool(t['narva'][r,c] or np.hypot(6*c-2417.1428225906,12282-6*r-6889.8850822322)<=620)
def solve(allow_narva):
    bounds=[]
    for r,c in vertices:
        locked=bool(t['reserve'][r,c] or t['platform'][r,c] or (narva(r,c) and not allow_narva))
        bounds.append((0,0 if locked else 1.))
    for r,c in vertices:
        locked=bool(t['reserve'][r,c] or t['platform'][r,c] or (narva(r,c) and not allow_narva))
        maximum=0 if locked else (max(0,h[r,c]-1) if t['cls'][r,c]==3 and h[r,c]>=1 else 1.)
        bounds.append((0,min(1.,maximum)))
    return linprog(np.ones(2*n),A_ub=np.asarray(A),b_ub=np.asarray(b),bounds=bounds,method='highs')
locked=solve(False);proposal=solve(True)
out=dict(status='PROPOSAL_ONLY_NOT_APPLIED',fault_points=len(faults),candidate_vertices=n,
         preserving_narva_feasible=bool(locked.success),preserving_narva_message=locked.message,
         allowing_narva_feasible=bool(proposal.success),allowing_narva_message=proposal.message)
if proposal.success:
    dh=proposal.x[:n]-proposal.x[n:];candidate=h.copy();changed=[]
    for (r,c),d in zip(vertices,dh):
        if abs(d)>1e-8:
            candidate[r,c]=np.float32(h[r,c]+d)
            changed.append(dict(row=r,col=c,x=6*c,z=12282-6*r,old=h[r,c],new=candidate[r,c],delta=candidate[r,c]-h[r,c],
                                narva_protected=narva(r,c),class_id=int(t['cls'][r,c]),
                                road_reserve=bool(t['reserve'][r,c]),platform=bool(t['platform'][r,c])))
    residuals=[((float(tri_sample(candidate,p['x'],p['z']))-target)*(1 if wet else -1)) for p,target,wet in constraints]
    assert max(residuals)<1e-5
    assert not any(v['road_reserve'] or v['platform'] for v in changed)
    path=B/'terrain_flat_shore_proposal.npz';assert not path.exists()
    np.savez_compressed(path,**dict(t,heights=candidate.astype(t['heights'].dtype)))
    out.update(changes=changed,changed_vertices=len(changed),narva_vertices=sum(v['narva_protected'] for v in changed),
               delta_min_max=[min(v['delta'] for v in changed),max(v['delta'] for v in changed)],
               sampled_constraints=len(constraints),max_constraint_residual=max(residuals),
               metadata_unchanged=True,roads_and_platforms_unchanged=True,
               candidate_path=str(path),candidate_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
out['limits']=['No source terrain, WRP, PBO or deployed files changed.',
               'Requires explicit decision on the protected Narva area before implementation.',
               'Minimal point-constrained delta, not completed shore smoothing or full terrain/road/boat validation.',
               'Full water assets, continuous geometry, wave and visual gates must follow any approved implementation.']
(E/'flat-shore-proposal.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='changes'},indent=2))
