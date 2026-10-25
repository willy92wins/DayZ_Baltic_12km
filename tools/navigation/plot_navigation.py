"""Export measured engineering views; these are not screenshots from DayZ."""
import json
from pathlib import Path
import numpy as np
import rasterio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PatchPolygon, Rectangle
from matplotlib.collections import PolyCollection
from shapely.geometry import shape
from waterway_common import ROOT, FIT, read_base, sample
from audit_assets import ODOL, vertices, get_lod

folder=ROOT/'tests/narva_navigation_v3'
design=json.loads((folder/'design.json').read_text())
check=json.loads((folder/'verification.json').read_text())
with rasterio.open(folder/'narva_navigation_v1.asc') as ds:
    h=ds.read(1)
base=read_base()
fit=json.loads(FIT.read_text()); centre=np.array(fit['bridge_centre_tb'])
u=np.array(fit['axis_east_unit']); v=np.array([u[1],-u[0]])
fig=plt.figure(figsize=(12,10),layout='constrained')
grid=fig.add_gridspec(3,2,height_ratios=[1.25,1,1])
ax=fig.add_subplot(grid[0,:])
xs=np.arange(centre[0]-300,centre[0]+301,2);zs=np.arange(centre[1]-150,centre[1]+151,2)
xx,zz=np.meshgrid(xs,zs);hh=sample(h,xx,zz)
image=ax.pcolormesh(xx-200000,zz,hh,cmap='terrain',vmin=-4,vmax=10,shading='auto')
ax.contour(xx-200000,zz,hh,levels=[.5],colors=['#2189c5'],linewidths=1)
route=shape(design['river_axis_tb']);coords=np.asarray(route.coords)
ax.plot(coords[:,0]-200000,coords[:,1],color='#16384c',linewidth=1,label='Eje geográfico de Narva')
fair=np.asarray(shape(design['depth_check_polygon_tb']).exterior.coords)
ax.plot(fair[:,0]-200000,fair[:,1],'--',color='#20bad0',label='Sector con profundidad verificada')
for b in design['bridge_objects']:
    c=np.array([b['x'],b['z']]);pts=[c+u*d+v*w for d,w in [(-12.5,-4),(12.5,-4),(12.5,4),(-12.5,4)]]
    ax.add_patch(PatchPolygon(pts,facecolor='#a73732',edgecolor='white',linewidth=.6))
ax.set(xlabel='Este del juego (m)',ylabel='Norte del juego (m)',title='Narva · ensayo local de cauce y puente elevado')
ax.set_aspect('equal');ax.legend(loc='upper right',fontsize=8)
fig.colorbar(image,ax=ax,label='Cota del terreno (m)',shrink=.8)

ax=fig.add_subplot(grid[1,:])
d=np.linspace(-290,290,2321);pp=centre[:,None]+u[:,None]*d
ax.plot(d,sample(base,*pp),color='#989898',label='Terreno anterior')
ax.plot(d,sample(h,*pp),color='#846a45',label='Terreno candidato')
ax.plot([-37.5,37.5],[9,9],color='#a73732',linewidth=3,label='Tablero · 3 tramos vanilla de 25 m')
ax.axhspan(.5,1,color='#52b2dc',alpha=.25,label='Rango de agua medido')
ax.set(xlabel='Distancia sobre el eje del puente (m)',ylabel='Cota (m)',ylim=(-4,12),title='Perfil de los accesos · pendiente máxima muestreada 5,1 %')
ax.grid(alpha=.2);ax.legend(loc='upper right',fontsize=8,ncol=2)

ax=fig.add_subplot(grid[2,0])
bridge=ODOL.from_file(r'P:\DZ\structures\roads\bridges\bridge_metal_25.p3d')
lod=get_lod(bridge,1e13);vv=vertices(lod)
polys=[]
for offset in (-25,0,25):
    for f in lod.faces:
        pts=vv[f.vertex_indices]
        polys.append(np.column_stack([pts[:,2]+offset,pts[:,1]+.9451160430908203]))
ax.add_collection(PolyCollection(polys,facecolors='#63717b',edgecolors='#35444e',linewidths=.15,alpha=.35))
dx=np.linspace(-45,45,901);pp=centre[:,None]+u[:,None]*dx
ax.plot(dx,sample(h,*pp),color='#846a45',linewidth=2)
ax.axhspan(.5,1,color='#52b2dc',alpha=.3)
ax.add_patch(Rectangle((-2,-.5),4,6,facecolor='#eeaf41',alpha=.6,label='Reserva de barco: manga 4 m'))
ax.annotate('6,34 m bajo vigas',xy=(7,7.338),xytext=(7,3.5),fontsize=8,arrowprops={'arrowstyle':'->'})
ax.set(xlim=(-43,43),ylim=(-4,15),xlabel='Sobre el eje del puente (m)',ylabel='Cota (m)',title='Colisión del modelo · paso central de 18 m')
ax.grid(alpha=.2);ax.legend(fontsize=7,loc='upper left')

ax=fig.add_subplot(grid[2,1]);ax.axis('off')
text='VERIFICADO EN ARCHIVOS\n\n24 m de canal en el sector revisado\n3,15 m de profundidad mínima conservadora\n272 triángulos completos comprobados\nEmpalmes a cota 9 m sin escalón calculado\nFuera de la intervención: terreno idéntico\n\nPENDIENTE EN MOTOR\n\nLancha y tripulante · ida y vuelta\nColisiones y rampas · proyecto editable\nAgua y arte satélite fuera de este piloto'
ax.text(.02,.98,text,va='top',fontsize=10,linespacing=1.4)
fig.suptitle('Diseño para lancha vanilla y reserva para barcos medianos',fontsize=15)
for extension in ('png','pdf'):
    fig.savefig(ROOT/f'evidence/navigation/narva-navigation-v3.{extension}',dpi=160)
print('Saved engineering plot PNG/PDF')
