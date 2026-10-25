from pathlib import Path
import hashlib,json,sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.lines import Line2D
B=Path(r'E:\DayZ-Baltic-Build\v30-mixed-bank-float32-20261010')
EV80=Path(r'E:\DayZ-Baltic-Build\v30-mixed-bank-constrained-20261010')
EV79=Path(r'E:\DayZ-Baltic-Build\v30-narva-dry-bank-relief-20261010')
CONSUMER=EV80/'review-luna'/'verify.py'
REPORT=EV80/'review-luna'/'report.json'
sys.path.insert(0,str(EV80/'review-luna'))
import verify as consumer

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rep=json.loads(REPORT.read_text(encoding='utf-8'))
assert rep['candidate_sha256']=='0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b'
anchors=rep['mixed_edge_counts_and_focuses']['focus_anchors']
strong=max(anchors,key=lambda a:a['local_energy_reduction'])
persist=next(a for a in anchors if a['x_m']==2196 and a['z_m']==1578)
assert strong['x_m']==1140 and strong['z_m']==1002 and strong['local_energy_reduction']>0.05
assert persist['changed'] is False and persist['local_energy_reduction']==0.0
src=np.load(EV79/'candidate'/'terrain.npz'); dst=np.load(EV80/'candidate'/'terrain.npz')
h0=src['heights'];h1=dst['heights']
p=np.load(EV79/'candidate'/'plane.npy',mmap_mode='r');f=np.load(EV79/'candidate'/'visible-field.npy',mmap_mode='r')
assert sha(EV79/'candidate'/'terrain.npz')==rep['source_sha256']
assert sha(EV80/'candidate'/'terrain.npz')==rep['candidate_sha256']
# These are offline source and EV80 arrays only. EV81 is intentionally not loaded.
centers=[('Mejora angular EV80',strong),('Foco EV80 persistente',persist)]
span_m=120.0; half=span_m/2; pad=0
patches=[]
for label,a in centers:
 row=int(a['row']);col=int(a['col']);r0=max(0,row-int(half/6)-pad);r1=min(h0.shape[0]-1,row+int(half/6)+pad);c0=max(0,col-int(half/6)-pad);c1=min(h0.shape[1]-1,col+int(half/6)+pad)
 patches.append((label,a,r0,r1,c0,c1))
mins=[];maxs=[];maxslope=0
for _,_,r0,r1,c0,c1 in patches:
 for heights in (h0,h1):
  q=heights[r0:r1+1,c0:c1+1];mins.append(float(q.min()));maxs.append(float(q.max()))
  for rr in range(r0,r1):
   for cc in range(c0,c1):
    hNW,hNE,hSW,hSE=(float(heights[rr,cc]),float(heights[rr,cc+1]),float(heights[rr+1,cc]),float(heights[rr+1,cc+1]))
    for vals in ((hNW,hNE,hSE),(hNW,hSW,hSE)):
     # Coordinates use native 6m spacing and the native NW-SE diagonal.
     xyz=np.array(((0,vals[0],0),(6,vals[1],0),(6,vals[2],-6)),dtype=float) if vals==(hNW,hNE,hSE) else np.array(((0,vals[0],0),(0,vals[1],-6),(6,vals[2],-6)),dtype=float)
     n=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]);slope=np.degrees(np.arctan2(np.hypot(n[0],n[2]),abs(n[1])));maxslope=max(maxslope,float(slope))
# Shared actual elevation range, no vertical exaggeration: each axis uses one world unit per display unit.
y0=min(mins)-1.0;y1=max(maxs)+1.0;yrange=y1-y0
norm=Normalize(vmin=0.0,vmax=max(60.0,np.ceil(maxslope/10)*10))
fig=plt.figure(figsize=(15.0,11.3),dpi=180)
for r,(label,a,r0,r1,c0,c1) in enumerate(patches):
 for col,(name,heights) in enumerate((('EV79 source',h0),('EV80 candidate',h1))):
  ax=fig.add_subplot(2,2,r*2+col+1,projection='3d')
  xs=np.arange(c0,c1+1,dtype=float)*6.0;zs=12282.0-np.arange(r0,r1+1,dtype=float)*6.0
  X,Z=np.meshgrid(xs,zs);Y=heights[r0:r1+1,c0:c1+1].astype(np.float64)
  polys=[];slopes=[];wet_polys=[]
  wf=consumer.wet_faces(heights,p,f)
  # consumer returns triangle masks ordered exactly NW,NE,SE then NW,SW,SE.
  for ir,rr in enumerate(range(r0,r1)):
   for ic,cc in enumerate(range(c0,c1)):
    pts=[(X[ir,ic],Z[ir,ic],Y[ir,ic]),(X[ir,ic+1],Z[ir,ic+1],Y[ir,ic+1]),(X[ir+1,ic],Z[ir+1,ic],Y[ir+1,ic]),(X[ir+1,ic+1],Z[ir+1,ic+1],Y[ir+1,ic+1])]
    tri_list=((0,1,3),(0,2,3))
    for ti,inds in enumerate(tri_list):
     poly=[pts[i] for i in inds];polys.append(poly)
     xyz=np.asarray(poly,dtype=float);n=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]);slope=np.degrees(np.arctan2(np.hypot(n[0],n[1]),abs(n[2])));slopes.append(slope)
     if wf[ti][rr,cc]:wet_polys.append(poly)
  mesh=Poly3DCollection(polys,cmap='viridis',norm=norm,edgecolors=(0.1,0.1,0.1,0.26),linewidths=.28,antialiased=True)
  mesh.set_array(np.asarray(slopes));ax.add_collection3d(mesh)
  if wet_polys:
   water=Poly3DCollection(wet_polys,facecolors='none',edgecolors=(0.15,0.83,0.94,0.9),linewidths=.75)
   ax.add_collection3d(water)
  x0=6*c1-6*c0
  centerx=float(a['x_m']);centerz=float(a['z_m']);rr=int(a['row']);cc=int(a['col'])
  mark=float(heights[rr,cc]);ax.scatter([centerx],[centerz],[mark],s=45,marker='*',c='#ffb000',edgecolors='black',linewidths=.5,depthshade=False)
  ax.set_xlim(6*c0,6*c1);ax.set_ylim(12282-6*r1,12282-6*r0);ax.set_zlim(y0,y1)
  ax.set_box_aspect((span_m,span_m,yrange))
  ax.set_proj_type('ortho');ax.view_init(elev=27,azim=-54)
  ax.set_xlabel('x este (m)',labelpad=0,fontsize=8);ax.set_ylabel('z norte (m)',labelpad=0,fontsize=8);ax.set_zlabel('altura (m)',labelpad=0,fontsize=8)
  ax.tick_params(labelsize=7,pad=0)
  energy=100*float(a['local_energy_reduction']); maxbefore=float(a['local_max_before']);maxafter=float(a['local_max_after'])
  if r==0:
   row_title=f"{label} · ({centerx:.0f},{centerz:.0f}) m · ΔY={float(a['candidate_height_m'])-float(a['source_height_m']):+.3f} m\nE_local −{energy:.3f}% · θmax {maxbefore:.2f}° → {maxafter:.2f}° · {name}"
  else:
   row_title=f"{label} · ({centerx:.0f},{centerz:.0f}) m · ΔY={float(a['candidate_height_m'])-float(a['source_height_m']):+.3f} m\nE_local {energy:.3f}% · θmax {maxbefore:.2f}° → {maxafter:.2f}° · {name}"
  ax.set_title(row_title,fontsize=8.5,pad=4)
sm=ScalarMappable(norm=norm,cmap='viridis');sm.set_array([])
cax=fig.add_axes([.92,.27,.014,.48]);cb=fig.colorbar(sm,cax=cax);cb.set_label('Pendiente de triángulo nativo (grados)',fontsize=8);cb.ax.tick_params(labelsize=7)
legend=[Line2D([0],[0],color='#14d4ef',lw=2,label='cara clasificada húmeda por P/F (consumidor EV80)'),Line2D([0],[0],marker='*',color='w',markerfacecolor='#ffb000',markeredgecolor='black',markersize=9,label='nodo ancla')]
fig.legend(handles=legend,loc='lower center',bbox_to_anchor=(.46,.015),ncol=2,frameon=True,fontsize=8)
fig.suptitle('Geometría offline EV79 → EV80 · malla nativa 6 m · triangulación NW–SE\nNo es una captura de DayZ · elevación sin exageración vertical · cámara ortográfica compartida',fontsize=12,y=.985)
fig.subplots_adjust(left=.03,right=.88,top=.90,bottom=.10,wspace=.04,hspace=.19)
out=B/'ev80-geometry-before-after.png';fig.savefig(out,bbox_inches='tight');plt.close(fig)
selected=[]
for label,a,r0,r1,c0,c1 in patches:
 selected.append({'label':label,'x_m':a['x_m'],'z_m':a['z_m'],'row':a['row'],'col':a['col'],'window_m':span_m,'grid_bounds_inclusive':{'row':[r0,r1],'col':[c0,c1]},'evidence_from_consumer':{k:a[k] for k in ('source_height_m','candidate_height_m','changed','selector','fixed','wet_support','local_edge_count','local_energy_before','local_energy_after','local_energy_reduction','local_max_before','local_max_after','local_over30_before','local_over30_after')}})
data={'status':'OFFLINE_GEOMETRY_FIGURE','figure_sha256':sha(out),'inputs':{'ev79_terrain_sha256':sha(EV79/'candidate'/'terrain.npz'),'ev80_terrain_sha256':sha(EV80/'candidate'/'terrain.npz'),'ev79_plane_sha256':sha(EV79/'candidate'/'plane.npy'),'ev79_visible_field_sha256':sha(EV79/'candidate'/'visible-field.npy'),'ev80_consumer_report_sha256':sha(REPORT),'consumer_source_sha256':sha(CONSUMER)},'camera_and_mesh':{'projection':'orthographic','elevation_deg':27,'azimuth_deg':-54,'same_view_all_panels':True,'native_spacing_m':6,'triangulation':'two faces per cell: NW-NE-SE and NW-SW-SE','vertical_exaggeration':1.0,'shared_actual_height_limits_m':[y0,y1],'shared_xz_crop_width_m':span_m,'wet_overlay':'consumer wet_faces(source heights, static P/F), cyan outlines'},'selected_foci':selected,'selection_reason':'EV80 consumer mixed_edge_counts_and_focuses.focus_anchors: highest local_energy_reduction among provided anchors (1140,1002) and unchanged reference anchor (2196,1578).','not_shown':'EV81 candidate; EV81 is rejected/pending consumer and is not represented as an improvement.','limits':['Offline native-grid geometry and consumer-classified wet-face overlay only; not a DayZ render/capture.','P/F is used only to outline the consumer wet-face classification, not drawn as a rendered water surface.','The strong anchor retains local maximum hinge angle and count >30 unchanged despite lower local energy.']}
(B/'ev80-geometry-before-after.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'figure':str(out),'figure_sha256':data['figure_sha256'],'selected':[(x['x_m'],x['z_m'],x['evidence_from_consumer']['local_energy_reduction']) for x in selected],'height_limits':[y0,y1]}))

