# Q03B1 — recuperación funcional del lector de escena guardada

Estado: REVISADO_PARA_IMPLEMENTAR_LECTOR_SINTETICO. Muse Wonder1.0 nativo28.969s SOUND-with-fixes adjudicado; contrato de escena permanece intacto. Sustituye la reescritura masiva Q03B R0/R1 retirada; no autoriza captura real ni modifica contrato de escena.

## Resultado y motivo

Q03C/Q05 necesitan un índice verificable de las superficies históricas para medir lechos y huellas completas. El lector Q03B compartido impidió ejecutar positivos y ocultó negativos. Tres repros independientes fijados detectaron descriptor truncado, NPY2 válido rechazado y proxy incorrecto aceptado, pese al delta Fable SOUND-with-fixes. El índice no se produjo; ningún defecto humano está resuelto.

Se conserva contratoR1e9672092ce285f5e59802bc3f4faa2341d67a11965551702e7adabcf3173ee65/oráculosb4ba70a4c18ea4718175069f07c23eb1bd21274bf3141c5c9990274118a113d4. No se cambia el universo5509+6, los201pilotos, matrices(n,12), los43ambiguos, la época3d9550bf ni caps.

## Corte1 autorizado por este plan [DESIGN]

Sólo un módulo nuevo tools/quality/saved_scene_archive_q03b1.py y tests/test_saved_scene_archive_q03b1.py, primero en carpeta exclusiva privada de autoría. No importar semántica del productor/consumerQ03B retirados ni reemplazarlos aún. API propuesta: read_snapshot(path,cap), inspect_npz(bytes,member_schemas,limits), load_verified_npz(...) y descriptor_json(dtype). API por cerrar contra definiciones reales antes de escribir; no copiar firma ficticia. Este lector será dependencia concreta del productor/consumer de los siguientes cortes; su salida son arrays/digests verificados con fixture independiente, no otro registro de aprobación.

Usar lectura NPY estándar de NumPy después de preleer header length y validar todos los miembros/cotas; no reimplementar interpretación de payload ni confundir dtype.descr con dtype.fields. NPY1.0 y2.0, littleendian exacto, signedzero y padding conservados; NPY3/Fortran/object/títulos/subarrays fuera del subconjunto exacto rechazados. structured META especificado de35bytes completo; reportar dtype como lista completa de campos. Verificar docs/source locales fijados runtime NumPy2.5.3; max_header_size16384 explícito. No NPZ mmap.

ZIP antes de asignar: nombres exactos.npy, duplicados/directorios/path/compression/encryption; sumas positivas y productos de shape por enteros acotados antes de operar; cabecera<=16384 y largo payload exacto, sin trailing. Límites originales:16MiB almacenado,128MiB archivo expandido,262434599total,35miembros,dimensión<=2M/3dimensiones. Presupuesto global se entrega al lector y se reserva ANTES de leer; nunca después de asignar. Sin pickle, flujos externos ni fallback. Snapshot conserva path/handleantes/después y mismoSHA de bytes parseados; no retirar dev/ino/mtime ni atribuir diferencias a cloud. OSError -> INCONCLUSIVE_SOURCE_IO, cambio de identidad -> INCONCLUSIVE_SOURCE_CHANGED; bug interno separado, no convertir todo en SOURCE_IO.

## Oráculos y validación del corte1

Antes de código fijar un archivo pequeño externo literal que contenga las cabeceras NPY1/2 y bytes esperados de float64[-0,1], matrizliteral2x12 y META35. No generar expectativas mediante el lector. La serialización estándar NumPy puede generar contenedores de prueba, pero comparaciones van contra bytes/valores literales. Añadir a la suite los dos repros de lector y conservar el proxy como deuda obligatoria del corte semántico, no afirmar que este corte lo corrige.

Lista cerrada: positivos NPY1/2 y header16384 válido; negativos16385antesdeleer, version3, objeto/pickle, Fortran, endian, dtype incorrecto, campos/subarray/título desconocidos, shapes/producto/cota global antesdeallocation, ZIPduplicado/directorio/comprimido no admitido/truncado/trailing; rechazo reparse real si privilegio y negativo simulado siempre; cambio identidad; errorI/O distinguido; JSONroundtrip descriptor+signedzero. Cada negativo debe alcanzar código preciso, no cualquierException. Comprobar consumo de bytes/llamadas para guardas prealloc. Confirmar que inputs fixtures coherentes permiten llegar a cada guarda.

Verde: suite propia del corte1 con intérpreteGIS real y las expectativas externas, todos los negativos alcanzan su guarda, revisión entre familias adjudicada y sin fallo de los dos repros. Un verde aquí es READER_FIXTURE_VERIFIED_ONLY, no binding real ni prueba motor.

## Reparto y presupuesto

Codex orquesta/revisa/integra; executor nativo recibe sólo los dos archivos y cápsula acotada. Autor120s, revisión90s, suite60s/256MiB. Una corrección120s como reserva explícita sólo si hay repro ejecutable del conjunto cerrado; repetir suite sólo tras delta. Si no converge, retirar esa ruta y volver al orquestador con reproducciones. No repetir Q03B R0/R1 ni sus suites/reviews; no nueva auditoría de la misma postimagen. Fuente de parada gates-ledger sección Cuándo para un bucle. No pedir permiso humano de nuevo para esta recuperación técnica autorizada.

## Cortes posteriores separados

Corte2: productor semántico con esquema real de JSON y contratos/pins originales, proxy literal {'model':string,'matrix':12} y co-mutantes completos que llegan a guarda; validar relaciones antes del gran NPZ. Corte3: consumidor independiente con recorrido propio y CLIJSONroundtrip, nunca importar checks del productor. Estos cortes necesitan handoff/plan acotado propios antes de código; no se autorizan por este documento.

Sólo cuando los tres cortes estén integrados, revisión/casos del contrato completos, podrá autorizarse ejecución única productor120s512MiB y consumidor120s512MiB, salida32MiB; destinos nuevos exclusivos. ContratoR1 no es por sí solo permiso para usar un nuevo código. No PBO/WRP/P3D/P:/DayZ, no mapa, ni geometría vanilla pública en esta recuperación.

Q03C/Q05, Q02Bángulos y referentes naturales/agua Q08/Q17 siguen en plan; la recuperación no convierte preparación en reparación ni congela esos frentes indefinidamente. Humanos0resueltos/C1NOT_REVIEWED.

## Cierre de revisión,29-10 [EXACT/DESIGN]

[EXACT] Runtime NumPy2.5.3 `_format_impl.py:187-191,629-638`: versión(1,0)longitud<H2bytes; (2,0)<I4bytes. MAGIC6+versión2, prefijo10/12bytes; minor distinto de0 rechaza. El largo del campo cuenta header dictionary con padding/newline, excluye prefijo en ambas versiones. Se refuta que la contabilidad del max_header_size cambie entre1/2; cambia el ancho del prefijo. Guard16384 contra el campo antes de leer esa cantidad. El positivo del límite debe ser aceptado por el lector estándar; no inventar un archivo que incumpla otro aspecto del formato para demostrarlo. Gate de longitud16384/16385 probado además por I/O espía.

[DESIGN] Un único budget de sesión posee bytes almacenados y expandidos; read_snapshot reserva almacenamiento<=16MiB antes de leer y sólo devuelve snapshot verificado contabilizado. inspect_npz recibe ese snapshot, valida metadata y reserva total expandido ANTES de payload/array. Rechaza bytes sin token contable de su sesión. Liberación tras archivo; total consumido se conserva separado del residentlive. Límite128MiB es suma file_size de TODOS miembros de un NPZ, no por miembro;262434599bytes suma expandida de TODO el lote, no elementos. ZIP_STORED/ZIP_DEFLATED admitidos, otros/encryption rechazados. Contrato por miembro/schema restringe dtype y producto antes de np.load/standardreadarray; private helpers no se invocan.

Codex integrador prepara y fija los oráculos literales externos ANTES de entregar dosarchivos al executor. No se los encarga al autor; conservar SHA/autor/postimagen en recibo. dtype.descr se conserva íntegro como lista de pares(name,format), sin f[0]; para META se verifica también el mapa literal de offsets0,4,8,12,16,20,21,22,23,27 eitemsize35. Descriptores con títulos/subarrays fuera del contrato no se aceptan.

Códigos predeclarados para los negativos: HEADER_LIMIT, NPY_VERSION, NPY_MAGIC, NPY_DTYPE, NPY_SHAPE, NPY_ORDER, NPY_TRAILING, ZIP_DUPLICATE, ZIP_DIRECTORY, ZIP_PATH, ZIP_COMPRESSION, ZIP_ENCRYPTED, ZIP_TRUNCATED, STORED_CAP, ARCHIVE_CAP, TOTAL_CAP, MEMBER_SCHEMA, REPARSE, INCONCLUSIVE_SOURCE_IO, INCONCLUSIVE_SOURCE_CHANGED, INTERNAL_ERROR. Rechazos de contenido y recursos no son PASS; tabla de fixtures especificará cuál corresponde a cada mutación antes del código. Los dos repros de lector pasan únicamente cuando dejan de reproducir defectos; el tercer repro de proxy sigue deuda explícita. API nueva se diseña en esos dos archivos, pero toda llamada a NumPy/zipfile/OS debe reanclarse a definición real. No otro sondeo masivo ni fase documental adicional.
