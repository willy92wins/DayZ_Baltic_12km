"""Read-only discriminators: vector coverage, road protection, and delta depth rule."""
from pathlib import Path
import sys, json
import numpy as np
import shapely
from shapely.geometry import shape
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

R=Path('P:/DayZ_Baltic_12km_dev'); E=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'tools/terrain'))
from v30_common import raster_vertices, cell_planes
from audit_fairway_triangles_v30 import records, describe, save
from verify_roads_v30 import road_chains

t=np.load('E:/DayZ-Baltic-Build/v30-fairway-candidate-bounded/terrain_v30.npz')
w=np.load(R/'tests/terrain_v30/water_v30.npz')
h=t['heights'].astype(float); cls=t['cls']; planes=cell_planes(cls,t['level'])
fc=json.loads((E/'axes-corridors.geojson').read_text())['features']
design=json.loads((R/'tests/water_v3/water_v3.geojson').read_text())['features']
inland=shapely.union_all([shape(f['geometry']) for f in design if f['properties']['class']!='pond'])
roads=road_chains(); rp=[]
for p in roads:
 if len(p)<2:continue
 st=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
 s=np.arange(0,st[-1]+.5,1.)
 rp.append(np.column_stack([np.interp(s,st,p[:,i]) for i in (0,1)]))
tree=cKDTree(np.vstack(rp))
out=[]
for f in fc:
 if f['properties']['kind']!='corridor24m':continue
 g=shape(f['geometry']); rec=records(g,planes)
 ids=np.unique(rec['ids']); rr,cc=np.divmod(ids,2048); xz=np.column_stack([cc*6.,12282-rr*6.])
 dry=cls[rr,cc]==0
 rd=tree.query(xz)[0]
 inside=shapely.intersects_xy(inland,xz[:,0],xz[:,1])
 branch=next(shape(b['geometry']) for b in design if b['properties'].get('name')==f['properties']['branch'] and b['properties']['class']=='delta_navigable')
 edge=np.maximum(w['dist_bank'][rr,cc]-6.,0.)
 carving=np.maximum(-2.5,t['level'][rr,cc]-(.15+.45*edge))
 samples=[]
 for i in np.flatnonzero(dry):
  samples.append(dict(xz=xz[i].tolist(),height_m=float(h[rr[i],cc[i]]),road_distance_m=float(rd[i]),platform=bool(t['platform'][rr[i],cc[i]]),reserve=bool(t['reserve'][rr[i],cc[i]]),in_inland_design=bool(inside[i]),distance_branch_m=float(shapely.distance(shapely.Point(xz[i]),branch))))
 # Isolate the bed rule on already classified wet vertices; no outline alteration.
 deep=h.copy(); wet_delta=(cls[rr,cc]==4)
 deep[rr[wet_delta],cc[wet_delta]]=np.minimum(deep[rr[wet_delta],cc[wet_delta]],-2.55)
 report=dict(branch=f['properties']['branch'],native_vertices=len(ids),classes={str(int(k)):int(np.sum(cls[rr,cc]==k)) for k in np.unique(cls[rr,cc])},
  dry_vertices=int(dry.sum()),dry_inside_design=int(np.sum(dry&inside)),dry_near_road_9m=int(np.sum(dry&(rd<=9))),
  platform_vertices=int(t['platform'][rr,cc].sum()),reserve_vertices=int(t['reserve'][rr,cc].sum()),
  dry_samples=samples,before=describe(h,rec),only_delta_bed_to_minus2_55=describe(deep,rec))
 out.append(report)
fig,ax=plt.subplots(figsize=(12,8))
r0,r1=306,391;c0,c1=1375,1459
im=ax.imshow(h[r0:r1,c0:c1],extent=(c0*6-3,(c1-1)*6+3,12282-(r1-1)*6-3,12282-r0*6+3),vmin=-4,vmax=6,cmap='terrain',origin='upper')
plt.colorbar(im,ax=ax,label='Altura del terreno (m)')
for f in fc:
 g=shape(f['geometry']); xy=np.asarray(g.coords if g.geom_type=='LineString' else g.exterior.coords)
 ax.plot(xy[:,0],xy[:,1],color='black' if f['properties']['kind']=='axis' else '#b82d35',lw=1)
for p in roads:
 if p[:,0].max()<8250 or p[:,0].min()>8750 or p[:,1].max()<9950 or p[:,1].min()>10430:continue
 ax.plot(p[:,0],p[:,1],color='magenta',lw=2)
ax.contour(np.arange(c0,c1)*6,12282-np.arange(r0,r1)*6,h[r0:r1,c0:c1],levels=[.5,1.],colors=['cyan','navy'],linewidths=.7)
ax.set(xlim=(8250,8750),ylim=(9950,10430),xlabel='X local',ylabel='Z local',title='Delta V30: suelo, ejes OSM y carreteras graduadas (magenta)');ax.set_aspect('equal')
fig.tight_layout();fig.savefig(E/'delta-suelo-carreteras.png',dpi=150);plt.close(fig)
save(E/'discriminators.json',dict(status='DIAGNOSTIC',branches=out))
print(json.dumps([{k:v for k,v in o.items() if k!='dry_samples'} for o in out]))
