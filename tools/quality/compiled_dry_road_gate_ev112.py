"""Saved ODOL/experimental-package gates. Conditional shader metadata is never a map PASS."""
import os,time
START=time.monotonic()
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
from pathlib import Path
import argparse,collections,hashlib,importlib.util,json,struct,sys,types
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'water'),str(HERE.parent/'playtest'),str(HERE)]
from review_compact_collision_v31 import load,overlay
from compare_non_geometry_lods_v31 import normalized,canonical_lod
from deployed_surface_inventory_ev112 import sections,transform
from attach_navmesh import read_pbo
import water_constraint_diagnostic_ev112 as meter

NAME='cs_kit_118_0000.p3d'
CANDIDATE_SHA='351424ab535a3e3eb40fc460a22360ab442776446055b116e10c0ba6134579f5'
ANCHORS={
 'package-kit7-contact-only-20261026/Addons/baltic_stream_pilot.pbo':'3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6',
 'pilot-kit7-fc-20261026/temp/baltic_stream_pilot/'+NAME:'0e3c8ef8b2b07ce8f81dfb45ad02fd64053cf9c2da41e2160b7a977126d26607',
 'pilot-kit7-fc-20261026/source/baltic_stream_pilot/'+NAME:'bbf4d5e40dfcb3bf5216981f10cbf21db681d403ea51c4e20676956289207c5a',
 'dry-road-compile-pair-20261028/control/saved-odol.p3d':'8b9892e1607c5477d521d87ed475a8ef381fbdca5eb3c437dcc72b1c5d4464f3',
 'dry-road-compile-pair-20261028/candidate/saved-odol.p3d':CANDIDATE_SHA,
 'dry-road-compiler-isolation-20261028/positions_only/saved-odol.p3d':'3e6f43446797fcdff44be18ee306b206c0273be3425c739254596dbbd1f7a28d',
 'dry-road-compiler-isolation-20261028/normals_only/saved-odol.p3d':'dee2dca15b99dfcecd8c629d25411250a4c471033619c8c4989abd7dc2182acc',
 'dry-road-mlod-candidate-r2-20261028/source/baltic_stream_pilot/'+NAME:'d13069d5ec2816cdacc90891a83e5f92f517c4c33703380d534d3f7538baddef',
 'dry-bed-road-candidate-20261028/kit-118-candidate.npz':'93168efe934d9ff8a95bde1ceff3e54d0667bb0b358b36c0b7c028a443fa707d',
 'dry-bed-road-consumer-20261028/report.json':'e39cd568426abceb70e71c0453d4f9587324b323e7487b534c65c1a5816ac1e4',
 'dry-road-mlod-consumer-20261028/report.json':'b71fd86932cc382c525fdb290b8e2b2daf0bd9055776f3d0adb8959145aa7e18',
 'deployed-surface-prototypes-20261028/instances.npz':'6c0ae3b5b9dc9bbcbb9333bd8c6877ac0ed914a3508ea543d0af5f01829f6e37',
}
READER_HASHES={'odol_reader.py':'fa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57','bis_reader.py':'c9e5194aaf03e3c1a54578fa52950a1e0236c52ecb6b2597756b6a9ee618b70b','math_types.py':'b6ac444ca190a5cb8a7e5c0f423fafeceb31ddc8a805f2374b466ae5da6fdd10'}
def require(ok,reason):
    if not bool(ok):raise ValueError(reason)
def sha(p):return meter.sha(p)
def xyz(values):return np.asarray([[p.x,p.y,p.z] for p in values],float).reshape(-1,3)
def key(t):
    v=tuple(map(tuple,t));return min(v,v[1:]+v[:1],v[2:]+v[:2])
def same(a,b):return normalized(a)==normalized(b)
def stripped(lod):
    value=canonical_lod(lod);value.pop('rest_data_offset_probe',None);return value
def read_backend(reader_root):
    for name,d in READER_HASHES.items():require(sha(reader_root/name)==d,'reader_changed:'+name)
    sys.path.insert(0,str(reader_root));p=reader_root/'odol_reader.py';source=p.read_text(encoding='utf-8')
    needle='        lod.size_of_rest_data = reader.read_uint32()';require(source.count(needle)==1,'reader_instrumentation_anchor')
    source=source.replace(needle,needle+'\n        lod.rest_data_offset_probe = reader.position')
    mod=types.ModuleType('dry_road_instrumented_odol');mod.__file__=str(p);sys.modules[mod.__name__]=mod;exec(compile(source,str(p),'exec'),mod.__dict__)
    return mod.ODOL

def known_fields(control,other,allowed,label):
    a,b=normalized(control),normalized(other)
    # Instrumentation-only absolute offset, checked separately against the end.
    for value in (a,b):value.pop('rest_data_offset_probe',None)
    changed={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
    require(changed<=set(allowed),label+':unknown_fields:'+','.join(sorted(changed-set(allowed))))
    return sorted(changed)

def st_frames(raw,normals):
    packed=np.frombuffer(raw,'<u4').reshape(-1,2);vectors=[]
    for i in range(2):
        a=packed[:,i];v=np.stack((a&1023,(a>>10)&1023,(a>>20)&1023),axis=1).astype(np.int32);v[v>511]-=1024;vectors.append(v*(-1/511))
    t,b=vectors;n=np.asarray(normals)
    return dict(normT=np.linalg.norm(t,axis=1),normB=np.linalg.norm(b,axis=1),dotTB=np.einsum('vc,vc->v',t,b),dotTN=np.einsum('vc,vc->v',t,n),dotBN=np.einsum('vc,vc->v',b,n),det=np.einsum('vc,vc->v',np.cross(t,b),n))

def check_frames(a,b):
    old=st_frames(a.st_raw,xyz(a.normals));new=st_frames(b.st_raw,xyz(b.normals))
    require(np.array_equal(np.sign(old['det']),np.sign(new['det'])),'ST_handedness')
    for label,value in new.items():require(np.isfinite(value).all() and (value>=old[label].min()).all() and (value<=old[label].max()).all(),'ST_control_envelope:'+label)

def check_st(a,b,y,n):
    coords=[xyz(l.vertices) for l in (a,b,y,n)];norms=[xyz(l.normals) for l in (a,b,y,n)]
    require(all(np.array_equal(coords[0][:,[0,2]],p[:,[0,2]]) for p in coords),'ST_vertex_domain')
    faces=[[int(i) for i in f.vertex_indices] for f in a.faces]
    require(all(faces==[[int(i) for i in f.vertex_indices] for f in l.faces] for l in (b,y,n)),'ST_face_domain')
    Y=np.any(coords[0]!=coords[1],axis=1);N=np.any(norms[0]!=norms[1],axis=1);ring=Y.copy()
    for ids in faces:
        if Y[ids].any():ring[ids]=True
    slots=[np.frombuffer(l.st_raw,np.uint8).reshape(-1,8) for l in (a,b,y,n)]
    require(all(len(s)==len(Y) for s in slots),'ST_slot_count');A,B,C,D=slots
    high=[np.frombuffer(l.st_raw,'<u4')&0xc0000000 for l in (a,b,y,n)]
    require(all(np.array_equal(high[0],h) for h in high[1:]),'ST_uninterpreted_high_bits')
    changed=np.any(A!=B,axis=1);cy=np.any(A!=C,axis=1);cn=np.any(A!=D,axis=1)
    require(not (changed&~ring&~N).any() and not (cy&~ring).any() and not (cn&~N).any(),'ST_nonlocal_change')
    require(np.array_equal(B[N&~ring],D[N&~ring]) and np.array_equal(B[ring&~N],C[ring&~N]),'ST_separated_dependency')
    require(all(np.array_equal(A[~changed],s[~changed]) for s in (C,D)),'ST_cancelled_or_new_diagnostic_change')
    check_frames(a,b)
    return dict(changed_vertices=int(Y.sum()),changed_normals=int(N.sum()),incident_vertices=int(ring.sum()),changed_ST_slots=int(changed.sum()),constant_slots=int((~changed).sum()),semantic_layout='HYPOTHESIS_ONLY',measured_control_envelope_preserved=True)

def section_metadata(a,b,y,n):
    require(len(a.sections)==len(b.sections)==len(y.sections)==len(n.sections)==2,'visual_sections')
    require(all(same(a.sections[1],l.sections[1]) for l in (b,y,n)),'water_section_changed')
    allowed={'area_over_tex'}
    for l in (b,y,n):known_fields(a.sections[0],l.sections[0],allowed,'bed_section')
    require(same(b.sections[0].area_over_tex,y.sections[0].area_over_tex) and same(a.sections[0].area_over_tex,n.sections[0].area_over_tex),'area_tex_dependency')
    values=np.asarray(b.sections[0].area_over_tex,float);require(np.isfinite(values).all() and (values>0).all(),'area_tex_nonpositive')
    return dict(water_section_exact=True,bed_area_tex_before=list(a.sections[0].area_over_tex),bed_area_tex_after=list(values),formula='INCONCLUSIVE_SEMANTIC',dependency='Y_ONLY')

def source_geometry(od,mlods,matrix,origin):
    require(not od.lod_errors and len(od.lods)==4 and all(l.lod_end_ok for l in od.lods),'incomplete_odol')
    require(np.array_equal((origin+xyz([od.model_info.bounding_center])[0]).astype(np.float32).astype(float),matrix[9:]),'world_pose_changed')
    roles=[];triangles={};attrs={};normal_corners=0;source_corners=0
    for li,lod in enumerate(od.lods):
        points=transform(xyz(lod.vertices),matrix);src=mlods[li]
        require(np.array_equal(np.frombuffer(lod.vertex_raw,'<f4').reshape(-1,3),xyz(lod.vertices)),'decoded_vertex_raw_mismatch')
        want=np.array([[np.array(v.point.coords)+origin for v in f.vertices] for f in src.faces]);got=np.array([points[f.vertex_indices] for f in lod.faces])
        require(collections.Counter(map(key,want))==collections.Counter(key(t[::-1]) for t in got),'source_face_counter:'+str(li))
        source_corners+=sum(len(f.vertices) for f in src.faces);triangles[li]=got
        if li not in (0,3):continue
        assignment,labels=sections(lod);uv=[np.asarray(s.uv_data).reshape(-1,2) for s in lod.uv_sets];normals=xyz(lod.normals);normal_words=np.frombuffer(lod.normal_raw,'<u4')
        require(all(len(v)==len(points) for v in uv) and len(normals)==len(points),'attribute_domain')
        require(len(normal_words)==len(points),'normal_raw_domain')
        lookup={};source_roles=collections.Counter();actual_roles=collections.Counter();rows=[]
        for f in src.faces:
            role=(f.material.lower().replace('\\','/'),f.texture.lower().replace('\\','/'));source_roles[role]+=1
            for v in f.vertices:
                p=np.array(v.point.coords)+origin;k=(role,tuple(p[[0,2]]));value=(tuple(p),tuple(src.facenormals[v.normal_index]),v.point_index)
                require(k not in lookup or lookup[k]==value,'ambiguous_source_role');lookup[k]=value
        for fi,f in enumerate(lod.faces):
            s=labels[int(assignment[fi])];role=(s['material'],s['texture']);actual_roles[role]+=1;corners=[]
            for i in f.vertex_indices:
                p=points[i];k=(role,tuple(p[[0,2]]));require(k in lookup,'source_corner_xz');value=lookup[k];require(tuple(p)==value[0],'source_corner')
                if li==0:
                    integers=np.rint(-np.array(value[1])*511).astype(np.int32);word=int(integers[0]&1023)|(int(integers[1]&1023)<<10)|(int(integers[2]&1023)<<20)
                    require(np.array_equal(normals[i],integers*(-1/511)) and int(normal_words[i])==word,'visual_normal_codec');normal_corners+=1
                corners.append((value[2],tuple(tuple(u[i]) for u in uv)))
            cycle=min(tuple(corners[i:]+corners[:i]) for i in range(len(corners)));rows.append((role,cycle))
        require(source_roles==actual_roles,'surface_role_counts');attrs[li]=collections.Counter(rows)
        roles.append(dict(lod=li,counts=[dict(material=m,texture=t,source_count=source_roles[(m,t)],compiled_count=count) for (m,t),count in sorted(actual_roles.items())]))
    assignment,labels=sections(od.lods[0]);bed=triangles[0][[labels[int(i)]['material']=='dz/water/streambed/data/streambed_leaf_long_straight.rvmat' for i in assignment]]
    geo=triangles[1];n=np.cross(geo[:,1]-geo[:,0],geo[:,2]-geo[:,0]);roof=geo[n[:,1]>1e-10];contact=overlay(bed,roof)
    require(all(contact['checks'].values()) and contact['minimum_pair_height_error_m']==contact['maximum_height_error_m']==0,'compiled_contact')
    return dict(source_corners_checked=source_corners,visual_normal_corners_checked=normal_corners,roles=roles,contact=contact),attrs

def verify_models(before,a,b,y,n,mlods_control,mlods_candidate,matrix):
    origin=np.array([8262.,7.,8934.]);require(np.array_equal(matrix[:9],[1,0,0,0,1,0,0,0,1]),'rotation_requires_new_proof')
    require(all(not od.lod_errors and len(od.lods)==4 and all(l.lod_end_ok for l in od.lods) for od in (before,a,b,y,n)),'incomplete_model_set')
    require(same(before.model_info,a.model_info) and all(stripped(x)==stripped(z) for x,z in zip(before.lods,a.lods)),'control_not_current_baseline')
    allowed_lod=[{'face_area','normal_raw','normals','sections','size_of_rest_data','st_raw','vertex_raw','vertices'}, {'size_of_rest_data','vertex_raw','vertices'},set(),{'size_of_rest_data','vertex_raw','vertices'}]
    differences=[]
    for tag,od in (('candidate',b),('Y_only',y),('N_only',n)):
        require(not od.lod_errors and len(od.lods)==4,'diagnostic_odol_incomplete')
        mi=known_fields(a.model_info,od.model_info,{'center_of_mass','inv_inertia'},tag+':model_info')
        changed=[]
        for li,(old,lod) in enumerate(zip(a.lods,od.lods)):
            require(lod.lod_end_ok and lod.size_of_rest_data==lod.declared_end-lod.rest_data_offset_probe+4,'rest_data_size:'+tag+':'+str(li))
            if li==3:
                # Same exact labelled/wound face multiset as the baseline proof;
                # a diagnostic compiler build can reorder Roadway faces too.
                changed.append(known_fields(canonical_lod(old),canonical_lod(lod),allowed_lod[li],tag+':LOD'+str(li)))
            else:changed.append(known_fields(old,lod,allowed_lod[li],tag+':LOD'+str(li)))
        differences.append(dict(build=tag,model_info=mi,lods=changed))
    for lod in a.lods:require(lod.size_of_rest_data==lod.declared_end-lod.rest_data_offset_probe+4,'control_rest_data_size')
    for li in range(4):
        require(same(b.lods[li].vertex_raw,y.lods[li].vertex_raw) and same(a.lods[li].vertex_raw,n.lods[li].vertex_raw),'position_dependency:'+str(li))
        require(same(a.lods[li].normal_raw,y.lods[li].normal_raw) and same(b.lods[li].normal_raw,n.lods[li].normal_raw),'normal_dependency:'+str(li))
    for field in ('center_of_mass','inv_inertia'):
        require(same(getattr(b.model_info,field),getattr(y.model_info,field)) and same(getattr(a.model_info,field),getattr(n.model_info,field)),'mass_property_dependency:'+field)
    require(b.lods[0].face_area==y.lods[0].face_area and a.lods[0].face_area==n.lods[0].face_area,'face_area_dependency')
    st=check_st(a.lods[0],b.lods[0],y.lods[0],n.lods[0]);section=section_metadata(a.lods[0],b.lods[0],y.lods[0],n.lods[0])
    old_geometry,oldattrs=source_geometry(a,mlods_control,matrix,origin);new_geometry,newattrs=source_geometry(b,mlods_candidate,matrix,origin)
    require(oldattrs==newattrs,'compiled_UV_or_role_topology_changed')
    return dict(status='COMPILED_GEOMETRY_GATE_PASS_METADATA_CONDITIONAL',control=old_geometry,candidate=new_geometry,ST=st,section=section,decoded_changes=differences,limits=['ST semantic layout and area_over_tex formula remain unverified; only dependency/locality/control-envelope evidence.','Experimental package may be composed; engine/visual/RAM/global acceptance is not granted.'])

def package_identity(before_props,before,after_props,after,expected_model_bytes):
    require(before_props==after_props and before_props.get('prefix')=='baltic_stream_pilot','PBO_properties')
    require(list(before)==list(after),'PBO_entry_order_or_identity')
    require(sum(k.endswith('.p3d') for k in before)==201 and set(before)=={k for k in before if k.endswith('.p3d')}|{'config.bin'},'PBO_universe')
    changed=[k for k in before if before[k]!=after[k]];require(changed==[NAME],'PBO_changed_entries')
    require(after[NAME]==expected_model_bytes,'PBO_candidate_payload')
    return dict(changed_entries=changed,unchanged_model_entries=sum(k.endswith('.p3d') and before[k]==after[k] for k in before),config_exact=before['config.bin']==after['config.bin'],properties_exact=before_props==after_props,ordered_identity_exact=list(before)==list(after))

def inputs(root,reader_root):
    pins={str(root/p):d for p,d in ANCHORS.items()};pins.update({str(reader_root/p):d for p,d in READER_HASHES.items()})
    for p,d in pins.items():require(sha(p)==d,'independent_anchor:'+p)
    for p in (Path(__file__).resolve(),HERE/'deployed_surface_inventory_ev112.py',HERE.parent/'water/review_compact_collision_v31.py',HERE.parent/'water/compare_non_geometry_lods_v31.py',HERE.parent/'playtest/attach_navmesh.py'):pins[str(p)]=sha(p)
    for p,d in json.loads((root/'dry-road-compile-pair-20261028/inputs.json').read_bytes()).items():require(sha(p)==d,'compile_input_changed:'+p);pins[p]=d
    return pins

def context(root,reader_root):
    ODOL=read_backend(reader_root);paths=['pilot-kit7-fc-20261026/temp/baltic_stream_pilot/'+NAME,'dry-road-compile-pair-20261028/control/saved-odol.p3d','dry-road-compile-pair-20261028/candidate/saved-odol.p3d','dry-road-compiler-isolation-20261028/positions_only/saved-odol.p3d','dry-road-compiler-isolation-20261028/normals_only/saved-odol.p3d']
    ods=[ODOL.from_file(str(root/p),strict=True) for p in paths]
    _,old,_=load(root/'pilot-kit7-fc-20261026/source/baltic_stream_pilot'/NAME)
    _,new,_=load(root/'dry-road-mlod-candidate-r2-20261028/source/baltic_stream_pilot'/NAME)
    grid=np.load(root/'dry-bed-road-candidate-20261028/kit-118-candidate.npz')['grid'][:21]
    require(np.array_equal(np.array([p.coords for p in new[0].points[:grid.size//3]])+[8262,7,8934],grid.reshape(-1,3)),'numeric_to_MLOD_chain')
    poses=np.load(root/'deployed-surface-prototypes-20261028/instances.npz');idx=np.flatnonzero(poses['ids']==19394363);require(len(idx)==1,'WRP_instance_identity')
    return ods,old,new,poses['matrix'][idx[0]],dict(rows_checked=int(grid.shape[0]),points_checked=int(grid.size//3),source='numeric candidate first model slice',comparison='EXACT')

def run(root,reader_root,out):
    pins=inputs(root,reader_root);ods,old,new,matrix,numeric_chain=context(root,reader_root);result=verify_models(*ods,old,new,matrix)
    for p,d in pins.items():require(sha(p)==d,'input_changed_during_verification:'+p)
    result.update(candidate_odol_sha256=CANDIDATE_SHA,numeric_candidate_sha256=ANCHORS['dry-bed-road-candidate-20261028/kit-118-candidate.npz'],numeric_proof_sha256=ANCHORS['dry-bed-road-consumer-20261028/report.json'],numeric_to_MLOD=numeric_chain,inputs=pins,measurement=meter.memory())
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('reader_root',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
    meter.STARTED=START;meter.MAX_SECONDS=300;stop=meter.bounded(a.output)
    try:result=run(a.root,a.reader_root,a.output);meter.dump(a.output/'report.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','control','candidate','decoded_changes')}))
    except Exception as exc:meter.dump(a.output/'failure.json',dict(type=type(exc).__name__,error=str(exc),measurement=meter.memory()));raise
    finally:stop.set()
