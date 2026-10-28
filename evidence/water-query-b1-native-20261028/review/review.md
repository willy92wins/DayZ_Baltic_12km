**Veredicto: SOUND-with-fixes.** Un fix mínimo obligatorio antes de sellar `accepted.json` (riesgo de FALSO FAIL que quemaría la única activación FIFO), más reservas menores sin impacto en falsos PASS.

**Qué verifiqué**
- Fuentes congeladas en `reviewed-source` contra las copias vivas: el binder en W es byte-a-byte idéntico en contenido al congelado 02; `tests.log` 17 OK; `water-query-b1-flow-tests` source_sha coincide con inputs.json (71f19633…). No pude hashear (sin Bash), así que el resto de hashes de inputs.json los acepto como declarados por Codex.
- Cadena de consumo: `files()` exige SHA externo del seal, status `B1_NATIVE_READY`, deployment.json dentro del seal, manifiesto completo incluyendo selected/original/CSV/producer/engine/4PBO, regenera el CSV desde A+original con `check_csv`, y `source_points` mantiene `original['status']=='FAIL'` y 2658. `consume_bound` vuelve a ejecutar `files()` después del run (revalidación post-run) y exige `result.json` inexistente; `gate()` prohíbe launch/result/native.log previos. Gate consumido y seal alterado cubiertos por tests.
- Formas reales de la API MCP contra los recibos reales del run dry-road (probe/*.json): `adopted_run{ok,run_id}` (loopback.py:5935-5944), `server_peer.run_id/binding_state/version_state/last_poll_age_s` (core.py:107-121), `processes[].role/pid/creation_time_utc` y `client_diagnostics[].state` (process_lifecycle.py:2422), `dayz_test_close` devuelve `run_retired` y `stop_required=(not run_retired) or status_unavailable` (dayz_test_tool.py:4563-4564) y la rama close_failed siempre `stop_required=True` (4288). `dayz_test_stop` exige sesión idle (3190) y el coordinador libera antes de stop; `dayz_test_stop` devuelve `status` succeeded/failed (1668). Preflight sin lease (server.py:5482-5493). Ruta de misión canónica: `str(Path('C:/temp/...'))` produce backslashes sin barra final, cumple `_valid_local_absolute_path`.
- Coordinador: sólo adopta `adopted_run.run_id===runid`, sin takeover; heartbeat antes de cada comando y en cada iteración (≤5s+comando, dentro de 20s); readiness 60×5s=300s; deadline capture fijado en readiness y el script PS rechaza deadlines >180s; captura verifica PID+creación cada 2s y no sobrescribe `native.log`; finally cierra, libera, fallback stop sólo si `stop_required && !run_retired`, estado terminal registrado; token sólo en `store`, y el test comprueba que ningún `apply_patch` contiene el token. `launch.json` real del dry-road no contiene credenciales.
- `capture_owned_server_identity.ps1` es el mismo fichero (700a2d6a) que produjo los recibos del dry-road, probado en motor real.

**Hallazgo 1 (fix obligatorio pre-deploy): igualdad exacta de instantes de creación mezcla redondeo y truncado**

`water_query_native_b1_ev112.py:69-70` exige `instant(host['created_utc']) == instant(mcp creation_time_utc)`.
- MCP genera `creation_time_utc` con `datetime.fromtimestamp(psutil_float).isoformat(timespec="microseconds")` (native_process_guard.py:134-135): redondeo al microsegundo más cercano.
- El host escribe `$created.ToString('o')` con 7 decimales (100 ns) y Python 3.12 (gis-env, pyvenv.cfg) trunca el séptimo dígito en `fromisoformat`.
- Recibos reales: MCP `…51.317316Z`, host `…51.3173164Z`. Coincidió porque el séptimo dígito era 4. Con séptimo dígito ≥5 MCP redondea hacia arriba y el host truncado queda un microsegundo por debajo: `creation_binding` falla con el proceso correcto.

Consecuencia: aproximadamente una de cada dos ejecuciones legítimas produce FALSO FAIL del binder después de haber consumido la activación FIFO, el preflight y el run. No es falso PASS, pero el plan prohíbe repetir sin cambio justificado, y corregir el binder tras el run rompe el seal de accepted.json. El dry-road tenía la misma exposición (consume_dry_road_full_native_20261028.py:21) y simplemente tuvo suerte en dos runs. El PS ya protege la identidad con ±2 ms (capture 18, identity 13), así que una tolerancia de 1 ms en Python no debilita nada: no hay reutilización de PID en 1 ms.

Contraprueba ejecutable (añadir a `test_water_query_native_b1_ev112.py`, debe FALLAR con el código actual y PASAR tras el fix; `test_creation_changed` con +1 s debe seguir fallando):

```python
def test_creation_rounding_tolerated(self):
    r=list(receipts())
    r[4]['processes']=[dict(role='server',pid=100,creation_time_utc='2026-10-28T13:00:00.000001+00:00')]
    r[2]['created_utc']='2026-10-28T13:00:00.0000006+00:00'   # host 'o' truncado por fromisoformat
    b.identity(*r)
```

Fix mínimo (`water_query_native_b1_ev112.py:70`):

```python
require(all(abs((instant(v)-created).total_seconds()) <= 0.001
            for v in (host['created_utc'], after['created_utc'], capture['created_utc'])), 'creation_binding')
```

Recalcular después el hash del binder y del test en inputs.json y en el futuro accepted.json.

**Hallazgo 2 (menor, opcional): `cleanup['close']` nulo produce TypeError, no ValueError**

`finish_water_query_b1_native_20261028.js:44-47` deja `close=null` si `dayz_test_close` lanza. El binder (`:63`, `:86`) indexa `cleanup['close']['run_id']` y revienta con TypeError en vez de `lifecycle_not_closed`. No hay falso PASS: `cleanup_error` ya está poblado y la excepción aborta el consumo. Consecuencia sólo de legibilidad del rechazo. Fix mínimo: `close = cleanup.get('close') or {}` y usar `close.get('run_id')`, `close.get('run_retired')`. Contraprueba: `self.bad(6,'close',None,'lifecycle_not_closed')` falla hoy con TypeError.

**Reservas reales (sin fix exigido)**

- **Adopción errónea deja vivo el run propio.** En `wrong_adoption`, el coordinador no intenta `dayz_test_stop(runid)` aunque sería una operación sólo-propia tras liberar (`:41`, `:49`). Coherente con el plan ("registrar y resolver oficialmente"), pero exige resolución manual con el servidor ocupando el box. Aceptable; documentar el paso manual.
- **Presupuesto 180 s desde readiness incluye hashing.** `frozen()` rehashea todos los inputs de accepted+deployment (incluye los 4 PBO, entre ellos narva_trial.pbo, y el native.log de 2658) y luego `identity()` rehashea PBOs y ejecutable, todo antes de arrancar el script de captura y con el deadline ya corriendo (`:28`, `:32-33`). Si el productor termina antes de readiness, la captura es inmediata y sobra tiempo. Si el hashing supera ~60 s, el margen efectivo se reduce. Sugiero que Codex mida la duración de `frozen()+identity()` en el run y la registre; no cambio el presupuesto del plan.
- **accepted.json debe usar la clave exacta** `E:\DayZ-Baltic-Build\shape-repair-20261025\water-query-b1-native-20261028\deployment.json` (`files():40`, construida con `str(root/...)`), con backslashes.
- **Sin aserción de hash en memoria**: el binder lo declara en `limits_binding`; la identidad del host sigue siendo PBO on-disk antes y después. Correcto y así se reporta.

**Lo que no bloqueo**
- Aislamiento imperfecto entre toolcalls y el instante entre `dayz_test_run` y `acquire_wait` (otro run idle haría `multiple_idle_runs` y el coordinador se detiene sin mutar ajeno).
- La captura toma `created_utc` del string esperado, no del proceso vivo; el proceso vivo ya se verificó a ±2 ms en la misma iteración.

Aprobación tras el fix 1 no implica mapa PASS: original 2658 FAIL conservado, H3 y referencia de producto INCONCLUSIVE, y ningún mock cuenta como ejecución del motor.

FIN_REVISION