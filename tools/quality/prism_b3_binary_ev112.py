"""B3B saved-ODOL consumer and isolated package identity. No DayZ or deployment."""
import os,time
START=time.monotonic()
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import argparse,collections,json,struct,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Point,Polygon
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'water'),str(HERE.parent/'playtest')]
import compiled_dry_road_gate_ev112 as old
import water_constraint_diagnostic_ev112 as meter
from compare_non_geometry_lods_v31 import normalized,canonical_lod
from review_compact_collision_v31 import load,vertices,overlay
from mesh_quality_v31 import bidirectional_error
from attach_navmesh import read_pbo
from verify_prism_contact_b3_ev112 import original_controls

NAME='cs_kit_118_0000.p3d'
EXPECTED_COUNTS=(9120,12160,1520)
EXPECTED_SELECTED_VERTICES=72
class Inconclusive(ValueError):
    def __init__(self,reason,details=None):
        super().__init__(reason);self.details=details

def need(ok,why,details=None):
    if not bool(ok):
        e=ValueError(why);e.details=details;raise e

def bind(ok,why):
    if not bool(ok):raise Inconclusive(why)

def unchanged(a,b,allowed,why):
    A,B=normalized(a),normalized(b)
    changed={k for k in set(A)|set(B) if k not in A or k not in B or A[k]!=B[k]}
    if not changed<=set(allowed):raise Inconclusive(why+':'+','.join(sorted(changed-set(allowed))),{k:dict(control=A.get(k),candidate=B.get(k),control_present=k in A,candidate_present=k in B) for k in changed})
    return sorted(changed)

def lod_value(lod):
    bind(lod.lod_end_ok and lod.size_of_rest_data==lod.declared_end-lod.rest_data_offset_probe+4,'lod_boundary')
    v=canonical_lod(lod);v.pop('rest_data_offset_probe',None);return v

def header(od):
    return {k:v for k,v in vars(od).items() if k not in ('model_info','lods')}

def control_identity(a,b):
    if normalized(header(a))!=normalized(header(b)) or normalized(a.model_info)!=normalized(b.model_info) or [lod_value(x) for x in a.lods]!=[lod_value(x) for x in b.lods]:
        raise Inconclusive('fresh_control_not_historical')

def key(tri):
    v=tuple(map(tuple,tri));return min(v,v[1:]+v[:1],v[2:]+v[:2])

def face_counter(tri):return collections.Counter(key(t) for t in tri)

def bind_context(c,offline,proof):
    bind(proof['status']=='OFFLINE_CANDIDATE_ONLY' and proof['candidate_sha256']==c['candidate_sha256'] and proof['contract_sha256']=='447d4a767183bdf95064387a7e0ef45d14a5e040aba6941c5584428e0829ff48','offline_proof_binding')
    bind(c['source_control']==offline['source'] and c['pins'][c['source_control']]==offline['pins'][offline['source']],'control_source_binding')
    for field in ('targets','origin','selected_components','original_result'):
        bind(c[field]==offline[field],'offline_context_changed:'+field)
    bind(proof['selected_components']==c['selected_components'],'offline_component_binding')
    bind(c['pins'][c['original_result']]==offline['pins'][offline['original_result']],'original_result_binding')

def pose_check(matrix,origin,centre):
    m=np.asarray(matrix,float);o=np.asarray(origin,float);c=np.asarray(centre,float)
    bind(m.shape==(12,) and np.isfinite(m).all(),'invalid_pose')
    bind(np.array_equal(m[:9],[1,0,0,0,1,0,0,0,1]),'rotated_pose')
    bind(np.array_equal((o+c).astype('<f4').astype(float),m[9:]),'pose_changed')

def strict_contacts(tri,targets,required=True):
    n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);roof=tri[n[:,1]>1e-10]
    results=[]
    for t in targets:
        point=Point(np.asarray([t['x'],t['z']],'<f4').astype(float));hits=[]
        for face in roof:
            p=Polygon(face[:,[0,2]])
            if p.is_valid and p.area>0 and p.contains(point):hits.append(p.boundary.distance(point))
        if required:need(hits,'compiled_contact_on_boundary_or_outside:'+str(t['id']))
        margin=max(hits) if hits else 0.;ulp=float(np.abs(np.spacing(np.array([t['x'],t['z']],'<f4'))).max())
        results.append(dict(id=t['id'],strict_interior=bool(hits),margin_m=margin,world_ulp_m=ulp,margin_ulps=margin/ulp))
    return results

def source_faces(mlod,geo,origin,matrix,centre):
    src=np.asarray([p.coords for p in mlod.points],float);dec=old.xyz(geo.vertices)
    raw=np.frombuffer(geo.vertex_raw,'<f4').reshape(-1,3)
    bind(np.array_equal(raw,dec),'vertex_raw_decode')
    world=(dec+np.asarray(matrix)[9:]).astype('<f4').astype(float)
    source_world=(src+origin).astype('<f4').astype(float)
    source_groups={k.lower():s for k,s in mlod.selections.items()}
    groups={s.name.lower():s for s in geo.named_selections}
    bind(len(groups)==len(geo.named_selections)==len(source_groups) and set(groups)==set(source_groups),'component_names')
    points=[];faces=[];maximum=0.;details=[]
    for name,s in groups.items():
        ids=list(map(int,s.selected_vertices));fs=list(map(int,s.selected_faces))
        bind(len(ids)==6 and len(fs)==8 and len(set(ids))==6 and len(set(fs))==8,'component_counts')
        bind(all(0<=i<len(dec) for i in ids) and all(0<=i<len(geo.faces) for i in fs),'component_indices')
        part=source_groups[name];A=np.array([p.coords for p in part.points]);B=dec[ids]
        predicted=(A-centre).astype('<f4').astype(float)
        # Compiler recentring is checked separately from world-space equality.
        local_match=collections.Counter(map(tuple,predicted))==collections.Counter(map(tuple,B))
        if not local_match:
            need(False,'local_recentering_prediction:'+name,dict(component=name,predicted=predicted.tolist(),decoded=B.tolist(),error_m=bidirectional_error(predicted,B),ulp_m=np.abs(np.spacing(predicted.astype('<f4'))).astype(float).tolist()))
        error=max(bidirectional_error(A+origin,B+np.asarray(matrix)[9:]).values());maximum=max(maximum,error)
        need(error<.001,'compiled_vertex_error:'+name)
        want=np.asarray([[source_world[v.point_index] for v in f.vertices] for f in part.faces])
        got=[]
        for fi in fs:
            ix=list(geo.faces[fi].vertex_indices)
            need(len(ix)==3 and set(ix)<=set(ids),'face_outside_component')
            got.append(world[ix][::-1])
        wc,gc=face_counter(want),face_counter(got)
        need(wc==gc,'compiled_face_counter:'+name,dict(component=name,source_only=list((wc-gc).elements()),compiled_only=list((gc-wc).elements()),maximum_vertex_error_m=error,source_world=(A+origin).astype('<f4').astype(float).tolist(),world_ulp_m=np.abs(np.spacing(world[ids].astype('<f4'))).astype(float).tolist()))
        points+=ids;faces+=fs
        details.append(dict(name=name,maximum_vertex_error_m=error))
    bind(sorted(points)==list(range(len(dec))) and sorted(faces)==list(range(len(geo.faces))),'component_coverage')
    return dict(components=len(groups),maximum_vertex_error_m=maximum,details=details),world

def control_surface(mlod,geo,origin,matrix,centre,targets):
    try:r,world=source_faces(mlod,geo,np.asarray(origin),matrix,centre)
    except ValueError as e:raise Inconclusive('control_source_geometry:'+str(e),getattr(e,'details',None)) from e
    tri=np.asarray([world[f.vertex_indices] for f in geo.faces])
    return dict(source_geometry=r,contacts=strict_contacts(tri,targets,required=False))

def verify_pair(baseline,control,candidate,mlod,control_mlod,matrix,origin,targets,selected):
    for od in (baseline,control,candidate):
        bind(not od.lod_errors and len(od.lods)==4 and all(x.lod_end_ok for x in od.lods),'incomplete_odol')
    control_identity(baseline,control)
    unchanged(header(control),header(candidate),set(),'header_changed')
    mi=unchanged(control.model_info,candidate.model_info,{'center_of_mass','inv_inertia'},'model_info_changed')
    centre=old.xyz([candidate.model_info.bounding_center])[0]
    pose_check(matrix,origin,centre)
    for i in (0,2,3):
        if lod_value(control.lods[i])!=lod_value(candidate.lods[i]):raise Inconclusive('protected_lod_changed:'+str(i))
    A,B=control.lods[1],candidate.lods[1]
    bind((len(A.vertices),len(A.faces),len(A.named_selections))==(len(B.vertices),len(B.faces),len(B.named_selections))==EXPECTED_COUNTS,'compiled_cost_changed')
    control_geometry=control_surface(control_mlod[1],A,origin,matrix,centre,targets)
    changes=unchanged(lod_value(A),lod_value(B),{'vertex_raw','vertices','normal_raw','normals','size_of_rest_data'},'geometry_metadata_changed')
    allowed={k.lower() for k in selected};ids=[]
    for group in B.named_selections:
        if group.name.lower() in allowed:ids+=list(group.selected_vertices)
    bind(len(ids)==EXPECTED_SELECTED_VERTICES,'selected_vertex_domain')
    mask=np.zeros(len(B.vertices),bool);mask[ids]=True
    for field,dt,stride in (('vertex_raw','<f4',3),('normal_raw','<u4',1)):
        a=np.frombuffer(getattr(A,field),dt).reshape(-1,stride);b=np.frombuffer(getattr(B,field),dt).reshape(-1,stride)
        bind(a.shape==b.shape and len(a)==len(mask) and np.array_equal(a[~mask].view('u1'),b[~mask].view('u1')),'nonselected_compiled_data_changed:'+field)
    surface,world=source_faces(mlod[1],B,np.asarray(origin),matrix,centre)
    tri=np.asarray([world[f.vertex_indices] for f in B.faces])
    contact=strict_contacts(tri,targets)
    bed=vertices(mlod[0],[f for f in mlod[0].faces if 'water_streambed.rvmat' not in f.material])+origin
    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);roof=tri[normal[:,1]>1e-10]
    over=overlay(bed,roof);need(all(over['checks'].values()),'compiled_overlay')
    return dict(status='COMPILED_B3_CONDITIONAL',source_geometry=surface,control_geometry=control_geometry,contacts=contact,overlay=over,
        geometry_changed_fields=changes,model_info_changed_fields=mi,
        model_info_changes={k:dict(control=normalized(getattr(control.model_info,k)),candidate=normalized(getattr(candidate.model_info,k))) for k in mi},
        geometry_diagnostics={k:dict(control=normalized(getattr(A,k)),candidate=normalized(getattr(B,k))) for k in ('b_radius','b_center','face_area')},
        unchanged_non_geometry_lods=True,pose_unchanged=True,geometry_counts=list(EXPECTED_COUNTS),
        frames='MLOD+origin and decoded ODOL+WRP converted separately to world float32; exact oriented-face equality certified. Contact margins apply to both frames.',
        limits=['Saved ODOL under fixed WRP matrix; no engine intersection algorithm or native success certified.','Mass centre/inertia semantics remain uncertified. Other metadata/protected LODs exact.','Original47FAIL21uncertain, water, RAM, visual and global acceptance remain open.'])

def verify_saved(root,contract,pair,reader_root):
    c=json.loads(contract.read_bytes());bind(c['candidate_sha256']=='c769dd9a0631156075ec61586dc8f5a1471964899e21bdf34e8d13adad8233ad','wrong_candidate')
    for k in ('source_control','candidate_mlod','original_result','baseline_odol','baseline_pbo','poses','offline_proof','offline_contract'):
        bind(c[k] in c['pins'],'unpinned_core:'+k)
    for p,h in c['pins'].items():bind(meter.sha(p)==h,'input_changed:'+p)
    bind(meter.sha(c['candidate_mlod'])==c['candidate_sha256'],'candidate_payload_binding')
    proof=json.loads(Path(c['offline_proof']).read_bytes())
    bind(meter.sha(c['offline_contract'])=='447d4a767183bdf95064387a7e0ef45d14a5e040aba6941c5584428e0829ff48','offline_contract_binding')
    bind_context(c,json.loads(Path(c['offline_contract']).read_bytes()),proof)
    poses=np.load(c['poses']);ix=np.flatnonzero(poses['ids']==19394363)
    bind(len(ix)==1 and np.array_equal(poses['matrix'][ix[0]],c['matrix']),'saved_WRP_pose_binding')
    original=json.loads(Path(c['original_result']).read_bytes())
    try:original_controls(original,c['targets'],c['origin'])
    except ValueError as e:raise Inconclusive(str(e)) from e
    baseline_path=Path(c['baseline_odol']);control_path=pair/'control/saved-odol.p3d';candidate_path=pair/'candidate/saved-odol.p3d'
    before_props,expected=None,None
    _,before_props,expected=read_pbo(Path(c['baseline_pbo']));bind(expected[NAME]==baseline_path.read_bytes(),'historical_package_payload')
    configs=[]
    for side in ('control','candidate'):
        p=pair/side;_,props,entries=read_pbo(p/'packed/baltic_stream_pilot.pbo')
        bind(set(entries)=={NAME,'config.bin'} and props['prefix']=='baltic_stream_pilot','pair_package_entries')
        bind(entries[NAME]==(p/'saved-odol.p3d').read_bytes(),'saved_odol_not_pbo_payload')
        configs.append(entries['config.bin'])
    bind(configs[0]==configs[1],'pair_config_changed')
    ODOL=old.read_backend(reader_root)
    ods=[ODOL.from_file(str(p),strict=True) for p in (baseline_path,control_path,candidate_path)]
    _,mlods,_=load(c['candidate_mlod']);_,control_mlods,_=load(c['source_control'])
    result=verify_pair(*ods,mlods,control_mlods,c['matrix'],c['origin'],c['targets'],c['selected_components'])
    result.update(candidate_odol_sha256=meter.sha(candidate_path),contract_sha256=meter.sha(contract),
        source_sha256=c['candidate_sha256'],inputs=c['pins'],compiled_pair={str(p):meter.sha(p) for p in (control_path,candidate_path)},
        control_odol_sha256=meter.sha(control_path),candidate_path=str(candidate_path),baseline_pbo=c['baseline_pbo'],
        metadata_scope='CONDITIONAL_NOT_NATIVE',measurement=meter.memory())
    for p,h in c['pins'].items():bind(meter.sha(p)==h,'input_changed_after:'+p)
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('contract',type=Path);ap.add_argument('pair',type=Path);ap.add_argument('reader',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
    meter.STARTED=START;meter.MAX_SECONDS=180;stop=meter.bounded(a.output)
    try:
        r=verify_saved(a.root,a.contract,a.pair,a.reader);meter.dump(a.output/'report.json',r);print(json.dumps({k:r[k] for k in ('status','contacts','geometry_changed_fields','model_info_changed_fields','measurement')}))
    except Inconclusive as e:meter.dump(a.output/'report.json',dict(status='INCONCLUSIVE_BINARY',reason=str(e),details=getattr(e,'details',None),measurement=meter.memory()));raise SystemExit(2)
    except ValueError as e:meter.dump(a.output/'report.json',dict(status='REJECTED_BINARY',reason=str(e),details=getattr(e,'details',None),measurement=meter.memory()));raise SystemExit(1)
    except Exception as e:meter.dump(a.output/'failure.json',dict(status='INCONCLUSIVE_BINARY',type=type(e).__name__,reason=str(e),measurement=meter.memory()));raise
    finally:stop.set()
