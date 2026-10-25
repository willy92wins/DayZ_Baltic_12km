"""Freeze only independently located contour regressions for C's single correction."""
from pathlib import Path
import sys,json
import numpy as np,shapely
from shapely.geometry import Point
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008');sys.argv=[sys.argv[0],'c']
scope={};code=(B/'verify_contour_valley.py').read_text()
exec(code[:code.index('outlines={};fig')],scope)
before,after,cut=scope['before'],scope['after'],scope['cut']
points=[];small=[]
for p in getattr(before,'geoms',[before]):
 if p.area<200:
  small.append(p.buffer(6.));continue
for name,source,target in [('source_to_C',before,after),('C_to_source',after,before)]:
 boundary=source.boundary.difference(cut)
 for line in getattr(boundary,'geoms',[boundary]):
  if line.geom_type!='LineString':continue
  sample=shapely.line_interpolate_point(line,np.arange(0,line.length,.5))
  distances=shapely.distance(sample,target.boundary)
  for p,d in zip(sample[distances>4.0],distances[distances>4.0]):points.append(dict(kind=name,x=p.x,z=p.y,distance=float(d)))
# R1 alone fails the turn gate. Pin new >30 degree kinks only where the old
# native line at the nearest arc position was at least 3 degrees smoother.
a=scope['axes']['R1'];rc=np.array(a['removed_cells']);rs,cs=rc.T
box=shapely.box(cs.min()*6-18,12282-(rs.max()+1)*6-18,(cs.max()+1)*6+18,12282-rs.min()*6+18)
aa=shapely.line_merge(before.boundary.intersection(box).difference(cut));bb=shapely.line_merge(after.boundary.intersection(box).difference(cut))
oldlines=[l for l in getattr(aa,'geoms',[aa]) if l.geom_type=='LineString' and l.length>12]
def angle(p,q,r):
 a=np.asarray(q)-p;b=np.asarray(r)-q
 return float(np.degrees(np.arccos(np.clip(np.dot(a,b)/max(np.linalg.norm(a)*np.linalg.norm(b),1e-12),-1,1))))
for line in getattr(bb,'geoms',[bb]):
 if line.geom_type!='LineString' or line.length<24:continue
 for s in np.arange(6.,line.length-6.,2.):
  p=line.interpolate(s);turn=angle(line.interpolate(s-6).coords[0],p.coords[0],line.interpolate(s+6).coords[0])
  if turn<=30:continue
  old=min(oldlines,key=lambda q:q.distance(p));os=old.project(p)
  if os<6 or os>old.length-6:continue
  oldturn=angle(old.interpolate(os-6).coords[0],old.interpolate(os).coords[0],old.interpolate(os+6).coords[0])
  if turn>oldturn+3:points.append(dict(kind='R1_new_kink',x=p.x,z=p.y,before=oldturn,after=turn))
regions=small+[Point(p['x'],p['z']).buffer(6.) for p in points]
geometry=shapely.union_all(regions)
x,z=scope['x'],scope['z'];mask=shapely.intersects_xy(geometry,x,z)
np.savez_compressed(B/'contour-c1-fixed.npz',fixed=mask)
out=dict(status='C1_LOCAL_REGRESSION_GUARDS',protected_vertices=int(mask.sum()),small_components=len(small),points=points,method='6 m native support neighborhood of >4 m displacement or newly sharper R1 corner; complete small water bodies below 200 m2 retain source shape. No sigma change or post-fit metadata snapping.')
(scope['E']/'contour-c1-guards.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='points'},indent=2));print('regression_samples',len(points))
