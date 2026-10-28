"""Offline A: inspect frozen native failures against real compiled surfaces and masks."""
from pathlib import Path
import os,time,sys,json,hashlib,collections,math
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='1'
R=Path(__file__).resolve().parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/quality'))
import compiled_dry_road_gate_ev112 as g
import numpy as np
from shapely import Polygon,Point,STRtree
O=R/'dry-road-native-discriminators-a-20261028';O.mkdir(exist_ok=False)
g.meter.STARTED=time.monotonic();g.meter.MAX_SECONDS=120;stop=g.meter.bounded(O);pins={}
def pin(p,h=None):
    p=Path(p);v=g.sha(p);g.require(h is None or v==h,'input_hash:'+str(p));pins[str(p)]=v;return p
def read(p):return json.loads(pin(p).read_bytes())
def nz(p):
    with np.load(pin(p),allow_pickle=False) as z:return {k:z[k] for k in z.files}
def bary(t,q):
    return np.linalg.solve(np.vstack((t[:,[0,2]].T,np.ones(3))),np.r_[q,1.])
def project(tris,metadata,q):
    pt=Point(q);indices=[int(i) for i in STRtree([Polygon(t[:,[0,2]]) for t in tris]).query(pt,predicate='intersects')]
    return [dict(metadata[i],face=i,bary=bary(tris[i],q).tolist(),height=float(bary(tris[i],q)@tris[i,:,1]),edge_distance=float(Polygon(tris[i][:,[0,2]]).boundary.distance(pt)),normal_y=float(np.cross(tris[i,1]-tris[i,0],tris[i,2]-tris[i,0])[1])) for i in indices]
def summary(v):return dict(count=len(v),minimum=min(v) if v else None,maximum=max(v) if v else None,mean=sum(v)/len(v) if v else None)
try:
    # Analytic plane y=2x+3z+5; independent exact expected point height and translation.
    t=np.array([[0.,5.,0.],[1.,7.,0.],[0.,8.,1.]])
    g.require(np.allclose(bary(t,[.25,.5]),[.25,.25,.5],atol=1e-15,rtol=0),'analytic_bary')
    g.require(float(bary(t,[.25,.5])@t[:,1])==7.,'analytic_plane')
    pose=np.array([1,0,0,0,1,0,0,0,1,10,20,30.])
    g.require(np.array_equal(g.transform(t,pose),t+[10,20,30]),'analytic_pose')
    try:g.transform(t,np.ones(11))
    except ValueError:pass
    else:raise ValueError('bad_pose_accepted')
    try:pin(W/'plans/ev112-dry-road-native-discriminators-20261028.md','0'*64)
    except ValueError:pass
    else:raise ValueError('bad_hash_accepted')
    S=R/'dry-road-full-native-20261028';result=read(S/'probe/result.json');dep=read(S/'deployment.json')
    for p,h in result['inputs'].items():pin(p,h)
    for p,h in dep['inputs'].items():pin(p,h)
    pin(W/'plans/ev112-dry-road-native-discriminators-20261028.md')
    a=nz(R/'dry-bed-road-candidate-20261028/kit-118-inputs.npz')
    c=nz(R/'dry-bed-road-candidate-20261028/kit-118-candidate.npz')['grid']
    s=nz(R/'pilot-visible-surface-extraction-20261028/models/cs_kit_118_0000.npz')
    g.require(np.array_equal(a['grid'][:21],s['source_grid']),'grid_mapping')
    g.require(np.array_equal(a['grid'][:,:,[0,2]],c[:,:,[0,2]]),'XZ_changed')
    poses=nz(R/'deployed-surface-prototypes-20261028/instances.npz')
    _,_,old_entries=g.read_pbo(pin(R/'package-kit7-contact-only-20261026/Addons/baltic_stream_pilot.pbo',g.ANCHORS['package-kit7-contact-only-20261026/Addons/baltic_stream_pilot.pbo']))
    _,_,new_entries=g.read_pbo(pin(R/'dry-road-final-package-20261028/Addons/baltic_stream_pilot.pbo','ef229f3275d4c412d49f208395091e8b91faa5425e06ca2476a699a49bdf1b84'))
    reader_root=Path('C:/temp/moto_lanes/review_g3/tools');ODOL=g.read_backend(reader_root)
    for n,h in g.READER_HASHES.items():pin(reader_root/n,h)
    collections_tri={k:[] for k in ('old_bed','new_bed','new_roof')};metadata={k:[] for k in collections_tri};model_hashes={}
    for iid,name in ((19394363,'cs_kit_118_0000.p3d'),(19394364,'cs_kit_118_0012.p3d')):
        pi=np.flatnonzero(poses['ids']==iid);g.require(len(pi)==1,'pose_identity');matrix=poses['matrix'][pi[0]]
        model_hashes[name]={tag:hashlib.sha256(entries[name]).hexdigest() for tag,entries in (('before',old_entries),('after',new_entries))}
        for tag,entries in (('old',old_entries),('new',new_entries)):
            od=ODOL.from_bytes(entries[name],strict=True);g.require(not od.lod_errors and len(od.lods)==4 and all(l.lod_end_ok for l in od.lods),'model_decode')
            ar,labels=g.sections(od.lods[3]);vp=g.transform(g.xyz(od.lods[3].vertices),matrix)
            for fi,f in enumerate(od.lods[3].faces):
                if labels[int(ar[fi])]['texture'].endswith('/water_ext.paa'):continue
                g.require(len(f.vertex_indices)==3,'nontriangle_support')
                collections_tri[tag+'_bed'].append(vp[f.vertex_indices]);metadata[tag+'_bed'].append(dict(instance=iid,model=name,compiled_face=fi))
            if tag=='new':
                vp=g.transform(g.xyz(od.lods[1].vertices),matrix)
                for fi,f in enumerate(od.lods[1].faces):
                    tr=vp[f.vertex_indices];g.require(len(tr)==3,'nontriangle_geometry')
                    if np.cross(tr[1]-tr[0],tr[2]-tr[0])[1]>1e-10:
                        collections_tri['new_roof'].append(tr);metadata['new_roof'].append(dict(instance=iid,model=name,compiled_face=fi))
    collections_tri={k:np.array(v) for k,v in collections_tri.items()}
    # Native summary over all source rows; no reclassification.
    rows={row['id']:row for row in result['rows']}
    failures={p['id'] for p in result['failures']};uncertain={p['id'] for p in result['inconclusive']};required=failures|uncertain
    good=[row for row in rows.values() if all(v=='PASS' for v in row['states'].values())]
    paired={};chosen={525}
    for i in sorted(required):
        p=rows[i]['expected'];kind=p['sources'][0][0];same=[v for v in good if v['expected']['sources'][0][0]==kind];pool=same or good
        hit=min(pool,key=lambda v:((v['expected']['x']-p['x'])**2+(v['expected']['z']-p['z'])**2,v['id']))
        chosen.add(hit['id']);paired[str(i)]=dict(id=hit['id'],same_source_class=bool(same),distance=math.hypot(hit['expected']['x']-p['x'],hit['expected']['z']-p['z']))
    g.require(all(v=='PASS' for v in rows[525]['states'].values()),'declared_positive525')
    residuals={};normals={};all_metrics=[]
    for i,row in rows.items():
        p,m=row['expected'],row['measured'];label=('kit' if 'baltic_stream_pilot' in m['rv_shapes'] else 'terrain' if not m['rv_shapes'] else 'other')
        norm=math.sqrt(sum(v*v for v in m['rv_normal']));key=p['expect']+'/'+row['states']['water']
        residual=m['depth']-(m['surface']-(m['ground']+.01))
        residuals.setdefault(key,[]).append(residual);normals.setdefault(label,[]).append(norm)
        all_metrics.append(dict(id=i,water_verdict=row['states']['water'],depth_surface_residual=residual,rv_identity_group=label,rv_normal=m['rv_normal'],rv_normal_length=norm,expect_original=p['expect'],expect2_diagnostic='wet' if p['water_ext'] is not None and p['water_ext']>max(p['ground'],p['effective_bed'] if p['effective_bed'] is not None else -math.inf) else 'dry'))
    oldflat=a['grid'].reshape(-1,3);newflat=c.reshape(-1,3);tri=a['triangles']
    wet=set(map(int,a['wet_faces']));protected=set(map(int,a['protected_faces']))
    qs=np.unique(np.r_[np.arange(-18,19,dtype=float),-2.25,2.25]);g.require(len(qs)==39,'column_contract')
    output=[]
    for i in sorted(required|chosen):
        row=rows[i];p=row['expected'];q=np.array([p['x'],p['z']]);surfaces={k:project(v,metadata[k],q) for k,v in collections_tri.items()}
        old_height=max((f['height'] for f in surfaces['old_bed']),default=None);new_height=max((f['height'] for f in surfaces['new_bed']),default=None)
        source_mapping=[]
        for kind,idx in p['sources']:
            if kind=='vertex':
                g.require(0<=idx<s['source_grid'].size//3,'vertex_index')
                origin=s['source_grid'].reshape(-1,3)[idx]
                g.require(np.array_equal(origin[[0,2]].astype(np.float32).astype(float),q),'vertex_coordinate_mapping')
                incident=np.flatnonzero(np.any(tri==idx,axis=1))
                source_mapping.append(dict(kind=kind,index=idx,row=int(idx//39),column=int(idx%39),q=float(qs[idx%39]),free=bool(a['free'][idx]),domain=bool(a['domain'][idx]),height_changed=bool(oldflat[idx,1]!=newflat[idx,1]),wet_faces=sorted(wet&set(map(int,incident))),protected_faces=sorted(protected&set(map(int,incident))),incident_faces=incident.tolist()))
            elif kind=='face_centroid':
                g.require(0<=idx<len(s['source_triangles']),'source_face_index');verts=s['source_triangles'][idx];center=s['source_grid'].reshape(-1,3)[verts].mean(0)
                g.require(np.array_equal(center[[0,2]].astype(np.float32).astype(float),q),'centroid_coordinate_mapping')
                matches=np.flatnonzero(np.all(np.sort(tri,axis=1)==np.sort(verts),axis=1));g.require(len(matches)==1,'global_face_mapping');fi=int(matches[0])
                source_mapping.append(dict(kind=kind,index=idx,global_face=fi,vertices=verts.tolist(),free=a['free'][verts].tolist(),domain=a['domain'][verts].tolist(),height_changed=(oldflat[verts,1]!=newflat[verts,1]).tolist(),wet_frozen=fi in wet,protected=fi in protected))
            else:source_mapping.append(dict(kind=kind,index=idx,status='NO_VERTEX_OR_CENTROID_MAPPING; projected surfaces retained'))
        output.append(dict(id=i,original_states=row['states'],is_original_failure=i in failures,is_predeclared_uncertain=i in uncertain,is_positive=i in chosen,expected=p,source_mapping=source_mapping,before_bed=old_height,after_bed=new_height,bed_delta=None if old_height is None or new_height is None else new_height-old_height,compiled_surfaces=surfaces,rv_normal=row['measured']['rv_normal']))
    g.require({r['id'] for r in output}==required|chosen,'coverage')
    waterfailed=[row for row in output if row['original_states']['water']=='FAIL']
    stats=dict(status='OFFLINE_DISCRIMINATORS_A_COMPLETE_PRODUCT_REFERENCE_INCONCLUSIVE',required_failures=len(failures),required_uncertain=len(uncertain),required_union=len(required),positive_ids=sorted(chosen),selected_count=len(output),water_failed_count=len(waterfailed),water_failed_unchanged_bed_count=sum(row['bed_delta']==0 for row in waterfailed),water_failed_bed_delta_range=summary([row['bed_delta'] for row in waterfailed if row['bed_delta'] is not None]),depth_residuals={k:summary(v) for k,v in residuals.items()},rv_normal_lengths={k:summary(v) for k,v in normals.items()},analytic_controls=4,product_reference='INCONCLUSIVE_PRODUCT_REFERENCE',tree_geometry='NOT_EVALUATED',model_hashes=model_hashes,paired_positives=paired,inputs=pins,measurement=g.meter.memory(),limits=['Original native FAIL unchanged; no consumer/map edit or new DayZ run.','Conservation does not establish correctness of original kit or water product labels.','Barycentric support/winding are offline evidence, not proof of why RV missed vertices.','Ray start free-space and native semantics remain for separately reviewed unit B.'])
    pin(Path(__file__));g.require(all(g.sha(p)==h for p,h in pins.items()),'input_drift_end')
    stats['inputs']=pins
    g.meter.dump(O/'selected-points.json',output);g.meter.dump(O/'all-row-metrics.json',all_metrics);g.meter.dump(O/'report.json',stats)
    print(json.dumps({k:v for k,v in stats.items() if k not in ('inputs','paired_positives','model_hashes')},indent=2))
except Exception as e:g.meter.dump(O/'failure.json',dict(type=type(e).__name__,error=str(e)));raise
finally:stop.set()

