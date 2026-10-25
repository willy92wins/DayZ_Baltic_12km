"""Bounded fairing of free neighbours around fixed native extrema; retain every rejected group."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, label, find_objects
sys.path.insert(0,str(Path(__file__).resolve().parent))
import despike_v31 as D
import census_pyramids_v31 as P
import census_creases_v31 as C
from repair_free_shapes_ev112 import fair_native_patch
from continuous_stream_pilot_v31 import fair_energy


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def crown_bounds(base, peaks, pits, radius=4):
    """Forbid newly crossing any protected extremum in its native neighbourhood.

    Each (row, col, height) uses local coordinates. Existing higher/lower
    neighbours remain legal; simultaneous peak/pit caps contain the baseline.
    """
    rr,cc=np.indices(base.shape)
    lo=np.full(base.shape,-np.inf);hi=np.full(base.shape,np.inf)
    for points,kind in ((peaks,'peak'),(pits,'pit')):
        for r,c,height in points:
            near=np.hypot(rr-r,cc-c)<=radius
            if kind=='peak':hi[near]=np.minimum(hi[near],np.maximum(base[near],height))
            else:lo[near]=np.maximum(lo[near],np.minimum(base[near],height))
    return lo,hi


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('base',type=Path);ap.add_argument('discovery',type=Path);ap.add_argument('out',type=Path)
    ap.add_argument('--expected-terrain-sha256',required=True);ap.add_argument('--expected-domains-sha256',required=True)
    ap.add_argument('--retain-candidate',type=Path);ap.add_argument('--expected-retained-sha256')
    ap.add_argument('--expected-retained-domains-sha256');ap.add_argument('--hybrid-witnesses',action='store_true')
    a=ap.parse_args();tp=a.base/'terrain-buried.npz';fp=a.base/'bury-work/fp0/footprint.npz';dp=a.discovery/'domains.npz'
    retention_args=(a.retain_candidate,a.expected_retained_sha256,a.expected_retained_domains_sha256)
    if any(retention_args) and not all(retention_args):ap.error('Retained terrain and domains hashes must accompany the retained candidate')
    if a.hybrid_witnesses and not a.retain_candidate:ap.error('Hybrid mode is restricted to failed clusters of a retained candidate')
    solver_path=Path(__file__).with_name('repair_free_shapes_ev112.py').resolve()
    if fair_native_patch.__module__!='repair_free_shapes_ev112' or Path(fair_native_patch.__code__.co_filename).resolve()!=solver_path:
        raise ValueError('Solver substitution is not an authored candidate')
    assert sha(tp)==a.expected_terrain_sha256 and sha(dp)==a.expected_domains_sha256
    discovery=json.loads((a.discovery/'report.json').read_text())
    assert discovery['terrain_sha256']==sha(tp) and discovery['footprint_sha256']==sha(fp)
    a.out.mkdir(parents=True,exist_ok=False)
    z=np.load(tp);arrays={k:z[k] for k in z.files};h0=arrays['heights'].astype(float);h=h0.copy()
    masks=np.load(dp);free=masks['free'];road=masks['road'];shore=masks['shore']
    groups=[g for g in discovery['groups'] if g['independently_feasible']]
    target=np.zeros_like(free);peak_target=np.zeros_like(free);pit_target=np.zeros_like(free)
    for g in groups:
        coords=np.array(g['target_vertices']);target[tuple(coords.T)]=True
        (peak_target if g['kind']=='peak' else pit_target)[tuple(coords.T)]=True
    assert not (target&free).any(), 'This author only handles fixed extrema'
    domain=distance_transform_edt(~target)<=4
    clusters,count=label(domain,structure=np.ones((3,3)))
    pk0,pt0,*_=P.prominence(h0)
    floor=np.minimum(h0,D.lower_floor(arrays,np.load(a.base/'envelope.npy')))
    prior=gaussian_filter(h0,2,mode='nearest')
    reports=[];accepted=np.zeros_like(free);retained=None;previous_changed=np.zeros_like(free);previous_clusters={}
    if a.retain_candidate:
        oldtp=a.retain_candidate/'terrain.npz';oldmp=a.retain_candidate/'domains.npz';oldrp=a.retain_candidate/'report.json'
        if sha(oldtp)!=a.expected_retained_sha256 or sha(oldmp)!=a.expected_retained_domains_sha256:raise ValueError('Retained candidate identity mismatch')
        old_report=json.loads(oldrp.read_text());old_arrays=np.load(oldtp);old_masks=np.load(oldmp)
        if old_report['status']!='PARTIAL_LOCAL_OFFLINE_PASS_PENDING_FULL_VALIDATION' or old_report['input_sha256']!=sha(tp) or old_report['domains_sha256']!=sha(dp) or old_report['output_sha256']!=sha(oldtp) or not old_report['checks'] or not all(old_report['checks'].values()):raise ValueError('Retained candidate provenance failed')
        for key in arrays:
            if key not in ('heights','v31_shape_repair') and not np.array_equal(arrays[key],old_arrays[key],equal_nan=True):raise ValueError('Retained metadata drift')
        h=old_arrays['heights'].astype(float);previous_changed=h!=h0
        if not np.array_equal(previous_changed,old_masks['changed']):raise ValueError('Retained change mask mismatch')
        for key,value in (('free',free),('road',road),('shore',shore),('target',target)):
            if not np.array_equal(old_masks[key],value):raise ValueError('Retained domain mismatch: '+key)
        accepted=old_masks['accepted'].copy()
        if (accepted&~target).any():raise ValueError('Retained acceptance outside target')
        if not np.array_equal(old_arrays['v31_shape_repair'],arrays.get('v31_shape_repair',np.zeros_like(free))|previous_changed):raise ValueError('Retained layer union mismatch')
        previous_clusters={item['cluster']:item for item in old_report['clusters']}
        if set(previous_clusters)!=set(range(1,count+1)):raise ValueError('Retained cluster coverage mismatch')
        pass_mask=np.isin(clusters,[i for i,x in previous_clusters.items() if x['status']=='LOCAL_CHECKS_PASS'])
        if (previous_changed&~pass_mask).any() or not np.array_equal(accepted,target&pass_mask):raise ValueError('Retained cluster masks mismatch')
        retained=dict(terrain_sha256=sha(oldtp),domains_sha256=sha(oldmp),report_sha256=sha(oldrp),groups_applied=old_report['groups_applied'],changed_vertices=int(previous_changed.sum()))
    for ident,sl0 in enumerate(find_objects(clusters),1):
        members=[g for g in groups if clusters[tuple(g['representative'])]==ident]
        assert all((clusters[tuple(np.array(g['target_vertices']).T)]==ident).all() for g in members)
        sl=tuple(slice(max(0,s.start-4),min(h0.shape[axis],s.stop+4)) for axis,s in enumerate(sl0))
        if retained:
            previous=previous_clusters[ident]
            if previous['status']!='SOLVER_FAILED':
                reports.append(dict(previous,inherited=True));continue
            if previous_changed[sl].any():
                reports.append(dict(previous,status='NOT_RETRIED_RETAINED_CONTEXT',reason='Retained terrain intersects the padded solver slice'));continue
        use=free[sl]&(clusters[sl]==ident)
        item=dict(cluster=ident,groups=[dict(kind=g['kind'],representative=g['representative']) for g in members],free_vertices=int(use.sum()))
        if not use.any() or use.sum()>600:
            item['status']='NOT_SOLVED_DOMAIN_BUDGET';reports.append(item);continue
        base=h0[sl];lo=np.maximum(base-.75,floor[sl]);hi=base+.75
        # Every protected extremum within the padded slice participates,
        # including those whose own defect cannot be repaired in this pass.
        peaks=[(r,c,base[r,c]) for r,c in np.argwhere((pk0[sl]>.3)&~free[sl])]
        pits=[(r,c,base[r,c]) for r,c in np.argwhere((pt0[sl]>.3)&~free[sl])]
        crown_lo,crown_hi=crown_bounds(base,peaks,pits)
        lo=np.maximum(lo,crown_lo);hi=np.minimum(hi,crown_hi)
        if (lo[use]>hi[use]).any():
            item['status']='INFEASIBLE_BOUNDS';reports.append(item);continue
        pc=np.maximum(pk0[sl],.2999);tc=np.maximum(pt0[sl],.2999)
        ptarg=peak_target[sl]&(clusters[sl]==ident);ttarg=pit_target[sl]&(clusters[sl]==ident)
        pc[ptarg]=.2999;tc[ttarg]=.2999
        try:
            patch,solve=fair_native_patch(base,prior[sl],use,lo,hi,pc,tc,bound_witnesses=True,preserve_satisfied_witnesses=a.hybrid_witnesses)
        except ValueError as exc:
            item.update(status='SOLVER_FAILED',error=str(exc));reports.append(item);continue
        patch=patch.astype(np.float32).astype(float)
        pk,pt,*_=P.prominence(patch);pb,tb,*_=P.prominence(base)
        before_angles,after_angles=C.angles(base),C.angles(patch)
        checks=dict(fixed_exact=bool(np.array_equal(patch[~use],base[~use])),
                    no_new_overshoot_exact=bool((patch[use]<=crown_hi[use]).all() and (patch[use]>=crown_lo[use]).all()),
                    bounds_respected=bool((patch[use]>=lo[use]-2e-6).all() and (patch[use]<=hi[use]+2e-6).all()),
                    target_clear=bool((pk[ptarg]<=.3).all() and (pt[ttarg]<=.3).all()),
                    no_new_or_worse_faults=not bool(((pk>np.maximum(pb,.3)+2e-6)|(pt>np.maximum(tb,.3)+2e-6)).any()),
                    no_new_or_worse_sharp_edges=all((after_angles[k]<=np.maximum(before_angles[k],20)+.01).all() for k in before_angles),
                    pure_energy_decreased=bool(fair_energy(patch,prior[sl],0)[0]<fair_energy(base,prior[sl],0)[0]))
        item.update(status='LOCAL_CHECKS_PASS' if all(checks.values()) else 'LOCAL_CHECKS_FAIL',checks=checks,solve=solve,
                    pure_energy_before=float(fair_energy(base,prior[sl],0)[0]),pure_energy_after=float(fair_energy(patch,prior[sl],0)[0]))
        reports.append(item)
        if all(checks.values()):
            h[sl][use]=patch[use];accepted[sl]|=ptarg|ttarg
        (a.out/'progress.json').write_text(json.dumps(reports,indent=2)+'\n')
        print(json.dumps(dict(cluster=ident,total=count,status=item['status'],free_vertices=item['free_vertices'])),flush=True)
    h=h.astype(np.float32);changed=h!=h0.astype(np.float32);pk,pt,*_=P.prominence(h)
    up0,lo0=D.tri_slopes(h0);up,low=D.tri_slopes(h.astype(float));angles0,angles=C.angles(h0),C.angles(h.astype(float))
    checks=dict(nonempty=bool(changed.any()),protected_exact=not bool((changed&~free).any()),
                target_heights_exact=bool(np.array_equal(h[target],h0[target])),outside_domain_exact=not bool((changed&~domain).any()),
                roads_exact=not bool((changed&road).any()),shore_edge_vertices_exact=not bool((changed&shore).any()),
                sea_classification_exact=bool(np.array_equal(h<.75,h0<.75)),
                no_new_peak_failures=not bool(((pk>.3)&(pk0<=.3)).any()),no_new_pit_failures=not bool(((pt>.3)&(pt0<=.3)).any()),
                no_worsened_faults=not bool(((pk>np.maximum(pk0,.3)+2e-6)|(pt>np.maximum(pt0,.3)+2e-6)).any()),
                accepted_targets_clear=bool((pk[accepted&peak_target]<=.3).all() and (pt[accepted&pit_target]<=.3).all()),
                slope_guard=not bool(((up>np.maximum(up0,35)+1e-5)|(low>np.maximum(lo0,35)+1e-5)).any()),
                no_new_or_worse_sharp_edges=all((angles[k]<=np.maximum(angles0[k],20)+.01).all() for k in angles0))
    if retained:checks['retained_changes_exact']=bool(np.array_equal(h[previous_changed],old_arrays['heights'][previous_changed]))
    footprint=np.load(fp);water=np.where(np.isfinite(footprint['plane'])[:,:,None],footprint['field'],.75)
    corners=lambda v:np.stack((v[:-1,:-1],v[:-1,1:],v[1:,:-1],v[1:,1:]),axis=-1)
    checks['visual_water_corner_classifications_exact']=bool(np.array_equal(corners(h)<water,corners(h0)<water))
    arrays['heights']=h;arrays['v31_shape_repair']=arrays.get('v31_shape_repair',np.zeros_like(changed))|changed
    np.savez_compressed(a.out/'terrain.npz',**arrays)
    np.savez_compressed(a.out/'domains.npz',free=free,road=road,shore=shore,target=target,accepted=accepted,changed=changed)
    accepted_groups=[g for g in groups if accepted[tuple(g['representative'])]]
    result=dict(status='PARTIAL_LOCAL_OFFLINE_PASS_PENDING_FULL_VALIDATION' if all(checks.values()) else 'FAIL',checks=checks,
                groups_considered=len(groups),groups_applied=len(accepted_groups),peak_groups_applied=sum(g['kind']=='peak' for g in accepted_groups),
                pit_groups_applied=sum(g['kind']=='pit' for g in accepted_groups),clusters=reports,
                changed_vertices=int(changed.sum()),raised_vertices=int((h>h0).sum()),lowered_vertices=int((h<h0).sum()),
                delta_min_m=float((h-h0).min()),delta_max_m=float((h-h0).max()),
                input_sha256=sha(tp),output_sha256=sha(a.out/'terrain.npz'),domains_sha256=sha(dp),author_sha256=sha(__file__),
                solver_sha256=sha(solver_path),retained_candidate=retained,witness_mode='hybrid' if a.hybrid_witnesses else 'bounds',
                scope='Only successfully verified clusters applied. Rejected clusters and all other findings stay open. No forest/binary/runtime/visual acceptance.')
    (a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='clusters'},indent=2))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__=='__main__':main()
