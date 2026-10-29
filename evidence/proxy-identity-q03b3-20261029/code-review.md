## Veredicto: **SOUND**

Revisión estática completa contra el oráculo congelado. No ejecuté la suite por la restricción de sólo lectura.

### Identidad y rutas

- El hijo se resuelve exclusivamente por la cadena `model` del proxy, normalizada y buscada en `by_name`. No se usa ningún índice de modelo como sustituto: [saved_scene_proxy_identity_q03b3.py](</E:/DayZ-Baltic-Build/shape-repair-20261025/q03b3-local-author-20261029/saved_scene_proxy_identity_q03b3.py:145>).
- `slot` es ordinal dentro de `proxies` del padre actual. Se rechaza fuera de rango con `ROUTE_SLOT`: [saved_scene_proxy_identity_q03b3.py](</E:/DayZ-Baltic-Build/shape-repair-20261025/q03b3-local-author-20261029/saved_scene_proxy_identity_q03b3.py:143>).
- Continuidad, raíz y destino final se comprueban en cada salto. El padre debe ser el modelo corriente y el último hijo debe coincidir con `source_model`: [saved_scene_proxy_identity_q03b3.py](</E:/DayZ-Baltic-Build/shape-repair-20261025/q03b3-local-author-20261029/saved_scene_proxy_identity_q03b3.py:137>).
- Los ciclos se detectan tanto al repetir un padre como al volver a un modelo ya visitado como hijo: [saved_scene_proxy_identity_q03b3.py](</E:/DayZ-Baltic-Build/shape-repair-20261025/q03b3-local-author-20261029/saved_scene_proxy_identity_q03b3.py:141>).
- LOD y sección se buscan por sus índices reales dentro del modelo fuente, no por posición en arrays. Por eso `lod=0` y `section=0` fallan cuando los índices reales son `7` y `9`: [saved_scene_proxy_identity_q03b3.py](</E:/DayZ-Baltic-Build/shape-repair-20261025/q03b3-local-author-20261029/saved_scene_proxy_identity_q03b3.py:162>).

### Validación estricta y multiplicidad

- Todos los registros anidados exigen conjuntos exactos de claves: modelo, LOD, sección, proxy, ruta, cara y `expected`: [saved_scene_proxy_identity_q03b3.py](</E:/DayZ-Baltic-Build/shape-repair-20261025/q03b3-local-author-20261029/saved_scene_proxy_identity_q03b3.py:27>).
- `bool` queda rechazado como entero o número porque se exige el tipo exacto. Esto cubre slots, índices, centros, matrices, resolución y filas esperadas: [saved_scene_proxy_identity_q03b3.py](</E:/DayZ-Baltic-Build/shape-repair-20261025/q03b3-local-author-20261029/saved_scene_proxy_identity_q03b3.py:31>).
- Las caras esperadas se comparan como multiconjunto completo con `Counter`. Una omisión compensada con un duplicado no pasa: [saved_scene_proxy_identity_q03b3.py](</E:/DayZ-Baltic-Build/shape-repair-20261025/q03b3-local-author-20261029/saved_scene_proxy_identity_q03b3.py:170>).
- Las rutas conservan ordinal y orden mediante igualdad de listas. Reordenarlas altera el enlace ordinal de las caras y produce `FACE_BINDING`: [saved_scene_proxy_identity_q03b3.py](</E:/DayZ-Baltic-Build/shape-repair-20261025/q03b3-local-author-20261029/saved_scene_proxy_identity_q03b3.py:159>).
- Las salidas se copian en profundidad. Mutar rutas o caras devueltas no aliasa la entrada: [test_saved_scene_proxy_identity_q03b3.py](</E:/DayZ-Baltic-Build/shape-repair-20261025/q03b3-local-author-20261029/test_saved_scene_proxy_identity_q03b3.py:61>).

### Negativos trazados

Los casos del oráculo quedan cubiertos con el código esperado: hijo literal incorrecto, raíz incorrecta, discontinuidad, slot exterior o booleano, hijo desconocido, fuente final incorrecta, ciclo, slots vacíos, ruta mala no referenciada, enlaces de cara incorrectos, LOD/sección/cara fuera de dominio, colisión canónica, traversal, falta de sufijo, claves desconocidas, omisión compensada, booleanos en `expected`, JSON duplicado o no finito, exceso de 1 MiB, SHA incorrecto y excepción de programación como `INTERNAL_ERROR`.

El cargador comprueba tamaño antes de parsear y antes de aceptar el SHA. Sólo es un cargador sintético de fixture, no un lector de escena histórica: [saved_scene_proxy_identity_q03b3.py](</E:/DayZ-Baltic-Build/shape-repair-20261025/q03b3-local-author-20261029/saved_scene_proxy_identity_q03b3.py:205>).

### Limitaciones correctamente no certificadas

- No se certifica pertenencia cara-sección: sólo existencia del ID de sección en el LOD fuente y `face < faces` total. Sigue `NOT_SAVED`.
- `kind` sólo discrimina la forma estructural del enlace. Su semántica permanece `NOT_EVALUATED`.
- Las matrices sólo se validan como 12 números finitos. No certifican marco mundial ni binding del motor.
- No se evalúa el grafo global de proxies fuera de las rutas suministradas.
- No se certifica escena actual, NPZ, exposición, mapa reparado ni consumidor completo.

El contrato R1 mantiene separados `schema` e `input_schema`, sin sobrescritura en el kernel: [contract-r1.json](</E:/DayZ-Baltic-Build/shape-repair-20261025/q03b3-proxy-inputs-20261029/contract-r1.json:31>).

**Sin bugs concretos accionables dentro de este corte.**
