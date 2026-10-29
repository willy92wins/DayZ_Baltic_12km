**Veredicto: NEEDS-WORK.** No encontré un falso PASS numérico, pero hay tres desvíos de contrato ejecutables en el consumidor, una duda no verificable en el productor y la suite no cubre los negativos obligatorios.

**Bugs ejecutables**

1. **Recurso del consumidor se convierte en REJECTED (falso FAIL).** `tools/quality/verify_shore_multiscale_coverage_ev112.py:221-222` convierte `Resource` en `Bad('chainresource_prepare')`; `:262-266` hace lo mismo con `Resource` y `Cap` durante la consulta; `:123-124` envuelve cualquier excepción de `idiv` (incluido agotamiento) en `Bad('t:...')`. El contrato (`output-contract:44,57`) exige NUMERIC_RESOURCE_INCONCLUSIVE preservando la captura cuando se agota el crédito propio. Además es inconsistente: `mk` sellado lanza `Cap`, que en `prepare` no es capturado en `:222` y cae en `:296` como inconcluso, mientras `CB.need` lanza `Resource` y rechaza. Fix: en 222 y 263-266 marcar `gu+=univ` (o flag de recurso de consumidor), registrar la cadena como no verificada y continuar/terminar con rc=2; en 123 capturar sólo `Bad` y dejar pasar `Resource`/`Cap`. El `except Resource` global de `:294` debe también volcar `completed_chains`/`covered_universe` ya acumulados en vez de dejarlos en cero.

2. **Cadena posterior al hueco aceptada en PARTIAL.** `:275-276` sólo rechaza si existe `terminal.json` tras el primer hueco. Un directorio `chain-0007/` con cache o shards tras hueco en 5 pasa el filtro de `:196` (todas las chain-dirs son esperadas) y no se revisa. Contrato `:24`: "no hay ninguna cadena posterior al primer hueco". Fix: en 275 comprobar `(cap/IO.chain_dir(cid)).exists()` y rechazar.

3. **bool-as-int en terminal/manifest/shards.** `:218` compara `term['chain_id']!=cid` y `term['universe']!=univ` con `!=` plano: `true` pasa para la cadena 1. Lo mismo en `:226/232` (`query_count`, `excluded_count` 0 ↔ `false`), `:250/252` (`sh['bytes']`, `sh['queries']`), `:289` (`excluded_count`, `unverified_numeric_count` 0 ↔ `false`). `bool_as_int` es negativo obligatorio del oráculo. Fix: sustituir esas comparaciones por `IO.strict_eq` o `IO.is_int(...) and ==`. Mismo defecto en `shore_coverage_io_ev112.py:105` (`s['chain_id']!=i` sin `is_int`), de bajo riesgo por selectores pinneados pero contractualmente obligatorio.

4. **Cota de shards duplica el +1.** `:241-242` computa `floor(...)+1` y luego tolera `>maxshards+1`, es decir `ceil+2` mientras el contrato (`:60`) fija `ceil+1`. El chequeo real de empaquetado en `:268-269` sí es correcto y consistente con el productor (`shore_multiscale_coverage_ev112.py:59`), así que no hay falso PASS, pero la cota declarada no es la aprobada. Fix: `maxshards=-(-univ*qb//(sb-qb))+1` y rechazar `len>maxshards`.

**No verificable con el material dado**

5. **Productor no reconoce `Cap`.** `shore_multiscale_coverage_ev112.py:30,53,78` sólo reconocen `('Resource','Res')`. El consumidor (`:265,296`) asume que el kernel sellado lanza `Cap`; el verificador certificado incluido también usa `Cap`. Si `shore_prefix_pilot_ev112.py` propaga `Cap` del kernel productor, un agotamiento real en `build_cache`/`query` abortará toda la captura con rc=1 en vez de producir terminal/registro de recurso. No tengo las definiciones del pilot; verificar el nombre de la excepción y añadir `'Cap'` a las tres tuplas si procede.

6. **Forma de encoding productor vs consumidor.** `:267` compara campo a campo el `result` del pilot con el encoding propio (`from_point`/`to_point`, soporte con `state`). Sólo `test_full_cli` lo cubre indirectamente; no puedo confirmarlo sin `shore_prefix_pilot`.

**Suite insuficiente respecto al contrato**

`tests/test_shore_multiscale_coverage_ev112.py` cubre CLI completa, partial, manifest forjado, bool en `center`, recurso ficticio y signed-zero. Faltan negativos exigidos (`oracles-r1.json:337-354`, `output-contract:50`): corrupt_internal_node, range_overlap/hole, cross_prefix_subtraction, duplicate_chain, missing_query, changed_h, reordered_shard, extra_shard, truncated_json_line, source_cache_comutation, terminal presente inválido, bool en terminal (que hoy fallaría por bug 3), y cadena posterior al hueco (bug 2). `test_station_literals:58` contiene una aserción vacía (`assertEqual(x, x)` vía `if False`): no verifica el punto exacto de A contra `a_exact` del oráculo. `test_consumer_imports_forbidden` sólo inspecciona `import`, no `load_sealed`; el consumidor carga helpers por hash, y los dos que carga (`verify_certified_shore_kernel`, `shore_numeric_discovery`) sí están en `consumer_imports`, así que el rol se respeta.

**Comprobado como correcto**

- Árbol y rangos (`:23-52`): cobertura exacta, padding (0,0) nunca arista, bits y ticks antes de sumar; literales del oráculo coinciden.
- Prefijo dirigido y costura (`:75-89`), `edge_at` reverse usa `to` como índice de arista, estación con segmento local y t de from a to: coinciden con `walk_locate` sellado.
- Bisección (`:111-128`): bajo `li>0` (garantizado por `:72` y el umbral) devuelve el mismo candidato que el caminante secuencial; igualdad final abierta, OUT_OF_RANGE y BOUNDARY_UNCERTAIN en el mismo orden.
- Soporte cerrado/abierto, degeneración `q<THR²` y estado de cuerda cero replican el sellado.
- Formas cerradas de `result` (`:178-184`), estados permitidos sin INVALID_QUERY/DEGENERATE en NUMERIC.
- RESOURCE declarado (consulta o cadena) nunca produce VERIFIED_FULL (`:279,291`); manifest se valida estrictamente y `terminals` se recomputa.
- IO: parse estricto sin duplicados ni constantes, caps de lectura, cierre bit a bit (`io:143`), hash del core, universo y `expected` recomputados, pins de helpers, roles y claims literales.
- Productor: atomic_new con `.tmp`+fsync+replace sólo a destino inexistente, shards exclusivos nunca vacíos, terminal tras cerrar archivos, manifest al final, caps por archivo y total.

**Menores**

- `:200,210-212` no rechazan symlinks/reparse ni subdirectorios con nombre válido (contrato `:11`).
- `:294` deja `completed_chains=0` aunque ya haya cadenas verificadas.

Fixes 1-4 son locales y pequeños; con ellos más los negativos faltantes la unidad pasaría a SOUND-with-fixes pendiente de confirmar el punto 5 contra el pilot sellado.