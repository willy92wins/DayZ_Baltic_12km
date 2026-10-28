Revisión read-only de los tres archivos adjuntos, sin herramientas ni escrituras.

**Veredicto: NEEDS-WORK.** Un contraejemplo verificable hace que la lectura real termine siempre en INCONCLUSIVE_CONTRACT; no produce falso PASS, pero inutiliza la única ejecución de 60 s. Corrección pequeña, agrupable con los menores.

**Bloqueante**

1. **Colisión de clave `seconds` en `Events`** (`preflight_read_discovery_ev112.py:27` frente a `:38-39` y `:81`).
   `Events.__call__` construye `dict(phase=..., seconds=..., **data)`. `read_hash` emite `read_done` con `**row`, y `row` contiene `seconds`. Resultado: `TypeError: dict() got multiple values for keyword argument 'seconds'` en el primer `read_done` (`receipt_old`), dentro de `discover`, capturado por `child()` como INCONCLUSIVE_CONTRACT. El mismo fallo afecta a `hash_mismatch` (`:81`). `directory_done` usa `seconds_spent`, lo que confirma que la colisión sólo se evitó allí.
   Repro mental: `e=d.Events(tmp/'ev.jsonl'); d.read_hash(cualquier_archivo,'x',e)` lanza TypeError. La suite no lo detecta porque el `emit` del fixture (`test:22`) omite `seconds` y `test_durable_events` emite sin datos.
   Consecuencia: la ejecución de producción nunca llega a leer herramientas; se gasta el presupuesto único con un INCONCLUSIVE espurio, sin eventos de fase. Fix: renombrar la marca temporal de `Events` a `elapsed` (o `duration` en `read_hash`), y añadir un test que pase un `d.Events` real a `discover` o a `read_hash`.

**Fixes agrupables (no bloquean, fallan cerrado)**

2. **Búsqueda de pins sin normalizar** (`:64-66`). `tools_sha256` se compara vía `key()` (abspath+normcase), pero `pins` se consulta con `str(p)` exacto, es decir `E:\...\Bin\Binarize\Binarize.exe` y `P:\bin\config.cpp`. Si `contract-r1.json` guarda barras `/`, otra capitalización o `P:/bin/config.cpp`, se obtiene `missing_prior_pin` → INCONCLUSIVE_CONTRACT antes de leer nada. El fixture construye las claves con `str(Path)`, así que no lo prueba. Fix: normalizar las claves de `pins` con `key()`, exigir unicidad tras normalizar (como en `:61`) y consultar por `key(p)`. No puedo inspeccionar el recibo real; declaro el riesgo.

3. **Clasificación de `is_dir`** (`:74-76`). `Path.is_dir()` devuelve False ante PermissionError y otros OSError, así que un fallo de E/S en `P:/DZ` se reporta como `missing_directory` (CONTRACT) y no como INCONCLUSIVE_IO. Fix opcional: `os.stat` directo o `p.stat()` dentro del try, propagando OSError.

4. **Sin lifecycle si el kill no surte efecto** (`:126-128`). Si `p.wait(...+10)` lanza TimeoutExpired, el `except` llama a `timeout()`, espera 10 s y relanza; el segundo `wait` puede volver a lanzar. El padre muere con traceback sin `lifecycle.json` ni `completion.json`, exit code 1 por excepción. No es falso PASS, pero se pierde la evidencia del padre. Fix: envolver en `try/except subprocess.TimeoutExpired` y escribir `lifecycle.json` con `status='INCONCLUSIVE_TIMEOUT'` y `returncode=None`.

5. **Carrera estrecha al borde de 60 s** (`:119-122`). Si el hijo sale entre `p.poll()` y `p.kill()`, `expired` queda activo y el resultado es INCONCLUSIVE_TIMEOUT con `returncode` posiblemente 0. Dirección conservadora (nunca PASS). Aceptable; documentarlo o comprobar `p.returncode` tras el kill.

**Controles verificados como correctos**

- **Falso PASS**: `main` exige status en el conjunto cerrado, `pid` igual al del handle, y concordancia exit 0 ⇔ HASHES_MATCH (`:141-143`). El directorio se crea con `exist_ok=False` (`:136`), así que no hay `report.json` rancio. Un hijo que muere antes de `dump` (p. ej. `child_output_reuse` fuera del try, `:88`) produce INCONCLUSIVE_CHILD.
- **Identidad y rutas**: `original_source` y las tres rutas de `tools_sha256` se validan con `key()` y multiplicidad exacta 3 antes de cualquier lectura de herramienta (`:57-61`); `test_unexpected_path_rejected_before_tools_read` lo cubre. 9 lecturas, 7 rutas, Binarize y config ×2 (`:62-67`).
- **Bytes inmutables**: receipts copiados por bytes (`:48`), relectura de integridad separada y etiquetada `post_receipt_` (`:83-84`), probada con mutación tras `config.cpp:2`.
- **Malformados**: JSON roto, no-objeto, mapas no-dict, digests inválidos y hash de recibo incorrecto fallan con ContractError; tests cubren cada rama.
- **Hash por bloques**: 4 MiB, frontera `+7` probada; `first_block` emitido una vez.
- **Timeout**: rango ≤60 exigido, medido desde antes de `Popen`, kill sobre el handle propio, `ProcessLookupError` inocuo en Windows (Popen.terminate ya maneja PermissionError de proceso terminado). `test_timeout_owned_child_and_persisted_event` verifica PID real escrito por el hijo igual al del handle, y `returncode` ≠ 0 por `TerminateProcess(…,1)`.
- **ctypes**: `GetModuleFileNameW(NULL, buffer, DWORD)` con `create_unicode_buffer` es aceptado por `LPWSTR` (arrays de `c_wchar` convierten); comprobación `0<size<len` detecta truncamiento. `GetProcessTimes` con `HANDLE`+4 `POINTER(FILETIME)` y `int(p._handle)` es correcto.
- **Salida/exit status**: `SystemExit(main())`; hijo 0 sólo con HASHES_MATCH; padre 1 para cualquier otro estado.

**Límites**

No puedo verificar fuera de la cápsula: la imagen CPython de Codex detrás de GIS (que `-I -S` encuentre su stdlib lo prueba la suite al ejecutar el hijo real), el formato de claves de `pins` en `contract-r1.json`, ni el comportamiento de `is_dir` sobre junctions en `P:`. No reabro P3D, tolerancias ni causalidad histórica. Los tests preliminares no se presumen PASS; el hallazgo 1 pasaría la suite actual tal como está escrita.

FIN_REVISION