# EV91 — mismo suavizado local con salida descendente conservada

Propuesta previa a autoría. EV90 permanece íntegro y sin aceptar: su cálculo
limitaba alturas pero no impedía mínimos nuevos; aparece uno de 0.01275146 m
en (844,375). No se cambia ese criterio para admitir el resultado.

Se conservan B, P/F, objetos, máscaras, las 85 variables y las cotas float32
del preflight EV90 `8c8ec80cbb7029f510c832adf90a8871e385fbd8ec52ee5043d5ea24e1099d63`.
El ámbito sigue siendo la misma ventana 17×17 con núcleo13 y collar2. No hay
extensión global, cambio de agua ni construcción de paquete en esta unidad.

## Cambios de método frente a EV90 [DESIGN]

EV90 completo también falló la energía del collar y su ángulo horizontal.
Se añade el guard certificado en `collar-guard-preflight.json` (SHA256
`1f1e68cf1b2358c2bb5d21d9268cfd2f030b46b6d7247227bc55be0efe2fc0df`):
fijar exactamente B en las43 variables que participan en cualquiera de las107
stencils del collar o en cualquiera de los4 vértices de las328 bisagras que
mide el consumidor. Quedan42 grados libres. Esto conserva las normales y la
energía del collar por identidad de sus soportes. No selecciona solo máximos.

Se mantienen85 entradas del vector, las350 stencils y todas las poblaciones
de medida originales. Solo se estrechan43 cotas del solver a L=U=B; las cotas
físicas originales se registran aparte. SLSQP admite variables fijadas mediante
bounds iguales (`_minimize.py:707-766`; las elimina temporalmente cuando hacen
falta diferencias finitas, condición que aquí no se activa con ambos Jacobianos
analíticos; `_validate_bounds:1108-1110` rechaza upper<lower, admite igualdad).
No se redefine collar, WINDOW ni CORE. La preparación D8-only y su rechazo
se preservan en `prepared-d8-only/`; todavía no se había ejecutado el solver.

Para cada centro cuyo vecindario3×3 toca cualquier variable, elegir a partir
de B el vecino de menor (altura,fila,columna). Si Bcentro ya era mínimo
estricto8, queda exento; en otro caso exigir Hcentro>=Hvecino. Incluir centros
fijos: podrían convertirse en mínimos al elevar sus vecinos. No añadir margen
ni romper ciclos planos; filas fijo/fijo se verifican sin añadir variables.

Conservar exactamente la matriz A/rhs y el funcional 0.5*||A*x-rhs||² de EV90.
Sustituir BVLS por una llamada SLSQP con gradiente analítico A.T@(A*x-rhs),
las cotas físicas estrechadas por el guard y LinearConstraint(C,d,+inf). Punto inicial B, tras comprobar
que cumple cotas y todas las filas. Si B no fuese factible, parar sin elegir
otra inicialización ni cambiar cotas. `ftol=1e-10,maxiter=1000`; worker120s,
una llamada, marker exclusivo. El presupuesto no es una garantía de convergencia.

Hacer un único cast final a float32. Rechazar sin reparación si no respeta
exactamente cotas y testigos; comprobar todos los criterios EV90 sin cambios:
forma sobre WINDOW, energía/collar, ángulos, topología, caras compiladas y P9.
El nuevo criterio no implica ausencia de mesetas; su gate independiente queda.
No se recalibran umbrales, radio ni pesos al ver la salida.

## Anclas y puertas antes de ejecutar

La propuesta de testigos está en `../ev90-author/descent-method-proposal.md`.
La afirmación inicial de versión SciPy1.17.1 en esa nota se corrigió contra el
runtime autorizado: GIS Python importa SciPy1.18.1. Fuentes reales:
`C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Lib/site-packages/scipy/optimize/`:
`_minimize.py:54,1134` (firma y normalización), `_constraints.py:139` (LinearConstraint),
`_slsqp_py.py:220-244` (firma, maxiter y ftol). [EXACT] esas APIs están presentes.

Fixtures sin solver: centro variable/testigo fijo, centro fijo/testigo variable,
ambos variables, mínimo heredado, meseta con ciclo y protección tras cuantizar.
Revisión independiente del autor y sus filas antes de una candidata. Tras
consumidor completo, inspección de cuatro perfiles/malla; no aceptación runtime.
EV90 full debe terminar antes de autorizar el solve EV91 y cualquier otro fallo
material se analizará antes, sin variar el contrato silenciosamente.
