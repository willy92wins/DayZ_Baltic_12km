"""Native NW-SE shared-edge angle constraints and their analytic Jacobian."""
import numpy as np


def crease_constraint(base, free, limit_degrees=20.):
    ids=np.full(base.shape,-1,int);ids[free]=np.arange(free.sum());n=int(free.sum())
    nr,nc=np.array(base.shape)-1
    # Triangle families agree with census_creases_v31, but coefficients are
    # assembled from individual native vertices for the optimization.
    derivatives=[];constants=[];index=np.empty((2,nr,nc),int)
    for kind in (0,1):
        for r in range(nr):
            for c in range(nc):
                nw,ne,sw,se=(r,c),(r,c+1),(r+1,c),(r+1,c+1)
                pairs=((nw,ne),(se,ne)) if kind==0 else ((sw,se),(sw,nw))
                jac=np.zeros((3,n));constant=np.array([0.,1.,0.])
                for axis,pair in zip((0,2),pairs):
                    for q,sgn in zip(pair,(1.,-1.)):
                        if ids[q]>=0:jac[axis,ids[q]]+=sgn/6
                        else:constant[axis]+=sgn*base[q]/6
                index[kind,r,c]=len(constants);derivatives.append(jac);constants.append(constant)
    J=np.asarray(derivatives);C=np.asarray(constants)
    one=np.r_[index[0].ravel(),index[0,:,:-1].ravel(),index[1,:-1,:].ravel()]
    two=np.r_[index[1].ravel(),index[1,:,1:].ravel(),index[0,1:,:].ravel()]
    active=np.any(J[one]!=0,axis=(1,2))|np.any(J[two]!=0,axis=(1,2));one=one[active];two=two[active]
    def normals(x):
        raw=np.einsum('tcn,n->tc',J,x)+C
        length=np.linalg.norm(raw,axis=1);unit=raw/length[:,None]
        return unit,length
    initial,_=normals(base[free]);original=np.sum(initial[one]*initial[two],axis=1)
    lower=np.minimum(original,np.cos(np.radians(limit_degrees)))
    def fun(x):
        unit,_=normals(x)
        return np.sum(unit[one]*unit[two],axis=1)-lower
    def jac(x):
        unit,length=normals(x)
        projection=np.einsum('tc,tcn->tn',unit,J)
        derivative=(J-unit[:,:,None]*projection[:,None,:])/length[:,None,None]
        return np.einsum('tcn,tc->tn',derivative[one],unit[two])+np.einsum('tc,tcn->tn',unit[one],derivative[two])
    return dict(type='ineq',fun=fun,jac=jac)
