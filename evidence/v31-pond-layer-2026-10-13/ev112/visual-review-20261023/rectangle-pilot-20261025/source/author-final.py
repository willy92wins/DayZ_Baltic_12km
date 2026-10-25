"""One bounded offline rectangle pilot, preserving the deployed GuardedE base."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, label

sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parents[1]/'quality'),str(Path(__file__).resolve().parents[1]/'water')]
import despike_v31 as D
import census_pyramids_v31 as P
import census_creases_v31 as C
from continuous_stream_pilot_v31 import fair_energy
from repair_guarded_shapes_ev112 import crown_bounds
from repair_free_shapes_ev112 import fair_native_patch
from shape_patterns_ev112 import rectangle_components


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def signed_limits(base,target):
    d=np.zeros((2,*base.shape))
    d[0,1:-1,1:-1]=base[1:-1,1:-1]-(base[1:-1,:-2]+base[1:-1,2:])/2
    d[1,1:-1,1:-1]=base[1:-1,1:-1]-(base[:-2,1:-1]+base[2:,1:-1])/2
    lower=np.minimum(d,-.2999);upper=np.maximum(d,.2999)
    lower[:,target]=-.2999;upper[:,target]=.2999
    return lower,upper


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('base',type=Path);ap.add_argument('domains',type=Path);ap.add_argument('out',type=Path)
    ap.add_argument('--expected-terrain-sha256',required=True);ap.add_argument('--expected-domains-sha256',required=True)
    a=ap.parse_args();tp=a.base/'terrain-buried.npz';fp=a.base/'bury-work/fp0/footprint.npz'
    if sha(tp)!=a.expected_terrain_sha256 or sha(a.domains)!=a.expected_domains_sha256:raise ValueError('Input identity mismatch')
    solver=Path(__file__).with_name('repair_free_shapes_ev112.py')
    hashes={'author':sha(__file__),'solver':sha(solver),'terrain':sha(tp),'domains':sha(a.domains),'footprint':sha(fp),'envelope':sha(a.base/'envelope.npy')}
    a.out.mkdir(parents=True,exist_ok=False)
    z=np.load(tp);arrays={k:z[k] for k in z.files};h0=arrays['heights'].astype(float)
    masks=np.load(a.domains);free=masks['free'];road=masks['road'];shore=masks['shore']
    before_rectangles=rectangle_components(h0)
    bbox=[906,484,911,490]
    if sum(x['bbox_rc']==bbox for x in before_rectangles)!=1:raise ValueError('Expected pilot rectangle is absent or ambiguous')
    residual=np.zeros_like(h0)
    residual[1:-1,1:-1]=np.maximum(abs(h0[1:-1,1:-1]-(h0[:-2,1:-1]+h0[2:,1:-1])/2),abs(h0[1:-1,1:-1]-(h0[1:-1,:-2]+h0[1:-1,2:])/2))
    labels,_=label(residual>.3,structure=np.ones((3,3)))
    local=labels[906:911,484:490];ids=np.unique(local[local>0])
    if len(ids)!=1:raise ValueError('Pilot component is ambiguous')
    component=labels==ids[0];rr,cc=np.where(component)
    if [int(rr.min()),int(cc.min()),int(rr.max()+1),int(cc.max()+1)]!=bbox:raise ValueError('Pilot component has changed extent')
    domain=distance_transform_edt(~component)<=4
    rr,cc=np.where(domain);sl=(slice(int(rr.min()-4),int(rr.max()+5)),slice(int(cc.min()-4),int(cc.max()+5)))
    if sl[0].start<0 or sl[1].start<0 or sl[0].stop>len(h0) or sl[1].stop>h0.shape[1]:raise ValueError('Pilot padding outside terrain')
    use=free[sl]&domain[sl];base=h0[sl]
    floor=np.minimum(h0,D.lower_floor(arrays,np.load(a.base/'envelope.npy')))
    lo=np.maximum(base-.75,floor[sl]);hi=base+.75
    pk0,pt0,*_=P.prominence(h0)
    peaks=[(r,c,base[r,c]) for r,c in np.argwhere((pk0[sl]>.3)&~free[sl])]
    pits=[(r,c,base[r,c]) for r,c in np.argwhere((pt0[sl]>.3)&~free[sl])]
    crown_lo,crown_hi=crown_bounds(base,peaks,pits)
    lo=np.maximum(lo,crown_lo);hi=np.minimum(hi,crown_hi)
    target=np.zeros_like(h0,bool);target[906:911,484:490]=True
    prior=gaussian_filter(h0,2,mode='nearest')[sl]
    limits=signed_limits(base,target[sl])
    fixture=dict(base=base,prior=prior,free=use,floor=lo,ceiling=hi,peak_cap=np.maximum(pk0[sl],.2999),pit_cap=np.maximum(pt0[sl],.2999))
    np.savez_compressed(a.out/'fixture.npz',**fixture,curvature_lower=limits[0],curvature_upper=limits[1],target=target[sl])
    report=dict(status='STARTED',input_hashes=hashes,bbox_rc=bbox,slice_rc=[[s.start,s.stop] for s in sl],free_vertices=int(use.sum()),protected_extrema={'peaks':len(peaks),'pits':len(pits)},limits=['Offline candidate only; no compiled, runtime, visual or navigation acceptance.'])
    try:
        patch,solve=fair_native_patch(**fixture,bound_witnesses=True,preserve_satisfied_witnesses=True,curvature_bounds=limits)
    except ValueError as exc:
        report.update(status='SOLVER_FAILED',error=str(exc))
        (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report,indent=2));return 1
    h=h0.copy();h[sl][use]=patch[use];h=h.astype(np.float32);changed=h!=h0
    pk,pt,*_=P.prominence(h.astype(float));up0,dn0=D.tri_slopes(h0);up,dn=D.tri_slopes(h.astype(float))
    edges0,edges=C.angles(h0),C.angles(h.astype(float))
    checks=dict(nonempty=bool(changed.any()),protected_exact=not bool((changed&~free).any()),outside_domain_exact=not bool((changed&~domain).any()),roads_exact=not bool((changed&road).any()),shore_exact=not bool((changed&shore).any()),delta_limit=bool(abs(h-h0).max()<=.750002),floor_preserved=bool((h>=floor-2e-6).all()),sea_classification_exact=bool(np.array_equal(h<.75,h0<.75)),no_new_peak_failures=not bool(((pk>.3)&(pk0<=.3)).any()),no_new_pit_failures=not bool(((pt>.3)&(pt0<=.3)).any()),no_worse_prominence=not bool(((pk>np.maximum(pk0,.3)+2e-6)|(pt>np.maximum(pt0,.3)+2e-6)).any()),slope_guard=bool((up<=np.maximum(up0,35)+1e-5).all() and (dn<=np.maximum(dn0,35)+1e-5).all()),sharp_edge_guard=all((edges[k]<=np.maximum(edges0[k],20)+.01).all() for k in edges),protected_crown_exact=bool((h[sl][use]>=crown_lo[use]).all() and (h[sl][use]<=crown_hi[use]).all()),pure_energy_decreased=bool(fair_energy(h[sl].astype(float),prior,0)[0]<fair_energy(base,prior,0)[0]))
    # Independent full-grid axis differences, including stencils centred outside
    # the editable domain. Never validate only the author's list of rows.
    curvature=[]
    for axis in (0,1):
        def diff(v):
            return v[1:-1,1:-1]-(v[1:-1,:-2]+v[1:-1,2:])/2 if axis==0 else v[1:-1,1:-1]-(v[:-2,1:-1]+v[2:,1:-1])/2
        d0=diff(h0);d=diff(h.astype(float));t=target[1:-1,1:-1]
        checks[f'target_stencils_axis_{axis}']=bool((abs(d[t])<=.3).all())
        checks[f'signed_outer_stencils_axis_{axis}']=bool((d[~t]>=np.minimum(d0[~t],-.3)-2e-6).all() and (d[~t]<=np.maximum(d0[~t],.3)+2e-6).all())
        curvature.append(dict(axis=axis,target_max_m=float(abs(d[t]).max()),before_max_m=float(abs(d0[t]).max())))
    water=np.load(fp);level=np.where(np.isfinite(water['plane'])[:,:,None],water['field'],.75)
    corners=lambda v:np.stack((v[:-1,:-1],v[:-1,1:],v[1:,:-1],v[1:,1:]),axis=-1)
    checks['visual_water_corners_exact']=bool(np.array_equal(corners(h)<level,corners(h0)<level))
    after_rectangles=rectangle_components(h)
    checks['only_target_rectangle_removed']=after_rectangles==[x for x in before_rectangles if x['bbox_rc']!=bbox]
    checks['source_identity_unchanged']=hashes['author']==sha(__file__) and hashes['solver']==sha(solver)
    arrays['heights']=h;arrays['v31_shape_repair']=arrays.get('v31_shape_repair',np.zeros_like(changed))|changed
    np.savez_compressed(a.out/'terrain.npz',**arrays)
    np.savez_compressed(a.out/'domains.npz',free=free,road=road,shore=shore,domain=domain,target=target,changed=changed)
    report.update(status='OFFLINE_CANDIDATE_PASS_PENDING_CONSUMERS' if all(checks.values()) else 'CHECKS_FAILED',checks=checks,solve=solve,curvature=curvature,changed_vertices=int(changed.sum()),max_delta_m=float(abs(h-h0).max()),rectangles_before=before_rectangles,rectangles_after=after_rectangles,terrain_sha256=sha(a.out/'terrain.npz'),fixture_sha256=sha(a.out/'fixture.npz'))
    # Existing source-stage consumer contract, bound to the same actual files.
    report.update(input_sha256=hashes['terrain'],output_sha256=report['terrain_sha256'])
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('rectangles_before','rectangles_after')},indent=2))
    return 0 if all(checks.values()) else 1


if __name__=='__main__':sys.exit(main())
