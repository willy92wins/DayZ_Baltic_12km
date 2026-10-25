"""One bounded-time minimax diagnosis of frozen full-road constraints, no terrain."""
from pathlib import Path
import argparse,hashlib,json,time,subprocess
import numpy as np
from scipy.sparse import load_npz,coo_matrix,eye,hstack,vstack
from scipy.optimize import linprog

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();assert not a.out.exists()
    d=np.load(a.folder/'variables.npz');B=load_npz(a.folder/'constraints.npz');n=B.shape[1];I=eye(n,format='csr')
    A=vstack([hstack([B,coo_matrix((B.shape[0],1))]),hstack([I,-np.ones((n,1))]),hstack([-I,-np.ones((n,1))])],format='csr')
    available=int(subprocess.check_output(['powershell','-NoProfile','-Command','(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory'],text=True).strip())*1024
    required=2*1024**3+4*(A.data.nbytes+A.indices.nbytes+A.indptr.nbytes)
    assert available>=required,(available,required)
    started=time.monotonic();result=linprog(np.r_[np.zeros(n),1.],A_ub=A,b_ub=np.r_[d['rhs'],np.zeros(2*n)],bounds=[(float(v),None) for v in d['floor']]+[(0,None)],method='highs',options={'time_limit':600,'threads':1,'primal_feasibility_tolerance':1e-8,'dual_feasibility_tolerance':1e-8})
    report=dict(status='MINIMAX_DIAGNOSIS_NO_TERRAIN',success=bool(result.success),solver_status=int(result.status),message=result.message,elapsed_s=time.monotonic()-started,constraints_sha256=hashlib.sha256((a.folder/'constraints.npz').read_bytes()).hexdigest(),available_memory_bytes=available,required_memory_bytes=required)
    if result.success:
        delta=result.x[:-1];ix=np.argsort(abs(delta))[-20:][::-1];ids=d['indices'][ix]
        report.update(minimum_maximum_delta_m=float(result.x[-1]),maximum_residual=float(np.max(B@delta-d['rhs'])),extremes=[dict(x_m=int(v%2048*6),z_m=int(12282-v//2048*6),delta_m=float(delta[i])) for i,v in zip(ix,ids)])
    a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':main()
