# Revisión acotada de la recuperación de agua

Encargo a Opus 5.5, solo lectura. No ejecutar herramientas ni cambiar archivos.
Lee únicamente los archivos enumerados y las definiciones concretas necesarias;
no explores otros proyectos ni memoria global. Trabajamos en una sesión autónoma
autorizada por Guillermo para acabar la base de terreno, con mapeado posterior.

Necesito fallos concretos del cambio, no una auditoría nueva de todo el mapa. Dos
operaciones independientes, ya implementadas: (1) restaurar cuatro lagunas del
diseño aprobado anuladas por la protección circular de Narva, conservando puente,
canal y carreteras; (2) corregir la continuidad de cursos secundarios sobre caras
reales, porque todos sus vértices mojados podían pasar y el eje seguir seco.

Fuentes en `P:/DayZ_Baltic_12km_dev`:

- `tools/terrain/restore_narva_ponds_v30.py` y `review_pond_recovery_v30.py`.
- `tools/terrain/connect_small_watercourses_v30.py` y `review_small_watercourse_fix_v30.py`.
- `tools/terrain/audit_small_watercourses_v30.py`.
- Definiciones usadas: `v30_common.py`, `audit_fairway_triangles_v30.py` (records,
  weights_at), `finish_shores_v30.py` (protect_corridors, discard_steeper_land_faces).
- Plan vivo: `plans/overnight-2026-10-03.md`, últimas dos secciones. Especificación:
  `plans/water-ground-rebuild-v1.md`, diseño agua/terreno, sin cargar el histórico.

Evidencia en `E:/DayZ-Baltic-Build`:

- `v30-pond-recovery/build.json`, `review.json`, `road-gates.json`,
  `small-watercourses.json`, `water/local-delta.json`.
- `v30-watercourse-continuity/build.json`, `review.json` (si terminó de escribir),
  `road-gates.json`, `legacy-terrain-gates.json`, `small-watercourses.json`.

El gate legado de Narva sigue devolviendo FAIL por los 75 vértices de lagunas:
no se modificó ni se esconde. El gate local comprueba explícitamente la excepción
y el resto de la protección. La continuidad conserva todos los metadatos de agua
y solo baja alturas. Dentro de la reserva puede bajar el lecho ya clasificado
como río/arroyo; todo el suelo seco queda idéntico. El objetivo de esa corrección
es franja central de 1 m y profundidad mínima 5 cm; máximo 1,2 m bajo el plano
menor y corte máximo 3 m. Es mejora parcial, no una declaración de ríos completos:
quedan 400 m de arroyos y 30 m de ríos secos fuera de plataformas/reservas viales.

Busca especialmente: (a) geometría o límites que el código no preserve, (b)
posibles falsos PASS o métricas engañosas del consumidor independiente, (c)
dependencias de empaquetado que invaliden el reuso de piezas al bajar solo alturas.
No pidas más renders para opinar: todavía no hay acceso al motor en esta sesión.
No propongas relajar umbrales solo para cerrar un PASS ni rediseñar la herramienta.

Devuelve máximo 900 palabras: hallazgos con severidad, mecanismo, path:line y
corrección mínima, o indica que no encontraste fallos dentro de ese alcance.
Distingue lo demostrado por lectura de lo que necesitaría prueba en DayZ.
