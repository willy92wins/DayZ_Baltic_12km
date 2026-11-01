**Veredicto: SOUND-with-fixes / CONVERGE.** Condición: sin F1 el consumidor emite VERIFIED falso; nada se materializa hasta aplicar F1–F3 y suite verde con los mismos bytes.

**Mecanismo estático observado (no hipótesis):**

**F1. report.elapsed_ns nunca se valida.** `consume_pair_c1c2a.py:95-108` lee `status`, `contract_sha256`, `claims`, `phase`, `reason`, `journals`, `marker`, `rows`; `elapsed_ns` del report no se toca. Confirma ambos repros de Codex: `True` pasa porque no hay chequeo de tipo; `fixed.done+20s` pasa porque no se compara con el último journal ni con el sobre finalize. Repro: tras `produce()`, reescribir report con `elapsed_ns=True` y repinar observación → VERIFIED. Corrección en `:108` dentro de `if full`: `type(report['elapsed_ns']) is int`, `last<=report['elapsed_ns']<=360e9`, `report['elapsed_ns']-last<=10e9`, y `report['elapsed_ns']<=receipt['seconds']*1e9+tolerancia`. Añadir N16 (bool) y N17 (+20s) como tests CLI.

**F2. receipt.rc comparado por igualdad sin tipo.** `consume_pair_c1c2a.py:108` `receipt['rc']==0` acepta `False` y `0.0`; `:109` idem con `!=0`. Repro: observación con `rc:false` y report PREPARED → VERIFIED. Fix: `type(receipt['rc']) is int`. Mismo hueco en `:82`: `type(x) in (float,int)` deja pasar `bool` para seconds/peak_rss/disk (`True<=536870912`). Fix: excluir bool explícitamente.

**F3. Supervisor mata al productor por excepciones transitorias propias.** `run_pair_c1c2a.py:49-57` recorre `diskroot` con `rglob` cada ~1s mientras el productor crea archivos; un `FileNotFoundError`/`PermissionError` de `file.stat()` sobre un archivo recién creado, o `psutil.AccessDenied` en `:40/:44` (sólo se captura `NoSuchProcess`), cae en `:60`, fija `reason=SUPERVISOR:*` y el `finally` `:62-65` mata una preparación válida. El consumidor luego clasifica INCONCLUSIVE sin culpa del productor. Repro estático: forzar `OSError` en el stat del bucle. Fix: `try/except OSError` por archivo en `:54` (contar como 0 y seguir) y `except psutil.Error` en `:40,:44`. Añadir test de supervisor con proceso ficticio.

**F4. child.wait(timeout=5) fuera de try.** `run_pair_c1c2a.py:66`: si el proceso no muere en 5s, `TimeoutExpired` escapa, no se escribe `completion.json` y `main:77` nunca produce observación externa. Fix: capturar y registrar `owned_retired=False`; `main:77` ya aborta con assert, pero debe guardar el hecho.

**F5. Sobre FINALIZE no aplicado en productor.** `prepare_pair_c1c2a.py:127` `need(time.monotonic()<until)` con `until=now+10` es trivialmente cierto; el único tope real entre `:127` y `:131` es `global_end`. No es falso PASS por sí solo, pero combinado con F1 nadie comprueba que el sellado cupiera en 10s. Fix mínimo: tomar `until` en `:127` y usarlo en `:130-131` para el rehash del marker y el `need` previo a `write_json`.

**F6. Esquema del report abierto.** `consume_pair_c1c2a.py:96` no fija el conjunto de claves del report ni los tipos de `rows`; claves extra o `rows.inputs` con estructuras adicionales pasan si los subconjuntos consultados coinciden. Fix: `set(report)=={contract_sha256,status,phase,reason,journals,marker,rows,claims,elapsed_ns}` y, en full, `set(report['rows'])=={inputs,profile_before,profile_after,source,work,fixed}`.

**F7. Código de rechazo mal etiquetado para C1B.** `consume_pair_c1c2a.py:110` usa `readjson` sobre el manifiesto C1B, cuyo fallo de pin se reporta como `OBSERVATION_PIN` aunque es `PIN` del contrato (N01 por manifiesto). No es falso verde; afecta a la tabla de estados congelada. Fix: parámetro de código en `readjson`.

**F8. Test faltante: identidad del intérprete.** `consume_pair_c1c2a.py:81` exige `command[0]==sys.executable`, pero no se contrasta con el python.exe pinado en `contract.json:357-366`. La atribución de la suite al runner fijado queda sólo nominal. Fix: comparar `checkfile(sys.executable)` con la fila de evidencia; test con pin alterado.

**Hipótesis no ejecutadas (no se afirman como fallo):**

- El par se lee cuatro veces completas (`:111` scan fuente, `:117` copia+relectura, `:122-123` rescan) más el `rglob` del supervisor por segundo sobre el mismo árbol en escritura. Puede presionar COPY150/FIXED80. No se infiere causa de latencia ni caché; sólo se registra que la suite real medirá esto y que F3 reduce I/O competitivo si se baja la cadencia a 5s.
- N06 en producción detecta cambio de tamaño/mtime, no sobrescritura in-place con tamaño y mtime preservados; límite declarado, no defecto nuevo.

**Lo que está bien y no se toca:** inventario exacto de raíz y directorios (`prepare:46-55`, `consume:37-52`), marker `xb` antes de operar, secuencia/orden/sobre por fase en journals (`consume:97-107`), rechazo de hash autodeclarado por rehash propio (N11), binding report↔observación↔journals, suite CLI real con oráculos literales y recuento 19 correcto.

**Cabida en una corrección de 180s:** sí. F1, F2, F6 son líneas añadidas en `consume:82,:96,:108`; F3, F4 son dos `try/except` en el supervisor; F5 un `until` propagado; F7 un parámetro; F8 un `checkfile`. Más cuatro tests cortos (N16, N17, rc bool, supervisor OSError). Ningún cambio toca lectura de fuentes, geometría ni sobres declarados. El contrato congelado no cambia; sólo `oracles.json` añade códigos N16/N17 y se refresca `author-completion.json`.

**Alcance preservado:** nada nativo, C1C1 BUDGET inmutable, sonda B fuera de alcance, sin revisión de postimagen independiente reclamada. R0 corre aparte; este dictamen no asume su resultado.