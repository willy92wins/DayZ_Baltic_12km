from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');O=R/'kit7-nav12-postprocess-review-20261027'
O.mkdir(exist_ok=False)
paths=[R/n for n in ['package_and_deploy_kit7_nav12.py','finish_kit7_nav12_probe.py','orchestrate_kit7_nav12_probe.js','verify_c_orderly_close.py','prepare_kit7_nav12_runtime.py','test_kit7_nav12_probe_flow.cjs','test_kit7_nav12_probe_command.cjs','test_kit7_nav12_consumer.py','verify_nav12_generation_budget.py','test_nav12_generation_budget.py','fix_kit7_nav12_postprocess.py']]
paths += [W/'tools/navigation/verify_kit7_nav_ev112.py',W/'tools/navigation/inspect_navmesh_v9_ev112.py',W/'tools/playtest/attach_navmesh.py',R/'kit7-nav12-consumer-20261027/frozen.json',R/'kit7-nav12-consumer-20261027/contract-parity.json']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p):sha(p) for p in paths};(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
brief='''Revisión independiente READ ONLY de la sonda y postproceso Nav12. Fable 5.1 por CLI nativo; solo Read/Glob/Grep. No escribas, ejecutes comandos, uses MCP, Git ni subagentes. Responde en stdout con SOUND / SOUND-with-fixes / NEEDS-WORK, hallazgos concretos con path:line, mecanismo y repro o contradicción, máximo 900 palabras.

Lista exacta: E:/DayZ-Baltic-Build/shape-repair-20261025/kit7-nav12-postprocess-review-20261027/source-hashes.json. R es su directorio padre. W es la worktree indicada en los scripts. La generación Nav12 ya está en curso, revisada SOUND aparte; no intervenir ni auditar ese coordinador. Aún no se ejecutará ningún empaquetado o sonda. El alcance es la adaptación nueva de package_and_deploy_kit7_nav12.py, finish_kit7_nav12_probe.py, orchestrate_kit7_nav12_probe.js y sus pruebas. Contrasta las dependencias reales si las necesitas.

Nav8 ya pasa 607 consultas y corrige las cuatro alturas, pero falla RAM (ratios 1.26591 / 1.24133). Plan Nav12 aprobado y revisado: input de 12 m, una generación, mismas consultas 607 y tolerancias .801 / .011 / 2.1, luego seis RAM nuevas si PASS. No es aceptación global ni de actores. El input ed1acb... cambia solo config y conserva NM previo 13e1ab... de 12.5 m; empaquetar exige salida nativa con inspector explícito --grid 1024 1024 --tile-width 12, reemplazando solo el NM, otras 6826 entradas idénticas. Se exige cierre original estricto, sin la excepción histórica de recuperación Nav8. verify_nav12_generation_budget.py añade comprobación independiente del recibo persistido: mismo run e inicio, 18000 s nativos / 18300 coordinador, fechas fijas. Respeta milisegundos de V8 frente a microsegundos Python; 1 positivo y 12 negativos pasan.

Nueva referencia UUID 3325b685-d8cf-42d1-a476-aa2a3fe2e857, CSV idéntico SHA305e808d58ac25d5fbf1a43a03eb1504600b102ebf433bca527395bfdcd6387d; cambian solo UUID/header/log. Mismos oráculos geométricos y testigos F. Hay 19 controles sintéticos del consumidor, no evidencia del motor. La sonda corrige el heartbeat dentro de cmd con recuperación antes de cualquier evento por shell, según el patrón ya ejercitado: 8 controles de comando, 13 de lifecycle y 2 mutantes rechazados. El harness antiguo tenía una búsqueda errónea de finish_kit7_nav_probe.py, ahora apunta al consumidor12 real; revisa que consumer_failure sí se ejercita. FIFO directo sin prelease ni consulta de ocupación, solo adopta y cierra su run verificado; un propietario ajeno se conserva.

Ataca falso PASS por malla vieja, grid incorrecto, referencia movida, tolerancia rebajada, identidad/cierre insuficiente o drift. El gate accepted.json se creará después de tu revisión y congelará todas tus fuentes. Diferencia una mejora opcional de un bloqueo reproducible. No pidas otro council, no modifiques el plan ni propongas repeticiones favorables. La RAM se prepara en una fase independiente; no afirmar nada de ella aquí.'''
(O/'brief.md').write_text(brief,encoding='utf-8')
args=['C:/Users/guill/.local/bin/claude.exe','--print','--safe-mode','--model','claude-fable-5-1','--effort','medium','--tools','Read,Glob,Grep','--allowedTools','Read,Glob,Grep','--output-format','json','--no-session-persistence']
start=time.monotonic()
with (O/'response.json').open('wb') as out,(O/'stderr.log').open('wb') as err:
 p=subprocess.Popen(args,cwd=W,stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=0x08000000)
 try:p.communicate(brief.encode(),timeout=300)
 except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=30);raise
assert all(sha(Path(k))==v for k,v in before.items())
(O/'completion.json').write_text(json.dumps(dict(returncode=p.returncode,seconds=time.monotonic()-start,inputs_unchanged=True),indent=2)+'\n')
print('FABLE_EXIT',p.returncode);raise SystemExit(p.returncode)
