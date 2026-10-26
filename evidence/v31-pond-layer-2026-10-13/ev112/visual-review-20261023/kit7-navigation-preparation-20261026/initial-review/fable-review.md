**Veredicto: NEEDS-WORK.** Hay un defecto determinista en la comparación de claves de paquetes que hace fallar el coordinador o antes del lanzamiento (bloqueo) o después (intento desperdiciado). El resto del flujo de propiedad, cancelación y reporte es sólido y es idéntico al coordinador C salvo nombres y las dos líneas nuevas de gate físico.

## Qué está confirmado y qué no

- **Simulado, no nativo.** `coordinator-control-flow.json` y `command-flow-controls.json` son controles con herramientas mock; su propio campo `scope` lo declara. No existe `kit7-overlap-native-20261026/full/result.json` ni `launch-inputs.json`. El único artefacto nativo es la calibración (`FRESH_VANILLA_CALIBRATION_PASS`, run 3eedb524), que no es la puerta de 6801 puntos.
- **Adaptación C→kit7 limpia.** Comparado línea a línea con `orchestrate_nav_c_retry_v3.js`: solo cambian nombres, rutas, hashes y se añaden las líneas 12 y 13 del gate físico. No hay regresión de lógica.
- **No pude verificar hashes** (sin comandos). Ambos JSON de control citan el coordinador 3536e84f…; `adaptation.json` cita 06689d1a… (ver fallo 2).

## Fallos concretos

1. **BLOQUEANTE. Claves de paquetes no normalizadas.** `consume_kit7_overlap_native.py:28` escribe `packages` con la clave del bridge en barras normales (`P:/Mods/@DayZ_MCP/Addons/DayZ_MCP.pbo`, ver `calibration/result.json:16`) y las tres kit7 con barras invertidas. `capture_owned_server_identity.ps1:32` escribe todas con barras invertidas. El coordinador compara claves exactas en `orchestrate_nav_kit7.js:13` (prepared vs physical) y en `orchestrate_nav_kit7.js:37` (host vs prepared, `$h.package_hashes.($v.Name)`). Ningún `launch-inputs.packages` satisface ambas: con claves copiadas del resultado físico, la línea 37 lanza `Loaded stack mismatch` después de arrancar el servidor; con claves del host, la línea 13 bloquea antes. El consumidor nativo sí normaliza (`consume_kit7_overlap_native.py:28`); el coordinador no. El test no lo detecta porque usa claves ficticias `world/water/pilot/bridge` y responde `ok()` a todo PowerShell inline.
   Corrección mínima: normalizar en ambos lados. En JS, línea 13: `const norm=p=>p.replace(/\//g,'\\').toLowerCase();const phys=Object.fromEntries(Object.entries(physical.packages||{}).map(([k,v])=>[norm(k),v]));` y comparar `phys[norm(path)]!==hash`. En la línea 37, construir `$hh=@{}; foreach($p in $h.package_hashes.PSObject.Properties){$hh[[IO.Path]::GetFullPath($p.Name).ToLowerInvariant()]=$p.Value}` y buscar `$hh[[IO.Path]::GetFullPath($v.Name).ToLowerInvariant()]`.

2. **`adaptation.json` describe otro coordinador.** Hash 06689d1a…, gate contra `kit7-water-native-20261026`, mod `Kit7Native` y piloto 46244e7f… (superado). El congelado actual usa `kit7-overlap-native-20261026`, `Kit7Overlap` y 3d9550bf…. El manifiesto launch-inputs debe citar 3536e84f… y un registro de adaptación regenerado; si no, la cadena de procedencia apunta a un borrador distinto.

3. **El gate físico no fija el mundo ni el piloto por valor.** Líneas 12 y 13 exigen 4 paquetes iguales entre físico y manifiesto, pero no que contengan 10e09e3f…, 97edcafe… y 3d9550bf…, ni que `physical.engine_sha256` sea a500be80…. Un manifiesto construido sobre un PASS antiguo coherente consigo mismo pasaría el pre-lanzamiento y fallaría solo en el wrapper Python (línea 43), tras arrancar. Corrección: tras la línea 13, `const must=['10e09e3f…','97edcafe…','3d9550bf…'];if(must.some(h=>!Object.values(prepared.packages).includes(h))||physical.engine_sha256!=='a500be80…')throw Error('Kit7 physical gate not bound to candidate');`.

4. **Sondeo del wrapper ya terminado en la cancelación** (`orchestrate_nav_kit7.js:70`). Si el wrapper salió con error (bucle principal terminado con `q.session_id` vacío), el `finally` vuelve a llamar `write_stdin` sobre una sesión muerta. Si la herramienta real lanza error en ese caso, se marca `preserveForRecovery` y se deja el servidor vivo con el generador ya confirmado `ALREADY_GONE`. El mock devuelve exit 1 repetidamente, así que no se prueba. Corrección: `const result=(q&&!q.session_id)?q:await tools.write_stdin(...)`.

5. **Evento `CLOSED` registrado sin cierre** (`orchestrate_nav_kit7.js:84`). Con dueño ajeno, `close` es null y aun así la línea de tiempo recibe `CLOSED`. `cleanup.json` lo desmiente, pero `timeline.jsonl` por sí solo es un cierre ajeno aparente. Corrección: `if(close&&close.run_retired&&!close.already_gone)await event('CLOSED')`.

6. **Un fallo transitorio de heartbeat aborta la generación** (`beat`, línea 25). Si la lease sigue `active` tras un error puntual, se lanza `Coordination lost`, se cancela un generador sano y luego se cierra el servidor. Es conservador y seguro, pero con 71 min de generación conviene un reintento único antes de declarar pérdida. Opcional.

## Tests: huecos, no tautologías

- Los tres escenarios de gate solo cubren estado, paquetes ausentes y hash de piloto distinto; faltan `points`, `identity_bound`, `inputs_unchanged` y, sobre todo, claves con barras mezcladas (fallo 1).
- Las comprobaciones PowerShell inline (líneas 11, 37, 67) nunca se ejecutan en el mock. Hay que declararlas explícitamente como no cubiertas.
- La ruta de recuperación de lease (línea 26, `LEASE_RECOVERED`) y `Own run not adopted` no tienen escenario: `session_acquire_wait` del mock siempre concede.
- La aserción `summary` (test línea 73) acepta cualquiera de los tres estados; en `success` debería exigir `GENERATION_STAGE_COMPLETE_PENDING_VALIDATION`.
- Nada tautológico en sentido estricto: las tres mutaciones negativas son reales y `assert.notEqual` evita mutaciones vacías. `test_nav_kit7_command.cjs` es correcto, incluido que la ausencia de `exit_code` se trata como fallo.

## Lo que está bien

Launch con `takeover:false` y banco vacío; adopción solo del run propio sin dueño ajeno; captura padre/hijo con reintento acotado; cancelación solo con identidad exacta (PID, creación, ejecutable, línea de comandos) y `preserveForRecovery` si no se confirma; cierre solo con lease activa; estados terminales que no reclaman navegación aceptada; helpers sin tocar DayZ.

Antes del READY: aplicar fallo 1 (obligatorio), 2 y 3, añadir un escenario de test con claves reales mezcladas, regenerar los dos JSON de control con el nuevo hash y citar ese hash en launch-inputs.
