from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'kit7-nav12-generation-review-20261027'
O.mkdir(exist_ok=False)
paths=[W/'plans/ev112-kit7-nav12-cost-20261027.md',R/'kit7-nav12-plan-review-20261027/accepted.json',W/'tools/navigation/package_nav12_config_ev112.py',W/'tests/test_nav12_config_ev112.py',W/'tools/navigation/inspect_navmesh_v9_ev112.py',W/'tests/test_navmesh_v9_prefixes_ev112.py',R/'orchestrate_kit7_nav12_generation.js',R/'test_kit7_nav12_generation.cjs',R/'nav-kit7-12m-preparation-20261027/generation-controls.json',R/'nav-kit7-12m-preparation-20261027/launch-inputs.json',R/'package-kit7-nav12-input-20261027/verification.json',R/'prepare_kit7_nav12_generation.py',R/'fix_nav12_generation_lifecycle.py']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths}
(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
brief='''Revisión adversarial READ ONLY de la implementación Nav12, Fable5.1 por CLI nativo. Codex es executor/integrador, tú otra familia. Solo Read/Glob/Grep; NO procesos, MCP, Git, subagentes, escritura en ningún lugar ni memoria. El cwd no contiene permisos: tampoco escribas fuera. Devuelve en stdout máximo1000palabras con SOUND / SOUND-with-fixes / UNSOUND, hallazgos con path:line, consecuencia y repro ejecutable o contradicción para bloqueantes. No modifiques nada. CLI2.1.310, Fable5.1 completó hoy la revisión del plan; esta llamada reconfirma disponibilidad e identidad.

W=C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c. R=E:/DayZ-Baltic-Build/shape-repair-20261025. Archivos y hashes en R/kit7-nav12-generation-review-20261027/source-hashes.json. Empieza por el plan W/plans/ev112-kit7-nav12-cost-20261027.md, R/orchestrate_kit7_nav12_generation.js, R/test_kit7_nav12_generation.cjs y R/nav-kit7-12m-preparation-20261027/generation-controls.json. Mira empaquetador/inspector/tests y preparación por las dimensiones del review; consulta fuentes restantes solo para verificar contratos. No audites otros módulos ni rediseñes gates futuros.

Contexto: Nav8 corrigió las4alturas (607PASS) pero falla RAM propia en6pasadas nuevas1.26591/1.24133 frentea1.10; todo publicado preservandoFAIL. PlanNav12 revisado SOUND-with-fixes y reconciliado: experimentoaislado12m, sin cambio de terreno/modelos/protecciones, mismos607/.801/.011/2.1 y nuevos6RAM1.10/5% trasPASS. No hay ninguna generación12nativa lanzada ni aceptación de producto. Consumidor607 y RAM se prepararán aparte, con los mismos oráculos, mientras genera si este gatepasa. Tu alcance es que el input y la generación sean seguros y no puedan declararse verdes sin evidencia; no juzgar código futuro inexistente.

Implementado: empaquetador12.5->12 específico, roundtripconfig y6826entradas byteexact. Input PBO ed1acb1d993a705996edad1bc3008f14e0b904483ad207d5b903a4d2aee35287 conservaNM12.5 para generación, noPASSgeométrico. Inspector añade12 explícito y requerirágrid1024x1024. Config3tests y prefijos6testsPASS. Coordinador derivado del8ejercitado, pero cmdrenueva conbeatrecuperable; después de caducar NO registraeventosporshellantesde readoptarsumismoRUNNING_IDLEy comprobaridentidad. Persistepresupuesto desdegeneration.json.started_utc:18000sgenerador/18300scoordinador (300s yaexistentesparahash/cierre), ambasfechasfijas; recuperacióncontrasta recibo contraoriginal/caché. Cancelaciónnativarequiereleasepropioyproceso coincidente; no toca procesos con propietarioajeno. FIFOdirecto600s,sinprelease/preconsulta. Cierreoficialyobservadororiginalestricto; nohereda excepción de cancelación8.

26 escenarios de control y8mutantesrechazados; artefacto indica alcance MOCK, nopretenden nativo. Casosnuevos:expiry_during_command,expiry_after_budget,budget_changed/missing_on_recovery,budget_preexists,expiry_with_foreign_owner,expiry_pid_reuse. Ataca falsoPASS delcoordinador, presupuestoreiniciado, recursióndebeat/registro y confusión depropiedad; verificaquecontrolespruebensucontrato, no solo untransformadoidéntico. La lista deproducto es plan§4: código+repros, inputexacto, generaciónpropiaexit0/inspector/cierre; luego607yRAMenfasesseparadas. Presupuesto: dosrondasdecódigoconrepros; noañadircontadoresdeformaarbitrarios.

Incidente resuelto antesdegenerar: Cseagotóal copiarinput12. Se retiró solo lacopia parcial propia; Nav8InputyNavV9 archivadosbyteexactaR/archived-mods-nav12-space-20261027 conmanifestyrestauración; Nav8funcional yOverlap6801sigueninstalados. Input12ya está completo, preflight32inputs (ahoraampliadosporlifecycle). No inferir corrupción de los paquetes conservados ni pedir permiso nuevo. El planaceptado registra esta nota ylos300sdecoordinador; no cambia límites.

Salida: findings concretos y límites de tu comprobación. Diferencia bloqueante reproducible de mejora opcional o incertidumbre ya cerrada por el consumidor nativo futuro. Si algo no permite este lanzamiento, di exactamente qué archivo/contrato/repro lo bloquea. No solicites otro council ni escribas código.
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
