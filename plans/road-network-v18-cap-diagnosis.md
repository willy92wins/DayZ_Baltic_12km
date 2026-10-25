# Diagnóstico del movimiento vertical necesario en la transición V18

V18 con transición lateral de 24 m elimina el certificado estructural anterior,
pero sigue siendo inviable con cambios de altura limitados a 3 m. El nuevo
certificado combina 243 restricciones y deja dos vértices dominantes:
`(4368,6954)` y `(4512,6924)`. Se verificó algebraicamente una necesidad local
de al menos 3,877807 m. No es una cota suficiente para toda la red.

Fuente: `tests/regional_road_network_v18_constraints/infeasibility-certificate/`.
Sin nuevo ASC, WRP o NM. La base V10 sigue siendo la única desplegada.

[DESIGN] Una exploración diagnóstica acotada, empezando en 4 m. Cada siguiente
cota debe derivarse del certificado anterior; detener si la contradicción es
estructural, si existe un primal factible, al llegar a 12 m o a 600 s totales
(650 s de proceso). Un hilo, control de RAM, ningún terreno exportado.
El resultado solo decide si un movimiento vertical local razonable permite
resolver los mismos límites de conducción. No relaja anchura, pendiente,
suavidad, hidrografía, reserva ni la envolvente de edición.

Antes de producir un candidato, registrar el máximo necesario y revisar las
localizaciones. No asumir que 12 m es aceptable para producción por ser el
techo de un diagnóstico. Después siguen pendientes los consumidores
independientes, negativos, importación nativa y nueva navmesh.
