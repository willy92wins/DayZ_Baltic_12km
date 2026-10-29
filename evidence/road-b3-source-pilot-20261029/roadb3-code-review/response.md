**Dictamen: SOUND-with-fixes.** La fuente cumple el contrato sellado: conserva todos los bytes previos al terminador, añade exactamente tres registros con IDs max+1..max+3, preserva el terminador opaco con NaN y falla cerrado ante alteración, truncamiento, bytes extra, ID duplicado y desbordamiento uint32. Los hallazgos siguientes son correcciones concretas, ninguna introduce tolerancias nuevas.

**Hallazgos (archivo:línea, fix)**

1. **Bit-exactitud de la matriz depende de una conversión no pineada.** `author_road_object_pilot_ev112.py:123` y `verify_road_object_pilot_ev112.py:119` convierten double→f32 con la misma expresión. El consumidor sólo confirma que su propio redondeo coincide con el del autor, no que los 48 bytes sean los de la receta. Fix: exigir ida y vuelta exacta (`struct.unpack("<f", struct.pack("<f", v))[0] == float(v)`, rechazando en caso contrario) o añadir `matrix12_hex` de 48 bytes al contrato y comparar bytes literales. Con las matrices identidad/90/90 y traslaciones 100/200/300 el redondeo es nulo, pero el invariante debe ser verificable, no asumido.

2. **Signed zero se pierde si el contrato escribe `-0` entero.** JSON `-0` parsea como int 0 y `float(0)` da +0.0 en ambos módulos de forma silenciosa. Fix en `_validate_contract` de ambos módulos (líneas 120 y 116): rechazar `int` en `matrix12`, admitir sólo `float`. El test `test_signed_zero_preserved_bit_exact:86` pasa sólo porque la fixture usa `-0.0` flotante.

3. **Separador slash admitido en nombre raw.** `author…:43-47` y `verify…:43-47` normalizan `/`→`\` sólo para comprobar componentes, pero escriben el byte `/` tal cual. El contrato fija backslash simple. Fix: `if b"/" in raw: raise ValueError`. Opcional, sin ser tolerancia: pin del prefijo `dz\structures\roads\` observado en los 28 registros existentes.

4. **Código muerto y comprobación redundante en el autor.** `author…:235-239`: el `any(... and False for i in [])` es inalcanzable y la segunda comparación de conteo duplica la línea 233. Fix: borrar 235-236, sustituir 237-239 por la comprobación de `max_id` y por `set(info["ids"]).issubset(census["ids"])` como hace el consumidor en la línea 262.

5. **Copias de 286 MB evitables.** `author…:257` y `:273`, `verify…:219`: `data[:prefix]` crea copias completas; el autor en CLI llega a cuatro imágenes residentes (fuente, slice, candidato, relectura) más el set de 2,58 M IDs. Cabe en 2 GiB con el archivo real, pero con el tope de 512 MiB podría no caber. Fix: `hashlib.sha256(memoryview(data)[:prefix])` y construir el candidato con `b"".join((memoryview(data)[:prefix], records, terminator))`. El plan hablaba de igualdad por streaming; la implementación es en memoria. Aceptable con esta corrección, pero conviene declararlo.

6. **Resolución de rutas con fallback a cwd.** `author…:311-321` y `verify…:302-312` prueban primero junto al contrato y luego el directorio actual. Dos archivos homónimos con distinto contenido se distinguen por pin, pero la ambigüedad es innecesaria. Fix: resolver sólo relativo al directorio del contrato.

7. **Cota de materiales laxa.** `_parse_prefix:157` admite `count` una unidad por encima de lo posible. El bucle posterior detecta el truncamiento, así que no hay lectura fuera de límites, pero la cota debe ser `count > (len(data)-offset)//4`.

**Tests: lo que cubren y lo que falta**

Los tests comprueban invariantes externos reales, no sólo autor→consumidor: prefijo literal, terminador literal y longitud total en `test_road_object_pilot_ev112.py:74-77`; mutaciones de prefijo, nombre, terminador, cola y truncamiento; IDs duplicados en contrato y en fuente; overflow saturado; NUL, padre, absoluto; magic, dimensiones, celda; colisión con ID del terminador; fuente vacía; claves JSON duplicadas; pins y hash del contrato en CLI. El terminador de prueba contiene NaN, NaN negativo y NaN señalizante, y se preserva opaco.

Faltan tests literales independientes:

- Decodificar con `struct` dentro del test los tres registros añadidos del candidato y compararlos contra `NAMES`, `MATRICES` empaquetadas y los IDs 21..23, sin pasar por `verify_bytes`. Hoy la estructura interna sólo la valida el propio consumidor.
- Registro con longitud de nombre 0 en mitad del flujo (falso terminador) y verificar el rechazo.
- Fuente con ID 4294967295 existente y contrato que pida max+1.
- Nombre con `/` tras el fix 3, y `-0` entero tras el fix 2.
- Consumidor con fuente alterada entre autoría y verificación, para cubrir "fuente que cambie entre hash y lectura" del plan.
- Material con varias cadenas antes del terminador 0, ya que la fixture sólo tiene una.

El test `test_modules_do_not_import_each_other:267` sólo demuestra no importación. Los dos módulos son copias casi idénticas, así que no hay diversidad de implementación: un error compartido en `_parse_prefix` pasaría por ambos. Esto no invalida el diseño porque el error sería de rechazo, no de aceptación, pero debe quedar registrado como límite.

**Límites de esta revisión**

- No he verificado que `_parse_prefix` aterrice en el offset 17307629 del archivo real; el modelo de materiales asumido (secuencia de cadenas con longitud hasta un 0) sólo está probado en la fixture mínima. Si diverge, el autor falla cerrado por "prefix is not all bytes before terminator" en `author…:260-261`, no produce candidato incorrecto. Es un fallo seguro pero deja la unidad sin resultado hasta corregir el lector.
- No se ha contrastado tiempo real: cuatro censos de 2,58 M registros en Python puro caben en los 120 s con margen razonable, pero sin medición.
- No se revisa interpretación de pivote, enlace nativo ni ODOL; la escritura de 12 f32 no escoge hipótesis, como exige el plan.
- Revisión sin ejecución, sobre el texto suministrado.

Con los fixes 1 a 4 aplicados y los tests literales añadidos, el estado puede pasar a candidato para una única ejecución real offline.