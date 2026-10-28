Revisión adversarial independiente de código B3D DayZ Baltic. Rol Fable5.1 revisor; Codex executor/integrator. Esta cápsula contiene los tres archivos íntegros e implementaciones auxiliares relevantes, con números de línea. NO herramientas, NO ejecutar/escribir, sin hijos ni otros informes. Devuelve <=700palabras, SOUND/SOUND-with-fixes/NEEDS-WORK; hallazgos con fichero:línea, consecuencia y repro; cobertura/límites e identidad. Termina FIN_REVISION. Presupuesto de entrega180s. Esto recupera una revisión sin informe (timeout previo); no hay dictamen anterior que confirmar.
Contrato: aplicar exclusivamente testigoJSON sellado de17Y sobre c769 MLOD y50normales incidentes, conservar demásbytes. El consumidor no importa autor ni solver. Fuente d1304560pares exactos; candidato anterior c769 sólo20/36seleccionados exactos. El nuevo consumidor exige todos4560pares EXACTOS (Fraction), planos/base<=1e-6 respecto d130, cierre/convexidad/normales, fuente/caja/LOD/XZ protegidos, dosmarcosmundiales bit-idénticos bajo centro/posefijos, overlay±.02m/.01m y márgenes700dry/723wet idénticos al recibo sellado. Grosor local recenter NO es requisito:17pares testigo noexactoslocales, filtroextra refutado; no lo reinserte. No motor/ODOL aceptado: resultado máximo OFFLINE_CANDIDATE_ONLY. ContratoR1 hash5df... y witness6e... hardcoded provienen de evidencias publicadas e8a37e7. No autoría real ejecutada todavía. 24tests sintéticos guardados pasaron antes de las últimas guardasCLI, suite final y negativosCLI pendientes.
Busca falsoPASS/FAIL o rutaCLI sin identidad/bytes/marco/protecciones, controles/indexmask/normal sharing, errores de clasificación, TOCTOU, cobertura negativa. No pedir un informe más largo ni nuevos oráculos sin repro. Si una dependencia no está en cápsula, limita la conclusión en vez de imaginarla. meter.sha usa hashlib.sha256(Path.read_bytes); bounded es watchdog de tiempo/memoria en mismo proceso, dump JSON a archivo. Revisor no ejecuta nada; Codex adjudica y prueba repros. Ninguna rebaja de tolerancia ni cambio producto.


FILE prism_b3_numeric_author_ev112.py SHA256 0aae1b47ecab1ddc66b27a207c6241fdaa6306789db2e13b83d188ef60d2f7a3
1: """B3D: apply a sealed numerical witness, Y and incident normals only."""
2: import os,time
3: START=time.monotonic()
4: for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
5: from pathlib import Path
6: import argparse,json,struct,sys
7: import numpy as np
8: HERE=Path(__file__).resolve().parent
9: sys.path[:0]=[str(HERE),str(HERE.parent/'water')]
10: from review_compact_collision_v31 import load
11: import water_constraint_diagnostic_ev112 as meter
12: 
13: def need(ok,reason):
14:     if not bool(ok):raise ValueError(reason)
15: 
16: def bits(a):return np.asarray(a,dtype='<f4').view('<u4')
17: 
18: def bind_contract(c,witness,prior):
19:     need(c['pins'][c['prior_contract']]=='5df5009176342658eb7b31c7c099e643c9e99cc898d2a14f319858a9df391244','prior_contract_identity')
20:     need(c['pins'][c['witness']]=='6e3653bb35321a72eee1c583c9345e7c8e27cc1d63340f192da4c0a238ce7028','witness_identity')
21:     for key,old in [('source','candidate_mlod'),('reference','source_control'),('previous_report','offline_proof'),('original_result','original_result')]:
22:         need(c[key]==prior[old] and c['pins'][c[key]]==prior['pins'][prior[old]],'prior_binding:'+key)
23:     for key in ('origin','matrix','targets','selected_components'):need(c[key]==prior[key],'context_binding:'+key)
24:     need(c['centre']==witness['centre_fixed'] and c['matrix'][9:]==witness['translation_fixed'],'witness_frame_binding')
25: 
26: def author(source,witness,selected,expected_changes=17):
27:     h,ls,blobs=load(source);g=ls[1]
28:     need(h==struct.pack('<4sII',b'MLOD',257,4),'header')
29:     need(struct.unpack_from('<4s6I',blobs[1])==(b'P3DM',28,256,len(g.points),len(g.facenormals),len(g.faces),0),'geometry_header')
30:     need(witness['status']=='FEASIBILITY_ONLY','witness_status')
31:     points=np.asarray([p.coords for p in g.points],float);new=points.copy()
32:     pi={id(p):i for i,p in enumerate(g.points)}
33:     need(set(selected)<=set(g.selections) and selected,'selected_components')
34:     allowed={pi[id(p)] for name in selected for p in g.selections[name].points}
35:     rows=witness['witness'];need(len(rows)==expected_changes,'witness_count');seen=set()
36:     for row in rows:
37:         i=row['source_index'];need(type(i) is int and i in allowed and i not in seen,'witness_index');seen.add(i)
38:         before=np.asarray(row['before'],float);after=np.asarray(row['after'],float)
39:         need(before.shape==after.shape==(3,) and np.isfinite([before,after]).all(),'witness_finite_shape')
40:         need(np.array_equal(before,before.astype('<f4').astype(float)) and np.array_equal(after,after.astype('<f4').astype(float)),'witness_not_float32')
41:         need(np.array_equal(bits(before),bits(points[i])),'witness_before')
42:         need(np.array_equal(bits(after[[0,2]]),bits(before[[0,2]])) and bits(after[1])!=bits(before[1]),'witness_not_y_change')
43:         new[i,1]=after[1]
44:     incident=[fi for fi,f in enumerate(g.faces) if any(v.point_index in seen for v in f.vertices)]
45:     fis={id(f):i for i,f in enumerate(g.faces)}
46:     allowed_faces={fis[id(f)] for name in selected for f in g.selections[name].faces}
47:     need(set(incident)<=allowed_faces,'incident_outside_components')
48:     normal_ids=[]
49:     for fi in incident:
50:         f=g.faces[fi];ns={v.normal_index for v in f.vertices}
51:         need(len(f.vertices)==3 and len(ns)==1,'face_normal_mapping');normal_ids.append(next(iter(ns)))
52:     need(len(set(normal_ids))==len(normal_ids),'shared_incident_normal')
53:     need(not any(v.normal_index in normal_ids for fi,f in enumerate(g.faces) if fi not in incident for v in f.vertices),'external_normal_sharing')
54:     blob=bytearray(blobs[1])
55:     for i in seen:struct.pack_into('<f',blob,28+16*i+4,new[i,1])
56:     for fi,ni in zip(incident,normal_ids):
57:         t=new[[v.point_index for v in g.faces[fi].vertices]];n=np.cross(t[1]-t[0],t[2]-t[0]);length=np.linalg.norm(n)
58:         need(length>1e-9,'degenerate_face');n/=length
59:         struct.pack_into('<3f',blob,28+16*len(g.points)+12*ni,*n)
60:     blobs[1]=bytes(blob)
61:     return h+b''.join(blobs),dict(status='WRITTEN_PENDING_INDEPENDENT_CONSUMER',changed_y=len(seen),incident_faces=len(incident),incident_normals=len(normal_ids))
62: 
63: def main():
64:     ap=argparse.ArgumentParser();ap.add_argument('contract',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
65:     meter.STARTED=START;meter.MAX_SECONDS=60;stop=meter.bounded(a.output)
66:     try:
67:         contract_sha=meter.sha(a.contract)
68:         c=json.loads(a.contract.read_bytes())
69:         need(c['schema']=='B3D_NUMERIC_MLOD_V1' and c['expected_changes']==17 and c['expected_counts']==[9120,12160,1520],'contract_schema')
70:         for key in ('source','reference','witness','previous_report','original_result','prior_contract'):need(c[key] in c['pins'],'unpinned_'+key)
71:         for p,h in c['pins'].items():need(meter.sha(p)==h,'input_changed:'+p)
72:         witness=json.loads(Path(c['witness']).read_bytes());bind_contract(c,witness,json.loads(Path(c['prior_contract']).read_bytes()))
73:         blob,report=author(c['source'],witness,c['selected_components'])
74:         dest=a.output/'candidate.p3d';dest.write_bytes(blob)
75:         need(meter.sha(a.contract)==contract_sha,'contract_changed_during_read')
76:         report.update(candidate_sha256=meter.sha(dest),source_sha256=meter.sha(c['source']),contract_sha256=contract_sha,measurement=meter.memory())
77:         for p,h in c['pins'].items():need(meter.sha(p)==h,'input_changed_after:'+p)
78:         meter.dump(a.output/'report.json',report);print(json.dumps(report))
79:     except Exception as e:meter.dump(a.output/'failure.json',dict(status='INCONCLUSIVE_AUTHOR',reason=str(e),measurement=meter.memory()));raise
80:     finally:stop.set()
81: 
82: if __name__=='__main__':main()

FILE verify_prism_b3_numeric_ev112.py SHA256 558a6ce5151c8f128c0b5d5af5741234f8776e6cce54ee27936684d2566ffad9
1: """B3D independent saved-MLOD consumer. Never imports author or B3C solver."""
2: import os,time
3: START=time.monotonic()
4: for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
5: from pathlib import Path
6: from fractions import Fraction
7: import argparse,json,struct,sys
8: import numpy as np
9: from shapely.geometry import Point,Polygon
10: HERE=Path(__file__).resolve().parent
11: sys.path[:0]=[str(HERE),str(HERE.parent/'water')]
12: from review_compact_collision_v31 import load,vertices,overlay
13: from verify_prism_contact_b3_ev112 import components,original_controls
14: import water_constraint_diagnostic_ev112 as meter
15: 
16: class Inconclusive(ValueError):pass
17: def bind(ok,reason):
18:     if not bool(ok):raise Inconclusive(reason)
19: def need(ok,reason):
20:     if not bool(ok):raise ValueError(reason)
21: def bit_equal(a,b):return np.array_equal(np.asarray(a,dtype='<f4').view('<u4'),np.asarray(b,dtype='<f4').view('<u4'))
22: 
23: def bind_contract(c,witness,prior):
24:     bind(c['pins'][c['prior_contract']]=='5df5009176342658eb7b31c7c099e643c9e99cc898d2a14f319858a9df391244','prior_contract_identity')
25:     bind(c['pins'][c['witness']]=='6e3653bb35321a72eee1c583c9345e7c8e27cc1d63340f192da4c0a238ce7028','witness_identity')
26:     expected={'source':prior['candidate_mlod'],'reference':prior['source_control'],'previous_report':prior['offline_proof'],'original_result':prior['original_result']}
27:     bind(all(c[k]==p and c['pins'][p]==prior['pins'][p] for k,p in expected.items()),'prior_input_binding')
28:     bind(all(c[k]==prior[k] for k in ('origin','matrix','targets','selected_components')),'context_binding')
29:     bind(c['centre']==witness['centre_fixed'] and c['matrix'][9:]==witness['translation_fixed'],'witness_frame_binding')
30: 
31: def saved(path):
32:     try:return load(path)
33:     except Exception as e:raise Inconclusive('read_or_eof:'+str(e)) from e
34: 
35: def contact_rows(xyz,groups,selected,targets,origin):
36:     result=[]
37:     for target in targets:
38:         local_point=Point(target['x']-origin[0],target['z']-origin[2]);world_point=Point(np.asarray([target['x'],target['z']],'<f4').astype(float))
39:         local=[];world=[]
40:         for name in selected:
41:             ids=groups[name]['top'];p=Polygon(xyz[ids][:,[0,2]])
42:             if p.contains(local_point):local.append(p.boundary.distance(local_point))
43:             p=Polygon((xyz[ids][:,[0,2]]+origin[[0,2]]).astype('<f4').astype(float))
44:             if p.is_valid and p.area>0 and p.contains(world_point):world.append((p.boundary.distance(world_point),name))
45:         need(local and world,'strict_contact:'+str(target['id']));margin,name=max(world)
46:         result.append(dict(id=target['id'],local_margin_m=max(local),world_float32_margin_m=margin,witness_component=name))
47:     return result
48: 
49: def exact_pairs(xyz,groups):
50:     count=0
51:     for name,g in groups.items():
52:         pairs={}
53:         for i in g['ids']:pairs.setdefault(tuple(xyz[i,[0,2]]),[]).append(i)
54:         need(len(pairs)==3 and all(len(v)==2 for v in pairs.values()),'pair_members')
55:         for pair in pairs.values():
56:             lo,hi=sorted(pair,key=lambda i:xyz[i,1]);count+=1
57:             need(Fraction(float(xyz[hi,1]))-Fraction(float(xyz[lo,1]))==Fraction(180,512),'exact_mlod_thickness:'+name)
58:     return count
59: 
60: def verify(source,candidate,reference,witness,selected,origin,centre,matrix,targets,previous,expected_counts=(9120,12160,1520),expected_changes=17):
61:     sh,sl,sb=saved(source);nh,nl,nb=saved(candidate);rh,rl,rb=saved(reference)
62:     bind(sh==nh==rh==struct.pack('<4sII',b'MLOD',257,4),'mlod_header')
63:     for ls,blobs in ((sl,sb),(nl,nb),(rl,rb)):
64:         g=ls[1];bind(len(g.points)==expected_counts[0] and len(g.faces)==expected_counts[1] and len(g.selections)==expected_counts[2],'geometry_counts')
65:         bind(struct.unpack_from('<4s6I',blobs[1])==(b'P3DM',28,256,len(g.points),len(g.facenormals),len(g.faces),0),'geometry_header')
66:     need(all(sb[i]==nb[i]==rb[i] for i in (0,2,3)),'non_geometry_changed')
67:     bind(len(sb[1])==len(nb[1])==len(rb[1]),'geometry_length')
68:     old,og=components(sl[1]);new,ng=components(nl[1]);ref,rg=components(rl[1])
69:     need(set(og)==set(ng)==set(rg) and len(set(selected))==len(selected) and set(selected)<=set(ng) and selected,'component_set')
70:     need(witness['status']=='FEASIBILITY_ONLY','witness_status');entries=witness['witness'];need(len(entries)==expected_changes,'witness_count')
71:     allowed={i for n in selected for i in og[n]['ids']};seen=set()
72:     for row in entries:
73:         i=row['source_index'];need(type(i) is int and i in allowed and i not in seen,'witness_index');seen.add(i)
74:         before=np.asarray(row['before'],float);after=np.asarray(row['after'],float)
75:         need(before.shape==after.shape==(3,) and np.isfinite([before,after]).all(),'witness_finite_shape')
76:         need(np.array_equal(before,before.astype('<f4').astype(float)) and np.array_equal(after,after.astype('<f4').astype(float)),'witness_not_float32')
77:         need(bit_equal(before,old[i]) and bit_equal(after,new[i]),'witness_saved_values')
78:         need(bit_equal(before[[0,2]],after[[0,2]]) and not bit_equal(before[1],after[1]),'witness_not_y_change')
79:     incident=[fi for fi,f in enumerate(nl[1].faces) if any(v.point_index in seen for v in f.vertices)]
80:     allowed_faces={i for n in selected for i in ng[n]['faces']};need(set(incident)<=allowed_faces,'incident_domain')
81:     mask=np.zeros(len(nb[1]),bool)
82:     for i in seen:mask[28+16*i+4:28+16*i+8]=True
83:     normal_ids=set()
84:     for fi in incident:
85:         ns={v.normal_index for v in nl[1].faces[fi].vertices};need(len(ns)==1,'normal_mapping');ni=next(iter(ns));need(ni not in normal_ids,'shared_normal');normal_ids.add(ni)
86:         start=28+16*len(new)+12*ni;mask[start:start+12]=True
87:     need(not any(v.normal_index in normal_ids for fi,f in enumerate(nl[1].faces) if fi not in incident for v in f.vertices),'external_normal')
88:     need(np.array_equal(np.frombuffer(sb[1],np.uint8)[~mask],np.frombuffer(nb[1],np.uint8)[~mask]),'unauthorized_bytes_changed')
89:     need(bit_equal(old[:,[0,2]],new[:,[0,2]]),'xz_changed')
90:     # Old B3 authorization against d130 is re-established independently.
91:     prior_mask=np.zeros(len(sb[1]),bool)
92:     for n in selected:
93:         need(og[n]['ids']==ng[n]['ids']==rg[n]['ids'] and og[n]['faces']==ng[n]['faces']==rg[n]['faces'],'component_members')
94:         for i in og[n]['ids']:prior_mask[28+16*i:28+16*i+12]=True
95:         for ni in og[n]['normals']:
96:             start=28+16*len(old)+12*ni;prior_mask[start:start+12]=True
97:     need(np.array_equal(np.frombuffer(sb[1],np.uint8)[~prior_mask],np.frombuffer(rb[1],np.uint8)[~prior_mask]),'baseline_outside_domain')
98:     pair_count=exact_pairs(new,ng)
99:     full_old=np.concatenate([np.asarray([p.coords for p in l.points]).reshape(-1,3) for l in sl]);full_new=np.concatenate([np.asarray([p.coords for p in l.points]).reshape(-1,3) for l in nl])
100:     need(bit_equal([old.min(0),old.max(0)],[new.min(0),new.max(0)]) and bit_equal([full_old.min(0),full_old.max(0)],[full_new.min(0),full_new.max(0)]),'bbox_changed')
101:     errors=[]
102:     for n in selected:
103:         top=ref[rg[n]['top']];normal=np.cross(top[1]-top[0],top[2]-top[0]);need(abs(normal[1])>1e-10,'reference_vertical_roof')
104:         for i in ng[n]['ids']:
105:             expect=top[0,1]-(normal[0]*(new[i,0]-top[0,0])+normal[2]*(new[i,2]-top[0,2]))/normal[1]
106:             if i not in ng[n]['top']:expect-=180/512
107:             error=abs(new[i,1]-expect);need(error<=1e-6,'reference_plane');errors.append(float(error))
108:     origin=np.asarray(origin,float);centre=np.asarray(centre,float);matrix=np.asarray(matrix,float)
109:     bind(origin.shape==centre.shape==(3,) and matrix.shape==(12,) and np.isfinite(np.r_[origin,centre,matrix]).all(),'frame_shape')
110:     bind(np.array_equal(matrix[:9],[1,0,0,0,1,0,0,0,1]) and bit_equal(origin+centre,matrix[9:]),'pose_frame')
111:     local=(new-centre).astype('<f4');world=(local.astype(float)+matrix[9:]).astype('<f4');source_world=(new+origin).astype('<f4')
112:     need(bit_equal(world,source_world),'world_frames')
113:     need(bit_equal([(old-centre).astype('<f4').min(0),(old-centre).astype('<f4').max(0)],[local.min(0),local.max(0)]),'predicted_bbox_changed')
114:     contacts=contact_rows(new,ng,selected,targets,origin)
115:     fields=('id','local_margin_m','world_float32_margin_m','witness_component')
116:     need(contacts==[{k:row[k] for k in fields} for row in previous['contacts']],'contact_receipt_changed')
117:     triangles=np.asarray([[world[v.point_index] for v in f.vertices] for f in nl[1].faces],float)
118:     cross=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);roof=triangles[cross[:,1]<-1e-10]
119:     bed=vertices(nl[0],[f for f in nl[0].faces if 'water_streambed.rvmat' not in f.material])+origin
120:     over=overlay(bed,roof);need(all(over['checks'].values()),'overlay')
121:     return dict(status='OFFLINE_CANDIDATE_ONLY',changed_y=len(seen),incident_faces=len(incident),incident_normals=len(normal_ids),exact_mlod_pairs=pair_count,geometry_counts=list(expected_counts),maximum_plane_error_m=max(errors),world_frames_bit_exact=True,source_and_predicted_bbox_exact=True,protected_bytes_exact=True,contacts=contacts,overlay=over,limits='Fixed-frame MLOD calculation only; no new ODOL, compiler centre, package or native certification.')
122: 
123: def main():
124:     ap=argparse.ArgumentParser();ap.add_argument('contract',type=Path);ap.add_argument('candidate',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
125:     meter.STARTED=START;meter.MAX_SECONDS=180;stop=meter.bounded(a.output)
126:     try:
127:         contract_sha=meter.sha(a.contract)
128:         try:c=json.loads(a.contract.read_bytes())
129:         except Exception as e:raise Inconclusive('contract_read:'+str(e)) from e
130:         bind(c['schema']=='B3D_NUMERIC_MLOD_V1' and c['expected_counts']==[9120,12160,1520] and c['expected_changes']==17,'contract_schema')
131:         for key in ('source','reference','witness','previous_report','original_result','prior_contract'):bind(c[key] in c['pins'],'unpinned_'+key)
132:         for p,h in c['pins'].items():bind(meter.sha(p)==h,'input_changed:'+p)
133:         witness=json.loads(Path(c['witness']).read_bytes());bind_contract(c,witness,json.loads(Path(c['prior_contract']).read_bytes()))
134:         candidate_sha=meter.sha(a.candidate)
135:         original_controls(json.loads(Path(c['original_result']).read_bytes()),c['targets'],c['origin'])
136:         report=verify(c['source'],a.candidate,c['reference'],witness,c['selected_components'],c['origin'],c['centre'],c['matrix'],c['targets'],json.loads(Path(c['previous_report']).read_bytes()))
137:         bind(meter.sha(a.candidate)==candidate_sha,'candidate_changed_during_read')
138:         bind(meter.sha(a.contract)==contract_sha,'contract_changed_during_read')
139:         report.update(candidate_sha256=candidate_sha,contract_sha256=contract_sha,measurement=meter.memory())
140:         for p,h in c['pins'].items():bind(meter.sha(p)==h,'input_changed_after:'+p)
141:         meter.dump(a.output/'report.json',report);print(json.dumps(report))
142:     except Exception as e:meter.dump(a.output/'failure.json',dict(status='INCONCLUSIVE' if isinstance(e,(Inconclusive,OSError,KeyError,json.JSONDecodeError)) else 'REJECTED_MLOD',reason=str(e),measurement=meter.memory()));raise
143:     finally:stop.set()
144: 
145: if __name__=='__main__':main()

FILE test_prism_b3_numeric_ev112.py SHA256 870f7fc0e2a94e97527618edead5fdab2ab6f17e529f5e9afd9535878d063955
1: """Saved-file fixtures and negative contracts for B3D; no production models."""
2: from pathlib import Path
3: import copy,io,struct,sys,tempfile,unittest
4: import numpy as np
5: sys.path.insert(0,str(Path(__file__).resolve().parent))
6: from test_prism_contact_b3_ev112 import fixture
7: from prism_b3_numeric_author_ev112 import author,bind_contract as author_bind
8: import verify_prism_b3_numeric_ev112 as v
9: from review_compact_collision_v31 import load,py3d
10: 
11: class SavedConsumer(unittest.TestCase):
12:     def setUp(self):
13:         self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);d=Path(self.tmp.name)
14:         self.source=d/'source.p3d';self.candidate=d/'candidate.p3d';fixture(self.source,(.125,-.25))
15:         _,ls,_=load(self.source);xyz=np.array([p.coords for p in ls[1].points]);ids=[i for i,p in enumerate(xyz) if p[0]==p[2]==0]
16:         self.witness=dict(status='FEASIBILITY_ONLY',witness=[dict(source_index=i,before=xyz[i].tolist(),after=(xyz[i]+[0,2**-25,0]).tolist()) for i in ids])
17:         self.assertEqual(len(ids),2)
18:         self.selected=['Component0001'];self.origin=np.array([8262.,7.,8934.]);self.centre=np.array([0.,.396484375,0.]);self.matrix=[1,0,0,0,1,0,0,0,1,8262.,7.396484375,8934.]
19:         self.targets=[dict(id=700,x=8262.25,z=8934.25),dict(id=723,x=8262.125,z=8934.125)]
20:         self.previous=dict(contacts=[dict(id=700,local_margin_m=.25,world_float32_margin_m=.25,witness_component='Component0001'),dict(id=723,local_margin_m=.125,world_float32_margin_m=.125,witness_component='Component0001')])
21:         self.write()
22: 
23:     def write(self,witness=None):
24:         witness=self.witness if witness is None else witness
25:         blob,r=author(self.source,witness,self.selected,len(witness['witness']));self.candidate.write_bytes(blob);return r
26: 
27:     def check(self,**kw):
28:         args=dict(source=self.source,candidate=self.candidate,reference=self.source,witness=self.witness,selected=self.selected,origin=self.origin,centre=self.centre,matrix=self.matrix,targets=self.targets,previous=self.previous,expected_counts=(18,24,3),expected_changes=2);args.update(kw)
29:         return v.verify(**args)
30: 
31:     def mutate(self,path,fn):
32:         _,ls,_=load(path);fn(ls);m=py3d.P3D();m.lods=ls;stream=io.BytesIO();m.write(stream);path.write_bytes(stream.getvalue())
33: 
34:     def test_saved_nontrivial_pass(self):
35:         r=self.check();self.assertEqual(r['status'],'OFFLINE_CANDIDATE_ONLY');self.assertEqual(r['exact_mlod_pairs'],9);self.assertEqual(r['changed_y'],2)
36:         self.assertTrue(r['world_frames_bit_exact']);self.assertTrue(all(r['overlay']['checks'].values()))
37:         self.assertNotEqual(self.source.read_bytes(),self.candidate.read_bytes())
38: 
39:     def test_noop_entry_rejected_by_both(self):
40:         w=copy.deepcopy(self.witness);w['witness'][0]['after']=w['witness'][0]['before']
41:         with self.assertRaises(ValueError):author(self.source,w,self.selected,2)
42:         with self.assertRaises(ValueError):self.check(witness=w)
43: 
44:     def test_duplicate_index_rejected_by_both(self):
45:         w=copy.deepcopy(self.witness);w['witness'][1]=w['witness'][0]
46:         with self.assertRaisesRegex(ValueError,'witness_index'):author(self.source,w,self.selected,2)
47:         with self.assertRaisesRegex(ValueError,'witness_index'):self.check(witness=w)
48: 
49:     def test_index_outside_component(self):
50:         w=copy.deepcopy(self.witness);w['witness'][0]['source_index']=8
51:         with self.assertRaisesRegex(ValueError,'witness_index'):author(self.source,w,self.selected,2)
52:         with self.assertRaisesRegex(ValueError,'witness_index'):self.check(witness=w)
53: 
54:     def test_wrong_before(self):
55:         w=copy.deepcopy(self.witness);w['witness'][0]['before'][1]+=.125
56:         with self.assertRaisesRegex(ValueError,'witness_before'):author(self.source,w,self.selected,2)
57:         with self.assertRaisesRegex(ValueError,'witness_saved_values'):self.check(witness=w)
58: 
59:     def test_nonrepresentable_after(self):
60:         w=copy.deepcopy(self.witness);w['witness'][0]['after'][1]+=1e-15
61:         with self.assertRaisesRegex(ValueError,'witness_not_float32'):author(self.source,w,self.selected,2)
62:         with self.assertRaisesRegex(ValueError,'witness_not_float32'):self.check(witness=w)
63: 
64:     def test_nan_rejected(self):
65:         w=copy.deepcopy(self.witness);w['witness'][0]['after'][1]=float('nan')
66:         with self.assertRaisesRegex(ValueError,'witness_finite_shape'):author(self.source,w,self.selected,2)
67:         with self.assertRaisesRegex(ValueError,'witness_finite_shape'):self.check(witness=w)
68: 
69:     def test_xz_witness_not_permitted(self):
70:         w=copy.deepcopy(self.witness);w['witness'][0]['after'][0]=.125
71:         with self.assertRaisesRegex(ValueError,'witness_not_y_change'):author(self.source,w,self.selected,2)
72:         with self.assertRaises(ValueError):self.check(witness=w)
73: 
74:     def test_omitted_base_fails_exact_thickness_below_old_tolerance(self):
75:         w=copy.deepcopy(self.witness);w['witness']=[r for r in w['witness'] if r['before'][1]==0.]
76:         self.assertEqual(len(w['witness']),1);self.write(w)
77:         with self.assertRaisesRegex(ValueError,'exact_mlod_thickness'):self.check(witness=w,expected_changes=1)
78: 
79:     def test_missing_witness_record(self):
80:         w=copy.deepcopy(self.witness);w['witness'].pop()
81:         with self.assertRaisesRegex(ValueError,'witness_count'):self.check(witness=w)
82: 
83:     def test_point_flag_untouched(self):
84:         h,ls,bs=load(self.candidate);g=bytearray(bs[1]);g[28+12]^=1;bs[1]=bytes(g);self.candidate.write_bytes(h+b''.join(bs))
85:         with self.assertRaisesRegex(ValueError,'unauthorized_bytes_changed'):self.check()
86: 
87:     def test_visual_changed(self):
88:         self.mutate(self.candidate,lambda ls:setattr(ls[0].points[0],'coords',(0.,.1,0.)))
89:         with self.assertRaisesRegex(ValueError,'non_geometry_changed'):self.check()
90: 
91:     def test_tagg_byte_changed(self):
92:         self.mutate(self.candidate,lambda ls:setattr(ls[1].points[0],'mass',3.))
93:         with self.assertRaisesRegex(ValueError,'unauthorized_bytes_changed'):self.check()
94: 
95:     def test_normal_inverted(self):
96:         self.mutate(self.candidate,lambda ls:ls[1].facenormals.__setitem__(0,tuple(-np.array(ls[1].facenormals[0]))))
97:         with self.assertRaisesRegex(ValueError,'normal_error'):self.check()
98: 
99:     def test_unrelated_normal_bytes_changed(self):
100:         def edit(ls):ls[1].facenormals[20]=tuple(np.array(ls[1].facenormals[20])+[1e-7,0,0])
101:         self.mutate(self.candidate,edit)
102:         with self.assertRaisesRegex(ValueError,'unauthorized_bytes_changed'):self.check()
103: 
104:     def test_receipt_margin_one_ulp_changed(self):
105:         receipt=copy.deepcopy(self.previous);receipt['contacts'][0]['local_margin_m']=float(np.nextafter(np.float64(.25),np.float64(1)))
106:         with self.assertRaisesRegex(ValueError,'contact_receipt_changed'):self.check(previous=receipt)
107: 
108:     def test_original_labels_and_positions(self):
109:         original=dict(rows=[dict(id=t['id'],expected=dict(**t,expect='dry' if t['id']==700 else 'wet')) for t in self.targets])
110:         v.original_controls(original,self.targets,self.origin.tolist())
111:         changed=copy.deepcopy(original);changed['rows'][1]['expected']['expect']='dry'
112:         with self.assertRaisesRegex(ValueError,'original_controls_changed'):v.original_controls(changed,self.targets,self.origin.tolist())
113:         moved=copy.deepcopy(self.targets);moved[1]['x']+=.001
114:         with self.assertRaisesRegex(ValueError,'original_controls_changed'):v.original_controls(original,moved,self.origin.tolist())
115: 
116:     def test_overlay_violation_with_identical_visual_lods(self):
117:         def raise_visual(ls):
118:             for p in ls[0].points:p.coords=tuple(np.array(p.coords)+[0,.03,0])
119:         self.mutate(self.source,raise_visual);self.write()
120:         with self.assertRaisesRegex(ValueError,'overlay'):self.check()
121: 
122:     def test_bad_counts_inconclusive(self):
123:         with self.assertRaises(v.Inconclusive):self.check(expected_counts=(19,24,3))
124: 
125:     def test_trailer_inconclusive(self):
126:         with self.candidate.open('ab') as f:f.write(b'X')
127:         with self.assertRaises(v.Inconclusive):self.check()
128: 
129:     def test_pose_mismatch_inconclusive(self):
130:         matrix=self.matrix.copy();matrix[10]+=.01
131:         with self.assertRaises(v.Inconclusive):self.check(matrix=matrix)
132: 
133:     def test_bbox_extremum_rejected(self):
134:         _,ls,_=load(self.source);xyz=np.array([p.coords for p in ls[1].points]);ids=[i for i,p in enumerate(xyz) if p[0]==-10 and p[2]==-20]
135:         w=dict(status='FEASIBILITY_ONLY',witness=[dict(source_index=i,before=xyz[i].tolist(),after=(xyz[i]+[0,2**-20,0]).tolist()) for i in ids])
136:         self.assertEqual(len(ids),2);selected=['Component0002'];blob,_=author(self.source,w,selected,2);self.candidate.write_bytes(blob)
137:         with self.assertRaisesRegex(ValueError,'bbox_changed'):self.check(witness=w,selected=selected)
138: 
139:     def test_exact_thickness_still_rejects_world_discrepancy(self):
140:         base=struct.unpack('<f',struct.pack('<I',0xbed90e97))[0];top=base+180/512
141:         def flatten_first(ls):
142:             for i,p in enumerate(ls[1].points[:6]):p.coords=(p.coords[0],top if i<3 else base,p.coords[2])
143:             for p in ls[0].points[:3]:p.coords=(p.coords[0],top,p.coords[2])
144:             for f in ls[1].faces:
145:                 tri=np.array([ls[1].points[x.point_index].coords for x in f.vertices]);n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);n/=np.linalg.norm(n)
146:                 for x in f.vertices:ls[1].facenormals[x.normal_index]=tuple(n)
147:         self.mutate(self.source,flatten_first);_,ls,_=load(self.source);xyz=np.array([p.coords for p in ls[1].points]);ids=[i for i,p in enumerate(xyz) if p[0]==1 and p[2]==0]
148:         w=dict(status='FEASIBILITY_ONLY',witness=[dict(source_index=i,before=xyz[i].tolist(),after=(xyz[i]+[0,2**-25,0]).tolist()) for i in ids])
149:         self.write(w)
150:         with self.assertRaisesRegex(ValueError,'world_frames'):self.check(witness=w)
151: 
152:     def test_authoritative_contract_binding(self):
153:         prior=dict(candidate_mlod='S',source_control='R',offline_proof='P',original_result='O',origin=self.origin.tolist(),matrix=self.matrix,targets=self.targets,selected_components=self.selected,pins={x:x+'hash' for x in 'SRPO'})
154:         witness=dict(centre_fixed=self.centre.tolist(),translation_fixed=self.matrix[9:])
155:         contract=dict(source='S',reference='R',previous_report='P',original_result='O',witness='W',prior_contract='C',centre=self.centre.tolist(),origin=self.origin.tolist(),matrix=self.matrix,targets=self.targets,selected_components=self.selected,pins={**prior['pins'],'C':'5df5009176342658eb7b31c7c099e643c9e99cc898d2a14f319858a9df391244','W':'6e3653bb35321a72eee1c583c9345e7c8e27cc1d63340f192da4c0a238ce7028'})
156:         for check in (v.bind_contract,author_bind):
157:             check(contract,witness,prior)
158:             for field,value in [('source','R'),('selected_components',['Component0002']),('centre',[0,0,0])]:
159:                 bad=copy.deepcopy(contract);bad[field]=value
160:                 with self.assertRaises(ValueError):check(bad,witness,prior)
161:             for key in ('C','W'):
162:                 bad=copy.deepcopy(contract);bad['pins'][key]='bad'
163:                 with self.assertRaises(ValueError):check(bad,witness,prior)
164: 
165: if __name__=='__main__':unittest.main()

HELPER verify_prism_contact_b3_ev112.py
23: def original_controls(original, targets, origin):
24:     retained = [row['expected'] for row in original['rows'] if row['id'] in (700, 723)]
25:     wanted = [dict(id=v['id'], x=v['x'], z=v['z']) for v in retained]
26:     require(len(retained) == 2 and {v['id']: v['expect'] for v in retained} == {700: 'dry', 723: 'wet'} and
27:             targets == wanted and origin == [8262., 7., 8934.], 'original_controls_changed')
28: 
29: def components(lod):
30:     xyz = np.asarray([p.coords for p in lod.points], float)
31:     pids = {id(p): i for i, p in enumerate(lod.points)}
32:     fids = {id(f): i for i, f in enumerate(lod.faces)}
33:     groups, used_points, used_faces, used_normals = {}, [], [], []
34:     for label, sel in lod.selections.items():
35:         ids, fs = [pids[id(p)] for p in sel.points], [fids[id(f)] for f in sel.faces]
36:         require(len(ids) == 6 and len(fs) == 8, 'component_family')
37:         pairs = {}
38:         for i in ids:
39:             pairs.setdefault(tuple(xyz[i, [0, 2]]), []).append(i)
40:         require(len(pairs) == 3 and all(len(v) == 2 for v in pairs.values()), 'vertical_pairing')
41:         top = []
42:         for pair in pairs.values():
43:             lo, hi = sorted(pair, key=lambda i: xyz[i, 1])
44:             require(abs(xyz[hi, 1] - xyz[lo, 1] - 180 / 512) <= 1e-6, 'thickness')
45:             top.append(hi)
46:         tri = vertices(lod, [lod.faces[i] for i in fs])
47:         closure = closed_component(tri)
48:         require(closure['closed'] and closure['signed_volume'] < 0, 'closed_winding')
49:         ns = []
50:         for fi, t in zip(fs, tri):
51:             face = lod.faces[fi]
52:             require(len(face.vertices) == 3 and all(v.point_index in ids for v in face.vertices), 'face_membership')
53:             nids = {v.normal_index for v in face.vertices}
54:             require(len(nids) == 1, 'normal_mapping')
55:             ni = next(iter(nids))
56:             n = np.cross(t[1] - t[0], t[2] - t[0])
57:             require(np.linalg.norm(n) > 1e-9, 'degenerate_face')
58:             n /= np.linalg.norm(n)
59:             require(np.linalg.norm(n - lod.facenormals[ni]) <= 1e-6, 'normal_error')
60:             require(((xyz[ids] - t[0]) @ n).min() >= -1e-6, 'nonconvex')
61:             ns.append(ni)
62:         groups[label] = dict(ids=ids, faces=fs, normals=ns, top=top,
63:                              polygon=Polygon(xyz[top][:, [0, 2]]))
64:         used_points += ids
65:         used_faces += fs
66:         used_normals += ns
67:     require(sorted(used_points) == list(range(len(lod.points))) and
68:             sorted(used_faces) == list(range(len(lod.faces))) and
69:             sorted(used_normals) == list(range(len(lod.facenormals))), 'unique_assignment')
70:     require(np.isfinite(xyz).all(), 'nonfinite')

HELPER review_compact_collision_v31.py
16: def load(path):
17:     data=Path(path).read_bytes();f=io.BytesIO(data);header=f.read(12);lods=[];blobs=[]
18:     for _ in range(4):
19:         start=f.tell();lods.append(py3d.LOD(f));blobs.append(data[start:f.tell()])
20:     if f.tell()!=len(data):raise ValueError('unexpected model trailer')
21:     return header,lods,blobs
22: 
23: 
24: def vertices(lod,faces):
25:     return np.array([[lod.points[v.point_index].coords for v in face.vertices] for face in faces])

PLAN adjudicado
100: visuales yC1 siguen abiertos. El council ampliado continúa en cola tras lo previo.
101: 
102: ## Adjudicación del plan — Fable5.1 nativo151.5s
103: 
104: SOUND-with-fixes, fuentes intactas. F1 aceptado tras medición propia: d130
105: 4560/4560pares exactos por resta Fraction (el guard histórico seleccionado
106: no demostraba por sí solo los1508 componentes restantes). El consumidor nuevo
107: exigirá grosor exacto en TODOS los4560pares del candidato guardado. Fuera de
108: los12componentes, identidad de bytes con c769/d130, comprobada por consumidor.
109: F2 aceptado: validación independiente de before/after representables float32,
110: bit-diferenciaY no vacía, XZ idénticos, índices únicos/autorizados, antes igual
111: a c769. Rechazar entrada redundante, NaN y un testigo parcial/fuente distinta.
112: F3 RECHAZADO por evidencia:17/36pares del testigo tienen grosor local recentrado
113: NO exacto; todos tienen grosor MLOD exacto y ambos marcos mundiales bit-idénticos.
114: Ese filtro adicional ya fue refutado y eliminado en B3C (H1:30válidos vs17).
115: No era condición previa ni motivo del testigo. Se reportarán grosores local y
116: mundial; no imponer un requisito nuevo ni relajar el MLOD exacto aprobado.
117: F4 aceptado: márgenes local/mundial y witness_component700/723 exactamente
118: iguales al recibo B3 sellado6b29e213; computados de nuevo desde archivo guardado.
119: F5 aceptado: Inconclusive para binding/lectura/cabeceras/EOF/conteos/recursos;
120: Rejected para violaciones geométricas/de máscara/contrato del testigo.
121: El consumidor no importa autor ni solver. Máscara desde caras/índices leídos,
122: no lista del autor. Dominio descubierto propio:17Y,50caras/50normales incidentes
123: sin compartir con caras exteriores. Techos MLOD winding negativoY, como antes.
124: Fixture sintético guardado positivo no trivial; candidato real se escribe UNA
125: vez tras code review y tests. No ejecutar el autor real como test y repetirlo.
126: Controles alterados/TAGG/margen1ULP/grosorresiduo/no-op se añaden a los negativos.
127: Preflight oficial sigue SyntaxError línea213; comprobación directaP:montada,
128: DZ/scripts,AddonBuilder yjunctionMods presentes. No se modificó skill gobernada.
129: Diag de ruta común Exp no encontrado; no se acredita entorno de ejecución;
130: esta unidad sólo autoría MLOD offline, ningún build niDayZ.