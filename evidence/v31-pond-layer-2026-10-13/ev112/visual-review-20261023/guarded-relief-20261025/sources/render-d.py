from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
R=Path(__file__).parent/'guarded-relief-batch-d'
z=np.load(R/'patch.npz');before,after=z['before'],z['after'];free=z['free'];n,m=before.shape
rr,cc=np.mgrid[:n,:m];x=(cc-8)*6.;north=(8-rr)*6.
tri=[]
for r in range(n-1):
    for c in range(m-1):
        a=r*m+c;tri.extend([(a,a+1,a+m+1),(a,a+m,a+m+1)])
mesh=Triangulation(x.ravel(),north.ravel(),np.array(tri))
fig=plt.figure(figsize=(12,9),layout='constrained')
for index,(heights,title) in enumerate([(before,'Antes: ápice y orilla fijados'),(after,'Candidato D: vecinos suavizados')],1):
    ax=fig.add_subplot(2,2,index,projection='3d')
    ax.plot_trisurf(mesh,heights.ravel(),cmap='terrain',edgecolor='#444444',linewidth=.22,
                   vmin=min(before.min(),after.min()),vmax=max(before.max(),after.max()))
    ax.scatter([0],[0],[heights[8,8]],c='#c00040',s=45)
    ax.set(title=title,xlabel='Este local (m)',ylabel='Norte local (m)',zlabel='Altura (m)',
           zlim=(min(before.min(),after.min()),max(before.max(),after.max())))
    ax.view_init(elev=32,azim=-55);ax.set_box_aspect((1,1,.5))
ax=fig.add_subplot(2,2,3);delta=after-before
im=ax.imshow(delta,extent=(-51,51,-51,51),cmap='RdBu_r',vmin=-.5,vmax=.5,interpolation='nearest')
ax.scatter(x[~free],north[~free],s=3,c='#4c4c4c',label='Vértices fijos')
ax.scatter([0],[0],c='#c00040',s=35,label='Ápice fijo');ax.legend(fontsize=8)
ax.set(title='Cambio de altura · rejilla nativa de 6 m',xlabel='Este local (m)',ylabel='Norte local (m)')
fig.colorbar(im,ax=ax,label='Delta (m)')
ax=fig.add_subplot(2,2,4)
for h,label,color in [(before,'Antes','#666666'),(after,'Después','#007c83')]:
    ax.plot(x[8],h[8],color=color,label=label+' · Este/Oeste')
    ax.plot(x[8],np.diag(h),color=color,linestyle='--',label=label+' · diagonal NO/SE')
ax.set(title='Secciones por el ápice protegido',xlabel='Paso de rejilla proyectado (m)',ylabel='Altura (m)')
ax.grid(alpha=.2);ax.legend(fontsize=8)
fig.suptitle('EV112 · candidato offline · fila181/col1316\nMalla nativa sin lámina de agua · requiere revisión en juego',fontsize=13)
fig.savefig(R/'before-after.png',dpi=160);print(R/'before-after.png')
