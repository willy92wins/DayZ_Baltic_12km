"""Bounded read-only HiGHS infeasible-subsystem extraction on frozen road data."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,time
import numpy as np
from scipy.sparse import load_npz
from scipy.optimize._highspy import _core as hs

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--worker',action='store_true');ap.add_argument('--ray',action='store_true');a=ap.parse_args();assert not a.out.exists()
    if not a.worker:
        try:
            r=subprocess.run([sys.executable,'-X','utf8',__file__,'--folder',str(a.folder),'--out',str(a.out),'--worker']+(['--ray'] if a.ray else []),capture_output=True,text=True,timeout=330)
            print(r.stdout);print(r.stderr,file=sys.stderr)
            if r.returncode:raise RuntimeError(f'Worker exit {r.returncode}')
        except subprocess.TimeoutExpired:
            if not a.out.exists():a.out.write_text(json.dumps(dict(status='DIAGNOSIS_TIMEOUT_NO_CERTIFICATE',wall_budget_s=330))+'\n',encoding='utf-8')
            print(a.out.read_text(encoding='utf-8'))
        return
    available=int(subprocess.check_output(['powershell','-NoProfile','-Command','(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory'],text=True).strip())*1024
    assert available>3*1024**3,available
    data=np.load(a.folder/'variables.npz');B=load_npz(a.folder/'constraints.npz');A=B.tocsc();n=B.shape[1];m=B.shape[0]
    original=json.loads((a.folder/'solve.json').read_text(encoding='utf-8'));cap=original['maximum_allowed_delta_m']
    lo=np.maximum(-cap,data['floor']);hi=np.full(n,cap)
    model=hs.HighsLp();model.num_col_=n;model.num_row_=m;model.col_cost_=np.zeros(n);model.col_lower_=lo;model.col_upper_=hi;model.row_lower_=np.full(m,-hs.kHighsInf);model.row_upper_=data['rhs']
    model.a_matrix_.num_col_=n;model.a_matrix_.num_row_=m;model.a_matrix_.format_=hs.MatrixFormat.kColwise;model.a_matrix_.start_=A.indptr;model.a_matrix_.index_=A.indices;model.a_matrix_.value_=A.data
    solver=hs._Highs()
    for key,value in [('output_flag',False),('threads',1),('time_limit',300.),('primal_feasibility_tolerance',1e-8),('dual_feasibility_tolerance',1e-8)]:assert solver.setOptionValue(key,value)==hs.HighsStatus.kOk,key
    # Match SciPy's installed wrapper: kWarning is accepted, kError is not.
    load_status=solver.passModel(model);assert load_status!=hs.HighsStatus.kError,str(load_status)
    start=time.monotonic();solver.run();state=solver.getModelStatus()
    report=dict(status='READ_ONLY_FEASIBILITY_DIAGNOSIS',model_load_status=str(load_status),model_status=solver.modelStatusToString(state),elapsed_s=time.monotonic()-start,matrix_sha256=hashlib.sha256((a.folder/'constraints.npz').read_bytes()).hexdigest(),available_memory_bytes=available)
    print(json.dumps(report),flush=True)
    if state==hs.HighsModelStatus.kInfeasible and a.ray:
        ray_status,exists,ray=solver.getDualRay()
        report.update(ray_status=str(ray_status),ray_exists=bool(exists),elapsed_s=time.monotonic()-start)
        if exists:
            y=-np.asarray(ray);combined=np.asarray(B.T@y);rhs=float(y@data['rhs']);floor=data['floor']
            def margin(cap):return float(np.sum(np.maximum(combined,0)*np.maximum(-cap,floor)+np.minimum(combined,0)*cap)-rhs)
            valid=bool(np.all(y>=-1e-9) and margin(cap)>1e-7)
            used=np.flatnonzero(y!=0);variables=np.flatnonzero(combined!=0)
            np.savez_compressed(a.out.with_suffix('.npz'),ray=y,combined=combined,rows=used)
            report.update(independent_ray_verified=valid,certificate_margin=margin(cap),margin_at_50m=margin(50),rows_count=len(used),bound_variables_count=len(variables),row_indices=used.tolist(),involved_vertices=[dict(variable=int(v),x_m=int(data['indices'][v]%2048*6),z_m=int(12282-data['indices'][v]//2048*6),lower=float(lo[v]),upper=float(hi[v]),combined_coefficient=float(combined[v])) for v in variables])
            if valid and margin(50)<=0:
                lower,upper=cap,50.
                for _ in range(60):
                    middle=(lower+upper)/2
                    if margin(middle)>0:lower=middle
                    else:upper=middle
                report['necessary_cap_for_this_certificate_m']=upper
    if state==hs.HighsModelStatus.kInfeasible and not a.ray:
        iis=hs.HighsIis();call=solver.getIis(iis);rows=np.asarray(iis.row_index,dtype=int);cols=np.asarray(iis.col_index,dtype=int)
        involved=np.unique(B[rows].indices) if len(rows) else np.array([],dtype=int)
        report.update(iis_call=str(call),iis_valid=bool(iis.valid),row_indices=rows.tolist(),row_bounds=list(map(int,iis.row_bound)),column_indices=cols.tolist(),column_bounds=list(map(int,iis.col_bound)),elapsed_s=time.monotonic()-start,involved_vertices=[dict(variable=int(v),x_m=int(data['indices'][v]%2048*6),z_m=int(12282-data['indices'][v]//2048*6),lower=float(lo[v]),upper=float(hi[v])) for v in involved])
        if len(rows):
            family=lambda r:'road' if r<original['road_constraints'] else 'slope' if r<original['road_constraints']+original['slope_constraints'] else 'chord'
            report['rows']=[dict(index=int(r),family=family(r),rhs=float(data['rhs'][r]),variables=B.getrow(r).indices.tolist(),coefficients=B.getrow(r).data.tolist()) for r in rows]
    a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ['rows','involved_vertices','row_indices','row_bounds','column_indices','column_bounds']}))

if __name__=='__main__':main()
