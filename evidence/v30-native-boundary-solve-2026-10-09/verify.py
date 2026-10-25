"""Independent clipped-triangle consumer; does not import solve.py or its edge graph."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import shapely
from shapely.geometry import box
R=Path('E:/DayZ-Baltic-Build');B=Path(__file__).parent
sys.path[:0]=[str(R/'v30-native-turn-optimizer-20261009'),str(R/'v30-native-contour-fit-20261009'),str(R/'v30-surface-crease-audit-20261009'),str(R/'v30-low-water-components-20261009')]
from verify_native_turns import geometry,gradient
from check_shape_metric import actual_kinks
from audit_native_surface import hinges,incident_any
from discover_components import connected,area
t=dict(np.load(R/'v30-native-hinge-finish-20261009/candidate/terrain.npz'));v=np.load(B/'candidate/terrain.npz')['heights'].astype(float);h=t['heights'].astype(float);p=np.load(R/'v30-global-water-risk-20261009/frozen-field-reference/plane.npy');f=np.load(R/'v30-frozen-water-stitch-20261009/preserved-field.npy')
d=np.load(R/'v30-area-constrained-bank-20261009/domain.npz');allowed=d['allowed'];fixed=d['fixed'];changed=h!=v
r0,c0,r1,c1=589,2027,610,2047;extent=box(c0*6,12282-r1*6,c1*6,12282-r0*6);cells=[(r,c) for r in range(r0,r1) for c in range(c0,c1) if np.isfinite(p[r,c])]
def lines(poly):
    out=shapely.line_merge(poly.boundary.difference(extent.boundary.buffer(.001)));return [q for q in getattr(out,'geoms',[out]) if q.geom_type=='LineString' and q.length>24]
stats=[]
for terrain in [h,v]:
    q=np.concatenate([vv[incident_any(allowed,kind)] for kind,vv in hinges(terrain)]);stats.append(dict(rms=float(np.sqrt(np.mean(q*q))),over30=int((q>30).sum()),maximum=float(q.max())))
physical_field=np.repeat(p[:,:,None],4,axis=2);a=geometry(h,physical_field,cells);b=geometry(v,physical_field,cells);aa=actual_kinks(lines(a));bb=actual_kinks(lines(b))
vis_a=geometry(h,f,cells);vis_b=geometry(v,f,cells)
gates=dict(outside_exact=np.array_equal(h[~allowed],v[~allowed]),fixed_exact=np.array_equal(h[fixed],v[fixed]),max_delta=abs(v-h).max()<=1.500001,bed_floor=v[allowed].min()>=1,area=abs(b.area-a.area)<=.001,displacement=shapely.hausdorff_distance(a.boundary,b.boundary)<=4.1,corner_max=bb['corner_max_degrees']<=aa['corner_max_degrees']+1e-6,angular_energy=bb['one_metre_turn_square_mean']<=.9*aa['one_metre_turn_square_mean'],native_rms=stats[1]['rms']<=stats[0]['rms'],slopes=all(np.max(gradient(v,dr,dc)-np.maximum(gradient(h,dr,dc),35))<=1e-4 for dr,dc in [(0,1),(1,0)]),terminal_exact=v[600,2037]==h[600,2037])
core=(d['signed']-float(d['offset']))<=-3;gates['core_depth']=np.all(3.425-v[d['rr'][core],d['cc'][core]]>=.3-1e-6)
ca=connected(h,p);cb=connected(v,p);gates['same_active_triangles']=np.array_equal(ca[8],cb[8]);gates['same_connections']=ca[-1]==cb[-1]
numchanged=int(changed.sum());report=dict(status='INDEPENDENT_GEOMETRY_PASS_OPTIMIZER_LIMIT_REMAINS' if all(gates.values()) else 'INDEPENDENT_GEOMETRY_FAIL',gates={k:bool(val) for k,val in gates.items()},changed_vertices=numchanged,max_delta=float(abs(v-h).max()),area_before=a.area,area_after=b.area,hausdorff_m=shapely.hausdorff_distance(a.boundary,b.boundary),physical_before=aa,physical_after=bb,visible_area_before=vis_a.area,visible_area_after=vis_b.area,native_hinges=stats,candidate_sha256=hashlib.sha256((B/'candidate/terrain.npz').read_bytes()).hexdigest(),limits=['Optimizer reached iteration limit; no claim of optimality or numerical convergence.','This consumer proves feasible geometry and quality, not packaged water model coverage or runtime.'])
(B/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
