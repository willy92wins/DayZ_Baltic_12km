from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'kit7-nav12-ram-ab-20261027';O=R/'kit7-nav12-ram-review-20261027'
O.mkdir(exist_ok=False)
paths=[R/n for n in ['prepare_nav12_ram_pass.py','orchestrate_nav12_ram.js','finish_nav12_ram_pass.py','finalize_nav12_ram_ab.py','test_nav12_ram_flow.cjs','test_nav12_ram_conditions.py','test_nav12_ram_command.cjs','prepare_nav12_ram_files.py','strengthen_nav12_ram_controls.py','verify_c_orderly_close.py','capture_owned_server_identity.ps1','copy_owned_server_rpt.ps1','record_nav_c_event.ps1']]
paths += [W/'tools/performance'/n for n in ['capture_server_baseline_ev112.ps1','bind_server_baseline_ev112.py','read_server_baseline_ev112.py','compare_server_baseline_ev112.py']]
paths += [W/'tools/navigation/observe_owned_server_exit.ps1',W/'tools/navigation/verify_terrain_perf.py',D/'missions.json',D/'mission-validation.json',D/'coordinator-controls.json',D/'conditions-controls.json',D/'command-flow-controls.json']
manifest=json.loads((D/'missions.json').read_text(encoding='utf-8-sig'))
paths += [Path(x['mission'])/'init.c' for x in manifest['passes']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths};(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
brief='''Revisión independiente READ ONLY de la preparación RAM de Nav12. Fable 5.1 por CLI nativo, solo Read/Glob/Grep. Sin escritura, comandos, MCP, Git ni subagentes. Entrega en stdout SOUND / SOUND-with-fixes / NEEDS-WORK con hallazgos path:line, mecanismo y repro o contradicción, máximo 900 palabras.

Lista: E:/DayZ-Baltic-Build/shape-repair-20261025/kit7-nav12-ram-review-20261027/source-hashes.json. R es su padre. El alcance es prepare_nav12_ram_pass.py, orchestrate_nav12_ram.js, finish_nav12_ram_pass.py y finalize_nav12_ram_ab.py, las seis misiones nuevas y sus controles. Se derivan de los scripts Nav8 finales que realmente completaron seis pasadas válidas. Compara con ellos si ayuda; no con drafts históricos. No hay resultados Nav12 ni se lanzará RAM antes del PASS nativo607. Generación Nav12 en curso, no intervenir.

Nav8 corrigió cuatro alturas (607 PASS) pero FAIL_RAM ratios 1.26591 / 1.24133. Experimento Nav12 aislado; no hereda mediciones ni afirma éxito. Misiones con UUID/log frescos y paridad exacta salvo world/log; siguen 30 segundos de calentamiento y 120 de medición, ABBAAB, tres por mapa, ratio máximo 1.10 y dispersión 5%. Lectores/consumidores originales inmutables. prepare exige PASS607 + identidad + deployment completo rehasheado, accepted.json con fuentes revisadas, y pasada anterior válida/cerrada. Debe cargar nav12RamConfig directamente desde missions.json congelado antes de ejecutar.

Corrección aislada de coordinación: cmd usa beat recuperable y no registra eventos por shell antes de adoptar su mismo RUNNING_IDLE sin propietario. FIFO directo sin prelease ni sondeo de banco; no cierra procesos ajenos. El sampler comienza al bind, antes de hashear paquetes; la captura de identidad pesada se realiza después del final de medición en ambos mapas. Cierre oficial estricto con observador/RPT, lease liberado y revalidación de seis resultados. No usa la excepción histórica Nav8 de cancelación de generación.

Pruebas offline: seis misiones validadas por el validador DayZ (un archivo cada una, sin warnings); 11 controles de equivalencia real de misiones/consumidor; 8 de comando; 14 escenarios de lifecycle y 3 mutantes rechazados. El lifecycle ejercita ambos conjuntos de mods Baltic/Chernarus, el hash antes del fin de medición como negativo y caducidad durante un comando. No confundir mocks o cantidad de pruebas con evidencia de rendimiento.

Ataca diferencias de condiciones, paquete viejo, herencia accidental de muestras, orden equivocado, falso PASS, deriva de fuentes, fecha/log/identidad y errores reales de adaptación. Los snapshots de procesos son descriptivos y se publicarán solo recuentos y hashes, sin nombres de aplicaciones. No prueban ausencia absoluta de carga. CPU descriptiva, no FPS, actores, capacidad ni aceptación global. Un FAIL se conservará; no se repite para seleccionar una pasada favorable. accepted.json congelará tus fuentes al terminar. No rediseñes el plan ni pidas otra ronda sin un repro bloqueante.'''
(O/'brief.md').write_text(brief,encoding='utf-8')
args=['C:/Users/guill/.local/bin/claude.exe','--print','--safe-mode','--model','claude-fable-5-1','--effort','medium','--tools','Read,Glob,Grep','--allowedTools','Read,Glob,Grep','--output-format','json','--no-session-persistence']
started=time.monotonic()
with (O/'response.json').open('wb') as out,(O/'stderr.log').open('wb') as err:
 p=subprocess.Popen(args,cwd=W,stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=0x08000000)
 try:p.communicate(brief.encode(),timeout=300)
 except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=30);raise
assert all(sha(Path(k))==v for k,v in before.items())
(O/'completion.json').write_text(json.dumps(dict(returncode=p.returncode,seconds=time.monotonic()-started,inputs_unchanged=True),indent=2)+'\n')
print('FABLE_EXIT',p.returncode);raise SystemExit(p.returncode)
