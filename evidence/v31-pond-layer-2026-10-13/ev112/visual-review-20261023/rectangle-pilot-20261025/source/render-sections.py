from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent
e=np.load(R/'guarded-relief-batch-e-merged/terrain-buried.npz')['heights']
f=np.load(R/'rectangle-pilot-f/terrain.npz')['heights']
sl=np.s_[898:919,476:498]
x=np.arange(476,498)*6;z=12282-np.arange(898,919)*6
xx,zz=np.meshgrid(x,z);lo=min(e[sl].min(),f[sl].min());hi=max(e[sl].max(),f[sl].max())
fig=plt.figure(figsize=(13,8),layout='constrained')
for i,(h,title) in enumerate(((e,'E — antes'),(f,'F — piloto')),1):
    ax=fig.add_subplot(2,2,i,projection='3d')
    ax.plot_surface(xx,zz,h[sl],cmap='terrain',vmin=lo,vmax=hi,linewidth=.2,edgecolor='#00000033')
    ax.set_zlim(lo,hi);ax.set_title(title);ax.set_xlabel('X (m)');ax.set_ylabel('Z (m)');ax.set_zlabel('Altura (m)');ax.view_init(30,-55)
for i,(row,title) in enumerate(((907,'Sección fila 907'),(909,'Sección fila 909')),3):
    ax=fig.add_subplot(2,2,i);ax.plot(x,e[row,476:498],label='E');ax.plot(x,f[row,476:498],label='F')
    ax.set_title(title);ax.set_xlabel('X (m)');ax.set_ylabel('Altura (m)');ax.grid(alpha=.25);ax.legend()
fig.suptitle('Narva: transición rectangular — comparación numérica, sin aceptación visual en juego\n94 vértices; Δmáx 0,502 m; stencil objetivo máximo 0,235 m',fontsize=13)
fig.savefig(R/'rectangle-pilot-f/sections-e-f.png',dpi=140)
