from pathlib import Path
import sys,json,hashlib
import numpy as np
B=Path(__file__).parent;R=B.parent;S=R/'v30-strict-dry-composition-20261009/candidate';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sys.path[:0]=[str(R/'v30-native-turn-optimizer-20261009'),str(R/'v30-surface-crease-audit-20261009'),str(R/'v30-low-water-components-20261009'),str(R/'v30-native-hinge-finish-20261009')]
from verify_native_turns import geometry,gradient
from audit_native_surface import incident_all,incident_any
from verify_hinges import face_normals,edges
from discover_components import connected
a=dict(np.load(S/'terrain.npz'));b=dict(np.load(B/'candidate/terrain.npz'));h=a['heights'].astype(float);v=b['heights'].astype(float);p=np.load(S/'plane.npy');q=np.load(B/'candidate/plane.npy');f=np.load(S/'visible-field.npy');g=np.load(B/'candidate/visible-field.npy');d=np.load(B/'domain.npz');rec=json.loads((B/'authoring.json').read_text());shift=rec['shift_m'];cells=list(zip(*np.nonzero(d['cells'])));nw=[(0,0),(0,1),(1,0),(1,1)]
depth_error=0.;visible_error=0.
# Independent support from all physical/visible positive-depth native triangles.
hv=np.stack([h[dr:dr+2047,dc:dc+2047] for dr,dc in nw],axis=2)
required=np.zeros(f.shape,bool)
for tri in [(0,1,3),(0,2,3)]:
    wet=np.isfinite(p)&(np.maximum(p[:,:,None]-hv,f-hv)[:,:,tri].max(axis=2)>1e-8)
    for k in tri:required[:,:,k]|=wet

for j,(dr,dc) in enumerate(nw):
    hh=h[dr:dr+2047,dc:dc+2047];vv=v[dr:dr+2047,dc:dc+2047];finite=np.isfinite(p)&required[:,:,j]
    depth_error=max(depth_error,float(abs(((q-vv)-(p-hh))[finite]).max()));visible_error=max(visible_error,float(abs(((g[:,:,j]-vv)-(f[:,:,j]-hh))[finite]).max()))
ga=geometry(h,np.repeat(p[:,:,None],4,axis=2),cells);gb=geometry(v,np.repeat(q[:,:,None],4,axis=2),cells);va=geometry(h,f,cells);vb=geometry(v,g,cells)
ca,cb=connected(h,p),connected(v,q);core_error=0.;apron_excess=0.;sharp_excess=0.
for (kind,before),(_,after) in zip(edges(*face_normals(h)),edges(*face_normals(v))):
    core=incident_all(d['core'],kind);apron=incident_any(d['allowed'],kind)&~core
    core_error=max(core_error,float(abs((after-before)[core]).max(initial=0)));apron_excess=max(apron_excess,float((after-before)[apron].max(initial=0)));sharp_excess=max(sharp_excess,float((after-np.maximum(before,10))[apron].max(initial=0)))
expected=a['level'].copy();expected[d['metadata']]+=shift

# Re-evaluate the original local level policy against this actual terrain.
perched_bad=[]; rings=json.loads((R/'v30-low-flowing-support-scope-20261009/volkhov-policy.json').read_text())['all_rings']
allwater=np.zeros(h.shape,bool)
for dr,dc in nw:allwater[dr:dr+2047,dc:dc+2047]|=np.isfinite(p)
for ring in rings:
    r,c=ring['row'],ring['col']; ar,br=max(0,r-10),min(2048,r+12); ac,bc=max(0,c-10),min(2048,c+12)
    rows,cols=np.mgrid[ar:br,ac:bc]; dist=np.hypot(rows-r-.5,cols-c-.5)*6
    mask=(a['cls'][ar:br,ac:bc]==0)&~allwater[ar:br,ac:bc]&~d['fixed'][ar:br,ac:bc]&(dist>ring['inner'])&(dist<=ring['outer'])
    assert int(mask.sum())==ring['vertices']
    old=float(p[r,c]-np.median(h[ar:br,ac:bc][mask])); new=float(q[r,c]-np.median(v[ar:br,ac:bc][mask]))
    if new>max(.3,old)+1e-6:perched_bad.append(dict(row=r,col=c,before=old,after=new))
negatives=dict(stale_terrain_rejected=geometry(h,np.repeat(q[:,:,None],4,axis=2),cells).symmetric_difference(gb).area>.002)
assert all(negatives.values())
gates=dict(converged=rec['solver_success'],perched_policy=not perched_bad,outside_exact=np.array_equal(v[~d['allowed']],h[~d['allowed']]),fixed_exact=np.array_equal(v[d['fixed']],h[d['fixed']]),metadata_exact=np.array_equal(expected,b['level'],equal_nan=True),other_arrays_exact=all(np.array_equal(a[k],b[k],equal_nan=True) for k in a if k not in ['heights','level']),minimum_bed=float(v[d['core']].min())>=1,physical_depth=depth_error<1e-6,visible_depth=visible_error<1e-6,physical_area=ga.symmetric_difference(gb).area<.002,visible_area=va.symmetric_difference(vb).area<.002,components=np.array_equal(ca[8],cb[8]),connections=ca[-1]==cb[-1],slopes=all(np.max(gradient(v,dr,dc)-np.maximum(gradient(h,dr,dc),35))<=1e-4 for dr,dc in [(0,1),(1,0)]),core_angles=core_error<1e-4,apron_angle_increment=apron_excess<=2,apron_new_sharp=sharp_excess<=1e-4)
report=dict(perched_failures=perched_bad,policy_rings=len(rings),negatives=negatives,status='PASS_GEOMETRIC_PROPOSAL_POLICY_PENDING' if all(gates.values()) else 'FAIL_NO_PROMOTION',gates={k:bool(v) for k,v in gates.items()},minimum_bed_m=float(v[d['core']].min()),physical_depth_error_m=depth_error,visible_depth_error_m=visible_error,physical_symmetric_difference_m2=ga.symmetric_difference(gb).area,visible_symmetric_difference_m2=va.symmetric_difference(vb).area,core_angle_error_degrees=core_error,max_apron_angle_increment_degrees=apron_excess,new_sharp_excess_degrees=sharp_excess,terrain_sha256=sha(B/'candidate/terrain.npz'),policy_exception_pending=[647,651],limits=['Independent geometry; depth is preserved on actually wet triangles, and dry faces are checked by GEOS/connectivity. Native and graphics pending.','Prepared proposal; EV61 remains the accepted working baseline pending level-policy exception.'])
(B/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
