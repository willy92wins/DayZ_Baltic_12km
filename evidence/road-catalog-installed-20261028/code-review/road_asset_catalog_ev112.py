"""Installed road-asset measurements only. No poses or drivable-road acceptance."""
import os,time
START=time.monotonic()
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
from pathlib import Path
import argparse,hashlib,importlib,io,json,math,struct,sys,traceback
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'playtest')]
import water_constraint_diagnostic_ev112 as meter
from attach_navmesh import read_pbo
from deployed_surface_inventory_ev112 import pbo_table,sections

PBO=Path('E:/SteamLibrary/steamapps/common/DayZ Exp/Addons/structures_roads.pbo')
PBO_SHA='34c1cabe608823dc09ec25dd62c3738a84075a7187484fc99dbdf4e1c2ed2f5f'
READER=Path('C:/temp/moto_lanes/review_g3/tools')
READER_PINS={'odol_reader.py':'fa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57','bis_reader.py':'c9e5194aaf03e3c1a54578fa52950a1e0236c52ecb6b2597756b6a9ee618b70b','math_types.py':'b6ac444ca190a5cb8a7e5c0f423fafeceb31ddc8a805f2374b466ae5da6fdd10'}
HELPER_PINS={'deployed_surface_inventory_ev112.py':'b7a17598c68294622b4bf2ba8bb36afe74d91b24876b8451e10ab0425651bcb6','../playtest/attach_navmesh.py':'717b81469e0a799690d1586cd7a4492f079c3b2db626eec7e2815cd15896e062'}
digest=lambda data:hashlib.sha256(data).hexdigest()
f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
ROLES={f32(v):k for k,v in {'Geometry':1e13,'Memory':1e15,'LandContact':2e15,'Roadway':3e15,'ViewGeometry':6e15,'FireGeometry':7e15}.items()}

def require(condition,reason):
    if not condition:raise ValueError(reason)

def xyz(p):
    v=[float(p.x),float(p.y),float(p.z)];require(all(map(math.isfinite,v)),'nonfinite_point');return v

def bbox(points):
    require(all(len(v)==3 and all(map(math.isfinite,v)) for v in points),'invalid_points')
    return dict(min=[min(v[k] for v in points) for k in range(3)],max=[max(v[k] for v in points) for k in range(3)]) if points else None

def category(name):
    n=name.lower().replace('\\','/')
    if not n.endswith('.p3d'):return 'non_model'
    if n.startswith('parts/'):return 'road_part_by_path'
    if 'bridge' in n:return 'bridge_candidate_by_name'
    return 'other_model'

def check_table(data,props,entries):
    """Second independent table parse must cover all original entries and bytes."""
    independent,table=pbo_table(io.BytesIO(data),len(data))
    require(independent==props,'properties_disagree')
    require(props.get('prefix','').replace('\\','/').lower()=='dz/structures/roads','unexpected_prefix')
    require([e['name'] for e in table]==[k.lower() for k in entries],'entry_order_or_coverage')
    rows=[]
    for e,(name,payload) in zip(table,entries.items()):
        require(e['mime']==0 and e['size']==len(payload),'entry_method_or_size')
        require(data[e['offset']:e['offset']+e['size']]==payload,'payload_disagrees')
        rows.append(dict(name=name,normalized_name=e['name'],category=category(name),size=e['size'],mime=e['mime'],sha256=digest(payload)))
    end=table[-1]['offset']+table[-1]['size'] if table else len(data)
    trailer=data[end:];require(len(trailer)==0 or (len(trailer)==21 and trailer[0]==0),'unexpected_trailer')
    return rows,dict(payload_end=end,file_bytes=len(data),trailer_hex=trailer.hex(),trailer_semantics='UNINTERPRETED; whole-image SHA256 externally pinned')

def model_metadata(od,scale=1):
    require(scale==1,'nonunit_input_scale')
    require(not od.lod_errors and len(od.lods)==od.n_lods==len(od.resolutions) and od.n_lods>0,'incomplete_model')
    require(all(l is not None and l.lod_end_ok for l in od.lods),'incomplete_lod')
    mi=od.model_info;out=[]
    for i,l in enumerate(od.lods):
        resolution=float(l.resolution);require(math.isfinite(resolution) and resolution==od.resolutions[i],'resolution')
        vertices=[xyz(v) for v in l.vertices]
        require(len(l.vertex_raw)==12*len(vertices),'raw_vertex_length')
        raw=[list(v) for v in struct.iter_unpack('<fff',l.vertex_raw)]
        require(raw==vertices,'raw_decoded_vertex_disagreement')
        raw_box=bbox(raw);decoded_box=bbox(vertices);require(raw_box==decoded_box,'bbox_disagreement')
        for f in l.faces:require(len(f.vertex_indices) in (3,4) and all(0<=v<len(vertices) for v in f.vertex_indices),'face_indices')
        assignment,ss=sections(l)
        role=ROLES.get(resolution,'Visual' if 0<=resolution<1000 else 'Unclassified')
        selections=[]
        for s in l.named_selections:
            require(all(0<=v<len(vertices) for v in s.selected_vertices) and all(0<=f<len(l.faces) for f in s.selected_faces),'selection_indices')
            selections.append(dict(name=s.name,vertices=len(s.selected_vertices),faces=len(s.selected_faces),sectional=bool(s.is_sectional),sections=list(s.sections)))
        out.append(dict(index=i,resolution=resolution,role=role,vertices=len(vertices),faces=len(l.faces),bbox=raw_box,
                        declared_bbox=dict(min=xyz(l.b_min),max=xyz(l.b_max)),declared_center=xyz(l.b_center),vertex_raw_sha256=digest(l.vertex_raw),
                        selections=selections,properties=list(l.named_properties),sections=ss,textures=list(l.textures),
                        materials=[m.material_name for m in l.materials],proxy_count=len(l.proxies),frame_count=len(l.frames)))
    return dict(version=od.version,lods=out,model_bbox=dict(min=xyz(mi.bbox_min),max=xyz(mi.bbox_max)),bounding_center=xyz(mi.bounding_center),
                animated=bool(mi.animated),scale=scale,space='model_local',usable_width='UNDETERMINED',roadway_present=any(l['role']=='Roadway' for l in out),
                limits=['No model arrays exported.','Role labels describe stored resolutions, not engine behavior.','No driving or placement acceptance.'])

def verify_coverage(entries,models):
    expected=[e for e in entries if e['category']!='non_model']
    require([(e['name'],e['sha256']) for e in expected]==[(m['name'],m['sha256']) for m in models],'model_coverage')
    require(all(m['status'] in ('READ_STRICT','INCONCLUSIVE_PARSE') for m in models),'model_status')
    require(all(m.get('measurement',{}).get('usable_width')=='UNDETERMINED' for m in models if m['status']=='READ_STRICT'),'false_width')
    return 'CATALOG_COMPLETE_NOT_PLACEMENT_ACCEPTANCE' if all(m['status']=='READ_STRICT' for m in models) and models else 'INCONCLUSIVE_CATALOG'

def collect(entries,payloads,decode,emit):
    models=[]
    for e in entries:
        if e['category']=='non_model':continue
        row=dict(name=e['name'],sha256=e['sha256'],category=e['category'])
        try:
            b=payloads[e['name']];require(digest(b)==e['sha256'] and b.startswith(b'ODOL'),'model_bytes')
            row.update(status='READ_STRICT',measurement=model_metadata(decode(b,strict=True)))
        except Exception as exc:row.update(status='INCONCLUSIVE_PARSE',error=type(exc).__name__+':'+str(exc))
        models.append(row);emit(row)
    return models

def check_pins(pins):
    for p,h in pins.items():require(meter.sha(p)==h,'input_changed:'+str(p))

def execute(output):
    pins={str(PBO):PBO_SHA,**{str(READER/n):h for n,h in READER_PINS.items()},**{str((HERE/n).resolve()):h for n,h in HELPER_PINS.items()}}
    check_pins(pins);meter.dump(output/'inputs.json',pins)
    # Parse original table even when the payload reader rejects compression.
    with PBO.open('rb') as f:props,table=pbo_table(f,PBO.stat().st_size)
    meter.dump(output/'source-table.json',dict(properties=props,entries=table))
    data,props,entries=read_pbo(PBO);require(digest(data)==PBO_SHA,'image_changed_during_read')
    rows,trailer=check_table(data,props,entries);meter.dump(output/'entries.json',rows);del data
    sys.path.insert(0,str(READER));backend=importlib.import_module('odol_reader')
    require(Path(backend.__file__).resolve()==(READER/'odol_reader.py').resolve(),'reader_module_shadowed')
    with (output/'models.jsonl').open('x',encoding='utf-8') as stream:
        def emit(row):stream.write(json.dumps(row,allow_nan=False)+'\n');stream.flush();os.fsync(stream.fileno())
        models=collect(rows,entries,backend.ODOL.from_bytes,emit)
    status=verify_coverage(rows,models);del entries
    check_pins(pins);measurement=meter.memory()
    require(measurement['seconds']<=120 and max(measurement['peak_resident_bytes'],measurement['peak_commit_bytes'])<=2*1024**3,'resource_budget')
    return dict(status=status,pbo_sha256=PBO_SHA,entry_count=len(rows),model_count=len(models),strict_models=sum(m['status']=='READ_STRICT' for m in models),
                failed_models=[m['name'] for m in models if m['status']!='READ_STRICT'],classes={c:sum(r['category']==c for r in rows) for c in sorted({r['category'] for r in rows})},
                bridge_scope='Name/path candidates in this PBO only; not global bridge census.',trailer=trailer,measurement=measurement,
                public_arrays=False,usable_width='UNDETERMINED',source_hashes_unchanged=True,no_build_or_dayz=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
    meter.STARTED=START;meter.MAX_SECONDS=120;meter.MAX_BYTES=2*1024**3;stop=meter.bounded(a.output)
    try:
        r=execute(a.output);meter.dump(a.output/'report.json',r);print(json.dumps(r));return 0 if r['status']=='CATALOG_COMPLETE_NOT_PLACEMENT_ACCEPTANCE' else 2
    except Exception as exc:
        meter.dump(a.output/'report.json',dict(status='INCONCLUSIVE_CATALOG',error=type(exc).__name__+':'+str(exc),traceback=traceback.format_exc(),measurement=meter.memory()));return 2
    finally:stop.set()

if __name__=='__main__':raise SystemExit(main())
