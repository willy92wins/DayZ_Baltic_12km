from pathlib import Path
import hashlib,json
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=R/'kit7-nav-consumer-20261026';O=R/'kit7-nav-postprocess-fix-review-20261026';O.mkdir(exist_ok=False)
paths=[W/'tools/navigation/verify_kit7_nav_ev112.py',R/'orchestrate_kit7_nav_probe.js',R/'finish_kit7_nav_probe.py',R/'package_and_deploy_kit7_nav9.py',R/'test_kit7_nav_consumer_v2.py',R/'test_kit7_nav_probe_flow_v2.cjs',D/'synthetic-controls-v2/result.json',D/'coordinator-controls-v2.json',D/'command-flow-controls-v2.json']
(O/'source-hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
brief='''Reviewer independiente Fable5.1 vía CLI nativo, SOLO LECTURA Read/Glob/Grep; no comandos, escrituras, MCP ni subagentes. Disponibilidad medida esta fecha con revisión previa. Codex integra. Presupuesto300s.
Revisión de fixes tras SOUND-with-fixes en R/kit7-nav-postprocess-review-20261026/review-response.json. Verifica cierre de1..4 y opcional5, y regresiones introducidas por el fix. Fuentes revisadas previas conservadas conSHAen reviewed-source de aquel directorio.
1readiness60x5s; test slow_readiness35esperas pasa, timeout60rechaza/cierra.2 finish usa hashrefen frozen.inputs; todo manifest hashverificado antes.3 verify recalcula corredor desdecenterline, allowedmodels, exterior solo caps, agua/coberturacontinua, simdiff<1e-6; fija0.801exacto.19controlessintéticosahora rechazan umbralrelajado,corridor/exteriorfalso,centrolineamodificada ademásdeanteriores.4 finish liga nombrelogfrozen.UUID.5 versiónexacta compara mcp-aftergeneración; suSHAse añade ainputsdeployment al empaquetar. frozen.jsonse sellarádespuésdeesta revisión ysuSHAse incluiráenaccepted.inputs, cerrando nota6sobreidentidaddefrozen.
Info6/plan: cuatroexcesosdelcorredororiginal yseisrutasconallowedextra son métricasdistintas: lasdoscap_tail ya teníanexteriorpermitidoencribadoinicial. No cambiancriteriosnisemántica.
19controlesconsumer+11fixturesgeométricos+11flujosmock+8wrapper. No navegación nativa todavía. Generaciónpropia activaencell229, no tocar. Entregable SOUND/SOUND-with-fixes/NEEDS-WORK con solo hallazgosconcretosresidualesbloqueantes. No reabrirglobal/locomoción/nuevasfeatures.
R=E:/DayZ-Baltic-Build/shape-repair-20261025. Entradascongeladas:\n'''+ '\n'.join(str(p) for p in paths)
(O/'review-brief.md').write_text(brief,encoding='utf-8')
s=(R/'run_kit7_nav_fix_review.py').read_text().replace('kit7-nav-coordinator-fix-review-20261026','kit7-nav-postprocess-fix-review-20261026')
(R/'run_kit7_nav_postprocess_fix_review.py').write_text(s)
