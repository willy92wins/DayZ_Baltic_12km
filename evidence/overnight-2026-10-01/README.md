# Baltic V10 — sesión autónoma de ocho horas

Ventana autorizada: **01-10-2026, 02:42:43–10:42:43 UTC**
(04:42:43–12:42:43 Madrid). Este informe se completa durante la sesión; el estado
de procesos vigente está en [state.json](state.json) y [HANDOFF](../../HANDOFF.md).
La versión V10 es una base regional con pruebas acotadas; no es el mapa1.0 poblado.
Persisten gates de IA, vistas y maniobras de lancha. Los procesos de ensayo están
cerrados; se está verificando la entrega documental dentro de la ventana autorizada.

## Qué cambió

El terreno regional se guarda y reabre en Terrain Builder con sus aguas como
objetos nativos. Narva tiene ahora nueve tramos de puente,225m de longitud y
tablero a11m, con accesos de8m y rasante máxima5.067%. La última corrección afecta
693 vértices; conserva las máscaras protegidas de agua, canales e islas.
No se reescala localmente San Petersburgo ni se cambia el encuadre aprobado.

La reserva conserva5.941km² de tierra seca protegida;0.126km² cambiaron en la
integración de agua y corredores. Su mediana de altura pasó de3.93 a3.95m.
La vegetación densa y las poblaciones siguen pendientes de colocación según P10.
La cobertura WorldCover y los corredores no son edificios, árboles ni piezas de
carretera ya colocados. Ver [revisión de áreas](../regional-foundation-v1/combined-protected-area-review-v10.json).

## Artefacto que debe usarse

**Mod:** `P:/Mods/@DayZ_Baltic_FoundationV10Native`. Cargar solo una variante de
este mundo. Los addons de sondas son temporales y no forman parte del mapa.

| Artefacto | SHA-256 |
|---|---|
| ASC V10 |`8e25fab25e8f0909fdda302ed4ba3db4c43884c523920f5ef3424db90780eb8b`|
| WRP nativo reabierto |`cdd6838f522a5b66b729db7c6bda39b0a5a41eb256fb26804eb39f5479ef905a`|
| WRP compilado |`b46c7fce053171a63a6f2670a56c10452efc049b1d24fbef2494fa79be3bece5`|
| Navmesh final,449360340bytes |`e8348efc2f361d8aa82cbd69c4fc8ad72470a628abd2a10ca8411d7f40fc313c`|
| PBO del mundo |`d1008dd6c882193706f06c5e7b8495ee1a357f5819a8574118784f7e90f18577`|
| PBO de aguas |`f9a5cdf7461ff09e80a102641289513896011a78b090fdbbd1056f9b985898d3`|

Editable: `tb/regional_foundation_v10`; export aceptado
`02_reopened_v10.wrp`. La NM se generó sobre su WRP compilado exacto:
966289/966289teselas,344s,1113521polígonos y312conexiones off-mesh.
Evidencia: [persistencia](native-v10-persistence-1-2.json),
[generación](navmesh-v10-native-generation.json) y
[paridad del paquete](../../build-output/regional_foundation_v10_native_freshnav/verification.json).

## Validación terminada

| Gate | Resultado | Alcance que no cubre |
|---|---|---|
| Persistencia nativa |PASS; alturas/materiales/10161objetos exactos tras reapertura;7 negativos|No sustituye comportamiento en juego|
| Agua y consultas NM |PASS;81212muestras agua/tierra,314puntos y15rutas; error altura≤0.499mm|Consultas, no locomoción exhaustiva|
| Lancha regional V3 |PASS8/8 sectores en ambos sentidos, salud600|Lancha vacía; sin tripulación ni casco mediano; termina con deriva|
| Coche en Narva V3 |PASS;1.019km en cada sentido, salud1000,4contactos, máximo26.9km/h;18 negativos|No red completa ni altas velocidades|
| IA regional V1 |10PASS/9FAIL|Tres regresos y todos los segmentos del puente quedaron abiertos|
| IA regional V3 |20PASS/6FAIL; tres regresos terrestres cubiertos por tramos solapados|Los dos grupos del puente siguen sin aceptar|
| Grafo del puente |PASS8rutas; filtroNONE rechazado;7 negativos|No prueba que un infectado recorra el tablero|
| Humano sin infectado |PASS control y cruce este;294.082m,973muestras,desviación0.357m,15negativos|Un sentido; no acredita persecuciónAI|
| Carga0/25/100/0 |PASS de medición;420muestras host por proceso,100infectados vivos/despiertos, servidor~2.52GiB|Un cliente, sinCE/ciudades/vegetación; no80–100jugadores|
| SPB con carga directa |Cliente visible y estable213.029s; cierre ordenado|Sampler host parcial82/90; no prueba completa de rendimiento|

Fuentes: [agua/NM](consumer-v5-final-native/verification.json),
[lancha](regional-boat-v3/runtime-complete/verification.json),
[coche](foundation-drive-v3/runtime-complete/verification.json),
[IA V3](regional-chase-v3/runtime-complete/verification.json),
[cobertura IA](regional-chase-v3/runtime-complete/coverage.json),
[grafo](bridge-path-v10/verification.json),
[cruce humano](bridge-human-control-v1/runtime-complete/verification.json),
[carga](foundation-load-v1/runtime-complete/verification.json),
[SPB directo](spb-basic-v1/verification.json).

La CPU de la prueba de carga no creció de forma monotónica. Un intervalo185ms
apareció en la fase final sin actores; se conserva sin asignarle causa. Las
llamadas OnUpdate no son FPS de render. Las fuentes nativas y los límites de los
contadores están en el informe de carga y en la skill de terreno.

## Comprobaciones finales

<!-- LATE-GATES:START -->
- **Cauces largos:** completo9PASS/3FAIL,12tramos independientes y solapados sobre26.600558km distintos. Todos visitaron sus puntos sin perder salud600. Narva6 falla orden de indices muestreados; delta8/10 radio final tras deriva. FAIL originales conservados. [Resultado](full-river-v2/runtime-complete/verification.json) y [cobertura](full-river-v2/coverage-v10.png).
- **Vistas agrupadas:** siete grupos/12poses y restauracion pasan telemetria, todos cerrados ordenadamente. Pixeles aceptados solo en vistas deNarva,SPB y norte; las demas son parciales o inconclusas. [Revision visual](visual-review.md). No se declara corregida la causa del crash de la transicion distante.
- **Persecucion continuaV1:** control localPASS; cruce este se detuvo al superar el jugador4m de corredor (4.005626m), todavia sobre el tablero. Verificador15negativos contra control real. FAIL original conservado; regreso sin ejecutar.
- **Persecución continuaV2:** FAIL conservado. El humano alcanza6.003488m lateral y pico9.237m/s; el infectado mantiene contacto y salud. El cruce completo y el regreso quedan sin acreditar. [Resultado](continuous-pursuit-v2/runtime-complete/verification.json).
- **Control sin infectado:** mismo controlador humano, control local y cruce este PASS. Avanza294.082m, permanece a menos de0.357m del eje y registra pico2.412m/s. No cambiar el mapa por el fallo de la persecución sin aislar la interacción. Las tres pruebas están cerradas ordenadamente; cada verificador rechaza15 negativos sobre su control real.
- **Repetición Neva:** telemetría y restauración PASS; Computer Use devolvió carga/otra ventana y no produjo píxeles aceptables. Control liberado; repetición de reserva preparada pero no ejecutada. [Registro](foundation-visual_g_neva_v1/repeat-01/visual-observation.json).
<!-- LATE-GATES:END -->

Los fallos anteriores no se eliminan al crear un nuevo ensayo. En particular,
salirse del corredor exigido±4m no demuestra automáticamente caer de un tablero
cuya Roadway alcanza±7.1m; otros desvíos sí rebasaron esa huella. Ver [bugs](../../bugs.md).
El [análisis de trayectorias](regional-chase-v3/bridge-behavior-analysis.png)
distingue ambos casos sin cambiar los resultados originales.
La [comparación de persecuciones y control humano](bridge-controller-comparison-v2.png)
añade las pruebas continuas sobre el mismo paquete, con velocidades de servidor.

## Recuperación y siguientes gates

Checkpoint editable y paquete:
`packages/baltic-foundation-v10-native-checkpoint/terrain-builder-foundation-v10.zip`,
SHA`f96d3d5c11da9c7debcbfe35b8edad3e9ffcf9fbc8d194d999a751762ee3903f`.
Sus miembros y las fuentes posteriores a compresión se comprobaron por hash.
Es una copia local: conserva rutas absolutasP:, requiere datos vanilla externos
y la junction `P:/baltic_water` al directorio de aguas registrado en su manifiesto.
La capa fuente incluida contiene una NM de bootstrap identificada; para jugar
usar los Addons finales y la NM final indicada arriba. No es un instalador portable.

Para cerrar la base todavía hacen falta los gates físicos/visuales abiertos.
El orden concreto y los criterios están en el [plan de continuación](../../plans/foundation-acceptance-next.md).
Después: carreteras físicas, poblaciones y vegetación por sectores, nueva NM
tras esos objetos, CE/loot/persistencia y carga representativa de80–100jugadores.
El gálibo geométrico6.338m sobre un paso18m y agua de diseño3m no acredita un casco
mediano sin probar sus dimensiones/colisiones reales.

**Cierre y coordinación:** runs propios cerrados ordenadamente en los ensayos
finales, lease libre y Computer Use terminado. Sesión de ocho horas cerrada y heartbeat desactivado. El estado está en `state.json`.
El archivo complementario y su verificación se encuentran en
[manifest.json](../../packages/baltic-foundation-v10-night-evidence/manifest.json).
Un reset autorizado ya se consumió a06:22:11UTC; recibo [usage-reset.json](usage-reset.json).
No se ha consumido un segundo. HEAD4ff154b7; cambios previos y `diagnostics/`
ajeno preservados. No se crea un commit que mezcle trabajo ajeno sin separarlo.

La [skill de terreno](<C:/Users/guill/.codex/skills/dayz-terrain-workflow/SKILL.md>)
incorpora las lecciones verificadas. Su familia existente cubre estos casos;
no se crea una duplicada. Para cargar la base sin sondas, usar las
[instrucciones del paquete](../../packages/baltic-foundation-v10-native/README.md).
