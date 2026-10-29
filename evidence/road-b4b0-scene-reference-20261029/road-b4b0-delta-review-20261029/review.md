**Revisor:** Claude Fable 5.1, revisión DELTA read-only, sin ejecutar nada.

**Veredicto: SOUND-with-fixes.** Un único defecto verificable, no bloqueante: el consumidor no replica la comprobación de nombre normalizado exacto de las entradas de road que el productor sí impone. El resto de los cambios del delta son correctos según la lectura del código.

**Defecto verificable**

- **Consumidor acepta entradas con `name` y `normalized_name` distintos.** El productor exige igualdad en `tools/quality/road_scene_reference_index_ev112.py:329-330` y lanza "road entry normalized name mismatch". El consumidor en `tools/quality/verify_road_scene_reference_index_ev112.py:317` indexa por `normalized_name` con fallback a `name` y nunca compara ambos. Además el fallback admite `normalized_name` vacío, que el productor rechaza. No produce un falso SAVED, porque el consumidor sólo emite OK si el informe del productor también es OK y el productor ya ha fallado. Pero rompe la premisa de parser independiente equivalente: una misma fixture da FATAL en un lado y tabla construida en el otro, y en modo diagnóstico el consumidor puede emitir una tabla que el productor nunca habría generado. Arreglo: añadir en el consumidor la misma comparación entre `_canonical_name(normalized_name)` y `_canonical_name(name)` antes de indexar, eliminando el fallback. La prueba `test_road_entry_name_normalization_comutant` sólo ejecuta el productor, por eso no lo detecta.

**Verificado como correcto en el delta**

- **Schema B4A3 sources reales.** Ambas herramientas ignoran claves que no empiecen por `previous:assets/` y tratan `models` y `catalog` aparte. Los pins `previous:report.json` y `helper` de la fixture no generan assets; `test_saved_asset_siblings_do_not_make_assets` lo cubre.
- **Consumidor sin set de IDs.** El consumidor no acumula identificadores; sólo el productor detecta duplicados. Coherente con el claim `INHERITED_SEALED_B3_PRODUCER_RECHECKED` y el presupuesto de 256 MiB. Con `dup_id` el productor emite FATAL y el consumidor rechaza el informe vacío en `_check_stats`, así que no hay OK espurio.
- **Parser independiente.** El consumidor usa offsets absolutos con `_read_at` e `int.from_bytes`; el productor usa cursor relativo con `struct`. Las comprobaciones de límites son equivalentes: cabecera, heights, índices de material, cuenta de materiales acotada por bytes restantes, longitud de nombre contra `name_bytes` antes de leer, terminador exacto en EOF. El crecimiento del fichero tras el fstat lo captura el productor con `f.read(1)` y el consumidor con la identidad de handle que incluye tamaño.
- **Stats.** `_statd` guarda ctime; las comparaciones dentro de cada API lo incluyen; el cruce path/handle sólo compara dev, ino, size y mtime. `_semantic` elimina ctime antes de comparar informes. `test_stat_identity_units` lo verifica.
- **Doble hash.** `_load_bytes` relee desde el mismo handle y compara digest y total; `_hash_handle`/`_hash_all` se invocan antes y después del escaneo sobre el mismo descriptor.
- **Cap de alias antes de insertar.** Ambos comprueban `alias_bytes+len(raw_b)` contra `report_bytes` antes de añadir. Los alias de los objetos añadidos no pasan por el cap en ninguno de los dos; es consistente y acotado por tres objetos.
- **Conteos candidate.** Productor usa `counts+added_names.count`, consumidor usa el tally acumulado en `scan_candidate`. Equivalentes; `test_consumer_rescans_against_full_comutant_counts` exige que el rescaneo real, no el informe, decida.
- **Fixtures truncadas.** Con `prefix_bytes=0` y sha del vacío para `truncated_header`, `truncated_material` y `truncated_name`, el guard "prefix beyond EOF" ya no intercepta y los detalles esperados coinciden con los mensajes de `_Cur.read` y `_Cur.skip`. Las pins de source en contrato, B3 contract y B3 report se calculan tras la mutación, así que el productor llega al parser. `truncated_terminator` y `candidate_truncated_name` conservan el prefijo original y alcanzan el mensaje esperado.
- **Comutantes de proveedor.** `norm` no colapsa `..`, así que `dz/sub/../a.p3d` no resuelve a `dz/a.p3d` y emite `B2A_PROVIDER_ENTRY`. El conflicto de proveedor usa shas de modelo distintos y produce `PROVIDER_CONFLICT`.
- **Contrato externo.** Constantes b148 y literal 8329 sin cambios en las tres ficheros; `test_literal_original_bytes_exact` reconstruye los bytes desde el literal pinned.
- **Semántica de estados.** `VERIFIED_MISMATCH_DIAGNOSTIC` sólo cuando ambos informes son BAD y semánticamente iguales; `test_consumer_verified_mismatch_diagnostic` lo cubre.

**Observaciones no bloqueantes**

- `_semantic` compara sólo códigos de issue, no detalles. Las diferencias de detalle quedan casi siempre reflejadas en la tabla, así que no es un hueco práctico, pero conviene dejarlo documentado como decisión.
- Las variantes truncadas sólo se ejercitan contra el productor. Un subtest que lance el consumidor con `--report` apuntando a un informe inexistente sobre una fixture truncada verificaría que el parser independiente llega al mismo mensaje. Opcional, dentro del alcance actual.

**Próximo paso:** aplicar el fix de una línea en el consumidor y reejecutar la suite R2; con eso el dictamen pasa a SOUND.