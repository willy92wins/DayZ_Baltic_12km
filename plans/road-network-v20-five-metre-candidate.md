# V20: candidato de mínimo movimiento total con cota local de5m

El diagnóstico minimax activo alcanzó un subproblema óptimo con cota necesaria
4,969460797m (603.712 filas originales). El primal todavía incumple otras filas:
no se afirma mínimo global ni que5m sean suficientes. Sin embargo, esa cota
inferior justifica probar5m de edición local, frente a4m certificados inviables.

[DESIGN] Un solve L1 con generación de restricciones y cota fija5m, sembrado
con317.978 filas del diagnósticoV19. Minimizar suma de cambios absolutos deja
el terreno no necesario en su altura original. Mismos datos, transición24m,
límites de conducción y protección V18. Todas las6.523.172 filas originales
deben pasar antes de escribir un ASC.600s/650s de proceso,un hilo/RAM>=2GiB.
Sin aumento automático de la cota. El minimax separado no genera terreno.

Este límite revisa explícitamente el anterior3/4m; no altera las tolerancias
de conducción ni la geografía. Revisar distribución y ubicación de los cambios,
no solo el máximo. El consumidor independiente deberá recibir límite5m y
envolvente36,5m expresamente, sin tomarlos de los valores que declara el productor.
Agua/fairways y Narva intactos; pisos de islas y reserva conservados. Negativos,
Terrain Builder, nueva navmesh y pruebas nativas siguen obligatorios.
