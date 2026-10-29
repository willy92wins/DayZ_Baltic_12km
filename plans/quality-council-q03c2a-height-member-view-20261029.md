# Q03C2A — vista de heights sin ampliar el lector de archivo completo

Estado: REVISADO_PARA_VISTA_DE_MIEMBRO_ACOTADA. Codex planner/integrator, executor local
explícito después de revisión. Una lane externa Muse CLI nativo. No nuevo council.
Muse Wonder1.0 nativo46.829s SOUND-with-fixes/CONVERGE adjudicado, siete
precisiones al final. No código, contrato o proyección todavía.

## Motivo y alcance [EXACT]

La inspección única Q03C2 paró en0.437s/46043136B con ARCHIVE_CAP en
saved_scene_archive_q03b2.py:163, antes de ZipFile/header NPY/arrays. No se
relanza el script ni se aumenta128MiB. No hubo contrato/código geométrico ni
medición Q03C2. Lectura del código163 demuestra que el rechazo es la suma de
declaraciones expandidas, no RSS, timeout, geometría inválida ni corrupción.
No se guardó esa suma; NO inventarla a partir de la excepción.

container-diagnostic.json guardado en river-kit7-merged-20261026 tiene
source_sha815ef8,source_bytes12875883,saved_bytes142613546 y lista histórica de
miembros NPY idénticos entre contenedor comprimido y STORED. saved_bytes incluye
overheadZIP, no se presenta como suma exacta. preserve_kit7_merge_bytes.py:10-23
verificó y preservó el NPZ original comprimido. Ese CLI está consumido.
Los demás miembros son capas auxiliares; esta medición necesita sólo heights.

Propuesta técnica: crear una NUEVA vista NPZ de un único miembro `heights.npy`,
conservar sus bytes locales/comprimidos exactos y ligarla al SHA del contenedor
original. No cambiarlo ni aceptar el archivo completo con el lector128MiB.
El rechazo original sigue vigente. La vista sólo certifica ese miembro; los
otros payloads no se decodifican, no adquieren integridad/semántica nueva.

## Contrato externo antes de autoría [DESIGN]

Fijar plan/review, original815ef8 completo, tamaño12875883, diagnósticohistórico
y merge-verification, script de inspección/receipt/stderr de Q03C2; helpers
archive79ef/header0514/IOd073 y sus firmas exactas. Congelar la lista literal
de nombres desde el JSON histórico pinado (no desde la nueva captura). Esperar
exactamente uno heights.npy. No basename ni fallback a otro terreno.

Un lector estructural acotado verifica directorio y layout ZIP del snapshot
original, ANTES de ZipFile. Límite almacenado16MiB/nombres35/header16384 y
registros de directorio en el mismo snapshot. La suma de expanded se OBSERVA
como enteros de metadata, no reserva ni permiso de descomprimir todos ellos.
Este es un alcance distinto al Session de archivo completo, no ampliar su cap.
No aceptar ZIP64 EOCD, multidisco, duplicados, cifrado, métodos fuera0/8, rutas,
gaps/overlaps/concatenaciones o extensiones no comprobadas. ZIP64local de tamaños
permitido según el subconjunto ya leído en archive:170-195. Nombres/orden exactos
respecto al listado histórico. Guardar todas filas/contabilidad de metadata.

El miembro heights seleccionado debe declarar <=33570828bytes expandidos
(32MiB f8 + header16384 + prefijo12) y comprimidos<=16MiB. No usar ese límite para otros
miembros. Su NPY declara f4/f8,2048x2048,Corder; no objeto/pickle. El header de
un f8 requiere overhead10/12 además deldictionary: el tope de miembro lo incluye.
La finitud/valores de heights no se interpretan en esta unidad.

## Construcción y consumo distintos [DESIGN]

Productor nuevo: snapshot estable pinado y parser estructural propio. Copiar
EL registro local completo del miembro (header/nombre/extraZIP64local/payload
comprimido) a offset0. Copiar su registro central exacto salvo campo de offset
local sustituido por0; construir EOCD de un miembro con offset/tamaño nuevos,
sin comentario. Comprimir/recrear datos NO es necesario. No modificar hashes
ni bytes internos del NPY para que pase. Si vista>16MiB, rechazo sin ampliación.

Sobre la vista nueva, el Session sellado original valida los límites16/128/262MiB,
headers y streamfísicoDEFLATE64KiB/CRC/SHA/eof, sin modificarlo. La reserva de
archivo completo ahora sólo tiene un miembro por la nueva identidad explícita.
Guardar el descriptor observado y hash del payload NPY, no publicar alturas.

Consumidor en proceso distinto: releer snapshot original porSHA; parser de
directorio con recorrido por posiciones independiente o stdlibZipFile sólo
DESPUÉS del preguard estructural. No aceptar campos del productor como prueba
de lectura. Leer heights original con máximo declarado+1, chunks64KiB, CRC de
ZipFile y longitud completa, y comparar cada byte NPY contra vista; computar
SHA/longitud propios. Comprobar el stream físico del miembro mediante helper
sellado sobre vista y que comprimidos/localrecord son literalmente iguales a
los del original. No importar la función de proyección del productor. Biblioteca
zlib común declarada; bytecomparación/recorrido independiente, no codec distinto.

Orden: fijar esquema de header de heights descubierto dentro de la ejecución,
antes de Session.open que materializa el array. Ese array es un coste de
verificación del contenedor, NO permiso para medir terreno/geometría/finitud.
Contar sus32MiB máximos, snapshot16MiB y buffers, cap256MiB. El futuro Q03C2
debe pinar la vista/recibo verificadas y cerrar su contrato propio; no continuar
automáticamente la captura geométrica ni convertir esta vista en terrain-ready.

## Oráculos, puertas y presupuestos [DESIGN]

Antes de código: fixtures ZIP sintéticos con dos miembros, heights literalNPY1/2
[-0,1] y matriz2x2, y auxiliar de declaración expandida>128MiB que NO se abre.
Sólo fixture pequeño conocido, no fabricar128MiB. Proyección esperada por bytes
del miembro, no por el autor. Negativos duplicado/offset/gap/extraZIP64/cifrado/
path/CRC/streamtruncado/bytestrasEOF/headeroversize/tamañoseleccionado/ordennombres,
fuente mutada, comprimidos co-mutados, y vista que pasa Session pero no proviene
del original. Marcador exclusivo de ejecución y no reintentos.

Codexexecutor600s contrato/oráculos/código compacto (productor/consumidor/test),
review180s incluye contrato, suite120s256MiB. Una corrección180 por repro cerrado
y una recuperación180 por noentrega. Una proyección60s256MiB y consumidor60s256MiB,
output16MiB más resumen1MiB; no ampliación de Session ni de los presupuestos.
Resultado VERIFIED_SINGLE_HEIGHT_MEMBER_VIEW_ONLY; whole_source_archive_validated
=false, terrain_geometry_evaluated=false, map_repaired=false. Reportar la suma
de metadata observada sin adjudicar retroactivamente payloads no leídos.

Esta vista es un derivado nuevo mínimo para la dimensión terreno; Q03C2 sigue
pendiente de contrato/autoría/revisión/suite. No cambia P9/P10/P11, agua/Narva,
colocaciones ni mapa. Q03C1medido y Q03C2rechazo quedan intactos. No copiar/cargar
todas las capas auxiliares ni ampliar límites para conseguir un falsoPASS.

## Precisiones adjudicadas [DESIGN]

1. Contrato previo fija conjunto cerrado dtype{<f4,<f8}, shape[2048,2048],
   Corder. El header observado sólo puede elegir dentro de ese conjunto ya
   declarado; después se pasa su descriptor exacto a Session. No adoptar un
   esquema arbitrario del candidato. La primera frase del hallazgo se aclara
   así, conforme a su alternativa de conjunto cerrado, sin necesitar una
   identidad de dtype histórico que todavía no se observó.
2. Preguard de TODAS las filas rechaza centinelas centralesZIP64, discos,
   extra/comentarios centrales, EOCDcomment y EOCDsin cierreEOF; layoutlocal
   contiguo0..central y flags sin data-descriptor. El listado histórico tiene
   28miembros; fijar nombres y orden externos. Suma es declaración observada,
   no validación de payloads auxiliares. La nueva vista no cambia ese alcance.
3. Registro central de vista idéntico salvo offsetlocal0; EOCDconteo1 y offsets
   recalculados. No recomprimir ni mutar registro local/payloadcomprimido.
4. Hashear/parsear mismo snapshot. Sessionread de vista debe devolver el mismo
   SHA externo antes/después; consumer reabre ambos y comparaNPY chunks64KiB,
   no recibe arrays del productor. No garantía de vigilancia continua.
5. Reservas previas snapshot16MiB+vista16MiB+array32MiB, buffers64KiB; RSS256MiB
   es cap del runner, no garantía de asignaciones internasNumPy/zlib.
6. Recibo con filas/declared_expanded_sum_observed, offsetsheights, SHAcomprimido,
   CRC/longitudexpandida, SHANPY, headerobservado y SHA/tamañovista.
7. Negativos adicionales: NPYigual recomprimido falla PROCEDENCIA aunque CRC y
   valores sean iguales; centinelaZIP64 de auxiliar fallaestructura sin leerse.

Integrador adjudica postimagen con contexto compartido, no otra revisiónexterna.
La revisión de código incluye contrato/oráculos antes de ejecutar una sola vista.
