"""Bounded local fairing of free dry native spikes; protected findings stay open."""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter, label, find_objects
from scipy.optimize import minimize, LinearConstraint
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parents[1]/'water')]
import despike_v31 as D
from continuous_stream_pilot_v31 import fair_energy
from shape_repair_constraints_ev112 import s3_road_guard
from native_crease_constraints_ev112 import crease_constraint
import census_creases_v31 as crease


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fair_native_patch(base, prior, free, floor, ceiling, peak_cap, pit_cap, *, bound_witnesses=False):
    """Thin-plate solve with native slope and prominence constraints.

    For each small native shape, retain a baseline witness pair for min/max.
    Bounding that pair is sufficient to bound the shape's prominence, even
    if another vertex becomes its extremum. Final full-grid consumer checks
    still use the independent, unrestricted min/max implementation.
    """
    ids=np.full(base.shape,-1,int);ids[free]=np.arange(free.sum());n=int(free.sum())
    lo=floor[free];hi=ceiling[free];rows=[];upper=[]
    witness_lo=np.where(free,floor,base) if bound_witnesses else base
    witness_hi=np.where(free,ceiling,base) if bound_witnesses else base
    for points,ring in D.rings():
        for r in range(1,base.shape[0]-2):
            for c in range(1,base.shape[1]-2):
                pp=[(r+dr,c+dc) for dr,dc in points];rr=[(r+dr,c+dc) for dr,dc in ring]
                for a,b,cap in ((min(pp,key=lambda q:witness_lo[q]),max(rr,key=lambda q:witness_hi[q]),min(peak_cap[q] for q in pp)),
                                (min(rr,key=lambda q:witness_lo[q]),max(pp,key=lambda q:witness_hi[q]),min(pit_cap[q] for q in pp))):
                    ia,ib=ids[a],ids[b]
                    if ia<0 and ib<0:
                        if bound_witnesses and base[a]-base[b]>cap+1e-9:
                            raise ValueError('Fixed prominence witnesses cannot satisfy the requested cap')
                        continue
                    row=np.zeros(n);constant=0.
                    for q,idx,sgn in ((a,ia,1),(b,ib,-1)):
                        if idx>=0:row[idx]+=sgn
                        else:constant+=sgn*base[q]
                    rhs=cap-constant
                    if np.sum(np.where(row>=0,row*hi,row*lo))>rhs:
                        rows.append(row);upper.append(rhs)
    # Every changed native triangle has both slope components constrained.
    gradx=[];gradz=[];constx=[];constz=[];caps=[]
    for r in range(base.shape[0]-1):
        for c in range(base.shape[1]-1):
            for a,b,d in (((r,c),(r,c+1),(r+1,c+1)),((r,c),(r+1,c),(r+1,c+1))):
                if not any(ids[q]>=0 for q in (a,b,d)):continue
                gx=np.zeros(n);gz=np.zeros(n);cx=cz=0.
                for vec,pair in ((gx,(a,b)),(gz,(b,d))):
                    constant=0.
                    for q,sgn in ((pair[0],-1),(pair[1],1)):
                        if ids[q]>=0:vec[ids[q]]+=sgn/6
                        else:constant+=sgn*base[q]/6
                    if vec is gx:cx=constant
                    else:cz=constant
                gradx.append(gx);gradz.append(gz);constx.append(cx);constz.append(cz)
                caps.append(max(np.tan(np.radians(35))**2,((base[b]-base[a])/6)**2+((base[d]-base[b])/6)**2))
    gx,gz,cx,cz,cap=map(np.asarray,(gradx,gradz,constx,constz,caps))
    def slope_value(x):return cap-(gx@x+cx)**2-(gz@x+cz)**2
    def slope_jac(x):return -2*((gx@x+cx)[:,None]*gx+(gz@x+cz)[:,None]*gz)
    def objective(x):
        h=base.copy();h[free]=x;value,gradient=fair_energy(h,prior)
        return value,gradient[free]
    constraints=[dict(type='ineq',fun=slope_value,jac=slope_jac),crease_constraint(base,free)]
    if rows:constraints.append(LinearConstraint(np.array(rows),-np.inf,np.array(upper)))
    result=minimize(objective,np.clip(base[free],lo,hi),method='SLSQP',jac=True,
                    bounds=list(zip(lo,hi)),constraints=constraints,options={'maxiter':300,'ftol':1e-10})
    if not result.success:raise ValueError(('constrained native fairing failed',str(result.message)))
    h=base.copy();h[free]=result.x
    return h,dict(success=True,iterations=int(result.nit),linear_prominence_constraints=len(rows),native_triangles=len(cap),energy=float(result.fun),witnesses='bounds' if bound_witnesses else 'baseline')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('base',type=Path);p.add_argument('build',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--expected-terrain-sha256',required=True)
    p.add_argument('--expected-footprint-sha256',required=True)
    a=p.parse_args();tp=a.base/'terrain-buried.npz';fp=a.base/'bury-work/fp0/footprint.npz'
    assert sha(tp)==a.expected_terrain_sha256 and sha(fp)==a.expected_footprint_sha256
    a.out.mkdir(parents=True,exist_ok=False)
    z=np.load(tp);arrays={k:z[k] for k in z.files};H0=arrays['heights'].astype(float);H=H0.copy()
    env=np.load(a.base/'envelope.npy')
    shore=D.shoreline_vertices(H0,fp,np.ones_like(H0,bool))
    free,protection,_=D.free_domain(arrays,env,[str(a.build/'records-nonforest.json')],shore)
    road,road_hashes=s3_road_guard();free&=~road
    for k in ('v31_dam','v31_causeway','v31_shore_ramp','v31_continuous_pilot','v31_road_repair','v31_road_mesh_repair'):
        if k in arrays:free&=~arrays[k]
    rr,cc=np.mgrid[:2048,:2048];free&=np.hypot(cc*6.-10397.4,12282.-rr*6.-9421.9)>60
    pond=D.env_vertex_plane(np.load(fp)['plane'])[0]
    pk0,pt0=D.prominence(H0);flagged=free&((pk0>.3)|(pt0>.3))
    # A 24 m neighbourhood, with exact surrounding heights, distributes each
    # correction over native faces instead of clipping a single apex.
    domain=binary_dilation(flagged,iterations=4)&free
    groups,count=label(binary_dilation(domain,iterations=1),structure=np.ones((3,3)))
    floor=np.minimum(H0,D.lower_floor(arrays,env))
    prior=gaussian_filter(H0,2,mode='nearest');solves=[]
    for index,sl0 in enumerate(find_objects(groups),1):
        if sl0 is None:continue
        sl=tuple(slice(max(0,s.start-3),min(2048,s.stop+3)) for s in sl0)
        use=domain[sl]&(groups[sl]==index)
        lo=np.maximum(floor[sl],H0[sl]-.75);hi=H0[sl]+.75
        peak_cap=np.maximum(pk0[sl],.29999);pit_cap=np.maximum(pt0[sl],.29999)
        peak_cap[flagged[sl]]=.29999;pit_cap[flagged[sl]]=.29999
        h,report=fair_native_patch(H0[sl],prior[sl],use,lo,hi,peak_cap,pit_cap)
        H[sl][use]=h[use];solves.append(report)
    H=H.astype(np.float32);changed=H!=H0.astype(np.float32)
    pk,pt=D.prominence(H.astype(float));up0,lo0=D.tri_slopes(H0);up,lo=D.tri_slopes(H.astype(float))
    checks=dict(nonempty_correction=bool(changed.any()),protected_exact=not bool((changed&~free).any()),
                road_triangles_exact=not bool((changed&road).any()),shoreline_edge_endpoints_exact=not bool((changed&shore).any()),
                sea_classification_exact=bool(np.array_equal(H<.75,H0<.75)),
                no_new_peak_failures=not bool(((pk>.3)&(pk0<=.3)).any()),
                no_new_pit_failures=not bool(((pt>.3)&(pt0<=.3)).any()),
                existing_faults_not_worsened=not bool(((pk>np.maximum(pk0,.3)+2e-6)|(pt>np.maximum(pt0,.3)+2e-6)).any()),
                slope_guard=not bool(((up>np.maximum(up0,35)+1e-5)|(lo>np.maximum(lo0,35)+1e-5)).any()),
                targeted_vertices_clear=not bool((flagged&((pk>.3)|(pt>.3))).any()))
    field=np.load(fp)['field'];plane=np.load(fp)['plane']
    visual=np.where(np.isfinite(plane)[:,:,None],field,.75)
    corners=lambda h:np.stack((h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]),axis=-1)
    checks['all_visual_water_corner_classifications_exact']=bool(np.array_equal(corners(H)<visual,corners(H0)<visual))
    before_angles=crease.angles(H0);after_angles=crease.angles(H.astype(float))
    crease_violations={k:int((after_angles[k]>np.maximum(before_angles[k],20)+.01).sum()) for k in before_angles}
    checks['no_new_or_worsened_sharp_edges']=not any(crease_violations.values())
    arrays['heights']=H;arrays['v31_shape_repair']=arrays.get('v31_shape_repair',np.zeros_like(changed))|changed
    np.savez_compressed(a.out/'terrain.npz',**arrays)
    np.savez_compressed(a.out/'domains.npz',free=free,target=flagged,changed=changed,road=road)
    report=dict(status='LOCAL_OFFLINE_PASS' if all(checks.values()) else 'FAIL',checks=checks,
                input_sha256=sha(tp),footprint_sha256=sha(fp),output_sha256=sha(a.out/'terrain.npz'),
                road_reference_hashes=road_hashes,source_sha256=sha(__file__),
                targeted_vertices=int(flagged.sum()),changed_vertices=int(changed.sum()),max_delta_m=float(np.max(np.abs(H-H0))),
                changed_dry_pond_corners=int((changed&pond).sum()),
                crease_violations=crease_violations,
                before=dict(spike_vertices=int((pk0>.3).sum()),pit_vertices=int((pt0>.3).sum())),
                after=dict(spike_vertices=int((pk>.3).sum()),pit_vertices=int((pt>.3).sum())),solves=solves,
                scope='Only free dry native spike/pit neighbourhoods; all other shape findings remain open. No compiled or visual acceptance.')
    (a.out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='solves'},indent=2));sys.exit(0 if all(checks.values()) else 1)


if __name__=='__main__':main()
