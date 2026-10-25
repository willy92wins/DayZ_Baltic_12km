"""Restore subcell land omissions under a local height exception, frozen V24 rows."""
from pathlib import Path
import json,hashlib,time,math
import numpy as np
from scipy.sparse import load_npz,eye,hstack,vstack,csr_matrix
from scipy.ndimage import distance_transform_edt
from scipy.optimize import linprog
import rasterio
ROOT=Path(__file__).resolve().parents[2];F=ROOT/'tests/regional_outline_smoothing_v24a';OUT=ROOT/'tests/regional_outline_smoothing_v25'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not OUT.exists();OUT.mkdir();begin=time.monotonic()
    B=load_npz(F/'constraints.npz');d=np.load(F/'variables.npz');ix=d['variables'];rhs=d['rhs'];macro=d['macro'];target=d['target'];n=B.shape[1]
    source=ROOT/'tests/regional_foundation_combined_v10/reference.npz';assert sha(source)=='a43cb0f128c17318207a114f94f08801ff35a81af5d36a4b7e3427dd3d6aca2d';ref=np.load(source);base=ref['candidate'];h=base.ravel()[ix].astype(float);wet=(ref['wet']|ref['ocean']).ravel()[ix];lo=np.where(wet,h-6,np.maximum(h-6,1.4));hi=h+6
    impossible=[]
    for start in range(0,len(rhs),250000):
        A=B[start:start+250000];minimum=A.maximum(0)@lo+A.minimum(0)@hi;impossible.extend((start+np.flatnonzero(minimum>rhs[start:start+len(minimum)]+1e-7)).tolist())
    assert len(impossible)==146
    seeds=np.unique(B[impossible].indices);seedgrid=np.zeros(base.shape,bool);seedgrid.ravel()[ix[seeds]]=True
    region=distance_transform_edt(~seedgrid)*6<=48
    local=region.ravel()[ix]&wet;hi[local]=h[local]+15
    descriptor=dict(status='BOUNDS_FROZEN_BEFORE_SOLVE',parent_matrix_sha256=sha(F/'constraints.npz'),parent_variables_sha256=sha(F/'variables.npz'),source_npz_sha256=sha(source),isolated_impossible_rows=len(impossible),seed_vertices=[dict(xz=[int(ix[i]%2048*6),int(12282-ix[i]//2048*6)],height=float(h[i])) for i in seeds],local_exception_vertices=int(local.sum()),local_exception_radius_m=48,maximum_upward_delta_in_exception_m=15,ordinary_delta_limit_m=6,reason='Source land intersects triangles whose vertices are all deep ocean; uniform6m bound cannot raise these omitted subcell features.')
    (OUT/'pre-solve.json').write_text(json.dumps(descriptor,indent=2)+'\n');np.savez_compressed(OUT/'local-exception.npz',region=region,lo=lo,hi=hi)
    print(json.dumps({k:v for k,v in descriptor.items() if k!='seed_vertices'}),flush=True)
    I=eye(n,format='csr');A=vstack([hstack([B,csr_matrix(B.shape)]),hstack([I,-I]),hstack([-I,-I])],format='csr');wanted=target.ravel()[ix]
    r=linprog(np.r_[np.zeros(n),np.ones(n)],A_ub=A,b_ub=np.r_[rhs,wanted,-wanted],bounds=list(zip(lo,hi))+[(0,None)]*n,method='highs',options={'time_limit':300,'threads':1,'primal_feasibility_tolerance':1e-8})
    report=dict(status=str(r.message),solver_success=bool(r.success),elapsed_s=time.monotonic()-begin,source_npz_sha256=sha(source),pre_solve_sha256=sha(OUT/'pre-solve.json'))
    if r.success:
        candidate=macro.astype('float32');candidate.ravel()[ix]=r.x[:n].astype('float32');residual=B@candidate.ravel()[ix]-rhs;report['maximum_constraint_residual_m']=float(residual.max())
        assert residual.max()<1e-4
        asc=OUT/'baltic_outline_smoothing_v25.asc'
        with asc.open('w',newline='\n') as f:
            f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n');np.savetxt(f,candidate,fmt='%.9g')
        with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),candidate)
        payload={k:ref[k] for k in ref.files};payload.update(candidate=candidate,parent=base,changed=candidate!=base);np.savez_compressed(OUT/'reference.npz',**payload)
        report.update(status='CANDIDATE_REQUIRES_INDEPENDENT_GATES',asc_sha256=sha(asc),changed_vertices=int((base!=candidate).sum()),maximum_delta_m=float(abs(base-candidate).max()))
    (OUT/'solve.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
