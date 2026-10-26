from pathlib import Path
import hashlib,json
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'kit7-nav-consumer-plan-review-20261026';O.mkdir(exist_ok=False)
paths=[W/'plans/ev112-kit7-navigation-consumer-20261026.md',R/'discover_kit7_nav_routes.py',R/'discover_kit7_packed_nav.py',W/'tools/navigation/verify_continuity_nav_v30.py',W/'tools/terrain/verify_v30_acceptance.py',W/'tools/navigation/verify_patch_nav_coverage_ev112.py',W/'missions/BalticV30ContinuityNavV1.BalticTrial/init.c']
(O/'source-hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
brief='''Asiento reviewer independiente, SOLO LECTURA, familia Anthropic mediante claude-fable-5-1 nativo. Codex integra. Tu ruta ya produjo revisión SOUND esta misma fecha en kit7-nav-coordinator-fix-review-20261026/review-response.json. Presupuesto300s. No comandos, escrituras, MCP ni subagentes. Usa solo Read/Glob/Grep. La generación nav propia está activa y no debe interrumpirse.
Revisa el plan antes de implementar el nuevo consumidor. Objetivo: probar 139piezas/138juntas/2extremos del kit7 con562consultas locales y45regresiones, con cobertura geométrica de los binarios reales, sin falsosPASS por esquivar modelos. Física6801/6801 yaPASS. Ruta planeada se fija antes de FindPath. Todos los umbrales antiguos permanecen. RetargetY solo2puntos porque el terreno sícambió. No se pretende locomoción ni cobertura global.
Entrégame SOUND / SOUND-with-fixes / NEEDS-WORK y hallazgos concretos accionables con fuente/línea, mecanismo e impacto. Comprueba coherencia de las pruebas geométricas, extremos exteriores, false-green, negativos y presupuesto. No inventes necesidad de probar todos los infinitos recorridos. No implementes. Salida por stdoutJSONcapturado por orquestador. Revisión recibida/adjudicada aquí por Codex.
Entradas pequeñas congeladas:\n'''+ '\n'.join(str(p) for p in paths)+'''
Datos grandes de descubrimiento solo si necesitas una sección concreta (no cargar enteros): R/kit7-nav-route-discovery-20261026/proposals.json; R/kit7-packed-nav-discovery-20261026/geometry.json. R=E:/DayZ-Baltic-Build/shape-repair-20261025. FuentePGFilter/AIWorld P:/scripts/3_game/AI/aiworld.c:55-123; game.c:923,1177. Producer existente ya ejecutó esos API. OPRWtabla heurística yLODreader tienen límites explícitos; no son navegación nativa.
'''
(O/'review-brief.md').write_text(brief,encoding='utf-8')
s=(R/'run_kit7_nav_fix_review.py').read_text().replace('kit7-nav-coordinator-fix-review-20261026','kit7-nav-consumer-plan-review-20261026')
(R/'run_kit7_nav_consumer_plan_review.py').write_text(s)
