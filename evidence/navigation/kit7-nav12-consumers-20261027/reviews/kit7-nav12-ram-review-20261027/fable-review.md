**Veredicto: SOUND**

Revisé los cuatro scripts del alcance contra los Nav8 finales que completaron seis pasadas (pass-01..06 con cleanup y comparison FAIL_RAM conservados), las seis misiones, los tres JSON de controles y los lectores inmutables. No encontré ningún repro bloqueante.

**Paridad con Nav8 verificada**

- `prepare_nav12_ram_pass.py`, `finish_nav12_ram_pass.py` y `finalize_nav12_ram_ab.py` son byte a byte el texto Nav8 con la sustitución nav8→nav12 (carpeta D, carpeta nativa, nombre de función). Ninguna puerta se relajó: PASS607 + identidad + deployment rehasheado (prepare:16-18), pasada anterior PASS y cerrada limpia (prepare:24-26), exe pinneado (prepare:27), conteo de extras 4/1 (prepare:32), ratio 1.10 y dispersión 5% intactos en `compare_server_baseline_ev112.py:37-38`, cuyo hash coincide con el aceptado en Nav8.
- `orchestrate_nav12_ram.js` difiere de Nav8 exactamente en las dos correcciones declaradas: `cmd` llama a `beat()` recuperable (línea 7) y el catch de `beat` ya no emite `HEARTBEAT_ERROR` por shell antes de comprobar `self.state none`, sin owner y RUNNING_IDLE propio (línea 17). Los dos mutantes `cmd_direct_heartbeat` y `event_before_recovery` revierten justo esos cambios y son rechazados. Sin TDZ: `cmd` solo evalúa `beat` cuando `token` es truthy, y `token` se asigna en la línea 19, después de definir `beat`.
- Orden del sampler: captura al bind (línea 24), observer (25), medición (30), y solo después `capture_owned_server_identity.ps1` (33) con hash de paquetes y comparación contra `benchmark-gate.json` (34), igual en ambos mundos. El mutante `hash_during_measurement` lo cubre.
- Cierre: `beat` → `session_status` → `checked` → CLOSE_INTENT → `dayz_test_close` solo con lease activa y run propio (línea 40); liberación de lease (41); recibo terminal (42). `validate_generation_exit` exige un único CLOSE_INTENT, sin GENERATOR_CANCEL_INTENT ni SERVER_EXIT_OBSERVED y salida ≤30 s (`verify_c_orderly_close.py:26-28`). La excepción Nav8 de cancelación no se usa.

**Condiciones y misiones**

- Las seis `init.c` tienen 30 s de calentamiento (línea 53), 120 muestras y END (75-77), guard de mundo único (27) y nombre de log en exactamente dos sitios (33, 64). UUIDs nuevos; en `profiles-130` existen logs `baltic_ab_*` de dos series anteriores pero con sufijos distintos, así que la comprobación "Fresh engine log required" (orchestrate:11) no colisiona. `missions.json.source_sha256` es el mismo e4178561 que en Nav8: misma plantilla, solo world/log cambian.
- Deployment: `package_and_deploy_kit7_nav12.py:12,78` escribe `kit7-nav12-consumer-20261027/deployment.json` con 3 PBO en `P:/Mods/@DayZ_Baltic_EV112_Kit7Nav12` más DayZ_MCP.pbo; coincide con `extra_mods` de orchestrate:12 y con el filtro de prepare:30-32. Hoy ese deployment.json, result.json e identity-verification.json no existen, por lo que prepare aborta en la línea 16: no hay forma de lanzar RAM antes del PASS607.
- Herencia de muestras: directorio de pasada fresco (prepare:23), host.jsonl fresco (`capture_server_baseline_ev112.ps1:9`), reference/result frescos, y finalize exige que no existan `comparison.json` ni `result-revalidated.json` (finalize:13,17). Una pasada FAIL deja `result.json` ≠ PASS y bloquea prepare de la siguiente; no hay vía para repetir y elegir.
- Deriva de fuentes: `benchmark-gate.json` incluye los hashes de accepted.json más orchestrator/finish/finalize/prepare; finish los rehashea (finish:14) y finalize rehashea los validadores antes y después de comparar (finalize:12,37).

**Controles**

- `coordinator-controls.json` y `command-flow-controls.json` llevan `coordinator_sha256` 2aafd7…, idéntico a `source-hashes.json`: los controles corresponden al orchestrator exacto. 14 escenarios + 3 mutantes y 8 de comando coinciden con lo declarado; `chernarus_success` cubre `extra_mods: []`.
- `conditions-controls.json` enlaza `missions.json` d22f19… y el comparador 59966a…, ambos iguales a la lista.

**Observaciones no bloqueantes (no requieren otra ronda)**

1. `test_nav12_ram_conditions.py:24-27`: `p.write_text(...)` sin `newline=''` en Windows convierte LF a CRLF en la copia temporal. `mismatched_engine_log` y `wrong_world_guard` siguen fallando por la razón esperada, pero `mission_drift_breaks_equivalence` rompería la equivalencia aun sin el comentario añadido, así que ese control es más débil de lo que parece. No afecta a los lectores ni al pipeline real.
2. El orchestrator no compara el `nav12RamConfig` del store con `missions.json` en disco antes de lanzar. Si divergieran, finish lo detectaría (`mission_path` y `profile_log` contra gate, finish:21) y la pasada se consumiría como FAIL, no como PASS falso. Basta con cumplir la instrucción de cargar el store desde el missions.json congelado.
3. Los snapshots de procesos conservan nombres en disco (`processes-before/after.json`); finalize publica solo recuentos y deltas, como se declara (finalize:33). Correcto que no se presenten como prueba de ausencia de carga.

Nada de lo anterior produce un PASS falso, hereda muestras Nav8, altera condiciones entre mapas ni toca procesos ajenos. La preparación puede congelarse en accepted.json tal cual.
