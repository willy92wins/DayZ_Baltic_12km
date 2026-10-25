"""Freeze server controls before deployment; includes every new terrain vertex."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
Q=Path('E:/DayZ-Baltic-Build/qc-council-20261024');sys.path[:0]=[str(W/'tools/water'),str(W/'tools/navigation')]
from waterway_common import sample
from review_compact_collision_v31 import load,vertices
from prepare_visual_probe_v31 import height
P=R/'probe-combined';path=P/'points.json';original=path.read_bytes();backup=P/'points-original.json';assert not backup.exists();backup.write_bytes(original);doc=json.loads(original)
H=np.load(R/'combined-merged/terrain-buried.npz')['heights'].astype(float);H0=np.load(Q/'road-merged-s3/terrain-buried.npz')['heights'];existing={(p['x'],p['z']) for p in doc['points']}
def add(x,z,kind,**kwargs):
    x,z=round(float(x),6),round(float(z),6)
    if (x,z) in existing:return
    ground=float(sample(H,np.array([x+200000]),np.array([z]))[0]);doc['points'].append(dict(id=len(doc['points']),x=x,z=z,ground=ground,expect='ground',kind=kind,**kwargs));existing.add((x,z))
for r,c in np.argwhere(H!=H0):add(c*6,12282-r*6,'all_changed_terrain_vertices')
target=np.load(R/'terrain-free-final/domains.npz')['target']
for r,c in np.argwhere(target):
    for dx,dz in ((4,-2),(2,-4)):add(c*6+dx,12282-r*6+dz,'target_native_triangle_centroid')
report=json.loads((R/'river-131-compact-a/contact-review-final.json').read_text());author=json.loads((R/'river-131-compact-a/author-report.json').read_text());bed=[];water=[]
for inst in author['instances']:
    _,lods,_=load(R/'river-131-compact-a/source'/inst['model'].replace('\\','/'))
    for dest,wet in ((bed,False),(water,True)):
        faces=[f for f in lods[0].faces if ('water_streambed.rvmat' in f.material)==wet];dest.extend(vertices(lods[0],faces)+inst['origin'])
bed=np.array(bed);water=np.array(water)
for label,row in report['contact']['extrema'].items():
    x,z=row['xz'];add(x,z,'compact_collision_'+label,site='131.0-0')
    p=doc['points'][-1];q=np.array([p['x'],p['z']]);p['bed']=height(bed,q);p['collision_pilot']=p['bed']>p['ground']+.03
    wy=height(water,q)
    if wy is None:p['expect']='dry';p['water_ext']=None
    else:p['expect']='wet';p['water_ext']=wy-.25
doc['counts']=dict(Counter(p['kind'] for p in doc['points']));doc['scope']+=' Includes all 1648 changed native vertices, both native triangles at 43 target spikes, and the two extrema of the compact collision certificate.'
mission=P/'BalticVisualProbeV1.BalticTrial';(mission/'points.csv').write_text(''.join(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n" for p in doc['points']),encoding='ascii')
doc['inputs'][str(mission/'points.csv')]=hashlib.sha256((mission/'points.csv').read_bytes()).hexdigest();doc['inputs'][str(Path(__file__))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
path.write_text(json.dumps(doc,indent=2),encoding='utf-8');print(len(doc['points']),doc['counts'])
