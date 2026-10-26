from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
R=Path(__file__).parent;O=R/'kit7-hybrid-pilot-20261026'
a=np.load(R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz')['heights']
b=np.load(O/'candidate/terrain.npz')['heights'];changed=a!=b
assert changed.sum()==14 and a[1171,190]==b[1171,190]
sl=np.s_[1163:1180,182:199];before,after=a[sl],b[sl]
rows,cols=np.indices(before.shape);x=(cols-8)*6.;z=(8-rows)*6.
tri=[]
for r in range(16):
    for c in range(16):
        i=r*17+c;tri.extend([(i,i+1,i+18),(i,i+17,i+18)])
mesh=mtri.Triangulation(x.ravel(),z.ravel(),np.asarray(tri))
fig=plt.figure(figsize=(13,8));lo=float(min(before.min(),after.min()));hi=float(max(before.max(),after.max()))
for index,(h,title) in enumerate([(before,'Antes'),(after,'Candidato híbrido')],1):
    ax=fig.add_subplot(2,2,index,projection='3d')
    ax.plot_trisurf(mesh,h.ravel(),cmap='terrain',vmin=lo,vmax=hi,linewidth=.25,edgecolor='#555555',alpha=.95)
    mask=changed[sl];ax.scatter(x[mask],z[mask],h[mask]+.03,c='#e25f25',s=12)
    ax.scatter([0],[0],[h[8,8]+.06],c='#a51b26',s=38,marker='x')
    ax.set(xlabel='Este (m)',ylabel='Norte (m)',zlabel='Altura (m)',zlim=(lo,hi+.2),title=title)
    ax.view_init(elev=32,azim=-55)
ax=fig.add_subplot(2,1,2)
ax.plot(x[8],before[8],'.-',label='Antes',color='#38688c')
ax.plot(x[8],after[8],'.--',label='Candidato',color='#e25f25')
ax.axvline(0,color='#888',linewidth=.7);ax.scatter([0],[before[8,8]],marker='x',s=65,c='#a51b26',label='Ápice protegido (sin cambio)')
ax.set(xlabel='Distancia este desde el ápice (m)',ylabel='Altura (m)',title='Sección por fila1171; misma escala en ambas mallas')
ax.legend(loc='upper right');ax.grid(alpha=.25)
fig.suptitle('Piloto aislado x1140 / z5256: 14 vecinos libres, ápice fijo',fontsize=14)
fig.text(.5,.02,'Vista de la malla numérica: no sustituye la revisión visual dentro de DayZ.',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.04,1,.95))
p=O/'terrain-comparison.png';assert not p.exists();fig.savefig(p,dpi=140);plt.close(fig)
print(str(p))
