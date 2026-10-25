"""Minimum required vertical delta on frozen V18 geometry, no terrain output."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,time
import numpy as np
from scipy.sparse import load_npz,eye,coo_matrix,hstack,vstack
from scipy.optimize._highspy import _core as hs
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'tests/regional_road_network_v18_constraints';OUT=SOURCE/'minimax-active'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--worker',action='store_true');a=ap.parse_args()
    if not a.worker:
        assert not OUT.exists();OUT.mkdir()
        try:
            r=subprocess.run([sys.executable,'-X','utf8',__file__,'--worker'],capture_output=True,text=True,timeout=650)
            (OUT/'worker.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8');print(r.stdout);print(r.stderr,file=sys.stderr);assert r.returncode==0
        except subprocess.TimeoutExpired:
            (OUT/'timeout.json').write_text(json.dumps(dict(status='INCONCLUSIVE_WALL_BUDGET',seconds=650))+'\n',encoding='utf-8')
        return
    assert sha(SOURCE/'constraints.npz')=='f0e6d9d9e0cc886ed6999457152951217f958268c1480d57ad9c48d7d7d0f15e'
    assert sha(SOURCE/'variables.npz')=='a70d811583dfcf6781eae1f084287f7f37f72ba7e8171e615f4242f5d77fc9f5'
    data=np.load(SOURCE/'variables.npz');B=load_npz(SOURCE/'constraints.npz');rhs=data['rhs'];n=B.shape[1];floor=data['floor']
    active=np.load(ROOT/'tests/regional_road_network_v19/certificate.npz')['active_rows'];I=eye(n,format='csr');col=coo_matrix(-np.ones((n,1)))
    bounds_rows=vstack([hstack([I,col]),hstack([-I,col])],format='csr');lo=np.r_[np.maximum(-12.,floor),0.];hi=np.r_[np.full(n,12.),12.]
    receipt=dict(status='NO_GLOBAL_MINIMUM_PROVEN',constraints_sha256=sha(SOURCE/'constraints.npz'),rounds=[],cap_ceiling_m=12.)
    begin=time.monotonic()
    while time.monotonic()-begin<600:
        available=int(subprocess.check_output(['powershell','-NoProfile','-Command','(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory'],text=True).strip())*1024
        if available<2*1024**3:receipt['stop_reason']='AVAILABLE_MEMORY_BELOW_2GIB';break
        A=vstack([hstack([B[active],coo_matrix((len(active),1))]),bounds_rows],format='csc')
        model=hs.HighsLp();model.num_col_=n+1;model.num_row_=A.shape[0];model.col_cost_=np.r_[np.zeros(n),1.];model.col_lower_=lo;model.col_upper_=hi;model.row_lower_=np.full(A.shape[0],-hs.kHighsInf);model.row_upper_=np.r_[rhs[active],np.zeros(2*n)]
        model.a_matrix_.num_col_=n+1;model.a_matrix_.num_row_=A.shape[0];model.a_matrix_.format_=hs.MatrixFormat.kColwise;model.a_matrix_.start_=A.indptr;model.a_matrix_.index_=A.indices;model.a_matrix_.value_=A.data
        solver=hs._Highs()
        for k,v in [('output_flag',False),('threads',1),('time_limit',max(1.,600-(time.monotonic()-begin))),('primal_feasibility_tolerance',1e-8),('dual_feasibility_tolerance',1e-8)]:assert solver.setOptionValue(k,v)==hs.HighsStatus.kOk
        assert solver.passModel(model)!=hs.HighsStatus.kError
        solver.run();state=solver.getModelStatus();solution=solver.getSolution()
        record=dict(round=len(receipt['rounds']),active_rows=len(active),model_status=solver.modelStatusToString(state),elapsed_s=time.monotonic()-begin)
        if not solution.value_valid:receipt['rounds'].append(record);break
        values=np.asarray(solution.col_value);delta=values[:n];t=float(values[-1]);res=B@delta-rhs
        valid=bool(len(values)==n+1 and np.isfinite(values).all() and np.all(values>=lo-1e-7) and np.all(values<=hi+1e-7) and np.max(abs(delta))<=t+1e-7)
        bad=np.flatnonzero(res>1e-7);record.update(bounds_valid=valid,maximum_full_residual=float(res.max()),violated_original_rows=len(bad),minimum_subproblem_t_m=t)
        receipt['rounds'].append(record);(OUT/'progress.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(record),flush=True)
        if valid and not len(bad):
            receipt.update(status='GLOBAL_MINIMUM_PROVEN_NO_TERRAIN' if state==hs.HighsModelStatus.kOptimal else 'FEASIBLE_UPPER_BOUND_ONLY_NO_TERRAIN',sufficient_cap_m=t,minimum_cap_m=t if state==hs.HighsModelStatus.kOptimal else None)
            ix=data['indices'];top=np.argsort(abs(delta))[-20:][::-1]
            receipt['largest_deltas']=[dict(x_m=int(ix[i]%2048*6),z_m=int(12282-ix[i]//2048*6),delta_m=float(delta[i])) for i in top]
            np.savez_compressed(OUT/'diagnostic-primal.npz',delta=delta,indices=ix,active_rows=active,t=t);break
        new=np.union1d(active,bad)
        if not valid or len(new)==len(active):receipt['stop_reason']='NO_NEW_ROWS_OR_INVALID_PRIMAL';break
        active=new;del solver,model,A
    receipt['elapsed_s']=time.monotonic()-begin
    (OUT/'report.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt))

if __name__=='__main__':main()
