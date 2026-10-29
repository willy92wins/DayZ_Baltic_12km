## Dictamen: SOUND-with-fixes

Revisión estática de las postimágenes suministradas. Los repros siguientes son sintéticos y derivados del código; no se ha ejecutado la suite en esta sesión de sólo lectura.

### Bugs

**1. Media-alta — una excepción ZIP surgida durante la fase de cabeceras se clasifica como `INTERNAL_ERROR`**

- El helper fijado sólo traduce `OSError` a `INCONCLUSIVE_SOURCE_IO` en [HEADER](/HEADER:26), y su envoltorio público convierte cualquier otra excepción en `HeaderError("INTERNAL_ERROR")` conservándola como causa en [HEADER](/HEADER:180).
- El módulo invoca ese helper en [MODULE](/MODULE:242) y, ante `header.HeaderError`, simplemente lo relanza en [MODULE](/MODULE:268). Por tanto, su posterior traducción de `BadZipFile`/`EOFError`/`zlib.error` a `ZIP_TRUNCATED` en [MODULE](/MODULE:270) nunca se alcanza para errores producidos **dentro** de `inspect_header`.
- Repro: miembro `DEFLATED` con cabeceras local/central y tamaños coherentes, pero con los primeros bytes DEFLATE que alimentan el prefijo NPY corruptos o truncados, de modo que `ZipExtFile.read()` lance `zlib.error`/`EOFError` durante `_read_exact`.
- Esperado según el contrato: `ZIP_TRUNCATED`. Actual: `HeaderError(INTERNAL_ERROR)`, con la excepción ZIP relegada a `__cause__`.
- Corrección sin editar el helper: en el módulo, al capturar `header.HeaderError`, recorrer de forma segura la cadena `__cause__` y, si aparece `zipfile.BadZipFile`, `EOFError` o `zlib.error`, relanzar `ArchiveError("ZIP_TRUNCATED") from exc` preservando toda la cadena. Los demás `HeaderError` (p. ej. `NPY_VERSION`, `MEMBER_SCHEMA`) deben conservar su código.

**2. Media — el EOF de `ZipExtFile` no certifica por sí solo la terminación DEFLATE ni el consumo íntegro del rango comprimido declarado**

- En [MODULE](/MODULE:249) el módulo acepta la extensión cuando `reader.read(1) == b""`, `reader.position == expanded` y coinciden CRC implícito de `ZipExtFile`, tamaño y digest del payload ([MODULE](/MODULE:255)).
- Eso certifica que se han entregado los `file_size` bytes declarados y que su CRC (comprobado por `ZipExtFile` al llegar a ese EOF lógico) coincide. **No** certifica que el `zlib` subyacente haya visto el bloque final (`decompressor.eof`) ni que no queden bytes comprimidos sin consumir dentro del `compress_size` declarado: `ZipExtFile` puede declarar EOF al agotar el tamaño descomprimido aunque el stream DEFLATE no esté terminado.
- Repro: payload NPY válido cuyo CRC se coloca en central/local, codificado con bloques DEFLATE **no finales** que producen exactamente el payload, sin bloque final, rellenando hasta el `compress_size` declarado y manteniendo coherentes rangos, CRC y digest. El pregueard crudo pasa y `read(1)` devuelve `b""`, por lo que el miembro se acepta pese a no existir terminación DEFLATE.
- Acotación/guarda necesaria: o bien se limita la afirmación a «tamaño declarado + CRC + digest verificados», o bien, antes de aceptar, se descomprime el slice comprimido ya delimitado con `zlib.decompressobj()` exigiendo `eof is True`, `unused_data == b""`, `unconsumed_tail == b""` y consumo exactamente igual a `compress_size`, además de tamaño/CRC/digest. Sin esa guarda no debe afirmarse integridad completa del stream DEFLATE, aunque los fixtures actuales pasen.

### Verificado sin violación en el resto de puntos pedidos

- Preguard crudo anterior a `ZipFile`: búsqueda de EOCD acotada y con fin exacto, conteo real de entradas del directorio antes de construir el `ZipFile`, rechazo de duplicados/directorios/rutas y control de solapes/rangos en [MODULE](/MODULE:108) y [MODULE](/MODULE:235).
- Preasignación lógica (no RSS): `STORED_CAP` antes de leer el snapshot en [MODULE](/MODULE:72), `ARCHIVE_CAP` acumulado durante el pregueard en [MODULE](/MODULE:162), y `TOTAL_CAP` comprobado antes de incrementar la reserva acumulada en [MODULE](/MODULE:231). El módulo declara explícitamente que son reservas lógicas, no límites RSS, en [MODULE](/MODULE:1).
- Mismo buffer para hash, pregueard y `ZipFile`: `_snapshot` devuelve `data` y su SHA-256, y `_prepare` reutiliza exactamente ese `bytes` en [MODULE](/MODULE:56) y [MODULE](/MODULE:227).
- Identidad path/handle y reparse: secuencia `lstat` de ruta y ancestros con detección symlink/reparse, `open` con `O_NOFOLLOW` donde existe, `fstat` antes/después y `lstat` final con identidad `(dev, ino, size, mtime_ns)` en [MODULE](/MODULE:48) y [MODULE](/MODULE:62), conforme a la secuencia aceptada en R4 (sin vigilancia continua).
- Doble fase real: primero se inspeccionan **todas** las cabeceras ([MODULE](/MODULE:242)) y sólo después se leen arrays ([MODULE](/MODULE:247)); el digest del payload tras la cabecera se contrasta con `memoryview(array).cast('B')`, rechazando discrepancias de padding en [MODULE](/MODULE:257).
- ZIP64 local exacto admitido (extra `0x0001` de 16 bytes y valores coherentes) y ZIP64 central/global rechazado como fuera del subconjunto, con extra central obligatoriamente vacía, en [MODULE](/MODULE:150) y [MODULE](/MODULE:185). No se exige ZIP universal ni semántica proxy.
- Liberaciones: al salir del contexto se vacían los arrays, se marca `closed` y se ponen a cero las reservas vivas sin devolver la reserva acumulada, en [MODULE](/MODULE:275).

Con las dos correcciones anteriores — reclasificación por cadena causal en el módulo y guarda/acotación de terminación DEFLATE — el diseño queda SOUND dentro del subconjunto de fixtures declarado.
