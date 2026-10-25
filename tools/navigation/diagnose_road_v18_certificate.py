"""One bounded infeasibility certificate for V18; never produce terrain."""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys, time
import numpy as np
from scipy.sparse import load_npz
from scipy.optimize._highspy import _core as hs
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'tests/regional_road_network_v18_constraints'
OUT=SOURCE/'infeasibility-certificate'

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--worker',action='store_true');a=ap.parse_args()
    if not a.worker:
        assert not OUT.exists();OUT.mkdir()
        try:
            r=subprocess.run([sys.executable,'-X','utf8',__file__,'--worker'],capture_output=True,text=True,timeout=210)
            (OUT/'worker.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8');print(r.stdout);print(r.stderr,file=sys.stderr)
            assert r.returncode==0,r.returncode
        except subprocess.TimeoutExpired:
            (OUT/'timeout.json').write_text(json.dumps(dict(status='INCONCLUSIVE_WALL_BUDGET',seconds=210))+'\n',encoding='utf-8')
        return
    assert hashlib.sha256((SOURCE/'constraints.npz').read_bytes()).hexdigest()=='f0e6d9d9e0cc886ed6999457152951217f958268c1480d57ad9c48d7d7d0f15e'
    assert hashlib.sha256((SOURCE/'variables.npz').read_bytes()).hexdigest()=='a70d811583dfcf6781eae1f084287f7f37f72ba7e8171e615f4242f5d77fc9f5'
    available=int(subprocess.check_output(['powershell','-NoProfile','-Command','(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory'],text=True).strip())*1024
    assert available>3*1024**3
    data=np.load(SOURCE/'variables.npz');B=load_npz(SOURCE/'constraints.npz');A=B.tocsc();n=B.shape[1];m=B.shape[0]
    rhs=data['rhs'];floor=data['floor'];lo=np.maximum(-3.,floor);hi=np.full(n,3.)
    model=hs.HighsLp();model.num_col_=n;model.num_row_=m;model.col_cost_=np.zeros(n);model.col_lower_=lo;model.col_upper_=hi;model.row_lower_=np.full(m,-hs.kHighsInf);model.row_upper_=rhs
    model.a_matrix_.num_col_=n;model.a_matrix_.num_row_=m;model.a_matrix_.format_=hs.MatrixFormat.kColwise;model.a_matrix_.start_=A.indptr;model.a_matrix_.index_=A.indices;model.a_matrix_.value_=A.data
    solver=hs._Highs()
    for k,v in [('output_flag',False),('threads',1),('time_limit',150.),('primal_feasibility_tolerance',1e-8),('dual_feasibility_tolerance',1e-8)]:assert solver.setOptionValue(k,v)==hs.HighsStatus.kOk
    assert solver.passModel(model)!=hs.HighsStatus.kError
    begin=time.monotonic();solver.run();state=solver.getModelStatus()
    result=dict(status='INCONCLUSIVE_NO_CERTIFICATE',model_status=solver.modelStatusToString(state),seconds=time.monotonic()-begin,cap_m=3.)
    if state==hs.HighsModelStatus.kInfeasible:
        rs,exists,ray=solver.getDualRay();result.update(ray_status=str(rs),ray_exists=bool(exists))
        if exists:
            y=-np.asarray(ray);combined=np.asarray(B.T@y);bound=float(y@rhs)
            margin=lambda cap:float(np.maximum(combined,0)@np.maximum(-cap,floor)+np.minimum(combined,0).sum()*cap-bound)
            valid=bool(np.all(y>=-1e-9) and margin(3)>1e-7)
            result.update(status='VERIFIED_INFEASIBILITY_CERTIFICATE' if valid else 'INVALID_CERTIFICATE',certificate_verified=valid,nonzero_rows=int(np.count_nonzero(y)),rhs_sum=bound,margin_m=margin(3),maximum_combined_coefficient=float(abs(combined).max()),persists_at_cap_50=margin(50)>1e-7)
            used=np.flatnonzero(abs(combined)>1e-9);ids=data['indices'][used]
            result['dominant_vertices']=[dict(x_m=int(v%2048*6),z_m=int(12282-v//2048*6),coefficient=float(combined[i])) for i,v in zip(used,ids)]
            if valid and margin(50)<=0:
                lower,upper=3.,50.
                for _ in range(60):
                    mid=(lower+upper)/2
                    if margin(mid)>0:lower=mid
                    else:upper=mid
                result['necessary_cap_for_this_certificate_m']=upper
            np.savez_compressed(OUT/'certificate.npz',ray=y,combined=combined,cap=3.)
    (OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))

if __name__=='__main__':main()
