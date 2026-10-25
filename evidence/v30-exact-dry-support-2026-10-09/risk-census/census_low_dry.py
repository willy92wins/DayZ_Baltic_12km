from pathlib import Path
import sys,json,csv,hashlib,time
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0,'E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
from audit_visible_field_domain import clip,area,UNIT
B=Path(__file__).parent;R=Path('E:/DayZ-Baltic-Build')
SOURCE=B.parent/'candidate/terrain.npz';PFILE=B.parent/'candidate/plane.npy';FFILE=B.parent/'candidate/visible-field.npy'
UPPER=1.79999;SEA=.85;CORNERS=([0,1,3],[0,2,3]);OFFSETS=((0,0),(0,1),(1,0),(1,1))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def polygon(values):
 poly=UNIT.copy()
 for v in values:poly=clip(poly,v)
 return poly

def interval(values):
 # Intersection of strict linear half-planes on the common edge t in [0,1].
 lo=np.zeros(values.shape[0]);hi=np.ones(values.shape[0])
 for d in np.moveaxis(values,1,0):
  a,b=d[:,0],d[:,1];delta=b-a;cross=np.zeros(len(a));np.divide(-a,delta,out=cross,where=abs(delta)>1e-14)
  crossing=np.clip(cross,0,1);lower=np.where((a<=0)&(b>0),crossing,0);upper=np.where((a>0)&(b<=0),crossing,1);upper[(a<=0)&(b<=0)]=0
  lo=np.maximum(lo,lower);hi=np.minimum(hi,upper)
 return lo,hi

def shared(a,b):
 al,ah=interval(a);bl,bh=interval(b);return np.minimum(ah,bh)-np.maximum(al,bl)>1e-8

def controls():
 assert area(polygon(np.array([[1,1,1],[1,1,1],[1,1,1]])))==18
 h=np.array([0.,2.,0.]);assert abs(area(polygon(np.array([2-h,h-1,h+.1])))-4.5)<1e-10
 h=np.full(3,1.5);f=np.array([1.6,1.2,1.2]);assert abs(area(polygon(np.array([1.8-h,h-.85,h-f])))-16.875)<1e-10
 assert area(polygon(np.array([1.8-h,h-1.6,h-f])))==0
 h=np.full(3,.7);assert area(polygon(np.array([1.8-h,h-.85,h-.6])))==0
 a=np.array([[[1,-1]],[[1,0]],[[1,1]]],float);b=np.array([[[-1,1]],[[0,1]],[[-1,1]]],float)
 assert shared(a,b).tolist()==[False,True,True]
 c=np.array([[[1,-1],[-1,1]]],float);lo,hi=interval(c);assert hi[0]-lo[0]==0
 return ['18m2_dry_triangle','4_5m2_height_band','16_875m2_sloping_visible_water_excluded','higher_physical_plane_excludes_triangle','ocean_submerged_excluded','zero_width_contact_not_connected','two_halfplanes_zero_width']

def main():
 begin=time.monotonic();checks=controls();assert sha(SOURCE)=='682d5553480e779cda1874725dd6a8a5a3615c356b65c546c77342f251857244'
 t=dict(np.load(SOURCE));h=t['heights'].astype(float);p=np.load(PFILE);f=np.load(FFILE)
 low=np.minimum.reduce((h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]));high=np.maximum.reduce((h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]));base=np.fmax(p,SEA)
 candidate=(low<UPPER)&(high>base)&(base<UPPER);rr,cc=np.nonzero(candidate);n=len(rr)
 ground=np.stack((h[rr,cc],h[rr,cc+1],h[rr+1,cc],h[rr+1,cc+1]),axis=1);visible=np.where(np.isfinite(p[rr,cc,None]),f[rr,cc],SEA)
 constraints=np.stack((UPPER-ground,ground-base[rr,cc,None],ground-visible),axis=1);assert np.isfinite(constraints).all()
 areas=np.zeros((n,2));centres=np.zeros((n,2,3));bounds=np.zeros((n,2,4))
 for index,(r,c) in enumerate(zip(rr,cc)):
  xyz=np.c_[[c*6,c*6+6,c*6,c*6+6],ground[index],[12282-r*6,12282-r*6,12276-r*6,12276-r*6]]
  for face,slots in enumerate(CORNERS):
   poly=polygon(constraints[index][:,slots]);value=area(poly);areas[index,face]=value
   if value<=1e-9:continue
   world=poly@xyz[slots];xz=world[:,[0,2]];bounds[index,face]=[*xz.min(axis=0),*xz.max(axis=0)]
   weights=[];points=[]
   for k in range(1,len(poly)-1):
    a=poly[[0,k,k+1]];weights.append(area(a));points.append(np.mean(a,axis=0)@xyz[slots])
   centres[index,face]=np.average(points,axis=0,weights=weights)
  if index%15000==0:print(json.dumps(dict(cells=index,total=n,seconds=time.monotonic()-begin)),flush=True)
 active=areas>1e-9;local=np.full((n,2),-1,np.int32);local[active]=np.arange(active.sum());lookup=np.full(p.shape,-1,np.int32);lookup[rr,cc]=np.arange(n);edges=[]
 def append(a,b,yes):
  ok=(a>=0)&(b>=0)&yes;edges.append(np.c_[a[ok],b[ok]])
 append(local[:,0],local[:,1],shared(constraints[:,:,[0,3]],constraints[:,:,[0,3]]))
 for axis in ('east','south'):
  possible=cc<p.shape[1]-1 if axis=='east' else rr<p.shape[0]-1;src=np.flatnonzero(possible)
  dst=lookup[rr[src]+(axis=='south'),cc[src]+(axis=='east')];keep=dst>=0;src,dst=src[keep],dst[keep]
  sa,sb,fa,fb=([1,3],[0,2],0,1) if axis=='east' else ([2,3],[0,1],1,0)
  append(local[src,fa],local[dst,fb],shared(constraints[src][:,:,sa],constraints[dst][:,:,sb]))
 pairs=np.concatenate(edges);nodes=int(active.sum());graph=coo_matrix((np.ones(len(pairs),np.uint8),(pairs[:,0],pairs[:,1])),shape=(nodes,nodes)).tocsr();count,labels=connected_components(graph,directed=False)
 totals=np.bincount(labels,weights=areas[active],minlength=count);centroid=np.array([np.bincount(labels,weights=areas[active]*centres[active,k],minlength=count) for k in range(3)]).T/totals[:,None]
 # A component centroid can lie in a pond-shaped hole. Report an actual dry
 # interior point from its largest convex native fragment as the probe pose.
 largest=np.zeros(count);np.maximum.at(largest,labels,areas[active]);chosen=np.full(count,nodes,np.int64);eligible=areas[active]==largest[labels];np.minimum.at(chosen,labels[eligible],np.flatnonzero(eligible));representative=centres[active][chosen]
 boxes=np.c_[np.full((count,2),np.inf),np.full((count,2),-np.inf)]
 for k in range(4):
  (np.minimum.at if k<2 else np.maximum.at)(boxes[:,k],labels,bounds[active,k])
 engineering=np.zeros(count,bool);narva=np.zeros(count,bool);inland=np.zeros(count,bool);bits=np.zeros(count,np.int32)
 for face,slots in enumerate(CORNERS):
  use=active[:,face];r,c=rr[use],cc[use];labs=labels[local[use,face]]
  np.logical_or.at(inland,labs,np.isfinite(p[r,c]))
  for slot in slots:
   dr,dc=OFFSETS[slot];np.logical_or.at(engineering,labs,t['reserve'][r+dr,c+dc]|t['platform'][r+dr,c+dc]);np.logical_or.at(narva,labs,t['narva'][r+dr,c+dc]);np.bitwise_or.at(bits,labs,1<<t['cls'][r+dr,c+dc].astype(int))
 rows=[dict(component=i,area_m2=float(totals[i]),x=float(representative[i,0]),y=float(representative[i,1]),z=float(representative[i,2]),centroid_x=float(centroid[i,0]),centroid_z=float(centroid[i,2]),xmin=float(boxes[i,0]),zmin=float(boxes[i,1]),xmax=float(boxes[i,2]),zmax=float(boxes[i,3]),touches_inland_plane=bool(inland[i]),touches_engineering_vertex=bool(engineering[i]),touches_narva=bool(narva[i]),incident_vertex_classes=','.join(str(j) for j in range(8) if bits[i]&(1<<j))) for i in range(count)]
 rows.sort(key=lambda v:-v['area_m2'])
 with (B/'components.csv').open('w',newline='') as out:
  writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 component_by_face=np.full((n,2),-1,np.int32);component_by_face[active]=labels
 # The reported point is allowed to leave the low-elevation risk band after repair.
 x,z=2718.4852496,6812.812874;r,c=int((12282-z)//6),int(x//6);aa,bb=x/6-c,(12282-z)/6-r;face=0 if aa>=bb else 1;weights=np.array([1-aa,aa-bb,bb]) if face==0 else np.array([1-bb,bb-aa,aa]);idx=int(lookup[r,c]);hc=np.array([h[r,c],h[r,c+1],h[r+1,c],h[r+1,c+1]])
 target=dict(x=x,z=z,height_m=float(weights@hc[CORNERS[face]]),inside_elevation_risk_band=bool(idx>=0 and np.all(constraints[idx][:,CORNERS[face]]@weights>0)))
 np.savez_compressed(B/'native-index.npz',rows=rr,cols=cc,areas=areas,labels=component_by_face,bounds=bounds,centres=centres)
 result=dict(status='GLOBAL_LOW_DRY_CANDIDATE_INDEX_NOT_RENDER_VERDICT',native_triangles=2*p.size,candidate_cells=n,active_fragments=nodes,positive_width_connections=len(pairs),components=count,components_at_least_1m2=int((totals>=1).sum()),area_m2=float(totals.sum()),thresholds=dict(lower_sea_crest_m=SEA,upper_dry_target_m=UPPER,rounding_exclusion_m=.00001),target=target,largest=rows[:15],controls=checks,inputs={str(path):sha(path) for path in (SOURCE,PFILE,FFILE)},seconds=time.monotonic()-begin,limits=['All native faces considered; outputs represent an elevation-risk index, not all possible graphical defects.','No assertion that every low dry component renders water, nor that higher terrain is immune.','Engineering/Narva flags mean at least one incident vertex, not that the entire polygon is engineered.','No terrain, water level, model, package or game process modified.'])
 (B/'census.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['largest','inputs']},indent=2))
if __name__=='__main__':main()
