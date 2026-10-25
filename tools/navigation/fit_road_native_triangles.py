"""Fit the road profile to native interpolation triangles in a separate candidate.

This improves raster approximation; it is not permission to change source
geometry, raise the acceptance thresholds, or skip an independent consumer.
"""
import hashlib,json
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.sparse import coo_matrix,diags,vstack
from scipy.sparse.linalg import lsmr
ROOT=Path(__file__).resolve().parents[2]
EV=ROOT/'evidence/regional-foundation-v1'
OUT=ROOT/'tests/regional_foundation_roads_v3'


def weights(p):
    col=p[:,0]/6;row=(12282-p[:,1])/6
    ci=np.floor(col).astype(int);ri=np.floor(row).astype(int)
    a=col-ci;b=row-ri;upper=b<=a
    ix=np.column_stack([ri*2048+ci,(ri+1)*2048+ci+1,np.where(upper,ri*2048+ci+1,(ri+1)*2048+ci)])
    w=np.column_stack([np.where(upper,1-a,1-b),np.where(upper,b,a),np.abs(a-b)])
    return ix,w


def main():
    assert not OUT.exists(),'Fresh output required'
    data=np.load(ROOT/'tests/regional_foundation_roads_v2/reference.npz')
    h=data['candidate'].copy();xy=data['xy'];profile=data['profile']
    chains=json.loads((EV/'road-grade-chains-v2.json').read_text())['chains']
    water=np.load(ROOT/'tests/regional_outline_v3/reference.npz')['water'].astype(bool)
    wet_distance=distance_transform_edt(~water)*6
    fit=json.loads((ROOT/'evidence/narva/evidence/narva-fit.json').read_text())
    centre=np.array(fit['bridge_centre_tb'])-[200000,0]
    rr,cc=np.mgrid[0:2048,0:2048]
    editable=(wet_distance>42)&(np.hypot(cc*6-centre[0],12282-rr*6-centre[1])>460)
    samples=[];targets=[]
    for indices in chains:
        p=xy[indices]
        if len(p)<4:continue
        tangent=np.gradient(p,axis=0);length=np.linalg.norm(tangent,axis=1)
        if np.any(length<1e-8):continue
        normal=np.column_stack([-tangent[:,1],tangent[:,0]])/length[:,None]
        for offset in (-4,-2,0,2,4):
            q=p+offset*normal
            ix,w=weights(q)
            valid=np.all(editable.ravel()[ix],axis=1)
            samples.append(q[valid]);targets.append(profile[indices][valid])
    samples=np.concatenate(samples);targets=np.concatenate(targets)
    ix,w=weights(samples)
    variables=np.unique(ix.ravel())
    index=np.full(h.size,-1,dtype=int);index[variables]=np.arange(len(variables))
    A=coo_matrix((w.ravel(),(np.repeat(np.arange(len(samples)),3),index[ix].ravel())),shape=(len(samples),len(variables))).tocsr()
    prior=h.ravel()[variables].astype(float)
    prior_weight=.002
    system=vstack([A,diags(np.full(len(variables),prior_weight))],format='csr')
    rhs=np.r_[targets,prior*prior_weight]
    solve=lsmr(system,rhs,atol=1e-10,btol=1e-10,maxiter=600,x0=prior)
    result=solve[0]
    residual=A@result-targets
    candidate=h.copy();candidate.ravel()[variables]=result.astype(np.float32)
    assert np.isfinite(candidate).all()
    assert not np.any((candidate!=h)&~editable)
    OUT.mkdir(parents=True)
    asc=OUT/'baltic_roads_pre_hydrology_v3.asc'
    with asc.open('w',encoding='ascii',newline='\n') as handle:
        handle.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(handle,candidate,fmt='%.9f')
    with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),candidate)
    arrays={key:data[key] for key in data.files}
    arrays['candidate']=candidate;arrays['changed']=candidate!=data['base']
    np.savez_compressed(OUT/'reference.npz',**arrays)
    (EV/'road-grade-chains-v3.json').write_bytes((EV/'road-grade-chains-v2.json').read_bytes())
    report={'status':'FIT_COMPLETE_NOT_ACCEPTED','constraints':len(samples),'variables':len(variables),
            'solver_stop':int(solve[1]),'iterations':int(solve[2]),
            'residual_abs_p50_p95_p99_max_m':np.percentile(abs(residual),[50,95,99,100]).tolist(),
            'max_native_adjustment_m':float(abs(candidate-h).max()),'candidate_sha256':hashlib.sha256(asc.read_bytes()).hexdigest(),
            'limits':['Must pass the unchanged native triangle consumer; solver residual is not a road quality verdict.','Junctions and approaches need combined-layer engineering.']}
    (EV/'road-triangle-fit-v3.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
