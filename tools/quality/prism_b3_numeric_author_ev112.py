"""B3D: apply a sealed numerical witness, Y and incident normals only."""
import os,time
START=time.monotonic()
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
from pathlib import Path
import argparse,json,struct,sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'water')]
from review_compact_collision_v31 import load
import water_constraint_diagnostic_ev112 as meter

def need(ok,reason):
    if not bool(ok):raise ValueError(reason)

def bits(a):return np.asarray(a,dtype='<f4').view('<u4')

def save_checked(blob,output,check_inputs):
    pending=output/'candidate.p3d.tmp';dest=output/'candidate.p3d'
    need(not dest.exists(),'candidate_already_exists')
    with pending.open('xb') as f:f.write(blob)
    digest=meter.sha(pending)
    check_inputs()
    pending.rename(dest)
    return dest,digest

def bind_contract(c,witness,prior):
    need(c['pins'][c['prior_contract']]=='5df5009176342658eb7b31c7c099e643c9e99cc898d2a14f319858a9df391244','prior_contract_identity')
    need(c['pins'][c['witness']]=='6e3653bb35321a72eee1c583c9345e7c8e27cc1d63340f192da4c0a238ce7028','witness_identity')
    for key,old in [('source','candidate_mlod'),('reference','source_control'),('previous_report','offline_proof'),('original_result','original_result')]:
        need(c[key]==prior[old] and c['pins'][c[key]]==prior['pins'][prior[old]],'prior_binding:'+key)
    for key in ('origin','matrix','targets','selected_components'):need(c[key]==prior[key],'context_binding:'+key)
    need(c['centre']==witness['centre_fixed'] and c['matrix'][9:]==witness['translation_fixed'],'witness_frame_binding')

def author(source,witness,selected,expected_changes=17):
    h,ls,blobs=load(source);g=ls[1]
    need(h==struct.pack('<4sII',b'MLOD',257,4),'header')
    need(struct.unpack_from('<4s6I',blobs[1])==(b'P3DM',28,256,len(g.points),len(g.facenormals),len(g.faces),0),'geometry_header')
    need(witness['status']=='FEASIBILITY_ONLY','witness_status')
    points=np.asarray([p.coords for p in g.points],float);new=points.copy()
    pi={id(p):i for i,p in enumerate(g.points)}
    need(set(selected)<=set(g.selections) and selected,'selected_components')
    allowed={pi[id(p)] for name in selected for p in g.selections[name].points}
    rows=witness['witness'];need(len(rows)==expected_changes,'witness_count');seen=set()
    for row in rows:
        i=row['source_index'];need(type(i) is int and i in allowed and i not in seen,'witness_index');seen.add(i)
        before=np.asarray(row['before'],float);after=np.asarray(row['after'],float)
        need(before.shape==after.shape==(3,) and np.isfinite([before,after]).all(),'witness_finite_shape')
        need(np.array_equal(before,before.astype('<f4').astype(float)) and np.array_equal(after,after.astype('<f4').astype(float)),'witness_not_float32')
        need(np.array_equal(bits(before),bits(points[i])),'witness_before')
        need(np.array_equal(bits(after[[0,2]]),bits(before[[0,2]])) and bits(after[1])!=bits(before[1]),'witness_not_y_change')
        new[i,1]=after[1]
    incident=[fi for fi,f in enumerate(g.faces) if any(v.point_index in seen for v in f.vertices)]
    fis={id(f):i for i,f in enumerate(g.faces)}
    allowed_faces={fis[id(f)] for name in selected for f in g.selections[name].faces}
    need(set(incident)<=allowed_faces,'incident_outside_components')
    normal_ids=[]
    for fi in incident:
        f=g.faces[fi];ns={v.normal_index for v in f.vertices}
        need(len(f.vertices)==3 and len(ns)==1,'face_normal_mapping');normal_ids.append(next(iter(ns)))
    need(len(set(normal_ids))==len(normal_ids),'shared_incident_normal')
    need(not any(v.normal_index in normal_ids for fi,f in enumerate(g.faces) if fi not in incident for v in f.vertices),'external_normal_sharing')
    blob=bytearray(blobs[1])
    for i in seen:struct.pack_into('<f',blob,28+16*i+4,new[i,1])
    for fi,ni in zip(incident,normal_ids):
        t=new[[v.point_index for v in g.faces[fi].vertices]];n=np.cross(t[1]-t[0],t[2]-t[0]);length=np.linalg.norm(n)
        need(length>1e-9,'degenerate_face');n/=length
        struct.pack_into('<3f',blob,28+16*len(g.points)+12*ni,*n)
    blobs[1]=bytes(blob)
    return h+b''.join(blobs),dict(status='WRITTEN_PENDING_INDEPENDENT_CONSUMER',changed_y=len(seen),incident_faces=len(incident),incident_normals=len(normal_ids))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('contract',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
    meter.STARTED=START;meter.MAX_SECONDS=60;stop=meter.bounded(a.output)
    try:
        contract_sha=meter.sha(a.contract)
        c=json.loads(a.contract.read_bytes())
        need(c['schema']=='B3D_NUMERIC_MLOD_V1' and c['expected_changes']==17 and c['expected_counts']==[9120,12160,1520],'contract_schema')
        for key in ('source','reference','witness','previous_report','original_result','prior_contract'):need(c[key] in c['pins'],'unpinned_'+key)
        for p,h in c['pins'].items():need(meter.sha(p)==h,'input_changed:'+p)
        witness=json.loads(Path(c['witness']).read_bytes());bind_contract(c,witness,json.loads(Path(c['prior_contract']).read_bytes()))
        blob,report=author(c['source'],witness,c['selected_components'])
        need(report['incident_faces']==report['incident_normals']==50,'incident_counts')
        def stable():
            need(meter.sha(a.contract)==contract_sha,'contract_changed_during_read')
            for p,h in c['pins'].items():need(meter.sha(p)==h,'input_changed_after:'+p)
        dest,digest=save_checked(blob,a.output,stable)
        report.update(candidate_sha256=digest,source_sha256=meter.sha(c['source']),contract_sha256=contract_sha,measurement=meter.memory())
        meter.dump(a.output/'report.json',report);print(json.dumps(report))
    except Exception as e:meter.dump(a.output/'failure.json',dict(status='INCONCLUSIVE_AUTHOR',reason=str(e),measurement=meter.memory()));raise
    finally:stop.set()

if __name__=='__main__':main()
