"""Compare already generated source variants without changing the live terrain."""
import hashlib
import json
from pathlib import Path
import numpy as np
import rasterio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'evidence/navigation/relief-decision'
out.mkdir(exist_ok=True)
paths=[ROOT/'source/baltic_physical_2048_6m.asc',ROOT/'source/baltic_relief3x_2048_6m.asc']
arrays=[rasterio.open(p).read(1) for p in paths]
labels=['Escala vertical física','Relieve ×3']
fig=plt.figure(figsize=(12,8),layout='constrained')
grid=fig.add_gridspec(2,2,height_ratios=[3,1.25])
for i,(label,h) in enumerate(zip(labels,arrays)):
    ax=fig.add_subplot(grid[0,i])
    im=ax.imshow(np.ma.masked_less(h[::4,::4],0),extent=(0,12.288,0,12.288),origin='upper',vmin=0,vmax=33,cmap='terrain')
    ax.set_facecolor('#cce6ee')
    ax.set_title(label+f' · máximo {h.max():.1f} m')
    ax.set(xlabel='Este del mapa (km)',ylabel='Norte del mapa (km)')
fig.colorbar(im,ax=fig.axes,label='Altura en metros (misma escala de color)',shrink=.8)
ax=fig.add_subplot(grid[1,:])
x=np.arange(2048)*6/1000
for label,h in zip(labels,arrays):
    ax.plot(x,h[1024],label=label)
ax.set(xlabel='Este del mapa (km)',ylabel='Altura (m)',title='Perfil central este–oeste · misma posición en las dos fuentes',ylim=(-14,35))
ax.axhline(0,color='#64748b',lw=.6)
ax.legend(loc='upper left');ax.grid(alpha=.2)
fig.suptitle('Elección de relieve · encuadre y posiciones intactos',fontsize=16)
fig.savefig(out/'comparacion.png',dpi=155)
plt.close(fig)
record={'status':'DESIGN_COMPARISON_ONLY_NO_TERRAIN_CHANGED','variants':[{'name':label,'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'min_m':float(h.min()),'max_m':float(h.max()),'positive_percentiles_50_90_99_m':np.percentile(h[h>0],[50,90,99]).tolist()} for path,h,label in zip(paths,arrays,labels)],'limits':['Source variants before water and Narva engineering edits; neither image is a new runtime import.','Profiles use different vertical and horizontal plot scales; apparent slopes are visually exaggerated.','Choosing relief does not determine final engineered lake levels or prove connected navigable water.','Local bridge deck, sea datum, road widths and asset sizes would remain engineering constraints, not multiplied blindly.']}
(out/'comparison.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
