from pathlib import Path
import json,collections
import numpy as np
import shapely
from shapely.geometry import shape,Point
B=Path(__file__).parent;data=json.loads((B/'census.json').read_text());t=dict(np.load('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz'))
design=Path('E:/DayZ-Baltic-Build/v30-v11/design');fs=json.loads((design/'streams_candidates.geojson').read_text())['features'];pf=np.load(design/'profiles.npz')
names=('river_057','stream_0207','stream_0431')
out=[]
for gap in data['long_dry_gaps']:
 a=pf[gap['id']];d=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(a[:,1:3],axis=0),axis=1))];s=np.arange(gap['start_s'],gap['end_s']+.1,.5)
 x=np.interp(s,d,a[:,1]);z=np.interp(s,d,a[:,2]);c=np.clip(np.rint(x/6).astype(int),0,2047);r=np.clip(np.rint((12282-z)/6).astype(int),0,2047)
 flags={key:int(np.count_nonzero(t[key][r,c])) for key in ['reserve','platform','narva','beach'] if key in t}
 cls=dict(collections.Counter(map(int,t['cls'][r,c])))
 row=gap|dict(probes=len(s),flags=flags,classes=cls)
 row['attribution']='ROAD_RESERVE_PRESENT' if flags.get('reserve',0) else ('PLATFORM_PRESENT' if flags.get('platform',0) else 'UNATTRIBUTED')
 out.append(row)
summary=dict(gaps=len(out),total_dry_length_m=sum(g['length_m'] for g in out),by_attribution=dict(collections.Counter(r['attribution'] for r in out)),courses_with_gaps=len(set(r['id'] for r in out)),unattributed=[g for g in out if g['attribution']=='UNATTRIBUTED'],terrain_keys=list(t),terminal_profiles=[r for r in data['records'] if r['id'] in names],stream_properties=[q['properties'] for q in fs if q['properties']['id'] in names],gaps_detail=out)
(B/'attribution.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ['gaps_detail','unattributed']},indent=2,ensure_ascii=False));print('UNATTRIBUTED',len(summary['unattributed']));print(json.dumps(summary['unattributed'][:3],indent=2))
