# Navegabilidad y prioridad de terreno — 30-09-2026

**Geometría local, propulsión y recorrido Narva de ida con lancha vacía confirmados.**
Exportación nativa tras reapertura aceptada y nueva navmesh completa guardada.
Paquete aislado fd2c7023 cargado. IA nativa pasa control local e ida/vuelta por
el puente elevado; las consultas geométricas conservan su fallo vertical.
No es terreno regional terminado.
El usuario pidió lancha vanilla más margen para barcos medianos y, después,
dejar el mapeado para el final. Fuente de aceptación: product-spec P9/P10;
secuencia actual: `plans/terrain-first.md`. P11 añade carreteras lisas y prueba
de conducción posterior; se reservan ahora las rasantes del terreno.

## Continuación12:26: persistencia, navmesh y coste fijo

`native-reopened-height-v2.json` y `native-reopened-bridge-v2.json` aceptan el
WRP literal9625ecf5: todas las alturas esperadas, tres poses de puente y pond0.
Guardado02:39:13 confirmado por la consola y lectura completa17307994bytes.
El export parcial anterior permanece como evidencia rechazada.

`native-build-parity-v1.json`: del candidato anterior al build nativo22a1f643
cambia solo WRP,6826entradas intactas. WRP compilado e3fbb224. Generación real
en run0cc4a53a:60025/60025teselas,3705full,110s; archivo68450401 guardado por
Computer Use sin clic manual,36331800bytes. `native-generation-v1.json`.
Paquete fd2c7023 reemplaza solo NM del build22a1f643;6826entradas conservadas.
Ruta aislada @DayZ_Baltic_NativeTrial; no se sustituyó la base ebc60f4f.

Rendimiento: `../performance/native-baseline-v1/README.md`,120 intervalos
servidor completos y170muestras host, sin población/clientes. Memoria residente
~1276MiB estable; CPU baja en esta base vacía. GetFPS64 constante14.2857 no
se interpreta como capacidad del servidor. No demuestra80–100 jugadores.

Sonda nativaV1: el motor rechazó su función enorme en init.c:1041 (Too many
instructions per function) y el proceso terminó con access violation. Logs en
native-nav-probe-v1-failed. No se ejecutaron consultas. V2 divide las mismas751
referencias en bloques32; geometría/umbrales/referencias idénticos, SHA misión
343a8752, sin tocar WRP/NM. El linter offline aceptó ambas; V2 compiló y produjo
el registro completo en el motor. Nunca confundir PASS del linter con carga de misión.

## Consultas y cruce físico, continuación12:44

`native-nav-v2/verification.json`: los cuatro caminos se encuentran. Las751
referencias secas dan750 muestras a≤2m; la restante está junto al acceso este
de Narva.625 puntos de cuadrícula regional pasan. No acredita conectividad
entre puntos ni incluye un control seco específico de Kronstadt.

El gate geométrico0.8m conserva FAIL:26 muestras por sentido fuera del límite,
error máximo7.2789m. Al este, navmesh≈2.2m y superficie física9m.
`native-nav-seam-v1` discrimina filtro WALK/ALL y Y solicitada; ambos reproducen
el resultado. No se aisló el algoritmo interno. El análisis de cabeceras de
teselas (`native-tile-comparison-v2.json`) solo prueba39 cambios de conteos/
bounds locales frente al NM anterior; no decodifica toda su geometría.

Consumidor: runfcd183c5, `native-chase-v2/verification.json`, PASS con613
registros de actor, salud100, desviación vertical respecto a la superficie
1.44–40.11mm y sin movimiento forzado de IA. Control local8.845s; ida49.822s;
regreso55.789s. Máximo hueco0.203s, lateral3.212m y deriva del prey0.
La espera previa20s está registrada. El anterior `native-chase-v1` conserva
FAIL por deriva5.246m del prey en su control inicial, aunque cruzó ambos sentidos.
Ocho corrupciones del registro real fueron rechazadas por el verificador.

Esto prueba el corredor ensayado; no acepta toda la red ni convierte la consulta
geométrica fallida en PASS. Evita deformar terreno correcto solo por una altura
navmesh que no predice la trayectoria física en este caso.

## Evidencia previa: paso bajo el puente

Run `c9dc7555-6ba7-4913-ae98-6a63d73c6dbb`, solo servidor, misma misión,
controlador y mapa. `route-input-server-v1/analysis.json` pasa todos los gates
sin cambiar el verificador:226 muestras continuas,196 consecutivas con
propulsión,97.828m netos entre extremos, salud600 constante y desvío máximo1.344m.
Las posiciones cruzan el plano del puente de+44.163 a−51.810m; las muestras bajo
el vano central permanecen a menos de2.321m del eje. END confirma llegada.
La ruta de diseño mide120m: distancia neta entre extremos no es longitud recorrida.
Log SHA8ad568ff819fd992d69b5c2d8d21df5fa8842a8a0e8c1edd8966c8bd09bc5ba3.

El run anterior `ca8a8d0f` también llegó sin daño, pero conservó un hueco2.387s
entre t0.994 y3.381, motor apagado y movimiento0.022m. Su verificador estricto
sigue INCONCLUSIVE_OR_FAIL en `route-input-complete-v1`; no se relajó el gate.
La repetición solo servidor eliminó ese hueco en esta observación; no aísla su
causa interna. No acredita imagen cliente, tripulación, regreso ni barcos medianos.

Seis negativos rechazan falta de END, hélice parada, daño, hueco durante marcha,
teletransporte y distancia declarada falsa. `test_route_verifier.py` usa el log
medido como origen, no fabrica una ejecución positiva. Navmesh nueva y red
regional siguen pendientes. Ambos runs cerrados por MCP; lease none/caja libre.

Terrain Builder abrió la copia `tb/narva_navigation_v3`. El ASC estaba en
`tests/narva_navigation_v3`; el diálogo miraba `tb/narva_navigation_v3`. Se copió
allí el mismo archivo, comprobando SHA c1f23f24, y se importó. Rebuild terrain
confirmado y proyecto guardado a01:49:01: TV4P18282bytes, nuevas capas v4d012/013
no vacías. La carpeta de salida ya apunta a la copia. El guardado estuvo sin
responder unos segundos y terminó sin cerrar el proceso.
WRP literal `baltic_navigation_native_heights_v1.wrp`, SHA321a9ccc, verificado.
`native-height-edit-ledger-v1.json` prueba1242 cambios exactamente iguales al
registro delta congelado y todos los demás vértices idénticos al baseline.
`native-height-import-v1.json` conserva el FAIL inicial de comparación directa
con ASCII: cuatro valores del borde ya discrepaban en el baseline por hasta
2.98e-8m. No se aisló el mecanismo interno; no se relajó tolerancia.
La base sin cambios falla como negativo contra el registro de1242 ediciones.

Reconstruir desplazó los objetos viejos. Central elevado aAbsolute8.476612;
dos tramos exteriores importados desdeTXT con Advanced options / Absolute,
misma cota. Pond retirado por selección única y Cut: interfaz muestra3 objetos,
pond0. Save Project terminado02:03:27; TV4P18210bytes. TXT relativo alternativo
se preparó pero NO se importó.

Export objects_v1 quedó incompleto a02:06:12:16777240bytes, exactamente cabecera
y alturas; ese prefijo coincide con el WRP válido321a9ccc. El lector completo
lo rechaza antes de la tabla de texturas. La consola solo conserva la confirmación
del export anterior; editor responde. Causa sin aislar, no aceptado ni desplegado.
Fuente: `native-objects-export-incomplete-v1.json`. Las dos copias de la cuadrícula
v4w coinciden por SHA3f813afe; esto no prueba que el exportador la haya consumido.
Discriminador histórico: cerrado y reabierto desde Recent projects, conserva3
puentes/pond0 en UI. Ctrl+E abrió export a `baltic_navigation_native_reopened_v2.wrp`.
El guardado terminó después en reopened_v2 y pasó ambos gates; ver continuación
vigente arriba. El proyecto sigue respaldado; no se regeneró Generate Layers.

`verify_native_bridge_layout.py` acepta el candidato derivado ya probado en motor
9f1154c9 y rechaza el export nativo antiguo de dos objetos. Las poses del nuevo
editable quedaron acreditadas después por reopened_v2. Mantiene los límites anteriores
de0.5mm en posición y1e-6 en rotación/escala, sin ampliarlos tras observar el resultado.
Cuatro mutaciones negativas independientes del candidato de referencia (altura,
rotación, ID duplicado y NaN) se rechazan con exit1; `bridge-verifier-controls`.
Copia del editable fuera de OneDrive: `native-project-checkpoint-receipt.json`,
ZIP778cfcf8,56 archivos/181742771bytes, CRC y SHA de cada entrada comprobados.
Excluye GIS/materiales/ASC/WRP/navmesh externos: respaldo de proyecto, no entrega completa.

## Lo preparado

- `vanilla-assets.json`: Boat_01 instalado mide5.016m de eslora y2.107m de manga
  en silueta estática. Se midieron seis puentes por Geometry/Roadway; calado
  flotando y tripulación no se deducen de esos límites.
- `baseline-waterways.json`:2417 muestras de los ejes Narva, Neva, delta y Luga;
  ninguna demuestra3m de profundidad si se conecta al mar mínimo0.5m. Es una
  comparación condicional: los lagos elevados todavía carecen de agua propia.
- `regional-hydrology-constraints.{json,png,pdf}`: estrechamientos, conflictos
  geométricos con islas y relaciones superpuestas de Peipus. Auditoría sin
  modificación regional; no se acredita una ruta conectada por contar muestras.
- `narva-navigation-v3.{png,pdf}`: dibujo de ingeniería, no captura del juego.

Narva V3 modifica1242 vértices conservando exactamente los demás. Canal útil24m
en el tramo auditado, mínimo conservador3.15m de profundidad en272 triángulos.
Tres tramos vanilla25m reservan tablero9m; hueco central18m y6.338m bajo las vigas
con agua máxima1m. Empalmes calculados a cota9m y pendiente máxima5.052%.
La reserva del barco mediano12×4m, calado1.5m y altura4.5m es [DESIGN].

### Control en mar abierto

El run759f03c7 (BalticBoatCalibration) separó el cauce del problema de entrada:
121 puntos de mar/fondo verificados alrededor de(2000,11200),170 muestras/85s,
0.30m netos, salud600 constante. En las cuatro fases de aceleración la marcha
actual1 era neutra1, RPM700 y hélice0. GetClutch devolvió-1832932600; no se usa
para inferir acople. Fuente: `calibration-v1/analysis.json`, log inmutable
SHA3bd676508467333b188deae21540a28cd5397361c1ea2a1f62a4aeb5fa4b324b.
Esto no valida navegación ni demuestra un bloqueo geométrico del río.

Segundo ensayo completo: run31271ac6, `calibration-input-v2/analysis.json`,
PASS_CALIBRATION_MOVEMENT_ONLY:89.278m netos entre muestras, salud600 constante,
85 muestras consecutivas con transmisión/propulsión. Termina por guardia de90m
(la última muestra periódica precede la parada), sin validar la fase de frenado.
GetThrottle desde CallLater lee0 mientras la simulación consume las entradas de
OnInput; no usar ese readback aislado para negar propulsión medida.

Runbf32f425 del regreso a Narva interrumpido al detener Computer Use con Escape.
151 muestras/75.5s,55.866m netos, salud600, desvío máximo1.330m y121 muestras
seguidas de propulsión. Sin END ni llegada al final: INCONCLUSO, no PASS del cruce.
Evidencia `route-input-v1/analysis.json`; la geometría medida coincide pero el
gate global rechaza la terminación incompleta. No hubo más inputs de Computer Use.
Ambos runs cerrados por MCP; estado final sin lease/run propio ni comandos pendientes.

Se preparó `plans/boat-control-calibration.md`: segundo discriminador con entradas
desde BoatScript.OnInput, contrato explícito de transport.c:251–262. Addon de
diagnóstico separado, activación por instancia en BalticTrial dedicado y parada
por inputs obsoletos; sin modificar vanilla o física/poses. PBO c5414ffe, fuente
empaquetada idéntica. La guía de empaquetado usada es dayz-pbo-build.

El verificador exige además10 muestras consecutivas de motor, RPM>800,
marcha no neutra, hélice girando y velocidad horizontal>0.5m/s. Rechaza como
prueba de propulsión un log manipulado con84.5m de deriva pero hélice0, y
rechaza log truncado sin END. Casos en `calibration-v1/verifier-tests.json`.

V1 falló por cinco vértices de talud dentro del cauce; V2 resolvió el agua pero
dejó2.64m de escalón al este; V3 pasó ambos criterios al comprobar que no comparten
vértices de soporte. Se conservan los FAIL. Negativos: base anterior y tapón
somero fallan la profundidad; no se redujeron criterios para aceptar el piloto.
El tramo termina en un río todavía sin preparar: no es navegación Narva completa.

## Fuente, paquete y límites

| Artefacto | SHA-256 |
|---|---|
| ASC regional anterior |d21cdf2c9e7bc7602f9d66e8a7ca0464258b0afccabe77c3ff26655b0bda6751|
| ASC candidato V3 |c1f23f24808cb6f1ff858f47a378f6bdf8211387f63c110a12ff72fd3bd82d3c|
| WRP derivado0WZD |9f1154c945a867c831a66222a3734ee114044613260039b476111a4df8e3586b|
| WRP compiladoOPRW29 |6859bda54de1e76f511b9a8e6fbfbc5eec001feae3b4e1ff04522212e550beb4|
| PBO de ensayo |ee93a4c4a00a81e246ea81fbd3d83b25ba642b24d650cbb738ecf26b022eb67d|
| PBO base conservado |ebc60f4f089b3e125426263b456d1f9662bc828c506993bbabbf0e43023a06d4|

Compilación aislada terminada exit0 y contenido comprobado. Únicamente cambia
`baltic_trial.wrp`:6826 entradas restantes idénticas a la base, incluida la navmesh.
Eso la convierte en navegación obsoleta para el candidato, conservada solo para
arrancar la prueba. No entregar este paquete como base técnica terminada.

El0WZD se deriva del nativo validado, comprobando4194304 alturas, cabecera,
asignaciones/materiales y poses. No es exportación literal de Terrain Builder.
La copia `tb/narva_navigation_v3` conserva8934 archivos de la base por hash;
el diálogo Abrir no confirmó carga, por tanto no se importó el ASC nuevo allí.
El arte satélite conserva aún el cauce antiguo. Ambos gates siguen abiertos.

## Medición real del motor

Run `8dbd91ff-5ea2-4146-b8ba-e60a567fdd17`, misión `BalticBoat.BalticTrial`.
Init compilado SHA `37f673890407c01a8a1d2fd17109db033f2d90ba6f0664ffa4b6513a544ff6ca`.
Registro completo `runtime-launch/boat-v3-complete.log`, SHA
`22a51c889bb7d1376add895193da78da571ecc7330efbded8f544d1cec326a2a`.
`runtime-verification.json` da PASS_SAMPLED_CHANNEL_AND_DECKS:

- 172 vértices únicos coinciden con el ASC candidato; error máximo9.54e-8m.
  El ASC anterior falla con diferencia4.65m. Todos informan mar.
- Agua mínimo/máximo/actual0.5/1/0.98245m; profundidad conservadora3.15m.
- Tres puntos Roadway transformados a mundo están aY=9m. Esta lectura no
  equivale a consulta de colisión ni prueba del gálibo con tripulación.

La sonda registró360 muestras en180s. Lancha vacía, salud600 sin pérdidas,
motor encendido en340 muestras y acelerador0.22 leído; desplazamiento neto
horizontal3.247799m, máximo salto horizontal entre muestras0.05831m. Terminó
TIMEOUT_CONTROL_INCONCLUSIVE en objetivo1; no completó el cauce ni el puente.
La velocidad total también contiene movimiento vertical: no convertir su
máximo1.98m/s en prueba de avance. Sin teletransporte/control de velocidad por
frame. No hay aceptación de conductor, ida/vuelta, IA ni ríos completos.
La captura de ventana no dio una vista fiable del juego; render de este run
no revisado. La navmesh conservada sigue siendo antigua.
El registro conserva avisos de PluginConfigDebugProfile y ficheros opcionales
de misión ausentes; no se declara un arranque libre de errores/avisos.

`tools/navigation/test_runtime_verifier.py` rechazó un log sin END y otro con
identidad ASC errónea, cada uno por su criterio correspondiente y exit1. Recibo
en `verifier-negative-tests.json`. Son negativos del verificador, no del barco.

## Carreteras lisas: medición del terreno de acceso

`approach-smoothness.json`, muestreo0.25m sobre8m de ancho y242.5m por acceso:

| Medida | Oeste | Este |
|---|---:|---:|
| Pendiente longitudinal máxima |4.905%|5.052%|
| Cambio entre pendientes de6m |0.732pp|1.021pp|
| Caída transversal máxima |0.190%|0.196%|
| Desviación respecto a cuerda de6m |9.09mm|8.75mm|
| Desnivel en empalme al tablero |0m|0m|

Estado MEASURED_ONLY_VEHICLE_ACCEPTANCE_PENDING. No hay piezas de carretera
colocadas ni velocidad de conducción aceptada. Medir rasantes ahora evita
dejar los accesos para resolverlos durante el mapeado final.

Ampliación del mismo muestreo hasta320m desde el centro del puente:
`approach-outer-transition.json` y `approach-profiles.png/pdf`. Fuera del tramo
diseñado aparecen cambios de pendiente de4.152/6.274pp y desviaciones de cuerda
de44.7/133.8mm. Las máximas están sobre terreno exterior sin preparar; no se
atribuyen al puente ni a una regresión introducida por V3. Extender la futura
rasante hasta conectar de forma suave con el siguiente tramo de carretera.

## Intentos anteriores y cierre

Primer RPT00:27: misión/mod correctos, readiness_timeout antes de Mission por
`mcp_weapon.c:929 Unsafe down-casting` del bridge compartido. No se modificó
DayZ_MCP. El RPT Chernarus00:29 es de otra sesión: la atribución inicial fue
corregida. El consumidor estuvo disponible en un ensayo posterior.

Dos intentos propios detectaron fallos reales que el linter no rechazaba:
812b37a1, Broken expression en la condición con Count()-1; se separó el cálculo.
993fd799, asignación0 a FileHandle; su typedef real esint[] y se cambió a null
(`P:/scripts/1_core/proto/ensystem.c:390`; misión actual:342).
Fuentes fallidas y logs preservados; última fuente compiló y ejecutó la sonda.

Todos los runs propios cerrados mediante MCP; el último devolvió forced_kill,
exit_metrics_valid=false y cleanup_degraded=false. Estado posterior self none,
caja libre,0 pendientes. No afirmar cierre normal ni intervenir procesos ajenos.
Refrescar session_status antes del próximo arranque; no basta este snapshot.

## Próximo avance

Copia externa verificada: `archive-receipt.json`, ZIP83 entradas/104900121 bytes,
SHA c7009f88ded6603f0cfdb1a047433914c07c399c7b232b960b8a858b36058cd9.
Contiene ASC/WRP/PBO, fuentes y evidencia de los pilotos; no sustituye el respaldo
anterior de los editables TB. El recibo y esta nota se añadieron tras verificar
el archivo, por lo que no están dentro de ese mismo ZIP.

Completar la exportación nativa de objetos y comprobar reapertura; después
cerrar hidrografía regional antes de generar la navegación base. Después del
mapeado habrá otra generación. No reiniciar el ensayo antiguo de IA sin un
discriminador nuevo ni declarar versión1.0 por esta prueba local.
