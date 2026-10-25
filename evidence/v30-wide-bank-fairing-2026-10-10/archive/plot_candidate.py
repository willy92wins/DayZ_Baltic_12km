"""Fixed-camera offline inspection of the single Q pilot; not an acceptance gate alone."""
from pathlib import Path
import hashlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
R=Path(__file__).parent;B=R.parent/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
assert hashlib.sha256((R/'candidate-terrain.npz').read_bytes()).hexdigest()=='cce4cd0c2f71355c6d8a110804b52570644e496055ada9ef17d07b4cb60c455c'
hb=np.load(B)['heights'];hq=np.load(R/'candidate-terrain.npz')['heights'];r,c=840,370
sl=np.s_[r-8:r+9,c-8:c+9];bb=hb[sl].astype(float);qq=hq[sl].astype(float)
fig=plt.figure(figsize=(14,10))
for j,axis in enumerate(('E–O','N–S')):
 ax=fig.add_subplot(2,2,j+1);bv=bb[8,:] if j==0 else bb[:,8];qv=qq[8,:] if j==0 else qq[:,8]
 ax.plot(np.arange(-8,9)*6,bv,'.-',label='B',color='#aa563c');ax.plot(np.arange(-8,9)*6,qv,'.-',label='Q',color='#21746e')
 ax.set_title(f'Perfil {axis} por X2220/Z7242');ax.set_xlabel('Distancia al foco (m)');ax.set_ylabel('Cota (m)');ax.grid(alpha=.2);ax.legend()
x,z=np.meshgrid(np.arange(-8,9)*6,np.arange(8,-9,-1)*6)
tris=[]
for rr in range(16):
 for cc in range(16):
  n=rr*17+cc;tris.extend(((n,n+1,n+18),(n,n+17,n+18)))
lo=min(bb.min(),qq.min());hi=max(bb.max(),qq.max());norm=Normalize(lo,hi)
for k,(name,data) in enumerate((('B',bb),('Q',qq))):
 ax=fig.add_subplot(2,2,k+3,projection='3d')
 ax.plot_trisurf(x.ravel(),z.ravel(),data.ravel(),triangles=tris,cmap='terrain',norm=norm,edgecolor='#11111150',linewidth=.3)
 ax.set(xlim=(-48,48),ylim=(-48,48),zlim=(lo,hi),xlabel='X relativo (m)',ylabel='Z relativo (m)',zlabel='Cota (m)',title=name+' · escala vertical real')
 ax.set_box_aspect((96,96,hi-lo));ax.view_init(elev=23,azim=-63)
fig.suptitle('Piloto Q: perfil ancho sobre malla nativa de 6 m\nMisma cámara y escala; propuesta offline pendiente de consumidor independiente',fontsize=13)
fig.tight_layout(rect=(0,0,1,.95));fig.savefig(R/'profiles-mesh.png',dpi=140)
out={'status':'OFFLINE_INSPECTION_ONLY','changed_vertices':int(np.count_nonzero(hb!=hq)),
 'focus_B':float(hb[r,c]),'focus_Q':float(hq[r,c]),'min_delta':float(np.min(hq.astype(float)-hb)),'max_delta':float(np.max(hq.astype(float)-hb))}
(R/'plot-diagnostic.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
