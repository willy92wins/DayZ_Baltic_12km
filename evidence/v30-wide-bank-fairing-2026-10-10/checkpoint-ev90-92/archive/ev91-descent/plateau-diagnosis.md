# Diagnóstico de la meseta EV91 — solo lectura

**EV91 sigue rechazado por forma.** El chequeo local detecta una meseta constante 2×2 nueva en la esquina superior izquierda `(836,370)`, un área geométrica de 36 m² con celdas de 6 m. La candidata y los artefactos EV91 permanecen sin cambios.

## Mecanismo observado

Los cuatro valores B son `[1.76762295, 1.88481438; 1.58114040, 1.8000000] m`; H los lleva a `1.92890799 m`. El rango original es `0.303674 m` y los incrementos son `+0.161285`, `+0.044094`, `+0.347768` y `+0.128908 m`. A esa altura un ULP float32 mide `1.19209e-7 m`; la convergencia supera 369 mil ULP incluso en el vértice que menos sube. Es una meseta real, no cuantización incidental.

Las cotas físicas de esos cuatro nodos no están activas en H. Tampoco hay un ciclo D8 que fuerce igualdad. Tres desigualdades D8 quedan activas con holgura cero y apuntan al nodo `(837,370)`: `(836,370)≥(837,370)` (fila 29), `(836,371)≥(837,370)` (fila 30) y `(837,371)≥(837,370)` (fila 38). Ese vértice era un mínimo estricto heredado y se exime de testigo. Las desigualdades permiten valores mayores y no imponen igualdad; en la solución observada, el objetivo de suavizado las deja activas y lleva los cuatro valores a un mismo nivel. Por tanto, la causa observada es el acoplamiento del objetivo cuadrático con restricciones de orden activas, no una igualdad contractual ni una cota física. Esto describe esta solución, no demuestra que sea la única solución posible.

## Discriminador en la recta B→H

Sin guardar una variante, evalué en memoria `h(α)=float32(B+α(H−B))`. La prominencia del foco alcanza la reducción requerida del 25% desde α=`0.2276403` en E–O y `0.2206448` en N–S. Para energía usé el consumidor independiente `verify_ev88q.stencil_records` y `stencil_energy`, que pesa las stencils Dxz por 2. Sus energías B, punto medio y H son `221.226392`, `149.252666` y `119.540296`; la forma cuadrática medida sobre la recta cruza el límite `0.75·E(B)` en α=`0.3538475102`. Esto reemplaza el cálculo anterior con el coste del autor, que no es la puerta del consumidor.

En ese único límite, tras un cast float32 en memoria, la energía baja `25.0000005%`; las cinco puertas locales de forma pasan, el ángulo local cae de `29.999999°` a `21.243630°` (reducción `8.756369°`) y la celda no queda plana (rango `0.196220 m`). La energía de collar queda igual que B (`1.031951484`). Es un testigo escalar diagnóstico, **no** un alpha escogido ni una candidata. Para la meseta de H, los cuatro valores pasan a la misma representación float32 solo cerca del extremo, cuando `α>0.9999998286`; mover un ULP en H fingiría una reparación.

El testigo demuestra coexistencia local de las puertas en un punto, pero no calcula el intervalo admisible conectado máximo, no certifica todos los gates globales/físicos/compilados y no sustituye el consumidor completo. Un diseño futuro tendría que derivar ese intervalo de forma determinista a partir de los gates ya fijados y, si se decide amortiguar, declarar de antemano una regla interior con margen; no se debe escoger alpha por barrido ni retocar umbrales tras ver el resultado.

## Alcance del plan

EV91 requiere una llamada SLSQP, un cast float32 y rechazo sin reparación (`plan.md:38-48`; `author_ev91.py:155-177`). Así que amortiguar H después del solve queda fuera del plan EV91 actual. Aquí no se eligió alpha, no se ejecutó solver ni consumidor completo y no se escribió terreno.

Fuentes: `author_ev91.py:25-38,75-81,155-177`; `next-method-consumer/shape_contract.py:23-31,65-84`; `review-independent/verify_ev88q.py:618-648,661-700`. Reproducción del cálculo energético en `recompute-consumer-energy.py`. Los SHA completos de inputs y herramientas están en `plateau-diagnosis.json`.
