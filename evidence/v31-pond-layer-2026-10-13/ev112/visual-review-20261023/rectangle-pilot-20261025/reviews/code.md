**Veredicto: SOUND-with-fixes.** El mecanismo es correcto y no encuentro falso PASS ni regresión de la ruta por defecto del solver. Hay una incoherencia de etiquetado que corregir y dos artefactos de evidencia que faltan antes de hablar de integración.

**Mecanismo verificado**

- Dominio exacto: componente 8-conexo de residual >.3 cruzado con la caja del detector, y dominio euclídeo ≤4 celdas con relleno de 4 para que todo stencil que toque un libre quede interior (`tools/terrain/repair_rectangle_pilot_ev112.py:47-56`). Coincide con la definición del detector (`tools/quality/shape_patterns_ev112.py:132-134`, umbral .30 en `:17`).
- Límites firmados por eje: fuera de la caja [min(d0,-.2999), max(d0,.2999)], dentro ±.2999 (`repair_rectangle_pilot_ev112.py:24-30`). La restricción usa el mismo signo y los mismos pesos +1/-.5/-.5 que el detector, incluye stencils de centro fijo con vecino libre, y falla cerrado si un stencil totalmente fijo no cabe en sus límites (`tools/terrain/repair_free_shapes_ev112.py:28-39`).
- Corona de los 4 pozos protegidos con el mismo convenio que el autor guardado (`repair_rectangle_pilot_ev112.py:61-64` frente a `repair_guarded_shapes_ev112.py:107-110`).
- Float32: el candidato se redondea antes de todos los controles; las segundas diferencias se recalculan en rejilla completa para ambos ejes, con tolerancia 2e-6 frente a un margen de 1e-4 entre cap y umbral (`:77-90`). La asignación `h[sl][use]=...` escribe por vista, es correcta.
- Ruta por defecto: comparado línea a línea con el solver de E (`evidence/.../hybrid-relief-20261025/replay/solver-used.py:18-85`), el único cambio es el kwarg `curvature_bounds=None` y la línea `:106`, que solo añade la restricción cuando no es None. `main()` idéntico. El replay de E no fija el hash del solver (`proof.json:7-10`) y el autor guardado comprueba identidad de módulo, no hash (`repair_guarded_shapes_ev112.py:48`). 164 tests PASS en el log, incluidos los 5 nuevos.
- Evidencia cruzada: fixture con el mismo sha en preflight-c, candidato f y `tests/fixtures/rectangle-narva.json`. Entrada 7051… es E merged (`HANDOFF.md:9`) y dominios 272a… son los de E (`proof.json:6`). La fusión recomputó la huella con el bury y la comparó array a array contra la de E merged, con cero cambios (`E:/.../validate_rectangle_consumers.py:13-16`). Carreteras PASS con cero fallos; la fila FAIL es la base antigua 07054c… con la máscara actual, no E, y no indica regresión.

**Fix requerida**

1. Etiquetas de eje cruzadas en el control independiente. En `repair_rectangle_pilot_ev112.py:86`, eje 0 es NS y eje 1 es EO, pero en `signed_limits` (`:26-27`), en la fixture y en el solver (`repair_free_shapes_ev112.py:30`) eje 0 es EO. No produce falso PASS, porque se comprueban ambos ejes contra d0 recalculado, pero `report.json.curvature[axis]` queda etiquetado al revés que `curvature_lower/upper[axis]`. Cambiar el orden de las dos expresiones en `:86`. No hace falta regenerar el candidato; sí el informe si se quiere evidencia coherente.

**Pendiente antes de preparar integración**

- No existen `rectangle-pilot-f/all-protected-audit.json` ni `rectangle-pilot-f/shape-screen.json` aunque hay scripts preparados para ambos (`rectangle_independent_audit.py`, `screen_rectangle_pilot.py`). El script de staging de E exige el audit PASS (`tools/terrain/stage_guarded_relief_ev112.py:23`). La comparación explícita "todos los vértices cambiados por D/E exactos" vive en el screen (`screen_rectangle_pilot.py:14`) y tampoco tiene salida registrada.
- Test de regresión del default: los 159 tests existentes cubren `curvature_bounds=None`, pero ninguno fija que el default no cambie. Opcional: un test que compare la salida del solver sin kwarg con la del replay de E en la fixture híbrida.

**Notas no bloqueantes**

- El control exterior usa .3 donde la restricción usa .2999 (`:89`). Es más laxo que el solver, pero igual al contrato del detector; `only_target_rectangle_removed` cierra el hueco.
- Extremos libres fuera del dominio no reciben corona. Es el mismo convenio que E, y `no_worse_prominence` lo cubre en rejilla completa.
- No he podido abrir los npz ni calcular hashes sin comandos. Las identidades las cruzo por los sha que recogen los informes y los scripts.