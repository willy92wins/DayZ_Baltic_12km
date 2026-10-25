"""Independent sampling of retained V3 fairways; no terrain writes."""
import json
import sys
from pathlib import Path
import numpy as np
from shapely.geometry import Point,shape

R=Path('P:/DayZ_Baltic_12km_dev'); E=R/'evidence/v30-resume-2026-10-02'
sys.path.insert(0,str(R/'tools/terrain'))
from v30_common import cell_planes,tri_sample
t=np.load(R/'tests/terrain_v30/terrain_v30.npz'); h=t['heights']
planes=cell_planes(t['cls'],t['level'].astype(float))
samples=np.load(R/'tests/water_v3/navigable_samples.npz')
features=json.loads((R/'tests/water_v3/water_v3.geojson').read_text())['features']
approved={f['properties'].get('id'):shape(f['geometry']) for f in features if f['properties']['class']=='navigable'}
reports=[]
for name in samples.files:
    if name not in approved:continue
    src=samples[name]; s=np.arange(24,float(src[-1,0])-24,2.)
    if len(s)<2:
        reports.append({'river':name,'excluded':'Too short after 24 m endpoint margins','length_m':float(src[-1,0])})
        continue
    xy=np.column_stack([np.interp(s,src[:,0],src[:,k]) for k in (1,2)])
    tangent=np.gradient(xy,axis=0); n=np.column_stack([-tangent[:,1],tangent[:,0]])
    n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-9)
    p=xy[:,None,:]+n[:,None,:]*np.arange(-12,13)[None,:,None]
    valid=(p[:,:,0]>0).all(1)&(p[:,:,0]<12282).all(1)&(p[:,:,1]>0).all(1)&(p[:,:,1]<12282).all(1)
    valid&=(np.hypot(xy[:,0]-2417.1428225906,xy[:,1]-6889.8850822322)>620)
    if not valid.any():
        reports.append({'river':name,'excluded':'All stations in preserved Narva or beyond map','length_m':float(src[-1,0])})
        continue
    p=p[valid];xy=xy[valid];s=s[valid]
    c=np.floor(p[:,:,0]/6).astype(int);r=np.floor((12282-p[:,:,1])/6).astype(int)
    water=np.maximum(np.nan_to_num(planes[r,c],nan=-np.inf),.5)
    depth=water-tri_sample(h,p[:,:,0],p[:,:,1]); centre=depth[:,12]
    indices=np.argsort(centre)[:5]
    def stats(d):return {'min_m':float(d.min()),'below_3m':int((d<2.99).sum()),'below_1m':int((d<1).sum()),'dry':int((d<=0).sum())}
    runs=[];bad=centre<1
    starts=np.flatnonzero(bad&~np.r_[False,bad[:-1]]);ends=np.flatnonzero(bad&~np.r_[bad[1:],False])
    for a,b in zip(starts,ends):
        runs.append({'start_s':float(s[a]),'end_s':float(s[b]),'length_m':float(s[b]-s[a]),'from':xy[a].tolist(),'to':xy[b].tolist(),'min_m':float(centre[a:b+1].min())})
    reports.append({'river':name,'stations':len(s),'center':stats(centre),'corridor_24m':stats(depth),
        'worst_center':[{'xz':xy[k].tolist(),'s':float(s[k]),'depth_m':float(centre[k]),'inside_approved':approved[name].covers(Point(xy[k])),'distance_to_bank_m':float(approved[name].boundary.distance(Point(xy[k])))} for k in indices],
        'center_below_1m_runs':runs})
out={'status':'DIAGNOSTIC_CURRENT_AXES','method':'Retained V3 axes sampled every 2 m with 1 m cross-sections spanning +/-12 m; native triangles; pond planes or sea minimum 0.5 m.',
     'exclusions':['Discarded historical Delta Neva axes','First and last 24 m of each axis','Preserved Narva within 620 m','Out of map samples'],
     'limits':['Offline consumer diagnostic, no boat collision or measured draft.','Does not certify the new Neva delta branches.'], 'rivers':reports}
(E/'current-fairways-diagnostic.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2))
