**Veredicto: SOUND-with-fixes.** La implementación respeta el plan (sin preadquisición, heartbeat sólo tras adopción exacta, deadline=ready+180s persistido, bytes reales del script en antes/captura, finally con close/release/status). Hay un fallo de limpieza real y dos puntos no verificados que deben cerrarse antes de la pareja nativa. No encuentro falso PASS.

**Hallazgos críticos**

- **Run propio sin retirar si la adopción falla.** `run_contact_b3g1.js:26` lanza `adopted_wrong_run` antes de poner `adopted=true`, y el finally en `:65` sólo cierra si `adopted`. Lo mismo ocurre si el lanzamiento devuelve run_id con estado distinto de `succeeded` (`:22`) o si `acquire` lanza excepción. Resultado: servidor vivo tras un outcome FAILED, bloqueando la caja FIFO del siguiente arm y violando "retirarlo siempre". El fixture `foreign` en `test_run_contact_b3g1.cjs:25` exige `!close`, es decir, codifica el bug. Fix: cerrar siempre que `run` esté definido (`if(run)`), y en `:80` evaluar release/self/pending cuando `run||token`, no sólo cuando `adopted`. Ajustar el fixture para que `foreign` y un nuevo caso "succeeded sin adopción" exijan close.

- **deployment.json de B2 sin pin.** `prepare_contact_b3g1_ev112.py:31` lee el deployment antiguo y de él toma engine, scripts, wrp, frozen, original, packages y hashes vanilla. Ese archivo no está en `required` (`:24-26`) ni se compara con constante. La verificación posterior en `:56` comprueba los hashes vanilla contra los valores que el propio archivo declara: es circular. Si el JSON cambió, el preparador bendice los nuevos valores. Fix: añadirlo a `required` (está dentro de la aprobación) o pinarlo con una constante SHA como PROOF/MANIFEST.

- **Regex de cabecera del script no validada contra un log real.** `observe_contact_b3g1.ps1:22` y `contact_b3g1_native_ev112.py:16` exigen `started at ... (YYYY-MM-DD HH:MM:SS UTC)`. Si el formato real de `script_*.log` difiere, cada observación lanza `Script header UTC missing` y la pareja fracasa por instrumentación, no por el motor. El run R0 dejó un script log con el error registrado; verificar el regex y el patrón `SCRIPT\s*\(E\)|Can.t compile` contra esos bytes archivados es una comprobación única y necesaria, no un test redundante.

**Hallazgos secundarios**

- **Decodificación estricta puede producir falso FAIL.** `observe_contact_b3g1.ps1:51` usa UTF8 con throwOnInvalid y `contact_b3g1_native_ev112.py:15` decodifica strict. Un byte cp1252 en el log (rutas, nombres) aborta una captura válida. El hash ya se calcula sobre bytes. Fix: decodificar con `errors='replace'` sólo para la búsqueda de patrones.

- **Margen del heartbeat ajustado.** `run_contact_b3g1.js:32` duerme 15s y `continuity` (`contact_b3g1_native_ev112.py:62`) exige gap ≤20s entre finalizaciones. Un heartbeat que espere el lock serializado tras `bridge_status` o `close` más de 5s invalida una captura correcta. Fix: dormir 10s, o medir el sello en el momento de la llamada y añadir el máximo de latencia al contrato.

- **Dependencia de `no_base_mods:true`.** `run_contact_b3g1.js:9` carga sólo el mod aislado, y el preparador deja `dayz_mcp.pbo` en su ruta original sin copiarlo (`prepare_contact_b3g1_ev112.py:47`). Si el launcher no inyecta el puente por sí mismo, el peer nunca llega a BOUND y se agota readiness. No puedo verificarlo; debe confirmarse que R0 usó la misma forma de petición y alcanzó BOUND.

- **Error del observador se pierde.** `contact_b3g1_tools.js:17` reduce cualquier rc≠0 a `host_command_failed:<log>`. El `NATIVE_SCRIPT_ERROR` queda sólo en host-N.log, no en outcome.json. Fix: incluir la última línea de stderr/salida en el mensaje.

- **save en finally puede escapar.** Si `apply_patch` falla en `:77` (archivo preexistente o ruta fuera del workdir permitido), la excepción sale de `runArm` sin outcome.json. Envolver los dos save finales en try/catch que marque FAILED_CLEANUP.

- **`proc.creation_time_utc`** en `contact_b3g1_tools.js:34` es un nombre de campo del bridge no verificado. Si no existe, el PowerShell falla de forma segura, pero toda la pareja fracasa. Confirmar el nombre en una respuesta real de `bridge_status`.

**Lo que está bien**

Observador y consumidor coinciden en deadline, PID/start con 1ms, hash de script antes y en captura, orden `capture_started ≤ checked ≤ capture_ended`, y ningún token llega a disco. La condición FAILED_CLEANUP se propaga a outcome.json, que el consumidor exige igual a CAPTURED_PENDING_CONSUMER, así que un cierre degradado no puede consumirse. El preparador exige destinos frescos y no toca addons compartidos.

**Orden recomendado:** aplicar fixes 1 y 2, validar regex contra el log R0 archivado, confirmar inyección del puente y nombre de campo, y sólo entonces lanzar control. Si el control reproduce `Formula too complex`, detener sin candidato como indica el plan.

FIN_REVISION