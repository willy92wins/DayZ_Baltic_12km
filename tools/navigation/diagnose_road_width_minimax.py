"""Quantify minimum maximum vertex delta; no terrain output or acceptance."""
from pathlib import Path
import argparse,hashlib,json,time,warnings
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.sparse import coo_matrix,eye,hstack,vstack
from scipy.optimize import linprog
from fit_road_native_triangles import weights
ROOT=Path(__file__).resolve().parents[2]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--diagnose-only',action='store_true');args=ap.parse_args();args.diagnose_only=True
    out=ROOT/'tests/regional_road_width_pilot_v12'
    assert args.diagnose_only or not out.exists()
    source=ROOT/'tests/regional_foundation_combined_v10/reference.npz'
    data=np.load(source);h=data['candidate'];roadpath=ROOT/'tests/regional_foundation_roads_v6/reference.npz'
    roads=np.load(roadpath);chains=json.loads((ROOT/'evidence/regional-foundation-v1/road-grade-chains-v6.json').read_text(encoding='utf-8'))['chains']
    wet=data['wet']|data['ocean'];wd=distance_transform_edt(~wet)*6
    rr,cc=np.mgrid[0:2048,0:2048]
    allowed=(wd>42)&~data['fairway_support']&~data['bank_support']&~data['island_support_conservative']&(np.hypot(cc*6-2417.1428225906,12282-rr*6-6889.8850822322)>480)
    offsets=np.arange(-4,4.01,.5);points=[];groups=[];routes=[];start=0
    for chain,lo,hi in [(5,193,427),(13,8,362),(68,954,1484)]:
        p=roads['xy'][chains[chain]];station=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        a=station[lo]+20;b=min(station[hi-1]-20,a+1000)
        s=np.linspace(max(0,a-50),min(station[-1],b+50),int(np.ceil(min(station[-1],b+50)-max(0,a-50)))+1)
        q=np.column_stack([np.interp(s,station,p[:,k]) for k in [0,1]])
        tangent=np.gradient(q,axis=0);normal=np.column_stack([-tangent[:,1],tangent[:,0]])/np.linalg.norm(tangent,axis=1)[:,None]
        sections=q[:,None,:]+normal[:,None,:]*offsets[None,:,None]
        r=np.clip(np.rint((12282-q[:,1])/6).astype(int),0,2047);c=np.clip(np.rint(q[:,0]/6).astype(int),0,2047)
        eligible=(wd[r,c]>48)&(np.linalg.norm(q-[2417.1428225906,6889.8850822322],axis=1)>480)
        core=(s>=a)&(s<=b);assert np.all(eligible[core]),'Cannot exclude core stations'
        points.append(sections.reshape(-1,2));groups.append((start,s,eligible));start+=len(s)*len(offsets)
        routes.append(dict(chain=chain,station_start_m=float(a),station_end_m=float(b),source_polyline=p.tolist(),solve_start_m=float(s[0]),solve_end_m=float(s[-1])))
    points=np.concatenate(points);ix,w=weights(points)
    variables=np.unique(ix[(w>1e-12)&allowed.ravel()[ix]])
    mapping=np.full(h.size,-1,int);mapping[variables]=np.arange(len(variables));mapped=mapping[ix]
    use=(mapped>=0)&(w>1e-12)
    A=coo_matrix((w[use],(np.broadcast_to(np.arange(len(points))[:,None],ix.shape)[use],mapped[use])),shape=(len(points),len(variables))).tocsr()
    baseline=(h.ravel()[ix]*w).sum(axis=1)
    blocks=[];bounds=[]
    for begin,s,eligible in groups:
        n=len(s);centre=begin+np.arange(n)*17+8
        other=np.array([begin+j*17+k for j in range(n) if eligible[j] for k in range(17) if k!=8]);mid=np.repeat(centre[eligible],16)
        B=A[other]-A[mid];d=baseline[other]-baseline[mid]
        blocks.extend([B,-B]);bounds.extend([.014-d,.014+d])
        pair=eligible[1:]&eligible[:-1];B=A[centre[1:][pair]]-A[centre[:-1][pair]];d=baseline[centre[1:][pair]]-baseline[centre[:-1][pair]];limit=.06*np.diff(s)[pair]
        blocks.extend([B,-B]);bounds.extend([limit-d,limit+d])
        chord=np.logical_and.reduce([eligible[j:n-6+j] for j in range(7)]);B=A[centre[3:-3][chord]]-.5*A[centre[:-6][chord]]-.5*A[centre[6:][chord]];d=baseline[centre[3:-3][chord]]-.5*baseline[centre[:-6][chord]]-.5*baseline[centre[6:][chord]]
        blocks.extend([B,-B]);bounds.extend([.022-d,.022+d])
    B=vstack(blocks,format='csr');rhs=np.concatenate(bounds);n=len(variables);I=eye(n,format='csr')
    constraint=vstack([hstack([B,coo_matrix((B.shape[0],1))]),hstack([I,-np.ones((n,1))]),hstack([-I,-np.ones((n,1))])],format='csr')
    started=time.monotonic()
    result=linprog(np.r_[np.zeros(n),1.],A_ub=constraint,b_ub=np.r_[rhs,np.zeros(2*n)],bounds=[(None,None)]*n+[(0,None)],method='highs',options={'time_limit':120,'threads':1,'primal_feasibility_tolerance':1e-8,'dual_feasibility_tolerance':1e-8})
    report=dict(status='MINIMAX_DIAGNOSTIC_NO_TERRAIN',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),success=bool(result.success),solver_status=int(result.status),message=result.message,elapsed_s=time.monotonic()-started,variables=n,physical_constraints=B.shape[0])
    if result.success:
        delta=result.x[:n];chosen=np.argsort(abs(delta))[-12:][::-1]
        report.update(minimum_maximum_delta_m=float(result.x[-1]),max_constraint_residual_m=float(np.max(B@delta-rhs)),delta_absolute_percentiles_m=np.percentile(abs(delta),[50,90,95,99,100]).tolist(),extremes=[dict(x_m=int(variables[i]%2048*6),z_m=int(12282-variables[i]//2048*6),delta_m=float(delta[i]),source_y_m=float(h.ravel()[variables[i]])) for i in chosen])
    dest=out/'minimax-diagnostic.json';assert not dest.exists();dest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2));return

if __name__=='__main__':main()
