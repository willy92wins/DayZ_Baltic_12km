"""Read-only discriminator for candidate river support and inactive water layers."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.spatial import cKDTree
import shapely
R=Path(__file__).parent;C=R/'river-kit7-a-on-f-20261026';F=R/'rectangle-pilot-f-merged'
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
sha=lambda p:hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
paths=[C/'terrain.npz',C/'kit-7-surfaces.npz',C/'envelope.npy',C/'cover.npy',F/'envelope.npy',F/'cover.npy',F/'bury-work/fp0/footprint.npz',R/'combined-merged/terrain-buried.npz',B.parent/'bridges/terrain-ev107.npz',R/'river-bounds-next-20261026/kit-7/bounds.npz']
inputs={str(p):sha(p) for p in paths}
assert inputs[str(C/'terrain.npz')]=='815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40'
assert inputs[str(F/'bury-work/fp0/footprint.npz')]=='95f7a26304e88c726679ec69ef076bb149ec1f1f8bdf4a6cd1e83e40f3b6be83'
assert inputs[str(R/'combined-merged/terrain-buried.npz')]=='ab96a8f6fb3da6ca02e566caa1cf5d61ad720d340ec611316c33bcbe2ce717ef'
report=json.loads((C/'author-report.json').read_text());assert inputs[str(B.parent/'bridges/terrain-ev107.npz')]==report['reference_terrain_sha256']
z=np.load(C/'kit-7-surfaces.npz');P=z['axis'];bed=z['bed'];tree=cKDTree(P)
bounds=np.load(R/'river-bounds-next-20261026/kit-7/bounds.npz')
diag=json.loads((R/'river-kit7-a-run-20261026/t-envelope-feasibility.json').read_text());r0,r1,c0,c1=diag['slice_rc'];sl=np.s_[r0:r1,c0:c1]
rows,cols=np.mgrid[r0:min(r1,2047),c0:min(c1,2047)]
dist=tree.query(np.c_[cols.ravel()*6+3,12282-rows.ravel()*6-3])[0].reshape(rows.shape)
pond=np.isfinite(np.load(F/'bury-work/fp0/footprint.npz')['plane'])
retire=np.zeros_like(pond);retire[r0:min(r1,2047),c0:min(c1,2047)]=(dist<42)&~pond[r0:min(r1,2047),c0:min(c1,2047)]
checks={};layers={}
for name in ('envelope.npy','cover.npy'):
 before=np.load(F/name);after=np.load(C/name);expected=before.copy();expected[retire]=np.nan
 checks[name+'_only_authorized_inactive_retirement']=bool(np.array_equal(after,expected,equal_nan=True))
 checks[name+'_all_current_pond_cells_exact']=bool(np.array_equal(after[pond],before[pond],equal_nan=True))
 change=~((before==after)|(np.isnan(before)&np.isnan(after)))
 layers[name]=dict(changed_cells=int(change.sum()),changed_active_pond_cells=int((change&pond).sum()))
H=np.load(C/'terrain.npz')['heights'];T=np.load(R/'combined-merged/terrain-buried.npz')['heights'];ref=np.load(B.parent/'bridges/terrain-ev107.npz')['heights']
rr,cc=np.nonzero(abs(H.astype(float)-T)>.750002);xy=np.c_[cc*6,12282-rr*6]
# Both diagonal halves of the saved bed ribbon, independently intersected in XZ.
tri=np.concatenate([np.stack([bed[:-1,:-1],bed[1:,:-1],bed[1:,1:]],axis=-2).reshape(-1,3,3),np.stack([bed[:-1,:-1],bed[1:,1:],bed[:-1,1:]],axis=-2).reshape(-1,3,3)])
polys=shapely.polygons(tri[:,:,[0,2]]);index=shapely.STRtree(polys)
point_idx,tri_idx=index.query(shapely.points(xy),predicate='intersects')
v=tri[tri_idx];q=xy[point_idx];a=v[:,0,[0,2]];u=v[:,1,[0,2]]-a;w=v[:,2,[0,2]]-a;d=q-a
det=u[:,0]*w[:,1]-u[:,1]*w[:,0];assert np.all(abs(det)>1e-12)
s=(d[:,0]*w[:,1]-d[:,1]*w[:,0])/det;t=(u[:,0]*d[:,1]-u[:,1]*d[:,0])/det
height=v[:,0,1]+s*(v[:,1,1]-v[:,0,1])+t*(v[:,2,1]-v[:,0,1])
covered=np.zeros(len(rr),bool);covered[point_idx]=True
under=np.zeros(len(rr),bool);under[point_idx[H[rr[point_idx],cc[point_idx]]<=height+.00001]]=True
highest=np.full(len(rr),-np.inf);np.maximum.at(highest,point_idx,height)
above=covered&~under
above_rows=[dict(rc=[int(rr[j]),int(cc[j])],xz=xy[j].tolist(),terrain=float(H[rr[j],cc[j]]),bed=float(highest[j]),gap_m=float(H[rr[j],cc[j]]-highest[j])) for j in np.flatnonzero(above)]
free=bounds['free'].copy();free[[0,-1],:]=False;free[:,[0,-1]]=False
Tlocal=T[sl].astype(float);lower=np.maximum(bounds['floor'],Tlocal-.75);upper=np.minimum(bounds['ceiling'],Tlocal+.75);conflict=free&(lower>upper)
data=dict(status='READ_ONLY_SCOPE_DISCRIMINATOR',inputs=inputs,checks=checks,layers=layers,retired_eligible_cells=int(retire.sum()),over_T_075_vertices=len(rr),over_T_075_inside_saved_bed=int(covered.sum()),over_T_075_below_saved_bed=int(under.sum()),over_T_075_outside_saved_bed=int((~covered).sum()),over_T_075_inside_but_above_saved_bed=int((covered&~under).sum()),envelope_conflicts=int(conflict.sum()),ceiling_driven_conflicts=int((conflict&(Tlocal-.75>bounds['ceiling'])).sum()),floor_driven_conflicts=int((conflict&(bounds['floor']>Tlocal+.75)).sum()),reference_ev107_free_delta_T_max_m=float(abs(ref[sl].astype(float)-Tlocal)[free].max()),reference_ev107_free_outside_T_075=int((free&(abs(ref[sl].astype(float)-Tlocal)>.750002)).sum()),limits=['Saved surface projection and barycentric heights at native vertices only; not continuous occlusion or compiled visibility.','The T +/-0.75 test is conditional relief-envelope comparison, not original river author acceptance.','Layer comparison validates only authorized retirement of inactive cells. New water footprint, coverage and topology still need regeneration.','No geometry, terrain, envelope, cover or deployed file modified.'])
data['source_sha256']=sha(Path(__file__))
data['inside_but_above_saved_bed_rows']=above_rows
data['inside_but_above_saved_bed_max_gap_m']=max((row['gap_m'] for row in above_rows),default=0.)
assert inputs=={str(p):sha(p) for p in paths}
out=R/'river-kit7-a-run-20261026/layers-and-cover-v2.json';assert not out.exists();out.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({k:v for k,v in data.items() if k!='inputs'},indent=2));assert all(checks.values())
