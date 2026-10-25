"""Reviewable R3 bank proposal after the bed-only correction failed its slope gate.

Finite linear programme, not another parameter sweep. Heights only decrease,
every mixed native face keeps an axis-wise box inscribed in its permitted slope
circle, and all engineered/corridor vertices remain immutable. The dry nature
bank exception is reported explicitly for decision before any deployment.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy import ndimage,sparse
from scipy.optimize import linprog
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008');E=W/'evidence/v30-curved-channel-pilot-2026-10-08'
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import cell_planes,vertex_plane_bounds
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=B/'flat-profile/terrain_flat.npz';t=dict(np.load(source));h=t['heights'].astype(float)
axes=json.loads(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/axes.json').read_text())
core=np.zeros(h.shape,bool)
for r,c in axes['R3']['removed_cells']:core[r:r+2,c:c+2]=True
mask=dict(np.load(B/'flat-profile/masks.npz'))
pmin,pmax=vertex_plane_bounds(cell_planes(t['cls'],t['level']))
nature=np.load(W.parents[2]/'tests/regional_outline_v1/reference.npz')['reserve'].astype(bool)
dist=ndimage.distance_transform_edt(~core,sampling=6.)
fixed=t['reserve']|t['platform']|mask['corridor']
allowed=(dist<=18)&~fixed&np.isin(t['cls'],(0,6))
rc=list(zip(*np.nonzero(allowed)));idx={v:i for i,v in enumerate(rc)};n=len(rc)
bounds=[]
for r,c in rc:
    floor=1. if t['cls'][r,c]==6 else max(1.4001,float(pmax[r,c]+.0501) if np.isfinite(pmax[r,c]) else 1.4001)
    lower=max(0.,float(h[r,c]-pmin[r,c]+.201)) if core[r,c] and t['cls'][r,c]==6 and np.isfinite(pmin[r,c]) else 0.
    upper=min(1.5,max(0.,float(h[r,c]-floor)))
    assert lower<=upper,(r,c,lower,upper)
    bounds.append((lower,upper))
rows=[];cols=[];values=[];rhs=[];edges={}
def add_edge(u,v,bound):
    key=tuple(sorted((u,v)))
    edges[key]=min(bound,edges.get(key,float('inf')))
for r,c in zip(*np.nonzero(ndimage.binary_dilation(allowed))):
    if not (0<=r<2047 and 0<=c<2047):continue
    for dr,dc in ((0,1),(1,0)):
        vv=[(r,c),(r+dr,c+dc),(r+1,c+1)]
        if not any(t['cls'][v]==0 for v in vv):continue
        dif=np.array([h[vv[1]]-h[vv[0]],h[vv[2]]-h[vv[1]]]);norm=np.linalg.norm(dif)
        factor=max(1.,6*np.tan(np.radians(35))/max(norm,1e-12))
        limit=np.abs(dif)*factor+1e-7
        add_edge(vv[0],vv[1],limit[0]);add_edge(vv[1],vv[2],limit[1])
for (u,v),limit in edges.items():
    if u not in idx and v not in idx:continue
    delta=float(h[v]-h[u])
    for sign in (-1,1):
        k=len(rhs)
        # new difference = old difference + d_u - d_v
        if u in idx:rows.append(k);cols.append(idx[u]);values.append(sign)
        if v in idx:rows.append(k);cols.append(idx[v]);values.append(-sign)
        rhs.append(limit-sign*delta)
A=sparse.csr_matrix((values,(rows,cols)),shape=(len(rhs),n))
cost=np.array([10. if t['cls'][r,c]==0 else 1. for r,c in rc])
solve=linprog(cost,A_ub=A,b_ub=rhs,bounds=bounds,method='highs')
report=dict(status='PROPOSAL_ONLY',success=bool(solve.success),message=solve.message,variables=n,constraints=len(rhs),source_sha256=sha(source))
if solve.success:
    candidate=h.copy()
    for (r,c),d in zip(rc,solve.x):candidate[r,c]=np.float32(h[r,c]-d)
    changed=candidate!=h;dry=changed&(t['cls']==0)
    out=B/'r3-transition-proposal';out.mkdir()
    np.savez_compressed(out/'terrain_flat.npz',**dict(t,heights=candidate.astype(t['heights'].dtype)))
    mask['allowed']|=allowed;mask['frozen']&=~allowed
    np.savez_compressed(out/'masks.npz',**mask)
    report.update(output=str(out/'terrain_flat.npz'),output_sha256=sha(out/'terrain_flat.npz'),
                  changed_vertices=int(changed.sum()),changed_dry_vertices=int(dry.sum()),changed_nature_dry_vertices=int((dry&nature).sum()),
                  max_lower_m=float((h-candidate).max()),max_dry_lower_m=float((h-candidate)[dry].max()) if dry.any() else 0.,
                  roads_platforms_corridors_exact=not bool(np.any(changed&fixed)),metadata_exact=True,
                  changes=[dict(row=int(r),col=int(c),cls=int(t['cls'][r,c]),nature=bool(nature[r,c]),old=float(h[r,c]),new=float(candidate[r,c])) for r,c in zip(*np.nonzero(changed))])
(E/'r3-transition-proposal.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='changes'},indent=2))
