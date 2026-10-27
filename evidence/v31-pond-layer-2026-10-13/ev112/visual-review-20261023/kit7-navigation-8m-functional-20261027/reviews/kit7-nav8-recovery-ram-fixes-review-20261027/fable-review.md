**Veredicto: Parte 1 SOUND. Parte 2 NEEDS-WORK** (no por el script vivo, que no hay que tocar, sino porque el cierre oficial fallará o perderá evidencia si no se actúa antes de que termine el generador).

**Parte 1: tres hallazgos corregidos**

- Logs: las seis `init.c` usan `baltic_ab_NN_<12hex>.log` dos veces (líneas 33 y 64) y guardan de mundo una vez (línea 27). `missions.json:12-52` coincide; `conditions-controls.json` liga el SHA actual de `missions.json` y del consumidor intacto (`59966ad…`).
- Regex estricto en `orchestrate_nav8_ram.js:4` y doble aparición exigida en `prepare_nav8_ram_pass.py:21-22`.
- `prepare_nav8_ram_pass.py:30` conserva los pares originales de `deployment.json`.
- `coordinator-controls.json:3` lleva `f719e39…` (SHA actual); el previo `7b59643…` quedó en `-before-review.json`. Flag `wx` en `test_nav8_ram_flow.cjs:34` explica el EEXIST. 11 casos y 11 controles de condiciones verificados.
- Menor: `orchestrate_nav8_ram.js:4` valida la misión desde memoria (`nav8RamConfig`), no contra `benchmark-gate.json` que escribe `prepare`. Fix: tras la línea 9, comprobar `m.mission` y `m.profile_log` contra `gate.mission`.

**Parte 2: recuperación viva**

Correcto: adopción solo si `self.state==='none'`, sin owner, run propio `RUNNING_IDLE`, y `checkedBridge` fija PID 46288 y creación 01:56:26.504 (`resume_kit7_nav8_generation.js:12,17-19`). `mcp-recovered.json` confirma mismo proceso. Deadline absoluto 07:04:33Z queda tras el timeout del wrapper (18000 s desde ~01:59:32, es decir ~06:59:32Z) y tras el fin del observer (~07:02:12Z). Revalidación de inputs en línea 25. Sin arranque nuevo. `generator-cancel.json` ausente: cancel no ejecutado.

Hallazgos:

1. **BLOQUEANTE para el cierre oficial.** `timeline.jsonl:27` contiene `GENERATOR_CANCEL_INTENT` (02:34:29). `verify_c_orderly_close.py:27` rechaza cualquier evento de ese tipo, así que `validate_generation_exit` fallará siempre para este run aunque todo termine bien. Mecanismo: el `event()` original se registró (el ps1 terminó en segundo plano) aunque el `cmd` falló por heartbeat. Fix: no editar el verificador original; añadir un verificador de recuperación que acepte exactamente ese evento solo si `generator-cancel.json` no existe, `progress.jsonl` muestra avance posterior a 02:34:29 y el wrapper 11394 terminó con exit 0 con el mismo PID 71040.

2. **Pérdida del recibo de cierre.** `cleanup.json` y `completion.json` siguen existiendo (idénticos a las copias `-before-lease-recovery.json`, verificado). `write()` usa `apply_patch Add File` (línea 9); si rechaza rutas existentes, las líneas 50 y 57 fallan, `cleanupProblem` se marca, el estado final será INCONCLUSIVE y el dict `close` de `dayz_test_close` solo quedará en `notify`. El `cleanup.json` estale diría `close:null`. Fix ahora, sin tocar el script: borrar o renombrar esos dos ficheros (las copias ya los preservan) antes de que termine el generador.

3. **Re-ejecución destructiva.** Si el resume falla y alguien lo relanza, `snapshot('mcp-recovered.json')` (línea 24) fallará por fichero existente, `problem` se marca y el `finally` cancela el generador propio (línea 41). Fix: nunca relanzar tal cual; una segunda recuperación necesita nombre de snapshot nuevo y gate explícito sobre la ruta de cancelación.

4. **Riesgo temporal heredado.** Solo hay un `beat()` por ronda (línea 29) y los eventos HEARTBEAT_OK muestran rondas de 35-160 s. Si una ronda supera TTL+gracia, `beat` lanza "Coordination lost" y, según si el ps1 de evento tarda más o menos de 10 s, se cancela o no el generador. No concluir sobre latencia sin medir; mitigación: no cargar el host.

5. Menor: `LEASE_RECOVERED` se registra incondicionalmente en línea 26 además del de `beat`; hay dos (02:16:08 y 02:42:35). El verificador no lo rechaza.

Sin falso PASS detectado: `genDone` exige exit 0 y estado de `generation.json`, y el cierre requiere lease propio y `checkedBridge`.
