"""Radial profile through the actual worst corridor-intersection point."""
from pathlib import Path
import sys,json
import numpy as np
from shapely.geometry import LineString,Point
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path('P:/DayZ_Baltic_12km_dev');E=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'tools/terrain'))
from v30_common import tri_sample
a=np.load(R/'tests/terrain_v30/terrain_v30.npz')['heights'].astype(float)
candidate=json.loads((E/'candidate.json').read_text())
b=np.load(candidate['file'])['heights'].astype(float)
src=np.load(R/'tests/water_v3/navigable_samples.npz')['Luga_0'];line=LineString(src[:,1:3])
worst=json.loads((E.parent/'constraints.json').read_text())['points'][0]
point=np.array([worst['x'],worst['z']]);s=line.project(Point(point))
center=np.asarray(line.interpolate(s).coords[0])
direction=(point-center)/np.linalg.norm(point-center)
offset=np.linspace(-25,25,1001);points=center+offset[:,None]*direction
before=tri_sample(a,points[:,0],points[:,1]);after=tri_sample(b,points[:,0],points[:,1])
fig,ax=plt.subplots(figsize=(9,4.7),layout='constrained')
ax.plot(offset,before,color='#b74630',label='Fondo anterior')
ax.plot(offset,after,color='#18579a',label='Copia corregida')
ax.axhline(worst['water_plane_m'],color='#339bbb',label='Agua nominal local')
ax.axhline(worst['water_plane_m']-3,color='#666666',ls='--',label='Fondo máximo para 3 m de calado')
ax.axvspan(-12,12,color='#bfdce3',alpha=.3,label='Radio útil de 12 m respecto al eje')
ax.scatter([np.linalg.norm(point-center)],[worst['water_plane_m']-worst['depth_m']],c='#b74630',s=30,zorder=4)
ax.set(xlabel='Distancia radial desde el eje por el punto más somero (m)',ylabel='Altura (m)',
       title='Luga: perfil por el defecto de calado detectado\nCopia offline; pendiente de integración y prueba con lancha')
ax.legend(fontsize=8);ax.grid(alpha=.15)
fig.savefig(E/'perfil-luga-antes-despues.png',dpi=150);plt.close(fig)
