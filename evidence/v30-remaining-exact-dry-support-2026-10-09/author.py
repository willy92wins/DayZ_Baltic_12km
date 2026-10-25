from pathlib import Path
import sys,json,time,hashlib,shutil
import numpy as np
from scipy.ndimage import distance_transform_edt
B=Path(__file__).parent;R=B.parent;S=R/'v30-exact-dry-support-20261009/candidate'
sys.path[:0]=[str(R/'v30-native-hinge-finish-20261009')]
from author_hinges import K,LAMBDA,build_groups,controls
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (B/'authoring.json').exists()
t=dict(np.load(S/'terrain.npz'));original=t['heights'].astype(float);h=original.copy()
prior=np.load(R/'v30-native-hinge-finish-20261009/constraints.npz');scope=np.load(R/'v30-low-dry-domain-classification-20261009/domain.npz')
other_fixed=scope['fixed']|t['water']|t['beach']|(t['cls']!=0)|prior['large_lake_banks']
other_fixed[:11]=True;other_fixed[-11:]=True;other_fixed[:,:11]=True;other_fixed[:,-11:]=True
assert np.array_equal(other_fixed|prior['water_support'],prior['fixed']), 'Every prior non-water protection must be reconstructed exactly'
fixed=other_fixed|scope['wet_face_support']
target=scope['editable']&~fixed&(original<1.79999)
assert int(target.sum())==164 and not (target&fixed).any()
assert sha(S/'terrain.npz')=='682d5553480e779cda1874725dd6a8a5a3615c356b65c546c77342f251857244'
released=prior['fixed']&~fixed
assert not (released&(scope['wet_face_support']|other_fixed)).any()

allowed=(distance_transform_edt(~target,sampling=6)<=36)&~fixed
groups,coeff=build_groups(original,allowed)
minimum=original.copy();minimum[target]=float(np.float32(1.8));maximum=np.maximum(original,np.load(R/'v30-strict-dry-composition-20261009/candidate/terrain.npz')['heights'].astype(float)+.4);h[target]=float(np.float32(1.8))
flat=h.ravel();base=original.ravel();lower=minimum.ravel();upper=maximum.ravel();aa=np.sum(coeff*coeff,axis=1)[None,:]
initial_excess=0.
for ids,tri,radius in groups:
    initial_excess=max(initial_excess,float(np.max(np.sum(np.diff(flat[tri],axis=2)**2,axis=2)-radius,initial=0)))
assert initial_excess<1e-8,('Initial floor is not slope feasible',initial_excess)
np.savez_compressed(B/'constraints.npz',fixed=fixed,allowed=allowed,target=target,water_support=scope['wet_face_support'],released_dry= released,other_fixed=other_fixed,large_lake_banks=prior['large_lake_banks'])
started=time.monotonic();history=[]
for sweep in range(60):
    largest=0.
    for ids,tri,radius in groups:
        if not len(ids):continue
        grad=LAMBDA*(flat[ids]-base[ids])
        for (dr,dc),w in K.items():grad+=w*flat[ids+dr*2048+dc]
        step=-grad/(K[(0,0)]+LAMBDA);g=np.diff(flat[tri],axis=2);bb=np.sum(g*coeff[None,:,:],axis=2);cc=np.sum(g*g,axis=2)-radius;disc=np.sqrt(np.maximum(0,bb*bb-aa*cc))
        lo=np.maximum(((-bb-disc)/aa).max(axis=1),lower[ids]-flat[ids]);hi=np.minimum(((-bb+disc)/aa).min(axis=1),upper[ids]-flat[ids]);assert np.max(lo-hi,initial=0)<1e-8
        step=np.clip(step,lo,hi);flat[ids]+=step;largest=max(largest,float(abs(step).max(initial=0)))
    elapsed=time.monotonic()-started;row=dict(sweep=sweep+1,max_step_m=largest,seconds=elapsed);history.append(row)
    if sweep%10==0:print(json.dumps(row),flush=True)
    if largest<.0001 or elapsed>600:break
v=h.astype(np.float32);dest=B/'candidate';dest.mkdir(exist_ok=False);
for name in ['plane.npy','visible-field.npy']:shutil.copyfile(S/name,dest/name)
np.savez_compressed(dest/'terrain.npz',**(t|dict(heights=v)))
rr,cc=np.nonzero(v!=t['heights']);np.savez_compressed(B/'terrain-delta.npz',row=rr,col=cc,before=t['heights'][rr,cc],after=v[rr,cc])
report=dict(status='CANDIDATE_REQUIRES_INDEPENDENT_CONSUMER',source_sha256=sha(S/'terrain.npz'),terrain_sha256=sha(dest/'terrain.npz'),released_dry_vertices=int((released&allowed).sum()),target_vertices=int(target.sum()),editable_vertices=int(allowed.sum()),changed_vertices=len(rr),max_uplift_m=float((v-original).max()),min_target_m=float(v[target].min()),initial_slope_radius_excess=initial_excess,sweeps=len(history),seconds=time.monotonic()-started,history=history,controls=controls())
(B/'authoring.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='history'},indent=2))
