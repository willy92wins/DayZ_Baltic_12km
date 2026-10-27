"""One source-array candidate. Its own assertions are not the consumer verdict."""
from pathlib import Path
import argparse
import importlib.util
import json
import sys
import time
import numpy as np

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--context',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    context=json.loads(args.context.read_text(encoding='utf-8-sig'))
    paths=context['paths'];w=Path(context['worktree']);start=time.monotonic()
    # Reuse only reviewed pure numeric helpers; importing this module does not run it.
    spec=importlib.util.spec_from_file_location('prior_helpers',paths['old_pilot'])
    helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
    helpers.check_expected(context['hashes'])
    args.output.mkdir(exist_ok=False)
    (args.output/'budget.json').write_text(json.dumps(dict(max_seconds=900,max_candidates=1,
        max_iterations=500,weight=.002,source_sha256=context['hashes'][paths['source']],
        plan_sha256=context['hashes'][paths['plan']]),indent=2)+'\n',encoding='utf-8')
    sys.path[:0]=[str(w/'tools/water'),str(w/'tools/terrain')]
    import streambed_kit_v31 as kit
    from shape_repair_constraints_ev112 import s3_road_guard
    with np.load(paths['source'],allow_pickle=False) as f:arrays={k:f[k].copy() for k in f.files}
    bed=arrays['bed'];original=bed[:,:,1].copy();qs=np.unique(np.r_[np.arange(-18,19,dtype=float),-2.25,2.25])
    assert original.shape==(1663,39) and np.array_equal(original,np.rint(original*512)/512)
    with np.load(paths['base'],allow_pickle=False) as base:
        keys=('reserve','platform','narva','v31_bridge_cut','v31_bridge_fill','v31_dam','v31_causeway','v31_shore_ramp')
        protected=np.logical_or.reduce([base[k] for k in keys])
        for key in ('v31_road_repair','v31_road_mesh_repair','v31_continuous_pilot'):
            if key in base.files:protected|=base[key]
    guard,refs=s3_road_guard();protected|=guard
    assert refs==helpers.read(Path(paths['author_report']))['road_reference_hashes']
    with np.load(paths['footprint'],allow_pickle=False) as f:protected|=kit.c2v(np.isfinite(f['plane']))
    rr,cc=np.mgrid[:2048,:2048];protected|=np.hypot(cc*6.-10397.4,12282-rr*6.-9421.9)<=60
    with np.load(paths['support'],allow_pickle=False) as f:H=f['heights'].astype(float)
    ground=kit.tri_h(H,bed[:,:,0],bed[:,:,2]);touch=kit.tri_h(protected.astype(float),bed[:,:,0],bed[:,:,2])>0
    # Historical provenance check covers only the domain the original author floored.
    historical=np.broadcast_to((abs(qs)>4)&(abs(qs)<18),original.shape).copy()
    historical[[0,-1],:]=False;historical&=~touch
    lower=helpers.support_rounding_lower_bound(H,bed[:,:,0],bed[:,:,2],ground)
    if np.any(original[historical]<lower[historical]+.02-1/1024-2e-6):
        raise ValueError('historical support provenance mismatch')
    cap=np.minimum(arrays['station'],arrays['station'][-1]-arrays['station'])<=6
    free=np.broadcast_to((abs(qs)>2.25)&(abs(qs)<18),original.shape).copy()
    free[cap,:]=False;free&=~touch
    floor=ground+.02;water=np.broadcast_to(arrays['level'][:,None],original.shape)
    floor=np.where(original>=water+.025,np.maximum(floor,water+.025),floor)
    infeasible=free&(floor>original);free&=~infeasible
    quant_bad=free&(np.ceil(floor*512)>np.floor(original*512));free&=~quant_bad
    prior=original.copy()
    for side in (-1,1):
        ii=int(np.flatnonzero(qs==side*2.25)[0]);oo=int(np.flatnonzero(qs==side*18)[0])
        cols=np.flatnonzero((qs*side>2.25)&(qs*side<18));t=(abs(qs[cols])-2.25)/15.75
        prior[:,cols]=original[:,ii,None]*(1-t)+original[:,oo,None]*t
    functions=helpers.historical_functions(Path(paths['author']))
    if np.any(free):values,solver=functions['fair_support'](original,prior,free,floor,original)
    else:values=original.copy();solver=dict(success=True,message='NO_FREE_POINTS',iterations=0)
    candidate,valid=helpers.quantize_bounded(values,original,free,floor,original)
    assert np.array_equal(free,valid)
    assert np.array_equal(candidate[~free],original[~free])
    outbed=bed.copy();outbed[:,:,1]=candidate;arrays['bed']=outbed
    np.savez_compressed(args.output/'candidate-surfaces.npz',**arrays)
    faces=functions['strip_faces'](*original.shape);points=[]
    for row in helpers.read(Path(paths['attribution']))['rows']:
        heights=[]
        for old in row['all_candidates']:
            vertices=faces[old['triangle']]
            assert np.array_equal(bed.reshape(-1,3)[vertices],np.array(old['triangle_vertices']))
            heights.append(float(np.array(old['weights'])@outbed.reshape(-1,3)[vertices,1]))
        y=max(heights)
        points.append(dict(mesh=row['mesh'],query=row['query'],index=row['index'],xz=row['xz'],
            previous_failed=row['failed'],candidate_surface_y=y,baseline_surface_y=row['native_roadway_y'],
            delta_y=y-row['native_roadway_y'],difference_to_OLD_nav_y=abs(y-row['navigation_y']),NOT_NATIVE_VERDICT=True))
    helpers.check_expected(context['hashes']);helpers.check_expected(refs)
    if time.monotonic()-start>=900:raise TimeoutError('candidate budget exhausted')
    report=dict(status='AUTHORED_PENDING_INDEPENDENT_CHECK',solver=solver,seconds=time.monotonic()-start,
        candidate_sha256=helpers.sha(args.output/'candidate-surfaces.npz'),free_points=int(free.sum()),
        infeasible_fixed=int(infeasible.sum()),no_quantized_value_fixed=int(quant_bad.sum()),points=points,
        context_sha256=helpers.sha(args.context),inputs_unchanged=True)
    (args.output/'author-report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='points'}))

if __name__=='__main__':main()
