"""Native-grid diagnostic only, not DayZ rendering or candidate acceptance."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
pre=json.loads((R/'preflight-run-01/preflight.json').read_text())
report=json.loads((R/'solve-run-01/solve-result.json').read_text())
path=Path(report['candidate_path'])
assert hashlib.sha256(path.read_bytes()).hexdigest()==report['candidate_sha256']
with np.load(path,allow_pickle=False) as z: b=z['base'];h=z['candidate']
seed=pre['selected_seed'];r0,r1,c0,c1=pre['local_context_rc_half_open']
sr,sc=seed['row']-r0,seed['col']-c0
fig,axes=plt.subplots(2,3,figsize=(15,8),constrained_layout=True)
extent=[c0*6,(c1-1)*6,12282-(r1-1)*6,12282-r0*6]
low=min(b.min(),h.min());high=max(b.max(),h.max())
for ax,a,title in [(axes[0,0],b,'Base focal actual'),(axes[0,1],h,'Candidato amplio · aún sin aceptar')]:
    im=ax.imshow(a,origin='upper',extent=extent,cmap='terrain',vmin=low,vmax=high,interpolation='nearest')
    ax.scatter(seed['col']*6,12282-seed['row']*6,s=70,c='red',marker='+')
    ax.set(title=title,xlabel='X del mapa (m)',ylabel='Z del mapa (m)')
fig.colorbar(im,ax=axes[0,:2],label='Cota (m)',shrink=.8)
delta=h.astype(float)-b.astype(float);limit=float(abs(delta).max())
im=axes[0,2].imshow(delta,origin='upper',extent=extent,cmap='RdBu_r',vmin=-limit,vmax=limit,interpolation='nearest')
axes[0,2].set(title='Cambio: rojo sube / azul baja',xlabel='X (m)',ylabel='Z (m)')
fig.colorbar(im,ax=axes[0,2],label='Cambio de cota (m)',shrink=.8)
offset=np.arange(-20,21)
for ax,dr,dc,title in [(axes[1,0],0,1,'Perfil este–oeste'),(axes[1,1],1,0,'Perfil norte–sur'),(axes[1,2],1,1,'Perfil diagonal de la malla')]:
    rr=sr+dr*offset;cc=sc+dc*offset;valid=(rr>=0)&(rr<b.shape[0])&(cc>=0)&(cc<b.shape[1])
    rr=rr[valid];cc=cc[valid];x=offset[valid]*6*np.sqrt(dr*dr+dc*dc)
    ax.plot(x,b[rr,cc],'.-',label='Base',lw=1.4,ms=3,color='#a35b20')
    ax.plot(x,h[rr,cc],'.-',label='Candidato',lw=1.4,ms=3,color='#2360a0')
    ax.set(title=title,xlabel='Distancia al punto de control (m)',ylabel='Cota (m)')
    ax.grid(alpha=.2);ax.legend()
fig.suptitle('Sector Narva · alturas nativas de la malla de 6 m\nRelieve con restricción de pendiente · gráfico offline, no captura del juego',fontsize=14)
out=R/'solve-run-01/native-sector-comparison.png'
if out.exists():raise FileExistsError(out)
fig.savefig(out,dpi=140);plt.close(fig)
print(json.dumps({'path':str(out),'candidate_sha256':report['candidate_sha256'],'changed_vertices':int(np.count_nonzero(delta))}))
