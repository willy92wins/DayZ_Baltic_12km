"""Scientific offline comparisons, with source-selected terrain windows and fixed scales."""
from pathlib import Path
import sys,json,numpy as np
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource,TwoSlopeNorm
from shapely.geometry import shape
W=Path(__file__).resolve().parents[3];sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import tri_sample,cell_planes
B=Path('E:/DayZ-Baltic-Build/v30-smoothing-pilot-20261007');F=W/'evidence/v30-smoothing-pilot-2026-10-07/figures';F.mkdir(exist_ok=True)
R=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev')
plt.rcParams.update({'font.size':10,'axes.titleweight':'bold','figure.facecolor':'white'})

def main():
 with np.load('E:/DayZ-Baltic-Build/v30-v12/inland/terrain_inland.npz') as f:t=dict(f)
 h=t['heights'].astype(float)
 with np.load(B/'dry-18-corrected/terrain_dry.npz') as f:dry=f['heights'].astype(float)
 with np.load(B/'dry-18-corrected/masks.npz') as f:editable=~f['fixed']
 with np.load(R/'tests/relief_v30/relief_v30_mix.npz') as f:high=f['high']>=.5
 curvature=ndimage.laplace(h)**2
 fig,axs=plt.subplots(2,3,figsize=(14,9),layout='constrained');windows=[]
 for row,(name,mask) in enumerate([('Zonas altas',editable&high),('Llanos',editable&~high)]):
  density=ndimage.uniform_filter(mask.astype(float),size=81)
  score=ndimage.uniform_filter(curvature*mask,size=81)
  score[density<.75]=0;score[:42]=0;score[-42:]=0;score[:,:42]=0;score[:,-42:]=0
  r,c=np.unravel_index(np.argmax(score),score.shape);sl=(slice(r-40,r+41),slice(c-40,c+41))
  extent=[(c-40)*6,(c+40)*6,12282-(r+40)*6,12282-(r-40)*6]
  windows.append({'sector':name,'centre_x':int(c*6),'centre_z':int(12282-r*6),'selection':'maximum source 81x81 mean squared Laplacian with at least75% eligible vertices'})
  for col,(a,label) in enumerate([(h,'V12'),(dry,'Relieve 18 m corregido')]):
   rgb=LightSource(315,45).shade(a[sl],cmap=plt.get_cmap('terrain'),dx=6,dy=6,vert_exag=1,vmin=h[sl].min(),vmax=h[sl].max(),blend_mode='soft')
   axs[row,col].imshow(rgb,extent=extent,origin='upper');axs[row,col].set_title(name+' · '+label)
  im=axs[row,2].imshow((dry-h)[sl],extent=extent,origin='upper',cmap='RdBu_r',vmin=-1,vmax=1)
  axs[row,2].set_title('Cambio de altura (m)');fig.colorbar(im,ax=axs[row,2],shrink=.8)
  for ax in axs[row]:ax.set_xlabel('X (m)');ax.set_ylabel('Z (m)');ax.ticklabel_format(style='plain',useOffset=False)
 fig.suptitle('Relieve · comparación offline, escala vertical real\nCarreteras, agua, reserva natural y 66 cimas conservadas',fontsize=16)
 fig.savefig(F/'relieve-comparativa.png',dpi=145);plt.close(fig)
 (F/'selection.json').write_text(json.dumps(windows,indent=2)+'\n',encoding='utf-8')
 with np.load(B/'luga-18-vector/terrain_inland.npz') as f:luga=f['heights'].astype(float)
 plane=cell_planes(t['cls'],t['level'],sea_cut=.51)
 stations=np.load(B/'luga-waterline-stations.npz');p=stations['points'];o=stations['offset_12'];keep=stations['keep']
 ix=np.flatnonzero(keep&np.isfinite(o)&(p[:,0]<5000));j=ix[np.argmax(np.abs(o[ix]))]
 east=np.flatnonzero(keep&np.isfinite(o)&(p[:,0]>8000)&(p[:,0]<10000));k=east[np.argmax(np.abs(o[east]))]
 points=[('Oeste: ajuste al contorno',p[j]),('Este: ajuste al contorno',p[k]),('Regresión: punto 7771',p[7771]),('Regresión: punto 7846',p[7846])]
 fs=json.loads(Path('E:/DayZ-Baltic-Build/v30-redesign/design/water_v3.geojson').read_text(encoding='utf-8'))['features'];g=next(shape(f['geometry']) for f in fs if f['properties'].get('id')=='Luga_0')
 fig,axs=plt.subplots(2,2,figsize=(12,10),layout='constrained')
 for ax,(title,centre) in zip(axs.ravel(),points):
  x=np.arange(centre[0]-70,centre[0]+70,.5);z=np.arange(centre[1]-70,centre[1]+70,.5);xx,zz=np.meshgrid(x,z)
  pl=plane[np.clip(np.floor((12282-zz)/6).astype(int),0,2046),np.clip(np.floor(xx/6).astype(int),0,2046)]
  for heights,color,lstyle,label in [(h,'#1565b0','--','V12'),(luga,'#dc5f17','-','Candidato vectorial')]:
   hh=tri_sample(heights,xx,zz);wet=(np.isfinite(pl)&(hh<pl))|(hh<.75)
   ax.contour(xx,zz,wet.astype(float),levels=[.5],colors=[color],linestyles=lstyle,linewidths=1.6)
   ax.plot([],[],color=color,linestyle=lstyle,label=label)
  for part in getattr(g,'geoms',[g]):
   for ring in [part.exterior,*part.interiors]:
    xy=np.asarray(ring.coords);ax.plot(xy[:,0],xy[:,1],':',color='#555',lw=.6)
  ax.scatter([centre[0]],[centre[1]],s=22,color='#222',zorder=8)
  ax.set_xlim(x[0],x[-1]);ax.set_ylim(z[0],z[-1]);ax.set_aspect('equal');ax.set_title(title);ax.set_xlabel('X (m)');ax.set_ylabel('Z (m)');ax.legend(loc='upper left',fontsize=8);ax.ticklabel_format(style='plain',useOffset=False)
 fig.suptitle('Luga · línea de agua en triángulos nativos\nCandidato sin aprobar: mejora general y dos regresiones locales',fontsize=15)
 fig.savefig(F/'luga-comparativa.png',dpi=145);plt.close(fig)
 print('Wrote',str(F))
if __name__=='__main__':main()
