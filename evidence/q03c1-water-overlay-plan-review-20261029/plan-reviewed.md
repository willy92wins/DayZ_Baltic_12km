# Q03C1 — medir cobertura vertical de agua guardada sobre un lecho completo

Estado: BORRADOR_PENDIENTE_DE_REVISION. Unidad geométrica concreta después del
índice Q03B6; no nueva infraestructura genérica. Planner/integrator Codex,
executor local Codex explícito para contrato/oráculos/código una vez revisado.
Una lane externa Muse Wonder1.0 CLI nativo; no nuevo council.

## Intención y evidencia [EXACT]

Q03/Q11 del plan quality-council-procedural-map-20261029 exigen distinguir lecho,
agua y oclusión antes de cambiar modelos/terreno. Q05 añadirá toda huella vial y
ambos accesos; el corredor histórico8m no sustituye piezas12/9m ni ancho útil.
Este corte entrega áreas y testigos geométricos de DOS capas históricas. No
denomina «visible» a un lecho que podría estar oculto por terreno u otro modelo.

Q03B6 report aa8d3ace483967ac5dec430f6a0e6e99cc7fed27196b16ac480040433454b060
y consumer verificado ligan los204NPZ/7046miembros. El JSON guardado contiene:
201 pilotos,4760 caras water en total; el modelo exacto
`baltic_stream_pilot/cs_kit_118_0000.p3d`, index3579, instance19394363,
pose_row13844, tiene1520 bed y24 water. Archivo relativo
`pilot-visible-surface-extraction-20261028/models/cs_kit_118_0000.npz`.
Todos los pilotos ya están en ALREADY_WORLD_UNCERTIFIED; no transformar de nuevo.
Época3d955, no instalado actual/candidatoB3/sonda nativa. El vínculo es por ID,
nombre e índice; no se vincula una fotografía a esta pieza por cercanía. Cont65
permanece sin geometría humana enlazada. Nueve rechazos abiertos, C1NOT_REVIEWED.

Anclas leídas: pilot_visible_surface_ev112.py:172-234 guarda grupos mundiales,
counts/flags/IDs y source_category; pilot_visible_exposure_ev112.py:68-121
separa footprint de agua y relación vertical, y usa unión para no duplicar
áreas; su corredor:28-47 es8m. pilot_surface_refinement_ev112.py:71-97 compara
contra terreno/agua nominal pero no certifica oclusores completos. Sus CLIs
consumidos NO se relanzan y sus tolerancias float no se trasladan a este corte.

Lectura aprobada disponible: saved_scene_archive_q03b2.py:260-352,
Session(**limits).open(path,schemas); source Q03B6 saved_scene_io_q03b6.py:74-110,
Reader.open(spec,names,predicate), sobre snapshot/hash y esquemas estrictos.
Estos helpers sellados se usan como primitivas pinadas, sin modificar ni
invocar CLIs anteriores. I/O/NumPy/zlib compartidos declarados.

## Alcance, contrato previo y lectura [DESIGN]

Congelar contrato/oráculos literales ANTES de código; revisión de código incluye
contrato. No otra investigación de contenedores ni lectura libre de204NPZ.
Pins externos: e967 escena, f8f8f6dc Q03B6, report+consumer+receipts; 201 specs
piloto exactas del contrato original, manifest/inputs/catalog rows necesarios,
Reader/Session/header y fuentes de las anclas. No derivar expectativa del
informe que producirá esta unidad ni cambiar pins para PASS.

Una Session acumulativa por caminante,201NPZ piloto, no prototipos/instancias
releídos innecesariamente. Verificar todos sus descriptores/digests contra el
índice verificado y SHA físico original; máximo16MiB stored porarchivo,
128MiB expandido porarchivo/262434599 acumulado/35miembros. No mmap/pickle.
Retener sólo copias de water/IDs de201pilotos y bed/IDs/category del seleccionado;
reservar copias antes de asignar y contabilizar memoria retenida. Memoria del
helper y de la escena no se confunde con reservas lógicas.

Gate de geometría: finite, n==3 y flags==0 para caras utilizadas; cuarto slot
de padding intacto y observado, no nueva triangulación de quads. Si se refuta
triangularidad o aparecen flags, REJECTED_GEOMETRY y no se triangula por cuenta
propia. Comprobar IDs fuente y cardinalidades1520/4760 mediante índices exactos,
no nombres parciales. Categorías sólo como anotación histórica; no semántica
render. AABB para descartar pares imposibles, nunca como huella ni ancho útil.

## Medición exacta [DESIGN]

Objetivo por cada cara bed: área proyectadaXZ total, cubierta por al menos una
cara water seleccionada con altura W>=B en el mismoXZ, y su complemento. También
área con footprint de agua sin condición de altura y área de footprint con agua
estrictamente inferior aB en TODOS los water que la cubren. De aquí:
total = covered_at_or_above + footprint_only_below + no_water_footprint.
No suma de áreas por pareja, ni suma por caras bed llamada unión mundial: bed
pueden superponerse. Informe conserva resultados porcara y, si suma, la etiqueta
FACE_AREA_SUM_WITH_MULTIPLICITY. Contacto W==B cuenta cubierto en esta medición,
sin certificar agua física, render, profundidad navegable ni oleaje.

Convertir cadafloat binario finito a racional exacto, sin redondear/soldar ni
epsilon. Determinantes XZ, planos afines, intersecciones y áreas racionales.
Proyección con área0: DEGENERATE_PROJECTION porcara, sin dividir ni aceptar área
visible0. Triángulo water degenerado que podría cruzar elbed deja estado
INCONCLUSIVE_GEOMETRY, no se omite como transparente. No atan2 ni raíces.

Productor: lista de pares candidata por bounding boxes exactas (sweep/buckets
puede ordenar, no alterar extremos). Para cada bed, intersectar cada triángulo
water y recortar por semiplano W-B>=0. Estos recortes convexos se unen mediante
sustracción incremental de polígonos convexos: partir cada resto por los lados
del recorte, emitir las piezas exteriores disjuntas y continuar con interior.
Repetir aparte sin condición de altura para footprint. Áreas racionales y
extremos W-B porpareja de intersección; testigos IDs/modelo/cara/XYZ condicional
en evidencia privada. Orden determinista por (model_index,face_index).

Consumidor propio: recarga fuentes y recorre cada bed contra TODOS los4760 water
con AABB independiente; enumera las líneas de las caras candidatas y W-B=0,
subdivide elbed en celdas convexas. Clasifica punto interior racional de cada
celda contra el conjunto de water; calcula por separado las tres áreas. Las
fronteras tienen área0; una región W-B idénticamente0 se clasifica contacto.
Compara valores/estados/pares/IDs y cobertura completos. No importa funciones
geométricas del productor ni acepta su lista de candidatos como denominador.
I/O compartido sí; sustracción frente a arreglo de líneas son recorridos distintos.

No certificar exposición final: terreno/agua nativa/modelosVisual ordinarios/
vegetación/oclusores NO evaluados. Water de otros modelos fuera201pilotos tampoco.
La ausencia aquí se llama NO_SELECTED_WATER_FOOTPRINT, nunca «sin agua mundial».
Esto localiza una relación geométrica reproducible para Q03C2, no decide reparación.

## Oráculos y rechazos [DESIGN]

Congelar arrays y resultados racionales calculables a mano antes de código:
triánguloXZ(0,0),(12,0),(0,12) área72; water completo superior=72/0/0,
inferior=0/72/0, contacto=72/0/0, media cobertura=36/0/36; dos capas duplicadas
superiores conservan72; capa inferior y superior concurrentes no duplican.
Plano cruzado W-B corta triángulo en proporción literal derivada en contrato.
Agua sólo de OTRO piloto debe cubrir; dos mitades con costura exacta suman72;
cara repetida bed aparece dos veces con IDs distintos, nunca unión mundial.
Invariantes tras permutación de water, inversión winding, traslación exacta y
subdivisión de water sin mover superficie, firmados con resultados independientes.

Negativos: NaN/infinito, n4, flag no0, ID omitido/duplicado, digest/epoch distinto,
dobletransformación, candidato AABB omitido, water debajo contado como superior,
unión duplicada, igualdad clasificada debajo, racional malformado/bool comoint,
denominador0, bitcap/opcap/piececap, salida parcial marcada completa, fuente o
informe co-mutados. CLI productor→JSON→consumidor con positivos y negativos reales.
Helpers antiguos/suites viejas no se repiten.

## Presupuestos y terminales [DESIGN]

Codexexecutor local900s contrato/oráculos+delta geométrico acotado,3módulos como
máximo más test; code review externa180s, suite120s/256MiB; una corrección180s
por repro cerrado y una recuperación180s de dictamen ausente. No bucle interno.
Una producción120s/512MiB y un consumidor120s/512MiB. Salida32MiB; evidencia
geométrica completa privada, público sólo métricas/IDs/digests/resumen.

Caps porcara100000 operaciones racionales/4096bits poroperando,1024fragmentos
vivos/8192vértices vivos; reservar antes de operar o materializar. El contador
de AABB independiente cubre exactamente1520*4760=7235200pares como máximo por
caminante; no es presupuesto racional compartido. No subir caps si no termina.
Estos son límites de recursos del corte, no tolerancias geométricas. Contrato
debe fijar cota conservadora de resultados/intermedios ANTES de cada operación.

Cada cara emite terminal íntegro fsync con estado y tiempos. FULL sólo si1520
terminales definidos y comprobados por consumidor; si una cara agota recursos,
RESOURCE_INCONCLUSIVE y no aceptar esa cara. Timeout conserva sólo terminales
ya íntegros, sin prometer resumen final. Consumidor puede verificar prefijo
guardado completo sin promoverlo a FULL. SOURCE_CHANGED/I/O/BUG diferenciados.
Estados finales MEASURED_SELECTED_WATER_OVERLAY_ONLY o VERIFIED_PARTIAL_OVERLAY,
siempre terrain_evaluated=false, exposure_evaluated=false, native_acceptance=false,
map_repaired=false, human_resolved=0, C1NOT_REVIEWED.

Después: usar testigos para plan Q03C2 terreno/oclusores y Q05 huellas completas,
sin repetir este corte ni buscar permisos de producto ya dados. Carreteras,
ángulos certificados/Q08/Q17 siguen en backlog activo; nada de P:/build/DayZ.
