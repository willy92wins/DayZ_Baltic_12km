# Revisión independiente EV85 y diagnóstico rechazado

El consumidor independiente está en `verify_ev85.py`; no importa el autor ni ejecuta el solver. Reconstruye el selector de 21+18 nodos y 220 aristas desde B, máscaras y P/F. Comprueba las 72 celdas del parche completo para cobertura ODOL, incluidas celdas cuyos nodos sean fijos. Fixtures: `fixture-self-test.json` PASS; `py_compile` PASS.

EV85 terminó `SOLVER_FAILED`; no existe candidato aceptado. Se inspeccionó únicamente `diagnostic-vector.npz` (SHA-256 `e3b6389586c88b7028f156bab7f8fc10b7f3503c91479aef3032672880b1861e`) con `--diagnostic-vector`. El informe `diagnostic-review.json` queda marcado `REJECTED_DIAGNOSTIC_REVIEW`; el NPZ solo contiene heights/delta y no prueba metadatos.

**Fallos que explican el rechazo:** al cuantizar float32 invierte 12 de 220 órdenes 8-vecinas; máximo `5.245208740234375e-6 m`. Hay 9 extremos axiales nuevos en los parches. Conserva 138 cruces, pero el máximo desplazamiento es `1.0000009444866953 m`, por encima del límite exacto de 1 m en `9.44e-7 m`. Estos son gates independientes del status 8 de SLSQP.

**Métricas que sí pasan en este diagnóstico:** energía de las 12 bisagras por foco baja 70.73% y 63.62%; energía de la unión deduplicada baja 49.35%. No aparecen bisagras nuevas >30°, los máximos sectoriales no empeoran y las pendientes respetan `max(35°, B)`. Contra la población congelada EV82-B, bank mantiene `n=1,591,990`, p99 `4.982070162°` frente a `4.982070187°` y un ángulo >30°; interior mantiene `n=7,170,630`, p99 `3.667753611°` y 112 >30°.

La cobertura offline usa ODOL compilados y transforms 0WZD de B: en 72 celdas, diferencia de diseño P/F menos exposición compilada <`5e-12 m²`; no gana exposición fuera del diseño ni en caras previamente secas. El área expuesta por el diagnóstico aumenta `39.12 m²` en ambos campos físicos/visibles y no pierde área. El PBO desplegado coincide con su `compiled_wrp_sha256`; el WRP fuente staged tiene su propia identidad (`3071395e…`), distinta del OPRW compilado por diseño. Los transforms son del 0WZD fuente vinculados por manifiesto/hashes, no readback del motor.

La reparación EV85-R descrita en `../quantized-repair-plan.md` parece coherente como única proyección determinista float32 con límite de corrección `1e-4 m`; sigue condicionada a pasar todos los gates independientes. No convierte el diagnóstico en candidato ni autoriza otra variante si falla. Sin empaquetado, despliegue o DayZ.

## EV85-R: evaluación del candidato reparado

Se comprobó `quantized-repair/candidate-terrain.npz`, SHA-256 `a4434bf7812e1e35299901e93c653f04472f343bcdb93ff3d2c9080c1b61e196`, en `repaired-review.json`. Veredicto `FAIL_EV85_REVIEW`: solo falla `no_new_axial_minima_or_maxima_in_either_7x7_patch`; los otros gates de geometría, agua, cotas, cruces, ángulos, distribuciones y cobertura pasan. El status original del solver sigue `SOLVER_FAILED`.

La reparación numérica concuerda con una reconstrucción independiente de la proyección descrita: 39 variables, 220 aristas, 96 grupos de igualdad, 33 alturas distintas, todos los órdenes y cotas float32 exactos, fijos inmutables y máximo delta frente al diagnóstico `6.198883056640625e-6 m`. No importé la función del autor como validador.

Los nueve extremos axiales nuevos no son todos microinversiones. En el vector previo a reparación, seis tenían margen estrictamente positivo entre `4.768e-7` y `4.768e-6 m`; tres eran ya empates exactos con lado opuesto estricto. Tras la proyección, el nuevo conjunto vuelve a tener nueve extremos débiles, todos con margen estricto exactamente `0 m`: son bordes de mesetas por igualdad, no inversión residual. El gate aprobado los cuenta como extremos, así que EV85-R queda rechazado aunque no haya máximos/minimos estrictos nuevos.

No se empaquetó, desplegó ni ejecutó DayZ. Los transforms de agua siguen siendo 0WZD fuente hash-vinculado, no readback del motor.
