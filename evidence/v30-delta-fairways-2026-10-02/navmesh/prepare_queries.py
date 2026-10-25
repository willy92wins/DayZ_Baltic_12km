"""Freeze additional navigation controls from terrain, before seeing new NM paths."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import label, distance_transform_edt

ROOT=Path('P:/DayZ_Baltic_12km_dev')
OUT=Path(__file__).resolve().parent
TERRAIN=Path('E:/DayZ-Baltic-Build/v30-delta-candidate/terrain_v30.npz')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(TERRAIN)=='a84dfff053523b94717b2068a96845193d01a21f0ea7ff01e0f9111280630081'
base=ROOT/'missions/BalticV30AcceptanceV1.BalticTrial'
assert sha(base/'init.c')=='0fea34a51c563d316e4a526efa4f736fc4b140a36c84c54407a838b038932041'
t=np.load(TERRAIN);h=t['heights'];dry=(t['cls']==0)&(h>=1.)
labels,_=label(dry,np.ones((3,3),dtype=int));clearance=distance_transform_edt(dry)*6
def point(x,z):
    assert x%6==0 and (12282-z)%6==0
    r,c=(12282-z)//6,x//6
    assert dry[r,c] and clearance[r,c]>=24
    return dict(vector=[x,float(h[r,c])+1,z],component=int(labels[r,c]),grid_clearance_m=float(clearance[r,c]))
a=point(8364,10200);b=point(8412,10200)
c=point(8400,10386);d=point(8448,10386)
assert a['component']==b['component'] and c['component']==d['component'] and a['component']!=c['component']
ref=json.loads((ROOT/'evidence/v30-resume-2026-10-02/acceptance-reference.json').read_text())
extra=[dict(name='island_local',start=a['vector'],end=b['vector'],expect='path'),
       dict(name='mainland_local',start=c['vector'],end=d['vector'],expect='path'),
       dict(name='island_gap',start=a['vector'],end=c['vector'],expect='disconnected')]
ref['queries']+=extra
mission=ROOT/'missions/BalticV30DeltaNavV1.BalticTrial'
deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
assert not mission.exists() and not deployed.exists() and not (OUT/'path-reference.json').exists()
code=(base/'init.c').read_text().replace('BalticV30AcceptanceMission','BalticV30DeltaNavMission').replace('baltic_v30_acceptance_v1.log','baltic_v30_delta_nav_v1.log')
csv=(base/'queries.csv').read_text()+''.join(q['name']+';'+' '.join(f'{v:.8f}' for v in q['start'])+';'+' '.join(f'{v:.8f}' for v in q['end'])+'\n' for q in extra)
for folder in (mission,deployed):
    folder.mkdir()
    (folder/'init.c').write_bytes(code.encode('utf-8'))
    (folder/'queries.csv').write_bytes(csv.encode('utf-8'))
assert (mission/'init.c').read_bytes()==(deployed/'init.c').read_bytes()
assert (mission/'queries.csv').read_bytes()==(deployed/'queries.csv').read_bytes()
ref.update(mission=str(mission),deployed_mission=str(deployed),code_sha256=sha(mission/'init.c'),queries_sha256=sha(mission/'queries.csv'),terrain_sha256=sha(TERRAIN),additional_points=[a,b,c,d])
ref['limits'].append('Additional island separation is a graph query, not actor traversal or a complete topological certification.')
(OUT/'path-reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(mission=str(mission),queries=len(ref['queries']),code_sha256=ref['code_sha256'],points=[a,b,c,d]),indent=2))
