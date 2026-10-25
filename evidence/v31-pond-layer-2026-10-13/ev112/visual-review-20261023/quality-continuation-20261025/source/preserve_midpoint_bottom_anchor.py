"""Directed B correction: ten buried vertices, unchanged contact roof and poses."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.spatial import ConvexHull
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/water'))
from review_compact_collision_v31 import load,vertices,py3d
from compact_stream_collision_v31 import add_component
from mesh_quality_v31 import closed_component
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bounds(lods):
    xyz=np.array([p.coords for lod in lods for p in lod.points]);return np.array([xyz.min(0),xyz.max(0)])
def roof(lod):
    tri=vertices(lod,lod.faces);n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);return tri[n[:,1]<-1e-10]
def cost(lod):return dict(components=len(lod.selections),faces=len(lod.faces),vertices=len(lod.points),max_vertices_per_component=max(len(s.points) for s in lod.selections.values()),max_faces_per_component=max(len(s.faces) for s in lod.selections.values()))

A=R/'river-131-midpoint-a';B=R/'river-131-midpoint-b';U=R/'collision-overlap-u2';name='cs_131p0_0_0300.p3d'
assert sha(A/'author-report.json')=='a04e40a2abb3f5f652fa30e3dbda3573b9b88653c319f0661dc66efa71ecea15'
author=json.loads((A/'author-report.json').read_text());urep=json.loads((U/'author-report.json').read_text())
inst=next(x for x in author['instances'] if x['model'].endswith('\\'+name));ui=next(x for x in urep['instances'] if x['model']==inst['model'])
source=A/'source/baltic_stream_pilot'/name;previous=U/'source/baltic_stream_pilot'/name
assert sha(source)==inst['sha256'] and sha(previous)==ui['sha256'] and inst['origin']==ui['origin']
header,lods,blobs=load(source);_,ulods,_=load(previous);old=lods[1]
target=min(p.coords[1] for p in ulods[1].points);assert target==-1.02734375
chosen=[]
for label,selection in old.selections.items():
    p=np.array([v.coords for v in selection.points]);lo=p[:,1].min()
    if lo<target:
        assert lo==-1.03515625 and (p[p[:,1]<target,1]==lo).all() and p[p[:,1]>lo,1].min()-target==.34375
        chosen.append(label)
assert chosen==['Component0036','Component0039']
B.mkdir(exist_ok=False);destroot=B/'source/baltic_stream_pilot';destroot.mkdir(parents=True);prov=B/'provenance';prov.mkdir()
for item in author['instances']:
    p=A/'source'/item['model'].replace('\\','/');assert sha(p)==item['sha256'];(destroot/p.name).write_bytes(p.read_bytes())
for n in ('config.cpp','$PBOPREFIX$'):(destroot/n).write_bytes((A/'source/baltic_stream_pilot'/n).read_bytes())
for n in ('terrain.npz','envelope.npy','cover.npy','131.0-0-surfaces.npz'):(B/n).write_bytes((A/n).read_bytes())
(prov/'parent-author-report.json').write_bytes((A/'author-report.json').read_bytes());(prov/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
geo=py3d.LOD();geo.resolution=old.resolution;geo.properties.update(old.properties);volumes=[];changed=0
for index,(label,selection) in enumerate(old.selections.items(),1):
    assert label==f'Component{index:04d}'
    points=list(selection.points);lookup={p:i for i,p in enumerate(points)}
    xyz=np.array([p.coords for p in points]);before=xyz.copy();faces=np.array([[lookup[v.point] for v in f.vertices] for f in selection.faces])
    assert faces.shape[1]==3
    if label in chosen:
        mask=xyz[:,1]<target;changed+=int(mask.sum());xyz[mask,1]=target
        assert np.array_equal(xyz[:,[0,2]],before[:,[0,2]]) and (xyz[mask,1]-before[mask,1]==.0078125).all()
    point_start=len(geo.points);part=dict(points=xyz,faces=faces,volume=float(ConvexHull(xyz).volume))
    volumes.append(add_component(py3d,geo,part,index))
    for newp,oldp in zip(geo.points[point_start:],points):newp.mass=oldp.mass
assert changed==10
one=py3d.P3D();one.lods.append(geo);tmp=prov/'corrected.geometry';one.save(str(tmp))
dest=destroot/name;dest.write_bytes(header+blobs[0]+tmp.read_bytes()[12:]+blobs[2]+blobs[3])
nh,saved,nb=load(dest);assert nh==header and all(nb[i]==blobs[i] for i in (0,2,3))
assert cost(saved[1])==cost(old) and np.array_equal(roof(saved[1]),roof(old))
assert np.array_equal(bounds(saved).mean(0),bounds(ulods).mean(0))
mass_errors=[]
for label,selection in saved[1].selections.items():
    tri=vertices(saved[1],list(selection.faces));closure=closed_component(tri);assert closure['closed'] and closure['signed_volume']<0
    n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.linalg.norm(n,axis=1)[:,None]
    pts=np.unique(tri.reshape(-1,3),axis=0);assert np.einsum('fpc,fc->fp',pts[None]-tri[:,0,None],n).min()>=-1e-6
    assert sum(p.mass for p in selection.points)==sum(p.mass for p in old.selections[label].points)
    if label not in chosen:assert np.array_equal([p.coords for p in selection.points],[p.coords for p in old.selections[label].points])
before_sha=inst['sha256'];inst['sha256']=sha(dest);inst['signed_collision_volume']=float(sum(volumes))
correction=dict(status='SAVED_BOTTOM_ANCHOR_REQUIRES_GLOBAL_BINARY_AND_RUNTIME',model=name,components=chosen,changed_vertices=changed,delta_y_m=.0078125,target_y=target,
    roof_triangles_exact=True,other_lods_byte_exact=True,cost_unchanged=cost(saved[1]),mass_per_component_exact=True,model_centre_matches_U2=True,
    before_sha256=before_sha,after_sha256=sha(dest),parent_author_sha256=sha(A/'author-report.json'),source_sha256=sha(__file__),
    limits=['Saved bounds match; compiled centre, existing WRP poses, global overlay and native contact still require checks.'])
packing=author['collision_packing'];assert packing['status']=='CANDIDATE_GLOBAL_OVERLAY_PENDING'
row=next(x for x in packing['models'] if x['model']==name);row['candidate_sha256']=sha(dest);row['bottom_anchor_correction']=correction
packing['bottom_anchor_correction']=correction;packing['sources'][str(Path(__file__))]=sha(__file__)
for item in author['instances']:assert sha(B/'source'/item['model'].replace('\\','/'))==item['sha256']
(B/'author-report.json').write_text(json.dumps(author,indent=2),encoding='utf-8');(B/'packing-report.json').write_text(json.dumps(packing,indent=2),encoding='utf-8')
(B/'bottom-anchor-report.json').write_text(json.dumps(correction,indent=2)+'\n',encoding='utf-8');print(json.dumps(correction,indent=2))
