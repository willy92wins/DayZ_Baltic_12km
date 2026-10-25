"""Local LP candidate; preserve the deployed V10 and all water/island supports."""
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
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--diagnose-only',action='store_true');args=ap.parse_args()
    out=ROOT/'tests/regional_road_width_pilot_v11'
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
        points.append(sections.reshape(-1,2));groups.append((start,s));start+=len(s)*len(offsets)
        routes.append(dict(chain=chain,station_start_m=float(a),station_end_m=float(b),source_polyline=p.tolist(),solve_start_m=float(s[0]),solve_end_m=float(s[-1])))
    points=np.concatenate(points);ix,w=weights(points)
    variables=np.unique(ix[(w>1e-12)&allowed.ravel()[ix]])
    mapping=np.full(h.size,-1,int);mapping[variables]=np.arange(len(variables));mapped=mapping[ix]
    use=(mapped>=0)&(w>1e-12)
    A=coo_matrix((w[use],(np.broadcast_to(np.arange(len(points))[:,None],ix.shape)[use],mapped[use])),shape=(len(points),len(variables))).tocsr()
    baseline=(h.ravel()[ix]*w).sum(axis=1)
    blocks=[];bounds=[]
    for begin,s in groups:
        n=len(s);centre=begin+np.arange(n)*17+8
        other=np.array([begin+j*17+k for j in range(n) for k in range(17) if k!=8]);mid=np.repeat(centre,16)
        B=A[other]-A[mid];d=baseline[other]-baseline[mid]
        blocks.extend([B,-B]);bounds.extend([.014-d,.014+d])
        B=A[centre[1:]]-A[centre[:-1]];d=baseline[centre[1:]]-baseline[centre[:-1]];limit=.06*np.diff(s)
        blocks.extend([B,-B]);bounds.extend([limit-d,limit+d])
        B=A[centre[3:-3]]-.5*A[centre[:-6]]-.5*A[centre[6:]];d=baseline[centre[3:-3]]-.5*baseline[centre[:-6]]-.5*baseline[centre[6:]]
        blocks.extend([B,-B]);bounds.extend([.022-d,.022+d])
    B=vstack(blocks,format='csr');rhs=np.concatenate(bounds);n=len(variables);I=eye(n,format='csr')
    constraint=vstack([hstack([B,coo_matrix((B.shape[0],n))]),hstack([I,-I]),hstack([-I,-I])],format='csr')
    objective=np.r_[np.zeros(n),np.ones(n)];rhs=np.r_[rhs,np.zeros(2*n)]
    receipt=dict(status='PLANNED_LP_NOT_ACCEPTED',source_npz_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),variables=n,constraints=constraint.shape[0],nonzeros=constraint.nnz,routes=routes,offsets_m=offsets.tolist(),vertex_delta_limit_m=.5,time_limit_s=120)
    if args.diagnose_only:
        minimum=-.5*np.asarray(abs(B).sum(axis=1)).ravel();bad=minimum>rhs[:B.shape[0]]+1e-8
        nnz=np.diff(B.indptr);chosen=np.flatnonzero(bad)
        diagnosis=dict(status='BOUND_INFEASIBILITY_WITNESS_NO_NEW_SOLVE',violated_rows=int(bad.sum()),fixed_violated_rows=int((bad&(nnz==0)).sum()),examples=[dict(row=int(i),variable_coefficients=int(nnz[i]),minimum_possible_lhs=float(minimum[i]),required_upper_bound=float(rhs[i])) for i in chosen[:12]])
        path=out/'infeasibility-diagnostic.json';assert not path.exists();path.write_text(json.dumps(diagnosis,indent=2)+'\n',encoding='utf-8');print(json.dumps(diagnosis));return
    out.mkdir();(out/'pre-solve.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:receipt[k] for k in ['status','variables','constraints','nonzeros']}),flush=True)
    began=time.monotonic()
    result=linprog(objective,A_ub=constraint,b_ub=rhs,bounds=[(-.5,.5)]*n+[(0,None)]*n,method='highs',options={'time_limit':120,'threads':1,'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
    receipt.update(success=bool(result.success),solver_status=int(result.status),message=result.message,elapsed_s=time.monotonic()-began,status='SOLVER_ONLY_NOT_ACCEPTED' if result.success else 'INCONCLUSIVE_SOLVER')
    if result.success:
        candidate=h.copy();candidate.ravel()[variables]=(h.ravel()[variables].astype(float)+result.x[:n]).astype('float32');changed=candidate!=h
        assert not np.any(changed&~allowed)
        receipt.update(changed_vertices=int(changed.sum()),max_delta_m=float(abs(candidate-h).max()))
        mask=np.zeros(h.shape,bool);mask.ravel()[variables]=True
        arrays={k:data[k] for k in data.files};arrays.update(candidate=candidate,changed=candidate!=data['base'],pilot_allowed=allowed,pilot_support=mask,parent=h)
        np.savez_compressed(out/'reference.npz',**arrays)
        asc=out/'baltic_road_width_pilot_v11.asc'
        with asc.open('w',encoding='ascii',newline='\n') as f:
            f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n');np.savetxt(f,candidate,fmt='%.9g')
        with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),candidate)
        receipt['asc_sha256']=hashlib.sha256(asc.read_bytes()).hexdigest()
    (out/'solve.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='routes'}));raise SystemExit(0 if result.success else 1)

if __name__=='__main__':main()
