"""Adversarial semantic mutations of actual decoded ODOLs and actual PBO payloads.

Mutations deliberately bypass the provenance hash gate: the consumer itself must
reject them. They are never written to deployable files. One full real positive
and focused mutants exercise the same consumer functions, without recompiling.
"""
from pathlib import Path
import argparse,copy,json,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import compiled_dry_road_gate_ev112 as g

def run(root,reader_root):
    pins=g.inputs(root,reader_root);pins[str(Path(__file__).resolve())]=g.sha(__file__);ods,old,new,matrix,numeric_chain=g.context(root,reader_root);before,a,b,y,n=ods
    positive=g.verify_models(*ods,old,new,matrix);rows=[]
    def reject(name,fn,reason,scope='full_compiled_consumer'):
        try:fn()
        except ValueError as exc:
            g.require(reason in str(exc),'wrong_rejection:'+name+':'+str(exc));rows.append(dict(name=name,rejected_by=str(exc),scope=scope));return
        raise AssertionError('false_PASS:'+name)
    def full(mutator):
        mutant=copy.deepcopy(b);mutator(mutant);return g.verify_models(before,a,mutant,y,n,old,new,matrix)
    reject('unknown_metadata',lambda:full(lambda m:setattr(m.lods[0],'unexpected_flag',1)),'unknown_fields:unexpected_flag')
    def reverse_roadway(m):m.lods[3].faces[0].vertex_indices=list(reversed(m.lods[3].faces[0].vertex_indices))
    reject('Roadway_winding',lambda:full(reverse_roadway),'unknown_fields:labelled_faces')
    coords=g.xyz(a.lods[0].vertices);other=g.xyz(b.lods[0].vertices);norms=g.xyz(a.lods[0].normals);nn=g.xyz(b.lods[0].normals)
    influenced=np.any(coords!=other,axis=1)
    for f in a.lods[0].faces:
        ids=f.vertex_indices
        if np.any(coords[ids]!=other[ids]):influenced[ids]=True
    influenced|=np.any(norms!=nn,axis=1);unaffected=int(np.flatnonzero(~influenced)[0])
    def st_byte(m):
        raw=bytearray(m.lods[0].st_raw);raw[8*unaffected]^=1;m.lods[0].st_raw=bytes(raw)
    reject('ST_byte_outside_influence',lambda:full(st_byte),'ST_nonlocal_change')
    mutant=copy.deepcopy(b.lods[0]);words=np.frombuffer(mutant.st_raw,'<u4').copy().reshape(-1,2)
    idx=int(np.flatnonzero(influenced)[0]);word=int(words[idx,0]);v=np.array([word&1023,(word>>10)&1023,(word>>20)&1023]);v[v>511]-=1024;v=-v
    words[idx,0]=(word&0xc0000000)|int(v[0]&1023)|(int(v[1]&1023)<<10)|(int(v[2]&1023)<<20);mutant.st_raw=words.tobytes()
    reject('ST_frame_handedness',lambda:g.check_frames(a.lods[0],mutant),'ST_handedness','frame_function')
    def normal_word(m):
        i=int(m.lods[0].faces[0].vertex_indices[0]);raw=bytearray(m.lods[0].normal_raw);raw[4*i+3]^=0x80;m.lods[0].normal_raw=bytes(raw)
    # Direct source consumer: the full gate rejects it even earlier because the
    # immutable N-only diagnostic no longer matches the changed codeword.
    mutant_normal=copy.deepcopy(b);normal_word(mutant_normal)
    reject('normal_codeword_high_bit',lambda:g.source_geometry(mutant_normal,new,matrix,np.array([8262.,7.,8934.])),'visual_normal_codec','source_geometry_consumer')
    def uv(m):
        s=m.lods[0].uv_sets[0];g.require(not s.default_fill,'test_requires_real_uv_stream');raw=bytearray(s.uv_raw);raw[0]^=1;s.uv_raw=bytes(raw)
    reject('UV_changed',lambda:full(uv),'unknown_fields:uv_sets')
    def water(m):
        assignments,labels=g.sections(m.lods[0]);face=next(f for i,f in enumerate(m.lods[0].faces) if 'water' in labels[int(assignments[i])]['material'] and 'streambed_leaf' not in labels[int(assignments[i])]['material']);i=int(face.vertex_indices[0])
        raw=np.frombuffer(m.lods[0].vertex_raw,'<f4').copy().reshape(-1,3);raw[i,1]=np.float32(raw[i,1]+np.float32(.25));m.lods[0].vertices[i].y=float(raw[i,1]);m.lods[0].vertex_raw=raw.tobytes()
    mutant=copy.deepcopy(b);water(mutant)
    reject('water_face_height',lambda:g.source_geometry(mutant,new,matrix,np.array([8262.,7.,8934.])),'source_face_counter:0','source_geometry_consumer')
    reject('serialized_size',lambda:full(lambda m:setattr(m.lods[0],'size_of_rest_data',m.lods[0].size_of_rest_data+1)),'rest_data_size:candidate:0')
    _,props,entries=g.read_pbo(root/'package-kit7-contact-only-20261026/Addons/baltic_stream_pilot.pbo');payload=(root/'dry-road-compile-pair-20261028/candidate/saved-odol.p3d').read_bytes();packed=entries.copy();packed[g.NAME]=payload
    package_positive=g.package_identity(props,entries,props,packed,payload)
    other_name=next(k for k in packed if k.endswith('.p3d') and k!=g.NAME)
    for name,k in [('second_model',other_name),('config','config.bin')]:
        bad=packed.copy();bad[k]=bad[k]+b'\x00';reject('PBO_'+name,lambda bad=bad:g.package_identity(props,entries,props,bad,payload),'PBO_changed_entries','package_consumer')
    bad=dict(reversed(list(packed.items())));reject('PBO_order',lambda:g.package_identity(props,entries,props,bad,payload),'PBO_entry_order_or_identity','package_consumer')
    bad=packed.copy();bad[g.NAME]=payload+b'\x00';reject('PBO_wrong_candidate',lambda:g.package_identity(props,entries,props,bad,payload),'PBO_candidate_payload','package_consumer')
    for p,d in pins.items():g.require(g.sha(p)==d,'input_changed_during_mutants:'+p)
    return dict(status='REAL_DECODED_CONSUMER_CONTROLS_PASS',positive=positive['status'],package_positive=package_positive,negative_count=len(rows),negative_tests=rows,limits=['Semantic mutations operate on decoded real data and bypass hashes, never deployable files.','No visual acceptance, ST layout proof or runtime result.'],inputs=pins,measurement=g.meter.memory())

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('reader_root',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False);g.meter.STARTED=time.monotonic();g.meter.MAX_SECONDS=300;stop=g.meter.bounded(a.output)
    try:result=run(a.root,a.reader_root);g.meter.dump(a.output/'report.json',result);print(json.dumps({k:v for k,v in result.items() if k!='inputs'}))
    except Exception as exc:g.meter.dump(a.output/'failure.json',dict(type=type(exc).__name__,error=str(exc),measurement=g.meter.memory()));raise
    finally:stop.set()
