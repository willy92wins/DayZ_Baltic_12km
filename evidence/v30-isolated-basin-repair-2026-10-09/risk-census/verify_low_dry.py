"""Independent area consumer: analytic bands and GEOS half-plane splits."""
from pathlib import Path
import sys,json,csv
import numpy as np
import shapely
from shapely.geometry import Polygon,LineString
from shapely.ops import split
sys.path.insert(0,'E:/DayZ-Baltic-Build/v30-low-water-components-20261009')
from discover_components import area as analytic_area
sys.path.insert(0,'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/tools/terrain')
from v30_common import tri_sample
B=Path(__file__).parent;R=Path('E:/DayZ-Baltic-Build');UP=1.79999

def geos_area(xz,constraints):
 polygon=Polygon(xz);matrix=np.c_[xz,np.ones(3)]
 for values in constraints:
  coeff=np.linalg.solve(matrix,values);a,b,c=coeff;n=np.hypot(a,b)
  if n<1e-12:
   if c<=0:return 0.
   continue
  anchor=-c*np.array([a,b])/(n*n);along=np.array([-b,a])/n*10000
  parts=split(polygon,LineString([anchor-along,anchor+along]))
  keep=[q for q in parts.geoms if a*q.representative_point().x+b*q.representative_point().y+c>0]
  polygon=shapely.union_all(keep)
  if polygon.is_empty:return 0.
 return polygon.area

def main():
 data=np.load(B/'native-index.npz');r,c=data['rows'],data['cols'];expected=data['areas'];h=np.load(B.parent/'candidate/terrain.npz')['heights'].astype(float);p=np.load(B.parent/'candidate/plane.npy');f=np.load(B.parent/'candidate/visible-field.npy')
 ground=np.stack((h[r,c],h[r,c+1],h[r+1,c],h[r+1,c+1]),axis=1).astype(float);visible=np.where(np.isfinite(p[r,c,None]),f[r,c],.85);base=np.fmax(p[r,c],.85)
 errors=[];parallel_count=0;sloping=[]
 for face,ids in enumerate(([0,1,3],[0,2,3])):
  g=ground[:,ids];v=visible[:,ids];flat=np.ptp(v,axis=1)<1e-12;cap=np.maximum(base[flat],v[flat,0]);a=analytic_area(UP-g[flat]);b=analytic_area(cap[:,None]-g[flat]);ref=np.where(cap<UP,np.maximum(0,a-b),0)
  errors.extend(abs(ref-expected[flat,face]).tolist());parallel_count+=int(flat.sum())
  indices=np.flatnonzero(~flat)
  if len(indices):
   chosen=indices[np.linspace(0,len(indices)-1,min(160,len(indices))).astype(int)]
   xy=np.array([[0,0],[6,0],[0,-6],[6,-6]],float)[ids]
   for i in chosen:
    value=geos_area(xy,np.array([UP-g[i],g[i]-base[i],g[i]-v[i]]));sloping.append(abs(value-expected[i,face]))
 assert max(errors,default=0)<1e-8 and max(sloping,default=0)<1e-8
 rows=list(csv.DictReader((B/'components.csv').open()));q=np.array([[float(row[k]) for k in ('x','y','z')] for row in rows]);height=tri_sample(h,q[:,0],q[:,2]);assert np.max(abs(height-q[:,1]))<1e-8
 cr=np.floor((12282-q[:,2])/6).astype(int);cc=np.floor(q[:,0]/6).astype(int);fc=q[:,0]/6-cc;fr=(12282-q[:,2])/6-cr;vv=f[cr,cc];fv=np.where(fc>=fr,vv[:,0]+fc*(vv[:,1]-vv[:,0])+fr*(vv[:,3]-vv[:,1]),vv[:,0]+fr*(vv[:,2]-vv[:,0])+fc*(vv[:,3]-vv[:,2]))
 assert np.all(height<UP) and np.all(height>np.fmax(p[cr,cc],.85)) and np.all(~np.isfinite(p[cr,cc])|(height>fv))
 # A component may surround a pond: the exposed probe must still be dry.
 report=dict(status='PASS_GEOMETRIC_INDEX_ONLY',analytic_triangles=parallel_count,analytic_max_area_error_m2=max(errors,default=0),geos_sloping_triangles=len(sloping),geos_max_area_error_m2=max(sloping,default=0),dry_representative_points=len(rows),native_sample_max_error_m=float(np.max(abs(height-q[:,1]))),limits=['Geometric area and dry probe locations checked independently; this is not a graphical defect verdict.'])
 (B/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
