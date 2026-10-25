"""Solve road smoothness inequalities on native vertices, keeping the gates fixed."""
import hashlib,json
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.sparse import coo_matrix,diags,hstack,vstack,csr_matrix
from scipy.optimize import linprog
from fit_road_native_triangles import weights
ROOT=Path(__file__).resolve().parents[2]
EV=ROOT/'evidence/regional-foundation-v1'
OUT=ROOT/'tests/regional_foundation_roads_v5'


def main():
    assert not OUT.exists(),'Fresh output required'
    data=np.load(ROOT/'tests/regional_foundation_roads_v2/reference.npz')
    h=data['candidate'];xy=data['xy'];profile=data['profile']
    chains=json.loads((EV/'road-grade-chains-v2.json').read_text())['chains']
    water=np.load(ROOT/'tests/regional_outline_v3/reference.npz')['water'].astype(bool)
    wet_distance=distance_transform_edt(~water)*6
    fit=json.loads((ROOT/'evidence/narva/evidence/narva-fit.json').read_text())
    centre=np.array(fit['bridge_centre_tb'])-[200000,0]
    rr,cc=np.mgrid[0:2048,0:2048]
    editable=(wet_distance>30)&(np.hypot(cc*6-centre[0],12282-rr*6-centre[1])>440)
    positions=[];targets=[];groups=[];count=0
    for indices in chains:
        p=xy[indices]
        if len(p)<4:continue
        tangent=np.gradient(p,axis=0);length=np.linalg.norm(tangent,axis=1)
        if np.any(length<1e-8):continue
        normal=np.column_stack([-tangent[:,1],tangent[:,0]])/length[:,None]
        q=np.stack([p-4*normal,p,p+4*normal],axis=1)
        ix,_=weights(q.reshape(-1,2))
        valid=np.all(editable.ravel()[ix].reshape(len(p),3,3),axis=(1,2))
        kept=np.flatnonzero(valid)
        if not len(kept):continue
        positions.append(q[kept].reshape(-1,2));targets.append(np.repeat(profile[indices][kept],3))
        station=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        groups.append((count,kept,station[kept]))
        count+=len(kept)*3
    positions=np.concatenate(positions);target=np.concatenate(targets)
    ix,w=weights(positions);variables=np.unique(ix)
    mapping=np.full(h.size,-1,int);mapping[variables]=np.arange(len(variables))
    A=coo_matrix((w.ravel(),(np.repeat(np.arange(len(positions)),3),mapping[ix].ravel())),shape=(len(positions),len(variables))).tocsr()
    dr=[];dc=[];dv=[];bounds=[]
    def constraint(cols,values,bound):
        row=len(bounds);dr.extend([row]*len(cols));dc.extend(cols);dv.extend(values);bounds.append(bound)
    for start,kept,station in groups:
        for j in range(len(kept)):
            mid=start+3*j+1
            constraint([mid-1,mid],[1,-1],.014)
            constraint([mid+1,mid],[1,-1],.014)
            if j and kept[j]-kept[j-1]==1:
                ds=station[j]-station[j-1]
                constraint([mid,mid-3],[1,-1],.060*ds)
            if 0<j<len(kept)-1 and kept[j+1]-kept[j-1]==2:
                a=station[j]-station[j-1];b=station[j+1]-station[j]
                constraint([mid,mid-3,mid+3],[1,-b/(a+b),-a/(a+b)],.022)
    D=coo_matrix((dv,(dr,dc)),shape=(len(bounds),len(positions))).tocsr()
    B=D@A
    n=len(variables);m=len(positions)
    prior=h.ravel()[variables].astype(float)
    # Bound and regularize every vertex, including vertices with tiny/zero
    # interpolation weights. A fit only at road samples has a dangerous nullspace.
    soft=vstack([A,diags(np.ones(n))],format='csr')
    goal=np.r_[target,prior]
    eye=diags(np.ones(m+n));zeros=csr_matrix((B.shape[0],m+n))
    constraints=vstack([hstack([soft,-eye]),hstack([-soft,-eye]),hstack([B,zeros]),hstack([-B,zeros])],format='csr')
    rhs=np.r_[goal,-goal,bounds,bounds]
    c=np.r_[np.zeros(n),np.ones(m),np.full(n,.02)]
    print(f'Solving {n} terrain variables, {m} deviation variables, {constraints.shape[0]} inequalities',flush=True)
    native_bounds=list(zip(np.maximum(1.25,prior-1),np.minimum(120,prior+1)))
    result=linprog(c,A_ub=constraints,b_ub=rhs,bounds=native_bounds+[(0,None)]*(m+n),method='highs',
                   options={'time_limit':180,'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
    receipt={'status':'SOLVER_ONLY_NOT_ACCEPTED' if result.success else 'INCONCLUSIVE_SOLVER',
             'success':bool(result.success),'solver_status':int(result.status),'message':result.message,
             'terrain_variables':n,'constraints':constraints.shape[0]}
    if result.success:
        candidate=h.copy();candidate.ravel()[variables]=result.x[:n].astype(np.float32)
        assert not np.any((candidate!=h)&~editable)
        assert not np.any((candidate!=h)&water)
        OUT.mkdir(parents=True)
        asc=OUT/'baltic_roads_pre_hydrology_v5.asc'
        with asc.open('w',encoding='ascii',newline='\n') as handle:
            handle.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
            np.savetxt(handle,candidate,fmt='%.9f')
        with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),candidate)
        arrays={key:data[key] for key in data.files};arrays['candidate']=candidate;arrays['changed']=candidate!=data['base']
        np.savez_compressed(OUT/'reference.npz',**arrays)
        (EV/'road-grade-chains-v5.json').write_bytes((EV/'road-grade-chains-v2.json').read_bytes())
        receipt.update(candidate_sha256=hashlib.sha256(asc.read_bytes()).hexdigest(),
                       max_adjustment_m=float(abs(candidate-h).max()),
                       average_profile_deviation_m=float(np.mean(abs(A@result.x[:n]-target))))
    (EV/'road-triangle-constraints-v5.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
    raise SystemExit(0 if result.success else 1)


if __name__=='__main__':main()
