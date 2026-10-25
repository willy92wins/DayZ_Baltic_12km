"""Unexaggerated offline mesh comparison. Not a DayZ capture or acceptance."""
from pathlib import Path
import json
import hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, Normalize

R=Path(__file__).resolve().parents[1]
B=R.parent/'v30-mixed-bank-incremental-fixed-20261010'
candidate=R/'candidate-terrain.npz'
assert hashlib.sha256(candidate.read_bytes()).hexdigest()=='a7146c27a634d3ee59bc4c2763d71050da3172724c4f2620a17fce0775fcf020'
hb=np.load(B/'candidate/terrain.npz')['heights']
hh=np.load(candidate)['heights']
p=np.load(B/'candidate/plane.npy')
raw=json.loads((R/'review-independent/ev87-review-p99-sector-corrected.json').read_text())
patches=sorted(raw['information']['patch_geometry'],key=lambda x:x['focus_energy_reduction'],reverse=True)
chosen=[];sectors=set()
for patch in patches:
    r,c=patch['center'];sector=(r//256,c//256)
    if min(r,c)<12 or max(r,c)>2035:continue
    if sector in sectors or not np.isfinite(p[r-7:r+8,c-7:c+8]).any():continue
    chosen.append(patch);sectors.add(sector)
    if len(chosen)==3:break
assert len(chosen)==3
fig=plt.figure(figsize=(15,15))
for index,patch in enumerate(chosen):
    r,c=patch['center'];radius=12
    rs=slice(r-radius,r+radius+1);cs=slice(c-radius,c+radius+1)
    before=hb[rs,cs].astype(float);after=hh[rs,cs].astype(float)
    x,z=np.meshgrid(np.arange(-radius,radius+1)*6,np.arange(radius,-radius-1,-1)*6)
    lo=min(before.min(),after.min());hi=max(before.max(),after.max());span=max(hi-lo,1)
    norm=Normalize(lo,hi)
    for col,(name,heights) in enumerate([('B desplegado',before),('EV87 candidato offline',after)]):
        ax=fig.add_subplot(3,2,index*2+col+1,projection='3d')
        triangles=[]
        for rr in range(24):
            for cc in range(24):
                nw=rr*25+cc
                triangles.extend(((nw,nw+1,nw+26),(nw,nw+25,nw+26)))
        ax.plot_trisurf(x.ravel(),z.ravel(),heights.ravel(),triangles=triangles,cmap='terrain',norm=norm,edgecolor='#3e4b3940',linewidth=.12)
        ax.set(xlim=(-72,72),ylim=(-72,72),zlim=(lo,hi),xlabel='X relativo (m)',ylabel='Z relativo (m)',zlabel='Cota (m)')
        ax.set_box_aspect((144,144,span));ax.view_init(elev=28,azim=-60)
        ax.set_title(f'{name} · X={c*6}, Z={12282-r*6}\nDescenso del foco: {patch["focus_delta_m"]:.2f} m',fontsize=10)
fig.suptitle('Malla de terreno sin exageración vertical · tres focos junto al agua con mayor reducción angular\nSelección favorable; no representa aceptación global ni render del motor',fontsize=13)
fig.tight_layout(rect=(0,0,1,.95))
fig.savefig(R/'residual-review/mesh-comparison.png',dpi=145)
(R/'residual-review/mesh-comparison.json').write_text(json.dumps({'status':'OFFLINE_DIAGNOSTIC_ONLY','selection':'Top focus angular reduction; finite P within 42m; distinct 1536m sectors; first 3','patches':chosen},indent=2)+'\n')
print(json.dumps({'selected':[p['center'] for p in chosen],'output':str(R/'residual-review/mesh-comparison.png')}))
