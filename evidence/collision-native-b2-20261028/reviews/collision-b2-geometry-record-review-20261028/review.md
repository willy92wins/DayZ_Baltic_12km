**Veredicto: SOUND-with-fixes.** La corrección preserva fielmente los 834 inconclusos sin fabricar PASS ni ocultar el defecto. Las dos correcciones pendientes afectan a la reproducibilidad de la regresión, no al consumidor.

**Diferencia real entre nuevo y archivado** (sólo tres puntos; el resto del archivo es idéntico):

- `tools/quality/collision_native_b2_ev112.py:148-156` sustituye el `finite(h['height'])` incondicional del archivado (l.150) por: estado obligatorio en el conjunto cerrado de tres valores, `height` finito obligatorio en los dos estados resueltos, y `height` prohibido en el vertical inconcluso. Cualquier otro estado o combinación lanza ValueError.
- `tools/quality/collision_native_b2_ev112.py:169` añade el confusor por fila cuando alguna geometría offline del punto no es FACE_INTERIOR.
- `tools/quality/collision_native_b2_ev112.py:195` produce `native_minus_geometry=None` si el registro no tiene altura, en vez de restar y explotar.

**Fidelidad a inconclusos.** El productor en `collision_scene_b2a_ev112.py:173` emite el registro vertical sin clave `height`, y en l.184-186 emite los dos estados resueltos con `height`. El consumidor nuevo exige exactamente ese contrato. No hay filtrado: cada registro de `byhit[key]` se copia a `geometry_at_nominal_xz` cuando el rayo impacta, así que la aritmética 834+194+78=1106 por fila se conserva. Un MISS nativo sigue dejando la comparación vacía y la altura de contacto en None, igual que antes.

**No fabrica PASS.** El estado sigue fijo en INCONCLUSIVE_DIAGNOSTIC, se conservan 47 FAIL y 21 inciertos originales, y no se toca VECTOR_ERROR ni ninguna tolerancia. El nuevo confusor sólo añade razones, nunca las quita.

**Tests.** Las cuatro mutaciones del test de rechazo mapean cada una a un `require` distinto: height ausente en resuelto, NaN, estado desconocido, y altura inventada en vertical. El recuento de 28 coincide con 13 tests en el fichero del consumidor más 8 y 7 en los dos ficheros de binding que lo importan. No ejecuté nada por el mandato de sólo lectura, así que el PASS lo acepto como reportado.

**Fixes requeridos:**

1. **El fixture real no está versionado.** El test de regresión lee `evidence/collision-scene-b2a-20261028/hits.json`, pero ese directorio aparece como no rastreado en git. En un clon limpio el test falla con FileNotFoundError y el SHA fijado no protege nada. Hay que commitear el fichero o registrar el SHA como requisito explícito del binder.
2. **El confusor nuevo no tiene test positivo.** Sólo se comprueba su ausencia en el fixture sintético, donde todo es FACE_INTERIOR. El test sobre datos reales no afirma que `offline_geometry_ambiguous_or_degenerate` aparezca en las filas con vertical. Una línea en ese test lo cerraría.

**Observación menor, no bloqueante.** `finite` acepta cualquier valor convertible a float, incluidos booleanos y cadenas numéricas. El contrato no lo restringe, y el productor siempre emite float, así que no es contraejemplo material.

No se detecta regresión en los llamadores: ambos bindings importan `consume` sin pasar hits de otro esquema. FIN_REVISION.