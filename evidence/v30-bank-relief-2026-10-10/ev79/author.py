"""Narva-only dry-bank smoothing after explicit semantic mask reconstruction; existing water support immutable."""
from pathlib import Path
import sys,time,json,hashlib,shutil
import numpy as np
from scipy.ndimage import distance_transform_edt,binary_dilation
B=Path(__file__).parent;R=B.parent
S=R/'v30-remaining-exact-dry-support-20261009/candidate'
sys.path.insert(0,str(R/'v30-native-hinge-finish-20261009'))
from author_hinges import K,LAMBDA,build_groups,controls
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED='b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36'
assert sha(S/'terrain.npz')==EXPECTED
assert not (B/'authoring.json').exists() and not (B/'candidate').exists(),'One calculation, preserve failed results'
t=dict(np.load(S/'terrain.npz'));base=t['heights'].astype(float);h=base.copy();n=len(h)
p=np.load(S/'plane.npy');f=np.load(S/'visible-field.npy')
assert h.shape==(2048,2048) and p.shape==(2047,2047) and f.shape==(2047,2047,4)
prior=dict(np.load(S.parent/'constraints.npz'))
corners=[(0,0),(0,1),(1,0),(1,1)]
hv=[base[dr:dr+2047,dc:dc+2047] for dr,dc in corners]
P=np.fmax(p,.85);F=np.where(np.isfinite(p)[:,:,None],f,.85)
support=np.zeros(h.shape,bool);water_floor=np.full(h.shape,.85)
for ids in [(0,1,3),(0,2,3)]:
    wet=np.logical_or.reduce([(P>hv[i])|(F[:,:,i]>hv[i]) for i in ids])
    for i in ids:
        dr,dc=corners[i];support[dr:dr+2047,dc:dc+2047]|=wet
for i,(dr,dc) in enumerate(corners):
    wf=water_floor[dr:dr+2047,dc:dc+2047]
    np.fmax(wf,np.fmax(P,F[:,:,i]),out=wf)
engineering=t['reserve']|t['platform']
engineering_halo=binary_dilation(engineering,structure=np.ones((3,3),bool))
m=dict(np.load(R/'v30-valley-smoothing-20261008/candidate-a/masks.npz'))
term=dict(np.load(R/'v30-native-terminal-finish-20261009/constraints.npz'))
rr,cc=np.indices(h.shape);x=cc*6;z=12282-rr*6
narva=(np.hypot(x-2417.1428225906,z-6889.8850822322)<=620)|t['narva']
border=(rr<11)|(rr>=2037)|(cc<11)|(cc>=2037)
other_fixed=(t['water']|t['beach']|(t['cls']!=0)|m['corridor']|m['summits']|border|term['controls'])
fixed=other_fixed|prior['large_lake_banks']|support|engineering_halo
flow=np.isin(t['cls'],[3,5,6]);distance=distance_transform_edt(~flow,sampling=6.)
bank_domain=(t['cls']==0)&(distance<=96)&narva
allowed=bank_domain&~fixed
guard=np.clip(distance_transform_edt(allowed,sampling=6.)/18.,0,1)
guard=guard**3*(10+guard*(-15+6*guard));cap=2*guard
lower=np.maximum(base-cap,np.maximum(np.minimum(base,1.8),np.minimum(base,water_floor+1e-4)))
upper=base+cap
assert np.all(lower<=base) and np.all(base<=upper)
np.savez_compressed(B/'constraints.npz',fixed=fixed,allowed=allowed,wet_support=support,engineering_halo=engineering_halo,cap=cap,lower=lower,bank_domain=bank_domain,narva=narva,other_fixed=other_fixed)
groups,coeff=build_groups(h,allowed)
flat=h.ravel();old=base.ravel();loflat=lower.ravel();hiflat=upper.ravel()
aa=np.sum(coeff*coeff,axis=1)[None,:]
history=[];started=time.monotonic()
for sweep in range(60):
    largest=0.
    for ids,tri,radius in groups:
        if not len(ids):continue
        grad=LAMBDA*(flat[ids]-old[ids])
        for (dr,dc),w in K.items():grad+=w*flat[ids+dr*n+dc]
        step=-grad/(K[(0,0)]+LAMBDA)
        g=np.diff(flat[tri],axis=2);bb=np.sum(g*coeff[None,:,:],axis=2)
        cc=np.sum(g*g,axis=2)-radius;disc=np.sqrt(np.maximum(0,bb*bb-aa*cc))
        lo=np.maximum(((-bb-disc)/aa).max(axis=1),loflat[ids]-flat[ids])
        hi=np.minimum(((-bb+disc)/aa).min(axis=1),hiflat[ids]-flat[ids])
        assert np.max(lo-hi,initial=0)<1e-8
        step=np.clip(step,lo,hi)*(1-1e-10);flat[ids]+=step;largest=max(largest,float(abs(step).max(initial=0)))
    row=dict(sweep=sweep+1,max_step_m=largest,seconds=time.monotonic()-started);history.append(row)
    if sweep%10==0:print(json.dumps(row),flush=True)
    if largest<1e-4 or row['seconds']>600:break
v=h.astype(np.float32);D=B/'candidate';D.mkdir()
np.savez_compressed(D/'terrain.npz',**(t|dict(heights=v)))
for name in ['plane.npy','visible-field.npy']:shutil.copyfile(S/name,D/name)
rr,cc=np.nonzero(v!=t['heights']);np.savez_compressed(B/'terrain-delta.npz',row=rr,col=cc,before=t['heights'][rr,cc],after=v[rr,cc])
delta=v.astype(float)-base
report=dict(status='CANDIDATE_PENDING_INDEPENDENT_CONSUMER',source_sha256=sha(S/'terrain.npz'),candidate_sha256=sha(D/'terrain.npz'),constraints_sha256=sha(B/'constraints.npz'),plane_sha256=sha(D/'plane.npy'),visible_field_sha256=sha(D/'visible-field.npy'),counts=dict(bank_vertices=int(bank_domain.sum()),editable_vertices=int(allowed.sum()),changed_vertices=len(rr),lowered=int((delta<0).sum()),raised=int((delta>0).sum()),water_support=int(support.sum()),engineering_halo=int(engineering_halo.sum())),delta_min=float(delta.min()),delta_max=float(delta.max()),params=dict(distance_from_flowing_m=96,transition_m=18,cap_m=2,lambda_fidelity=LAMBDA,max_sweeps=60,max_seconds=600),history=history,controls=controls(),seconds=time.monotonic()-started)
(B/'authoring.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='history'}),flush=True)
