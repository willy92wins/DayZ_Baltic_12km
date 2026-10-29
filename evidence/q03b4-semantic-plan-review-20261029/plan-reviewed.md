# Q03B4 — índice de escena guardada para medir exposición y huellas

Estado: BORRADOR_PARA_REVISION. Consumidores posteriores: Q03C (exposición de lechos y caps) y Q05 (contactos carretera/agua, huella y ambos accesos). Este corte entrega un índice que permite seleccionar las caras y poses guardadas sin volver a extraer modelos. No mide todavía exposición ni modifica el mapa.

## 1. Alcance y fuente única

Se conserva el contrato histórico e9672092ce285f5e59802bc3f4faa2341d67a11965551702e7adabcf3173ee65 de `q03b-contract-inputs-20261029/contract-r1.json`: diez JSON, 204 NPZ, 201 pilotos, época 3d9550bf/WRP0da, todos sus pins, cotas y expectativas. Los destinos Q03B anteriores están consumidos; nuevos destinos exclusivos Q03B4. No reabrir PBO/P3D/WRP, P:, archivos originales de GIS ni repetir extractores. La revisión del presente plan no autoriza por sí sola abrir esos NPZ.

Codex actúa como planner/orchestrator/integrator. Se propone asignación explícita de EXECUTOR local para el código de esta unidad, tras congelar contrato y oráculos; se conserva la decisión técnica de entrega local de Q03B1L/B2/B3. Autor e integrador compartirán contexto. Revisión externa por Muse Wonder nativo; una recuperación de noentrega por Fable nativo, nunca dos dictámenes ficticios ni nuevo council. La familia/identidad servida se registra al recibir una entrega.

## 2. Anclas verificadas y diferencia de interfaz que hay que resolver

[EXACT] `tools/quality/saved_scene_archive_q03b2.py:260-341` ofrece `Session(**limits).open(path, schemas)`. Su esquema es un diccionario exacto de nombres `*.npy` y de dtype/shape por miembro. `saved_scene_npy_header_q03b1l.py:104-172` exige shape concreta, no predicados ni rangos. Ambos módulos se mantienen byte a byte: archive79ef0195 y header051436d9. El contrato e967, en cambio, permite tipos enteros de 4/8 bytes en poses y dimensiones variables acotadas en source_grid. NO inventar que Session acepta esos esquemas variables.

[EXACT] `saved_scene_archive_q03b2.py:56-83` obtiene un snapshot y su SHA con path/handle estable; `:108-199` valida directorio ZIP antes de ZipFile, sólo examina claves del diccionario schemas; `:202-241` comprueba el flujo físico. Son primitivas privadas leídas y fijadas por hash, no una API pública estable. El nuevo adaptador puede llamar las dos primeras con el módulo sellado; no copiarlas, modificarlas, monkeypatch ni omitir la validación física de Session.

[EXACT] `deployed_surface_inventory_ev112.py:140-170` guarda caras y metadatos, `:173-198` expande sólo agua de proxies; `:222-227` liga poses a cuentas de catálogo. `pilot_visible_surface_ev112.py:44-53` exige una instancia por cada piloto; `:157-158` lee instances6c0. `:219-230` guarda seis grupos de caras, source_grid/triangles/extremos/categorías y el mapa bed_source_face. Matriz(n,12), pilotos ya mundiales. No transformar ni aplicar bounding_center otra vez.

[EXACT] Q03B3 valida un expected literal de fixtures, con caps64modelos/512caras. No sirve como validador completo de539009caras. No llamarlo por lotes con un expected generado del propio candidato ni importar su núcleo privado como supuesto consumidor independiente.

## 3. Adaptador acotado de esquema, sin rehacer lectores

[DESIGN] Un adaptador pequeño compartible de I/O, dos módulos semánticos nuevos (productor y consumidor) y una suite de integración. No recuperar ni reescribir los cuatro archivos rechazados Q03B. El adaptador sólo convierte cabeceras observadas en esquemas concretos después de comprobar los predicados externos; no decide identidad de modelos, caras, poses o cobertura.

Secuencia por archivo, ejecutada también por el consumidor sobre su propia lectura:

1. Obtener snapshot mediante `_snapshot` sellado con stored<=16MiB, verificar tamaño y SHA externos ANTES de parsear. Comprobar raíz/ruta exacta autorizada. No fallback.
2. `_central(data, {nombre: None}, limits)` con nombres externos exactos; comprobar expanded_bound del archivo, <=128MiB y reserva disponible de262434599 antes de ZipFile. Esta reserva temporal de inspección no acredita arrays leídos; se libera antes de la carga completa. No ampliar el acumulador de Session ni cobrar dos veces la misma carga de arrays.
3. Leer exclusivamente MAGIC, versión, longitud y cabecera. NPY1: longitud2 bytes; NPY2:4; cap16384 ANTES de leer diccionario. El estándar NumPy recibe una copia acotada de cabecera. No leer payload ni asignar arrays en esta fase. Rechazar dtype objeto/nested/subarray, Fortran, dimensiones fuera de contrato, miembros extras y producto*itemsize+cabecera distinto de longitud declarada. Registrar descriptor entero, no truncar cadenas.
4. Los predicados de shape/dtype del contrato son implementados por separado por cada caminante. Para grupos de piloto las cuentas F vienen del JSON fijado; para grid/triangles se aplican TODAS las cotas e invariantes e967, no una estimación de tamaño. Tras aceptación del predicado, `inspect_header` sellado verifica la cabecera con el esquema ya concreto. El adaptador devuelve sólo la descripción observada y SHA del snapshot.
5. Cerrar ZipFile y soltar el snapshot temporal. Ejecutar `Session.open` sobre la ruta con schemas concretos: mantiene sus pregates, reserva acumulada, comprobación DEFLATE/CRC/SHA y cabeceras antes de arrays. Exigir que `source_sha256` sea exactamente el pin y el SHA de la inspección previa ANTES de consumir semánticamente los arrays o emitir filas. Un cambio entre lecturas es SOURCE_CHANGED, nunca aceptación. Las dos lecturas y sus límites se declaran; no vigilancia continua ni un único handle entre fases.

No habrá un discovery separado ni una captura previa de cabeceras históricas. La comprobación de esta integración forma parte de los tests sintéticos del código, y su primera lectura histórica ocurre únicamente en el productor autorizado. No se modifica Session para exponer un resultado antes de tiempo.

## 4. Índice semántico y límites de las afirmaciones

[DESIGN] Se congela un contrato Q03B4 externo antes de código: referencia completa a e967 y a sus expectativas, pins de helpers y fuentes de las anclas, destinos nuevos, esquema terminal, lista cerrada de negativos y oráculos literales. No repinar archivos históricos. La revisión de código incluye ese contrato concreto; no añadir otra revisión del mismo plan por rutina.

El productor construye 5515 terminales:5509modelos fuente y6proxy-only; conserva72vegetación NOT_SAVED y5437 no vegetación. Conserva todos los modelos aunque una capa no tenga caras guardadas. Las afirmaciones de conjuntos exactos de META en e967 se comprueban: si una resulta falsa en la captura, detener y conservar el contraejemplo, no reemplazarla silenciosamente por subconjunto. Sin inferir ABSENT de NOT_SAVED.

Prototipos:539009 filas con META35 completo; identidad por model/source_model/lod/section/face/kind/proxy y multiplicidad original. Índices LOD/section por su campo; cara dentro de lod.faces. Guardar rangos [inicio,fin) del array original por modelo y capa; cobertura disjunta y exhaustiva. Los vértices/flags/planarity se conservan por digest de payload y referencias, sin geometría duplicada en JSON. Sólo 3/4 vértices y padding positivo cero fuera del contador; signedzero dentro de vértices usados se preserva. Flags admitidos1/2/4, conteos y estados del contrato, no recalcular tolerancias geométricas.

Proxies: recorrer todas las siete rutas por ordinal de lista y p['model'] literal normalizado; continuidad, raíz, hijo final, profundidad16 y ausencia de ciclos en cada ruta. Kinds0/1 tienen proxy=-1/source=model; kind2 enlaza ruta. No asumir IDs contiguos ni sufijo faltante; sin basename. Se valida también cada ruta sin caras. Matrices12 y centros3 sólo finitos. Campos engine de proxy perdidos UNKNOWN. Grafo completo fuera de las rutas guardadas NOT_EVALUATED.

LOD/material: conservar resolución y materiales crudos/canónicos como metadatos; comprobar kind0 contra resolución Roadway literal3000000028082176.0 y kinds1/2 contra Visual mínimo único y los dos materiales exactos de WATER_MATERIALS del escritor fijado. Eso es coherencia del clasificador histórico, no semántica de render. Face-section membership NOT_SAVED: sección existente y face<lod.faces no certifican pertenencia física; las cuentas de sección no se convierten en rangos inventados.

Poses:17818 IDs únicos y cuentas por índice iguales al catálogo no vegetación; bytes de ids/model_index/matrix iguales entre selected e instances con dtype/shape exactos, no igualdad entre ZIP distintos. Conservar métricas norm/determinant/nonorthogonality como observaciones guardadas, sin certificar el marco. Cada piloto liga modelo/nombre/ID a exactamente una fila de pose y a su archivo fijado. Prohibido atribuir poses por proximidad.

Pilotos:201 archivos completos, seis grupos, extremos/source_triangles/source_grid, categorías y mapas de caras. Mantener cada digest de payload, aridad, winding y orden. Validar source_ids contra LOD y sección guardados del piloto; membresía física sigue no guardada. bed_source_face es permutación completa0..B-1; extremos son min/max de índices de triángulo por fila/columna. Las categorías se contrastan por fila con cap_before/after y extremos, además de cuentas del JSON. npz_start es offset GLOBAL: no exigir que quepa en n local. No recomputar equivalencia MLOD/ODOL ni convertir checks históricos en verificaciones actuales.

Época: enlazar por claves exactas inputs/manifests/pilotos y los pins e967. Referente histórico3d955, no ef229 ni instalado hoy. Los hashes de binarios son declaraciones históricas ligadas, no nueva lectura de esos archivos.

Salida metadata<=32MiB: `report.json` con schema/contract_sha/status/claims/coverage/sources/models/pilots/proxy_routes/limitations; miembros referenciados por archivo, nombre, shape, descriptor y SHA de payload. Rangos por modelo/capa, filas de pose y enlaces completos a piloto. El consumidor de exposición podrá abrir por esas referencias guardadas después de su propio plan, no resolver nombres de nuevo ni multiplicar todas las caras por todas las instancias.

Éxito máximo `VERIFIED_SAVED_SCENE_INDEX_ONLY`. world_frame_certified/exposure_evaluated/native_acceptance/build_ready/map_repaired=false. kind_coherence=SAVED_CLASSIFIER_ONLY; renderer_semantics=NOT_EVALUATED. Humanos0resueltos, C1NOT_REVIEWED. La diferencia entre este índice y reparación queda explícita.

## 5. Recorrido independiente del consumidor

[DESIGN] El productor recorre filas de META en orden, abre/cierra rangos por cambio de clave, y agrupa poses por índice. El consumidor no importa productor ni su constructor de salida: relee JSON y NPZ fijados, recorre por modelo/LOD/ruta y contrasta los rangos declarados contra las filas originales, además de cobertura exacta de todas las filas. Recorre piloto por piloto y compara cada enlace/digest/cuenta contra su propia lectura. No reconstruir expected desde el informe del productor.

Puede compartir solamente primitives selladas de lectura, adaptador acotado de cabeceras y digest. Sus validadores de predicados del contrato y joins semánticos son independientes. Misma NumPy/zlib y posible punto ciego común se declaran, sin alegar diversidad de implementación de I/O. Contrastar todo el esquema final con tipos exactos, unknownkeys rechazadas y bool!=int; ningún campo o terminal queda silenciosamente fuera. El consumidor debe rechazar reportes co-mutados y no sólo SHAs alterados.

## 6. Puertas y presupuesto cerrado

Antes de autoría, contrato externo y pequeños oráculos completos literales: dos modelos fuente, hijo proxy distinto, caras duplicadas legítimas, IDs/poses concretos, un piloto con grid y triángulos de2x2 y categorías explícitas. Expectativas escritas sin funciones del productor, incluso rangos y joins. Reutilizar fixtures históricos sólo por hash; no repetir sus CLIs ni suites.

Verde requiere: CLI productor fixture -> archivo real -> CLI consumidor fixture, informe completo literal; consumidor lee la fuente aun si informe dice SHA correcto. Negativos cerrados: N01 fuente cambiada entre header/load; N02 dtype/shape permitido pero relación grid/triangles falsa; N03 signedzero/padding; N04 raíz/hijo proxy equivocado con índices coherentes; N05 LOD/section confundido con posición; N06 ID/pose piloto duplicado o cambiado; N07 pin de época de otro PBO; N08 cara/rango omitido, duplicado o solapado; N09 categoría permutada conservando cuentas; N10 source_id fuera de LOD; N11 descriptor META/miembro extra; N12 reporte co-mutado + SHA autodeclarado; N13 bool/int y campo desconocido; N14 reserva/cap antes de asignación; N15 contador de archivo/pin incompleto. Cada repro debe nombrar el predicado que falla; un rechazo anterior no prueba la guarda objetivo.

Presupuestos nuevos para esta unidad, sin ampliar los consumidos: plan review180s; una recuperación de entrega ausente180s. Contrato/oráculos y executor local900s con reloj host y entrega en carpeta exclusiva; code review240s; suite180s/256MiB sintética. Reserva única de corrección240s sólo por repro del conjunto cerrado, luego suite por delta. Una ausencia de revisión admite una recuperación240s sobre los mismos bytes; segunda ausencia retira la ruta y no aprueba código. Fallo fuera de presupuesto retira la unidad para reevaluación técnica; no pide permisos de producto ya dados.

Después de código revisado, suite verde y todos los pins verificados: productor UNA vez120s/512MiB, consumidor UNA vez120s/512MiB, salida32MiB. Límite temporal no promete terminar. Conserva16MiBstored/128MiBexpanded por NPZ/262434599 acumulado/35miembros/16384cabecera. Tipos/dimensiones del contrato antes de arrays. Una referencia temporal de poses seleccionadas es acotada y explicitada; no retener todos los NPZ piloto en listas. Reservas lógicas no son RSS. El driver mide proceso y descendientes propios y persiste recibos.

No lanzamiento real si faltan puertas. Sin retries internos, sin aceptar prefijo como índice completo. Fallo de archivo/identidad/ZIP/schema distinto de INTERNAL_ERROR; no traducir bug a fuente corrupta ni timeout a éxito. Marcador de salida exclusivo consumido aun en fallo, estado público separado del informe parcial. No existe autorización de build/DayZ ni de modificación del mapa en Q03B4.

Al terminar, Q03C/Q05 deben usar este índice para medir superficies reales; no abrir otra ronda genérica de lectores. Q02B ángulos, Q08/Q17 referentes independientes y las carreteras continúan pendientes con sus planes. Council ya ejecutado, no se repite. P9/P10/P11 y Nav8 histórico intactos.
