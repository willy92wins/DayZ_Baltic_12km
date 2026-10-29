**Veredicto: SOUND-with-fixes.** Los siete defectos de la revisión anterior están corregidos y coherentes en ambos lados. No encuentro ruta de PASS falso. Quedan asimetrías productor/consumidor que producen rc 1 en lugar de fila MALFORMED, una pérdida de trazabilidad en candidatos descartados y cobertura de oráculos truncada. Nada verificado todavía contra los 5512 nombres reales.

Revisor: Claude Fable 5.1, model id `claude-fable-5-1`, lectura sin herramientas.

## Delta sobre los bugs previos

- **Expected (bug 1):** ahora ambos lados comparan las ocho claves con `is_int_exact` y fallan cerrados con `EXPECTED_COUNT_MISMATCH` (`road_content_identity_ev112.py:80-88`, `verify_road_content_identity_ev112.py:404-412`). Simétrico. Consecuencia: un desajuste en datos reales no deja reporte, sólo stderr. Aceptable como fail-closed; distinto de lo que pedí (issue en reporte), pero no es un defecto.
- **Punteros (bug 2):** `orig_index` capturado antes de ordenar en ambos (`:201-207`, `verify:180-192`), y el test con tabla invertida resuelve el puntero contra la fuente real (`tests…:287-296`). Correcto.
- **Tipos (bug 3):** consumidor exige `is_int_exact` en `counts`, `by_state`, `by_method`, `observed_keys`, `provenance_indices`, `inputs[].bytes`; `mime` guardado por `is_int_exact` antes de `!= 0`; `is_sha256` en paquetes, grupos, provenances, historial. Kelvin rechazado antes de `lower()` (`io:66-69`). Correcto.
- **Oráculos y negativos (bugs 4-5):** `classify_provider_dicts` eliminado; `oracles-r2.json` se ejecuta contra `build_report`/`verify` con sha pinado. Ver pendientes.
- **Código muerto (bug 6):** bucle sin efecto, `and False` y ternarios frágiles eliminados; `resolve_pointer` se usa para provenances e issues de B4B0 (`verify:366-369,379-385`).
- **pbo (bug 7):** validado con `is_sha256` en `_validate_bindings` antes de construir.

## Comprobaciones específicas

**Independencia de reconstrucción.** El consumidor no lee nada del reporte para reconstruir: `reconstruct` (`verify:89-291`) parte sólo de fuentes pinadas y luego compara `canon(table)` completo (`:393`). Toda falsificación de fila, grupo, puntero o estado cae ahí; los chequeos de tipo previos sólo refinan el diagnóstico. La independencia es por copia del algoritmo, no por diversidad; un error conceptual compartido no se detectaría. Es lo que el contrato pide, no más.

**Binding contra muestras.** Trece bindings de recibos/pines probados por omisión en ambos lados (`tests…:275-285`). Camino de `road_catalog_code` cotejado con clave exacta en `approval.pins`. `road_inputs` normaliza barras al cotejar el pbo (`:62-67`); es un pin, no un join de contenido, aceptable.

**Counters RAW.** `raw_counts` usa `canon` de la tupla cruda con locator sin normalizar (`:249`); el par B2A backslash + road forward-slash da 2 raws y 1 grupo. Las filas MALFORMED con un raw siguen contando como single; filas sin candidatos no cuentan en ninguno, y el literal `references` lo atraparía. Coherente ambos lados.

**Prioridad de historia.** `not hist_ok or malformed` → MALFORMED precede a BLOCKED, UNRESOLVED y resto (`:291-304`, `verify:268-279`). Historia nula con conflicto SHA real da BLOCKED_SHA_CONFLICT (test `:91-101`). Correcto.

**Límites.** Caps de referencias, provenances, grupos, archivo individual y total antes de abrir; test verifica que sólo se abre el contrato (`tests…:347-357`). Suma pinada ≈16 MB. El tamaño del reporte real con 5512 filas no está estimado; cap de 16 MB lo cortaría con rc 1.

## Fixes requeridos

1. **Asimetría en campos históricos preservados.** El productor marca MALFORMED si `provider` tiene claves distintas o SHA inválido (`:277`), pero el consumidor rechaza el reporte entero con `historical_provider typed mismatch` (`verify:333-336`). Igual con `historical_state` no string (`verify:331`) y `aliases` con elementos no string (`verify:329`), que el productor no valida. Un B4B0 real con esa forma da productor rc 2 y consumidor rc 1 sin diagnóstico de fila. Validar esos tipos en el productor y fallar cerrado antes de escribir, o relajar el consumidor a "JSON preservado" y dejar que la reconstrucción decida.

2. **Candidatos descartados sin rastro.** Filas de `road_models` o `b2a_models` con nombre no normalizable se saltan con `continue` (`:154-157,169-172`; `verify:152-155,162-165`) sin `rejected_provenance`. El contrato exige registrar motivo cuando se excluye un candidato relevante. Debe registrarse al menos cuando el nombre crudo, tras sólo reemplazo de barras y minúsculas, coincide con una referencia de la tabla.

3. **Oráculos truncados.** `oracle['grouping'][:4]` (`tests…:242`) deja sin ejecutar los oráculos restantes de agrupación. Quitar el corte.

4. **Test muerto.** `test_original_index_pointer` (`tests…:111-117`) sólo comprueba que el fixture inválido falla; borrarlo, ya está cubierto por `:287-296`.

5. **Recibos con valor cambiado.** `test_every_required_receipt_binding_missing_or_changed` sólo borra claves; no prueba un SHA válido pero distinto. Añadir una mutación por binding.

## Riesgos no verificables desde código

- Historia nula exige ≥2 raws canónicos distintos. Si en datos reales el locator de B2A coincide byte a byte con `b4a3_summary.pbo.path` y prefix/entry crudos coinciden, los cuatro puentes caen a MALFORMED con `distinct_raw == 1`. Depende de que B2A tenga más de un paquete por nombre o distinto formato de locator.
- Las tres filas nuevas exigen que el `provider` histórico de B4B0 sea exactamente `{pbo.path, pbo.sha256, pbo.prefix, entry crudo del catálogo, sha}`. Cualquier diferencia de barras o mayúsculas en B4B0 las hace MALFORMED.
- Un `road_entries` con un nombre no ASCII aborta todo el run (`:143`), no sólo la fila.

Con los fixes 1 y 2 aplicados y el 3 reejecutado, pasaría a SOUND a nivel de código. El dictamen sobre datos reales sigue pendiente hasta ejecutar sobre el contrato R2 pinado.
