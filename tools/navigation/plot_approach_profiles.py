"""Plot centerline plus 8m corridor worst grades on the unchanged heightfield."""
import json
import numpy as np
import rasterio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from waterway_common import ROOT, FIT, read_base, sample, sha

asc=ROOT/'tests/narva_navigation_v3/narva_navigation_v1.asc'
design=json.loads((asc.parent/'design.json').read_text())
if sha(asc)!=design['candidate_sha256']: raise ValueError('Candidate drift')
base=read_base()
with rasterio.open(asc) as ds: current=ds.read(1)
fit=json.loads(FIT.read_text())
c=np.array(fit['bridge_centre_tb']);u=np.array(fit['axis_east_unit']);v=np.array([u[1],-u[0]])
s=np.arange(37.5,320.001,.25)
offsets=np.arange(-4,4.001,.25)
fig,axes=plt.subplots(2,2,figsize=(13,7),sharex=True,layout='constrained')
for col,side in enumerate((-1,1)):
    pp=c[:,None,None]+u[:,None,None]*(side*s[None,:])+v[:,None,None]*offsets[:,None]
    for data,label,color in ((base,'Base anterior','#89939e'),(current,'Piloto V3','#006e99')):
        y=sample(data,pp[0],pp[1])
        axes[0,col].plot(s,y[len(offsets)//2],color=color,label=label,lw=2)
        grade=np.diff(y,axis=1)/.25*100
        axes[1,col].plot(s[:-1],grade[len(offsets)//2],color=color,lw=1.5)
        if label=='Piloto V3': axes[1,col].fill_between(s[:-1],grade.min(axis=0),grade.max(axis=0),color=color,alpha=.2,label='Rango en los 8 m de ancho')
    axes[0,col].set_title('Acceso oeste' if side==-1 else 'Acceso este')
    axes[0,col].set_ylabel('Cota del eje (m)')
    axes[1,col].set_ylabel('Pendiente hacia fuera (%)')
    axes[1,col].set_xlabel('Distancia desde el centro del puente (m)')
    for ax in axes[:,col]:
        ax.axvline(280,color='#b87712',linestyle='--',lw=1,label='Fin de rasante diseñada')
        ax.axvspan(292,320,color='#bd7339',alpha=.10)
        ax.grid(alpha=.2)
    axes[0,col].legend(fontsize=8)
axes[1,0].legend(fontsize=8,loc='lower left')
fig.suptitle('P11 · Accesos del piloto: el terreno exterior también necesita rasante',fontsize=15)
fig.supxlabel('Geometría calculada de ASC V3. Banda naranja: fuera de la intervención. No es prueba de conducción.',fontsize=10)
dest=ROOT/'evidence/navigation/approach-profiles.png'
fig.savefig(dest,dpi=160)
fig.savefig(dest.with_suffix('.pdf'))
print(dest)
