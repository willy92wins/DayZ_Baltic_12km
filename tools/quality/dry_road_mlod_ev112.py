"""Byte-preserving MLOD overlay for a validated dry height candidate; no deployment."""
import os,time
START=time.monotonic()
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='1'
from pathlib import Path
import argparse,hashlib,importlib.util,json,struct,sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'water'))
from review_compact_collision_v31 import load

def require(ok,reason):
    if not bool(ok):raise ValueError(reason)
def normals(points,triangles,up=False):
    t=points[triangles];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);size=np.linalg.norm(n,axis=1)
    require((size>1e-9).all(),'degenerate_face');n/=size[:,None];out=np.zeros_like(points)
    for j in range(3):np.add.at(out,triangles[:,j],n)
    length=np.linalg.norm(out,axis=1);require((length>0).all(),'unreferenced_bed_point');out/=length[:,None]
    return (-out if up else out).astype('<f4')
def face_normals(points,faces):
    tri=points[faces];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);size=np.linalg.norm(n,axis=1)
    require((size>1e-9).all(),'degenerate_geometry_face');return (n/size[:,None]).astype('<f4')
def patch_lod(blob,lod,ys,new_normals):
    require(struct.unpack_from('<4s6I',blob)==(b'P3DM',28,256,len(lod.points),len(lod.facenormals),len(lod.faces),0),'lod_layout')
    out=bytearray(blob);writes=[]
    for i,y in ys.items():
        raw=struct.pack('<f',float(y));require(struct.unpack('<f',raw)[0]==float(y),'nonrepresentable_height')
        offset=28+16*int(i)+4
        if blob[offset:offset+4]!=raw:out[offset:offset+4]=raw;writes.append([offset,4,'Y',int(i)])
    normal_base=28+16*len(lod.points)
    for i,n in new_normals.items():
        raw=struct.pack('<3f',*map(float,n));offset=normal_base+12*int(i)
        if blob[offset:offset+12]!=raw:out[offset:offset+12]=raw;writes.append([offset,12,'normal',int(i)])
    return bytes(out),writes
def patch_model(source,source_grid,candidate_grid,origin):
    header,lods,blobs=load(source);require(struct.unpack('<4sII',header)==(b'MLOD',257,4),'mlod_layout')
    old=np.asarray(source_grid,float).reshape(-1,3)-origin;new=np.asarray(candidate_grid,float).reshape(-1,3)-origin
    require(old.shape==new.shape and np.array_equal(old[:,[0,2]],new[:,[0,2]]) and np.isfinite(new).all() and (new[:,1]<=old[:,1]).all(),'height_only_contract')
    require(np.array_equal(old.min(0),new.min(0)) and np.array_equal(old.max(0),new.max(0)),'bounds_change_requires_new_plan')
    output=list(blobs);patches={};source_faces=None
    for li in (0,3):
        lod=lods[li];coords=np.asarray([p.coords for p in lod.points]);count=len(old)
        require(np.array_equal(coords[:count],old),'source_grid_mapping')
        faces=[f for f in lod.faces if (f.material.lower().replace('\\','/')=='dz/water/streambed/data/streambed_leaf_long_straight.rvmat' if li==0 else f.texture.lower().replace('\\','/')=='dz/surfaces/data/roadway/gravel_small_ext.paa')]
        triangles=np.asarray([[v.point_index for v in f.vertices] for f in faces],int)
        require(triangles.shape==(2*(len(source_grid)-1)*38,3) and set(triangles.ravel())==set(range(count)),'surface_topology')
        require(all(v.normal_index==v.point_index for f in faces for v in f.vertices),'normal_mapping')
        n0=normals(old,triangles,li==3);require(np.array_equal(n0,np.asarray(lod.facenormals[:count],dtype='<f4')),'source_normal_algorithm')
        if source_faces is None:source_faces=triangles
        else:require(np.array_equal(source_faces,triangles),'visual_roadway_topology')
        n1=normals(new,triangles,li==3)
        output[li],patches[str(li)]=patch_lod(blobs[li],lod,{i:y for i,y in enumerate(new[:,1])},{i:n for i,n in enumerate(n1)})
    # Strict supported family: six-point, eight-face prisms matching source bed.
    geo=lods[1];xyz=np.asarray([p.coords for p in geo.points]);updated=xyz.copy();index={tuple(v):i for i,v in enumerate(old)}
    require(len(index)==len(old),'duplicate_source_point')
    pidx={id(p):i for i,p in enumerate(geo.points)};fidx={id(f):i for i,f in enumerate(geo.faces)}
    expected={tuple(sorted(tuple(v) for v in old[t])) for t in source_faces};seen_points=[];seen_faces=[];seen_triangles=[];changed_components=[]
    for label,selection in geo.selections.items():
        ids=[pidx[id(p)] for p in selection.points];fs=[fidx[id(f)] for f in selection.faces]
        require(len(ids)==6 and len(fs)==8,'unsupported_geometry_component')
        top=[];bottom=[]
        for gi in ids:
            key=tuple(xyz[gi]);lifted=tuple(xyz[gi]+[0,180/512,0]);direct=key in index;below=lifted in index
            require(direct!=below,'ambiguous_prism_vertex')
            si=index[key if direct else lifted];(top if direct else bottom).append(si)
            updated[gi,1]+=new[si,1]-old[si,1]
        identity=tuple(sorted(tuple(v) for v in old[top]));require(len(top)==3 and sorted(top)==sorted(bottom) and identity in expected,'prism_not_source_face')
        seen_triangles.append(identity);seen_points.extend(ids);seen_faces.extend(fs)
        if not np.array_equal(updated[ids],xyz[ids]):changed_components.append(label)
    require(len(seen_triangles)==len(expected) and set(seen_triangles)==expected,'component_face_coverage')
    require(sorted(seen_points)==list(range(len(geo.points))) and sorted(seen_faces)==list(range(len(geo.faces))),'geometry_assignment')
    faces=np.asarray([[v.point_index for v in f.vertices] for f in geo.faces],int);nids=[]
    for f in geo.faces:
        ns={v.normal_index for v in f.vertices};require(len(ns)==1,'geometry_normal_sharing');nids.append(next(iter(ns)))
    require(sorted(nids)==list(range(len(geo.facenormals))),'geometry_normal_assignment')
    n0=face_normals(xyz,faces);require(np.array_equal(n0,np.asarray(geo.facenormals,dtype='<f4')[nids]),'source_geometry_normals')
    n1=face_normals(updated,faces);output[1],patches['1']=patch_lod(blobs[1],geo,{i:y for i,y in enumerate(updated[:,1])},{ni:n for ni,n in zip(nids,n1)})
    require(np.array_equal(xyz.min(0),updated.min(0)) and np.array_equal(xyz.max(0),updated.max(0)),'geometry_bounds_changed')
    require(output[2]==blobs[2] and all(len(a)==len(b) for a,b in zip(output,blobs)),'byte_layout_changed')
    return header+b''.join(output),dict(patches=patches,changed_components=changed_components,counts=[dict(points=len(l.points),normals=len(l.facenormals),faces=len(l.faces),components=len(l.selections)) for l in lods])

def run(root,w,out,meter):
    pins={}
    def pin(p,expected=None):
        digest=meter.sha(p)
        if expected:require(digest==expected,'input_changed:'+str(p))
        pins[str(p)]=digest;return p
    lineage=root/'deployed-surface-consumer-lineage-20261028/current-source-pins.json';manifest=json.loads((w/'evidence/deployed-surface-prototypes-20261028/artifact-hashes.json').read_bytes());pin(lineage,manifest[lineage.relative_to(root).as_posix()]['sha256'])
    sources=json.loads(lineage.read_bytes());require(sum(p.endswith('.p3d') for p in sources)==201,'source_universe')
    for path,digest in sources.items():pin(Path(path),digest)
    candidate=pin(root/'dry-bed-road-candidate-20261028/kit-118-candidate.npz','93168efe934d9ff8a95bde1ceff3e54d0667bb0b358b36c0b7c028a443fa707d')
    receipt=json.loads(pin(root/'dry-bed-road-consumer-20261028/report.json').read_bytes());require(receipt['status']=='DRY_BED_ROAD_CANDIDATE_INDEPENDENTLY_VERIFIED','numeric_candidate_unverified')
    raw=root/'pilot-visible-surface-extraction-20261028';models=json.loads(pin(raw/'models.json').read_bytes());m=next(x for x in models if x['model']=='baltic_stream_pilot/cs_kit_118_0000.p3d');data=np.load(pin(raw/m['file'],m['sha256']))
    model=m['model'];base=root/'pilot-kit7-fc-20261026';source=pin(base/'source'/model,'bbf4d5e40dfcb3bf5216981f10cbf21db681d403ea51c4e20676956289207c5a')
    author=json.loads((base/'author-report.json').read_bytes());inst=next(x for x in author['instances'] if x['model'].replace('\\','/')==model);origin=np.array(inst['origin'],float)
    require(np.array_equal(origin,[8262,7,8934]) and inst['sha256']==pins[str(source)],'source_origin')
    # The current source is model-only; config/prefix live in the verified PBO.
    sys.path.insert(0,str(HERE.parent/'playtest'))
    from attach_navmesh import read_pbo
    package=pin(root/'package-kit7-contact-only-20261026/Addons/baltic_stream_pilot.pbo','3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6')
    config=pin(root/'package-kit7-contact-only-20261026/compiled/baltic_stream_pilot/config.bin','57d0d0ae31a33fa329598ce2c17df43fbb8451fd3acc0844467b87fec3a239ca')
    _,props,entries=read_pbo(package)
    require(props.get('prefix')=='baltic_stream_pilot' and entries['config.bin']==config.read_bytes(),'current_config_prefix')
    del entries
    for p in (Path(__file__),HERE.parent/'water/review_compact_collision_v31.py',HERE.parent/'playtest/attach_navmesh.py'):pin(p)
    import py3d
    for p in Path(py3d.__file__).parent.rglob('*.py'):pin(p)
    old=data['source_grid'];new=np.load(candidate)['grid'][:len(old)]
    blob,detail=patch_model(source,old,new,origin);target=out/'source'/model;target.parent.mkdir(parents=True);target.write_bytes(blob)
    detail.update(model=model,source_sha256=pins[str(source)],candidate_sha256=meter.sha(target),origin=origin.tolist(),unchanged_other_models=200,bytes=len(blob))
    meter.dump(out/'patch-report.json',detail);meter.dump(out/'inputs.json',pins)
    effective={x['model'].replace('\\','/'):sources[str(base/'source'/x['model'].replace('\\','/'))] for x in author['instances']}
    effective[model]=meter.sha(target);meter.dump(out/'effective-models.json',effective)
    for p,d in pins.items():require(meter.sha(p)==d,'changed_after:'+p)
    return dict(status='MLOD_WRITTEN_PENDING_CONSUMER',model=model,sha256=detail['candidate_sha256'],changed_components=len(detail['changed_components']),measurement=meter.memory())

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('worktree',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
    sp=importlib.util.spec_from_file_location('meter',HERE/'water_constraint_diagnostic_ev112.py');meter=importlib.util.module_from_spec(sp);sp.loader.exec_module(meter);meter.STARTED=START;meter.MAX_SECONDS=120;stop=meter.bounded(a.output)
    try:result=run(a.root,a.worktree,a.output,meter);meter.dump(a.output/'report.json',result);print(json.dumps(result))
    except Exception as e:meter.dump(a.output/'failure.json',dict(type=type(e).__name__,error=str(e),measurement=meter.memory()));raise
    finally:stop.set()
