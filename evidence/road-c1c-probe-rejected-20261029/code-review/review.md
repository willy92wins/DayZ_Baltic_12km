## Dictamen: NEEDS-WORK

No ejecutar todavía. La estructura general es correcta, pero hay huecos que pueden quemar la única sonda o producir una aceptación débil. No hay captura real: todo lo probado es sintético.

### Bloqueantes concretos

1. **Preflight no auditable en la cápsula.** `contract.json` fija `preflight-local.py` por hash, pero su contenido no fue entregado. El wrapper sólo exige `rc == 0` y `reason is None` en [probe_road_compile_c1c.py](E:\DayZ-Baltic-Build\shape-repair-20261025\road-c1c-local-author-20261029\probe_road_compile_c1c.py). No queda probado que el original reproduzca `SyntaxError`, que la copia tenga único delta de prefijo raw, ni que su AST/diff se archiven.  
   **Fix mínimo:** entregar `preflight-local.py` y test negativo: original falla, copia parsea, diff de un solo literal.

2. **Árbol fuente no cerrado antes del control.** La copia verifica por hash los archivos esperados, pero `trees()` sobre `source_stage` recién corre **después** del control. Un archivo extra preexistente dentro de `source_stage/<arm>/root` puede estar presente durante la compilación y detectarse tarde.  
   **Fix:** ejecutar `trees(source_stage)` y `trees(work)` tras la copia y antes de `help`/build; mantener la verificación entre brazos ya existente.

3. **`include`/`exclude` no son privados.** El contrato apunta a rutas del directorio autor y el wrapper las pasa directamente. Contradice la adjudicación de rutas absolutas privadas y deja ventana de mutación entre el `pincheck` inicial y cada brazo. El observador sólo re-chequea al final.  
   **Fix:** copiar ambos al root privado, verificar pin, re-hashear inmediatamente antes de cada brazo y pasar esas rutas.

4. **Identidad de la copia portable incompleta.** Los `pincheck` post-brazo verifican las rutas **instaladas**, no los bytes en `root/tools/AddonBuilder`. El observador tampoco hashea la copia portable ni valida `logger_sha256` contra `logger_bytes(raw, paths)`. Si el proceso raíz es demasiado breve para ser fotografiado, una copia portable alterada puede pasar inadvertida.  
   **Fix:** hashear el set portable antes/después de cada lanzamiento y que [observe_road_compile_c1c.py](E:\DayZ-Baltic-Build\shape-repair-20261025\road-c1c-local-author-20261029\observe_road_compile_c1c.py) lo verifique, incluido logger.

5. **Ownership con fuga y excepción no sellada.** `proc_run()` descubre descendientes sólo a través de procesos vivos ya conocidos cada 150 ms: un nieto creado y huérfano entre muestreos puede no entrar en `owned`, ni ser matado ni observado. Además, `child.wait(timeout=5)` en el `finally` puede lanzar `TimeoutExpired`, que no es `Stop` ni `OSError`, enmascarando recibo/reporte. La atestación es honesta —`loaded_image_attestation: False`, `continuous_identity: False`— pero no debe presentarse como identidad continua.  
   **Fix:** convertir ese timeout en `MONITOR_ERROR`, declarar huérfano/no observado como `PROBE_INCONCLUSIVE_NOT_OBSERVED`, y añadir test real con nieto.

6. **Gate de `help` no bloquea hijos.** En modo `help_mode`, `gate()` retorna antes de aplicar `allowed_images`. Un hijo desconocido o `DSSignFile` durante `-help` no bloquea, y el observador ignora por completo help, preflight, perfiles y logger.  
   **Fix:** aplicar `UNEXPECTED_CHILD` también a help, con allowlist explícita, y verificar esa fase en el observador.

7. **Logs: marcador agregado y binding laxo.** `gate()` y `arm_check()` aceptan `Build Successful` de **cualquier** log entre stdout/stderr/`.rpt`; basta que exista algún `.rpt`. Si el “recibo privado” debe ser el `.rpt`, el marcador tiene que estar en el `.rpt` privado. Además, el observador define `allowed_logs` como stdout/stderr **más todo archivo presente** en `logs/<arm>`: un extra dentro del directorio queda automáticamente permitido.  
   **Fix:** exigir marcador en `.rpt`, conjunto exacto de nombres esperados, y rechazar extras.

8. **Presupuestos inconsistentes.** El writer usa `total_seconds = 1050`, pero el observador consume 120 s **fuera** de ese deadline; la ejecución completa puede llegar a ~1170 s contra el techo adjudicado de 1050 s. Aparte, tras un build de hasta 300 s, el mismo sobre de 300 s del brazo debe absorber `snapshot_logs`, gate, doble `trees()` y pinchecks: un control exitoso puede ser rechazado por tiempo de verificación, no por compilación.  
   **Fix:** reservar los 120 s del observador dentro del total (deadline del writer en 930 s) o redefinir el techo **antes** de ejecutar, nunca después. Separar “cap proceso del brazo” de “verificación post-brazo” con presupuesto propio acotado.

### Tests tautológicos o insuficientes

En [test_probe_road_compile_c1c.py](E:\DayZ-Baltic-Build\shape-repair-20261025\road-c1c-local-author-20261029\test_probe_road_compile_c1c.py):

- `test_candidate_requires_control` sólo compara strings contra el oráculo. **No prueba** que el candidato no se lance. La secuencia real en `mainrun()` sí bloquea —`need(st == 'ARTIFACT_OBSERVED_ONLY')` tras control—, pero falta test de integración que lo demuestre.
- El positivo colapsa identidades: la misma imagen/hash hace de ejecutable sintético, AddonBuilder y Binarize. Así, el proceso raíz solo podría satisfacer `any(sha == binarize_sha)`. En producción los hashes reales son distintos, pero el test no prueba esa discriminación.  
  **Fix:** hashes/pids distintos para raíz y Binarize, más negativo “sólo raíz observada” → `PROBE_INCONCLUSIVE_NOT_OBSERVED`.
- `test_artifact_pin` muta sólo el reporte. El oráculo “reporte/hash co-mutados” no está probado: artefacto + `header_hex` + hash co-mutados, con mtime forzado a la ventana, pasarían.  
  **Fix:** fijar el `report_sha` desde un canal separado en cuanto el writer termina, y test de co-mutación con `utime` forjado.
- Sin tests de: help con hijo inesperado, DSSignFile específico, mutación de work entre brazos, mutación de include, mutación portable, límites RSS/disco, ni preflight.

### Lo que sí está sound

- El orden control→candidato en código, y el bloqueo del candidato si control no da `ARTIFACT_OBSERVED_ONLY`.
- Rechazo de rc≠0, timeout, sin marcador, log fuera de ventana, WRP múltiple/ausente y magic `0WZD`; sólo se acepta magic `OPRW` con header de 8 bytes registrado, sin fijar versión 32 ni decodificar terreno. `COMPILE_PROBE_OBSERVED_ONLY` no habilita motor ni aceptación nativa.
- `DSSignFile` queda fuera de la allowlist de imágenes observadas y no se pasa `-sign`. No exijo validación de `-binpath`: la resolución de rutas sigue siendo objeto de observación runtime, no una promesa.
- Si el control vacío no compila, el código se detiene con la razón de proceso/artefacto observada y no atribuye la causa al vacío. Esa lectura debe conservarse.
- `claims` permanecen en falso y el observador declara `NOT_EVALUATED` / `NOT_IMPLEMENTED` para semántica y decoder.

**Conclusión:** corregir 1–8 y reforzar los tres tests indicados antes de consumir el intento.