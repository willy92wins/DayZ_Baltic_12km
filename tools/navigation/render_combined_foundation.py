"""Reviewable engineering overview; no claim of in-game appearance."""
from pathlib import Path
import argparse,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from matplotlib.collections import LineCollection
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'
ap=argparse.ArgumentParser();ap.add_argument('--version',default='v9');args=ap.parse_args()
d=np.load(ROOT/f'tests/regional_foundation_combined_{args.version}/reference.npz')
old=np.load(ROOT/'tests/regional_outline_v3/reference.npz')
h=d['candidate'];base=d['base'];wet=d['wet']|d['ocean'];reserve=old['reserve']
shade=LightSource(azdeg=315,altdeg=45).hillshade(h,vert_exag=3,dx=6,dy=6)
rgb=np.zeros((*h.shape,3),dtype='float32')
rgb[:]=[.62,.72,.48];rgb*=.65+.35*shade[...,None]
rgb[wet]=[.35,.67,.78]
rgb[reserve&~wet]=rgb[reserve&~wet]*[.7,1,.76]
fig,ax=plt.subplots(figsize=(12,12))
ax.imshow(rgb,extent=(0,12282,0,12282),origin='upper')
roads=np.load(ROOT/'tests/regional_foundation_roads_v6/reference.npz')
chains=json.loads((EV/'road-grade-chains-v6.json').read_text())['chains']
ax.add_collection(LineCollection([roads['xy'][indices] for indices in chains],colors='#57534a',linewidths=.7))
ax.contour(reserve[::-1],levels=[.5],extent=(0,12282,0,12282),colors=['#22764d'],linewidths=1.2)
for a in json.loads((EV/'road-network-selection.json').read_text())['anchors']:
    x,z=a['xz'];ax.scatter([x],[z],s=14,color='#222222')
    ax.annotate(a['name'],(x,z),xytext=(4,4),textcoords='offset points',fontsize=8,
                bbox=dict(facecolor='white',alpha=.8,edgecolor='none',pad=1))
ax.set(xlim=(0,12282),ylim=(0,12282),aspect='equal',xlabel='X del juego (m)',ylabel='Z del juego (m)',
       title=f'Base regional de terreno — candidato geométrico {args.version}\nAgua prevista azul · corredores de carretera gris · reserva verde oscuro; mapeado pendiente')
ax.grid(alpha=.15);fig.tight_layout();fig.savefig(EV/f'combined-foundation-{args.version}.png',dpi=130)
stats={}
for name,mask in [('reserve_dry',reserve&~wet),('spb_dry',old['spb']&~wet)]:
    stats[name]={'area_km2':float(mask.sum()*36/1e6),'changed_area_km2':float((mask&(h!=base)).sum()*36/1e6),
                 'before_p10_p50_p90_max':np.r_[np.percentile(base[mask],[10,50,90]),base[mask].max()].tolist(),
                 'after_p10_p50_p90_max':np.r_[np.percentile(h[mask],[10,50,90]),h[mask].max()].tolist()}
(EV/f'combined-protected-area-review-{args.version}.json').write_text(json.dumps(stats,indent=2)+'\n')
print(json.dumps(stats,indent=2))
