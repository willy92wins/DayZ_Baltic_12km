"""Bounded native-gradient jump minimization on dry terrain; source water faces exact."""
from pathlib import Path
from collections import defaultdict
import json, sys, time, hashlib
import numpy as np
from scipy.ndimage import distance_transform_edt
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path[:0]=[str(W/'tools/terrain'),'E:/DayZ-Baltic-Build/v30-surface-crease-audit-20261009']
from relevel_bodies_v30 import label_bodies
from audit_native_surface import hinges,SOURCE,PLANE,FIXED,sha
LAMBDA=1/16
PATTERNS=[(2,[(0,0,1),(1,1,1),(0,1,-1),(1,0,-1)]),(1,[(0,1,1),(1,1,1),(0,0,-1),(1,2,-1)]),(1,[(1,0,1),(1,1,1),(0,0,-1),(2,1,-1)])]
def kernel():
    k=defaultdict(float)
    for w,p in PATTERNS:
        for ra,ca,a in p:
            for rb,cb,b in p:k[(rb-ra,cb-ca)]+=w*a*b
    return {key:v for key,v in k.items() if v}
K=kernel()

def direct_energy(h):
    q=h[:-1,:-1]+h[1:,1:]-h[:-1,1:]-h[1:,:-1]
    v=h[:-1,1:-1]+h[1:,1:-1]-h[:-1,:-2]-h[1:,2:]
    z=h[1:-1,:-1]+h[1:-1,1:]-h[:-2,:-1]-h[2:,1:]
    return 2*np.sum(q*q)+np.sum(v*v)+np.sum(z*z)

def controls():
    rng=np.random.default_rng(91872);h=rng.normal(size=(15,15));r,c=7,7
    grad=sum(w*h[r+dr,c+dc] for (dr,dc),w in K.items())
    a=h.copy();b=h.copy();a[r,c]+=1e-5;b[r,c]-=1e-5
    error=abs((direct_energy(a)-direct_energy(b))/4e-5-grad)
    assert error<1e-7
    a=h.copy();a[r,c]-=grad/K[(0,0)]
    assert direct_energy(a)<direct_energy(h)
    assert all(abs(dr)<5 and abs(dc)<5 for dr,dc in K)
    return dict(directional_derivative_error=error,explicit_energy_decreased=True,noninteracting_colours=True)

def prepare():
    assert sha(SOURCE)=='70f74c9334620c458880f728d3ff15cec7867ffe2bd8bd2e9d5135e1692b7ed5'
    assert sha(PLANE)=='d59dcdb908b4381a456629fb080a9769147b6fb1a3e321a6423bc931a0fb8803'
    t=dict(np.load(SOURCE));h=t['heights'].astype(float);p=np.load(PLANE)
    water_support=np.zeros(h.shape,bool)
    for dr,dc in ((0,0),(0,1),(1,0),(1,1)):water_support[dr:dr+2047,dc:dc+2047]|=np.isfinite(p)
    fixed=np.load(FIXED)['fixed']|water_support|t['water']|t['beach']|(t['cls']!=0)
    fixed[:11]=True;fixed[-11:]=True;fixed[:,:11]=True;fixed[:,-11:]=True
    labels=label_bodies(t['cls'],t['level']);lakes=np.zeros(h.shape,bool)
    for x,z in [(622.4,840),(10436.5,308.2)]:
        body=int(labels[round((12282-z)/6),round(x/6)]);assert body>0
        lakes|=distance_transform_edt(labels!=body,sampling=6)<=72
    fixed|=lakes
    sharp=np.zeros(h.shape,bool)
    for kind,values in hinges(h):
        r,c=np.nonzero(values>=10)
        offsets={'diagonal':[(0,0),(0,1),(1,0),(1,1)],'vertical':[(0,0),(0,1),(1,1),(1,2)],'horizontal':[(0,0),(1,0),(1,1),(2,1)]}[kind]
        for dr,dc in offsets:sharp[r+dr,c+dc]=True
    allowed=(distance_transform_edt(~sharp,sampling=6)<=36)&~fixed
    floor=np.minimum(h,1.8)
    np.savez_compressed(B/'constraints.npz',fixed=fixed,allowed=allowed,water_support=water_support,large_lake_banks=lakes)
    report=dict(source_sha256=sha(SOURCE),plane_sha256=sha(PLANE),previous_constraints_sha256=sha(FIXED),editable_vertices=int(allowed.sum()),water_support_vertices=int(water_support.sum()),large_lake_fixed_vertices=int(lakes.sum()),sharp_vertices=int(sharp.sum()),max_change_m=2,lambda_fidelity=LAMBDA,sweeps_budget=60,seconds_budget=600,controls=controls())
    (B/'discovery.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
    return t,h,allowed,floor

def build_groups(h,allowed):
    n=h.shape[0];r,c=np.nonzero(allowed);ids=r*n+c
    # Six incident faces ordered along their right-angle vertex (NW, NE/SW, SE).
    offsets=np.array([[0,1,n+1],[0,n,n+1],[-1,0,n],[-n,0,1],[-n-1,-n,0],[-n-1,-1,0]])
    coeff=np.array([[-1,0],[-1,0],[1,-1],[1,-1],[0,1],[0,1]])
    groups=[];base=h.ravel()
    for colour in range(25):
        ix=ids[(r%5)*5+c%5==colour];tri=ix[:,None,None]+offsets[None,:,:]
        vals=base[tri];g=np.diff(vals,axis=2);radius=np.maximum(np.sum(g*g,axis=2),(6*np.tan(np.deg2rad(35)))**2)
        groups.append((ix,tri,radius))
    return groups,coeff

def main():
    assert not (B/'authoring.json').exists(),'One bounded candidate only'
    t,h,allowed,floor=prepare();original=h.copy();groups,coeff=build_groups(h,allowed)
    flat=h.ravel();base=original.ravel();minimum=np.maximum(base-2,floor.ravel());maximum=base+2
    aa=np.sum(coeff*coeff,axis=1)[None,:];started=time.monotonic();history=[]
    for sweep in range(60):
        largest=0.
        for ids,tri,radius in groups:
            if not len(ids):continue
            grad=LAMBDA*(flat[ids]-base[ids])
            for (dr,dc),w in K.items():grad+=w*flat[ids+dr*2048+dc]
            step=-grad/(K[(0,0)]+LAMBDA)
            g=np.diff(flat[tri],axis=2);b=np.sum(g*coeff[None,:,:],axis=2);cc=np.sum(g*g,axis=2)-radius
            disc=np.sqrt(np.maximum(0,b*b-aa*cc))
            lo=np.maximum(((-b-disc)/aa).max(axis=1),minimum[ids]-flat[ids])
            hi=np.minimum(((-b+disc)/aa).min(axis=1),maximum[ids]-flat[ids])
            assert np.max(lo-hi,initial=0)<1e-8
            step=np.clip(step,lo,hi)*(1-1e-10)
            flat[ids]+=step;largest=max(largest,float(abs(step).max(initial=0)))
        elapsed=time.monotonic()-started;row=dict(sweep=sweep+1,max_step_m=largest,seconds=elapsed);history.append(row)
        if sweep%5==0:print(json.dumps(row),flush=True)
        if largest<.0001 or elapsed>600:break
    v=h.astype(np.float32);target=B/'candidate';target.mkdir(exist_ok=False)
    np.savez_compressed(target/'terrain.npz',**(t|dict(heights=v)))
    changed=v!=t['heights'];rr,cc=np.nonzero(changed)
    np.savez_compressed(B/'terrain-delta.npz',row=rr,col=cc,before=t['heights'][rr,cc],after=v[rr,cc])
    report=dict(status='CANDIDATE_REQUIRES_INDEPENDENT_CONSUMER',source_sha256=sha(SOURCE),candidate_sha256=sha(target/'terrain.npz'),constraints_sha256=sha(B/'constraints.npz'),changed_vertices=len(rr),maximum_change_m=float(abs(v-original).max()),seconds=time.monotonic()-started,sweeps=len(history),history=history)
    (B/'authoring.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='history'}),flush=True)

if __name__=='__main__':main()
