"""One overview for reviewing the prepared terrain, without pretending it is DayZ."""
from pathlib import Path
import argparse
import hashlib
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LightSource,Normalize,LinearSegmentedColormap
from matplotlib.lines import Line2D
import numpy as np
import shapely
from shapely.geometry import shape

from v30_common import cell_planes

ROOT=Path(__file__).resolve().parents[2]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();assert not a.out.exists()
    digest=hashlib.sha256(a.candidate.read_bytes()).hexdigest()
    t=np.load(a.candidate);h=t['heights'].astype(float)
    # At the native diagonal midpoint the height is the average of NW and SE.
    ground=(h[:-1,:-1]+h[1:,1:])/2
    pond=cell_planes(t['cls'],t['level'])
    surface=np.maximum(np.nan_to_num(pond,nan=.75),.75)
    wet=ground<surface
    norm=Normalize(0,float(np.max(h)))
    # A sea-blue low end obscures the distinction between low dry land and water.
    # Elevation colours describe ground only; no land-cover/vegetation inference.
    cmap=LinearSegmentedColormap.from_list('baltic_land',
        [(0,'#708455'),(.35,'#97a466'),(.65,'#b8ac76'),(1,'#d2c2a5')])
    rgb=cmap(norm(ground))[...,:3]
    shade=LightSource(azdeg=315,altdeg=38).hillshade(ground,vert_exag=1,dx=6,dy=6)
    rgb*=.60+.40*shade[...,None]
    rgb[wet]=[.35,.62,.73]
    xx=(np.arange(2047)+.5)*6;zz=12282-(np.arange(2047)+.5)*6
    roads_path=ROOT/'evidence/regional-foundation-v1/road-network-game.json'
    road_lines=[]
    for f in json.loads(roads_path.read_text())['features']:
        for g in shapely.get_parts(shape(f['geometry'])):
            if g.geom_type=='LineString':road_lines.append(np.asarray(g.coords)[:,:2])
    nature_path=ROOT/'tests/regional_outline_v1/reference.npz'
    nature=np.load(nature_path)['reserve'][:-1,:-1]
    case_path=a.candidate.parent/'local-cases/residual-cases.json'
    cases=json.loads(case_path.read_text())['cases'];points=np.array([c['xz'] for c in cases])
    delta=np.argwhere(t['cls']==4)
    delta_bounds=(max(0,float(delta[:,1].min()*6)-200),min(12282,float(delta[:,1].max()*6)+200),
                  max(0,float(12282-delta[:,0].max()*6)-200),min(12282,float(12282-delta[:,0].min()*6)+200))
    fig=plt.figure(figsize=(16,11),layout='constrained')
    grid=fig.add_gridspec(2,2,width_ratios=(1.4,1))
    axes=[fig.add_subplot(grid[:,0]),fig.add_subplot(grid[0,1]),fig.add_subplot(grid[1,1])]
    extent=(0,12282,0,12282)
    limits=[extent,(1850,3250,6200,7750),delta_bounds]
    titles=['Región completa','Narva y lagunas recuperadas','Delta del Neva']
    for ax,view,title in zip(axes,limits,titles):
        ax.imshow(rgb,origin='upper',extent=extent,interpolation='nearest')
        ax.add_collection(LineCollection(road_lines,colors='#f7e6c4',linewidths=.6,alpha=.9))
        ax.contour(xx,zz,nature.astype(float),levels=[.5],colors=['#c8fa77'],linewidths=1.1)
        # Analytic sea envelope. Inland pond planes retain their own elevation.
        for sea,color in ((.5,'#225377'),(1.,'#b4ecf5')):
            wet_at=ground<np.maximum(np.nan_to_num(pond,nan=sea),sea)
            ax.contour(xx,zz,wet_at.astype(float),levels=[.5],colors=[color],linewidths=.35,alpha=.7)
        ax.scatter(points[:,0],points[:,1],s=15,c='#dc483b',edgecolors='white',linewidths=.35,zorder=4)
        ax.set_xlim(view[0],view[1]);ax.set_ylim(view[2],view[3]);ax.set_aspect('equal')
        ax.set_title(title,fontsize=12);ax.set_xlabel('X local (m)');ax.set_ylabel('Z local (m)')
    axes[0].legend(handles=[Line2D([0],[0],color='#d8b885',label='Corredores viales, sin piezas'),
                           Line2D([0],[0],color='#84a945',label='Ámbito protegido de naturaleza'),
                           Line2D([0],[0],marker='o',color='none',markerfacecolor='#dc483b',label=f'{len(cases)} cortes residuales de al menos 6 m')],
                   loc='lower left',fontsize=8,framealpha=.95)
    bar=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=axes[0],
                    orientation='horizontal',fraction=.045,pad=.06,shrink=.7)
    bar.set_label('Cota de tierra (m); colores de altura, no de vegetación',fontsize=9)
    fig.suptitle(f'Baltic · base de terreno preparada {digest[:4]}\nModelo geométrico, sin edificios ni vegetación colocados · pendiente del motor',fontsize=16)
    fig.text(.79,.025,'Agua nominal 0,75 m; contornos marinos 0,50 / 1,00 m.\nEl perímetro de naturaleza es el ámbito de trabajo, no un límite legal.',fontsize=8,ha='center')
    a.out.mkdir(parents=True)
    fig.savefig(a.out/'overview.png',dpi=160)
    fig.savefig(a.out/'overview.pdf',dpi=160)
    plt.close(fig)
    receipt=dict(status='OFFLINE_REVIEW_FIGURE_NOT_ENGINE',candidate_sha256=digest,
                 sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (roads_path,nature_path,case_path,Path(__file__))},
                 height_range_m=[float(h.min()),float(h.max())],residual_points=len(cases),neva_view_bounds=delta_bounds,
                 limits=['Midpoint raster is a review view, not an exact shoreline-area or flooding measurement.',
                         'No buildings, trees, railway pieces or runtime navigation shown.'])
    (a.out/'overview.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
