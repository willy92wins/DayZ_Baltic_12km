## Dictamen: **SOUND-with-fixes / CONVERGE**

Revisión estática independiente. No ejecuté suite, productor, consumidor ni la fuente real; no afirmo ningún resultado de ejecución.

### Correcto en el diseño implementado

- No se amplía el lector de archivo completo ni se relanza Q03C2: la fuente original sólo recibe snapshot acotado y recorrido de metadata; `Session.open` se aplica únicamente a la vista de un miembro. La suma expandida permanece como entero observado, sin certificar auxiliares.
- El productor copia literalmente registro local completo y payload comprimido de `heights.npy`, copia el registro central cambiando sólo el offset local a 0 y construye un EOCD nuevo de un miembro, sin recomprimir: [height_view_producer_q03c2a.py](/E:/DayZ-Baltic-Build/shape-repair-20261025/q03c2a-local-author-20261029/height_view_producer_q03c2a.py:42).
- Productor y consumidor tienen recorridos ZIP propios y semánticamente distintos —offsets `struct` frente a offsets manuales— y ambos rechazan centinelas centrales ZIP64, discos, extra/comentario central, EOCD sin cierre exacto en EOF, huecos/solapamientos locales, descriptores de datos y ZIP64 local distinto del subconjunto exacto de 20 bytes.
- El consumidor no acepta la palabra del productor: reabre la fuente pinada, repite el preguard, compara byte a byte el NPY descomprimido en chunks de 64 KiB, exige igualdad literal de registro local y de bytes comprimidos, y reconstruye el reporte esperado completo antes de emitir `VERIFIED`: [height_view_consumer_q03c2a.py](/E:/DayZ-Baltic-Build/shape-repair-20261025/q03c2a-local-author-20261029/height_view_consumer_q03c2a.py:43).
- Los claims quedan correctamente cerrados en falso y la salida del productor queda como `UNVERIFIED` hasta la verificación del consumidor. El dtype/shape queda limitado al conjunto cerrado del contrato antes de pasar el descriptor observado a `Session`.
- La dependencia común en el I/O sellado, NumPy y zlib está declarada. Es un residuo de modo común aceptado por el plan; la igualdad literal de bytes comprimidos y del registro local lo mitiga para la procedencia de `heights`.

### Fixes obligatorios antes de la ejecución real

1. **El artefacto final del consumidor no marca fixture.** El reporte del productor sí lleva `fixture: bool`, pero `consumer.json` usa el mismo `VERIFIED_SINGLE_HEIGHT_MEMBER_VIEW_ONLY` y omite ese campo. Si ese JSON circula como recibo autónomo, una corrida fixture puede leerse como resultado real. Añadir `fixture` al resultado final del consumidor —o un status distinto en modo fixture— y afirmarlo en la suite.

2. **La suite tiene un falso-pase de identidad de contrato.** Calcula el SHA del contrato desde el propio archivo presente y no lo compara con el SHA congelado `33de008a…`; tampoco usa los campos congelados del oráculo `negative_codes`, `output_member_names`, `eocd_count` ni `view_central_local_offset`: [test_height_view_q03c2a.py](/E:/DayZ-Baltic-Build/shape-repair-20261025/q03c2a-local-author-20261029/test_height_view_q03c2a.py:7). Debe fijar literalmente el SHA esperado y consumir esos campos, no redefinirlos desde el objeto bajo prueba.

3. **Varios negativos aceptan “cualquier rechazo”.** El helper `reject` no exige código en buena parte de los casos ZIP, de stream y de esquema. Eso permite pasar por una causa equivocada. Deben afirmarse los códigos deterministas del oráculo donde el contrato los fija. En particular, el camino de header puede emitir `SCHEMA` desde [saved_scene_io_q03b6.py](/E:/DayZ-Baltic-Build/shape-repair-20261025/q03b6-local-author-20261029/saved_scene_io_q03b6.py:59) mientras el oráculo de esquema espera `MEMBER_SCHEMA`; hay que traducir ese borde de forma acotada en productor y consumidor, preservando `ZIP_TRUNCATED` para truncamiento/CRC/stream.

### Condiciones que siguen siendo del coordinador

El código no impone por sí mismo tiempo, RSS ni destinos contractuales: `--out` y `--capture` no se ligan a `output`/`consumer_output` del contrato. Antes de la única ejecución real deben mantenerse el marcador exclusivo consumido incluso en fallo, la verificación externa de pins de productor/consumidor/tests/helpers, los topes externos de 60 s/60 s y 256 MiB, y los destinos exactos del contrato.

Con esos tres fixes acotados, el integrador puede adjudicar la postimagen en el mismo contexto sin otra lane externa: **CONVERGE**. Sin ellos, no debe lanzarse la ejecución real.
