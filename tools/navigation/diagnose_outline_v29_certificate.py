"""Extract and algebraically verify a geometric conflict; never write terrain."""
from pathlib import Path
import json,time,subprocess,sys
import numpy as np
from scipy.sparse import load_npz,vstack
from scipy.ndimage import distance_transform_edt
from scipy.optimize._highspy import _core as hs
ROOT=Path(__file__).resolve().parents[2];F=ROOT/'tests/regional_outline_smoothing_v28';S=ROOT/'tests/regional_outline_smoothing_v29';OUT=S/'geometry-conflict'
def worker():
    d=np.load(F/'variables.npz');ix=d['variables'];original=load_npz(F/'constraints.npz');meta=json.loads((F/'build.json').read_text());nd=meta['category_counts']['dry_plane'];nc=meta['category_counts']['lake_core'];extra=load_npz(S/'island-constraints.npz');B=vstack([original[:nd+nc],extra],format='csr');rhs=np.r_[d['rhs'][:nd+nc],np.load(S/'island-rhs.npy')]
    ref=np.load(ROOT/'tests/regional_foundation_combined_v10/reference.npz');base=ref['candidate'];h=base.ravel()[ix].astype(float);wet=(ref['wet']|ref['ocean']).ravel()[ix];lo=np.where(wet,h-6,np.maximum(h-6,1.4));hi=h+6;pre=json.loads((S/'pre-solve.json').read_text());seed=np.zeros(base.shape,bool)
    for p in pre['seed_vertices']:x,z=p['xz'];seed[(12282-z)//6,x//6]=True
    exception=(distance_transform_edt(~seed)*6<=48).ravel()[ix]&wet;hi[exception]=h[exception]+15
    n=B.shape[1];m=B.shape[0];A=B.tocsc();lp=hs.HighsLp();lp.num_col_=n;lp.num_row_=m;lp.col_cost_=np.zeros(n);lp.col_lower_=lo;lp.col_upper_=hi;lp.row_lower_=np.full(m,-hs.kHighsInf);lp.row_upper_=rhs;lp.a_matrix_.num_col_=n;lp.a_matrix_.num_row_=m;lp.a_matrix_.format_=hs.MatrixFormat.kColwise;lp.a_matrix_.start_=A.indptr;lp.a_matrix_.index_=A.indices;lp.a_matrix_.value_=A.data
    solver=hs._Highs()
    for k,v in [('output_flag',False),('threads',1),('time_limit',120.),('primal_feasibility_tolerance',1e-8),('dual_feasibility_tolerance',1e-8)]:assert solver.setOptionValue(k,v)==hs.HighsStatus.kOk
    assert solver.passModel(lp)!=hs.HighsStatus.kError;t=time.monotonic();solver.run();state=solver.getModelStatus();report=dict(status='GEOMETRY_SUBSET_DIAGNOSIS',model_status=solver.modelStatusToString(state),rows=m,seconds=time.monotonic()-t,scope='No slope rows. A contradiction here also applies to the full system.');print(json.dumps(report),flush=True)
    if state==hs.HighsModelStatus.kInfeasible:
        call,exists,ray=solver.getDualRay();report.update(ray_status=str(call),ray_exists=bool(exists))
        if exists:
            y=-np.asarray(ray);combined=np.asarray(B.T@y);margin=float(np.maximum(combined,0)@lo+np.minimum(combined,0)@hi-y@rhs);used=np.flatnonzero(y!=0);dominant=np.flatnonzero(abs(combined)>1e-8);valid=bool(np.all(y>=-1e-9) and margin>1e-7)
            np.savez_compressed(OUT/'ray.npz',ray=y,combined=combined,rows=used)
            records=[]
            for i in used:
                r=B.getrow(i);records.append(dict(index=int(i),kind='dry' if i<nd else 'lake' if i<nd+nc else 'island',weight=float(y[i]),rhs=float(rhs[i]),vertices=[dict(variable=int(k),xz=[int(ix[k]%2048*6),int(12282-ix[k]//2048*6)],coefficient=float(v),height=float(h[k])) for k,v in zip(r.indices,r.data) if abs(v)>1e-10]))
            report.update(independent_certificate_valid=valid,margin_m=margin,row_count=len(used),dominant_bounds=[dict(xz=[int(ix[k]%2048*6),int(12282-ix[k]//2048*6)],coefficient=float(combined[k]),lower=float(lo[k]),upper=float(hi[k])) for k in dominant],rows_detail=records)
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows_detail'}),flush=True)
if __name__=='__main__':
    if '--worker' in sys.argv:worker()
    else:
        assert not OUT.exists();OUT.mkdir()
        try:
            r=subprocess.run([sys.executable,'-X','utf8',__file__,'--worker'],capture_output=True,text=True,timeout=150);(OUT/'worker.log').write_text(r.stdout+r.stderr);print(r.stdout);print(r.stderr);assert r.returncode==0
        except subprocess.TimeoutExpired:(OUT/'timeout.json').write_text(json.dumps(dict(status='NO_CERTIFICATE_WITHIN150S'))+'\n');print('No certificate within150s')
