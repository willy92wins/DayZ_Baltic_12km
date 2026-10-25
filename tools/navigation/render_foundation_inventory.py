"""Plot the selected network and unmodified regional terrain for engineering review."""
import json
from pathlib import Path
import numpy as np
import rasterio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from shapely.geometry import shape
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'evidence/regional-foundation-v1'
with rasterio.open(ROOT/'tests/regional_outline_v3/baltic_regional_outline_v3.asc') as ds:
    h=ds.read(1)
roads=json.loads((OUT/'road-network-game.json').read_text())['features']
water=json.loads((OUT/'water-bodies-game.json').read_text())['features']
rivers=json.loads((OUT/'main-rivers-game.json').read_text())['features']
anchors=json.loads((OUT/'road-network-selection.json').read_text())['anchors']
fig,ax=plt.subplots(figsize=(12,12))
ax.imshow(h[::2,::2],extent=(0,12282,0,12282),cmap='terrain',vmin=-4,vmax=110,origin='upper',alpha=.8)
for f in water:
    g=shape(f['geometry'])
    x,z=g.exterior.xy
    ax.plot(x,z,color='#156ab0',lw=.65)
    for ring in g.interiors:
        x,z=ring.xy
        ax.plot(x,z,color='#156ab0',lw=.5)
for f in rivers:
    g=shape(f['geometry'])
    for line in g.geoms if hasattr(g,'geoms') else [g]:
        if line.geom_type!='LineString':continue
        x,z=line.xy;ax.plot(x,z,color='#1db8ee',lw=1)
ax.add_collection(LineCollection([f['geometry']['coordinates'] for f in roads],colors='#ef8618',linewidths=.9))
for a in anchors:
    x,z=a['xz'];ax.scatter([x],[z],s=15,color='black')
    ax.annotate(a['name'],(x,z),xytext=(5,5),textcoords='offset points',fontsize=9,bbox=dict(facecolor='white',alpha=.75,edgecolor='none',pad=1))
ax.set(xlim=(0,12282),ylim=(0,12282),aspect='equal',xlabel='X del juego (m)',ylabel='Z del juego (m)',
       title='Base regional — inventario de agua y conexiones principales\nSelección OSM: pendiente de rasantes, cruces y validación física')
ax.grid(alpha=.2)
fig.tight_layout()
fig.savefig(OUT/'foundation-inventory.png',dpi=130)
print(OUT/'foundation-inventory.png')
