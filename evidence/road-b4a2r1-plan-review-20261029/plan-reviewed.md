# RoadB4A2R1 — completar muestras desde la captura guardada

Estado: BORRADOR_PENDIENTE_DE_REVISION. No repetir extractor, tablas ni PBOs de B4A2.

B4A2 alcanzó ocho extracciones: siete hashes iguales al R0 y asphalt_ext resuelto literalmente en surfaces. Los tres PBOs tienen doble hash e identidad de handle/ruta guardados. Se conservan ambos RVMAT con firma raP. El primer CfgConvert terminó rc0/0.344s y produjo texto, pero el consumidor esperaba stdout.bin/stderr.bin y campos *_sha256. El runner fijado realmente escribe stdout/stderr y *_sha. La ejecución padre falló en2.375s; informe INCONCLUSIVE intacto, segunda conversión no lanzada. Los mocks reprodujeron el esquema incorrecto: fallo de revisión, no de CfgConvert ni de materiales.

La corrección literal de nombres/campos ya tiene39testsPASS, incluida una fixture del recibo real independiente del mock. No se ha vuelto a ejecutar B4A2. El texto guardado del primer material muestra clases Stage1/Stage2 anidadas y referencias nohq/sm adicionales; no se interpreta como cierre transitivo.

## Unidad nueva [DESIGN]

Contrato externo nuevo fija por hash: contrato dc707, informe/manifest parcial, ejecución padre, ocho assets, primer texto guardado, running/completion/stdout/stderr reales, código fallido259610 y corregido, runner33dad3 y CfgConvert4c4fc15, aprobación original. Fijar JSON y bytes antes de parsear/usar. Snapshot privado exclusivo, copia byte a byte de recursos, no geometría pública. Las fuentes originales no se modifican.

Consumidor previo independiente y declarativo: exige ocho virtual paths únicos, siete exactamente iguales a selected del contrato inicial y el octavo al external declarado; tamaños/hash de cada archivo, proveedor surfaces único en reporte y doble hash/identidades de los tres PBOs guardadas. Verifica el contrato original por hash y enlaces del partial. No reabre PBOs, no vuelve a extraer ODOL. Esto acredita la captura guardada, no estado presente del juego ni equivalencia semántica.

Para conversión1: verifica hashes literales de los cuatro recibos, PID/birth de running presentes en completion, rc0/reason null, hashes stdout/stderr con sus claves reales, input_sha de running igual al RVMAT1, executable igual al CfgConvert fijado. Preserva el texto existente no vacío y acotado, sin atribuir a su contenido una semántica aún no parseada. No relanza esa conversión ni reescribe sus recibos. El padre fallido y el hijo rc0 son hechos separados.

Para RVMAT2: copia original verificada, requiere firma exacta 00raP; como máximo UN CfgConvert nuevo de30s/256MiB con mismo argv anclado. Runner propio con PID/birth, output nuevo, rc0/reason null, recibos y streams reales, bytes input/tool inmutables. Presupuesto unidad90s/512MiB, sin reintentos. Preserva también fracaso parcial; no promoción si falla. Sólo ese recurso pendiente se convierte.

Salida MATERIAL_SAMPLES_RECOVERED_ONLY cuando ambos textos y procedencia están completos; build_ready=false, dependency_closure=NOT_EVALUATED. No fabricar un INITIAL_DISCOVERY_ONLY retroactivo para B4A2 ni reparar su reporte. Describir dimensiones verificadas y límites temporales por archivo. No stage/build/WRP/DayZ ni despliegue.

## Verificación y parada

Plan review90s; implementación120s; código review90s y suite120s antes de una recuperación. Pruebas contra recibo real y fixtures literales: filename/key equivocados rechazados, PID/birth distinto, input_sha/executable equivocados, rc/reason incorrectos, omisión/duplicación de recurso, pin roto antes de parsear, byte alterado, output ya existente, segunda conversión no repetida, padre fallido no promovido. Consumidor independiente no importa extractor B4A2. La gramática y cierre transitivo requieren plan posterior basado en estas muestras. El corpus Q17A ya revisado sigue independiente; no detenerlo por esta recuperación.
