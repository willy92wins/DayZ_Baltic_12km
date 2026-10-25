"""One global dry-land pass, preserving EV112 water and engineered surfaces.

This is the non-kit part of the approved general relief review. Kit, bridges,
shore corrections, Narva, reserve/platforms and 015-45 are fixed, not accepted
by exclusion. Uses the already measured 12m EV97 smoothing scale. A bounded
pullback rejects new >20-degree native creases; 20 is a diagnostic guard, not
the aesthetic acceptance of the map. Runtime and forest reseating are later.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter,distance_transform_edt,binary_dilation
sys.path.insert(0,str(Path(__file__).resolve().parent))
import despike_v31 as despike
import census_creases_v31 as crease


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sharp_vertices(bad):
    """All corners of either triangle incident to a rejected native edge."""
    A=bad['diagonal'].copy();B=A.copy()
    A[:,:-1]|=bad['east'];B[:,1:]|=bad['east']
    B[:-1]|=bad['south'];A[1:]|=bad['south']
    return despike.tri_to_vertices(A,B)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build');ap.add_argument('out');ap.add_argument('--pilot-terrain');a=ap.parse_args()
    root=Path(a.build);out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    tp=root/'water-fix-b/terrain.npz';fp_path=root/'water-fix-b/bury-work/fp0/footprint.npz';ep=root/'dam/envelope-dam.npy'
    assert sha(tp)=='07054c46ebf2861bc905fe2d68fb3b734d7b8e9ad1d538c73a7ee745edd56d62'
    z=np.load(tp);arrays={k:z[k] for k in z.files};H0=arrays['heights'].astype(float);env=np.load(ep)
    assert np.isfinite(H0).all(),'non-finite source terrain'
    records=root/'records-nonforest.json';assert records.is_file()
    shore=despike.shoreline_vertices(H0,fp_path,np.ones_like(H0,bool))
    free,protections,_=despike.free_domain(arrays,env,[str(records)],shore)
    for k in ('v31_causeway','v31_shore_ramp','v31_dam'):
        free&=~binary_dilation(arrays[k],iterations=2)
    rr,cc=np.mgrid[:2048,:2048];disk=np.hypot(6*cc-10397.4,12282-6*rr-9421.9)<=60;free&=~disk
    fp=np.load(fp_path);pond=despike.env_vertex_plane(fp['plane'])[0];free&=~pond
    pilot_guard=np.zeros_like(free)
    if a.pilot_terrain:
        pilot=np.load(a.pilot_terrain)['heights'];assert pilot.shape==H0.shape
        pilot_guard=binary_dilation(pilot!=H0,iterations=3);free&=~pilot_guard
    floor=np.minimum(H0,despike.lower_floor(arrays,env))
    dry=H0>=.8
    smooth=gaussian_filter(np.where(dry,H0,0.),2,mode='nearest')/np.maximum(gaussian_filter(dry.astype(float),2,mode='nearest'),1e-9)
    angle0=crease.angles(H0);limits={k:np.maximum(20,v)+1e-4 for k,v in angle0.items()};pullbacks=[]
    eligible=free.copy();rejected=np.zeros_like(free)
    for iteration in range(13):
        w=np.clip(distance_transform_edt(eligible)/4,0,1);w=w*w*(3-2*w)
        H=np.maximum(H0+w*(smooth-H0),floor);H[~eligible]=H0[~eligible]
        H=H.astype(np.float32).astype(float);angles=crease.angles(H)
        bad={k:v>limits[k] for k,v in angles.items()};count=sum(int(v.sum()) for v in bad.values())
        pullbacks.append(dict(iteration=iteration,regressed_sharp_edges=count))
        if not count:break
        # Retire the failing collar and recompute the SAME global pass with a
        # smooth ramp around it. Pointwise half-reverts made a new sharp seam.
        affected=sharp_vertices(bad)&eligible
        rejected|=binary_dilation(affected,iterations=3)&free
        eligible=free&~rejected
    H=H.astype(np.float32).astype(float);angles=crease.angles(H)
    violations=sum(int((v>limits[k]).sum()) for k,v in angles.items())
    changed=H!=H0;affected=crease.pair_union(*crease.tri_any(changed))
    diagnostics={k:dict(affected_edges=int(affected[k].sum()),before_over20=int(((angle0[k]>20)&affected[k]).sum()),
                        after_over20=int(((v>20)&affected[k]).sum()),max_before=float(angle0[k][affected[k]].max()),
                        max_after=float(v[affected[k]].max())) for k,v in angles.items()}
    checks=dict(finite_heights=bool(np.isfinite(H).all()),frozen_exact=not bool((changed&~free).any()),shoreline_exact=not bool((changed&shore).any()),
                pond_corners_exact=not bool((changed&pond).any()),protected_01545_exact=not bool((changed&disk).any()),
                sea_classification_exact=bool(np.array_equal(H<.75,H0<.75)),no_regressed_sharp_edges=violations==0)
    checks['pilot_collar_exact']=not bool((changed&pilot_guard).any())
    arrays['heights']=H.astype(np.float32);arrays['v31_relief_general']=changed
    np.savez_compressed(out/'terrain.npz',**arrays)
    report=dict(schema='ev112-global-free-relief-v1',status='OFFLINE_PASS' if all(checks.values()) else 'FAIL',
                author_sha256=sha(__file__),terrain_input_sha256=sha(tp),terrain_sha256=sha(out/'terrain.npz'),
                footprint_sha256=sha(fp_path),envelope_sha256=sha(ep),records_sha256=sha(records),
                checks=checks,sigma_m=12,free_vertices=int(free.sum()),changed_vertices=int(changed.sum()),
                change_range_m=[float((H-H0).min()),float((H-H0).max())],native_edges=diagnostics,pullbacks=pullbacks,
                retired_regression_collar_vertices=int(rejected.sum()),
                pilot_terrain=(dict(path=a.pilot_terrain,sha256=sha(a.pilot_terrain)) if a.pilot_terrain else None),
                limitations=['Protected defects and kits are still open, not accepted by exclusion.','Pond regeneration, forest support, build and visual view pending.'])
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
    assert all(checks.values())


if __name__=='__main__':main()
