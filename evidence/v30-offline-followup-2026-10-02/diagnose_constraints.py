"""Explain the rejected bounded candidate; no solve and no terrain writes."""
import csv
import json
import sys
from pathlib import Path
import numpy as np
from shapely.geometry import LineString, Point, box
from shapely.ops import substring

R = Path('P:/DayZ_Baltic_12km_dev')
E = Path(__file__).resolve().parent
sys.path.insert(0, str(R/'tools/terrain'))
from audit_fairway_triangles_v30 import LIMITS, NARVA, records, depths, save
from v30_common import cell_planes

t = np.load(R/'tests/terrain_v30/terrain_v30.npz')
h = t['heights'].astype(float)
src = np.load(R/'tests/water_v3/navigable_samples.npz')['Luga_0']
line = LineString(src[:, 1:3])
domain = box(1e-6, 1e-6, 12282-1e-6, 12282-1e-6).difference(Point(NARVA).buffer(620, quad_segs=256))
corridor = substring(line, 24, line.length-24).buffer(12, cap_style='flat', join_style='round', quad_segs=32).intersection(domain)
rec = records(corridor, cell_planes(t['cls'], t['level'].astype(float)))
d = depths(h, rec)
bad = np.flatnonzero(d < 2.99)
mutable = t['water'] & ~t['platform'] & ~t['narva']
rows = []
for i in bad:
    ids = rec['ids'][i]; weights = rec['weights'][i]
    free = mutable.ravel()[ids]
    capacity = np.sum(weights[free] * np.minimum(1., h.ravel()[ids[free]] + 12.))
    demand = 3.05-d[i]
    wsum = float(weights[free].sum())
    rows.append(dict(x=float(rec['xz'][i, 0]), z=float(rec['xz'][i, 1]), depth_m=float(d[i]),
                     face=int(rec['face'][i]), chainage_m=float(line.project(Point(rec['xz'][i]))),
                     water_plane_m=float(rec['level'][i]), mutable_weight=wsum,
                     required_equal_lowering_m=float(demand/wsum) if wsum else None,
                     insufficient_at_1m=bool(capacity+1e-7 < demand),
                     vertices=[dict(row=int(v//2048), col=int(v%2048), height_m=float(h.ravel()[v]),
                                    cls=int(t['cls'].ravel()[v]), platform=bool(t['platform'].ravel()[v]),
                                    narva=bool(t['narva'].ravel()[v]), weight=float(w)) for v,w in zip(ids, weights)]))
rows.sort(key=lambda row: row['depth_m'])
save(E/'constraints.json', dict(status='EXPLAINS_REJECTED_CANDIDATE', points=rows,
     insufficient_constraints=sum(row['insufficient_at_1m'] for row in rows),
     minimum_equal_lowering_bound_m=max(row['required_equal_lowering_m'] or 0 for row in rows),
     limits='Bound is per constraint, not a solved or validated alternative. No second candidate attempted.'))
with (E/'luga-defects.csv').open('x', newline='', encoding='utf-8') as stream:
    fields=['x','z','depth_m','chainage_m','water_plane_m','mutable_weight','required_equal_lowering_m','insufficient_at_1m']
    writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
    for row in rows: writer.writerow({k:row[k] for k in fields})
print(json.dumps({'worst':rows[0], 'insufficient':sum(row['insufficient_at_1m'] for row in rows),
                  'equal_lowering_bound':max(row['required_equal_lowering_m'] or 0 for row in rows)},indent=2))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

fig, axes = plt.subplots(1,2,figsize=(12,5.5), layout='constrained')
axes[0].plot(src[:,1],src[:,2],color='#6298b5',lw=3,label='Eje Luga V3')
axes[0].scatter([r['x'] for r in rows],[r['z'] for r in rows],c='#bb4028',s=20,label='Calado < 2,99 m',zorder=3)
axes[0].set(title='Defectos localizados en el Luga',xlabel='X del juego (m)',ylabel='Z del juego (m)',aspect='equal')
axes[0].legend(loc='best')
worst=rows[0]; x,z=worst['x'],worst['z']
c0,c1=int((x-35)//6),int((x+35)//6)+1
r0,r1=int((12282-z-35)//6),int((12282-z+35)//6)+1
xs=np.arange(c0,c1+1)*6;zs=12282-np.arange(r0,r1+1)*6
hh=h[r0:r1+1,c0:c1+1]
water=worst['water_plane_m']
im=axes[1].pcolormesh(xs,zs,water-hh,shading='nearest',cmap='RdYlBu',vmin=0,vmax=5)
axes[1].contour(xs,zs,water-hh,levels=[0,3],colors=['black','white'],linewidths=1)
parts=list(corridor.geoms) if hasattr(corridor,'geoms') else [corridor]
for part in parts:
    xx,zz=part.exterior.xy; axes[1].plot(xx,zz,color='#c22b95',lw=1)
axes[1].scatter([x],[z],s=50,c='#111111',marker='x')
axes[1].set(xlim=(x-35,x+35),ylim=(z-35,z+35),aspect='equal',
            title='Detalle peor punto: 2,19 m\nMagenta: canal útil de 24 m',xlabel='X del juego (m)',ylabel='Z del juego (m)')
fig.colorbar(im,ax=axes[1],label='Agua local − cota del vértice (m)')
fig.suptitle('Diagnóstico geométrico offline — no captura del juego ni prueba de lancha')
fig.savefig(E/'luga-calado.png',dpi=150)
plt.close(fig)
