"""Exact ray/heightfield intersections via native NW-SE triangle traversal."""
import numpy as np

def trace(h,field,origin,directions,sea=.85,maximum=1500.):
 h=np.asarray(h,float);origin=np.asarray(origin,float);d=np.asarray(directions,float);n=len(d);zmax=(h.shape[0]-1)*6
 time=np.zeros(n);active=np.ones(n,bool);hit=np.full(n,np.nan);kind=np.zeros(n,np.uint8);dc=d[:,0]/6;dr=-d[:,2]/6
 # A ray cannot cross more than 2*(rows+columns) native edges before leaving this heightfield.
 for iteration in range(2*sum(h.shape)+4):
  ids=np.flatnonzero(active)
  if not len(ids):break
  t=time[ids]+1e-8;point=origin+t[:,None]*d[ids];c=point[:,0]/6;r=(zmax-point[:,2])/6
  valid=(r>=0)&(r<h.shape[0]-1)&(c>=0)&(c<h.shape[1]-1)&(t<maximum)
  active[ids[~valid]]=False;ids=ids[valid];t=t[valid];point=point[valid];r=r[valid];c=c[valid]
  if not len(ids):continue
  ri=np.floor(r).astype(int);ci=np.floor(c).astype(int);fr=r-ri;fc=c-ci;first=fc>=fr
  def boundary(v,derivative):
   delta=np.where(derivative>0,np.floor(v)+1-v,np.floor(v)-v)
   result=np.full(len(v),np.inf);np.divide(delta,derivative,out=result,where=abs(derivative)>1e-14);return result
  leave=np.minimum(boundary(c,dc[ids]),boundary(r,dr[ids]))
  diff=dc[ids]-dr[ids];diag=np.full(len(ids),np.inf);np.divide(fr-fc,diff,out=diag,where=abs(diff)>1e-14);diag[diag<=1e-10]=np.inf;leave=np.minimum(leave,diag)
  ground=np.stack((h[ri,ci],h[ri,ci+1],h[ri+1,ci],h[ri+1,ci+1]),axis=1)
  water=field[ri,ci];best=np.full(len(ids),np.inf);material=np.zeros(len(ids),np.uint8)
  for label,values in ((1,ground),(2,water),(3,np.full_like(ground,sea))):
   gc=np.where(first,values[:,1]-values[:,0],values[:,3]-values[:,2]);gr=np.where(first,values[:,3]-values[:,1],values[:,2]-values[:,0]);surface=values[:,0]+fc*gc+fr*gr
   gap=point[:,1]-surface;slope=d[ids,1]-gc*dc[ids]-gr*dr[ids];dt=np.full(len(ids),np.inf);np.divide(-gap,slope,out=dt,where=(slope<0)&np.isfinite(gap));dt[(gap>=0)&(dt<0)]=np.inf
   # Finite water tiles have no vertical side wall. Entering their x/z
   # footprint below the plane is not a visible surface intersection.
   if label==1:dt[np.isfinite(gap)&(gap<=0)]=0
   else:dt[gap<0]=np.inf
   validhit=(dt<=leave+1e-8)&(dt<best);best[validhit]=dt[validhit];material[validhit]=label
  found=np.isfinite(best);selected=ids[found];hit[selected]=t[found]+best[found];kind[selected]=material[found];active[selected]=False
  remaining=ids[~found];time[remaining]=t[~found]+leave[~found]
 else:raise RuntimeError('Native triangle traversal did not terminate')
 return origin+hit[:,None]*d,kind,hit

def controls():
 r,c=np.indices((12,12));h=3+.02*(6*c)+.03*(66-6*r);field=np.full((11,11,4),np.nan);origin=np.array([15,25,55]);d=np.array([[0,-1,0],[.5,-.8,-.1],[-.1,-.9,-.6]],float);d/=np.linalg.norm(d,axis=1)[:,None]
 xyz,kind,hit=trace(h,field,origin,d,sea=-100)
 exact=(3+.02*origin[0]+.03*origin[2]-origin[1])/(d[:,1]-.02*d[:,0]-.03*d[:,2]);assert np.max(abs(hit-exact))<1e-9 and np.all(kind==1)
 f=np.full_like(field,8);xyz,kind,hit=trace(h,f,origin,d,sea=-100);assert np.max(abs(hit-(8-origin[1])/d[:,1]))<1e-9 and np.all(kind==2)
 xyz,kind,hit=trace(h,field,origin,d,sea=9);assert np.max(abs(hit-(9-origin[1])/d[:,1]))<1e-9 and np.all(kind==3)
 # A native triangular ridge is encountered before the flat-ground hit.
 hill=np.zeros((12,12));hill[4,5]=18;origin2=np.array([30,20,60]);d2=np.array([[0,-.5,-1.]])/np.sqrt(1.25);xyz,kind,hit=trace(hill,field,origin2,d2,sea=-100)
 assert kind[0]==1 and hit[0]<20/abs(d2[0,1])-5
 return ['inclined_plane_exact_three_rays','vertical_ray_supported','water_plane_intercepts_ground','sea_plane_intercepts_ground','native_ridge_not_skipped']

if __name__=='__main__':print(controls())
