# Fondo conservado y calado de 0,95 m

Decisión viva del usuario, 08-10: conservar el fondo de 1 m y aceptar 0,95 m de calado mínimo. Base local 53c530d; paquete JunctionPreviewR2. No aplicar el antiguo candidato que rebajaba fondos y reserva vial.

1. Enumerar independientemente por cajas las caras nativas que intersectan los 19 corredores congelados de 24 m; evaluar todos los extremos de su intersección. Umbral 0,95 m sin descontar el antiguo centímetro. Comprobar cobertura del polígono y rechazar un obstáculo de 0,94 m. Los niveles siguen la regla de planos actual; no es prueba de oleaje máximo.
2. Dos vértices altos fuera de Narva estaban bajo el fondo de 1 m: (1992,6432) y (1836,6384). Ambos son componentes aisladas de un vértice, omitidas por min_vertices=4; profile_inland_v30 exigía componente perfilada también para elevar el fondo. Corregir esa condición solo para navegables altos. Una variante y una corrección de implementación como máximo; mantener bajos, Narva, cauces sustituidos, clases, niveles y tierra seca.
3. Candidato separado sobre el terreno actual. Verificar suelo mínimo, corredores completos, caras mixtas, carreteras, observadores y distancia a rutas ya probadas. Si pasa, mundo nuevo conservando todas las piezas del agua R2. Verificar fuentes, PBO y lecturas de suelo/agua en los dos puntos y controles. No repetir viajes que queden fuera de los cambios y de su halo físico.
4. Actualizar P9, registro vivo y handoff. Sin promoción de la base completa, push ni navmesh antes de Terrain Builder. El diagnóstico visual de tiles sigue abierto y separado.
