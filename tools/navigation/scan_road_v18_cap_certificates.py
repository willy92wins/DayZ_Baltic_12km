"""Certificate-guided feasibility diagnosis; no ASC or deployed terrain writes."""
from pathlib import Path
import argparse,hashlib,json,math,subprocess,sys,time
import numpy as np
from scipy.sparse import load_npz
from scipy.optimize._highspy import _core as hs
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'tests/regional_road_network_v18_constraints';OUT=SOURCE/'cap-certificate-scan'

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--worker',action='store_true');a=ap.parse_args()
    if not a.worker:
        assert not OUT.exists();OUT.mkdir()
        try:
            r=subprocess.run([sys.executable,'-X','utf8',__file__,'--worker'],capture_output=True,text=True,timeout=650)
            (OUT/'worker.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8');print(r.stdout);print(r.stderr,file=sys.stderr)
            if r.returncode:raise RuntimeError(r.returncode)
        except subprocess.TimeoutExpired:
            (OUT/'timeout.json').write_text(json.dumps(dict(status='GLOBAL_WALL_BUDGET_STOP',seconds=650))+'\n',encoding='utf-8');print('GLOBAL_WALL_BUDGET_STOP')
        return
    assert hashlib.sha256((SOURCE/'constraints.npz').read_bytes()).hexdigest()=='f0e6d9d9e0cc886ed6999457152951217f958268c1480d57ad9c48d7d7d0f15e'
    available=int(subprocess.check_output(['powershell','-NoProfile','-Command','(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory'],text=True).strip())*1024;assert available>3*1024**3
    d=np.load(SOURCE/'variables.npz');B=load_npz(SOURCE/'constraints.npz');A=B.tocsc();n=B.shape[1];m=B.shape[0];cap=4.;floor=d['floor'];lo=np.maximum(-cap,floor);hi=np.full(n,cap)
    model=hs.HighsLp();model.num_col_=n;model.num_row_=m;model.col_cost_=np.zeros(n);model.col_lower_=lo;model.col_upper_=hi;model.row_lower_=np.full(m,-hs.kHighsInf);model.row_upper_=d['rhs']
    model.a_matrix_.num_col_=n;model.a_matrix_.num_row_=m;model.a_matrix_.format_=hs.MatrixFormat.kColwise;model.a_matrix_.start_=A.indptr;model.a_matrix_.index_=A.indices;model.a_matrix_.value_=A.data
    solver=hs._Highs()
    for k,v in [('output_flag',False),('threads',1),('primal_feasibility_tolerance',1e-8),('dual_feasibility_tolerance',1e-8)]:assert solver.setOptionValue(k,v)==hs.HighsStatus.kOk
    assert solver.passModel(model)!=hs.HighsStatus.kError
    begin=time.monotonic();steps=[];status='NO_FEASIBLE_CAP_PROVEN';necessary=3.877806675469233
    while time.monotonic()-begin<600 and cap<=12:
        solver.setOptionValue('time_limit',min(120.,600-(time.monotonic()-begin)))
        started=time.monotonic();solver.run();state=solver.getModelStatus();record=dict(cap_m=cap,model_status=solver.modelStatusToString(state),seconds=time.monotonic()-started)
        if state!=hs.HighsModelStatus.kInfeasible:
            sol=solver.getSolution()
            if sol.value_valid:
                delta=np.asarray(sol.col_value);residual=float(np.max(B@delta-d['rhs']))
                valid=len(delta)==n and np.isfinite(delta).all() and np.all(delta>=lo-1e-7) and np.all(delta<=hi+1e-7) and residual<=1e-7
                record.update(primal_verified=bool(valid),maximum_residual=residual)
                if valid:status='FEASIBLE_CAP_BRACKET_NO_TERRAIN';np.savez_compressed(OUT/'diagnostic-primal.npz',delta=delta,indices=d['indices'],cap=cap)
            steps.append(record);break
        ray_status,exists,ray=solver.getDualRay();record.update(ray_status=str(ray_status),ray_exists=bool(exists))
        if not exists:steps.append(record);break
        y=-np.asarray(ray);combined=np.asarray(B.T@y);rhs=float(y@d['rhs'])
        def margin(value):return float(np.maximum(combined,0)@np.maximum(-value,floor)+np.minimum(combined,0).sum()*value-rhs)
        valid=bool(np.all(y>=-1e-9) and margin(cap)>1e-7);record.update(certificate_verified=valid,margin=margin(cap),nonzero_rows=int(np.count_nonzero(y)))
        used=np.flatnonzero(abs(combined)>1e-9);ids=d['indices'][used]
        record['dominant_vertices']=[dict(x_m=int(v%2048*6),z_m=int(12282-v//2048*6),coefficient=float(combined[i])) for i,v in zip(used,ids)]
        np.savez_compressed(OUT/f'certificate-{len(steps):02d}.npz',ray=y,combined=combined,cap=cap)
        if not valid or margin(50)>0:steps.append(record);break
        lower,upper=cap,50.
        for _ in range(60):
            mid=(lower+upper)/2
            if margin(mid)>0:lower=mid
            else:upper=mid
        necessary=max(necessary,upper);nextcap=math.ceil((upper+.01)*4)/4
        record.update(necessary_cap_for_certificate_m=upper,next_cap_m=nextcap,negative_controls=dict(inverted_sign_rejected=bool(np.any(-y<-1e-9)),relaxed_rhs_rejected=margin(cap)-(abs(margin(cap))+1)<0,larger_bound_no_longer_contradicted=margin(nextcap)<=1e-7))
        assert all(record['negative_controls'].values())
        steps.append(record);(OUT/f'step-{len(steps):02d}.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in record.items() if k!='dominant_vertices'}),flush=True)
        if nextcap<=cap+.001 or nextcap>12:break
        cap=nextcap;lo=np.maximum(-cap,floor);hi=np.full(n,cap)
        assert solver.changeColsBounds(n,np.arange(n,dtype='int32'),lo,hi)!=hs.HighsStatus.kError
    report=dict(status=status,elapsed_s=time.monotonic()-begin,necessary_cap_lower_bound_m=necessary,sufficient_cap_upper_bound_m=cap if status.startswith('FEASIBLE_') else None,steps=steps,limit='Diagnostic height-cap bracket only; no terrain generated or accepted.')
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='steps'}))

if __name__=='__main__':main()
