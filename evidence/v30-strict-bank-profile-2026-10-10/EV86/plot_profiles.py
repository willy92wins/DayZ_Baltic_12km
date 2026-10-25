"""True-aspect full sections for the accepted offline pilot."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).parent;R=O.parent
paths=[R/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz',
       R/'v30-coupled-shore-pilot-20261010/quantized-repair/candidate-terrain.npz',O/'candidate-terrain.npz']
heights=[np.load(p)['heights'] for p in paths]
labels=['B: preview actual','EV85-R: mesetas rechazadas','EV86: perfil con pendiente']
styles=[('tab:blue','o','-'),('tab:gray','s','--'),('tab:green','^','-')]
fig,ax=plt.subplots(2,2,figsize=(14,7));profiles=[]
for row,(r,c) in enumerate(((1880,191),(1785,366))):
 for col,axis in enumerate(('E–O','N–S')):
  v=np.arange(-3,4);xx=v*6;ys=[]
  for h,label,(color,marker,ls) in zip(heights,labels,styles):
   y=h[r,c+v] if col==0 else h[r+v,c]
   ax[row,col].plot(xx,y,label=label,color=color,marker=marker,ls=ls);ys.append(y.tolist())
  a=ax[row,col];a.set_aspect('equal',adjustable='box');a.grid(alpha=.25)
  a.set(xlabel='Distancia desde el foco (m)',ylabel='Altura (m)',
        title=f'{axis}: x={c*6}, z={12282-r*6} · tramo 36 m')
  profiles.append({'row':r,'col':c,'axis':axis,'x':xx.tolist(),'B_EV85R_EV86':ys})
fig.suptitle('Perfiles 1:1 del terreno · EV86 verificado offline; no es una captura de DayZ')
fig.legend(labels,loc='lower center',ncol=3);fig.tight_layout(rect=(0,.07,1,.95))
fig.savefig(O/'profiles-36m-1to1.png',dpi=160);plt.close(fig)
(O/'profiles-36m-1to1.json').write_text(json.dumps({'profiles':profiles,'labels':labels},indent=2)+'\n')
