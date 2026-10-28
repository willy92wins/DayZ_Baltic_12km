"""B3E saved-binary consumer; no authoring, compiler invocation or deployment."""
import os,time
START=time.monotonic()
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
from pathlib import Path
from collections import Counter
import argparse,json,sys,traceback
import numpy as np
import shapely
from shapely.geometry import Point,Polygon
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'water'),str(HERE.parent/'playtest')]
import prism_b3_binary_ev112 as old
import water_constraint_diagnostic_ev112 as meter
from verify_prism_b3_numeric_ev112 import contact_rows as mlod_contact_rows

CANDIDATE='f2b7018bea6a692ef5964bae4894172e0a73eeabe8be55ea68244a774cb7e634'
OFFLINE='b44553ee67478e597511e6a075452b07858d6f2457f9a035c3f1101d4bdbf31a'
PROOF='ae5eea19e819cc7c5f61041b77cea0c15f4269ed080dcb470c2acf2a994d25b6'
PRIOR='5df5009176342658eb7b31c7c099e643c9e99cc898d2a14f319858a9df391244'
Inconclusive=old.Inconclusive
bind=old.bind
need=old.need

def read_checked(label,fn,*args,**kwargs):
    try:return fn(*args,**kwargs)
    except Exception as e:raise Inconclusive('read:'+label+':'+type(e).__name__+':'+str(e)) from e

def failure_status(error):
    # Explicit geometric checks use old.need, which attaches details even if None.
    return 'REJECTED_BINARY' if type(error) is ValueError and hasattr(error,'details') else 'INCONCLUSIVE_BINARY'

def source_contact_reference(mlod,c,proof):
    xyz=np.asarray([p.coords for p in mlod.points],float);ids={id(p):i for i,p in enumerate(mlod.points)};groups={}
    for name in c['selected_components']:
        pairs={}
        for p in mlod.selections[name].points:
            i=ids[id(p)];pairs.setdefault(tuple(xyz[i,[0,2]]),[]).append(i)
        bind(len(pairs)==3 and all(len(v)==2 for v in pairs.values()),'reference_contact_pairs')
        groups[name]=dict(top=[max(v,key=lambda i:xyz[i,1]) for v in pairs.values()])
    rows=read_checked('reference_contact_metric',mlod_contact_rows,xyz,groups,c['selected_components'],c['targets'],np.asarray(c['origin']))
    fields=('id','local_margin_m','world_float32_margin_m','witness_component')
    bind(rows==[{k:r[k] for k in fields} for r in proof['contacts']],'reference_contact_metric_not_reproduced')
    return dict(status='HISTORICAL_METRIC_REPRODUCED',numpy=np.__version__,shapely=shapely.__version__,geos=shapely.geos_version_string,
                limit='Current libraries reproduce the sealed MLOD metrics; historical library versions were not recorded and are not inferred.')

def bits(a):return np.asarray(a,dtype='<f4').view('<u4')
def row_counter(a):return Counter(tuple(map(int,row)) for row in bits(a))
def face_bits(triangles):
    result=Counter()
    for tri in bits(triangles):
        v=tuple(tuple(map(int,row)) for row in tri)
        result[min(v,v[1:]+v[:1],v[2:]+v[:2])]+=1
    return result

def census(mlod,geo,origin,matrix,centre):
    """Visit the full union, preserving every discrepancy before any rejection."""
    src=np.asarray([p.coords for p in mlod.points],float);dec=old.old.xyz(geo.vertices)
    bind(len(geo.vertex_raw)%12==0,'raw_coordinate_length')
    raw=np.frombuffer(geo.vertex_raw,'<f4').reshape(-1,3)
    bind(src.ndim==dec.ndim==2 and src.shape[1]==dec.shape[1]==3 and np.isfinite(src).all() and np.isfinite(dec).all(),'census_coordinates')
    bind(raw.shape==dec.shape and np.array_equal(bits(raw),bits(dec)),'raw_decode_bits')
    source={k.lower():v for k,v in mlod.selections.items()};compiled={v.name.lower():v for v in geo.named_selections}
    global_errors=[]
    if len(source)!=len(mlod.selections) or len(compiled)!=len(geo.named_selections):global_errors.append('duplicate_component_name')
    if set(source)!=set(compiled):global_errors.append('component_name_set')
    point_ids={id(p):i for i,p in enumerate(mlod.points)};face_ids={id(f):i for i,f in enumerate(mlod.faces)}
    world=(dec+np.asarray(matrix)[9:]).astype('<f4');source_world=(src+origin).astype('<f4')
    rows=[];cp=[];cf=[];sp=[];sf=[]
    for name in sorted(set(source)|set(compiled)):
        row=dict(component=name,structural_errors=[]);rows.append(row)
        if name not in source or name not in compiled:row['structural_errors'].append('missing_component');continue
        a=source[name];b=compiled[name]
        try:
            ai=[point_ids[id(p)] for p in a.points];af=[face_ids[id(f)] for f in a.faces]
            bi=list(map(int,b.selected_vertices));bf=list(map(int,b.selected_faces))
        except (KeyError,TypeError,ValueError):row['structural_errors'].append('component_members');continue
        cp+=bi;cf+=bf;sp+=ai;sf+=af
        if any(len(x)!=n or len(set(x))!=n for x,n in [(ai,6),(bi,6),(af,8),(bf,8)]):row['structural_errors'].append('component_counts')
        if not all(0<=i<len(dec) for i in bi) or not all(0<=i<len(geo.faces) for i in bf):row['structural_errors'].append('component_bounds')
        if row['structural_errors']:continue
        wanted=[];got=[]
        for f in a.faces:
            ix=[v.point_index for v in f.vertices]
            if len(ix)!=3 or not set(ix)<=set(ai):row['structural_errors'].append('source_face_domain');break
            wanted.append(source_world[ix])
        for fi in bf:
            ix=list(map(int,geo.faces[fi].vertex_indices))
            if len(ix)!=3 or not set(ix)<=set(bi):row['structural_errors'].append('compiled_face_domain');break
            got.append(world[ix][::-1])
        if row['structural_errors']:continue
        predicted=(src[ai]-centre).astype('<f4');pc,bc=row_counter(predicted),row_counter(raw[bi])
        wc,gc=face_bits(wanted),face_bits(got)
        error=max(old.bidirectional_error(src[ai]+origin,dec[bi]+np.asarray(matrix)[9:]).values())
        row.update(local_bits_exact=pc==bc,world_oriented_bits_exact=wc==gc,pre_world_rounding_error_m=error,
                   geometric_pass=pc==bc and wc==gc and error<.001)
        if not row['geometric_pass']:
            row.update(local_expected_only=list((pc-bc).elements()),local_actual_only=list((bc-pc).elements()),
                       world_expected_only=list((wc-gc).elements()),world_actual_only=list((gc-wc).elements()),
                       predicted_local=predicted.astype(float).tolist(),saved_local=raw[bi].astype(float).tolist(),
                       local_ulp_m=np.abs(np.spacing(predicted)).astype(float).tolist(),world_ulp_m=np.abs(np.spacing(world[bi])).astype(float).tolist())
    for label,values,total in [('compiled_points',cp,len(dec)),('compiled_faces',cf,len(geo.faces)),('source_points',sp,len(src)),('source_faces',sf,len(mlod.faces))]:
        if sorted(values)!=list(range(total)):global_errors.append('coverage_'+label)
    structural=sum(bool(r['structural_errors']) for r in rows);failures=[r['component'] for r in rows if r.get('geometric_pass') is False]
    status='INCONCLUSIVE_CENSUS' if global_errors or structural else 'REJECTED_CENSUS' if failures else 'EXACT_CENSUS'
    return dict(status=status,expected_components=len(source),observed_components=len(compiled),visited_components=len(rows),
                compared_components=sum('geometric_pass' in r for r in rows),global_errors=global_errors,
                structural_failures=structural,geometric_failures=failures,components=rows),world

def require_census(result,control=False):
    if result['status']!='EXACT_CENSUS':
        if control or result['status']=='INCONCLUSIVE_CENSUS':raise Inconclusive('census_not_certified',result)
        need(False,'compiled_geometry_discrepancies',result)

def gate_control(baseline,control,mlods,matrix,origin,targets,write_census):
    for od in (baseline,control):bind(not od.lod_errors and len(od.lods)==4 and all(l.lod_end_ok for l in od.lods),'control_incomplete')
    old.control_identity(baseline,control)
    centre=old.old.xyz([control.model_info.bounding_center])[0];old.pose_check(matrix,origin,centre)
    result,world=census(mlods[1],control.lods[1],np.asarray(origin),matrix,centre);write_census(result);require_census(result,True)
    bind((len(control.lods[1].vertices),len(control.lods[1].faces),len(control.lods[1].named_selections))==old.EXPECTED_COUNTS,'control_counts')
    tri=np.asarray([world[f.vertex_indices] for f in control.lods[1].faces])
    return dict(status='CONTROL_B3E_CERTIFIED',census_status=result['status'],components=result['visited_components'],contacts=old.strict_contacts(tri,targets,required=False),
                winding='This saved d130/control pair matches source oriented faces with inverse ODOL winding; control is semantically equal3514. Not a universal compiler or engine law.')

def contact_witness(geo,world,targets,source_names,previous,selected):
    canonical={n.lower():n for n in source_names};rows=[]
    domain={n.lower() for n in selected}
    for target in targets:
        point=Point(np.asarray([target['x'],target['z']],'<f4').astype(float));hits=[]
        for group in geo.named_selections:
            if group.name.lower() not in domain:continue
            for fi in map(int,group.selected_faces):
                t=world[list(geo.faces[fi].vertex_indices)].astype(float)
                if np.cross(t[1]-t[0],t[2]-t[0])[1]<=1e-10:continue
                poly=Polygon(t[:,[0,2]])
                if poly.is_valid and poly.area>0 and poly.contains(point):hits.append((poly.boundary.distance(point),canonical[group.name.lower()],fi))
        need(hits,'compiled_contact_boundary:'+str(target['id']));margin,name,fi=max(hits)
        expected=[r for r in previous['contacts'] if r['id']==target['id']];bind(len(expected)==1,'contact_proof_identity')
        need(margin==expected[0]['world_float32_margin_m'] and name==expected[0]['witness_component'],'contact_proof_changed')
        rows.append(dict(id=target['id'],margin_m=margin,witness_component=name,compiled_face_index=fi))
    return rows

def gate_candidate(baseline,control,candidate,mlods,control_mlods,c,proof,write_census):
    bind(not candidate.lod_errors and len(candidate.lods)==4 and all(l.lod_end_ok for l in candidate.lods),'candidate_incomplete')
    centre=old.old.xyz([candidate.model_info.bounding_center])[0]
    bind(np.array_equal(bits(centre),bits(c['centre'])),'candidate_centre_changed');old.pose_check(c['matrix'],c['origin'],centre)
    report,world=census(mlods[1],candidate.lods[1],np.asarray(c['origin']),c['matrix'],centre)
    write_census(report);require_census(report)
    result=old.verify_pair(baseline,control,candidate,mlods,control_mlods,c['matrix'],c['origin'],c['targets'],c['selected_components'])
    result.update(status='COMPILED_B3E_CONDITIONAL',census_status=report['status'],contact_witnesses=contact_witness(candidate.lods[1],world,c['targets'],mlods[1].selections,proof,c['selected_components']),
                  frames='Saved ODOL raw-local and world oriented float32 bits match B3D MLOD at fixed pose. Inverse winding verified on this d130/control pair, not universal engine behavior.',
                  source_mlod_sha256=CANDIDATE)
    return result

def check_pins(c):
    for p,h in c['pins'].items():bind(meter.sha(p)==h,'input_changed:'+p)

def context(path):
    c=json.loads(path.read_bytes());bind(c['schema']=='B3E_COMPILED_V1','contract_schema')
    for k in ('offline_contract','offline_proof','prior_contract','source_control','candidate_mlod','baseline_odol','baseline_pbo','original_result','poses'):
        bind(c[k] in c['pins'],'unpinned:'+k)
    check_pins(c)
    for key,expected in [('offline_contract',OFFLINE),('offline_proof',PROOF),('prior_contract',PRIOR),('candidate_mlod',CANDIDATE)]:bind(c['pins'][c[key]]==expected,'anchor_identity:'+key)
    d=json.loads(Path(c['offline_contract']).read_bytes());proof=json.loads(Path(c['offline_proof']).read_bytes());prior=json.loads(Path(c['prior_contract']).read_bytes())
    bind(proof['status']=='OFFLINE_CANDIDATE_ONLY' and proof['candidate_sha256']==CANDIDATE and proof['contract_sha256']==OFFLINE and proof['exact_mlod_pairs']==4560,'offline_proof')
    bind(all(c['pins'].get(p)==h for p,h in d['pins'].items()),'transitive_pins')
    bind(c['source_control']==d['reference'] and c['original_result']==d['original_result'],'source_context')
    for k in ('origin','matrix','centre','targets','selected_components'):bind(c[k]==d[k],'context:'+k)
    for k in ('baseline_odol','baseline_pbo','poses'):bind(c[k]==prior[k] and c['pins'][c[k]]==prior['pins'][prior[k]],'prior_context:'+k)
    poses=read_checked('poses',np.load,c['poses']);ix=np.flatnonzero(poses['ids']==19394363)
    bind(len(ix)==1 and np.array_equal(poses['matrix'][ix[0]],c['matrix']),'WRP_pose')
    try:old.original_controls(json.loads(Path(c['original_result']).read_bytes()),c['targets'],c['origin'])
    except ValueError as e:raise Inconclusive('original_controls:'+str(e)) from e
    return c,proof

def payload(pair,side,c):
    p=pair/side;_,props,entries=read_checked('pbo:'+side,old.read_pbo,p/'packed/baltic_stream_pilot.pbo')
    bind(set(entries)=={old.NAME,'config.bin'} and props['prefix']=='baltic_stream_pilot','package_entries')
    bind(entries[old.NAME]==(p/'saved-odol.p3d').read_bytes(),'saved_payload')
    source=p/'source/baltic_stream_pilot'
    expected=c['source_control'] if side=='control' else c['candidate_mlod']
    bind(meter.sha(source/old.NAME)==c['pins'][expected],'staged_source')
    bind(meter.sha(source/'config.cpp')==c['config_sha256'] and (source/'$PBOPREFIX$').read_bytes()==b'baltic_stream_pilot','staged_config')
    return entries['config.bin']

def consume(mode,contract,pair,reader,output):
    contract_sha=meter.sha(contract);c,proof=context(contract)
    phases=['control'] if mode=='control' else ['control','candidate']
    paths=[pair/s/n for s in phases for n in ('saved-odol.p3d','packed/baltic_stream_pilot.pbo','source/baltic_stream_pilot/'+old.NAME,'source/baltic_stream_pilot/config.cpp','source/baltic_stream_pilot/$PBOPREFIX$')]
    if mode=='candidate':paths += [pair/'control-gate/report.json',pair/'control-gate/census.json']
    snapshots={str(p):meter.sha(p) for p in paths}
    configs=[payload(pair,s,c) for s in phases];bind(all(x==configs[0] for x in configs),'config_bin_changed')
    _,_,base_entries=read_checked('baseline_pbo',old.read_pbo,Path(c['baseline_pbo']));bind(base_entries[old.NAME]==Path(c['baseline_odol']).read_bytes(),'historical_payload')
    ODOL=read_checked('backend',old.old.read_backend,reader);baseline=read_checked('baseline_odol',ODOL.from_file,c['baseline_odol'],strict=True)
    control=read_checked('control_odol',ODOL.from_file,str(pair/'control/saved-odol.p3d'),strict=True);_,control_mlods,_=read_checked('control_mlod',old.load,c['source_control'])
    if mode=='control':
        bind(not (pair/'candidate').exists(),'candidate_started_before_control')
        result=gate_control(baseline,control,control_mlods,c['matrix'],c['origin'],c['targets'],lambda r:meter.dump(output/'census.json',r))
    else:
        receipt=json.loads((pair/'control-gate/report.json').read_bytes())
        bind(receipt['status']=='CONTROL_B3E_CERTIFIED' and receipt['contract_sha256']==contract_sha,'control_gate_receipt')
        bind(all(snapshots.get(p)==h for p,h in receipt['outputs'].items()),'control_receipt_payload_changed')
        bind(meter.sha(pair/'control-gate/census.json')==receipt['census_sha256'],'control_census_binding')
        old.control_identity(baseline,control)
        candidate=read_checked('candidate_odol',ODOL.from_file,str(pair/'candidate/saved-odol.p3d'),strict=True)
        _,mlods,_=read_checked('candidate_mlod',old.load,c['candidate_mlod'])
        metric=source_contact_reference(mlods[1],c,proof)
        result=gate_candidate(baseline,control,candidate,mlods,control_mlods,c,proof,lambda r:meter.dump(output/'census.json',r))
        result.update(candidate_sha256=meter.sha(pair/'candidate/saved-odol.p3d'),contact_metric_reference=metric)
    check_pins(c);bind(meter.sha(contract)==contract_sha,'contract_changed_during_read')
    for p,h in snapshots.items():bind(meter.sha(p)==h,'output_changed_during_read:'+p)
    result.update(contract_sha256=contract_sha,outputs=snapshots,census_sha256=meter.sha(output/'census.json'),measurement=meter.memory(),no_package201_or_dayz=True)
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['control','candidate']);ap.add_argument('contract',type=Path);ap.add_argument('pair',type=Path);ap.add_argument('reader',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
    meter.STARTED=START;meter.MAX_SECONDS=180;stop=meter.bounded(a.output)
    try:
        r=consume(a.mode,a.contract,a.pair,a.reader,a.output);meter.dump(a.output/'report.json',r);print(json.dumps(dict(status=r['status'],measurement=r['measurement'])))
    except Exception as e:
        status=failure_status(e)
        meter.dump(a.output/'report.json',dict(status=status,type=type(e).__name__,reason=str(e),details=getattr(e,'details',None),traceback=traceback.format_exc(),measurement=meter.memory()));raise SystemExit(1 if status=='REJECTED_BINARY' else 2)
    finally:stop.set()

if __name__=='__main__':main()
