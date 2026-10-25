"""Read-only candidate review: native surface, tide contours, widths and island split."""
from pathlib import Path
import json,sys
import numpy as np
import shapely
from shapely.geometry import shape
from scipy.ndimage import label, distance_transform_edt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
R=Path('P:/DayZ_Baltic_12km_dev');E=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'tools/terrain'))
from v30_common import tri_sample
from pilot_narva_shore_v30 import shore_segments,mixed_slopes
from audit_fairway_triangles_v30 import save,sha
b=np.load('E:/DayZ-Baltic-Build/v30-fairway-candidate-bounded/terrain_v30.npz')
a=np.load('E:/DayZ-Baltic-Build/v30-delta-candidate/terrain_v30.npz')
hb=b['heights'].astype(float);ha=a['heights'].astype(float)
fc=json.loads((E/'axes-corridors.geojson').read_text())['features']
rows=range(300,395);cols=range(1370,1461)
xx=np.arange(8230,8760,.5);zz=np.arange(9910,10480,.5);X,Z=np.meshgrid(xx,zz)
fig,axs=plt.subplots(1,2,figsize=(13,8),sharex=True,sharey=True)
reports=[]
for ax,h,title in zip(axs,[hb,ha],['V30 / Luga corregido','Corrección local del delta']):
 hh=tri_sample(h,X,Z);ax.imshow(hh,origin='lower',extent=(xx[0],xx[-1],zz[0],zz[-1]),cmap='terrain',vmin=-4,vmax=6)
 for sea,col,ls in [(.5,'#6ef4ff','-'),(1.,'#183b9e','--')]:
  seg=shore_segments(h,np.full((2047,2047),sea),rows,cols)
  ax.add_collection(LineCollection(seg,colors=col,linestyles=ls,linewidths=.65,label=f'Mar {sea:.2f} m'))
 for f in fc:
  if f['properties']['kind']=='axis':
   xy=np.asarray(shape(f['geometry']).coords);ax.plot(xy[:,0],xy[:,1],c='black',lw=.65)
 ax.set(xlim=(8230,8760),ylim=(9910,10480),title=title,xlabel='X local (m)',ylabel='Z local (m)');ax.set_aspect('equal');ax.legend(fontsize=8,loc='lower left')
fig.suptitle('Delta del Neva — comparación sobre triángulos nativos',fontsize=14)
fig.tight_layout();fig.savefig(E/'delta-antes-despues.png',dpi=150);plt.close(fig)
for f in fc:
 if f['properties']['kind']!='axis':continue
 line=shape(f['geometry']);s=np.linspace(0,line.length,int(np.ceil(line.length))+1)
 q=np.array([line.interpolate(v).coords[0] for v in s]);tan=np.gradient(q,axis=0);normal=np.column_stack([-tan[:,1],tan[:,0]])/np.linalg.norm(tan,axis=1)[:,None]
 offsets=np.arange(-80,80.001,.25);pts=q[:,None,:]+normal[:,None,:]*offsets[None,:,None]
 heights=tri_sample(ha,pts[:,:,0],pts[:,:,1]);c=len(offsets)//2
 widths=[];censored=0
 for row in heights:
  assert row[c]<.5
  left=np.flatnonzero(row[:c]>=.5);right=np.flatnonzero(row[c+1:]>=.5)
  if not len(left) or not len(right):censored+=1;continue
  li=left[-1];ri=c+1+right[0]
  # Conservative sub-sample span, not exact continuous minimum along the axis.
  widths.append(float(offsets[ri-1]-offsets[li+1]))
 reports.append(dict(name=f['properties']['name'],stations=len(s),widths_measured=len(widths),open_water_sections_censored=censored,
   min_visible_width_low_tide_m=min(widths) if widths else None,p50_m=float(np.median(widths)) if widths else None,max_m=max(widths) if widths else None))
lb,nb=label(hb>=1.,np.ones((3,3)));la,na=label(ha>=1.,np.ones((3,3)))
split=[]
for old in np.unique(lb[(ha!=hb)&(lb>0)]):
 mask=lb==old;children=np.unique(la[mask&(la>0)])
 if len(children)<2:continue
 for child in children:
  cm=la==child
  if cm[0].any() or cm[-1].any() or cm[:,0].any() or cm[:,-1].any():continue
  rr,cc=np.nonzero(cm);d=distance_transform_edt(cm)*6;idx=int(np.argmax(d));r,c=divmod(idx,2048)
  split.append(dict(area_m2=int(cm.sum())*36,bounds_xz=[int(cc.min()*6),int(12282-rr.max()*6),int(cc.max()*6),int(12282-rr.min()*6)],
   core_xz=[int(c*6),int(12282-r*6)],core_height_before=float(hb[r,c]),core_height_after=float(ha[r,c]),core_radius_m=float(d[r,c])))
local=np.zeros((2047,2047),bool);local[300:395,1370:1461]=True
out=dict(status='REVIEW_MEASURED',width_sampling='Axes <=1 m; perpendicular offsets .25 m, low sea .50. Not a continuous width proof between stations.',
 widths=reports,dry_components_before=int(nb),dry_components_after=int(na),new_separated_islands=split,
 mixed_slopes_before=mixed_slopes(hb,b['water'],local),mixed_slopes_after=mixed_slopes(ha,a['water'],local),
 inputs={str(p):sha(p) for p in [Path('E:/DayZ-Baltic-Build/v30-delta-candidate/terrain_v30.npz'),Path(__file__)]})
save(E/'geometry-review.json',out);print(json.dumps(out))
