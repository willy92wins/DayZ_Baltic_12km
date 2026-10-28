Decisión delegar JUICIO de código a Claude Fable5.1 nativo (CLI2.1.310 sondeado hoy); Codex executor/integrador. Una lane independiente read-only de cápsula, sin herramientas/escrituras/hijos, <=180s <=850palabras. Devuelve SOUND/SOUND-with-fixes/NEEDS-WORK, bugs verificables con líneas/repro/consecuencia/fix, límites. FIN_REVISION al terminar. Sólo bloquean contraejemplos verificables. Plan ya revisado66.25s y adjudicado, código nuevo ahora. Unit tests preliminares están en ejecución; no presumir PASS. Receptor Codex verifica hallazgos y aplica una corrección agrupada antes de suite final30s y una lectura real60s. No DayZ/build/lease ni editarskills. Dos recibos históricos SHA fijos, sólolecturas definidas,9lecturas/7paths+4isdir, primero copia exacta de recibos y luego relectura integridad. No causalidad histórica ni entorno aprobado. Misma chunk4MiB, multiplicidadBinarize/config2, otras1. Windows stdlibctypes: GetProcessTimes HANDLE+4LPFILETIME BOOL y GetModuleFileNameW(NULL,LPWSTR,DWORD) comprobados en Microsoft. GIS sys.executable es launcher; imagen real de proceso GIS es CPython bundled de Codex. Hijo usa esa MISMA imagen con -I -S (sin paquetes) para tener handle del proceso real, no launcher que deje huérfano. Parent por GISenv. Captura PID reportado debeigualhandle, timeoutmedido desdePopen (no ampliar60); killhandlepropio, childno subprocess. Testtimeout exigePIDreal emitidoigualhandle. Revisa falsePASS, controlesdeidentidad/ruta, eventflush,timeout yretirada, bytesinmutables, malformados, salidaexitstatus. No reabrir P3D ni tolerancias. Fuentes completas debajo, anclas de producciónoldtools report contieneexact3tools, actualsourceP:config. No puedes inspeccionar nada fuera de cápsula; declara límites.


FILE preflight_read_discovery_ev112.py
1: """One bounded read-only discovery; never imports preflight or build helpers."""
2: from pathlib import Path
3: import argparse,ctypes,hashlib,json,os,re,subprocess,sys,threading,time,traceback
4: from ctypes import wintypes
5: 
6: ROOT=Path('E:/DayZ-Baltic-Build/shape-repair-20261025')
7: RECEIPTS=(('old',ROOT/'dry-road-build-preflight-20261028/report.json','354fbb2e5edea80e88521f02cd135ac2f6a7608a14085af5cc088395a542e68e'),
8:           ('prior',ROOT/'prism-b3-binary-replay-20261028/contract-r1.json','5df5009176342658eb7b31c7c099e643c9e99cc898d2a14f319858a9df391244'))
9: SOURCES=(Path('C:/Users/guill/.agents/skills/dayz-preflight/preflight.py'),ROOT/'dry-road-build-preflight-20261028/preflight_syntax_repaired.py')
10: TOOLS=('Bin/AddonBuilder/AddonBuilder.exe','Bin/PboUtils/FileBank.exe','Bin/CfgConvert/CfgConvert.exe')
11: LIMIT='Read timings only; neither historical causality nor complete preflight/native readiness.'
12: 
13: class ContractError(ValueError):pass
14: class HashMismatch(ValueError):pass
15: def require(ok,label):
16:     if not ok:raise ContractError(label)
17: def key(p):return os.path.normcase(os.path.abspath(p))
18: def digest_valid(h):return isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h) is not None
19: def dump(path,value):
20:     with Path(path).open('w',encoding='utf-8') as f:
21:         json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
22: 
23: class Events:
24:     def __init__(self,path):self.path=path;self.start=time.monotonic()
25:     def __call__(self,phase,**data):
26:         with self.path.open('a',encoding='utf-8') as f:
27:             f.write(json.dumps(dict(phase=phase,seconds=time.monotonic()-self.start,**data),allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
28: 
29: def read_hash(path,label,emit,keep=False):
30:     start=time.monotonic();emit('read_start',label=label,path=str(path));h=hashlib.sha256();size=0;blocks=[]
31:     with Path(path).open('rb') as f:
32:         while True:
33:             block=f.read(4<<20)
34:             if not block:break
35:             if size==0:emit('first_block',label=label,bytes=len(block))
36:             h.update(block);size+=len(block)
37:             if keep:blocks.append(block)
38:     row=dict(label=label,path=str(path),sha256=h.hexdigest(),bytes=size,seconds=time.monotonic()-start)
39:     emit('read_done',**row);return row,b''.join(blocks) if keep else None
40: 
41: def load_receipts(receipts,out,emit):
42:     result={}
43:     require([r[0] for r in receipts]==['old','prior'],'receipt_names')
44:     for name,path,expected in receipts:
45:         require(digest_valid(expected),'receipt_expected_hash')
46:         row,data=read_hash(path,'receipt_'+name,emit,True)
47:         require(row['sha256']==expected,'receipt_hash:'+name)
48:         (out/('input-'+name+'.json')).write_bytes(data)
49:         try:value=json.loads(data)
50:         except (ValueError,UnicodeError) as e:raise ContractError('receipt_json:'+name) from e
51:         require(isinstance(value,dict),'receipt_object:'+name);result[name]=value
52:     return result
53: 
54: def jobs_from_receipts(old,prior,sources,config):
55:     require(isinstance(old.get('tools_root'),str),'tools_root')
56:     root=Path(old['tools_root']);require(root.is_absolute(),'relative_tools_root')
57:     require(key(old.get('original_source',''))==key(sources[0]),'unexpected_preflight_source')
58:     raw=old.get('tools_sha256');pins=prior.get('pins')
59:     require(isinstance(raw,dict) and isinstance(pins,dict),'receipt_maps')
60:     expected=[root/n for n in TOOLS];normalized={key(p):h for p,h in raw.items()}
61:     require(len(normalized)==len(raw)==3 and set(normalized)=={key(p) for p in expected},'unexpected_tool_path')
62:     result=[('source_original',sources[0],old.get('original_sha256')),('source_archived',sources[1],old.get('local_sha256'))]
63:     result +=[(p.name,p,normalized[key(p)]) for p in expected]
64:     for p in (root/'Bin/Binarize/Binarize.exe',config):
65:         require(str(p) in pins,'missing_prior_pin:'+str(p))
66:         result +=[(p.name+':'+str(i),p,pins[str(p)]) for i in (1,2)]
67:     require(len(result)==9 and all(digest_valid(h) for _,_,h in result),'job_hashes')
68:     return result
69: 
70: def discover(receipts,out,sources,config,dirs,emit):
71:     start=time.monotonic();docs=load_receipts(receipts,out,emit)
72:     jobs=jobs_from_receipts(docs['old'],docs['prior'],sources,config)
73:     for p in dirs:
74:         stamp=time.monotonic();emit('directory_start',path=str(p));present=Path(p).is_dir()
75:         emit('directory_done',path=str(p),is_directory=present,seconds_spent=time.monotonic()-stamp)
76:         require(present,'missing_directory:'+str(p))
77:     rows=[]
78:     for label,p,expected in jobs:
79:         row,_=read_hash(p,label,emit);row['expected_sha256']=expected;rows.append(row)
80:         if row['sha256']!=expected:
81:             emit('hash_mismatch',**row);raise HashMismatch(json.dumps(row))
82:     # Receipts are read again only for integrity, not included in measured tool phases.
83:     for name,p,h in receipts:
84:         row,_=read_hash(p,'post_receipt_'+name,emit);require(row['sha256']==h,'receipt_changed:'+name)
85:     return dict(status='HASHES_MATCH',readings=rows,readings_count=len(rows),distinct_paths=len({key(p) for _,p,_ in jobs}),seconds=time.monotonic()-start,limitation=LIMIT,read_mode='4MiB blocks; instrumentation and fsync included')
86: 
87: def child(output):
88:     require(output.is_dir() and not any((output/n).exists() for n in ('events.jsonl','report.json','input-old.json','input-prior.json')),'child_output_reuse')
89:     emit=Events(output/'events.jsonl')
90:     try:
91:         report=discover(RECEIPTS,output,SOURCES,Path('P:/bin/config.cpp'),[Path('P:/'+n) for n in ('DZ','bin','core','scripts')],emit);code=0
92:     except Exception as e:
93:         status='HASH_MISMATCH' if isinstance(e,HashMismatch) else ('INCONCLUSIVE_IO' if isinstance(e,OSError) else 'INCONCLUSIVE_CONTRACT')
94:         report=dict(status=status,type=type(e).__name__,reason=str(e),traceback=traceback.format_exc(),limitation=LIMIT);code=1
95:     report['pid']=os.getpid();dump(output/'report.json',report);return code
96: 
97: def interpreter_image():
98:     # Same loaded CPython behind the GIS venv, not a PATH/global interpreter.
99:     # Direct image + -I -S avoids the venv launcher creating an unowned child.
100:     kernel=ctypes.WinDLL('kernel32',use_last_error=True);fn=kernel.GetModuleFileNameW
101:     fn.argtypes=[wintypes.HMODULE,wintypes.LPWSTR,wintypes.DWORD];fn.restype=wintypes.DWORD
102:     text=ctypes.create_unicode_buffer(32768);size=fn(None,text,len(text))
103:     require(0<size<len(text),'interpreter_image');return text.value
104: 
105: def creation_time(process):
106:     # Microsoft GetProcessTimes: HANDLE + four LPFILETIME; handle owned by Popen.
107:     # https://learn.microsoft.com/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes
108:     kernel=ctypes.WinDLL('kernel32',use_last_error=True);fn=kernel.GetProcessTimes
109:     fn.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4;fn.restype=wintypes.BOOL
110:     values=[wintypes.FILETIME() for _ in range(4)]
111:     if not fn(int(process._handle),*[ctypes.byref(v) for v in values]):raise ctypes.WinError(ctypes.get_last_error())
112:     return (values[0].dwHighDateTime<<32)|values[0].dwLowDateTime
113: 
114: def launch(command,output,seconds=60):
115:     require(0<seconds<=60,'timeout_range');start=time.monotonic();expired=threading.Event()
116:     with (output/'child.stdout').open('wb') as stdout,(output/'child.stderr').open('wb') as stderr:
117:         p=subprocess.Popen(command,stdout=stdout,stderr=stderr,creationflags=0x08000000)
118:         def timeout():
119:             if p.poll() is None:
120:                 expired.set()
121:                 try:p.kill() # uses this Popen's process handle, never lookup by PID
122:                 except ProcessLookupError:pass
123:         timer=threading.Timer(max(0,seconds-(time.monotonic()-start)),timeout);timer.daemon=True;timer.start()
124:         try:
125:             identity=dict(pid=p.pid,creation_filetime=creation_time(p),max_seconds=seconds,command=command)
126:             dump(output/'identity.json',identity);p.wait(timeout=max(0,seconds-(time.monotonic()-start))+10)
127:         except BaseException:
128:             timeout();p.wait(timeout=10);raise
129:         finally:timer.cancel()
130:     result=dict(status='INCONCLUSIVE_TIMEOUT' if expired.is_set() else 'CHILD_FINISHED',returncode=p.returncode,seconds=time.monotonic()-start,identity=identity)
131:     dump(output/'lifecycle.json',result);return result
132: 
133: def main():
134:     parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);parser.add_argument('--child',action='store_true');args=parser.parse_args()
135:     if args.child:return child(args.output)
136:     args.output.mkdir(exist_ok=False)
137:     lifecycle=launch([interpreter_image(),'-I','-S',str(Path(__file__).resolve()),str(args.output),'--child'],args.output)
138:     if lifecycle['status']=='INCONCLUSIVE_TIMEOUT':report=dict(status='INCONCLUSIVE_TIMEOUT',limitation=LIMIT)
139:     else:
140:         try:
141:             report=json.loads((args.output/'report.json').read_bytes());require(report['status'] in ('HASHES_MATCH','HASH_MISMATCH','INCONCLUSIVE_IO','INCONCLUSIVE_CONTRACT'),'child_status')
142:             require(report['pid']==lifecycle['identity']['pid'],'child_pid_not_owned_handle')
143:             require((lifecycle['returncode']==0)==(report['status']=='HASHES_MATCH'),'exit_status_disagreement')
144:         except Exception as e:report=dict(status='INCONCLUSIVE_CHILD',reason=str(e),limitation=LIMIT)
145:     report['lifecycle']=lifecycle;dump(args.output/'completion.json',report);print(report['status']);return 0 if report['status']=='HASHES_MATCH' else 1
146: 
147: if __name__=='__main__':raise SystemExit(main())

FILE test_preflight_read_discovery_ev112.py
1: from pathlib import Path
2: import copy,hashlib,json,subprocess,sys,tempfile,unittest
3: from unittest import mock
4: sys.path.insert(0,str(Path(__file__).resolve().parent))
5: import preflight_read_discovery_ev112 as d
6: 
7: class Fixture(unittest.TestCase):
8:     def setUp(self):
9:         self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.out=self.root/'out';self.out.mkdir()
10:         self.sources=[self.root/'original.py',self.root/'archived.py'];self.config=self.root/'config.cpp';self.tools=self.root/'Tools';self.dirs=[self.root/'DZ'];self.dirs[0].mkdir();self.events=[]
11:         paths=self.sources+[self.config]+[self.tools/n for n in d.TOOLS]+[self.tools/'Bin/Binarize/Binarize.exe']
12:         for p in paths:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'abc')
13:         self.h='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
14:         self.old=dict(tools_root=str(self.tools),original_source=str(self.sources[0]),original_sha256=self.h,local_sha256=self.h,tools_sha256={str(self.tools/n):self.h for n in d.TOOLS})
15:         self.prior=dict(pins={str(self.tools/'Bin/Binarize/Binarize.exe'):self.h,str(self.config):self.h})
16:         self.receipts=self.save_receipts()
17:     def save_receipts(self):
18:         result=[]
19:         for name,v in [('old',self.old),('prior',self.prior)]:
20:             p=self.root/(name+'.json');p.write_text(json.dumps(v),encoding='utf-8');result.append((name,p,hashlib.sha256(p.read_bytes()).hexdigest()))
21:         return result
22:     def emit(self,phase,**kw):self.events.append(dict(phase=phase,**kw))
23:     def run_discovery(self):return d.discover(self.receipts,self.out,self.sources,self.config,self.dirs,self.emit)
24:     def test_positive_exact_multiplicity_and_unchanged_inputs(self):
25:         original={p:p.read_bytes() for _,p,_ in self.receipts};r=self.run_discovery();self.assertEqual(r['status'],'HASHES_MATCH');self.assertEqual(r['readings_count'],9);self.assertEqual(r['distinct_paths'],7)
26:         self.assertEqual(sum(row['path']==str(self.config) for row in r['readings']),2)
27:         self.assertEqual(sum(row['path'].endswith('Binarize.exe') for row in r['readings']),2)
28:         self.assertTrue(all(p.read_bytes()==data for p,data in original.items()));self.assertTrue(any(e['phase']=='directory_done' for e in self.events))
29:     def test_modified_tool_fails_with_expected_observed(self):
30:         (self.tools/d.TOOLS[1]).write_bytes(b'changed')
31:         with self.assertRaises(d.HashMismatch):self.run_discovery()
32:         row=self.events[-1];self.assertEqual(row['phase'],'hash_mismatch');self.assertEqual(row['expected_sha256'],self.h);self.assertNotEqual(row['sha256'],self.h)
33:     def test_missing_path_is_io_error(self):
34:         self.config.unlink()
35:         with self.assertRaises(FileNotFoundError):self.run_discovery()
36:         self.assertEqual(self.events[-1]['phase'],'read_start')
37:     def test_unexpected_path_rejected_before_tools_read(self):
38:         self.old['tools_sha256'][str(self.root/'unapproved.exe')]=self.old['tools_sha256'].pop(str(self.tools/d.TOOLS[0]));self.receipts=self.save_receipts()
39:         with self.assertRaisesRegex(d.ContractError,'unexpected_tool_path'):self.run_discovery()
40:         self.assertTrue(all(e.get('label','').startswith('receipt_') for e in self.events))
41:     def test_receipt_hash_format_and_schema_fail_closed(self):
42:         bad=list(self.receipts);bad[0]=('old',bad[0][1],'0'*64)
43:         with self.assertRaisesRegex(d.ContractError,'receipt_hash'):d.load_receipts(bad,self.out,self.emit)
44:         self.old['tools_sha256']=[];self.receipts=self.save_receipts()
45:         with self.assertRaisesRegex(d.ContractError,'receipt_maps'):self.run_discovery()
46:         self.old['tools_sha256']={str(self.tools/n):'invalid' for n in d.TOOLS};self.receipts=self.save_receipts()
47:         with self.assertRaisesRegex(d.ContractError,'job_hashes'):self.run_discovery()
48:     def test_malformed_receipt_is_contract_error(self):
49:         p=self.receipts[0][1];p.write_bytes(b'{broken');self.receipts[0]=('old',p,hashlib.sha256(p.read_bytes()).hexdigest())
50:         with self.assertRaisesRegex(d.ContractError,'receipt_json'):self.run_discovery()
51:     def test_permission_failure_not_a_mismatch(self):
52:         op=Path.open
53:         def denied(p,*a,**kw):
54:             if p==self.config:raise PermissionError('fixture')
55:             return op(p,*a,**kw)
56:         with mock.patch.object(Path,'open',denied),self.assertRaises(PermissionError):self.run_discovery()
57:         self.assertFalse(any(e['phase']=='hash_mismatch' for e in self.events))
58:     def test_changed_receipt_after_read_is_inconclusive(self):
59:         def mutate(phase,**kw):
60:             self.emit(phase,**kw)
61:             if phase=='read_done' and kw['label']=='config.cpp:2':self.receipts[0][1].write_bytes(b'{}')
62:         with self.assertRaisesRegex(d.ContractError,'receipt_changed'):d.discover(self.receipts,self.out,self.sources,self.config,self.dirs,mutate)
63:     def test_hash_chunk_boundary(self):
64:         p=self.root/'blocks';data=b'a'*((4<<20)+7);p.write_bytes(data);r,_=d.read_hash(p,'blocks',self.emit)
65:         self.assertEqual(r['sha256'],hashlib.sha256(data).hexdigest());self.assertEqual(r['bytes'],len(data));self.assertEqual(self.events[1]['bytes'],4<<20)
66:     def test_durable_events(self):
67:         path=self.root/'events';event=d.Events(path)
68:         with mock.patch.object(d.os,'fsync',wraps=d.os.fsync) as sync:event('first');event('last')
69:         self.assertEqual(sync.call_count,2);self.assertEqual([json.loads(s)['phase'] for s in path.read_text().splitlines()],['first','last'])
70:     def test_timeout_owned_child_and_persisted_event(self):
71:         code="import os,time; f=open('"+str(self.out/'slow.txt').replace('\\','/')+"','w');f.write(str(os.getpid()));f.flush();os.fsync(f.fileno());time.sleep(20)"
72:         r=d.launch([d.interpreter_image(),'-I','-S','-c',code],self.out,2)
73:         self.assertEqual(r['status'],'INCONCLUSIVE_TIMEOUT');self.assertNotEqual(r['returncode'],0);self.assertGreater(r['identity']['creation_filetime'],0);self.assertEqual(int((self.out/'slow.txt').read_text()),r['identity']['pid'])
74:     def test_timeout_upper_bound_and_finished_child(self):
75:         with self.assertRaisesRegex(d.ContractError,'timeout_range'):d.launch([],self.out,61)
76:         r=d.launch([d.interpreter_image(),'-I','-S','-c','pass'],self.out,5);self.assertEqual(r['status'],'CHILD_FINISHED');self.assertEqual(r['returncode'],0)
77: 
78: if __name__=='__main__':unittest.main()

FILE ev112-b3e-preflight-timeout-discovery-20261028.md
1: # B3E: localizar el agotamiento de preflight
2: 
3: Estado: REVISADO_PARA_IMPLEMENTAR. Fable 5.1 nativo 66.25 s, SOUND-with-fixes
4: adjudicado abajo. Sólo lectura y nuevos recibos. No build.
5: 
6: ## Hechos e hipótesis
7: 
8: B3E dispone de 41 tests PASS y code review Fable adjudicada. La única ejecución
9: se detuvo por INCONCLUSIVE_RESOURCE: 60.047 s, pico residente 86.49 MB. El log
10: oficial confirma P:, Tools, DayZDiag, vanilla y junction Mods. No report.json de
11: preflight, contrato B3E, carpeta control ni candidato: no hubo compilación.
12: No se atribuye causa a Steam, antivirus, OneDrive, corrupción ni caché.
13: 
14: [HIPÓTESIS] El bloqueo está en una lectura o hash posterior al log oficial.
15: El consumidor actual no guarda fases intermedias, así que no permite localizarlo.
16: La comprobación de cinco metadatos muestra cuatro ejecutables de 0.19–24.81 MB
17: y P:/bin/config.cpp de 201417 bytes. Tamaño pequeño no prueba lectura rápida.
18: 
19: ## Unidad independiente propuesta
20: 
21: [DESIGN] Un script stdlib de diagnóstico, sin importar ni ejecutar el preparador
22: consumido, carga sólo los dos recibos anteriores fijados por SHA256 y obtiene las
23: cinco rutas exactas: AddonBuilder, FileBank, CfgConvert, Binarize y P:/bin/config.cpp.
24: No búsquedas recursivas ni seguimiento de junctions fuera de esas rutas. Verifica
25: cada SHA256 esperado y registra inicio, primer bloque, final, tamaño y duración.
26: Cada evento se vacía al disco para conservar el último paso si agota presupuesto.
27: Conserva también tiempo antes/después de leer los dos recibos. Los recibos se
28: copian por bytes al nuevo directorio, sin modificar originales.
29: 
30: Un padre propio lanza ese script sin ventana, identidad PID/nacimiento y timeout
31: total de 60 s desde Popen; el hijo no lanza descendientes. Al agotar, termina sólo
32: ese hijo, guarda timeout y bytes parciales; no reintenta. No aumentar este límite.
33: No invocar preflight oficial otra vez ni mover/montar P:, editar skills, compilar,
34: empaquetar, desplegar, solicitar lease o iniciar DayZ. Sin caché que sustituya hashes.
35: 
36: ## Interpretación y presupuesto
37: 
38: HASHES_MATCH: los cinco hashes coinciden en esta lectura; no demuestra qué ocurrió
39: en el intento anterior ni certifica todo el preflight. HASH_MISMATCH: conservar
40: archivo/ruta/esperado/observado y bloquear continuación. INCONCLUSIVE_TIMEOUT o
41: INCONCLUSIVE_IO: preservar fases, no declarar válido el entorno. Un fallo de
42: formato, ruta, esquema o hash de los recibos también es inconcluso.
43: 
44: Una revisión independiente de plan de hasta 180 s, entrega breve. Tras adjudicar,
45: implementación stdlib pequeña revisada antes de una única lectura de hasta 60 s.
46: Positivo y negativos de hash/ruta/error/timeout en archivos temporales antes del
47: censo real, agrupados en una suite de hasta 30 s. Ninguna repetición de B3E ni
48: reclasificación de su INCONCLUSIVE_RESOURCE. Una futura continuación de binarización
49: requerirá plan y evidencia propios; B3D continúa sólo OFFLINE_CANDIDATE_ONLY.
50: 
51: ## Adjudicación — 28-10-2026
52: 
53: Revisión y entrega en R/b3e-preflight-discovery-plan-review-20261028. Una entrega
54: completa, identidad claude-fable-5-1, fuentes intactas. Código aún no implementado.
55: 
56: - Se acepta cronometrar también is_dir de P:/DZ, P:/bin, P:/core y P:/scripts,
57:   la lectura del contrato y los dos hashes de fuentes preflight posteriores al
58:   log oficial. Sin importar ni ejecutar preflight ni tocar P:. El alcance de
59:   lectura se amplía sólo a esas dos fuentes y cuatro metadatos conocidos.
60: - La multiplicidad se toma del código y de los recibos reales, no del ejemplo
61:   del dictamen: tres herramientas se leen una vez; Binarize y config.cpp DOS
62:   veces cada uno. tools_sha256 contiene AddonBuilder, FileBank y CfgConvert,
63:   no Binarize. Las dos fuentes de preflight se leen una vez en esta fase.
64: - El helper consumido usa hashlib.sha256 con bloques de 4 MiB; se reproduce
65:   ese patrón. Se refuta la hipótesis de read_bytes para el hash de binarios.
66: - Un resultado rápido sólo mide esta lectura. No permite deducir retrospectivamente
67:   caché, fase oficial lenta ni causa global. Se conserva HASHES_MATCH y duraciones
68:   numéricas; no se crea HASHES_MATCH_FAST con un umbral arbitrario sin contrato.
69:   Si no aparece el retraso, otra fase necesitará una propuesta separada.
70: - Eventos con flush y os.fsync; el coste de la instrumentación se incluye y se
71:   declara. Timeout del padre 60 s total desde Popen, sólo reducción para tests.
72: - Valores esperados fijados ahora en el plan, no calculados por el hijo:
73:   dry-road-build-preflight-20261028/report.json:
74:   354fbb2e5edea80e88521f02cd135ac2f6a7608a14085af5cc088395a542e68e;
75:   prism-b3-binary-replay-20261028/contract-r1.json:
76:   5df5009176342658eb7b31c7c099e643c9e99cc898d2a14f319858a9df391244.
77:   El primero es un recibo de entorno histórico; el segundo es además la ancla
78:   de procedencia ya preservada en B3D/B3E. Ninguno demuestra entorno actual.
79: - Tests previos: positivo completo, mismatch, ruta ausente/ajena, error E/S,
80:   formato/esquema/hash de recibos inválido y timeout con hijo propio lento.
81:   Preservar último evento y originales; ningún reintento. Suite de hasta 30 s.
82: 
83: Se mantiene la revisión de código antes de una única ejecución diagnóstica.
84: No amplía los 60 s ni autoriza compilación. B3E sigue inconcluso y consumido.
85: 
86: ## Ejecución asignada — petición viva posterior
87: 
88: Guillermo pide continuar pruebas y preparar carreteras. Codex implementa esta
89: unidad separable mientras descubre el siguiente trabajo vial. Code review
90: independiente de hasta180s antes de producción; una corrección agrupada, suite30s,
91: una lectura real60s. No autoriza relanzar B3E. El padre usa el handle propio de
92: Popen y GetProcessTimes para PID/nacimiento; kill se dirige al handle, no busca
93: procesos por nombre. Firma verificada en documentación Microsoft de GetProcessTimes.
94: La medición registra también la relectura de integridad de ambos recibos;
95: no se suma esa relectura como lectura de herramientas ni se oculta su coste.
96: 
97: Descubrimiento del ejecutor: sys.executable de GIS es un launcher Windows y su
98: imagen real es el CPython empaquetado de Codex detrás de ese entorno. Para el
99: hijo stdlib se resuelve GetModuleFileNameW(NULL) del proceso GIS vivo y se usa
100: esa MISMA imagen con -I -S, sin paquetes ni Python global resuelto por PATH.
101: Así el handle de Popen corresponde al intérprete que lee y se puede terminar
102: sin dejar al hijo del launcher. Se exige igualdad de PID reportado y handle,
103: y el negativo de timeout comprueba el PID escrito por el hijo antes de pararlo.
104: Firma GetModuleFileNameW verificada en documentación Microsoft. No es evidencia
105: retroactiva de causalidad del preflight anterior ni un cambio de runtime GIS.