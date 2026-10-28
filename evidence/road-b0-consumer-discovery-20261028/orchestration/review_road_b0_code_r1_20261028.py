from pathlib import Path
import hashlib,json,subprocess,time
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=Path(r'E:/DayZ-Baltic-Build/shape-repair-20261025');O=R/'road-b0-code-r1-review-20261028';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[W/'tools/quality/road_consumer_discovery_ev112.py',W/'tools/quality/test_road_consumer_discovery_ev112.py',W/'plans/ev112-road-consumer-discovery-b0-20261028.md',R/'run_road_b0_execution_r1_20261028.py',W/'plans/ev112-road-b0-instrument-correction-20261028.md']
pins={str(p):sha(p) for p in files};(O/'inputs.json').write_text(json.dumps(pins,indent=2),encoding='utf-8')
brief='Delegar JUICIO correccion de instrumento RoadB0 R1. Una lane Fable5.1 CLI nativo medido hoy, Codex executor/integrator adjudica. Read-only sin herramientas/hijos/escrituras/Git.180s <=550palabras SOUND/SOUND-with-fixes/NEEDS-WORK con lineas y FIN_REVISION. No otra opinion sobre codigo intacto: revisar correccion NUEVA demostrada por fallo real. R0 ValueError:prefix en1.734s,716783616bytes ANTES de CfgConvert/caras. Source-table A PBO34c1 exacto props prefix DZ\\structures\\roads (D yZ mayusculas), guard anterior exigia dz. R1 exige literal instalado, PBOhash inmutable. Ademas brief anterior erroneo: base.run_tree REAL build_prism_b3e_ev112.py65 hace if child.returncode or reason:raise RuntimeError despuesdeguardar log.with_suffix(.receipt.json). No permite rc2 directamente. WrapperR1 captura SOLO RuntimeError, registra excepcion, relee receipt exclusivo, exige stop_reasonNone/seconds<=120/RSS<=2GiB/rc0o2, todos pins, report3modelos/sinerror yfuncionaccept_run_receipt comprueba par0+COMPLETE o2+INCONCLUSIVE. Fallo verdadero sigue rechazado. No cambiahelpers. R0 fuentes/recibos archivados, outputR1nuevo.22testsPASS0.954s incluyeprefijoreal yreceiptpositivo2,contradictorio0,error ytimeout. Unknownconsumer/pivot/width/crossings preservados;3modelos yconfigsololectura, sinWRP/build/deploy/DayZ. PlanR1 fijaunaextraccionnueva120s2GiB sinreintentos, no relajacion. Revisar contratos/recibo falso/reuso/alcance errores nuevos; no pedirrepetirA/R0. Fuente run_tree base ya sellada: observa PIDcreate_time/runnableowns, muestreaRSSdescendants, guarda .running, .receipt y arroja RuntimeError porrc!=0; mismo hash914bef55. Firmas CfgConvert -txt -dst verificadas, numpy/shapely importados en misma suiteGIS-I; no suponersiteuser. Fuentes completas actuales adjuntas, distinguir limitaciones fuera de R1. ReceptorCodex verificaadjudica.'
capsule=brief+'\n\n'+'\n\n'.join('FILE '+str(p)+'\n'+'\n'.join(f'{i+1}: {s}' for i,s in enumerate(p.read_text(encoding='utf-8').splitlines())) for p in files);(O/'capsule.md').write_text(capsule,encoding='utf-8')
for p in files:(O/p.name).write_bytes(p.read_bytes())
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
