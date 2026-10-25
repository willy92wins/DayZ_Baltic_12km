from pathlib import Path
import sys,json,time,hashlib,shutil
import numpy as np
from scipy.optimize import minimize

B=Path(__file__).parent; R=B.parent; OLD=R/'v30-volkhov-wet-support-20261009'; S=R/'v30-strict-dry-composition-20261009/candidate'
sys.path[:0]=[str(R/'v30-native-hinge-finish-20261009'),str(R/'v30-surface-crease-audit-20261009')]
from verify_hinges import face_normals,edges
from audit_native_surface import incident_any
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (B/'authoring.json').exists()
t=dict(np.load(OLD/'candidate/terrain.npz')); h=np.load(S/'terrain.npz')['heights'].astype(float); seed=t['heights'].astype(float); result=seed.copy(); d=np.load(OLD/'domain.npz'); domain=np.load(OLD/'crease-repair-domain.npz'); repair=domain['repair']; groups=domain['groups']; dry=np.load(R/'v30-volkhov-bed-proposal-20261009/exact-support-discovery.npz')['dry_lower_uplift']
specs={'diagonal':([(0,0),(0,1),(1,0),(1,1)],[0,1,3],[0,2,3]),'vertical':([(0,0),(0,1),(1,1),(1,2)],[0,1,2],[1,2,3]),'horizontal':([(0,0),(1,0),(1,1),(2,1)],[0,1,2],[1,2,3])}
original=dict(edges(*face_normals(h))); matrices={}
for kind,(offsets,ta,tb) in specs.items():
    xz=np.array([[c*6,-r*6] for r,c in offsets]); ms=[]
    for tri in [ta,tb]:
        coeff=np.linalg.inv(np.column_stack([xz[tri],np.ones(3)])); m=np.zeros((3,4));m[0,tri]=-coeff[0];m[2,tri]=-coeff[1];ms.append(m)
    matrices[kind]=ms
started=time.monotonic(); outcomes=[]; control_error=0.; derivative_error=0.
for gid in sorted(set(groups[repair].tolist())):
    mask=repair&(groups==gid); ids=np.flatnonzero(mask); index=np.full(h.size,-1,np.int32);index[ids]=np.arange(len(ids)); packs=[]
    for kind,(offsets,_,_) in specs.items():
        rr,cc=np.nonzero(incident_any(mask,kind)); quad=np.array([(rr+dr)*2048+cc+dc for dr,dc in offsets]).T; mapping=index[quad]; var=mapping>=0
        assert not np.any(repair.ravel()[quad]&~var),'No cross-group hinge variables'
        ma,mb=matrices[kind]; vals=h.ravel()[quad]; na=vals@ma.T;nb=vals@mb.T;na[:,1]=1;nb[:,1]=1
        normA=np.linalg.norm(na,axis=1);normB=np.linalg.norm(nb,axis=1);unA=na/normA[:,None];unB=nb/normB[:,None]
        cos=np.einsum('ij,ij->i',unA,unB); angle=np.degrees(np.arctan2(np.linalg.norm(np.cross(unA,unB),axis=1),cos))
        control_error=max(control_error,float(abs(angle-original[kind][rr,cc]).max(initial=0)))
        limit=np.minimum(angle+2,np.maximum(angle,10)+.00005); rad=np.deg2rad(limit); scale=np.maximum(np.sin(rad),.01)
        slopesA=np.tan(np.maximum(np.arctan(np.hypot(na[:,0],na[:,2])),np.deg2rad(35))+np.deg2rad(.00005));slopesB=np.tan(np.maximum(np.arctan(np.hypot(nb[:,0],nb[:,2])),np.deg2rad(35))+np.deg2rad(.00005))
        packs.append((quad,mapping,var,ma,mb,np.cos(rad),scale,slopesA,slopesB))
    cached=[None,None,None]
    def evaluate(x):
        if cached[0] is not None and np.array_equal(cached[0],x):return cached[1],cached[2]
        work=result.ravel().copy();work[ids]=x; cons=[]; jac=[]
        for quad,mapping,var,ma,mb,limit,scale,slopeA,slopeB in packs:
            vals=work[quad];na=vals@ma.T;nb=vals@mb.T;na[:,1]=1;nb[:,1]=1
            normA=np.linalg.norm(na,axis=1);normB=np.linalg.norm(nb,axis=1);unA=na/normA[:,None];unB=nb/normB[:,None]
            cos=np.einsum('ij,ij->i',unA,unB)
            dc=((unB-cos[:,None]*unA)/normA[:,None])@ma+((unA-cos[:,None]*unB)/normB[:,None])@mb
            sa=np.hypot(na[:,0],na[:,2]);sb=np.hypot(nb[:,0],nb[:,2]);dsa=(na[:,0,None]*ma[0]+na[:,2,None]*ma[2])/np.maximum(sa[:,None],1e-10);dsb=(nb[:,0,None]*mb[0]+nb[:,2,None]*mb[2])/np.maximum(sb[:,None],1e-10)
            for val,der in [((cos-limit)/scale,dc/scale[:,None]),(slopeA-sa,-dsa),(slopeB-sb,-dsb)]:
                out=np.zeros((len(quad),len(ids)));rows,cols=np.nonzero(var);np.add.at(out,(rows,mapping[rows,cols]),der[rows,cols]);cons.append(val);jac.append(out)
        cached[:]=[x.copy(),np.concatenate(cons),np.concatenate(jac)];return cached[1],cached[2]
    x0=seed.ravel()[ids]; lower=h.ravel()[ids]+np.minimum(.425,dry.ravel()[ids]);upper=h.ravel()[ids]+.425
    x0=np.clip(x0,lower,upper);rng=np.random.default_rng(66000+gid);direction=rng.normal(size=len(ids));direction/=np.linalg.norm(direction);eps=1e-5
    cons,jac=evaluate(x0);error=np.max(abs((evaluate(x0+eps*direction)[0]-evaluate(x0-eps*direction)[0])/(2*eps)-jac@direction));derivative_error=max(derivative_error,float(error));assert error<1e-7;assert control_error<1e-9
    iteration=[0]
    def callback(x):
        iteration[0]+=1
        if iteration[0]%10==0:print(json.dumps(dict(group=gid,iteration=iteration[0],seconds=time.monotonic()-started,min_constraint=float(evaluate(x)[0].min()))),flush=True)
        if time.monotonic()-started>300:raise TimeoutError('EV66 total 300 s budget')
    res=minimize(lambda x: .5*np.sum((x-x0)**2),x0,jac=lambda x:x-x0,method='SLSQP',bounds=list(zip(lower,upper)),
        constraints=[dict(type='ineq',fun=lambda x:evaluate(x)[0],jac=lambda x:evaluate(x)[1])],callback=callback,options=dict(maxiter=100,ftol=1e-11))
    result.ravel()[ids]=res.x
    outcome=dict(group=gid,variables=len(ids),success=bool(res.success),message=str(res.message),iterations=int(res.nit),minimum_constraint=float(evaluate(res.x)[0].min()));outcomes.append(outcome);print(json.dumps(outcome),flush=True)
out=B/'candidate';out.mkdir(exist_ok=False);np.savez_compressed(out/'terrain.npz',**(t|dict(heights=result.astype(np.float32))))
for name in ['plane.npy','visible-field.npy']:shutil.copyfile(OLD/'candidate'/name,out/name)
shutil.copyfile(OLD/'domain.npz',B/'domain.npz');shutil.copyfile(OLD/'verify.py',B/'verify.py')
report=json.loads((OLD/'authoring.json').read_text())|dict(terrain_sha256=sha(out/'terrain.npz'),status='CONSTRAINED_PROPOSAL_REQUIRES_CONSUMER',
    changed_vertices=int((result.astype(np.float32)!=h).sum()),solver_success=all(x['success'] for x in outcomes),solver_groups=outcomes,
    solver_message='Independent SLSQP groups',iterations=sum(x['iterations'] for x in outcomes),seconds=time.monotonic()-started,
    analytic_normal_vs_cross_product_error_degrees=control_error,analytic_constraint_derivative_error=derivative_error,prior_candidate_sha256=sha(OLD/'candidate/terrain.npz'))

for key in ['history','controls','gradient_direction_error','displacement_bending_energy']:report.pop(key,None)
report['author_precision_margin_degrees']=.00005
report['independent_consumer_precision_degrees']=.0001
(B/'authoring.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['object_translations','solver_groups']},indent=2))
