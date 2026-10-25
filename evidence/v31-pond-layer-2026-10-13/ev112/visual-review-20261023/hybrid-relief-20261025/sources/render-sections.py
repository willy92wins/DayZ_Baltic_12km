from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent
d=np.load(R/'guarded-relief-batch-d/terrain.npz')['heights']
e=np.load(R/'guarded-relief-batch-e/terrain.npz')['heights']
report=json.loads((R/'guarded-relief-batch-e-replay/report.json').read_text())
groups=[g for cluster in report['clusters'] if cluster.get('retried') and cluster['status']=='LOCAL_CHECKS_PASS' for g in cluster['groups']]
fig,axes=plt.subplots(len(groups),2,figsize=(11,2.5*len(groups)),layout='constrained')
for row,g in enumerate(groups):
    r,c=g['representative'];sl=np.s_[r-5:r+6,c-5:c+6]
    x=np.arange(-5,6)*6
    ax=axes[row,0]
    ax.plot(x,d[r,c-5:c+6],label='D · Este/Oeste',color='#657080')
    ax.plot(x,e[r,c-5:c+6],label='E · Este/Oeste',color='#007d7a')
    ax.plot(x,np.diag(d[sl]),ls='--',color='#657080',label='D · diagonal')
    ax.plot(x,np.diag(e[sl]),ls='--',color='#007d7a',label='E · diagonal')
    ax.scatter([0],[e[r,c]],color='#a8273e',s=24,zorder=5)
    ax.set(title=('Pico' if g['kind']=='peak' else 'Depresión')+f' · X={c*6}, Z={12282-r*6}',xlabel='Distancia proyectada (m)',ylabel='Cota nativa (m)')
    ax.grid(alpha=.2)
    if row==0:ax.legend(fontsize=7,ncol=2)
    ax=axes[row,1];im=ax.imshow(e[sl]-d[sl],cmap='RdBu_r',vmin=-.75,vmax=.75,extent=(-33,33,-33,33),interpolation='nearest')
    ax.scatter([0],[0],c='#111111',s=15);ax.set(title='Cambio D → E · punto central fijo',xlabel='Este local (m)',ylabel='Norte local (m)')
    fig.colorbar(im,ax=ax,label='Cambio de cota (m)')
fig.suptitle('EV112 · cinco grupos adicionales corregidos\nSecciones numéricas con escalas horizontal/vertical distintas; no son capturas del juego.',fontsize=12)
fig.savefig(R/'guarded-relief-batch-e/sections-d-e.png',dpi=145)
print(len(groups),'groups rendered')
