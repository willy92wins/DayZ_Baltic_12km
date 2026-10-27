from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'kit7-nav12-plan-review-20261027'
O.mkdir(exist_ok=False)
paths=[W/'plans/ev112-kit7-nav12-cost-20261027.md',R/'kit7-nav8-ram-ab-20261027/comparison.json',R/'kit7-nav8-consumer-20261027/height-comparison.json',R/'kit7-nav-budget-planning-summary-20261027.json',W/'tools/navigation/package_nav8_config_ev112.py',W/'tools/navigation/inspect_navmesh_v9_ev112.py',R/'orchestrate_kit7_nav8_generation.js',R/'resume_kit7_nav8_generation.js',W/'product-spec.md']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths}
(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
brief='''Revisión técnica independiente y acotada del plan de coste Nav12 de Baltic. Modelo pedido por Guillermo: Fable 5.1 por CLI nativo; Codex es executor/integrador, tú revisor de otra familia. Disponibilidad medida hoy: CLI 2.1.310 y revisiones anteriores completadas con modelUsage claude-fable-5-1; esta llamada vuelve a comprobarla. Solo Read/Glob/Grep: NO procesos, MCP, subagentes, Git, escritura de archivos, skills ni memoria. Devuelve una respuesta final de máximo 900 palabras; yo guardo stdout. El cwd no es un sandbox: tampoco escribas fuera de él.

Workspace W=C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c. Evidencias y hashes exactos en E:/DayZ-Baltic-Build/shape-repair-20261025/kit7-nav12-plan-review-20261027/source-hashes.json. Lee primero el plan completo plans/ev112-kit7-nav12-cost-20261027.md, comparison.json, height-comparison.json y kit7-nav-budget-planning-summary-20261027.json; consulta el resto solo para verificar citas o contratos. Los resultados grandes están enlazados en los checkpoints; no cargues enteros miles de casos por rutina.

Hechos: 8 m corrigió las cuatro alturas y pasa 607 consultas nativas con límites intactos .801/.011/2.1; seis pasadas RAM nuevas ABBAAB fallan residente1.26591 y privada1.24133 respecto a Chernarus, dispersión<=.205%. No hay cliente ni prueba de capacidad. Todo publicado conservando FAIL. Usuario pidió corregir hasta pasar sin rebajar tolerancias, avanzar autónomamente y commit/push. Ya autorizó comparación con Chernarus. No hay nuevo consentimiento pendiente para el experimento aislado.

Plan propone una generación de 12 m porque baja de2359296 a1048576 teselas esperadas, divide12288m y estima .715m en los ocho puntos originales. Las estimaciones NO son gate: 12m predice74 excesos en todos los waypoints, 8m predice10 y pasa realmente;12.5m predice125 y falla4. 10.5m es otra alternativa con .535m en los ocho y56 excesos amplios; no se cambiará de candidato silenciosamente. No presumir RAM lineal ni éxito geométrico. Debe pasar generación propia, mismos607, misma referencia/CSV/filtros/tolerancias y otras seis pasadas RAM1.10/5%. Geometría/WRP/agua/protecciones idénticas por bytes; sin parchear NM. Además corrige solo en el nuevo coordinador la caducidad dentro de cmd y el registro de eventos antes de recuperar, observados en la generación8m y resueltos en su runner de recuperación.

Intenta refutar este PLAN, no la implementación futura. Decide si el experimento está suficientemente motivado y si los gates, presupuesto y recuperación son verificables sin falso PASS. Contrasta API/citas reales. Distingue defecto bloqueante de incertidumbre experimental ya cubierta por gate nativo. Veredicto SOUND / SOUND-with-fixes / UNSOUND; hallazgos con archivo:línea, consecuencia y corrección mínima. Para bloqueantes incluye repro o contradicción concreta. Puedes rechazar la elección de12m si hay motivo verificable; no impongas otro diseño por mera preferencia. No pidas un segundo council ni revises módulos ajenos. Esta es una ronda de plan, con un experimento nativo presupuestado; tras fallo se replantea antes de otra variante. Entregable: veredicto y límites, no modificación de archivos.
'''
(O/'brief.md').write_text(brief,encoding='utf-8')
args=['C:/Users/guill/.local/bin/claude.exe','--print','--safe-mode','--model','claude-fable-5-1','--effort','medium','--tools','Read,Glob,Grep','--allowedTools','Read,Glob,Grep','--output-format','json','--no-session-persistence']
start=time.monotonic()
with (O/'response.json').open('wb') as out,(O/'stderr.log').open('wb') as err:
    p=subprocess.Popen(args,cwd=W,stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=0x08000000)
    try:p.communicate(brief.encode(),timeout=300)
    except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=30);raise
assert all(sha(Path(k))==v for k,v in before.items())
(O/'completion.json').write_text(json.dumps(dict(returncode=p.returncode,seconds=time.monotonic()-start,inputs_unchanged=True),indent=2)+'\n')
print('FABLE_EXIT',p.returncode)
raise SystemExit(p.returncode)
