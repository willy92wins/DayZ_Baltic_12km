"""B3D independent saved-MLOD consumer. Never imports author or B3C solver."""
import os,time
START=time.monotonic()
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
from pathlib import Path
from fractions import Fraction
import argparse,json,struct,sys
import numpy as np
from shapely.geometry import Point,Polygon
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'water')]
from review_compact_collision_v31 import load,vertices,overlay
from verify_prism_contact_b3_ev112 import components,original_controls
import water_constraint_diagnostic_ev112 as meter

class Inconclusive(ValueError):pass
def failure_status(error):
    # Only explicit geometric ValueError checks are rejections. Unexpected
    # interpreter/reader failures never become evidence against the model.
    return 'REJECTED_MLOD' if type(error) is ValueError else 'INCONCLUSIVE'
def bind(ok,reason):
    if not bool(ok):raise Inconclusive(reason)
def need(ok,reason):
    if not bool(ok):raise ValueError(reason)
def bit_equal(a,b):return np.array_equal(np.asarray(a,dtype='<f4').view('<u4'),np.asarray(b,dtype='<f4').view('<u4'))

def bind_contract(c,witness,prior):
    bind(c['pins'][c['prior_contract']]=='5df5009176342658eb7b31c7c099e643c9e99cc898d2a14f319858a9df391244','prior_contract_identity')
    bind(c['pins'][c['witness']]=='6e3653bb35321a72eee1c583c9345e7c8e27cc1d63340f192da4c0a238ce7028','witness_identity')
    expected={'source':prior['candidate_mlod'],'reference':prior['source_control'],'previous_report':prior['offline_proof'],'original_result':prior['original_result']}
    bind(all(c[k]==p and c['pins'][p]==prior['pins'][p] for k,p in expected.items()),'prior_input_binding')
    bind(all(c[k]==prior[k] for k in ('origin','matrix','targets','selected_components')),'context_binding')
    bind(c['centre']==witness['centre_fixed'] and c['matrix'][9:]==witness['translation_fixed'],'witness_frame_binding')

def saved(path):
    try:return load(path)
    except Exception as e:raise Inconclusive('read_or_eof:'+str(e)) from e

def contact_rows(xyz,groups,selected,targets,origin):
    result=[]
    for target in targets:
        local_point=Point(target['x']-origin[0],target['z']-origin[2]);world_point=Point(np.asarray([target['x'],target['z']],'<f4').astype(float))
        local=[];world=[]
        for name in selected:
            ids=groups[name]['top'];p=Polygon(xyz[ids][:,[0,2]])
            if p.contains(local_point):local.append(p.boundary.distance(local_point))
            p=Polygon((xyz[ids][:,[0,2]]+origin[[0,2]]).astype('<f4').astype(float))
            if p.is_valid and p.area>0 and p.contains(world_point):world.append((p.boundary.distance(world_point),name))
        need(local and world,'strict_contact:'+str(target['id']));margin,name=max(world)
        result.append(dict(id=target['id'],local_margin_m=max(local),world_float32_margin_m=margin,witness_component=name))
    return result

def exact_pairs(xyz,groups):
    count=0
    for name,g in groups.items():
        pairs={}
        for i in g['ids']:pairs.setdefault(tuple(xyz[i,[0,2]]),[]).append(i)
        need(len(pairs)==3 and all(len(v)==2 for v in pairs.values()),'pair_members')
        for pair in pairs.values():
            lo,hi=sorted(pair,key=lambda i:xyz[i,1]);count+=1
            need(Fraction(float(xyz[hi,1]))-Fraction(float(xyz[lo,1]))==Fraction(180,512),'exact_mlod_thickness:'+name)
    return count

def verify(source,candidate,reference,witness,selected,origin,centre,matrix,targets,previous,expected_counts=(9120,12160,1520),expected_changes=17):
    sh,sl,sb=saved(source);nh,nl,nb=saved(candidate);rh,rl,rb=saved(reference)
    bind(sh==nh==rh==struct.pack('<4sII',b'MLOD',257,4),'mlod_header')
    for ls,blobs in ((sl,sb),(nl,nb),(rl,rb)):
        g=ls[1];bind(len(g.points)==expected_counts[0] and len(g.faces)==expected_counts[1] and len(g.selections)==expected_counts[2],'geometry_counts')
        bind(struct.unpack_from('<4s6I',blobs[1])==(b'P3DM',28,256,len(g.points),len(g.facenormals),len(g.faces),0),'geometry_header')
    need(all(sb[i]==nb[i]==rb[i] for i in (0,2,3)),'non_geometry_changed')
    bind(len(sb[1])==len(nb[1])==len(rb[1]),'geometry_length')
    old,og=components(sl[1]);new,ng=components(nl[1]);ref,rg=components(rl[1])
    need(set(og)==set(ng)==set(rg) and len(set(selected))==len(selected) and set(selected)<=set(ng) and selected,'component_set')
    need(witness['status']=='FEASIBILITY_ONLY','witness_status');entries=witness['witness'];need(len(entries)==expected_changes,'witness_count')
    allowed={i for n in selected for i in og[n]['ids']};seen=set()
    for row in entries:
        i=row['source_index'];need(type(i) is int and i in allowed and i not in seen,'witness_index');seen.add(i)
        before=np.asarray(row['before'],float);after=np.asarray(row['after'],float)
        need(before.shape==after.shape==(3,) and np.isfinite([before,after]).all(),'witness_finite_shape')
        need(np.array_equal(before,before.astype('<f4').astype(float)) and np.array_equal(after,after.astype('<f4').astype(float)),'witness_not_float32')
        need(bit_equal(before,old[i]) and bit_equal(after,new[i]),'witness_saved_values')
        need(bit_equal(before[[0,2]],after[[0,2]]) and not bit_equal(before[1],after[1]),'witness_not_y_change')
    incident=[fi for fi,f in enumerate(nl[1].faces) if any(v.point_index in seen for v in f.vertices)]
    allowed_faces={i for n in selected for i in ng[n]['faces']};need(set(incident)<=allowed_faces,'incident_domain')
    mask=np.zeros(len(nb[1]),bool)
    for i in seen:mask[28+16*i+4:28+16*i+8]=True
    normal_ids=set()
    for fi in incident:
        ns={v.normal_index for v in nl[1].faces[fi].vertices};need(len(ns)==1,'normal_mapping');ni=next(iter(ns));need(ni not in normal_ids,'shared_normal');normal_ids.add(ni)
        start=28+16*len(new)+12*ni;mask[start:start+12]=True
    need(not any(v.normal_index in normal_ids for fi,f in enumerate(nl[1].faces) if fi not in incident for v in f.vertices),'external_normal')
    need(np.array_equal(np.frombuffer(sb[1],np.uint8)[~mask],np.frombuffer(nb[1],np.uint8)[~mask]),'unauthorized_bytes_changed')
    need(bit_equal(old[:,[0,2]],new[:,[0,2]]),'xz_changed')
    # Old B3 authorization against d130 is re-established independently.
    prior_mask=np.zeros(len(sb[1]),bool)
    for n in selected:
        need(og[n]['ids']==ng[n]['ids']==rg[n]['ids'] and og[n]['faces']==ng[n]['faces']==rg[n]['faces'],'component_members')
        for i in og[n]['ids']:prior_mask[28+16*i:28+16*i+12]=True
        for ni in og[n]['normals']:
            start=28+16*len(old)+12*ni;prior_mask[start:start+12]=True
    need(np.array_equal(np.frombuffer(sb[1],np.uint8)[~prior_mask],np.frombuffer(rb[1],np.uint8)[~prior_mask]),'baseline_outside_domain')
    pair_count=exact_pairs(new,ng)
    full_old=np.concatenate([np.asarray([p.coords for p in l.points]).reshape(-1,3) for l in sl]);full_new=np.concatenate([np.asarray([p.coords for p in l.points]).reshape(-1,3) for l in nl])
    need(bit_equal([old.min(0),old.max(0)],[new.min(0),new.max(0)]) and bit_equal([full_old.min(0),full_old.max(0)],[full_new.min(0),full_new.max(0)]),'bbox_changed')
    errors=[]
    for n in selected:
        top=ref[rg[n]['top']];normal=np.cross(top[1]-top[0],top[2]-top[0]);need(abs(normal[1])>1e-10,'reference_vertical_roof')
        for i in ng[n]['ids']:
            expect=top[0,1]-(normal[0]*(new[i,0]-top[0,0])+normal[2]*(new[i,2]-top[0,2]))/normal[1]
            if i not in ng[n]['top']:expect-=180/512
            error=abs(new[i,1]-expect);need(error<=1e-6,'reference_plane');errors.append(float(error))
    origin=np.asarray(origin,float);centre=np.asarray(centre,float);matrix=np.asarray(matrix,float)
    bind(origin.shape==centre.shape==(3,) and matrix.shape==(12,) and np.isfinite(np.r_[origin,centre,matrix]).all(),'frame_shape')
    bind(np.array_equal(matrix[:9],[1,0,0,0,1,0,0,0,1]) and bit_equal(origin+centre,matrix[9:]),'pose_frame')
    local=(new-centre).astype('<f4');world=(local.astype(float)+matrix[9:]).astype('<f4');source_world=(new+origin).astype('<f4')
    need(bit_equal(world,source_world),'world_frames')
    need(bit_equal([(old-centre).astype('<f4').min(0),(old-centre).astype('<f4').max(0)],[local.min(0),local.max(0)]),'predicted_bbox_changed')
    contacts=contact_rows(new,ng,selected,targets,origin)
    fields=('id','local_margin_m','world_float32_margin_m','witness_component')
    need(contacts==[{k:row[k] for k in fields} for row in previous['contacts']],'contact_receipt_changed')
    triangles=np.asarray([[world[v.point_index] for v in f.vertices] for f in nl[1].faces],float)
    cross=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);roof=triangles[cross[:,1]<-1e-10]
    bed=vertices(nl[0],[f for f in nl[0].faces if 'water_streambed.rvmat' not in f.material])+origin
    over=overlay(bed,roof);need(all(over['checks'].values()),'overlay')
    return dict(status='OFFLINE_CANDIDATE_ONLY',changed_y=len(seen),incident_faces=len(incident),incident_normals=len(normal_ids),exact_mlod_pairs=pair_count,geometry_counts=list(expected_counts),maximum_plane_error_m=max(errors),world_frames_bit_exact=True,source_and_predicted_bbox_exact=True,protected_bytes_exact=True,contacts=contacts,overlay=over,limits='Fixed-frame MLOD calculation only; no new ODOL, compiler centre, package or native certification.')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('contract',type=Path);ap.add_argument('candidate',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
    meter.STARTED=START;meter.MAX_SECONDS=180;stop=meter.bounded(a.output)
    try:
        contract_sha=meter.sha(a.contract)
        try:c=json.loads(a.contract.read_bytes())
        except Exception as e:raise Inconclusive('contract_read:'+str(e)) from e
        bind(c['schema']=='B3D_NUMERIC_MLOD_V1' and c['expected_counts']==[9120,12160,1520] and c['expected_changes']==17,'contract_schema')
        for key in ('source','reference','witness','previous_report','original_result','prior_contract'):bind(c[key] in c['pins'],'unpinned_'+key)
        for p,h in c['pins'].items():bind(meter.sha(p)==h,'input_changed:'+p)
        witness=json.loads(Path(c['witness']).read_bytes());bind_contract(c,witness,json.loads(Path(c['prior_contract']).read_bytes()))
        candidate_sha=meter.sha(a.candidate)
        original_controls(json.loads(Path(c['original_result']).read_bytes()),c['targets'],c['origin'])
        report=verify(c['source'],a.candidate,c['reference'],witness,c['selected_components'],c['origin'],c['centre'],c['matrix'],c['targets'],json.loads(Path(c['previous_report']).read_bytes()))
        need(report['incident_faces']==report['incident_normals']==50,'incident_counts')
        bind(meter.sha(a.candidate)==candidate_sha,'candidate_changed_during_read')
        bind(meter.sha(a.contract)==contract_sha,'contract_changed_during_read')
        report.update(candidate_sha256=candidate_sha,contract_sha256=contract_sha,measurement=meter.memory())
        for p,h in c['pins'].items():bind(meter.sha(p)==h,'input_changed_after:'+p)
        meter.dump(a.output/'report.json',report);print(json.dumps(report))
    except Exception as e:meter.dump(a.output/'failure.json',dict(status=failure_status(e),reason=str(e),measurement=meter.memory()));raise
    finally:stop.set()

if __name__=='__main__':main()
