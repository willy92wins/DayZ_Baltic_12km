"""Render reproducible geographic and relief figures from processed datasets."""
from collections import Counter
import json
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1]/'evidence/mpl-cache'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle
import rasterio
from PIL import Image
from shapely.geometry import shape
from geo_common import *
from prepare_prototype import load_layer,pieces

OUT=DERIVED/'preview';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})

def line_segments(layer):
    return [np.asarray(line.coords)/1000-np.array([TB_X/1000,0]) for geom,_ in layer for line in pieces(geom,{'LineString'})]

def main():
    roads=load_layer('roads');border=load_layer('border')
    mainroads=[(g,p) for g,p in roads if p.get('highway') in {'motorway','trunk','primary','motorway_link','trunk_link','primary_link'}]
    minor=[(g,p) for g,p in roads if p.get('highway') in {'secondary','tertiary'}]
    fig,ax=plt.subplots(figsize=(12,12),dpi=160)
    fig.patch.set_facecolor('#f5f3ec');ax.set_facecolor('#dce7ed')
    sat=np.asarray(Image.open(DERIVED/'tb/source/sat_preview.png'))
    ax.imshow(sat,extent=[0,SIZE/1000,0,SIZE/1000],origin='upper')
    ax.add_collection(LineCollection(line_segments(minor),colors='#eee2c3',linewidths=.24,alpha=.6))
    ax.add_collection(LineCollection(line_segments(mainroads),colors='#fff4d6',linewidths=.8,alpha=.94))
    ax.add_collection(LineCollection(line_segments(border),colors='#663269',linewidths=1.5,linestyles='dashed'))
    geo=json.loads((EVIDENCE/'georef-v0.json').read_text())
    labels={'Narva':(-52,10),'Sosnovy Bor':(-40,11),'Kingisepp':(7,-12),'San Petersburgo':(-64,14),
      'Gatchina':(9,-7),'Luga':(8,9),'Gdov':(9,-3),'Tosno':(7,-5)}
    for c in geo['points']:
        x,y=game_xy(c['lon'],c['lat']);x/=1000;y/=1000
        ax.scatter(x,y,s=17,facecolor='#f8f3de',edgecolor='#252d28',zorder=5)
        ax.annotate(c['name'],(x,y),xytext=labels.get(c['name'],(6,6)),textcoords='offset points',
          weight='bold',fontsize=10,color='#172821',bbox={'boxstyle':'round,pad=.18','facecolor':'#f5f3ec','alpha':.91,'edgecolor':'none'},zorder=6)
    rect=geo['detail_pixel'];frame=geo['frame_pixel']
    gx=(rect['x']-frame['x'])/frame['width']*SIZE/1000
    gy=(frame['y']+frame['height']-rect['y']-rect['height'])/frame['height']*SIZE/1000
    gw=rect['width']/frame['width']*SIZE/1000;gh=rect['height']/frame['height']*SIZE/1000
    ax.add_patch(Rectangle((gx,gy),gw,gh,fill=False,ec='#d7ebff',lw=1.6,ls='--'))
    ax.text(gx+.10,gy+gh-.17,'ACERCAMIENTO CONSERVADO',color='#203d58',fontsize=9,va='top',bbox={'facecolor':'#f4f4eb','edgecolor':'none','alpha':.9,'pad':2})
    ax.text(.35,5.8,'ZONA OCCIDENTAL\nReserva de territorio para el lore',fontsize=9,color='#372145',bbox={'facecolor':'#f7eff8','edgecolor':'none','alpha':.9,'pad':3})
    rx=(740+20)/1135*SIZE/1000;ry=(1099-624)/1135*SIZE/1000
    ax.annotate('Mshinskoye boloto\nzona de referencia',(rx,ry),xytext=(14,12),textcoords='offset points',fontsize=9,
       bbox={'facecolor':'#f2f5e9','edgecolor':'none','alpha':.9,'pad':3},arrowprops={'arrowstyle':'-','color':'#f2f5e9'})
    ax.set(xlim=(0,12.288),ylim=(0,12.288),xlabel='Este · km de juego',ylabel='Norte · km de juego')
    ax.set_aspect('equal');ax.set_xticks(np.arange(0,13,2));ax.set_yticks(np.arange(0,13,2))
    ax.set_title('BÁLTICO · BASE GEOGRÁFICA 12,288 × 12,288 KM',loc='left',fontsize=17,weight='bold',pad=28)
    ax.text(0,1.014,'Recorte aprobado · agua, costa y ejes viarios · colores provisionales del suelo',transform=ax.transAxes,fontsize=10,color='#495649')
    fig.text(.12,.04,'Líneas claras: carreteras de referencia, todavía sin piezas DayZ.  Morado: frontera administrativa OSM.\nAgua interior: capa geográfica; no acredita agua funcional en juego. © OpenStreetMap contributors · ESA WorldCover 2021 v200.',fontsize=8,color='#555d55')
    fig.subplots_adjust(bottom=.1,top=.89,left=.08,right=.98)
    fig.savefig(OUT/'base-geografica.png',facecolor=fig.get_facecolor());plt.close(fig)
    grids={}
    for name in ['physical','relief3x']:
        with rasterio.open(DERIVED/f'gis/height_{name}_game.tif') as src:grids[name]=src.read(1)
    fig,axes=plt.subplots(2,2,figsize=(13,10),dpi=150,gridspec_kw={'height_ratios':[1.25,.8]})
    fig.patch.set_facecolor('#f5f3ec')
    for ax,(name,z),title in zip(axes[0],grids.items(),['Escala física · máximo ≈ 10,9 m','Comparación ×3 · máximo ≈ 32,6 m']):
        im=ax.imshow(z,extent=[0,12.288,0,12.288],origin='upper',cmap='terrain',vmin=-12,vmax=35)
        ax.set_title(title,loc='left',fontsize=12);ax.set_xlabel('km');ax.set_ylabel('km')
        for north_km in [9,4.5]:
            ax.axhline(north_km,color='#222222',lw=.6,ls='--',alpha=.6)
    x=(np.arange(N)+.5)*CELL/1000
    for ax,row,label in [(axes[1,0],round((12288-9000)/6),'Perfil oeste–este · a 9 km del borde sur'),
                         (axes[1,1],round((12288-4500)/6),'Perfil oeste–este · a 4,5 km del borde sur')]:
        for name,title,color in [('physical','Física','#527b62'),('relief3x','Comparación ×3','#a46a35')]:
            ax.plot(x,grids[name][row,:],label=title,color=color,lw=1)
        ax.axhline(0,color='#407eac',lw=.7,ls='--');ax.set_title(label,loc='left',fontsize=10)
        ax.set(xlabel='Distancia desde el oeste · km',ylabel='Altura · m',xlim=(0,12.288),ylim=(-13,36));ax.grid(alpha=.17);ax.legend(frameon=False,fontsize=9)
    fig.suptitle('DOS VARIANTES DE RELIEVE · ELECCIÓN PENDIENTE',x=.07,ha='left',fontsize=17,weight='bold')
    fig.text(.07,.018,'Copernicus GLO-30 (DSM) · misma geometría XY. Fondo marino sintético del prototipo; los lagos conservan su referencia de cota.\nEstas vistas no son capturas de Terrain Builder ni de DayZ.',fontsize=8,color='#555d55')
    fig.subplots_adjust(left=.07,right=.9,top=.91,bottom=.1,hspace=.30,wspace=.23)
    cax=fig.add_axes([.925,.52,.016,.34])
    fig.colorbar(im,cax=cax,label='Altura de juego · m')
    fig.savefig(OUT/'comparacion-relieve.png',facecolor=fig.get_facecolor());plt.close(fig)
    print('PREVIEWS COMPLETE')

if __name__=='__main__':main()
