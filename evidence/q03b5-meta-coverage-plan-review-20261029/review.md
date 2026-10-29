## Dictamen: **SOUND-with-fixes**

No es un rechazo real repetido ni infraestructura genérica: es un testigo acotado de las dos igualdades que Q03B4 rechazó sin guardar diferencias. Antes de autorizar el executor local de 300s deben cerrarse estos fixes, sin ampliar alcance.

### Anclas — correctas, pero insuficientes como explicación
- En [deployed_surface_inventory_ev112.py](/C:/Users/guill/OneDrive/Documentos/DayZ%20Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c/tools/quality/deployed_surface_inventory_ev112.py:140), `extract` solo emite Roadway del LOD roadway y agua del LOD visual; un modelo puede devolver `(0,4,3)` y META vacío.
- `inventory` conserva ese modelo en catálogo/`model-sections.json` y concatena solo las caras seleccionadas — mecanismo compatible con “está guardado, no está en META”.
- El plan acierta al marcarlo **[HIPÓTESIS]**, no causa: también quedan contrato erróneo, epoch/IDs, fuente parcial o joins. No abrir NPZ real en esta revisión; el ancla no cuantifica el rechazo.

### Fixes obligatorios
1. **Separar las dos igualdades y los dos universos.** Q03B4 falló en `model_set==nonveg and source_set==set(models)`. El testigo debe reportar cada igualdad por separado y en ambas direcciones, sin fundir “catálogo no-vegetación”, “secciones” y `set(models)` — este último puede incluir bindings añadidos tras el catálogo. Definir desde qué JSON fijado se reconstruye cada universo y el mapeo índice↔nombre sellado por hash.
2. **Estado por (ID, rol), no por ID.** Un mismo ID puede estar como `model` y faltar como `source_model`. Estados solo observacionales: `OBSERVED_SAVED`, `NO_META_ROWS_IN_ROLE`, `UNEXPECTED_META_ID`. Renombrar `NO_SELECTED_META_ROWS`: “sin filas META” es lo observado; “sin cara seleccionada” ya es interpretación causal. Causas siempre `NOT_ESTABLISHED`.
3. **Desglose directo vs proxy.** Incluir conjuntos por `kind`/LOD y por campo `proxy`, porque un root proxy-only puede aparecer vía filas `kind==2` sin filas directas. El oráculo proxy-only debe fijar ese resultado esperado literalmente, junto a fuente-presente/modelo-ausente y viceversa.
4. **Independencia real del consumidor.** Compartir helper I/O solo para bytes crudos y guardas de archivo/hashes; el consumidor parsea META por offsets del dtype de 35B con código propio, sin reutilizar array parseado, `np.unique` ni agrupación del productor. Declarar “misma NumPy/zlib” está bien si queda así delimitado. Reconciliar filas por kind/LOD contra el total 539009, como ya exige el plan.
5. **Presupuesto y salida fail-closed.** 300s executor + revisión 120s + suite 60s/256MiB y producción/consumidor 60s cada uno es creíble para META de 539009×35B, pero cargar también vértices 539009×4×3 f8 debe justificarse como coste forzado del helper reutilizado, medido dentro de los 256MiB — no como permiso de geometría. Si “todos los IDs testigo” no caben en 4MiB, rechazo por presupuesto, nunca truncar ni muestrear. Una corrección de 120s y una recuperación de 120s, sin retries, quedan intactas.

### Guardas y límites — preservados
Se mantiene Q03B4 `REJECTED:COVERAGE`, contrato e967 intacto, éxito máximo `VERIFIED_META_COVERAGE_DIAGNOSTIC`, prohibido degradar igualdad a subconjunto, ocultar un ID inesperado para “pasar”, o autorizar nueva captura/reparación. Pin/epoch, dtype, conteos co-mutados, sets omitidos, bool/int y unknown-keys deben rechazar.

Con los fixes 1–5 incorporados literalmente al contrato y a los oráculos previos al código: **SOUND-with-fixes**, listo para executor local 300s.
