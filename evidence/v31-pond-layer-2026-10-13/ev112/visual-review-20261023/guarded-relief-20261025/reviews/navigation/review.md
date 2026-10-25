**Veredicto: wrapper SOUND-with-fixes; sonda EV112 NEEDS-WORK (dos fallos bloqueantes antes de desplegarla).** Nada de esto afecta al cálculo en curso del generador.

**Bloqueantes en la sonda**

1. **Y de tablero sobrescrito con terreno** en `tools/navigation/prepare_current_nav_probe_ev112.py:34-38`. El bucle aplica `tri_sample(h)+0.1` a las 37 consultas, incluidas `bridge_out`/`bridge_back` (`missions/BalticV30ContinuityNavV1.BalticTrial/queries.csv:8-9`, Y≈11.03 de tablero). La preparación histórica las excluía explícitamente (`prepare_continuity_nav_v30.py:68-69`, "Physical deck query, not terrain Y"). Impacto: el request baja al cauce; `SampleNavmeshPosition(…,2,…)` puede fallar o engancharse a otro polígono, produciendo FAIL/PASS por motivo distinto al evaluado. La aserción de la línea 41 no lo detecta porque sólo compara XZ y `expect`. Fix: `if q['name'].startswith('bridge_'): continue` y registrar la exclusión en `endpoint-updates.json`.

2. **Drift de formato del CSV/init.c** en `:47-49`. `write_text(...,encoding='utf-8')` sin `newline='\n'` genera CRLF en Windows; el artefacto aceptado usaba `ascii`, LF (`prepare_continuity_nav_v30.py:120-121`) y `.8f`, no `.9f`. Impacto: `FGets`/`Split(";")` recibe `\r` en el tercer campo; comportamiento de `ToVector()` no probado, y el `code_sha256` deja de ser comparable. Fix: replicar `encoding='ascii', newline='\n'` y `.8f`.

**Menores en la sonda**

- `:30` no fija SHA esperado de `--previous-reference`; sólo lo registra. Añadir `--expected-previous-sha256`.
- `:44-45` no asegura que las cadenas sustituidas existan (histórico: `assert source in code`). Mitigado por `--expected-source-sha256`, pero con otro fuente el header queda viejo y el fallo aparece tarde.
- `:51` guarda `str(a.terrain)` sin `resolve()`; el verificador lo abre relativo al cwd (`verify_continuity_nav_v30.py:58`).
- Fail-closed por `assert` (líneas 27-29, 40-42): desaparece con `-O`. Convertir en `raise`.

**Wrapper del generador** (`generate_navmesh_console.py`)

- Identidad y drift: correctos. SHA del ejecutable pinneado por perfil (`:21-25`), inputs verificados antes (`:58`) y después (`:89`), `returncode==0` exigido, sin `--kill`, no toca el servidor en TIMEOUT. Versión serializada debe ser 9 para el nuevo SHA (`:99`); no reinterpreta TESM6.
- **Cabecera v9 es supuesto TESM6** (`:97-100`): `count == nx*nz` y layout `<5I`. Si el formato 9 difiere, un archivo válido se marca `GENERATION_FAILED` indistinguible de un fallo real, y `header_ok` no se guarda en el recibo. Fix: añadir `receipt['header_ok']` y `receipt['failure_reasons']`; con generador v9, estado `GENERATED_FILE_HEADER_LAYOUT_UNVERIFIED` cuando magic/version coinciden pero la aritmética no. Sigue devolviendo 1.
- Piloto no obligatorio: `--additional-pbo` es opcional, pero el plan (`:15`) exige el piloto en la identidad. Hacer obligatorio al menos uno o documentar en `limits`.
- `--timeout-s` por defecto 1800 vs plan 3600 (`:17`). Cosmético si el caller lo pasa.
- Si `sha()` en `:89` lanza `FileNotFoundError`, el recibo queda en `STARTED` sin `finished_utc`. Envolver y marcar `POSTCHECK_FAILED`.
- Duplicados de input se detectan por cadena, no por `resolve()`.

**Tests** (`test_navmesh_generator_identity.py`): cubren versión, mutación, SHA desconocido y piloto erróneo con generador simulado; coherente con lo declarado. Faltan casos de returncode≠0, archivo ausente/corto y `count≠nx*nz`. Ninguno prueba navmesh real ni formato 9.

**False PASS del evaluador**: no encontrado. `verify_continuity_nav_v30.py:18` exige header exacto, `verify_v30_acceptance.py:21` exige `END;37` y cobertura idéntica, Y del request se compara con la referencia actualizada (`:42-43`), el control de terreno (`:31,39`) sigue atando el WRP cargado al `.npz`. Umbral 0.801 heredado sin cambios.

**Plan**: coherente con el código salvo los puntos 1 y 2 anteriores y el piloto opcional. Pendientes explícitos (estructura, carga, 37 rutas, aceptación visual/rendimiento) quedan correctamente fuera del recibo.
