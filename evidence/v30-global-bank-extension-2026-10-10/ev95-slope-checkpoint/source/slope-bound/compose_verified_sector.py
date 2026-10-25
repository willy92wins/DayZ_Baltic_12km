"""Materialize the exact full grid evaluated by the passing sector consumer."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent/'focus-unit/author-run-01/candidate-terrain.npz'
BASE_SHA = '30d0ed33e477846297a17e758e34a51490d54ee809e8b63ec9d69229170d15a1'
CONTEXT = (710,970,240,500)
GATES = {
    'fresh_pending_solve_and_resources', 'independent_domain_matrices_bounds_rebuilt',
    'independent_baseline_C_and_order_feasible', 'independent_kkt_closure_objective',
    'float32_bounds_and_D8', 'scalar_slope_face_bounded_from_baseline',
    'retained_499_windows_halo2_and_focus_exact', 'water_civil_P9_exact',
    'P_F_SEA_signs_crossings_within_1m', 'no_new_local_minima',
    'slope_hinge_global_nonregression', 'bank_interior_p99_nonworse',
    'corridor_geometry_covered', 'known_P_depth_ge_0_95', 'unknown_P_preserved',
    'high_navigable_bed_floor_1m', 'seed_improved',
}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()

def require(ok,msg):
    if not ok: raise ValueError(msg)

def read_npz(path):
    with np.load(path,allow_pickle=False) as z: return {k:z[k] for k in z.files}

def main(a):
    require(not a.out.exists(),'Fresh destination required')
    report_sha=sha(a.report)
    require(report_sha==a.report_sha,'Report pin differs')
    r=json.loads(a.report.read_text(encoding='utf-8'))
    require(r['status']=='PASS_EV94_REBASE_SECTOR_OFFLINE_OPEN_P_UNKNOWN','Independent consumer is not PASS')
    require(set(r['gates'])==GATES and all(x is True for x in r['gates'].values()),'Exact seventeen-gate set must pass')
    require(sha(r['consumer_path'])==r['consumer_sha256'],'Evaluated consumer source changed')
    info=r['information']
    require(info['base_sha256']==BASE_SHA and sha(BASE)==BASE_SHA,'Wrong full-grid base')
    require(sha(a.local)==info['candidate_sha256'],'Wrong evaluated local candidate')
    b=read_npz(BASE);c=read_npz(a.local)
    require(c['candidate'].dtype==c['base'].dtype==np.float32 and c['candidate'].shape==(260,260),'Wrong local layout')
    r0,r1,c0,c1=CONTEXT
    require(np.array_equal(c['base'],b['heights'][r0:r1,c0:c1]),'Local base is not focal context')
    changed=np.argwhere(c['candidate']!=c['base'])
    declared={tuple(map(int,x)) for x in c['nodes_local']}
    require(all(tuple(map(int,x)) in declared for x in changed),'Changed fixed local vertex')
    require(len(changed)==info['changed_vertices'],'Changed count differs from independent consumer')
    assembled={k:v.copy() for k,v in b.items()}
    assembled['heights'][r0:r1,c0:c1]=c['candidate']
    require(assembled['heights'][840,370]==b['heights'][840,370],'Focal pin changed')
    a.out.mkdir(parents=True,exist_ok=False)
    target=a.out/'terrain.npz'
    np.savez_compressed(target,**assembled)
    got=read_npz(target)
    require(set(got)==set(b),'Readback field set changed')
    # Verify the written full grid by sparse node composition, independently
    # from the rectangular assignment used above.
    expected=b['heights'].copy()
    global_rc=changed+np.asarray((r0,c0))
    expected[tuple(global_rc.T)]=c['candidate'][tuple(changed.T)]
    for k in b:
        want=expected if k=='heights' else b[k]
        require(got[k].dtype==want.dtype and got[k].shape==want.shape
                and got[k].tobytes()==want.tobytes(),'Sparse readback mismatch: '+k)
    require(sha(a.report)==report_sha and sha(BASE)==BASE_SHA
            and sha(a.local)==info['candidate_sha256'],'Composition input drift')
    receipt={'status':'PASS_EXACT_FULL_GRID_COMPOSITION_OFFLINE',
        'base':{'path':str(BASE),'sha256':BASE_SHA},
        'local':{'path':str(a.local),'sha256':sha(a.local)},
        'independent_report':{'path':str(a.report),'sha256':report_sha,'status':r['status']},
        'consumer_source_sha256':r['consumer_sha256'],
        'candidate':{'path':str(target),'sha256':sha(target),'bytes':target.stat().st_size},
        'changed_vertices_vs_focal':len(changed),'metadata_byte_exact':True,
        'outside_declared_nodes_byte_exact':True,'sparse_readback_exact':True,
        'compiled_water_corners_preserved_by_consumer':info['fixed_support']['water_corners_exact'],
        'map_status':'OPEN_INHERITED_MAP_DEFECTS','native_acceptance':False,'visual_acceptance':False,
        'composer':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)}}
    (a.out/'composition.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True)
    p.add_argument('--report-sha',required=True);p.add_argument('--local',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);main(p.parse_args())
