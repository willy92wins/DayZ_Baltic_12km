"""Actual Visual201 faces and exact source topology. Diagnostic, not map acceptance."""
import os,time
STARTED=time.monotonic()
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'): os.environ[k]='1'
import argparse,collections,hashlib,io,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
BED_MAT='dz/water/streambed/data/streambed_leaf_long_straight.rvmat'
BED_TEX='dz/water/streambed/data/cp_stream_gravel_co.paa'
WATER_MAT='dz/water/streams/data/water_streambed.rvmat'
WATER_TEX='dz/water/streams/data/streams_flowmap_ca.paa'
BED_ROAD='dz/surfaces/data/roadway/gravel_small_ext.paa'
WATER_ROAD='dz/surfaces/data/roadway/water_ext.paa'
HELPER_SHA='b7a17598c68294622b4bf2ba8bb36afe74d91b24876b8451e10ab0425651bcb6'
SITES={'kit-7':139,'kit-118':26,'65.0-0':9,'131.0-0':27}
ARRAYS={
 'kit-7':('river-kit7-contact-only-20261026/kit-7-surfaces.npz','9d8caf0fb75d2bd34f71b877ecd3f71079898fbc01c28e67ddab0bf8dca50063'),
 'kit-118':('collision-overlap-u2/kit-118-surfaces.npz','55a99316f6f0a5885cf1eaa22a238b05348567cfbd23caacbdf03e4510ecb9f7'),
 '65.0-0':('collision-overlap-u2/65.0-0-surfaces.npz','c1de91650f55bd85fc7c5947ce37e3ace31dd9f0f47983a0c8a7453e67bcf260'),
 '131.0-0':('collision-overlap-u2/131.0-0-surfaces.npz','7ea32aaf5a285763ff481a4f20146f98e689b8b38941ac6d0b3c6d57ce288f99')}

def require(ok,message):
    if not bool(ok): raise ValueError(message)

def norm(text): return text.replace('\\','/').lower().strip('/')

def key(face,oriented=False):
    """Exact identity: arity, multiplicity and optionally winding; never rounding."""
    vertices=tuple(tuple(float(c) for c in row) for row in face)
    require(len(vertices) in (3,4) and np.isfinite(face).all(),'invalid_face')
    if not oriented: return tuple(sorted(vertices))
    return min(vertices[i:]+vertices[:i] for i in range(len(vertices)))

def equivalence(left,right):
    a,b=collections.Counter(map(key,left)),collections.Counter(map(key,right))
    ac=collections.Counter(key(f,True) for f in left)
    bc=collections.Counter(key(f,True) for f in right)
    return dict(exact_faces=a==b,exact_oriented_faces=ac==bc,
                left_only_faces=sum((a-b).values()),right_only_faces=sum((b-a).values()),
                left_duplicate_faces=sum(n-1 for n in a.values()),
                right_duplicate_faces=sum(n-1 for n in b.values()))

def coverage_guard(author,catalog,ids,mi):
    names=[norm(x['model']) for x in author]
    require(len(names)==len(set(names))==201,'author_coverage')
    selected=[x for x in catalog if x['group']=='custom_pilot']
    require(len(selected)==201 and set(names)=={x['name'] for x in selected},'pilot_model_coverage')
    require(collections.Counter(x['site'] for x in author)==SITES,'site_coverage')
    require(len(ids)==len(set(map(int,ids))),'duplicate_instance_id')
    counts=collections.Counter(map(int,mi))
    require(all(counts[x['index']]==1 for x in selected),'pilot_instance_coverage')
    return {x['name']:x for x in selected}

def visual_role(material,texture):
    if norm(material)==BED_MAT and norm(texture)==BED_TEX: return 'bed'
    if norm(material)==WATER_MAT and norm(texture)==WATER_TEX: return 'water'
    return 'unknown'  # Including empty or partial matches; never silently excluded.

def strip_mapping(points,triangles,station,array_bed,array_water,source_water,span):
    """Prove complete source strip and NPZ body. CAP heights are actual MLOD rows."""
    points,triangles=np.asarray(points,float),np.asarray(triangles,int)
    require(points.ndim==2 and points.shape[1]==3 and np.isfinite(points).all(),'source_points')
    require(triangles.ndim==2 and triangles.shape[1]==3,'nontriangle_source')
    require(np.isfinite(station).all() and (np.diff(station)>0).all(),'station_order')
    endpoints=[np.flatnonzero(station==s) for s in span]
    require(all(len(x)==1 for x in endpoints),'station_anchor')
    start,stop=(int(x[0]) for x in endpoints); require(start<stop,'station_span')
    m=array_bed.shape[1]; before=8 if start==0 else 0; after=8 if stop==len(station)-1 else 0
    n=stop-start+1+before+after
    require(points.shape==(n*m,3),'source_strip_size')
    require(triangles.min()>=0 and triangles.max()<len(points),'source_strip_indices')
    expected=collections.Counter()
    for r in range(n-1):
        for c in range(m-1):
            a=r*m+c; b=a+m; d=b+1; e=a+1
            expected.update((tuple(sorted((a,b,d))),tuple(sorted((a,d,e)))))
    require(collections.Counter(tuple(sorted(t)) for t in triangles)==expected,'source_strip_topology')
    grid=points.reshape(n,m,3); body=grid[before:n-after if after else n]
    require(np.array_equal(body,array_bed[start:stop+1]),'npz_body_not_source')
    require(np.array_equal(source_water,array_water[start:stop+1]),'npz_water_not_source')
    row=triangles//m; col=triangles%m
    category=np.where(row.max(axis=1)<=before,'CAP_START',
             np.where(row.min(axis=1)>=n-after-1,'CAP_END','BODY'))
    if not before: category[category=='CAP_START']='BODY'
    if not after: category[category=='CAP_END']='BODY'
    cap_info=[]
    for side,count,boundary,direction in (('start',before,before,-1),('end',after,n-after-1,1)):
        if not count: continue
        rows=np.arange(boundary+direction,boundary+direction*(count+1),direction)
        shifts=grid[rows][:,:,(0,2)]-grid[boundary][:,(0,2)]
        mean=shifts.mean(axis=1); cross=grid[boundary,-1,(0,2)]-grid[boundary,0,(0,2)]
        tangent=np.array([cross[1],-cross[0]])/np.linalg.norm(cross)
        along=mean@(direction*tangent)
        cap_info.append(dict(side=side,rows=rows.tolist(),boundary_row=boundary,along_m=along.tolist(),
          retrograde=bool(np.any(np.diff(np.r_[0,along])<=0)),
          max_cross_row_shift_residual_m=float(np.max(abs(shifts-mean[:,None])))))
    return grid,row.min(axis=1),row.max(axis=1),col.min(axis=1),col.max(axis=1),category,cap_info,start,before,after

def odol_faces(od,helper,matrix):
    require(not od.lod_errors and len(od.lods)==len(od.resolutions),'incomplete_odol')
    vi,ri=helper.select_lods([l.resolution for l in od.lods]); require(ri is not None,'missing_pilot_roadway')
    groups={'bed':[],'water':[],'unknown':[],'road_bed':[],'road_water':[],'road_unknown':[]}
    sections=[]; source_ids=collections.defaultdict(list)
    for li in (vi,ri):
        lod=od.lods[li]; require(lod.lod_end_ok,'lod_cursor')
        require(not lod.proxies,'pilot_proxy_requires_explicit_expansion')
        assignment,ss=helper.sections(lod)
        p=np.array([[v.x,v.y,v.z] for v in lod.vertices],float)
        sections.append(dict(lod=li,resolution=lod.resolution,sections=ss))
        for fi,f in enumerate(lod.faces):
            ind=np.asarray(f.vertex_indices,int)
            require(len(ind) in (3,4) and (ind>=0).all() and (ind<len(p)).all(),'face_index')
            s=ss[int(assignment[fi])]
            if li==vi: role=visual_role(s['material'],s['texture'])
            elif s['texture']==BED_ROAD: role='road_bed'
            elif s['texture']==WATER_ROAD: role='road_water'
            else: role='road_unknown'
            groups[role].append(helper.transform(p[ind],matrix))
            source_ids[role].append((fi,int(assignment[fi])))
    require(groups['bed'] and groups['water'] and groups['road_bed'],'empty_pilot_surface')
    return groups,source_ids,sections

def source_faces(model,origin):
    visuals=[x for x in model.lods if 0<=x.resolution<1000]; require(visuals,'source_visual_missing')
    lod=min(visuals,key=lambda x:x.resolution)
    groups=collections.defaultdict(list); indices=[]
    for f in lod.faces:
        role=visual_role(f.material,f.texture)
        groups[role].append(np.asarray([v.point.coords for v in f.vertices])+origin)
        if role=='bed': indices.append([v.point_index for v in f.vertices])
    ids=sorted({v for tri in indices for v in tri})
    require(ids==list(range(len(ids))),'bed_point_layout')
    points=np.asarray([lod.points[i].coords for i in ids])+origin
    water_ids=sorted({v.point_index for f in lod.faces if visual_role(f.material,f.texture)=='water' for v in f.vertices})
    wp=np.asarray([lod.points[i].coords for i in water_ids])+origin; require(len(wp)%2==0,'water_rows')
    return groups,points,np.asarray(indices),wp.reshape(-1,2,3)

def read_inputs(root,worktree,meter):
    hp=HERE/'deployed_surface_inventory_ev112.py'; require(meter.sha(hp)==HELPER_SHA,'pinned_A_helper_changed')
    helper=meter.module('sealed_A',hp)
    manifest=worktree/'evidence/deployed-surface-prototypes-20261028/artifact-hashes.json'
    artifact=helper.manifest_keys(json.loads(manifest.read_bytes()))
    pins={str(manifest):meter.sha(manifest),str(hp):HELPER_SHA}
    def sealed(rel):
        p=root/rel; data=helper.sealed_bytes(p,root,artifact)
        pins[str(p)]=hashlib.sha256(data).hexdigest(); return data
    old=json.loads(sealed('deployed-surface-prototypes-20261028/inputs.json'))
    catalog=json.loads(sealed('deployed-surface-prototypes-20261028/model-catalog.json'))
    prior=old['source_pins']; raw='geometry-payload-discovery-resolved-20261028/'
    def pinned(path):
        require(str(path) in prior and meter.sha(path)==prior[str(path)],'source_pin_missing_or_changed:'+str(path))
        pins[str(path)]=prior[str(path)]; return path.read_bytes()
    bindings=json.loads(pinned(root/(raw+'payload-bindings.json')))
    discovery=json.loads(pinned(root/(raw+'inputs.json')))
    for path,digest in discovery['reader'].items():
        require(meter.sha(path)==digest,'reader_changed:'+path); pins[path]=digest
    with np.load(io.BytesIO(sealed('deployed-surface-prototypes-20261028/instances.npz'))) as f:
        poses={k:f[k] for k in ('ids','model_index','matrix')}
    source_pins=json.loads(sealed('deployed-surface-consumer-lineage-20261028/current-source-pins.json'))
    for path,digest in source_pins.items():
        require(meter.sha(path)==digest,'current_source_changed:'+path); pins[path]=digest
    author=json.loads((root/'pilot-kit7-fc-20261026/author-report.json').read_bytes())
    selected=coverage_guard(author['instances'],catalog,poses['ids'],poses['model_index'])
    for path,digest in prior.items():
        require(meter.sha(path)==digest,'A_input_changed:'+path); pins[path]=digest
    arrays={}
    for site,(rel,digest) in ARRAYS.items():
        path=root/rel; require(meter.sha(path)==digest,'npz_changed'); pins[str(path)]=digest
        with np.load(path) as f: arrays[site]={k:f[k] for k in ('bed','water','station')}
    reader=Path('C:/temp/moto_lanes/review_g3/tools/odol_reader.py')
    pyroot=Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d')
    for p in (pyroot/'py3d').rglob('*.py'): pins[str(p)]=meter.sha(p)
    return helper,pins,bindings,discovery,author,selected,poses,arrays,reader,pyroot

def extract(root,worktree,output,meter,preflight):
    helper,pins,bindings,discovery,author,selected,poses,arrays,reader,pyroot=read_inputs(root,worktree,meter)
    cost=dict(models=201,sites=SITES,expected_visual_faces=sum(x['visual_triangles'] for x in author['instances']),
              source_array_bytes=sum(v.nbytes for d in arrays.values() for v in d.values()),all_other_models_decoded=0)
    meter.dump(output/'cost.json',cost)
    meter.dump(output/'inputs.json',dict(pins=pins,script_sha256=meter.sha(__file__)))
    if preflight: return dict(status='INPUT_COVERAGE_PREFLIGHT_ONLY',**cost)
    sys.path.insert(0,str(reader.parent)); from odol_reader import ODOL
    sys.path.insert(0,str(pyroot)); import py3d
    packages={x['path'].replace('\\','/').split('/')[-1]:x for x in discovery['packages']}
    binding={b['name']:b for b in bindings}; package_cache={}; reports=[]
    (output/'models').mkdir()
    for inst in author['instances']:
        name=norm(inst['model']); mi=selected[name]['index']
        pos=int(np.flatnonzero(poses['model_index']==mi)[0]); matrix=poses['matrix'][pos]
        b=binding[name]; package=packages[b['package']]; path=Path(package['path'])
        if str(path) not in package_cache:
            with path.open('rb') as f: props,entries=helper.pbo_table(f,path.stat().st_size)
            require(norm(props['prefix'])==package['prefix'],'package_prefix')
            package_cache[str(path)]={x['name']:x for x in entries}
        require(package['prefix']+'/'+b['entry']==name,'binding_path')
        with path.open('rb') as f: data=helper.read_payload(f,package_cache[str(path)][b['entry']],b['sha256'])
        groups,face_ids,sections=odol_faces(ODOL.from_bytes(data,strict=True),helper,matrix)
        mlod=root/'pilot-kit7-fc-20261026/source'/name
        require(meter.sha(mlod)==inst['sha256'],'mlod_changed')
        with mlod.open('rb') as f: model=py3d.P3D(f)
        source,points,tris,wp=source_faces(model,np.asarray(inst['origin']))
        checks={k:equivalence(groups[k],source[k]) for k in ('bed','water','unknown')}
        checks['visual_vs_roadway']=equivalence(groups['bed'],groups['road_bed'])
        a=arrays[inst['site']]
        try:
            grid,rmin,rmax,cmin,cmax,category,caps,start,before,after=strip_mapping(points,tris,a['station'],a['bed'],a['water'],wp,inst['station'])
        except ValueError as e:
            raise ValueError(str(e)+':'+name) from e
        lookup=collections.defaultdict(list)
        for i,f in enumerate(source['bed']): lookup[key(f)].append(i)
        mapped=np.full(len(groups['bed']),-1,np.int32)
        for i,f in enumerate(groups['bed']):
            match=lookup.get(key(f),[])
            if len(match)==1: mapped[i]=match[0]
        payload={}; ambiguity={}
        for kind in groups:
            faces=groups[kind]; v=np.zeros((len(faces),4,3)); count=np.array([len(f) for f in faces],np.uint8)
            flags=np.empty(len(faces),np.uint8)
            for i,face in enumerate(faces): v[i,:len(face)]=face; flags[i]=helper.face_flag(face)
            payload[kind]=v; payload[kind+'_n']=count; payload[kind+'_flags']=flags
            payload[kind+'_source_ids']=np.asarray(face_ids[kind],np.int32).reshape(-1,2)
            ambiguity[kind]=int((flags!=0).sum())
        payload.update(source_grid=grid,source_triangles=tris,body_row_min=rmin,body_row_max=rmax,
                       body_col_min=cmin,body_col_max=cmax,source_category=category,bed_source_face=mapped,
                       npz_start=np.int32(start),cap_before=np.int32(before),cap_after=np.int32(after))
        basename=Path(name).stem+'.npz'; np.savez_compressed(output/'models'/basename,**payload)
        reports.append(dict(model=name,model_index=mi,instance_id=int(poses['ids'][pos]),site=inst['site'],
          station=inst['station'],file='models/'+basename,sha256=meter.sha(output/'models'/basename),
          checks=checks,sections=sections,faces={k:len(v) for k,v in groups.items()},ambiguous_faces=ambiguity,
          unmapped_bed_faces=int((mapped<0).sum()),cap_rows=caps,source_regions=dict(collections.Counter(category.tolist()))))
    for p,digest in pins.items(): require(meter.sha(p)==digest,'input_changed_during_extraction:'+p)
    require(len(reports)==201,'incomplete_production'); meter.dump(output/'models.json',reports)
    return dict(status='EXTRACTED_DIAGNOSTIC_ONLY',models=len(reports),sites=SITES,
      exact_geometry_models=sum(all(c['exact_faces'] for c in row['checks'].values()) for row in reports),
      unmapped_bed_faces=sum(x['unmapped_bed_faces'] for x in reports),
      unknown_visual_faces=sum(x['faces']['unknown'] for x in reports),
      unknown_roadway_faces=sum(x['faces']['road_unknown'] for x in reports),
      faces={k:sum(x['faces'][k] for x in reports) for k in groups},
      limits=['No H/W exposure or corridor census yet. No render, transparency, driving or map acceptance.',
              'Exact face equivalence preserves multiplicity; normals, UVs and materials/rendering are not compared.',
              'Body NPZ equals source; CAP positions/heights come from actual MLOD, not regenerated arrays.',
              'CAP includes the triangle strip touching its boundary body row; npz_start/cap_before/cap_after make indexing explicit.'])

if __name__=='__main__':
    import importlib.util
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('worktree',type=Path)
    ap.add_argument('output',type=Path); ap.add_argument('--preflight',action='store_true'); a=ap.parse_args()
    a.output.mkdir(exist_ok=False)
    spec=importlib.util.spec_from_file_location('meter',HERE/'water_constraint_diagnostic_ev112.py')
    meter=importlib.util.module_from_spec(spec); spec.loader.exec_module(meter)
    meter.STARTED=STARTED; meter.MAX_SECONDS=120 if a.preflight else 600; stop=meter.bounded(a.output)
    try:
        result=extract(a.root,a.worktree,a.output,meter,a.preflight); m=meter.memory()
        require(m['seconds']<=meter.MAX_SECONDS and max(m['peak_commit_bytes'],m['peak_resident_bytes'])<=meter.MAX_BYTES,'resource_budget')
        result['measurement']=m; meter.dump(a.output/'report.json',result); print(json.dumps(result))
    except Exception as e:
        meter.dump(a.output/'failure.json',dict(reason=str(e),type=type(e).__name__,measurement=meter.memory())); raise
    finally: stop.set()
