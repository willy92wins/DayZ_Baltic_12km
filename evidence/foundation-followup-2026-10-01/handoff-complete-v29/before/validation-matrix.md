# Matriz de validación

## Estado vigente — base V10, cierre de pruebas nocturnas01-10-2026

Fuente única detallada: [informe nocturno](<P:/DayZ_Baltic_12km_dev/evidence/overnight-2026-10-01/README.md>)
y [LIVE-STATE](<P:/DayZ_Baltic_12km_dev/HANDOFF.md>). Los bloques anteriores se
conservan más abajo como históricos; no describen la variante desplegada V10.

| Gate | Resultado | Alcance pendiente |
|---|---|---|
| Native V10 |WRP reabierto cdd6838f; alturas/materiales/10161poses exactos|La importación anteriorV9 no es el entregable actual|
| Agua y outline |81212muestras reales,0fallos; protegidoXY/agua/islas/reserva|No implica todas las orillas recorridas|
| NM final |e8348efc;966289teselas;449360340bytes;314puntos/15rutasPASS|El grafo no sustituye IA física|
| Paquete |@DayZ_Baltic_FoundationV10Native; mundo d1008dd6/agua f9a5cdf7|Baselines0.2/outline preservados|
| Narva |Puente225m/tablero11m; accesos8m/5.067%; coche ida/vuelta1.019kmPASS|Solo hasta26.9km/h; otras vías físicas pendientes|
| Lancha |V3 ocho sectores ida/vueltaPASS; largos9PASS/3FAIL sobre26.601km|Narva6 muestreo de objetivos; delta8/10 deriva final; sin tripulantes/casco mediano|
| IA |V3 completo20PASS/6FAIL; continuasV1/V2 con control localPASS|Puente sin aceptar; objetivo humano se desvía durante persecución|
| Humano sinAI |PASS control y cruce este294.082m,973muestras,desviación0.357m|No prueba IA ni causa única del fallo; regreso no ensayado aquí|
| Render |Siete grupos/12poses+restauraciónPASS; Narva/SPB/norte con píxeles útiles|Neva/reserva/sur/conjunto parciales; crash distante sin causa aislada|
| Carga |0/25/100/0,420muestras host cada proceso;100vivos/activos; servidor~2.52GiB|Sin80–100clientes/CE/ciudades; CPU no causal; intervalo185msfinal|
| Recuperación |CheckpointZIP f96d3d5c,miembros/fuentes verificados|RutasP/junction yvanilla externos; no instalador portable|

El mapeado sigue después según P10: no hay ciudades, vegetación colocada ni red
completa de piezas de carretera. No se declara versión1.0 ni capacidad80–100.

## Histórico — outline y relieve regional30-09-2026

Fuente: [informe regional](<P:/DayZ_Baltic_12km_dev/evidence/regional-outline-v3/README.md>)
y [LIVE-STATE](<P:/DayZ_Baltic_12km_dev/HANDOFF.md>). P12/P13, misma huella aprobada.

| Gate | Resultado verificado | Límite |
|---|---|---|
| Relieve selectivo V3 |1.672.627 vértices modificados, máximo109.5685m, pendientes afectadas<=34.1696°|Sin cambios en máscaras de agua, reserva, SPB, Narva ni corredores|
| Persistencia nativa |4194304 alturas exactas tras Rebuild, guardar, reabrir y exportar; WRP9bf50853|Primera exportación antigua FAIL conservada; no Generate Layers|
| Outline y reserva |6 áreas,11229 segmentos, SHP/GeoJSON releídos; reserva6.04km²|Envolvente de diseño; bosque futuro sin colocar y rasantes pendientes|
| Navmesh50/25 |253/279 y276/279 puntos;2/6 y4/6 rutas|FAIL3D conservados, mismo WRP y umbral2m|
| Navmesh12.5 |eb0f131e,966289teselas,439493936bytes;279/279 puntos y6/6 rutas PASS|Log28e99b1e; muestreo/grafo, no locomoción ni conectividad exhaustiva|
| Paquete regional |55d7163c,542360979bytes,6826entradas conservadas al sustituir NM|Trial separado; base0.2 fd2c7023 intacta|
| Consumidor físico de cima |V4 PASS control/ida/vuelta,746 registros,salud100,contacto<44mm,8 negativos|Ruido4×; nuevo contrato terreno abierto congelado antes del run. Una cima, no toda la región; V2/V3 FAIL conservados|
| Coste comparado25/12.5 |120s cada una, residente1444.47/2185.09MiB,0timeslices>50ms|Pareja descriptiva en escritorio compartido; no prueba80–100 ni causalidad de CPU|
| Agua/rasantes/mapeado |Pendientes a escala regional|Proteger la huella no acredita navegación, conducción ni densidad de árboles|
| Checkpoint candidato0.3 |ZIP14556324,8974miembros releídos; config recompilada/PBO/biomas/misión por hash|Dependencias absolutas locales; base0.2 conservada; no1.0|

Computer Use por bloques breves anunciados, preparación offline y reset al acabar;
sin control durante generación, empaquetado ni logs. Lifecycle: consultar LIVE-STATE.

## Base0.2 — terreno, cauces y carreteras30-09-2026

Fuente: [informe del piloto](<P:/DayZ_Baltic_12km_dev/evidence/navigation/README.md>)
y [sesión](../../30_Sessions/2026-09-30-dayz-baltic-12km-terreno-cauces.md).
P9/P10/P11: ríos navegables, terreno/navmesh antes del mapeado y carreteras lisas.

| Gate | Resultado verificado | Límite |
|---|---|---|
| Candidato local Narva V3 | PASS offline,1242 vértices modificados; demás exactos | No es red regional preparada. |
| Profundidad bajo el paso | PASS172 soportes en motor, mínimo conservador3.15m en272 triángulos | Mar medido0.5–1m; no incluye el resto del río. |
| Tableros | Tres puntos Roadway a9m; lancha vacía cruzó el vano central | Gálibo6.338m/paso18m calculados; tripulante y embarcación mediana pendientes. |
| Movimiento de lancha | PASS Narva ida vacía:226 muestras continuas,196 propulsadas,97.828m netos,salud600,END | Run c9dc7555 solo servidor. Sin regreso/tripulante/imagen cliente ni ruta regional; ca8a8d0f conserva FAIL por hueco2.387s. |
| Carreteras lisas | Accesos8m/junta0m; hasta280m cuerda6m menor1cm | Hasta320m terreno exterior muestra133.8mm/6.274pp; diseñar continuidad, conducción pendiente. |
| Persistencia Terrain Builder | PASS reabierto9625ecf5:1242 ediciones exactas/resto nativo intacto/tres poses/pond0 | Parcial objects_v1 rechazado y conservado. Evidencia native-reopened-height-v2 y native-reopened-bridge-v2. |
| Navmesh del candidato | Propia68450401,60025/60025teselas y carga real con PBO fd2c7023 | WRP compiladoe3fbb224. Regenerar tras cambios posteriores de terreno/mapeado. |
| Consultas de navegación |4 caminos encontrados,750/751 secos a≤2m | Gate vertical0.8m FAIL26 muestras/sentido; causa interna no aislada. No equivale a caída de IA. |
| IA nativa sobre puente elevado | PASS control local,ida,vuelta;613 registros/salud100/prey estable | Un actor a la vez, corredor Narva. native-chase-v2/verification.json y8 negativos. |
| Coste fijo del servidor |120s completos sin clientes/CE/IA, residente~1276MiB | No acredita80–100 jugadores; FPS headless de semántica no validada. |
| Carga IA acotada | PASS0/25/100/0,4×60s;100 vivos/activos; servidor~1645MiB | CPU no monotónica, no comparación causal. Sin ciudades, CE ni100 clientes. |
| Base técnica activa | fd2c7023 en @DayZ_Baltic_12km, misión limpia cargó cliente/servidor | CheckpointZIPbbd4584a/8945entradas; rollbackebc60f4f conservado. No1.0regional. |
| Integridad de entrega anterior | PASS hash ebc60f4f en paquete de rollback sin cambios | fd2c7023 también en @DayZ_Baltic_NativeTrial; nunca cargar variantes juntas. |
| Lifecycle vigente | Consultar LIVE-STATE del HANDOFF y session_status | No inferir procesos desde la matriz; cierres medidos hasta aquí fueron forzados. |

El fallo previo del bridge no persistió en el último run; misión actual37f67389
compilada. No interpretar el linter como prueba de compilación del motor.

## Estado anterior — continuación autónoma29-09-2026

| Gate | Resultado verificado | Límite |
|---|---|---|
| Grandes cuadros de render | PASS SAT1M, conservado en PBOebc60f4f | Arte WorldCover provisional; remuestreo no añade detalle. |
| Geometría tras SAT1M | PASS byte a byte,4194304 alturas y dos objetos | Compilación4775RVMAT/2048PAA, paquete real comprobado. |
| Navegación propia | Regenerada sobre WRPd12ae049; .nm0fc26281 cargada en cliente/servidor | Rutas de cruce encontradas; muestreo del acceso oriental difiere0.833077m de superficie. Gate local de0.8m FAIL, IA real pendiente. |
| Cruce Narva a pie | PASS repetido sobreebc60f4f,354 muestras servidor, salud100 y sin nado | Control humano scriptado ambos lados; no teclado, vehículo o IA. |
| Agua regional | PASS tras importación/reapertura:1299 alturas,751 secos,0 inundados/0 bajo máximo1m | Solo muestras estratificadas; no toda la costa ni lagos elevados. |
| Geometría corregida | PASS4194304 alturas y puente con pose exacta en WRP derivado313600cb | Export nativo41b32584 produjo deltaY1.02mm en2objetos. Restitución explícita verificada, sin ampliar tolerancia. |
| Cámara aérea SPB | Franjas aisladas por nearplane0.07/10/0.07/10, original restaurado | Arco1300m/1600 persiste. Panorama1300m/12000near10 y vistas normales limpias; no cambiar perfil/jugador a near10. |
| IA nativa de Narva | NO ACEPTADA: control local pasa, cruce incompleto y fuera del corredor | Ruido timeout; prueba humano termina con actor muerto, causa no aislada. Crash inicial era loggingGetType. |
| Entrega técnica | packages/baltic-basic-v0.1: PBOebc60f4f, misión limpia y ZIP8937 entradas | No es1.0 del mapa poblado. Misión limpia arrancada, revisión visual final cancelada por Escape físico. |
| CE, ciudades, carreteras y80–100 | PENDIENTE | No declarar versión1.0 ni rendimiento. |

Fuentes actuales: HANDOFF del repo, evidence/render-distance, evidence/walk y
evidence/regional-water. Las secciones posteriores son hitos históricos.

## Historia de render y geometría — 29-09-2026

La entrada al juego y puente/río están confirmados por el usuario. La sonda de
misión pasa contra el ASC corregido: 612 muestras, error máximo 4,9 mm. El ASC
anterior al agua falla como negativo; la comparación antigua V3 ya no es el gate
vigente. Render a distancia **ABIERTO** por capturas de cuadros azules; 50 PAA /
400 mipmaps decodificados y asignación nativa de tiles correcta no lo resuelven.
Candidato magenta preparado, no desplegado ni probado. Detalles y siguiente ensayo:
[sesión de distancia](../../30_Sessions/2026-09-29-dayz-baltic-12km-render-distancia.md).
Las filas siguientes conservan los hitos históricos y sus límites originales.

29-09-2026. Evidencia: [resultados GIS](<C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/evidence/validation-report.json>) y [fixtures](<C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/evidence/validator-tests.json>).

| Gate | Resultado actual | PASS requerido |
|---|---|---|
| Entorno | PASS existencia/montaje | P:, Tools, Diag y vanilla leídos desde host. |
| GIS/formato | PASS, 28 comprobaciones | Hashes del recorte, 2048²/6 m, norte, muestras finitas, cobertura y controles de fuente; consumidores GDAL/SHP. |
| Validador | PASS, 13 casos | Rechaza inversiones, desplazamientos, huecos, NaN, truncado y cabeceras inválidas; acepta el caso válido y centros equivalentes. |
| Red de referencia | Analizada | Ocho anclas en componente común al añadir detalle de Narva; no test de conducción. |
| Importación/persistencia TB | PASS acotado | Probe y región física guardados; exportación comparada; región reabierta. |
| Registro centro/vértice y anclas TB | OBSERVADO / PASS GEOMETRÍA | Cuatro positivos/cuatro negativos UI; seis anclas, error máximo 0,000006440 m. XY de malla inferido, no propiedad numérica directa. |
| Contornos de agua TB | PASS REFERENCIAS | 19.346 anillos completos, 19.384 segmentos; máximo 0,000006600 m. Polígonos directos FALLAN y están ocultos. |
| Muestreo adaptado de alturas | PASS ENSAYO, producción PENDIENTE | TB: 16.129 interiores analíticos exactos; negativo +0,25 m. No demuestra adecuación de costa/bordes reales. |
| Buldozer | RENDER OBSERVADO CON AVISOS | Render texturado comprobado; aislar errores de consola/RPT antes de declarar arranque limpio. |
| Agua y puente | INCONCLUSO | Jugador cruza/nada/sale, colisión correcta; lago elevado probado. |
| WRP/PBO | PASS COMPILACIÓN/ARCHIVO; juego PENDIENTE | 420 entradas verificadas; falta despliegue/carga en juego. |
| IA y CE | NO EJECUTADO | Misión vacía preparada; no economía ni navmesh acreditados. |
| 80–100 jugadores | NO EJECUTADO | Hardware/escenario y carga medidos, cliente y servidor separados. |

Comandos verificados en esta máquina: `python tools/test_ascii_validator.py` y `python tools/validate_prototype.py`, con el intérprete GIS aislado indicado en README. No usar Python global por defecto. Guía: [importación](<C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/plans/terrain-builder-import.md>).

Validación de importación: `tools/verify_tb_roundtrip.py --repo P:\DayZ_Baltic_12km_dev` con Python GIS aislado; tolerancia ASC exportado 0.00501 m. Evidencia y límites en [sesión de importación](../../30_Sessions/2026-09-29-dayz-baltic-12km-importacion-tb-buldozer.md).

## Narva, 29-09-2026 — actualización de Gate C

| Gate acotado | Estado | Evidencia / cierre pendiente |
|---|---|---|
| Registro nativo LOCAL | MEDIDO | 289 cuadrícula + 289 perfil, X=200000+6c; N=6(2047-r), NW-SE. La predicción UI previa no sirve para estas alturas. |
| Serialización de corrección local v2 | PASS | 4194304 muestras, máximo 5.000114 mm; negativo original rechazado, 569 archivos regionales intactos. |
| Ambos accesos a tablero 2 m | PASS V3 | 34 muestras sobre ancho 8 m, gap medido 0; rejilla/perfil independientes, sin refit a V3. |
| Persistencia de geometría tras reabrir | PASS WRP | 4194304 alturas y pose de puente verificadas; selector de modo de altura no inspeccionado tras reabrir. |
| Agua elevada y cruce jugador | INCONCLUSO | Pond oculto, dos crashes al cerrar con pond visible frente a tres terminaciones normales oculto; causa no aislada. |
| Manchas negras | PASS A/B/A/B acotado | Completar 1378 slots en344 RVMAT elimina manchas; originales las reproducen. Avisos de motor siguen abiertos. |

Reproducción y límites: [sesión](../../30_Sessions/2026-09-29-dayz-baltic-12km-narva-ensayo.md), `P:/DayZ_Baltic_12km_dev/evidence/narva/informe.md`. El script `tools/narva/verify_engine_probe.py` requiere un log V3 real; fue ejecutado sobre V3 real y pasó. No convertir exportación PASS en agua/locomoción PASS.

## Primer paquete, 29-09-2026

Build aislado: PBO OPRW29, 367 RVMAT/50 PAA, contenido idéntico a compilados; puente sí, pond diagnóstico no. `evidence/playtest/pbo-verification.json`. Misión: 1 script lintado sin errores/avisos; 15 XML parseados; fixture positivo y 9 negativos del lector pasan. Esto es validación offline, no compilación de misión/CE en motor.

Revisión posterior: bloqueo de permisos resuelto; session_status y server_reload PASS. PBO desplegado por hash y run servidor/cliente lanzado. Carga de misión NO PASS: aviso navmesh y ErrorMessage minidump; sonda no recibida. Run detenido y lease libre; cierre forzado, no salida normal acreditada. [Entregable](<C:/Users/guill/Documents/Codex/2026-09-29/vamos/outputs/baltic-playtest/README.md>).

Evidencia del consumidor: [primera ejecución](<C:/Users/guill/Documents/Codex/2026-09-29/vamos/outputs/baltic-runtime/README.md>).

## Agua y renderer, continuación actual

Sonda441 puntos: mar0.5..1m;44/297 puntos secos interiores tienen agua real;108 no superan el máximo. Corrección local ya importada y guardada: 4194304 alturas dentro de5,01mm; WRP/pose del puente PASS; negativo WRP anterior rechazado con exit1. En70933 vértices secos interiores del núcleo,28278 estaban <=1m y ahora0; mínimo1,25m. Materiales completos tras rebuild. Nuevo PBO420 entradas PASS offline, SHAe3e6b361..., no desplegado.

Recheck de agua INCONCLUSO: Buldozer sin respuesta en carga desde16:37:59, logs vacíos. No crash demostrado; cierre manual solicitado tras rechazo de acceso a ventana dwm. Sondas retiradas por hash. Nueva reapertura también pendiente. Dos configuraciones Navmesh no superan la carga; app NavMeshGenerator pendiente de autorización específica por rechazo automático. [Informe y dos respaldos](<C:/Users/guill/Documents/Codex/2026-09-29/vamos/outputs/baltic-render-agua/README.md>).
