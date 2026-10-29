**Veredicto: NEEDS-WORK** (defectos acotados; sin false PASS observado en la ruta real, pero con falso rechazo del consumidor y violaciones de contrato en punteros y tipos).

Metadatos del revisor: Claude Fable 5.1, model id `claude-fable-5-1`, revisión solo lectura, sin herramientas ni rerun.

## Bugs

**1. Chequeo de `expected` asimétrico entre productor y consumidor → falso rechazo y causa no registrada.**
`tools/quality/road_content_identity_ev112.py:364-373` compara seis literales más `historical_conflicts` e `historical_conflict_instances`. `tools/quality/verify_road_content_identity_ev112.py:238-243` sólo compara `references` e `historical_conflicts`. Mecanismo: si en datos reales `single` ≠ 5508 o `delta` ≠ 3, el productor fuerza `INCONCLUSIVE_SAVED_CONTENT_IDENTITY` pero el consumidor recalcula `INCONCLUSIVE_METHOD_BINDING` y aborta con `status mismatch` rc 1. Negativo concreto: contrato con `expected.single_pinned_content_references: 5507` sobre fixture correcto → productor rc 2, consumidor rc 1 "status mismatch" (diagnóstico erróneo, no "expected mismatch"). Además el productor no emite ningún issue explicando el forzado; el contrato exige "Recompute counts from table; compare to literals" en ambos.

**2. Puntero `/table/N` apunta al índice ordenado, no al índice en el origen pinado.**
`road_content_identity_ev112.py:213,299` y `verify_road_content_identity_ev112.py:83,141`: `ridx`/`orig_idx` enumeran la tabla ya ordenada por nombre. Contrato: "pointers resolve in pinned exact source bytes". Negativo: B4B0 con tabla en orden no alfabético y una fila con `HISTORY_PROVIDER_MISMATCH` → `issues[].pointer` resuelve a otra fila. Ambos lados comparten el error, así que la reconstrucción no lo detecta (independencia nominal, no real).

**3. Coerción bool aceptada en el consumidor.**
`verify_road_content_identity_ev112.py:207,230`: igualdad Python `True == 1`. Negativo: reporte con `counts.by_state.MALFORMED: false` o `groups[0].provenance_indices: [false, true]` pasa la verificación. Contrato: "no bool/int coercions". Falta `is_int_exact` sobre `counts.*`, `by_state/by_method` y `provenance_indices`. Igual en `verify…:100` (`mime != 0` acepta `false`) y `verify…:40,94` sin `is_sha256`; el productor valida (`road_content_identity_ev112.py:148`), el consumidor no.

**4. Oráculos de agrupación se prueban contra un helper muerto.**
`tests/test_road_content_identity_ev112.py:46-55` ejercita `classify_provider_dicts` (`road_content_identity_ev112.py:12-44`), que la ruta de producción nunca llama. El código real de agrupación (`:263-319`) no está cubierto por `oracles-r2.json`. Faltan oráculos `historical_rows`, `method_cases`, `joins` MALFORMED, `á/b`, cadena >4096 y `jsonl` CR. El pin de `oracles` se carga pero no se evalúa.

**5. Negativos requeridos ausentes.**
De 24 `required_negatives` sólo hay dos (`changed_instance_count`, sha mayúsculas). Faltan al menos `forged_pointer`, `omit_provenance`, `duplicate_reference`, `receipt_pin_mismatch`, `blocked_groups_counted`, `alter_history_provider`, `remove_reconstructed_candidate_while_history_stays_null`, `mime_nonzero_rejected_provider`, `jsonl_blank_index_shift`, `silent_locator_normalization`.

**6. Código muerto / expresiones frágiles.**
`road_content_identity_ev112.py:255-261` bucle sin efecto; `:336` expresión `... and False` siempre 0; `:294` y `verify…:136` dependen de precedencia del condicional ternario (funciona por accidente, `:296` es redundante). `resolve_pointer` (`io:219`) no se usa en ninguna parte, por lo que ningún puntero del reporte se resuelve explícitamente.

**7. Validación débil de `b4a3_summary.pbo` en productor.**
`road_content_identity_ev112.py:248-249`: `pbo['path']`, `pbo['sha256']` sin `is_sha256`/`str`. Negativo: `pbo.sha256` no hex → el productor escribe un reporte con grupo inválido que el consumidor rechaza después; debería fallar cerrado antes de escribir.

## Observaciones sin bug

- Historia nula: `raw_map` por `canon` garantiza ≥2 tuplas RAW canónicas distintas (`:281,291`); el par B2A (`E:\…\structures_roads.pbo`, entry `bridges/…`) + road (`E:/…`, entry `Bridges/Bridge_Metal_25.p3d`) produce 2 raws y 1 grupo → `SAME_PINNED_CONTENT`, coherente con 4 multi/28 instancias.
- Las 3 filas nuevas exigen `NEW_REFERENCE_WITH_B4A3_PIN`, proveedor road y pin `previous:assets/` (`:242,301-305`). Si el proveedor histórico de B4B0 para esas filas usa otro formato de locator distinto de `b4a3_summary.pbo.path`, serán MALFORMED. No verificable desde las muestras; no es defecto del código.
- Método global: el peor estado se toma de provenances realmente usadas (`:374-377`), con B2A `METHOD_UNVERIFIED` → `INCONCLUSIVE_METHOD_BINDING`, igual al preregistro. No se emite `INDEPENDENT_PIN_MATCH`.
- Normalización cumple los oráculos listados; `'part.p3d '` conserva espacio; `:` y no-ASCII rechazados tras `lower()`.
- Pins/recibos: `contract_sha256` de report y consumer, `source_report_sha256`/`consumer_sha256`, pins b4a3 y adjudicación verificados en ambos lados (`:57-86`, `verify:22-31`). El consumidor no compara `consumer.json` con `report.json` fila a fila; el contrato no lo exige.
- CLI: rc 0/1/2 correctos; `write_exclusive` sólo tras éxito; sha de contrato en mayúsculas rechazado.
- Límites: total ≈16 MB < 32 MB; doble lectura dentro de presupuesto.
- Los fixtures sintéticos de `build_case` sólo prueban el esqueleto; no prueban el mapa ni los 5512 nombres reales.

## Fixes mínimos para pasar a SOUND

1. Mover la comparación completa de `expected` a una función en el módulo io compartido, usarla en ambos lados y emitir un issue `EXPECTED_COUNT_MISMATCH` por literal fallido.
2. Guardar el índice original de B4B0 antes de ordenar y usarlo en `/table/N`.
3. Añadir `is_int_exact` a `counts`, `by_state`, `by_method`, `provenance_indices` y `mime`; `is_sha256` a `pbo.sha256` y `pkgs` en el consumidor.
4. Ejecutar `oracles-r2.json` contra la ruta de producción (fixtures por caso) y añadir los negativos requeridos.
5. Eliminar `classify_provider_dicts`, `:255-261`, `:336`, y reescribir `:294-297` sin ternario.