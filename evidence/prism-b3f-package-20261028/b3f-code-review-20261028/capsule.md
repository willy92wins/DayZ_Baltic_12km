Delegar JUICIO codigo B3F. Una lane Claude Fable5.1 CLI nativo confirmado hoy2.1.310, identidad modelUsage requerida. Codex executor/integrator adjudica. Read-only sin tools/hijos/escrituras/git. <=180s850palabras SOUND/SOUND-with-fixes/NEEDS-WORK con lineas/fixes y FIN_REVISION. Plan ya revisado62.812s. Nuevo codigo solo composicion201 de ODOL2581 aprobadoB3E2 y baseline ef229 target3514 config20157d0. No geometry authoring/binarize/DayZ/deploy.22tests inicialesPASS5.734s; nuevos tres tests agregados esperan suitefinal. Pure package_identity sellado compara beforeprops==afterprops, prefix, list(before)==list(after),201P3D+config, changed==[NAME],aftertarget==expectedbytes; no consulta CANDIDATE_SHA/ANCHORS, test contrafactual. read_pbo compartido cuerpos limite declarado. Nuevo header guard independiente antesdict detecta duplicados/orden. gate.context sellado revalida pins externos B3D/proof/prior/candidate/transitivos, originalcontrols/pose; no recomputa censos. runtime.run_process (B3E2 sellado) run_tree con Popen oculta/psutil7.2.2 PIDcreate_time, muestreo0.1s RSSdescendientes propios, mata soloidentidadespropias siagotado, guarda running/receipt, retorno0tardio rechaza. No certifica hijos noobservados. Preflight official.run es primitiva reutilizada, noCLI consumido: officialchecks warnNone mas hardgatesP,toolsroot/hash,vanilla dirs,Modsjunction; literalfixsyntax213 archivadoydiffverificado;60s. NuevohijoB3F stdlib usa esa primitiva, agregaPboUtils/disk yreportepropio; no skillgobernadaedit. Padrepreparaciontotal60/pack120/consumer120/2GiB, outer300s techo suma protegiendo RSSparent+child sin ampliar fases. Controles/noislands/moves intactos,47FAIL21inciertos abiertos. Revisa falsosPASS/rechazos/mutacion/manifiestocontratos/primitivas/transitivos; no plantear segundo parsercompleto ni redisenarirrestricto. Presupuesto una composicion, sin reintentos. Si faltan pruebas especificas indicar observables, no tests espejo de texto. Fuentes incluidas son codigo ejecutable salvoplanDESIGN.

FILE C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\tools\quality\prism_b3f_package_ev112.py
1: """Compose and independently consume the one approved ODOL replacement in 201 models."""
2: import time
3: START=time.monotonic()
4: from pathlib import Path
5: import argparse,hashlib,json,struct,sys,traceback
6: HERE=Path(__file__).resolve().parent;W=HERE.parent.parent;sys.path.insert(0,str(HERE))
7: import build_prism_b3e2_ev112 as runtime
8: import preflight_b3f_ev112 as flight
9: from compiled_dry_road_gate_ev112 import package_identity
10: gate=runtime.gate;R=runtime.R;meter=gate.meter;sha=meter.sha;dump=meter.dump
11: NAME='cs_kit_118_0000.p3d';PAIR=R/'prism-b3e2-pair-20261028'
12: BASE=R/'dry-road-final-package-20261028/Addons/baltic_stream_pilot.pbo';BASE_SHA='ef229f3275d4c412d49f208395091e8b91faa5425e06ca2476a699a49bdf1b84'
13: CANDIDATE=PAIR/'candidate/saved-odol.p3d';CANDIDATE_SHA='2581a99ff60f5a6242af55483cce6dd1aa3556cbc36e8a2f1c1488fa08c93545';CONTROL_SHA='351424ab535a3e3eb40fc460a22360ab442776446055b116e10c0ba6134579f5';CONFIG_SHA='57d0d0ae31a33fa329598ce2c17df43fbb8451fd3acc0844467b87fec3a239ca'
14: ANCHORS={BASE:BASE_SHA,CANDIDATE:CANDIDATE_SHA,PAIR/'contract.json':'c3709a1929214e1372fb2026b8d84c8ae83466aa83e033da968fa196a598f8e4',PAIR/'candidate-gate/report.json':'9a541c82274a9cad75c337d734db2d3ab62120a5e8694c3502fc09f9dd841884',PAIR/'control-gate/census.json':'a895ab0375d1c5838c37775e296d393c2f46807481af61f0a91d8b9705c5deea',PAIR/'candidate-gate/census.json':'1ad63bfc09f0a1ff537225028911ceacae45954a8655ffadef17d9b7c8c2467e',W/'evidence/prism-b3e2-compiled-20261028/report.json':'f850319aaae07f415af179235efe9fd52c3c1d879a3546925b938cb85dce3c06'}
15: HELPERS={**runtime.HELPERS,HERE/'build_prism_b3e2_ev112.py':'b131794d75a2748f40dfdd87e5e01389cf6434ca2f9b160253f70f241f538cbb',HERE/'preflight_b3e2_ev112.py':'7b9f2a7191099f7cbc6570954ef1810fbaf890904f291601625d961574a1c447',HERE/'compiled_dry_road_gate_ev112.py':'00a68cabe86628ae9e659bfb6b6779f6efa2ab1fdb184b7731f8e493c7831c6c'}
16: 
17: class Rejected(Exception):pass
18: class Inconclusive(Exception):pass
19: def require(ok,reason):
20:     if not ok:raise Rejected(reason)
21: def bind(ok,reason):
22:     if not ok:raise Inconclusive(reason)
23: digest=lambda data:hashlib.sha256(data).hexdigest()
24: def pins_check(pins):
25:     for p,h in pins.items():bind(sha(p)==h,'pin_changed:'+str(p))
26: 
27: def header(data):
28:     """Independent ordered header guard before the shared body reader collapses dicts."""
29:     offset=0;props=[];names=[];sizes=[];seen_props=set();seen_names=set();extensions=0
30:     def string():
31:         nonlocal offset
32:         end=data.index(b'\0',offset);s=data[offset:end].decode('utf-8');offset=end+1;return s
33:     while True:
34:         name=string();mime,original,reserved,stamp,size=struct.unpack_from('<5I',data,offset);offset+=20
35:         if not name:
36:             if mime==0x56657273:
37:                 extensions+=1;require(extensions==1 and not names,'property_header_position')
38:                 while True:
39:                     k=string()
40:                     if not k:break
41:                     v=string();require(k not in seen_props,'duplicate_property');seen_props.add(k);props.append((k,v))
42:                 continue
43:             require(mime==0 and original==0 and reserved==0 and stamp==0 and size==0,'terminator');break
44:         require(mime==0,'compressed_entry');name=name.replace('\\','/')
45:         require(not name.startswith('/') and ':' not in name and all(s not in ('','.','..') for s in name.split('/')),'unsafe_name')
46:         require(name.lower() not in seen_names,'duplicate_entry');seen_names.add(name.lower());names.append(name);sizes.append(size)
47:     require(extensions==1 and offset+sum(sizes)<=len(data),'truncated_or_missing_header')
48:     return props,names,sizes
49: 
50: def read_package(path):
51:     data=path.read_bytes();props,names,sizes=header(data)
52:     raw,decoded,entries=gate.old.read_pbo(path)
53:     bind(raw==data and decoded==dict(props) and list(entries)==names and [len(v) for v in entries.values()]==sizes,'reader_disagreement')
54:     return props,entries
55: 
56: def compare(before_props,before,after_props,after,candidate):
57:     require(before_props==after_props,'property_sequence')
58:     try:identity=package_identity(dict(before_props),before,dict(after_props),after,candidate)
59:     except ValueError as e:raise Rejected(str(e)) from e
60:     return identity
61: 
62: def census_check(row):
63:     bind(row['status']=='EXACT_CENSUS' and row['compared_components']==row['visited_components']==row['expected_components']==row['observed_components']==1520 and not row['global_errors'] and not row['geometric_failures'] and row['structural_failures']==0,'census_incomplete')
64: 
65: def output_universe(folder):
66:     require(sorted(p.name for p in folder.iterdir())==['baltic_stream_pilot.pbo'],'output_universe')
67:     require((folder/'baltic_stream_pilot.pbo').is_file() and not (folder/'baltic_stream_pilot.pbo').is_symlink(),'output_not_regular')
68: 
69: def context():
70:     pins={str(p):h for p,h in {**ANCHORS,**HELPERS}.items()};pins_check(pins)
71:     j=lambda p:json.loads(p.read_bytes())
72:     old,_=gate.context(PAIR/'contract.json');pins.update(old['pins']);pins_check(pins)
73:     proof=j(PAIR/'candidate-gate/report.json');summary=j(W/'evidence/prism-b3e2-compiled-20261028/report.json')
74:     bind(proof['status']==summary['status']=='COMPILED_B3E_CONDITIONAL','proof_status')
75:     bind(proof['contract_sha256']==summary['contract_sha256']==ANCHORS[PAIR/'contract.json'] and summary['proof_sha256']==ANCHORS[PAIR/'candidate-gate/report.json'] and summary['candidate_odol_sha256']==CANDIDATE_SHA and summary['control_odol_sha256']==CONTROL_SHA,'proof_links')
76:     bind(proof['outputs'].get(str(CANDIDATE))==CANDIDATE_SHA,'proof_output')
77:     for side in ('control','candidate'):
78:         path=PAIR/(side+'-gate/census.json');row=j(path)
79:         census_check(row)
80:     bind(proof['census_sha256']==ANCHORS[PAIR/'candidate-gate/census.json'],'census_proof')
81:     props,entries=read_package(BASE)
82:     bind(digest(entries[NAME])==CONTROL_SHA and digest(entries['config.bin'])==CONFIG_SHA,'baseline_control_config')
83:     candidate=CANDIDATE.read_bytes();bind(digest(candidate)==CANDIDATE_SHA,'candidate_bytes')
84:     expected=entries.copy();expected[NAME]=candidate;compare(props,entries,props,expected,candidate)
85:     return pins,props,entries,candidate
86: 
87: def source_check(folder,expected):
88:     paths=[p for p in folder.rglob('*')]
89:     require(all(not p.is_symlink() and not p.is_junction() for p in paths),'source_link')
90:     actual={p.relative_to(folder).as_posix():p.read_bytes() for p in paths if p.is_file()}
91:     require(list(sorted(actual))==list(sorted(expected)) and actual==expected,'source_bytes')
92: 
93: def approval(path,output):
94:     a=json.loads(path.read_bytes());bind(a['schema']=='B3F_EXECUTION_V1' and a['status']=='REVIEW_ADJUDICATED_TESTS_PASS' and Path(a['output']).resolve()==output.resolve(),'approval')
95:     required=[Path(__file__).resolve(),HERE/'preflight_b3f_ev112.py',HERE/'test_prism_b3f_ev112.py',W/'plans/ev112-b3f-package-composition-20261028.md']
96:     bind(all(str(p) in a['pins'] for p in required),'approval_sources');pins_check(a['pins']);pins_check({str(p):h for p,h in HELPERS.items()})
97:     bind(a['review_adjudication'] in a['pins'] and a['tests'] in a['pins'],'approval_receipts');suite=json.loads(Path(a['tests']).read_bytes())
98:     bind(suite['status']=='TESTS_PASS' and suite['tests']>0 and suite['seconds']<=120 and all(suite['postimages'].get(str(p))==a['pins'][str(p)] for p in required[:-1]),'suite')
99:     return a
100: 
101: def consume(execution,output):
102:     pins,props,before,candidate=context();manifest=json.loads((execution/'manifest.json').read_bytes());pins_check(manifest['pins'])
103:     bind(manifest['schema']=='B3F_COMPOSITION_V1' and all(manifest['pins'].get(p)==h for p,h in pins.items()),'manifest_transitive')
104:     output_universe(execution/'Addons')
105:     expected=before.copy();expected[NAME]=candidate;source_check(execution/'compiled/baltic_stream_pilot',expected)
106:     actual_props,after=read_package(execution/'Addons/baltic_stream_pilot.pbo');identity=compare(props,before,actual_props,after,candidate)
107:     bind(manifest['preflight'] in manifest['pins'],'preflight_unpinned')
108:     pre=json.loads(Path(manifest['preflight']).read_bytes());bind(pre['status']=='FRESH_B3F_PREFLIGHT','preflight_status');bind(flight.inventory(flight.FILEBANK.parent)==pre['pboutils'],'tool_inventory_changed');pins_check(manifest['pins'])
109:     return dict(status='EXPERIMENTAL_B3F_PACKAGE_IDENTITY_PASS_CONDITIONAL',identity=identity,properties=actual_props,pbo_sha256=sha(execution/'Addons/baltic_stream_pilot.pbo'),candidate_sha256=digest(after[NAME]),baseline_sha256=BASE_SHA,config201_sha256=digest(after['config.bin']),manifest_sha256=sha(execution/'manifest.json'),compiled_proof_sha256=ANCHORS[PAIR/'candidate-gate/report.json'],entries={n:digest(v) for n,v in after.items()},measurement=meter.memory(),limits=['No DayZ, deployment, native contact or global acceptance.','Shared read_pbo for bodies; independent header and synthetic writer do not constitute a second full parser.','Installed tool directory identity is not loaded DLL attestation.'])
110: 
111: def execute(approval_path,output):
112:     a=approval(approval_path,output);output.mkdir(exist_ok=False);phase='preflight';emit=runtime.reads.Events(output/'events.jsonl');started=time.monotonic()
113:     try:
114:         emit(phase);runtime.run_process([str(runtime.reads.interpreter_image()),'-I','-S',str(HERE/'preflight_b3f_ev112.py'),str(output/'preflight')],output/'preflight-driver.log',60)
115:         pre_path=output/'preflight/report.json';pre=json.loads(pre_path.read_bytes());identity=json.loads((output/'preflight-driver.running.json').read_bytes());bind(pre['status']=='FRESH_B3F_PREFLIGHT' and pre['measurement']['pid']==identity['pid'],'preflight_identity')
116:         approval(approval_path,output);pins,props,before,candidate=context();pins.update(a['pins']);pins.update(pre['pins']);pins[str(pre_path)]=sha(pre_path);pins[str(approval_path)]=sha(approval_path)
117:         pins_check(pins);expected=before.copy();expected[NAME]=candidate;folder=output/'compiled/baltic_stream_pilot';folder.mkdir(parents=True);dest=output/'Addons';dest.mkdir()
118:         for name,data in expected.items():p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
119:         source_check(folder,expected);bind(flight.inventory(flight.FILEBANK.parent)==pre['pboutils'],'tools_before_pack')
120:         manifest=output/'manifest.json';dump(manifest,dict(schema='B3F_COMPOSITION_V1',pins=pins,preflight=str(pre_path)));manifest_sha=sha(manifest)
121:         bind(time.monotonic()-started<=60,'preparation_deadline');measured=meter.memory();bind(max(measured['peak_resident_bytes'],measured['peak_commit_bytes'])<=2*1024**3,'preparation_memory')
122:         args=[str(flight.FILEBANK)]
123:         for key,value in props:args+=['-property',key+'='+value]
124:         phase='pack';emit(phase);receipt=runtime.run_process(args+['-dst',str(dest),str(folder)],output/'pack.log',120)
125:         source_check(folder,expected);pins_check(pins);bind(sha(manifest)==manifest_sha,'manifest_changed');bind(flight.inventory(flight.FILEBANK.parent)==pre['pboutils'],'tools_after_pack')
126:         phase='consumer';emit(phase);runtime.run_process([sys.executable,'-I',str(Path(__file__).resolve()),'consume',str(output),str(output/'consumer')],output/'consumer.log',120)
127:         result=json.loads((output/'consumer/report.json').read_bytes());bind(result['status']=='EXPERIMENTAL_B3F_PACKAGE_IDENTITY_PASS_CONDITIONAL' and result['manifest_sha256']==manifest_sha,'consumer_status');pins_check(pins)
128:         dump(output/'completion.json',dict(status=result['status'],pbo_sha256=result['pbo_sha256'],proof_sha256=sha(output/'consumer/report.json'),manifest_sha256=manifest_sha,pack=receipt,no_deployment_or_dayz=True))
129:     except Exception as e:runtime.linked_failure(output,e,phase);raise
130: 
131: def main():
132:     ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['execute','consume']);ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
133:     if a.mode=='execute':execute(a.input,a.output);return 0
134:     a.output.mkdir(exist_ok=False);meter.STARTED=START;meter.MAX_SECONDS=120;meter.MAX_BYTES=2*1024**3;stop=meter.bounded(a.output)
135:     try:dump(a.output/'report.json',consume(a.input,a.output));return 0
136:     except Exception as e:
137:         status='REJECTED_PACKAGE' if isinstance(e,Rejected) else 'INCONCLUSIVE_PACKAGE';dump(a.output/'report.json',dict(status=status,type=type(e).__name__,reason=str(e),traceback=traceback.format_exc()));return 1 if status=='REJECTED_PACKAGE' else 2
138:     finally:stop.set()
139: 
140: if __name__=='__main__':raise SystemExit(main())

FILE C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\tools\quality\preflight_b3f_ev112.py
1: """New B3F stdlib preflight entry; does not invoke a consumed B3E2 CLI."""
2: import time
3: START=time.monotonic()
4: from pathlib import Path
5: import argparse,json,shutil,sys,traceback
6: sys.path.insert(0,str(Path(__file__).resolve().parent))
7: import preflight_b3e2_ev112 as official
8: meter=official.meter
9: FILEBANK=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe')
10: FILEBANK_SHA='f89aaeb22421b9158fbbf173f75d52b6f3de69986cb462e58956c78da82c4caf'
11: 
12: def inventory(directory):
13:     result={}
14:     for p in sorted(directory.rglob('*')):
15:         if p.is_symlink() or p.is_junction():raise ValueError('tool_link:'+str(p))
16:         if p.is_file():result[p.relative_to(directory).as_posix()]=meter.sha(p)
17:     if not result:raise ValueError('empty_tools')
18:     return result
19: 
20: def main():
21:     ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
22:     meter.STARTED=START;meter.MAX_SECONDS=60;meter.MAX_BYTES=2*1024**3;stop=meter.bounded(a.output)
23:     try:
24:         result=official.run(a.output);before=inventory(FILEBANK.parent)
25:         if before.get(FILEBANK.name)!=FILEBANK_SHA:raise ValueError('filebank_identity')
26:         free=shutil.disk_usage(a.output).free
27:         if free<256*1024**2:raise ValueError('staging_disk_space')
28:         result.update(status='FRESH_B3F_PREFLIGHT',pboutils_directory=str(FILEBANK.parent),pboutils=before,free_bytes=free,measurement=meter.memory(),tool_inventory_limit='Installed directory bytes only; not a loaded-DLL attestation.')
29:         if result['measurement']['seconds']>60:raise ValueError('preflight_deadline')
30:         meter.dump(a.output/'report.json',result);return 0
31:     except Exception as e:meter.dump(a.output/'report.json',dict(status='INCONCLUSIVE_PREFLIGHT',type=type(e).__name__,reason=str(e),traceback=traceback.format_exc()));return 2
32:     finally:stop.set()
33: 
34: if __name__=='__main__':raise SystemExit(main())

FILE C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\tools\quality\test_prism_b3f_ev112.py
1: """PBO fixtures written independently of the shared reader and composition code."""
2: from pathlib import Path
3: import hashlib,json,struct,subprocess,sys,tempfile,unittest
4: from unittest import mock
5: sys.path.insert(0,str(Path(__file__).resolve().parent))
6: import prism_b3f_package_ev112 as p
7: import compiled_dry_road_gate_ev112 as legacy
8: 
9: PROPS=[('prefix','baltic_stream_pilot'),('product','dayz ugc')]
10: def sample():
11:     files={p.NAME:b'ODOL control'}
12:     files.update({f'cs_other_{i:04d}.p3d':b'ODOL'+bytes([i]) for i in range(200)})
13:     files['config.bin']=b'\0raP201 configuration';return files
14: def writer(path,props,files):
15:     out=b'\0'+struct.pack('<5I',0x56657273,0,0,0,0)
16:     for k,v in props:out+=k.encode()+b'\0'+v.encode()+b'\0'
17:     out+=b'\0'
18:     for n,v in files.items():out+=n.encode()+b'\0'+struct.pack('<5I',0,len(v),0,123,len(v))
19:     out+=b'\0'+bytes(20)+b''.join(files.values());path.write_bytes(out)
20: 
21: class PboFixtures(unittest.TestCase):
22:     def setUp(self):self.before=sample();self.candidate=b'ODOL approved candidate';self.after={**self.before,p.NAME:self.candidate}
23:     def test_saved_pbo_positive_preserves_201_and_config(self):
24:         with tempfile.TemporaryDirectory() as td:
25:             root=Path(td);writer(root/'before.pbo',PROPS,self.before);writer(root/'after.pbo',PROPS,self.after)
26:             bp,b=p.read_package(root/'before.pbo');ap,a=p.read_package(root/'after.pbo');r=p.compare(bp,b,ap,a,self.candidate)
27:             self.assertEqual(r['unchanged_model_entries'],200);self.assertTrue(r['config_exact']);self.assertEqual(r['changed_entries'],[p.NAME])
28:     def test_wrong_config_extra_missing_and_control_payload(self):
29:         variants=[{**self.after,'config.bin':b'one model config'},{**self.after,'extra.p3d':b'ODOL'},dict(list(self.after.items())[1:]),self.before]
30:         for actual in variants:
31:             with self.subTest(keys=len(actual)),self.assertRaises(p.Rejected):p.compare(PROPS,self.before,PROPS,actual,self.candidate)
32:     def test_entry_order_is_physical(self):
33:         actual=dict(reversed(list(self.after.items())))
34:         with self.assertRaisesRegex(p.Rejected,'PBO_entry_order'):p.compare(PROPS,self.before,PROPS,actual,self.candidate)
35:     def test_extra_or_reordered_properties(self):
36:         for props in [PROPS+[('extra','x')],list(reversed(PROPS)),[('prefix','wrong'),PROPS[1]]]:
37:             with self.subTest(props=props),self.assertRaisesRegex(p.Rejected,'property_sequence'):p.compare(PROPS,self.before,props,self.after,self.candidate)
38:     def test_duplicate_property_rejected_before_dict(self):
39:         with tempfile.TemporaryDirectory() as td:
40:             f=Path(td)/'x.pbo';writer(f,PROPS+[PROPS[0]],self.before)
41:             with self.assertRaisesRegex(p.Rejected,'duplicate_property'):p.read_package(f)
42:     def test_duplicate_casefold_entry_rejected(self):
43:         with tempfile.TemporaryDirectory() as td:
44:             f=Path(td)/'x.pbo';writer(f,PROPS,{'a.p3d':b'x','A.p3d':b'y'})
45:             with self.assertRaisesRegex(p.Rejected,'duplicate_entry'):p.read_package(f)
46:     def test_unsafe_name(self):
47:         with tempfile.TemporaryDirectory() as td:
48:             f=Path(td)/'x.pbo';writer(f,PROPS,{'../escape':b'x'})
49:             with self.assertRaisesRegex(p.Rejected,'unsafe_name'):p.read_package(f)
50:     def test_truncated_body_rejected(self):
51:         with tempfile.TemporaryDirectory() as td:
52:             f=Path(td)/'x.pbo';writer(f,PROPS,self.before);f.write_bytes(f.read_bytes()[:-1])
53:             with self.assertRaisesRegex(p.Rejected,'truncated'):p.read_package(f)
54:     def test_old_candidate_and_anchors_do_not_control_new_identity(self):
55:         with mock.patch.multiple(legacy,CANDIDATE_SHA='unrelated',ANCHORS={'alien':'wrong'}):
56:             self.assertEqual(p.compare(PROPS,self.before,PROPS,self.after,self.candidate)['unchanged_model_entries'],200)
57:     def test_all_copied_files_and_mutated_candidate(self):
58:         with tempfile.TemporaryDirectory() as td:
59:             root=Path(td)
60:             for n,v in self.after.items():(root/n).write_bytes(v)
61:             p.source_check(root,self.after);(root/p.NAME).write_bytes(self.before[p.NAME])
62:             with self.assertRaisesRegex(p.Rejected,'source_bytes'):p.source_check(root,self.after)
63:     def test_unexpected_source_file(self):
64:         with tempfile.TemporaryDirectory() as td:
65:             root=Path(td);(root/'a').write_bytes(b'x');(root/'extra').write_bytes(b'y')
66:             with self.assertRaisesRegex(p.Rejected,'source_bytes'):p.source_check(root,{'a':b'x'})
67: 
68: class Bindings(unittest.TestCase):
69:     def test_census_positive_and_missing_failed_component(self):
70:         row=dict(status='EXACT_CENSUS',compared_components=1520,visited_components=1520,expected_components=1520,observed_components=1520,global_errors=[],geometric_failures=[],structural_failures=0);p.census_check(row)
71:         for key,value in [('status','INCONCLUSIVE'),('compared_components',1519),('visited_components',1519),('observed_components',1521),('global_errors',['missing']),('geometric_failures',['c1335']),('structural_failures',1)]:
72:             with self.subTest(key=key),self.assertRaises(p.Inconclusive):p.census_check({**row,key:value})
73:     def test_output_extra_file_or_folder_rejected(self):
74:         with tempfile.TemporaryDirectory() as td:
75:             root=Path(td);target=root/'baltic_stream_pilot.pbo';target.write_bytes(b'package');p.output_universe(root);(root/'extra').write_bytes(b'other')
76:             with self.assertRaises(p.Rejected):p.output_universe(root)
77:             (root/'extra').unlink();target.unlink();target.mkdir()
78:             with self.assertRaises(p.Rejected):p.output_universe(root)
79:     def test_late_zero_exit_and_rss_limit(self):
80:         r=dict(returncode=0,stop_reason=None,seconds=.1,peak_sampled_tree_rss_bytes=1);p.runtime.enforce_receipt(r,.1,120)
81:         with self.assertRaises(p.gate.Inconclusive):p.runtime.enforce_receipt(r,120.001,120)
82:         with self.assertRaises(p.gate.Inconclusive):p.runtime.enforce_receipt({**r,'peak_sampled_tree_rss_bytes':2*1024**3+1},.1,120)
83:     def test_real_saved_chain_matches_published_witness(self):
84:         pins,props,before,candidate=p.context();self.assertEqual(p.digest(candidate),p.CANDIDATE_SHA);self.assertEqual(p.digest(before[p.NAME]),p.CONTROL_SHA);self.assertEqual(len(before),202)
85:         self.assertEqual(pins[str(p.PAIR/'contract.json')],'c3709a1929214e1372fb2026b8d84c8ae83466aa83e033da968fa196a598f8e4')
86:     def test_foreign_receipt_hash_fails_before_fields(self):
87:         with tempfile.TemporaryDirectory() as td:
88:             f=Path(td)/'proof.json';f.write_bytes(b'{"status":"COMPILED_B3E_CONDITIONAL"}')
89:             with self.assertRaisesRegex(p.Inconclusive,'pin_changed'):p.pins_check({str(f):p.ANCHORS[p.PAIR/'candidate-gate/report.json']})
90:     def test_unknown_inherited_pin_change(self):
91:         with tempfile.TemporaryDirectory() as td:
92:             f=Path(td)/'source';f.write_bytes(b'old');pins={str(f):p.sha(f)};f.write_bytes(b'new')
93:             with self.assertRaises(p.Inconclusive):p.pins_check(pins)
94:     def test_tool_inventory_detects_added_removed_and_changed(self):
95:         with tempfile.TemporaryDirectory() as td:
96:             root=Path(td);f=root/'a.dll';f.write_bytes(b'old');a=p.flight.inventory(root);f.write_bytes(b'new');self.assertNotEqual(a,p.flight.inventory(root));f.write_bytes(b'old');(root/'x.dll').write_bytes(b'extra');self.assertNotEqual(a,p.flight.inventory(root));f.unlink();self.assertNotEqual(a,p.flight.inventory(root))
97:     def test_empty_tool_inventory(self):
98:         with tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(ValueError,'empty_tools'):p.flight.inventory(Path(td))
99:     def test_child_imports_preflight_in_isolated_image(self):
100:         code='import sys;sys.path.insert(0,sys.argv[1]);import preflight_b3f_ev112;print("IMPORT_ONLY")'
101:         r=subprocess.run([str(p.runtime.reads.interpreter_image()),'-I','-S','-c',code,str(p.HERE)],capture_output=True,timeout=10);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout.strip(),b'IMPORT_ONLY')
102:     def approval_fixture(self,root):
103:         here=root/'tools/quality';here.mkdir(parents=True);(root/'plans').mkdir()
104:         files=[here/'package.py',here/'preflight_b3f_ev112.py',here/'test_prism_b3f_ev112.py',root/'plans/ev112-b3f-package-composition-20261028.md']
105:         for f in files:f.write_bytes(b'fixture')
106:         review=root/'review.md';review.write_bytes(b'adjudicated');suite=root/'tests.json';p.dump(suite,dict(status='TESTS_PASS',tests=5,seconds=1,postimages={str(f):p.sha(f) for f in files[:-1]}))
107:         a=dict(schema='B3F_EXECUTION_V1',status='REVIEW_ADJUDICATED_TESTS_PASS',output=str(root/'out'),pins={str(f):p.sha(f) for f in files+[review,suite]},review_adjudication=str(review),tests=str(suite));return a,files,here
108:     def check_approval(self,root,mutate=None):
109:         a,files,here=self.approval_fixture(root)
110:         if mutate:mutate(a,files)
111:         f=root/'approval.json';p.dump(f,a)
112:         with mock.patch.multiple(p,HERE=here,W=root,__file__=str(files[0]),HELPERS={}):return p.approval(f,root/'out')
113:     def test_new_approval_positive(self):
114:         with tempfile.TemporaryDirectory() as td:self.assertEqual(self.check_approval(Path(td))['schema'],'B3F_EXECUTION_V1')
115:     def test_foreign_or_missing_approval(self):
116:         for mutate in [lambda a,f:a.update(schema='B3E2_EXECUTION_V1'),lambda a,f:a.update(output='other'),lambda a,f:a['pins'].pop(str(f[1]))]:
117:             with tempfile.TemporaryDirectory() as td,self.assertRaises(p.Inconclusive):self.check_approval(Path(td),mutate)
118:     def test_approval_cannot_rebind_untested_source(self):
119:         def mutate(a,files):files[0].write_bytes(b'changed');a['pins'][str(files[0])]=p.sha(files[0])
120:         with tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(p.Inconclusive,'suite'):self.check_approval(Path(td),mutate)
121:     def test_zero_tests_not_pass(self):
122:         def mutate(a,files):s=Path(a['tests']);r=json.loads(s.read_bytes());r['tests']=0;p.dump(s,r);a['pins'][str(s)]=p.sha(s)
123:         with tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(p.Inconclusive,'suite'):self.check_approval(Path(td),mutate)
124:     def test_cli_missing_manifest_is_inconclusive_and_cannot_clobber(self):
125:         with tempfile.TemporaryDirectory() as td:
126:             root=Path(td);out=root/'out';cmd=[sys.executable,'-I',str(Path(p.__file__)),'consume',str(root),str(out)]
127:             r=subprocess.run(cmd,capture_output=True,timeout=15);self.assertEqual(r.returncode,2,r.stderr);f=out/'report.json';raw=f.read_bytes();self.assertEqual(json.loads(raw)['status'],'INCONCLUSIVE_PACKAGE')
128:             r=subprocess.run(cmd,capture_output=True,timeout=15);self.assertNotEqual(r.returncode,0);self.assertEqual(f.read_bytes(),raw)
129: 
130: if __name__=='__main__':unittest.main()

FILE C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\plans\ev112-b3f-package-composition-20261028.md
1: # B3F — composición experimental de201 modelos
2: 
3: Estado: REVISADO_PARA_IMPLEMENTAR. Codex ejecutor/integrador.
4: No autoriza ejecución antes de revisión de plan/código y tests. No DayZ ni despliegue.
5: 
6: ## Hipótesis, producto y entradas
7: 
8: P2/P8/P9/P11: trasladar el ODOL que ya preserva geometría y controles al mismo
9: universo de modelos usado por B2, sin rehacer modelos ni mover poses. Sólo
10: composición de un PBO experimental. B3E2 es COMPILED_B3E_CONDITIONAL, no nativo.
11: 
12: [EXACT] Contrato B3E2 c3709a1929214e1372fb2026b8d84c8ae83466aa83e033da968fa196a598f8e4;
13: proof9a541c82274a9cad75c337d734db2d3ab62120a5e8694c3502fc09f9dd841884;
14: candidato ODOL2581a99ff60f5a6242af55483cce6dd1aa3556cbc36e8a2f1c1488fa08c93545,
15: en R/prism-b3e2-pair-20261028/candidate/saved-odol.p3d.
16: Baseline R/dry-road-final-package-20261028/Addons/baltic_stream_pilot.pbo
17: ef229f3275d4c412d49f208395091e8b91faa5425e06ca2476a699a49bdf1b84:
18: descubrimiento sólo lectura28-10 acredita202entradas/201P3D, target351424ab y
19: config.bin57d0d0ae31a33fa329598ce2c17df43fbb8451fd3acc0844467b87fec3a239ca.
20: Es config201, NO el config de la pareja B3E2 de un modelo. Prefijo
21: baltic_stream_pilot, product dayz ugc. Reporte R/b3f-package-input-discovery-20261028.
22: 
23: ## Diseño acotado
24: 
25: [EXACT] tools/quality/compiled_dry_road_gate_ev112.py:164-171 package_identity
26: compara propiedades, orden/universo201, entradaúnica modificada y bytes exactos.
27: tools/playtest/attach_navmesh.py:read_pbo recibe Path. El CLI y compose del viejo
28: package_dry_road_compiled_ev112.py están consumidos y fijan candidato3514:
29: NO invocarlos ni cambiar constantes. Se pueden reutilizar primitivas verificadas.
30: 
31: [DESIGN] Preparador/consumidor/tests nuevos y aprobación específica con pins
32: externos de contrato, proof, ambos census, baseline, candidato y herramientas.
33: Reverificar código/recibos/transitivos antes de leer y tras escribir. Comprobar
34: ambos census EXACT_CENSUS1520 y proof completo, sin recalcular geometría antigua.
35: El candidato copiado debe ser exactamente2581; no lectura desde una ruta de
36: despliegue mutable. La lista ordenada/propiedades y200modelos restantes/config201
37: deben proceder de baseline ef229 y conservar bytes exactos.
38: 
39: Preparar carpeta exclusiva sin junctions ni escrituras P:/Mods. Sustituir
40: únicamente cs_kit_118_0000.p3d. FileBank.exe fijado
41: f89aaeb22421b9158fbbf173f75d52b6f3de69986cb462e58956c78da82c4caf,
42: con argumentos de propiedades leídas; no Binarize/AddonBuilder. Fresh preflight
43: de herramientas y disco para esta fase; no reusar éxito viejo como entorno vivo.
44: La copia local de preflight sólo se ejecutaría desde entrada nueva revisada,
45: sin relanzar CLI/carpeta B3E2 consumidos ni editar skill gobernada.
46: 
47: Releer el PBO escrito con lector fijado. Comparar entradas completas, orden,
48: propiedades, config y200modelos con baseline mediante consumidor independiente;
49: extraer target y hash comparado con el ODOL aprobado. Guardar recibos y árbol
50: de procesos observados; ningún proceso ajeno. Resultado permitido:
51: EXPERIMENTAL_B3F_PACKAGE_IDENTITY_PASS_CONDITIONAL, REJECTED_PACKAGE o
52: INCONCLUSIVE_PACKAGE. Ninguno cierra los47FAIL21inciertos ni certifica juego.
53: 
54: ## Puertas y presupuesto antes de empezar
55: 
56: Revisión plan180s, código180s, suite120s. Una preparación/preflight60s/2GiB,
57: una composición120s/2GiB y un consumo120s/2GiB, sin reintentos internos.
58: Antes de empaquetar, fixtures PBO escritos independientemente positivos y
59: negativos: modelo omitido/extra/orden distinto, config de1modelo sustituido por
60: error, target/control intercambiado, propiedades mutadas, proof/census/contrato
61: ajenos, archivo modificado entre fases, rc0 tardío y fallo de lectura preservado.
62: También integridad transitoria del candidato/200restantes y salida ya existente.
63: 
64: Si no cumple, conservar reporte y parar; no recompilar ni cambiar representación.
65: Tras éxito, plan NATIVO separado: discriminadores basados en evidenciaB2 y
66: controles originales, geometría+poses+paquetes sellados, FIFO oficial y cierre.
67: No repetir2658/B1/B2 ni asumir que estos dos contactos resuelven causa global.
68: 
69: ## Adjudicación de Fable5.1 — 62.812s
70: 
71: Recibos en evidence/b3f-package-plan-review-20261028; revisión consumida.
72: Antes de implementar se fijan estos cierres, sin variar presupuesto ni geometría:
73: 
74: - Baseline target==control ODOL del proof B3E2==351424ab535a3e3eb40fc460a22360ab442776446055b116e10c0ba6134579f5.
75: - Resumen evidence/prism-b3e2-compiled-20261028/report.json:
76:   f850319aaae07f415af179235efe9fd52c3c1d879a3546925b938cb85dce3c06.
77:   Ambos census en R/prism-b3e2-pair-20261028: control-gate/census.json
78:   a895ab0375d1c5838c37775e296d393c2f46807481af61f0a91d8b9705c5deea,
79:   candidate-gate/census.json1ad63bfc09f0a1ff537225028911ceacae45954a8655ffadef17d9b7c8c2467e.
80:   El consumidor liga sus campos con contrato/proof/output, no sólo etiquetas.
81: - Orden FÍSICO de entradas exacto. Guard de cabecera antes de dict: propiedades
82:   en secuencia exacta, sin duplicados, extra ni valores cambiados; fixture propio.
83: - Rehash fuente202entradas antes y tras FileBank, candidato incluido; exigir
84:   Addons/baltic_stream_pilot.pbo como único archivo de ese directorio.
85: - Pinear módulo package_identity; consumir sólo esa función pura y no constantes
86:   CANDIDATE_SHA/ANCHORS históricos. Fixture contrafactual altera esos valores para
87:   comprobar que no intervienen, sin test superficial de texto de implementación.
88: - Inventario de archivos/hashPboUtils antes/después; diferencias rechazan. Es
89:   inventario instalado, no prueba de DLL realmente cargadas. read_pbo compartido
90:   para cuerpos sigue límite; cabecera independiente no es segundo parser completo.

FILE E:\DayZ-Baltic-Build\shape-repair-20261025\run_b3f_execution_20261028.py
1: """Outer 300s/2GiB observed-tree cap; internal 60/120/120 phase caps still apply."""
2: from pathlib import Path
3: import sys,json
4: W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=Path(r'E:/DayZ-Baltic-Build/shape-repair-20261025');sys.path.insert(0,str(W/'tools/quality'))
5: import build_prism_b3e2_ev112 as runtime
6: log=R/'b3f-execution-driver-20261028.log';out=R/'prism-b3f-package-20261028'
7: if log.exists() or out.exists():raise RuntimeError('execution_already_started')
8: r=runtime.run_process([sys.executable,'-I',str(W/'tools/quality/prism_b3f_package_ev112.py'),'execute',str(R/'b3f-execution-approval-20261028.json'),str(out)],log,300)
9: print(json.dumps(r))