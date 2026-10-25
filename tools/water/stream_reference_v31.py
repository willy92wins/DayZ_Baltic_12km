"""Recover frozen pre-kit terminals independently of a pilot author's report."""
from collections import deque
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.ndimage import label

PINS={'bridges/terrain-ev107.npz':'b804f6ff16bce28ba47a5c9a01184c66212c93bcd20ed57509ac7ea4192f2e1c',
      'bridges/fp-ev107/footprint.npz':'f107f71bcff557c5e9fb3651c991bcbcf344737b2d9f39ce098551a8e5de95b7',
      'ev112-ot1-20261018/sites-d.json':'ef53e72a30c4da9f936c472ec6775e96dcda8afd21a5a3b05519c9870970f4b2'}
NEIGHBOURS=((0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,-1))

def farthest(body,start):
    seen={start};todo=deque([start]);last=start
    while todo:
        last=todo.popleft()
        for dr,dc in NEIGHBOURS:
            n=(last[0]+dr,last[1]+dc)
            if 0<=n[0]<body.shape[0] and 0<=n[1]<body.shape[1] and n not in seen and body[n]:seen.add(n);todo.append(n)
    return last

def require_original_endpoints(actual,expected):
    actual,expected=np.asarray(actual,float),np.asarray(expected,float)
    if actual.shape!=(2,2) or expected.shape!=(2,2) or not np.array_equal(actual,expected):
        raise ValueError('pilot original endpoints differ from pinned pre-kit reference')

def recover(build,site_ids):
    root=Path(build).parent
    for rel,digest in PINS.items():
        if hashlib.sha256((root/rel).read_bytes()).hexdigest()!=digest:raise ValueError(('changed pre-kit reference',rel))
    H=np.load(root/'bridges/terrain-ev107.npz')['heights'];plane=np.load(root/'bridges/fp-ev107/footprint.npz')['plane']
    p=np.where(np.isfinite(plane),plane,-np.inf);vp=np.full(H.shape,-np.inf)
    for dr in (0,1):
        for dc in (0,1):vp[dr:dr+2047,dc:dc+2047]=np.maximum(vp[dr:dr+2047,dc:dc+2047],p)
    wet=np.isfinite(vp)&(H<vp);lab,_=label(wet,np.array([[1,1,0],[1,1,1],[0,1,1]]));sites=json.loads((root/'ev112-ot1-20261018/sites-d.json').read_text());ends={}
    for sid in site_ids:
        site=next(s for s in sites if s['id']==sid)
        if site.get('mode','component')=='component':
            r=int(round((12282-site['seed'][1])/6));c=int(round(site['seed'][0]/6))
            points=np.argwhere(wet[r-3:r+4,c-3:c+4]);assert len(points)
            rr,cc=points[np.argmin(np.hypot(points[:,0]-3,points[:,1]-3))]+(r-3,c-3)
            body=lab==lab[rr,cc];first=tuple(map(int,np.argwhere(body)[0]));a=farthest(body,first);b=farthest(body,a)
            # The original path starts at the second sweep's far end.
            pair=[b,a]
            if vp[pair[0]]<vp[pair[1]]:pair.reverse()
        else:pair=[site['stem'][0],site['stem'][-1]]
        ends[sid]=[[int(c)*6,12282-int(r)*6] for r,c in pair]
    return ends
