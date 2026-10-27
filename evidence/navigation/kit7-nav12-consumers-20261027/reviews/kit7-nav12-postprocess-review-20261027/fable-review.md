Contrasté los tres scripts, las pruebas, el inspector, el empaquetador, el verificador 607 y los recibos ya persistidos. Emito el veredicto.

**Veredicto: SOUND**

No encuentro un bloqueo reproducible. Los seis vectores de falso PASS que pide el brief quedan cerrados por código verificable, y las pruebas ejercitan los caminos declarados.

**Malla vieja / grid incorrecto**

- `package_and_deploy_kit7_nav12.py:63-64` exige que `baltic_trial.nm` del directorio de generación tenga el SHA del recibo y lo pasa al inspector con `--grid 1024 1024 --tile-width 12`. El inspector (`inspect_navmesh_v9_ev112.py:23-27`) rechaza cualquier NM cuyo header no declare exactamente 1024×1024 y ancho 12.0. La malla previa de 12.5 m (983×983) falla ahí con `Unexpected grid coverage`.
- `attach_navmesh.py:84-86` solo reemplaza si el NM existente es exactamente `13e1ab…`; el empaquetador lo pasa en `:65` y después valida `baseline_pbo_sha256 == ed1acb…`, `original_entries_unchanged == 6826` y `replaced_entry` (`:67-68`). Un baseline distinto o un segundo NM abortan.
- `:62` fija los cuatro hashes de paquete del host de generación, incluido `narva_trial.pbo = ed1acb…`, y `:58-59` rehashea `gen['inputs']`, `dep['inputs']` y `host['package_hashes']`. Contrastado con `launch-inputs.json` y `host-identity.json` reales: coinciden.

**Referencia movida / tolerancia rebajada**

- `verify_kit7_nav_ev112.py:36` rechaza `max_waypoint_surface_error_m != .801`; `:39-49` fija 607 consultas, 562 locales, 8 testigos F, 139 modelos; `:65-71` reconstruye corredor/exterior desde la centerline con buffer 2.1 y exige diferencia simétrica < 1e-6. `verify_continuity_nav_v30.py:35,39` fija .011. Ninguno es parametrizable desde el consumidor.
- `finish_kit7_nav12_probe.py:55` pasa `--reference-sha256` tomado de `frozen.json`, y `frozen.json` está en la lista del gate. `reference.json` real contiene `.801`, UUID `3325b685…`, header y log_name coherentes; `contract-parity.json` registra CSV `305e80…` idéntico.
- Un log de Nav8 no puede pasar: `verify_continuity_nav_v30.py:18` exige el header con el UUID nuevo, y `capture_kit7_nav_log.ps1:5,12,14` exige log fresco posterior al arranque del proceso y `END;607`.

**Identidad / cierre**

- Cierre estricto sin excepción de recuperación: `package_and_deploy_kit7_nav12.py:31-32` exige `graceful`, `self.state none`, `preserve_for_recovery` falso; `verify_c_orderly_close.py:7-9` exige `orderly_close`, `stop_required False`, `reason None`; `:24` acepta solo exit 0/-1; `:28` observed dentro de 30 s tras CLOSE_INTENT.
- `:34` añade validación UUID del run_id en vez del literal de Nav9. `:35` encadena run_id en gen/host/completion/close.
- Sonda: `finish_kit7_nav12_probe.py:17-30` ata run_id, PID, creación ±2 ms, mission, init.c hash, packages canónicos = `deployment['packages']` y log binding al PID; `:53` reutiliza `validate_generation_exit`.

**Drift**

- Cadena completa: gate → `package` (`:23-26` incluye a sí mismo, `verify_c_orderly_close.py` y `verify_nav12_generation_budget.py`) → `deployment.json` (`:78` mezcla frozen + packages + gate + mcp-after) → precheck del orquestador (`orchestrate_kit7_nav12_probe.js:8`) → `finish` (`:14-15`). `finish_kit7_nav12_probe.py` está en el gate, así que se autoverifica vía `deployment['inputs']`.

**Presupuesto de generación**

- `verify_nav12_generation_budget.py:12-23` compara cadena exacta de `started_utc`, enteros estrictos 18000/18300 (rechaza bool por `type is int`), trunca a milisegundos como hace V8 con `Date.parse`, y acota `finished_utc`. El `generation-budget.json` real (`07:29:02.448146+00:00` → `12:29:02.448Z`) satisface la regla. `generate_navmesh_console.py:66,91` escribe `started_utc` con el mismo `now()` que leerá la comparación de cadena.

**Pruebas**

- `test_kit7_nav12_probe_flow.cjs:15` busca `finish_kit7_nav12_probe.py`, que sí aparece en `orchestrate_kit7_nav12_probe.js:48`. En `consumer_failure` el mock devuelve exit 1, `cmd` lanza (`:6`), y la aserción `:31` exige `consumed`, `closed==1`, `released==1`. Antes, con el nombre viejo, `consumed` nunca se activaba y ese assert habría fallado; ahora el camino sí se ejercita.
- Heartbeat: `:6` llama `beat()` dentro del bucle de `cmd`; `:14` recupera antes de cualquier `event()` por shell. El mutante `event_before_recovery` recurre (`HEARTBEAT_ERROR` → `cmd` → `beat` → …) hasta `Command recursion bound` (`test…flow.cjs:9`), y `cmd_direct_heartbeat` muere en el `assert(active)` del mock. `coordinator-controls.json` y `command-flow-controls.json` registran `coordinator_sha256 = 80ec15…`, el mismo que el gate.
- FIFO: `dayz_test_run` con `on_busy:'queue'`, `takeover:false`, sin `session_status` previo (`:20-21` lo prohíbe). `foreign_takeover` y `command_lease_foreign` exigen `closed==0, released==0`.

**Mejoras opcionales, no bloqueantes**

1. `finish_kit7_nav12_probe.py:50` hashea el observador vivo desde W. Está cubierto por `frozen.json`, pero sería más explícito comparar también con `deployment['inputs']`.
2. `package_and_deploy_kit7_nav12.py:64` fallará con `Output already exists` si el coordinador de generación llegara a escribir `inspection.json` en G. Hoy G solo contiene `generation.json` y logs, así que no aplica.
3. `test_kit7_nav12_probe_command.cjs` inyecta `beat` como mock trivial; la recuperación real se prueba solo en el harness de lifecycle. Es coherente con la separación declarada.

Nada de lo anterior afecta a la RAM, que queda fuera de este alcance.
