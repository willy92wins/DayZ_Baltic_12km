# Revisión de colisión compacta del río131 (solo lectura)

Usuario autoriza reparar ríos/terreno, autonomía y optimización frente a Chernarus. El candidato anterior131 tiene25.156 componentes frente a169 del kit. Esta unidad reduce ese coste; no afirma rendimiento ni aceptación en motor.

W=C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c
R=E:/DayZ-Baltic-Build/shape-repair-20261025

Solo Read/Grep/Glob. No ejecutar, escribir, delegar ni usar MCP/Git. Revisa una vez estos archivos y da un veredicto con defectos concretos y mecanismo/path:line; separar hipótesis. Presupuesto15min.

- W/tools/water/compact_stream_collision_v31.py. Particiona grid de lecho. ConvexHull de techo y base plana inferior; bound suficiente min_facet max_source_triangle_vertices. Cuando es demasiado conservador, refinamiento planar exacto de polígonos. Devuelve bound bruto<=.03m y extensión lateral<=.01m. No acepta motor.
- R/author_compact_collision.py. Consume MLOD original firmado por hash y preserva BYTES de LOD0 visual, memoria y roadway. Solo cambia Geometry. Centra cada techo bajándolo ceil(bound/2*512)/512: margen local inferior hasta15,625mm; después requiere consumidor global absoluto<=20mm. Reserializa solo Geometry en contenedores MLOD, con componentes convexos cerrados y volumen negativo.273? Consultar packing-report para el número real, no asumir esta cifra.
- W/tools/water/review_compact_collision_v31.py. Independiente sobre MLOD guardado: todas las caras asignadas exactamente una vez, cierre/manifold/volumen, convexidad por semiespacios, BYTES de otros LOD idénticos, refinamiento planar de todas las caras superiores contra TODAS las caras originales (incluye interacciones entre componentes y chunks). Comprueba cobertura completa, extensión lateral<=1cm y error vertical absoluto<=2cm. Revisa especialmente falsos PASS por fondo/laterales confundidos con techo o caras desaparecidas, normal, y si máximos de diferencias lineales están cubiertos por los vértices del refinamiento común.
- W/tests/test_compact_stream_collision_v31.py: plano, valle que no puede cerrarse, error interior con esquinas idénticas, hueco y expansión lateral.
- R/river-131-compact-a/packing-report.json (suma2245 componentes) y contact-review.json si ya terminó. R/tests-compact.log. Modelos/source están en esa carpeta, pero no hace falta leer binarios enormes.

Compilado y review binario posterior reutilizan verify_compiled_stream_pilot_v31.py. No hay despliegue, no se acepta peor colisión en motor por pasar estas cotas; es una candidatura offline. Los demás ríos, formas protegidas y pruebas de rendimiento siguen pendientes. Prohibido suavizar los checks para obtener PASS.
