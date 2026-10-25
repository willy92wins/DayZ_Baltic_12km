from pathlib import Path
import sys,json,hashlib,shutil,time
import numpy as np
from scipy.optimize import minimize

B=Path(__file__).parent; R=B.parent; OLD=R/'v30-volkhov-bed-proposal-20261009'; S=R/'v30-strict-dry-composition-20261009/candidate'
sys.path.insert(0,str(R/'v30-native-hinge-finish-20261009'))
from author_hinges import K,direct_energy,controls
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (B/'authoring.json').exists()
assert sha(S/'terrain.npz')=='7bcfae7662acf3f83ff0f52434a3d9c3f1e8af745574b2fdc3ad689db123a990'
t=dict(np.load(S/'terrain.npz')); h=t['heights']; old=dict(np.load(OLD/'domain.npz')); s=np.load(OLD/'exact-support-discovery.npz'); core=s['wetcore']; allowed=old['allowed']; fixed=old['fixed']; shift=.425
assert not (core&fixed).any() and np.all(~core|allowed)
rr,cc=np.nonzero(allowed); r0,r1=rr.min()-3,rr.max()+4; c0,c1=cc.min()-3,cc.max()+4; sl=np.s_[r0:r1,c0:c1]
free=(allowed&~core&~fixed)[sl]; ix=np.flatnonzero(free); n=free.shape[1]
u=np.zeros(free.shape,float); u[core[sl]]=shift
lower=np.minimum(shift,s['dry_lower_uplift'][sl].ravel()[ix]); upper=np.full(len(ix),shift)
neighbours=[(ix+dr*n+dc,w) for (dr,dc),w in K.items()]
def objective(x):
    u.ravel()[ix]=x
    value=direct_energy(u)/2
    grad=sum(w*u.ravel()[at] for at,w in neighbours)
    return value,grad
rng=np.random.default_rng(65429); x0=(lower+upper)/2; direction=rng.normal(size=len(ix)); direction/=np.linalg.norm(direction)
val,grad=objective(x0); eps=1e-5
err=abs((objective(x0+eps*direction)[0]-objective(x0-eps*direction)[0])/(2*eps)-grad@direction)
assert err<1e-7
started=time.monotonic(); history=[]
def callback(x):
    if len(history)%25==0:print(json.dumps(dict(iteration=len(history)+1,seconds=time.monotonic()-started)),flush=True)
    history.append(float(objective(x)[0]))
    if time.monotonic()-started>120:raise TimeoutError('EV65 single solve time budget')
res=minimize(objective,x0,method='L-BFGS-B',jac=True,bounds=list(zip(lower,upper)),callback=callback,
    options=dict(maxiter=1000,ftol=1e-14,gtol=1e-8,maxls=30))
objective(res.x); v=h.copy(); v[sl]=(h[sl].astype(float)+u).astype(np.float32)
out=B/'candidate'; out.mkdir(exist_ok=False)
other=dict(np.load(OLD/'candidate/terrain.npz')); np.savez_compressed(out/'terrain.npz',**(other|dict(heights=v)))
for name in ['plane.npy','visible-field.npy']:shutil.copyfile(OLD/'candidate'/name,out/name)
np.savez_compressed(B/'domain.npz',**(old|dict(core=core)))
report=json.loads((OLD/'authoring.json').read_text())|dict(status='SOLVED_PROPOSAL_PENDING_VERIFICATION' if res.success else 'FAIL_CONVERGENCE',
    terrain_sha256=sha(out/'terrain.npz'),changed_vertices=int((v!=h).sum()),core_vertices=int(core.sum()),variables=len(ix),
    support_discovery_sha256=sha(OLD/'exact-support-discovery.npz'),solver_success=bool(res.success),solver_message=str(res.message),
    iterations=int(res.nit),seconds=time.monotonic()-started,gradient_direction_error=err,controls=controls(),
    displacement_bending_energy=float(res.fun),maximum_change_m=float(abs(v.astype(float)-h).max()),history=history)
(B/'authoring.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['object_translations','history']},indent=2))
