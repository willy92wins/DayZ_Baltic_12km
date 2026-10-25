"""Bounded L1 constraint generation, checked against every frozen V27 row."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,time
import numpy as np
import rasterio
from scipy.sparse import load_npz,eye,coo_matrix,hstack,vstack
from scipy.ndimage import distance_transform_edt
from scipy.optimize._highspy import _core as hs
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'tests/regional_road_network_v27_constraints'
OUT=ROOT/'tests/regional_road_network_v27'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--worker',action='store_true');a=ap.parse_args()
    if not a.worker:
        assert not OUT.exists();OUT.mkdir()
        try:
            r=subprocess.run([sys.executable,'-X','utf8',__file__,'--worker'],capture_output=True,text=True,timeout=650)
            (OUT/'worker-stdout.log').write_text(r.stdout,encoding='utf-8');(OUT/'worker-stderr.log').write_text(r.stderr,encoding='utf-8');print(r.stdout);print(r.stderr,file=sys.stderr)
            assert r.returncode==0,r.returncode
        except subprocess.TimeoutExpired:
            (OUT/'timeout.json').write_text(json.dumps(dict(status='STOPPED_WALL_BUDGET_NO_ACCEPTANCE',seconds=650))+'\n',encoding='utf-8')
        return
    frozen=json.loads((SOURCE/'build-receipt.json').read_text(encoding='utf-8'))
    assert frozen['lateral_transition_m']==48. and frozen['maximum_geographic_distance_m']==60.5
    assert sha(SOURCE/'constraints.npz')==frozen['constraints_sha256']
    assert sha(SOURCE/'variables.npz')==frozen['variables_sha256']
    parent=ROOT/'tests/regional_outline_smoothing_v33/reference.npz'
    assert sha(parent)=='8e84d5ce38da8863116c52ecdf9953d5b201a097459513054eea8e0f0e14c45a'
    ref=np.load(parent);h=ref['candidate'];data=np.load(SOURCE/'variables.npz');B=load_npz(SOURCE/'constraints.npz');rhs=data['rhs'];ix=data['indices'];n=B.shape[1]
    cap=6.;floor=data['floor']
    original=ROOT/'tests/regional_foundation_combined_v10/reference.npz'
    assert sha(original)=='a43cb0f128c17318207a114f94f08801ff35a81af5d36a4b7e3427dd3d6aca2d'
    v10=np.load(original)['candidate'].ravel()[ix].astype(float);current=h.ravel()[ix].astype(float)
    lo=np.maximum.reduce([np.full(n,-cap),floor,v10-cap-current]);hi=np.minimum(cap,v10+cap-current)
    assert np.all(lo<=hi)
    active=np.flatnonzero(-rhs>1e-8)
    receipt=json.loads((SOURCE/'build-receipt.json').read_text(encoding='utf-8'));receipt.update(status='STOPPED_NO_CANDIDATE',maximum_allowed_delta_m=cap,vertex_delta_limit_m=cap,rounds=[])
    (OUT/'pre-solve.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    I=eye(n,format='csr');identity_rows=vstack([hstack([I,-I]),hstack([-I,-I])],format='csr')
    begin=time.monotonic();feasible=False
    while time.monotonic()-begin<600:
        available=int(subprocess.check_output(['powershell','-NoProfile','-Command','(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory'],text=True).strip())*1024
        if available<2*1024**3:receipt['stop_reason']='AVAILABLE_MEMORY_BELOW_2GIB';break
        A=vstack([hstack([B[active],coo_matrix((len(active),n))]),identity_rows],format='csc')
        model=hs.HighsLp();model.num_col_=2*n;model.num_row_=A.shape[0];model.col_cost_=np.r_[np.zeros(n),np.ones(n)];model.col_lower_=np.r_[lo,np.zeros(n)];model.col_upper_=np.r_[hi,np.full(n,hs.kHighsInf)];model.row_lower_=np.full(A.shape[0],-hs.kHighsInf);model.row_upper_=np.r_[rhs[active],np.zeros(2*n)]
        model.a_matrix_.num_col_=2*n;model.a_matrix_.num_row_=A.shape[0];model.a_matrix_.format_=hs.MatrixFormat.kColwise;model.a_matrix_.start_=A.indptr;model.a_matrix_.index_=A.indices;model.a_matrix_.value_=A.data
        solver=hs._Highs()
        for k,v in [('output_flag',False),('threads',1),('time_limit',max(1.,600-(time.monotonic()-begin))),('primal_feasibility_tolerance',1e-8),('dual_feasibility_tolerance',1e-8)]:assert solver.setOptionValue(k,v)==hs.HighsStatus.kOk
        assert solver.passModel(model)!=hs.HighsStatus.kError
        solver.run();state=solver.getModelStatus();solution=solver.getSolution()
        record=dict(round=len(receipt['rounds']),active_original_rows=len(active),model_status=solver.modelStatusToString(state),elapsed_s=time.monotonic()-begin)
        if state==hs.HighsModelStatus.kInfeasible:
            rs,exists,ray=solver.getDualRay();record.update(ray_status=str(rs),ray_exists=bool(exists))
            if exists:
                y=-np.asarray(ray);coef=np.asarray(A.T@y);bound=float(y@model.row_upper_)
                lower=np.r_[lo,np.zeros(n)];upper=np.r_[hi,np.full(n,np.inf)]
                # A valid contradiction cannot have negative coefficients on
                # the unbounded nonnegative L1 auxiliaries.
                aux_valid=bool(np.all(coef[n:]>=-1e-8));combined=coef[:n]
                margin=float(np.maximum(combined,0)@lo+np.minimum(combined,0)@hi-bound)
                valid=bool(np.all(y>=-1e-9) and aux_valid and margin>1e-7)
                record.update(certificate_verified=valid,certificate_margin=margin,certificate_rhs=bound,nonzero_certificate_rows=int(np.count_nonzero(y)))
                used=np.flatnonzero(abs(combined)>1e-9)
                record['dominant_vertices']=[dict(x_m=int(ix[i]%2048*6),z_m=int(12282-ix[i]//2048*6),coefficient=float(combined[i])) for i in used]
                np.savez_compressed(OUT/'certificate.npz',active_rows=active,ray=y,combined=combined)
            receipt['rounds'].append(record);break
        if not solution.value_valid:receipt['rounds'].append(record);break
        values=np.asarray(solution.col_value);delta=values[:n]
        bounds=bool(len(values)==2*n and np.isfinite(values).all() and np.all(delta>=lo-1e-7) and np.all(delta<=hi+1e-7))
        violations=B@delta-rhs;bad=np.flatnonzero(violations>1e-7)
        record.update(bounds_valid=bounds,maximum_full_residual=float(violations.max()),violated_original_rows=len(bad));receipt['rounds'].append(record)
        (OUT/'progress.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(record),flush=True)
        if bounds and not len(bad):feasible=True;break
        new=np.union1d(active,bad)
        if not bounds or len(new)==len(active):receipt['stop_reason']='NO_NEW_ROWS_OR_INVALID_BOUNDS';break
        np.savez_compressed(OUT/'active-checkpoint.npz',active_rows=new,last_delta=delta)
        active=new
        del solver,model,A
    if feasible:
        candidate=h.copy();candidate.ravel()[ix]=(h.ravel()[ix].astype(float)+delta).astype('float32');support=data['support'];changed=candidate!=h;assert not np.any(changed&~support)
        asc=OUT/'baltic_road_network_v27.asc'
        with asc.open('w',encoding='ascii',newline='\n') as f:
            f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n');np.savetxt(f,candidate,fmt='%.9g')
        with rasterio.open(asc) as ds:assert np.array_equal(candidate,ds.read(1))
        rr,cc=np.mgrid[:2048,:2048];wd=distance_transform_edt(~(ref['wet']|ref['ocean']))*6
        allowed=(wd>30)&~ref['fairway_support']&(np.hypot(cc*6-2417.1428225906,12282-rr*6-6889.8850822322)>480)
        allowed=data['allowed'];assert not np.any(changed&~allowed)
        arrays={k:ref[k] for k in ref.files};arrays.update(candidate=candidate,parent=h,changed=candidate!=ref['base'],pilot_support=support,pilot_allowed=allowed)
        np.savez_compressed(OUT/'reference.npz',**arrays)
        receipt.update(status='FULL_MATRIX_FEASIBLE_CANDIDATE_NOT_ACCEPTED',asc_sha256=sha(asc),changed_vertices=int(changed.sum()),max_delta_m=float(abs(candidate-h).max()),native_float32_constraint_residual=float(np.max(B@(candidate.ravel()[ix].astype(float)-h.ravel()[ix])-rhs)))
    receipt['elapsed_s']=time.monotonic()-begin
    (OUT/'solve.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in receipt.items() if k!='routes'}))

if __name__=='__main__':main()
