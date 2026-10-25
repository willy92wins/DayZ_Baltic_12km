from pathlib import Path
import sys,json
import numpy as np
import shapely
from shapely.geometry import shape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path('P:/DayZ_Baltic_12km_dev');E=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'tools/terrain'))
from v30_common import cell_planes,tri_sample
t=np.load('E:/DayZ-Baltic-Build/v30-fairway-candidate-bounded/terrain_v30.npz')
h=t['heights'].astype(float);plane=cell_planes(t['cls'],t['level'].astype(float))
fc=json.loads((E/'axes-corridors.geojson').read_text())['features']
design=json.loads((R/'tests/water_v3/water_v3.geojson').read_text())['features']
fig,ax=plt.subplots(figsize=(10,8));reports=[]
for f in design:
 g=shape(f['geometry'])
 if not g.intersects(shapely.box(8200,9900,8750,10400)):continue
 for p in (g.geoms if hasattr(g,'geoms') else [g]):
  if p.geom_type!='Polygon':continue
  xy=np.asarray(p.exterior.coords);ax.fill(xy[:,0],xy[:,1],color='#cbe4ef',alpha=.6)
for f in fc:
 if f['properties']['kind']!='axis':continue
 g=shape(f['geometry']);s=np.arange(24,g.length-24+.001,1.0);q=np.array([g.interpolate(v).coords[0] for v in s])
 rr=np.floor((12282-q[:,1])/6).astype(int);cc=np.floor(q[:,0]/6).astype(int)
 lv=np.maximum(np.nan_to_num(plane[rr,cc],nan=-np.inf),.5)
 ground=tri_sample(h,q[:,0],q[:,1]);depth=lv-ground
 k=np.argmin(depth);name=f['properties']['branch']
 reports.append(dict(branch=name,axis_samples=len(s),below_2_99=int(np.sum(depth<2.99)),dry_axis_samples=int(np.sum(depth<=0)),min_depth_m=float(depth[k]),worst_xz=q[k].tolist(),max_level_m=float(lv.max()),classes_at_axis=sorted(np.unique(t['cls'][rr,cc]).tolist())))
 ax.plot(q[:,0],q[:,1],color='navy',lw=1,label=name)
 ax.scatter(q[depth<2.99,0],q[depth<2.99,1],c=depth[depth<2.99],cmap='RdYlGn',vmin=-1,vmax=3,s=13)
 ax.annotate(name,q[len(q)//2]+[5,10],fontsize=9)
 for f2 in fc:
  if f2['properties']['kind']=='corridor24m' and f2['properties']['branch']==name:
   b=np.asarray(shape(f2['geometry']).exterior.coords);ax.plot(b[:,0],b[:,1],c='#b34b24',lw=.8)
ax.set(xlim=(8250,8700),ylim=(9950,10380),xlabel='X local (m)',ylabel='Z local (m)',title='Delta: ejes OSM y corredores útiles de 24 m')
ax.set_aspect('equal');ax.grid(alpha=.2);ax.legend(fontsize=8)
fig.text(.5,.01,'Azul claro: agua del diseño. Puntos: eje con menos de 3 m de calado (rojo = somero/seco).',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.03,1,1));fig.savefig(E/'delta-calado.png',dpi=150);plt.close(fig)
(E/'axis-samples.json').write_text(json.dumps(reports,indent=2)+'\n')
print(json.dumps(reports))
