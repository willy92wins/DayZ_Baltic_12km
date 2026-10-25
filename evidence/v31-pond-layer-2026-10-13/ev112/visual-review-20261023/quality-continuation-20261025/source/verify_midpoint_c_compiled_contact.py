"""Full packed geometry contact at the unchanged compiled F WRP poses."""
from pathlib import Path
import hashlib,io,json,struct,sys,collections
import numpy as np
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;B=R/'river-131-midpoint-c';A=R/'river-131-a'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/water'),str(W/'tools/playtest'),'C:/temp/moto_lanes/review_g3/tools']
from review_compact_collision_v31 import overlay,vertices,py3d,require_eligible_packing,load
from mesh_quality_v31 import closed_component
from attach_navmesh import read_pbo
from odol_reader import ODOL
import odol_reader,review_compact_collision_v31,mesh_quality_v31
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
assert sha(A/'author-report.json')=='3dbfcf567cbd549c20beda594eda3719b9d4944add2b244a9ffaf2f004317833'
assert sha(B/'author-report.json')=='23c5f93336b9ef781569575a35f274a7e05b6943278d7774cca46bc97ba6ed50'
assert sha(Path(odol_reader.__file__))=='fa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57'
pbo=R/'package-midpoint-c/Addons/baltic_stream_pilot.pbo';assert sha(pbo)=='c7dc430d809bcec2f29ff1fe86f266f0f9680b8ad676a8722b0b45d4494de02f'
assert sha(B/'f-compiled-poses.json')=='cb5f15a10cb1c891088a9de0d501c85e4da9097b6497334da9d60b6f31b00f9a'
assert read(B/'f-pose-binding.json')['status']=='F_WRP_62_POSES_BOUND_B27_EXACT'
new=read(B/'author-report.json');require_eligible_packing(new)
old={x['model']:x for x in read(A/'author-report.json')['instances']};poses={x['model']:x for x in read(B/'f-compiled-poses.json')}
_,_,entries=read_pbo(pbo)
base_pbo=Path('P:/Mods/@DayZ_Baltic_EV112_RectangleF/Addons/baltic_stream_pilot.pbo')
assert sha(base_pbo)=='c0be9abc9d36ee19c636325b825dbf09880a9dc31b5dfb8432e0f91d0e1cfa87'
_,_,base_entries=read_pbo(base_pbo)
model_names={i['model'].split('\\')[-1] for i in new['instances']}
changed=model_names-{'cs_131p0_0_0300.p3d','cs_131p0_0_0312.p3d'}
assert len(model_names)==27 and len(changed)==25 and set(entries)==set(base_entries)
assert {n for n in entries if entries[n]!=base_entries[n]}==changed
assert len([n for n in entries if n.lower().endswith('.p3d')])==62

all_source=[];all_roof=[];rows=[]
def oriented(tri):
    t=tuple(map(tuple,tri));return min(t,t[1:]+t[:1],t[2:]+t[:2])
for inst in new['instances']:
    name=inst['model'].split('\\')[-1];source=A/'source'/inst['model'].replace('\\','/');raw=source.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==old[inst['model']]['sha256'] and inst['origin']==old[inst['model']]['origin']
    f=io.BytesIO(raw);assert struct.unpack('<4sII',f.read(12))==(b'MLOD',257,4);visual=py3d.LOD(f)
    bed=vertices(visual,[f for f in visual.faces if 'water_streambed.rvmat' not in f.material])+inst['origin']
    path=B/'temp/baltic_stream_pilot'/name;assert entries[name]==path.read_bytes()
    od=ODOL.from_file(str(path),strict=True);assert len(od.lods)==4 and not getattr(od,'lod_errors',{}) and all(l.lod_end_ok for l in od.lods)
    geo=min(od.lods,key=lambda l:abs(l.resolution-1e13));matrix=poses[inst['model']]['matrix'];assert matrix[:9]==[1,0,0,0,1,0,0,0,1]
    xyz=(np.array([(v.x,v.y,v.z) for v in geo.vertices])+matrix[9:]).astype(np.float32).astype(float);assert np.isfinite(xyz).all()
    ids=np.array([face.vertex_indices for face in geo.faces]);assert ids.ndim==2 and ids.shape[1]==3 and ids.min()>=0 and ids.max()<len(xyz)
    tri=xyz[ids];assigned=[];component_count=0
    candidate_source=B/'source'/inst['model'].replace('\\','/')
    assert sha(candidate_source)==inst['sha256']
    _,mlods,_=load(candidate_source)
    source_geometry=(vertices(mlods[1],mlods[1].faces)+inst['origin']).astype(np.float32).astype(float)
    # Read packed winding directly and prove every triangle is the reversed
    # source triangle at the actual WRP pose, including multiplicity.
    assert collections.Counter(map(oriented,source_geometry))==collections.Counter(map(oriented,tri[:,::-1]))
    for s in geo.named_selections:
        assert s.name.startswith('component') and not s.is_sectional and not s.sections,'unverified selection encoding'
        assert s.selected_faces and len(s.selected_faces)==len(set(s.selected_faces))
        selected=np.array(s.selected_faces,dtype=int);assert selected.min()>=0 and selected.max()<len(tri)
        assert set(ids[selected].ravel())==set(s.selected_vertices)
        t=tri[selected];closure=closed_component(t);assert closure['closed'] and closure['signed_volume']>0
        normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);normal/=np.linalg.norm(normal,axis=1)[:,None]
        p=np.unique(t.reshape(-1,3),axis=0);assert np.einsum('fpc,fc->fp',p[None]-t[:,0,None],normal).max()<=1e-6
        assigned.extend(s.selected_faces);component_count+=1
    assert sorted(assigned)==list(range(len(tri))) and component_count==inst['collision_components']
    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);roof=tri[normal[:,1]>1e-10];assert len(roof)
    all_source.extend(bed);all_roof.extend(roof)
    rows.append(dict(model=name,components=component_count,faces=len(tri),vertices=len(xyz),closed_convex_components=True,all_faces_assigned_once=True,pose_from_F_WRP=True,all_packed_faces_exact_reversed_source=True,odol_sha256=hashlib.sha256(entries[name]).hexdigest()))
source=np.asarray(all_source);roof=np.asarray(all_roof);contact=overlay(source,roof)
assert all(contact['checks'].values())
# Independent consumer negative controls on the same packed roof: raising it
# breaks contact, and removing a complete spatial half leaves source uncovered.
raised=roof.copy();raised[:,:,1]+=.05;negative_height=overlay(source,raised)
mid=float(np.median(roof[:,:,0]));half=roof[(roof[:,:,0].max(axis=1)<mid)];assert len(half)
negative_hole=overlay(source,half)
assert not negative_height['checks']['vertical_contact_error'] and not negative_hole['checks']['full_source_covered']
report=dict(status='PACKED_COLLISION_AT_F_POSES_PASS',models=rows,contact=contact,
    negative_controls=dict(raised_5cm_rejected=True,removed_half_rejected=True),
    sources={str(p):sha(p) for p in (pbo,base_pbo,R/'package-midpoint-c/verification.json',A/'author-report.json',B/'author-report.json',B/'f-compiled-poses.json',B/'f-pose-binding.json',Path(__file__),Path(odol_reader.__file__),Path(review_compact_collision_v31.__file__),Path(mesh_quality_v31.__file__))},
    limits=['Full decoded packed geometry at existing float32 F poses, including all river131 joints.','Reader is the locally verified v56 backend; no native/contact/AI/FPS acceptance.'])
target=B/'compiled-contact-review.json';assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],models=len(rows),components=sum(x['components'] for x in rows),checks=contact['checks'],negative_controls=report['negative_controls']),indent=2))
