**Veredicto: SOUND-with-fixes** (delta B3G1 únicamente; no certifica Enforce ni autoriza ejecución nativa).

**Lo que está bien**

- `normalize_launch` cumple la adjudicación: `type(value) in (int, float)` excluye bool, `== 600` descarta 599, 600.0000001 (distinto en doble precisión), NaN e inf; `isfinite` queda tras el `and` y no explota con 10**500. Raw intacto, copia por `deepcopy`, clave única.
- `capture_window` exige basis exacto, deadline = ready+180s, `ready <= start <= end <= deadline` y `mission_error_before_capture is False` (rechaza 0). Es consistente con readyUTC/deadline persistidos.
- `identity` conserva `previous.identity` y añade proceso-antes-de-ready, fin de captura == snapshot y last_write <= captured. No toca funciones puras.
- Misión: la única diferencia frente a R0 es la partición de la segunda asignación W en tres asignaciones (`init.c:220-222`); header, 20 campos, consultas, relojes, nombre de log y `CreateCustomMission` intactos. El test de secuencia verifica prefijo, sufijo y orden sea/pond/ref por referencia.

**Bugs y falsos PASS/FAIL**

1. **Timestamps naive aceptados.** `instant` sólo reemplaza `Z`; un recibo con hora local sin sufijo produce datetimes naive y, si los cuatro campos lo son, la ventana pasa con una base de reloj falsa (falso PASS). Si se mezclan naive y aware, Python lanza `TypeError`, no `ValueError`, y el consumidor no lo distingue de un error de programa. Fix: en el wrapper exigir `tzinfo` no nulo (o sufijo `Z` literal) por campo y fallar con `require(..., 'clock_not_utc')`.
2. **Ventana sin vínculo al run.** El recibo de ventana no lleva run id ni PID; `identity` podría emparejar la ventana de otro run con la captura actual. Fix: `require(window['run_id'] == launch run/adopted id, 'window_run_mismatch')` y lo mismo para `host` PID si está disponible.
3. **`identity` no tiene tests.** Ninguno de los tres `require` nuevos (`ready_before_process`, `capture_end_binding`, `capture_after_snapshot`) está cubierto; un error de signo o campo pasaría la suite. Fix: tres negativos con stub de `previous.identity` (monkeypatch) y un positivo que compruebe que `previous.identity` recibe la copia normalizada y no el raw.
4. **Claves ausentes → `KeyError`.** Tanto `normalize_launch` como `capture_window` lanzan `KeyError` si falta `request`/`wait_for_box_s` o un campo de ventana; el plan pide falsos negativos claros. Fix: resolver claves con `require(k in ...)` antes de usarlas.
5. **`mission_error_before_capture` es autodeclarado.** Un `False` escrito por el coordinador no prueba que se inspeccionó el script log fresco. Como mínimo exigir en el recibo el `script_log_checked_utc` (entre ready y start) y que sea `<= capture_started_utc`. Esto puede diferirse al coordinador pendiente, pero el contrato debería dejar el campo ya definido.

**Observaciones menores**

- El test de orden no asegura que la línea original de R0 contenga exactamente los nueve tokens en ese orden; añadir el mismo parseo sobre `oldlines[index]` cerraría la equivalencia semántica.
- `test_wrong_numeric_rejected` depende del orden `== 600 and isfinite`; si alguien lo invierte, 10**500 lanza `OverflowError`. Dejar un comentario o testear explícitamente el `OverflowError` ausente.
- El límite `end <= deadline` admite fin exactamente en deadline; acorde al plan (dentro de plazo), no es bug.
- En la misión las líneas 211, 217, 224 y 226 siguen siendo concatenaciones largas con ints/vectores; no quedan certificadas por no haber sido el primer error. Esto es aceptado, no aprobado.

**Test útil adicional**

Un test que serialice un recibo normalizado y el raw y compruebe que el hash del raw original no cambia tras `normalize_launch` e `identity` (protege al futuro consumidor que debe hashear el raw intacto).

**Condición de cierre:** corregir 1-4 antes de que el nuevo consumidor invoque `normalize_launch`; 5 queda ligado al coordinador aún no escrito. Sin cambios en la misión. No se autoriza nueva admisión nativa.

FIN_REVISION