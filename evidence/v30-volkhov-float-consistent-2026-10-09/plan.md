# EV68 — única corrección de precisión de EV66

EV66 exigía ángulos y pendientes exactos sobre vértices de núcleo ya cuantizados a float32, aunque el consumidor permite 0,0001 grados de precisión en esos dos gates desde EV63. El discriminador `EV66/float-feasibility.json` comprueba 131 bisagras con una sola variable: 82 no pueden alcanzar la restricción exacta ni siquiera en su mínimo escalar y extremos. Su exceso máximo es 0,00000550 grados; ninguna excede el criterio independiente. Por tanto, el dominio continuo era estrictamente incompatible por cuantización en esos puntos.

Mantener la semilla EV65, las 1019 variables, seis grupos, 100 iteraciones por grupo, 300 s totales, niveles, dominio y todas las protecciones. Incorporar 0,00005 grados de margen de precisión en las restricciones de autoría de pliegue existente y pendiente, la mitad de la tolerancia ya declarada del consumidor. El límite de incremento de 2 grados sigue exacto. Ningún gate se modifica. Una ejecución de reparación; si falla, no repetir.

La derivada y las normales se siguen comprobando contra consumidores independientes antes de resolver. El consumidor EV65 sigue byte-idéntico. La excepción de política de las charcas647/651 continúa pendiente; la preparación y la prueba no promueven el candidato.
