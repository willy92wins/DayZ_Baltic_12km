"""Read-only design diagnostic: native wet polygons and true signed smoothed contour."""
from pathlib import Path
import sys,json
import numpy as np,shapely
from scipy import ndimage
from shapely.geometry import Polygon,LineString,mapping
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008');scope={}
code=(B/'correct_shore.py').read_text();exec(code[:code.index('native=lines_for')],scope)
for k in ('W','E','h','water','patched','core','fixed','x','z','cls','t','lines_for'):
 globals()[k]=scope[k]
cells=list(zip(*np.nonzero(patched)));polys=[]
for r,c in cells:
 for dr,dc in ((0,1),(1,0)):
  rc=[(r,c),(r+dr,c+dc),(r+1,c+1)]
  xy=np.array([(j*6,12282-i*6) for i,j in rc]);d=np.array([h[i,j]-water[i,j] for i,j in rc]);points=[]
  if not np.isfinite(d).all():continue
  for i,j in ((0,1),(1,2),(2,0)):
   if d[i]<=0:points.append(xy[i])
   if d[i]*d[j]<0:points.append(xy[i]+d[i]/(d[i]-d[j])*(xy[j]-xy[i]))
  if len(points)>=3:polys.append(Polygon(np.round(points,7)))
old=shapely.union_all(polys,grid_size=1e-6)
domain=shapely.union_all([shapely.box(c*6,12282-(r+1)*6,(c+1)*6,12282-r*6) for r,c in cells])
cut=old.boundary.intersection(domain.boundary.buffer(.0001))
def rounded(ring):
 p=np.array(ring.coords);s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
 if s[-1]<36:return p
 q=np.linspace(0,s[-1],max(12,int(np.ceil(s[-1]/1.5))),endpoint=False)
 pp=np.c_[np.interp(q,s,p[:,0]),np.interp(q,s,p[:,1])]
 smooth=ndimage.gaussian_filter1d(pp,18/(s[-1]/len(q)),axis=0,mode='wrap')
 delta=smooth-pp;delta*=np.minimum(1.,4./np.maximum(np.linalg.norm(delta,axis=1),1e-12))[:,None]
 dist=shapely.distance(shapely.points(pp),cut)
 a=np.clip(dist/24.,0,1);a=a*a*(3-2*a)
 out=pp+a[:,None]*delta
 return np.vstack([out,out[:1]])
parts=[g for g in getattr(old,'geoms',[old]) if isinstance(g,Polygon)]
smooth=shapely.union_all([Polygon(rounded(g.exterior),[rounded(r) for r in g.interiors]) for g in parts])
assert smooth.is_valid,shapely.is_valid_reason(smooth)
rw,cw=np.nonzero(core);points=shapely.points(x[rw,cw],z[rw,cw])
inside=shapely.contains(smooth,points);dist=shapely.distance(points,smooth.boundary)
sd=np.full(h.shape,np.nan);sd[rw,cw]=np.where(inside,-dist,dist)
flip=core&~fixed&((sd<0)!=(cls>0))&np.isfinite(sd)&(np.abs(sd)>.01)
# Boundary edges of the clipped domain are not shoreline design.
away=shapely.distance(points,cut)>24
interior=np.zeros_like(core);interior[rw[away],cw[away]]=True;flip&=interior
np.savez_compressed(B/'contour-design.npz',sd=sd,core=core,interior=interior,flip=flip)
geometry=dict(original=mapping(old),smoothed=mapping(smooth),domain=mapping(domain))
(E/'contour-design.geojson').write_text(json.dumps(geometry)+'\n')
axes=json.loads(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/axes.json').read_text())
report=dict(status='DESIGN_DIAGNOSTIC_ONLY',flip_to_water=int((flip&(sd<0)).sum()),flip_to_dry=int((flip&(sd>0)).sum()),area_before=old.area,area_after=smooth.area,groups={})
fig,axs=plt.subplots(1,3,figsize=(15,6),layout='constrained')
for ax,(name,entry) in zip(axs,axes.items()):
 rc=np.array(entry['removed_cells']);rr,cc=rc.T
 box=shapely.box(cc.min()*6,12282-(rr.max()+1)*6,(cc.max()+1)*6,12282-rr.min()*6)
 region=(x>=box.bounds[0])&(x<=box.bounds[2])&(z>=box.bounds[1])&(z<=box.bounds[3])
 report['groups'][name]=dict(flip_to_water=int((flip&region&(sd<0)).sum()),flip_to_dry=int((flip&region&(sd>0)).sum()))
 for geom,col,label in ((old,'#397dba','Actual'),(smooth,'#338b6b','Contorno redondeado')):
  g=geom.boundary.intersection(box)
  for j,line in enumerate(getattr(g,'geoms',[g])):
   if hasattr(line,'coords'):ax.plot(*np.array(line.coords).T,c=col,lw=1.2,label=label if j==0 else None)
 ax.scatter(x[flip&region],z[flip&region],s=10,c='#c74945',label='Vértice cambia de lado')
 ax.set(xlim=(box.bounds[0]-6,box.bounds[2]+6),ylim=(box.bounds[1]-6,box.bounds[3]+6),aspect='equal',title=name);ax.legend(fontsize=7)
fig.savefig(E/'contour-topology.png',dpi=150)
(E/'contour-topology.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
