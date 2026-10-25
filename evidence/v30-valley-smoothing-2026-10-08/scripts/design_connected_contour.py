"""C representation: preserve native wet connectivity before fitting heights."""
from pathlib import Path
import json,heapq
import numpy as np
from scipy.ndimage import label
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-valley-smoothing-2026-10-08'
t=np.load(B/'candidate-land180/terrain_valley.npz');h=t['heights'].astype(float)
water=np.load('E:/DayZ-Baltic-Build/v30-water-visual-fix-20261008/stitched-water/visual_vertex_levels.npy')
d=dict(np.load(B/'contour-design.npz'));sd=d['sd'].copy();core=d['core']
zone=np.load(B/'candidate-b/masks.npz')['edited_shore']
old=core&np.isfinite(water)&(h<water-1e-6)
structure=np.array([[1,1,0],[1,1,1],[0,1,1]],bool)
original,n=label(old,structure)
new=np.where(zone,sd<0,old)&core
rails=np.zeros_like(old);rows=[];offsets=[(-1,-1),(-1,0),(0,-1),(0,1),(1,0),(1,1)]
for k in range(1,n+1):
    comp=original==k;rr,cc=np.nonzero(comp)
    if len(rr)==0:continue
    seed_index=int(np.argmax((water-h)[comp]));seed=(int(rr[seed_index]),int(cc[seed_index]))
    new[seed]=True;rails[seed]=True
    if zone[seed]:sd[seed]=min(sd[seed],-3.)
    r0=max(0,rr.min()-1);r1=min(2048,rr.max()+2);c0=max(0,cc.min()-1);c1=min(2048,cc.max()+2)
    box=np.s_[r0:r1,c0:c1];links=[]
    for iteration in range(len(rr)+1):
        labels,count=label(new[box],structure);seed_label=labels[seed[0]-r0,seed[1]-c0]
        foreign=comp[box]&new[box]&(labels!=seed_label)
        if not foreign.any():break
        visited=comp[box]&(labels==seed_label);vr,vc=np.nonzero(visited)
        queue=[];distance={};previous={}
        for r,c in zip(vr+r0,vc+c0):
            rc=(int(r),int(c));distance[rc]=0.;heapq.heappush(queue,(0.,rc))
        target=None
        while queue:
            cost,rc=heapq.heappop(queue)
            if cost!=distance.get(rc):continue
            r,c=rc
            if foreign[r-r0,c-c0]:target=rc;break
            for dr,dc in offsets:
                nr,nc=r+dr,c+dc
                if not (0<=nr<2048 and 0<=nc<2048 and comp[nr,nc]):continue
                # Prefer the continuous vector channel; traverse old water only.
                dist=max(0.,float(sd[nr,nc])) if np.isfinite(sd[nr,nc]) else 0.
                value=cost+(2.**.5 if dr and dc else 1.)*(1.+dist*dist)
                dest=(nr,nc)
                if value<distance.get(dest,float('inf')):
                    distance[dest]=value;previous[dest]=rc;heapq.heappush(queue,(value,dest))
        assert target is not None,('original wet component cannot reconnect',k)
        path=[];rc=target
        while rc in previous:
            path.append(rc);rc=previous[rc]
        for rc in path:
            new[rc]=True;rails[rc]=True
            if zone[rc]:sd[rc]=min(sd[rc],-3.)
        links.append(dict(vertices=len(path),cost=distance[target]))
    else:raise RuntimeError('finite connection budget exhausted')
    rows.append(dict(source_component=k,vertices=len(rr),links=links,anchor=list(seed)))
d['sd']=sd;d['flow_rails']=rails;d['native_wet_target']=new
np.savez_compressed(B/'contour-design-c.npz',**d)
out=dict(status='CONNECTED_SIGN_FIELD_PENDING_HEIGHT_AND_CONSUMER_GATES',source_components=n,rails=int(rails.sum()),changed_sign_vertices=int(((sd<0)!=(np.load(B/'contour-design.npz')['sd']<0))[zone].sum()),components=rows,limits=['Connectivity is a design constraint, not a proof that the fitted heights or physical water pass.','Only original wet vertices reconnect broken target supports; minimum rail field magnitude is 3 m.'])
(E/'connected-contour-design.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
