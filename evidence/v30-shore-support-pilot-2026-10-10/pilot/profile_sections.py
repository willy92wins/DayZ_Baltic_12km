"""Independent full native-grid cuts of the two EV83 pilot vertices, equal axis scale."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path('E:/DayZ-Baltic-Build'); O=Path(__file__).parent
a=np.load(R/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')['heights']
b=np.load(O/'candidate/terrain.npz')['heights']
fig,axs=plt.subplots(4,1,figsize=(12,12),layout='constrained')
for j,(r,c) in enumerate([(1880,191),(1785,366)]):
 for k,direction in enumerate(['Este-oeste','Sur-norte']):
  ax=axs[2*j+k]; s=np.arange(-3,4); rr=r+0*s if k==0 else r-s; cc=c+s if k==0 else c+0*s
  ax.plot(s*6,a[rr,cc],'-o',color='#56647d',label='EV82-B desplegado',lw=2,ms=4)
  ax.plot(s*6,b[rr,cc],'-o',color='#bb4649',label='EV83 piloto',lw=2,ms=4)
  ax.axvline(0,color='gray',lw=.8,ls=':');ax.set_xlim(-19,19)
  lo=min(float(a[rr,cc].min()),float(b[rr,cc].min()));hi=max(float(a[rr,cc].max()),float(b[rr,cc].max()))
  ax.set_ylim(lo-.7,hi+.7);ax.set_aspect('equal',adjustable='box');ax.grid(alpha=.25)
  ax.set_title(f'({c*6}, {12282-r*6}) m · {direction} · escala 1:1');ax.set_ylabel('Altura (m)');ax.set_xlabel('Distancia al vértice (m)')
  ax.legend(loc='upper left',fontsize=9)
fig.suptitle('Perfiles de terreno de 36 m · cálculo sobre la malla nativa de 6 m\nNo son capturas ni una aceptación visual de DayZ',fontsize=13)
fig.savefig(O/'profiles-full-1to1.png',dpi=140)
print(str(O/'profiles-full-1to1.png'))
