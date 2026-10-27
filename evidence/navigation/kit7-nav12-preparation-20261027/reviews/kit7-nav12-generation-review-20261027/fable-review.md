**Veredicto: SOUND.** No encuentro ningún contrato que permita declarar verde la generación 12 m sin evidencia ni terminar procesos ajenos. Las mejoras abajo son opcionales y no bloquean el lanzamiento.

**Qué comprobé (solo lectura, sin ejecutar nada; hashes de source-hashes.json no recalculados)**

- Coordinador `R/orchestrate_kit7_nav12_generation.js` contra sus dependencias reales: wrapper, observador, scripts de captura/cancelación/eventos, launch-inputs.
- Harness `R/test_kit7_nav12_generation.cjs`, 26 casos y 8 mutantes, y si cada control prueba su contrato.
- Empaquetador, inspector, tests y preparación.

**Contratos verificados correctamente**

1. **Recibo de presupuesto.** El wrapper escribe `run_id` y `started_utc` antes de lanzar el proceso (`tools/navigation/generate_navmesh_console.py:66-74`) y conserva la misma cadena al reescribir (`:120`). `budgetFrom` exige `run_id` idéntico y fecha parseable (coordinador `:42-46`); `checkBudget` compara todas las claves del archivo contra el recibo del wrapper y contra la copia en memoria (`:47-52`). El bucle usa `deadline` fijo del recibo (`:82`), nunca la hora de reanudación. Recibo preexistente rechazado (`:77`). Cualquier fallo aquí termina en cancelación e INCONCLUSIVE, no en PASS.
2. **Recursión de beat.** `cmd` usa `beat()` recuperable (`:6`); la recuperación no registra ningún evento por shell antes de comprobar `self.state==='none'`, sin owner, mismo run RUNNING_IDLE, adopción, identidad del servidor y presupuesto (`:35-38`). El mutante `event_before_recovery` cae por el límite de recursión del mock y `cmd_direct_heartbeat` por fallo del comando: ambos prueban el contrato, no un transformado idéntico.
3. **Propiedad y cancelación.** La cancelación exige beat válido, lease activo propio, run presente y `checkedBridge` (PID y creación del servidor) antes de llamar al script (`:96`). El script verifica PID, hora de creación ±2 ms, ejecutable, hash y línea de comandos del generador (`R/cancel_owned_nav_c_generator.ps1:12-18`) y nunca toca DayZ. Sin `generator-identity.json` la cancelación falla y se preserva servidor y lease.
4. **Falso PASS.** `GENERATION_STAGE_COMPLETE_PENDING_VALIDATION` exige exit 0, estado exacto del wrapper, snapshot posterior, inputs sin deriva y cero `cleanupProblem`, incluido observador completo (`:91-93,105-112`). El wrapper devuelve 0 solo con `header_ok`, inputs inalterados y returncode 0 (`:114-122`). El inspector 12 m sigue siendo paso aparte, como declara el plan.
5. **Input.** `rewrite_tile_width` exige exactamente una declaración `tileWidth=12.5;` (`tools/navigation/package_nav12_config_ev112.py:28-31`); el roundtrip compara carácter a carácter ignorando solo layout, con cadenas entrecomilladas intactas (`:22-24,34-36`). Preparación revalida 6826 entradas idénticas, WRP y lineage con Overlap (`R/prepare_kit7_nav12_generation.py:14-22`). Inspector: 12 explícito sin ampliar tolerancias (`inspect_navmesh_v9_ev112.py:16,26,88`); test rechaza 8/12,5 bajo `--tile-width 12`, grid 1024×1024 falso y límites corruptos (`tests/test_navmesh_v9_prefixes_ev112.py:101-121`).
6. **FIFO.** Harness afirma sin `status` ni `acquire` previos al launch, `on_busy=queue`, `wait_for_box_s=600`, `takeover=false` (`test_kit7_nav12_generation.cjs:91`).

**Mejoras opcionales (no bloqueantes)**

- **Control débil de origen de `started_utc`.** En `expiry_during_command` y `expiry_after_budget` el reloj del mock no avanza entre el lanzamiento del generador y la escritura del recibo. Un mutante que usara `new Date()` en lugar de `generation.json` pasaría igual. El código es correcto por lectura (`:78`), pero el contrato no está probado. Repro: en `test_kit7_nav12_generation.cjs:59` añadir `clock+=30000` tras fijar `generatorStarted`; si el mutante `source.replace("budget=budgetFrom(await read(out+'/generation.json'))","budget=budgetFrom({run_id:runid,started_utc:new Date().toISOString()})")` sobrevive con el harness actual, confirma el hueco.
- **`Date.parse` sobre isoformat de Python.** El wrapper emite microsegundos (`+00:00`, seis decimales). V8 lo acepta, pero no hay fixture con esa forma: el mock usa `Z` sin fracción. Fallo posible solo hacia `Invalid generation clock receipt` → cancelación segura. Repro en Node: `Date.parse('2026-10-27T10:00:00.123456+00:00')` debe ser número.
- **Observador etiquetado.** El observador parte antes que el generador con 18300 s desde su propio inicio (`observe_owned_server_exit.ps1:32,46`); su timeout se registra como `SERVER_EXIT_OBSERVED` (`:85`). Como el wrapper limita a 18000 s, el generador caduca primero mientras la brecha de arranque sea <300 s. Solo afecta a la legibilidad del timeline.
- **Flip de estado no vinculado.** El coordinador exige `READY_AFTER_CODE_REVIEW` (`:10`) y launch-inputs está en `PREPARED_PENDING_CODE_REVIEW`. El cambio altera el hash registrado en source-hashes.json y nada verifica que solo cambie ese campo. Recomiendo que el recibo de lanzamiento registre el hash de launch-inputs tras el flip y el diff de una sola línea.
- **`expiry_pid_reuse` libera lease.** Tras `Server process changed` el coordinador no cierra ni preserva, pero sí libera la lease (`:104`), dejando el run sin propietario en el lifecycle. Conservador respecto a procesos; podría preferirse `preserveForRecovery` para diagnóstico.
- **Deadline tras recuperación.** Ningún test demuestra que el bucle no recalcula `deadline` tras `LEASE_RECOVERED`; el código es const (`:82`). Un mutante que reasigne `deadline` dentro de `beat` no está cubierto.

**Límites de esta revisión**

- No ejecuté tests, hashes ni Node; las afirmaciones de PASS del harness son las del artefacto, que declara alcance MOCK.
- PowerShell inline (`:11,:59,:93`) no está cubierto por el harness, como el artefacto admite; lo verifiqué solo por lectura.
- No audité los módulos MCP ni el consumidor 607/RAM futuro.
- Incidente de espacio en C: y archivado NavV9/Nav8 aceptados como notas del plan, sin reverificar.

Identidad reconfirmada: Claude Fable 5.1 vía CLI nativo, sesión de solo lectura, sin escrituras ni procesos.
