**Veredicto: NEEDS-WORK.** Un bloqueo determinista en la finalización y dos ajustes menores. No encontré falso PASS ni artefactos stale; el flujo FIFO, heartbeat, observer, cierre y rehash están bien adaptados desde v2.

**Hallazgos**

1. **BLOQUEANTE: nombres de log incompatibles con el consumidor de equivalencia.**
   `compare_server_baseline_ev112.py:58-62` exige que init.c contenga exactamente dos apariciones de `baltic_ab_\d{2}_[0-9a-f]{12}\.log` y que el engine artifact tenga ese nombre. Las seis misiones usan `baltic_nav8_ab_NN_<hex>.log` (`BalticNav8AB01_131442df91e4.BalticTrial\init.c:33,64` y análogas; `missions.json:12,20,28,36,44,52`). La subcadena `baltic_ab_` no existe, `findall` devuelve 0 y `conditions_identity` lanza "Mission and engine log identity differ".
   Mecanismo: `finalize_nav8_ram_ab.py:18` llama a `load_pass` en la pasada 1 y aborta antes de `require_equivalent`/`compare`.
   Impacto: las seis pasadas runtime (~15 min cada una) se consumen correctamente en `finish` y luego la comparación final es imposible. No es falso PASS, pero inutiliza el experimento y no se puede corregir sin tocar el consumidor, que está vetado.
   Fix: regenerar las seis misiones con nombres `baltic_ab_NN_<12hex nuevo>.log` (sufijos distintos de los de v2 para que `orchestrate_nav8_ram.js:11` no rechace por log preexistente), actualizar `missions.json`, `mission-validation.json`, los hashes de init.c en `source-hashes.json`, y solo entonces crear `accepted.json`. El resto del pipeline no cambia.

2. **MENOR: validación del coordinador más laxa que el consumidor.**
   `orchestrate_nav8_ram.js:4` acepta `^[a-z0-9_]+\.log$`. Impacto: el mismo error del punto 1 vuelve a pasar inadvertido en futuras regeneraciones. Fix: usar el regex exacto del consumidor `^baltic_ab_\d{2}_[0-9a-f]{12}\.log$` y, si se desea, que `prepare_nav8_ram_pass.py:19-20` compruebe que `row['profile_log']` aparece dos veces en init.c.

3. **MENOR: dependencia de formato de claves en deployment.json (aún inexistente).**
   `prepare_nav8_ram_pass.py:28-30` reconvierte claves con `Path(p)` y luego indexa `dep['packages'][str(p)]`. Si deployment.json se escribe con barras `/` o distinta capitalización, se produce KeyError, no falso PASS. Fix: iterar `dep['packages'].items()` y conservar la clave original, o normalizar ambos lados con `resolve()` como hace `finish_nav8_ram_pass.py:40`.

**Verificado como correcto**

- Lanzamiento FIFO: `orchestrate_nav8_ram.js:12` fija `on_busy:queue`, `wait_for_box_s:600`, `takeover:false`; sin sondeo previo ni prelease (`session_acquire_wait` solo tras run propio, línea 19). El mock `test_nav8_ram_flow.cjs:19-20` lo hace cumplir y `coordinator-controls.json:3` lleva el hash actual del coordinador, no stale.
- Orden de medida: sampler arranca al BOUND (línea 24) antes del hashing de paquetes (líneas 33-34), igual para ambos mundos. El consumidor exige cobertura de warmup (`read_server_baseline_ev112.py:45-51`) así que un BOUND tardío produce FAIL, no PASS.
- Frescura: log de motor ausente antes de lanzar (línea 11), `host.jsonl`, observer, identity y RPT rechazan salida preexistente; `prepare` rechaza directorio de pasada existente y exige cleanup limpio de la pasada previa (líneas 21-24).
- Identidad antes/después: `finish_nav8_ram_pass.py:20,27,30-41` compara creación de proceso, pid, run_id, hashes de misión/ejecutable/config e inventario completo de paquetes contra `before.json`. Sin clientes (línea 18,31), sin `navmesh_data_server`.
- Cierre oficial: `verify_c_orderly_close.py:6-9,20-28` exige `orderly_close`, exit 0/-1, un único CLOSE_INTENT y salida observada ≤30 s; RPT con línea de terminación única.
- No herencia de RAM: cada pasada es proceso nuevo y `compare_server_baseline_ev112.py:22` rechaza identidades repetidas; el pbo de la malla nueva se hasheó contra deployment en `prepare:30` y en host tras la medida.
- Gates: `prepare:13-18` exige accepted.json, PASS607 nativo e identity-verification; el consumidor mantiene 1.10 de ratio y 5% de dispersión sin tocar (`compare:37-40`). `finalize_nav8_ram_ab.py` es idéntico a v2 salvo la nota retenida de pass-05, que correctamente no se arrastra.
- Snapshots de procesos siguen siendo informativos; no se reclama ausencia de carga del host.

**Siguiente paso**: corregir el punto 1 (y opcionalmente 2 y 3), re-hashear y regenerar `source-hashes.json` antes de crear `accepted.json`. Hasta entonces, no lanzar la pasada 1.
