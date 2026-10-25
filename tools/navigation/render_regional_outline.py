"""Compare exact candidate heights with baseline and protected geography."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
from geo_common import game_xy, tb_geometry


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--version', default='v1')
    args = p.parse_args()
    reference = np.load(ROOT/f'tests/regional_outline_{args.version}/reference.npz')
    out = ROOT/f'evidence/regional-outline-{args.version}'
    out.mkdir(exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(14, 12), gridspec_kw={'height_ratios':[3,1]}, layout='constrained')
    geo = json.loads((ROOT/'evidence/georef-v0.json').read_text())
    for ax, key, title in zip(axes[0], ['base', 'candidate'], ['Base nativa 0.2', 'Candidato regional '+args.version]):
        a = reference[key]
        im = ax.imshow(np.ma.masked_where(reference['water'][::3,::3], a[::3,::3]),
                       origin='upper', extent=(0, 12.288, 0, 12.288), cmap='terrain', vmin=0, vmax=180)
        ax.set_facecolor('#9dcbdc')
        ax.contour(reference['reserve'][::3,::3], levels=[.5], origin='upper',
                   extent=(0, 12.288, 0, 12.288), colors=['#ab2384'], linewidths=1.2)
        ax.set(title=title+f' · máximo {a.max():.1f} m', xlabel='Este (km)', ylabel='Norte (km)')
        for pt in geo['points']:
            if pt['name'] not in ['Gatchina','Luga','Narva','San Petersburgo']:
                continue
            x,y=game_xy(pt['lon'],pt['lat'])
            ax.plot(float(x)/1000,float(y)/1000,'.',color='#17241a',ms=3)
            ax.annotate(pt['name'],(float(x)/1000,float(y)/1000),xytext=(4,5),textcoords='offset points',
                        fontsize=8,bbox={'facecolor':'white','alpha':.8,'edgecolor':'none','pad':1})
    fig.colorbar(im, ax=list(axes[0]), label='Altura en metros · escala común', shrink=.7)
    for ax, north in zip(axes[1], [7900, 1100]):
        row=int(round((12282-north)/6))
        for key, name in [('base','Base'),('candidate','Candidato')]:
            ax.plot(np.arange(2048)*.006, reference[key][row], lw=1, label=name)
        ax.set(title=f'Perfil oeste–este · norte {north/1000:.1f} km', xlabel='Este (km)', ylabel='Altura (m)', ylim=(-14,185))
        ax.grid(alpha=.2); ax.legend()
    fig.suptitle('RELIEVE REGIONAL · COMPARACIÓN OFFLINE',fontsize=17)
    fig.supxlabel('Magenta: reserva de conservación. Agua y piloto preservados. Perfiles con exageración vertical; no captura del juego.',fontsize=9)
    fig.savefig(out/'comparacion.png',dpi=140)
    plt.close(fig)


if __name__ == '__main__':
    main()
