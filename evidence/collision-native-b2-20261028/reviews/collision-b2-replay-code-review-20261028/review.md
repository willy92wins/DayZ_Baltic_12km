**Dictamen: SOUND-with-fixes** (un fallo material, fix mínimo de una línea).

Revisado sólo el diff del consumidor frente al archivo `R/collision-b2-replay-inputs-20261028/collision_native_b2_ev112.py`, el nuevo `tools/quality/collision_b2_replay_binding_ev112.py`, sus tests y el test del consumidor actualizado. Lectura sin ejecución.

**Diff del consumidor: correcto.** El único cambio semántico está en `tools/quality/collision_native_b2_ev112.py:59-82` (positivo, uniforme en las 270 Q, `bullet_layer_drift` si cambia), `:162` (confusor `native_bullet_layer_ordinal_unverified` incondicional en cada grupo, también con valor 2) y `:212-216` (observación cruda, `mapping_status='UNVERIFIED_FOR_ANY_VALUE'`). Nada más cambia: `source_points`, `csv_for`, puntos, offsets, estados, tolerancias, `evaluate` y `status='INCONCLUSIVE_DIAGNOSTIC'` son byte-equivalentes al archivado. El test `('Q',14,'3')` sigue rechazando porque `alter` muta una sola Q y dispara deriva; los uniformes 2/8/16 producen el mismo confusor y nunca PASS. Correcto frente al plan.

**Wrapper de replay: cadena de sellos correcta salvo un eslabón.** Verificado en `collision_b2_replay_binding_ev112.py:11-20`: exactamente dos excepciones por basename, bytes archivados contra `d['inputs']` del deployment original (que sí contiene ambas fuentes con los SHA `f0b1dda1…` y `39cdff0d…`, líneas 63 y 66 de `deployment.json`), fuente nueva contra `a['new_sources']`, y TODO lo demás del deployment byte-idéntico, lo que incluye el binder `collision_native_b2_binding_ev112.py` y los módulos `water_query_*`. Reutiliza `identity` sin modificar, re-verifica el CSV, no escribe nada y rechaza `result.json` preexistente. El rechazo original queda sólo como copia en el resultado.

**Fallo material (único):** `collision_b2_replay_binding_ev112.py:27-30`. El receipt es el ÚNICO sello de los artefactos del run (`host-identity`, `host-after`, `mcp-identity`, `log-capture`, `cleanup`, `launch`, `native.log`), porque el `accepted.json` original es pre-run y no los contiene. Pero el código no exige que `a['receipt']` esté en `a['inputs']`; sólo hace `verify(receipt['inputs'])`, es decir, el receipt se verifica a sí mismo. El binder sí impone el patrón análogo (`unsealed_deployment`, `collision_native_b2_binding_ev112.py:38`); aquí falta.

Contraejemplo: `accepted.json` con `status='B2_REPLAY_READY'`, `new_sources` correctos y `inputs` sin el receipt. Se reescriben `native.log` y `log-capture.json` de forma consistente (`count=270`, `sha256` recalculado) y se regenera `receipt.json` con `inputs` recalculados y `original_rejection` libre. `replay_seal_drift`, `original_seal_drift`, `original_launch_binding`, `verify_superseded` e `identity` pasan todos, porque ninguno compara el receipt contra un sello externo. El test `test_capture_or_other_historical_input_drift` no cubre esto: mete `native.log` en `inputs` del deployment, pero en los datos reales el log NO está en `deployment.json`, sólo en `receipt['inputs']`.

Fix mínimo, tras la línea 27:
```python
require(a['receipt'] in a['inputs'] and str(Path(__file__)) in a['inputs'] and
        all(p in a['inputs'] for p in a['new_sources']), 'replay_manifest_unsealed')
```
Esto hace que el sello de replay (`accepted_sha`) cubra receipt, helper y las dos fuentes, que es exactamente lo que el nuevo accepted externo debe incluir según el encargo. Añadir un subcaso en el test de replay que elimine `a['receipt']` de `inputs` y espere `replay_manifest_unsealed`.

**No material, sin acción:** el resultado del replay no incluye el manifiesto `inputs` que sí emite `consume_bound`; las referencias por SHA de ambos accepted son suficientes. `replay()` omite `incomplete_manifest`/`unbound_package` de `files()`, pero esos bytes están sellados por `16afbdb6…` y ya pasaron en el run original rechazado.

No se afirma que INCONCLUSIVE sea PASS ni que el 8 esté certificado; el código tampoco lo hace. 47 FAIL / 21 inciertos no se tocan.

FIN_REVISION