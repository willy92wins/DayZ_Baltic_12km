"""One non-overlapping bounded pass of the validated native contour objective."""
from pathlib import Path
import argparse, json, sys, time, traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import shapely
from shapely.geometry import Polygon, box
from scipy.optimize import minimize

B=Path(__file__).parent
B13=Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
sys.path.insert(0,str(B13))
from discover_native_turns import B9,B10,B12,W,sha,graph,positions
from optimize_native_turns import bounds_for,face_constraints
from verify_native_turns import geometry,line_stats
from contour_objective import ContourObjective
SOURCE=Path('E:/DayZ-Baltic-Build/v30-global-contour-pass-20261009/candidate-repaired/terrain.npz')
SOURCE_SHA='223029dedd7122096bb51c704fc722629b2be549f6c946b9cb89c7d1a8b6d6eb'
H=F=P=FIXED=None


def initialize():
    global H,F,P,FIXED
    H=np.load(SOURCE)['heights'].astype(float)
    F=np.load(B12/'preserved-field.npy')
    P=np.load(B10/'frozen-field-reference/plane.npy')
    FIXED=np.load(B/'constraints.npz')['fixed']


def contour_lines(shape,extent):
    line=shapely.line_merge(shape.boundary.difference(extent.boundary.buffer(.001)))
    return [part for part in getattr(line,'geoms',[line]) if part.geom_type=='LineString' and part.length>24]


def local_topology(before,after):
    old=[x for x in getattr(before,'geoms',[before]) if x.geom_type=='Polygon' and x.area>=1]
    new=[x for x in getattr(after,'geoms',[after]) if x.geom_type=='Polygon' and x.area>=1]
    if len(old)!=len(new):return False
    intersections=np.array([[a.intersection(b).area for b in new] for a in old])
    if len(old) and (np.any(intersections.max(1)<.9*np.array([a.area for a in old])) or np.any((intersections>1e-6).sum(0)!=1) or np.any((intersections>1e-6).sum(1)!=1)):return False
    islands=lambda parts:sum(Polygon(r).area>=1 for part in parts for r in part.interiors)
    return islands(new)>=islands(old)


def project_ray(x,objective,h,faces):
    before,_=objective.contour(np.zeros(len(x)));after,_=objective.contour(x)
    displacement=np.linalg.norm(after-before,axis=1);alpha=1.
    d=objective.depth;step=np.einsum('ijk,k->ij',objective.J,x)
    for k in np.flatnonzero(displacement>4.1):
        t0=d[k,0]/(d[k,0]-d[k,1]);t1=(d[k,0]+step[k,0])/(d[k,0]-d[k,1]+step[k,0]-step[k,1])
        length=np.linalg.norm(objective.xy[k,1]-objective.xy[k,0]);target=t0+np.sign(t1-t0)*4.1/length
        limit=(target*(d[k,0]-d[k,1])-d[k,0])/(step[k,0]-target*(step[k,0]-step[k,1]))
        alpha=min(alpha,max(0.,float(limit)))
    lookup={int(v):i for i,v in enumerate(objective.ids)}
    changes=np.array([[x[lookup[int(i)]] if int(i) in lookup else 0. for i in face] for face in faces])
    g=np.diff(h.ravel()[faces],axis=1);s=np.diff(changes,axis=1)
    radius=np.maximum(np.sum(g*g,axis=1),(6*np.tan(np.deg2rad(35)))**2)
    bad=np.sum((g+s)**2,axis=1)>radius
    for gg,ss,rad in zip(g[bad],s[bad],radius[bad]):
        a=float(ss@ss);b=float(2*gg@ss);c=float(gg@gg-rad)
        if a>0:alpha=min(alpha,max(0.,float((-b+np.sqrt(max(0,b*b-4*a*c)))/(2*a))))
    return x*alpha*(1-1e-6),alpha


def solve_tile(job):
    started=time.monotonic();r0,c0,r1,c1=job['box_cells']
    report=dict(row=r0,col=c0,box_cells=job['box_cells'],features=job['features'],status='UNCHANGED',reason=None)
    try:
        ra,ca=max(0,r0-3),max(0,c0-3);rb,cb=min(2047,r1+3),min(2047,c1+3)
        cells=[(r,c) for r in range(ra,rb) for c in range(ca,cb) if np.isfinite(P[r,c])]
        g=graph(H,F,cells)
        if not g['nodes']:report['reason']='no_contour';return report
        assert not g['branch_nodes'] and not g['exact_zero_support']
        support=np.unique(np.array([node['ids'] for node in g['nodes']]).ravel());rr,cc=np.divmod(support,2048)
        ids=support[(rr>r0)&(rr<r1)&(cc>c0)&(cc<c1)&~FIXED.ravel()[support]]
        report['support']=len(support)
        if not len(ids):report['reason']='all_supports_fixed_or_perimeter';return report
        lo,hi,_=bounds_for(ids,H,F,P)
        # Exact physical zero remains zero, not silently reclassified as dry.
        for dr,dc in ((0,0),(0,1),(1,0),(1,1)):
            rr,cc=np.divmod(ids,2048);r,c=rr-dr,cc-dc
            good=(r>=0)&(r<2047)&(c>=0)&(c<2047);j=np.flatnonzero(good)
            zero=H.ravel()[ids[j]]==P[r[j],c[j]];lo[j[zero]]=0;hi[j[zero]]=0
        keep=hi-lo>1e-8;ids,lo,hi=ids[keep],lo[keep],hi[keep];report['variables']=len(ids)
        if not len(ids):report['reason']='bounds_pin_all_supports';return report
        fn=ContourObjective(H,g,ids)
        if not fn.samplers:report['reason']='only_short_chains';return report
        fun,jac,faces=face_constraints(ids,H);last=np.zeros(len(ids));iterations=0
        def callback(x):
            nonlocal last,iterations
            iterations+=1;last=x.copy()
            if time.monotonic()-started>30:raise TimeoutError('30 second block budget')
        try:
            result=minimize(fn,np.zeros(len(ids)),jac=True,method='SLSQP',bounds=list(zip(lo,hi)),
                constraints=[dict(type='ineq',fun=fun,jac=jac)],callback=callback,
                options=dict(maxiter=80,ftol=1e-8,disp=False))
            x=result.x;report['solver_success']=bool(result.success);report['solver_message']=str(result.message)
        except TimeoutError as error:
            x=last;report['solver_success']=False;report['solver_message']=str(error)
        x,alpha=project_ray(x,fn,H,faces);report.update(iterations=iterations,ray_fraction=alpha)
        # Float32 is the consumer terrain, so assess and export those exact values.
        v=H.copy();v.ravel()[ids]=(H.ravel()[ids]+x).astype(np.float32);x=v.ravel()[ids]-H.ravel()[ids]
        report['objective_before']=fn(np.zeros(len(ids)))[0];report['objective_after']=fn(x)[0]
        if report['objective_after']>=report['objective_before']-1e-10:report['reason']='no_objective_improvement';return report
        if np.min(fun(x)) < -1e-5:report['reason']='serialized_slope';return report
        old=geometry(H,F,cells);new=geometry(v,F,cells)
        extent=box(ca*6,12282-rb*6,cb*6,12282-ra*6)
        oldlines=contour_lines(old,extent);newlines=contour_lines(new,extent)
        if not oldlines or not newlines:report['reason']='no_independent_long_contour';return report
        before,after=line_stats(oldlines),line_stats(newlines)
        distance=float(shapely.hausdorff_distance(shapely.union_all(oldlines),shapely.union_all(newlines)))
        report.update(before=before,after=after,hausdorff_m=distance)
        gates=dict(p90=after['p90_degrees']<=before['p90_degrees']+1e-5,
                   over30=after['over30_share']<=before['over30_share']+1e-12,
                   maximum=after['max_degrees']<=before['max_degrees']+1e-5,
                   distance=distance<=4.1,topology=local_topology(old,new))
        report['gates']=gates
        if not all(gates.values()):report['reason']='independent_geometry';return report
        changed=x!=0;report.update(status='INTEGRATE_SOURCE_ONLY',reason=None,ids=ids[changed].tolist(),heights=v.ravel()[ids[changed]].tolist())
        return report
    except Exception as error:
        report.update(status='ERROR_UNCHANGED',reason=str(error),traceback=traceback.format_exc())
        return report
    finally:
        report['seconds']=time.monotonic()-started


def run(workers):
    assert json.loads((B/'derivative-controls.json').read_text())['status']=='PASS_PRODUCTION_DERIVATIVE'
    discovery_data=json.loads((B/'discovery.json').read_text());assert sha(SOURCE)==discovery_data['source_sha256']
    assert not (B/'tiles.jsonl').exists(),'One pass only; do not silently rerun a completed or interrupted candidate'
    started=time.monotonic();results=[];jobs=discovery_data['jobs']
    with (B/'tiles.jsonl').open('w') as log,ProcessPoolExecutor(max_workers=workers,initializer=initialize) as pool:
        pending={pool.submit(solve_tile,job):job for job in jobs}
        for future in as_completed(pending):
            result=future.result();results.append(result);log.write(json.dumps(result)+'\n');log.flush()
            if len(results)%1==0 or len(results)==len(jobs):
                print(json.dumps(dict(done=len(results),total=len(jobs),integrated=sum(r['status']=='INTEGRATE_SOURCE_ONLY' for r in results),errors=sum(r['status']=='ERROR_UNCHANGED' for r in results),seconds=time.monotonic()-started)),flush=True)
            if time.monotonic()-started>1200:
                for other in pending:other.cancel()
                raise TimeoutError('Terminal 20 minute budget. Partial results are not an accepted whole-map pass.')
    data=dict(np.load(SOURCE));h=data['heights'].copy();seen=set()
    for result in results:
        if result['status']!='INTEGRATE_SOURCE_ONLY':continue
        ids=result['ids'];assert not seen.intersection(ids);seen.update(ids)
        h.ravel()[ids]=result['heights']
    data['heights']=h;folder=B/'candidate';folder.mkdir(exist_ok=False)
    np.savez_compressed(folder/'terrain.npz',**data)
    from collections import Counter
    report=dict(status='GLOBAL_CANDIDATE_REQUIRES_INDEPENDENT_GATES',source_sha256=sha(SOURCE),candidate_sha256=sha(folder/'terrain.npz'),
                tiles=len(results),changed_vertices=len(seen),status_counts=dict(Counter(r['status'] for r in results)),
                unchanged_reasons=dict(Counter(r.get('reason') for r in results if r['status']!='INTEGRATE_SOURCE_ONLY')),
                seconds=time.monotonic()-started,workers=workers)
    (B/'authoring.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--discover',action='store_true');parser.add_argument('--run',action='store_true');parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    if args.discover:raise SystemExit("Run discover_terminals.py instead")
    if args.run:run(args.workers)
