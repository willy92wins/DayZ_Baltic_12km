from pathlib import Path
import sys,json,hashlib,time
import numpy as np
import shapely
from shapely.geometry import shape,Point,Polygon,LineString,box,mapping
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import lsq_linear
from scipy.sparse import coo_matrix
B=Path(__file__).parent
sys.path.insert(0,'E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
from verify_native_turns import geometry,line_stats
from optimize_native_turns import face_constraints
SOURCE=Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz')
PFILE=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def ring(coords):
 line=LineString(coords);ds=np.linspace(0,line.length,max(8,int(np.ceil(line.length/3))),endpoint=False)
 xy=np.array([line.interpolate(s).coords[0] for s in ds]);sigma=6/(line.length/len(ds))
 return gaussian_filter1d(xy,sigma,axis=0,mode='wrap')

def main():
 assert not (B/'authoring.json').exists(),'one inverse-fit candidate'
 assert sha(SOURCE)=='fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6'
 t=dict(np.load(SOURCE));h=t['heights'].astype(float);p=np.load(PFILE);f=np.load('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009/preserved-field.npy');fixed=np.load('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/constraints.npz')['fixed']
 jobs=json.loads(Path('E:/DayZ-Baltic-Build/v30-rounded-terminal-footprint-20261009/discovery.json').read_text())['jobs'];job=next(j for j in jobs if j['features']==['stream_0207:0']);wet=shape(job['physical_geometry']);assert wet.geom_type=='Polygon'
 target=Polygon(ring(wet.exterior.coords),[ring(q.coords) for q in wet.interiors]);assert target.is_valid
 cx,cz=job['center'];r0,c0,r1,c1=job['box_cells'];lam=3.425
 assert np.max(abs(p[r0:r1,c0:c1][np.isfinite(p[r0:r1,c0:c1])]-lam))<1e-9
 rr,cc=np.mgrid[r0+1:r1,c0+1:c1];rr=rr.ravel();cc=cc.ravel();xy=np.c_[cc*6,12282-rr*6]
 radial=np.linalg.norm(xy-[cx,cz],axis=1);distance=shapely.distance(shapely.points(xy),target.boundary)
 keep=(radial<72)&(distance<30)&~fixed[rr,cc]&np.isin(t['cls'][rr,cc],[0,6]);rr,cc,xy=rr[keep],cc[keep],xy[keep];ids=rr*2048+cc
 inside=shapely.covers(target,shapely.points(xy));support=np.zeros(len(ids),bool)
 for dr,dc in ((0,0),(0,1),(1,0),(1,1)):support|=np.isfinite(p[rr-dr,cc-dc])
 assert np.all(~inside|support),'Target needs a new water plane: outside this hypothesis'
 low=h.ravel()[ids]-3;high=h.ravel()[ids]+3;low=np.maximum(low,np.where(inside,1.,max(1.8,lam+.0501)));high=np.minimum(high,np.where(inside,lam-.30,np.inf));assert np.all(low<high)
 lookup={int(key):i for i,key in enumerate(ids)};rows=[];cols=[];values=[];rhs=[]
 def equation(keys,weights,value,scale):
  row=len(rhs);rest=value;terms=[]
  for key,w in zip(keys,weights):
   key=int(key)
   if key in lookup:terms.append((lookup[key],w))
   else:rest-=w*h.ravel()[key]
  if not terms:return
  rhs.append(rest*scale)
  for j,w in terms:rows.append(row);cols.append(j);values.append(w*scale)
 # Actual native triangle weights of every target shoreline station.
 samples=[]
 for boundary in (target.exterior,*target.interiors):
  line=LineString(boundary);ds=np.arange(0,line.length,1.)
  for s in ds:
   x,z=line.interpolate(s).coords[0]
   if np.hypot(x-cx,z-cz)>60:continue
   rf,cf=(12282-z)/6,x/6;r,c=int(rf),int(cf);a,b=rf-r,cf-c
   assert np.isfinite(p[r,c]) and abs(p[r,c]-lam)<1e-9
   if b>=a:keys=[r*2048+c,r*2048+c+1,(r+1)*2048+c+1];weights=[1-b,b-a,a]
   else:keys=[r*2048+c,(r+1)*2048+c,(r+1)*2048+c+1];weights=[1-a,a-b,b]
   equation(keys,weights,lam,12.);samples.append([x,z])
 for key in ids:equation([key],[1],h.ravel()[key],.25)
 for r in range(r0-2,min(r1+1,2046)):
  for c in range(c0-2,min(c1+1,2046)):
   for weight,offsets in [(2,[(0,0,1),(1,1,1),(0,1,-1),(1,0,-1)]),(1,[(0,1,1),(1,1,1),(0,0,-1),(1,2,-1)]),(1,[(1,0,1),(1,1,1),(0,0,-1),(2,1,-1)])]:
    equation([(r+dr)*2048+c+dc for dr,dc,w in offsets],[w for dr,dc,w in offsets],0,np.sqrt(weight)*.5)
 A=coo_matrix((values,(rows,cols)),shape=(len(rhs),len(ids))).tocsr();start=time.monotonic();result=lsq_linear(A,np.array(rhs),bounds=(low,high),tol=1e-10,max_iter=100,lsmr_tol=1e-10,lsmr_maxiter=1000)
 v=h.copy();v.ravel()[ids]=result.x.astype(np.float32);changed=ids[v.ravel()[ids]!=h.ravel()[ids]]
 out={k:a.copy() for k,a in t.items()};out['heights']=v.astype(np.float32);level=float(np.nanmedian(t['level'][rr[t['cls'][rr,cc]==6],cc[t['cls'][rr,cc]==6]]))
 for key,wetflag in zip(ids,inside):
  r,c=divmod(int(key),2048);out['cls'][r,c]=6 if wetflag else 0;out['water'][r,c]=wetflag;out['level'][r,c]=level if wetflag else np.nan
 candidate=B/'candidate';candidate.mkdir(exist_ok=False);np.savez_compressed(candidate/'terrain.npz',**out);np.savez_compressed(B/'delta.npz',ids=changed,before=h.ravel()[changed],after=v.ravel()[changed],authorized_ids=ids)
 cells=[(r,c) for r in range(r0,r1) for c in range(c0,c1) if np.isfinite(p[r,c])];field=np.repeat(p[:,:,None],4,axis=2);before=geometry(h,field,cells);after=geometry(v,field,cells);extent=box(c0*6,12282-r1*6,c1*6,12282-r0*6)
 def lines(poly):
  z=shapely.line_merge(poly.boundary.difference(extent.boundary.buffer(.001)));return [q for q in getattr(z,'geoms',[z]) if q.geom_type=='LineString' and q.length>24]
 a,b=line_stats(lines(before)),line_stats(lines(after));fun,jac,faces=face_constraints(ids,h)
 report=dict(status='INVERSE_CONTOUR_CANDIDATE_REQUIRES_CONSUMER',source_sha256=sha(SOURCE),candidate_sha256=sha(candidate/'terrain.npz'),target=mapping(target),target_samples=samples,variables=len(ids),equations=len(rhs),solver_success=bool(result.success),solver_message=result.message,iterations=result.nit,cost=float(result.cost),optimality=float(result.optimality),seconds=time.monotonic()-start,changed_vertices=len(changed),class_changes=int(np.count_nonzero(t['cls']!=out['cls'])),before=a,after=b,area_before_m2=before.area,area_after_m2=after.area,new_water_m2=after.difference(before).area,lost_water_m2=before.difference(after).area,hausdorff_m=float(shapely.hausdorff_distance(before.boundary,after.boundary)),minimum_slope_constraint=float(np.min(fun(v.ravel()[ids]-h.ravel()[ids]))))
 (B/'authoring.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['target','target_samples']},indent=2))
if __name__=='__main__':main()
