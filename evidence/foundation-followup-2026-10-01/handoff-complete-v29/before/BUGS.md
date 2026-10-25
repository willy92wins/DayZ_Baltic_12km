# Problemas vivos — Baltic

Estado de pruebas de la sesión nocturna01-10-2026. El paquete bajo prueba es
`@DayZ_Baltic_FoundationV10Native`, mundo SHA256 `d1008dd6c882193706f06c5e7b8495ee1a357f5819a8574118784f7e90f18577`.
Las variantes fallidas se conservan y no sustituyen ese paquete.

| ID | Estado | Superficie afectada | Evidencia vigente |
|---|---|---|---|
| BALTIC-001 |ABIERTO|Sonda de cámara, transición distante|V3/V4 reproducidos; carga directaSPB estable|
| BALTIC-002 |ACEPTADO CRUCE CONTINUO|Consumidor físico de IA del puente|ContinuaV4: control y ambos sentidosPASS,18negativos; ensayos de ruido anteriores conservados|
| BALTIC-003 |ACEPTADO CASOS AISLADOS|Control terminal de la sonda de lancha|Delta8 aisladoV4 y10 aisladoV5 PASS; cadauno12negativos+4relojes. Sin aceptación de flotilla|
| BALTIC-004 |ACEPTADO CASO NARVA6|Muestreo de objetivos de la sonda fluvial|V5 aislado PASS3951muestras/549transiciones,12negativos+4relojes; historialV2FAIL preservado|
| BALTIC-005 |ACEPTADO TERRENO V29|Anchura de los corredores de carretera|239126secciones/0fallos; seis viajes congelados PASS entre V3/V4;18negativos. No prueba toda la red conduciendo ni piezas colocadas|
| BALTIC-006 |ACEPTADO DOS MANIOBRAS|Parada de sonda de coche en colinas|V1 sobrepasaba el extremo por frenar tarde. V2 ambos sentidosPASS y18negativos; mismo terreno, sin escrituras de pose/velocidad|

| BALTIC-007 |PARCIAL; ABIERTO|Orillas y relieve facetado|V29 geometria/nativo/navmesh/V7 PASS; agua dinamica local y render del paquete final pendientes|

R1: cada ID representa el mismo síntoma; las variantes se agregan a su entrada,
sin borrar los resultados anteriores. R2: cerrar requiere prueba del consumidor
y hash del paquete/probe que la produjo; un cambio preparado no cierra el fallo.
El hash del mundo identifica el ensayo y no atribuye automáticamente la causa.

## BALTIC-001 — Crash en transición lejana de cámara

- Estado: reproducido; mecanismo no aislado.
- Disparador: sonda de cámara Narva aérea → San Petersburgo a altura de jugador,
  POSE3 alrededor de150s. V3 y V4 terminan con access violation nativa; V4 retiró
  MakeScreenshot y reprodujo el fallo. No basta atribuirlo a capturar imágenes.
- Impacto: esa secuencia automatizada no sirve como aceptación visual regional.
  No se ha demostrado un crash de la carga directa normal de San Petersburgo:
  el control directo permaneció vivo213s y se cerró ordenadamente.
- Evidencia: [V3](evidence/overnight-2026-10-01/foundation-visual-v3/crash-attempt01/),
  [V4](evidence/overnight-2026-10-01/foundation-visual-v4/crash-attempt01/),
  [control SPB](evidence/overnight-2026-10-01/spb-basic-v1/verification.json).
- Discriminador completado: siete grupos y12poses con jugador cercano, todos
  cerrados ordenadamente sin reproducir el crash. TelemetríaPASS, píxeles
  parcialmente válidos; `evidence/overnight-2026-10-01/visual-review.md`.
  No acredita corregir la causa del salto distante. Completar las tomas pendientes.

## BALTIC-002 — Locomoción de infectados en el puente sin aceptar

- Estado: reproducido; separar percepción, ruta elegida y contacto físico.
- Disparador: objetivo humano estacionario y ruido sintético, actor vanilla
  sin modificaciones de movimiento. La prueba V1 completa obtuvo10PASS/9FAIL:
  tres regresos terrestres agotaron tiempo y los seis casos del puente fallaron
  llegada, corredor4m o contacto. Se observaron desvíos fuera del tablero.
- Evidencia: [V1 completo](evidence/overnight-2026-10-01/regional-chase-v1/runtime-complete/verification.json),
  [consulta del grafo](evidence/overnight-2026-10-01/bridge-path-v10/verification.json),
  [V2 control fallido](evidence/overnight-2026-10-01/regional-chase-v2/failed-control/).
- Discriminadores: ocho consultas FindPath del puente pasan y el filtroNONE
  falla como corresponde. AddNoiseTarget falló incluso en el control local;
  no es estímulo validado. La V3 por tramos cortos terminó con20PASS/6FAIL y se
  cerró ordenadamente. Tres regresos terrestres quedan cubiertos por intervalos
  solapados; ambos grupos del puente fallan su aceptación agregada. Casos
  fallidos12/14/15/17/21/23, sin declarar causa raíz ni ampliar límites.
  Evidencia: `regional-chase-v3/runtime-complete/verification.json` y
  `regional-chase-v3/runtime-complete/coverage.json`, bajo la carpeta nocturna.
  El análisis de trayectorias identifica cuatro casos12/14/21/23 fuera de la
  envolvente Roadway con descenso de Y y sin estadoCHASE registrado. Los casos
  15/17 llegaron, mantuvieron Y≈11m y no salieron de±7.1m; sus FAIL de corredor
  y superficie física siguen vigentes. El cálculo de suelo esperado del
  verificador también usa el corredor±4m. Todos los casos de puente que pasan registraron CHASE: es una
  asociación, no un aislamiento causal. Informe y figura:
  `evidence/overnight-2026-10-01/regional-chase-v3/bridge-behavior-analysis.json`.
- Límite del verificador: corredor exigido±4m, más estrecho que Roadway real
  hasta±7.1m. Salirse de4m falla el corredor aunque aún pueda pisar el tablero;
  otros desvíos sí superaron7.1m. No convertir todos los fallos en caídas ni
  relajar retrospectivamente el gate. El coche ya cruzó ambos sentidos.
- Impacto: navmesh guardada/cargada y consultas regionales válidas no bastan para
  declarar resuelta toda la locomoción de IA del cruce. Mantener ese gate abierto.
- ContinuaV1 ejecutada: control localPASS. Cruce este detenido al apartarse el
  jugador4.005626m, aún en tableroY11; actor máximo3.746769m y salud100.
  El cálculo de piso comparte el límite4m y también falla contacto del jugador.
  FAIL conservado; no acredita llegada ni regreso.15negativos contra control real.
- ContinuaV2: criterio adicional fijado antes del run, tablero principal6m y
  accesos4m. ControlPASS; cruce falla cuando el jugador llega a6.003488m lateral,
  con pico9.236822m/s pese a solicitar marcha lenta y retroceso en su recorrido.
  Actor contactoPASS, máximo5.508567m lateral. Al terminar ambos conservan salud100
  y Y≈11, sin llegar al destino. El FAIL físico del jugador ocurre al salir de la
  huella principal6m, todavía dentro de las aceras laterales7.1m. No prueba caída.
  No ampliar otra vez el contrato: control sin infectado preparado para separar
  la interacción conAI del movimiento humano. No cambia WRP/NM.
  Evidencia: `continuous-pursuit-v1/` y `continuous-pursuit-v2/` bajo la carpeta
  nocturna, con logs completos, negativos y cierre ordenado.
- Control sin infectado completado: control local y recorrido este PASS;
  avance294.082m,973muestras,194.645s,desviación0.357m,pico2.412m/s, salud y
  contacto conservados.15negativos. El humano camina por este puente sinAI;
  esto no prueba causa única de los fallos durante combate/persecución.
  `bridge-human-control-v1/runtime-complete/verification.json`. Era el estado anterior al seguimiento siguiente.
- Continuación01-10: la conversión de rumbo restaba GetHeadingAngle. V3 cambió
  a suma en ambos peers:2019muestras con rumbo no nulo siguieron la dirección
  deseada con error mediano0.155°. Completó ambos sentidos, pero el verificador
  conservó FAIL por tasas entre eventos a pocos milisegundos y END cliente ausente
  tras cierre forzado. No había que reconstruir el navmesh por esos fallos.
- Nuevo runV4 `c1e21f1d-90ff-4fc5-9db3-6e772afed17d`: control y ambos crucesPASS,
  2188registros activos, actor máximo lateral0.954m, humano0.357m; contacto,
  salud y metas válidos. Tasas con SAMPLE200ms; todos los eventos conservan
  controles físicos y envolvente de posición.18negativos rechazados, incluidos
  saltos en SAMPLE/evento y ausencia de SAMPLE. Cierra la aceptación de cruce
  continuo del tablero, sin promover los casos históricos de ruido estacionario.
- Mundo `d1008dd6`, NM `e8348efc`, sondaV4 `31c74cf3`. Pruebas cerradas antes de
  gestionar procesos; cierre del run reportado forced_kill, no cierre ordenado.
  Evidencia: `evidence/foundation-followup-2026-10-01/continuous-pursuit-v4/`
  `runtime-complete/{verification,negative-controls}.json`, referencia y cleanup.

## BALTIC-003 — Llegada registrada seguida de deriva fuera del radio

- Estado: reproducido en la sonda; el run largo terminó y se cerró ordenadamente.
- Paquete: mundoV10 anterior; probe `c5414ffe385eae5b85e1fe6dfef671db568d50a8eb11c74a3f4346f7c6417b2e`.
- Casos8/10 del delta: todos los puntos visitados, salud600, continuidad,
  corredor y altura del lecho correctos. Después de `BalticProbeStop` el motor
  aparece apagado pero la lancha sigue avanzando; posición final a7.495/7.314m
  del extremo. El gate congelado `start_and_endpoint` falla y se conserva.
- Mecanismo leído: `missions/BalticFullRiverV2.BalticTrial/init.c:98-102,138`
  corta motor al entrar a4m y espera10s. `ARRIVED_AND_STOPPED` es un nombre
  heredado, no una comprobación de velocidad nula. No atribuir a cauce bloqueado.
- Evidencia: `evidence/overnight-2026-10-01/full-river-v2/delta-complete/`.
- Próximo paso del consumidor: desaceleración nativa antes del extremo, con
  nueva referencia previa al ensayo y mismo radio; no ampliar el umbral ni
  editar el terreno para hacer pasar una maniobra terminal.

Actualización de BALTIC-003: `delta-isolated-v4/closed-logs/verification.json`
conserva FAIL conjunto por interrupción10; el caso8 sí supera física y eventos,
1139muestras,155transiciones y12negativos. Cuatro corrupciones de reloj rechazadas.
El paso de simultáneo a aislado funcionó para8 en esta repetición; no prueba por
sí solo colisión como causa deV3. RunV4 cerrado normalmente por el motor; inicio
del cierre no aislado. No considerar el nombre ARRIVED_AND_STOPPED como velocidad0.

Delta10 aisladoV5: `river-single-10-v5/verification.json` PASS físico/eventos y
reloj435.914s. Mismo mundo/probe/controladorV3; solo una lancha.12negativos físicos
y4de reloj rechazados. Logs cerrados antes del cierre lifecycle forced_kill,
sin atribuir métricas de salida ordenada. Referencia `bf6cabd2`, log `30514730`.
Con delta8V4 se aceptan ambos casos individualmente; no prueba simultánea ni
causa única de las desviacionesV3. Se conservan los FAIL y la interrupciónV4.

## BALTIC-004 — Orden de objetivos muestreado cada 500 ms

- Run largo V2 terminado: 9 PASS y 3 FAIL sobre 12 tramos independientes.
  Todos visitaron sus puntos sin pérdida de salud. El caso6 de Narva falla
  únicamente `targets_in_order`; no se elimina ese FAIL.
- Entre376.504 y377.004s el índice pasa111→114, con desplazamiento de unos0.68m
  y velocidad1.35m/s. Los puntos próximos forman una curva cerrada. La misión
  puede avanzar un objetivo por control100ms, pero registra solo cada quinto
  control. Fuente: `missions/BalticFullRiverV2.BalticTrial/init.c:95-106,122-134`.
  Esa cadencia permite varios avances entre dos muestras; no prueba un atasco.
- Evidencia: `full-river-v2/case6-target-order-observation.json` y
  `full-river-v2/runtime-complete/verification.json`, bajo la carpeta nocturna.
- Próximo discriminador: registrar cada transición de objetivo y contrastarla
  con el movimiento físico. Congelar ese contrato antes del nuevo ensayo;
  no ampliar retrospectivamente el límite del verificador ni modificar el cauce.

Actualización BALTIC-004, 01-10 13:32UTC: Narva6 aisladoV5 completo,
run `6dd0ab94-f2cb-40b7-a65c-d6e765db31a8`, 1757.178s, 3951muestras y
549transiciones con testigo físico en el mismo tick. Todos los objetivos,
corredor, lecho y extremoPASS; salud600 constante. Paso bajo puente incluido.
Máximo error de altura0.000140m, final a1.966055m y velocidad0.215074m/s:
motor apagado observado10.01s, no prueba amarre ni inmovilidad total.
12alteraciones físicas/eventos y4de reloj rechazadas. MundoV10/probe congelados.
Registro cerrado SHA `f4068e7ab865ef7e5162411fee4fdff573cf67c192bb102934915e1075944f3e`.
Lifecycle posterior `forced_kill`; session_status libre tras cierre. Evidencia:
`evidence/foundation-followup-2026-10-01/river-single-6-v5/`.
La aceptación sustituye el pendiente de muestreo, no borra V2 ni acredita flotilla.

## BALTIC-005 — Ondulación transversal entre estaciones del ajuste

Actualización01-10: V19/V20/V21 conservan INFEASIBLE con cotas4/5/6m.
V21:79filas del certificado verificadas contra matrizV18;67carretera/12talud,
único borde fijo(4326,6936),42.319954m,a33.453699m del eje y492m del agua.
Impone cambio>=6.301367m en otro vértice. V22 abre la transición a48m solo en
x[4278,4572],z[6876,7008], conserva24m fuera y reintenta con cota5m.
Minimax agotó600s: última cota inferior5.131519m, no mínimo global probado.
Plan `plans/road-network-local-transition-v22.md`. No modificar V10 aún.

Actualización BALTIC-005: V16/V17 se trazó a8vértices fijos secos fuera de la
transición12m; ampliar la cota no solucionaba ese certificado estructural.
V18 amplía solo la transición a24m. Sigue inviable con3m: certificado243filas
verificado algebraicamente, dos vértices dominantes(4368,6954)/(4512,6924),
necesidad local>=3.877807m. Diagnóstico acotado desde4m, sin terreno exportado,
según `plans/road-network-v18-cap-diagnosis.md`. No relajar las pruebas de conducción.

- Estado: geometría observada, efecto físico regional pendiente de conducción.
- Sobre V10,88452secciones secas elegibles medidas cada<=1m y17puntos laterales
  cada0.5m:6854amplitudes>3cm y un par del eje>6.5%. No equivale a6854baches
  independientes: son muestras, y la curva de la polilínea cambia sus normales.
- Muestrear solo eje y bordes a esas estaciones daba1781excesos; los puntos
  interiores revelan ondulaciones que el ajuste original no medía.
  Fuente: `evidence/foundation-followup-2026-10-01/dense-road-sections-v3.json`.
- Tres rutas diagnósticas de coche preparadas en costa/colinas/sur, ambos
  sentidos. Sus futuros PASS físicos no borran el FAIL de anchura8m.
- PilotoV11 no produjo ASC:335restricciones imposibles sobre alturas protegidas
  de los márgenes. Corregido ese dominio, V12 sigue inviable con±0.5m de cambio;
  no hay ahora contradicción individual demostrada, falta aislar restricciones
  acopladas. No se ha importado ni desplegado ningún candidato nuevo.
  `tests/regional_road_width_pilot_v11/` y `regional_road_width_pilot_v12/`.
- El minimax midió1.263453m de cambio necesario. V13 con cota1.35m produjo
  alturas, pero el consumidor independiente detectó20secciones>3cm y24nuevos
  triángulos>35°: FAIL conservado, sin importar.
- V14 restringe gradientes sobre bandas continuas y el talud de transición:
  PASS tres corredores,7139secciones a0.37m/0.25m lateral,729vértices,
  delta máximo1.464067m. Agua/islas/exterior exactos; cinco negativos rechazados.
  `tests/regional_road_triangles_pilot_v14/independent-consumer-with-support.json`.
  Es piloto offline; no navmesh ni conducción de ese candidato.
- Extensión conjuntaV15:94992variables/4850084restricciones, solver INFEASIBLE,
  ningún ASC. Diagnóstico:224filas individualmente imposibles,204completamente
  congeladas;199de anchura/rasante y25de cuerda, ninguna de talud. El plan
  detiene ese candidato; no eliminar restricciones para presentarlo como PASS.
  `tests/regional_road_network_v15/{solve,infeasibility-diagnostic}.json`.

## BALTIC-006 — Frenada tardía de la sonda regional

V1 terminó cuatro casos costa/sur PASS y dos colinas FAIL terminales; todos los
puntos, salud1000 y contacto físico válidos. Mantenía35km/h hasta estar a5m del
fin y sobrepasaba el corredor cerrado al frenar. Evidencia `regional-drive-v1/`
`terminal-observation.json`,9.67/9.10m/s cerca de ARRIVED.
V2 desacelera desde50m y aplica BalticDriveStop al llegar lento: dos sentidos
PASS,1648muestras,contacto4ruedas,extremos1.417/1.414m,parada5.4s,salud1000.
18negativos rechazados. Mismo mundo d1008dd6 y sonda4f693887; no pose ni velocidad
forzadas después del spawn. Ref f943ddc3, log4555334b.
Run c0692986 cerrado forced_kill después de logs completos; release informo
lease_expired, estado posterior libre. No aceptación de toda la red ni vehículos
con conductor/piezas de carretera. V1FAIL conservado.

## BALTIC-007 — Orillas entre vértices y relieve facetado

01-10, nueva prioridad del usuario. V10 tiene todos los vértices nativos secos
a1.25m o más, pero25647 de214742muestras secas dentro de celdas de orilla están
bajo1.25m. El diagnóstico no estima área. Una sonda local de129.47s/512épocas
observó agua sobre12puntos de borde;4controles interiores1.25m no se inundaron.
Registro parcial: el gestor se cerró antes de COMPLETE por un error de secuencia
de esta sesión. Conservar esa limitación. Captura original y logs en
`evidence/foundation-followup-2026-10-01/outline-water-probe-v1/`.

El candidatoV24a con planos de orilla resultó inviable:146filas no caben en±6m.
Entre ellas, un islote vectorial14.4969m² ocupa triángulos con todos sus vértices
a−12m. V25 permite subir15m solo en759vértices mojados próximos a estas formas.
ASC `f7a220fd` calculado; NO importado, aceptación independiente en curso.
El relieve seco usa suavizado12m y transición48m alrededor de ejes protegidos.
Mantener V10 hasta pasar geometría, comparación nativa, agua dinámica y navmesh.

Actualización posterior: consumidorV25 termina FAIL; costa631284extremos PASS,
núcleos grandes/ríos PASS,34islas pierden margen. V26 corrige736vértices secos
con subidas≤1.697mm y conserva8vértices protegidos del puente; sigue rechazado
por9lagos estrechos sin15cm de agua entre23sin núcleo a8.485m. V27 añade agua
y resulta inviable. En lake127/172, el representante mojado cae dentro de la
envolvente convexa de la parte seca del mismo triángulo: contradicción afín
de0.5m independiente de límites de pendiente o delta.

V28 en cálculo bajo plan explícito: transición de6m solo alrededor de esos
23lagos; el soporte nativo de islas no puede bajar del V10. Vectores/modelos
de agua y recorte conservados. No aceptación ni importación todavía.

Actualización16:04UTC: V28/V29 rechazados por límites conservadores de isla y
redondeo respectivamente; V30 pasa geometría continua, pero pierde profundidad
en242puntos de lago de la referenciaV5: rechazado antes de importar. V31 añade
esa referencia y resulta inviable; certificado de3filas válido sobre lake168,
no ruido numérico. V32/V33 extienden la transición6m a todos los lagos y exigen
además≥1.4m en tierra seca original frente al mar. V33 calculado ASC9d2954fc;
81212puntosV5 PASS sin mover/reclasificar muestras. Verificación continua y
reserva/accesos en curso. V10 sigue siendo el único paquete aceptado/desplegado.

Actualizacion2026-10-01T16:46:46.220838+00:00: V33 pasa las13puertas geometricas y reserva/accesos.
Importado y reabierto. Primeras exportaciones desplazaban4952objetos soloY;
corregidos offsets relativos en capa respaldada. Exports5/6 persistidos exactos,
con670residuosY de agua<=0.954micrometre contraV10. Puentes exactos. Derivados
explicitos restituyen solo esosY y pasan todas las poses estrictas. Paquete
aisladov33 en compilacion; BALTIC007 sigue abierto hasta agua dinamica/render.

## Checkpoint 2026-10-01T17:21:34.793050+00:00

V33 está desplegado aisladamente para pruebas; V10 permanece intacto.
## Checkpoint V33 — navmesh y agua comprobadas; carreteras pendientes

Ver `evidence/foundation-followup-2026-10-01/outline-v33-checkpoint.md`.
Agua local PASS:664épocas/15936muestras, margen seco mínimo0.28706m; no aceptación global.
BALTIC005: mismo barrido V10 1781/1 frente V33 7261/147, regresión verificada.
Plan corrector V24 congelado y solver acotado; no ASC aceptado ni importado.
CU detenido con Escape, Neva incompleto FAIL. Sin procesos DayZ propios; lease libre.

## Checkpoint V29 nativo — 2026-10-01T19:13:42.937701+00:00

[WORKS, MECHANISM UNKNOWN] La exportación r1 reproduce todas las alturas y
materiales previstos, pero desplaza dos piezas de agua +5,5003/+6,1817 cm frente
a V33. Dos offsets relativos corregidos con backup y tres negativos rechazados;
exportación corregida y save/reopen pendientes. No se cierra BALTIC-005/007.
Las seis puertas offline V29 ya pasan, incluidos orillas continuas y negativos.
V24–V28 rechazados conservados. Detalle: checkpoint y road-v29-native/.
CU detenido por discrepancia de ventana, no por falta de autorización.

## Checkpoint V29 — persistencia, navmesh y conduccion

Paquete final b3418f92, WRP2c95ab7d, NMfacaf1e3;966289teselas generadas y
verificadas. V7 PASS81212puntos/314nav/15rutas. Exports r2/r3 persistidos; dos
desplazamientos de agua corregidos,670residuos heredados solo en derivados.
DriveV3 completo5PASS/1FAIL: regreso sur termina a3.423m de la meta y supera
todos los checks fisicos, pero no entra en1.5m para registrar ARRIVED antes
de300s. No ampliar criterios: experimentoV4 acotado en ambos sentidos sur,
solo acelerador terminal a0.5 cuando velocidad<0.2m/s dentro de8m.
Plan regional-drive-v4-terminal-recovery.md. V3 se conserva; BALTIC005/007
siguen pendientes de los consumidores restantes.

Actualizacion V4: ambos sentidos sur PASS;1.582muestras, cuatro contactos,
salud1000, destino1.448/1.491m y parada5.4s;18negativos rechazados.
Solo cambio de control terminal, sin cambios del mapa. V3 FAIL permanece.
road-v29-driving-coverage.json consolida seis viajes sobre el mismo V29:
5.282735km totales/2.641368km de trazados unicos, entre dos runs.
BALTIC005 aceptado para la geometria medida y estos consumidores; no todas
las velocidades, conductores humanos ni carreteras fisicas.
