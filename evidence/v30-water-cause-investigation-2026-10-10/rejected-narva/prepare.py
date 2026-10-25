from pathlib import Path
import hashlib,json,sys
import numpy as np

B=Path(__file__).parent
SRC=Path('E:/DayZ-Baltic-Build/v30-remaining-exact-dry-support-20261009/candidate')
OFF=((0,0),(0,1),(1,0),(1,1))
TRI=((0,1,3),(0,2,3))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    assert sha(SRC/'terrain.npz')=='b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36'
    t=dict(np.load(SRC/'terrain.npz')); h=t['heights'].astype(float)
    p=np.load(SRC/'plane.npy'); f=np.load(SRC/'visible-field.npy')
    r,c=np.indices(h.shape); x=c*6;z=12282-r*6
    scope=(x-2417.1428225906)**2+(z-6889.8850822322)**2<=480**2
    allowed=scope & ~t['reserve'].astype(bool) & ~t['platform'].astype(bool) & (t['cls']==3) & (h<1)
    forbidden=np.zeros(h.shape,bool)
    edge_limit=6*np.tan(np.deg2rad(35))/np.sqrt(2)
    for ids in TRI:
        hv=np.stack([h[OFF[i][0]:OFF[i][0]+2047,OFF[i][1]:OFF[i][1]+2047] for i in ids],axis=-1)
        # Every affected triangle stays fully inside both water representations.
        valid=np.isfinite(p)&(p>=1.95)&np.all(np.isfinite(f[:,:,ids]),axis=-1)&np.all(f[:,:,ids]>=1.95,axis=-1)
        valid &= np.all(hv<p[:,:,None],axis=-1)&np.all(hv<f[:,:,ids],axis=-1)
        valid &= np.all(p[:,:,None]-hv>=.95,axis=-1)&np.all(f[:,:,ids]-hv>=.95,axis=-1)
        # Freeze inherited steep faces; all remaining axis edges admit an L-infinity
        # slope envelope inscribed in the 35-degree Euclidean gradient limit.
        valid &= (np.abs(hv[:,:,1]-hv[:,:,0])<=edge_limit)&(np.abs(hv[:,:,2]-hv[:,:,1])<=edge_limit)
        for i in ids:
            dr,dc=OFF[i];forbidden[dr:dr+2047,dc:dc+2047]|=~valid
    allowed &= ~forbidden
    # Boundary support is outside the meaningful local diagnostic and stays frozen.
    allowed[[0,-1],:]=False;allowed[:,[0,-1]]=False
    v=h.copy();v[allowed]=1.0
    assert np.any(allowed)
    for iteration in range(1000):
        cap=v.copy()
        np.minimum(cap[1:,:],v[:-1,:]+edge_limit,out=cap[1:,:])
        np.minimum(cap[:-1,:],v[1:,:]+edge_limit,out=cap[:-1,:])
        np.minimum(cap[:,1:],v[:,:-1]+edge_limit,out=cap[:,1:])
        np.minimum(cap[:,:-1],v[:,1:]+edge_limit,out=cap[:,:-1])
        nv=v.copy();nv[allowed]=np.maximum(h[allowed],cap[allowed])
        change=float(np.max(np.abs(nv-v)));v=nv
        if change<1e-9:break
    else:raise AssertionError('slope transition failed to converge')
    # Stored consumer must use actual float32 terrain, including tiny unchanged values.
    v=v.astype(t['heights'].dtype).astype(float)
    changed=v!=h
    out=B/'candidate';out.mkdir(exist_ok=True)
    tt=dict(t);tt['heights']=v.astype(t['heights'].dtype)
    np.savez_compressed(out/'terrain.npz',**tt)
    np.savez_compressed(B/'selection.npz',allowed=allowed,scope=scope)
    rows=[]
    for label,rr,cc in [('optical_nw',889,402),('optical_ne',889,403),('optical_sw',890,402),('optical_se',890,403),('bridge_nw',898,402),('bridge_ne',898,403),('bridge_sw',899,402),('bridge_se',899,403)]:
        rows.append(dict(label=label,row=rr,col=cc,x=cc*6,z=12282-rr*6,before=float(h[rr,cc]),after=float(v[rr,cc]),changed=bool(changed[rr,cc]),reserve=bool(t['reserve'][rr,cc]),platform=bool(t['platform'][rr,cc])))
    report=dict(status='PROPOSAL_BUILT_PENDING_INDEPENDENT_FACE_CONSUMER',inputs={str(SRC/name):sha(SRC/name) for name in ['terrain.npz','plane.npy','visible-field.npy']},candidate_sha256=sha(out/'terrain.npz'),changed_vertices=int(changed.sum()),raised_to_1m=int(np.count_nonzero(changed&(v==1))),transition_vertices=int(np.count_nonzero(changed&(v<1))),transition_iterations=iteration+1,edge_limit_m=edge_limit,raise_max_m=float((v-h).max()),xz_bounds=[int(x[changed].min()),int(x[changed].max()),int(z[changed].min()),int(z[changed].max())],points=rows,limits=['Diagnostic only; no package or engine test yet.','Water, fields and object list not rebuilt.','Dry-pass fixed mask is not the contract of this water-only test; reserve/platform and shore geometry remain fixed.','Transition retains some subsea terrain; only the complete lifted core is a treatment area.'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
