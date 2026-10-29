# RoadB4B — preparar el piloto compilado sin alterar P:

Estado: BORRADOR_PENDIENTE_DE_REVISION. No autoriza build, paquete o DayZ.
Trazabilidad Q04/P10/P11. El piloto fuente RoadB3 conserva el mapa y añade tres piezas elevadas; no son pavimento colocado en las carreteras del mapa.

## Anclas verificadas

- tools/quality/author_road_object_pilot_ev112.py:163–165 exige firma 0WZD. La fuente46063f37 NO es OPRW compilado listo para empaquetar; no saltar conversión por confundir ambas representaciones.
- tools/terrain/compile_visual_pilot_ev112.ps1:9–25 usa AddonBuilder y raíz de proyecto, enlaces DZ/bin/core de P: más los dos addons propios. Es historia, no entrypoint aprobado reutilizable.
- tools/terrain/package_visual_forest_ev112.py conserva un comparador de objetos OPRW histórico; su excepción de altura forestal no se hereda a este piloto.
- evidence/road-b4a3-material-dependencies-20261029 cierra únicamente doce recursos de tres modelos instalados. No fija precedencia global ni resuelve los5509modelos del WRP. Versiones build e instalado distintas quedaron documentadas, no igualadas semánticamente.
- Receta B2/B3: identidad y rotación90 de dos rectas, curva90; cuatro hipótesis de pivote/origen/fila/columna. Hay caras locales guardadas porhash, no ancho útil medido.

## Decisión técnica pendiente y unidad inicial propuesta

Antes de una pareja control/candidato, escribir un manifiesto de resolución explícita por referencia WRP y por raíz de build. Los dos brazos usarán exactamente el mismo conjunto de recursos; únicamente cambian los tres objetos añadidos por RoadB3. Una raíz P: histórica no demuestra identidad actual con instalada. Usar inventarios y recibos ya guardados como índices, no repetir catálogos A/B0/B1.

Primera unidad propuesta sólo de lectura: resolver las rutas exactas del conjunto de modelos de escena desde inventario guardado, identificar proveedor y reglas de precedencia concretas del stage privado propuesto. Separar modelos propios, vanilla instalado, rutas build históricas y externos no resueltos; registrar por referencia una identidad verificable y fuente. No crear enlaces ni copiar árboles todavía. Múltiple proveedor o precedencia no demostrada => UNRESOLVED, no elegir por basename o por proximidad. No tratar timestamps como hashes ni doce recursos como cierre global. Acotar conteos, bytes y tiempos tras leer dimensiones del inventario; no aprobar un presupuesto inventado sin esa lectura.

Alternativas a resolver en revisión: (a) raíz privada completa ligada a recursos actuales instalados; (b) raíz de build existente fijada byte a byte para ambos brazos y diferencias frente a instalación explícitas, impidiendo usar sus resultados como oráculo de pivote nativo hasta cerrar correspondencia. No modificar P: ni fuentes compartidas. Evitar binarizar con una mezcla incidental.

## Pareja posterior y gates que deberá concretar otro contrato

Preflight fresco; control compilado antes del candidato. Conservar objetos anteriores, terreno/materiales y transforms, comparando representación decodificada completa donde compiler transforme bytes. No importar excepciones históricas de altura ni tolerancias por comodidad. Leer OPRW guardado con dos consumidores verificados antes de empaquetar. Paquete/runtime y oclusores se planifican después, sin declarar que SourcePASS demuestra motor.

La sonda posterior debe diferenciar las cuatro hipótesis por testigos de caras completas (Visual y Roadway), con acceso desde ambas direcciones y espacio libre demostrado. Bounding center no es ancho útil; ninguna pose se elige por una captura del personaje. Pilotos de carretera49, cruce49/301, Narva71 y kit118/cadena76 siguen pendientes hasta resolver transformaciones.

## Límites

Este borrador no ejecuta descubrimiento ni build y no cambia aceptación de carreteras. Pavimentado, anchura transitable, apoyo, puentes, accesos y conducción continúan abiertos. No desplaza Q02B2/Q03/Q05. Primero revisión del diseño y presupuesto propio; luego autoría, revisión y una ejecución acotada.

## Unidad B4B0 concreta para revisión: correspondencia fuente–índice guardado [DESIGN]

Lectura de diseño del29-10: collision-scene-b2a-r1-20261028/models.json tiene6318366bytes; es LISTA de modelos con name,sha256,package,entry y geometría resumida. ReportB2A3602bytes fija5509modelos/2578398instancias y8PBOs históricos. model-catalog.json fija nombre poríndice ycuenta. B4A3summary añade raíces3modelos del piloto, no significa queB2A ya incluyera esos nombres. Leer estos índices guardados no repite su censo ni abre PBO.

Hipótesis verificable: el conjunto y multiplicidad de referencias en la fuente0WZD antes de añadir piezas corresponde al catálogo histórico de B2A. Debe comprobarse, no inferirse de contar igual. Es una relación de nombres/cuentas, NO identidad geométrica fuente–compilado. Sin ella no usar catálogo como resolución completa de la fuente.

Entradas fijadas externamente antes de código: fuente0WZDb108 de286261435bytes y candidatoRoadB3sha46063f37 de286261718bytes; contrato7454f8b7/report deB3 guardados; catálogoae1a5ff7; report/models/configB2A con sus hashes calculados desde recibos guardados; B4A3contract178c/summary/model-jsonl84c3aafb y entries465aa. Nuevos pins son observación actual de archivos guardados, nunca identidad retroactiva sin recibo. Reutilizar sólo definición leída de formato: author_road_object_pilot_ev112._parse_prefix:159 y _parse_census:199, verify_road_object_pilot_ev112._CursorReader:159 y census:208. No llamar CLI/census históricos ni modificar esos módulos sellados. Los lectores antiguos descartan nombres; nuevo extractor debe contarlos y validarlos.

Única lectura secuencial nueva de la fuente con lectorstreaming, memoria sin guardar2578398objetos: estructura0WZD, skips de alturas/materiales acotados, IDs positivos, terminador exacto alEOF porcontrato, nombresASCII/path canónico sin traversal, hasharchivo antes/después con stat/handle. Contador por nombre y lista de todas formasraw por alias. No usar basename. No recomputar candidato: comprobar tamaño/hash/prefixpin y tresregistrosfinales segúnB3; validar delta de nombre/multiplicidad esperado. Si preservar IDsúnicos requiere set, cabe en1GiB pero acotar3M; no sustituirlo por total/max. Check previo de longitud512MiB/nombre4096bytes/referencias10000; caps antes dealloc/read. No afirmar vigilar cambios revertidos entre snapshots.

Consumidor independiente sobre reporte guardado con catálogo/receta/modelos sellados: igualdad de conjunto/cuenta exacta y suma2578398; delta3exacto; referencias5509 esperadas deB2A sólo sijoinreal lo demuestra. Cada referencia a proveedor único histórico por prefix+entry+SHA. Duplicado de name normalizado con bytesrawdiferentes, hash conflictivo, proveedor no fijado, ausente o rutas externas => estado explícito UNRESOLVED. Distinguir alias por slash/case documentado, nunca fusionar dos contenidos por parecido. No afirmar precedencia actual ni cierreTODOSLOD a partir de GeometryB2A. Cobertura de materiales texturas y proveedores nativos quedaNOT_EVALUATED. build_readyfalse en todo resultado.

Salida SAVED_SCENE_REFERENCE_INDEX_ONLY si la relación completa está demostrada; INCONCLUSIVE_REFERENCE_MISMATCH si difiere. Debe incluir tabla de modelo/instancias/fuente/paquete/pin/entry, estados agregados y nombres faltantes; no caras ni texturas vanilla. Raíz de stage privado sólo queda propuesta como tabla determinista de recursos, no se copia. Duplicado o recurso nuevo no cambia reglas ni orden para lograrMATCH.

Pruebas: fixturehex literal de0WZD con nombres separados yduplicados; permutar IDs conserva conteos pero no pasar duplicaciónID; truncarheader/material/nombre/terminador; nombrepathtraversal; duplicado proveedor con diferenteSHA; co-mutación de contadores preservando total; deltaobjeto omitido y cambio nombreoriginal. Consumidor negativo contra referente literal, no solamente productor y su propiooutput.

Presupuesto propuesto antes de ronda1: implementación240s,review180s,suite120s, extracciónúnica120s/1GiB, consumidor60s/256MiB; máximo16MiB deJSON deíndices+16MiB dereporte; WRP source/candidato512MiB cadauno conhashstreaming. No reintentos internos, no build/PBO/DayZ. Si discrepancia, registrar yplanseparado; noadjudicarcausa ni modificarfuente. Tras esto: plan deprecedencia/recursosmateriales faltantes ypareja compilada con referencia0WZD demostrada, no asumir queíndice==buildlisto.
