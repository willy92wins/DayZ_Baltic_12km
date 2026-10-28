Delegar JUICIO planB3E2, Fable5.1 nativoCLI2.1.310 verificado hoy, Codexejecutor/integrador. Una lane read-only sin herramientas/hijos/escrituras. <=180s850palabras, SOUND/SOUND-with-fixes/NEEDS-WORK con problemas concretos, fix y FIN_REVISION. Receptor Codex adjudica frente a fuentes. B3E anterior no compiló nada: preflight agotó60s tras rutasOK antes de hashseal. Nueva sonda leyó9veces7archivos, hashmatch0.641s;16testsR2PASS2.734s. Eso NO aísla causa timeout histórico ni sustituye preflight. Nueva unidad propuesta para pareja control/candidato, no CLI/carpetaconsumidos. El código viejo debajo es referencia no implementaciónnueva. No reabrir41testsconsumidorB3E ya publicado; requerir cobertura de cambios nuevoorquestador contra consumidor/recibos. Presupuestos60preflight/150buildcada/180gatecada2GiB sin relajación. Censo1520todo, comparaciónmundialbits/controlantescandidato/overlay/contactoinalterados. No native/paquete201/DayZ/lease. Revisar cómo hacer continuación mínima segura sin mutarhelpers, pinapprovals/contracts y errores/recursos. No pedir opinión nueva sobre dictamenexistente. Limita inferencia de muestreo de procesos; no prometer cronómetro/árbol más fuerte que disponible. Usuarioquiere continuar pruebas y prepararcarreteras; éstasindependientesdeestaunidad.

FILE ev112-b3e-build-continuation-20261028.md
1: # B3E2 — completar preflight y ejecutar la pareja pendiente
2: 
3: Estado: BORRADOR_PENDIENTE_DE_REVISION. Codex ejecutor/integrador.
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

FILE build_prism_b3e_ev112.py
1: """One fresh control/candidate pair; no full package, deployment or DayZ."""
2: from pathlib import Path
3: import contextlib,hashlib,importlib.util,io,json,os,subprocess,sys,time,traceback
4: HERE=Path(__file__).resolve().parent;W=HERE.parent.parent
5: R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025')
6: sys.path[:0]=[str(HERE),str(HERE.parent/'water'),str(HERE.parent/'playtest')]
7: sys.path.append(str(R/'dry-road-build-dependencies-20261028'))
8: import psutil
9: import prism_b3e_compiled_ev112 as gate
10: from continuous_stream_pilot_v31 import model_config
11: meter=gate.meter
12: sha=meter.sha
13: dump=meter.dump
14: 
15: def run_tree(command,cwd,log,seconds,limit=2*1024**3):
16:     """Sample and bound only descendants of this Popen; never match by name."""
17:     borns={};observed={};peak=0;start=time.monotonic();reason=None
18:     def live_owned():
19:         live=[]
20:         for pid,born in list(borns.items()):
21:             try:
22:                 p=psutil.Process(pid)
23:                 if p.create_time()!=born or not p.is_running():continue
24:                 live.append(p)
25:             except psutil.NoSuchProcess:pass
26:         return live
27:     def stop_owned():
28:         for p in reversed(live_owned()):
29:             try:
30:                 if p.create_time()==borns[p.pid]:p.kill()
31:             except psutil.NoSuchProcess:pass
32:     with log.open('wb') as out:
33:         child=subprocess.Popen(command,cwd=cwd,stdout=out,stderr=subprocess.STDOUT,creationflags=0x08000000)
34:         parent=psutil.Process(child.pid);borns[parent.pid]=parent.create_time()
35:         dump(log.with_suffix('.running.json'),dict(pid=parent.pid,create_time=borns[parent.pid],command=command,max_seconds=seconds,max_sampled_tree_rss_bytes=limit))
36:         try:
37:             while True:
38:                 for p in live_owned():
39:                     try:
40:                         for d in p.children(recursive=True):borns[d.pid]=d.create_time()
41:                     except psutil.NoSuchProcess:pass
42:                 live=live_owned();rss=0
43:                 for p in live:
44:                     try:
45:                         rss+=p.memory_info().rss
46:                     except psutil.NoSuchProcess:continue
47:                     # Memory/identity failures remain fail-closed. Executable naming
48:                     # is optional telemetry and must not terminate a valid build.
49:                     key=str(p.pid)+'@'+str(borns[p.pid])
50:                     if key not in observed:
51:                         try:
52:                             exe=p.exe();observed[key]=dict(executable=exe,sha256=sha(exe),create_time=borns[p.pid])
53:                         except (psutil.Error,OSError) as e:
54:                             observed[key]=dict(executable=None,sha256=None,create_time=borns[p.pid],reason=type(e).__name__+':'+str(e))
55:                 peak=max(peak,rss)
56:                 if time.monotonic()-start>seconds or peak>limit:
57:                     reason='timeout' if time.monotonic()-start>seconds else 'sampled_tree_memory';stop_owned();child.wait(timeout=10);break
58:                 if child.poll() is not None and not live:break
59:                 time.sleep(.1)
60:         except BaseException:
61:             stop_owned();child.wait(timeout=10);raise
62:     result=dict(returncode=child.returncode,stop_reason=reason,seconds=time.monotonic()-start,peak_sampled_tree_rss_bytes=peak,observed_processes=observed,
63:                 observation_limit='Sampled descendants only. Installed hashes do not prove unobserved short-lived children executed.')
64:     dump(log.with_suffix('.receipt.json'),result)
65:     if child.returncode or reason:raise RuntimeError('owned_process_failed:'+str(result))
66:     return result
67: 
68: def preflight(output):
69:     output.mkdir(exist_ok=False);meter.STARTED=time.monotonic();meter.MAX_SECONDS=60;stop=meter.bounded(output)
70:     try:
71:         old=json.loads((R/'dry-road-build-preflight-20261028/report.json').read_bytes());src=Path(old['original_source']);fixed=R/'dry-road-build-preflight-20261028/preflight_syntax_repaired.py'
72:         gate.bind(sha(src)==old['original_sha256'] and sha(fixed)==old['local_sha256']=='5fb698727b6c70e8dfa21267963b54cafa60b1ade8b4df3ebfe6b8124e5fc7f2','preflight_sources')
73:         a=src.read_text();b=fixed.read_text();gate.bind(b.replace("        r'subst P:","        'subst P:")==a,'preflight_literal_only')
74:         try:compile(a,str(src),'exec');syntax='original_compiles'
75:         except SyntaxError as e:syntax=f'{type(e).__name__}:line{e.lineno}:{e.msg}'
76:         spec=importlib.util.spec_from_file_location('b3e_official_preflight',fixed);pf=importlib.util.module_from_spec(spec);spec.loader.exec_module(pf)
77:         log=io.StringIO()
78:         with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):code=pf.main();mods=pf.validate_p_mods();tools=pf.find_dayz_tools()
79:         (output/'official-checks.log').write_text(log.getvalue(),encoding='utf-8')
80:         gate.bind(code==0 and mods is None and str(tools)==old['tools_root'],'preflight_failed')
81:         for p in ('P:/DZ','P:/bin','P:/core','P:/scripts'):gate.bind(Path(p).is_dir(),'dependency_missing:'+p)
82:         pins={str(src):sha(src),str(fixed):sha(fixed)}
83:         for p,h in old['tools_sha256'].items():gate.bind(sha(p)==h,'tool_changed:'+p);pins[p]=h
84:         prior=json.loads((R/'prism-b3-binary-replay-20261028/contract-r1.json').read_bytes())
85:         for p in [tools/'Bin/Binarize/Binarize.exe',Path('P:/bin/config.cpp')]:
86:             key=str(p);gate.bind(key in prior['pins'] and sha(p)==prior['pins'][key],'prior_tool_or_config:'+key);pins[key]=sha(p)
87:         result=dict(status='FRESH_PREFLIGHT_B3E',tools_root=str(tools),pins=pins,original_parse=syntax,
88:                     installed_skill_modified=False,repair='Archived display-literal raw-prefix only; exact source/diff binding verified.',native_environment_certified=False,measurement=meter.memory())
89:         dump(output/'report.json',result);return result
90:     finally:stop.set()
91: 
92: def sequence(build_control,check_control,build_candidate,check_candidate):
93:     build_control();check_control();build_candidate();check_candidate()
94: 
95: def execute(output):
96:     output.mkdir(exist_ok=False)
97:     gate.bind(psutil.__version__=='7.2.2' and Path(psutil.__file__).resolve().is_relative_to(R/'dry-road-build-dependencies-20261028'),'psutil_binding')
98:     # Human-reviewed code and final tests are required before this entry point.
99:     approval=R/'prism-b3e-execution-approval-20261028.json';approval_data=json.loads(approval.read_bytes())
100:     gate.bind(approval_data['status']=='REVIEW_ADJUDICATED_TESTS_PASS','execution_not_ready')
101:     for p in [Path(__file__),Path(gate.__file__),HERE/'test_prism_b3e_ev112.py',W/'plans/ev112-prism-b3e-compiled-witness-20261028.md']:
102:         gate.bind(str(p) in approval_data['pins'],'approval_unpinned:'+str(p))
103:     for p,h in approval_data['pins'].items():gate.bind(sha(p)==h,'approval_postimage_changed:'+p)
104:     pre=preflight(output/'preflight')
105:     dpath=R/'prism-b3d-execution-20261028/contract.json';ppath=R/'prism-b3d-consumer-20261028/report.json';priorpath=R/'prism-b3-binary-replay-20261028/contract-r1.json'
106:     gate.bind(sha(dpath)==gate.OFFLINE and sha(ppath)==gate.PROOF and sha(priorpath)==gate.PRIOR,'ancestry_hash')
107:     d=json.loads(dpath.read_bytes());prior=json.loads(priorpath.read_bytes());pins=dict(d['pins'])
108:     for p,h in pins.items():gate.bind(sha(p)==h,'inherited_pin_changed:'+p)
109:     historic=json.loads((R/'dry-road-compile-pair-20261028/inputs.json').read_bytes())
110:     for p,h in historic.items():
111:         if 'dry-road-build-dependencies-20261028' in p:gate.bind(sha(p)==h,'dependency_changed:'+p);pins[p]=h
112:     for p,h in pre['pins'].items():gate.bind(p not in pins or pins[p]==h,'preflight_ancestry_mismatch:'+p);pins[p]=h
113:     files=[dpath,ppath,priorpath,R/'prism-b3d-candidate-20261028/candidate.p3d',output/'preflight/report.json',approval,Path(__file__),HERE/'prism_b3e_compiled_ev112.py',HERE/'test_prism_b3e_ev112.py',W/'plans/ev112-prism-b3e-compiled-witness-20261028.md']
114:     for p in files:pins[str(p)]=sha(p)
115:     for p,h in approval_data['pins'].items():gate.bind(p not in pins or pins[p]==h,'approval_inherited_mismatch');pins[p]=h
116:     config=model_config([dict(model='baltic_stream_pilot\\'+gate.old.NAME)]).encode('ascii')
117:     c=dict(schema='B3E_COMPILED_V1',offline_contract=str(dpath),offline_proof=str(ppath),prior_contract=str(priorpath),source_control=d['reference'],candidate_mlod=str(R/'prism-b3d-candidate-20261028/candidate.p3d'),original_result=d['original_result'],pins=pins,config_sha256=hashlib.sha256(config).hexdigest())
118:     for k in ('origin','matrix','centre','targets','selected_components'):c[k]=d[k]
119:     for k in ('baseline_odol','baseline_pbo','poses'):c[k]=prior[k]
120:     contract=output/'contract.json';dump(contract,c);contract_sha=sha(contract);gate.context(contract)
121:     reader='C:/temp/moto_lanes/review_g3/tools';receipts=[]
122:     def stable():gate.check_pins(c);gate.bind(sha(contract)==contract_sha,'contract_changed')
123:     def build(side):
124:         stable();folder=output/side/'source/baltic_stream_pilot';folder.mkdir(parents=True,exist_ok=False)
125:         source=Path(c['source_control'] if side=='control' else c['candidate_mlod']);(folder/gate.old.NAME).write_bytes(source.read_bytes());(folder/'config.cpp').write_bytes(config);(folder/'$PBOPREFIX$').write_bytes(b'baltic_stream_pilot')
126:         gate.bind(sha(folder/gate.old.NAME)==c['pins'][str(source)],'copied_source')
127:         result=run_tree(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(W/'tools/water/pack_continuous_stream_pilot_v31.ps1'),'-Pilot',str(output/side)],W,output/side/'driver.log',150)
128:         _,props,entries=gate.old.read_pbo(output/side/'packed/baltic_stream_pilot.pbo')
129:         gate.bind(set(entries)=={gate.old.NAME,'config.bin'} and props['prefix']=='baltic_stream_pilot' and entries[gate.old.NAME].startswith(b'ODOL'),'build_payload')
130:         (output/side/'saved-odol.p3d').write_bytes(entries[gate.old.NAME]);stable()
131:         result.update(side=side,odol_sha256=sha(output/side/'saved-odol.p3d'),pbo_sha256=sha(output/side/'packed/baltic_stream_pilot.pbo'),config_sha256=hashlib.sha256(entries['config.bin']).hexdigest());dump(output/side/'receipt.json',result);receipts.append(result)
132:     def check(side):
133:         dest=output/('control-gate' if side=='control' else 'candidate-gate')
134:         run_tree([sys.executable,'-I',str(HERE/'prism_b3e_compiled_ev112.py'),side,str(contract),str(output),reader,str(dest)],W,output/(side+'-gate.log'),180)
135:         report=json.loads((dest/'report.json').read_bytes());gate.bind(report['contract_sha256']==contract_sha and report['status']==('CONTROL_B3E_CERTIFIED' if side=='control' else 'COMPILED_B3E_CONDITIONAL'),'gate_result');stable()
136:     sequence(lambda:build('control'),lambda:check('control'),lambda:build('candidate'),lambda:check('candidate'))
137:     gate.bind(receipts[0]['config_sha256']==receipts[1]['config_sha256'],'pair_config_changed')
138:     dump(output/'completion.json',dict(status='COMPILED_B3E_CONDITIONAL',contract_sha256=contract_sha,proof_sha256=sha(output/'candidate-gate/report.json'),builds=receipts,no_package201_or_dayz=True));print('COMPILED_B3E_CONDITIONAL')
139: 
140: def main():
141:     import argparse
142:     p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args()
143:     try:execute(a.output)
144:     except Exception as e:
145:         if a.output.exists():dump(a.output/'execution-failure.json',dict(status='INCONCLUSIVE_EXECUTION',type=type(e).__name__,reason=str(e),traceback=traceback.format_exc(),note='See child gate reports for any geometric rejection; this wrapper does not reclassify them.'))
146:         raise
147: 
148: if __name__=='__main__':main()

FILE report.json
1: {
2:   "status": "HASHES_MATCH",
3:   "readings": 9,
4:   "distinct_paths": 7,
5:   "child_seconds": 0.6410000000032596,
6:   "read_seconds": 0.5620000000017171,
7:   "tests": 16,
8:   "tests_seconds": 2.734,
9:   "full_preflight": false,
10:   "builds": 0,
11:   "dayz": false,
12:   "historical_timeout_cause": "UNDETERMINED"
13: }