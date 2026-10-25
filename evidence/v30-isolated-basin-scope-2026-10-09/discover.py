"""Read-only closure of finite water support under rigid compiled-instance moves."""
from pathlib import Path
import json,csv,hashlib
import numpy as np
from scipy.ndimage import label
B=Path(__file__).parent;R=Path('E:/DayZ-Baltic-Build');BASE=R/'v30-low-water-components-20261009'
t=dict(np.load(R/'v30-native-hinge-finish-20261009/candidate/terrain.npz'));h=t['heights'];p=np.load(R/'v30-global-water-risk-20261009/frozen-field-reference/plane.npy')
labels=np.load(BASE/'physical-component-labels.npz')['triangles'];support,n=label(np.isfinite(p),structure=np.ones((3,3)))
parent=np.arange(n+1)
def root(a):
    while a!=parent[a]:parent[a]=parent[parent[a]];a=parent[a]
    return a
def union(values):
    values=list(values)
    if values:
        a=root(values[0])
        for b in values[1:]:parent[root(b)]=a
def bounds(o,pad=0):
    x0,z0,x1,z1=o['bounds'];return max(0,int(np.floor((12282-z1)/6))-pad),min(2047,int(np.ceil((12282-z0)/6))+pad),max(0,int(np.floor(x0/6))-pad),min(2047,int(np.ceil(x1/6))+pad)
objects=json.loads((BASE/'compiled-instance-bounds.json').read_text())['objects'];object_domains=[]
for o in objects:
    r0,r1,c0,c1=bounds(o,1)
    ids=np.unique(support[r0:r1,c0:c1]);ids=ids[ids>0];union(ids);object_domains.append(ids)
mapping=np.array([root(i) for i in range(n+1)]);groups={}
for i,ids in enumerate(object_domains):
    if not len(ids):continue
    gid=int(mapping[ids[0]]);groups.setdefault(gid,[]).append(i)
physical={int(r['component']):r for r in csv.DictReader(open(BASE/'physical-components.csv'))};rows=[]
target={i for i,r in physical.items() if float(r['area_m2'])>=1 and r['has_flowing']=='False' and float(r['below_sea_crest_m2'])>=1}
processed=set()
for gid,indices in groups.items():
    # Native support is closed under compiled boxes and shared terrain vertices.
    wetcells=mapping[support]==gid;components=set(map(int,np.unique(labels[wetcells])))-{-1}
    hit=components&target
    if not hit:continue
    corecells=wetcells.copy()
    for i in indices:
        r0,r1,c0,c1=bounds(objects[i]);corecells[r0:r1,c0:c1]=True
    core=np.zeros(h.shape,bool)
    for dr,dc in [(0,0),(0,1),(1,0),(1,1)]:core[dr:dr+2047,dc:dc+2047]|=corecells
    other=np.zeros(h.shape,bool)
    for dr,dc in [(0,0),(0,1),(1,0),(1,1)]:other[dr:dr+2047,dc:dc+2047]|=np.isfinite(p)&~corecells
    engineering=core&(t['reserve']|t['platform']);flow=any(physical[k]['has_flowing']=='True' for k in components)
    large=any(float(physical[k]['area_m2'])>100000 for k in components)
    delta=float(np.ceil((1.001-float(h[core].min()))/.025)*.025)
    rows.append(dict(group=gid,target_components=sorted(hit),all_components=sorted(components),objects=[objects[i]['id'] for i in indices],water_cells=int(wetcells.sum()),support_cells=int(corecells.sum()),core_vertices=int(core.sum()),low_bed_m=float(h[core].min()),proposed_shift_m=delta,engineering_vertices=int(engineering.sum()),shared_other_water_vertices=int((core&other).sum()),flowing=flow,big_lake=large,narva_vertices=int((core&t['narva']).sum()),eligible=not(engineering.any() or flow or large or (core&other).any()),level_range=[float(p[wetcells].min()),float(p[wetcells].max())]))
    processed|=hit
report=dict(status='READ_ONLY_LEVEL_POLICY_SCOPE_NO_TERRAIN_EDIT',target_standing_components=len(target),covered=sorted(processed),missing=sorted(target-processed),groups=rows,eligible_groups=sum(r['eligible'] for r in rows),eligible_targets=sum(len(r['target_components']) for r in rows if r['eligible']),limits=['Closure is conservative and can include dry compiled bounding support.','No level policy approved by this file; no new terrain authored.','Proposed shifts reuse EV26 bed>=1.001m quantization, not a new visual tuning sweep.'])
(B/'scope.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['groups','covered']}));print(json.dumps([{k:v for k,v in row.items() if k not in ['all_components','objects','target_components']} for row in rows],indent=2))
