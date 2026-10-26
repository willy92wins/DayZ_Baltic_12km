"""Full packed kit7 contact at poses derived from each actual compiled ODOL centre."""
from pathlib import Path
import hashlib,io,json,struct,sys,collections
import numpy as np
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;B=R/'river-kit7-contact-only-20261026';A=R/'river-kit7-a-on-f-20261026'
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
build=read(R/'kit7-contact-only-build-20261026/receipt.json')
assert build['status']=='ISOLATED_OVERLAP_BINARY_PASS_PACKED_OVERLAY_PENDING'
frozen=read(R/'kit7-contact-only-build-20261026/inputs.json')
assert all(sha(Path(p))==h for p,h in frozen.items())
assert sha(Path(odol_reader.__file__))=='fa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57'
pbo=B/'packed/baltic_stream_pilot.pbo';binary=read(B/'binary-review.json')
assert binary['status']=='BINARY_PASS' and sha(pbo)==binary['pbo_sha256']==build['pbo_sha256']
assert read(B/'records.json')==read(R/'river-kit7-midpoint-a-20261026/records.json')
new=read(B/'author-report.json');require_eligible_packing(new)
old={x['model']:x for x in read(A/'author-report.json')['instances']};poses={x['model']:x for x in read(B/'records.json')}
_,_,entries=read_pbo(pbo);assert {n for n in entries if n.lower().endswith('.p3d')}=={i['model'].split('\\')[-1] for i in new['instances']}
assert len(new['instances'])==len(old)==len(poses)==139
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
    bc=od.model_info.bounding_center
    assert np.array_equal(matrix[9:],(np.array(inst['origin'])+[bc.x,bc.y,bc.z]).astype(np.float32).astype(float))
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
        assert len(s.selected_vertices)<=72 and len(s.selected_faces)<=140
        t=tri[selected];closure=closed_component(t);assert closure['closed'] and closure['signed_volume']>0
        normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);normal/=np.linalg.norm(normal,axis=1)[:,None]
        p=np.unique(t.reshape(-1,3),axis=0);assert np.einsum('fpc,fc->fp',p[None]-t[:,0,None],normal).max()<=1e-6
        assigned.extend(s.selected_faces);component_count+=1
    assert sorted(assigned)==list(range(len(tri))) and component_count==inst['collision_components']
    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);roof=tri[normal[:,1]>1e-10];assert len(roof)
    all_source.extend(bed);all_roof.extend(roof)
    rows.append(dict(model=name,components=component_count,source_bed_triangles=len(bed),roof_triangles=len(roof),faces=len(tri),vertices=len(xyz),closed_convex_components=True,all_faces_assigned_once=True,derived_pose_from_actual_ODOL_center=True,all_packed_faces_exact_reversed_source=True,odol_sha256=hashlib.sha256(entries[name]).hexdigest()))
source=np.asarray(all_source);roof=np.asarray(all_roof);contact=overlay(source,roof)
assert all(contact['checks'].values())
# Negative controls on the first two adjacent real models; the positive overlay above covers all139.
source_n=np.asarray(all_source[:sum(x['source_bed_triangles'] for x in rows[:2])])
roof_n=np.asarray(all_roof[:sum(x['roof_triangles'] for x in rows[:2])])
raised=roof_n.copy();raised[:,:,1]+=.05;negative_height=overlay(source_n,raised)
mid=float(np.median(roof_n[:,:,0]));half=roof_n[(roof_n[:,:,0].max(axis=1)<mid)];assert len(half)
negative_hole=overlay(source_n,half)
assert not negative_height['checks']['vertical_contact_error'] and not negative_hole['checks']['full_source_covered']
report=dict(status='PACKED_KIT7_OVERLAP_CONTACT_PASS',models=rows,contact=contact,
    negative_controls=dict(raised_5cm_rejected=True,removed_half_rejected=True,scope_models=[r['model'] for r in rows[:2]]),
    sources={str(p):sha(p) for p in (pbo,A/'author-report.json',B/'author-report.json',B/'records.json',B/'binary-review.json',R/'kit7-contact-only-build-20261026/receipt.json',Path(__file__),Path(odol_reader.__file__),Path(review_compact_collision_v31.__file__),Path(mesh_quality_v31.__file__))},
    limits=['Full decoded packed kit7 geometry at derived float32 poses, all139models/joints. No compiled WRP placement yet.','Reader is the locally verified v56 backend; no native/contact/AI/FPS acceptance.'])
target=B/'compiled-contact-review.json';assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],models=len(rows),components=sum(x['components'] for x in rows),checks=contact['checks'],negative_controls=report['negative_controls']),indent=2))
