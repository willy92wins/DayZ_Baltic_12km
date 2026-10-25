"""Freeze representative changed shores and produce a geometry review atlas.

Selection is mechanical by water class and changed-height mass in 240 m bins;
it is coverage of authoring types, not a claim that every shoreline looks good.
Figures use native triangles and pond cell levels, not nearest-water flooding.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
from scipy.ndimage import distance_transform_edt

from review_shores_v30 import waterline
from v30_common import cell_planes, tri_sample

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('E:/DayZ-Baltic-Build/v30-delta-candidate/terrain_v30.npz')
CANDIDATE = Path('E:/DayZ-Baltic-Build/v30-shore-finish-tidal/terrain_v30.npz')
CLASSES = {1:'Costa marina', 2:'Lago', 3:'Río navegable', 4:'Delta',
           5:'Río secundario', 6:'Arroyo', 7:'Laguna'}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def xz(row, col):
    return np.array([col*6., 12282-row*6.])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, default=CANDIDATE)
    a = ap.parse_args()
    if a.out.exists():
        raise ValueError('Fresh output required')
    a.out.mkdir(parents=True)
    old, new = np.load(SOURCE), np.load(a.candidate)
    h0, h1, cls = old['heights'].astype(float), new['heights'].astype(float), new['cls']
    delta = h1-h0
    changed = delta != 0
    planes = cell_planes(cls, new['level'])
    dist, nearest = distance_transform_edt(cls==0, sampling=6., return_indices=True)
    nearclass = cls[nearest[0], nearest[1]]
    rr, cc = np.indices(cls.shape)
    key = (rr//40)*52+cc//40
    sites = []
    taken = []
    for code, label in CLASSES.items():
        eligible = changed & (nearclass==code) & (rr>12) & (rr<2035) & (cc>12) & (cc<2035)
        if not eligible.any():
            sites.append(dict(code=code, label=label, status='NO_CHANGED_VERTICES'))
            continue
        totals = np.bincount(key[eligible], weights=abs(delta[eligible]), minlength=52*52)
        chosen = None
        for k in np.argsort(totals)[::-1]:
            if totals[k] <= 0: break
            r,c = np.nonzero(eligible & (key==k))
            # A changed vertex close to the weighted centroid avoids arbitrary
            # empty crops and ties the cross-section to a real alteration.
            weights = abs(delta[r,c])
            cr,cl = np.average(r,weights=weights),np.average(c,weights=weights)
            i = np.argmin((r-cr)**2+(c-cl)**2)
            target = xz(r[i],c[i])
            if all(np.linalg.norm(target-q)>200 for q in taken):
                chosen=(int(r[i]),int(c[i]),target);break
        if chosen is None:
            sites.append(dict(code=code,label=label,status='OVERLAPS_ANOTHER_SITE'))
            continue
        row,col,target = chosen; taken.append(target)
        # Use the nearest wet vertex and a dry viewpoint 25-80 m away. No
        # runtime teleport or camera API is invoked by this preparer.
        nr,nc = int(nearest[0,row,col]),int(nearest[1,row,col])
        water = xz(nr,nc)
        local = (abs(rr-row)<=18)&(abs(cc-col)<=18)
        radius = np.hypot((rr-row)*6,(cc-col)*6)
        dry = local & (cls==0) & (h1>1.4) & (radius>=25) & (radius<=80)
        r,c = np.nonzero(dry)
        if not len(r): raise ValueError(f'No dry view for {label}')
        score=abs(radius[r,c]-42)+np.maximum(h1[r,c]-h1[row,col]-6,0)*4
        i=int(np.argmin(score));view=xz(r[i],c[i])
        direction=target-view;direction/=np.linalg.norm(direction)
        yaw=math.degrees(math.atan2(direction[0],direction[1]))
        # A slightly wider profile includes both the foreground and shoreline.
        distances=np.linspace(-50,80,521)
        profile=target[None,:]+distances[:,None]*direction[None,:]
        heights0=tri_sample(h0,profile[:,0],profile[:,1])
        heights1=tri_sample(h1,profile[:,0],profile[:,1])
        pr=np.clip(np.floor((12282-profile[:,1])/6).astype(int),0,2046)
        pc=np.clip(np.floor(profile[:,0]/6).astype(int),0,2046)
        level=np.maximum(np.nan_to_num(planes[pr,pc],nan=.75),.75)
        # Actual local native intersection, including unchanged neighboring
        # cells. A global no-water NaN plane denotes only global sea.
        scope=(abs(rr[:-1,:-1]-row)<27)&(abs(cc[:-1,:-1]-col)<27)
        before=waterline(h0,planes,scope);after=waterline(h1,planes,scope)
        fig,axes=plt.subplots(1,3,figsize=(17,5),gridspec_kw={'width_ratios':[1,1,1.45]})
        r0,r1=max(0,row-27),min(2047,row+27)
        c0,c1=max(0,col-27),min(2047,col+27)
        extent=(c0*6,c1*6,12282-r1*6,12282-r0*6)
        for ax,title,heights,segments in [(axes[0],'Antes',h0,before),(axes[1],'Candidato',h1,after)]:
            ax.imshow(heights[r0:r1+1,c0:c1+1],origin='upper',extent=extent,cmap='terrain',
                      vmin=min(h0[r0:r1+1,c0:c1+1].min(),h1[r0:r1+1,c0:c1+1].min()),
                      vmax=max(h0[r0:r1+1,c0:c1+1].max(),h1[r0:r1+1,c0:c1+1].max()))
            ax.add_collection(LineCollection(segments,colors='#1460df',linewidths=1))
            ax.plot(profile[:,0],profile[:,1],'k--',lw=.7)
            ax.scatter(*view,c='white',s=22,edgecolors='black')
            ax.scatter(*target,c='red',s=15)
            ax.set(xlim=extent[:2],ylim=extent[2:],title=title,xlabel='X (m)',ylabel='Z (m)')
            ax.set_aspect('equal')
        ax=axes[2]
        ax.plot(distances,heights0,color='#b77632',lw=1.2,label='Terreno anterior')
        ax.plot(distances,heights1,color='#245843',lw=1.5,label='Terreno candidato')
        ax.plot(distances,level,color='#1460df',lw=.8,label='Plano agua / mar nominal')
        ax.fill_between(distances,heights1,level,where=heights1<level,color='#5599df',alpha=.35)
        ax.set(xlabel='Distancia sobre el corte (m)',ylabel='Cota (m)',title='Perfil: triángulos nativos')
        ax.grid(alpha=.25);ax.legend(fontsize=8)
        fig.suptitle(f'{label} — X {target[0]:.0f}, Z {target[1]:.0f} — geometría offline, pendiente del motor')
        fig.tight_layout();figure=a.out/f'{code:02d}-geometry.png';fig.savefig(figure,dpi=135);plt.close(fig)
        sites.append(dict(code=code,label=label,status='PREPARED',target_xz=target.tolist(),
                          view_xz=view.tolist(),water_xz=water.tolist(),yaw=yaw,
                          view_height_m=float(tri_sample(h1,*view)),
                          changed_vertices_in_patch=int(changed[r0:r1+1,c0:c1+1].sum()),
                          patch_abs_change_sum_m=float(abs(delta[r0:r1+1,c0:c1+1]).sum()),
                          figure=str(figure)))
    manifest=dict(status='FROZEN_GEOMETRY_REVIEW_SITES',source_sha256=sha(SOURCE),candidate_sha256=sha(a.candidate),
                  selection='Largest 240m changed-height mass by nearest water class, non-overlapping patches.',
                  sites=sites,limits=['No in-game appearance, water rendering, AI or player traversal acceptance.',
                                     'Selection maximizes changed-area coverage; it does not cover every shore.',
                                     'Side profile has different horizontal/vertical display scales; axes are metres.'])
    (a.out/'sites.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
