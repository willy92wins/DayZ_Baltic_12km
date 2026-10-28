from pathlib import Path
import hashlib,json,subprocess,time
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=Path(r'E:/DayZ-Baltic-Build/shape-repair-20261025');O=R/'b3e2-code-review-20261028';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[W/'tools/quality'/n for n in ('build_prism_b3e2_ev112.py','preflight_b3e2_ev112.py','consume_prism_b3e2_ev112.py','test_prism_b3e2_ev112.py')]+[W/'plans/ev112-b3e-build-continuation-20261028.md']
pins={str(p):sha(p) for p in files};(O/'inputs.json').write_text(json.dumps(pins,indent=2),encoding='utf-8')
for p in files:(O/p.name).write_bytes(p.read_bytes())
brief='''Delegar JUICIO: revision de codigo B3E2 nuevo. Una lane Claude Fable5.1 nativo CLI2.1.310 sondeado hoy; identidad real debe figurar en recibo. Codex es executor/integrator y adjudica. Read-only, sin tools/hijos/escrituras, sin git. Entrega <=850palabras180s, SOUND/SOUND-with-fixes/NEEDS-WORK, hallazgos concretos con lineas/fix y FIN_REVISION. No council aun. Plan ya revisado y adjudicado; revisa diff nuevo frente a ese plan. Tests iniciales21PASS8.109s incluyendo hijo real que escribe PBO independiente, lector real, gate real positivo/negativo, arbol propio observado y retirado. No pareja real, preflight ni DayZ ejecutados en esta unidad. B3E original agotó preflight60s; no se cambia presupuesto. Nuevo padre usa run_tree sellado, hijo stdlib aislado para comprobaciones oficiales y hashes. Mismo consumidor geométrico sellado36bce0... sin relajar igualdad/tolerancias. B3D pins hereda packer/model_config/3lectores/psutil; nuevos lzo/lzss y modulos cargados. Padre crea contrato NUEVO mismo esquema geometrico. Rutas son identidad privada solo; publicacion no binarios. Context consumidor verifica esquema,pins,OFFLINE=b445,PROOF=ae5e,PRIOR=5df,CANDIDATE=f2b7,transitivos,4560pares y controles originales. Consume escribe census completo1520, control gate primero y candidato solo si control certificado, tambien prueba Visual/Memory/Roadway,bbox,overlay±.02/.01,margen700dry723wet. No exactitud de grosor local recentrado: no estaba aprobada. Run_tree sellado Popen no-window, PID/create_time propio, muestreo.1s RSS/arbol, guarda running/receipt y mata solo identidades propias si timeout; no promise hijos cortos no observados. Fail rc/deadline levanta RuntimeError. Nuevo wrapper postverifica retornos tardios. Observa errores de paths/binding/control que impidan ejecucion o falsos PASS. Evita especular causa historica. Ninguna autorizacion para201/native. No pedir re-revision de historia.'''
capsule=brief+'\n\n'+'\n\n'.join('FILE '+p.name+'\n'+'\n'.join(f'{i+1}: {s}' for i,s in enumerate(p.read_text(encoding='utf-8').splitlines())) for p in files);(O/'capsule.md').write_text(capsule,encoding='utf-8')
t=time.monotonic();timeout=False
with (O/'events.jsonl').open('wb') as out,(O/'stderr.log').open('wb') as err:
 p=subprocess.Popen(['C:/Users/guill/.local/bin/claude.exe','--print','--safe-mode','--model','claude-fable-5-1','--effort','medium','--output-format','stream-json','--verbose','--include-partial-messages','--no-session-persistence','--tools',''],cwd=W,stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=0x08000000)
 (O/'running.json').write_text(json.dumps(dict(pid=p.pid,max_seconds=180)),encoding='utf-8')
 try:p.communicate(capsule.encode(),timeout=180)
 except subprocess.TimeoutExpired:timeout=True;p.terminate();p.wait(timeout=20)
events=[]
for line in (O/'events.jsonl').read_text(encoding='utf-8-sig').splitlines():
 try:events.append(json.loads(line))
 except json.JSONDecodeError:pass
result=next((e for e in reversed(events) if e.get('type')=='result'),{});elapsed=time.monotonic()-t
c=dict(returncode=p.returncode,timeout=timeout,seconds=elapsed,within_budget=elapsed<=180,models=list(result.get('modelUsage',{})),complete='FIN_REVISION' in result.get('result',''),inputs_unchanged=all(sha(Path(p))==h for p,h in pins.items()),denials=result.get('permission_denials',[]))
(O/'review.md').write_text(result.get('result',''),encoding='utf-8');(O/'completion.json').write_text(json.dumps(c,indent=2),encoding='utf-8');print(json.dumps(c))
