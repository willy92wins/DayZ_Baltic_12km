Delegar JUICIO: revision de codigo B3E2 nuevo. Una lane Claude Fable5.1 nativo CLI2.1.310 sondeado hoy; identidad real debe figurar en recibo. Codex es executor/integrator y adjudica. Read-only, sin tools/hijos/escrituras, sin git. Entrega <=850palabras180s, SOUND/SOUND-with-fixes/NEEDS-WORK, hallazgos concretos con lineas/fix y FIN_REVISION. No council aun. Plan ya revisado y adjudicado; revisa diff nuevo frente a ese plan. Tests iniciales21PASS8.109s incluyendo hijo real que escribe PBO independiente, lector real, gate real positivo/negativo, arbol propio observado y retirado. No pareja real, preflight ni DayZ ejecutados en esta unidad. B3E original agotó preflight60s; no se cambia presupuesto. Nuevo padre usa run_tree sellado, hijo stdlib aislado para comprobaciones oficiales y hashes. Mismo consumidor geométrico sellado36bce0... sin relajar igualdad/tolerancias. B3D pins hereda packer/model_config/3lectores/psutil; nuevos lzo/lzss y modulos cargados. Padre crea contrato NUEVO mismo esquema geometrico. Rutas son identidad privada solo; publicacion no binarios. Context consumidor verifica esquema,pins,OFFLINE=b445,PROOF=ae5e,PRIOR=5df,CANDIDATE=f2b7,transitivos,4560pares y controles originales. Consume escribe census completo1520, control gate primero y candidato solo si control certificado, tambien prueba Visual/Memory/Roadway,bbox,overlay±.02/.01,margen700dry723wet. No exactitud de grosor local recentrado: no estaba aprobada. Run_tree sellado Popen no-window, PID/create_time propio, muestreo.1s RSS/arbol, guarda running/receipt y mata solo identidades propias si timeout; no promise hijos cortos no observados. Fail rc/deadline levanta RuntimeError. Nuevo wrapper postverifica retornos tardios. Observa errores de paths/binding/control que impidan ejecucion o falsos PASS. Evita especular causa historica. Ninguna autorizacion para201/native. No pedir re-revision de historia.

FILE build_prism_b3e2_ev112.py
1: """B3E2 continuation: fresh approval/output, isolated preflight, same binary gates."""
2: from pathlib import Path
3: import hashlib,json,os,sys,time,traceback
4: HERE=Path(__file__).resolve().parent;W=HERE.parent.parent;sys.path.insert(0,str(HERE))
5: import build_prism_b3e_ev112 as base
6: import preflight_b3e2_ev112 as flight
7: import preflight_read_discovery_ev112 as reads
8: gate=base.gate;R=base.R;sha=base.sha;dump=reads.dump
9: READER=Path('C:/temp/moto_lanes/review_g3/tools')
10: EXTRA={'lzo_decompress.py':'5ecb852cca9f38258121e2b5246ff8ba438d672b04390442e2e536bc080b8658','lzss_decompress.py':'be3fdf6d38794494cc657639215823fb64035e8d0b26701a6fa0122b0f613898'}
11: HELPERS={HERE/'build_prism_b3e_ev112.py':'914bef55add8016bec4e82996863a647520d1aa016a67bf7529b5fca94861eaa',HERE/'prism_b3e_compiled_ev112.py':'36bce0d822621e5879179243591d028ed9ae9c09f40c624d6b755db768b9a5eb',HERE/'water_constraint_diagnostic_ev112.py':'a3fe3afd08a516428a7de72251bdad6b175fd6f9d469306d9dcbf11cb709ff45',HERE/'preflight_read_discovery_ev112.py':'308438e6aee0a0a744e2f7f83e5c0c22efe1c15f46f057052a8638bfd40be6a6'}
12: HELPERS[HERE/'road_asset_catalog_ev112.py']='fb8ac8972e834c21084b2f22c6dd7409daeb052c6c466d97a6ea4929ad5f0427'
13: 
14: def checked_approval(path,output):
15:     a=json.loads(path.read_bytes());gate.bind(a['schema']=='B3E2_EXECUTION_V1' and a['status']=='REVIEW_ADJUDICATED_TESTS_PASS','approval_schema')
16:     gate.bind(Path(a['output']).resolve()==output.resolve(),'approval_output')
17:     required=[Path(__file__),HERE/'preflight_b3e2_ev112.py',HERE/'consume_prism_b3e2_ev112.py',HERE/'test_prism_b3e2_ev112.py',W/'plans/ev112-b3e-build-continuation-20261028.md']
18:     for p in required:gate.bind(str(p) in a['pins'],'approval_missing:'+str(p))
19:     for p,h in a['pins'].items():gate.bind(sha(p)==h,'approval_changed:'+p)
20:     for p,h in HELPERS.items():gate.bind(sha(p)==h,'helper_changed:'+str(p))
21:     for key in ('review_adjudication','tests'):
22:         gate.bind(a[key] in a['pins'],'approval_receipt:'+key)
23:     suite=flight.pinned_json(Path(a['tests']),a['pins'][a['tests']])
24:     gate.bind(suite['status']=='TESTS_PASS' and suite['tests']>0 and suite['seconds']<=120,'approval_tests')
25:     for p in required[:-1]:gate.bind(suite['postimages'].get(str(p))==a['pins'][str(p)],'suite_postimage:'+str(p))
26:     return a
27: 
28: def enforce_receipt(result,elapsed,limit):
29:     gate.bind(result['returncode']==0 and result['stop_reason'] is None,'process_failed')
30:     gate.bind(elapsed<=limit and result['seconds']<=limit,'process_deadline')
31:     gate.bind(result['peak_sampled_tree_rss_bytes']<=2*1024**3,'process_memory')
32: 
33: def run_process(command,log,seconds):
34:     start=time.monotonic();result=base.run_tree(command,W,log,seconds);enforce_receipt(result,time.monotonic()-start,seconds);return result
35: 
36: def linked_failure(output,exc,phase):
37:     child=output/phase/'report.json';link=None
38:     if child.is_file():
39:         raw=child.read_bytes();link=dict(path=str(child),sha256=hashlib.sha256(raw).hexdigest())
40:         try:link['status']=json.loads(raw)['status']
41:         except Exception as error:link['read_error']=type(error).__name__+':'+str(error)
42:     dump(output/'execution-failure.json',dict(status='INCONCLUSIVE_EXECUTION',phase=phase,type=type(exc).__name__,reason=str(exc),gate_or_preflight=link,traceback=traceback.format_exc(),note='Child status is preserved, not reclassified.'))
43: 
44: def make_contract(pre,approval,approval_path,pre_path):
45:     dpath=R/'prism-b3d-execution-20261028/contract.json';ppath=R/'prism-b3d-consumer-20261028/report.json';priorpath=R/'prism-b3-binary-replay-20261028/contract-r1.json'
46:     d=flight.pinned_json(dpath,gate.OFFLINE);flight.pinned_json(ppath,gate.PROOF);prior=flight.pinned_json(priorpath,gate.PRIOR)
47:     pins=dict(d['pins']);gate.check_pins(dict(pins=pins))
48:     extra={**pre['pins'],**{str(p):h for p,h in HELPERS.items()},**{str(READER/n):h for n,h in EXTRA.items()},**approval['pins']}
49:     # The sealed B3D contract already includes the psutil package bytes.
50:     gate.bind(any('dry-road-build-dependencies-20261028' in p for p in pins),'missing_dependency_pins')
51:     for p in [dpath,ppath,priorpath,R/'prism-b3d-candidate-20261028/candidate.p3d',pre_path,approval_path]:extra[str(p)]=sha(p)
52:     for p,h in extra.items():gate.bind(p not in pins or pins[p]==h,'inherited_pin_conflict:'+p);gate.bind(sha(p)==h,'input_changed:'+p);pins[p]=h
53:     config=base.model_config([dict(model='baltic_stream_pilot\\'+gate.old.NAME)]).encode('ascii')
54:     c=dict(schema='B3E_COMPILED_V1',offline_contract=str(dpath),offline_proof=str(ppath),prior_contract=str(priorpath),source_control=d['reference'],candidate_mlod=str(R/'prism-b3d-candidate-20261028/candidate.p3d'),original_result=d['original_result'],pins=pins,config_sha256=hashlib.sha256(config).hexdigest())
55:     for k in ('origin','matrix','centre','targets','selected_components'):c[k]=d[k]
56:     for k in ('baseline_odol','baseline_pbo','poses'):c[k]=prior[k]
57:     return c,config
58: 
59: def sequence(build,check):
60:     build('control');check('control');build('candidate');check('candidate')
61: 
62: def execute(approval_path,output):
63:     approval=checked_approval(approval_path,output);output.mkdir(exist_ok=False);phase='preflight';emit=reads.Events(output/'events.jsonl')
64:     try:
65:         gate.bind(base.psutil.__version__=='7.2.2' and Path(base.psutil.__file__).resolve().is_relative_to(R/'dry-road-build-dependencies-20261028'),'psutil_binding')
66:         emit(phase);image=reads.interpreter_image()
67:         run_process([str(image),'-I','-S',str(HERE/'preflight_b3e2_ev112.py'),str(output/'preflight')],output/'preflight-driver.log',60)
68:         pre=json.loads((output/'preflight/report.json').read_bytes());gate.bind(pre['status']=='FRESH_PREFLIGHT_B3E2','preflight_status')
69:         identity=json.loads((output/'preflight-driver.running.json').read_bytes());gate.bind(pre['measurement']['pid']==identity['pid'],'preflight_process_identity')
70:         checked_approval(approval_path,output)
71:         c,config=make_contract(pre,approval,approval_path,output/'preflight/report.json');contract=output/'contract.json';dump(contract,c);contract_sha=sha(contract);gate.context(contract)
72:         receipts=[]
73:         def stable():gate.check_pins(c);gate.bind(sha(contract)==contract_sha,'contract_changed')
74:         def build(side):
75:             nonlocal phase
76:             phase=side;emit('build',side=side);stable();folder=output/side/'source/baltic_stream_pilot';folder.mkdir(parents=True,exist_ok=False)
77:             source=Path(c['source_control'] if side=='control' else c['candidate_mlod']);(folder/gate.old.NAME).write_bytes(source.read_bytes());(folder/'config.cpp').write_bytes(config);(folder/'$PBOPREFIX$').write_bytes(b'baltic_stream_pilot')
78:             gate.bind(sha(folder/gate.old.NAME)==c['pins'][str(source)],'copied_source')
79:             result=run_process(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(W/'tools/water/pack_continuous_stream_pilot_v31.ps1'),'-Pilot',str(output/side)],output/side/'driver.log',150)
80:             _,props,entries=gate.old.read_pbo(output/side/'packed/baltic_stream_pilot.pbo')
81:             gate.bind(set(entries)=={gate.old.NAME,'config.bin'} and props['prefix']=='baltic_stream_pilot' and entries[gate.old.NAME].startswith(b'ODOL'),'build_payload')
82:             (output/side/'saved-odol.p3d').write_bytes(entries[gate.old.NAME]);stable()
83:             result.update(side=side,odol_sha256=sha(output/side/'saved-odol.p3d'),pbo_sha256=sha(output/side/'packed/baltic_stream_pilot.pbo'),config_sha256=hashlib.sha256(entries['config.bin']).hexdigest());dump(output/side/'receipt.json',result);receipts.append(result)
84:         def check(side):
85:             nonlocal phase
86:             phase=side+'-gate';emit('gate',side=side);stable();dest=output/phase
87:             run_process([sys.executable,'-I',str(HERE/'consume_prism_b3e2_ev112.py'),side,str(contract),str(output),str(READER),str(dest)],output/(phase+'.log'),180)
88:             report=json.loads((dest/'report.json').read_bytes());gate.bind(report['contract_sha256']==contract_sha and report['status']==('CONTROL_B3E_CERTIFIED' if side=='control' else 'COMPILED_B3E_CONDITIONAL'),'gate_result');stable()
89:         sequence(build,check)
90:         gate.bind(receipts[0]['config_sha256']==receipts[1]['config_sha256'],'pair_config_changed')
91:         dump(output/'completion.json',dict(status='COMPILED_B3E_CONDITIONAL',contract_sha256=contract_sha,proof_sha256=sha(output/'candidate-gate/report.json'),builds=receipts,no_package201_or_dayz=True))
92:     except Exception as exc:linked_failure(output,exc,phase);raise
93: 
94: def main():
95:     import argparse
96:     ap=argparse.ArgumentParser();ap.add_argument('approval',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();execute(a.approval,a.output)
97: 
98: if __name__=='__main__':main()

FILE preflight_b3e2_ev112.py
1: """Fresh official checks in an isolated stdlib child, with durable phase markers."""
2: import time
3: START=time.monotonic()
4: from pathlib import Path
5: import argparse,contextlib,importlib.util,json,os,sys,traceback
6: HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
7: import preflight_read_discovery_ev112 as reads
8: import water_constraint_diagnostic_ev112 as meter
9: R=reads.ROOT
10: ORIGINAL='9f8786a5f37b6b2abbd206bce51d4cad44d58536e766b97fd93bae692804c9a7'
11: ARCHIVED='5fb698727b6c70e8dfa21267963b54cafa60b1ade8b4df3ebfe6b8124e5fc7f2'
12: 
13: def pinned_json(path,expected):
14:     raw=path.read_bytes();reads.require(__import__('hashlib').sha256(raw).hexdigest()==expected,'receipt_hash:'+str(path));return json.loads(raw)
15: 
16: def run(output):
17:     emit=reads.Events(output/'events.jsonl');pins={};emit('external_receipts')
18:     old=pinned_json(reads.RECEIPTS[0][1],reads.RECEIPTS[0][2]);prior=pinned_json(reads.RECEIPTS[1][1],reads.RECEIPTS[1][2])
19:     for _,p,h in reads.RECEIPTS:pins[str(p)]=h
20:     src,fixed=reads.SOURCES
21:     for p,h in [(src,ORIGINAL),(fixed,ARCHIVED)]:
22:         reads.require(meter.sha(p)==h,'source_hash:'+str(p));pins[str(p)]=h
23:     a=src.read_text();b=fixed.read_text();reads.require(b.replace("        r'subst P:","        'subst P:")==a,'literal_diff')
24:     try:compile(a,str(src),'exec');syntax='original_compiles'
25:     except SyntaxError as e:syntax=f'{type(e).__name__}:line{e.lineno}:{e.msg}'
26:     emit('import_official');spec=importlib.util.spec_from_file_location('b3e2_official',fixed);pf=importlib.util.module_from_spec(spec);spec.loader.exec_module(pf)
27:     with (output/'official-checks.log').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
28:         emit('check_p_drive');reads.require(pf.check_p_drive(),'p_drive');log.flush();os.fsync(log.fileno())
29:         for name in ('check_dayz_tools','check_dayz_diag','check_vanilla_data','check_workshop_deploy'):
30:             emit(name);getattr(pf,name)();log.flush();os.fsync(log.fileno())
31:         emit('validate_p_mods');reads.require(pf.validate_p_mods() is None,'mods_junction')
32:         emit('find_tools');tools=pf.find_dayz_tools();reads.require(str(tools)==old['tools_root'],'tools_root')
33:     for p in ('P:/DZ','P:/bin','P:/core','P:/scripts'):
34:         emit('dependency',path=p);reads.require(Path(p).is_dir(),'dependency:'+p)
35:     expected=dict(old['tools_sha256'])
36:     for p in [tools/'Bin/Binarize/Binarize.exe',Path('P:/bin/config.cpp')]:
37:         key=str(p);reads.require(key in prior['pins'],'missing_prior_pin:'+key);h=prior['pins'][key]
38:         reads.require(key not in expected or expected[key]==h,'pin_conflict:'+key);expected[key]=h
39:     for p,h in expected.items():
40:         emit('tool_hash',path=p);row,_=reads.read_hash(Path(p),p,emit);reads.require(row['sha256']==h,'tool_changed:'+p);pins[p]=h
41:     emit('recheck_inputs')
42:     for p,h in pins.items():reads.require(meter.sha(p)==h,'changed_during_preflight:'+p)
43:     measured=meter.memory();reads.require(measured['seconds']<=60 and max(measured['peak_resident_bytes'],measured['peak_commit_bytes'])<=2*1024**3,'resource_budget')
44:     return dict(status='FRESH_PREFLIGHT_B3E2',tools_root=str(tools),pins=pins,original_parse=syntax,native_environment_certified=False,installed_skill_modified=False,measurement=measured)
45: 
46: def main():
47:     ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
48:     meter.STARTED=START;meter.MAX_SECONDS=60;meter.MAX_BYTES=2*1024**3;stop=meter.bounded(a.output)
49:     try:r=run(a.output);reads.dump(a.output/'report.json',r);return 0
50:     except Exception as e:reads.dump(a.output/'report.json',dict(status='INCONCLUSIVE_PREFLIGHT',type=type(e).__name__,reason=str(e),traceback=traceback.format_exc()));return 2
51:     finally:stop.set()
52: 
53: if __name__=='__main__':raise SystemExit(main())

FILE consume_prism_b3e2_ev112.py
1: """Pin loaded reader modules before the unchanged B3E binary consumer."""
2: from pathlib import Path
3: import argparse,hashlib,importlib,json,sys,time,traceback
4: START=time.monotonic();HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
5: from road_asset_catalog_ev112 import READER_PINS
6: import prism_b3e_compiled_ev112 as gate
7: 
8: def bind_reader(root,pins):
9:     for name,expected in READER_PINS.items():
10:         path=root/name
11:         gate.bind(str(path) in pins and pins[str(path)]==expected and gate.meter.sha(path)==expected,'reader_pin:'+name)
12:     sys.path.insert(0,str(root));importlib.import_module('odol_reader')
13:     for name in READER_PINS:
14:         module=sys.modules.get(Path(name).stem)
15:         gate.bind(module is not None and Path(module.__file__).resolve()==(root/name).resolve(),'loaded_reader_path:'+name)
16: 
17: def main():
18:     ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['control','candidate']);ap.add_argument('contract',type=Path);ap.add_argument('pair',type=Path);ap.add_argument('reader',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
19:     gate.meter.STARTED=START;gate.meter.MAX_SECONDS=180;stop=gate.meter.bounded(a.output)
20:     try:
21:         c,_=gate.context(a.contract);bind_reader(a.reader,c['pins'])
22:         r=gate.consume(a.mode,a.contract,a.pair,a.reader,a.output);r['loaded_reader_modules_bound']=True
23:         gate.meter.dump(a.output/'report.json',r);return 0
24:     except Exception as e:
25:         status=gate.failure_status(e);gate.meter.dump(a.output/'report.json',dict(status=status,type=type(e).__name__,reason=str(e),details=getattr(e,'details',None),traceback=traceback.format_exc(),measurement=gate.meter.memory()));return 1 if status=='REJECTED_BINARY' else 2
26:     finally:stop.set()
27: 
28: if __name__=='__main__':raise SystemExit(main())

FILE test_prism_b3e2_ev112.py
1: """Continuation acceptance: real children/readers and independent geometric fixtures."""
2: from pathlib import Path
3: import copy,hashlib,json,struct,subprocess,sys,tempfile,types,unittest
4: from unittest import mock
5: sys.path.insert(0,str(Path(__file__).resolve().parent))
6: import build_prism_b3e2_ev112 as b
7: import consume_prism_b3e2_ev112 as c
8: from test_prism_b3e_ev112 import fixture
9: from test_prism_b3_binary_ev112 import IDENTITY
10: g=b.gate
11: 
12: class Receipts(unittest.TestCase):
13:     def test_hash_before_json(self):
14:         with tempfile.TemporaryDirectory() as td:
15:             p=Path(td)/'receipt';p.write_bytes(b'not json')
16:             with self.assertRaisesRegex(Exception,'receipt_hash'):b.flight.pinned_json(p,'0'*64)
17:             with self.assertRaises(json.JSONDecodeError):b.flight.pinned_json(p,b.sha(p))
18:     def test_saved_receipt_and_mutation(self):
19:         with tempfile.TemporaryDirectory() as td:
20:             p=Path(td)/'receipt';p.write_bytes(b'{"n":9}');h=b.sha(p)
21:             self.assertEqual(b.flight.pinned_json(p,h),dict(n=9));p.write_bytes(b'{"n":8}')
22:             with self.assertRaisesRegex(Exception,'receipt_hash'):b.flight.pinned_json(p,h)
23:     def make(self,root):
24:         here=root/'tools/quality';here.mkdir(parents=True);(root/'plans').mkdir()
25:         paths=[here/n for n in ('build.py','preflight_b3e2_ev112.py','consume_prism_b3e2_ev112.py','test_prism_b3e2_ev112.py')]+[root/'plans/ev112-b3e-build-continuation-20261028.md']
26:         for p in paths:p.write_bytes(b'fixture')
27:         suite=root/'suite.json';b.dump(suite,dict(status='TESTS_PASS',tests=1,seconds=1,postimages={str(p):b.sha(p) for p in paths[:-1]}))
28:         review=root/'review.md';review.write_text('Adjudicated fixture')
29:         a=dict(schema='B3E2_EXECUTION_V1',status='REVIEW_ADJUDICATED_TESTS_PASS',output=str(root/'out'),tests=str(suite),review_adjudication=str(review),pins={str(p):b.sha(p) for p in paths+[suite,review]})
30:         return a,paths,here
31:     def run_approval(self,root,change=None):
32:         a,paths,here=self.make(root)
33:         if change:change(a,paths)
34:         p=root/'approval.json';b.dump(p,a)
35:         with mock.patch.multiple(b,__file__=str(paths[0]),HERE=here,W=root,HELPERS={}):return b.checked_approval(p,root/'out')
36:     def test_approval_bound_positive(self):
37:         with tempfile.TemporaryDirectory() as td:self.assertEqual(self.run_approval(Path(td))['schema'],'B3E2_EXECUTION_V1')
38:     def test_wrong_schema_or_output(self):
39:         for key,value in [('schema','B3E'),('output','elsewhere')]:
40:             with self.subTest(key=key),tempfile.TemporaryDirectory() as td,self.assertRaises(g.Inconclusive):self.run_approval(Path(td),lambda a,p:a.update({key:value}))
41:     def test_missing_source_pin(self):
42:         with tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(g.Inconclusive,'approval_missing'):self.run_approval(Path(td),lambda a,p:a['pins'].pop(str(p[2])))
43:     def test_changed_source(self):
44:         with tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(g.Inconclusive,'approval_changed'):self.run_approval(Path(td),lambda a,p:p[0].write_bytes(b'changed'))
45:     def test_missing_review_receipt(self):
46:         with tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(g.Inconclusive,'approval_receipt'):self.run_approval(Path(td),lambda a,p:a['pins'].pop(a['review_adjudication']))
47:     def test_zero_tests_or_late_suite(self):
48:         for field,value in [('tests',0),('seconds',120.001),('status','RESOURCE_FAIL')]:
49:             def change(a,p):
50:                 q=Path(a['tests']);r=json.loads(q.read_bytes());r[field]=value;b.dump(q,r);a['pins'][str(q)]=b.sha(q)
51:             with self.subTest(field=field),tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(g.Inconclusive,'approval_tests'):self.run_approval(Path(td),change)
52:     def test_stale_suite_postimage(self):
53:         def change(a,p):p[0].write_bytes(b'new source');a['pins'][str(p[0])]=b.sha(p[0])
54:         with tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(g.Inconclusive,'suite_postimage'):self.run_approval(Path(td),change)
55:     def test_late_zero_return_and_memory(self):
56:         base=dict(returncode=0,stop_reason=None,seconds=.1,peak_sampled_tree_rss_bytes=1)
57:         b.enforce_receipt(base,.2,1)
58:         for update,elapsed in [({},1.01),({'seconds':1.01},.2),({'returncode':2},.2),({'stop_reason':'timeout'},.2),({'peak_sampled_tree_rss_bytes':2*1024**3+1},.2)]:
59:             with self.subTest(update=update),self.assertRaises(g.Inconclusive):b.enforce_receipt({**base,**update},elapsed,1)
60: 
61: class GateOrder(unittest.TestCase):
62:     def setUp(self):
63:         self.od,self.ml=fixture();self.patch=mock.patch.object(g.old,'EXPECTED_COUNTS',(12,16,2));self.patch.start();self.addCleanup(self.patch.stop)
64:     def control(self,compiled=None):return g.gate_control(self.od,self.od if compiled is None else compiled,self.ml,IDENTITY,[0,0,0],[dict(id=700,x=.25,z=.25)],lambda row:None)
65:     def test_real_gate_positive_then_candidate(self):
66:         events=[]
67:         def build(side):events.append(side+'build')
68:         def check(side):
69:             if side=='control':self.assertEqual(self.control()['status'],'CONTROL_B3E_CERTIFIED')
70:             events.append(side+'gate')
71:         b.sequence(build,check);self.assertEqual(events,['controlbuild','controlgate','candidatebuild','candidategate'])
72:     def test_real_gate_fail_no_candidate_and_new_failure_link(self):
73:         bad=copy.deepcopy(self.od);bad.lods[1].faces[0].vertex_indices.reverse()
74:         with tempfile.TemporaryDirectory() as td:
75:             root=Path(td)
76:             def build(side):(root/side).mkdir()
77:             def check(side):
78:                 dest=root/(side+'-gate');dest.mkdir()
79:                 try:self.control(bad)
80:                 except Exception as e:
81:                     b.dump(dest/'report.json',dict(status=g.failure_status(e)));raise
82:             with self.assertRaises(g.Inconclusive) as caught:b.sequence(build,check)
83:             b.linked_failure(root,caught.exception,'control-gate');r=json.loads((root/'execution-failure.json').read_bytes())
84:             self.assertEqual(r['gate_or_preflight']['status'],'INCONCLUSIVE_BINARY');self.assertEqual(r['gate_or_preflight']['sha256'],b.sha(root/'control-gate/report.json'));self.assertFalse((root/'candidate').exists())
85:     def test_geometry_rejection_link_preserved(self):
86:         with tempfile.TemporaryDirectory() as td:
87:             root=Path(td);(root/'candidate-gate').mkdir();b.dump(root/'candidate-gate/report.json',dict(status='REJECTED_BINARY'))
88:             b.linked_failure(root,RuntimeError('child nonzero'),'candidate-gate');self.assertEqual(json.loads((root/'execution-failure.json').read_bytes())['gate_or_preflight']['status'],'REJECTED_BINARY')
89:     def test_missing_report_does_not_become_pass(self):
90:         with tempfile.TemporaryDirectory() as td:
91:             root=Path(td);b.linked_failure(root,RuntimeError('terminated'),'control-gate');r=json.loads((root/'execution-failure.json').read_bytes());self.assertIsNone(r['gate_or_preflight']);self.assertEqual(r['status'],'INCONCLUSIVE_EXECUTION')
92:     def test_config_mutation_between_phases_prevents_candidate(self):
93:         with tempfile.TemporaryDirectory() as td:
94:             root=Path(td);p=root/'config.cpp';p.write_bytes(b'original');pins={str(p):b.sha(p)}
95:             def build(side):g.check_pins(dict(pins=pins));(root/side).mkdir()
96:             def check(side):self.control();p.write_bytes(b'mutated')
97:             with self.assertRaises(g.Inconclusive):b.sequence(build,check)
98:             self.assertFalse((root/'candidate').exists())
99: 
100: class ReaderAndChildren(unittest.TestCase):
101:     def test_reader_missing_pin(self):
102:         with self.assertRaisesRegex(g.Inconclusive,'reader_pin'):c.bind_reader(Path('missing'),{})
103:     def test_loaded_shadow_rejected(self):
104:         with tempfile.TemporaryDirectory() as td:
105:             root=Path(td);p=root/'odol_reader.py';p.write_bytes(b'#fixture');pins={str(p):b.sha(p)}
106:             with mock.patch.object(c,'READER_PINS',{'odol_reader.py':b.sha(p)}),mock.patch.dict(sys.modules,{'odol_reader':types.SimpleNamespace(__file__=str(root/'shadow.py'))}),self.assertRaisesRegex(g.Inconclusive,'loaded_reader_path'):c.bind_reader(root,pins)
107:     def test_loaded_matching_module(self):
108:         with tempfile.TemporaryDirectory() as td:
109:             root=Path(td);p=root/'odol_reader.py';p.write_bytes(b'#fixture');pins={str(p):b.sha(p)}
110:             with mock.patch.object(c,'READER_PINS',{'odol_reader.py':b.sha(p)}),mock.patch.dict(sys.modules,{'odol_reader':types.SimpleNamespace(__file__=str(p))}):c.bind_reader(root,pins)
111:     def test_real_child_writes_independent_pbo_fixture(self):
112:         # Plain PBO layout from the format: header, entry, terminator, body.
113:         with tempfile.TemporaryDirectory() as td:
114:             root=Path(td);p=root/'x.pbo';payload=b'ODOL'+bytes(12)
115:             raw=b'\0'+struct.pack('<5I',0x56657273,0,0,0,0)+b'prefix\0fixture\0\0'+b'model.p3d\0'+struct.pack('<5I',0,len(payload),0,0,len(payload))+b'\0'+bytes(20)+payload
116:             cmd=[str(b.reads.interpreter_image()),'-I','-S','-c','from pathlib import Path;import sys;Path(sys.argv[1]).write_bytes(bytes.fromhex(sys.argv[2]))',str(p),raw.hex()]
117:             r=b.run_process(cmd,root/'child.log',10);_,props,entries=g.old.read_pbo(p)
118:             self.assertEqual(props['prefix'],'fixture');self.assertEqual(entries,{'model.p3d':payload});self.assertEqual(r['returncode'],0)
119:     def test_observed_descendant_prevents_early_success_and_is_retired(self):
120:         with tempfile.TemporaryDirectory() as td:
121:             root=Path(td);childfile=root/'child.json'
122:             code="import subprocess,sys,time,json;from pathlib import Path;p=subprocess.Popen([sys.executable,'-I','-S','-c','import time;time.sleep(20)']);Path(sys.argv[1]).write_text(json.dumps({'pid':p.pid}));time.sleep(.7)"
123:             with self.assertRaises(RuntimeError):b.run_process([str(b.reads.interpreter_image()),'-I','-S','-c',code,str(childfile)],root/'tree.log',2)
124:             r=json.loads((root/'tree.receipt.json').read_bytes());pid=json.loads(childfile.read_bytes())['pid'];matching=[x for k,x in r['observed_processes'].items() if k.startswith(str(pid)+'@')]
125:             self.assertEqual(r['stop_reason'],'timeout');self.assertEqual(len(matching),1)
126:             try:p=b.base.psutil.Process(pid);self.assertTrue(p.create_time()!=matching[0]['create_time'] or not p.is_running())
127:             except b.base.psutil.NoSuchProcess:pass
128:     def test_consumer_cli_invalid_and_output_reuse(self):
129:         with tempfile.TemporaryDirectory() as td:
130:             root=Path(td);p=root/'bad.json';p.write_bytes(b'{bad');dest=root/'out'
131:             command=[sys.executable,'-I',str(Path(c.__file__)),'control',str(p),str(root/'pair'),str(root/'reader'),str(dest)]
132:             r=subprocess.run(command,capture_output=True,timeout=15);self.assertEqual(r.returncode,2);report=dest/'report.json';self.assertEqual(json.loads(report.read_bytes())['status'],'INCONCLUSIVE_BINARY');raw=report.read_bytes()
133:             r=subprocess.run(command,capture_output=True,timeout=15);self.assertNotEqual(r.returncode,0);self.assertEqual(report.read_bytes(),raw)
134: 
135: if __name__=='__main__':unittest.main()

FILE ev112-b3e-build-continuation-20261028.md
1: # B3E2 — completar preflight y ejecutar la pareja pendiente
2: 
3: Estado: REVISADO_PARA_IMPLEMENTAR. Codex ejecutor/integrador.
4: Nuevo intento acotado; no relanzar el CLI ni la carpeta B3E consumidos.
5: 
6: La sonda de lectura nueva confirmó9lecturas/7archivos con hashes externos,
7: 0.641s de hijo,16tests finales. No demuestra causa del timeout previo60.047s
8: ni sustituye las comprobaciones oficiales. B3E anterior no llegó a compilar.
9: 
10: ## Alcance y trazabilidad
11: 
12: Mismo producto P2/P8/P9/P11 y contrato geométrico B3E revisado. Control d130,
13: candidato B3D f2b7, proof ae5e, contrato b445, cadena5df; no autoría nueva.
14: Preservar Visual/Memory/Roadway,201modelos,poses,controles700dry/723wet,
15: 4560pares exactos MLOD, plano1e-6, overlay±.02/.01, bits mundiales incluso
16: signedzero y censo1520completo. No exigir grosor local exacto no aprobado.
17: Resultado sólo COMPILED_B3E_CONDITIONAL o rechazo/inconcluso; no motor/paquete201.
18: 
19: ## Implementación propuesta
20: 
21: [EXACT] build_prism_b3e_ev112.py sha914bef55add8016bec4e82996863a647520d1aa016a67bf7529b5fca94861eaa
22: contiene run_tree,preflight,sequence y execute. El CLI/execute original quedan
23: consumidos. prism_b3e_compiled_ev112.py sha36bce0d822621e5879179243591d028ed9ae9c09f40c624d6b755db768b9a5eb
24: es consumidor publicado; sus41fixtures ya pasaron y no necesitan repetirse por rutina.
25: 
26: [DESIGN] Preparador nuevo, con aprobación/plan y carpeta exclusivos. Importar sólo
27: primitivas publicadas; no modificar fuentes selladas. Separar los pasos oficiales
28: del preflight y sellado de hashes mediante eventos flush+fsync; todo el preflight
29: mantiene60s/2GiB. Verificar hash externo de recibos ANTES de confiar en sus campos.
30: Reusar la copia local con arreglo literal archivado5fb69872, comprobando el diff
31: con el original9f8786a5; no tocar la skill gobernada. No bootstrap/montaje/reparación
32: de entorno. Diag ausente no es permiso nativo; requisito de build ausente bloquea.
33: 
34: Fijar nueva aprobación con postimágenes de preparador, consumidor, tests nuevos,
35: este plan y recibos de revisión/suite. Copiar contrato de parentesco, no reemplazar
36: pins históricos por lo que se observe. Crear una pareja de fuentes nuevas con
37: config idéntica; primero compilar control, releer PBO/ODOL y pasar gate_control;
38: únicamente entonces compilar candidato y consumirlo con gate B3E sin cambios.
39: No invocar solver, editor ni preparadores antiguos. No repetir la sonda diagnóstica.
40: 
41: El preparador nuevo debe conservar orden de fases, devolución de fallos geométricos,
42: pinning transitivo y outputs antes/después. Observar únicamente procesos propios
43: por PID/create_time; evidenciar cierre y distinguir hashes instalados de procesos
44: realmente observados. Cualquier fallo conserva recibos; nada de reintentos internos.
45: 
46: ## Validación y presupuesto
47: 
48: Una revisión de este plan180s; código180s y suite120s para los cambios nuevos.
49: Fixtures contra consumidores: aprobación ajena/ausente, recibo de preflight cambiado,
50: control fallido impide candidato, deadline pese a retorno0 tardío, fuentes/config
51: mutadas entre pasos, propagación de rechazo e INCONCLUSIVE sin falso PASS.
52: No basta un mock que repita la implementación: comparar contrato/manifest contra
53: pins publicados y hacer prueba positiva/negativa del consumidor real sobre fixture.
54: 
55: Una ejecución: preflight60s/2GiB; control150s/2GiB; gatecontrol180s/2GiB;
56: candidato150s/2GiB; consumidor180s/2GiB. Límites de pared comprobados incluso
57: si la espera devuelve éxito tardío. Si preflight vuelve a agotar60s, parar,
58: conservar fase y reevaluar ruta; no aumentar presupuesto para obtener PASS.
59: Si control rechaza, no compilar candidato. Si geometría rechaza, no barrer parámetros.
60: 
61: No DayZ/lease/201/despliegue. Original2658 sigue47FAIL/21inciertos; RAM,nueve
62: regresiones,C1sinrevisar y calidadglobal abiertas. Carreteras siguen como preparación
63: independiente: catálogo A y planes de corredores, nunca puente por proximidad.
64: 
65: ## Adjudicación de revisión — 28-10
66: 
67: Fable5.1 nativo85.109s, SOUND-with-fixes; entrega íntegra, fuentes intactas.
68: Recibos R/b3e2-build-plan-review-20261028. Se concretan los requisitos:
69: 
70: 1. Antes de parsear recibos: SHA literal354fbb2e5edea80e88521f02cd135ac2f6a7608a14085af5cc088395a542e68e
71:    para preflight histórico;5df50091 para contrato previo, b445 y ae5e completos
72:    desde los pins publicados. No confiar en el hash que se declara a sí mismo.
73: 2. Comprobaciones oficiales en hijo aislado (misma imagen PythonGIS), con PID real,
74:    fases flush+fsync y deadline60s que incluye sellado. No llamada opaca dentro
75:    del orquestador sin recibo. No atribuir causa: F2 del dictamen especula dónde
76:    agotó; el log anterior ya terminó comprobaciones oficiales antes de hashes.
77: 3. Verificar pins transitivos antes de cada fase. F3 parcialmente refutado: contrato
78:    B3D YA fija packer526159a7, model_config8b340a2a y los tres lectores. No duplicar
79:    ni sustituir esos pins por actuales. Añadir lzo/lzss y comprobar módulos cargados
80:    contra las rutas fijadas, como en el catálogo vial. Hash no prueba ejecución.
81: 4. Esquema de aprobación B3E2_EXECUTION_V1 y ruta de salida nueva fijada; exigir plan
82:    B3E2 y preparador nuevo. Rechazar aprobación/entrypoint B3E antiguo, sin prohibir
83:    que se pine el helper antiguo si sólo se importan sus primitivas autorizadas.
84: 5. Tras fallo de un gate, leer sólo su reporte NUEVO si existe y enlazar estado/hash
85:    sin reinterpretación. No leer un reporte preexistente antes de lanzar, como
86:    podría entenderse en F5. Fixture demuestra que no se crea carpeta candidata.
87: 6. Hijo trivial real para prueba de orquestador y PBO fixture aceptado por lector,
88:    además de prueba de consumidor real independiente. Retorno0 fuera de deadline
89:    rechaza; descendiente observado vivo impide cierre y se retira por identidad.
90:    Se mantiene limitación de muestreo, sin promesa de detectar hijos no observados.
91: 
92: No implementación ni pareja ejecutadas aún. Suite/code review nuevos antes de
93: ejecución. No repetir diagnóstico, catálogo, preparador antiguo ni sus revisiones.