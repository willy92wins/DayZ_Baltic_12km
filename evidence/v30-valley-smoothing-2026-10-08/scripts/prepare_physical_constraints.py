"""Repair omitted physical-control constraints, without changing contour objectives."""
from pathlib import Path
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
text=(B/'correct_connected_valley.py').read_text()
def rep(a,b):
 global text
 assert text.count(a)==1,a
 text=text.replace(a,b)
rep("out=B/'candidate-c1'","out=B/'candidate-c1physical'")
rep("out.mkdir(exist_ok=False)","out.mkdir(exist_ok=True);assert not (out/'terrain_valley.npz').exists()")
rep("E/'authoring-c1.json'","E/'authoring-c1physical.json'")
rep('newwet=np.where(zone,sd<0,oldwet)',"""observer_points=[]
observer_support=np.zeros_like(oldwet)
for p in ref['points']:
 lv=p.get('actual_pond_level_m')
 if lv is None:continue
 cc=p['x']/6.;rr=(12282-p['z'])/6.;r=int(np.floor(rr));c=int(np.floor(cc));fc=cc-c;fr=rr-r
 if fc>=fr:rc=[(r,c),(r,c+1),(r+1,c+1)];weights=[1-fc,fc-fr,fr]
 else:rc=[(r,c),(r+1,c),(r+1,c+1)];weights=[1-fr,fr-fc,fc]
 y=sum(h[i,j]*w for (i,j),w in zip(rc,weights))
 if lv-y<=.02:continue
 observer_points.append(dict(id=p['id'],rc=rc,weights=weights,limit=y))
 for q in rc:observer_support[q]=True
 support=observer_support&zone
 sd[support]=np.where(oldwet[support],-1.,1.)*np.maximum(.5,np.abs((h-water)[support]/.25))
newwet=np.where(zone,sd<0,oldwet)""")
rep('AA=(A.T@A).tocsc();ab=A.T@np.array(rhs);M=(sparse.eye(len(ids))+G.T@G).tocsc()',"""nr=[];nc=[];nv=[];physical_constant=[];physical_limit=[];physical_ids=[]
for p in observer_points:
 if not any(lookup[r*n+c]>=0 for r,c in p['rc']):continue
 row=len(physical_limit);const=0.
 for (rrc,ccc),w in zip(p['rc'],p['weights']):
  j=lookup[rrc*n+ccc]
  if j<0:const+=w*base[rrc,ccc]
  else:nr.append(row);nc.append(j);nv.append(w)
 physical_constant.append(const);physical_limit.append(p['limit']);physical_ids.append(p['id'])
N=sparse.csr_matrix((nv,(nr,nc)),shape=(len(physical_limit),len(ids)))
pn=np.array(physical_constant);limit=np.array(physical_limit)
AA=(A.T@A).tocsc();ab=A.T@np.array(rhs);M=(sparse.eye(len(ids))+G.T@G+N.T@N).tocsc()""")
rep('zb=x.copy();zg=project(G@x+c);ub=np.zeros_like(x);ug=np.zeros_like(c)',"zb=x.copy();zg=project(G@x+c);ub=np.zeros_like(x);ug=np.zeros_like(c)\nzn=np.minimum(N@x+pn,limit);un=np.zeros_like(limit)")
rep('x=solve(ab+rho*(zb-ub+G.T@(zg-ug-c)))','x=solve(ab+rho*(zb-ub+G.T@(zg-ug-c)+N.T@(zn-un-pn)))')
rep('gx=G@x+c;oldb=zb;oldg=zg','gx=G@x+c;nx=N@x+pn;oldb=zb;oldg=zg;oldn=zn')
rep('zb=np.clip(x+ub,lower,upper);zg=project(gx+ug)','zb=np.clip(x+ub,lower,upper);zg=project(gx+ug);zn=np.minimum(nx+un,limit)')
rep('ub+=x-zb;ug+=gx-zg','ub+=x-zb;ug+=gx-zg;un+=nx-zn')
rep('primal=max(float(np.max(np.abs(x-zb))),float(np.max(np.abs(gx-zg))))','primal=max(float(np.max(np.abs(x-zb))),float(np.max(np.abs(gx-zg))),float(np.max(np.abs(nx-zn),initial=0.)))')
rep('dual=float(rho*np.max(np.abs(zb-oldb+G.T@(zg-oldg))))','dual=float(rho*np.max(np.abs(zb-oldb+G.T@(zg-oldg)+N.T@(zn-oldn))))')
rep('ub*=rho/updated;ug*=rho/updated;rho=updated;solve=factorized(AA+rho*M)','ub*=rho/updated;ug*=rho/updated;un*=rho/updated;rho=updated;solve=factorized(AA+rho*M)')
rep("report=dict(status='JOINT_CONVERGED_PENDING_GATES'", "report=dict(physical_control_ids=physical_ids,physical_max_rise=float(np.max(N@x+pn-limit,initial=0.)),status='JOINT_CONVERGED_PENDING_GATES'")
(B/'repair_physical_valley.py').write_text(text)
print('Prepared physical sample inequalities and original wet support signs; no contour parameter changes.')
