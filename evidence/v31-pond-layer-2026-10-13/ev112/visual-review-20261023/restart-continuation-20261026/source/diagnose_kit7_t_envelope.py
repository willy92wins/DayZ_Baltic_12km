"""Necessary feasibility only, from the captured real-author support bounds."""
from pathlib import Path
import hashlib,json
import numpy as np
R=Path(__file__).parent
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
tp=R/'combined-merged/terrain-buried.npz'
bp=R/'river-bounds-next-20261026/kit-7/bounds.npz'
sp=R/'river-kit7-a-on-f-20261026/kit-7-surfaces.npz'
assert sha(tp)=='ab96a8f6fb3da6ca02e566caa1cf5d61ad720d340ec611316c33bcbe2ce717ef'
P=np.load(sp)['axis'];b=np.load(bp)
# Exact author rectangle at continuous_stream_pilot_v31.py:239-240.
r0=max(0,int((12282-P[:,1].max()-42)//6));r1=min(2048,int((12282-P[:,1].min()+42)//6)+2)
c0=max(0,int((P[:,0].min()-42)//6));c1=min(2048,int((P[:,0].max()+42)//6)+2)
t=np.load(tp)['heights'][r0:r1,c0:c1].astype(float)
assert t.shape==b['floor'].shape==b['free'].shape
free=b['free'].copy();free[[0,-1],:]=False;free[:,[0,-1]]=False
lo=np.maximum(b['floor'],t-.75);hi=np.minimum(b['ceiling'],t+.75)
conflict=free&(lo>hi)
rows=[]
for r,c in np.argwhere(conflict):
 rows.append(dict(rc=[int(r+r0),int(c+c0)],xz=[int(c+c0)*6,12282-int(r+r0)*6],T=float(t[r,c]),author_floor=float(b['floor'][r,c]),author_ceiling=float(b['ceiling'][r,c]) if np.isfinite(b['ceiling'][r,c]) else None,intersection_floor=float(lo[r,c]),intersection_ceiling=float(hi[r,c]),shortfall_m=float(lo[r,c]-hi[r,c])))
out=R/'river-kit7-a-run-20261026/t-envelope-feasibility.json';assert not out.exists()
data=dict(status='INFEASIBLE_WITH_FROZEN_SUPPORT_AND_T_ENVELOPE' if rows else 'NECESSARY_BOUNDS_ONLY_PASS',inputs={str(p):sha(p) for p in [tp,bp,sp,Path(__file__)]},slice_rc=[r0,r1,c0,c1],free_vertices=int(free.sum()),conflicts=len(rows),max_shortfall_m=max((q['shortfall_m'] for q in rows),default=0.),rows=rows,limits=['Necessary pointwise condition only, not a coupled feasibility proof.','T +/-0.75 remains unchanged. No terrain/model write, clamp, solver, integration or deployment.','Does not rule out a new approved river design changing the fixed support/axis/level contract.'])
out.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in data.items() if k not in ('rows','inputs')},indent=2))
