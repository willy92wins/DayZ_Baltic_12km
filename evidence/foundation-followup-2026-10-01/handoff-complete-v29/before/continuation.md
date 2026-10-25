# Baltic — continuación de la base, 1 de octubre de 2026

Sesión única de Codex, executor/integrador por petición viva de Guillermo:
continuar el terreno/navmesh y agrupar Computer Use al mínimo. Edificios,
vegetación colocada y carreteras físicas siguen para después. El estado de
procesos cambia durante el trabajo: consultar el
[HANDOFF](<P:/DayZ_Baltic_12km_dev/HANDOFF.md>) y
[state.json](<P:/DayZ_Baltic_12km_dev/evidence/foundation-followup-2026-10-01/state.json>).

## Resultado comprobado

El mundo V10 `d1008dd6`, agua `f9a5cdf7` y navmesh `e8348efc` permanecen
intactos. No se ha vuelto a importar terreno ni alterado el encuadre.

- Cruce continuo del puente: control y ambos sentidos PASS, 2.188 registros
  activos, salud/contacto/llegada correctos y 18 pruebas negativas rechazadas.
  [Evidencia V4](<P:/DayZ_Baltic_12km_dev/evidence/foundation-followup-2026-10-01/continuous-pursuit-v4/runtime-complete/verification.json>).
  Se corrigió la conversión del rumbo de la sonda humana. El registro V3 midió
  2.019 muestras con rumbo no nulo. Las velocidades V4 se evalúan sobre muestras
  periódicas de 200 ms; los eventos conservan controles físicos de envolvente.
  No convierte los ensayos anteriores de ruido estacionario en PASS ni prueba
  todos los comportamientos posibles de IA.
- El piloto de carreteras V14 pasa geometría independiente en costa, colinas y
  sur: 7.139 secciones cada 0,37 m, 33 posiciones laterales por sección, sin
  excesos de anchura, pendiente ni cuerda. Protecciones y exterior conservados;
  cinco alteraciones deliberadas rechazadas. Cambia 729 vértices, como máximo
  1,464067 m. [Piloto](<P:/DayZ_Baltic_12km_dev/tests/regional_road_triangles_pilot_v14/independent-consumer-with-support.json>).
  Sigue siendo offline y parcial: no es el terreno desplegado ni su conducción.

- Hidrografía independiente del piloto V14: 408 polígonos de agua,
  1.025.150 celdas nativas de agua inalteradas, 283 polígonos de tierra
  protegida y 5,941332 km² de reserva seca preservados. Tres alteraciones
  deliberadas de agua/isla/reserva rechazadas, además de los cinco negativos
  geométricos. `tests/regional_road_triangles_pilot_v14/hydrology-independent.json`.
- Narva6 aisladoV5: 2,199 km, 1.757,178 s, 3.951 muestras y 549 transiciones
  completas; salud600, continuidad, paso bajo puente, extremo y lecho PASS.
  Delta8 aisladoV4 y delta10 aisladoV5 también PASS. Cada uno tiene 12 controles
  negativos de física/eventos y cuatro de reloj. El agregadoV4 conserva FAIL
  por interrupción de10; los casos8/10 solo se aceptan individualmente.
  [Cobertura consolidada](<P:/DayZ_Baltic_12km_dev/evidence/foundation-followup-2026-10-01/river-accepted-segment-coverage.json>):
  12 segmentos aceptados entre distintas ejecuciones, 26,600558 km de cauces
  seleccionados. No recorrido único continuo, flotilla, tripulación o barco
  mediano. BALTIC003 y004 cerrados para esos consumidores concretos.

## Fallos conservados y trabajo pendiente

El muestreo denso de V10 encontró 6.854 secciones sobre el límite transversal
de 3 cm, de 88.452 elegibles; son muestras, no ese número de baches diferentes.
V11/V12 no resolvieron. V13 produjo alturas pero falló la revisión independiente
y creó 24 taludes sobre 35 grados, por lo que no se importó. V14 cambió el modelo
a gradientes de triángulos que cubren toda la banda y sus transiciones.

La extensión conjunta V15 tiene 94.992 variables y 4.850.084 restricciones;
resultó inviable y no escribió ASC. Hay 224 contradicciones individuales,
204 sobre alturas completamente congeladas, de anchura/rasante/cuerda.
La continuación V16 conservó agua/fairways y permitió ajustar tierra seca
protegida sin perder cota mínima. V16/V17 siguieron inviables: se reconstruyó
un certificado de189filas que dependía de ocho vértices fijos secos, a más de
475m del agua. Aumentar el límite vertical no podía resolver esa transición
lateral estrecha. V18 amplió la transición de12 a24m; con3m de cota máxima
otro certificado local exige al menos3,877807m. A4m el solve completo devolvió
Infeasible sin conseguir certificado dentro del presupuesto. V19 usó generación
de restricciones sobre la matriz original y consiguió certificar en43s que
los mismos dos puntos necesitan al menos4,384321m. V20/V21,cotas5/6m,
siguen inviables. La traza exacta de79filasV21 identifica un borde fijo seco
a33,45m del eje: V22 abre transición48m solo en x[4278,4572],z[6876,7008],
manteniendo24m fuera. Nueva matriz en construcción, cota5m prevista. No ASC.
Minimax agotó600s, última cota inferior5,131519m; no mínimo global probado.
[Diagnóstico](<P:/DayZ_Baltic_12km_dev/tests/regional_road_network_v15/infeasibility-diagnostic.json>).

Fluvial V3: control 11 PASS; la primera ejecución quedó incompleta al expirar
el lease. En la repetición, delta 8/10 se desvió antes de la fase terminal y
Narva 6 recibió OnMissionFinish a los 923 s. El motor terminó normalmente,
con lease activo; no se ha aislado qué inició ese cierre. Las dos rutas del
delta coincidían temporalmente cerca de un mismo cruce, con separación nominal
de 3,11 m entre centros; no demuestra colisión. La prueba aisladaV4 y los casos
únicosV5 completaron después los tres pendientes, con los mismos cauces,
radios y criterios físicos; ver arriba. Los resultados previos se conservan.

Coche regionalV1: costa/sur cuatro casos PASS; ambos de colinas fallaron solo
la maniobra terminal. V2 desacelera antes y corta motor/frena al llegar despacio:
ambos sentidos PASS,1.648muestras,4contactos,salud1000,parada5.4s,18negativos.
Mismo terreno y addon de mando; registros completos antes del cierre forzado.
V2release informó lease_expired; estado posterior libre. BALTIC006 aceptado.

Faltan vistas Neva/reserva/sur/conjunto. NevaV2 pidió captura con aplicación
activa, sin DDS; V3 estaba inactivo y no ejecutó la llamada. V4 mantiene poses
y óptica, amplía a90s cada pose: tres grupos empaquetados/lint/paridad.
Bloque CU aplazado al detectar lease ajeno para una prueba KP Rule12.
El crash de transición distante de cámara sigue separado del uso normal por
regiones. La carga anterior de 100 infectados no acredita 80–100 jugadores.

## Escritorio, conocimientos y conservación

Hasta este checkpoint no se ha usado Computer Use. Las pruebas son de servidor
y los cálculos se hacen fuera del editor. No se ha reactivado la automatización
nocturna cerrada ni consumido otro reset; lectura13:40UTC:57% semanal restante.

Se actualizaron dos referencias de la skill local `dayz-terrain-workflow`:
rumbo/muestreo/consumidor físico del puente y continuidad transversal de las
carreteras. `SKILL.md` conserva exactamente su hash anterior; UTF-8 y enlaces
locales verificados. El validador YAML completo no pudo ejecutarse en los
runtimes aislados por ausencia de PyYAML; no se instalaron dependencias
compartidas. [Recibo](<P:/DayZ_Baltic_12km_dev/evidence/foundation-followup-2026-10-01/skill-reference-update.json>).

Sin commit: HEAD `4ff154b7`, con cambios anteriores compartidos preservados.
Los archivos nocturnos permanecen inmutables; evidencia nueva exclusivamente
en `evidence/foundation-followup-2026-10-01/` y carpetas nuevas de pilotos.
No es aceptación de mapa 1.0 ni del conjunto del terreno.

## Actualización posterior — outline y agua, 01-10 tarde

Esta actualización sustituye los pendientes y el estado de escritorio anteriores.
Neva/reserva/surV4 ya tienen capturas Sky originales y telemetría completa;
Neva/sur17controles negativos PASS. Sur se capturó en la repetición c6288e84,
pero faltó guardar la identidad de sus procesos antes del cierre: el archiver
canónico conserva FAIL. No convertir esa vista en aceptación visual global.

Petición viva: suavizar el outline y eliminar agua intermitente fuera de orillas.
Plan `P:/DayZ_Baltic_12km_dev/plans/outline-water-smoothing-v1.md`.
Sonda localV10 d6efac88 cerrada prematuramente por un error de secuencia propio:
129.47s/512épocas parciales, sin COMPLETE.12bordes secos vectoriales inundados;
4controles interiores a1.25m secos. Mar0.5..0.999984m; máximo visual observado
en el control1.107m. No sumar amplitudes como fórmula interna demostrada.

Auditoría geométrica:25647muestras secas bajo1.25m dentro de celdas costeras;
no contradice vértices secos≥1.25m ni mide superficie inundada. V24a inviable
por146restricciones individuales; ejemplo islote14.4969m² entre vértices a−12m.
V25 amplía solo el límite superior15m en759vértices mojados cercanos. Resuelve
en186.7s, ASC f7a220fd,3234825vértices cambiados, delta máximo13.923m local.
Consumidor independiente en curso; NO importado, V10/despliegue intactos.
Ningún proceso DayZ propio; CU terminó tras capturas. El registro `runs` es una
lista y vacía identidades de procesos al cerrar: guardar el vínculo mientras vive.


## Checkpoint V33 — navmesh y agua comprobadas; carreteras pendientes

La petición sigue siendo terminar terreno y navmesh, suavizar el contorno y evitar
agua intermitente en tierra. Computer Use se detuvo por Escape físico del usuario;
no hubo más uso del escritorio. DayZ se cerró ordenadamente, lease liberado y
session_status confirma sin procesos propios ni ocupación. Neva quedó sin captura
y con protocolo de cámara incompleto: su FAIL permanece guardado.

Candidato aislado @DayZ_Baltic_OutlineV33: mundo SHA256
38ebe847b5dd553ac31bd0d51bd9d1c192965352a8a04188b7bdcef5c8eaea0c,
WRP compilado 2ccb8dc4b34d3064100d130a2421ebd77d3f3fcc5ef8a5618c1d7c4221ac92f0.
ASC9d2954fc y referencia8e84d5ce. Importación y reapertura nativas verificadas.
Las exportaciones literales 5/6 conservan670 residuos Y de agua de hasta0.954µm;
el paquete usa un derivado explícito que restituye solo esas Y. No llamarlo
exportación literal. V10 estable d1008dd6 sigue intacto.

Navmesh nueva generada sobre ese WRP:966289/966289 tiles,
446230080bytes, SHA256425b84885d05a588c4c80e0561eb01d02849816f7ff9c0c61f6b49922a4fc842.
Adjunta sin rebinarizar:6826 entradas restantes idénticas.
Consumidor regional V6 PASS:81212 puntos de agua/tierra,0 fallos,
314 muestras de navegación/15 rutas; no equivale a locomoción física completa.
Evidencia: outline-v33-native/, outline-v33-consumer/acceptance.json.

Agua dinámica local PASS:664 épocas/15936 muestras en24 coordenadas congeladas,
20..189.846s, COMPLETE198.006s. Margen seco mínimo0.28706m; profundidad mojada
mínima0.487773m; mar observado0.500012..1m. Positivo real y18 negativos PASS.
No acredita máximo global de oleaje ni todas las orillas.
Evidencia: outline-v33-water/{acceptance,real-negative-controls}.json.
Sur y reserva tienen imágenes originales y protocolos de cámara/restauración
completos. Textura provisional gruesa y franja azul visual siguen pendientes;
no declarar arreglados todos los píxeles. Neva V33 necesita repetición al retomar.
No utilizar sus41 métricas parciales como aceptación de rendimiento.

La auditoría idéntica a1m/17 offsets sobre8m detectó regresión vial:
V10 1781/88452 secciones fuera de3cm y1 intervalo central >6.5%;
V33 7261/88452 y147. Son muestras, no baches contados. El filtro protegía
vértices sueltos y el incremento de bajos incluía carreteras; contribuciones
individuales no aisladas. BALTIC005 y007 siguen abiertos.

Plan nuevo: plans/road-network-v24-on-outline-v33.md. Restricciones congeladas
con247503 variables/9713332 filas y transición48m sobre V33; agua+30m, fairways,
Narva480m y suelos de islas protegidos. Delta<=6m respecto a V33 y V10 para evitar
acumular dos cambios máximos. Solver iniciado a17:16UTC, sesión88223, límite600s
con padre650s/1 hilo/guardia2GiB. Al checkpoint sigue vivo; sin candidato aceptado.
Identidades exactas: road-v24-process-checkpoint.json. Revisar progress.json,
solve.json y resultado de sesión antes de actuar; el estado de progress no prueba
que haya terminado mientras el worker siga vivo. No iniciar otro cálculo igual.

Después de cualquier ASC: consumidores independientes de banda0.37m×0.25m,
hidrología, regiones continuas de costa y81212 puntos congelados, negativos,
reserva/Narva y límites compuestos. Las extensiones de los consumidores a padre
V33 solo están comprobadas sintácticamente; no han validado candidato V24.
No importar ni sustituir paquete sin esas puertas. Si cambia el terreno,
repetir nativo/compilación/navmesh/consumidor y conducción aplicable.

Referencias de la skill local dayz-terrain-workflow actualizadas con persistencia
Y, empaquetado derivado, regresión vial y superficie local de lagos. UTF-8/enlaces
locales PASS; sin validación YAML completa ni nueva skill innecesaria.
No commit: HEAD4ff154b7 y cambios anteriores compartidos preservados. No mapa1.0
ni aceptación global. La automatización nocturna sigue cerrada; ningún reset nuevo.

Checkpoint: P:\DayZ_Baltic_12km_dev\evidence\foundation-followup-2026-10-01\outline-v33-checkpoint.md
Actualizado UTC: 2026-10-01T17:21:34.793050+00:00

## Continuación V29 — 2026-10-01T19:13:42.937701+00:00

Este estado sustituye los pendientes del checkpoint 17:21UTC. [WORKS, MECHANISM UNKNOWN] V29 pasa seis puertas offline: 239.126 secciones viales, cero fallos;
621.260 extremos de orilla y 631.284 marinos, 81.212 puntos congelados,
reserva/Narva/islas, siete negativos viales y cuatro hidrológicos. Diecinueve
caras de agua cambiadas se aceptan por prueba continua nueva, no por herencia.
ASC `ed6cdaa5`; V24–V28 rechazados quedan conservados.

Importación/Rebuild/guardado y export r1 reales en copia V29. Alturas/materiales
correctos, dos nuevas piezas de agua con Y +5,5003/+6,1817 cm. Corregidos solo dos
offsets ALB1 con backup verificado, seis bytes cambiados y tres negativos.
Capa `98a9bed6`; falta comprobar r2 y persistencia al guardar/reabrir/exportar r3.
Los 9.036 archivos V33 originales siguen iguales. V10 y V33 desplegados intactos.

El control volvió a mostrar otra aplicación después de seleccionar/activar TB;
se detuvo y reseteó. Pregunta de foco pendiente, sin pedir nuevas autorizaciones.
TB PID321476 en diálogo Select, nombre vacío; r2 no existe. No DayZ/Navgen activos,
lease libre y cero comandos pendientes. No se envía entrada a la otra aplicación.

Próximos consumidores ya preparados: V7 regional y seis viajes de sedan V3 con
XY/criterios congelados y Y de V29; linter PASS un archivo sin errores ni avisos.
No ejecutados, requieren nuevo paquete identificado y navegación regenerada.
Skill local regional-relief actualizada con comparación de poses exportadas;
corrección marcada pendiente, UTF-8/enlaces verificados y entrypoint idéntico.
Validador YAML completo no disponible por PyYAML ausente, sin instalarlo.

[Checkpoint vigente](<P:/DayZ_Baltic_12km_dev/evidence/foundation-followup-2026-10-01/outline-v33-checkpoint.md>).
[Recibo skill](<P:/DayZ_Baltic_12km_dev/evidence/foundation-followup-2026-10-01/road-v29-native-skill-update.json>).
BALTIC-005/007 abiertos, sin aceptación 1.0/global. HEAD `4ff154b7`, sin commit;
no se restauran cambios compartidos. Cuota 19:07UTC: 15% restante; sin reset nuevo.
La ventana nocturna anterior permanece completada, automatización PAUSED.

Cierre documental local: índice de esta sesión y enlaces nuevos comprobados;
PROJECT-MAP regenerado solo para Baltic. Auditoría global del vault FAIL por
19 sesiones sin índice y cinco pares vivos de prime-agent-package/delegar ajenos
a este cambio. Pin compartido del generador no coincide con su fuente vigente;
no se modifica ese pin ni se declara PASS global. Evidencia en
`road-v29-native/documentation-checkpoint.json` y `vault-link-audit.txt`.
