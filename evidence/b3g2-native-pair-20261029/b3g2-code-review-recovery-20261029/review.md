**Entrega acotada B3G2 (post-imágenes lector/observador/consumidor). Hallazgos 1-7 ya adjudicados no se repiten.**

**Veredicto:** APTO para ejecutar la suite final y pasar a preparación, con dos correcciones pequeñas recomendadas antes del run real. Ninguna invalida el diseño ni toca modelo, puntos, golden ni misión.

**Bugs nuevos concretos**

1. **Carrera nativa en cabecera (observador `native_health`, líneas 26-29).** Un snapshot del `baltic_contact_b3g.log` recién creado pero aún vacío, o con la primera línea a medio escribir, falla duro con `native_header` en vez de devolver PENDING. Con un solo poll por unidad y sin reintentos, ese fallo pierde la unidad entera. Corrección mínima: si `len(raw)==0` o `raw` no termina en salto de línea y aún no hay `END;270`, devolver `None` (PENDING_SAMPLES) antes de evaluar cabecera y FAIL. El consumidor sigue exigiendo cabecera y 270 sobre los bytes capturados.

2. **Enmascaramiento en fallo repetido (observador líneas 46-48).** `save` abre con `xb`. Si un segundo poll vuelve a fallar health, `FileExistsError` sustituye la excepción real y el motivo original no aparece en el error del poll. Sigue siendo fail-closed y el consumidor bloquea por `script_failure_present`, pero el diagnóstico del operador se pierde. Corrección: no reescribir si ya existe, relanzar la excepción original.

3. **Nativo viejo aborta en vez de PENDING (observador línea 25).** Un `baltic_contact_b3g.log` residual en el mismo perfil con `last_write` anterior al proceso hace fallar `stale_native` en el primer poll. Correcto sólo si preflight o preparador garantizan perfil limpio. Si no está garantizado, tratar ese caso como PENDING hasta que el productor lo reescriba, manteniendo la verificación de FileID por `native_rotated`.

4. **Asimetría latente en detección del bloque (lector líneas 90 y 93).** La primera línea se compara cruda contra `expected[0]`, mientras el grupo se compara tras sustituir la ruta de misión por `$MISSION`. Hoy el mensaje no contiene ruta, así que no hay efecto. Si el golden cambiara y el mensaje incluyera ruta, el bloque nunca se reconocería y pasaría a `unknown_script_error`. Fail-closed, pero conviene aplicar la misma sustitución antes de comparar.

5. **Campo semántico fijo (observador línea 52).** `mission_error_before_capture=False` es constante aunque `script-before-diagnostic.json` contenga el DumpStack conocido. No miente sobre bloqueo, pero el nombre sugiere ausencia de SCRIPT(E). Recomiendo derivarlo de `known_diagnostics` o renombrarlo a `blocking_script_error_before_capture`.

**Cobertura verificada en las post-imágenes**

- Tiempos: FILETIME crudo en 100 ns, comparación entera en `snapshot_times`, `stamp` sólo representación con floor; `filetime_binding` recalculado en consumidor.
- Identidad: FileID de cuatro componentes obtenido del mismo handle, antes y después de leer; FileID igual más prefijo exacto en el log de script; par estable con misma longitud y hash para END270.
- Clasificador: un único bloque, timestamp igual, contigüidad estricta, frames exactos con ruta de misión explícita, SCRIPT(E) fuera del bloque bloquea, SCRIPT(W) listados, compilación fallida bloquea.
- Consumidor: rehace health sobre bytes exactos y exige igualdad con los diagnósticos guardados, continuidad before/at-capture, orden de ventanas y snapshots, vínculo log-capture, NTFS antes y después, `script-failure` ausente, lista completa de entradas en `inputs`.

**Pendiente del lado del usuario:** ejecutar la suite final tras los fixes de timestamps y añadir un test de nativo vacío y de cabecera parcial para el bug 1.

FIN_REVISION