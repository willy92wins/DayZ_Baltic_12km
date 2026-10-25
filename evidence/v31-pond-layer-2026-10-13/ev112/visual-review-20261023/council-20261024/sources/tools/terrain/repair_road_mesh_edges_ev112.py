"""Bounded repair of reproduced native-edge P11 failures; isolated candidate.

Retains exact input outside dry 24m discs around the frozen failure inventory.
Uses author barycentric rows; an independent consumer measures native extrema.
No deployment: full water/forest/build gates are still required afterwards.
"""
import argparse,hashlib,json,sys,time
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_dilation,minimum_filter,distance_transform_edt
from scipy.optimize import minimize,linprog
sys.path.insert(0,str(Path(__file__).resolve().parent))
import repair_roads_v30 as R
import verify_roads_v30 as J
import despike_v31 as G
import census_creases_v31 as C
from solve_visual_road_joint_ev112 import Edges
from audit_road_mesh_edges_ev112 import segment_breaks

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def exact_rows(H,free,water):
    lookup=np.full(H.shape,-1,int);lookup[free]=np.arange(free.sum());nv=int(free.sum())
    wd=distance_transform_edt(~water)*6;near=distance_transform_edt(~free)*6;blocks=[];lo=[];hi=[]
    def sample(points):
        r,c,w=R.bary(points[:,0],points[:,1]);iv=lookup[r,c];A=np.zeros((len(points),nv))
        for k in range(3):
            ok=iv[:,k]>=0;A[np.flatnonzero(ok),iv[ok,k]]+=w[ok,k]
        return A,(H[r,c]*w).sum(1)
    def add(A,v,bound):
        touched=np.any(A!=0,axis=1)
        if touched.any():blocks.append(A[touched]);lo.extend((-bound-v)[touched]);hi.extend((bound-v)[touched])
    for p in R.road_chains():
        if len(p)<4:continue
        p=np.asarray(p);s,q,n,length=R.stations(p);s0=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        rr=np.clip(np.rint((12282-q[:,1])/6).astype(int),0,2047);cc=np.clip(np.rint(q[:,0]/6).astype(int),0,2047)
        lim=J.LIMITS
        valid=(wd[rr,cc]>lim['water_clear_m'])&(np.linalg.norm(q-J.NARVA,axis=1)>lim['narva_clear_m'])&(s>lim['end_margin_m'])&(s<length-lim['end_margin_m'])
        # Native triangles touching free vertices lie within 12m of them.
        ix=np.flatnonzero(valid&(near[rr,cc]<18))
        if not len(ix):continue
        # Preserve the complete frozen centre-line chord metric too.
        Ac,vc=sample(q)
        ok=valid[:-1]&valid[1:]
        add(np.diff(Ac,axis=0)[ok],np.diff(vc)[ok],.064*np.diff(s)[ok])
        ok=valid[3:-3]&valid[:-6]&valid[6:]
        add((Ac[3:-3]-.5*(Ac[:-6]+Ac[6:]))[ok],(vc[3:-3]-.5*(vc[:-6]+vc[6:]))[ok],.0295)
        for i in ix:
            _,points=segment_breaks(q[i]-4*n[i],q[i]+4*n[i]);A,v=sample(points)
            # P11 constrains the total range, not twice the centre offset.
            # All pair differences express that range without imposing a
            # fictitious symmetric cross-section on the original terrain.
            u,w=np.triu_indices(len(points),1)
            add(A[u]-A[w],v[u]-v[w],.0295)
        for i in ix:
            if i>=len(s)-1 or not valid[i+1]:continue
            ss=np.r_[s[i],s0[(s0>s[i])&(s0<s[i+1])],s[i+1]]
            qq=np.column_stack([np.interp(ss,s0,p[:,d]) for d in (0,1)])
            for start,end in zip(qq[:-1],qq[1:]):
                _,points=segment_breaks(start,end);A,v=sample(points);lengths=np.linalg.norm(np.diff(points,axis=0),axis=1)
                ok=lengths>1e-8
                add(np.diff(A,axis=0)[ok]/lengths[ok,None],np.diff(v)[ok]/lengths[ok],.064)
    return np.vstack(blocks),np.array(lo),np.array(hi)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('build',type=Path);ap.add_argument('failures',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args()
    B=a.build;out=a.out
    if out.exists():raise FileExistsError(out)
    src=B/'road-merged-20261024-h/terrain-buried.npz';fpath=B/'road-merged-20261024-h/bury-work/fp0/footprint.npz'
    report=json.loads(a.failures.read_text());assert sha(src) in report['inputs'].values() and report['failure_count']>0
    data=dict(np.load(src));H=data['heights'].astype(float);fp=np.load(fpath);wetpath=B/'roads-visual-review-20261024-c/water-vertices.npz';wet=np.load(wetpath)['wet']
    assert J.evaluate(H,wet,report['coverage_sha256'])['coverage_matches_reference']
    pond=G.env_vertex_plane(fp['plane'])[0];shore=G.shoreline_vertices(H,fpath,np.ones_like(H,bool))
    fixed=data['narva']|pond|shore|(H<.9)|G.records_mask([str(B/'records-nonforest.json')])[0]
    for key in ('v31_kit','v31_bridge_cut','v31_bridge_fill','v31_dam','v31_shore_ramp','v31_causeway','v31_continuous_pilot'):
        fixed|=binary_dilation(data[key],iterations=2)
    rr,cc=np.mgrid[:2048,:2048];fixed|=np.hypot(6*cc-10397.4,12282-6*rr-9421.9)<=60
    domain=np.zeros_like(fixed)
    for f in report['failures']:domain|=np.hypot(cc*6-f['x'],12282-rr*6-f['z'])<=24
    free=domain&~fixed
    stagedwet=np.load(B/'forest-visual-consumers-20261024-a/water1m.npy',mmap_mode='r')
    local=minimum_filter(H,size=3)
    for r,c in np.argwhere(free):
        x,z=int(c*6),int(12282-r*6)
        free[r,c]=0<r<2047 and 0<c<2047 and local[r,c]>.9 and not np.isfinite(fp['plane'][r-1:r+1,c-1:c+1]).any() and not stagedwet[12288-z-6:12288-z+6,x-6:x+6].any()
    # Same physical dry-star proof as the previous approved own-road repair;
    # legacy labels are reported, never silently used as actual water evidence.
    nv=int(free.sum());assert nv>0
    A,l,u=exact_rows(H,free,wet);edge=Edges(H,free)
    original_cos=edge.values_jac(np.zeros(nv))[0]+edge.threshold
    original_angles=np.degrees(np.arccos(np.clip(original_cos,-1,1)))
    edge.threshold=np.cos(np.radians(np.maximum(20,original_angles)+.00005))
    def cons(x):
        y=A@x;return np.r_[y-l,u-y,edge.values_jac(x)[0]]
    def jac(x):return np.vstack([A,-A,edge.values_jac(x)[1]])
    start=time.monotonic()
    def callback(x):
        if time.monotonic()-start>240:raise TimeoutError('single solve 240s budget')
    print(json.dumps(dict(vertices=nv,linear=len(l),legacy_water_labels=int((free&data['water']).sum()))),flush=True)
    feasible=linprog(np.zeros(nv),A_ub=np.vstack([A,-A]),b_ub=np.r_[u,-l],bounds=[(-.5,.5)]*nv,method='highs')
    print(json.dumps(dict(linear_feasible=bool(feasible.success),message=feasible.message)),flush=True)
    initial=feasible.x if feasible.success else np.zeros(nv)
    result=minimize(lambda x:float(x@x)/2,initial,jac=lambda x:x,method='SLSQP',
                    constraints=[dict(type='ineq',fun=cons,jac=jac)],bounds=[(-.5,.5)]*nv,callback=callback,
                    options=dict(maxiter=160,ftol=1e-11))
    h=H.copy();h[free]+=result.x;h=h.astype(np.float32).astype(float);changed=h!=H
    before,after=C.angles(H),C.angles(h);reg={k:int((after[k]>np.maximum(20,before[k])+1e-4).sum()) for k in before}
    road=J.evaluate(h,wet,report['coverage_sha256'])
    checks=dict(solver_feasible=bool(cons(h[free]-H[free]).min()>=-1e-5),finite=bool(np.isfinite(h).all()),fixed_exact=not bool((changed&~free).any()),
                no_regressed_sharp_edges=not any(reg.values()),sea_exact=bool(np.array_equal(h<.75,H<.75)),
                dry_stars=bool((minimum_filter(h,size=3)[free]>.9).all()),legacy_p11=road['status']=='PASS')
    out.mkdir(parents=True);data['heights']=h.astype(np.float32);data['v31_road_mesh_repair']=changed;np.savez_compressed(out/'terrain.npz',**data)
    np.savez_compressed(out/'domain.npz',free=free)
    info=dict(status='CANDIDATE_PENDING_INDEPENDENT_MESH_GATE' if all(checks.values()) else 'REJECTED_NOT_INTEGRATED',checks=checks,regressed=reg,solver_success=bool(result.success),
              solver_message=str(result.message),iterations=int(result.nit),min_constraint=float(cons(result.x).min()),
              changed_vertices=int(changed.sum()),delta_range=[float((h-H).min()),float((h-H).max())],
              legacy_water_label_vertices=int((changed&data['water']).sum()),coverage=report['coverage_sha256'],road=road,
              sources={str(p):sha(p) for p in (src,fpath,a.failures,wetpath,Path(__file__))},terrain_sha256=sha(out/'terrain.npz'),
              changes=[dict(row=int(r),col=int(c),before=float(H[r,c]),after=float(h[r,c])) for r,c in np.argwhere(changed)])
    (out/'report.json').write_text(json.dumps(info,indent=2));print(json.dumps({k:v for k,v in info.items() if k not in ('road','changes','sources')},indent=2))
    if not all(checks.values()):raise SystemExit(1)

if __name__=='__main__':main()
