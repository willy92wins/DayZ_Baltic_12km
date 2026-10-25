"""GEOS clipping and vector-heading consumer; never imports the optimizer."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import shapely
from shapely.geometry import box
B=Path(__file__).parent;R=B.parent
sys.path[:0]=[str(R/'v30-native-turn-optimizer-20261009'),str(R/'v30-surface-crease-audit-20261009'),str(R/'v30-low-water-components-20261009')]
from verify_native_turns import geometry,gradient
from audit_native_surface import hinges,incident_any
from discover_components import connected
h=np.load(R/'v30-msta-dry-bank-solve-20261009/candidate/terrain.npz')['heights'].astype(float)
v=np.load(B/'candidate/terrain.npz')['heights'].astype(float)
p=np.load(R/'v30-isolated-basin-repair-20261009/candidate/plane.npy');f=np.load(R/'v30-isolated-basin-repair-20261009/candidate/visible-field.npy')
d=np.load(B/'domain.npz');allowed=d['allowed'];changed=h!=v
r0,c0,r1,c1=1494,2027,1515,2047;extent=box(c0*6,12282-r1*6,c1*6,12282-r0*6);cells=[(r,c) for r in range(r0,r1) for c in range(c0,c1) if np.isfinite(p[r,c])]
def corners(coords,closed):
    q=np.asarray(coords);q=q[:-1] if closed and np.linalg.norm(q[0]-q[-1])<1e-6 else q
    edges=np.diff(np.vstack([q,q[0]]) if closed else q,axis=0)
    headings=np.arctan2(edges[:,1],edges[:,0])
    delta=np.diff(np.r_[headings,headings[0]]) if closed else np.diff(headings)
    return abs((delta+np.pi)%(2*np.pi)-np.pi)
def stats(poly):
    out=shapely.line_merge(poly.boundary.difference(extent.boundary.buffer(.001)))
    lines=[q for q in getattr(out,'geoms',[out]) if q.geom_type=='LineString' and q.length>24]
    report=[]
    for line in lines:
        xy=np.asarray(line.coords);closed=line.is_closed;a=corners(xy,closed)
        if closed:en=float(np.sum(a*a))
        else:
            if tuple(xy[0])>tuple(xy[-1]):line=shapely.reverse(line)
            es=[]
            for phase in [0,.25,.5,.75]:
                points=shapely.line_interpolate_point(line,np.arange(phase,line.length,1.))
                q=shapely.get_coordinates(points);aa=corners(q,False);es.append(float(np.sum(aa*aa)))
            en=float(np.mean(es))
        report.append(dict(closed=closed,length_m=line.length,energy=en,max_corner_degrees=float(np.degrees(a.max()))))
    return sorted(report,key=lambda q:q['closed'])
fields=[np.repeat(p[:,:,None],4,axis=2),f];geos=[]
for field in fields:
    a=geometry(h,field,cells);b=geometry(v,field,cells)
    geos.append(dict(area_before=a.area,area_after=b.area,displacement_m=shapely.hausdorff_distance(a.boundary,b.boundary),before=stats(a),after=stats(b)))
hs=[]
for terrain in [h,v]:
    q=np.concatenate([a[incident_any(allowed,kind)] for kind,a in hinges(terrain)]);hs.append(dict(rms=float(np.sqrt(np.mean(q*q))),over30=int((q>30).sum()),maximum=float(q.max())))
ca=connected(h,p);cb=connected(v,p)
before=geos[1]['before'];after=geos[1]['after']
gates=dict(outside_exact=np.array_equal(h[~allowed],v[~allowed]),fixed_exact=np.array_equal(h[d['fixed']],v[d['fixed']]),all_wet_support_exact=np.array_equal(h[d['wet']],v[d['wet']]),max_delta=abs(v-h).max()<=1.500001,dry_floor=bool(np.all(v[allowed]>=np.minimum(h[allowed],1.8)-1e-6)),areas=all(abs(a['area_after']-a['area_before'])<=.001 for a in geos),displacement=all(a['displacement_m']<=4.1 for a in geos),visible_contour_topology=[a['closed'] for a in before]==[a['closed'] for a in after],angular_energy=all(b['energy']<=.9*a['energy'] for a,b in zip(before,after)),corner_max=max(a['max_corner_degrees'] for a in after)<=max(a['max_corner_degrees'] for a in before)+1e-6,native_rms=hs[1]['rms']<=hs[0]['rms'],slopes=all(np.max(gradient(v,dr,dc)-np.maximum(gradient(h,dr,dc),35))<=1e-4 for dr,dc in [(0,1),(1,0)]),same_active_triangles=np.array_equal(ca[8],cb[8]),same_connections=ca[-1]==cb[-1],solver_converged=json.loads((B/'solver.json').read_text())['success'])
report=dict(status='PASS_INDEPENDENT_GEOMETRY' if all(gates.values()) else 'FAIL_NO_PROMOTION',gates={k:bool(a) for k,a in gates.items()},changed_vertices=int(changed.sum()),max_delta=float(abs(v-h).max()),physical=geos[0],visible=geos[1],native_hinges=hs,terrain_sha256=hashlib.sha256((B/'candidate/terrain.npz').read_bytes()).hexdigest(),limits=['Passing geometry alone does not waive the declared convergence gate.','Native rendering and compiled water coverage are separate gates.'])
(B/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
