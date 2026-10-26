from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'kit7-hybrid-rebase-review-20261026';O.mkdir(exist_ok=False)
paths=[W/'plans/ev112-rebased-hybrid-relief-20261026.md',W/'tools/terrain/repair_guarded_shapes_ev112.py',W/'tools/terrain/repair_free_shapes_ev112.py',W/'tests/test_hybrid_witnesses_ev112.py',W/'tests/test_guarded_retention_ev112.py',W/'tests/fixtures/feasible-witness-1171-190.npz',W/'tests/fixtures/feasible-witness-1171-190.json',R/'kit7-hybrid-pilot-20261026/candidate/report.json',R/'kit7-hybrid-pilot-20261026/candidate/all-protected-audit.json',R/'kit7-hybrid-pilot-merged-20261026/merge-verification.json',R/'kit7-hybrid-pilot-roads-20261026/review.json',R/'kit7-hybrid-rebase-tests-20261026/result.json',R/'audit_kit7_hybrid_all.py',R/'merge_kit7_hybrid_relief.py',R/'validate_kit7_hybrid_rebase.py',R/'kit7-existing-hybrid-rebased-diagnostic.json']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p):sha(p) for p in paths}
(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
brief='''Revisión final READ ONLY Fable5.1 nativo, máximo650palabras. Codex executor, Fable reviewer independiente. No comandos/MCP/escrituras/subagentes. Solo Read/Glob/Grep. El usuario autorizó corrección autónoma y commit/push de unidades comprobadas; no desplegar aquí.
Cambio mínimo en tools/terrain/repair_guarded_shapes_ev112.py: permitir --hybrid-witnesses sin --retain-candidate, quitando solo la restricción CLI. Solver repair_free_shapes_ev112.py volvió EXACTAMENTE a su SHA anterior5f575db39c594f231860528b69bc515e0ebc4c00ac9ab249fbe5b992c791aad0. Tests test_hybrid_witnesses_ev112 y test_guarded_retention_ev112 añaden fixture real e integración fresh;29testsPASS. Plan plans/ev112-rebased-hybrid-relief-20261026.md. Lista de fuentes/evidencia en E:/DayZ-Baltic-Build/shape-repair-20261025/kit7-hybrid-rebase-review-20261026/source-hashes.json.
Corrección importante respecto a la review del planMILP: el grupo1171,190 había sido OMITIDO por contexto en el lote híbridoE. Nunca se había probado híbrido sobre la base kit7. Comparación posterior demuestra que el modo existente también resuelve el caso, prácticamente misma energía que el pilotoMILP. Por ello NO se promueve el helperMILP; prototipo archivado fuera del repositorio. No revises código abandonado como si estuviera en producción.
Piloto fresco aislado kit7-hybrid-pilot-20261026/candidate:14vértices libres suben como máximo0,594242811m; ápice fijo; prominencia0,299900055; energía164,129606→161,897188; todos los guards locales/globales autorPASS. Auditoría independiente rederiva free/shore/road,2extremos protegidos afectados,0coronas indebidas. Bury0cambios,huella exacta; P11carreteras77559muestrasPASS. Censo exhaustivo de formas sigue calculándose y no se da por pasado; deberá terminar antes de publicar la aceptación offline. No hay bosque/stage/binario/native/visual y no se heredará nav607. Generador actual independiente permanece sobre kit7 original.
Busca regresiones concretas, falsosPASS y criterio insuficiente en el diff mínimo y sus consumidores. Emite SOUND / SOUND-with-fixes / NEEDS-WORK, hallazgos con path:line y fix, límites. No pedir aceptación global de todos los ríos para esta unidad aislada. La ausencia de nueva versión de solver es una ventaja de alcance, no una prueba en sí misma.
'''
(O/'review-brief.md').write_text(brief,encoding='utf-8')
args=['C:/Users/guill/.local/bin/claude.exe','--print','--safe-mode','--model','claude-fable-5-1','--effort','medium','--tools','Read,Glob,Grep','--allowedTools','Read,Glob,Grep','--output-format','json','--no-session-persistence']
with (O/'review-response.json').open('wb') as out,(O/'review-stderr.log').open('wb') as err:
    p=subprocess.Popen(args,cwd=W,stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=0x08000000);start=time.monotonic()
    (O/'process.json').write_text(json.dumps(dict(pid=p.pid,args=args),indent=2)+'\n')
    try:p.communicate(brief.encode(),timeout=300)
    except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=30);raise
    assert all(sha(Path(k))==v for k,v in before.items())
    (O/'completion.json').write_text(json.dumps(dict(returncode=p.returncode,seconds=time.monotonic()-start,inputs_unchanged=True),indent=2)+'\n')
    print('FABLE_EXIT',p.returncode);raise SystemExit(p.returncode)
