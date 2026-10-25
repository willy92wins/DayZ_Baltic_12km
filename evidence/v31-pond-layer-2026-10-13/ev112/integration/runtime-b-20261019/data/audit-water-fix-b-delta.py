"""Independent native-cell, protection and graph-sign checks for the physical margin candidate."""
from pathlib import Path
import numpy as np,json,sys,hashlib
O=Path(__file__).parent;D=O/'water-fix-b';P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(P/'tools/water'));import shore_ramp_v31 as sr
a=np.load(O/'terrain-ev112-c.npz');b=np.load(D/'terrain.npz');h0=a['heights'].astype(float);h=b['heights'].astype(float);ch=h!=h0;rr,cc=np.nonzero(ch)
assert set(zip(rr,cc))=={(796,1721),(963,1876),(631,1685),(324,1135)}
f=np.load(O/'fp-ev112-c/footprint.npz');W,pond=sr.corner_water(f['plane'],f['field'])
other={k:bool(np.array_equal(a[k],b[k],equal_nan=a[k].dtype.kind=='f')) for k in a.files if k!='heights'}
frozen={k:int((ch&a[k].astype(bool)).sum()) for k in ('reserve','platform','narva','v31_bridge_cut','v31_bridge_fill','v31_dam','v31_lagoon')}
corners0=np.stack([h0[:-1,:-1],h0[:-1,1:],h0[1:,:-1],h0[1:,1:]],axis=2);corners=np.stack([h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]],axis=2)
water_signs=np.array_equal(corners0<W,corners<W);sea=np.array_equal(h0<.75,h<.75)
slopes=[]
for r,c in zip(rr,cc):
 for cr in (r-1,r):
  for cl in (c-1,c):
   for ti,ids in enumerate(((0,1,3),(0,3,2))):
    rc=[(cr+(k//2),cl+(k%2)) for k in ids]
    if (r,c) not in rc:continue
    xy=np.array([[cc_*6,12282-rr_*6,1] for rr_,cc_ in rc],float)
    z0=np.array([h0[q] for q in rc]);z=np.array([h[q] for q in rc]);s0=np.linalg.solve(xy,z0);s=np.linalg.solve(xy,z)
    before=float(np.degrees(np.arctan(np.hypot(*s0[:2]))));after=float(np.degrees(np.arctan(np.hypot(*s[:2]))));slopes.append(dict(cell=[int(cr),int(cl)],triangle=ti,before=before,after=after,passed=after<=max(35.,before)+1e-4))
e0=sr.extract_segments(h0,W,pond,f['plane'],320,328,1131,1139);e=sr.extract_segments(h,W,pond,f['plane'],320,328,1131,1139)
shore_exact={k:bool(np.array_equal(e0[k],e[k],equal_nan=e0[k].dtype.kind=='f')) for k in e0}
checks=dict(exactly_four_vertices=int(ch.sum())==4,all_other_arrays_identical=all(other.values()),zero_protected_changes=not any(frozen.values()),protected01545_clear=bool((np.hypot(cc*6-10397.4,12282-rr*6-9421.9)>60).all()),native_pond_sea_corner_signs_identical=water_signs,sea_graph_identical=sea,all_incident_slopes_valid=all(x['passed'] for x in slopes),shore_segments_identical=all(shore_exact.values()))
out=dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks,other_arrays=other,frozen_changed=frozen,shore_segments=shore_exact,incident_triangles=slopes,scope='Exact sign identity at all native water corners preserves wet/dry graph topology; shoreline position is proved identical only around the sea fix. Kit/old-bed pond shoreline and all affected consumers remain separately checked.')
(D/'delta-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(status=out['status'],checks=checks,max_incident_slope=max(x['after'] for x in slopes))));sys.exit(0 if all(checks.values()) else 1)
