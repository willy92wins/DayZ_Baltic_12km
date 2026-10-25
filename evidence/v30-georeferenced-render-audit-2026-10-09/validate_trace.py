"""Independent triangle consumer and adversarial finite-water boundary fixture."""
from pathlib import Path
import json
import numpy as np
from trace_native import trace,controls

def brute(h,f,origin,directions):
 triangles=[];labels=[];zmax=(len(h)-1)*6
 for r in range(len(h)-1):
  for c in range(h.shape[1]-1):
   x=np.array([c,c+1,c,c+1])*6;z=zmax-np.array([r,r,r+1,r+1])*6
   for label,y in ((1,h[r:r+2,c:c+2].ravel()),(2,f[r,c])):
    for ids in ([0,1,3],[0,3,2]):
     tri=np.c_[x[ids],y[ids],z[ids]]
     if np.isfinite(tri).all():triangles.append(tri);labels.append(label)
 a=np.array(triangles);labels=np.array(labels);e1=a[:,1]-a[:,0];e2=a[:,2]-a[:,0];s=origin-a[:,0]
 distances=[];kinds=[]
 for d in directions:
  cross=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,cross);valid=abs(det)>1e-12
  inv=np.zeros_like(det);inv[valid]=1/det[valid]
  u=np.einsum('ij,ij->i',s,cross)*inv;q=np.cross(s,e1);v=q@d*inv;t=np.einsum('ij,ij->i',e2,q)*inv
  ok=valid&(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)&(t>1e-9)
  t[~ok]=np.inf;i=np.argmin(t);distances.append(t[i] if np.isfinite(t[i]) else np.nan);kinds.append(labels[i] if np.isfinite(t[i]) else 0)
 return np.array(distances),np.array(kinds)

def main():
 results=controls()
 # A ray enters the x/z extent of a finite water plane below that plane.
 # There is no vertical wall there: first visible surface must be terrain.
 h=np.zeros((9,9));f=np.full((8,8,4),np.nan);f[:,3,:]=6
 origin=np.array([0.1,10,23.1]);d=np.array([[1,-1/3,0.] ]);d/=np.linalg.norm(d,axis=1)[:,None]
 _,kind,hit=trace(h,f,origin,d,sea=-100);expected,ek=brute(h,f,origin,d)
 assert np.max(abs(hit-expected))<1e-8 and np.array_equal(kind,ek),dict(case='no_false_water_sidewall',actual=hit.tolist(),expected=expected.tolist(),kind=kind.tolist(),expected_kind=ek.tolist())
 results.append('finite_water_has_no_vertical_sidewall')
 rng=np.random.default_rng(20261009);h=rng.uniform(1,5,(9,9));f=np.full((8,8,4),np.nan);f[2:6,2:6]=3.6
 origin=np.array([23.1,18,25.1]);target=np.c_[rng.uniform(1,47,500),np.zeros(500),rng.uniform(1,47,500)];d=target-origin;d/=np.linalg.norm(d,axis=1)[:,None]
 _,kind,hit=trace(h,f,origin,d,sea=-100);expected,ek=brute(h,f,origin,d)
 assert np.array_equal(np.isnan(hit),np.isnan(expected)) and np.nanmax(abs(hit-expected))<1e-7
 assert np.array_equal(kind,ek)
 results.append('500_rays_against_independent_triangle_intersection')
 report=dict(status='PASS',controls=results,max_independent_error_m=float(np.nanmax(abs(hit-expected))))
 (Path(__file__).parent/'trace-controls.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
