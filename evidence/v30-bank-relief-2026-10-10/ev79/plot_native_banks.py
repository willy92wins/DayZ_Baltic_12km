"""Offline 1:1 native triangles; not a rendered DayZ acceptance image."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
B=Path(__file__).parent
source=np.load(B.parent/'v30-remaining-exact-dry-support-20261009/candidate/terrain.npz')['heights']
candidate=np.load(B/'candidate/terrain.npz')['heights']
anchors=[(2187,6717),(2577,6864),(2295,6918)]
fig=plt.figure(figsize=(15,8))
for col,(x,z) in enumerate(anchors):
    r,c=round((12282-z)/6),round(x/6)
    rr,cc=np.mgrid[r-8:r+9,c-8:c+9];xx=cc*6;zz=12282-rr*6
    top=max(float(source[rr,cc].max()),float(candidate[rr,cc].max()))
    low=min(float(source[rr,cc].min()),float(candidate[rr,cc].min()))
    ids=np.arange(rr.size).reshape(rr.shape)
    tri=np.concatenate([np.stack((ids[:-1,:-1],ids[:-1,1:],ids[1:,1:]),-1).reshape(-1,3),np.stack((ids[:-1,:-1],ids[1:,1:],ids[1:,:-1]),-1).reshape(-1,3)])
    for row,(label,h) in enumerate([('Fuente EV71',source),('Candidato EV79',candidate)]):
        ax=fig.add_subplot(2,3,row*3+col+1,projection='3d',proj_type='ortho')
        ax.plot_trisurf(xx.ravel(),zz.ravel(),h[rr,cc].ravel(),triangles=tri,color='#b9b687',linewidth=.15,edgecolor='#676753',shade=True,lightsource=LightSource(315,40))
        ax.set_zlim(low,top);ax.set_box_aspect((96,96,max(top-low,.1)));ax.view_init(28,-65)
        ax.set_title(f'{label}: x={x}, z={z}',fontsize=11)
        ax.set_xlabel('x (m)',fontsize=8);ax.set_ylabel('z (m)',fontsize=8);ax.set_zlabel('altura (m)',fontsize=8)
        ax.tick_params(labelsize=7)
fig.suptitle('Crestas secas de Narva · triángulos nativos de 6 m · escala geométrica 1:1\nComparación offline; no representa texturas ni render de DayZ',fontsize=14)
fig.tight_layout(rect=(0,0,1,.93))
fig.savefig(B/'native-bank-comparison.png',dpi=150)
print(B/'native-bank-comparison.png')
