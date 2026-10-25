"""One-shot, scoped documentation close. No changes to terrain or runtime."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re

root = Path('P:/DayZ_Baltic_12km_dev')
vault = Path('C:/Users/guill/ObsidianVault/AI')
out = root / 'evidence/foundation-followup-2026-10-01/handoff-complete-v29'
backup = out / 'before'
backup.mkdir(parents=True, exist_ok=False)
now = dt.datetime.now(dt.timezone.utc).isoformat()
canonical = vault / '30_Sessions/2026-10-01-dayz-baltic-handoff-base-v29.md'
link = '<C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-01-dayz-baltic-handoff-base-v29.md>'
paths = {
    'HANDOFF.md': root / 'HANDOFF.md',
    'BUGS.md': root / 'BUGS.md',
    'state.json': root / 'evidence/foundation-followup-2026-10-01/state.json',
    'outline-v33-checkpoint.md': root / 'evidence/foundation-followup-2026-10-01/outline-v33-checkpoint.md',
    'product-spec.md': root / 'product-spec.md',
    'project-brief.md': vault / '10_Projects/DayZ_Baltic_12km/project-brief.md',
    'validation-matrix.md': vault / '10_Projects/DayZ_Baltic_12km/validation-matrix.md',
    'continuation.md': vault / '30_Sessions/2026-10-01-dayz-baltic-continuacion-base.md',
    'index.md': vault / '30_Sessions/index.md',
    '_estado-proyectos.md': vault / '10_Projects/_estado-proyectos.md',
    'PROJECT-MAP.md': root / 'PROJECT-MAP.md',
}
original = {k: p.read_bytes() for k,p in paths.items()}
for k,b in original.items(): (backup/k).write_bytes(b)
changes = []
def write(key, text):
    p = paths[key]
    assert p.read_bytes() == original[key], f'Concurrent edit: {key}'
    old = original[key].decode('utf-8-sig').replace('\r\n','\n')
    assert len(text) >= .9*len(old), f'Unexpected shrink: {key}'
    p.write_text(text, encoding='utf-8', newline='\n')
    changes.append({'path':str(p), 'before_sha256':hashlib.sha256(original[key]).hexdigest(), 'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
def read(key): return original[key].decode('utf-8-sig').replace('\r\n','\n')

h = read('HANDOFF.md')
a=h.index('<!-- LIVE-STATE:START -->'); b=h.index('<!-- LIVE-STATE:END -->',a)
live = h[a:b]
print('Existing LIVE-STATE characters:', len(live))
updates = {
 'updated': now,
 'status': 'HANDOFF_V29_PARTIAL_ACCEPTANCE_NO_ACTIVE_RUNTIME',
 'terrain': 'ACTUAL V29 ed6cdaa5; 2048x2048 a6m/12.288km. Seis gates offlinePASS,239126secciones viales,621260extremos de orilla;0infracciones. Agua/fairways/islas/reserva/Narva protegidos. Delta max5.079304m contraV33; compuesto<=6m contraV10.',
 'native': 'ACTUAL road_v29.tv4p; r2 1763facc/r3 9cd94334 con cierre/reapertura reales. Alturas/materiales/10161poses iguales semanticamente. Literales FAILestrictoV10 por670residuosY heredados<=0.954micrometros; solo derivados explicitos restaurados. Provenance y negativos en road-v29-native.',
 'package': 'ACTUAL @DayZ_Baltic_RoadV29: world b3418f92, compiledWRP2c95ab7d, waterf9a5cdf7, NMfacaf1e3/445971256bytes. Otras6826entradas exactas. V10d1008dd6 yV3338ebe847 rehasheados intactos al cierre. RoadV29Data es intermedio conNMheredada: no entrega jugable.',
 'navmesh': 'ACTUAL V29966289/966289teselas,12.5m; guardada/empaquetada desdeWRP2c95ab7d. Decoder estructuralTESM6,1091979poligonos. ConsumidorV7 separado; regenerar tras mapeado. Recibo road-v29-native/nav-generation-saved.json.',
 'boat': 'HEREDADO V10:12segmentos seleccionados/26.600558km aceptados entre runs aislados; V29 conserva fairways/modelos protegidos, sin repetir lancha en PBO final. No viaje continuo unico,flotilla,tripulantes ni barco mediano. Fallos anteriores preservados.',
 'ai': 'HEREDADO V10 cruce continuoV4 control+ambos sentidosPASS/18negativos. ACTUAL V29 queries314/15PASS y carga100vivos/despiertos; load INCONCLUSIVEpor deriva objetivo2.06473m. No locomocion fisica regional completa ni100jugadores.',
 'driving': 'ACTUAL V29 seis rutas costa/colinas/sur ida/vueltaPASS entre DriveV3 casos0..3 yV4 casos0..1;5282.735m acumulados/2641.368m unicos,salud1000/4contactos,18negativos. DriveV3 5PASS/1FAILterminal conservado. No toda red ni piezas colocadas.',
 'visual': 'V29 PENDIENTE: grupo agua con foco ajeno/entrada humana; CU reseteado sin insistir. Neva/reserva/surV29 referencias preparadas, no ejecutadas. V33 tiene capturas historicas; texturaWorldCover provisional. Crash transicion lejana BALTIC001 abierto.',
 'performance': 'V29 INCONCLUSIVE_ACTIVE_LOAD:0/25/100/0 completo,60muestras/fase,420host/proceso. Objetivo deriva2.06473m>2m fases2/3. Sitios101/rutasWALK100PASS;servidor~2.50-2.52GiB. Escritorio no aislado; noFPS ni capacidad80-100. HistorialV10PASS no sustituye esta prueba.',
 'archive': 'Checkpoint ZIP anterior V10 f96d3d5c, no V29. Manifest/snapshots documentales V29 en handoff-complete-v29; fuentes editables yPBO actuales en workspace. Falta checkpoint V29 completo tras aceptar base. DependenciasP/vanilla/junction no portables.',
 'coordination': 'CIERRE: load ebffaa12 EXITED_ORDERLY cliente/servidor;420muestras cada sampler;4logs archivados. Lease liberado; selfnone/boxempty/sinforeign. Sin DayZDiag/TB/NavMeshGenerator/AddonBuilder. ComputerUse reset/OFF. No operaciones UI nuevas.',
 'next': 'Ante nueva peticion: revisar handoff completo; visual Neva/reserva/sur con escritorio disponible yrefs congeladas; aislar deriva del fixtureload sin relajar2m; repetir carga en reposo. No reactivar automaticamente noche8h. Base aun sin aceptacion1.0.',
 'skills': 'dayz-terrain-workflow/references/regional-relief.md actualizado: persistencia observada,residuos heredados y especificidad aguaV7. SHA61e52ae3; SKILL.md intacto. Recibos skill-persistence-update/skill-consumer-specificity-update. No skill nueva redundante.',
 'closure': 'Peticion viva: handoff completo. Pruebas y procesos cerrados. Ventana nocturna02:42:43-10:42:43UTC previa completada/heartbeatPAUSED;unreset anterior;ningunreset nuevo consumido. Cuota individual pendiente no es accion de continuacion.',
}
for key,value in updates.items():
    live,n = re.subn(r'^'+re.escape(key)+r':.*$', key+': '+value, live, flags=re.M)
    assert n == 1, key
live += 'bugs: 8 registros;5aceptados con alcance,1abierto,1parcial abierto,1inconcluso. BUGS.md autoridad.\n'
live += 'handoff_complete: '+str(canonical).replace('\\','/')+'\n'
new = h[:a]+live+h[b:]
assert h[b:] == new[new.index('<!-- LIVE-STATE:END -->'):], 'History changed'
old_pointer='Ver LIVE-STATE y `evidence/foundation-followup-2026-10-01/outline-v33-checkpoint.md` para el trabajo actual. El archivo nocturno conserva el hito anterior. `continuation-v9.md` conserva el estado anterior.'
assert old_pointer in new
new=new.replace(old_pointer, f'Leer primero el [handoff completo V29]({link}), LIVE-STATE y `evidence/foundation-followup-2026-10-01/state.json`. El checkpoint y los apartados siguientes conservan historia; no son una instruccion de retomar pruebas ni describen procesos activos.')
write('HANDOFF.md',new)

s=json.loads(read('state.json'))
s.update(status='HANDOFF_V29_PARTIAL_ACCEPTANCE_NO_ACTIVE_RUNTIME',updated_utc=now,active_run=None,run_id=None,
 own_processes='None: exact owned load client/server orderly closed; samplers exit0; status none/empty.',
 computer_use='Reset/OFF; no further UI work during handoff.',
 runtime_pending='No running test. Final visual acceptance and a valid bounded load test remain pending.',
 remaining=['Visual acceptance on final V29 at frozen local camera groups','Isolate target drift in load fixture, then repeat controlled load without relaxing criteria','Close base acceptance and create full V29 recoverable checkpoint; mapping remains later'],
 canonical_handoff=str(canonical).replace('\\','/'))
s['last_run_closed']='ebffaa12-9252-4a77-88a9-ffb4706dde99'
s['coordination']={'self_state':'none','box_occupied':False,'runs':[],'foreign':[],'receipt':'road-v29-load/cleanup.json'}
s['road_v29_load']={'status':'INCONCLUSIVE_ACTIVE_LOAD','issues':['phase2:prey_moved','phase3:prey_moved'],'prey_drift_max_m':2.06473,'limit_m':2,'engine_complete_s':385.266,'samples_per_phase':60,'host_samples_each':420,'sites':101,'walk_routes':100,'sites_status':'PASS_LOAD_SITES_WALK_QUERIES','evidence':'road-v29-load/runtime-complete/verification.json','cleanup':'orderly_close'}
s['skills']='regional-relief native persistence and consumer specificity updated; latest SHA61e52ae3; no new skill.'
write('state.json', json.dumps(s,ensure_ascii=False,indent=2)+'\n')

checkpoint=read('outline-v33-checkpoint.md')
checkpoint=checkpoint.replace('Estado: persistencia nativa, paquete final y navmesh V29 verificados; consumidor regional PASS. Seis recorridos fisicos de coche en curso.','Estado al cierre: V29 geometria/nativo/navmesh, consumidor regional, seis recorridos y agua local aceptados en su alcance. Carga INCONCLUSA y visual final pendiente; no version1.0.')
checkpoint=checkpoint.replace('Computer Use esta reseteado; lease mantenido durante la prueba fisica.','Computer Use reseteado/OFF. Ultimo run cliente/servidor cerrado ordenadamente; lease liberado y runtime vacio.\n\nHandoff completo: [sesion V29]('+link+').')
checkpoint=checkpoint.replace('## Siguiente bloque','## Secuencia prevista entonces — historica, ya sustituida')
checkpoint=checkpoint.replace('BALTIC-005/007 siguen abiertos hasta consumidores y render.','BALTIC-005 aceptado para geometria y seis viajes; BALTIC-007 sigue abierto en render; BALTIC-008 carga inconclusa por deriva2.06473m frente2m.')
checkpoint+='\n## Cierre solicitado por el usuario\n\nDriveV3 conserva5PASS/1FAIL; DriveV4 ambos sentidos surPASS con18negativos, sin cambiar terreno ni criterios. Cobertura consolidada road-v29-driving-coverage.json:5.282735km acumulados/2.641368km unicos. AguaV29:646epocas/15504muestrasPASS, minimo margen seco0.28495m,18negativos. Carga0/25/100/0 completa,420host/proceso:INCONCLUSIVE_ACTIVE_LOAD por deriva del objetivo2.06473m>2m; sitios101/rutasWALK100PASS. No repetir ni relajar en este cierre. Cuatro logs archivados y cierre orderly; sin runtime propio. Referencias visuales Neva/reserva/sur listas, sin ejecutar en V29.\n'
write('outline-v33-checkpoint.md',checkpoint)

bugs=read('BUGS.md')
bugs=bugs.replace('Estado de pruebas de la sesión nocturna01-10-2026. El paquete bajo prueba es\n`@DayZ_Baltic_FoundationV10Native`, mundo SHA256 `d1008dd6c882193706f06c5e7b8495ee1a357f5819a8574118784f7e90f18577`.\nLas variantes fallidas se conservan y no sustituyen ese paquete.', 'Estado al handoff completo01-10-2026. Candidato actual: `@DayZ_Baltic_RoadV29`, mundo SHA256 `b3418f927f6cc4adf8ba03b86de0ce1491f32adf87f3a124120c62eff20f856e`. V10/V33 son baselines preservados. Los resultados inferiores identifican la version concreta; no se hereda automaticamente un PASS.')
bugs=bugs.replace('V29 geometria/nativo/navmesh/V7 PASS; agua dinamica local y render del paquete final pendientes','V29 geometria/nativo/navmesh/V7 y agua dinamica localPASS; visual final pendiente')
assert '| BALTIC-008 |' not in bugs
row='| BALTIC-008 |INCONCLUSO|Fixture de carga, deriva del objetivo|V29 0/25/100/0 completo; deriva2.06473m>2m en fases2/3. No causa aislada ni aceptacion de rendimiento|'
bugs=bugs.replace('\n\n| BALTIC-007 |','\n| BALTIC-007 |')
marker='\n\nR1: cada ID'
assert marker in bugs
bugs=bugs.replace(marker,'\n'+row+marker,1)
bugs+='\n## BALTIC-008 — Carga V29 inconclusa por deriva\n\nRun ebffaa12-9252-4a77-88a9-ffb4706dde99, mundo b3418f92; referencia f126e20c. COMPLETE385.266s;60muestras/fase y420host/proceso. Fases2/3 objetivo a2.06473m del inicial, limite congelado2m: INCONCLUSIVE_ACTIVE_LOAD.100infectados vivos/despiertos y salud100 no anulan ese fallo del contrato. Sitios101/WALK100PASS. No cambiar tolerancia ni llamar esto fallo de terreno: causa no aislada, escritorio compartido. Proximo: discriminador del fixture y repeticion en reposo, conservando este resultado. Evidencia: evidence/foundation-followup-2026-10-01/road-v29-load/runtime-complete/verification.json. Ambos procesos orderly_close,lease liberado.\n\nActualizacion BALTIC-007: agua localV29 PASS646epocas/15504muestras,minimo margen seco0.28495m y18negativos. ObservacionUI INCONCLUSIVE_FOREGROUND_INTERFERENCE, CU reseteado; render final y calidad global siguen pendientes. No sustituye mareas globales con24puntos.\n'
write('BUGS.md',bugs)

product=read('product-spec.md').replace('El puente de Narva a tablero2m es provisional y no satisface este requisito.','El antiguo ensayo de Narva a tablero2m no satisface este requisito; el candidato posterior debe acreditarlo con su geometria y consumidores identificados en el HANDOFF.')
product=product.replace('El criterio de relieve selectivo está aprobado; las cotas regionales y niveles de agua finales siguen por diseñar y validar.','El criterio de relieve selectivo está aprobado; las cotas del candidato regional ya estan implementadas y medidas, con aceptacion final segun HANDOFF. No confundir ese candidato con una decision de cerrar todos los niveles de agua.')
write('product-spec.md',product)
brief=read('project-brief.md').replace('con cotas regionales por diseñar.','con cotas del candidato y su validacion en los planes y HANDOFF del repo.')
brief+='\n## Punto de continuacion\n\n[Handoff completo de la base V29](../../30_Sessions/2026-10-01-dayz-baltic-handoff-base-v29.md), cierre01-10-2026. Documento de entrada para artefactos, evidencia y pendientes; LIVE-STATE conserva autoridad sobre el estado posterior.\n'
write('project-brief.md',brief)

matrix=read('validation-matrix.md').replace('## Estado vigente — base V10, cierre de pruebas nocturnas01-10-2026','## Historico — base V10, cierre de pruebas nocturnas01-10-2026',1)
intro='''## Estado vigente — candidato V29, handoff completo01-10-2026

Fuente detallada: [handoff V29](../../30_Sessions/2026-10-01-dayz-baltic-handoff-base-v29.md). Paquete b3418f92/WRP2c95ab7d/NMfacaf1e3/agua f9a5cdf7; los bloques inferiores son historicos.

| Gate | Resultado actual | Limite |
|---|---|---|
| Geometria conjunta |Seis gates offlinePASS;239126secciones,621260extremos costeros;7+4negativos|Sin aceptacion visual global|
| Persistencia TB |r2/r3 iguales por identidad tras cierre/reapertura reales;10161poses|670residuos heredados solo restaurados en derivados explicitos; literalesFAILV10 conservados|
| NM y paquete |966289teselas, NM nueva445971256bytes;6826entradas restantes exactas|Regenerar tras colocar objetos|
| Motor regional |81212agua/tierra,314nav,15rutasPASS;9controles|Queries no son locomocion|
| Conduccion V29 |Seis viajes entreV3/V4,5.282735km/2.641368unicos;18negativos|V3 5PASS/1FAIL conservado; no toda la red ni piezas colocadas|
| Agua local V29 |646epocas/15504muestrasPASS,margen seco0.28495m;18negativos|24posiciones y ventana observada; no maximo global ni render|
| Sitios de carga |101sitios/100rutasWALKPASS|Antes de carga; no capacidad|
| Carga V29 |INCONCLUSIVE_ACTIVE_LOAD;0/25/100/0 completo;420host/proceso|Deriva2.06473m>2m fases2/3; escritorio no aislado; no80-100jugadores|
| Visual V29 |PENDIENTE; referencias Neva/reserva/sur preparadas|Foco/entrada humana impidieron observacion final; CU liberado|
| Herencia V10 |12tramos lancha26.600558km y cruce continuoIA ambos sentidos aceptados|No repetidos fisicamente sobrePBO finalV29|
| Cierre |Ultimo run cliente/servidororderly_close;4logs archivados;lease liberado|No version1.0; mapeado despues|

'''
matrix=matrix.replace('# Matriz de validación\n\n','# Matriz de validación\n\n'+intro,1)
write('validation-matrix.md',matrix)
cont=read('continuation.md')
cont=cont.replace('\n\n','\n\n> Continuacion cerrada: leer el [handoff completo V29](./2026-10-01-dayz-baltic-handoff-base-v29.md). Los checkpoints inferiores son historicos; ningun run de esta sesion sigue activo.\n\n',1)
write('continuation.md',cont)
index=read('index.md')
filename='2026-10-01-dayz-baltic-handoff-base-v29.md'
assert filename not in index
index=index.replace('## 2026-10-01\n','## 2026-10-01\n\n- [DayZ Baltic12km — handoff completo de la base V29](./'+filename+') — editable, paquete y NM finales; geometria/agua/conduccion acotadas PASS; visual pendiente y carga inconclusa; runtime liberado.\n',1)
index=index.replace('— V33 probado; V29 geometría conjunta PASS e importada, corrección de objetos pendiente de exportación; pruebas V7/V3 preparadas.','— historial de la continuacion; cierre y estado actual en el handoff completo V29.')
write('index.md',index)
status=read('_estado-proyectos.md')
start=status.index('## DayZ_Baltic_12km —'); end=status.index('\n## ',start+4)
body='''## DayZ_Baltic_12km — candidato V29 y handoff completo01-10-2026

Recorte aprobado12.288km, vanilla primero,80–100jugadores objetivo. Agua/SPB/Narva/reserva protegidos; mapeado despues del terreno. [Estado vivo](<P:/DayZ_Baltic_12km_dev/HANDOFF.md>) y [handoff completo](../30_Sessions/2026-10-01-dayz-baltic-handoff-base-v29.md).
V29 persistida en TB; mundo b3418f92/WRP2c95ab7d/NMfacaf1e3/agua f9a5cdf7. Geometria conjunta,81212puntos/314nav/15rutas,agua local y seis viajes de cochePASS. V10/V33 intactos;12tramos de lancha26.600558km y cruce continuoIA son pruebas anteriores con alcance explicito.
Carga V29 completa0/25/100/0,420host/proceso, INCONCLUSA por deriva objetivo2.06473m>2m. Visual final pendiente, textura provisional. No80–100clientes acreditados ni mapa1.0; sin arboles/ciudades colocados. Ultimo run cerradoordenadamente,lease libre,CUreset. No reactivar noche8h desde este snapshot.
Sin concurrencia conExta; no hay ASC suyo incorporado. Historia: [sesion nocturnaV10](../30_Sessions/2026-10-01-dayz-baltic-12km-sesion-nocturna.md) y [continuacion](../30_Sessions/2026-10-01-dayz-baltic-continuacion-base.md). Proyecto hermano: [[IberiaMap|IberiaMap]].
'''
write('_estado-proyectos.md',status[:start]+body+status[end:])
(out/'document-changes.json').write_text(json.dumps({'utc':now,'changes':changes,'backup':str(backup),'scope':'Only this project records and its entries in shared indexes; no terrain/runtime mutation.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'updated':len(changes),'backup_files':len(original),'canonical':str(canonical)},ensure_ascii=False))
