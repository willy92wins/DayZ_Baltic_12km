from pathlib import Path
import sys,json,hashlib
import numpy as np
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water')]
import census_pyramids_v31 as P,census_creases_v31 as C,streambed_kit_v31 as K
from shape_repair_constraints_ev112 import s3_road_guard
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
base=R/'rectangle-pilot-f-merged/terrain-buried.npz';candidate=R/'river-kit7-a-on-f-20261026/terrain.npz';T=R/'combined-merged/terrain-buried.npz'
assert sha(base)=='caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc'
assert sha(candidate)=='815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40'
assert sha(T)=='ab96a8f6fb3da6ca02e566caa1cf5d61ad720d340ec611316c33bcbe2ce717ef'
z0=np.load(base);z=np.load(candidate);a={k:z0[k] for k in z0.files};h0=a['heights'].astype(float);h=z['heights'].astype(float);t=np.load(T)['heights'].astype(float)
changed=h!=h0
checks={}
for key in z0.files:
 if key not in ('heights','v31_continuous_pilot'):checks['metadata_'+key]=np.array_equal(z[key],z0[key],equal_nan=True)
checks['pilot_mask_exact']=np.array_equal(z['v31_continuous_pilot'],a['v31_continuous_pilot']|changed)
protected={}
for key in ('reserve','platform','narva','v31_bridge_cut','v31_bridge_fill','v31_dam','v31_causeway','v31_shore_ramp','v31_continuous_pilot','v31_road_repair','v31_road_mesh_repair'):
 if key in a:protected[key]=int((changed&a[key]).sum())
fp=np.load(R/'rectangle-pilot-f-merged/bury-work/fp0/footprint.npz')
protected['pond_corners']=int((changed&K.c2v(np.isfinite(fp['plane']))).sum())
road,road_hashes=s3_road_guard();protected['road_triangles']=int((changed&road).sum())
rr,cc=np.mgrid[:2048,:2048];protected['01545_disk60m']=int((changed&(np.hypot(cc*6.-10397.4,12282-rr*6.-9421.9)<=60)).sum())
checks['all_protected_exact']=not any(protected.values())
checks['water_corner_classification_exact']=all(np.array_equal(h[dr:dr+2047,dc:dc+2047]<fp['field'][:,:,j],h0[dr:dr+2047,dc:dc+2047]<fp['field'][:,:,j]) for j,(dr,dc) in enumerate([(0,0),(0,1),(1,0),(1,1)]))
checks['sea_classification_exact']=np.array_equal(h<.75,h0<.75)
checks['prior_F_repairs_exact']=np.array_equal(h[t!=h0],h0[t!=h0])
p0,q0,*_=P.prominence(h0);p,q,*_=P.prominence(h)
newpk=(p>.3)&(p0<=.3);newpt=(q>.3)&(q0<=.3)
edges0=C.angles(h0);edges=C.angles(h)
worse_edges={key:int((value>np.maximum(edges0[key],20)+.01).sum()) for key,value in edges.items()}
row=dict(status='DIAGNOSTIC_NOT_ACCEPTED',inputs={str(x):sha(x) for x in [base,candidate,T,Path(__file__),Path(P.__file__),Path(C.__file__)]},changed_vertices=int(changed.sum()),checks={k:bool(v) for k,v in checks.items()},protected_changes=protected,delta_from_F_max_m=float(abs(h-h0).max()),delta_from_T_max_m=float(abs(h-t).max()),over_T_075_vertices=int((abs(h-t)>.750002).sum()),native_new_peaks=int(newpk.sum()),native_new_pits=int(newpt.sum()),native_worsened_sharp_edges=worse_edges,native_new_peak_locations_rc=np.argwhere(newpk).tolist(),native_new_pit_locations_rc=np.argwhere(newpt).tolist(),road_reference_hashes=road_hashes,limits=['Native substrate diagnostics; saved bed/water may occlude faults, so do not call them visible defects without the independent visibility measurement.','No terrain or model modified by this audit. No build, engine or acceptance claim.','Full footprint regeneration and all consumers still required.'])
out=R/'river-kit7-a-run-20261026/native-guards.json';assert not out.exists();out.write_text(json.dumps(row,indent=2)+'\n')
print(json.dumps({k:v for k,v in row.items() if k not in ('inputs','checks','native_new_peak_locations_rc','native_new_pit_locations_rc','road_reference_hashes')},indent=2))
print('FAILED_CHECKS',[k for k,v in row['checks'].items() if not v])

