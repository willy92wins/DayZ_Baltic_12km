"""One bounded L1 solve on frozen V18 geometry with a wider lateral transition, with a justified 3m edit cap."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,time
import numpy as np
import rasterio
from scipy.sparse import load_npz,eye,coo_matrix,hstack,vstack
from scipy.ndimage import distance_transform_edt
from scipy.optimize._highspy import _core as hs
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'tests/regional_road_network_v18_constraints';OUT=ROOT/'tests/regional_road_network_v18'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--worker',action='store_true');a=ap.parse_args()
    if not a.worker:
        assert not OUT.exists();OUT.mkdir()
        try:
            r=subprocess.run([sys.executable,'-X','utf8',__file__,'--worker'],capture_output=True,text=True,timeout=650)
            (OUT/'worker-stdout.log').write_text(r.stdout,encoding='utf-8');(OUT/'worker-stderr.log').write_text(r.stderr,encoding='utf-8')
            print(r.stdout);print(r.stderr,file=sys.stderr)
            if r.returncode:raise RuntimeError(f'Solver worker exit {r.returncode}')
        except subprocess.TimeoutExpired:
            if not (OUT/'solve.json').exists():(OUT/'solve.json').write_text(json.dumps(dict(status='STOPPED_WALL_BUDGET_NO_ACCEPTANCE',wall_budget_s=650))+'\n',encoding='utf-8')
            print('STOPPED_WALL_BUDGET_NO_ACCEPTANCE')
        return
    assert sha(SOURCE/'constraints.npz')=='f0e6d9d9e0cc886ed6999457152951217f958268c1480d57ad9c48d7d7d0f15e'
    parent=ROOT/'tests/regional_foundation_combined_v10/reference.npz'
    assert sha(parent)=='a43cb0f128c17318207a114f94f08801ff35a81af5d36a4b7e3427dd3d6aca2d'
    ref=np.load(parent);h=ref['candidate'];variables=np.load(SOURCE/'variables.npz');ix=variables['indices'];B=load_npz(SOURCE/'constraints.npz');rhs=variables['rhs'];n=B.shape[1];I=eye(n,format='csr')
    A=vstack([hstack([B,coo_matrix((B.shape[0],n))]),hstack([I,-I]),hstack([-I,-I])],format='csc')
    available=int(subprocess.check_output(['powershell','-NoProfile','-Command','(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory'],text=True).strip())*1024
    required=2*1024**3+4*(A.data.nbytes+A.indices.nbytes+A.indptr.nbytes);assert available>=required,(available,required)
    cap=3.;lo=np.maximum(-cap,variables['floor']);hi=np.full(n,cap)
    receipt=json.loads((SOURCE/'solve.json').read_text(encoding='utf-8'))
    for key in ['success','message','elapsed_s','vertex_delta_limit_m']:receipt.pop(key,None)
    receipt.update(status='FROZEN_V18_SOLVE_PENDING',maximum_allowed_delta_m=cap,parent_solver=str(SOURCE),constraint_source_sha256=sha(SOURCE/'constraints.npz'),variables_source_sha256=sha(SOURCE/'variables.npz'),available_memory_bytes=available,required_memory_bytes=required)
    (OUT/'pre-solve.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    model=hs.HighsLp();model.num_col_=2*n;model.num_row_=A.shape[0];model.col_cost_=np.r_[np.zeros(n),np.ones(n)];model.col_lower_=np.r_[lo,np.zeros(n)];model.col_upper_=np.r_[hi,np.full(n,hs.kHighsInf)];model.row_lower_=np.full(A.shape[0],-hs.kHighsInf);model.row_upper_=np.r_[rhs,np.zeros(2*n)]
    model.a_matrix_.num_col_=2*n;model.a_matrix_.num_row_=A.shape[0];model.a_matrix_.format_=hs.MatrixFormat.kColwise;model.a_matrix_.start_=A.indptr;model.a_matrix_.index_=A.indices;model.a_matrix_.value_=A.data
    solver=hs._Highs()
    for key,value in [('output_flag',False),('threads',1),('time_limit',600.),('primal_feasibility_tolerance',1e-8),('dual_feasibility_tolerance',1e-8)]:assert solver.setOptionValue(key,value)==hs.HighsStatus.kOk
    load_status=solver.passModel(model);assert load_status!=hs.HighsStatus.kError
    begin=time.monotonic();solver.run();state=solver.getModelStatus();solution=solver.getSolution()
    receipt.update(model_load_status=str(load_status),model_status=solver.modelStatusToString(state),elapsed_s=time.monotonic()-begin,solver_value_valid=bool(solution.value_valid),status='STOPPED_NO_CANDIDATE')
    feasible=False
    if solution.value_valid:
        values=np.asarray(solution.col_value);delta=values[:n]
        feasible=bool(len(values)==2*n and np.isfinite(values).all() and np.all(delta>=lo-1e-7) and np.all(delta<=hi+1e-7) and np.max(B@delta-rhs)<=1e-7)
        receipt.update(independent_primal_feasible=feasible,maximum_residual=float(np.max(B@delta-rhs)),maximum_delta_m=float(abs(delta).max()))
    if feasible:
        candidate=h.copy();candidate.ravel()[ix]=(h.ravel()[ix].astype(float)+delta).astype('float32');support=variables['support'];changed=candidate!=h;assert not np.any(changed&~support)
        asc=OUT/'baltic_road_network_v18.asc'
        with asc.open('w',encoding='ascii',newline='\n') as f:
            f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n');np.savetxt(f,candidate,fmt='%.9g')
        with rasterio.open(asc) as ds:assert np.array_equal(candidate,ds.read(1))
        rr,cc=np.mgrid[:2048,:2048];wd=distance_transform_edt(~(ref['wet']|ref['ocean']))*6
        allowed=(wd>30)&~ref['fairway_support']&(np.hypot(cc*6-2417.1428225906,12282-rr*6-6889.8850822322)>480)
        arrays={k:ref[k] for k in ref.files};arrays.update(candidate=candidate,parent=h,changed=candidate!=ref['base'],pilot_support=support,pilot_allowed=allowed)
        np.savez_compressed(OUT/'reference.npz',**arrays)
        receipt.update(status='SOLVER_OPTIMAL_CANDIDATE_NOT_ACCEPTED' if state==hs.HighsModelStatus.kOptimal else 'SOLVER_FEASIBLE_NOT_OPTIMAL_NOT_ACCEPTED',asc_sha256=sha(asc),changed_vertices=int(changed.sum()),max_delta_m=float(abs(candidate-h).max()),vertex_delta_limit_m=cap,native_float32_constraint_residual=float(np.max(B@(candidate.ravel()[ix].astype(float)-h.ravel()[ix])-rhs)))
    (OUT/'solve.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in receipt.items() if k!='routes'}))

if __name__=='__main__':main()
