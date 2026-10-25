"""Separate Narva bathymetry layer for the approved sea-to-dam finish.

Only the already cut 33 cells may supply candidate vertices. All 21 previous
contract vertices and all upstream pond corners stay exact. The old contract
is evidence of the earlier layer; it is not rewritten to approve this one.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.ndimage import label
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import dam_v31 as dam


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build');ap.add_argument('out');ap.add_argument('--terrain')
    a=ap.parse_args();B=Path(a.build);out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    contract=HERE.parents[1]/'evidence/v31-pond-layer-2026-10-13/dam/frozen-exception-narva.json'
    assert sha(contract)=='28191cce4fe4ec7f240bbaf14cc7a07546748a98fdaa5221661b1649150668a2'
    con=json.loads(contract.read_text());tp=Path(a.terrain) if a.terrain else B/'water-fix-b/terrain.npz'
    z=np.load(tp);arrays={k:z[k] for k in z.files};H0=arrays['heights'].astype(float);H=H0.copy()
    fp=np.load(B/'water-fix-b/bury-work/fp0/footprint.npz');pond=np.isfinite(fp['plane']);pond_vertices=dam.c2v_any(pond)
    old_contract=np.zeros_like(H,bool)
    for v in con['vertices']:old_contract[v['r'],v['c']]=True
    candidates=np.zeros_like(H,bool)
    for cell in con['cut_cells']:
        r,c=cell['r'],cell['c'];candidates[r:r+2,c:c+2]=True
    frozen=old_contract|pond_vertices|arrays['reserve']|arrays['platform']
    allowed=candidates&~frozen
    report=json.loads((B/'dam/dam-report.json').read_text());site=report['sites'][0]
    front=report['model']['vis_max'][2];assert abs(front-2.0388801097869873)<1e-8
    axis_row=(12282-6942)//6
    # Keep the cross-dam ridge intact. The first seaward vertex is solved from
    # the actual NW-SE plane to target 0.25 at grid columns. Cross-cell
    # variation is measured separately against reference sea 0.75.
    for r,c in np.argwhere(allowed):
        assert 12282-6*r>6942
        target=-.5
        if r==axis_row-1:
            target=min(target,H0[axis_row,c]+(.25-H0[axis_row,c])*6/front)
        H[r,c]=min(H0[r,c],target)
    arrays['heights']=H.astype(np.float32);H=arrays['heights'].astype(float);changed=H!=H0
    arrays['v31_narva_seaward']=changed
    vertices=[dict(r=int(r),c=int(c),x=int(c*6),z=int(12282-r*6),old=float(H0[r,c]),new=float(H[r,c]),delta=float(H[r,c]-H0[r,c])) for r,c in np.argwhere(changed)]
    # Every new submerged vertex must join already existing sea, never become
    # an inland pocket. The NW-SE adjacency matches the actual native mesh.
    conn=np.array([[1,1,0],[1,1,1],[0,1,1]]);wet0=H0<.75;wet=H<.75;lab,n=label(wet,conn)
    old_ids=set(np.unique(lab[wet0]))-{0};new_ids=set(np.unique(lab[wet&~wet0]))-{0}
    xs=np.arange(2400,2460.001,.25);face=dam.height_grid(H,xs,np.full_like(xs,6942+front))
    mats=[dam.record_matrix(x,site['origin_y'],z,site['bearing']) for x,z in site['pieces']]
    seats=[dam.seat(lambda x,z:dam.height(H,x,z),m,[-1] if i==0 else [1],site['level']) for i,m in enumerate(mats)]
    baseline_seats=[dam.seat(lambda x,z:dam.height(H0,x,z),m,[-1] if i==0 else [1],site['level']) for i,m in enumerate(mats)]
    # Independent barrier: the unchanged continuous ridge across the wall sits
    # above the upstream pond. Lowering the sea side cannot open a wet route.
    crest=dam.height_grid(H,np.arange(2394,2460.001,.25),np.full(265,6942.))
    checks=dict(delta_inside_old_cut_vertices=not bool((changed&~candidates).any()),
                old_21_vertices_exact=bool(np.array_equal(H[old_contract],H0[old_contract])),
                upstream_pond_corners_exact=bool(np.array_equal(H[pond_vertices],H0[pond_vertices])),
                reserve_platform_exact=not bool((changed&(arrays['reserve']|arrays['platform'])).any()),
                front_below_reference_sea=bool((face<.75).all()),
                new_sea_joins_existing=bool(new_ids<=old_ids and new_ids),
                wet_ridge_closed=bool((crest>site['level']).all()),
                no_gap_below_wall=all(s['bottom_clearance_min']>.1 for s in seats),
                lateral_seats_exact=all(s['end_exposure']==b['end_exposure'] for s,b in zip(seats,baseline_seats)))
    np.savez_compressed(out/'terrain.npz',**arrays)
    result=dict(schema='narva-seaward-layer-v1',status='OFFLINE_PASS' if all(checks.values()) else 'FAIL',
                author_sha256=sha(__file__),terrain_input=str(tp),terrain_input_sha256=sha(tp),terrain_sha256=sha(out/'terrain.npz'),
                old_contract_sha256=sha(contract),approval='Guillermo picker: mar hasta el pie de la presa, tierra solo en apoyos laterales',
                checks=checks,changed_vertices=len(vertices),vertices=vertices,seats=seats,baseline_seats=baseline_seats,
                front_sample_count=len(face),front_height_range=[float(face.min()),float(face.max())],
                ridge_min=float(crest.min()),new_sea_vertices=int((wet&~wet0).sum()),
                limitations=['Reference sea 0.75m; runtime tide and view pending.','Bury/footprint regeneration and final integration still required.','Old dam layer gates remain historical, not silently redefined.'])
    (out/'layer-report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('vertices','baseline_seats')},indent=2))
    assert all(checks.values())


if __name__=='__main__':main()
